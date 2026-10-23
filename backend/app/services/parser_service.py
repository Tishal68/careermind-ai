import re
import logging
from typing import Dict, Any, List
import pdfplumber
import docx
from app.intelligence.skill_catalog import ALIASES

logger = logging.getLogger(__name__)

TECHNICAL_SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "react", "next.js", "node.js", "fastapi", "flask", "django",
    "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", "azure",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "data science", "data analysis", "nlp", "computer vision", "generative ai", "langchain", "rag",
    "statistics", "excel", "tableau", "mlops", "llm", "opencv", "transformers", "terraform", "vector databases",
    "git", "ci/cd", "linux", "rest api", "graphql", "c++", "java", "go", "rust", "tailwind css", "html", "css"
]

SOFT_SKILL_KEYWORDS = [
    "leadership", "communication", "problem solving", "critical thinking", "teamwork",
    "collaboration", "adaptability", "time management", "agile", "scrum", "project management",
    "analytical skills", "creativity", "decision making"
]


class ResumeParserService:
    @staticmethod
    def extract_raw_text(file_path: str, file_type: str) -> str:
        try:
            if file_type.lower() == ".pdf":
                with pdfplumber.open(file_path) as pdf:
                    if len(pdf.pages) > 30:
                        raise ValueError("Resume exceeds 30 pages.")
                    parts = []
                    total = 0
                    for page in pdf.pages:
                        part = page.extract_text() or ""
                        total += len(part)
                        if total > 100000:
                            raise ValueError("Resume text exceeds limits.")
                        parts.append(part)
                    text = "\n".join(parts)
            elif file_type.lower() == ".docx":
                document = docx.Document(file_path)
                parts = []
                seen_hdrftr_parts = set()

                def _extract_container_items(container):
                    items_text = []
                    if hasattr(container, "iter_inner_content"):
                        for item in container.iter_inner_content():
                            if isinstance(item, docx.text.paragraph.Paragraph):
                                t = item.text.strip()
                                if t:
                                    items_text.append(t)
                            elif isinstance(item, docx.table.Table):
                                seen_c = set()
                                for r in item.rows:
                                    for c in r.cells:
                                        if c._element not in seen_c:
                                            seen_c.add(c._element)
                                            t = c.text.strip()
                                            if t:
                                                items_text.append(t)
                    else:
                        for p in getattr(container, "paragraphs", []):
                            t = p.text.strip()
                            if t:
                                items_text.append(t)
                        for tbl in getattr(container, "tables", []):
                            seen_c = set()
                            for r in tbl.rows:
                                for c in r.cells:
                                    if c._element not in seen_c:
                                        seen_c.add(c._element)
                                        t = c.text.strip()
                                        if t:
                                            items_text.append(t)
                    return items_text

                # 1. Section Headers (deduplicating linked headers)
                for idx, section in enumerate(document.sections):
                    hdrs = []
                    if getattr(section, "different_first_page_header_footer", False):
                        if getattr(section.first_page_header, "_has_definition", False):
                            hdrs.append(section.first_page_header)
                    if getattr(section.header, "_has_definition", False) or (idx == 0 and not section.header.is_linked_to_previous):
                        hdrs.append(section.header)
                    try:
                        if getattr(document.settings, "odd_and_even_pages_header_footer", False):
                            if getattr(section.even_page_header, "_has_definition", False):
                                hdrs.append(section.even_page_header)
                    except Exception:
                        pass

                    for h in hdrs:
                        try:
                            p_id = id(h.part)
                        except Exception:
                            p_id = id(h._element)
                        if p_id not in seen_hdrftr_parts:
                            seen_hdrftr_parts.add(p_id)
                            parts.extend(_extract_container_items(h))

                # 2. Main Body (paragraphs and tables in document order)
                parts.extend(_extract_container_items(document))

                # 3. Section Footers (deduplicating linked footers)
                for idx, section in enumerate(document.sections):
                    ftrs = []
                    if getattr(section, "different_first_page_header_footer", False):
                        if getattr(section.first_page_footer, "_has_definition", False):
                            ftrs.append(section.first_page_footer)
                    if getattr(section.footer, "_has_definition", False) or (idx == 0 and not section.footer.is_linked_to_previous):
                        ftrs.append(section.footer)
                    try:
                        if getattr(document.settings, "odd_and_even_pages_header_footer", False):
                            if getattr(section.even_page_footer, "_has_definition", False):
                                ftrs.append(section.even_page_footer)
                    except Exception:
                        pass

                    for f in ftrs:
                        try:
                            p_id = id(f.part)
                        except Exception:
                            p_id = id(f._element)
                        if p_id not in seen_hdrftr_parts:
                            seen_hdrftr_parts.add(p_id)
                            parts.extend(_extract_container_items(f))

                text = "\n".join(parts)
            else:
                raise ValueError("Upload a PDF or DOCX resume.")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Unable to read this resume. Upload a valid PDF or DOCX file.") from exc
        if len(text) > 100000:
            raise ValueError("Resume text exceeds 100,000 characters.")
        if not text.strip():
            raise ValueError("No readable text found. Use a text-based PDF or DOCX; scanned PDFs need OCR first.")
        return text.strip()

    @staticmethod
    def parse_resume_content(raw_text: str) -> Dict[str, Any]:
        text = raw_text.casefold()
        found = []
        for keyword in TECHNICAL_SKILL_KEYWORDS:
            canonical = next((name for name in ALIASES if name.casefold() == keyword), keyword.title())
            terms = [keyword, *ALIASES.get(canonical, [])]
            if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) for term in terms):
                found.append(canonical)
        soft = [kw.title() for kw in SOFT_SKILL_KEYWORDS if re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", text)]
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_text)
        contact = {"email": emails[0] if emails else None}
        return {
            "contact": contact,
            "contact_info": contact,
            "technical_skills": found,
            "soft_skills": soft,
            "tools_frameworks": [],
            "education": [],
            "experience": [],
            "projects": [],
        }
