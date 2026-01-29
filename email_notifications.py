"""
Email notification module for flagged chat alerts.
Sends notifications to on-call reviewers based on time of day (EST).
Uses Elastic Email API for sending.
"""

import os
import logging
import requests
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# Timezone for routing emails
EST = pytz.timezone('US/Eastern')

# Email configuration - set TEST_MODE=true to use test emails
TEST_MODE = os.getenv('FLAG_EMAIL_TEST_MODE', 'true').lower() == 'true'

# Test emails (used when TEST_MODE is true)
TEST_EMAILS = {
    'akanksha': 'suha.dewan@gmail.com',
    'bhavya': 'suhad@vt.edu',
    'anwesha': 'suhad@vt.edu'
}

# Production emails (used when TEST_MODE is false)
PRODUCTION_EMAILS = {
    'akanksha': os.getenv('EMAIL_AKANKSHA', 'akankshada@gmail.com'),
    'bhavya': os.getenv('EMAIL_BHAVYA', 'bsrivastava@worldbank.org'),
    'anwesha': os.getenv('EMAIL_ANWESHA', 'anb9945@g.harvard.edu')
}

# Elastic Email configuration
ELASTIC_EMAIL_API_KEY = os.getenv('ELASTIC_EMAIL_API_KEY', '')
ELASTIC_EMAIL_FROM = os.getenv('ELASTIC_EMAIL_FROM', 'alerts@mind-mitra.com')
ELASTIC_EMAIL_FROM_NAME = os.getenv('ELASTIC_EMAIL_FROM_NAME', 'MindMitra Alert System')

# Elastic Email API endpoint
ELASTIC_EMAIL_API_URL = 'https://api.elasticemail.com/v2/email/send'


def get_on_call_reviewer() -> dict:
    """
    Determine which reviewer is on call based on current EST time.

    Schedule (EST):
    - Akanksha: 9 PM - 5 AM EST
    - Bhavya: 5 AM - 1 PM EST
    - Anwesha: 1 PM - 9 PM EST

    Returns dict with 'name' and 'email'
    """
    now_est = datetime.now(EST)
    hour = now_est.hour

    emails = TEST_EMAILS if TEST_MODE else PRODUCTION_EMAILS

    if 21 <= hour or hour < 5:  # 9 PM - 5 AM
        return {'name': 'Akanksha', 'email': emails['akanksha']}
    elif 5 <= hour < 13:  # 5 AM - 1 PM
        return {'name': 'Bhavya', 'email': emails['bhavya']}
    else:  # 1 PM - 9 PM (13 <= hour < 21)
        return {'name': 'Anwesha', 'email': emails['anwesha']}


def format_flag_type(flag_type: str) -> str:
    """Format flag type for display"""
    flag_labels = {
        'SI': 'Suicidal Ideation',
        'SH': 'Self-Harm',
        'HI': 'Homicidal Ideation / Safety Concern',
        'EA': 'Emotional/Physical Abuse',
        'crisis': 'Crisis',
        'abuse': 'Abuse',
        'moderation': 'Content Moderation',
        'safety_concern': 'Safety Concern'
    }
    return flag_labels.get(flag_type, flag_type)


def build_alert_email_html(access_code: str, message: str, flag_type: str,
                           emergency_contact: dict = None, reviewer_name: str = '') -> str:
    """Build HTML email content for flagged chat alert"""

    flag_display = format_flag_type(flag_type)

    # Emergency contact section
    emergency_section = ''
    if emergency_contact and emergency_contact.get('name'):
        emergency_section = f'''
        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px; border-radius: 4px;">
            <h3 style="color: #92400e; margin: 0 0 10px 0;">Emergency Contact Provided</h3>
            <p style="margin: 5px 0;"><strong>Name:</strong> {emergency_contact.get('name', 'N/A')}</p>
            <p style="margin: 5px 0;"><strong>Relationship:</strong> {emergency_contact.get('relationship', 'N/A')}</p>
            <p style="margin: 5px 0;"><strong>Phone:</strong> {emergency_contact.get('phone', 'N/A')}</p>
        </div>
        '''
    else:
        emergency_section = '''
        <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin-top: 20px; border-radius: 4px;">
            <p style="color: #991b1b; margin: 0;"><strong>No emergency contact provided by user</strong></p>
        </div>
        '''

    # Get current EST time for the email
    now_est = datetime.now(EST)
    timestamp = now_est.strftime('%B %d, %Y at %I:%M %p EST')

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #dc2626, #991b1b); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Flagged Chat Alert</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Immediate attention required</p>
        </div>

        <div style="background: white; padding: 25px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p style="color: #6b7280; margin-top: 0;">Hi {reviewer_name},</p>

            <p>A chat message has been flagged and requires your review:</p>

            <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280; width: 120px;"><strong>Access Code:</strong></td>
                        <td style="padding: 8px 0; font-family: monospace; font-size: 16px; color: #1f2937;">{access_code}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280;"><strong>Flag Type:</strong></td>
                        <td style="padding: 8px 0;">
                            <span style="background: #fef2f2; color: #dc2626; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">
                                {flag_display}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280;"><strong>Time:</strong></td>
                        <td style="padding: 8px 0;">{timestamp}</td>
                    </tr>
                </table>
            </div>

            <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; border-radius: 4px;">
                <h3 style="color: #991b1b; margin: 0 0 10px 0;">Flagged Message:</h3>
                <p style="margin: 0; color: #374151; white-space: pre-wrap;">{message}</p>
            </div>

            {emergency_section}

            <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px; margin: 0;">
                    <strong>Next Steps:</strong> Please review this conversation in the
                    <a href="https://mind-mitra.com/admin" style="color: #667eea;">Admin Dashboard</a>
                    and take appropriate action if needed.
                </p>
            </div>
        </div>

        <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
            <p style="margin: 0;">MindMitra Alert System</p>
            <p style="margin: 5px 0 0 0;">This is an automated message. Please do not reply directly.</p>
        </div>
    </body>
    </html>
    '''

    return html


def build_alert_email_text(access_code: str, message: str, flag_type: str,
                           emergency_contact: dict = None, reviewer_name: str = '') -> str:
    """Build plain text email content for flagged chat alert"""

    flag_display = format_flag_type(flag_type)
    now_est = datetime.now(EST)
    timestamp = now_est.strftime('%B %d, %Y at %I:%M %p EST')

    emergency_text = ''
    if emergency_contact and emergency_contact.get('name'):
        emergency_text = f'''
