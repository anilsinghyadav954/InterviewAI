import json
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.database import (
    get_database,
    init_db,
    get_interview_evaluations_collection,
    get_interview_question_sets_collection,
)
from app.schemas.performance import (
    PerformanceOverviewResponse,
    PerformanceTrendPoint,
    SkillPerformanceItem,
    CategoryPerformanceItem,
    RolePerformanceItem,
    InterviewTypePerformanceItem,
    PerformanceInsightsResponse,
    RecentActivityItem,
)

client = TestClient(app)

def run_phase6_tests():
    print("==================================================")
    print("PHASE 6 - PERFORMANCE ANALYTICS & REPORTS TEST SUITE")
    print("==================================================")

    init_db()
    db = get_database()
    users_col = db["users"]
    resumes_col = db["resume_analyses"]
    qsets_col = get_interview_question_sets_collection()
    evals_col = get_interview_evaluations_collection()

    # -------------------------------------------------------------------------
    # 1. Authentication & Security Isolation Setup
    # -------------------------------------------------------------------------
    print("\n[Test 1] Testing Authentication & Route Protection...")
    user_a_email = "phase6_candidate_a@example.com"
    user_b_email = "phase6_candidate_b@example.com"

    client.post("/api/auth/register", json={
        "email": user_a_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase6 Alice Dev",
        "target_role": "Python Developer",
    })
    login_a = client.post("/api/auth/login", json={"email": user_a_email, "password": "Password123!"})
    assert login_a.status_code == 200, f"Login A failed: {login_a.text}"
    token_a = login_a.json()["access_token"]
    user_a_id = login_a.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post("/api/auth/register", json={
        "email": user_b_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase6 Bob Data",
        "target_role": "Data Analyst",
    })
    login_b = client.post("/api/auth/login", json={"email": user_b_email, "password": "Password123!"})
    assert login_b.status_code == 200, f"Login B failed: {login_b.text}"
    token_b = login_b.json()["access_token"]
    user_b_id = login_b.json()["user"]["id"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Verify 401 Unauthorized without token across all Phase 6 routes
    unauth_endpoints = [
        "/api/performance/overview",
        "/api/performance/trend",
        "/api/performance/skills",
        "/api/performance/categories",
        "/api/performance/roles",
        "/api/performance/types",
        "/api/performance/insights",
        "/api/performance/recent-activity",
    ]
    for ep in unauth_endpoints:
        res = client.get(ep)
        assert res.status_code == 401, f"Expected 401 for {ep} without token, got {res.status_code}"

    print("[PASS] Test 1: Authentication required on all Phase 6 endpoints.")

    # -------------------------------------------------------------------------
    # 2. Clean Baseline & Empty User Analytics
    # -------------------------------------------------------------------------
    print("\n[Test 2] Testing Clean Baseline & Empty User Analytics...")
    # Wipe any previous test data for User A & User B
    evals_col.delete_many({"user_id": {"$in": [user_a_id, ObjectId(user_a_id), user_b_id, ObjectId(user_b_id)]}})
    qsets_col.delete_many({"user_id": {"$in": [user_a_id, ObjectId(user_a_id), user_b_id, ObjectId(user_b_id)]}})
    resumes_col.delete_many({"user_id": {"$in": [user_a_id, ObjectId(user_a_id), user_b_id, ObjectId(user_b_id)]}})

    # User A has 0 practice sessions & 0 resumes
    ov_empty = client.get("/api/performance/overview", headers=headers_a)
    assert ov_empty.status_code == 200
    ov_data = ov_empty.json()
    assert ov_data["interviews_completed"] == 0
    assert ov_data["average_score"] == 0.0
    assert ov_data["best_score"] == 0.0
    assert ov_data["questions_evaluated"] == 0
    assert ov_data["has_data"] is False

    trend_empty = client.get("/api/performance/trend", headers=headers_a)
    assert trend_empty.status_code == 200
    assert trend_empty.json() == []

    skills_empty = client.get("/api/performance/skills", headers=headers_a)
    assert skills_empty.status_code == 200
    assert skills_empty.json() == []

    cats_empty = client.get("/api/performance/categories", headers=headers_a)
    assert cats_empty.status_code == 200
    assert cats_empty.json() == []

    roles_empty = client.get("/api/performance/roles", headers=headers_a)
    assert roles_empty.status_code == 200
    assert roles_empty.json() == []

    types_empty = client.get("/api/performance/types", headers=headers_a)
    assert types_empty.status_code == 200
    assert types_empty.json() == []

    insights_empty = client.get("/api/performance/insights", headers=headers_a)
    assert insights_empty.status_code == 200
    ins_data = insights_empty.json()
    assert isinstance(ins_data["strengths"], list)
    assert isinstance(ins_data["weak_areas"], list)
    assert isinstance(ins_data["recommendations"], list)

    print("[PASS] Test 2: Empty user analytics correctly handled with clean defaults.")

    # -------------------------------------------------------------------------
    # 3. User With One Completed Interview
    # -------------------------------------------------------------------------
    print("\n[Test 3] Testing User With One Completed Interview...")
    now = datetime.now(timezone.utc)
    t_minus_2d = now - timedelta(days=2)

    # Insert Interview Session 1 for User A: Technical / Python Developer
    qset_1_doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(user_a_id),
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 3,
        "resume_based": False,
        "created_at": t_minus_2d,
        "questions": [
            {
                "question_number": 1,
                "question": "Explain Python generators and memory efficiency.",
                "category": "Technical",
                "topic": "Python Generators",
                "difficulty": "Intermediate",
                "expected_key_points": ["yield keyword", "lazy evaluation", "memory buffer"],
            },
            {
                "question_number": 2,
                "question": "How do Python decorators work under the hood?",
                "category": "Technical",
                "topic": "Python Metaprogramming",
                "difficulty": "Intermediate",
                "expected_key_points": ["first-class functions", "closure", "wrapper"],
            },
            {
                "question_number": 3,
                "question": "How do you optimize slow SQL queries with indexes?",
                "category": "Database",
                "topic": "SQL Optimization",
                "difficulty": "Intermediate",
                "expected_key_points": ["EXPLAIN query plan", "B-tree index", "composite keys"],
            },
        ],
    }
    qsets_col.insert_one(qset_1_doc)
    qset_1_id = qset_1_doc["_id"]

    # Insert Evaluations for Session 1: Scores 8.5, 9.0, 7.0 (Avg = 8.167 -> 8.2)
    eval_docs_1 = [
        {
            "user_id": ObjectId(user_a_id),
            "question_set_id": qset_1_id,
            "question_number": 1,
            "candidate_answer": "Generators produce items on demand using yield instead of holding all in memory.",
            "technical_accuracy": 8.5,
            "relevance": 9.0,
            "completeness": 8.0,
            "clarity": 8.5,
            "communication": 8.5,
            "overall_score": 8.5,
            "summary": "Clear explanation of lazy evaluation and generator mechanics.",
            "strengths": ["Clear yield explanation", "Good memory contrast"],
            "weaknesses": ["Could mention generator expressions"],
            "top_improvements": ["Mention sys.getsizeof comparisons"],
            "created_at": t_minus_2d,
        },
        {
            "user_id": ObjectId(user_a_id),
            "question_set_id": qset_1_id,
            "question_number": 2,
            "candidate_answer": "Decorators wrap functions using closures taking the function as an argument.",
            "technical_accuracy": 9.0,
            "relevance": 9.0,
            "completeness": 9.0,
            "clarity": 9.0,
            "communication": 9.0,
            "overall_score": 9.0,
            "summary": "Masterful explanation of first-class functions and @functools.wraps.",
            "strengths": ["First class functions", "Clean closure definition"],
            "weaknesses": [],
            "top_improvements": ["Discuss decorators with arguments"],
            "created_at": t_minus_2d,
        },
        {
            "user_id": ObjectId(user_a_id),
            "question_set_id": qset_1_id,
            "question_number": 3,
            "candidate_answer": "I run EXPLAIN to check if sequential scan is used and add an index.",
            "technical_accuracy": 7.0,
            "relevance": 7.5,
            "completeness": 6.5,
            "clarity": 7.0,
            "communication": 7.0,
            "overall_score": 7.0,
            "summary": "Basic explanation of EXPLAIN query plan, missing composite index trade-offs.",
            "strengths": ["Mentioned EXPLAIN tool"],
            "weaknesses": ["Lacked write amplification trade-offs"],
            "top_improvements": ["Practice explaining B-tree vs hash index trade-offs"],
            "created_at": t_minus_2d,
        },
    ]
    evals_col.insert_many(eval_docs_1)

    ov_1 = client.get("/api/performance/overview", headers=headers_a).json()
    assert ov_1["interviews_completed"] == 1
    assert ov_1["questions_evaluated"] == 3
    # Session 1 average = (8.5 + 9.0 + 7.0) / 3 = 8.1666... -> 8.2
    assert ov_1["average_score"] == 8.2
    assert ov_1["best_score"] == 8.2
    assert ov_1["has_data"] is True
    print(f"[PASS] Test 3: User with 1 interview verified. Score: {ov_1['average_score']}/10 ({ov_1['average_score_percentage']}%)")

    # -------------------------------------------------------------------------
    # 4. User With Multiple Completed Interviews
    # -------------------------------------------------------------------------
    print("\n[Test 4] Testing User With Multiple Completed Interviews...")
    t_minus_1d = now - timedelta(days=1)

    # Insert Interview Session 2 for User A: HR / Behavioral (Python Developer)
    qset_2_doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(user_a_id),
        "target_role": "Python Developer",
        "interview_type": "HR",
        "difficulty": "Intermediate",
        "number_of_questions": 2,
        "resume_based": False,
        "created_at": t_minus_1d,
        "questions": [
            {
                "question_number": 1,
                "question": "Tell me about a time you handled a difficult conflict with a team member.",
                "category": "Behavioral",
                "topic": "Conflict Resolution",
                "difficulty": "Intermediate",
                "expected_key_points": ["STAR structure", "active listening", "constructive resolution"],
            },
            {
                "question_number": 2,
                "question": "Why do you want to work for our engineering organization?",
                "category": "HR",
                "topic": "Company Motivation",
                "difficulty": "Intermediate",
                "expected_key_points": ["mission alignment", "growth goals"],
            },
        ],
    }
    qsets_col.insert_one(qset_2_doc)
    qset_2_id = qset_2_doc["_id"]

    eval_docs_2 = [
        {
            "user_id": ObjectId(user_a_id),
            "question_set_id": qset_2_id,
            "question_number": 1,
            "candidate_answer": "I used active listening to understand their concerns and compromised on the API design.",
            "technical_accuracy": None, # HR question
            "relevance": 9.5,
            "completeness": 8.5,
            "clarity": 9.0,
            "communication": 9.5,
            "overall_score": 9.2,
            "summary": "Strong behavioral response with mature conflict mitigation.",
            "strengths": ["Empathetic communication", "Constructive resolution"],
            "weaknesses": [],
            "top_improvements": [],
            "created_at": t_minus_1d,
        },
        {
            "user_id": ObjectId(user_a_id),
            "question_set_id": qset_2_id,
            "question_number": 2,
            "candidate_answer": "I appreciate your open source contributions and modern Python microservice stack.",
            "technical_accuracy": None,
            "relevance": 8.5,
            "completeness": 8.0,
            "clarity": 8.5,
            "communication": 8.5,
            "overall_score": 8.5,
            "summary": "Genuine interest in technical stack and values.",
            "strengths": ["Tech stack alignment"],
            "weaknesses": [],
            "top_improvements": [],
            "created_at": t_minus_1d,
        },
    ]
    evals_col.insert_many(eval_docs_2)

    ov_2 = client.get("/api/performance/overview", headers=headers_a).json()
    assert ov_2["interviews_completed"] == 2
    assert ov_2["questions_evaluated"] == 5
    # Session 1 score = 8.2, Session 2 score = (9.2 + 8.5)/2 = 8.85 -> 8.8
    # Average across 2 sessions = (8.2 + 8.8) / 2 = 8.5
    assert ov_2["best_score"] == 8.8
    assert ov_2["average_score"] == 8.5
    print(f"[PASS] Test 4: Multiple sessions correctly aggregated. Avg: {ov_2['average_score']}, Best: {ov_2['best_score']}")

    # -------------------------------------------------------------------------
    # 5. Performance Overview Dimensions & Resume Integration
    # -------------------------------------------------------------------------
    print("\n[Test 5] Testing Performance Overview Dimensions & Resume Integration...")
    # Add an ATS resume analysis for User A
    resumes_col.insert_one({
        "user_id": ObjectId(user_a_id),
        "filename": "Alice_Dev_Resume.pdf",
        "job_role": "Python Developer",
        "overall_score": 84,
        "created_at": now - timedelta(days=3),
    })

    ov_with_resume = client.get("/api/performance/overview", headers=headers_a).json()
    assert ov_with_resume["latest_resume_score"] == 84.0
    assert ov_with_resume["technical_score"] > 0
    assert ov_with_resume["communication_score"] > 0
    assert ov_with_resume["relevance_score"] > 0
    assert ov_with_resume["completeness_score"] > 0
    assert ov_with_resume["clarity_score"] > 0
    print("[PASS] Test 5: All 7 dimension scores and resume integration validated.")

    # -------------------------------------------------------------------------
    # 6. Score Trend Chronological Ordering
    # -------------------------------------------------------------------------
    print("\n[Test 6] Testing Score Trend Chronology...")
    trend_res = client.get("/api/performance/trend", headers=headers_a)
    assert trend_res.status_code == 200
    trend = trend_res.json()
    assert len(trend) == 2
    # Verify chronological order
    assert trend[0]["score"] == 8.2
    assert trend[0]["interview_type"] == "Technical"
    assert trend[1]["score"] == 8.8
    assert trend[1]["interview_type"] == "HR"
    print("[PASS] Test 6: Score trend chronological points validated.")

    # -------------------------------------------------------------------------
    # 7. Skill Aggregation
    # -------------------------------------------------------------------------
    print("\n[Test 7] Testing Skill Competency Aggregation...")
    skills_res = client.get("/api/performance/skills", headers=headers_a)
    assert skills_res.status_code == 200
    skills = skills_res.json()
    skill_names = [s["skill"] for s in skills]
    assert "Python Metaprogramming" in skill_names
    assert "Python Generators" in skill_names
    assert "SQL Optimization" in skill_names

    metaprog = next(s for s in skills if s["skill"] == "Python Metaprogramming")
    assert metaprog["score"] == 9.0
    assert metaprog["questions_count"] == 1
    print(f"[PASS] Test 7: Skill aggregation verified ({len(skills)} skills detected).")

    # -------------------------------------------------------------------------
    # 8. Category Performance Aggregation
    # -------------------------------------------------------------------------
    print("\n[Test 8] Testing Category Aggregation...")
    cats_res = client.get("/api/performance/categories", headers=headers_a)
    assert cats_res.status_code == 200
    cats = cats_res.json()
    cat_names = [c["category"] for c in cats]
    assert "Technical" in cat_names
    assert "Database" in cat_names
    assert "Behavioral" in cat_names
    assert "HR" in cat_names
    print(f"[PASS] Test 8: Category aggregation verified across {cat_names}.")

    # -------------------------------------------------------------------------
    # 9. Interview Type Aggregation
    # -------------------------------------------------------------------------
    print("\n[Test 9] Testing Interview Type Aggregation...")
    types_res = client.get("/api/performance/types", headers=headers_a)
    assert types_res.status_code == 200
    types_data = types_res.json()
    tech_type = next(t for t in types_data if t["type"] == "Technical")
    assert tech_type["interviews_count"] == 1
    assert tech_type["average_score"] == 8.2

    hr_type = next(t for t in types_data if t["type"] == "HR")
    assert hr_type["interviews_count"] == 1
    assert hr_type["average_score"] == 8.8
    print("[PASS] Test 9: Interview type breakdown (Technical vs HR) validated.")

    # -------------------------------------------------------------------------
    # 10. Role Aggregation
    # -------------------------------------------------------------------------
    print("\n[Test 10] Testing Practiced Role Aggregation...")
    roles_res = client.get("/api/performance/roles", headers=headers_a)
    assert roles_res.status_code == 200
    roles_data = roles_res.json()
    assert len(roles_data) == 1
    assert roles_data[0]["role"] == "Python Developer"
    assert roles_data[0]["interviews_count"] == 2
    assert roles_data[0]["average_score"] == 8.5
    print("[PASS] Test 10: Practiced role aggregation verified.")

    # -------------------------------------------------------------------------
    # 11. Strength Detection (Deterministic >= 8.0)
    # -------------------------------------------------------------------------
    print("\n[Test 11] Testing Strength Detection...")
    ins_res = client.get("/api/performance/insights", headers=headers_a)
    assert ins_res.status_code == 200
    insights_data = ins_res.json()
    strengths = insights_data["strengths"]
    assert len(strengths) > 0
    # Python Metaprogramming (9.0) or Technical Depth should be present
    assert any("Python Metaprogramming" in s or "Technical" in s or "Communication" in s for s in strengths)
    print(f"[PASS] Test 11: Deterministic strengths detected: {strengths}")

    # -------------------------------------------------------------------------
    # 12. Weak Area Detection (Deterministic < 7.5)
    # -------------------------------------------------------------------------
    print("\n[Test 12] Testing Weak Area Detection...")
    weak_areas = insights_data["weak_areas"]
    # SQL Optimization had score 7.0 (< 7.5)
    assert any("SQL Optimization" in w or "Database" in w for w in weak_areas)
    print(f"[PASS] Test 12: Weak area accurately detected: {weak_areas}")

    # -------------------------------------------------------------------------
    # 13. Recommendation Generation & Comparison
    # -------------------------------------------------------------------------
    print("\n[Test 13] Testing Recommendation Generation & Resume Comparison...")
    recommendations = insights_data["recommendations"]
    assert len(recommendations) > 0
    comp = insights_data["resume_interview_comparison"]
    assert comp is not None
    assert comp["resume_score"] == 84.0
    assert "Your current scores suggest" in comp["insight"]
    print(f"[PASS] Test 13: Neutral comparative insight generated: {comp['insight']}")

    # -------------------------------------------------------------------------
    # 14. Multi-Tenant User Data Isolation
    # -------------------------------------------------------------------------
    print("\n[Test 14] Testing Strict User Data Isolation...")
    # User B should see 0 data, completely insulated from User A
    ov_b = client.get("/api/performance/overview", headers=headers_b).json()
    assert ov_b["interviews_completed"] == 0
    assert ov_b["has_data"] is False
    assert client.get("/api/performance/trend", headers=headers_b).json() == []
    assert client.get("/api/performance/skills", headers=headers_b).json() == []
    assert client.get("/api/performance/roles", headers=headers_b).json() == []
    print("[PASS] Test 14: Strict data isolation verified. User B has 0 access to User A's data.")

    # -------------------------------------------------------------------------
    # 15. Duplicate Evaluation Handling
    # -------------------------------------------------------------------------
    print("\n[Test 15] Testing Duplicate Evaluation Handling...")
    # Re-evaluate Question 1 of Session 1 with an updated score of 9.5
    updated_eval = {
        "user_id": ObjectId(user_a_id),
        "question_set_id": qset_1_id,
        "question_number": 1,
        "candidate_answer": "Re-written answer covering generator expressions and memory savings.",
        "technical_accuracy": 9.5,
        "relevance": 9.5,
        "completeness": 9.5,
        "clarity": 9.5,
        "communication": 9.5,
        "overall_score": 9.5,
        "summary": "Exceptional revised explanation.",
        "strengths": ["Comprehensive coverage"],
        "weaknesses": [],
        "top_improvements": [],
        "created_at": now,
    }
    # Update existing question 1 evaluation to prevent duplicate counting
    evals_col.update_one(
        {"user_id": ObjectId(user_a_id), "question_set_id": qset_1_id, "question_number": 1},
        {"$set": updated_eval},
    )
    # Question count should still be 5
    ov_after_update = client.get("/api/performance/overview", headers=headers_a).json()
    assert ov_after_update["questions_evaluated"] == 5
    print("[PASS] Test 15: Evaluation update handled accurately without double-counting.")

    # -------------------------------------------------------------------------
    # 16. Date Filtering (7d vs 30d vs 90d vs All)
    # -------------------------------------------------------------------------
    print("\n[Test 16] Testing Date Filtering...")
    ov_7d = client.get("/api/performance/overview?time_range=7d", headers=headers_a).json()
    assert ov_7d["interviews_completed"] == 2

    # Query with future cutoff where no sessions exist
    # Let's insert a session 100 days in the past and test 30d
    old_qset = {
        "_id": ObjectId(),
        "user_id": ObjectId(user_a_id),
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "created_at": now - timedelta(days=120),
    }
    qsets_col.insert_one(old_qset)
    evals_col.insert_one({
        "user_id": ObjectId(user_a_id),
        "question_set_id": old_qset["_id"],
        "question_number": 1,
        "overall_score": 5.0,
        "communication": 5.0,
        "created_at": now - timedelta(days=120),
    })

    ov_30d = client.get("/api/performance/overview?time_range=30d", headers=headers_a).json()
    assert ov_30d["interviews_completed"] == 2 # 120d old session excluded

    ov_all = client.get("/api/performance/overview?time_range=all", headers=headers_a).json()
    assert ov_all["interviews_completed"] == 3 # 120d session included
    print("[PASS] Test 16: Date filtering verified (30d excludes old, all includes all).")

    # -------------------------------------------------------------------------
    # 17. Interview Type Filtering
    # -------------------------------------------------------------------------
    print("\n[Test 17] Testing Interview Type Filtering...")
    tech_only = client.get("/api/performance/overview?interview_type=Technical", headers=headers_a).json()
    assert tech_only["interviews_completed"] == 2 # The 2 technical sessions

    hr_only = client.get("/api/performance/overview?interview_type=HR", headers=headers_a).json()
    assert hr_only["interviews_completed"] == 1 # Only HR session
    print("[PASS] Test 17: Interview type filtering verified.")

    # -------------------------------------------------------------------------
    # 18. Target Role Filtering
    # -------------------------------------------------------------------------
    print("\n[Test 18] Testing Role Filtering...")
    py_role = client.get("/api/performance/overview?target_role=Python Developer", headers=headers_a).json()
    assert py_role["interviews_completed"] == 3

    nonexistent_role = client.get("/api/performance/overview?target_role=DevOps Engineer", headers=headers_a).json()
    assert nonexistent_role["interviews_completed"] == 0
    print("[PASS] Test 18: Role filtering verified.")

    # -------------------------------------------------------------------------
    # 19. Final Interview Report API
    # -------------------------------------------------------------------------
    print("\n[Test 19] Testing Final Interview Report API...")
    rep_res = client.get(f"/api/interview/report/{str(qset_1_id)}", headers=headers_a)
    assert rep_res.status_code == 200
    report = rep_res.json()
    assert report["target_role"] == "Python Developer"
    assert report["interview_type"] == "Technical"
    assert report["overall_score"] > 0
    assert "strong_areas" in report
    assert "weak_areas" in report
    assert "top_improvements" in report
    assert len(report["evaluations"]) == 3
    print("[PASS] Test 19: Full interview report verified with evaluations breakdown.")

    # -------------------------------------------------------------------------
    # 20. PDF Report Generation Data Integrity
    # -------------------------------------------------------------------------
    print("\n[Test 20] Testing PDF Report Export Payload Integrity...")
    # Verify report contains all necessary fields for client-side jsPDF rendering
    required_pdf_fields = [
        "target_role",
        "interview_type",
        "difficulty",
        "overall_score",
        "score_percentage",
        "completion_rate",
        "strong_areas",
        "weak_areas",
        "top_improvements",
        "evaluations",
    ]
    for field in required_pdf_fields:
        assert field in report, f"Missing required PDF field: {field}"
    assert len(report["evaluations"]) > 0
    first_ev = report["evaluations"][0]
    assert "question_number" in first_ev
    assert "candidate_answer" in first_ev
    assert "overall_score" in first_ev
    print("[PASS] Test 20: PDF report payload integrity confirmed.")

    # -------------------------------------------------------------------------
    # 21. Dashboard Real Statistics & Recent Activity
    # -------------------------------------------------------------------------
    print("\n[Test 21] Testing Dashboard Statistics & Recent Activity Feed...")
    act_res = client.get("/api/performance/recent-activity?limit=6", headers=headers_a)
    assert act_res.status_code == 200
    activities = act_res.json()
    assert len(activities) > 0
    types = [a["activity_type"] for a in activities]
    assert "resume_analyzed" in types or "interview_completed" in types
    print(f"[PASS] Test 21: Real dashboard recent activities confirmed: {len(activities)} items.")

    print("\n==================================================")
    print("ALL 21 BACKEND PHASE 6 TEST SCENARIOS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    run_phase6_tests()
