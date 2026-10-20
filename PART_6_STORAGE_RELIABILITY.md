# Part 6: storage reliability — code preparation

## Implemented

- Alembic 1.20.0 and a frozen baseline schema replace import-time create_all. FastAPI startup migrates before the research dispatcher starts or requests are accepted.
- A fresh database is migrated automatically. An unversioned database is adopted only if its complete schema matches the Part 5 application schema. Unknown/partial schemas and unknown revisions fail startup without silently being marked current.
- Repeat startup preserves saved records. PostgreSQL migrators use a transaction-scoped advisory lock; SQLite requires the existing single-instance deployment with one startup process.
- Readiness checks require both a reachable users table and the expected schema revision. The existing public endpoint does not reveal database details.
- Backup restore validates paths, cross-platform filename collisions, file counts, decompressed size, checksums, and SQLite integrity in a temporary staging directory. Only a fully validated restore is published. Defaults: 2 GiB total and 10,000 data files; operators can deliberately raise CLI limits for a known larger archive.
- Offline orphan-upload maintenance defaults to dry-run, preserves referenced and recent files, enforces a 24-hour minimum grace period and a scan limit, and rejects ambiguous stored paths. Stop writers before using its explicit --delete option.
- A dedicated PostgreSQL 17 CI service exercises migrations, concurrent research admission, interrupted-worker recovery, and interview claim/retry fencing against a real database. It does not provision a Render database.

## Migration and recovery procedure

Quiesce writes and stop research workers before backing up database plus uploads together. Run backend/scripts/storage_backup.py backup DATABASE UPLOADS ARCHIVE, keep the archive private and encrypted off the service, and test restore into a new operator-controlled directory. The script is for SQLite; PostgreSQL requires pg_dump/pg_restore and a separate uploads backup.

Run backend/scripts/storage_backup.py restore ARCHIVE NEW_DIRECTORY. Original resume file_path values are preserved: before cutover, reconcile paths beneath the old upload root with the restored upload root and verify every referenced file. The restore tool does not silently rewrite application records.

The initial schema revision is 0001_baseline. Future changes must add a new Alembic revision; never edit the baseline or return to create_all. Unversioned legacy adoption deliberately stops working after a later revision is added: operators must first adopt at this baseline release, then upgrade. Destructive baseline downgrade is disabled. Roll back using a verified database/uploads backup with the matching application revision, in an isolated directory first.

## Live hosting status — verified 2026-10-20

The existing Render service is still free, has no configured readiness path, and has no activated durable storage. No paid resources were created and no live data was migrated in this change. Do not merge/redeploy until the current data-preservation decision is confirmed, because the free service filesystem is temporary.

Proposed existing-service cutover: smallest paid web instance, one 1 GB disk at /app/data, DATABASE_URL=sqlite:////app/data/careermind.db, UPLOAD_DIR=/app/data/uploads/resumes, readiness path /api/v1/ready, and one instance. Preserve SECRET_KEY. Confirm the mounted directory is writable by runtime UID 10001 before accepting traffic.

Public pricing checked 2026-10-20 lists $7/month for the smallest paid instance plus $0.25/GB/month disk storage, approximately $7.25/month for this configuration before taxes, usage charges, or workspace charges. Obtain approval before changing billing. Sources: https://render.com/pricing and https://render.com/docs/disks.

After approval: reconfirm whether data is still disposable; preserve valuable records before any restart; activate storage and readiness; upload a synthetic canary; create saved report/interview records; restart/redeploy and verify record IDs and file hashes survive; test a private off-service backup/restore. Establish backup scheduling and retention. A disk enables persistence but is not itself an off-service backup and prevents horizontal scaling and zero-downtime deployments.

## Validation and remaining boundaries

Local validation: 129 backend tests passed, then the 10 new restore/cleanup tests and the existing backup round-trip passed; dependency audit found no known vulnerabilities. CI results are tracked on the pull request. PostgreSQL runtime verification is only established when its new CI job passes.

Part 6 remains incomplete until paid storage is approved, mounted-path writes and persistence across real redeploys are verified, readiness is configured on the existing service, and operational backup/retention and the offline cleanup schedule are established. No claim of live durability or zero bugs is made by these code changes.