EMERGENCY CONTACT PROVIDED:
- Name: {emergency_contact.get('name', 'N/A')}
- Relationship: {emergency_contact.get('relationship', 'N/A')}
- Phone: {emergency_contact.get('phone', 'N/A')}
'''
    else:
        emergency_text = '\n** NO EMERGENCY CONTACT PROVIDED BY USER **\n'

    text = f'''
FLAGGED CHAT ALERT - Immediate Attention Required

Hi {reviewer_name},

A chat message has been flagged and requires your review.

-------------------
DETAILS
-------------------
Access Code: {access_code}
Flag Type: {flag_display}
Time: {timestamp}

-------------------
FLAGGED MESSAGE
-------------------
{message}

{emergency_text}
-------------------
NEXT STEPS
-------------------
Please review this conversation in the Admin Dashboard:
https://mind-mitra.com/admin

-------------------
MindMitra Alert System
This is an automated message. Please do not reply directly.
'''

    return text


def send_flag_notification(access_code: str, message: str, flag_type: str,
                          emergency_contact: dict = None) -> bool:
    """
    Send email notification for a flagged chat.

    Args:
        access_code: The user's access code
        message: The flagged message content
        flag_type: Type of flag (SI, SH, HI, EA, etc.)
        emergency_contact: Dict with 'name', 'relationship', 'phone' if available

    Returns:
        True if email sent successfully, False otherwise
    """

    if not ELASTIC_EMAIL_API_KEY:
        logger.warning("ELASTIC_EMAIL_API_KEY not set - skipping flag notification email")
        return False

    try:
        # Get on-call reviewer
        reviewer = get_on_call_reviewer()

        if not reviewer['email']:
            logger.error(f"No email configured for on-call reviewer: {reviewer['name']}")
            return False

        # Build email content
        subject = f"[FLAGGED] {format_flag_type(flag_type)} - {access_code}"
        html_body = build_alert_email_html(access_code, message, flag_type, emergency_contact, reviewer['name'])
        text_body = build_alert_email_text(access_code, message, flag_type, emergency_contact, reviewer['name'])

        # Send via Elastic Email API
        payload = {
            'apikey': ELASTIC_EMAIL_API_KEY,
            'from': ELASTIC_EMAIL_FROM,
            'fromName': ELASTIC_EMAIL_FROM_NAME,
            'to': reviewer['email'],
            'subject': subject,
            'bodyHtml': html_body,
            'bodyText': text_body,
            'isTransactional': True
        }

        response = requests.post(ELASTIC_EMAIL_API_URL, data=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"Flag notification sent to {reviewer['name']} ({reviewer['email']}) for {access_code}")
                return True
            else:
                logger.error(f"Elastic Email API error: {result.get('error', 'Unknown error')}")
                return False
        else:
            logger.error(f"Elastic Email API HTTP error: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error("Elastic Email API timeout")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Elastic Email API request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending flag notification: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_flag_notification_async(access_code: str, message: str, flag_type: str,
                                 emergency_contact: dict = None):
    """
    Send flag notification in a background thread (non-blocking).
    Use this in the main request flow to avoid slowing down responses.
    """
    import threading

    def send_async():
        send_flag_notification(access_code, message, flag_type, emergency_contact)

    thread = threading.Thread(target=send_async, daemon=True)
    thread.start()
