import hashlib
import importlib.util
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("storage_backup", Path(__file__).parents[1] / "scripts/storage_backup.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def archive_at(tmp_path, files):
    archive = tmp_path / "backup.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        manifest = {}
        for name, value in files.items():
            bundle.writestr(name, value)
            manifest[name] = hashlib.sha256(value).hexdigest()
        bundle.writestr("manifest.json", json.dumps(manifest))
    return archive


def test_corrupt_database_never_publishes_destination(tmp_path):
    archive = archive_at(tmp_path, {"database.sqlite": b"not a database"})
    target = tmp_path / "restore"
    with pytest.raises(sqlite3.DatabaseError):
        backup.restore(archive, target)
    assert not target.exists()
    assert not list(tmp_path.glob(".careermind-restore-*"))


@pytest.mark.parametrize("files", [
    {"uploads/A.txt": b"a", "uploads/a.txt": b"b"},
    {"uploads/folder": b"a", "uploads/folder/child": b"b"},
    {"uploads/../escape": b"a"},
    {"uploads/C:/escape": b"a"},
    {"uploads/CON": b"a"},
    {"uploads/hidden.": b"a"},
])
def test_ambiguous_archive_paths_are_rejected(tmp_path, files):
    archive = archive_at(tmp_path, {"database.sqlite": b"placeholder", **files})
    with pytest.raises(ValueError):
        backup.restore(archive, tmp_path / "restore")
    assert not (tmp_path / "restore").exists()


def test_decompression_and_file_limits(tmp_path):
    archive = archive_at(tmp_path, {"database.sqlite": b"a" * 100000, "uploads/file": b"b"})
    for limits in ({"max_bytes": 1000}, {"max_files": 1}):
        with pytest.raises(ValueError, match="limits"):
            backup.restore(archive, tmp_path / "restore", **limits)
    assert not (tmp_path / "restore").exists()


def test_bad_checksum_does_not_leave_partial_restore(tmp_path):
    archive = tmp_path / "backup.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("database.sqlite", b"content")
        bundle.writestr("manifest.json", json.dumps({"database.sqlite": "0" * 64}))
    with pytest.raises(ValueError, match="checksum"):
        backup.restore(archive, tmp_path / "restore")
    assert not (tmp_path / "restore").exists()


def test_offline_cleanup_preserves_referenced_and_recent_files(tmp_path):
    import os
    import time
    spec = importlib.util.spec_from_file_location("storage_cleanup", Path(__file__).parents[1] / "scripts/storage_cleanup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    for name in ("saved", "orphan", "recent"):
        (uploads / name).write_text("synthetic")
    old = time.time() - 48 * 3600
    for name in ("saved", "orphan"):
        os.utime(uploads / name, (old, old))
    database = tmp_path / "data.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE resume_sessions (file_path TEXT)")
        connection.execute("INSERT INTO resume_sessions VALUES ('uploads/saved')")
    assert module.cleanup(database, uploads, tmp_path) == ["orphan"]
    assert (uploads / "orphan").exists()
    with pytest.raises(ValueError, match="Scan limit"):
        module.cleanup(database, uploads, tmp_path, delete=True, max_files=1)
    assert (uploads / "orphan").exists()
    assert module.cleanup(database, uploads, tmp_path, delete=True) == ["orphan"]
    assert (uploads / "saved").exists() and (uploads / "recent").exists()
    assert not (uploads / "orphan").exists()
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO resume_sessions VALUES ('elsewhere/resume')")
    with pytest.raises(ValueError, match="outside"):
        module.cleanup(database, uploads, tmp_path, delete=True)
