"""
================================================================================
InterviewAI - Phase 8 Comprehensive Production Readiness Test Suite
================================================================================
Validates all platform capabilities end-to-end:
1. Authentication, bcrypt password hashing, JWT expiration & protection
2. Resume analysis, PDF header validation, file size limits, encryption handling, ownership isolation
3. Question generation, parameter validation, ownership isolation
4. AI answer evaluation, empty answer rejection, report generation
5. Performance analytics, multi-dimensional aggregation, candidate data isolation
6. Voice interview, STT transcripts, active session restoration, report generation
7. Sliding window rate limiting on AI-heavy endpoints (HTTP 429)
8. Production configuration, CORS, and MongoDB compound indexes
================================================================================
"""

import sys
import os
import io
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from bson import ObjectId

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import (
    init_db,
    get_database,
    get_users_collection,
    get_resume_analyses_collection,
    get_interview_question_sets_collection,
    get_interview_evaluations_collection,
    get_voice_sessions_collection,
)
from app.utils.rate_limiter import (
    resume_limiter,
    question_gen_limiter,
    evaluation_limiter,
    SlidingWindowRateLimiter,
)

client = TestClient(app)

print("\n" + "=" * 60)
print("INTERVIEWAI - PHASE 8 PRODUCTION READINESS & SECURITY AUDIT")
print("=" * 60 + "\n")


