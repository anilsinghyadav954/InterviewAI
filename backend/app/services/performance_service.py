import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.database import (
    get_database,
    get_interview_evaluations_collection,
    get_interview_question_sets_collection,
)
from app.services.ai_service import get_latest_resume_for_user

logger = logging.getLogger(__name__)


def _parse_time_cutoff(time_range: Optional[str]) -> Optional[datetime]:
    """Helper to convert time_range string into a timezone-aware UTC datetime cutoff."""
    if not time_range or time_range.lower() in ["all", "all time"]:
        return None
    now = datetime.now(timezone.utc)
    tr = time_range.lower().strip()
    if tr in ["7d", "last 7 days"]:
        return now - timedelta(days=7)
    elif tr in ["30d", "last 30 days"]:
        return now - timedelta(days=30)
    elif tr in ["90d", "last 90 days"]:
        return now - timedelta(days=90)
    return None


def _get_user_filtered_data(
    user_id: str,
    time_range: Optional[str] = None,
    interview_type: Optional[str] = None,
    target_role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetches and filters question sets and their evaluations for the authenticated user.
    Ensures strict user ownership isolation.
    """
    db = get_database()
    qsets_col = get_interview_question_sets_collection()
    evals_col = get_interview_evaluations_collection()

    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
    user_filter = {"$or": [{"user_id": user_id}, {"user_id": u_oid}]}

    cutoff = _parse_time_cutoff(time_range)

    # 1. Fetch user question sets
    qset_query = {**user_filter}
    if cutoff:
        qset_query["created_at"] = {"$gte": cutoff}
    if interview_type and interview_type.lower() != "all":
        qset_query["interview_type"] = interview_type
    if target_role and target_role.lower() != "all":
        qset_query["target_role"] = target_role

    user_qsets = list(qsets_col.find(qset_query).sort("created_at", 1))
    qset_map = {str(qs["_id"]): qs for qs in user_qsets}

    # 2. Fetch all evaluations for these sets (or for user)
    matching_qset_ids = [qs["_id"] for qs in user_qsets]
    if not matching_qset_ids:
        return {
            "qsets": [],
            "evaluations": [],
            "completed_sessions": [],
        }

    eval_query = {
        **user_filter,
        "question_set_id": {"$in": matching_qset_ids + [str(q) for q in matching_qset_ids]},
    }
    evaluations = list(evals_col.find(eval_query).sort("question_number", 1))

    # 3. Group evaluations by question_set_id
    evals_by_set: Dict[str, List[dict]] = {}
    for ev in evaluations:
        set_id_str = str(ev.get("question_set_id"))
        if set_id_str not in evals_by_set:
            evals_by_set[set_id_str] = []
        evals_by_set[set_id_str].append(ev)

    # 4. Form completed session summaries
    completed_sessions = []
    for set_id_str, qset in qset_map.items():
        set_evals = evals_by_set.get(set_id_str, [])
        if set_evals:
            scores = [e.get("overall_score", 0.0) for e in set_evals]
            session_score = round(sum(scores) / len(scores), 1)
            total_questions = qset.get("number_of_questions", len(qset.get("questions", []))) or len(set_evals)
            completion_rate = round((len(set_evals) / (total_questions or 1)) * 100, 1)

            completed_sessions.append({
                "question_set_id": set_id_str,
                "qset": qset,
                "created_at": qset.get("created_at") or datetime.now(timezone.utc),
                "score": session_score,
                "score_percentage": round((session_score / 10.0) * 100, 1),
                "evaluations": set_evals,
                "target_role": qset.get("target_role", "Software Developer"),
                "interview_type": qset.get("interview_type", "Technical"),
                "difficulty": qset.get("difficulty", "Intermediate"),
                "evaluated_count": len(set_evals),
                "total_questions": total_questions,
                "completion_rate": completion_rate,
            })

    # Sort completed sessions chronologically
    completed_sessions.sort(key=lambda s: s["created_at"])

    return {
        "qsets": user_qsets,
        "evaluations": evaluations,
        "completed_sessions": completed_sessions,
    }


def get_performance_overview(
    user_id: str,
    time_range: Optional[str] = None,
    interview_type: Optional[str] = None,
    target_role: Optional[str] = None,
) -> dict:
    """Calculates comprehensive candidate performance metrics."""
    data = _get_user_filtered_data(user_id, time_range, interview_type, target_role)
    completed_sessions = data["completed_sessions"]
    evaluations = data["evaluations"]
    total_qsets = len(data["qsets"])

    # Fetch latest resume score for user
    latest_resume = get_latest_resume_for_user(user_id)
    latest_resume_score = float(latest_resume.get("overall_score", 0.0)) if latest_resume else 0.0

    if not completed_sessions or not evaluations:
        return {
            "interviews_completed": 0,
            "average_score": 0.0,
            "average_score_percentage": 0.0,
            "best_score": 0.0,
            "best_score_percentage": 0.0,
            "questions_evaluated": 0,
            "total_practice_sessions": total_qsets,
            "latest_resume_score": latest_resume_score,
            "technical_score": 0.0,
            "communication_score": 0.0,
            "relevance_score": 0.0,
            "completeness_score": 0.0,
            "clarity_score": 0.0,
            "has_data": False,
        }

    session_scores = [s["score"] for s in completed_sessions]
    avg_score = round(sum(session_scores) / len(session_scores), 1)
    best_score = round(max(session_scores), 1)

    # Component dimensions from evaluated questions
    tech_evals = [e.get("technical_accuracy") for e in evaluations if e.get("technical_accuracy") is not None]
    tech_score = round(sum(tech_evals) / len(tech_evals), 1) if tech_evals else 0.0

    comm_scores = [e.get("communication", 0.0) for e in evaluations]
    comm_score = round(sum(comm_scores) / len(comm_scores), 1) if comm_scores else 0.0

    rel_scores = [e.get("relevance", 0.0) for e in evaluations]
    rel_score = round(sum(rel_scores) / len(rel_scores), 1) if rel_scores else 0.0

    comp_scores = [e.get("completeness", 0.0) for e in evaluations]
    comp_score = round(sum(comp_scores) / len(comp_scores), 1) if comp_scores else 0.0

    clar_scores = [e.get("clarity", 0.0) for e in evaluations]
    clar_score = round(sum(clar_scores) / len(clar_scores), 1) if clar_scores else 0.0

    return {
        "interviews_completed": len(completed_sessions),
        "average_score": avg_score,
        "average_score_percentage": round((avg_score / 10.0) * 100, 1),
        "best_score": best_score,
        "best_score_percentage": round((best_score / 10.0) * 100, 1),
        "questions_evaluated": len(evaluations),
        "total_practice_sessions": total_qsets,
        "latest_resume_score": latest_resume_score,
        "technical_score": tech_score,
        "communication_score": comm_score,
        "relevance_score": rel_score,
        "completeness_score": comp_score,
        "clarity_score": clar_score,
        "has_data": True,
    }


def get_performance_trend(
    user_id: str,
    time_range: Optional[str] = None,
    interview_type: Optional[str] = None,
    target_role: Optional[str] = None,
) -> List[dict]:
    """Returns chronological interview score datapoints for line chart rendering."""
    data = _get_user_filtered_data(user_id, time_range, interview_type, target_role)
    completed_sessions = data["completed_sessions"]

    trend = []
    for s in completed_sessions:
        dt = s["created_at"]
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except Exception:
                dt = datetime.now(timezone.utc)
        
        iso_date = dt.strftime("%Y-%m-%d")
        display_date = dt.strftime("%b %d")

        trend.append({
            "interview_id": s["question_set_id"],
            "date": iso_date,
            "display_date": display_date,
            "score": s["score"],
            "score_percentage": s["score_percentage"],
            "role": s["target_role"],
            "type": s["interview_type"],
            "interview_type": s["interview_type"],
            "difficulty": s["difficulty"],
        })

    return trend


def get_skill_performance(
    user_id: str,
    time_range: Optional[str] = None,
    interview_type: Optional[str] = None,
    target_role: Optional[str] = None,
) -> List[dict]:
    """Aggregates topic/skill performance across evaluated questions."""
    data = _get_user_filtered_data(user_id, time_range, interview_type, target_role)
    qset_map = {str(qs["_id"]): qs for qs in data["qsets"]}
    evaluations = data["evaluations"]

    skill_buckets: Dict[str, Dict[str, Any]] = {}

    for ev in evaluations:
        set_id_str = str(ev.get("question_set_id"))
        qset = qset_map.get(set_id_str)
        q_num = ev.get("question_number", 1)

        # Lookup question topic from question set
        topic = "General Concepts"
        cat = "Technical"
        if qset and "questions" in qset:
            for q in qset["questions"]:
                if q.get("question_number") == q_num:
                    topic = q.get("topic") or topic
                    cat = q.get("category") or cat
                    break

        clean_topic = topic.strip()
        if clean_topic not in skill_buckets:
            skill_buckets[clean_topic] = {
                "scores": [],
                "category": cat,
            }
        skill_buckets[clean_topic]["scores"].append(ev.get("overall_score", 0.0))

    results = []
    for skill, bucket in skill_buckets.items():
        sc = bucket["scores"]
        avg_score = round(sum(sc) / len(sc), 1)
        results.append({
            "skill": skill,
            "score": avg_score,
            "score_percentage": round((avg_score / 10.0) * 100, 1),
            "questions": len(sc),
            "questions_count": len(sc),
            "category": bucket["category"],
        })

    # Sort by questions count descending, then score descending
    results.sort(key=lambda x: (x["questions"], x["score"]), reverse=True)
    return results


def get_category_performance(
    user_id: str,
    time_range: Optional[str] = None,
    interview_type: Optional[str] = None,
    target_role: Optional[str] = None,
) -> List[dict]:
    """Aggregates performance by category (Technical, HR, Coding, Database, System Design, etc.)."""
    data = _get_user_filtered_data(user_id, time_range, interview_type, target_role)
    qset_map = {str(qs["_id"]): qs for qs in data["qsets"]}
    evaluations = data["evaluations"]

    category_buckets: Dict[str, List[float]] = {}

    for ev in evaluations:
        set_id_str = str(ev.get("question_set_id"))
        qset = qset_map.get(set_id_str)
        q_num = ev.get("question_number", 1)

        cat = "Technical"
        if qset and "questions" in qset:
            for q in qset["questions"]:
                if q.get("question_number") == q_num:
                    cat = q.get("category") or cat
                    break

        cat = cat.strip()
        if cat not in category_buckets:
            category_buckets[cat] = []
        category_buckets[cat].append(ev.get("overall_score", 0.0))

    results = []
    for cat, scores in category_buckets.items():
        avg_score = round(sum(scores) / len(scores), 1)
        results.append({
            "category": cat,
            "score": avg_score,
            "score_percentage": round((avg_score / 10.0) * 100, 1),
            "questions": len(scores),
            "questions_count": len(scores),
        })

    results.sort(key=lambda x: x["questions"], reverse=True)
    return results


def get_role_performance(
    user_id: str,
    time_range: Optional[str] = None,
    interview_type: Optional[str] = None,
) -> List[dict]:
    """Aggregates performance across target roles practiced by the candidate."""
    data = _get_user_filtered_data(user_id, time_range, interview_type, target_role=None)
    completed_sessions = data["completed_sessions"]

    role_buckets: Dict[str, List[float]] = {}
    for s in completed_sessions:
        r = s["target_role"]
        if r not in role_buckets:
            role_buckets[r] = []
        role_buckets[r].append(s["score"])

    results = []
    for role, scores in role_buckets.items():
        avg_score = round(sum(scores) / len(scores), 1)
        results.append({
            "role": role,
            "score": avg_score,
            "score_percentage": round((avg_score / 10.0) * 100, 1),
            "interviews": len(scores),
            "interviews_count": len(scores),
            "best_score": round(max(scores), 1),
            "average_score": avg_score,
        })

    results.sort(key=lambda x: x["interviews"], reverse=True)
    return results


def get_interview_type_performance(
    user_id: str,
    time_range: Optional[str] = None,
    target_role: Optional[str] = None,
) -> List[dict]:
    """Aggregates performance by interview type (Technical, HR, Mixed)."""
    data = _get_user_filtered_data(user_id, time_range, interview_type=None, target_role=target_role)
    completed_sessions = data["completed_sessions"]

    type_buckets: Dict[str, List[float]] = {}
    for s in completed_sessions:
        t = s["interview_type"]
        if t not in type_buckets:
            type_buckets[t] = []
        type_buckets[t].append(s["score"])

    results = []
    for itype in ["Technical", "HR", "Mixed"]:
        if itype in type_buckets:
            scores = type_buckets[itype]
            avg_s = round(sum(scores) / len(scores), 1)
            results.append({
                "type": itype,
                "interviews_count": len(scores),
                "interviews": len(scores),
                "average_score": avg_s,
                "score_percentage": round((avg_s / 10.0) * 100, 1),
                "best_score": round(max(scores), 1),
            })

    return results


def get_performance_insights(
    user_id: str,
    time_range: Optional[str] = None,
    interview_type: Optional[str] = None,
    target_role: Optional[str] = None,
) -> dict:
    """
    Deterministically computes strengths, weak areas, and actionable recommendations
    based on actual evaluated metrics and resume alignment.
    """
    overview = get_performance_overview(user_id, time_range, interview_type, target_role)
    skills = get_skill_performance(user_id, time_range, interview_type, target_role)
    categories = get_category_performance(user_id, time_range, interview_type, target_role)
    data = _get_user_filtered_data(user_id, time_range, interview_type, target_role)
    evaluations = data["evaluations"]

    strengths = []
    weak_areas = []
    recommendations = []

    # 1. Strengths from High-Scoring Categories and Dimensions
    if overview["technical_score"] >= 8.0:
        strengths.append(f"Strong Technical Depth ({overview['technical_score'] * 10:.0f}%)")
    if overview["communication_score"] >= 8.0:
        strengths.append(f"Effective Communication & Structure ({overview['communication_score'] * 10:.0f}%)")
    if overview["clarity_score"] >= 8.0:
        strengths.append(f"Concise & Clear Articulation ({overview['clarity_score'] * 10:.0f}%)")
    if overview["relevance_score"] >= 8.0:
        strengths.append("High Answer Relevance to Evaluated Prompts")

    for cat in categories:
        if cat["score"] >= 8.0 and len(strengths) < 4:
            strengths.append(f"Mastery in {cat['category']} ({cat['score_percentage']}%)")

    for sk in skills:
        if sk["score"] >= 8.0 and len(strengths) < 5:
            strengths.append(f"Solid Command of {sk['skill']} ({sk['score_percentage']}%)")

    # Recurring strengths from DB
    all_eval_strengths = []
    for ev in evaluations:
        all_eval_strengths.extend(ev.get("strengths", []))
    for st in all_eval_strengths:
        st_clean = st.strip()
        if st_clean and st_clean not in strengths and len(strengths) < 5:
            strengths.append(st_clean)

    if not strengths:
        strengths = [
            "Consistent interview practice cadence",
            "Willingness to tackle intermediate and advanced questions",
        ]

    # 2. Weak Areas from Lower Scores (< 7.5)
    for cat in categories:
        if cat["score"] < 7.5:
            weak_areas.append(f"{cat['category']} Fundamentals ({cat['score_percentage']}%)")

    for sk in skills:
        if sk["score"] < 7.5 and len(weak_areas) < 4:
            weak_areas.append(f"{sk['skill']} ({sk['score_percentage']}%)")

    if overview["completeness_score"] < 7.5 and overview["completeness_score"] > 0:
        weak_areas.append(f"Solution Completeness & Edge Cases ({overview['completeness_score'] * 10:.0f}%)")

    if overview["clarity_score"] < 7.0 and overview["clarity_score"] > 0:
        weak_areas.append("Answer Structure & Brevity")

    # Recurring weaknesses from DB
    all_eval_weaknesses = []
    for ev in evaluations:
        all_eval_weaknesses.extend(ev.get("weaknesses", []))
    for wk in all_eval_weaknesses:
        wk_clean = wk.strip()
        if wk_clean and wk_clean not in weak_areas and len(weak_areas) < 5:
            weak_areas.append(wk_clean)

    if not weak_areas:
        weak_areas = [
            "Advanced scalability & distributed edge cases",
            "Quantifying operational impact with specific metrics",
        ]

    # 3. Deterministic Recommendations
    # Database / SQL recommendation
    db_cat = next((c for c in categories if "database" in c["category"].lower() or "sql" in c["category"].lower()), None)
    if db_cat and db_cat["score"] < 7.8:
        recommendations.append(
            f"Your {db_cat['category']} performance ({db_cat['score_percentage']}%) is below your target average. "
            "Practice compound indexing, transaction isolation levels, and join optimizations."
        )

    # Completeness vs Accuracy recommendation
    if overview["technical_score"] >= 7.5 and overview["completeness_score"] < 7.5 and overview["completeness_score"] > 0:
        recommendations.append(
            "Your technical accuracy is solid, but completeness scores are lower. "
            "Try explicitly detailing trade-offs, defensive validation, and failure scenarios."
        )

    # Communication recommendation
    if overview["communication_score"] < 7.5 and overview["communication_score"] > 0:
        recommendations.append(
            "Structure behavioral and leadership responses more tightly using the STAR method (Situation, Task, Action, Result)."
        )

    # Resume vs Interview alignment comparison
    resume_score = overview["latest_resume_score"]
    int_score = overview["average_score_percentage"]
    comparison = None

    if resume_score > 0 and int_score > 0:
        diff = resume_score - int_score
        if diff >= 10:
            insight_text = (
                f"Your current scores suggest your resume credentials are high ({resume_score}%), "
                f"while your live interview conversion ({int_score}%) is slightly lower. Focus on mock interview repetitions."
            )
        elif diff <= -10:
            insight_text = (
                f"Your mock interview performance ({int_score}%) exceeds your resume ATS score ({resume_score}%). "
                "Consider optimizing your resume keywords to showcase your proven competencies."
            )
        else:
            insight_text = (
                f"Your current scores suggest balanced alignment between your resume profile ({resume_score}%) "
                f"and mock interview performance ({int_score}%)."
            )

        comparison = {
            "resume_score": resume_score,
            "interview_score": int_score,
            "difference": round(diff, 1),
            "insight": insight_text,
        }
        recommendations.append(insight_text)

    if not recommendations:
        recommendations = [
            "Maintain your momentum with 2–3 weekly mock interview sessions.",
            "Review past evaluated answer outlines to incorporate recommended structural points.",
        ]

    return {
        "strengths": strengths[:5],
        "weak_areas": weak_areas[:5],
        "recommendations": recommendations[:4],
        "resume_interview_comparison": comparison,
    }


def get_recent_activity(user_id: str, limit: int = 6) -> List[dict]:
    """Aggregates recent candidate activities (resumes, question sets, completed interviews)."""
    db = get_database()
    resumes_col = db["resume_analyses"]
    qsets_col = get_interview_question_sets_collection()
    evals_col = get_interview_evaluations_collection()

    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
    user_filter = {"$or": [{"user_id": user_id}, {"user_id": u_oid}]}

    activities = []

    # 1. Resumes Analyzed
    resumes = list(resumes_col.find(user_filter).sort("created_at", -1).limit(limit))
    for r in resumes:
        activities.append({
            "id": str(r["_id"]),
            "activity_type": "resume_analyzed",
            "title": f"Resume Analyzed: {r.get('filename', 'Resume')}",
            "description": f"ATS Match Score: {r.get('overall_score', 0)}% for {r.get('job_role', 'Target Role')}",
            "date": r.get("created_at", datetime.now(timezone.utc)),
            "score": float(r.get("overall_score", 0)),
            "metadata": {
                "filename": r.get("filename"),
                "job_role": r.get("job_role"),
            },
        })

    # 2. Question Sets & Completed Interviews
    qsets = list(qsets_col.find(user_filter).sort("created_at", -1).limit(limit))
    for qs in qsets:
        qs_id = qs["_id"]
        evals = list(evals_col.find({"question_set_id": {"$in": [qs_id, str(qs_id)]}}))

        if evals:
            avg_sc = round(sum(e.get("overall_score", 0.0) for e in evals) / len(evals), 1)
            activities.append({
                "id": str(qs_id),
                "activity_type": "interview_completed",
                "title": f"Mock Interview: {qs.get('target_role', 'Practice')}",
                "description": f"Scored {avg_sc}/10 ({len(evals)} answers evaluated • {qs.get('interview_type', 'Technical')})",
                "date": qs.get("created_at", datetime.now(timezone.utc)),
                "score": avg_sc,
                "metadata": {
                    "target_role": qs.get("target_role"),
                    "interview_type": qs.get("interview_type"),
                    "difficulty": qs.get("difficulty"),
                },
            })
        else:
            activities.append({
                "id": str(qs_id),
                "activity_type": "question_generated",
                "title": f"Question Bank Generated: {qs.get('target_role', 'Role')}",
                "description": f"{qs.get('number_of_questions', 5)} questions ready ({qs.get('interview_type', 'Technical')} • {qs.get('difficulty', 'Intermediate')})",
                "date": qs.get("created_at", datetime.now(timezone.utc)),
                "score": None,
                "metadata": {
                    "target_role": qs.get("target_role"),
                    "interview_type": qs.get("interview_type"),
                },
            })

    activities.sort(key=lambda a: a["date"], reverse=True)
    return activities[:limit]
