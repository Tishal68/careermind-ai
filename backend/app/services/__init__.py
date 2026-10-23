"""
Service layer package exports with PEP 562 module lazy loading.
Prevents isolated worker child processes from eagerly importing FastAPI, AI agents,
and unrelated services on startup.
"""

import importlib

def __getattr__(name: str):
    if name == "ResumeParserService":
        mod = importlib.import_module("app.services.parser_service")
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name in ("GeminiAnalysisService", "call_gemini_api"):
        mod = importlib.import_module("app.services.gemini_service")
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name == "CoachService":
        mod = importlib.import_module("app.services.coach_service")
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name == "RAGAssistantService":
        mod = importlib.import_module("app.services.rag_service")
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name == "RoadmapService":
        mod = importlib.import_module("app.services.roadmap_service")
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name == "InterviewService":
        mod = importlib.import_module("app.services.interview_service")
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name == "action_plans":
        mod = importlib.import_module("app.services.action_plans")
        globals()[name] = mod
        return mod
    try:
        mod = importlib.import_module(f"app.services.{name}")
        globals()[name] = mod
        return mod
    except ModuleNotFoundError:
        pass
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "ResumeParserService",
    "GeminiAnalysisService",
    "call_gemini_api",
    "CoachService",
    "RAGAssistantService",
    "RoadmapService",
    "InterviewService"
]
