# CareerMind AI

CareerMind compares resume evidence with job requirements and helps you plan practical next steps. It uses Next.js, FastAPI and SQLAlchemy with configured Ollama/Gemini providers.

## Main workflow

1. Create an account and upload a text-based PDF or DOCX resume (up to 5 MB).
2. Inspect the extracted text. The quick keyword preview covers a limited technical vocabulary; it is not a complete assessment of your skills.
3. Enter any professional job title, location and experience level. Supply a company job description or enable market research.
4. Review **best-fit openings** separately from **typical requirements**. Evidence coverage uses validated source and resume quotations; it is not an ATS score or hiring prediction.
5. Create a report-specific action plan, save task progress, and discuss results with the career coach.
6. Practice interviews for your chosen profession and review AI feedback before moving to the next question.

Custom job titles are accepted across research, settings and interview practice. This does not guarantee model expertise or available job sources for every profession. Professional registration and eligibility need independent verification. Provider failures and insufficient evidence are surfaced rather than replaced with invented results.

## Setup and deployment

- [Local setup](RUN_LOCAL.md)
- [Render deployment and environment settings](RENDER_SETUP.md)
- [Research behavior, evidence and limits](JOB_RESEARCH.md)

The root Dockerfile runs Next.js and FastAPI together. Configure provider credentials privately; never commit secrets. The current free Render deployment uses temporary storage: accounts, resumes and reports can be lost on redeployment. Persistent production storage remains a separate infrastructure task.

## Verification

Backend (from `backend`):

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Frontend (from `frontend`):

```sh
npm ci
npm test
npm run build
npx playwright install chromium
npm run test:ui
```

GitHub Actions also checks dependencies and runs a smoke test against the production Docker image. Automated checks do not establish that all providers, professions or real-world inputs are error-free.

`main` is the canonical branch. Completed work is merged into it before temporary
branches are removed. Generated frontend exports, browser reports, dependencies,
local databases and secrets do not belong in Git. Build the frontend from source.
The maintained API smoke test is `backend/scripts/container_smoke.py`; browser
coverage lives in `frontend/tests/browser`. Neither requires shared demo accounts.

## Code map

- `frontend/src/app`: research, reports, resume management, action plans, coach, interviews and settings.
- `frontend/src/context/AuthContext.tsx`: account/session state.
- `backend/app/api/v1`: authenticated API endpoints.
- `backend/app/services`: document parsing, evidence-based research, background research processing and action plans.
- `backend/app/models`: persisted accounts, resumes, research jobs, reports and interviews.
- `backend/app/intelligence`: older curated engines retained for compatibility. Their fixed technology profiles are not the universal role-research system.

See [Part 1](PART_1_ACTION_PLANS.md), [Part 2](PART_2_ACCOUNT_LOADING.md) and [Part 3](PART_3_OPEN_ROLES.md) for implementation boundaries and validation notes.
