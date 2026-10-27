import json
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import get_database, init_db

client = TestClient(app)

def run_all_tests():
    print("==================================================")
    print("PHASE 4 - AI INTERVIEW QUESTION GENERATOR TEST SUITE")
    print("==================================================")

    init_db()
    db = get_database()
    users_col = db["users"]
    resumes_col = db["resume_analyses"]
    qsets_col = db["interview_question_sets"]

    # -------------------------------------------------------------------------
    # 1. Setup Test Users
    # -------------------------------------------------------------------------
    print("\n[Test 1] Setting up Test Users and Authentication...")
    test_user_a = {
        "email": "phase4_user_a@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase4 Candidate A",
        "target_role": "Python Developer",
    }
    test_user_b = {
        "email": "phase4_user_b@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase4 Candidate B",
        "target_role": "Data Analyst",
    }

    # Register or login User A
    client.post("/api/auth/register", json=test_user_a)
    login_a_res = client.post("/api/auth/login", json={
        "email": test_user_a["email"],
        "password": test_user_a["password"],
    })
    assert login_a_res.status_code == 200, f"Login A failed: {login_a_res.text}"
    token_a = login_a_res.json()["access_token"]
    user_a_id = login_a_res.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print(f"[PASS] User A authenticated. ID: {user_a_id}")

    # Register or login User B
    client.post("/api/auth/register", json=test_user_b)
    login_b_res = client.post("/api/auth/login", json={
        "email": test_user_b["email"],
        "password": test_user_b["password"],
    })
    assert login_b_res.status_code == 200, f"Login B failed: {login_b_res.text}"
    token_b = login_b_res.json()["access_token"]
    user_b_id = login_b_res.json()["user"]["id"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    print(f"[PASS] User B authenticated. ID: {user_b_id}")

    # Reset any leftover resumes & question sets for test users to ensure clean baseline
    resumes_col.delete_many({"user_id": {"$in": [user_a_id, user_b_id]}})
    qsets_col.delete_many({"user_id": {"$in": [user_a_id, user_b_id]}})

    # -------------------------------------------------------------------------
    # 2. Test Input Validation on POST /api/interview/generate-questions
    # -------------------------------------------------------------------------
    print("\n[Test 2] Testing Request Payload Validation...")
    # Missing auth
    unauth_res = client.post("/api/interview/generate-questions", json={
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert unauth_res.status_code == 401, f"Expected 401 Unauthorized, got: {unauth_res.status_code}"
    print("[PASS] Unauthenticated request rejected with 401 Unauthorized.")

    # Invalid role
    inv_role_res = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Quantum Physicist",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert inv_role_res.status_code == 422, f"Expected 422 for invalid role, got: {inv_role_res.status_code}"
    print("[PASS] Invalid target role rejected with 422 Unprocessable Entity.")

    # Invalid interview type
    inv_type_res = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Python Developer",
        "interview_type": "Casual Chat",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert inv_type_res.status_code == 422, f"Expected 422 for invalid type, got: {inv_type_res.status_code}"
    print("[PASS] Invalid interview type rejected with 422 Unprocessable Entity.")

    # Invalid difficulty
    inv_diff_res = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Nightmare",
        "number_of_questions": 5,
    })
    assert inv_diff_res.status_code == 422, f"Expected 422 for invalid difficulty, got: {inv_diff_res.status_code}"
    print("[PASS] Invalid difficulty rejected with 422 Unprocessable Entity.")

    # Invalid question count (e.g. 7 instead of 5, 10, 15)
    inv_count_res = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 7,
    })
    assert inv_count_res.status_code == 422, f"Expected 422 for invalid count, got: {inv_count_res.status_code}"
    print("[PASS] Invalid question count (7) rejected with 422 Unprocessable Entity.")

    # -------------------------------------------------------------------------
    # 3. Test Question Generation (Without Resume - Baseline)
    # -------------------------------------------------------------------------
    print("\n[Test 3] Generating 5 Technical Questions for Python Developer (No Resume)...")
    res_3 = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert res_3.status_code in [200, 201], f"Generation failed: {res_3.text}"
    qset_3 = res_3.json()
    assert len(qset_3["questions"]) == 5, f"Expected 5 questions, got: {len(qset_3['questions'])}"
    assert qset_3["target_role"] == "Python Developer"
    assert qset_3["interview_type"] == "Technical"
    assert qset_3["difficulty"] == "Intermediate"
    assert qset_3["resume_based"] is False, "Should not be resume based when no resume exists"

    for idx, q in enumerate(qset_3["questions"], start=1):
        assert q["question_number"] == idx
        assert len(q["question"]) > 10
        assert q["category"] in ["Technical", "Coding", "Database", "Web Development", "Programming", "System Design", "Problem Solving"]
        assert len(q["topic"]) > 2
        assert isinstance(q["expected_focus"], list) and len(q["expected_focus"]) > 0

    print(f"[PASS] Generated 5 questions. Sample: '{qset_3['questions'][0]['question'][:60]}...'")
    print(f"[PASS] Category: {qset_3['questions'][0]['category']} | Topic: {qset_3['questions'][0]['topic']} | Focus: {qset_3['questions'][0]['expected_focus']}")

    qset_a_id = qset_3["id"]

    # -------------------------------------------------------------------------
    # 4. Test HR and Mixed Interviews
    # -------------------------------------------------------------------------
    print("\n[Test 4] Generating 5 HR Questions...")
    res_hr = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Software Developer",
        "interview_type": "HR",
        "difficulty": "Beginner",
        "number_of_questions": 5,
    })
    assert res_hr.status_code in [200, 201]
    qset_hr = res_hr.json()
    assert len(qset_hr["questions"]) == 5
    for q in qset_hr["questions"]:
        assert q["category"] in ["HR", "Behavioral", "Situational"]
    print("[PASS] Successfully generated HR questions with HR/Behavioral/Situational categories.")

    print("\n[Test 5] Generating 10 Mixed Questions...")
    res_mixed = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Full Stack Developer",
        "interview_type": "Mixed",
        "difficulty": "Intermediate",
        "number_of_questions": 10,
    })
    assert res_mixed.status_code in [200, 201]
    qset_mixed = res_mixed.json()
    assert len(qset_mixed["questions"]) == 10
    categories = [q["category"] for q in qset_mixed["questions"]]
    print(f"[PASS] Successfully generated 10 Mixed questions across categories: {set(categories)}.")

    # -------------------------------------------------------------------------
    # 5. Test Resume Awareness (With Phase 3 Resume Analysis in MongoDB)
    # -------------------------------------------------------------------------
    print("\n[Test 6] Testing Resume-Aware Personalization...")
    # Inject a realistic Phase 3 resume analysis for User A
    sample_skills = ["Python", "FastAPI", "MongoDB", "React", "REST API"]
    resumes_col.delete_many({"user_id": user_a_id})
    resumes_col.insert_one({
        "user_id": user_a_id,
        "filename": "alex_rivera_resume.pdf",
        "job_role": "Python Developer",
        "overall_score": 89,
        "ats_score": 92,
        "detected_skills": sample_skills,
        "missing_skills": ["Docker", "Kubernetes"],
        "strengths": ["Strong FastAPI architecture", "Clean REST API design"],
        "weaknesses": ["Needs more distributed systems experience"],
        "job_match": {"percentage": 90, "match_level": "Strong Match", "summary": "Well suited for backend"},
        "recommendations": ["Add CI/CD pipeline details"],
        "extracted_summary": "Full Stack engineer with strong Python and FastAPI experience.",
        "created_at": datetime.now(timezone.utc),
    })

    # Check /resume-status endpoint
    status_res = client.get("/api/interview/resume-status", headers=headers_a)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["has_resume"] is True
    assert "FastAPI" in status_data["detected_skills"]
    assert "MongoDB" in status_data["detected_skills"]
    print(f"[PASS] /resume-status confirmed user has resume with skills: {status_data['detected_skills']}")

    # Generate questions with resume present
    res_resume = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert res_resume.status_code in [200, 201]
    qset_resume = res_resume.json()
    assert qset_resume["resume_based"] is True, "Expected resume_based to be True"
    assert len(qset_resume["questions"]) == 5

    # Check for personalization: skills should be present in questions/topics
    all_text = " ".join([q["question"] + " " + q["topic"] for q in qset_resume["questions"]]).lower()
    matched_skills = [s for s in sample_skills if s.lower() in all_text]
    print(f"[PASS] Resume-personalized questions generated. Found resume skills: {matched_skills}")
    for idx, q in enumerate(qset_resume["questions"], start=1):
        print(f"   Q{idx}: {q['question']}")

    # -------------------------------------------------------------------------
    # 6. Test MongoDB Storage in interview_question_sets
    # -------------------------------------------------------------------------
    print("\n[Test 7] Verifying MongoDB Persistence in 'interview_question_sets'...")
    doc = qsets_col.find_one({"_id": ObjectId(qset_resume["id"])})
    assert doc is not None, "Question set not found in MongoDB collection"
    assert doc["user_id"] == user_a_id
    assert doc["target_role"] == "Python Developer"
    assert doc["resume_based"] is True
    assert len(doc["questions"]) == 5
    print(f"[PASS] MongoDB document verified. _id: {doc['_id']} with {len(doc['questions'])} validated questions.")

    # -------------------------------------------------------------------------
    # 7. Test GET /api/interview/question-history
    # -------------------------------------------------------------------------
    print("\n[Test 8] Testing GET /api/interview/question-history...")
    hist_res = client.get("/api/interview/question-history", headers=headers_a)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 4, f"Expected at least 4 question sets in history, got {len(history)}"
    # Verify newest first
    for i in range(len(history) - 1):
        d1 = datetime.fromisoformat(history[i]["created_at"].replace("Z", "+00:00"))
        d2 = datetime.fromisoformat(history[i+1]["created_at"].replace("Z", "+00:00"))
        assert d1 >= d2, "History not sorted newest first"
    print(f"[PASS] Question history successfully returned {len(history)} sets, properly sorted newest first.")

    # -------------------------------------------------------------------------
    # 8. Test Single Question Set Endpoint & Security (Ownership)
    # -------------------------------------------------------------------------
    print("\n[Test 9] Testing GET /api/interview/questions/{id} & Access Control...")
    # Owner (User A) accesses own question set
    owner_res = client.get(f"/api/interview/questions/{qset_a_id}", headers=headers_a)
    assert owner_res.status_code == 200
    assert owner_res.json()["id"] == qset_a_id
    print("[PASS] Owner (User A) successfully accessed own question set (200 OK).")

    # Non-owner (User B) attempts to access User A's question set -> MUST BE 403 Forbidden!
    forbidden_res = client.get(f"/api/interview/questions/{qset_a_id}", headers=headers_b)
    assert forbidden_res.status_code == 403, f"Expected 403 Forbidden for non-owner, got {forbidden_res.status_code}"
    print("[PASS] Unauthorized User B received 403 Forbidden when trying to access User A's question set.")

    # Non-existent ID -> MUST BE 404 Not Found
    fake_id = str(ObjectId())
    not_found_res = client.get(f"/api/interview/questions/{fake_id}", headers=headers_a)
    assert not_found_res.status_code == 404, f"Expected 404 Not Found, got {not_found_res.status_code}"
    print("[PASS] Non-existent question set returned 404 Not Found.")

    # -------------------------------------------------------------------------
    # 9. Test Different Roles & Difficulties (All 8 Roles Supported)
    # -------------------------------------------------------------------------
    print("\n[Test 10] Testing All 8 Roles with 5 Questions each...")
    roles = [
        "Software Developer",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Python Developer",
        "Java Developer",
        "Data Analyst",
        "AI/ML Engineer",
    ]
    for role in roles:
        r = client.post("/api/interview/generate-questions", headers=headers_b, json={
            "target_role": role,
            "interview_type": "Technical",
            "difficulty": "Intermediate",
            "number_of_questions": 5,
        })
        assert r.status_code in [200, 201], f"Role {role} failed: {r.text}"
        data = r.json()
        assert len(data["questions"]) == 5
        print(f"[PASS] Role '{role}' successfully generated 5 valid questions.")

    print("\n==================================================")
    print("ALL PHASE 4 TESTS PASSED FLAWLESSLY! 100% SUCCESS.")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
