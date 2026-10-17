# Part 4: Resume inspection and interview practice

Resume management now provides an on-demand view of the extracted source text. The authenticated endpoint filters by owner, returns 404 to other accounts and marks responses no-store. Text is not added to resume-list payloads or browser storage. The UI renders plain escaped text, supports retry, and resets the preview when selecting a different resume. Missing parsed metadata does not prevent source-text inspection.

Interview practice is available in dashboard navigation. After submission the question and its feedback remain together until the user chooses Next question. Answers survive provider failures, and inputs are disabled during evaluation. Feedback shows strengths, improvements, the submitted answer and a suggested answer. The twentieth answer returns no next question; the UI shows completion and allows starting another session. This does not introduce interview history recovery across reloads or guarantee concurrent multi-tab evaluation consistency.

The 404 page and reusable navbar use CareerMind AI branding. README now describes current behavior, setup, tests and temporary-storage limitations instead of claiming fabricated ATS/readiness scores, streaming, token refresh, comprehensive structured extraction or production readiness.

Validation: backend ownership, no-cache response, minimal list payload and final-interview-question regression tests; browser lazy loading/retry/plain-text display/resume selection and interview failure/feedback/advance/completion/restart flows. Existing account, session, role and action-plan tests retained.
