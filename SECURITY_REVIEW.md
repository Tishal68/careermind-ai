# CareerMind AI — deeper security review and repairs

Date: 13 October 2026. Scope: repository/API review, regression tests, dependency audits, local browser checks, and deployment configuration validation. Changes extend PR #1. This is not a claim that all possible security defects have been eliminated.

## Critical and high findings repaired

- **Another published signing key in Docker Compose:** removed the fixed signing key/database password, require private environment values, reject both historical signing keys, and require an explicit stable signing key in production.
- **Vulnerable development dependencies:** migrated Tailwind to version 4 and its PostCSS integration, removing the vulnerable Tailwind 3 tree. Full npm audit now reports zero known vulnerabilities. Migration reference: https://tailwindcss.com/docs/upgrade-guide
- **Unbounded document parsing:** DOCX preflight rejects excessive archive expansion, member count, encryption, and compression ratios. PDF/DOCX parsing runs in a child process with a 20-second deadline; Linux additionally has CPU/address-space limits. Limit: 30 PDF pages and 100,000 extracted characters. Synchronous processing no longer blocks the async event loop.
- **Request resource exhaustion and password guessing:** request bodies are capped before multipart parsing (6 MiB upload envelope, 64 KiB other writes) with a 20-second receive deadline. Authentication attempts are limited; costly upload/chat/interview operations have per-account limits, two process-wide slots, and a same-account concurrency guard. Accounts can retain at most 20 resumes.
- **Private file retention and unsafe deletion paths:** admin deletion removes private upload files; resume deletion resolves and confines paths to user storage and reports cleanup failures. Research-active deletion returns a conflict. Foreign-key enforcement and profile/research cascades improve relational cleanup.
- **Credential disclosure to custom model endpoints:** the global Ollama Cloud key is only attached to the Ollama Cloud hostname. Explicit custom-provider keys remain possible. Upstream exceptions are logged by type rather than potentially sensitive response text.
- **Container secrets and privileges:** separate build contexts exclude local databases, uploads, and environment files. Containers run as unprivileged users, runtime images omit frontend development dependencies, and the unified backend listens only on loopback. Forwarded headers are disabled in container backend commands so forged forwarding headers cannot bypass peer-based limits.

## Medium findings repaired

- Logout now records token revocation server-side; replay of that token returns 401. Tokens have unique identifiers and a default one-hour lifetime. A new login token is independent of a previous revoked token.
- New passwords require 12–1024 characters. Existing shorter account passwords remain usable for migration. Other user-controlled schema fields have explicit length/type limits.
- Interview failures no longer create fictional questions/scores in the API or UI. Provider output is schema-validated, including finite 0–100 scores. Evaluations are tied to the authenticated owner's active question, persisted, and stale-question replay is rejected.
- New-account dashboard progress no longer invents completed projects, interview scores, or learning progress.
- Public URL validation rejects trailing-dot private hosts, legacy numeric IP forms, encoded host tricks, backslashes and control characters. The application delegates job fetching to Ollama rather than connecting to arbitrary destinations locally.
- API responses use no-store. Frontend security headers restrict framing, MIME sniffing, referrers, permissions and resource origins. Optional static hosting validates each resolved candidate, including suffix/index candidates, and returns a real 404 for missing files.
- Added the missing PostgreSQL driver and normalized PostgreSQL URLs. Compose waits for PostgreSQL health, keeps database ports private, supplies a frontend service, and stores uploads in a volume. Standalone frontend builds now retain the proxy config and use the intended backend address.
- Render configuration now describes a one-instance Starter service with a 1 GB persistent disk for SQLite/uploads. It validates against Render's published schema. This is a proposed paid configuration only; it has not been applied. Existing data needs migration before changing its storage path.
- Added CI definitions for backend tests, frontend builds and both dependency audits. Python runtime dependencies are directly pinned; unused heavyweight libraries were removed. Transitive Python dependencies are still resolved by pip and checked by audit.

## Validation

- 86 backend tests passed, including 23 additional hostile-input/security cases in this pass. The targeted 23-test security file passed again after final middleware/static-route edits.
- Next.js production build and TypeScript checks passed for all 16 routes.
- npm audit including development dependencies: zero known vulnerabilities.
- pip-audit of the installed Python validation environment: zero known vulnerabilities after updating pip; includes the newly installed PostgreSQL driver.
- Render Blueprint validated against https://render.com/schema/render.yaml.json; Compose and CI YAML parsed successfully.
- Browser checks cover registration, protected-route redirects, login persistence, responsive widths 320/390/768/1440, PDF/DOCX selection validation, valid DOCX upload, saved resume reload/delete, coach navigation and logout. Final browser outcome is recorded in the chat.

## Remaining boundaries and operational requirements

- No Docker executable was available here. Container builds, Linux parser limits, PostgreSQL runtime behavior and actual Render deployment have not been verified locally. CI is added to validate Linux builds/tests when it runs.
- Do not apply the new paid Render plan/disk or move an existing database without backing up and migrating it. No paid service was provisioned and no production deployment was performed.
- Request limits, processing slots and the research worker are process-local. Use a shared ingress limiter and durable job queue before deploying multiple workers/instances. Through the Next.js proxy, peer-based authentication limits are shared; tune ingress limits for real traffic.
- JWTs remain in browser localStorage. The CSP retains inline scripts for the current statically rendered Next.js app; it is not a strict nonce-based XSS defense. A future session-cookie migration requires CSRF protection. React escapes displayed text, and this review found no active raw-HTML rendering sink.
- Logout during a network outage clears the browser but cannot guarantee server revocation until connectivity returns; the token expires within its configured lifetime.
- Cloud fetching still relies on the provider's DNS/redirect protections. AI quote checks constrain evidence but cannot guarantee model semantic accuracy or immunity to prompt injection. Live Ollama/Cloud inference was not tested.
- Rate limits and the per-account resume cap reduce abuse; they do not replace global storage quotas, monitoring, backups, malware scanning, or an external penetration test.

## Safe rollout

1. Back up the existing database and uploaded files. Configure a private SECRET_KEY and production environment. Do not reuse historical repository values.
2. Register a personal account and provision its administrator role locally with `python -m app.manage_admin registered-email@example.com`.
3. For Compose, supply a private URL-safe POSTGRES_PASSWORD and SECRET_KEY. Existing PostgreSQL volumes retain their old password; rotate that database credential explicitly rather than assuming a new environment value changes it.
4. Before applying Render's proposed disk, migrate the existing SQLite database and uploads to /app/data and ensure the application user can write there. Starter/disk services incur charges when applied.
5. Run CI and target-environment smoke tests, then verify provider configuration and backups before releasing to users.
