# Part 1: report-based action plans

## Changes

- Reports link to their own saved action plan. The navigation defaults to the latest report; report selection and pagination are available in the plan workspace.
- The old roadmap/projects pages share this workspace. Neither uses report ID 1, a fixed AI Engineer role, or canned success content after an error.
- Practice suggestions are explicitly labeled deterministic suggestions from report gaps. Eligibility, qualification and experience requirements produce verification tasks, not invented technical projects. Insufficient typical-market evidence produces no inferred plan.
- Completion is persisted with an owned report, survives browser reload, and uses a revision check to reject conflicting edits. Repeated plan creation preserves completion. Keyboard-accessible checkboxes replace click-only divs.
- Read, create, update and project lookup enforce report ownership. The project endpoint now requires report_id; old role-only clients receive validation errors rather than unrelated projects.
- Errors expose reload/retry actions and do not optimistically mark failed updates as saved.

## Scope and compatibility

This part repairs the roadmap/project user flow. The older auto-pipeline/brain engines remain outside this release scope. Plans use the existing report JSON column, so no new database schema is needed. Previously generated legacy roadmap JSON is replaced when a new action plan is explicitly created; the legacy UI had no persisted task-completion API. New-format plans are never silently regenerated. The old roadmap API remains a compatibility wrapper; its week-oriented response fields should not be interpreted as a personalized schedule.

The coach still uses the latest report; the plan screen makes that limitation visible before linking to it. Per-selected-report coaching is later work.

## Verification

Backend coverage includes report ownership, no-gap/insufficient-evidence cases, eligibility separation, persistence across requests, idempotent creation, and competing updates. Browser coverage includes selected-report links, keyboard completion/reload, report switching, failure/retry UI, conflicting edits and responsive overflow. CI now runs the browser tests against a production frontend build with controlled API responses; backend tests separately exercise persistence.

Permanent data survival across a Render redeploy is NOT provided by this change. The current free instance still uses temporary storage. Moving real-user data to persistent storage and testing restore is the next infrastructure phase and needs paid-resource approval.
