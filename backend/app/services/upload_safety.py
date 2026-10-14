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
    # Uvicorn's --app-dir changes its import path, not the child process cwd.
    # Resolve uploads before switching to the backend package directory.
    path = Path(path).resolve()
    try:
        result = subprocess.run([sys.executable, '-m', 'app.services.document_worker', str(path), extension],
                                cwd=Path(__file__).resolve().parents[2],
                                capture_output=True, text=True, encoding='utf-8', timeout=20,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Reading this file took too long. Try exporting a simpler PDF or DOCX and upload it again.") from exc
    try:
        data = json.loads(result.stdout)
    except ValueError as exc:
        raise HTTPException(503, "The resume reader is temporarily unavailable. Please retry.") from exc
    if isinstance(data, dict) and isinstance(data.get('error'), str):
        raise ValueError(data['error'])
    if result.returncode or not isinstance(data, dict) or not isinstance(data.get('text'), str):
        raise HTTPException(503, "The resume reader is temporarily unavailable. Please retry.")
    return data['text']


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
