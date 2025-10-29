-- Test Streak Data for Therabot
-- This script creates fake streak data to test the streak visualization
-- Run this in your Supabase SQL Editor

-- Clear existing streak data for ADMIN001 (optional - comment out if you want to keep real data)
DELETE FROM streak_tracking WHERE user_id = 'ADMIN001';

-- Insert streak data for the past 7 days (Monday to Sunday of current week)
-- Adjust dates as needed for your testing

-- Monday (2025-10-27)
INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, timestamp)
VALUES ('ADMIN001', 'ADMIN001', '2025-10-27', 3, '2025-10-27 10:30:00+00');

-- Tuesday (2025-10-28)
INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, timestamp)
VALUES ('ADMIN001', 'ADMIN001', '2025-10-28', 5, '2025-10-28 14:20:00+00');

-- Wednesday (2025-10-29) - Today
INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, timestamp)
VALUES ('ADMIN001', 'ADMIN001', '2025-10-29', 2, '2025-10-29 09:15:00+00')
ON CONFLICT (user_id, activity_date) DO UPDATE SET message_count = streak_tracking.message_count + 1;

-- Thursday (2025-10-30) - Future date for testing
INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, timestamp)
VALUES ('ADMIN001', 'ADMIN001', '2025-10-30', 4, '2025-10-30 11:45:00+00');

-- Friday (2025-10-31) - Future date for testing
INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, timestamp)
VALUES ('ADMIN001', 'ADMIN001', '2025-10-31', 1, '2025-10-31 16:00:00+00');

-- Verify the data was inserted
SELECT * FROM streak_tracking WHERE user_id = 'ADMIN001' ORDER BY activity_date;

-- Expected Result:
-- This should give you a 5-day streak (Mon, Tue, Wed, Thu, Fri)
-- with 2 days gap (Sat, Sun) showing inactive

