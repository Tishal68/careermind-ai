# Reliability repair report — 2026-10-15

## Scope and severity

No confirmed critical vulnerability was established by this bounded review. Findings below distinguish repaired defects from open operational risks. This is not a certification that the application is vulnerability-free.

## High priority

- **Fixed: shared small authentication bucket.** The unified proxy made all public clients appear as loopback. A single account could consume the 30-attempt budget for everybody. Loopback now uses independent hashed account budgets plus a 300/minute global capacity guard; verified direct clients also receive a client budget. Forwarded addresses are ignored unless the socket and chain match explicit TRUSTED_PROXY_CIDRS. Tests cover forged leading addresses and independent trusted clients. The production Render chain has not been established, so no speculative trust networks were enabled. Global capacity protection can intentionally reject all requests under sustained abuse; external ingress protection is still advisable.
- **Open: data durability.** Render confirms free service, no attached persistent disk. The owner confirmed only disposable test data exists and authorized continuation on that basis. Restarts/redeploys may erase accounts, uploads, reports and job state. STORAGE_MIGRATION.md supplies a costed proposal, backup/restore procedure and rollback checks. No paid resources were provisioned.
- **Fixed: duplicate/unbounded research admission.** A database admission transaction, per-account active slot, idempotency key, 12/hour account budget and 100-active-job queue bound replace read-then-insert behavior. PostgreSQL admission uses a transaction advisory lock; SQLite serializes writes. Tests exercise simultaneous repeated requests and input/key conflicts. The PostgreSQL branch still needs an actual PostgreSQL integration run.

## Medium priority

- **Fixed within the supported single-instance deployment: research recovery and saturation.** A database-backed dispatcher claims work with leases, heartbeat and fenced completion. Busy workers leave tasks queued. A crashed lease is retried once; results expire after ten minutes and stale-worker commits are rejected. Execution metadata expires after 30 days; reports are preserved. This is not an exactly-once guarantee for upstream AI calls, and database loss defeats recovery. Long upstream calls can continue until their configured provider timeout even after the job result expires.
- **Fixed: misleading model settings.** Settings expose the actual configured research model, coach provider/model and fallback flag. Attempts to save unsupported preferences return an actionable error.
- **Fixed: unsupported scores.** Hardcoded skill match and minimum resume-quality scores were removed. ATS, resume-quality and readiness metrics serialize as null, including old placeholder values. Reports show evidence/keyword coverage and do not invent a default score or executive-summary claim.
- **Fixed: unbounded history responses.** Lightweight cursor-paginated report summaries, owned report-detail lookup, bounded legacy report lists and cursor-paginated coach messages reduce payloads. Dashboard only requests the latest report. The API keeps historical reports; quota-based report retention/deletion can be a subsequent policy decision.
- **Fixed: cross-tab authentication state.** Login/logout changes in another tab trigger session revalidation; in-flight session checks are invalidated on logout. Existing reconnect behavior remains.
- **Fixed endpoint; deployment wiring open:** /health is liveness; /ready checks database/schema access with bounded connection/pool/query waits. Blueprint points at readiness. The existing manually configured Render service's healthCheckPath was empty when inspected; changing the Blueprint file does not automatically update that service setting.
- **Open hardening:** Bearer tokens remain in localStorage and production CSP permits inline scripts. No XSS exploit was established. A cookie-based session migration needs HttpOnly/Secure/SameSite settings, login CSRF and Origin checks, compatibility for bearer API clients, token rotation/revocation tests, and a nonce/hash CSP compatible with Next.js rendering. This should be an independently tested change, not an unverified switch during the queue repair.

## Validation evidence

- Concurrent same-key requests produce one database job; another active request is rejected.
- Restart recovery of an expired lease produces one report; a repeated worker call does not create a duplicate.
- Saturation leaves jobs pending; hourly quota enforced; ownership protects report details.
- Backup/restore round-trip, integrity check, manifest verification, unsafe-path rejection and no-overwrite behavior tested. Writes must be quiesced for database/upload consistency. Backups contain personal data and must be protected.
- Frontend production build and TypeScript passed. Browser tests used controlled API responses for report loading, zero match, model settings, 320/390/768/1440px overflow and cross-tab logout. Screenshots saved separately.
- CI now includes the production Docker build and real readiness, registration/login, PDF/DOCX extraction, resume deletion and revoked-token smoke test. Local Docker is unavailable; CI outcome must be recorded before deployment.

## Performance measurements

Synthetic fixture: 60 owned reports, each with 10,000 characters of evidence. For a page of 50 reports, the full endpoint response was 514,401 bytes; the summary endpoint was 5,078 bytes (99.01% smaller). These are actual serialized response lengths from local test-client requests, not an internet latency benchmark.

Pre-change live /login browser sample: 155,985 encoded JavaScript bytes over 9 resources; DOMContentLoaded 2,294.7 ms. Single cold-browser observation, dependent on network/hosting state. Do not infer a percentage speedup from one sample. Post-deployment sample and live verification will be appended when available.

## Rollout and rollback

New research slot/submission/lease tables are additive and created at startup. Existing report rows are not destructively migrated; output serialization masks unsupported historical scores. Stop writes and workers before real-data migration, verify a backup and file paths, then deploy. Application rollback must account for pending queue work and the prior BackgroundTasks implementation. Keep a verified backup before any production change once real data is admitted. See STORAGE_MIGRATION.md for cost and storage details.

## Live verification and follow-up

PR #5 CI passed: 99 backend tests, dependency audits, frontend build, and production Docker smoke checks. Render deployed merge a1a8524 on 2026-10-16. Live API checks passed registration, login, readiness, DOCX/PDF extraction, deletion and revoked logout. A first PDF check timed out during startup contention; a subsequent full check passed. Cold-start upload performance remains a limitation on the free instance.

A synthetic company-description research request completed with a report in 5.5 seconds and unsupported scores remained null. Repeating the idempotency key returned the same job. A separate market-search request terminated in 16.5 seconds with an actionable no-evidence-backed-vacancies result; successful live market discovery is not established.

Live browser testing found a medium-severity delayed-401 race after logout: pending dashboard responses could redirect a new login. Follow-up repair compares the response's original token to the current stored token before clearing/redirecting; session validation likewise ignores results for a replaced token. Three controlled request-race regression tests cover signed-out, replacement-session and genuinely expired-current-session cases.

Post-deployment login sample: 156,056 encoded JavaScript bytes, 9 resources, DOMContentLoaded 1,830.9 ms. This single observation is not proof of a latency improvement.
