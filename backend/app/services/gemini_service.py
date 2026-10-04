import os
import json
import logging
from typing import Dict, Any, List
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)


def call_gemini_api(prompt: str) -> str:
    """Call Google Gemini API using official google-genai SDK if valid GEMINI_API_KEY is configured."""
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not api_key or not api_key.startswith("AIzaSy"):
        return ""
    try:
        client = genai.Client(api_key=api_key)
        for model_name in ["gemini-1.5-flash", "gemini-2.0-flash", settings.GEMINI_MODEL]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as inner_e:
                logger.warning(f"Gemini model {model_name} failed: {inner_e}")
                continue
    except Exception as e:
        logger.error(f"Gemini API Client error: {e}")
    return ""


class GeminiAnalysisService:
    @staticmethod
    def analyze_resume_gap(
        parsed_resume: Dict[str, Any],
        field: str,
        job_role: str,
        experience_level: str
    ) -> Dict[str, Any]:
        skills = parsed_resume.get("technical_skills", [])
        prompt = f"""
Act as a Senior Executive Tech Recruiter and AI Career Strategist.
Candidate Skills: {', '.join(skills)}
Target Field: {field}
Target Job Role: {job_role}
Target Experience Level: {experience_level}

Analyze the candidate's resume against the target role requirements. Return ONLY a valid JSON object matching this schema:
{{
  "ats_score": <float 50-100>,
  "resume_score": <float 50-100>,
  "readiness_score": <float 50-100>,
  "matched_skills": [<array of matched skill strings>],
  "missing_skills": [<array of missing skill strings>],
  "strengths": [<array of strength strings>],
  "weaknesses": [<array of weakness strings>],
  "reasoning": "<strategic summary>",
  "recommended_certifications": [<array of certification strings>]
}}
"""
        raw_res = call_gemini_api(prompt)
        if raw_res:
            try:
                json_str = raw_res.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                parsed_json = json.loads(json_str)
                ats = float(parsed_json.get("ats_score", 82.0))
                qual = float(parsed_json.get("resume_score", 80.0))
                readiness = float(parsed_json.get("readiness_score", 75.0))
                return {
                    "resume_score": qual,
                    "ats_score": ats,
                    "readiness_score": readiness,
                    "analysis_data": {
                        "matched_skills": parsed_json.get("matched_skills", skills[:4]),
                        "strengths": parsed_json.get("strengths", ["Solid Python & software core"]),
                        "weaknesses": parsed_json.get("weaknesses", ["Missing deployment metrics"])
                    },
                    "gap_analysis": {
                        "missing_skills": parsed_json.get("missing_skills", ["System Architecture", "Docker"]),
                        "reasoning": parsed_json.get("reasoning", f"To become a top candidate for {job_role}, bridge key skill gaps."),
                        "recommended_certifications": parsed_json.get("recommended_certifications", ["AWS Certified Solutions Architect"])
                    }
                }
            except Exception as e:
                logger.warning(f"Failed to parse Gemini JSON output: {e}")

        tech_skills = set(s.lower() for s in skills)
        role_reqs = {
            "ai engineer": {"python", "pytorch", "tensorflow", "fastapi", "docker", "langchain", "rag", "vector databases"},
            "machine learning engineer": {"python", "scikit-learn", "pandas", "numpy", "mlops", "docker", "sql"},
            "data scientist": {"python", "sql", "pandas", "numpy", "statistics", "data analysis", "tableau"},
            "data analyst": {"sql", "excel", "power bi", "tableau", "python", "data analysis"},
            "generative ai engineer": {"python", "langchain", "rag", "transformers", "fastapi", "llms"},
            "software development": {"python", "javascript", "react", "fastapi", "sql", "git", "docker"}
        }

        target_reqs = role_reqs.get(job_role.lower(), {"python", "git", "sql", "docker", "rest api"})
        missing = [s.title() for s in target_reqs if s not in tech_skills]
        matched = [s.title() for s in tech_skills if s in target_reqs]

        matched_count = len(matched)
        total_reqs = max(len(target_reqs), 1)
        base_match_ratio = matched_count / total_reqs

        ats_score = round(min(100.0, max(50.0, base_match_ratio * 40 + 55.0)), 1)
        resume_score = round(min(100.0, max(60.0, len(skills) * 4.0 + 50.0)), 1)
        readiness_score = round((ats_score * 0.5 + resume_score * 0.5), 1)

        return {
            "resume_score": resume_score,
            "ats_score": ats_score,
            "readiness_score": readiness_score,
            "analysis_data": {
                "matched_skills": matched,
                "strengths": [
                    f"Strong baseline technical foundation in {', '.join(skills[:3]) if skills else 'Software Engineering'}.",
                    "Structured education and practical project exposure."
                ],
                "weaknesses": [
                    f"Missing core requirements for {job_role}: {', '.join(missing[:3]) if missing else 'None'}.",
                    "Needs more quantified impact metrics in experience section."
                ]
            },
            "gap_analysis": {
                "missing_skills": missing if missing else ["Advanced System Design", "CI/CD Pipeline Automation"],
                "reasoning": f"To qualify as a competitive {experience_level} {job_role}, focus on bridging gaps in {', '.join(missing[:3]) if missing else 'system architecture'}.",
                "recommended_certifications": [
                    "AWS Certified Machine Learning - Specialty",
                    "Google Professional Machine Learning Engineer"
                ]
            }
        }
