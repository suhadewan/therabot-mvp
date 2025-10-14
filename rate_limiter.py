"""
Rate Limiter for Production Deployment
Prevents API abuse and controls OpenAI costs
"""

from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict
import threading

# In-memory rate limiter
# TODO: Upgrade to Redis for multi-server deployment
rate_limit_store = defaultdict(list)
lock = threading.Lock()


def rate_limit(max_requests=20, window_hours=1):
    """
    Rate limiter decorator to prevent API abuse
    
    Args:
        max_requests: Maximum messages allowed per window
        window_hours: Time window in hours
    
    Returns:
        Decorated function that enforces rate limit
    
    Example:
        @app.route('/api/chat', methods=['POST'])
        @rate_limit(max_requests=20, window_hours=1)
        def chat():
            # ... your code
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get user ID from request
            user_id = None
            if request.json:
                user_id = request.json.get('user_id')
            
            if not user_id:
                return jsonify({
                    "error": "User ID required",
                    "type": "error"
                }), 400
            
            current_time = time.time()
            window_seconds = window_hours * 3600
            
            with lock:
                # Clean old entries outside the time window
                rate_limit_store[user_id] = [
                    timestamp for timestamp in rate_limit_store[user_id]
                    if current_time - timestamp < window_seconds
                ]
                
                # Check if limit exceeded
                if len(rate_limit_store[user_id]) >= max_requests:
                    # Calculate retry time
                    oldest_request = min(rate_limit_store[user_id])
                    retry_after = int(window_seconds - (current_time - oldest_request))
                    
                    return jsonify({
                        "error": f"Rate limit exceeded. You can send {max_requests} messages per {window_hours} hour(s).",
                        "type": "rate_limit",
                        "retry_after_seconds": retry_after,
                        "retry_after_minutes": round(retry_after / 60, 1)
                    }), 429
                
                # Add current request timestamp
                rate_limit_store[user_id].append(current_time)
                
                # Log for monitoring
                remaining = max_requests - len(rate_limit_store[user_id])
                print(f"Rate limit: {user_id} - {len(rate_limit_store[user_id])}/{max_requests} used, {remaining} remaining")
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


def get_rate_limit_status(user_id: str, max_requests: int = 20, window_hours: int = 1) -> dict:
    """
    Get current rate limit status for a user
    
    Args:
        user_id: User identifier
        max_requests: Maximum allowed requests
        window_hours: Time window in hours
    
    Returns:
        Dictionary with rate limit status
    """
    current_time = time.time()
    window_seconds = window_hours * 3600
    
    with lock:
        # Clean old entries
        rate_limit_store[user_id] = [
            timestamp for timestamp in rate_limit_store[user_id]
            if current_time - timestamp < window_seconds
        ]
        
        used = len(rate_limit_store[user_id])
        remaining = max_requests - used
        
        # Calculate reset time
        if rate_limit_store[user_id]:
            oldest = min(rate_limit_store[user_id])
            reset_seconds = int(window_seconds - (current_time - oldest))
        else:
            reset_seconds = 0
        
        return {
            "user_id": user_id,
            "used": used,
            "remaining": remaining,
            "limit": max_requests,
            "window_hours": window_hours,
            "reset_seconds": reset_seconds,
            "reset_minutes": round(reset_seconds / 60, 1)
        }


def reset_rate_limit(user_id: str):
    """
    Reset rate limit for a specific user (admin function)
    
    Args:
        user_id: User identifier to reset
    """
    with lock:
        if user_id in rate_limit_store:
            del rate_limit_store[user_id]
            print(f"Rate limit reset for user: {user_id}")


# For production: Redis-based rate limiter
# Uncomment and configure when scaling to multiple servers
"""
import redis
from flask import current_app

def redis_rate_limit(max_requests=20, window_hours=1):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = request.json.get('user_id') if request.json else None
            if not user_id:
                return jsonify({"error": "User ID required"}), 400
            
            redis_client = redis.from_url(current_app.config['REDIS_URL'])
            key = f"rate_limit:{user_id}"
            window_seconds = window_hours * 3600
            
            # Use Redis sorted set for time-based rate limiting
            current_time = time.time()
            
            # Remove old entries
            redis_client.zremrangebyscore(key, 0, current_time - window_seconds)
            
            # Count current requests
            request_count = redis_client.zcard(key)
            
            if request_count >= max_requests:
                return jsonify({
                    "error": f"Rate limit exceeded",
                    "retry_after": window_seconds
                }), 429
            
            # Add current request
            redis_client.zadd(key, {str(current_time): current_time})
            redis_client.expire(key, window_seconds)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
"""

