"""Offline SQLite + uploads backup/restore. Quiesce writes before taking a backup."""
from contextlib import closing
import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath


def backup(database, uploads, archive):
    database,uploads,archive=Path(database).resolve(),Path(uploads).resolve(),Path(archive).resolve()
    if not database.is_file() or not uploads.is_dir():raise ValueError('Database and upload directory must exist')
    if archive.exists():raise ValueError('Refusing to overwrite an existing backup')
    if uploads == archive or uploads in archive.parents:raise ValueError('Store backups outside uploads')
    with tempfile.TemporaryDirectory() as scratch:
        snapshot=Path(scratch)/'database.sqlite'
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as source, closing(sqlite3.connect(snapshot)) as dest:
            source.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed')
        manifest={}
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as bundle:
            paths=[('database.sqlite',snapshot)]
            for file in uploads.rglob('*'):
                if file.is_symlink():raise ValueError('Symlinks are not supported')
                if file.is_file():paths.append(('uploads/'+file.relative_to(uploads).as_posix(),file))
            for name,file in paths:
                contents=file.read_bytes();manifest[name]=hashlib.sha256(contents).hexdigest();bundle.writestr(name,contents)
            bundle.writestr('manifest.json',json.dumps(manifest,sort_keys=True))


def restore(archive, destination, *, max_bytes=2 * 1024**3, max_files=10000):
    """Validate into a private staging directory; publish only a complete restore.

    Run offline in an operator-controlled parent directory. Limits can be raised
    deliberately for a known larger backup through the CLI.
    """
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Restore destination must not already exist')
    if max_bytes <= 0 or max_files <= 0:
        raise ValueError('Restore limits must be positive')
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive entries')
        if len(entries) > max_files + 1 or sum(e.file_size for e in entries) > max_bytes:
            raise ValueError('Backup exceeds restore limits')
        manifest_entry = bundle.getinfo('manifest.json')
        if manifest_entry.file_size > 4 * 1024**2:
            raise ValueError('Backup manifest exceeds restore limits')
        manifest = json.loads(bundle.read(manifest_entry))
        if not isinstance(manifest, dict) or set(names) != set(manifest) | {'manifest.json'}:
            raise ValueError('Backup manifest mismatch')
        canonical = set()
        for name, digest in manifest.items():
            path = PurePosixPath(name)
            if (not name or path.is_absolute() or '..' in path.parts
                    or path.as_posix() != name or '\\' in name
                    or PureWindowsPath(name).drive or ':' in name
                    or any(part.endswith(('.', ' ')) or PureWindowsPath(part).is_reserved() for part in path.parts)):
                raise ValueError('Unsafe archive path')
            if name != 'database.sqlite' and not name.startswith('uploads/'):
                raise ValueError('Unsafe archive path')
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError('Invalid backup checksum')
            key = name.casefold()
            if key in canonical:
                raise ValueError('Conflicting archive paths')
            canonical.add(key)
        if 'database.sqlite' not in manifest:
            raise ValueError('Backup database is missing')
        for name in canonical:
            if any(parent.as_posix() in canonical for parent in PurePosixPath(name).parents):
                raise ValueError('Conflicting archive paths')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.careermind-restore-', dir=destination.parent) as scratch:
            staging = Path(scratch) / 'complete'
            staging.mkdir()
            total = 0
            for name, digest in manifest.items():
                target = staging / name
                target.parent.mkdir(parents=True, exist_ok=True)
                checksum = hashlib.sha256()
                with bundle.open(name) as source, target.open('xb') as output:
                    while chunk := source.read(1024 * 1024):
                        total += len(chunk)
                        if total > max_bytes:
                            raise ValueError('Backup exceeds restore limits')
                        checksum.update(chunk)
                        output.write(chunk)
                if checksum.hexdigest() != digest:
                    raise ValueError('Backup checksum mismatch')
            with closing(sqlite3.connect((staging / 'database.sqlite').as_uri() + '?mode=ro', uri=True)) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('Restored database integrity check failed')
            (staging / 'uploads').mkdir(exist_ok=True)
            if destination.exists() or destination.is_symlink():
                raise ValueError('Restore destination must not already exist')
            staging.rename(destination)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    save=sub.add_parser('backup');save.add_argument('database');save.add_argument('uploads');save.add_argument('archive')
    load=sub.add_parser('restore');load.add_argument('archive');load.add_argument('destination');load.add_argument('--max-bytes',type=int,default=2*1024**3);load.add_argument('--max-files',type=int,default=10000)
    args=parser.parse_args()
    if args.command=='backup':backup(args.database,args.uploads,args.archive)
    else:restore(args.archive,args.destination,max_bytes=args.max_bytes,max_files=args.max_files)
    print('Storage operation completed; keep backups private.')
