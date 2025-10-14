-- Add access_code column to flagged_chats table
-- Run this in your Supabase SQL editor before deploying

-- Add the column if it doesn't exist
ALTER TABLE flagged_chats
ADD COLUMN IF NOT EXISTS access_code TEXT;

-- Optional: Backfill access_code from user_id if they're the same
-- UPDATE flagged_chats SET access_code = user_id WHERE access_code IS NULL;
