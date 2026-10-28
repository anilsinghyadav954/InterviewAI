import json
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import (
    get_database,
    init_db,
    get_voice_sessions_collection,
    get_interview_question_sets_collection,
    get_interview_evaluations_collection,
)
from app.schemas.voice import VoiceSessionResponse, VoiceAnswerResponse, VoiceHistoryItem
from app.schemas.interview import FinalInterviewReportResponse

client = TestClient(app)


def run_phase7_tests():
    print("==================================================")
    print("PHASE 7 - VOICE INTERVIEW & SPEECH-TO-TEXT TESTS")
    print("==================================================")

    init_db()
    db = get_database()
    users_col = db["users"]
    qsets_col = get_interview_question_sets_collection()
    evals_col = get_interview_evaluations_collection()
    voice_col = get_voice_sessions_collection()

    # -------------------------------------------------------------------------
    # 1. User Authentication & Isolation Setup
    # -------------------------------------------------------------------------
    print("\n[Test 1] Testing User Authentication & Setup...")
    user_a_data = {
        "email": "phase7_alice_dev@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase7 Alice Voice Candidate",
        "target_role": "Python Developer",
    }
    user_b_data = {
        "email": "phase7_bob_dev@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Phase7 Bob Voice Candidate",
        "target_role": "Full Stack Developer",
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

    print("[PASS] Candidate A and Candidate B successfully authenticated.")

    # -------------------------------------------------------------------------
    # 2. Unauthorized Access Protection (401 Unauthorized)
    # -------------------------------------------------------------------------
    print("\n[Test 2] Testing Unauthorized Access Protection (HTTP 401)...")
    res = client.post("/api/voice-interview/start", json={"question_set_id": "123"})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    res = client.post("/api/voice-interview/answer", json={"session_id": "123", "question_number": 1, "transcript": "test"})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    res = client.get("/api/voice-interview/active")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    res = client.get("/api/voice-interview/history")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    res = client.get("/api/voice-interview/session/123")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    res = client.post("/api/voice-interview/finish/123")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    res = client.get("/api/voice-interview/report/123")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    print("[PASS] All Phase 7 Voice Interview endpoints strictly reject unauthenticated requests with 401.")

    # -------------------------------------------------------------------------
    # 3. Question Set Generation for Voice Interview
    # -------------------------------------------------------------------------
    print("\n[Test 3] Generating Questions for Candidate A...")
    gen_res = client.post(
        "/api/interview/generate-questions",
        headers=headers_a,
        json={
            "target_role": "Python Developer",
            "interview_type": "Technical",
            "difficulty": "Intermediate",
            "number_of_questions": 5,
        },
    )
    assert gen_res.status_code == 201, f"Question generation failed: {gen_res.text}"
    qset_a = gen_res.json()
    qset_id = qset_a["id"]
    print(f"[PASS] Question set created with ID: {qset_id} ({len(qset_a['questions'])} questions).")

    # -------------------------------------------------------------------------
    # 4. Authenticated Voice Session Creation (POST /start)
    # -------------------------------------------------------------------------
    print("\n[Test 4] Starting Voice Interview Session (POST /start)...")
    start_res = client.post(
        "/api/voice-interview/start",
        headers=headers_a,
        json={"question_set_id": qset_id},
    )
    assert start_res.status_code == 201, f"Voice session start failed: {start_res.text}"
    session_data = start_res.json()
    session_id = session_data["session_id"]

    assert session_data["question_set_id"] == qset_id
    assert session_data["status"] == "active"
    assert session_data["current_question"] == 1
    assert session_data["total_questions"] == 5
    assert session_data["mode"] == "Voice"
    assert len(session_data["questions"]) == 5

    # Check MongoDB document
    s_doc = voice_col.find_one({"_id": ObjectId(session_id)})
    assert s_doc is not None, "Session document not found in MongoDB"
    assert str(s_doc["user_id"]) == str(user_a_id)
    assert s_doc["status"] == "active"

    # Check question set mode updated
    qs_doc = qsets_col.find_one({"_id": ObjectId(qset_id)})
    assert qs_doc.get("mode") == "Voice"

    print(f"[PASS] Voice session initialized successfully. Session ID: {session_id}")

    # -------------------------------------------------------------------------
    # 5. Session Ownership Security & Access Control (HTTP 403 & 404)
    # -------------------------------------------------------------------------
    print("\n[Test 5] Testing Session Ownership & Candidate Isolation...")
    # Bob attempts to get Alice's session
    bob_get = client.get(f"/api/voice-interview/session/{session_id}", headers=headers_b)
    assert bob_get.status_code == 404, f"Expected 404 for unauthorized session view, got {bob_get.status_code}"

    # Bob attempts to submit answer to Alice's session
    bob_sub = client.post(
        "/api/voice-interview/answer",
        headers=headers_b,
        json={
            "session_id": session_id,
            "question_number": 1,
            "transcript": "I am answering Alice's question unauthorized.",
        },
    )
    assert bob_sub.status_code == 403, f"Expected 403 Forbidden for foreign session submit, got {bob_sub.status_code}"

    # Bob attempts to finish Alice's session
    bob_fin = client.post(f"/api/voice-interview/finish/{session_id}", headers=headers_b)
    assert bob_fin.status_code == 403, f"Expected 403 Forbidden for foreign session finish, got {bob_fin.status_code}"

    print("[PASS] Strict user isolation confirmed. Foreign candidate received 403 Forbidden.")

    # -------------------------------------------------------------------------
    # 6. Invalid Input & Empty Transcript Rejection (HTTP 400)
    # -------------------------------------------------------------------------
    print("\n[Test 6] Testing Empty Transcript & Malformed Request Rejection...")
    # Empty transcript
    empty_res = client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={"session_id": session_id, "question_number": 1, "transcript": ""},
    )
    assert empty_res.status_code in [400, 422], f"Expected 400 or 422 for empty transcript, got {empty_res.status_code}"

    # Whitespace only
    ws_res = client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={"session_id": session_id, "question_number": 1, "transcript": "     "},
    )
    assert ws_res.status_code in [400, 422], f"Expected 400 or 422 for whitespace transcript, got {ws_res.status_code}"

    # Invalid question set on start
    bad_qset = client.post(
        "/api/voice-interview/start",
        headers=headers_a,
        json={"question_set_id": str(ObjectId())},
    )
    assert bad_qset.status_code == 404, f"Expected 404 for non-existent question set, got {bad_qset.status_code}"

    # Invalid question number on answer
    bad_qnum = client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={"session_id": session_id, "question_number": 99, "transcript": "Some answer"},
    )
    assert bad_qnum.status_code == 400, f"Expected 400 for invalid question number, got {bad_qnum.status_code}"

    print("[PASS] Input validation strictly enforced: empty transcript rejected (400), invalid numbers rejected.")

    # -------------------------------------------------------------------------
    # 7. Submitting Candidate Voice Transcript Answer & Phase 5 Evaluation
    # -------------------------------------------------------------------------
    print("\n[Test 7] Submitting Voice Answer to AI Evaluation (Question 1)...")
    ans1_transcript = (
        "In Python, the Global Interpreter Lock ensures only one native thread executes bytecode at a time. "
        "For CPU-bound tasks, we use multiprocessing to spawn separate processes with their own memory spaces. "
        "For I/O-bound tasks, we utilize AsyncIO or threading since I/O operations release the GIL during syscalls."
    )
    ans1_res = client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={
            "session_id": session_id,
            "question_number": 1,
            "transcript": ans1_transcript,
        },
    )
    assert ans1_res.status_code == 200, f"Voice answer submit failed: {ans1_res.text}"
    ans1_data = ans1_res.json()

    assert ans1_data["question_number"] == 1
    assert ans1_data["transcript"] == ans1_transcript
    assert ans1_data["is_last_question"] is False
    assert ans1_data["session_status"] == "active"
    assert "evaluation" in ans1_data

    evaluation = ans1_data["evaluation"]
    assert evaluation["overall_score"] is not None
    assert 0.0 <= evaluation["overall_score"] <= 10.0
    assert evaluation["relevance"] is not None
    assert evaluation["completeness"] is not None
    assert evaluation["clarity"] is not None
    assert len(evaluation["strengths"]) > 0

    # Verify evaluation in MongoDB tagged with mode: Voice
    saved_eval = evals_col.find_one({"question_set_id": {"$in": [ObjectId(qset_id), qset_id]}, "question_number": 1})
    assert saved_eval is not None, "Evaluation not found in interview_answer_evaluations"
    assert saved_eval.get("mode") == "Voice"

    print(f"[PASS] Answer evaluated via Phase 5 engine. Overall Score: {evaluation['overall_score']}/10. Tagged mode: Voice.")

    # -------------------------------------------------------------------------
    # 8. Duplicate Submission / Answer Update
    # -------------------------------------------------------------------------
    print("\n[Test 8] Testing Answer Re-submission & Deduplication...")
    updated_transcript = ans1_transcript + " Additionally, Jython and IronPython do not have a GIL."
    re_res = client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={
            "session_id": session_id,
            "question_number": 1,
            "transcript": updated_transcript,
        },
    )
    assert re_res.status_code == 200

    # Ensure no duplicate answers stored in session doc
    s_doc_re = voice_col.find_one({"_id": ObjectId(session_id)})
    ans_list = s_doc_re["answers"]
    q1_count = len([a for a in ans_list if a["question_number"] == 1])
    assert q1_count == 1, f"Expected exactly 1 answer item for Question 1, found {q1_count}"
    print("[PASS] Duplicate submission correctly upserted and deduplicated.")

    # -------------------------------------------------------------------------
    # 9. Active Voice Session Lookup & Page Refresh Restoration (GET /active)
    # -------------------------------------------------------------------------
    print("\n[Test 9] Testing Active Voice Session Retrieval for Refresh Restoration...")
    active_res = client.get("/api/voice-interview/active", headers=headers_a)
    assert active_res.status_code == 200, f"Active session lookup failed: {active_res.text}"
    active_data = active_res.json()

    assert active_data is not None
    assert active_data["session_id"] == session_id
    assert active_data["status"] == "active"
    assert active_data["current_question"] == 2
    assert len(active_data["answers"]) == 1
    assert active_data["answers"][0]["question_number"] == 1
    assert active_data["answers"][0]["overall_score"] is not None
    assert active_data["answers"][0]["evaluation_id"] is not None

    print("[PASS] Active session restoration endpoint returned in-progress interview state with prior evaluations.")

    # -------------------------------------------------------------------------
    # 10. Completing Remaining Questions and Automatic Last-Question Finish
    # -------------------------------------------------------------------------
    print("\n[Test 10] Answering Questions 2, 3, 4, and 5 (Final Question)...")
    # Question 2
    client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={
            "session_id": session_id,
            "question_number": 2,
            "transcript": "Decorators in Python are callables that accept a function and return an altered wrapper function.",
        },
    )

    # Question 3
    client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={
            "session_id": session_id,
            "question_number": 3,
            "transcript": "Generators produce items on demand using the yield keyword, preserving function frame and saving memory.",
        },
    )

    # Question 4
    client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={
            "session_id": session_id,
            "question_number": 4,
            "transcript": "Context managers implement enter and exit dunder methods to guarantee resource allocation and cleanup like file handles.",
        },
    )

    # Question 5 (Final of 5)
    ans5_res = client.post(
        "/api/voice-interview/answer",
        headers=headers_a,
        json={
            "session_id": session_id,
            "question_number": 5,
            "transcript": "Metaclasses in Python define how classes themselves are constructed, allowing enforcement of API constraints at class definition time.",
        },
    )
    assert ans5_res.status_code == 200
    ans5_data = ans5_res.json()
    assert ans5_data["is_last_question"] is True
    assert ans5_data["session_status"] == "completed"

    s_doc_completed = voice_col.find_one({"_id": ObjectId(session_id)})
    assert s_doc_completed["status"] == "completed"
    assert s_doc_completed["completed_at"] is not None

    print("[PASS] Session automatically transitioned to 'completed' upon answering final question (5 of 5).")

    # -------------------------------------------------------------------------
    # 11. Final Voice Interview Report Generation (GET /report/{session_id})
    # -------------------------------------------------------------------------
    print("\n[Test 11] Testing Comprehensive Final Voice Interview Report API...")
    rep_res = client.get(f"/api/voice-interview/report/{session_id}", headers=headers_a)
    assert rep_res.status_code == 200, f"Report generation failed: {rep_res.text}"
    report_data = rep_res.json()

    assert report_data["overall_score"] is not None
    assert 0.0 <= report_data["overall_score"] <= 10.0
    assert report_data["evaluated_questions"] == 5
    assert report_data["total_questions"] == 5
    assert "strong_areas" in report_data
    assert "weak_areas" in report_data
    assert "top_improvements" in report_data
    assert len(report_data["evaluations"]) == 5

    print(f"[PASS] Voice interview report generated successfully. Score: {report_data['overall_score']}/10 ({report_data['score_percentage']}%).")

    # -------------------------------------------------------------------------
    # 12. Voice Interview History (GET /history)
    # -------------------------------------------------------------------------
    print("\n[Test 12] Testing Voice Interview History API (GET /history)...")
    hist_res = client.get("/api/voice-interview/history", headers=headers_a)
    assert hist_res.status_code == 200, f"History fetch failed: {hist_res.text}"
    history_items = hist_res.json()

    assert len(history_items) >= 1
    found_item = None
    for item in history_items:
        if item["session_id"] == session_id:
            found_item = item
            break

    assert found_item is not None, "Completed session not found in candidate history"
    assert found_item["mode"] == "Voice"
    assert found_item["status"] == "completed"
    assert found_item["score"] is not None
    assert found_item["questions_count"] == 5

    print(f"[PASS] Candidate history contains voice session with mode 'Voice' and score {found_item['score']}/10.")

    # -------------------------------------------------------------------------
    # 13. MongoDB Schema & Index Verification
    # -------------------------------------------------------------------------
    print("\n[Test 13] Verifying MongoDB Schema and Indexes for voice_interview_sessions...")
    col_indexes = voice_col.index_information()
    assert "user_id_1_started_at_-1" in col_indexes, "Missing user_id + started_at index"
    assert "user_id_1_status_1" in col_indexes, "Missing user_id + status index"
    assert "question_set_id_1" in col_indexes, "Missing question_set_id index"

    print("[PASS] MongoDB indexes verified: user_id + started_at, user_id + status, question_set_id.")

    print("\n==================================================")
    print("ALL PHASE 7 VOICE INTERVIEW TESTS PASSED FLAWLESSLY! 100% SUCCESS.")
    print("==================================================")


if __name__ == "__main__":
    run_phase7_tests()