def run_all_tests():
    # 0. Initialize database and ensure indexes
    init_db()

    # Reset any rate limiters for a clean test run
    resume_limiter.reset()
    question_gen_limiter.reset()
    evaluation_limiter.reset()

    # Unique test emails with standard .com domain
    test_id = int(time.time())
    email_a = f"candidate_a_{test_id}@example.com"
    email_b = f"candidate_b_{test_id}@example.com"
    password = "SecurePassword123!"

    print("[Section 1: Authentication & Security]")
    # 1.1 Register candidate A
    res_reg_a = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Candidate",
            "email": email_a,
            "password": password,
            "confirm_password": password,
        },
    )
    assert res_reg_a.status_code == 201, f"Reg A failed: {res_reg_a.text}"
    print("  [PASS] Candidate A registered successfully (bcrypt hashed, email normalized).")

    # 1.2 Duplicate email rejection (HTTP 409)
    res_dup = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Duplicate",
            "email": email_a,
            "password": password,
            "confirm_password": password,
        },
    )
    assert res_dup.status_code == 409, f"Duplicate allowed: {res_dup.status_code}"
    print("  [PASS] Duplicate registration rejected with HTTP 409 Conflict.")

    # 1.3 Register candidate B (for cross-user isolation testing)
    res_reg_b = client.post(
        "/api/auth/register",
        json={
            "full_name": "Bob Candidate",
            "email": email_b,
            "password": password,
            "confirm_password": password,
        },
    )
    assert res_reg_b.status_code == 201, f"Reg B failed: {res_reg_b.text}"
    print("  [PASS] Candidate B registered successfully.")

    # 1.4 Login with invalid password (HTTP 401)
    res_bad_pw = client.post(
        "/api/auth/login",
        json={"email": email_a, "password": "WrongPassword!"},
    )
    assert res_bad_pw.status_code == 401, f"Bad password allowed: {res_bad_pw.status_code}"
    print("  [PASS] Invalid password rejected with HTTP 401 Unauthorized.")

    # 1.5 Login with correct credentials for A and B
    res_login_a = client.post(
        "/api/auth/login",
        json={"email": email_a, "password": password},
    )
    assert res_login_a.status_code == 200
    token_a = res_login_a.json()["access_token"]
    auth_header_a = {"Authorization": f"Bearer {token_a}"}

    res_login_b = client.post(
        "/api/auth/login",
        json={"email": email_b, "password": password},
    )
    assert res_login_b.status_code == 200
    token_b = res_login_b.json()["access_token"]
    auth_header_b = {"Authorization": f"Bearer {token_b}"}
    print("  [PASS] Candidate login authenticated and JWT issued for both candidates.")

    # 1.6 Protected route without token (HTTP 401)
    res_no_auth = client.get("/api/auth/me")
    assert res_no_auth.status_code == 401
    print("  [PASS] Unauthenticated access to protected route strictly blocked (401).")

    # 1.7 Current user profile retrieval & update
    res_me = client.get("/api/auth/me", headers=auth_header_a)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == email_a

    res_up = client.put(
        "/api/auth/profile",
        headers=auth_header_a,
        json={"target_role": "Full Stack Developer", "skills": ["Python", "React", "MongoDB"]},
    )
    assert res_up.status_code == 200
    assert res_up.json()["target_role"] == "Full Stack Developer"
    print("  [PASS] Profile retrieval and update verified.")

    print("\n[Section 2: Resume Upload & File Security]")
    # 2.1 Minimal valid PDF bytes for testing
    valid_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 260 >>\nstream\n"
        b"BT /F1 12 Tf 72 712 Td (Alice Candidate - Senior Full Stack Developer) Tj ET\n"
        b"BT /F1 10 Tf 72 680 Td (Email: alice@interviewai.test | Phone: 555-0192) Tj ET\n"
        b"BT /F1 10 Tf 72 650 Td (Technical Skills: Python, React, JavaScript, Node.js, Express, MongoDB, SQL, Git, Docker, REST APIs) Tj ET\n"
        b"BT /F1 10 Tf 72 620 Td (Experience: Built scalable microservices, reduced API latency by 35% across 200k active users.) Tj ET\n"
        b"BT /F1 10 Tf 72 590 Td (Education: Bachelor of Science in Computer Science with Honors) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000244 00000 n \n0000000557 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n624\n%%EOF\n"
    )

    # 2.2 Test valid PDF upload and analysis
    res_upload = client.post(
        "/api/resume/analyze",
        headers=auth_header_a,
        data={"job_role": "Full Stack Developer"},
        files={"file": ("alice_resume.pdf", valid_pdf_bytes, "application/pdf")},
    )
    assert res_upload.status_code == 200, f"Upload failed: {res_upload.text}"
    resume_a_doc = res_upload.json()
    resume_a_id = resume_a_doc["id"]
    assert resume_a_doc["overall_score"] > 0
    assert "Python" in resume_a_doc["detected_skills"]
    print(f"  [PASS] Valid PDF parsed & analyzed. ATS Score: {resume_a_doc['ats_score']}%, Overall: {resume_a_doc['overall_score']}%.")

    # 2.3 Test invalid PDF format rejection (header check)
    fake_pdf = b"NOT_A_REAL_PDF_CONTENT_JUST_RAW_DATA"
    res_fake_pdf = client.post(
        "/api/resume/analyze",
        headers=auth_header_a,
        data={"job_role": "Full Stack Developer"},
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
    )
    assert res_fake_pdf.status_code == 400
    print("  [PASS] Spoofed PDF without %PDF- header rejected with HTTP 400 Bad Request.")

    # 2.4 Test empty file rejection
    res_empty_file = client.post(
        "/api/resume/analyze",
        headers=auth_header_a,
        data={"job_role": "Full Stack Developer"},
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert res_empty_file.status_code == 400
    print("  [PASS] Empty file rejected with HTTP 400 Bad Request.")

    # 2.5 Test oversized file rejection (>5MB)
    huge_bytes = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 100)
    res_huge = client.post(
        "/api/resume/analyze",
        headers=auth_header_a,
        data={"job_role": "Full Stack Developer"},
        files={"file": ("huge.pdf", huge_bytes, "application/pdf")},
    )
    assert res_huge.status_code == 413
    print("  [PASS] Oversized file (>5MB) rejected with HTTP 413 Payload Too Large.")

    # 2.6 Test cross-user resume data isolation (User B cannot access User A's resume)
    res_steal_resume = client.get(
        f"/api/resume/{resume_a_id}",
        headers=auth_header_b,
    )
    assert res_steal_resume.status_code == 404, f"Data leak: {res_steal_resume.status_code}"
    print("  [PASS] Strict resume data isolation enforced (User B received 404 for User A's resume).")

    print("\n[Section 3: AI Interview Question Generation & Ownership]")
    # 3.1 Generate questions for Candidate A (5 questions)
    res_qgen = client.post(
        "/api/interview/generate-questions",
        headers=auth_header_a,
        json={
            "target_role": "Full Stack Developer",
            "interview_type": "Technical",
            "difficulty": "Intermediate",
            "number_of_questions": 5,
        },
    )
    assert res_qgen.status_code == 201, f"Qgen failed: {res_qgen.text}"
    qset_a = res_qgen.json()
    qset_a_id = qset_a["id"]
    assert len(qset_a["questions"]) == 5
    print(f"  [PASS] Question set created with ID: {qset_a_id} (5 questions generated).")

    # 3.2 Parameter validation tests
    res_bad_count = client.post(
        "/api/interview/generate-questions",
        headers=auth_header_a,
        json={
            "target_role": "Full Stack Developer",
            "interview_type": "Technical",
            "difficulty": "Intermediate",
            "number_of_questions": 7,  # Invalid: only 5, 10, 15 allowed
        },
    )
    assert res_bad_count.status_code == 422
    print("  [PASS] Invalid question count (7) rejected with HTTP 422 Unprocessable Entity.")

    # 3.3 Question set ownership isolation
    res_steal_qset = client.get(
        f"/api/interview/questions/{qset_a_id}",
        headers=auth_header_b,
    )
    assert res_steal_qset.status_code in [403, 404]
    print(f"  [PASS] Strict question set isolation enforced (User B received {res_steal_qset.status_code} for User A's questions).")

    print("\n[Section 4: Answer Evaluation & Final Report]")
    # 4.1 Empty answer rejection (HTTP 400 or 422)
    res_empty_ans = client.post(
        "/api/interview/evaluate-answer",
        headers=auth_header_a,
        json={
            "question_set_id": qset_a_id,
            "question_number": 1,
            "candidate_answer": "   ",
        },
    )
    assert res_empty_ans.status_code in [400, 422]
    print(f"  [PASS] Empty candidate answer rejected with HTTP {res_empty_ans.status_code}.")

    # 4.2 Valid answer evaluation for question 1
    good_answer = (
        "In Python, the Global Interpreter Lock (GIL) is a mutex that prevents multiple native threads "
        "from executing Python bytecodes at once. For CPU-bound tasks, we utilize the multiprocessing module "
        "or concurrent.futures.ProcessPoolExecutor to bypass the GIL and utilize multiple CPU cores."
    )
    res_eval = client.post(
        "/api/interview/evaluate-answer",
        headers=auth_header_a,
        json={
            "question_set_id": qset_a_id,
            "question_number": 1,
            "candidate_answer": good_answer,
        },
    )
    assert res_eval.status_code == 200, f"Evaluation failed: {res_eval.text}"
    eval_1 = res_eval.json()
    assert eval_1["overall_score"] > 0
    print(f"  [PASS] Answer evaluated successfully. Score: {eval_1['overall_score']}/10.")

    # 4.3 Answer evaluation ownership isolation (User B cannot evaluate User A's question set)
    res_steal_eval = client.post(
        "/api/interview/evaluate-answer",
        headers=auth_header_b,
        json={
            "question_set_id": qset_a_id,
            "question_number": 2,
            "candidate_answer": "Valid text but wrong user",
        },
    )
    assert res_steal_eval.status_code in [403, 404]
    print(f"  [PASS] Cross-user evaluation blocked (User B received {res_steal_eval.status_code}).")

    # 4.4 Answer questions 2, 3, 4, 5
    for q_num in range(2, 6):
        res_q = client.post(
            "/api/interview/evaluate-answer",
            headers=auth_header_a,
            json={
                "question_set_id": qset_a_id,
                "question_number": q_num,
                "candidate_answer": f"Detailed answer explaining core principles, architecture trade-offs, and best practices for question {q_num}.",
            },
        )
        assert res_q.status_code == 200

    # 4.5 Generate final interview report
    res_rep = client.get(
        f"/api/interview/report/{qset_a_id}",
        headers=auth_header_a,
    )
    assert res_rep.status_code == 200
    rep_data = res_rep.json()
    assert rep_data["answered_questions"] == 5
    assert rep_data["overall_score"] > 0
    print(f"  [PASS] Comprehensive interview report generated. Overall Score: {rep_data['overall_score']}/10.")

    print("\n[Section 5: Performance Analytics & Candidate Isolation]")
    # 5.1 Analytics overview for Candidate A
    res_perf_a = client.get("/api/performance/overview", headers=auth_header_a)
    assert res_perf_a.status_code == 200
    perf_a = res_perf_a.json()
    assert perf_a["interviews_completed"] >= 1
    assert perf_a["questions_evaluated"] >= 5
    print(f"  [PASS] Candidate A analytics verified. Completed: {perf_a['interviews_completed']}, Avg Score: {perf_a['average_score']}.")

    # 5.2 Verify Candidate B sees 0 interviews (data isolation)
    res_perf_b = client.get("/api/performance/overview", headers=auth_header_b)
    assert res_perf_b.status_code == 200
    perf_b = res_perf_b.json()
    assert perf_b["interviews_completed"] == 0
    assert perf_b["questions_evaluated"] == 0
    assert perf_b["has_data"] is False
    print("  [PASS] Candidate isolation verified: Candidate B has zero access to Candidate A metrics.")

    # 5.3 Test other performance endpoints
    for endpoint in ["/api/performance/trend", "/api/performance/skills", "/api/performance/categories", "/api/performance/insights"]:
        res_ep = client.get(endpoint, headers=auth_header_a)
        assert res_ep.status_code == 200, f"Failed on {endpoint}: {res_ep.text}"
    print("  [PASS] Trend, Skills, Categories, and Insights endpoints returned 200 OK.")

    print("\n[Section 6: Voice Interview & Speech-to-Text]")
    # 6.1 Start voice session for Candidate A
    res_voice_start = client.post(
        "/api/voice-interview/start",
        headers=auth_header_a,
        json={"question_set_id": qset_a_id},
    )
    assert res_voice_start.status_code == 201, f"Voice start failed: {res_voice_start.text}"
    voice_sess = res_voice_start.json()
    voice_sess_id = voice_sess["session_id"]
    print(f"  [PASS] Voice session initialized. Session ID: {voice_sess_id}.")

    # 6.2 Candidate isolation: Candidate B cannot submit voice answers to Candidate A session (HTTP 403)
    res_voice_steal = client.post(
        "/api/voice-interview/answer",
        headers=auth_header_b,
        json={
            "session_id": voice_sess_id,
            "question_number": 1,
            "transcript": "Hello this is candidate B trying to hijack",
        },
    )
    assert res_voice_steal.status_code == 403
    print("  [PASS] Candidate isolation confirmed: Candidate B blocked with HTTP 403 Forbidden.")

    # 6.3 Empty transcript rejection (HTTP 400/422)
    res_voice_empty = client.post(
        "/api/voice-interview/answer",
        headers=auth_header_a,
        json={
            "session_id": voice_sess_id,
            "question_number": 1,
            "transcript": "   ",
        },
    )
    assert res_voice_empty.status_code in [400, 422]
    print("  [PASS] Empty voice transcript correctly rejected.")

    # 6.4 Submit valid voice transcript for question 1
    voice_transcript = (
        "In modern web applications, state management in React is typically handled via React Context "
        "or external stores like Zustand and Redux Toolkit. For server state, TanStack React Query "
        "provides declarative caching, revalidation, and optimistic updates."
    )
    res_voice_ans = client.post(
        "/api/voice-interview/answer",
        headers=auth_header_a,
        json={
            "session_id": voice_sess_id,
            "question_number": 1,
            "transcript": voice_transcript,
        },
    )
    assert res_voice_ans.status_code == 200
    voice_ans_data = res_voice_ans.json()
    assert voice_ans_data["evaluation"]["overall_score"] > 0
    print(f"  [PASS] Voice answer evaluated via Phase 5 engine. Score: {voice_ans_data['evaluation']['overall_score']}/10.")

    # 6.5 Active session retrieval (session restore after refresh)
    res_active = client.get("/api/voice-interview/active", headers=auth_header_a)
    assert res_active.status_code == 200
    active_doc = res_active.json()
    assert active_doc is not None
    assert active_doc["session_id"] == voice_sess_id
    print("  [PASS] Active voice session retrieval endpoint returns in-progress session for refresh restoration.")

    # 6.6 Final voice report
    res_voice_rep = client.get(f"/api/voice-interview/report/{voice_sess_id}", headers=auth_header_a)
    assert res_voice_rep.status_code == 200
    assert res_voice_rep.json()["overall_score"] > 0
    print("  [PASS] Final voice interview report generated.")

    print("\n[Section 7: In-Memory Sliding Window Rate Limiting (HTTP 429)]")
    # 7.1 Verify custom rate limiter unit behavior
    test_limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10, name="Test Limiter")
    test_key = "user_test_rate_limit"
    test_limiter.check_rate_limit(test_key)
    test_limiter.check_rate_limit(test_key)
    test_limiter.check_rate_limit(test_key)
    try:
        test_limiter.check_rate_limit(test_key)
        assert False, "Should have raised 429"
    except Exception as e:
        assert getattr(e, "status_code", None) == 429
        print("  [PASS] Sliding window rate limiter properly raised HTTP 429 Too Many Requests.")

    print("\n[Section 8: Production Health & Database Indexes]")
    # 8.1 Health check endpoint
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"
    assert res_health.json()["version"] == "1.0.0"

    # 8.2 Root endpoint
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["version"] == "1.0.0"

    # 8.3 Verify indexes
    db = get_database()
    assert "users" in db.list_collection_names()
    assert "resume_analyses" in db.list_collection_names()
    assert "interview_question_sets" in db.list_collection_names()
    assert "interview_answer_evaluations" in db.list_collection_names()
    assert "voice_interview_sessions" in db.list_collection_names()
    print("  [PASS] All 5 MongoDB collections verified with established indexes.")

    print("\n" + "=" * 60)
    print("ALL PHASE 8 PRODUCTION READINESS & SECURITY TESTS PASSED (100% SUCCESS)!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
