import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

logger = logging.getLogger(__name__)

from app.routes.auth import get_current_user
from app.schemas.interview import (
    QuestionGenerationRequest,
    QuestionSetResponse,
    QuestionHistoryItem,
    QuestionItem,
    AnswerEvaluationRequest,
    AnswerEvaluationResponse,
    FinalInterviewReportResponse,
    InterviewDashboardMetricsResponse,
)
from app.services.ai_service import (
    get_latest_resume_for_user,
    generate_interview_questions,
    save_question_set,
    get_user_question_history,
    get_question_set_by_id,
    evaluate_interview_answer,
    save_answer_evaluation,
    get_answer_evaluation,
    get_question_set_evaluations,
    generate_final_interview_report,
    get_user_dashboard_metrics,
)

router = APIRouter(prefix="/api/interview", tags=["AI Interview Question Generator & Evaluation"])


from app.utils.rate_limiter import question_gen_limiter, evaluation_limiter

@router.post(
    "/generate-questions",
    response_model=QuestionSetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate personalized AI interview questions using Gemini",
)
def generate_questions(
    request: QuestionGenerationRequest,
    current_user: dict = Depends(get_current_user),
):
    # 0. Check rate limiting for question generation
    question_gen_limiter.check_rate_limit(current_user["id"])

    # 1. Check if user has an existing resume analysis from Phase 3
    latest_resume = get_latest_resume_for_user(current_user["id"])
    resume_based = False
    resume_context = None

    if latest_resume and latest_resume.get("detected_skills"):
        resume_based = True
        resume_context = {
            "detected_skills": latest_resume.get("detected_skills", []),
            "job_role": latest_resume.get("job_role", ""),
            "extracted_summary": latest_resume.get("extracted_summary", ""),
        }

    # 2. Call AI service to generate questions with Gemini (or smart fallback)
    raw_questions = generate_interview_questions(
        target_role=request.target_role,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        number_of_questions=request.number_of_questions,
        resume_context=resume_context,
    )

    # 3. Validate against Pydantic QuestionItem schema
    validated_questions = []
    for idx, q in enumerate(raw_questions[:request.number_of_questions], start=1):
        try:
            q_copy = dict(q)
            q_copy["question_number"] = idx
            q_copy["difficulty"] = q_copy.get("difficulty") or request.difficulty
            item = QuestionItem(**q_copy)
            validated_questions.append(item.model_dump())
        except Exception as e:
            logger.warning(f"Question validation recovery for index {idx}: {e}")
            item = QuestionItem(
                question_number=idx,
                question=q.get("question") or f"Explain core concepts and real-world application in {request.target_role}.",
                category=q.get("category") or ("Technical" if request.interview_type != "HR" else "HR"),
                topic=q.get("topic") or request.target_role,
                difficulty=request.difficulty,
                expected_focus=q.get("expected_focus") or ["Core principles", "Practical application"],
            )
            validated_questions.append(item.model_dump())

    if len(validated_questions) != request.number_of_questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate the requested number of questions. Please retry.",
        )

    # 4. Save question set to MongoDB collection 'interview_question_sets'
    saved_doc = save_question_set(
        user_id=current_user["id"],
        target_role=request.target_role,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        number_of_questions=request.number_of_questions,
        resume_based=resume_based,
        questions=validated_questions,
    )

    return saved_doc


