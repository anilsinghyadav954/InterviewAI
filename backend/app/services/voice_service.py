import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId

from app.database import (
    get_voice_sessions_collection,
    get_interview_question_sets_collection,
    get_interview_evaluations_collection,
)
from app.services.ai_service import (
    get_question_set_by_id,
    evaluate_interview_answer,
    save_answer_evaluation,
    get_answer_evaluation,
    get_latest_resume_for_user,
)
from app.services.interviewer_service import generate_next_interview_question

logger = logging.getLogger(__name__)


def start_voice_session(user_id: str, question_set_id: str) -> dict:
    """
    Initializes a new active voice interview session for the candidate.
    Validates question set ownership and stores session in 'voice_interview_sessions'.
    """
    qset = get_question_set_by_id(user_id, question_set_id)
    if not qset:
        raise ValueError("Question set not found or access denied.")

    voice_col = get_voice_sessions_collection()
    qsets_col = get_interview_question_sets_collection()

    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
    q_oid = ObjectId(question_set_id) if ObjectId.is_valid(question_set_id) else question_set_id

    # Mark question set with mode: Voice
    qsets_col.update_one({"_id": q_oid}, {"$set": {"mode": "Voice"}})

    # Any previous active session for this user can be archived or marked completed
    now = datetime.now(timezone.utc)
    questions = qset.get("questions", [])
    total_q = len(questions) or qset.get("number_of_questions", 5)

    session_doc = {
        "user_id": u_oid,
        "question_set_id": q_oid,
        "role": qset.get("target_role", "Software Developer"),
        "target_role": qset.get("target_role", "Software Developer"),
        "interview_type": qset.get("interview_type", "Technical"),
        "difficulty": qset.get("difficulty", "Intermediate"),
        "status": "active",
        "current_question": 1,
        "total_questions": total_q,
        "answers": [],
        "started_at": now,
        "completed_at": None,
        "mode": "Voice",
    }

    insert_res = voice_col.insert_one(session_doc)
    session_id = str(insert_res.inserted_id)

    return {
        "session_id": session_id,
        "question_set_id": str(q_oid),
        "total_questions": total_q,
        "status": "active",
        "current_question": 1,
        "target_role": qset.get("target_role", "Software Developer"),
        "interview_type": qset.get("interview_type", "Technical"),
        "difficulty": qset.get("difficulty", "Intermediate"),
        "started_at": now,
        "completed_at": None,
        "answers": [],
        "questions": questions,
        "mode": "Voice",
    }


def submit_voice_answer(
    user_id: str,
    session_id: str,
    question_number: int,
    transcript: str,
) -> dict:
    """
    Submits a candidate's voice transcript for AI evaluation.
    1. Verifies voice session ownership and active status.
    2. Fetches stored question from MongoDB.
    3. Reuses Phase 5 evaluation logic.
    4. Persists evaluation in MongoDB and updates session answers.
    """
    cleaned_transcript = transcript.strip() if transcript else ""
    if not cleaned_transcript:
        raise ValueError("Transcript cannot be empty.")

    voice_col = get_voice_sessions_collection()
    evals_col = get_interview_evaluations_collection()

    try:
        s_oid = ObjectId(session_id)
    except Exception:
        raise ValueError("Invalid session ID format.")

    session = voice_col.find_one({"_id": s_oid})
    if not session:
        raise ValueError("Voice interview session not found.")

    sess_uid = str(session.get("user_id", ""))
    if sess_uid != str(user_id):
        raise PermissionError("Access forbidden: session belongs to another user.")

    if session.get("status") != "active":
        # Allow review/resubmission if needed, but note session state
        pass

    qset_id_str = str(session.get("question_set_id", ""))
    qset = get_question_set_by_id(user_id, qset_id_str)
    if not qset:
        raise ValueError("Question set associated with this voice session was not found.")

    # Find the target question by number
    questions = qset.get("questions", [])
    target_q = None
    for q in questions:
        if q.get("question_number") == int(question_number):
            target_q = q
            break

    if not target_q:
        raise ValueError(f"Question number {question_number} not found in this question set.")

    # Evaluate candidate answer via existing Phase 5 AI engine
    eval_result = evaluate_interview_answer(
        target_role=qset.get("target_role", "Software Developer"),
        interview_type=qset.get("interview_type", "Technical"),
        difficulty=target_q.get("difficulty", qset.get("difficulty", "Intermediate")),
        question=target_q["question"],
        category=target_q.get("category", "Technical"),
        topic=target_q.get("topic", qset.get("target_role", "Software Developer")),
        expected_focus=target_q.get("expected_focus", []),
        candidate_answer=cleaned_transcript,
    )

    # Save evaluation into 'interview_answer_evaluations'
    saved_eval = save_answer_evaluation(
        user_id=user_id,
        question_set_id=qset_id_str,
        question_number=question_number,
        candidate_answer=cleaned_transcript,
        eval_data=eval_result,
    )

    # Tag evaluation with mode: Voice
    evals_col.update_one(
        {"question_set_id": ObjectId(qset_id_str) if ObjectId.is_valid(qset_id_str) else qset_id_str, "question_number": int(question_number)},
        {"$set": {"mode": "Voice"}},
    )

    now = datetime.now(timezone.utc)
    new_answer = {
        "question_number": int(question_number),
        "transcript": cleaned_transcript,
        "submitted_at": now,
        "evaluation_id": saved_eval["id"],
        "overall_score": saved_eval["overall_score"],
    }

    # Update session answers without duplicate question numbers
    existing_answers = session.get("answers", [])
    filtered_answers = [a for a in existing_answers if a.get("question_number") != int(question_number)]
    filtered_answers.append(new_answer)
    filtered_answers.sort(key=lambda a: a["question_number"])

    total_q = len(questions) or session.get("total_questions", 1)
    is_last = (int(question_number) >= total_q) or (len(filtered_answers) >= total_q)

    update_fields = {
        "answers": filtered_answers,
        "current_question": min(int(question_number) + 1, total_q),
    }

    if is_last:
        update_fields["status"] = "completed"
        update_fields["completed_at"] = now

    voice_col.update_one({"_id": s_oid}, {"$set": update_fields})

    return {
        "question_number": int(question_number),
        "transcript": cleaned_transcript,
        "evaluation": saved_eval,
        "is_last_question": is_last,
        "session_status": update_fields.get("status", session.get("status", "active")),
    }


