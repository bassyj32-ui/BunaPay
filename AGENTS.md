# BunaPay Agent Coding Rules

1. NEVER attempt to view, interpret, or describe images, screenshots, or photos.
   Treat all image files as opaque data — validate type/size only, never content.

2. Verify behavior with text/structured evidence only:
   - Telegram Bot API getUpdates / sendMessage responses & bot logs
   - Supabase queries (status changes, timestamps, row counts)
   - API responses and HTTP status codes
   - Read real values — never fabricate or assume test results

3. When UI verification is needed, use accessibility snapshots (browser
   take_snapshot), console messages, or network logs — not screenshots.

4. If something cannot be verified programmatically, ask you (the user) to confirm.

5. Secrets live only in .env / Supabase secrets — never in code or commits.

6. Make the smallest change that works. No speculative features.

7. Confirm facts against the actual codebase/database before claiming success.
