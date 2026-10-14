"""Offline SQLite + uploads backup/restore. Quiesce writes before taking a backup."""
from contextlib import closing
import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path


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


def restore(archive,destination):
    destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Restore destination must not already exist')
    with zipfile.ZipFile(archive) as bundle:
        names=bundle.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate archive entries')
        manifest=json.loads(bundle.read('manifest.json'))
        if set(names)!=set(manifest)|{'manifest.json'}:raise ValueError('Backup manifest mismatch')
        # Validate every path and digest before creating the output directory.
        for name,digest in manifest.items():
            target=(destination/name).resolve()
            if destination not in target.parents or '\\' in name:raise ValueError('Unsafe archive path')
            if hashlib.sha256(bundle.read(name)).hexdigest()!=digest:raise ValueError('Backup checksum mismatch')
        destination.mkdir(parents=True)
        for name in manifest:
            target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(bundle.read(name))
    (destination/'uploads').mkdir(exist_ok=True)
    with closing(sqlite3.connect(destination/'database.sqlite')) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Restored database integrity check failed')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    save=sub.add_parser('backup');save.add_argument('database');save.add_argument('uploads');save.add_argument('archive')
    load=sub.add_parser('restore');load.add_argument('archive');load.add_argument('destination')
    args=parser.parse_args()
    if args.command=='backup':backup(args.database,args.uploads,args.archive)
    else:restore(args.archive,args.destination)
    print('Storage operation completed; keep backups private.')