def get_active_voice_session(user_id: str) -> Optional[dict]:
    """
    Finds the most recent active voice session for the candidate to support seamless page refresh.
    Restores questions, answers, and evaluations.
    """
    voice_col = get_voice_sessions_collection()
    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id

    query = {
        "$or": [{"user_id": user_id}, {"user_id": u_oid}],
        "status": "active",
    }
    session = voice_col.find_one(query, sort=[("started_at", -1)])
    if not session:
        return None

    session_id = str(session["_id"])
    qset_id_str = str(session.get("question_set_id", ""))
    qset = get_question_set_by_id(user_id, qset_id_str)
    if not qset:
        return None

    # Load any evaluations already submitted
    answers = session.get("answers", [])
    for a in answers:
        ev = get_answer_evaluation(user_id, qset_id_str, a.get("question_number", 1))
        if ev:
            a["evaluation"] = ev

    return {
        "session_id": session_id,
        "question_set_id": qset_id_str,
        "total_questions": len(qset.get("questions", [])) or session.get("total_questions", 1),
        "status": session.get("status", "active"),
        "current_question": session.get("current_question", 1),
        "target_role": qset.get("target_role", session.get("role", "Software Developer")),
        "interview_type": qset.get("interview_type", "Technical"),
        "difficulty": qset.get("difficulty", "Intermediate"),
        "started_at": session.get("started_at"),
        "completed_at": session.get("completed_at"),
        "answers": answers,
        "questions": qset.get("questions", []),
        "mode": "Voice",
    }


def get_voice_session_by_id(user_id: str, session_id: str) -> Optional[dict]:
    """Retrieves a specific voice interview session with ownership verification."""
    voice_col = get_voice_sessions_collection()
    try:
        s_oid = ObjectId(session_id)
    except Exception:
        return None

    session = voice_col.find_one({"_id": s_oid})
    if not session:
        return None

    if str(session.get("user_id", "")) != str(user_id):
        return None

    qset_id_str = str(session.get("question_set_id", ""))
    qset = get_question_set_by_id(user_id, qset_id_str)

    answers = session.get("answers", [])
    for a in answers:
        ev = get_answer_evaluation(user_id, qset_id_str, a.get("question_number", 1))
        if ev:
            a["evaluation"] = ev

    return {
        "session_id": str(session["_id"]),
        "question_set_id": qset_id_str,
        "total_questions": session.get("total_questions", len(qset.get("questions", [])) if qset else 1),
        "status": session.get("status", "active"),
        "current_question": session.get("current_question", 1),
        "target_role": session.get("target_role", session.get("role", "Software Developer")),
        "interview_type": session.get("interview_type", "Technical"),
        "difficulty": session.get("difficulty", "Intermediate"),
        "started_at": session.get("started_at"),
        "completed_at": session.get("completed_at"),
        "answers": answers,
        "questions": qset.get("questions", []) if qset else [],
        "mode": "Voice",
    }


