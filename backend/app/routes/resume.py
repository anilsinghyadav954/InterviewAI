from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import List

from app.routes.auth import get_current_user
from app.schemas.resume import ResumeAnalysisResponse, ResumeHistoryItem
from app.services.resume_service import (
    analyze_resume,
    save_resume_analysis,
    get_user_resume_history,
    get_resume_analysis_by_id,
    delete_resume_analysis,
)

router = APIRouter(prefix="/api/resume", tags=["Resume Analyzer"])


import os
from app.utils.rate_limiter import resume_limiter

@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload PDF resume, extract text, run AI analysis, and persist report",
)
async def analyze_uploaded_resume(
    file: UploadFile = File(..., description="PDF or text resume file"),
    job_role: str = Form("Full Stack Developer", description="Target role to benchmark against"),
    current_user: dict = Depends(get_current_user),
):
    # 1. Rate limiting check (abuse prevention)
    resume_limiter.check_rate_limit(current_user["id"])

    # 2. Validate filename and sanitize against path traversal
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename."
        )

    safe_filename = os.path.basename(file.filename.replace("\\", "/"))
    allowed_extensions = (".pdf", ".txt")
    if not any(safe_filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF (.pdf) and text (.txt) files are currently supported."
        )

    # 3. Read bytes and validate size (Max 5MB)
    content = await file.read()
    max_size = 5 * 1024 * 1024  # 5MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 5MB limit. Please upload a smaller resume document."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # 4. Strict content validation (magic header check)
    if safe_filename.lower().endswith(".pdf"):
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF format. The file header does not match standard PDF specifications."
            )
    elif safe_filename.lower().endswith(".txt"):
        if b"\x00" in content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid text format. Binary characters or null bytes detected in text file."
            )

    # 5. Perform analysis (PDF text extraction -> Gemini / smart NLP engine)
    analysis_result = analyze_resume(content, safe_filename, job_role)

    # 6. Persist analysis to MongoDB linked to authenticated candidate
    saved_doc = save_resume_analysis(
        user_id=current_user["id"],
        filename=safe_filename,
        job_role=job_role,
        analysis=analysis_result,
    )

    return saved_doc


@router.get(
    "/history",
    response_model=List[ResumeHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get user's past resume audit history",
)
def get_history(current_user: dict = Depends(get_current_user)):
    return get_user_resume_history(current_user["id"])


@router.get(
    "/{analysis_id}",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full details of a specific past resume analysis report",
)
def get_analysis_details(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    doc = get_resume_analysis_by_id(current_user["id"], analysis_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis record not found or access denied."
        )
    return doc


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a past resume analysis from history",
)
def remove_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = delete_resume_analysis(current_user["id"], analysis_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume record not found or already deleted."
        )
    return {"message": "Resume analysis record deleted successfully"}
