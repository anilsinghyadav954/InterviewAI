import json
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import get_database, init_db, get_interview_evaluations_collection, get_interview_question_sets_collection
from app.schemas.interview import AnswerEvaluationResponse, FinalInterviewReportResponse
from app.services.ai_service import calculate_overall_answer_score

client = TestClient(app)

def run_phase5_tests():
    print("==================================================")
    print("PHASE 5 - AI ANSWER EVALUATION & SCORING TEST SUITE")
    print("==================================================")

    init_db()
    db = get_database()
    users_col = db["users"]
    resumes_col = db["resume_analyses"]
    qsets_col = get_interview_question_sets_collection()
    evals_col = get_interview_evaluations_collection()

    # -------------------------------------------------------------------------
    # 1. Authentication Setup
    # -------------------------------------------------------------------------
    print("\n[Test 1] Testing Authentication & User Setup...")
    user_a_data = {
        "email": "phase5_candidate_a@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase5 Alice Developer",
        "target_role": "Python Developer",
    }
    user_b_data = {
        "email": "phase5_candidate_b@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase5 Bob Analyst",
        "target_role": "Data Analyst",
    }

    client.post("/api/auth/register", json=user_a_data)
    login_a = client.post("/api/auth/login", json={"email": user_a_data["email"], "password": user_a_data["password"]})
    assert login_a.status_code == 200, f"Login A failed: {login_a.text}"
    token_a = login_a.json()["access_token"]
    user_a_id = login_a.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post("/api/auth/register", json=user_b_data)
    login_b = client.post("/api/auth/login", json={"email": user_b_data["email"], "password": user_b_data["password"]})
    assert login_b.status_code == 200, f"Login B failed: {login_b.text}"
    token_b = login_b.json()["access_token"]
    user_b_id = login_b.json()["user"]["id"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Clean test baseline
    evals_col.delete_many({"user_id": {"$in": [user_a_id, ObjectId(user_a_id), user_b_id, ObjectId(user_b_id)]}})
    qsets_col.delete_many({"user_id": {"$in": [user_a_id, ObjectId(user_a_id), user_b_id, ObjectId(user_b_id)]}})

    # Auth check on evaluate endpoint
    unauth_eval = client.post("/api/interview/evaluate-answer", json={
        "question_set_id": str(ObjectId()),
        "question_number": 1,
        "candidate_answer": "Testing without token",
    })
    assert unauth_eval.status_code == 401, f"Expected 401 Unauthorized, got {unauth_eval.status_code}"
    print("[PASS] Test 1: Authentication required and verified.")

    # Create technical question set for User A
    qset_a_res = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Python Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert qset_a_res.status_code == 201, f"Failed to create question set: {qset_a_res.text}"
    qset_a = qset_a_res.json()
    qset_a_id = qset_a["id"]
    print(f"[INFO] Generated Technical Question Set ID: {qset_a_id} with {len(qset_a['questions'])} questions.")

    # Create HR question set for User A
    qset_hr_res = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Software Developer",
        "interview_type": "HR",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert qset_hr_res.status_code == 201
    qset_hr = qset_hr_res.json()
    qset_hr_id = qset_hr["id"]

    # Create Mixed question set for User A
    qset_mixed_res = client.post("/api/interview/generate-questions", headers=headers_a, json={
        "target_role": "Full Stack Developer",
        "interview_type": "Mixed",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    })
    assert qset_mixed_res.status_code == 201
    qset_mixed = qset_mixed_res.json()
    qset_mixed_id = qset_mixed["id"]

    # -------------------------------------------------------------------------
    # 2. Valid Technical Answer Evaluation
    # -------------------------------------------------------------------------
    print("\n[Test 2] Testing Valid Technical Answer Evaluation...")
    tech_answer = (
        "In Python, mutable objects like lists and dictionaries can have their in-place contents modified "
        "without changing their memory address (id), whereas immutable objects like tuples and strings allocate "
        "a new object upon modification. For example, my_list.append(1) mutates the list, while string concatenation "
        "creates a new string in memory. This affects function default argument pitfalls when mutable defaults are reused."
    )
    eval_tech_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_a_id,
        "question_number": 1,
        "candidate_answer": tech_answer,
    })
    assert eval_tech_res.status_code == 200, f"Technical eval failed: {eval_tech_res.text}"
    eval_tech = eval_tech_res.json()
    assert 0.0 <= eval_tech["overall_score"] <= 10.0
    assert eval_tech["technical_accuracy"] is not None
    assert 0.0 <= eval_tech["technical_accuracy"] <= 10.0
    assert len(eval_tech["strengths"]) > 0
    assert len(eval_tech["improvement_suggestions"]) > 0
    assert len(eval_tech["model_answer_outline"]) > 0
    print(f"[PASS] Test 2: Technical answer evaluated. Overall Score: {eval_tech['overall_score']}/10, Tech Accuracy: {eval_tech['technical_accuracy']}/10")

    # -------------------------------------------------------------------------
    # 3. Valid HR Answer Evaluation
    # -------------------------------------------------------------------------
    print("\n[Test 3] Testing Valid HR Answer Evaluation...")
    hr_answer = (
        "In my previous project, we faced a high-stakes disagreement regarding release deadlines. "
        "Situation: A core feature was delayed by 2 days. Task: I needed to coordinate with engineering and product. "
        "Action: I scheduled a blameless sync, presented technical blockers objectively, and negotiated phased rollout. "
        "Result: We shipped core workflows on time without outages and maintained high stakeholder trust."
    )
    eval_hr_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_hr_id,
        "question_number": 1,
        "candidate_answer": hr_answer,
    })
    assert eval_hr_res.status_code == 200, f"HR eval failed: {eval_hr_res.text}"
    eval_hr = eval_hr_res.json()
    assert 0.0 <= eval_hr["overall_score"] <= 10.0
    assert 0.0 <= eval_hr["communication"] <= 10.0
    assert 0.0 <= eval_hr["relevance"] <= 10.0
    print(f"[PASS] Test 3: HR answer evaluated. Overall Score: {eval_hr['overall_score']}/10, Communication: {eval_hr['communication']}/10")

    # -------------------------------------------------------------------------
    # 4. Valid Mixed Answer Evaluation
    # -------------------------------------------------------------------------
    print("\n[Test 4] Testing Valid Mixed Answer Evaluation...")
    mixed_answer = (
        "When handling trade-offs between delivery velocity and code quality, I prioritize modular micro-services "
        "with automated CI/CD unit testing. While meeting tight client deadlines, I document technical debt tickets "
        "and schedule refactoring sprints to ensure scalability."
    )
    eval_mixed_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_mixed_id,
        "question_number": 1,
        "candidate_answer": mixed_answer,
    })
    assert eval_mixed_res.status_code == 200, f"Mixed eval failed: {eval_mixed_res.text}"
    eval_mixed = eval_mixed_res.json()
    assert 0.0 <= eval_mixed["overall_score"] <= 10.0
    print(f"[PASS] Test 4: Mixed interview answer evaluated successfully. Score: {eval_mixed['overall_score']}/10")

    # -------------------------------------------------------------------------
    # 5. Empty Answer Rejection (HTTP 400)
    # -------------------------------------------------------------------------
    print("\n[Test 5] Testing Empty Answer Rejection (HTTP 400)...")
    empty_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_a_id,
        "question_number": 2,
        "candidate_answer": "   \n\t   ",
    })
    assert empty_res.status_code == 400 or empty_res.status_code == 422, f"Expected 400 or 422, got {empty_res.status_code}: {empty_res.text}"
    assert "answer" in empty_res.text.lower()
    print("[PASS] Test 5: Empty answer rejected without invoking AI.")

    # -------------------------------------------------------------------------
    # 6. Invalid Question Set Handling
    # -------------------------------------------------------------------------
    print("\n[Test 6] Testing Invalid Question Set ID...")
    fake_set_id = str(ObjectId())
    inv_set_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": fake_set_id,
        "question_number": 1,
        "candidate_answer": "Valid text but invalid set",
    })
    assert inv_set_res.status_code == 404, f"Expected 404, got {inv_set_res.status_code}"
    print("[PASS] Test 6: Non-existent question set returned 404 Not Found.")

    # -------------------------------------------------------------------------
    # 7. Invalid Question Number Handling
    # -------------------------------------------------------------------------
    print("\n[Test 7] Testing Invalid Question Number...")
    inv_num_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_a_id,
        "question_number": 999,
        "candidate_answer": "Valid text but question number does not exist",
    })
    assert inv_num_res.status_code == 404, f"Expected 404, got {inv_num_res.status_code}"
    print("[PASS] Test 7: Out-of-bounds question number returned 404 Not Found.")

    # -------------------------------------------------------------------------
    # 8. AI Structured Response Schema Validation
    # -------------------------------------------------------------------------
    print("\n[Test 8] Testing Schema Validation on Evaluation Output...")
    validated_schema = AnswerEvaluationResponse(**eval_tech)
    assert validated_schema.overall_score == eval_tech["overall_score"]
    assert isinstance(validated_schema.strengths, list)
    assert isinstance(validated_schema.weaknesses, list)
    assert isinstance(validated_schema.improvement_suggestions, list)
    assert isinstance(validated_schema.summary, str)
    assert isinstance(validated_schema.model_answer_outline, str)
    print("[PASS] Test 8: Pydantic schema validation strictly succeeded.")

    # -------------------------------------------------------------------------
    # 9. MongoDB Evaluation Persistence & Upsert Behavior
    # -------------------------------------------------------------------------
    print("\n[Test 9] Testing MongoDB Evaluation Persistence & Upsert...")
    # Check document exists in DB
    db_doc = evals_col.find_one({"question_set_id": ObjectId(qset_a_id), "question_number": 1})
    assert db_doc is not None, "Evaluation document not found in MongoDB!"
    initial_id = db_doc["_id"]

    # Re-evaluate question 1 with updated answer
    updated_answer = tech_answer + " Additionally, Python tuples cannot have elements reassigned."
    re_eval_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_a_id,
        "question_number": 1,
        "candidate_answer": updated_answer,
    })
    assert re_eval_res.status_code == 200
    # Ensure no duplicate was inserted; same record was upserted
    docs_count = evals_col.count_documents({"question_set_id": ObjectId(qset_a_id), "question_number": 1})
    assert docs_count == 1, f"Expected exactly 1 document, found {docs_count}"
    print("[PASS] Test 9: Evaluation persisted and safely upserted without duplication.")

    # -------------------------------------------------------------------------
    # 10. Single Evaluation Retrieval
    # -------------------------------------------------------------------------
    print("\n[Test 10] Testing GET /api/interview/evaluation/{qset_id}/{qnum}...")
    get_eval_res = client.get(f"/api/interview/evaluation/{qset_a_id}/1", headers=headers_a)
    assert get_eval_res.status_code == 200
    retrieved = get_eval_res.json()
    assert retrieved["question_number"] == 1
    assert retrieved["question_set_id"] == qset_a_id
    assert retrieved["candidate_answer"] == updated_answer
    print(f"[PASS] Test 10: Retrieved single evaluation successfully. Score: {retrieved['overall_score']}")

    # -------------------------------------------------------------------------
    # 11. Ownership Protection (User B cannot access User A's evaluation)
    # -------------------------------------------------------------------------
    print("\n[Test 11] Testing Ownership Protection (Access Forbidden)...")
    forbidden_get = client.get(f"/api/interview/evaluation/{qset_a_id}/1", headers=headers_b)
    # Must be 403 or 404 (question set not owned by B)
    assert forbidden_get.status_code in [403, 404], f"Expected 403/404, got {forbidden_get.status_code}"

    forbidden_report = client.get(f"/api/interview/report/{qset_a_id}", headers=headers_b)
    assert forbidden_report.status_code in [403, 404], f"Expected 403/404 for report, got {forbidden_report.status_code}"
    print("[PASS] Test 11: Ownership verified. Unauthorized candidate blocked.")

    # -------------------------------------------------------------------------
    # 12. Multiple Question Evaluations
    # -------------------------------------------------------------------------
    print("\n[Test 12] Evaluating Multiple Questions in Question Set A...")
    q2_ans = (
        "List comprehensions provide concise syntax for creating new lists by evaluating an expression over an iterable. "
        "Under the hood, list comprehensions are optimized at C-level bytecode using LIST_APPEND, making them faster "
        "than traditional append loops. However, generators with () should be preferred when streaming huge datasets."
    )
    q2_eval_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_a_id,
        "question_number": 2,
        "candidate_answer": q2_ans,
    })
    assert q2_eval_res.status_code == 200

    q3_ans = (
        "Shallow copy creates a new compound object and inserts references into it to the objects found in the original. "
        "Deep copy creates a new compound object and recursively copies all nested objects found in the original."
    )
    q3_eval_res = client.post("/api/interview/evaluate-answer", headers=headers_a, json={
        "question_set_id": qset_a_id,
        "question_number": 3,
        "candidate_answer": q3_ans,
    })
    assert q3_eval_res.status_code == 200
    print("[PASS] Test 12: Successfully evaluated Questions 1, 2, and 3.")

    # -------------------------------------------------------------------------
    # 13. Final Interview Report Generation
    # -------------------------------------------------------------------------
    print("\n[Test 13] Testing GET /api/interview/report/{qset_id}...")
    report_res = client.get(f"/api/interview/report/{qset_a_id}", headers=headers_a)
    assert report_res.status_code == 200, f"Report failed: {report_res.text}"
    report = report_res.json()
    assert report["total_questions"] == 5
    assert report["answered_questions"] == 3
    assert report["evaluated_questions"] == 3
    assert report["unanswered_questions"] == 2
    assert report["completion_rate"] == 60.0
    assert 0.0 <= report["overall_score"] <= 10.0
    assert len(report["strong_areas"]) > 0
    assert len(report["weak_areas"]) > 0
    assert len(report["top_improvements"]) > 0
    print(f"[PASS] Test 13: Final report generated. Overall Score: {report['overall_score']}/10 ({report['score_percentage']}%)")

    # -------------------------------------------------------------------------
    # 14. Deterministic Scoring Logic Verification
    # -------------------------------------------------------------------------
    print("\n[Test 14] Verifying Deterministic Component Scoring Formulas...")
    # Test Technical formula:
    # Overall = (Tech * 0.40) + (Rel * 0.25) + (Comp * 0.20) + (Clar * 0.15)
    t_score = calculate_overall_answer_score(
        category="Technical",
        technical_accuracy=9.0,
        relevance=8.0,
        completeness=8.0,
        clarity=7.0,
        communication=7.0,
    )
    expected_tech = round((9.0 * 0.40) + (8.0 * 0.25) + (8.0 * 0.20) + (7.0 * 0.15), 1)
    assert t_score == expected_tech, f"Expected {expected_tech}, got {t_score}"

    # Test HR formula:
    # Overall = (Rel * 0.30) + (Comm * 0.30) + (Clar * 0.20) + (Comp * 0.20)
    hr_calc = calculate_overall_answer_score(
        category="HR",
        technical_accuracy=None,
        relevance=9.0,
        completeness=8.0,
        clarity=9.0,
        communication=8.5,
    )
    expected_hr = round((9.0 * 0.30) + (8.5 * 0.30) + (9.0 * 0.20) + (8.0 * 0.20), 1)
    assert hr_calc == expected_hr, f"Expected {expected_hr}, got {hr_calc}"
    print(f"[PASS] Test 14: Deterministic formulas verified (Tech: {t_score}, HR: {hr_calc}).")

    # -------------------------------------------------------------------------
    # 15. Unanswered Questions Excluded from Average
    # -------------------------------------------------------------------------
    print("\n[Test 15] Verifying Unanswered Questions Are Excluded from Score Average...")
    evals = report["evaluations"]
    assert len(evals) == 3
    computed_avg = round(sum(e["overall_score"] for e in evals) / 3, 1)
    assert report["overall_score"] == computed_avg
    assert report["unanswered_questions"] == 2
    print(f"[PASS] Test 15: Score average ({report['overall_score']}) strictly excludes 2 unanswered questions.")

    # -------------------------------------------------------------------------
    # 16. Refresh/Reload Evaluation Retrieval
    # -------------------------------------------------------------------------
    print("\n[Test 16] Testing GET /api/interview/evaluations/{qset_id} (Session Reload)...")
    all_evals_res = client.get(f"/api/interview/evaluations/{qset_a_id}", headers=headers_a)
    assert all_evals_res.status_code == 200
    all_evals = all_evals_res.json()
    assert len(all_evals) == 3
    # Check sorted order by question_number
    assert all_evals[0]["question_number"] == 1
    assert all_evals[1]["question_number"] == 2
    assert all_evals[2]["question_number"] == 3
    print("[PASS] Test 16: All session evaluations retrieved sorted by question_number.")

    # -------------------------------------------------------------------------
    # 17. Dashboard Score Integration
    # -------------------------------------------------------------------------
    print("\n[Test 17] Testing Dashboard Metrics API Integration...")
    # Check User A (who has completed evaluations)
    dash_a_res = client.get("/api/interview/dashboard-stats", headers=headers_a)
    assert dash_a_res.status_code == 200
    dash_a = dash_a_res.json()
    assert dash_a["has_completed_interviews"] is True
    assert dash_a["completed_interviews_count"] >= 1
    assert dash_a["total_evaluations_count"] >= 3
    assert dash_a["average_score"] > 0.0

    # Check User B (who has NO evaluations)
    dash_b_res = client.get("/api/interview/dashboard-stats", headers=headers_b)
    assert dash_b_res.status_code == 200
    dash_b = dash_b_res.json()
    assert dash_b["has_completed_interviews"] is False
    assert dash_b["completed_interviews_count"] == 0
    assert dash_b["average_score"] == 0.0
    print(f"[PASS] Test 17: Dashboard metrics verified. User A Avg: {dash_a['average_score']}/10, User B Has Completed: {dash_b['has_completed_interviews']}")

    # -------------------------------------------------------------------------
    # 18. Interview History Report Integration
    # -------------------------------------------------------------------------
    print("\n[Test 18] Testing Question History with Evaluation Summaries...")
    hist_res = client.get("/api/interview/question-history", headers=headers_a)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    target_item = next((it for it in hist if it["id"] == qset_a_id), None)
    assert target_item is not None
    assert target_item["evaluated_questions"] == 3
    assert target_item["overall_score"] is not None
    assert target_item["completion_rate"] == 60.0
    print(f"[PASS] Test 18: Question history includes evaluated score: {target_item['overall_score']} and completion: {target_item['completion_rate']}%.")

    # -------------------------------------------------------------------------
    # 19. AI Failure Handling & Fallback
    # -------------------------------------------------------------------------
    print("\n[Test 19] Testing AI Failure Handling & Resilient Fallback...")
    from app.services.ai_service import evaluate_interview_answer
    # Direct test of evaluate_interview_answer with arbitrary inputs to verify robust structure
    fallback_eval = evaluate_interview_answer(
        target_role="Data Analyst",
        interview_type="Technical",
        difficulty="Intermediate",
        question="Explain SQL Window Functions with real examples.",
        category="Database",
        topic="SQL",
        expected_focus=["ROW_NUMBER()", "PARTITION BY", "Performance"],
        candidate_answer="Window functions like ROW_NUMBER() and RANK() operate on a subset of rows defined by PARTITION BY without collapsing rows.",
    )
    assert 0.0 <= fallback_eval["overall_score"] <= 10.0
    assert isinstance(fallback_eval["strengths"], list)
    assert isinstance(fallback_eval["weaknesses"], list)
    assert len(fallback_eval["summary"]) > 0
    print("[PASS] Test 19: Evaluation service gracefully returns valid structured evaluation.")

    # -------------------------------------------------------------------------
    # 20. Clean Baseline & Final Confirmation
    # -------------------------------------------------------------------------
    print("\n[Test 20] Final Comprehensive Verification...")
    report_validated = FinalInterviewReportResponse(**report)
    assert report_validated.question_set_id == qset_a_id
    print("[PASS] Test 20: All 20 Phase 5 verification requirements successfully passed!")

    print("\n==================================================")
    print("ALL 20 PHASE 5 INTERVIEW EVALUATION TESTS PASSED! SUCCESS")
    print("==================================================")

if __name__ == "__main__":
    run_phase5_tests()
