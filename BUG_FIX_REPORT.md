# CareerMind AI bug fixes — 13 October 2026

Scope: source review of the main branch, backend regression suite, production build, dependency audit, and local browser checks. This is a verified repair pass, not a claim that every possible defect has been eliminated. No production deployment or live provider inference was performed.

## Critical technical bugs — fixed

1. **Authentication bypass:** missing, invalid, expired, and malformed tokens fell back to a shared demo/first account. Protected routes now return 401 and require an active account.
2. **Administrator authorization bypass:** every user passed the administrator dependency, including destructive user-management routes. Ordinary users now receive 403.
3. **Public administrator credentials:** startup seeded a known administrator password and the login page advertised it. Seeding and shortcut buttons were removed. Existing seeded demo/admin accounts still using those public passwords are disabled on startup; accounts with independently changed passwords are preserved.
4. **Public JWT signing secret:** the fallback was a published constant, allowing forged tokens. Development now uses a random process-local key; known placeholder/old keys and short keys are rejected. Production must configure one stable private SECRET_KEY.
5. **Vulnerable production framework dependency:** upgraded Next.js to 16.4.0 and compatible React, animation, icon, and type packages. Production dependency audit now reports zero known vulnerabilities. Migration guidance: https://nextjs.org/docs/app/guides/upgrading/version-16

## Medium UI and technical bugs — fixed

6. **Login and logout did not work consistently:** token was never stored; UI started as a fabricated superuser; logout restored that user. Authentication now persists the real token, restores the account, clears login/research state on logout, and guards dashboard rendering.
7. **No sign-out control:** added a dashboard sign-out button and wrapped navigation for narrow screens.
8. **My resumes did not list saved resumes:** added loading/error states, saved resume selection, preview, deletion, and a role-comparison link.
9. **Invalid upload reused the previous file:** invalid/empty/oversized selection now clears the queued file. Uploads share authenticated API error handling and proper multipart headers.
10. **Long passwords silently truncated at 72 bytes:** new hashes use SHA-256 before bcrypt; distinct suffixes remain significant. Existing ordinary bcrypt passwords still authenticate. Existing legacy passwords over 72 bytes require a reset rather than accepting ambiguous truncation.
11. **Inactive accounts could log in:** login and token validation now reject inactive accounts.
12. **Missing admin toggle endpoint:** implemented the UI's requested route, enforcing admin authorization and preventing self-demotion.
13. **Settings accepted invalid types:** validated lengths/types and preserved unspecified settings; malformed input now produces 422 rather than database errors.
14. **Duplicate registration race:** integrity conflicts roll back and return a controlled duplicate-account response.
15. **CORS ignored its configured allowlist:** middleware now uses BACKEND_CORS_ORIGINS rather than all origins with credentials.
16. **Old static UI could shadow current frontend:** backend static hosting is now explicit via STATIC_FRONTEND_DIR, rather than automatically using the obsolete checked-in export. Static file paths are constrained to that directory.
17. **Research rows could obstruct parent deletion:** ORM cascades now remove research jobs with their user/report. This change was checked by the backend suite; concurrent research/deletion was not stress-tested.
18. **Career context fabricated positive fallback scores:** removed hard-coded 75–92 score fallbacks, preserved legitimate zero scores, and cleared stale report context when no report exists.
19. **Session deletion errors appeared successful:** deletion failures now propagate instead of clearing client state as though deletion succeeded.

## Normal/minor UI and technical bugs — fixed

20. **Unassociated input labels and errors:** shared inputs have stable IDs, associated labels, invalid state, and error descriptions; registration exposes its minimum password length.
21. **Keyboard-inaccessible upload selection and long filenames:** visually hidden file control remains focusable, its label shows keyboard focus, and filenames wrap.
22. **Navigation did not announce the current page:** added aria-current.
23. **Invalid CSS custom-property name:** corrected a malformed declaration that the new production compiler rejected.
24. **Health response had the wrong project name:** aligned it with CareerMind AI and its existing health test.
25. **Obsolete validation command:** replaced the removed Next.js lint command with an explicit TypeScript typecheck script. This is type checking, not an ESLint ruleset.
26. **Empty API responses:** explicitly handle HTTP 204 and redirect expired authenticated requests to login.

## Remaining findings and limitations

- **Development dependencies: 5 high and 2 moderate advisory findings remain** in Tailwind 3's build-tool dependency tree (braces/chokidar/micromatch/fast-glob and selector parsing). These are not production-runtime dependencies; the full audit still fails. The audit proposes a breaking Tailwind 4 migration, and braces was reported without a patched version. A separate styling migration and visual regression pass is required; these findings are not claimed fixed.
- Live Ollama/Cloud research and inference were not validated. Existing automated tests cover provider failure handling and evidence/ownership behavior using mocks.
- Render's existing SQLite configuration is ephemeral: redeployments can lose account/resume data. No paid storage or deployment resources were changed.
- Legacy secondary pages were build-checked, but not exhaustively exercised in a browser. No claim of a complete security audit or penetration test.

## Validation

- Backend: 63 tests passed, including 10 new security regression cases.
- Frontend: Next.js production build passed, including TypeScript checks and all 16 generated routes.
- Production dependency audit: 0 known vulnerabilities.
- Browser: registration, protected-route redirect, token persistence after reload, logout, invalid resume validation, valid DOCX upload, saved resume persistence and deletion, coach navigation; no browser exceptions.
- Responsive checks: no document-width overflow at 320, 390, 768, or 1440 pixels on the main role-match page.
- Static hosting boundary, CORS configuration, and some minor UI changes were source-reviewed; they do not each have a dedicated browser test.

## Deployment and account recovery

1. Back up the database/uploads and set a new private SECRET_KEY of at least 32 characters before deployment. Use the same key across workers. Rotating it invalidates old sessions. Without a configured key, local development sessions expire on process restart.
2. Register a personal account. Use a trusted database administration session to grant administrator status only to the intended account. Public demo/admin accounts retaining their original passwords are intentionally disabled; do not re-enable them with those passwords.
3. Build and run the Next.js frontend with the API backend. Do not serve the old frontend/out export. Set STATIC_FRONTEND_DIR only if deliberately deploying a freshly built compatible static frontend.
4. Configure persistent storage before retaining real resume data. Verify live provider credentials/inference in the target environment.
