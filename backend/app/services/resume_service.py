import io
import re
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
import requests
from pypdf import PdfReader
from fastapi import HTTPException, status

from app.config import settings
from app.database import get_resume_analyses_collection

logger = logging.getLogger(__name__)

# Comprehensive role skill taxonomies
ROLE_TAXONOMIES: Dict[str, Dict[str, List[str]]] = {
    "Full Stack Developer": {
        "core": ["JavaScript", "TypeScript", "React", "Node.js", "Express", "HTML5", "CSS3", "Git", "REST APIs", "SQL"],
        "secondary": ["Next.js", "Python", "MongoDB", "PostgreSQL", "Docker", "Tailwind CSS", "GraphQL", "Redux", "CI/CD", "AWS"],
    },
    "Frontend Engineer": {
        "core": ["JavaScript", "TypeScript", "React", "HTML5", "CSS3", "Tailwind CSS", "Responsive Design", "Git", "REST APIs"],
        "secondary": ["Next.js", "Vue.js", "Redux", "Webpack", "Vite", "Jest", "UI/UX", "Web Performance", "Accessibility (a11y)"],
    },
    "Backend Engineer": {
        "core": ["Python", "Java", "Node.js", "Go", "SQL", "PostgreSQL", "REST APIs", "Git", "Data Structures", "System Design"],
        "secondary": ["FastAPI", "Django", "Spring Boot", "MongoDB", "Redis", "Docker", "Kubernetes", "Microservices", "Kafka", "AWS"],
    },
    "Data Scientist": {
        "core": ["Python", "SQL", "Machine Learning", "Pandas", "NumPy", "Scikit-Learn", "Data Analysis", "Statistics"],
        "secondary": ["TensorFlow", "PyTorch", "Deep Learning", "Data Visualization", "Matplotlib", "Seaborn", "Jupyter", "Big Data", "R"],
    },
    "AI/ML Engineer": {
        "core": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "NumPy", "Data Structures", "Algorithms"],
        "secondary": ["NLP", "Computer Vision", "LLMs", "Transformers", "MLOps", "Docker", "LangChain", "Vector Databases", "CUDA", "FastAPI"],
    },
    "DevOps / Cloud Engineer": {
        "core": ["Linux", "Docker", "Kubernetes", "CI/CD", "Git", "Bash", "Cloud Computing", "Networking"],
        "secondary": ["AWS", "Azure", "GCP", "Terraform", "Ansible", "Prometheus", "Grafana", "Jenkins", "GitHub Actions", "Python"],
    },
    "Mobile Developer": {
        "core": ["React Native", "Flutter", "Swift", "Kotlin", "Mobile UI", "REST APIs", "Git"],
        "secondary": ["iOS", "Android", "Redux", "Firebase", "App Store Deployment", "GraphQL", "State Management"],
    },
    "Data Analyst": {
        "core": ["SQL", "Excel", "Data Analysis", "Data Visualization", "Python", "Tableau", "Power BI"],
        "secondary": ["Pandas", "NumPy", "Statistics", "Reporting", "A/B Testing", "ETL", "Business Intelligence"],
    },
}

ALL_TECH_KEYWORDS = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Golang", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "SQL", "HTML", "HTML5", "CSS", "CSS3", "Bash", "Shell", "R",
    # Frontend
    "React", "React.js", "Next.js", "Vue.js", "Angular", "Svelte", "Redux", "Tailwind CSS", "Bootstrap", "Material UI", "Sass", "Webpack", "Vite",
    # Backend & Frameworks
    "Node.js", "Express", "Express.js", "FastAPI", "Django", "Flask", "Spring Boot", "ASP.NET", "NestJS", "GraphQL", "REST APIs", "gRPC", "Microservices",
    # Databases & Caches
    "MongoDB", "PostgreSQL", "MySQL", "SQLite", "Redis", "Elasticsearch", "DynamoDB", "Cassandra", "Prisma", "Mongoose", "SQLAlchemy",
    # Cloud & DevOps
    "Docker", "Kubernetes", "AWS", "Amazon Web Services", "Azure", "Google Cloud", "GCP", "CI/CD", "GitHub Actions", "GitLab CI", "Terraform", "Linux", "Nginx", "Jenkins",
    # AI/ML & Data
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "PyTorch", "TensorFlow", "Pandas", "NumPy", "Scikit-Learn", "NLP", "LLMs", "LangChain", "Computer Vision", "Tableau", "Power BI",
    # Tools & Concepts
    "Git", "GitHub", "GitLab", "Jira", "Agile", "Scrum", "Unit Testing", "Jest", "PyTest", "System Design", "Object Oriented Programming", "OOP", "Data Structures", "Algorithms"
]

