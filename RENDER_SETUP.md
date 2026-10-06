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
3. Open the site, upload a test resume, and select a job role.
4. Run the analysis, then ask the Career coach what to learn first.
5. An authentication error means the key needs checking. A model-not-found
   error means the cloud model name or base URL needs checking. A usage-limit
   error means the cloud account's limit has been reached.

The local automated tests mock cloud responses and verify the request headers,
payload, and error handling. A successful live cloud deployment still requires
a valid key, model access, and available account quota.

## Demo storage and access

The current app retains its standalone shared demo workspace. It is not isolated
multi-user resume storage. SQLite and uploaded files on Render's ordinary
filesystem are temporary; configure persistent storage and enforced user
authentication before using this as a public service for personal resumes.
