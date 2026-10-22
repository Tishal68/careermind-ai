# Part 7: account security, first increment

Settings now supports changing a password after confirming the current password.
The replacement must contain 12 to 1024 characters and differ from the current
password. A successful change increments the account's session version and returns
a replacement login token. All earlier tokens fail subsequent authentication,
including legacy tokens without a version. Requests authenticated before the
change may already be in flight; this does not cancel background research jobs.

The browser replaces its token and clears the password fields. Other tabs sharing
the same browser storage receive the replacement through the existing storage
listener. Other browsers must sign in again. A lost response has an uncertain
outcome: try the new password before retrying the change.

An atomic conditional database update prevents two concurrent changes authorized
by the same old password from overwriting each other. Login signs the version from
the same user snapshot whose password was verified. Five attempts per account per
minute are allowed in the current single-process deployment. Shared limits are
required before adding application workers or instances.

## Migration and rollback

Startup applies `0002_session_version` after the existing `0001_baseline` migration.
Existing accounts start at version zero. Fresh databases run both migrations.
Unversioned installations must first run the baseline-adoption release. Existing
versioned installations upgrade directly. Migration tests cover data preservation.

Do not roll back to an application release that ignores session versions: it can
reactivate revoked sessions. The migration intentionally refuses downgrade.
Emergency rollback requires an explicit session-invalidating secret rotation and
a reviewed database recovery plan.

## Remaining work

This increment does not complete account security. Secure HttpOnly cookies with
CSRF protection, email verification, password recovery, account export/deletion,
and broader release security checks remain. Browser tokens still use localStorage.
The free Render deployment still has temporary storage; durable user data requires
a separate storage decision. No paid hosting changes are included.