ACTION_VERBS = [
    "accelerated", "achieved", "analyzed", "architected", "automated", "built", "collaborated",
    "configured", "created", "decreased", "delivered", "deployed", "designed", "developed",
    "engineered", "established", "executed", "formulated", "implemented", "improved",
    "increased", "initiated", "integrated", "launched", "lead", "led", "managed", "maximized",
    "mentored", "minimized", "modeled", "optimized", "orchestrated", "overhauled", "pioneered",
    "programmed", "reduced", "refactored", "resolved", "revamped", "scaled", "spearheaded",
    "standardized", "streamlined", "strengthened", "tested", "transformed", "upgraded"
]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts raw text from PDF bytes using pypdf."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if reader.is_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Encrypted or password-protected PDF files cannot be analyzed. Please upload an unprotected PDF."
            )
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            extracted_pages.append(text)
        full_text = "\n".join(extracted_pages).strip()

        if len(full_text) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to extract readable text from PDF. Please ensure the file is text-based and not a scanned image."
            )
        return full_text
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process PDF file: {str(e)}"
        )


def analyze_with_gemini(text: str, job_role: str) -> Optional[dict]:
    """Queries Google Gemini API for deep AI resume parsing."""
    if not settings.GEMINI_API_KEY:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    prompt = f"""You are an elite Senior Tech Recruiter and ATS (Applicant Tracking System) Evaluation Expert.
Analyze the following candidate resume text specifically against the target role: "{job_role}".

Resume Text:
\"\"\"{text[:10000]}\"\"\"

Perform a rigorous evaluation and respond ONLY with a valid JSON object matching this exact structure:
{{
  "overall_score": <int between 0 and 100>,
  "ats_score": <int between 0 and 100 measuring ATS formatting, readability, and keyword density>,
  "detected_skills": [<array of tech and hard skills found in the resume>],
  "missing_skills": [<array of critical or desired skills for {job_role} that are absent from the resume>],
  "strengths": [<array of 3 to 5 specific, high-impact strengths of this candidate's resume>],
  "weaknesses": [<array of 3 to 5 constructive, concrete areas for improvement in the resume>],
  "job_match": {{
    "percentage": <int between 0 and 100>,
    "match_level": <"Strong Match", "Moderate Match", or "Potential Match">,
    "summary": <concise 2-sentence summary of role alignment>
  }},
  "recommendations": [<array of 4 to 5 actionable steps candidate can take immediately to boost interview callbacks>],
  "extracted_summary": <concise 2-sentence professional profile summary extracted from the resume>
}}
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                raw_text = candidates[0]["content"]["parts"][0]["text"]
                data = json.loads(raw_text)
                # Basic validation
                if "overall_score" in data and "ats_score" in data:
                    logger.info("Successfully analyzed resume via Google Gemini API.")
                    return data
        else:
            logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Gemini API call failed, falling back to smart NLP engine: {e}")

    return None


def analyze_with_nlp(text: str, job_role: str) -> dict:
    """Smart heuristic NLP engine for ATS scoring and skill taxonomy matching."""
    lower_text = text.lower()

    # 1. Detected skills
    detected = set()
    for skill in ALL_TECH_KEYWORDS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, lower_text):
            detected.add(skill)

    detected_skills = sorted(list(detected))

    # 2. Missing skills for target job role
    role_info = ROLE_TAXONOMIES.get(job_role, ROLE_TAXONOMIES["Full Stack Developer"])
    core_skills = role_info["core"]
    secondary_skills = role_info["secondary"]

    missing_core = [s for s in core_skills if s not in detected_skills]
    missing_sec = [s for s in secondary_skills if s not in detected_skills]
    missing_skills = missing_core + missing_sec[:3]

    # 3. ATS Checks & Scoring
    ats_score = 70  # Baseline
    strengths = []
    weaknesses = []

    # Check for contact info
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text))
    has_phone = bool(re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text))
    has_links = bool(re.search(r"(github\.com|linkedin\.com)", lower_text))

    if has_email and has_phone:
        ats_score += 6
        strengths.append("Standard contact information (Email and Phone) is clearly detectable by ATS parsers.")
    else:
        ats_score -= 6
        weaknesses.append("Missing or hard-to-parse contact details (ensure email and phone are present in plain text).")

    if has_links:
        ats_score += 4
        strengths.append("Includes verified professional links (GitHub / LinkedIn profiles).")

    # Section headings check
    sections_found = 0
    for section in ["experience", "work history", "education", "projects", "skills"]:
        if section in lower_text:
            sections_found += 1

    if sections_found >= 4:
        ats_score += 8
        strengths.append("Standard ATS section headers (Education, Experience, Projects, Skills) are well organized.")
    else:
        ats_score -= 6
        weaknesses.append("Non-standard or missing primary section headers reduce automated resume parsing accuracy.")

    # Action verbs and metrics check
    verb_count = sum(1 for verb in ACTION_VERBS if re.search(r"\b" + verb + r"\b", lower_text))
    metrics_count = len(re.findall(r"\b\d+([.,]\d+)?\s*(%|\+|k|x|million|users|ms|s|gb|x|\$)?\b", lower_text))

    if verb_count >= 6:
        ats_score += 6
        strengths.append(f"Strong action-verb utilization ({verb_count}+ dynamic action verbs detected in bullet points).")
    else:
        ats_score -= 5
        weaknesses.append("Action verbs are underutilized; replace passive descriptions with strong verbs (e.g., 'Engineered', 'Optimized').")

    if metrics_count >= 4:
        ats_score += 6
        strengths.append("Demonstrates quantified business and technical outcomes (numbers, percentages, and metrics detected).")
    else:
        weaknesses.append("Bullet points lack quantifiable metrics; incorporate specific numbers (e.g., '% latency reduced', 'users served').")

    # Clamp ATS score
    ats_score = max(52, min(95, ats_score))

    # 4. Job Match calculation
    matched_core = len(core_skills) - len(missing_core)
    core_match_ratio = matched_core / max(1, len(core_skills))

    matched_sec = len(secondary_skills) - len([s for s in secondary_skills if s in missing_skills])
    sec_match_ratio = matched_sec / max(1, len(secondary_skills))

    match_pct = int((core_match_ratio * 70) + (sec_match_ratio * 30))
    match_pct = max(45, min(98, match_pct))

    if match_pct >= 80:
        match_level = "Strong Match"
        match_summary = f"Your background strongly aligns with typical industry requirements for {job_role}. Most core technical competencies are verified."
    elif match_pct >= 65:
        match_level = "Moderate Match"
        match_summary = f"You possess solid foundational skills for {job_role}, but targeted additions in missing domain competencies will significantly improve callback rates."
    else:
        match_level = "Potential Match"
        match_summary = f"You show transferable engineering skills, but several core prerequisites for {job_role} need to be incorporated."

    # 5. Overall Score
    overall_score = int((match_pct * 0.55) + (ats_score * 0.45))
    overall_score = max(50, min(97, overall_score))

    # 6. Actionable recommendations
    recommendations = [
        f"Incorporate target skills: Prioritize adding hands-on experience or projects featuring {', '.join(missing_core[:3]) if missing_core else 'advanced cloud architectures'}.",
        "Optimize bullet formulas: Use the Google XYZ formula ('Accomplished [X] as measured by [Y], by doing [Z]') across all experience bullets.",
        "Add a targeted role title: Ensure the top headline or summary explicitly reflects the desired title '" + job_role + "'.",
        "Keyword placement: Place critical keywords naturally in both your Skills section and directly within project bullet points.",
        "Clean single-column layout: Retain straightforward typography to maintain 90%+ parse accuracy across Workday, Greenhouse, and Lever."
    ]

    # 7. Candidate Summary
    summary_words = text.split()[:40]
    extracted_summary = " ".join(summary_words).replace("\n", " ").strip()
    if len(extracted_summary) > 200:
        extracted_summary = extracted_summary[:197] + "..."
    if not extracted_summary:
        extracted_summary = f"Technical candidate evaluating resume qualifications for {job_role}."

    return {
        "overall_score": overall_score,
        "ats_score": ats_score,
        "detected_skills": detected_skills,
        "missing_skills": missing_skills,
        "strengths": strengths[:4],
        "weaknesses": weaknesses[:4],
        "job_match": {
            "percentage": match_pct,
            "match_level": match_level,
            "summary": match_summary,
        },
        "recommendations": recommendations,
        "extracted_summary": extracted_summary,
    }


def analyze_resume(file_bytes: bytes, filename: str, job_role: str) -> dict:
    """Full pipeline: extracts text from PDF and runs AI or smart NLP analysis."""
    # 1. Extract text
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    else:
        # Fallback to plain text decoding
        text = file_bytes.decode("utf-8", errors="ignore")

    # 2. Try Gemini LLM first if configured
    result = analyze_with_gemini(text, job_role)

    # 3. Fallback to smart NLP heuristics
    if not result:
        result = analyze_with_nlp(text, job_role)

    return result


def save_resume_analysis(
    user_id: str, filename: str, job_role: str, analysis: dict
) -> dict:
    """Persists analysis result document to MongoDB."""
    collection = get_resume_analyses_collection()
    now = datetime.now(timezone.utc)

    doc = {
        "user_id": user_id,
        "filename": filename,
        "job_role": job_role,
        "overall_score": analysis["overall_score"],
        "ats_score": analysis["ats_score"],
        "detected_skills": analysis["detected_skills"],
        "missing_skills": analysis["missing_skills"],
        "strengths": analysis["strengths"],
        "weaknesses": analysis["weaknesses"],
        "job_match": analysis["job_match"],
        "recommendations": analysis["recommendations"],
        "extracted_summary": analysis.get("extracted_summary", ""),
        "created_at": now,
    }

    result = collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc["_id"] = str(result.inserted_id)
    return doc


def get_user_resume_history(user_id: str) -> List[dict]:
    """Retrieves all past resume analyses for a user."""
    collection = get_resume_analyses_collection()
    cursor = collection.find({"user_id": user_id}).sort("created_at", -1)

    history = []
    for doc in cursor:
        history.append({
            "id": str(doc["_id"]),
            "filename": doc.get("filename", "resume.pdf"),
            "job_role": doc.get("job_role", "Software Engineer"),
            "overall_score": doc.get("overall_score", 0),
            "ats_score": doc.get("ats_score", 0),
            "created_at": doc.get("created_at", datetime.now(timezone.utc)),
        })
    return history


def get_resume_analysis_by_id(user_id: str, analysis_id: str) -> Optional[dict]:
    """Retrieves a single complete analysis document by id."""
    collection = get_resume_analyses_collection()
    try:
        oid = ObjectId(analysis_id)
    except Exception:
        return None

    doc = collection.find_one({"_id": oid, "user_id": user_id})
    if not doc:
        return None

    doc["id"] = str(doc["_id"])
    return doc


def delete_resume_analysis(user_id: str, analysis_id: str) -> bool:
    """Deletes an analysis document by id."""
    collection = get_resume_analyses_collection()
    try:
        oid = ObjectId(analysis_id)
    except Exception:
        return False

    result = collection.delete_one({"_id": oid, "user_id": user_id})
    return result.deleted_count > 0
