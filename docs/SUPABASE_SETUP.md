# Supabase PostgreSQL for CareerMind

The existing FastAPI login system stays in use. Supabase supplies PostgreSQL;
Supabase Auth and a public Supabase API key are not required.

## Connect the existing Render service

1. Create a free Supabase project and set its database password privately.
2. In **Connect**, select **Session pooler**, port **5432**. Use the exact host
   and username provided by Supabase. Do not use the HTTPS project API URL.
3. In Render's service environment settings, set `DATABASE_URL` to the pooler
   connection URI. Replace the password placeholder and percent-encode reserved
   characters in the password. Add `?sslmode=require` (or `&sslmode=require` when
   the URI already has query parameters).
4. Keep `SECRET_KEY` stable. Remove an explicit `DEMO_MODE=true` override, or set
   `DEMO_MODE=false`. Do not put the database URI in any `NEXT_PUBLIC_` variable,
   repository, screenshot, or chat.
5. Deploy the commit containing migration `0005_resume_files`. Startup creates
   or upgrades the app tables; `/api/v1/ready` returns 200 only at the current
   migration version. Never point this service at an unrelated application's DB.

Use the owner connection supplied by Supabase: migrations and the backend need
table-owner permissions. The app enables row-level security on its managed tables
without public client policies, blocking anon/authenticated Data API reads.
Keep the owner URI server-only. Do not expose these tables with permissive policies.
Session pooling supports the migrations' advisory lock and normal sessions.
The application uses a small connection pool, reconnect checks, and TLS for Supabase.

The `render.yaml` keeps Render on the free plan and requires a privately supplied
`DATABASE_URL` (`sync: false`). It no longer supplies a SQLite production default.
For an existing service, retain its working database URI and `SECRET_KEY`.

## Resume persistence and limits

New uploads store their original bytes and extracted text in the same database
transaction. Local files are used only for bounded document extraction, then
removed. Lists and AI context queries defer the original binary column. Users can
download their own originals from **My resumes**; deleting a resume or account
also deletes its stored bytes.

This intentionally simple college-project design uses database storage for files:
5 MB per upload and 20 resumes per account. Supabase's free 500 MB database quota
is shared by all users and reports; it is not 500 MB per account. Watch project
usage and move files to object storage before scaling beyond a small demo.

Switching from Render SQLite to a new Supabase project starts an empty database.
The approved disposable test accounts are not automatically transferred. Existing
versioned databases upgrade without deleting records; older rows without original
bytes retain their parsed text but need re-upload for original-file downloads.
Do not use this cutover procedure for valuable data without a separate migration.

## Verify and maintain

After deployment, create a disposable account, upload a PDF/DOCX, download it and
compare its bytes, then redeploy and confirm the same account and resume survive.
Check that `/api/v1/deployment-info` reports `disposable_demo: false`.
Check RLS is enabled on app tables in Supabase. Back up PostgreSQL independently;
the database holds resumes as well as accounts/reports. Free projects may pause
after inactivity; Render cold starts and AI provider limits still apply.

References:
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/pricing
