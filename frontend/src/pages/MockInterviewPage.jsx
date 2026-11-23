import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Video,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  Brain,
  Sliders,
  Play,
  Pause,
  RotateCcw,
  FileText,
  History,
  Copy,
  Check,
  ChevronRight,
  ChevronLeft,
  ArrowRight,
  Layers,
  Award,
  Zap,
  Bookmark,
  Eye,
  EyeOff,
  Send,
  RefreshCw,
  FileCheck,
  LogOut,
  CheckCircle,
  BarChart3,
  Target,
  ThumbsUp,
  AlertTriangle,
  Lightbulb,
  Download,
  Mic,
} from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { exportInterviewReportPDF } from '../utils/pdfExport';
import {
  generateInterviewQuestions,
  getQuestionHistory,
  getQuestionSet,
  getInterviewResumeStatus,
  evaluateInterviewAnswer,
  getQuestionSetEvaluations,
  getInterviewFinalReport,
} from '../services/api';

const MockInterviewPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();

  // Form states
  const [targetRole, setTargetRole] = useState('Full Stack Developer');
  const [interviewType, setInterviewType] = useState('Technical');
  const [difficulty, setDifficulty] = useState('Intermediate');
  const [questionCount, setQuestionCount] = useState('10');

  // Generation & display states
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [generatedQuestions, setGeneratedQuestions] = useState(null);
  const [error, setError] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Resume status & Question history states
  const [resumeStatus, setResumeStatus] = useState({
    has_resume: false,
    filename: null,
    job_role: null,
    detected_skills: [],
    overall_score: 0,
  });
  const [historyList, setHistoryList] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState('generator'); // 'generator' | 'history'

  // Interactive Question Flow states (Phase 4 & 5)
  const [sessionActive, setSessionActive] = useState(false);
  const [isReviewScreen, setIsReviewScreen] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [candidateAnswers, setCandidateAnswers] = useState({});
  const [markedQuestions, setMarkedQuestions] = useState({});
  const [showFocusGuidance, setShowFocusGuidance] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(true);
  const [isFinishConfirmOpen, setIsFinishConfirmOpen] = useState(false);
  const [isExitConfirmOpen, setIsExitConfirmOpen] = useState(false);
  const [copiedTranscript, setCopiedTranscript] = useState(false);

  // Phase 5 AI Answer Evaluation & Report states
  const [evaluations, setEvaluations] = useState({}); // { [questionIndex]: AnswerEvaluationResponse }
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationError, setEvaluationError] = useState(null);
  const [finalReport, setFinalReport] = useState(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  const roles = [
    'Software Developer',
    'Frontend Developer',
    'Backend Developer',
    'Full Stack Developer',
    'Python Developer',
    'Java Developer',
    'Data Analyst',
    'AI/ML Engineer',
  ];

  const types = ['Technical', 'HR', 'Mixed'];
  const difficulties = ['Beginner', 'Intermediate', 'Advanced'];
  const questionOptions = ['5', '10', '15'];

  // Load resume status and past question sets on mount if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadResumeStatus();
      loadHistory();
    }
  }, [isAuthenticated]);

  // Check if routed with a questionSet state (e.g. from history page or query)
  useEffect(() => {
    if (location.state?.questionSet) {
      const qSet = location.state.questionSet;
      setGeneratedQuestions(qSet);
      if (location.state.autoStart) {
        handleStartSession(qSet);
      }
    }
  }, [location.state]);

  const loadResumeStatus = async () => {
    try {
      const data = await getInterviewResumeStatus();
      setResumeStatus(data);
      if (data.has_resume && data.job_role && roles.includes(data.job_role)) {
        setTargetRole(data.job_role);
      }
    } catch (err) {
      console.warn('Failed to load resume status:', err);
    }
  };

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const data = await getQuestionHistory();
      setHistoryList(data);
    } catch (err) {
      console.warn('Failed to load question history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Restore stored evaluations from MongoDB on session start or page reload
  const loadExistingEvaluations = async (qSetId) => {
    if (!qSetId) return;
    try {
      const storedEvals = await getQuestionSetEvaluations(qSetId);
      if (storedEvals && Array.isArray(storedEvals) && storedEvals.length > 0) {
        const evMap = {};
        const ansMap = {};
        storedEvals.forEach((ev) => {
          const idx = ev.question_number - 1;
          evMap[idx] = ev;
          if (ev.candidate_answer) {
            ansMap[idx] = ev.candidate_answer;
          }
        });
        setEvaluations((prev) => ({ ...prev, ...evMap }));
        setCandidateAnswers((prev) => ({ ...ansMap, ...prev }));
      }
    } catch (err) {
      console.warn('Failed to load stored evaluations:', err);
    }
  };

  // Stepped loading simulation during question generation
  useEffect(() => {
    let timer;
    if (isGenerating) {
      setGenerationStep(0);
      const step1 = setTimeout(() => setGenerationStep(1), 700);
      const step2 = setTimeout(() => setGenerationStep(2), 1600);
      const step3 = setTimeout(() => setGenerationStep(3), 2800);

      return () => {
        clearTimeout(step1);
        clearTimeout(step2);
        clearTimeout(step3);
      };
    }
  }, [isGenerating]);

  // Session timer ticker
  useEffect(() => {
    let interval = null;
    if (sessionActive && isTimerRunning && !isReviewScreen) {
      interval = setInterval(() => {
        setTimerSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [sessionActive, isTimerRunning, isReviewScreen]);

  const formatTimer = (totalSecs) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleGenerateQuestions = async (e) => {
    if (e) e.preventDefault();
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    setIsGenerating(true);
    setError(null);

    const payload = {
      target_role: targetRole,
      interview_type: interviewType,
      difficulty: difficulty,
      number_of_questions: parseInt(questionCount, 10),
    };

    try {
      const result = await generateInterviewQuestions(payload);
      setGeneratedQuestions(result);
      setActiveTab('generator');
      loadHistory();
      setTimeout(() => {
        const el = document.getElementById('questions-result');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.error('Question generation failed:', err);
      const detail =
        err.response?.data?.detail ||
        'Failed to generate interview questions. Please verify your connection and try again.';
      setError(detail);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleViewHistoricalSet = async (setId) => {
    try {
      setIsLoadingHistory(true);
      const data = await getQuestionSet(setId);
      setGeneratedQuestions(data);
      setActiveTab('generator');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Failed to fetch historical question set:', err);
      alert('Failed to load historical question set.');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleOpenHistoricalReport = async (setId) => {
    try {
      setIsLoadingHistory(true);
      const [fullSet, report] = await Promise.all([
        getQuestionSet(setId),
        getInterviewFinalReport(setId),
      ]);
      setGeneratedQuestions(fullSet);
      setFinalReport(report);
      if (report.evaluations && Array.isArray(report.evaluations)) {
        const evMap = {};
        const ansMap = {};
        report.evaluations.forEach((ev) => {
          const idx = ev.question_number - 1;
          evMap[idx] = ev;
          if (ev.candidate_answer) ansMap[idx] = ev.candidate_answer;
        });
        setEvaluations(evMap);
        setCandidateAnswers(ansMap);
      }
      setIsReviewScreen(true);
      setSessionActive(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Failed to load historical report:', err);
      alert('Failed to load final report for this set.');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Interactive Session flow controls
  const handleStartSession = (questionSet = null) => {
    const targetSet = questionSet || generatedQuestions;
    if (!targetSet || !targetSet.questions || targetSet.questions.length === 0) return;
    setGeneratedQuestions(targetSet);
    setCurrentQuestionIndex(0);
    setCandidateAnswers({});
    setMarkedQuestions({});
    setEvaluations({});
    setFinalReport(null);
    setTimerSeconds(0);
    setIsTimerRunning(true);
    setShowFocusGuidance(false);
    setIsReviewScreen(false);
    setSessionActive(true);
    setEvaluationError(null);

    // Retrieve any previously stored evaluations for this set from MongoDB
    if (targetSet.id) {
      loadExistingEvaluations(targetSet.id);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRetakeSession = () => {
    setCurrentQuestionIndex(0);
    setCandidateAnswers({});
    setMarkedQuestions({});
    setEvaluations({});
    setFinalReport(null);
    setTimerSeconds(0);
    setIsTimerRunning(true);
    setShowFocusGuidance(false);
    setIsReviewScreen(false);
    setSessionActive(true);
    setEvaluationError(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAnswerChange = (text) => {
    setCandidateAnswers((prev) => ({
      ...prev,
      [currentQuestionIndex]: text,
    }));
    if (evaluationError) setEvaluationError(null);
  };

  // Phase 5 AI Answer Evaluation Action
  const handleEvaluateCurrentAnswer = async () => {
    if (!generatedQuestions) return;
    const currentQ = generatedQuestions.questions[currentQuestionIndex];
    const answer = (candidateAnswers[currentQuestionIndex] || '').trim();

    if (!answer) {
      setEvaluationError('Please provide an answer before evaluating.');
      return;
    }

    setIsEvaluating(true);
    setEvaluationError(null);

    try {
      const payload = {
        question_set_id: generatedQuestions.id,
        question_number: currentQ.question_number || currentQuestionIndex + 1,
        candidate_answer: answer,
      };

      const result = await evaluateInterviewAnswer(payload);
      setEvaluations((prev) => ({
        ...prev,
        [currentQuestionIndex]: result,
      }));
    } catch (err) {
      console.error('Answer evaluation failed:', err);
      const detail = err.response?.data?.detail || 'Failed to evaluate answer. Please try again.';
      setEvaluationError(detail);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleToggleMark = (idx = currentQuestionIndex) => {
    setMarkedQuestions((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const totalQuestions = generatedQuestions?.questions?.length || 0;
  const answeredCount = Object.keys(candidateAnswers).filter(
    (k) => candidateAnswers[k] && candidateAnswers[k].trim().length > 0
  ).length;
  const evaluatedCount = Object.keys(evaluations).length;
  const unansweredCount = Math.max(0, totalQuestions - answeredCount);
  const markedCount = Object.values(markedQuestions).filter(Boolean).length;

  const handleNextQuestion = () => {
    if (!generatedQuestions) return;
    setEvaluationError(null);
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
      setShowFocusGuidance(false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      triggerFinishFlow();
    }
  };

  const handlePrevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setEvaluationError(null);
      setCurrentQuestionIndex((prev) => prev - 1);
      setShowFocusGuidance(false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const triggerFinishFlow = () => {
    if (unansweredCount > 0) {
      setIsFinishConfirmOpen(true);
    } else {
      executeFinishSession();
    }
  };

  const executeFinishSession = async () => {
    setIsFinishConfirmOpen(false);
    setIsTimerRunning(false);
    setIsLoadingReport(true);
    setIsReviewScreen(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
      if (generatedQuestions?.id) {
        const report = await getInterviewFinalReport(generatedQuestions.id);
        setFinalReport(report);
      }
    } catch (err) {
      console.warn('Failed to fetch final report from backend:', err);
    } finally {
      setIsLoadingReport(false);
    }
  };

  const handleExitSession = () => {
    setSessionActive(false);
    setIsReviewScreen(false);
    setIsExitConfirmOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCopyTranscript = () => {
    if (!generatedQuestions) return;
    let transcript = `# Interview Evaluation Report: ${generatedQuestions.target_role}\n`;
    transcript += `Type: ${generatedQuestions.interview_type} | Difficulty: ${generatedQuestions.difficulty}\n`;
    transcript += `Date: ${new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })} | Time Spent: ${formatTimer(timerSeconds)}\n`;
    transcript += `Progress: ${answeredCount}/${totalQuestions} Questions Answered | Evaluated: ${evaluatedCount}/${totalQuestions}\n`;
    if (finalReport) {
      transcript += `Overall Interview Score: ${finalReport.overall_score}/10 (${finalReport.score_percentage}%)\n`;
    }
    transcript += `\n================================================================================\n\n`;

    generatedQuestions.questions.forEach((q, idx) => {
      const ans = candidateAnswers[idx]?.trim();
      const ev = evaluations[idx];
      transcript += `### Q${idx + 1} [${q.category} - ${q.topic} - ${q.difficulty}]:\n`;
      transcript += `${q.question}\n\n`;
      transcript += `**Candidate Draft / Notes**:\n${ans ? ans : '*(No answer recorded)*'}\n\n`;
      if (ev) {
        transcript += `**AI Evaluation Score**: ${ev.overall_score} / 10\n`;
        transcript += `**Interviewer Summary**: ${ev.summary}\n`;
        if (ev.strengths?.length > 0) {
          transcript += `**Strengths**:\n` + ev.strengths.map((s) => `- ${s}`).join('\n') + `\n`;
        }
        if (ev.weaknesses?.length > 0) {
          transcript += `**Weaknesses**:\n` + ev.weaknesses.map((w) => `- ${w}`).join('\n') + `\n`;
        }
        if (ev.missing_points?.length > 0) {
          transcript += `**Missing Points**:\n` + ev.missing_points.map((m) => `- ${m}`).join('\n') + `\n`;
        }
        if (ev.improvement_suggestions?.length > 0) {
          transcript += `**Suggestions**:\n` + ev.improvement_suggestions.map((sg) => `- ${sg}`).join('\n') + `\n`;
        }
        if (ev.model_answer_outline) {
          transcript += `**Suggested Answer Outline**:\n${ev.model_answer_outline}\n`;
        }
        transcript += `\n`;
      }
      if (q.expected_focus && q.expected_focus.length > 0) {
        transcript += `**Expected Focus Areas**:\n`;
        q.expected_focus.forEach((f) => {
          transcript += `- ${f}\n`;
        });
        transcript += `\n`;
      }
      transcript += `--------------------------------------------------------------------------------\n\n`;
    });

    navigator.clipboard.writeText(transcript);
    setCopiedTranscript(true);
    setTimeout(() => setCopiedTranscript(false), 2500);
  };

  const handleCopyQuestion = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getCategoryBadgeVariant = (category) => {
    switch (category) {
      case 'Technical':
        return 'primary';
      case 'Coding':
        return 'blue';
      case 'Database':
        return 'success';
      case 'Web Development':
        return 'primary';
      case 'System Design':
        return 'purple';
      case 'Problem Solving':
        return 'warning';
      case 'HR':
      case 'Behavioral':
      case 'Situational':
        return 'purple';
      default:
        return 'neutral';
    }
  };

  const getDifficultyBadgeVariant = (diff) => {
    switch (diff) {
      case 'Beginner':
        return 'success';
      case 'Intermediate':
        return 'primary';
      case 'Advanced':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  // ---------------------------------------------------------------------------
  // RENDER: Active Interactive Session Mode with AI Answer Evaluation
  // ---------------------------------------------------------------------------
  if (sessionActive && !isReviewScreen && generatedQuestions) {
    const currentQ = generatedQuestions.questions[currentQuestionIndex];
    const currentAnswer = candidateAnswers[currentQuestionIndex] || '';
    const currentEval = evaluations[currentQuestionIndex];
    const wordCount = currentAnswer.trim().split(/\s+/).filter(Boolean).length;
    const charCount = currentAnswer.length;
    const isCurrentMarked = !!markedQuestions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex === totalQuestions - 1;

    return (
      <div className="max-w-6xl mx-auto space-y-6 pb-16">
        {/* Session Top Bar */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 sm:p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                if (answeredCount > 0) {
                  setIsExitConfirmOpen(true);
                } else {
                  handleExitSession();
                }
              }}
              className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors flex items-center gap-1.5 text-xs font-semibold cursor-pointer"
              title="Exit Practice Session"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Exit Session</span>
            </button>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="primary" size="sm">
                  {generatedQuestions.target_role}
                </Badge>
                <Badge
                  variant={generatedQuestions.interview_type === 'HR' ? 'purple' : 'primary'}
                  size="sm"
                >
                  {generatedQuestions.interview_type}
                </Badge>
                <Badge variant={getDifficultyBadgeVariant(generatedQuestions.difficulty)} size="sm">
                  {generatedQuestions.difficulty}
                </Badge>
              </div>
              <h2 className="text-sm sm:text-base font-bold text-slate-900 mt-1 flex items-center gap-2">
                <span>Phase 5 Interactive AI Interview</span>
                <span className="text-xs text-indigo-600 font-normal">
                  • AI Scoring & Evaluation Active
                </span>
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap justify-between md:justify-end">
            {/* Live Timer Widget */}
            <div className="flex items-center gap-2 bg-slate-900 text-white px-3.5 py-1.5 rounded-xl font-mono text-xs font-bold shadow-xs">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              <span>{formatTimer(timerSeconds)}</span>
              <button
                type="button"
                onClick={() => setIsTimerRunning(!isTimerRunning)}
                className="text-slate-400 hover:text-white transition-colors cursor-pointer ml-1 p-0.5 rounded hover:bg-slate-800"
                title={isTimerRunning ? 'Pause timer' : 'Resume timer'}
              >
                {isTimerRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              </button>
            </div>

            {/* Question Progress Pill */}
            <div className="text-xs font-semibold text-slate-700 bg-slate-100 px-3 py-1.5 rounded-xl">
              Question {currentQuestionIndex + 1} of {totalQuestions}
            </div>

            {/* Finish Button */}
            <Button
              size="sm"
              variant="primary"
              icon={CheckCircle}
              onClick={triggerFinishFlow}
            >
              Finish Interview
            </Button>
          </div>
        </div>

        {/* Main Grid: Question Workspace + Navigation Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Question & Answering Area */}
          <div className="lg:col-span-8 space-y-6">
            {/* Active Question Card */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-7 shadow-xs space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span className="w-9 h-9 rounded-xl bg-indigo-600 text-white font-mono text-sm font-bold flex items-center justify-center shrink-0 shadow-xs">
                    {String(currentQ.question_number || currentQuestionIndex + 1).padStart(2, '0')}
                  </span>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={getCategoryBadgeVariant(currentQ.category)} size="sm">
                        {currentQ.category}
                      </Badge>
                      <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-md">
                        {currentQ.topic}
                      </span>
                      <Badge variant={getDifficultyBadgeVariant(currentQ.difficulty)} size="sm">
                        {currentQ.difficulty}
                      </Badge>
                      {currentEval && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md border border-purple-200">
                          <Sparkles className="w-3 h-3 text-purple-600" />
                          Evaluated: {currentEval.overall_score}/10
                        </span>
                      )}
                      {isCurrentMarked && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                          <Bookmark className="w-3 h-3 fill-amber-500 text-amber-500" />
                          Marked for Review
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleCopyQuestion(currentQ.question, currentQuestionIndex)}
                  title="Copy question text"
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors shrink-0 cursor-pointer"
                >
                  {copiedIndex === currentQuestionIndex ? (
                    <Check className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Large Question Display */}
              <h1 className="text-lg sm:text-xl font-bold text-slate-900 leading-relaxed font-heading">
                {currentQ.question}
              </h1>

              {/* Guidance / Expected Focus Toggle */}
              <div className="pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowFocusGuidance(!showFocusGuidance)}
                  className="flex items-center gap-2 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors cursor-pointer"
                >
                  {showFocusGuidance ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  <span>
                    {showFocusGuidance
                      ? 'Hide Interviewer Evaluation Focus'
                      : 'Show Interviewer Evaluation Focus & Tips'}
                  </span>
                </button>

                {showFocusGuidance && (
                  <div className="mt-3 p-4 bg-indigo-50/70 border border-indigo-100 rounded-xl space-y-2 text-xs">
                    <div className="flex items-center gap-1.5 font-bold text-indigo-900">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Interviewer Assessment Criteria:</span>
                    </div>
                    <p className="text-indigo-800/90 text-[11px]">
                      A strong response should directly address these concepts and demonstrate practical application:
                    </p>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {currentQ.expected_focus?.map((f, fIdx) => (
                        <span
                          key={fIdx}
                          className="px-2.5 py-1 rounded-lg bg-white border border-indigo-200 text-indigo-900 font-medium text-xs shadow-2xs flex items-center gap-1.5"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Candidate Response Workspace */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-7 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Your Response & Solution Notes
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Structure your approach, trade-offs, or behavioral STAR points.
                  </p>
                </div>
                <div className="text-xs font-mono text-slate-400">
                  {wordCount} {wordCount === 1 ? 'word' : 'words'} • {charCount} chars
                </div>
              </div>

              <textarea
                value={currentAnswer}
                onChange={(e) => handleAnswerChange(e.target.value)}
                placeholder="Draft your answer here... Mention architecture choices, algorithms, trade-offs, or specific project stories using the STAR method (Situation, Task, Action, Result)..."
                rows={8}
                className="w-full p-4 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none text-xs sm:text-sm text-slate-800 placeholder-slate-400 font-sans leading-relaxed resize-y transition-all"
              />

              {/* Evaluate Button & Notification Area */}
              <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Button
                    type="button"
                    size="md"
                    variant="primary"
                    icon={Sparkles}
                    loading={isEvaluating}
                    disabled={isEvaluating || !currentAnswer.trim()}
                    onClick={handleEvaluateCurrentAnswer}
                  >
                    {isEvaluating ? 'AI is evaluating your answer...' : currentEval ? 'Re-evaluate Answer' : 'Evaluate Answer'}
                  </Button>

                  {currentEval && (
                    <span className="text-xs text-purple-700 font-semibold flex items-center gap-1.5 bg-purple-50 px-2.5 py-1.5 rounded-lg border border-purple-200">
                      <CheckCircle2 className="w-3.5 h-3.5 text-purple-600" />
                      Answer evaluated ({currentEval.overall_score}/10)
                    </span>
                  )}
                </div>

                {evaluationError && (
                  <span className="text-xs text-rose-600 font-medium flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {evaluationError}
                  </span>
                )}
              </div>
            </div>

            {/* Phase 5: AI Evaluation Results Card */}
            {currentEval && (
              <div className="bg-gradient-to-b from-purple-50/70 to-white border border-purple-200/90 rounded-2xl p-6 sm:p-7 shadow-xs space-y-6">
                {/* Score & Category Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-purple-100">
                  <div className="flex items-center gap-3.5">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-700 text-white flex flex-col items-center justify-center font-bold shadow-xs shrink-0">
                      <span className="text-xl leading-none font-extrabold">{currentEval.overall_score}</span>
                      <span className="text-[10px] text-purple-200 font-medium">/ 10</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          variant={currentEval.overall_score >= 8 ? 'success' : currentEval.overall_score >= 6 ? 'primary' : 'warning'}
                          size="sm"
                        >
                          {currentEval.overall_score >= 8 ? 'Strong Answer' : currentEval.overall_score >= 6 ? 'Competent Answer' : 'Needs Development'}
                        </Badge>
                        <span className="text-xs font-bold text-purple-900">
                          AI Evaluation Scorecard
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        Objective evaluation based on correctness, relevance, completeness, clarity, and communication.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Sub-Dimension Scores */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                  {currentEval.technical_accuracy !== null && currentEval.technical_accuracy !== undefined && (
                    <div className="p-3 rounded-xl bg-white border border-purple-100 text-center shadow-2xs">
                      <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Tech Depth</span>
                      <span className="text-base font-extrabold text-slate-900 mt-0.5 block">{currentEval.technical_accuracy} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
                    </div>
                  )}
                  <div className="p-3 rounded-xl bg-white border border-purple-100 text-center shadow-2xs">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Relevance</span>
                    <span className="text-base font-extrabold text-slate-900 mt-0.5 block">{currentEval.relevance} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-purple-100 text-center shadow-2xs">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Completeness</span>
                    <span className="text-base font-extrabold text-slate-900 mt-0.5 block">{currentEval.completeness} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-purple-100 text-center shadow-2xs">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Clarity</span>
                    <span className="text-base font-extrabold text-slate-900 mt-0.5 block">{currentEval.clarity} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-purple-100 text-center shadow-2xs">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Communication</span>
                    <span className="text-base font-extrabold text-slate-900 mt-0.5 block">{currentEval.communication} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
                  </div>
                </div>

                {/* Interviewer Summary */}
                {currentEval.summary && (
                  <div className="p-4 rounded-xl bg-white border border-purple-100 text-xs space-y-1.5 shadow-2xs">
                    <span className="text-[11px] font-bold text-purple-950 uppercase tracking-wider block">
                      Interviewer Summary & Assessment
                    </span>
                    <p className="text-slate-700 leading-relaxed">{currentEval.summary}</p>
                  </div>
                )}

                {/* Strengths & Weaknesses */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  {currentEval.strengths?.length > 0 && (
                    <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
                      <span className="text-[11px] font-bold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        Demonstrated Strengths
                      </span>
                      <ul className="space-y-1.5">
                        {currentEval.strengths.map((str, sIdx) => (
                          <li key={sIdx} className="text-emerald-900 flex items-start gap-2">
                            <span className="text-emerald-600 font-bold">•</span>
                            <span className="leading-snug">{str}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {currentEval.weaknesses?.length > 0 && (
                    <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 space-y-2">
                      <span className="text-[11px] font-bold text-amber-950 uppercase tracking-wider flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4 text-amber-600" />
                        Areas to Strengthen
                      </span>
                      <ul className="space-y-1.5">
                        {currentEval.weaknesses.map((wk, wIdx) => (
                          <li key={wIdx} className="text-amber-900 flex items-start gap-2">
                            <span className="text-amber-600 font-bold">•</span>
                            <span className="leading-snug">{wk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Missing Points */}
                {currentEval.missing_points?.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 text-xs space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-800 uppercase tracking-wider block">
                      Omitted Expected Focus Points
                    </span>
                    <ul className="space-y-1">
                      {currentEval.missing_points.map((mp, mIdx) => (
                        <li key={mIdx} className="text-slate-600 flex items-start gap-2">
                          <span className="text-slate-400 font-bold">•</span>
                          <span>{mp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Improvement Suggestions */}
                {currentEval.improvement_suggestions?.length > 0 && (
                  <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200 text-xs space-y-2">
                    <span className="text-[11px] font-bold text-indigo-950 uppercase tracking-wider flex items-center gap-1.5">
                      <Lightbulb className="w-4 h-4 text-indigo-600" />
                      Actionable Improvement Suggestions
                    </span>
                    <ul className="space-y-1.5">
                      {currentEval.improvement_suggestions.map((sug, sgIdx) => (
                        <li key={sgIdx} className="text-indigo-900 flex items-start gap-2">
                          <span className="text-indigo-600 font-bold">•</span>
                          <span>{sug}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Model Answer Outline */}
                {currentEval.model_answer_outline && (
                  <div className="p-4 rounded-xl bg-white border border-slate-200 text-xs space-y-2">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <span className="text-[11px] font-bold text-slate-800 uppercase tracking-wider">
                        Suggested Answer Outline
                      </span>
                      <span className="text-[11px] text-slate-400 italic">
                        (Suggested outline structure, not a guaranteed answer)
                      </span>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 font-mono text-[11px] text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {currentEval.model_answer_outline}
                    </div>
                  </div>
                )}

                <div className="p-3 bg-purple-100/60 rounded-xl text-xs text-purple-900 font-medium flex items-center justify-between">
                  <span>Review your feedback above, then click <strong>Next Question</strong> to continue.</span>
                  {isLastQuestion ? (
                    <Button size="sm" variant="primary" icon={CheckCircle2} onClick={triggerFinishFlow}>
                      Finish Interview
                    </Button>
                  ) : (
                    <Button size="sm" variant="primary" icon={ArrowRight} iconPosition="right" onClick={handleNextQuestion}>
                      Next Question
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Navigation Controls Bar */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-4 sm:p-5 shadow-xs flex items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  icon={ChevronLeft}
                  onClick={handlePrevQuestion}
                  disabled={currentQuestionIndex === 0}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant={isCurrentMarked ? 'warning' : 'outline'}
                  icon={Bookmark}
                  onClick={() => handleToggleMark(currentQuestionIndex)}
                >
                  {isCurrentMarked ? 'Marked' : 'Mark for Review'}
                </Button>
              </div>

              <div className="flex items-center gap-2.5">
                {isLastQuestion ? (
                  <Button
                    size="sm"
                    variant="primary"
                    icon={CheckCircle2}
                    onClick={triggerFinishFlow}
                  >
                    Finish Interview
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="primary"
                    icon={ArrowRight}
                    iconPosition="right"
                    onClick={handleNextQuestion}
                  >
                    Next Question
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Right Sidebar: Navigator & Progress */}
          <div className="lg:col-span-4 space-y-6">
            {/* Session Progress Card */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-5">
              <div>
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2">
                  <span>Session Completion</span>
                  <span>{Math.round((answeredCount / (totalQuestions || 1)) * 100)}%</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 transition-all duration-300 rounded-full"
                    style={{
                      width: `${Math.round((answeredCount / (totalQuestions || 1)) * 100)}%`,
                    }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                  <span>{answeredCount} Answered ({evaluatedCount} Evaluated)</span>
                  {markedCount > 0 && (
                    <span className="text-amber-600 font-semibold">{markedCount} Marked</span>
                  )}
                </div>
              </div>

              {/* Question Navigator Grid */}
              <div className="space-y-3 pt-3 border-t border-slate-100">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Question Matrix
                </h4>
                <div className="grid grid-cols-5 gap-2">
                  {generatedQuestions.questions.map((q, idx) => {
                    const isCurrent = idx === currentQuestionIndex;
                    const hasAnswer = candidateAnswers[idx] && candidateAnswers[idx].trim().length > 0;
                    const hasEval = !!evaluations[idx];
                    const isMarked = !!markedQuestions[idx];

                    let btnClass = 'border-slate-200 text-slate-700 bg-slate-50 hover:bg-slate-100';
                    if (isCurrent) {
                      btnClass = 'ring-2 ring-indigo-600 bg-indigo-600 text-white font-bold shadow-xs';
                    } else if (hasEval) {
                      btnClass = 'border-purple-300 bg-purple-50 text-purple-900 font-bold';
                    } else if (isMarked) {
                      btnClass = 'border-amber-300 bg-amber-50 text-amber-800 font-bold';
                    } else if (hasAnswer) {
                      btnClass = 'border-emerald-300 bg-emerald-50 text-emerald-800 font-semibold';
                    }

                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setEvaluationError(null);
                          setCurrentQuestionIndex(idx);
                          setShowFocusGuidance(false);
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }}
                        className={`h-10 rounded-xl border text-xs flex flex-col items-center justify-center transition-all cursor-pointer relative ${btnClass}`}
                      >
                        <span>{idx + 1}</span>
                        {hasEval && !isCurrent && (
                          <span className="w-1.5 h-1.5 rounded-full bg-purple-600 absolute bottom-1"></span>
                        )}
                        {!hasEval && hasAnswer && !isCurrent && (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 absolute bottom-1"></span>
                        )}
                        {isMarked && !isCurrent && (
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 absolute top-1 right-1"></span>
                        )}
                      </button>
                    );
                  })}
                </div>

                {/* Navigator Legend */}
                <div className="grid grid-cols-2 gap-2 pt-3 text-[11px] text-slate-500 border-t border-slate-100">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-md bg-indigo-600"></span>
                    <span>Current</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-md bg-purple-100 border border-purple-300"></span>
                    <span>Evaluated (AI)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-md bg-emerald-100 border border-emerald-300"></span>
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-md bg-amber-100 border border-amber-300"></span>
                    <span>Marked</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-md bg-slate-100 border border-slate-200"></span>
                    <span>Unanswered</span>
                  </div>
                </div>
              </div>

              {/* Bottom Quick Finish Action */}
              <div className="pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  fullWidth
                  icon={CheckCircle2}
                  onClick={triggerFinishFlow}
                >
                  End & View Final Report
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Finish Confirmation Modal */}
        <Modal
          isOpen={isFinishConfirmOpen}
          onClose={() => setIsFinishConfirmOpen(false)}
          title="Finish Practice Session?"
          subtitle="Review before ending your mock interview session"
        >
          <div className="space-y-4">
            {unansweredCount > 0 ? (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 flex items-start gap-3 text-xs">
                <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold">Unanswered Questions Remaining</h4>
                  <p className="mt-1 text-amber-800">
                    You have <strong>{unansweredCount}</strong> unanswered {unansweredCount === 1 ? 'question' : 'questions'}. Would you like to finish and view your final evaluation report now?
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 flex items-start gap-3 text-xs">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold">All Questions Completed!</h4>
                  <p className="mt-1 text-emerald-800">
                    You have answered all {totalQuestions} questions ({evaluatedCount} evaluated with AI scoring).
                  </p>
                </div>
              </div>
            )}

            <div className="text-xs text-slate-600">
              <p>
                Finishing will generate your final interview evaluation report with overall scores, strength breakdown, and areas for improvement.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button size="sm" variant="outline" onClick={() => setIsFinishConfirmOpen(false)}>
                Continue Interview
              </Button>
              <Button size="sm" variant="primary" onClick={executeFinishSession}>
                Finish & View Report
              </Button>
            </div>
          </div>
        </Modal>

        {/* Exit Confirmation Modal */}
        <Modal
          isOpen={isExitConfirmOpen}
          onClose={() => setIsExitConfirmOpen(false)}
          title="Exit Practice Session?"
          subtitle="Confirm returning to question generator"
        >
          <div className="space-y-4 text-xs text-slate-600">
            <p>
              Are you sure you want to exit? Your evaluated responses are saved in MongoDB and can be viewed later in Question History.
            </p>
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button size="sm" variant="outline" onClick={() => setIsExitConfirmOpen(false)}>
                Stay in Session
              </Button>
              <Button size="sm" variant="danger" onClick={handleExitSession}>
                Exit Session
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // RENDER: Final Session Report & Review Screen (Phase 5)
  // ---------------------------------------------------------------------------
  if (sessionActive && isReviewScreen && generatedQuestions) {
    const reportData = finalReport || {
      overall_score: evaluatedCount > 0 ? (Object.values(evaluations).reduce((sum, e) => sum + e.overall_score, 0) / evaluatedCount).toFixed(1) : '0.0',
      score_percentage: evaluatedCount > 0 ? Math.round((Object.values(evaluations).reduce((sum, e) => sum + e.overall_score, 0) / evaluatedCount) * 10) : 0,
      total_questions: totalQuestions,
      answered_questions: answeredCount,
      evaluated_questions: evaluatedCount,
      completion_rate: Math.round((answeredCount / (totalQuestions || 1)) * 100),
      strong_areas: ['Strong foundational grasp of primary technical concepts'],
      weak_areas: ['Include more practical production scale and latency trade-offs'],
      top_improvements: ['Structure answers with concrete metrics and clear problem-solution-impact narratives'],
    };

    return (
      <div className="max-w-5xl mx-auto space-y-8 pb-16">
        {/* Congratulations & Final Score Banner */}
        <div className="bg-gradient-to-r from-indigo-950 via-purple-950 to-slate-950 text-white p-7 sm:p-9 rounded-3xl shadow-md space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="success" size="sm">
                  Interview Evaluation Complete
                </Badge>
                <span className="text-xs text-indigo-300">
                  • {new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold font-heading tracking-tight">
                Final Interview Scorecard 🎉
              </h1>
              <p className="text-xs sm:text-sm text-indigo-200 mt-1 max-w-xl">
                Comprehensive evaluation for <strong>{generatedQuestions.target_role}</strong> ({generatedQuestions.interview_type} • {generatedQuestions.difficulty}).
              </p>
            </div>

            {/* Overall Score Circle Card */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 text-center shrink-0 self-start md:self-center flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-indigo-500 text-white flex flex-col items-center justify-center font-bold shadow-lg">
                <span className="text-2xl font-black leading-none">{reportData.overall_score}</span>
                <span className="text-[10px] text-white/80 font-normal">/ 10</span>
              </div>
              <div className="text-left pr-2">
                <span className="text-xs text-indigo-200 font-semibold uppercase tracking-wider block">
                  Overall Score
                </span>
                <span className="text-xl font-bold text-white block">
                  {reportData.score_percentage}%
                </span>
                <span className="text-[11px] text-emerald-300 font-medium">
                  {reportData.overall_score >= 8 ? 'Interview Ready' : reportData.overall_score >= 6 ? 'Competent' : 'Developing'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="bg-white/10 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
              <span className="text-[11px] font-semibold text-indigo-200 uppercase tracking-wider block">
                Evaluated Questions
              </span>
              <span className="text-2xl font-bold mt-1 block">
                {reportData.evaluated_questions} / {reportData.total_questions}
              </span>
            </div>
            <div className="bg-white/10 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
              <span className="text-[11px] font-semibold text-indigo-200 uppercase tracking-wider block">
                Completion Rate
              </span>
              <span className="text-2xl font-bold mt-1 block">
                {reportData.completion_rate}%
              </span>
            </div>
            <div className="bg-white/10 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
              <span className="text-[11px] font-semibold text-indigo-200 uppercase tracking-wider block">
                Time Elapsed
              </span>
              <span className="text-2xl font-bold mt-1 block font-mono">
                {formatTimer(timerSeconds)}
              </span>
            </div>
            <div className="bg-white/10 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
              <span className="text-[11px] font-semibold text-indigo-200 uppercase tracking-wider block">
                Personalization
              </span>
              <span className="text-base font-bold mt-2 block truncate">
                {generatedQuestions.resume_based ? 'Resume Tailored' : 'Standard Bank'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
          <div className="text-xs text-slate-600">
            <strong>{reportData.evaluated_questions} evaluated questions</strong> analyzed across correctness, depth, and communication.
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Button
              size="sm"
              variant="outline"
              icon={copiedTranscript ? Check : Copy}
              onClick={handleCopyTranscript}
            >
              {copiedTranscript ? 'Report Copied!' : 'Copy Full Report'}
            </Button>
            <Button
              size="sm"
              variant="outline"
              icon={Download}
              onClick={() => {
                exportInterviewReportPDF({
                  ...reportData,
                  target_role: generatedQuestions.target_role,
                  interview_type: generatedQuestions.interview_type,
                  difficulty: generatedQuestions.difficulty,
                  evaluations: evaluations,
                  questions: generatedQuestions.questions,
                }, user?.full_name);
              }}
            >
              Download Report (PDF)
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleExitSession}
            >
              Back to Generator
            </Button>
            <Button
              size="sm"
              variant="primary"
              icon={RotateCcw}
              onClick={handleRetakeSession}
            >
              Retake Interview
            </Button>
          </div>
        </div>

        {/* Aggregate Strengths, Weaknesses, and Improvements */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-emerald-50/80 border border-emerald-200 rounded-2xl p-5 space-y-3 shadow-2xs">
            <span className="text-xs font-bold text-emerald-950 uppercase tracking-wider flex items-center gap-2">
              <ThumbsUp className="w-4 h-4 text-emerald-600" />
              Strong Areas
            </span>
            <ul className="space-y-2 text-xs">
              {(finalReport?.strong_areas || reportData.strong_areas).map((item, idx) => (
                <li key={idx} className="text-emerald-900 flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">•</span>
                  <span className="leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-amber-50/80 border border-amber-200 rounded-2xl p-5 space-y-3 shadow-2xs">
            <span className="text-xs font-bold text-amber-950 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Weak Areas
            </span>
            <ul className="space-y-2 text-xs">
              {(finalReport?.weak_areas || reportData.weak_areas).map((item, idx) => (
                <li key={idx} className="text-amber-900 flex items-start gap-2">
                  <span className="text-amber-600 font-bold">•</span>
                  <span className="leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-indigo-50/80 border border-indigo-200 rounded-2xl p-5 space-y-3 shadow-2xs">
            <span className="text-xs font-bold text-indigo-950 uppercase tracking-wider flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-indigo-600" />
              Top Recommendations
            </span>
            <ul className="space-y-2 text-xs">
              {(finalReport?.top_improvements || reportData.top_improvements).map((item, idx) => (
                <li key={idx} className="text-indigo-900 flex items-start gap-2">
                  <span className="text-indigo-600 font-bold">•</span>
                  <span className="leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Detailed Question Review Breakdown */}
        <div className="space-y-5">
          <h2 className="text-lg font-bold text-slate-900 font-heading">
            Per-Question Evaluation Breakdown
          </h2>

          {generatedQuestions.questions.map((q, idx) => {
            const candidateAns = candidateAnswers[idx]?.trim();
            const ev = evaluations[idx];

            return (
              <div
                key={idx}
                className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-5"
              >
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex items-start gap-3">
                    <span className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 font-mono text-xs font-bold flex items-center justify-center shrink-0">
                      {String(idx + 1).padStart(2, '0')}
                    </span>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={getCategoryBadgeVariant(q.category)} size="sm">
                          {q.category}
                        </Badge>
                        <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                          {q.topic}
                        </span>
                        <Badge variant={getDifficultyBadgeVariant(q.difficulty)} size="sm">
                          {q.difficulty}
                        </Badge>
                        {ev && (
                          <Badge variant={ev.overall_score >= 8 ? 'success' : ev.overall_score >= 6 ? 'primary' : 'warning'} size="sm">
                            Score: {ev.overall_score} / 10
                          </Badge>
                        )}
                      </div>
                      <h3 className="text-base font-bold text-slate-900 pt-1">
                        {q.question}
                      </h3>
                    </div>
                  </div>
                </div>

                {/* Candidate Response */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                    Candidate Response:
                  </span>
                  {candidateAns ? (
                    <p className="text-xs sm:text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
                      {candidateAns}
                    </p>
                  ) : (
                    <p className="text-xs italic text-slate-400">
                      No response drafted for this question.
                    </p>
                  )}
                </div>

                {/* Evaluation Feedback */}
                {ev ? (
                  <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-3 text-xs">
                    <div>
                      <span className="text-[11px] font-bold text-purple-950 uppercase tracking-wider block mb-1">
                        AI Evaluator Feedback:
                      </span>
                      <p className="text-purple-900 leading-relaxed">{ev.summary}</p>
                    </div>

                    {ev.strengths?.length > 0 && (
                      <div>
                        <span className="text-[10px] font-bold text-emerald-800 uppercase block">Strengths:</span>
                        <ul className="text-emerald-900 space-y-0.5 mt-0.5">
                          {ev.strengths.map((s, sIdx) => (
                            <li key={sIdx}>✓ {s}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {ev.weaknesses?.length > 0 && (
                      <div>
                        <span className="text-[10px] font-bold text-amber-800 uppercase block">Areas for Growth:</span>
                        <ul className="text-amber-900 space-y-0.5 mt-0.5">
                          {ev.weaknesses.map((w, wIdx) => (
                            <li key={wIdx}>• {w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {ev.model_answer_outline && (
                      <div className="pt-2 border-t border-purple-100">
                        <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Suggested Outline:</span>
                        <div className="bg-white/80 p-2.5 rounded-lg border border-purple-100 text-slate-700 font-mono text-[11px]">
                          {ev.model_answer_outline}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-400 italic">
                    Not evaluated during the session.
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom Navigation */}
        <div className="flex justify-between items-center bg-slate-50 border border-slate-200 p-5 rounded-2xl">
          <Button size="sm" variant="outline" onClick={handleExitSession}>
            Return to Generator
          </Button>
          <Button size="sm" variant="primary" icon={RotateCcw} onClick={handleRetakeSession}>
            Practice Again
          </Button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // RENDER: Default Generator / History Tab View
  // ---------------------------------------------------------------------------
  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="sm">
              Phase 5 AI Interview Evaluator
            </Badge>
            <span className="text-xs text-slate-400">• Gemini 1.5 Flash Scoring & Evaluation</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
            AI Interview Question Generator & Evaluator
          </h1>
          <p className="mt-1 text-sm text-slate-500 max-w-2xl">
            Configure target role, interview type, and difficulty. Practice interactive mock interviews with instant AI scoring, dimensional feedback, and comprehensive session reports.
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl self-start sm:self-auto shrink-0">
          <button
            type="button"
            onClick={() => setActiveTab('generator')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'generator'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Question Generator
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('history')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'history'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Question History</span>
            {historyList.length > 0 && (
              <span className="ml-0.5 px-1.5 py-0.2 bg-indigo-100 text-indigo-700 text-[10px] rounded-full font-bold">
                {historyList.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Phase 7 Voice Interview Switch Banner */}
      <div className="p-4 bg-gradient-to-r from-rose-50/90 via-indigo-50/70 to-purple-50/80 border border-rose-200/80 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-rose-600 text-white flex items-center justify-center shrink-0 shadow-xs">
            <Mic className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-900">
                Prefer Speaking Aloud? Try Voice Interview Mode
              </span>
              <Badge variant="danger" size="sm" className="bg-rose-100 text-rose-700">
                Phase 7
              </Badge>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              Practice answering using your microphone with real-time Speech-to-Text transcription and AI feedback.
            </p>
          </div>
        </div>
        <Button
          size="sm"
          variant="primary"
          icon={Mic}
          onClick={() => navigate('/voice-interview')}
          className="bg-rose-600 hover:bg-rose-700 shrink-0"
        >
          Open Voice Interview
        </Button>
      </div>

      {/* Resume Awareness Integration Banner */}
      {isAuthenticated && (
        <div>
          {resumeStatus.has_resume ? (
            <div className="p-4 bg-gradient-to-r from-emerald-50/90 to-teal-50/70 border border-emerald-200/90 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                  <Sparkles className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-emerald-950">
                      Questions will be personalized using your latest resume analysis.
                    </span>
                    <Badge variant="success" size="sm">
                      {resumeStatus.overall_score}% Match Score
                    </Badge>
                  </div>
                  <p className="text-xs text-emerald-800/90 mt-1">
                    Detected skills from <strong>{resumeStatus.filename}</strong>:
                  </p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {resumeStatus.detected_skills.map((skill) => (
                      <span
                        key={skill}
                        className="px-2 py-0.5 bg-white/90 border border-emerald-300 text-emerald-800 text-[11px] font-semibold rounded-md shadow-2xs"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <Link to="/resume-analyzer" className="shrink-0 self-end md:self-center">
                <Button size="sm" variant="outline" icon={FileText}>
                  Update Resume
                </Button>
              </Link>
            </div>
          ) : (
            <div className="p-4 bg-slate-50 border border-slate-200/90 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-600">
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                <span>Upload your resume to get more personalized interview questions.</span>
              </div>
              <Link to="/resume-analyzer">
                <Button size="sm" variant="outline" icon={ArrowRight} iconPosition="right">
                  Analyze Resume
                </Button>
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Generator Tab */}
      {activeTab === 'generator' && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Form Section */}
            <div className="lg:col-span-7">
              <Card
                title="Interview Parameters"
                subtitle="Choose your interview specifications"
                icon={Sliders}
              >
                <form onSubmit={handleGenerateQuestions} className="space-y-6">
                  {/* Role Selector */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-semibold text-slate-700 tracking-wide">
                        Target Role
                      </label>
                      <span className="text-[11px] text-slate-400">8 Supported Roles</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {roles.map((r) => (
                        <button
                          key={r}
                          type="button"
                          disabled={isGenerating}
                          onClick={() => setTargetRole(r)}
                          className={`px-3 py-2.5 rounded-xl text-xs font-medium text-left border transition-all cursor-pointer flex items-center justify-between ${
                            targetRole === r
                              ? 'border-indigo-600 bg-indigo-50/70 text-indigo-700 font-semibold shadow-xs'
                              : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                          } ${isGenerating ? 'opacity-60 cursor-not-allowed' : ''}`}
                        >
                          <span>{r}</span>
                          {targetRole === r && (
                            <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Interview Type */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 tracking-wide mb-2">
                      Interview Type
                    </label>
                    <div className="grid grid-cols-3 gap-2.5">
                      {types.map((t) => (
                        <button
                          key={t}
                          type="button"
                          disabled={isGenerating}
                          onClick={() => setInterviewType(t)}
                          className={`py-2.5 px-3 rounded-xl text-xs font-medium border text-center transition-all cursor-pointer ${
                            interviewType === t
                              ? 'border-indigo-600 bg-indigo-50/70 text-indigo-700 font-semibold shadow-xs'
                              : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                          } ${isGenerating ? 'opacity-60 cursor-not-allowed' : ''}`}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Difficulty */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 tracking-wide mb-2">
                      Difficulty Level
                    </label>
                    <div className="grid grid-cols-3 gap-2.5">
                      {difficulties.map((d) => (
                        <button
                          key={d}
                          type="button"
                          disabled={isGenerating}
                          onClick={() => setDifficulty(d)}
                          className={`py-2.5 px-3 rounded-xl text-xs font-medium border text-center transition-all cursor-pointer ${
                            difficulty === d
                              ? 'border-indigo-600 bg-indigo-50/70 text-indigo-700 font-semibold shadow-xs'
                              : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                          } ${isGenerating ? 'opacity-60 cursor-not-allowed' : ''}`}
                        >
                          {d}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Question Count */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 tracking-wide mb-2">
                      Number of Questions
                    </label>
                    <div className="grid grid-cols-3 gap-2.5">
                      {questionOptions.map((opt) => (
                        <button
                          key={opt}
                          type="button"
                          disabled={isGenerating}
                          onClick={() => setQuestionCount(opt)}
                          className={`py-2.5 px-3 rounded-xl text-xs font-medium border text-center transition-all cursor-pointer ${
                            questionCount === opt
                              ? 'border-indigo-600 bg-indigo-50/70 text-indigo-700 font-semibold shadow-xs'
                              : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                          } ${isGenerating ? 'opacity-60 cursor-not-allowed' : ''}`}
                        >
                          {opt} Questions
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Submit Button */}
                  <div className="pt-2">
                    <Button
                      type="submit"
                      size="lg"
                      variant="primary"
                      fullWidth
                      icon={Sparkles}
                      disabled={isGenerating}
                      loading={isGenerating}
                    >
                      {isGenerating ? 'Generating personalized interview questions...' : 'Generate Questions'}
                    </Button>
                  </div>
                </form>
              </Card>
            </div>

            {/* Sidebar Summary & Tips */}
            <div className="lg:col-span-5 space-y-6">
              <Card
                title="Session Configuration"
                subtitle="Live summary of your setup"
                icon={Video}
              >
                <div className="space-y-4 text-xs">
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Selected Role:</span>
                    <span className="font-semibold text-slate-800">{targetRole}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Interview Type:</span>
                    <span className="font-semibold text-slate-800">{interviewType}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Difficulty:</span>
                    <Badge variant={getDifficultyBadgeVariant(difficulty)} size="sm">
                      {difficulty}
                    </Badge>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Questions Count:</span>
                    <span className="font-semibold text-slate-800">{questionCount} Questions</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Estimated Duration:</span>
                    <span className="font-semibold text-slate-800">
                      {parseInt(questionCount, 10) * 3} - {parseInt(questionCount, 10) * 4} mins
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Resume Personalization:</span>
                    <Badge variant={resumeStatus.has_resume ? 'success' : 'neutral'} size="sm">
                      {resumeStatus.has_resume ? 'Active' : 'Standard'}
                    </Badge>
                  </div>
                </div>

                <div className="mt-6 p-4 rounded-xl bg-indigo-50/70 border border-indigo-100 text-indigo-900 space-y-2">
                  <div className="flex items-center gap-1.5 font-semibold text-xs text-indigo-700">
                    <Brain className="w-4 h-4 text-indigo-600" />
                    <span>Gemini AI Engine & Scoring Active</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-indigo-700">
                    Questions are dynamically calibrated to your role, difficulty tier, and candidate skills with comprehensive AI evaluation on submission.
                  </p>
                </div>
              </Card>

              <Card title="Preparation Tips" icon={HelpCircle}>
                <ul className="space-y-2.5 text-xs text-slate-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>
                      Structure behavioral answers using the <strong>STAR</strong> method (Situation, Task, Action, Result).
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>
                      Address computational complexity and memory tradeoffs upfront before elaborating solutions.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>
                      Click <strong>Evaluate Answer</strong> after typing to receive multidimensional scoring and improvement suggestions.
                    </span>
                  </li>
                </ul>
              </Card>
            </div>
          </div>

          {/* Stepped Loading Animation */}
          {isGenerating && (
            <div className="bg-white border border-indigo-100 rounded-2xl p-6 shadow-sm space-y-5 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center animate-spin">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Generating your personalized questions...
                  </h3>
                  <p className="text-xs text-slate-500">
                    Gemini AI is crafting realistic questions for {targetRole} ({interviewType} • {difficulty})
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2">
                {[
                  { label: 'Analyzing role', desc: 'Parsing target competencies' },
                  {
                    label: 'Preparing topics',
                    desc: resumeStatus.has_resume
                      ? 'Integrating resume skills'
                      : 'Mapping domain syllabus',
                  },
                  { label: 'Generating questions', desc: 'Synthesizing realistic prompts' },
                  { label: 'Finalizing question set', desc: 'Validating Pydantic schema' },
                ].map((step, idx) => (
                  <div
                    key={step.label}
                    className={`p-3 rounded-xl border text-xs transition-all ${
                      generationStep >= idx
                        ? 'border-indigo-500 bg-indigo-50/50 text-indigo-900 font-medium'
                        : 'border-slate-100 bg-slate-50/50 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-bold mb-0.5">
                      <span
                        className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center ${
                          generationStep >= idx
                            ? 'bg-indigo-600 text-white'
                            : 'bg-slate-200 text-slate-500'
                        }`}
                      >
                        {idx + 1}
                      </span>
                      <span>{step.label}</span>
                    </div>
                    <span className="text-[11px] text-slate-500">{step.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="space-y-2">
                <h4 className="text-xs font-bold">Failed to Generate Questions</h4>
                <p className="text-xs text-rose-700">{error}</p>
                <Button size="sm" variant="outline" onClick={handleGenerateQuestions}>
                  Retry Generation
                </Button>
              </div>
            </div>
          )}

          {/* Generated Questions Result Display */}
          {generatedQuestions && (
            <div id="questions-result" className="space-y-6 pt-4">
              <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-5">
                <div>
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <Badge variant="primary" size="md">
                      {generatedQuestions.target_role}
                    </Badge>
                    <Badge
                      variant={generatedQuestions.interview_type === 'HR' ? 'purple' : 'primary'}
                      size="md"
                    >
                      {generatedQuestions.interview_type}
                    </Badge>
                    <Badge variant={getDifficultyBadgeVariant(generatedQuestions.difficulty)} size="md">
                      {generatedQuestions.difficulty}
                    </Badge>
                    <Badge variant={generatedQuestions.resume_based ? 'success' : 'neutral'} size="md">
                      {generatedQuestions.resume_based ? 'Personalized with Resume' : 'Role Standard'}
                    </Badge>
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 font-heading">
                    Generated Interview Questions ({generatedQuestions.questions.length})
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Review each question or launch an active self-paced practice session with live timer, answer notes, and AI scoring.
                  </p>
                </div>

                <div className="flex items-center gap-2.5 flex-wrap">
                  <Button
                    size="sm"
                    variant="outline"
                    icon={RotateCcw}
                    onClick={() => {
                      setGeneratedQuestions(null);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                  >
                    Generate New
                  </Button>
                  <Button
                    size="sm"
                    variant="primary"
                    icon={Play}
                    onClick={() => handleStartSession()}
                  >
                    Start Interview
                  </Button>
                </div>
              </div>

              {/* Questions List */}
              <div className="space-y-4">
                {generatedQuestions.questions.map((q, idx) => {
                  const numFormatted = String(q.question_number || idx + 1).padStart(2, '0');
                  const isCopied = copiedIndex === idx;

                  return (
                    <div
                      key={q.question_number || idx}
                      className="bg-white border border-slate-200/90 hover:border-indigo-300 rounded-2xl p-6 shadow-2xs hover:shadow-xs transition-all space-y-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <span className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 font-mono text-xs font-bold flex items-center justify-center shrink-0">
                            {numFormatted}
                          </span>
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <Badge variant={getCategoryBadgeVariant(q.category)} size="sm">
                                {q.category}
                              </Badge>
                              <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                                {q.topic}
                              </span>
                              <Badge variant={getDifficultyBadgeVariant(q.difficulty)} size="sm">
                                {q.difficulty}
                              </Badge>
                            </div>
                            <h3 className="text-sm sm:text-base font-semibold text-slate-900 pt-1 leading-snug">
                              {q.question}
                            </h3>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleCopyQuestion(q.question, idx)}
                          title="Copy question text"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors shrink-0 cursor-pointer"
                        >
                          {isCopied ? (
                            <Check className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      {/* Expected Focus Areas */}
                      {q.expected_focus && q.expected_focus.length > 0 && (
                        <div className="pt-3 border-t border-slate-100/90">
                          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                            Expected Focus Areas:
                          </span>
                          <div className="flex flex-wrap gap-2">
                            {q.expected_focus.map((focusItem, fIdx) => (
                              <span
                                key={fIdx}
                                className="px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200/80 text-slate-700 text-xs font-medium flex items-center gap-1.5"
                              >
                                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                                {focusItem}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Bottom Quick Action Bar */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-xs text-slate-600">
                  <span>Questions generated and stored in your profile archives. Ready to practice?</span>
                </div>
                <div className="flex gap-2.5">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setGeneratedQuestions(null);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                  >
                    Generate New
                  </Button>
                  <Button
                    size="sm"
                    variant="primary"
                    icon={Play}
                    onClick={() => handleStartSession()}
                  >
                    Start Interview
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <Card
          title="Generated Question Sets History"
          subtitle="Review all previously generated interview question sets"
          icon={History}
        >
          {isLoadingHistory ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading question set archives...
            </div>
          ) : historyList.length === 0 ? (
            <div className="py-12 text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                <Sliders className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-800">No Question Sets Generated Yet</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Configure your target parameters and generate your first AI personalized question set.
              </p>
              <Button size="sm" variant="primary" onClick={() => setActiveTab('generator')}>
                Go to Generator
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Difficulty</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3">Completion</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {historyList.map((item) => {
                    const hasEvaluations = (item.evaluated_questions || 0) > 0 || item.overall_score !== null;
                    return (
                      <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-4 py-3.5 font-bold text-slate-900">{item.target_role}</td>
                        <td className="px-4 py-3.5">
                          <Badge variant={item.interview_type === 'HR' ? 'purple' : 'primary'} size="sm">
                            {item.interview_type}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant={getDifficultyBadgeVariant(item.difficulty)} size="sm">
                            {item.difficulty}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5">
                          {item.overall_score !== null && item.overall_score !== undefined ? (
                            <span className="font-extrabold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                              {item.overall_score}/10
                            </span>
                          ) : (
                            <span className="text-slate-400 italic text-[11px]">Not evaluated</span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 font-semibold text-slate-700">
                          {item.completion_rate !== undefined ? `${item.completion_rate}% (${item.evaluated_questions || 0}/${item.number_of_questions})` : `${item.number_of_questions} Qs`}
                        </td>
                        <td className="px-4 py-3.5 text-slate-500">
                          {new Date(item.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {hasEvaluations && (
                              <Button
                                size="sm"
                                variant="outline"
                                icon={Award}
                                onClick={() => handleOpenHistoricalReport(item.id)}
                              >
                                Report
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewHistoricalSet(item.id)}
                            >
                              View
                            </Button>
                            <Button
                              size="sm"
                              variant="primary"
                              icon={Play}
                              onClick={async () => {
                                try {
                                  setIsLoadingHistory(true);
                                  const fullSet = await getQuestionSet(item.id);
                                  handleStartSession(fullSet);
                                } catch (e) {
                                  console.error('Failed to load set:', e);
                                } finally {
                                  setIsLoadingHistory(false);
                                }
                              }}
                            >
                              Practice
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default MockInterviewPage;
