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
from app.schemas.voice import (
    VoiceSessionResponse,
    VoiceAnswerResponse,
    VoiceNextQuestionResponse,
    VoiceHistoryItem,
)
from app.schemas.interview import FinalInterviewReportResponse

client = TestClient(app)


def run_voice_interviewer_tests():
    print("==================================================")
    print("AI INTERVIEWER DYNAMIC VOICE INTERVIEW TESTS")
    print("==================================================")

    init_db()
    db = get_database()
    users_col = db["users"]
    qsets_col = get_interview_question_sets_collection()
    evals_col = get_interview_evaluations_collection()
    voice_col = get_voice_sessions_collection()

    # -------------------------------------------------------------------------
    # 1. Setup Candidate Accounts
    # -------------------------------------------------------------------------
    print("\n[Test 1] Setting up Candidate A and Candidate B...")
    user_a = {
        "email": "ai_interviewer_cand_a@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Dynamic Candidate A",
        "target_role": "Full Stack Developer",
    }
    user_b = {
        "email": "ai_interviewer_cand_b@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Dynamic Candidate B",
        "target_role": "Python Developer",
    }

    client.post("/api/auth/register", json=user_a)
    login_a = client.post("/api/auth/login", json={"email": user_a["email"], "password": user_a["password"]})
    assert login_a.status_code == 200, f"Candidate A login failed: {login_a.text}"
    token_a = login_a.json()["access_token"]
    user_a_id = login_a.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post("/api/auth/register", json=user_b)
    login_b = client.post("/api/auth/login", json={"email": user_b["email"], "password": user_b["password"]})
    assert login_b.status_code == 200
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    print("[PASS] Candidate accounts authenticated successfully.")

    # -------------------------------------------------------------------------
    # 2. Authentication Enforcement on /next-question
    # -------------------------------------------------------------------------
    print("\n[Test 2] Testing Unauthorized Access Protection (401)...")
    res_unauth = client.post(
        "/api/voice-interview/next-question",
        json={"session_id": "dummy_session", "question_number": 1, "transcript": "Some answer"},
    )
    assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
    print("[PASS] POST /next-question strictly rejects unauthenticated requests with 401.")

    # -------------------------------------------------------------------------
    # 3. Initialize Voice Interview Session
    # -------------------------------------------------------------------------
    print("\n[Test 3] Generating 5-Question Interview Set for Candidate A...")
    gen_payload = {
        "target_role": "Full Stack Developer",
        "interview_type": "Technical",
        "difficulty": "Intermediate",
        "number_of_questions": 5,
    }
    gen_res = client.post("/api/interview/generate-questions", json=gen_payload, headers=headers_a)
    assert gen_res.status_code == 201, f"Generate questions failed: {gen_res.text}"
    qset_id = gen_res.json()["id"]

    start_res = client.post("/api/voice-interview/start", json={"question_set_id": qset_id}, headers=headers_a)
    assert start_res.status_code == 201, f"Start voice session failed: {start_res.text}"
    session_data = start_res.json()
    session_id = session_data["session_id"]
    assert session_data["total_questions"] == 5
    assert session_data["current_question"] == 1
    print(f"[PASS] Voice interview session initialized: {session_id} (5 questions).")

    # -------------------------------------------------------------------------
    # 4. Session Ownership Protection (403 Forbidden)
    # -------------------------------------------------------------------------
    print("\n[Test 4] Testing Session Ownership Protection on /next-question...")
    foreign_res = client.post(
        "/api/voice-interview/next-question",
        json={
            "session_id": session_id,
            "question_number": 1,
            "transcript": "I built a React and FastAPI application with Docker.",
        },
        headers=headers_b,
    )
    assert foreign_res.status_code == 403, f"Expected 403 Forbidden for foreign user, got {foreign_res.status_code}"
    print("[PASS] Session ownership verified. Cross-user access rejected with 403 Forbidden.")

    # -------------------------------------------------------------------------
    # 5. Empty Transcript & Validation Rejection (400 Bad Request)
    # -------------------------------------------------------------------------
    print("\n[Test 5] Testing Empty Transcript & Malformed Request Validation...")
    empty_res = client.post(
        "/api/voice-interview/next-question",
        json={"session_id": session_id, "question_number": 1, "transcript": "   "},
        headers=headers_a,
    )
    assert empty_res.status_code == 422 or empty_res.status_code == 400
    print("[PASS] Empty transcript rejected.")

    # -------------------------------------------------------------------------
    # 6. Question 1 Spoken Answer & Dynamic Follow-up Generation
    # -------------------------------------------------------------------------
    print("\n[Test 6] Submitting Answer 1 with Project Details -> Testing Dynamic Follow-up Question...")
    ans_1_text = (
        "In my recent project, I designed a microservices architecture using FastAPI and MongoDB. "
        "We needed to handle high write loads and implemented custom indexing and database aggregation pipelines."
    )
    next_res_1 = client.post(
        "/api/voice-interview/next-question",
        json={"session_id": session_id, "question_number": 1, "transcript": ans_1_text},
        headers=headers_a,
    )
    assert next_res_1.status_code == 200, f"Next question 1 failed: {next_res_1.text}"
    next_data_1 = next_res_1.json()

    # Validate response schema
    VoiceNextQuestionResponse(**next_data_1)

    assert next_data_1["interview_complete"] is False
    assert next_data_1["is_last_question"] is False
    assert next_data_1["next_question"] is not None
    assert next_data_1["next_question"]["question_number"] == 2
    assert len(next_data_1["next_question"]["question"]) > 10
    assert next_data_1["acknowledgement"] is not None
    assert next_data_1["evaluation"] is not None
    assert next_data_1["evaluation"]["overall_score"] is not None

    q2_text = next_data_1["next_question"]["question"]
    print(f"[PASS] Answer 1 evaluated (Score: {next_data_1['evaluation']['overall_score']}/10).")
    print(f"       AI Interviewer Acknowledgement: '{next_data_1['acknowledgement']}'")
    print(f"       AI Generated Next Question (Q2): '{q2_text}'")
    print(f"       Reason: '{next_data_1.get('reason')}'")

    # -------------------------------------------------------------------------
    # 7. Verify Database Persistence of Dynamically Generated Question
    # -------------------------------------------------------------------------
    print("\n[Test 7] Verifying Dynamic Question Persisted in MongoDB Question Set...")
    active_sess = client.get("/api/voice-interview/active", headers=headers_a).json()
    assert active_sess["current_question"] == 2
    q2_stored = next(q for q in active_sess["questions"] if q["question_number"] == 2)
    assert q2_stored["question"] == q2_text
    print("[PASS] MongoDB question set and active session dynamically updated with Question 2.")

    # -------------------------------------------------------------------------
    # 8. Answering Question 2 -> Dynamic Follow-up Question 3
    # -------------------------------------------------------------------------
    print("\n[Test 8] Answering Question 2 with Team/Architecture details -> Generating Question 3...")
    ans_2_text = (
        "We used compound indexes on tenant_id and timestamp, and added Redis caching with TTL to prevent "
        "cache stampedes. Our team also had daily standups to align on schema migrations."
    )
    next_res_2 = client.post(
        "/api/voice-interview/next-question",
        json={"session_id": session_id, "question_number": 2, "transcript": ans_2_text},
        headers=headers_a,
    )
    assert next_res_2.status_code == 200, f"Next question 2 failed: {next_res_2.text}"
    next_data_2 = next_res_2.json()

    assert next_data_2["interview_complete"] is False
    assert next_data_2["next_question"]["question_number"] == 3
    assert next_data_2["evaluation"] is not None
    print(f"[PASS] Answer 2 evaluated (Score: {next_data_2['evaluation']['overall_score']}/10).")
    print(f"       AI Generated Next Question (Q3): '{next_data_2['next_question']['question']}'")

    # -------------------------------------------------------------------------
    # 9. Answering Question 3 & 4 -> Dynamic Follow-up Questions 4 & 5
    # -------------------------------------------------------------------------
    print("\n[Test 9] Answering Question 3 and 4...")
    ans_3_text = (
        "When an unexpected outage occurred, we checked Datadog APM metrics, identified a database connection pool "
        "exhaustion bug, rolled back the faulty migration, and added an integration test to prevent regressions."
    )
    next_res_3 = client.post(
        "/api/voice-interview/next-question",
        json={"session_id": session_id, "question_number": 3, "transcript": ans_3_text},
        headers=headers_a,
    )
    assert next_res_3.status_code == 200
    next_data_3 = next_res_3.json()
    assert next_data_3["next_question"]["question_number"] == 4

    ans_4_text = (
        "I implemented OAuth2 and JWT authentication with short-lived access tokens and refresh token rotation, "
        "storing tokens securely with HttpOnly cookies to mitigate XSS attacks."
    )
    next_res_4 = client.post(
        "/api/voice-interview/next-question",
        json={"session_id": session_id, "question_number": 4, "transcript": ans_4_text},
        headers=headers_a,
    )
    assert next_res_4.status_code == 200
    next_data_4 = next_res_4.json()
    assert next_data_4["next_question"]["question_number"] == 5
    print(f"[PASS] Questions 3 and 4 evaluated; AI generated Question 5.")

    # -------------------------------------------------------------------------
    # 10. Answering Question 5 (Final Question) -> Interview Completion
    # -------------------------------------------------------------------------
    print("\n[Test 10] Answering Final Question 5 -> Verifying Session Completion...")
    ans_5_text = (
        "For CI/CD we used GitHub Actions with automated linting, pytest suites, and Docker image builds "
        "pushed to AWS ECR, followed by zero-downtime rolling deployments."
    )
    next_res_5 = client.post(
        "/api/voice-interview/next-question",
        json={"session_id": session_id, "question_number": 5, "transcript": ans_5_text},
        headers=headers_a,
    )
    assert next_res_5.status_code == 200, f"Final question submission failed: {next_res_5.text}"
    next_data_5 = next_res_5.json()

    assert next_data_5["interview_complete"] is True
    assert next_data_5["is_last_question"] is True
    assert next_data_5["next_question"] is None
    assert next_data_5["session_status"] == "completed"
    assert next_data_5["evaluation"] is not None
    print(f"[PASS] Final question completed. Session status set to 'completed'. Next question is None.")

    # -------------------------------------------------------------------------
    # 11. Generating Final Evaluation Report for Dynamic Session
    # -------------------------------------------------------------------------
    print("\n[Test 11] Generating Final Comprehensive Report for Dynamic Interview...")
    report_res = client.get(f"/api/voice-interview/report/{session_id}", headers=headers_a)
    assert report_res.status_code == 200, f"Final report failed: {report_res.text}"
    report_data = report_res.json()

    FinalInterviewReportResponse(**report_data)
    assert report_data["total_questions"] == 5
    assert report_data["answered_questions"] == 5
    assert report_data["evaluated_questions"] == 5
    assert report_data["overall_score"] > 0
    assert len(report_data["evaluations"]) == 5
    print(f"[PASS] Comprehensive Final Report generated successfully!")
    print(f"       Overall Score: {report_data['overall_score']}/10 ({report_data['score_percentage']}%)")
    print(f"       Total Evaluated Questions: {report_data['evaluated_questions']}")
    print(f"       Strengths: {report_data['strong_areas'][:2]}")
    print(f"       Growth Areas: {report_data['weak_areas'][:2]}")

    print("\n==================================================")
    print("ALL AI INTERVIEWER DYNAMIC TESTS PASSED (100% SUCCESS)!")
    print("==================================================")


if __name__ == "__main__":
    run_voice_interviewer_tests()
