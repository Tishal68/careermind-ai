"""Bounded extraction child process; invoked without a shell."""
import json
import sys
if sys.platform != "win32":
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
from app.services.parser_service import ResumeParserService

if __name__ == "__main__":
    try:
        print(json.dumps({"text": ResumeParserService.extract_raw_text(sys.argv[1], sys.argv[2])}))
    except Exception:
        print(json.dumps({"error": "Unable to read this resume within the document limits. Use a valid text-based PDF or DOCX."}))
        sys.exit(1)
