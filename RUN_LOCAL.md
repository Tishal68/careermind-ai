# CareerMind AI with Ollama

The main workspace accepts any job role, a PDF or DOCX resume, location and experience
level. It compares job requirements with resume evidence and supports career coaching.
See [JOB_RESEARCH.md](JOB_RESEARCH.md) for live research and company comparisons.

For hosting with an Ollama Cloud API key, see [RENDER_SETUP.md](RENDER_SETUP.md).

## Start locally

1. Install Python 3.12, Node.js 20, and Ollama.
2. Start Ollama and install the model: `ollama pull llama3.2`.
   If Ollama is not running in the background, run `ollama serve`.
3. In a terminal at the repository root:

   ```powershell
   cd backend
   py -m pip install -r requirements.txt
   Copy-Item .env.example .env
   py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

4. In a second terminal at the repository root:

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

5. Open http://localhost:3000. Enter a role, location and experience level, then upload
   a resume. Add `OLLAMA_API_KEY` for live web research. Without a key, paste a full
   company job description and turn off **Also research current market openings**.
   Click **Research my role match**, then open **Career coach**.

The frontend proxies `/api/v1` to the backend. For a different backend port, set `BACKEND_URL` before starting or building Next.js (for example `$env:BACKEND_URL="http://127.0.0.1:8001"`). Local model replies may take a minute or longer; the proxy allows up to 210 seconds and the Ollama request up to 180 seconds. Configure `OLLAMA_BASE_URL` and
`OLLAMA_MODEL` in `backend/.env` to use another local Ollama instance or model.
The router and resume coach respect `DEFAULT_AI_PROVIDER` from commit `f4de0e0`, which defaults to `ollama`. Choosing `gemini` explicitly sends coaching prompts to Gemini instead. `AI_FALLBACK_ENABLED=false` is the default, so an Ollama outage does not silently send resume prompts to Gemini. Set it to `true` only if you want cross-provider fallback. The new role match and coach flow needs no Gemini API key. Older interview
features elsewhere in the repository still use their existing provider.

## What the result means

New reports show requirement coverage for each opening, quoted evidence, a dated
research sample, and company-specific priorities. Market frequencies require at least
three comparable postings and are not market-wide statistics. Pasted descriptions
and local inference need no web search key. Research runs in a background task; reload
the page to reconnect. A stopped server interrupts running work; retry after timeout.

### Legacy baseline reports

The older `/analysis/analyze` endpoint is retained for existing clients:

- Nine technology roles have explicit core skill lists.
- Skills overlap is `matched core skills / total core skills × 100`.
- 80% or more is labeled strong, 50–79% partial, and below 50% limited.
  These are product thresholds, not validated hiring probabilities.
- Matching uses keyword boundaries and common aliases. A mention does not prove
  proficiency, and missing text does not prove a person lacks a skill.
- The parser extracts text and recognized skills without inventing personal
  details, education, employment, or fallback skills. Scanned PDFs need OCR first.
- Learning steps address each missing skill and suggest portfolio and interview work.
- Coaching uses the most recent analysis and its associated resume, plus the
  recent conversation. Each report has a separate daily chat session.
- The model is instructed to redirect unrelated questions to career topics.
  This is an LLM instruction, not a guaranteed content filter.
- If Ollama is unavailable, the app shows an error and preserves the question
  for retry rather than inventing a reply.

## Local scope

The repository retains its existing standalone demo authentication behavior:
unauthenticated visitors share a demo workspace. Run it on localhost for personal
use. Multi-user public deployment requires replacing that fallback with enforced
authentication, removing seeded demo/admin accounts, and configuring deployment
secrets. A remote backend cannot reach Ollama on your laptop via its own localhost.

## Checks

```powershell
cd backend
py -m pytest tests/test_career_flow.py tests/test_provider_compatibility.py tests/test_job_research.py -q
cd ../frontend
npm run build
```

Regression coverage includes all role profiles, alias matching, no-match and
full-match outcomes, invalid uploads, resume ownership, role-specific chat
context, conversation history, and Ollama failure handling.