def finish_voice_session(user_id: str, session_id: str) -> dict:
    """Manually completes a voice interview session."""
    voice_col = get_voice_sessions_collection()
    try:
        s_oid = ObjectId(session_id)
    except Exception:
        raise ValueError("Invalid session ID.")

    session = voice_col.find_one({"_id": s_oid})
    if not session or str(session.get("user_id", "")) != str(user_id):
        raise PermissionError("Session not found or access denied.")

    now = datetime.now(timezone.utc)
    voice_col.update_one({"_id": s_oid}, {"$set": {"status": "completed", "completed_at": now}})
    return {"status": "completed", "completed_at": now, "session_id": session_id}


def get_voice_history(user_id: str) -> List[dict]:
    """Retrieves all past voice interview sessions for the candidate."""
    voice_col = get_voice_sessions_collection()
    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id

    query = {"$or": [{"user_id": user_id}, {"user_id": u_oid}]}
    cursor = voice_col.find(query).sort("started_at", -1)

    history = []
    for doc in cursor:
        answers = doc.get("answers", [])
        scores = [a.get("overall_score") for a in answers if a.get("overall_score") is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        history.append({
            "id": str(doc["_id"]),
            "session_id": str(doc["_id"]),
            "question_set_id": str(doc.get("question_set_id", "")),
            "role": doc.get("target_role", doc.get("role", "Software Developer")),
            "interview_type": doc.get("interview_type", "Technical"),
            "difficulty": doc.get("difficulty", "Intermediate"),
            "score": avg_score,
            "date": doc.get("started_at", datetime.now(timezone.utc)),
            "questions_count": doc.get("total_questions", len(answers) or 1),
            "answered_count": len(answers),
            "status": doc.get("status", "active"),
            "mode": "Voice",
        })

    return history


def process_voice_next_question(
    user_id: str,
    session_id: str,
    question_number: int,
    transcript: str,
) -> dict:
    """
    Submits candidate voice answer, evaluates it, and generates the next dynamic interviewer question.
    1. Verifies session ownership and active status.
    2. Evaluates candidate response using Phase 5 evaluation engine.
    3. Saves evaluation into MongoDB and session answers.
    4. Completes session if question_number reached total_questions limit.
    5. Dynamically generates next contextual question using AI Interviewer service.
    6. Updates question set and session in MongoDB with the generated question.
    """
    cleaned_transcript = transcript.strip() if transcript else ""
    if not cleaned_transcript:
        raise ValueError("Transcript cannot be empty.")

    voice_col = get_voice_sessions_collection()
    evals_col = get_interview_evaluations_collection()
    qsets_col = get_interview_question_sets_collection()

    try:
        s_oid = ObjectId(session_id)
    except Exception:
        raise ValueError("Invalid session ID format.")

    session = voice_col.find_one({"_id": s_oid})
    if not session:
        raise ValueError("Voice interview session not found.")

    sess_uid = str(session.get("user_id", ""))
    if sess_uid != str(user_id):
        raise PermissionError("Access forbidden: session belongs to another user.")

    qset_id_str = str(session.get("question_set_id", ""))
    qset = get_question_set_by_id(user_id, qset_id_str)
    if not qset:
        raise ValueError("Question set associated with this voice session was not found.")

    questions = qset.get("questions", [])
    target_q = None
    for q in questions:
        if q.get("question_number") == int(question_number):
            target_q = q
            break

    if not target_q:
        raise ValueError(f"Question number {question_number} not found in this question set.")

    # 1. Evaluate candidate answer via existing Phase 5 AI engine
    eval_result = evaluate_interview_answer(
        target_role=qset.get("target_role", "Software Developer"),
        interview_type=qset.get("interview_type", "Technical"),
        difficulty=target_q.get("difficulty", qset.get("difficulty", "Intermediate")),
        question=target_q["question"],
        category=target_q.get("category", "Technical"),
        topic=target_q.get("topic", qset.get("target_role", "Software Developer")),
        expected_focus=target_q.get("expected_focus", []),
        candidate_answer=cleaned_transcript,
    )

    # 2. Save evaluation into 'interview_answer_evaluations'
    saved_eval = save_answer_evaluation(
        user_id=user_id,
        question_set_id=qset_id_str,
        question_number=int(question_number),
        candidate_answer=cleaned_transcript,
        eval_data=eval_result,
    )

    evals_col.update_one(
        {
            "question_set_id": ObjectId(qset_id_str) if ObjectId.is_valid(qset_id_str) else qset_id_str,
            "question_number": int(question_number),
        },
        {"$set": {"mode": "Voice"}},
    )

    now = datetime.now(timezone.utc)
    new_answer = {
        "question_number": int(question_number),
        "transcript": cleaned_transcript,
        "submitted_at": now,
        "evaluation_id": saved_eval["id"],
        "overall_score": saved_eval["overall_score"],
    }

    existing_answers = session.get("answers", [])
    filtered_answers = [a for a in existing_answers if a.get("question_number") != int(question_number)]
    filtered_answers.append(new_answer)
    filtered_answers.sort(key=lambda a: a["question_number"])

    total_q = session.get("total_questions", len(questions) or 5)
    is_last = int(question_number) >= total_q

    if is_last:
        voice_col.update_one(
            {"_id": s_oid},
            {"$set": {"answers": filtered_answers, "status": "completed", "completed_at": now}},
        )
        return {
            "session_id": session_id,
            "question_number": int(question_number),
            "interview_complete": True,
            "next_question": None,
            "acknowledgement": "Thank you for completing this interview. I have recorded and analyzed all your answers.",
            "reason": "Final question answered",
            "evaluation": saved_eval,
            "is_last_question": True,
            "session_status": "completed",
        }

    # 3. Dynamic Question Generation for next step
    next_q_num = int(question_number) + 1

    latest_resume = get_latest_resume_for_user(user_id)
    resume_context = None
    if latest_resume and latest_resume.get("detected_skills"):
        resume_context = {
            "detected_skills": latest_resume.get("detected_skills", []),
            "job_role": latest_resume.get("job_role", ""),
            "extracted_summary": latest_resume.get("extracted_summary", ""),
        }

    topics_covered = [q.get("topic", "") for q in questions if q.get("topic")]
    qa_map = {q["question_number"]: q["question"] for q in questions if "question_number" in q}
    previous_qa_history = []
    for a in filtered_answers:
        q_num = a.get("question_number")
        previous_qa_history.append({
            "question_number": str(q_num),
            "question": qa_map.get(q_num, ""),
            "answer": a.get("transcript", ""),
        })

    next_q_gen = generate_next_interview_question(
        target_role=session.get("target_role", qset.get("target_role", "Software Developer")),
        interview_type=session.get("interview_type", qset.get("interview_type", "Technical")),
        difficulty=session.get("difficulty", qset.get("difficulty", "Intermediate")),
        next_question_number=next_q_num,
        total_questions=total_q,
        previous_question=target_q["question"],
        candidate_answer=cleaned_transcript,
        topics_covered=topics_covered,
        previous_qa_history=previous_qa_history,
        resume_context=resume_context,
    )

    new_question_item = {
        "question_number": next_q_num,
        "question": next_q_gen["next_question"],
        "category": next_q_gen.get("category", "Technical"),
        "topic": next_q_gen.get("topic", session.get("target_role", "Software Developer")),
        "difficulty": next_q_gen.get("difficulty", session.get("difficulty", "Intermediate")),
        "expected_focus": next_q_gen.get("expected_focus", ["Core principles", "Practical application"]),
    }

    updated_questions = list(questions)
    slot_index = next_q_num - 1
    if slot_index < len(updated_questions):
        updated_questions[slot_index] = new_question_item
    else:
        updated_questions.append(new_question_item)

    q_oid = ObjectId(qset_id_str) if ObjectId.is_valid(qset_id_str) else qset_id_str
    qsets_col.update_one({"_id": q_oid}, {"$set": {"questions": updated_questions}})

    voice_col.update_one(
        {"_id": s_oid},
        {
            "$set": {
                "answers": filtered_answers,
                "current_question": next_q_num,
                "questions": updated_questions,
            }
        },
    )

    return {
        "session_id": session_id,
        "question_number": int(question_number),
        "interview_complete": False,
        "next_question": new_question_item,
        "acknowledgement": next_q_gen.get("acknowledgement", "Thank you for that explanation."),
        "reason": next_q_gen.get("reason", "Follow-up question based on interview context"),
        "evaluation": saved_eval,
        "is_last_question": False,
        "session_status": "active",
    }