@router.get(
    "/question-history",
    response_model=List[QuestionHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get user's past generated question sets",
)
def get_history(current_user: dict = Depends(get_current_user)):
    return get_user_question_history(current_user["id"])


@router.get(
    "/resume-status",
    status_code=status.HTTP_200_OK,
    summary="Check if authenticated user has a Phase 3 resume analysis for personalization",
)
def get_resume_status(current_user: dict = Depends(get_current_user)):
    latest_resume = get_latest_resume_for_user(current_user["id"])
    if latest_resume and latest_resume.get("detected_skills"):
        return {
            "has_resume": True,
            "filename": latest_resume.get("filename", "resume.pdf"),
            "job_role": latest_resume.get("job_role", ""),
            "detected_skills": latest_resume.get("detected_skills", [])[:8],
            "overall_score": latest_resume.get("overall_score", 0),
        }
    return {
        "has_resume": False,
        "filename": None,
        "job_role": None,
        "detected_skills": [],
        "overall_score": 0,
    }


@router.get(
    "/questions/{question_set_id}",
    response_model=QuestionSetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific question set (owner only)",
)
def get_question_set(
    question_set_id: str,
    current_user: dict = Depends(get_current_user),
):
    doc = get_question_set_by_id(current_user["id"], question_set_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found."
        )
    return doc


# ==============================================================================
# Phase 5: AI Answer Evaluation & Final Report Endpoints
# ==============================================================================

@router.post(
    "/evaluate-answer",
    response_model=AnswerEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit candidate answer for AI evaluation and per-question scoring",
)
def evaluate_answer(
    request: AnswerEvaluationRequest,
    current_user: dict = Depends(get_current_user),
):
    # 0. Check rate limiting for answer evaluation
    evaluation_limiter.check_rate_limit(current_user["id"])

    # 1. Reject empty answer with HTTP 400
    answer_text = request.candidate_answer.strip()
    if not answer_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an answer before evaluating.",
        )

    # 2. Retrieve question set and verify ownership
    qset = get_question_set_by_id(current_user["id"], request.question_set_id)
    if not qset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found.",
        )

    # 3. Retrieve actual stored question by question_number
    questions = qset.get("questions", [])
    target_q = None
    for q in questions:
        if q.get("question_number") == request.question_number:
            target_q = q
            break

    if not target_q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question number {request.question_number} not found in this question set.",
        )

    # 4. Evaluate answer against stored question context
    eval_result = evaluate_interview_answer(
        target_role=qset.get("target_role", "Software Developer"),
        interview_type=qset.get("interview_type", "Technical"),
        difficulty=target_q.get("difficulty", qset.get("difficulty", "Intermediate")),
        question=target_q["question"],
        category=target_q.get("category", "Technical"),
        topic=target_q.get("topic", qset.get("target_role", "Software Developer")),
        expected_focus=target_q.get("expected_focus", []),
        candidate_answer=answer_text,
    )

    # 5. Persist evaluation
    saved_eval = save_answer_evaluation(
        user_id=current_user["id"],
        question_set_id=request.question_set_id,
        question_number=request.question_number,
        candidate_answer=answer_text,
        eval_data=eval_result,
    )

    return saved_eval


@router.get(
    "/evaluation/{question_set_id}/{question_number}",
    response_model=AnswerEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single question evaluation (owner only)",
)
def get_single_evaluation(
    question_set_id: str,
    question_number: int,
    current_user: dict = Depends(get_current_user),
):
    eval_doc = get_answer_evaluation(current_user["id"], question_set_id, question_number)
    if not eval_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation for question {question_number} not found.",
        )
    return eval_doc


@router.get(
    "/evaluations/{question_set_id}",
    response_model=List[AnswerEvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all evaluated answers for a question set (owner only)",
)
def get_set_evaluations(
    question_set_id: str,
    current_user: dict = Depends(get_current_user),
):
    return get_question_set_evaluations(current_user["id"], question_set_id)


@router.get(
    "/report/{question_set_id}",
    response_model=FinalInterviewReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate comprehensive final interview report with aggregated scores (owner only)",
)
def get_final_report(
    question_set_id: str,
    current_user: dict = Depends(get_current_user),
):
    return generate_final_interview_report(current_user["id"], question_set_id)


@router.get(
    "/dashboard-stats",
    response_model=InterviewDashboardMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get candidate interview scoring statistics for dashboard",
)
def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    return get_user_dashboard_metrics(current_user["id"])

