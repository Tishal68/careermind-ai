import json
import subprocess
import sys
import zipfile
from pathlib import Path
from fastapi import HTTPException

MAX_EXPANDED = 20 * 1024 * 1024

def preflight_docx(path):
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > 256 or sum(item.file_size for item in entries) > MAX_EXPANDED:
                raise ValueError()
            if any(item.flag_bits & 1 or item.file_size > 8 * 1024 * 1024 or
                   item.file_size > max(item.compress_size, 1) * 300 for item in entries):
                raise ValueError()
            if 'word/document.xml' not in archive.namelist():
                raise ValueError()
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        raise ValueError("DOCX is invalid or exceeds safe archive limits.") from exc

def extract_isolated(path, extension):
    if extension == '.docx':
        preflight_docx(path)
    try:
        result = subprocess.run([sys.executable, '-m', 'app.services.document_worker', str(path), extension],
                                capture_output=True, text=True, encoding='utf-8', timeout=20,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        data = json.loads(result.stdout)
        if result.returncode or not isinstance(data.get('text'), str):
            raise ValueError()
        return data['text']
    except (subprocess.TimeoutExpired, ValueError) as exc:
        raise ValueError("Unable to read this resume within the document limits. Use a text-based PDF or DOCX of at most 30 pages.") from exc

def remove_owned_directory(directory, root):
    """Refuse deletion outside upload storage, including symlink escapes."""
    import shutil
    target, base = Path(directory).resolve(), Path(root).resolve()
    if target == base or base not in target.parents:
        raise HTTPException(500, "Stored upload path is invalid; contact the administrator.")
    if target.exists():
        try:
            shutil.rmtree(target)
        except OSError as exc:
            raise HTTPException(503, "Could not delete stored resume files. Please retry.") from exc
