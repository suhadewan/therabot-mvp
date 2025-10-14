-- Remove unused tables from Supabase database
-- These tables were created but are never used by the application

-- chat_sessions: Created but no INSERT/UPDATE/SELECT operations exist
DROP TABLE IF EXISTS chat_sessions;

-- user_accounts: Legacy table from old multi-login design
-- New simplified design: access_code = user_id (no separate user_accounts needed)
DROP TABLE IF EXISTS user_accounts;
