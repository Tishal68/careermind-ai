# Part 2: reliable account data loading

The active dashboard, resume list and report pages now distinguish failed requests from empty accounts. Resume refresh keeps the last successfully loaded list on transient failure; explicit Retry buttons recover each resource independently. Retrying reports does not overwrite newly typed role preferences. A new upload invalidates an older list request, so an older response cannot hide the new file.

Unused Session/Career/Workspace provider trees and their unused hook were removed. These providers made duplicate background requests without active page consumers. Account pages now own their data loading. The dashboard subtree is keyed by account ID, resource requests are cancelled on session change/unmount, and the API client rejects successful responses issued under a replaced login token before callers can apply them.

The report list and selected detail now have independent errors and request cancellation. Detail Retry uses the failed report ID rather than unexpectedly selecting the newest report. Failed reads no longer show a misleading no-reports message.

Verification includes deterministic delayed-success/401 response tests and browser cases for partial failures, preserving cached resumes on refresh failure, preserving user edits during retries, real cross-tab account changes with delayed old responses, and independent report list/detail retries. Previous action-plan browser regressions remain in the suite.

This change does not add password reset/email delivery, permanent storage, provider failover or cookie-based sessions. Those remain separate planned work. No paid resources or backend schema changes are required.
