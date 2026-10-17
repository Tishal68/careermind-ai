# Part 3: Open professional roles

Research already accepted arbitrary titles. Settings and interview practice still exposed technology-only dropdowns; they now use a shared free-text input with optional cross-industry examples. Custom titles do not need to appear in a catalogue. Titles are trimmed and limited to 2-100 characters.

Saved settings update the active account immediately. A delayed settings response cannot replace a title being edited. Research and interview initialize from the account preference; a restored report retains its own role.

The legacy curated keyword engine no longer substitutes Python, Git, SQL and Docker for unknown professions. Its old endpoints direct those callers to resume upload plus /analysis/research. Known legacy technology profiles remain for compatibility; they are not universal role coverage. The active research UI uses the evidence-based endpoint.

Interview prompts treat technical questions as knowledge of the selected profession. Resume previews identify their limited technical-keyword vocabulary and explain unstructured education/experience rather than implying these are absent.

## Boundaries

Accepting any title does not establish model expertise in every profession. Research requires a supplied job description or retrieved sources. Source/resume quotations are validated; unavailable market evidence is reported honestly. Professional licensing, eligibility and jurisdictional rules require verification. The model was not retrained, and no exhaustive occupation taxonomy was added.

## Validation

114 backend tests passed, then the additional nursing evidence test passed with the 10 new role tests (115 total). All 12 browser cases passed across the full run and targeted rerun after correcting a test navigation selector. Six session tests and the production build passed. Nursing evidence extraction is mocked in the regression test; live provider coverage is a separate check.
