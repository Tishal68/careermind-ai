# Job research and resume evidence

## User flow

1. Enter any job title, location (or Worldwide), experience level (or Any), and
   whether only remote openings should be considered. Upload a text PDF or DOCX.
2. Optionally enter a company name and its exact job URL or full job description.
   A company name alone cannot establish requirements; the result asks for the vacancy.
3. Start research. The browser polls a saved task and can reconnect after reload.
4. Read best-fit openings, recurring requirements, and the separate company match.
5. Use the career coach for evidence-based resume edits, projects and study plans.
   Research is a dated snapshot. Refresh from the dashboard to look for new openings.

## Data and scoring

- Two bounded searches (general and employer ATS) use role, region and seniority.
  Resume text, contact details and company descriptions are never search queries.
- Read up to five unique market pages plus one company description. Search snippets
  alone cannot produce a match. Prefer ATS pages; reject articles and vacancy lists.
- Ollama extracts up to 12 requirements per posting. Every accepted requirement has
  a quote present in its source. Positive resume evidence must quote the resume.
  These checks prevent fabricated quotations, but semantic interpretation is still
  model-dependent; users should review the visible quotes.
- Required requirements have weight 2; preferred requirements weight 1. Explicit
  evidence earns full credit, partial evidence half, and no evidence zero. Scores
  cover extracted requirements, not all possible hiring factors or hiring probability.
- Compare only postings the model identifies as matching role, region and seniority.
  Unknown or mismatched preferences are excluded from ranking and frequency counts.
  Closed postings with source evidence are excluded. Availability of remaining jobs
  is not independently verified; users must check before applying.
- Deduplicate URLs, identical page text and company/title/location combinations.
  Each requirement counts once per job. At least three comparable jobs are required
  for the typical-requirements summary; this small sample is not a market statistic.
- Company requirements remain separate from market counts. Improvement priorities
  follow that company when supplied, otherwise requirements recurring in the sample.
  Experience/eligibility gaps prompt verification instead of misleading course advice.
- Long inputs are bounded: 14,000 resume characters, 10,000 per fetched page and
  16,000 for pasted descriptions. Truncation is disclosed. Uploads still support
  up to 5 MB, but scanned PDFs need OCR outside this app.
- Public sources are cached for up to 24 hours, with a 128-query cap. Pasted company
  descriptions and resumes are not cached. Refresh bypasses public-source caching.
  Completed tasks discard their copy of the pasted description; reports retain
  quoted evidence. Paste the description again to analyze it with new preferences.

## API

`POST /api/v1/analysis/research` returns HTTP 202 with an `id` and `status`.
Request fields: `resume_id`, `job_role`, `location`, `experience_level`, optional
`remote`, `company`, `job_url`, `job_description`, `search_market` (default true),
and `refresh` (default false). Job URLs must be public HTTPS URLs.

`GET /api/v1/analysis/research/{id}` returns pending/running/completed/failed,
an error if failed, and the saved report if complete. Failed research does not
create a fabricated or empty report. Existing reports remain readable.

`analysis_data.research` contains sources and quotes, preferences, ranked openings,
company match, frequency counts, sample size, timestamps, limitations and methodology.
The career coach uses the latest report and its associated resume.

## Operations and checks

Ollama Cloud generation, search and page fetch use the existing `OLLAMA_API_KEY`.
A local model can compare a pasted description with market search disabled, without
any key. Missing keys, quota limits, unreadable sources and invalid model output
produce actionable errors. Output validation retries at most once. No autonomous
tool loop, model-written scores, applications, or scheduled background searches.

The initial worker is in-process (two concurrent tasks), with persisted status and
a ten-minute expiration. It is appropriate for the existing single-service demo.
Restarts interrupt work; scale with a durable task queue and authenticated users.
The repository's shared demo authentication and ephemeral Render storage limitations
still apply; see RENDER_SETUP.md before accepting personal resumes publicly.

Run from backend: `py -m pytest tests/test_career_flow.py tests/test_provider_compatibility.py tests/test_job_research.py -q`.
Run from frontend: `npm run build`.
Tests cover source deduplication, cache refresh, quote validation, weighted coverage,
small samples, unrelated/closed jobs, Cloud JSON compatibility, bounded retries,
saved jobs, report ownership, coaching context and provider failures.
Live Cloud verification additionally requires a valid key and account quota.
