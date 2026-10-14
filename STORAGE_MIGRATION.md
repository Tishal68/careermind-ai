# Persistent storage migration and rollback

The current Render service is free and has no persistent disk. The owner confirmed that current data is disposable test data. This approval does not authorize losing future real-user data. Do not claim persistence on the current service.

## Proposed smallest paid configuration (approval required)

Starter web service ($7/month) plus a 1 GB persistent disk ($0.25/month): approximately $7.25/month before taxes, usage overages, or workspace charges. Verify the final Dashboard quote before applying. Sources checked 2026-10-14: https://render.com/pricing and https://render.com/docs/disks . A disk requires one service instance and disables zero-downtime deploys. Managed PostgreSQL plus object storage is the preferred later multi-instance design, but requires a separately priced migration.

The existing render.yaml defines a disk mounted at /app/data. Set DATABASE_URL=sqlite:////app/data/careermind.db and UPLOAD_DIR=/app/data/uploads/resumes. Verify the mounted directory is writable by UID 10001; an image-layer chown is not proof of mounted-volume permissions. Keep SECRET_KEY unchanged during migration unless intentionally revoking all sessions.

## Before a real-data migration

1. Freeze uploads, research, chat, and account writes; allow active workers to finish. Record deployed commit and non-secret configuration, table counts, and upload count.
2. Take a private snapshot with the database-native backup tool: python backend/scripts/storage_backup.py backup <database-path> <upload-directory> <private-backup.zip>. This uses SQLite's backup API and a checksummed upload manifest. Store the archive encrypted and away from the service. It contains personal data and password hashes; never commit it.
3. Restore to a fresh directory with: python backend/scripts/storage_backup.py restore <private-backup.zip> <fresh-directory>. Verify counts, file hashes, ownership relations, and sample account/report/upload behavior. Reconcile any stored file_path values if the upload root changes. Do not blindly replace paths outside the old upload root.
4. Free Render services do not expose SSH/shell access (https://render.com/docs/ssh). They also lose local files on deploy/restart (https://render.com/docs/free). Therefore, if valuable data exists only inside a free instance and no supported export is already available, stop before upgrading/redeploying. Arrange a supported export with the owner/Render support. Installing an export endpoint by redeploying would itself risk losing the data.

## Cutover for the currently disposable dataset

After explicit cost approval, provision the disk and Starter service, configure the persistent paths, validate permissions and create a fresh database. No real-data preservation is promised for the discarded test dataset. Run registration/login/upload/research smoke checks; record a test row and uploaded-file hash, restart the service, and verify both survive. Take a backup and restore it in isolation. Configure scheduled private database-native backups before admitting real users; disk snapshots alone are not a database backup strategy.

## Rollback

Keep the prior image commit and verified backup. Stop writes and workers, preserve the failed database as a separate private snapshot, then restore the backup into a fresh directory. Verify integrity and counts before changing paths. Avoid destructive overwrite or restoring a disk snapshot as the only SQLite recovery strategy. Roll back application code only after checking schema compatibility. New queue tables are additive; retained legacy reports and accounts are not rewritten. Never point a rollback at temporary storage and describe it as durable.

## Current deployment boundary

Code improvements can run on the authorized free plan, but research restart recovery only works while its database survives. A host/container replacement on ephemeral storage can lose the database, queue, accounts and uploaded files. Paid persistence remains an explicit open dependency.
