import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

from app.routes.auth import get_current_user
from app.schemas.voice import (
    VoiceSessionStartRequest,
    VoiceAnswerSubmitRequest,
    VoiceSessionResponse,
    VoiceAnswerResponse,
    VoiceHistoryItem,
    VoiceNextQuestionRequest,
    VoiceNextQuestionResponse,
)
from app.schemas.interview import FinalInterviewReportResponse
from app.services.voice_service import (
    start_voice_session,
    submit_voice_answer,
    process_voice_next_question,
    get_active_voice_session,
    get_voice_session_by_id,
    finish_voice_session,
    get_voice_history,
)
from app.services.ai_service import generate_final_interview_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-interview", tags=["Voice Interview & Speech-to-Text"])


@router.post(
    "/start",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize an active voice interview session from a question set",
)
def start_session(
    request: VoiceSessionStartRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        session = start_voice_session(
            user_id=current_user["id"],
            question_set_id=request.question_set_id,
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting voice session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize voice interview session.",
        )


from app.utils.rate_limiter import evaluation_limiter

@router.post(
    "/answer",
    response_model=VoiceAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit candidate voice transcript for AI evaluation",
)
def submit_answer(
    request: VoiceAnswerSubmitRequest,
    current_user: dict = Depends(get_current_user),
):
    # Rate limiting check
    evaluation_limiter.check_rate_limit(current_user["id"])

    # Reject empty transcript
    if not request.transcript or not request.transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript cannot be empty. Please speak or provide an answer before submitting.",
        )

    try:
        result = submit_voice_answer(
            user_id=current_user["id"],
            session_id=request.session_id,
            question_number=request.question_number,
            transcript=request.transcript,
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error evaluating voice answer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate voice answer.",
        )


@router.post(
    "/next-question",
    response_model=VoiceNextQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit candidate voice answer, evaluate, and dynamically generate next interviewer question",
)
def next_question(
    request: VoiceNextQuestionRequest,
    current_user: dict = Depends(get_current_user),
):
    # Rate limiting check
    evaluation_limiter.check_rate_limit(current_user["id"])

    # Reject empty transcript
    if not request.transcript or not request.transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript cannot be empty. Please speak or provide an answer before submitting.",
        )

    try:
        result = process_voice_next_question(
            user_id=current_user["id"],
            session_id=request.session_id,
            question_number=request.question_number,
            transcript=request.transcript,
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing next interview question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate next interview question.",
        )



@router.get(
    "/active",
    response_model=Optional[VoiceSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve active voice session for session resumption after refresh",
)
def get_active(current_user: dict = Depends(get_current_user)):
    return get_active_voice_session(current_user["id"])


@router.get(
    "/session/{session_id}",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific voice session (owner only)",
)
def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    session = get_voice_session_by_id(current_user["id"], session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice interview session not found or access denied.",
        )
    return session


@router.post(
    "/finish/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Mark voice interview session as completed",
)
def finish_session(session_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return finish_voice_session(current_user["id"], session_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/history",
    response_model=List[VoiceHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get user's past voice interview sessions",
)
def get_history(current_user: dict = Depends(get_current_user)):
    return get_voice_history(current_user["id"])


@router.get(
    "/report/{session_id}",
    response_model=FinalInterviewReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get comprehensive evaluation report for completed voice interview",
)
def get_voice_report(session_id: str, current_user: dict = Depends(get_current_user)):
    session = get_voice_session_by_id(current_user["id"], session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice interview session not found.",
        )

    qset_id = session.get("question_set_id")
    if not qset_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No question set associated with this voice session.",
        )

    return generate_final_interview_report(current_user["id"], qset_id)
