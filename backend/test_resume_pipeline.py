import io
import sys
import os
from pypdf import PdfReader
from bson import ObjectId
from fastapi.testclient import TestClient

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import init_db, get_database, get_resume_analyses_collection

client = TestClient(app)

# 1. Create a valid text PDF
def make_pdf():
    lines = [
        "Alex Rivera",
        "Email: alex.rivera@example.com | Phone: (555) 123-4567 | github.com/alexrivera",
        "Target Role: Full Stack Developer",
        "PROFESSIONAL SUMMARY",
        "Full Stack Engineer with 4 years experience building web applications using React, Node.js, and Python.",
        "EXPERIENCE",
        "Senior Software Engineer at GlobalTech (2022 - Present)",
        "- Architected high-scale microservices using Node.js, Express, and PostgreSQL, reducing latency by 45%.",
        "- Developed responsive web applications using React, TypeScript, and Tailwind CSS serving 250k+ active users.",
        "- Automated deployment pipelines using Docker, GitHub Actions, and AWS.",
        "PROJECTS",
        "AI Platform",
        "- Engineered full-stack mock interview application using FastAPI, MongoDB, and Python.",
        "- Implemented secure JWT authentication and optimized database queries by 40%.",
        "EDUCATION",
        "Stanford University - B.S. in Computer Science (2021)",
        "SKILLS",
        "JavaScript, TypeScript, React, Node.js, Express, Python, FastAPI, MongoDB, PostgreSQL, Docker, Git, REST APIs"
    ]
    
    stream = "BT /F1 12 Tf 50 750 Td 15 TL "
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream += f"({escaped}) ' "
    stream += "ET"
    stream_bytes = stream.encode("latin1")
    stream_len = len(stream_bytes)
    
    parts = [
        b"%PDF-1.4\n",
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        b"4 0 obj\n<< /Length " + str(stream_len).encode("ascii") + b" >>\nstream\n",
        stream_bytes,
        b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000244 00000 n \n0000000557 00000 n \n",
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n624\n%%EOF\n"
    ]
    return b"".join(parts)


def run_tests():
    init_db()

    print("=== Step 1: User Login & Setup ===")
    email = "alex.rivera@example.com"
    password = "Password123!"

    # Ensure user exists
    client.post("/api/auth/register", json={
        "full_name": "Alex Rivera",
        "email": email,
        "password": password,
        "confirm_password": password,
    })

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("User authenticated successfully via JWT.")

    print("\n=== Step 2: Generate PDF Resume ===")
    pdf_data = make_pdf()
    reader = PdfReader(io.BytesIO(pdf_data))
    extracted = reader.pages[0].extract_text()
    assert len(extracted) > 50, "PDF extraction produced insufficient text"
    print(f"Generated PDF with {len(extracted)} characters of text.")

    print("\n=== Step 3: Call POST /api/resume/analyze ===")
    files = {"file": ("Alex_Rivera_Resume.pdf", pdf_data, "application/pdf")}
    data = {"job_role": "Full Stack Developer"}
    res = client.post("/api/resume/analyze", headers=headers, files=files, data=data)
    assert res.status_code == 200, f"Analyze failed: {res.text}"
    result = res.json()
    print("Analyze response status: 200 OK")
    print(f"Overall Score: {result['overall_score']}/100")
    print(f"ATS Score: {result['ats_score']}%")
    print(f"Detected Skills ({len(result['detected_skills'])}): {result['detected_skills']}")
    print(f"Missing Skills ({len(result['missing_skills'])}): {result['missing_skills']}")
    print(f"Strengths ({len(result['strengths'])}): {result['strengths']}")
    print(f"Weaknesses ({len(result['weaknesses'])}): {result['weaknesses']}")
    print(f"Job Match: {result['job_match']['percentage']}% ({result['job_match']['match_level']}) - {result['job_match']['summary']}")
    print(f"Recommendations ({len(result['recommendations'])}): {result['recommendations']}")

    # Verify all expected keys exist
    for key in ["overall_score", "ats_score", "detected_skills", "missing_skills", "strengths", "weaknesses", "job_match", "recommendations"]:
        assert key in result, f"Missing key {key} in response"

    analysis_id = result["id"]

    print("\n=== Step 4: Verify MongoDB Persistence ===")
    resumes_col = get_resume_analyses_collection()
    doc = resumes_col.find_one({"_id": ObjectId(analysis_id)})
    assert doc is not None, "Document not found in MongoDB resume_analyses collection"
    print(f"MongoDB record verified: ID={doc['_id']}, User={doc['user_id']}, File={doc['filename']}")

    print("\n=== Step 5: Test GET /api/resume/history ===")
    hist_res = client.get("/api/resume/history", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 1, "History returned empty list"
    assert history[0]["id"] == analysis_id, "Latest history item does not match current analysis"
    print(f"History retrieved: {len(history)} item(s), most recent is {history[0]['filename']} ({history[0]['overall_score']}/100)")

    print("\n=== Step 6: Test GET /api/resume/{id} ===")
    detail_res = client.get(f"/api/resume/{analysis_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == analysis_id
    assert detail["overall_score"] == result["overall_score"]
    print("Detailed report retrieved successfully by ID.")

    print("\n==========================================")
    print("ALL RESUME PIPELINE WORKFLOW STEPS VERIFIED AND PASSED!")
    print("==========================================")


if __name__ == "__main__":
    run_tests()
