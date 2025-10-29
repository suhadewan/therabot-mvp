# Streak System Feature

## Overview
A Duolingo-style streak tracking system has been implemented for the Therabot PWA. Users earn streaks by sending messages to the chatbot each day, encouraging daily engagement with the mental health support tool.

## Features Implemented

### 1. Database Schema
- **New Table**: `streak_tracking`
  - Tracks daily user activity
  - Records message count per day
  - Stores activity dates for streak calculation
  - Supports both SQLite and PostgreSQL

### 2. Backend API
- **Endpoint**: `GET /api/streak/<user_id>`
  - Returns streak data including:
    - `current_streak`: Number of consecutive days with activity
    - `longest_streak`: Best streak achieved
    - `total_days`: Total days with activity
    - `weekly_activity`: Last 7 days activity map
    - `has_activity_today`: Boolean flag for today's activity

### 3. Automatic Tracking
- Streak automatically updates when users send messages
- Integrated into the existing chat message flow
- No user action required beyond normal chatbot usage

### 4. Visual Display

#### Streak Widget Components:
1. **Flame Icon** 🔥 - Visual indicator of the streak
2. **Streak Counter** - Large, bold number showing current streak
3. **Motivational Message** - Dynamic message based on streak status
4. **Weekly Calendar** - 7-day view showing activity pattern

#### Design Features:
- Dark theme matching existing UI
- Amber/orange color scheme (consistent with app branding)
- Responsive design for mobile and desktop
- Animated checkmarks for active days
- Blue border highlight for today
- Gray-out effect for inactive days

### 5. User Experience

#### First-time User:
- Shows "0 day streak"
- Message: "Send a message today to start your streak!"
- All calendar days grayed out

#### Active User (with activity today):
- Shows current streak count
- Message: "🎉 Amazing! You've kept your streak going for X days!"
- Today's calendar day highlighted with checkmark

#### User Without Activity Today:
- Shows yesterday's streak count
- Message: "Send a message today to keep your streak alive!"
- Today's calendar day highlighted but not checked

## Location
The streak widget is displayed in the sidebar, above the emergency helplines section, making it visible without cluttering the main chat interface.

## Technical Implementation

### Files Modified:
1. **database.py**
   - Added `streak_tracking` table
   - Implemented `update_streak()` method
   - Implemented `get_streak_data()` method
   - Added support for both SQLite and PostgreSQL

2. **pwa_app.py**
   - Added `/api/streak/<user_id>` endpoint
   - Integrated streak update in message processing
   - Added to the `process_message()` function

3. **templates/index.html**
   - Added streak container HTML
   - Added CSS styling for streak display
   - Implemented JavaScript functions:
     - `loadStreakData()` - Fetches streak from API
     - `renderStreak()` - Updates UI with streak data
     - `renderWeeklyCalendar()` - Displays 7-day calendar
   - Auto-updates after each message sent

## Mobile Responsive
- Scales appropriately on smaller screens
- Touch-friendly interface
- Optimized layout for mobile view
- Adapts to different screen sizes (768px, 480px breakpoints)

## Benefits
1. **Engagement**: Encourages daily interaction with mental health support
2. **Habit Formation**: Builds consistent wellness check-in routine
3. **Motivation**: Visual feedback and gamification elements
4. **Progress Tracking**: Users can see their commitment over time
5. **Positive Reinforcement**: Celebratory messages for streak milestones

## How It Works

1. User logs in and chat interface loads
2. Streak data automatically fetched from server
3. Weekly calendar and streak count displayed
4. When user sends a message:
   - Message saved to database
   - Streak record updated/created for today
   - Streak display refreshes automatically
5. Streak counter shows consecutive days with activity
6. Missing a day resets the streak to 0

## Future Enhancements (Possible)
- Push notifications to remind users to maintain streak
- Milestone badges (7 days, 30 days, 100 days, etc.)
- Streak recovery option (1-time streak freeze)
- Social sharing of streak achievements
- Streak leaderboard (if multiple users)
- Personalized streak goals

## Testing
To test the feature:
1. Log in to the app
2. Observe the streak display showing "0 day streak"
3. Send a message to the chatbot
4. Streak should update to "1 day streak" with today marked
5. Return tomorrow and send another message
6. Streak should increment to "2 day streak"
7. Skip a day and the streak resets

## Database Migration
The new `streak_tracking` table will be created automatically on next app startup. No manual migration required as the `init_db()` function handles table creation.

## Notes
- Streaks are timezone-aware (uses IST/Asia/Kolkata timezone from app config)
- Each user's first message of the day counts for the streak
- Multiple messages in one day don't create multiple streak entries
- Database uses UNIQUE constraint on (user_id, activity_date) to prevent duplicates

