import json
import logging
import re
from typing import Optional, List, Dict, Any
import requests
from pydantic import BaseModel, Field

from app.config import settings
from app.services.ai_service import FALLBACK_QUESTIONS_DB

logger = logging.getLogger(__name__)


class InterviewerAIOutput(BaseModel):
    interview_complete: bool = False
    next_question: Optional[str] = None
    category: Optional[str] = "Technical"
    topic: Optional[str] = "Core Competencies"
    difficulty: Optional[str] = "Intermediate"
    expected_focus: Optional[List[str]] = Field(default_factory=list)
    reason: Optional[str] = None
    acknowledgement: Optional[str] = None


def generate_next_interview_question(
    target_role: str,
    interview_type: str,
    difficulty: str,
    next_question_number: int,
    total_questions: int,
    previous_question: Optional[str],
    candidate_answer: Optional[str],
    topics_covered: List[str],
    previous_qa_history: List[Dict[str, str]],
    resume_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Orchestrates dynamic next-question generation for the AI Interviewer.
    Attempts Gemini call with dedicated interviewer prompt, falling back safely
    to an intelligent contextual question engine.
    """
    if next_question_number > total_questions:
        return {
            "interview_complete": True,
            "next_question": None,
            "category": "Conclusion",
            "topic": "Wrap Up",
            "difficulty": difficulty,
            "expected_focus": [],
            "reason": "Total question limit reached.",
            "acknowledgement": "Thank you for completing the interview questions.",
        }

    # 1. Try Gemini dedicated interviewer prompt if API key configured
    if settings.GEMINI_API_KEY:
        try:
            gemini_result = _generate_interviewer_question_gemini(
                target_role=target_role,
                interview_type=interview_type,
                difficulty=difficulty,
                next_question_number=next_question_number,
                total_questions=total_questions,
                previous_question=previous_question,
                candidate_answer=candidate_answer,
                topics_covered=topics_covered,
                previous_qa_history=previous_qa_history,
                resume_context=resume_context,
            )
            if gemini_result and gemini_result.next_question:
                return {
                    "interview_complete": False,
                    "next_question": gemini_result.next_question.strip(),
                    "category": gemini_result.category or ("Technical" if interview_type != "HR" else "HR"),
                    "topic": gemini_result.topic or target_role,
                    "difficulty": gemini_result.difficulty or difficulty,
                    "expected_focus": gemini_result.expected_focus or ["Core principles", "Practical application"],
                    "reason": gemini_result.reason or "Contextual follow-up",
                    "acknowledgement": gemini_result.acknowledgement or "Thank you.",
                }
        except Exception as e:
            logger.warning(f"Interviewer Gemini call failed, using smart interviewer fallback: {e}")

    # 2. Smart Contextual Fallback Engine
    return _generate_smart_fallback_question(
        target_role=target_role,
        interview_type=interview_type,
        difficulty=difficulty,
        next_question_number=next_question_number,
        total_questions=total_questions,
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        topics_covered=topics_covered,
        resume_context=resume_context,
    )


def _generate_interviewer_question_gemini(
    target_role: str,
    interview_type: str,
    difficulty: str,
    next_question_number: int,
    total_questions: int,
    previous_question: Optional[str],
    candidate_answer: Optional[str],
    topics_covered: List[str],
    previous_qa_history: List[Dict[str, str]],
    resume_context: Optional[Dict[str, Any]],
) -> Optional[InterviewerAIOutput]:
    """Dedicated Gemini prompt for the AI Interviewer."""
    resume_info = ""
    if resume_context:
        skills = resume_context.get("detected_skills", [])
        summary = resume_context.get("extracted_summary", "")
        role = resume_context.get("job_role", "")
        resume_info = f"""
Candidate Verified Background from Resume:
- Background Role: {role or 'Not specified'}
- Verified Skills: {', '.join(skills[:8]) if skills else 'Not specified'}
- Summary: {summary[:200] if summary else 'N/A'}
NOTE: You may reference these verified skills or ask about related architecture if appropriate, but do NOT invent unverified background.
"""

    history_str = ""
    if previous_qa_history:
        recent_history = previous_qa_history[-3:]  # Reasonable memory window
        history_lines = []
        for item in recent_history:
            q_num = item.get("question_number", "?")
            q_txt = item.get("question", "")
            a_txt = (item.get("answer", "") or "")[:200]
            history_lines.append(f"Q{q_num}: {q_txt}\nA{q_num}: {a_txt}")
        history_str = "\n".join(history_lines)

    covered_topics_str = ", ".join(topics_covered) if topics_covered else "None"

    prompt = f"""You are an elite Senior HR & Technical Interviewer conducting a realistic, conversational voice interview.
You are interviewing a candidate for the role of '{target_role}'.

INTERVIEW CONFIGURATION:
- Target Role: {target_role}
- Interview Mode: {interview_type} (Technical, HR, or Mixed)
- Difficulty: {difficulty}
- Current Question Progress: Question {next_question_number} of {total_questions}
- Topics Already Covered: {covered_topics_str}
{resume_info}

PREVIOUS INTERVIEW CONTEXT:
Most Recent Question Asked:
"{previous_question or 'Tell me about yourself and your background.'}"

Candidate's Spoken Answer:
"{candidate_answer or 'No previous answer provided.'}"

Recent Conversation Memory:
{history_str or 'First question of the interview.'}

INTERVIEWER BEHAVIOR & RULES:
1. Speak naturally as a real interviewer. The candidate is listening to your question via Text-to-Speech.
2. Keep the question concise and focused (1 to 2 sentences maximum). Do NOT make lengthy speeches.
3. Natural follow-up: If the candidate mentioned specific technologies, projects, metrics, or challenges in their previous answer, formulate an intelligent follow-up question digging deeper into their technical decisions, architecture, trade-offs, or role.
4. If their previous answer was complete and the topic is covered, transition smoothly to the next core competency or behavioral situation required for '{target_role}'.
5. Avoid repeating questions or topics listed in 'Topics Already Covered'.
6. In 'HR' mode, emphasize behavioral scenarios (STAR method), teamwork, conflict resolution, leadership, and communication.
7. In 'Technical' mode, emphasize technical correctness, system architecture, data flow, error handling, and trade-offs.
8. In 'Mixed' mode, maintain a balance of technical and behavioral questions across the session.
9. Provide a natural, concise interviewer acknowledgement (e.g., "Thank you.", "That's an interesting approach.", "Understood.", "Thank you for explaining that."). Keep it under 10 words.
10. Do NOT evaluate the answer or reveal scores, hidden rubrics, or solution keys.

Respond ONLY with valid JSON conforming to this schema:
{{
  "interview_complete": false,
  "next_question": "Can you explain the main challenge you faced while building that system, and how you solved it?",
  "category": "Technical",
  "topic": "System Architecture",
  "difficulty": "{difficulty}",
  "expected_focus": [
    "Bottleneck diagnosis",
    "Architectural trade-offs",
    "Outcome"
  ],
  "reason": "Follow-up based on candidate's project implementation details",
  "acknowledgement": "Thank you for that explanation."
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.35,
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=25)
    if response.status_code == 200:
        res_json = response.json()
        candidates = res_json.get("candidates", [])
        if candidates:
            raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
            # Clean markdown fences
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            return InterviewerAIOutput(**parsed)
    else:
        logger.warning(f"Gemini returned status {response.status_code}: {response.text}")

    return None


def _generate_smart_fallback_question(
    target_role: str,
    interview_type: str,
    difficulty: str,
    next_question_number: int,
    total_questions: int,
    previous_question: Optional[str],
    candidate_answer: Optional[str],
    topics_covered: List[str],
    resume_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Intelligent context-aware fallback question engine.
    Analyzes candidate answer keywords to create realistic follow-up questions
    or selects the next appropriate topic from domain questions bank.
    """
    ans_lower = (candidate_answer or "").lower().strip()
    words = ans_lower.split()

    # Natural acknowledgement pools
    acknowledgements = [
        "Thank you for sharing that.",
        "Understood, that's helpful context.",
        "Thank you. Let's build on that.",
        "I appreciate the detailed explanation.",
        "That's an interesting perspective.",
    ]
    ack = acknowledgements[(next_question_number - 1) % len(acknowledgements)]

    # 1. Check for specific keywords to generate dynamic follow-up
    # Project & Architecture follow-up
    if any(k in ans_lower for k in ["project", "built", "implemented", "application", "system", "designed", "created"]):
        if any(k in ans_lower for k in ["database", "mongo", "sql", "postgres", "data"]):
            return {
                "interview_complete": False,
                "next_question": "You mentioned working with data storage in your project. How did you structure your schema and handle indexing or query optimization?",
                "category": "Database",
                "topic": "Data Modeling & Indexing",
                "difficulty": difficulty,
                "expected_focus": ["Schema design", "Indexing strategy", "Query performance"],
                "reason": "Follow-up on candidate's project database implementation",
                "acknowledgement": ack,
            }
        return {
            "interview_complete": False,
            "next_question": "You discussed implementing that project. What was the most significant technical roadblock or trade-off you encountered, and how did you resolve it?",
            "category": "Problem Solving",
            "topic": "Project Architecture & Trade-offs",
            "difficulty": difficulty,
            "expected_focus": ["Technical roadblock", "Decision rationale", "Resolution outcome"],
            "reason": "Follow-up on project technical challenges",
            "acknowledgement": ack,
        }

    # API / Microservices follow-up
    if any(k in ans_lower for k in ["api", "endpoint", "rest", "fastapi", "microservice", "backend"]):
        return {
            "interview_complete": False,
            "next_question": "When designing APIs for that workflow, how do you handle error boundaries, status codes, and input validation to keep the service reliable?",
            "category": "Web Development",
            "topic": "API Resilience & Validation",
            "difficulty": difficulty,
            "expected_focus": ["Error response format", "Input validation", "Resilience"],
            "reason": "Follow-up on API design and validation practices",
            "acknowledgement": ack,
        }

    # Team / Collaboration follow-up
    if any(k in ans_lower for k in ["team", "colleague", "agile", "lead", "mentor", "scrum", "client"]):
        return {
            "interview_complete": False,
            "next_question": "Can you describe a situation where someone on the team disagreed with your approach, and how you navigated that conversation to reach alignment?",
            "category": "Behavioral",
            "topic": "Team Collaboration & Conflict",
            "difficulty": difficulty,
            "expected_focus": ["Communication approach", "Constructive alignment", "Positive outcome"],
            "reason": "Follow-up on candidate's team collaboration experience",
            "acknowledgement": ack,
        }

    # Performance / Caching follow-up
    if any(k in ans_lower for k in ["cache", "redis", "latency", "scale", "performance", "slow", "load"]):
        return {
            "interview_complete": False,
            "next_question": "How do you ensure cache invalidation consistency, and what strategies do you employ to prevent cache stampedes or stale data?",
            "category": "System Design",
            "topic": "Caching Strategies & Consistency",
            "difficulty": difficulty,
            "expected_focus": ["Cache invalidation", "TTL management", "Stampede mitigation"],
            "reason": "Follow-up on caching and performance considerations",
            "acknowledgement": ack,
        }

    # Brief answer elaboration request
    if len(words) < 15 and len(words) > 0:
        return {
            "interview_complete": False,
            "next_question": "Could you elaborate on that with a concrete example or scenario from your past experience?",
            "category": "Communication",
            "topic": "In-Depth Elaboration",
            "difficulty": difficulty,
            "expected_focus": ["Concrete example", "Context & Action", "Result"],
            "reason": "Prompting candidate to provide practical detail on a brief response",
            "acknowledgement": "Thank you.",
        }

    # 2. Domain Bank Selection: Find next unused question from domain questions DB
    role_key = target_role if target_role in FALLBACK_QUESTIONS_DB else "Software Developer"
    type_key = interview_type if interview_type in ["Technical", "HR"] else "Technical"
    diff_key = difficulty if difficulty in ["Beginner", "Intermediate", "Advanced"] else "Intermediate"

    candidate_questions = FALLBACK_QUESTIONS_DB.get(role_key, {}).get(type_key, {}).get(diff_key, [])

    # Filter out already covered topics
    for item in candidate_questions:
        topic_name = item.get("topic", "")
        if topic_name not in topics_covered and item.get("question") != previous_question:
            return {
                "interview_complete": False,
                "next_question": item.get("question"),
                "category": item.get("category", type_key),
                "topic": topic_name,
                "difficulty": diff_key,
                "expected_focus": item.get("expected_focus", ["Core concepts", "Real-world usage"]),
                "reason": f"Next domain question for {target_role} ({diff_key})",
                "acknowledgement": ack,
            }

    # Fallback default if all bank questions exhausted
    return {
        "interview_complete": False,
        "next_question": f"How do you approach debugging and monitoring unexpected production issues in a {target_role} environment?",
        "category": "Problem Solving",
        "topic": "Production Observability & Debugging",
        "difficulty": difficulty,
        "expected_focus": ["Logging & metrics", "Root cause analysis", "Post-mortem prevention"],
        "reason": f"Core competency question for {target_role}",
        "acknowledgement": ack,
    }
