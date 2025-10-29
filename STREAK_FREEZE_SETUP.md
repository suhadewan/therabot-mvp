# Streak Freeze Feature Setup Guide

## Overview
The Duolingo-style streak freeze feature has been implemented! Users can now freeze their streak once per week to maintain their streak on days they miss.

## Setup Steps

### Step 1: Add the Freeze Column to Supabase

**IMPORTANT**: You must run this SQL in your Supabase SQL Editor first:

```sql
-- Add freeze column to streak_tracking table
ALTER TABLE streak_tracking 
ADD COLUMN IF NOT EXISTS is_freeze BOOLEAN DEFAULT FALSE;

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_streak_tracking_freeze ON streak_tracking(user_id, is_freeze);

-- Verify the column was added
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'streak_tracking'
ORDER BY ordinal_position;
```

**How to run:**
1. Go to your Supabase Dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New Query"
4. Paste the SQL above
5. Click "Run" or press Ctrl+Enter

### Step 2: Restart the Flask App

After adding the column, restart your app:

```bash
# Stop the current app
lsof -ti:5002 | xargs kill -9

# Start it again
python3 pwa_app.py
```

## Features

### For Users

1. **Streak Tracking**: Users build streaks by sending messages daily
2. **Weekly Calendar**: Shows Monday-Sunday with visual indicators:
   - ✓ Green: Active day (message sent)
   - ❄️ Blue: Frozen day (streak preserved)
   - Grey: Inactive day
   - Blue border: Today

3. **Freeze Usage**: 
   - 1 freeze available per week (Monday-Sunday)
   - Click on any grey (inactive) day to freeze it
   - Cannot freeze:
     - Days with existing activity
     - Future dates
     - If already used this week's freeze

4. **Freeze Status**: Bottom of modal shows remaining freezes

### How It Works

1. **Streak Calculation**: Counts consecutive days with activity (including frozen days)
2. **Weekly Reset**: Freeze allowance resets every Monday
3. **Smart Validation**: Prevents misuse (can't freeze active days, future dates, etc.)

## API Endpoints

1. `GET /api/streak/<user_id>` - Get streak data
2. `POST /api/streak/freeze` - Freeze a specific date
3. `GET /api/streak/freeze-status/<user_id>` - Get freeze usage info

## Database Schema

The `streak_tracking` table now includes:
- `id`: Primary key
- `user_id`: User identifier
- `access_code`: Access code
- `activity_date`: Date of activity/freeze
- `message_count`: Number of messages (0 for frozen days)
- `is_freeze`: Boolean indicating if this is a freeze day
- `timestamp`: When the record was created

## Testing

To test the feature with simulated data, you can use `test_streak_data.sql`:

```sql
-- Clean up test data
DELETE FROM streak_tracking WHERE user_id = 'YOUR_USER_ID';

-- Add test streak data (replace YOUR_USER_ID and YOUR_ACCESS_CODE)
INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, is_freeze)
VALUES 
  ('YOUR_USER_ID', 'YOUR_ACCESS_CODE', '2025-10-27', 5, FALSE),  -- Monday
  ('YOUR_USER_ID', 'YOUR_ACCESS_CODE', '2025-10-28', 3, FALSE),  -- Tuesday
  ('YOUR_USER_ID', 'YOUR_ACCESS_CODE', '2025-10-29', 2, FALSE),  -- Wednesday
  ('YOUR_USER_ID', 'YOUR_ACCESS_CODE', '2025-10-30', 0, TRUE)    -- Thursday (frozen)
ON CONFLICT (user_id, activity_date) DO UPDATE SET
  message_count = EXCLUDED.message_count,
  is_freeze = EXCLUDED.is_freeze;
```

## Troubleshooting

### "0 day streak" showing even with data

**Cause**: The `is_freeze` column hasn't been added to the database yet.

**Solution**: Run Step 1 above to add the column.

### Freeze not working

1. Check if you've already used your freeze this week
2. Make sure you're clicking on an inactive (grey) day
3. Can't freeze days with existing activity or future dates

### App won't start

**Error**: `TypeError: Can't instantiate abstract class PostgreSQLDatabase`

**Cause**: The database code was updated but the app needs to be restarted.

**Solution**: 
```bash
# Stop all instances
lsof -ti:5002 | xargs kill -9
# Start fresh
python3 pwa_app.py
```

## UI Design

- **Compact Header Button**: Top-left corner, shows flame emoji 🔥 and current streak count
- **Full Modal**: Clicked to open, shows:
  - Large streak count with flame
  - Motivational message
  - Weekly calendar (Monday-Sunday)
  - Freeze status indicator
- **Frozen Days**: Display with ❄️ emoji and blue glow
- **Clickable Inactive Days**: Hover shows "Click to freeze this day"

## Notes

- Streaks include both active days (messages sent) and frozen days
- Freeze allowance is per calendar week (Monday-Sunday), not rolling 7 days
- Each freeze counts as a day in the streak but shows differently in the UI
- The freeze feature encourages consistency while being forgiving of occasional misses

