"""Offline orphan-upload maintenance. Stop all writers first; defaults to dry-run."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
import time


def cleanup(database, uploads, working_directory, *, delete=False, older_than_hours=24, max_files=10000):
    database = Path(database).resolve()
    uploads = Path(uploads)
    if uploads.is_symlink():
        raise ValueError("Upload root must not be a symlink")
    uploads = uploads.resolve()
    working_directory = Path(working_directory).resolve()
    if not database.is_file() or not uploads.is_dir():
        raise ValueError("Database and upload directory must exist")
    if older_than_hours < 24 or max_files < 1:
        raise ValueError("Use at least a 24-hour grace period and a positive file limit")
    referenced = set()
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
        for (value,) in connection.execute("SELECT file_path FROM resume_sessions"):
            if not value:
                continue
            path = (working_directory / value).resolve()
            if uploads not in path.parents:
                raise ValueError("A stored path is outside the upload root; reconcile paths before cleanup")
            referenced.add(path)
    cutoff = time.time() - older_than_hours * 3600
    candidates = []
    count = 0
    for path in uploads.rglob("*"):
        count += 1
        if count > max_files:
            raise ValueError("Scan limit exceeded; no files were deleted")
        if path.is_symlink():
            raise ValueError("Symlinks are not supported; no files were deleted")
        if path.is_file() and path.resolve() not in referenced and path.stat().st_mtime < cutoff:
            candidates.append(path)
    # The complete scan succeeds before deletion. Offline use prevents a new
    # upload or reference being added between this snapshot and deletion.
    if delete:
        for path in candidates:
            path.unlink()
    return [str(path.relative_to(uploads)) for path in candidates]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database")
    parser.add_argument("uploads")
    parser.add_argument("working_directory", help="Original application working directory for relative stored paths")
    parser.add_argument("--delete", action="store_true", help="Delete reviewed orphan files; all app writers must be stopped")
    parser.add_argument("--older-than-hours", type=int, default=24)
    parser.add_argument("--max-files", type=int, default=10000)
    args = parser.parse_args()
    candidates = cleanup(args.database, args.uploads, args.working_directory, delete=args.delete,
                         older_than_hours=args.older_than_hours, max_files=args.max_files)
    print({"deleted" if args.delete else "candidates": candidates})
