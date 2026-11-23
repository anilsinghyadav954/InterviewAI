import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History,
  Search,
  Filter,
  Calendar,
  CheckCircle2,
  Clock,
  Video,
  Eye,
  ArrowRight,
  Sparkles,
  Sliders,
  Layers,
  Play,
  Award,
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
import { mockRecentInterviews } from '../utils/mockData';
import {
  getQuestionHistory,
  getQuestionSet,
  getInterviewFinalReport,
  getVoiceHistory,
  getVoiceReport,
} from '../services/api';
import { exportInterviewReportPDF } from '../utils/pdfExport';

const InterviewHistoryPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [selectedReport, setSelectedReport] = useState(null);
  const [viewTab, setViewTab] = useState('question-sets'); // 'question-sets' | 'voice-sessions' | 'session-reports'

  // Real question sets from Phase 4 & Phase 5
  const [questionSets, setQuestionSets] = useState([]);
  const [isLoadingSets, setIsLoadingSets] = useState(false);
  const [selectedQuestionSet, setSelectedQuestionSet] = useState(null);
  const [isLoadingSetDetails, setIsLoadingSetDetails] = useState(false);

  // Phase 7 Voice Sessions state
  const [voiceSessions, setVoiceSessions] = useState([]);
  const [isLoadingVoice, setIsLoadingVoice] = useState(false);

  // Real Final Report Modal state
  const [loadedReport, setLoadedReport] = useState(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [reportError, setReportError] = useState(null);

  // Extended mock history items for Phase 1 session reports
  const historyItems = [
    ...mockRecentInterviews,
    {
      id: 'int-05',
      role: 'Backend Developer',
      type: 'Technical',
      difficulty: 'Intermediate',
      score: 82,
      date: 'Sep 08, 2026',
      status: 'Completed',
      questionsCount: 10,
      duration: '30 mins',
      summary: 'Solid reasoning regarding relational schema design, connection pooling, and JWT authorization flow.',
    },
    {
      id: 'int-06',
      role: 'Full Stack Developer',
      type: 'Mixed',
      difficulty: 'Beginner',
      score: 95,
      date: 'Aug 29, 2026',
      status: 'Completed',
      questionsCount: 5,
      duration: '15 mins',
      summary: 'Flawless communication of HTML semantics, CSS flexbox/grid mechanics, and REST principles.',
    },
  ];

  useEffect(() => {
    loadSets();
    loadVoiceSessions();
  }, []);

  const loadSets = async () => {
    setIsLoadingSets(true);
    try {
      const data = await getQuestionHistory();
      setQuestionSets(data);
    } catch (err) {
      console.warn('Failed to fetch question sets in history:', err);
    } finally {
      setIsLoadingSets(false);
    }
  };

  const loadVoiceSessions = async () => {
    setIsLoadingVoice(true);
    try {
      const data = await getVoiceHistory();
      setVoiceSessions(data || []);
    } catch (err) {
      console.warn('Failed to fetch voice interview history:', err);
    } finally {
      setIsLoadingVoice(false);
    }
  };

  const handleOpenQuestionSet = async (setId) => {
    setIsLoadingSetDetails(true);
    try {
      const fullSet = await getQuestionSet(setId);
      setSelectedQuestionSet(fullSet);
    } catch (err) {
      console.error('Failed to load question set details:', err);
    } finally {
      setIsLoadingSetDetails(false);
    }
  };

  const handleOpenFinalReport = async (setId) => {
    setIsLoadingReport(true);
    setReportError(null);
    try {
      const rep = await getInterviewFinalReport(setId);
      setLoadedReport(rep);
    } catch (err) {
      console.error('Failed to load final interview report:', err);
      setReportError(err.response?.data?.detail || 'Failed to load evaluation report.');
    } finally {
      setIsLoadingReport(false);
    }
  };

  const handleOpenVoiceReport = async (sessionId) => {
    setIsLoadingReport(true);
    setReportError(null);
    try {
      const rep = await getVoiceReport(sessionId);
      setLoadedReport(rep);
    } catch (err) {
      console.error('Failed to load voice interview report:', err);
      setReportError(err.response?.data?.detail || 'Failed to load voice evaluation report.');
    } finally {
      setIsLoadingReport(false);
    }
  };

  const filteredReports = historyItems.filter((item) => {
    const matchesSearch =
      item.role.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType =
      selectedType === 'All' || item.type.toLowerCase() === selectedType.toLowerCase();
    return matchesSearch && matchesType;
  });

  const filteredVoiceSessions = voiceSessions.filter((item) => {
    const matchesSearch =
      (item.role || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.interview_type || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType =
      selectedType === 'All' || (item.interview_type || '').toLowerCase() === selectedType.toLowerCase();
    return matchesSearch && matchesType;
  });

  const filteredSets = questionSets.filter((item) => {
    const matchesSearch =
      item.target_role.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.interview_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType =
      selectedType === 'All' || item.interview_type.toLowerCase() === selectedType.toLowerCase();
    return matchesSearch && matchesType;
  });

  const getDifficultyBadge = (diff) => {
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

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="sm">
              Session Archives & Question Sets
            </Badge>
            <span className="text-xs text-slate-400">• Phase 5 AI Evaluated</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
            Interview History & Evaluation Reports
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Review past generated AI question sets, evaluated sessions, and comprehensive candidate scoring reports.
          </p>
        </div>

        <Button
          size="sm"
          variant="primary"
          icon={Video}
          onClick={() => navigate('/mock-interview')}
        >
          New Question Set
        </Button>
      </div>

      {/* Tabs & Search Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* View Switch */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setViewTab('question-sets')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              viewTab === 'question-sets'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Question Sets & Evaluations</span>
            {questionSets.length > 0 && (
              <span className="px-1.5 py-0.2 bg-indigo-100 text-indigo-700 text-[10px] rounded-full font-bold">
                {questionSets.length}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setViewTab('voice-sessions')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              viewTab === 'voice-sessions'
                ? 'bg-white text-rose-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Mic className="w-3.5 h-3.5 text-rose-600" />
            <span>Voice Interviews</span>
            {voiceSessions.length > 0 && (
              <span className="px-1.5 py-0.2 bg-rose-100 text-rose-700 text-[10px] rounded-full font-bold">
                {voiceSessions.length}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setViewTab('session-reports')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              viewTab === 'session-reports'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Prototype Sessions</span>
          </button>
        </div>

        {/* Type Filter */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          {['All', 'Technical', 'HR', 'Mixed'].map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setSelectedType(type)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                selectedType === type
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input Bar */}
      <div className="relative w-full sm:w-80">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Filter by job role or category..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 shadow-2xs"
        />
      </div>

      {/* Tab 1: AI Question Sets & Evaluated Sessions Table */}
      {viewTab === 'question-sets' && (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <th className="px-5 py-4">Role</th>
                  <th className="px-5 py-4">Type</th>
                  <th className="px-5 py-4">Difficulty</th>
                  <th className="px-5 py-4">Score</th>
                  <th className="px-5 py-4">Completion</th>
                  <th className="px-5 py-4">Date</th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {isLoadingSets ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                      Loading question sets...
                    </td>
                  </tr>
                ) : filteredSets.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                      No question sets found. Use Mock Interview to generate your first AI question set!
                    </td>
                  </tr>
                ) : (
                  filteredSets.map((item) => {
                    const hasEvaluations = (item.evaluated_questions || 0) > 0 || item.overall_score !== null;
                    return (
                      <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-5 py-4 font-bold text-slate-900">{item.target_role}</td>
                        <td className="px-5 py-4">
                          <Badge variant={item.interview_type === 'HR' ? 'purple' : 'primary'} size="sm">
                            {item.interview_type}
                          </Badge>
                        </td>
                        <td className="px-5 py-4 font-medium text-slate-600">
                          <Badge variant={getDifficultyBadge(item.difficulty)} size="sm">
                            {item.difficulty}
                          </Badge>
                        </td>
                        <td className="px-5 py-4">
                          {item.overall_score !== null && item.overall_score !== undefined ? (
                            <span className="font-extrabold text-sm text-purple-700 bg-purple-50 px-2.5 py-1 rounded-lg border border-purple-200">
                              {item.overall_score} / 10
                            </span>
                          ) : (
                            <span className="text-slate-400 italic text-[11px]">Not evaluated</span>
                          )}
                        </td>
                        <td className="px-5 py-4 font-semibold text-slate-700">
                          {item.completion_rate !== undefined ? (
                            <span className="flex items-center gap-1.5">
                              <span>{item.completion_rate}%</span>
                              <span className="text-slate-400 font-normal text-[11px]">
                                ({item.evaluated_questions || 0}/{item.number_of_questions})
                              </span>
                            </span>
                          ) : (
                            `${item.number_of_questions} Qs`
                          )}
                        </td>
                        <td className="px-5 py-4 text-slate-500">
                          {new Date(item.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </td>
                        <td className="px-5 py-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {hasEvaluations && (
                              <Button
                                size="sm"
                                variant="outline"
                                icon={Award}
                                onClick={() => handleOpenFinalReport(item.id)}
                              >
                                View Report
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              icon={Eye}
                              onClick={() => handleOpenQuestionSet(item.id)}
                            >
                              Set
                            </Button>
                            <Button
                              size="sm"
                              variant="primary"
                              icon={Play}
                              onClick={async () => {
                                try {
                                  const fullSet = await getQuestionSet(item.id);
                                  navigate('/mock-interview', { state: { questionSet: fullSet, autoStart: true } });
                                } catch (e) {
                                  console.error('Failed to load question set:', e);
                                }
                              }}
                            >
                              Practice
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 2: Voice Interview Sessions Table (Phase 7) */}
      {viewTab === 'voice-sessions' && (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <th className="px-5 py-4">Job Role</th>
                  <th className="px-5 py-4">Mode</th>
                  <th className="px-5 py-4">Type</th>
                  <th className="px-5 py-4">Difficulty</th>
                  <th className="px-5 py-4">Score</th>
                  <th className="px-5 py-4">Status</th>
                  <th className="px-5 py-4">Date</th>
                  <th className="px-5 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {isLoadingVoice ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center text-slate-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-rose-500" />
                      Loading voice interview sessions...
                    </td>
                  </tr>
                ) : filteredVoiceSessions.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center text-slate-400">
                      <Mic className="w-6 h-6 mx-auto mb-2 text-slate-300" />
                      No voice interview sessions recorded yet.{' '}
                      <button
                        type="button"
                        onClick={() => navigate('/voice-interview')}
                        className="text-rose-600 font-semibold hover:underline"
                      >
                        Start your first voice round →
                      </button>
                    </td>
                  </tr>
                ) : (
                  filteredVoiceSessions.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-5 py-4 font-semibold text-slate-900">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                            <Mic className="w-3.5 h-3.5" />
                          </div>
                          <span>{item.role}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <Badge variant="danger" size="sm" className="bg-rose-50 text-rose-700 border-rose-200">
                          Voice
                        </Badge>
                      </td>
                      <td className="px-5 py-4">
                        <Badge
                          variant={item.interview_type === 'HR' ? 'purple' : 'primary'}
                          size="sm"
                        >
                          {item.interview_type}
                        </Badge>
                      </td>
                      <td className="px-5 py-4">
                        <Badge variant={getDifficultyBadge(item.difficulty)} size="sm">
                          {item.difficulty}
                        </Badge>
                      </td>
                      <td className="px-5 py-4">
                        {item.score !== null && item.score !== undefined ? (
                          <span
                            className={`font-bold text-sm ${
                              item.score >= 8
                                ? 'text-emerald-600'
                                : item.score >= 6
                                ? 'text-indigo-600'
                                : 'text-amber-600'
                            }`}
                          >
                            {item.score} <span className="text-[11px] font-normal text-slate-400">/ 10</span>
                          </span>
                        ) : (
                          <span className="text-slate-400 font-normal italic">In Progress</span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <Badge
                          variant={item.status === 'completed' ? 'success' : 'warning'}
                          size="sm"
                        >
                          {item.status === 'completed' ? 'Completed' : 'Active'}
                        </Badge>
                      </td>
                      <td className="px-5 py-4 text-slate-500">
                        {new Date(item.date).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            size="sm"
                            variant="outline"
                            icon={Award}
                            onClick={() => handleOpenVoiceReport(item.session_id || item.id)}
                          >
                            View Report
                          </Button>
                          {item.status === 'active' && (
                            <Button
                              size="sm"
                              variant="primary"
                              icon={Play}
                              onClick={() => navigate('/voice-interview')}
                              className="bg-rose-600 hover:bg-rose-700"
                            >
                              Resume
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 3: Mock Session Reports Table */}
      {viewTab === 'session-reports' && (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-4">Job Role</th>
                  <th className="px-6 py-4">Interview Type</th>
                  <th className="px-6 py-4">Difficulty</th>
                  <th className="px-6 py-4">Score</th>
                  <th className="px-6 py-4">Date</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {filteredReports.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">{item.role}</td>
                    <td className="px-6 py-4">
                      <Badge variant={item.type === 'HR' ? 'purple' : 'primary'} size="sm">
                        {item.type}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-medium">{item.difficulty}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`font-bold text-sm ${
                          item.score >= 90
                            ? 'text-emerald-600'
                            : item.score >= 80
                            ? 'text-indigo-600'
                            : 'text-amber-600'
                        }`}
                      >
                        {item.score}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500">{item.date}</td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        icon={Eye}
                        onClick={() => setSelectedReport(item)}
                      >
                        View Report
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* AI Question Set Details Modal */}
      {selectedQuestionSet && (
        <Modal
          isOpen={!!selectedQuestionSet}
          onClose={() => setSelectedQuestionSet(null)}
          title={`Generated Question Set – ${selectedQuestionSet.target_role}`}
          subtitle={`${selectedQuestionSet.interview_type} • ${selectedQuestionSet.difficulty} • ${selectedQuestionSet.questions?.length} Questions`}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100 flex-wrap">
              <Badge variant="primary" size="sm">
                {selectedQuestionSet.target_role}
              </Badge>
              <Badge variant={selectedQuestionSet.interview_type === 'HR' ? 'purple' : 'primary'} size="sm">
                {selectedQuestionSet.interview_type}
              </Badge>
              <Badge variant={getDifficultyBadge(selectedQuestionSet.difficulty)} size="sm">
                {selectedQuestionSet.difficulty}
              </Badge>
              <Badge variant={selectedQuestionSet.resume_based ? 'success' : 'neutral'} size="sm">
                {selectedQuestionSet.resume_based ? 'Personalized with Resume' : 'Standard Bank'}
              </Badge>
            </div>

            <div className="space-y-3">
              {selectedQuestionSet.questions?.map((q, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200/90 bg-white hover:border-indigo-300 transition-all space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-indigo-700 font-mono">
                      Q{String(q.question_number || idx + 1).padStart(2, '0')}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded font-semibold text-[10px]">
                        {q.category}
                      </span>
                      <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded font-semibold text-[10px]">
                        {q.topic}
                      </span>
                    </div>
                  </div>
                  <p className="font-semibold text-slate-900 leading-relaxed">
                    {q.question}
                  </p>
                  {q.expected_focus && q.expected_focus.length > 0 && (
                    <div className="pt-2 border-t border-slate-100">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                        Expected Focus:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {q.expected_focus.map((item, fIdx) => (
                          <span
                            key={fIdx}
                            className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-slate-600 text-[11px]"
                          >
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <Button size="sm" variant="outline" onClick={() => setSelectedQuestionSet(null)}>
                Close
              </Button>
              <Button
                size="sm"
                variant="primary"
                icon={Play}
                onClick={() => {
                  const set = selectedQuestionSet;
                  setSelectedQuestionSet(null);
                  navigate('/mock-interview', { state: { questionSet: set, autoStart: true } });
                }}
              >
                Practice This Question Set
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Session Evaluation Report Modal */}
      {selectedReport && (
        <Modal
          isOpen={!!selectedReport}
          onClose={() => setSelectedReport(null)}
          title={`Evaluation Report – ${selectedReport.role}`}
          subtitle={`Session ID: ${selectedReport.id} • ${selectedReport.date}`}
          maxWidth="max-w-xl"
        >
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200 text-center">
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">
                  Final Score
                </span>
                <span className="text-3xl font-extrabold text-indigo-600">
                  {selectedReport.score}%
                </span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">
                  Type
                </span>
                <span className="text-sm font-bold text-slate-800 mt-1 block">
                  {selectedReport.type}
                </span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">
                  Questions
                </span>
                <span className="text-sm font-bold text-slate-800 mt-1 block">
                  {selectedReport.questionsCount} ({selectedReport.duration})
                </span>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 mb-2">
                Evaluator Feedback Summary
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed bg-white p-4 rounded-xl border border-slate-200/80">
                {selectedReport.summary}
              </p>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-slate-400">
                Phase 1 Prototype Session
              </span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => setSelectedReport(null)}>
                  Close
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => {
                    setSelectedReport(null);
                    navigate('/mock-interview');
                  }}
                >
                  Practice Questions
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Real Phase 5 Final Interview Evaluation Report Modal */}
      {loadedReport && (
        <Modal
          isOpen={!!loadedReport}
          onClose={() => setLoadedReport(null)}
          title={`Final Evaluation Report – ${loadedReport.target_role}`}
          subtitle={`${loadedReport.interview_type} • ${loadedReport.difficulty} • ${loadedReport.evaluated_questions}/${loadedReport.total_questions} Questions Evaluated`}
          maxWidth="max-w-3xl"
        >
          <div className="space-y-6 max-h-[75vh] overflow-y-auto pr-1">
            {/* Score & Completion Header */}
            <div className="bg-gradient-to-r from-indigo-900 to-purple-900 text-white p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
              <div className="flex items-center gap-3.5">
                <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-md text-white flex flex-col items-center justify-center font-bold border border-white/20">
                  <span className="text-2xl font-black">{loadedReport.overall_score}</span>
                  <span className="text-[10px] text-purple-200">/ 10</span>
                </div>
                <div>
                  <span className="text-xs uppercase font-bold text-indigo-200 tracking-wider block">
                    Overall Interview Score
                  </span>
                  <span className="text-2xl font-bold">{loadedReport.score_percentage}%</span>
                  <span className="text-xs text-emerald-300 block mt-0.5 font-medium">
                    {loadedReport.overall_score >= 8 ? 'Interview Ready' : loadedReport.overall_score >= 6 ? 'Competent' : 'Needs Development'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs bg-white/10 p-3 rounded-xl border border-white/10">
                <div>
                  <span className="text-purple-200 block text-[10px] uppercase">Completion</span>
                  <span className="font-bold text-sm">{loadedReport.completion_rate}%</span>
                </div>
                <div>
                  <span className="text-purple-200 block text-[10px] uppercase">Evaluated</span>
                  <span className="font-bold text-sm">{loadedReport.evaluated_questions} / {loadedReport.total_questions}</span>
                </div>
              </div>
            </div>

            {/* Sub-Dimension Averages */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
              {loadedReport.average_technical_accuracy !== null && loadedReport.average_technical_accuracy !== undefined && (
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Tech Accuracy</span>
                  <span className="text-base font-extrabold text-slate-800 mt-0.5 block">{loadedReport.average_technical_accuracy} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
                </div>
              )}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">Relevance</span>
                <span className="text-base font-extrabold text-slate-800 mt-0.5 block">{loadedReport.average_relevance} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">Completeness</span>
                <span className="text-base font-extrabold text-slate-800 mt-0.5 block">{loadedReport.average_completeness} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">Clarity</span>
                <span className="text-base font-extrabold text-slate-800 mt-0.5 block">{loadedReport.average_clarity} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">Communication</span>
                <span className="text-base font-extrabold text-slate-800 mt-0.5 block">{loadedReport.average_communication} <span className="text-xs font-normal text-slate-400">/ 10</span></span>
              </div>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {loadedReport.strong_areas?.length > 0 && (
                <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
                  <span className="text-[11px] font-bold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                    <ThumbsUp className="w-4 h-4 text-emerald-600" />
                    Strong Areas
                  </span>
                  <ul className="space-y-1.5">
                    {loadedReport.strong_areas.map((str, sIdx) => (
                      <li key={sIdx} className="text-emerald-900 flex items-start gap-2">
                        <span className="text-emerald-600 font-bold">•</span>
                        <span className="leading-snug">{str}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {loadedReport.weak_areas?.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 space-y-2">
                  <span className="text-[11px] font-bold text-amber-950 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Areas to Strengthen
                  </span>
                  <ul className="space-y-1.5">
                    {loadedReport.weak_areas.map((wk, wIdx) => (
                      <li key={wIdx} className="text-amber-900 flex items-start gap-2">
                        <span className="text-amber-600 font-bold">•</span>
                        <span className="leading-snug">{wk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Top Improvements */}
            {loadedReport.top_improvements?.length > 0 && (
              <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200 text-xs space-y-2">
                <span className="text-[11px] font-bold text-indigo-950 uppercase tracking-wider flex items-center gap-1.5">
                  <Lightbulb className="w-4 h-4 text-indigo-600" />
                  Key Recommendations
                </span>
                <ul className="space-y-1.5">
                  {loadedReport.top_improvements.map((sug, sgIdx) => (
                    <li key={sgIdx} className="text-indigo-900 flex items-start gap-2">
                      <span className="text-indigo-600 font-bold">•</span>
                      <span>{sug}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Per-Question Evaluations List */}
            {loadedReport.evaluations?.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Evaluated Answers Breakdown ({loadedReport.evaluations.length})
                </h4>
                <div className="space-y-3">
                  {loadedReport.evaluations.map((ev, eIdx) => (
                    <div key={eIdx} className="p-4 rounded-xl border border-slate-200 bg-white space-y-2.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-indigo-700 font-mono">
                          Question #{ev.question_number}
                        </span>
                        <Badge variant={ev.overall_score >= 8 ? 'success' : ev.overall_score >= 6 ? 'primary' : 'warning'} size="sm">
                          Score: {ev.overall_score} / 10
                        </Badge>
                      </div>

                      <div className="p-2.5 bg-slate-50 rounded-lg text-slate-800">
                        <span className="text-[10px] font-bold text-slate-400 block mb-1 uppercase">Candidate Answer:</span>
                        <p className="whitespace-pre-wrap">{ev.candidate_answer}</p>
                      </div>

                      <div className="p-2.5 bg-purple-50/50 rounded-lg text-purple-900 border border-purple-100">
                        <span className="text-[10px] font-bold text-purple-800 block mb-0.5 uppercase">AI Feedback:</span>
                        <p>{ev.summary}</p>
                      </div>

                      {ev.model_answer_outline && (
                        <div className="p-2.5 bg-slate-50 rounded-lg text-slate-700 border border-slate-100 font-mono text-[11px]">
                          <span className="text-[10px] font-bold text-slate-400 block mb-0.5 font-sans uppercase">Suggested Outline:</span>
                          <p>{ev.model_answer_outline}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Footer */}
            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 flex-wrap">
              <Button size="sm" variant="outline" onClick={() => setLoadedReport(null)}>
                Close
              </Button>
              <Button
                size="sm"
                variant="outline"
                icon={Download}
                onClick={() => {
                  exportInterviewReportPDF(loadedReport, user?.full_name);
                }}
              >
                Download PDF Report
              </Button>
              <Button
                size="sm"
                variant="primary"
                icon={Play}
                onClick={async () => {
                  const qSetId = loadedReport.question_set_id;
                  setLoadedReport(null);
                  try {
                    const fullSet = await getQuestionSet(qSetId);
                    navigate('/mock-interview', { state: { questionSet: fullSet, autoStart: true } });
                  } catch (e) {
                    console.error('Failed to load question set:', e);
                  }
                }}
              >
                Practice This Set Again
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default InterviewHistoryPage;
