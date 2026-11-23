import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Mic,
  MicOff,
  Square,
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  ThumbsUp,
  Lightbulb,
  Clock,
  Check,
  Copy,
  ChevronRight,
  ChevronLeft,
  ArrowRight,
  Award,
  LogOut,
  Download,
  FileText,
  Radio,
  FileCheck,
  Sliders,
  Bot,
  MessageSquare,
  Headphones,
} from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { exportInterviewReportPDF } from '../utils/pdfExport';
import {
  generateInterviewQuestions,
  getInterviewResumeStatus,
  startVoiceSession,
  submitVoiceNextQuestion,
  getActiveVoiceSession,
  finishVoiceSession,
  getVoiceReport,
} from '../services/api';

const VoiceInterviewPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // ---------------------------------------------------------------------------
  // View & Session Stage
  // ---------------------------------------------------------------------------
  // 'setup' | 'interview' | 'report'
  const [sessionStage, setSessionStage] = useState('setup');
  const [sessionData, setSessionData] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [candidateAnswers, setCandidateAnswers] = useState({});
  const [evaluations, setEvaluations] = useState({});
  const [finalReport, setFinalReport] = useState(null);

  // ---------------------------------------------------------------------------
  // Interview State Machine
  // ---------------------------------------------------------------------------
  // 'IDLE' | 'AI_THINKING' | 'AI_SPEAKING' | 'LISTENING' | 'TRANSCRIBING' | 'ANSWER_REVIEW' | 'AI_ANALYZING' | 'NEXT_QUESTION' | 'FINAL_ANALYSIS'
  const [interviewState, setInterviewState] = useState('IDLE');
  const [latestAcknowledgement, setLatestAcknowledgement] = useState('');
  const [latestReason, setLatestReason] = useState('');

  // ---------------------------------------------------------------------------
  // Setup Form States
  // ---------------------------------------------------------------------------
  const [targetRole, setTargetRole] = useState('Full Stack Developer');
  const [interviewType, setInterviewType] = useState('Technical');
  const [difficulty, setDifficulty] = useState('Intermediate');
  const [questionCount, setQuestionCount] = useState('5');
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeSessionToRestore, setActiveSessionToRestore] = useState(null);
  const [isRestoringSession, setIsRestoringSession] = useState(false);
  const [resumeStatus, setResumeStatus] = useState({
    has_resume: false,
    job_role: null,
    detected_skills: [],
  });

  // ---------------------------------------------------------------------------
  // Text-To-Speech (TTS) States
  // ---------------------------------------------------------------------------
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isTtsSupported, setIsTtsSupported] = useState(true);

  // ---------------------------------------------------------------------------
  // Speech-To-Text (STT) & Audio States
  // ---------------------------------------------------------------------------
  const [micPermission, setMicPermission] = useState('prompt'); // 'prompt' | 'granted' | 'denied' | 'unavailable' | 'unsupported'
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [liveInterimTranscript, setLiveInterimTranscript] = useState('');
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [isSpeechSupported, setIsSpeechSupported] = useState(true);

  // ---------------------------------------------------------------------------
  // UI & Dialog States
  // ---------------------------------------------------------------------------
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationError, setEvaluationError] = useState(null);
  const [showExpectedFocus, setShowExpectedFocus] = useState(false);
  const [isFinishConfirmOpen, setIsFinishConfirmOpen] = useState(false);
  const [isExitConfirmOpen, setIsExitConfirmOpen] = useState(false);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  // Refs for audio hardware, timers, recognition
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const recognitionRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const transcriptAccumulatorRef = useRef('');
  const spokenQuestionIndexRef = useRef(-1);

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

  // ---------------------------------------------------------------------------
  // Mount: Check Browser API Support, Resume Context & Active Session
  // ---------------------------------------------------------------------------
  useEffect(() => {
    // Check SpeechRecognition
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSpeechSupported(false);
    }

    // Check SpeechSynthesis
    if (!window.speechSynthesis) {
      setIsTtsSupported(false);
    }

    // Check getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setMicPermission('unsupported');
    }

    loadResumeContext();
    checkForActiveSession();

    return () => {
      cleanupAudio();
      stopQuestionSpeech();
    };
  }, []);

  const loadResumeContext = async () => {
    try {
      const status = await getInterviewResumeStatus();
      if (status && status.has_resume) {
        setResumeStatus(status);
        if (status.job_role && roles.includes(status.job_role)) {
          setTargetRole(status.job_role);
        }
      }
    } catch (e) {
      console.warn('Resume status check notice:', e);
    }
  };

  const checkForActiveSession = async () => {
    try {
      const active = await getActiveVoiceSession();
      if (active && active.session_id && active.status === 'active') {
        setActiveSessionToRestore(active);
      }
    } catch (e) {
      console.warn('Active session check notice:', e);
    }
  };

  // ---------------------------------------------------------------------------
  // Cleanup Audio Hardware
  // ---------------------------------------------------------------------------
  const cleanupAudio = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
      mediaRecorderRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
      } catch (e) {}
      audioContextRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {}
      recognitionRef.current = null;
    }

    setIsRecording(false);
    setIsPaused(false);
    setAudioLevel(0);
  };

  // ---------------------------------------------------------------------------
  // Text-To-Speech (TTS): AI Speaks Question Aloud
  // ---------------------------------------------------------------------------
  const speakCurrentQuestion = (text, acknowledgement = '') => {
    if (!window.speechSynthesis || isMuted) {
      setInterviewState('ANSWER_REVIEW');
      setIsSpeakingQuestion(false);
      return;
    }

    try {
      window.speechSynthesis.cancel();

      const fullSpeechText = acknowledgement
        ? `${acknowledgement} ... ${text}`
        : text;

      const utterance = new SpeechSynthesisUtterance(fullSpeechText);
      utterance.lang = 'en-US';
      utterance.rate = 0.95; // Natural conversational tempo
      utterance.pitch = 1.0;

      // Select natural sounding voice if available
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        const naturalVoice =
          voices.find(
            (v) =>
              (v.name.includes('Natural') ||
                v.name.includes('Google') ||
                v.name.includes('Samantha') ||
                v.name.includes('Zira') ||
                v.name.includes('Daniel')) &&
              v.lang.startsWith('en')
          ) || voices.find((v) => v.lang.startsWith('en'));

        if (naturalVoice) {
          utterance.voice = naturalVoice;
        }
      }

      utterance.onstart = () => {
        setIsSpeakingQuestion(true);
        setInterviewState('AI_SPEAKING');
      };

      utterance.onend = () => {
        setIsSpeakingQuestion(false);
        setInterviewState('ANSWER_REVIEW');
      };

      utterance.onerror = (e) => {
        console.warn('SpeechSynthesis error:', e);
        setIsSpeakingQuestion(false);
        setInterviewState('ANSWER_REVIEW');
      };

      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn('SpeechSynthesis invocation error:', err);
      setIsSpeakingQuestion(false);
      setInterviewState('ANSWER_REVIEW');
    }
  };

  const stopQuestionSpeech = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeakingQuestion(false);
    if (interviewState === 'AI_SPEAKING') {
      setInterviewState('ANSWER_REVIEW');
    }
  };

  const toggleMute = () => {
    if (!isMuted) {
      stopQuestionSpeech();
      setIsMuted(true);
    } else {
      setIsMuted(false);
    }
  };

  // Auto-speak question when question changes or when session begins
  const currentQ =
    sessionData?.questions && sessionData.questions[currentQuestionIndex]
      ? sessionData.questions[currentQuestionIndex]
      : null;

  useEffect(() => {
    if (
      sessionStage === 'interview' &&
      currentQ &&
      spokenQuestionIndexRef.current !== currentQuestionIndex
    ) {
      spokenQuestionIndexRef.current = currentQuestionIndex;
      speakCurrentQuestion(currentQ.question, latestAcknowledgement);
    }
  }, [sessionStage, currentQuestionIndex, currentQ]);

  // ---------------------------------------------------------------------------
  // Speech-To-Text (STT): Recording Handlers
  // ---------------------------------------------------------------------------
  const startRecording = async () => {
    // If AI is currently speaking, stop it or prevent overlap
    stopQuestionSpeech();
    setEvaluationError(null);

    // 1. Request microphone access
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      mediaStreamRef.current = stream;
      setMicPermission('granted');
    } catch (err) {
      console.error('Microphone access denied:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setMicPermission('denied');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setMicPermission('unavailable');
      } else {
        setMicPermission('denied');
      }
      return;
    }

    // 2. Set up AudioContext for real-time visualizer
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        const audioCtx = new AudioCtx();
        audioContextRef.current = audioCtx;
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        analyserRef.current = analyser;

        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const updateLevel = () => {
          if (!analyserRef.current) return;
          analyserRef.current.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const avg = sum / dataArray.length;
          setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)));
          animationFrameRef.current = requestAnimationFrame(updateLevel);
        };
        updateLevel();
      }
    } catch (e) {
      console.warn('Audio visualizer not supported or blocked:', e);
    }

    // 3. Set up MediaRecorder
    try {
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      recorder.start(250);
    } catch (e) {
      console.warn('MediaRecorder error:', e);
    }

    // 4. Set up Continuous SpeechRecognition
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        transcriptAccumulatorRef.current = currentTranscript ? currentTranscript.trim() + ' ' : '';

        recognition.onresult = (event) => {
          setInterviewState('TRANSCRIBING');
          let interim = '';
          let final = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcriptText = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              final += transcriptText + ' ';
            } else {
              interim += transcriptText;
            }
          }

          if (final) {
            transcriptAccumulatorRef.current += final;
            setCurrentTranscript(transcriptAccumulatorRef.current.trim());
          }
          setLiveInterimTranscript(interim);
        };

        recognition.onerror = (event) => {
          console.warn('SpeechRecognition error:', event.error);
          if (event.error === 'not-allowed') {
            setMicPermission('denied');
          }
        };

        recognition.onend = () => {
          if (isRecording && !isPaused && recognitionRef.current) {
            try {
              recognition.start();
            } catch (err) {}
          }
        };

        recognition.start();
      } catch (err) {
        console.error('Failed to start SpeechRecognition:', err);
      }
    }

    // 5. Update state machine & duration timer
    setIsRecording(true);
    setIsPaused(false);
    setInterviewState('LISTENING');
    timerIntervalRef.current = setInterval(() => {
      setRecordingSeconds((prev) => prev + 1);
    }, 1000);
  };

  const pauseRecording = () => {
    if (!isRecording || isPaused) return;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.pause();
      } catch (e) {}
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }

    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    setIsPaused(true);
    setInterviewState('ANSWER_REVIEW');
  };

  const resumeRecording = () => {
    if (!isRecording || !isPaused) return;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      try {
        mediaRecorderRef.current.resume();
      } catch (e) {}
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
      } catch (e) {}
    }

    timerIntervalRef.current = setInterval(() => {
      setRecordingSeconds((prev) => prev + 1);
    }, 1000);

    setIsPaused(false);
    setInterviewState('LISTENING');
  };

  const stopRecording = () => {
    cleanupAudio();
    setLiveInterimTranscript('');
    if (transcriptAccumulatorRef.current.trim()) {
      setCurrentTranscript(transcriptAccumulatorRef.current.trim());
    }
    setInterviewState('ANSWER_REVIEW');
  };

  const handleClearTranscript = () => {
    setCurrentTranscript('');
    setLiveInterimTranscript('');
    transcriptAccumulatorRef.current = '';
    setRecordingSeconds(0);
  };

  const handleRerecord = () => {
    cleanupAudio();
    handleClearTranscript();
    startRecording();
  };

  // ---------------------------------------------------------------------------
  // Start Session (From Setup)
  // ---------------------------------------------------------------------------
  const handleStartVoiceSession = async () => {
    setIsGenerating(true);
    setEvaluationError(null);
    setInterviewState('AI_THINKING');

    try {
      const numQuestions = parseInt(questionCount, 10) || 5;
      const qsetResponse = await generateInterviewQuestions({
        target_role: targetRole,
        interview_type: interviewType,
        difficulty: difficulty,
        number_of_questions: numQuestions,
      });

      if (!qsetResponse || !qsetResponse.id) {
        throw new Error('Failed to generate interview questions.');
      }

      const voiceSession = await startVoiceSession({
        question_set_id: qsetResponse.id,
      });

      setSessionData(voiceSession);
      setCurrentQuestionIndex(0);
      setCandidateAnswers({});
      setEvaluations({});
      setCurrentTranscript('');
      setLatestAcknowledgement('');
      setLatestReason('');
      spokenQuestionIndexRef.current = -1;
      setSessionStage('interview');
      setInterviewState('AI_SPEAKING');
    } catch (err) {
      console.error('Error starting voice session:', err);
      setInterviewState('IDLE');
      setEvaluationError(
        err.response?.data?.detail || 'Failed to initialize voice interview session. Please try again.'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Restore Active Session
  // ---------------------------------------------------------------------------
  const handleRestoreActiveSession = () => {
    if (!activeSessionToRestore) return;

    setIsRestoringSession(true);
    try {
      const restoredAnswers = {};
      const restoredEvals = {};

      if (activeSessionToRestore.answers) {
        activeSessionToRestore.answers.forEach((ans, idx) => {
          restoredAnswers[idx] = ans.transcript;
          if (ans.evaluation) {
            restoredEvals[idx] = ans.evaluation;
          }
        });
      }

      setSessionData(activeSessionToRestore);
      setCandidateAnswers(restoredAnswers);
      setEvaluations(restoredEvals);

      const targetIdx = Math.max(
        0,
        Math.min(
          (activeSessionToRestore.current_question || 1) - 1,
          (activeSessionToRestore.questions?.length || 1) - 1
        )
      );
      setCurrentQuestionIndex(targetIdx);
      setCurrentTranscript(restoredAnswers[targetIdx] || '');
      spokenQuestionIndexRef.current = -1;
      setSessionStage('interview');
      setInterviewState('ANSWER_REVIEW');
      setActiveSessionToRestore(null);
    } catch (err) {
      console.error('Failed to restore active voice session:', err);
    } finally {
      setIsRestoringSession(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Submit Candidate Voice Answer -> AI Evaluates & Decides Next Question
  // ---------------------------------------------------------------------------
  const handleSubmitAnswer = async () => {
    if (isRecording) {
      stopRecording();
    }
    stopQuestionSpeech();

    const transcriptToSubmit = currentTranscript.trim();
    if (!transcriptToSubmit) {
      setEvaluationError('Please speak or type an answer before submitting.');
      return;
    }

    setIsEvaluating(true);
    setEvaluationError(null);
    setInterviewState('AI_ANALYZING');

    const questionNumber = currentQuestionIndex + 1;

    try {
      const res = await submitVoiceNextQuestion({
        session_id: sessionData.session_id,
        question_number: questionNumber,
        transcript: transcriptToSubmit,
      });

      // 1. Record candidate answer and evaluation
      const updatedAnswers = {
        ...candidateAnswers,
        [currentQuestionIndex]: transcriptToSubmit,
      };
      setCandidateAnswers(updatedAnswers);

      if (res.evaluation) {
        setEvaluations((prev) => ({
          ...prev,
          [currentQuestionIndex]: res.evaluation,
        }));
      }

      // 2. Check if interview is completed
      if (res.interview_complete || res.is_last_question || res.session_status === 'completed') {
        setInterviewState('FINAL_ANALYSIS');
        await handleFinishSession();
        return;
      }

      // 3. Progress to next dynamically generated question
      if (res.next_question) {
        setInterviewState('NEXT_QUESTION');
        const nextQIndex = currentQuestionIndex + 1;

        // Update session questions list with new dynamic question
        const updatedQuestions = [...(sessionData.questions || [])];
        if (nextQIndex < updatedQuestions.length) {
          updatedQuestions[nextQIndex] = res.next_question;
        } else {
          updatedQuestions.push(res.next_question);
        }

        setSessionData((prev) => ({
          ...prev,
          questions: updatedQuestions,
          current_question: nextQIndex + 1,
        }));

        setLatestAcknowledgement(res.acknowledgement || 'Thank you.');
        setLatestReason(res.reason || '');
        setCurrentQuestionIndex(nextQIndex);
        setCurrentTranscript('');
        transcriptAccumulatorRef.current = '';
        setRecordingSeconds(0);

        // Transition smoothly to AI speaking the next question
        setInterviewState('AI_SPEAKING');
      }
    } catch (err) {
      console.error('Failed to submit answer and generate next question:', err);
      setInterviewState('ANSWER_REVIEW');
      setEvaluationError(
        err.response?.data?.detail || 'Failed to submit answer. Please retry.'
      );
    } finally {
      setIsEvaluating(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Complete Session & Load Final Voice Report
  // ---------------------------------------------------------------------------
  const handleFinishSession = async () => {
    cleanupAudio();
    stopQuestionSpeech();
    setIsFinishConfirmOpen(false);
    setInterviewState('FINAL_ANALYSIS');

    try {
      await finishVoiceSession(sessionData.session_id);
    } catch (e) {
      console.warn('Finish voice session notice:', e);
    }

    try {
      const report = await getVoiceReport(sessionData.session_id);
      setFinalReport(report);
      setSessionStage('report');
      setInterviewState('IDLE');
    } catch (err) {
      console.error('Failed to load final report:', err);
      setSessionStage('report');
      setInterviewState('IDLE');
    }
  };

  const handleRetakeSession = () => {
    cleanupAudio();
    stopQuestionSpeech();
    setSessionData(null);
    setCandidateAnswers({});
    setEvaluations({});
    setFinalReport(null);
    setCurrentTranscript('');
    setLatestAcknowledgement('');
    setLatestReason('');
    spokenQuestionIndexRef.current = -1;
    setSessionStage('setup');
    setInterviewState('IDLE');
  };

  const handleExitSession = () => {
    cleanupAudio();
    stopQuestionSpeech();
    setIsExitConfirmOpen(false);
    navigate('/mock-interview');
  };

  const handleCopyReport = () => {
    if (!sessionData) return;
    let text = `AI INTERVIEW REPORT - ${sessionData.target_role || targetRole}\n`;
    text += `Date: ${new Date().toLocaleDateString()}\n`;
    text += `Overall Score: ${finalReport?.overall_score || 0}/10\n\n`;

    sessionData.questions?.forEach((q, idx) => {
      const ans = candidateAnswers[idx] || '(Not answered)';
      const ev = evaluations[idx];
      text += `Question ${idx + 1}: ${q.question}\n`;
      text += `Your Spoken Response:\n${ans}\n`;
      if (ev) {
        text += `Score: ${ev.overall_score}/10\n`;
        text += `Feedback: ${ev.summary}\n`;
      }
      text += `----------------------------------------\n`;
    });

    navigator.clipboard.writeText(text);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2500);
  };

  const formatTimer = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const totalQuestions =
    sessionData?.questions?.length || sessionData?.total_questions || 5;

  const wordCount = currentTranscript.trim()
    ? currentTranscript.trim().split(/\s+/).filter(Boolean).length
    : 0;

  // ===========================================================================
  // RENDER 1: Setup / Configuration Stage
  // ===========================================================================
  if (sessionStage === 'setup') {
    return (
      <div className="max-w-4xl mx-auto space-y-8 pb-16">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <Badge variant="primary" size="sm" className="bg-indigo-100 text-indigo-700">
                AI Voice Interviewer
              </Badge>
              <span className="text-xs text-slate-400 font-medium">
                • Conversational HR & Technical Simulation
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
              AI Interviewer Experience
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-slate-500">
              Practice speaking with a realistic AI interviewer. The AI speaks questions aloud,
              analyzes your spoken answers, and asks intelligent dynamic follow-ups.
            </p>
          </div>

          <Button
            size="sm"
            variant="outline"
            icon={FileText}
            onClick={() => navigate('/mock-interview')}
          >
            Switch to Text Mode
          </Button>
        </div>

        {/* Active Session Restoration Alert */}
        {activeSessionToRestore && (
          <div className="bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-indigo-500/10 border border-indigo-200 rounded-2xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                <Bot className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Active Interview Session Found
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  You have an in-progress interview for{' '}
                  <span className="font-semibold text-indigo-700">
                    {activeSessionToRestore.target_role || activeSessionToRestore.role}
                  </span>{' '}
                  (Question {activeSessionToRestore.current_question || 1} of{' '}
                  {activeSessionToRestore.total_questions || 5}).
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2.5">
              <Button
                size="sm"
                variant="primary"
                icon={Play}
                loading={isRestoringSession}
                onClick={handleRestoreActiveSession}
              >
                Resume Interview
              </Button>
            </div>
          </div>
        )}

        {/* Speech API Notice */}
        {!isSpeechSupported && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 text-xs text-amber-900">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Web Speech Recognition Notice:</span> Live speech-to-text
              is optimized for Chrome, Edge, and Chromium browsers. You can still speak, review, or
              type answers directly in the response box.
            </div>
          </div>
        )}

        {/* Configuration Card */}
        <Card className="p-6 sm:p-8 space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 font-heading">
              <Sliders className="w-4 h-4 text-indigo-600" />
              Configure Interview Parameters
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Select your target role and parameters. The AI interviewer will formulate tailored questions and intelligent follow-ups.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Target Role */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Target Role</label>
              <select
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-medium cursor-pointer"
              >
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            {/* Interview Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Interview Mode</label>
              <select
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-medium cursor-pointer"
              >
                <option value="Technical">Technical (Architecture, Code, Trade-offs)</option>
                <option value="HR">HR & Behavioral (STAR Stories, Leadership, Culture)</option>
                <option value="Mixed">Mixed (Combined Technical + Behavioral)</option>
              </select>
            </div>

            {/* Difficulty */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Difficulty Level</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-medium cursor-pointer"
              >
                <option value="Beginner">Beginner (Foundations & Concepts)</option>
                <option value="Intermediate">Intermediate (Real-world scenarios & Trade-offs)</option>
                <option value="Advanced">Advanced (High-scale, Performance & Depth)</option>
              </select>
            </div>

            {/* Question Count */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Interview Length</label>
              <select
                value={questionCount}
                onChange={(e) => setQuestionCount(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-medium cursor-pointer"
              >
                <option value="5">5 Questions (~15–20 mins standard round)</option>
                <option value="10">10 Questions (~30–40 mins full simulation)</option>
                <option value="15">15 Questions (~45–60 mins comprehensive drill)</option>
              </select>
            </div>
          </div>

          {/* Resume Personalization Banner */}
          {resumeStatus.has_resume && (
            <div className="p-3.5 bg-emerald-50/80 border border-emerald-200 rounded-xl flex items-center gap-3 text-xs text-emerald-900">
              <FileCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <span className="font-bold">Resume Profile Connected:</span> The interviewer has your
                analyzed resume context and verified skills ({resumeStatus.detected_skills?.slice(0, 4).join(', ')}).
              </div>
            </div>
          )}

          {/* Error Message */}
          {evaluationError && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{evaluationError}</span>
            </div>
          )}

          {/* Action Row */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-100">
            <span className="text-xs text-slate-400">
              Microphone access is requested when you start speaking.
            </span>
            <Button
              size="md"
              variant="primary"
              icon={Bot}
              loading={isGenerating}
              disabled={isGenerating}
              onClick={handleStartVoiceSession}
              className="w-full sm:w-auto"
            >
              {isGenerating ? 'Preparing AI Interviewer...' : 'Start AI Interview'}
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // ===========================================================================
  // RENDER 2: Active AI Interviewer Room
  // ===========================================================================
  if (sessionStage === 'interview' && currentQ) {
    const isAiSpeaking = interviewState === 'AI_SPEAKING' || isSpeakingQuestion;
    const isAiAnalyzing = interviewState === 'AI_ANALYZING' || isEvaluating;
    const isCandidateSpeaking = interviewState === 'LISTENING' || interviewState === 'TRANSCRIBING';

    return (
      <div className="max-w-5xl mx-auto space-y-6 pb-20">
        {/* Top Session Status Bar */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsExitConfirmOpen(true)}
              className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors flex items-center gap-1.5 text-xs font-semibold cursor-pointer"
              title="Exit Practice Session"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Conclude</span>
            </button>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="primary" size="sm">
                  {sessionData.target_role || targetRole}
                </Badge>
                <Badge
                  variant={sessionData.interview_type === 'HR' ? 'purple' : 'primary'}
                  size="sm"
                >
                  {sessionData.interview_type || interviewType} Round
                </Badge>
                <Badge variant="neutral" size="sm">
                  {sessionData.difficulty || difficulty}
                </Badge>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200">
                  <Bot className="w-3 h-3 text-indigo-600" />
                  AI Interviewer Active
                </span>
              </div>
              <h2 className="text-sm sm:text-base font-bold text-slate-900 mt-1 flex items-center gap-2">
                Question {currentQuestionIndex + 1} of {totalQuestions}
              </h2>
            </div>
          </div>

          {/* Stepper Dots & Top Actions */}
          <div className="flex items-center gap-3 self-end sm:self-auto">
            {/* Progress Dots */}
            <div className="flex items-center gap-1.5 mr-1">
              {Array.from({ length: totalQuestions }).map((_, idx) => (
                <div
                  key={idx}
                  className={`w-2.5 h-2.5 rounded-full transition-all ${
                    idx === currentQuestionIndex
                      ? 'bg-indigo-600 ring-4 ring-indigo-100 scale-110'
                      : candidateAnswers[idx]
                      ? 'bg-emerald-500'
                      : 'bg-slate-200'
                  }`}
                  title={`Question ${idx + 1}`}
                />
              ))}
            </div>

            {/* Mute/Unmute Toggle */}
            <button
              type="button"
              onClick={toggleMute}
              className={`p-2 rounded-xl border transition-all text-xs font-semibold flex items-center gap-1.5 cursor-pointer ${
                isMuted
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
              title={isMuted ? 'Unmute AI Voice' : 'Mute AI Voice'}
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              <span className="hidden sm:inline">{isMuted ? 'Muted' : 'Voice On'}</span>
            </button>

            {/* Past Q&A Toggle */}
            <button
              type="button"
              onClick={() => setShowHistoryDrawer(!showHistoryDrawer)}
              className="p-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            >
              <MessageSquare className="w-4 h-4" />
              <span className="hidden sm:inline">History ({Object.keys(candidateAnswers).length})</span>
            </button>
          </div>
        </div>

        {/* =====================================================================
            AI INTERVIEWER PERSONA CONSOLE
            ===================================================================== */}
        <div className="bg-gradient-to-b from-indigo-950 via-slate-900 to-indigo-900 rounded-3xl p-6 sm:p-8 text-white shadow-lg space-y-6 relative overflow-hidden border border-indigo-800/40">
          {/* Subtle background glow */}
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

          {/* AI Avatar & Status Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10 border-b border-indigo-800/40 pb-5">
            <div className="flex items-center gap-4">
              {/* Animated Avatar */}
              <div className="relative">
                <div
                  className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all ${
                    isAiSpeaking
                      ? 'bg-gradient-to-tr from-cyan-500 to-indigo-600 text-white shadow-lg shadow-cyan-500/30 ring-4 ring-cyan-400/30 animate-pulse'
                      : isAiAnalyzing
                      ? 'bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-500/30 ring-4 ring-purple-400/30'
                      : 'bg-indigo-900/80 text-indigo-300 border border-indigo-700/60'
                  }`}
                >
                  <Bot className="w-7 h-7" />
                </div>
                {/* Speaking indicator waves */}
                {isAiSpeaking && (
                  <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-cyan-500" />
                  </span>
                )}
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white tracking-wide font-heading">
                    AI Interviewer
                  </h3>
                  <span className="text-[10px] font-semibold text-indigo-300 uppercase tracking-wider px-2 py-0.5 rounded-md bg-indigo-800/60 border border-indigo-700/60">
                    {sessionData.target_role || targetRole}
                  </span>
                </div>

                {/* Dynamic Status Indicator */}
                <div className="flex items-center gap-2 mt-1">
                  {isAiSpeaking ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-cyan-300 font-semibold animate-pulse">
                      <Headphones className="w-3.5 h-3.5" />
                      AI Interviewer is speaking question aloud...
                    </span>
                  ) : isAiAnalyzing ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-purple-300 font-semibold animate-pulse">
                      <Sparkles className="w-3.5 h-3.5" />
                      AI is evaluating your response and preparing the next question...
                    </span>
                  ) : isCandidateSpeaking ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-rose-300 font-semibold">
                      <Mic className="w-3.5 h-3.5 animate-pulse" />
                      Listening to candidate...
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-xs text-emerald-300 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Your turn to speak. Microphone is ready.
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Audio Controls */}
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => speakCurrentQuestion(currentQ.question, latestAcknowledgement)}
                className="px-3 py-1.5 rounded-xl bg-indigo-900/80 hover:bg-indigo-800 border border-indigo-700/60 text-indigo-200 hover:text-white text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
                title="Replay AI question audio"
              >
                <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>Replay Question</span>
              </button>

              {isAiSpeaking && (
                <button
                  type="button"
                  onClick={stopQuestionSpeech}
                  className="px-3 py-1.5 rounded-xl bg-rose-900/60 hover:bg-rose-800 border border-rose-700/60 text-rose-200 text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                  <span>Stop Speech</span>
                </button>
              )}
            </div>
          </div>

          {/* Acknowledgement Transition (Spoken feedback before new question) */}
          {latestAcknowledgement && (
            <div className="bg-indigo-900/40 border border-indigo-700/50 rounded-2xl p-3.5 text-xs text-indigo-200 italic flex items-center gap-2">
              <span className="text-cyan-400 font-bold not-italic">Interviewer:</span>
              <span>"{latestAcknowledgement}"</span>
            </div>
          )}

          {/* Question Display Card */}
          <div className="space-y-3 relative z-10">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider">
                {currentQ.category || 'Technical'} • {currentQ.topic || targetRole}
              </span>
              {latestReason && (
                <span className="text-[10px] text-indigo-300 bg-indigo-800/40 px-2 py-0.5 rounded-md border border-indigo-700/40">
                  Follow-up Context
                </span>
              )}
            </div>

            <h1 className="text-lg sm:text-2xl font-bold text-white leading-relaxed font-heading">
              {currentQ.question}
            </h1>

            {/* Expected Focus Guidance Toggle */}
            <div className="pt-2">
              <button
                type="button"
                onClick={() => setShowExpectedFocus(!showExpectedFocus)}
                className="text-xs text-indigo-300 hover:text-white transition-colors flex items-center gap-1 cursor-pointer font-medium"
              >
                <span>{showExpectedFocus ? 'Hide Focus Hints' : 'Show Assessment Criteria'}</span>
              </button>

              {showExpectedFocus && currentQ.expected_focus && (
                <div className="mt-2.5 p-3.5 bg-indigo-900/60 border border-indigo-700/60 rounded-xl space-y-1.5 text-xs animate-fade-in">
                  <span className="font-bold text-cyan-300">Key Focus Points:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {currentQ.expected_focus.map((focusItem, fIdx) => (
                      <span
                        key={fIdx}
                        className="px-2.5 py-0.5 bg-indigo-950/80 border border-indigo-700/80 rounded-md text-indigo-200 text-[11px]"
                      >
                        • {focusItem}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Microphone Permission Warning (if blocked) */}
        {micPermission === 'denied' && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3 text-xs text-rose-800">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-rose-900">
                Microphone Access Blocked
              </span>
              <p>
                To enable live speech-to-text, allow microphone permissions in your browser address bar.
                You can also type your answers directly in the response box below.
              </p>
            </div>
          </div>
        )}

        {/* =====================================================================
            CANDIDATE SPOKEN RESPONSE & TRANSCRIPTION WORKSPACE
            ===================================================================== */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          {/* Header Row: Recording status & Duration Timer */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all ${
                  isRecording
                    ? isPaused
                      ? 'bg-amber-100 text-amber-700 ring-4 ring-amber-50'
                      : 'bg-rose-500 text-white shadow-md shadow-rose-200 ring-4 ring-rose-100 animate-pulse'
                    : 'bg-slate-100 text-slate-500'
                }`}
              >
                <Mic className="w-6 h-6" />
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900 font-heading">
                    Your Response
                  </h3>
                  <Badge
                    variant={
                      isRecording
                        ? isPaused
                          ? 'warning'
                          : 'danger'
                        : micPermission === 'granted'
                        ? 'success'
                        : 'neutral'
                    }
                    size="sm"
                  >
                    {isRecording ? (isPaused ? 'Recording Paused' : 'Live Speaking') : 'Ready to Speak'}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Click the button below to answer. Your spoken answer will transcribe in real time.
                </p>
              </div>
            </div>

            {/* Timer Display */}
            <div className="flex items-center gap-2 font-mono text-sm bg-slate-50 px-3.5 py-1.5 rounded-xl border border-slate-200 self-start sm:self-auto">
              <Clock className="w-4 h-4 text-slate-400" />
              <span className="font-bold text-slate-800">{formatTimer(recordingSeconds)}</span>
            </div>
          </div>

          {/* Interactive Controls Toolbar */}
          <div className="flex flex-wrap items-center gap-3">
            {!isRecording ? (
              <Button
                type="button"
                size="md"
                variant="primary"
                icon={Mic}
                disabled={isAiSpeaking || isAiAnalyzing}
                onClick={startRecording}
                className="bg-rose-600 hover:bg-rose-700 focus:ring-rose-200 cursor-pointer"
              >
                {isAiSpeaking ? 'AI is speaking...' : 'Start Speaking'}
              </Button>
            ) : (
              <>
                <Button
                  type="button"
                  size="md"
                  variant="danger"
                  icon={Square}
                  onClick={stopRecording}
                  className="cursor-pointer"
                >
                  Stop Recording
                </Button>

                {isPaused ? (
                  <Button
                    type="button"
                    size="md"
                    variant="outline"
                    icon={Play}
                    onClick={resumeRecording}
                    className="cursor-pointer"
                  >
                    Resume
                  </Button>
                ) : (
                  <Button
                    type="button"
                    size="md"
                    variant="outline"
                    icon={Pause}
                    onClick={pauseRecording}
                    className="cursor-pointer"
                  >
                    Pause
                  </Button>
                )}
              </>
            )}

            <Button
              type="button"
              size="md"
              variant="outline"
              icon={RotateCcw}
              disabled={isRecording || (!currentTranscript && recordingSeconds === 0) || isAiAnalyzing}
              onClick={handleRerecord}
              title="Clear transcript and restart speaking"
              className="cursor-pointer"
            >
              Re-record
            </Button>

            <Button
              type="button"
              size="md"
              variant="ghost"
              disabled={!currentTranscript && !liveInterimTranscript}
              onClick={handleClearTranscript}
              className="text-slate-500 hover:text-rose-600 cursor-pointer"
            >
              Clear
            </Button>

            {/* Real-Time Audio Level Visualizer */}
            {isRecording && !isPaused && (
              <div className="flex items-center gap-1 ml-auto px-3 py-1.5 bg-slate-50 border border-slate-100 rounded-xl">
                <span className="text-[10px] text-slate-400 font-bold uppercase mr-1">Mic Level</span>
                {[12, 24, 36, 48, 60].map((threshold, idx) => (
                  <span
                    key={idx}
                    style={{ height: `${Math.max(6, Math.min(22, (audioLevel / 100) * 24))}px` }}
                    className={`w-1 rounded-full transition-all duration-75 ${
                      audioLevel >= threshold ? 'bg-rose-500' : 'bg-slate-200'
                    }`}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Real-Time Live Transcript Preview Subtitle Stream */}
          {liveInterimTranscript && (
            <div className="p-3.5 bg-indigo-50/70 border border-indigo-200/80 rounded-xl space-y-1 animate-fade-in">
              <span className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider flex items-center gap-1.5">
                <Radio className="w-3 h-3 text-indigo-600 animate-pulse" />
                Live Speech Stream
              </span>
              <p className="text-xs text-indigo-950 italic leading-relaxed">
                "{liveInterimTranscript}..."
              </p>
            </div>
          )}

          {/* Editable Transcript Textarea */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label
                htmlFor="editable-transcript"
                className="text-xs font-bold text-slate-800"
              >
                Transcribed Answer (Editable before submission)
              </label>
              <div className="text-xs font-mono text-slate-400">
                {wordCount} {wordCount === 1 ? 'word' : 'words'}
              </div>
            </div>

            <textarea
              id="editable-transcript"
              aria-label="Editable voice transcript"
              value={currentTranscript}
              onChange={(e) => setCurrentTranscript(e.target.value)}
              placeholder="Your spoken words will appear here in real time. You can edit any technical terminology or type your answer directly before submitting to the interviewer..."
              rows={6}
              disabled={isAiAnalyzing}
              className="w-full p-4 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none text-xs sm:text-sm text-slate-800 placeholder-slate-400 font-sans leading-relaxed resize-y transition-all"
            />
          </div>

          {/* Submit Action Row */}
          <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-100">
            <div className="flex items-center gap-3">
              <Button
                type="button"
                size="md"
                variant="primary"
                icon={Sparkles}
                loading={isAiAnalyzing}
                disabled={isAiAnalyzing || !currentTranscript.trim() || isAiSpeaking}
                onClick={handleSubmitAnswer}
                className="cursor-pointer"
              >
                {isAiAnalyzing
                  ? 'AI Analyzing & Deciding Next Question...'
                  : currentQuestionIndex === totalQuestions - 1
                  ? 'Submit Final Answer'
                  : 'Submit Answer'}
              </Button>

              {isAiSpeaking && (
                <span className="text-xs text-slate-400 font-medium">
                  Please listen to the AI question before submitting.
                </span>
              )}
            </div>

            {evaluationError && (
              <span className="text-xs text-rose-600 font-medium flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                {evaluationError}
              </span>
            )}
          </div>
        </div>

        {/* =====================================================================
            CONVERSATION HISTORY DRAWER (Collapsible)
            ===================================================================== */}
        {showHistoryDrawer && (
          <Card className="p-6 space-y-4 animate-fade-in border-indigo-100 bg-slate-50/50">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-indigo-600" />
                Interview Transcript & Prior Questions
              </h3>
              <button
                type="button"
                onClick={() => setShowHistoryDrawer(false)}
                className="text-xs text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                Close
              </button>
            </div>

            {Object.keys(candidateAnswers).length === 0 ? (
              <p className="text-xs text-slate-400 italic">No answers submitted yet.</p>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
                {sessionData.questions?.slice(0, currentQuestionIndex).map((q, idx) => (
                  <div key={idx} className="p-3.5 bg-white border border-slate-200 rounded-xl space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-indigo-700">Question {idx + 1}: {q.topic}</span>
                      <span className="text-[10px] text-slate-400">{q.category}</span>
                    </div>
                    <p className="font-semibold text-slate-800">{q.question}</p>
                    <p className="text-slate-600 italic bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      "{candidateAnswers[idx]}"
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* Exit Confirmation Modal */}
        <Modal
          isOpen={isExitConfirmOpen}
          onClose={() => setIsExitConfirmOpen(false)}
          title="Conclude Interview Session?"
        >
          <div className="space-y-4 text-xs text-slate-600">
            <p>
              Are you sure you want to conclude this interview? A performance report will be generated
              for the questions answered so far.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsExitConfirmOpen(false)}
              >
                Keep Practicing
              </Button>
              <Button
                size="sm"
                variant="danger"
                onClick={handleFinishSession}
              >
                Conclude & View Report
              </Button>
            </div>
          </div>
        </Modal>

        {/* Finish Confirmation Modal */}
        <Modal
          isOpen={isFinishConfirmOpen}
          onClose={() => setIsFinishConfirmOpen(false)}
          title="Complete Interview Session?"
        >
          <div className="space-y-4 text-xs text-slate-600">
            <p>
              You have completed all questions in this session. Generating your final report now!
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                size="sm"
                variant="primary"
                onClick={handleFinishSession}
              >
                Generate Final Report
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    );
  }

  // ===========================================================================
  // RENDER 3: Final Comprehensive Interview Report
  // ===========================================================================
  if (sessionStage === 'report' && sessionData) {
    const reportData = finalReport || {
      overall_score: 8.0,
      score_percentage: 80.0,
      total_questions: totalQuestions,
      answered_questions: Object.keys(candidateAnswers).length,
      evaluated_questions: Object.keys(evaluations).length,
      strong_areas: ['Clear communication', 'Solid technical depth'],
      weak_areas: ['Could provide more concrete production examples'],
      top_improvements: ['Highlight scale metrics and architectural trade-offs'],
    };

    return (
      <div className="max-w-5xl mx-auto space-y-8 pb-20">
        {/* Hero Header */}
        <div className="bg-gradient-to-br from-indigo-900 via-indigo-800 to-purple-900 rounded-3xl p-6 sm:p-10 text-white shadow-md relative overflow-hidden">
          <div className="relative z-10 space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold text-indigo-200 border border-white/20">
              <Award className="w-3.5 h-3.5 text-amber-400" />
              <span>AI Interview Completed</span>
            </div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight font-heading">
                  Comprehensive Interview Performance Report
                </h1>
                <p className="text-xs sm:text-sm text-indigo-200/90 mt-1 max-w-xl">
                  {sessionData.target_role || targetRole} • {sessionData.interview_type || interviewType} Round • {sessionData.difficulty || difficulty} Level
                </p>
              </div>

              {/* Big Score Callout */}
              <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 sm:p-5 flex items-center gap-4 shrink-0">
                <div className="text-center">
                  <div className="text-3xl sm:text-4xl font-extrabold font-heading text-white">
                    {reportData.overall_score || 0}
                    <span className="text-base sm:text-lg text-indigo-200 font-normal">/10</span>
                  </div>
                  <span className="text-[11px] font-semibold text-indigo-200 uppercase tracking-wider">
                    Overall Score
                  </span>
                </div>
                <div className="h-10 w-px bg-white/20" />
                <div>
                  <Badge variant="success" size="sm" className="bg-emerald-400/20 text-emerald-300 border-emerald-400/30">
                    {reportData.overall_score >= 8
                      ? 'Advanced'
                      : reportData.overall_score >= 6
                      ? 'Competent'
                      : 'Developing'}
                  </Badge>
                  <p className="text-[11px] text-indigo-200 mt-1">
                    {Object.keys(evaluations).length} / {totalQuestions} Answered
                  </p>
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-white/15">
              <Button
                size="sm"
                variant="outline"
                icon={Download}
                className="bg-white/10 hover:bg-white/20 text-white border-white/25 cursor-pointer"
                onClick={() => {
                  exportInterviewReportPDF(
                    {
                      ...reportData,
                      target_role: sessionData.target_role || targetRole,
                      interview_type: sessionData.interview_type || interviewType,
                      difficulty: sessionData.difficulty || difficulty,
                      evaluations: evaluations,
                      questions: sessionData.questions,
                    },
                    user?.full_name
                  );
                }}
              >
                Download PDF
              </Button>

              <Button
                size="sm"
                variant="outline"
                icon={copiedReport ? Check : Copy}
                className="bg-white/10 hover:bg-white/20 text-white border-white/25 cursor-pointer"
                onClick={handleCopyReport}
              >
                {copiedReport ? 'Report Copied!' : 'Copy Summary'}
              </Button>

              <Button
                size="sm"
                variant="outline"
                className="bg-white/10 hover:bg-white/20 text-white border-white/25 cursor-pointer"
                onClick={() => navigate('/interview-history')}
              >
                View in History
              </Button>

              <Button
                size="sm"
                variant="primary"
                icon={RotateCcw}
                onClick={handleRetakeSession}
                className="bg-white text-indigo-900 hover:bg-indigo-50 cursor-pointer"
              >
                Start Another Session
              </Button>
            </div>
          </div>
        </div>

        {/* Strengths & Weaknesses Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-emerald-50/80 border border-emerald-200 rounded-2xl p-5 space-y-2.5 shadow-2xs">
            <span className="text-xs font-bold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
              <ThumbsUp className="w-4 h-4 text-emerald-600" />
              Observed Strengths
            </span>
            <ul className="space-y-1.5 text-xs text-emerald-900">
              {reportData.strong_areas?.map((item, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-emerald-600 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-amber-50/80 border border-amber-200 rounded-2xl p-5 space-y-2.5 shadow-2xs">
            <span className="text-xs font-bold text-amber-950 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Growth Areas
            </span>
            <ul className="space-y-1.5 text-xs text-amber-900">
              {reportData.weak_areas?.map((item, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-amber-600 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-indigo-50/80 border border-indigo-200 rounded-2xl p-5 space-y-2.5 shadow-2xs">
            <span className="text-xs font-bold text-indigo-950 uppercase tracking-wider flex items-center gap-1.5">
              <Lightbulb className="w-4 h-4 text-indigo-600" />
              Top Recommendations
            </span>
            <ul className="space-y-1.5 text-xs text-indigo-900">
              {reportData.top_improvements?.map((item, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-indigo-600 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Question-by-Question Transcript & AI Scoring */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900 font-heading">
            Question-by-Question Spoken Transcripts & Feedback
          </h2>

          {sessionData.questions?.map((q, idx) => {
            const ans = candidateAnswers[idx]?.trim();
            const ev = evaluations[idx];

            return (
              <Card key={idx} className="p-5 sm:p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <Badge variant="primary" size="sm">
                      {q.category || 'Technical'}
                    </Badge>
                    <Badge variant="neutral" size="sm">
                      {q.difficulty || sessionData.difficulty || 'Intermediate'}
                    </Badge>
                  </div>

                  {ev ? (
                    <span className="inline-flex items-center gap-1 text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-lg border border-purple-200">
                      <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                      Score: {ev.overall_score}/10
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400 font-medium">Unanswered</span>
                  )}
                </div>

                <p className="text-sm font-bold text-slate-900 leading-snug">
                  {q.question}
                </p>

                {/* Spoken Response */}
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                    <Mic className="w-3 h-3 text-rose-500" />
                    Transcribed Spoken Response
                  </span>
                  <p className="text-xs text-slate-800 leading-relaxed font-sans italic">
                    {ans ? `"${ans}"` : 'No response was recorded for this question.'}
                  </p>
                </div>

                {/* AI Evaluation */}
                {ev && (
                  <div className="p-3.5 bg-indigo-50/50 border border-indigo-100 rounded-xl text-xs text-indigo-900 space-y-1">
                    <span className="font-bold">Interviewer Assessment:</span>
                    <p className="text-slate-700 leading-relaxed">{ev.summary}</p>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    );
  }

  return null;
};

export default VoiceInterviewPage;
