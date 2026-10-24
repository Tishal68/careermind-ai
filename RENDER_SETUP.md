# Render with Ollama Cloud

Use the repository's root `Dockerfile` to run Next.js and FastAPI together.
The Render Blueprint now selects `runtime: docker`; a Python-only start command
does not start the Next.js website. For an existing service, verify its runtime
is Docker and it uses `./Dockerfile` before redeploying. If using Blueprints, sync
the updated Blueprint. See https://render.com/docs/docker.

## Environment variables

In Render's service Environment page, configure:

```dotenv
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=gemma4:31b
OLLAMA_API_KEY=<your-Ollama-Cloud-key>
AI_FALLBACK_ENABLED=false
SECRET_KEY=<keep-your-existing-generated-secret>
```

Create the cloud key at https://ollama.com/settings/keys and enter it only in
Render's backend environment. Do not put it in source code or a `NEXT_PUBLIC_`
variable. The backend sends it as an Authorization Bearer header.

`OLLAMA_BASE_URL` is the base origin without `/api` or `/api/chat`; the client
appends `/api/chat`. `gemma4:31b` is a cloud model listed by Ollama's API. You can
choose another model returned by https://ollama.com/api/tags. Local `llama3.2`
is not the model setting for this cloud configuration. Cloud requests send resume
context to Ollama Cloud. See https://docs.ollama.com/cloud and
https://docs.ollama.com/api/authentication.

Keep `NEXT_PUBLIC_API_URL` and `BACKEND_URL` unset for this unified Docker setup.
The website uses its same-origin `/api/v1` proxy to the internal FastAPI server.
Render supplies `PORT`; there is no need to add it manually. Gemini is not
required for resume matching or Ollama coaching.

## Verify after deployment

1. Redeploy the latest commit after saving the environment variables.
2. Open `/api/v1/health` on the service URL and check for `healthy`.
3. Open the site, upload a test resume, and enter a role, location and experience level.
4. Click **Research my role match**. Check the sourced openings and requirement
   evidence, then ask the Career coach what to learn first. Try a company job URL
   or pasted description as well.
5. An authentication error means the key needs checking. A model-not-found
   error means the cloud model name or base URL needs checking. A usage-limit
   error means the cloud account's limit has been reached.

The local automated tests mock cloud responses and verify the request headers,
payload, and error handling. A successful live cloud deployment still requires
a valid key, model access, and available account quota.

## Live job research

No additional API key is required: `OLLAMA_API_KEY` also authenticates Ollama's
`https://ollama.com/api/web_search` and `/api/web_fetch` services. Research always
uses Ollama for extraction; `DEFAULT_AI_PROVIDER` controls the existing coach router.
The model must reliably follow JSON instructions. Cloud does not support Ollama's
`format` schema parameter, so the app validates outputs and retries once.
See https://docs.ollama.com/capabilities/web-search and
https://docs.ollama.com/capabilities/structured-outputs.

The app creates a `research_jobs` table on startup through the existing SQLAlchemy
initialization. Reports and task status use the configured database. The lightweight
background worker supports two concurrent research tasks per process; each user can
have one active task. Status polling avoids holding a browser request open during
inference. Interrupted tasks become retryable after ten minutes; they are not resumed
automatically after a restart. Use a durable external queue before scaling workers.
Public source text is cached in memory for up to 24 hours (maximum 128 searches),
without resumes or pasted descriptions. **Refresh research** bypasses that cache.

## Health check and readiness configuration

Configure the Render service HTTP readiness health check:
- In the Render Dashboard under **Settings > Health Check Path**, enter: `/api/v1/ready`
- Or via the repository Blueprint `render.yaml` which specifies `healthCheckPath: /api/v1/ready`

This ensures Render routes inbound traffic only after FastAPI has started, database schema migrations have executed, and the internal proxy is responsive.

## Storage durability risks on Render Free Tier

The active deployment runs on the Render Free web tier. The implications are:
1. **Ephemeral storage**: The SQLite database (`/app/data/careermind.db`) and uploaded resumes (`/app/data/uploads/resumes`) reside entirely on the container filesystem. When Render restarts, spins down after inactivity, or redeploys the container, this local data is reset.
2. **Cold starts**: Free instances spin down after 15 minutes of inactivity and require 30–60 seconds to spin up on subsequent requests.
3. **No persistent disk**: Persistent disks cannot be attached to free services on Render.

## Compatible durable storage roadmap (Paid production paths)

Before onboarding production users with valuable personal data, select an authorized durable storage path:

- **Path A: Single-Instance with Persistent Disk (Lowest Cost)**
  - Upgrade web service to Render **Starter** plan ($7/mo).
  - Attach a **1 GB Persistent Disk** ($0.25/mo) mounted at `/app/data`.
  - Retains the existing SQLite database and filesystem storage without application changes.
  - *Limitation*: Single instance only; rolling zero-downtime deploys are disabled when a disk is mounted.

- **Path B: Scalable Multi-Instance Architecture (Recommended for Production)**
  - **Database**: Managed PostgreSQL (Render PostgreSQL, Neon, AWS RDS, or Supabase). Set `DATABASE_URL=postgresql+psycopg://user:pass@host/dbname`. Schema migrations run automatically via Alembic on startup.
  - **Object Storage**: S3-compatible cloud storage (AWS S3, Cloudflare R2, or Google Cloud Storage) for resume file persistence.
  - **Scaling**: Completely stateless web containers allow horizontal scaling across multiple instances with zero-downtime deployments.

Do not apply paid Blueprints or provision paid database/disk resources without explicit approval.

