# Part 5: Interview recovery and grounded coaching

## Behavior

Interview practice lists the 20 most recent owned sessions and lets users resume/review or start another. Saved answers and feedback survive page reloads while the database survives. Unsubmitted drafts are not persisted; the UI states this. Resume/reload checks ownership. Existing generated personal anecdotes are replaced in recovered guidance with a labeled template using the submitted answer.

Every new answer sends its question index. An additive interview_evaluations table has one claim per session/index, a request fingerprint, status, a ten-minute lease token and the successful response. Retries of a completed identical answer return that response without calling the provider again. Different completed answers and simultaneous evaluations conflict. Provider failures release the claim. Expired claims can be retried; token checks prevent older workers from overwriting a newer result. The claim and saved history commit atomically. No database lock is held during provider processing. The existing process-local capacity guard remains enabled.

This is not exactly-once upstream inference: a crash after calling the provider but before saving, or an expired lease, may require another provider call. Durable recovery also depends on persistent storage, still Part 6. SQLite concurrency is tested; PostgreSQL production behavior is not yet established. The table is currently created additively by existing startup create_all; versioned migrations remain Part 6.

Suggested answers now use a deterministic answer-building template, the user's exact supplied answer (bounded excerpt), and explicit placeholders for missing facts. AI strengths/improvements remain model judgments, not verified facts. No model-authored first-person biography is presented as the answer. Coach prompts also prohibit invented achievements and require placeholders or labeled hypothetical examples.

The coach now selects an owned report explicitly. Context, send, history and clear requests carry that report ID. Action-plan links open their selected report. Choosing a report updates the URL, and changing reports remounts the conversation to prevent late responses from populating a different report. Older API clients may still omit the report ID to use the latest report.

## Validation

Regression coverage includes overlapping duplicate/conflicting submissions, lost-response replay, provider-failure retry, expired-worker fencing, ownership denial, stable indexes for repeated question text, recovery of older examples, and independent report conversations/clear behavior. Concurrency tests bypass only the process-local guard to exercise database protection as if requests came from separate workers. Browser tests cover page-refresh recovery, answer preservation, question indexes and report-pinned conversations. Provider mocking is distinguished from live verification in the release report.
