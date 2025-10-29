-- Add Streak Freeze Feature to Supabase
-- Run this in your Supabase SQL Editor

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
