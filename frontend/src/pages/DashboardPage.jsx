import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Video,
  FileText,
  HelpCircle,
  TrendingUp,
  ArrowRight,
  Sparkles,
  Calendar,
  Clock,
  CheckCircle2,
  ChevronRight,
  Award,
  Layers,
  BarChart3,
  RefreshCw,
  Lightbulb,
  AlertCircle,
  FileCheck,
  Mic,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import StatCard from '../components/StatCard';
import Card from '../components/Card';
import Button from '../components/Button';
import Badge from '../components/Badge';
import { useAuth } from '../context/AuthContext';
import {
  getPerformanceOverview,
  getPerformanceTrend,
  getPerformanceInsights,
  getRecentActivity,
} from '../services/api';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [overview, setOverview] = useState({
    interviews_completed: 0,
    average_score: 0.0,
    average_score_percentage: 0.0,
    best_score: 0.0,
    best_score_percentage: 0.0,
    questions_evaluated: 0,
    latest_resume_score: 0.0,
    total_practice_sessions: 0,
    technical_score: 0.0,
    communication_score: 0.0,
    relevance_score: 0.0,
    completeness_score: 0.0,
    clarity_score: 0.0,
    has_data: false,
  });

  const [trendData, setTrendData] = useState([]);
  const [insights, setInsights] = useState({
    strengths: [],
    weak_areas: [],
    recommendations: [],
    resume_interview_comparison: null,
  });
  const [recentActivities, setRecentActivities] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [ovRes, trendRes, insightsRes, actRes] = await Promise.allSettled([
        getPerformanceOverview(),
        getPerformanceTrend(),
        getPerformanceInsights(),
        getRecentActivity(6),
      ]);

      if (ovRes.status === 'fulfilled' && ovRes.value) {
        setOverview(ovRes.value);
      }
      if (trendRes.status === 'fulfilled' && Array.isArray(trendRes.value)) {
        // Map trend data for Recharts
        const formattedTrend = trendRes.value.map((pt, idx) => ({
          name: pt.date || `Session ${idx + 1}`,
          score: pt.score_percentage || Math.round(pt.score * 10),
          rawScore: pt.score,
          role: pt.role,
          type: pt.interview_type,
        }));
        setTrendData(formattedTrend);
      }
      if (insightsRes.status === 'fulfilled' && insightsRes.value) {
        setInsights(insightsRes.value);
      }
      if (actRes.status === 'fulfilled' && Array.isArray(actRes.value)) {
        setRecentActivities(actRes.value);
      }
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
      setError('Unable to load some dashboard metrics. Please refresh.');
    } finally {
      setIsLoading(false);
    }
  };

  const displayName = user?.full_name || 'Candidate';
  const targetRole = user?.target_role || 'Software Engineer';

  // 6 Real Dashboard Statistics
  const statCardsData = [
    {
      id: 'interviews_completed',
      label: 'Interviews Completed',
      value: overview.interviews_completed > 0 ? String(overview.interviews_completed) : 'No interviews yet',
      change: overview.interviews_completed > 0
        ? `${overview.interviews_completed} finished mock sessions`
        : 'Complete a mock interview to track stats',
      trend: overview.interviews_completed > 0 ? 'up' : 'neutral',
      icon: Video,
      color: 'indigo',
    },
    {
      id: 'average_score',
      label: 'Average Interview Score',
      value: overview.interviews_completed > 0 ? `${overview.average_score} / 10` : 'No score yet',
      change: overview.interviews_completed > 0
        ? `${overview.average_score_percentage}% aggregate performance`
        : 'No interviews completed yet.',
      trend: overview.average_score_percentage >= 70 ? 'up' : 'neutral',
      icon: Award,
      color: 'emerald',
    },
    {
      id: 'questions_evaluated',
      label: 'Questions Evaluated',
      value: overview.questions_evaluated > 0 ? String(overview.questions_evaluated) : '0 questions',
      change: overview.questions_evaluated > 0
        ? `${overview.questions_evaluated} answers scored with AI feedback`
        : 'Answers are evaluated instantly by AI',
      trend: overview.questions_evaluated > 0 ? 'up' : 'neutral',
      icon: HelpCircle,
      color: 'blue',
    },
    {
      id: 'latest_resume_score',
      label: 'Latest Resume Score',
      value: overview.latest_resume_score > 0 ? `${overview.latest_resume_score}%` : 'Not analyzed',
      change: overview.latest_resume_score > 0
        ? 'Latest ATS analysis score'
        : 'Upload resume to scan ATS compatibility',
      trend: overview.latest_resume_score >= 70 ? 'up' : 'neutral',
      icon: FileText,
      color: 'purple',
    },
    {
      id: 'best_score',
      label: 'Best Interview Score',
      value: overview.interviews_completed > 0 ? `${overview.best_score} / 10` : 'No score yet',
      change: overview.interviews_completed > 0
        ? `${overview.best_score_percentage}% personal best`
        : 'Your highest scoring session appears here',
      trend: overview.best_score_percentage >= 80 ? 'up' : 'neutral',
      icon: Sparkles,
      color: 'amber',
    },
    {
      id: 'total_practice_sessions',
      label: 'Total Practice Sessions',
      value: overview.total_practice_sessions > 0 ? String(overview.total_practice_sessions) : '0 sessions',
      change: overview.total_practice_sessions > 0
        ? `${overview.total_practice_sessions} question banks generated`
        : 'Generate custom AI question banks',
      trend: overview.total_practice_sessions > 0 ? 'up' : 'neutral',
      icon: Layers,
      color: 'rose',
    },
  ];

  const comparison = insights.resume_interview_comparison;

  return (
    <div className="space-y-8">
      {/* Top Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-heading">
              Welcome back, {displayName}! 👋
            </h1>
            <Badge variant="primary" size="sm">
              Phase 6 Analytics
            </Badge>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Targeting <strong className="text-slate-800">{targetRole}</strong>. Real performance data calculated directly from your practice sessions.
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Link to="/mock-interview">
            <Button size="sm" variant="primary" icon={Video}>
              Mock Interview
            </Button>
          </Link>
          <Link to="/voice-interview">
            <Button size="sm" variant="outline" icon={Mic} className="border-rose-200 text-rose-700 hover:bg-rose-50">
              Voice Interview
            </Button>
          </Link>
          <Link to="/resume-analyzer">
            <Button size="sm" variant="outline" icon={FileText}>
              Analyze Resume
            </Button>
          </Link>
          <Button
            size="sm"
            variant="ghost"
            icon={RefreshCw}
            onClick={loadDashboardData}
            title="Refresh Dashboard"
          />
        </div>
      </div>

      {/* Error alert if any */}
      {error && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center justify-between text-xs">
          <span>{error}</span>
          <Button size="sm" variant="outline" onClick={loadDashboardData}>Retry</Button>
        </div>
      )}

      {/* 6 Real Dashboard Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {statCardsData.map((stat) => (
          <StatCard
            key={stat.id}
            label={stat.label}
            value={stat.value}
            change={stat.change}
            trend={stat.trend}
            icon={stat.icon}
            color={stat.color}
          />
        ))}
      </div>

      {/* Main Grid: Score Trend Chart + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Score Trend Chart (8 cols) */}
        <div className="lg:col-span-8">
          <Card
            title="Interview Performance Trend"
            subtitle="Chronological scoring progression across evaluated sessions"
            icon={TrendingUp}
            headerAction={
              <Link to="/performance">
                <Button size="sm" variant="ghost" icon={ArrowRight} iconPosition="right">
                  Detailed Analytics
                </Button>
              </Link>
            }
          >
            <div className="h-72 w-full pt-4">
              {isLoading ? (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">
                  <RefreshCw className="w-5 h-5 animate-spin mr-2 text-indigo-500" />
                  Loading score trajectory...
                </div>
              ) : trendData.length >= 2 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={trendData}
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.28} />
                        <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey="name"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fill: '#64748b', fontSize: 11 }}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tickLine={false}
                      axisLine={false}
                      tick={{ fill: '#64748b', fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        borderRadius: '12px',
                        border: 'none',
                        color: '#ffffff',
                        fontSize: '12px',
                        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                      }}
                      formatter={(val, name, item) => [
                        `${val}% (${item.payload.rawScore} / 10)`,
                        `${item.payload.role || 'Interview'} (${item.payload.type || ''})`,
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="score"
                      name="Score"
                      stroke="#4f46e5"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#scoreGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : trendData.length === 1 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50/70 rounded-2xl border border-dashed border-slate-200">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-lg mb-2">
                    {trendData[0].score}%
                  </div>
                  <h4 className="text-sm font-bold text-slate-800">
                    First Interview Evaluated: {trendData[0].score}% ({trendData[0].rawScore}/10)
                  </h4>
                  <p className="text-xs text-slate-500 max-w-sm mt-1">
                    Complete at least 2 completed interview sessions to view score trajectory trends over time.
                  </p>
                  <Link to="/mock-interview" className="mt-3">
                    <Button size="sm" variant="primary" icon={Video}>
                      Start Next Interview
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50/70 rounded-2xl border border-dashed border-slate-200">
                  <Award className="w-10 h-10 text-slate-300 mb-2" />
                  <h4 className="text-sm font-bold text-slate-700">No interviews completed yet.</h4>
                  <p className="text-xs text-slate-500 max-w-sm mt-1">
                    Launch a mock interview session to evaluate candidate answers and track your score over time.
                  </p>
                  <Link to="/mock-interview" className="mt-3">
                    <Button size="sm" variant="primary" icon={Video}>
                      Start First Mock Interview
                    </Button>
                  </Link>
                </div>
              )}
            </div>

            {trendData.length >= 2 && (
              <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5 font-medium text-slate-700">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                    Live Sessions Evaluated: {trendData.length}
                  </span>
                  <span className="text-slate-400">•</span>
                  <span>Range: {overview.average_score_percentage}% average</span>
                </div>
                <span className="text-[11px] text-indigo-700 font-semibold bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">
                  Real Evaluated Data
                </span>
              </div>
            )}
          </Card>
        </div>

        {/* Quick Actions & Resume-Interview Alignment (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Resume vs Interview Comparison Card */}
          <Card
            title="Resume vs Interview Alignment"
            subtitle="Comparative analysis of ATS score & interview performance"
            icon={BarChart3}
          >
            {comparison ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="p-3 bg-purple-50/80 border border-purple-100 rounded-xl">
                    <span className="text-[11px] font-semibold text-purple-700 uppercase tracking-wider block">
                      Resume Score
                    </span>
                    <span className="text-2xl font-bold text-purple-900 mt-1 block">
                      {comparison.resume_score}%
                    </span>
                  </div>
                  <div className="p-3 bg-indigo-50/80 border border-indigo-100 rounded-xl">
                    <span className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider block">
                      Interview Average
                    </span>
                    <span className="text-2xl font-bold text-indigo-900 mt-1 block">
                      {comparison.interview_score}%
                    </span>
                  </div>
                </div>

                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/90 text-xs text-slate-700 leading-relaxed">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                    <span>{comparison.insight}</span>
                  </div>
                </div>
              </div>
            ) : overview.latest_resume_score > 0 ? (
              <div className="p-4 bg-slate-50 rounded-xl text-xs text-slate-600 space-y-2 border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800">Resume ATS Score:</span>
                  <Badge variant="purple" size="sm">{overview.latest_resume_score}%</Badge>
                </div>
                <p className="text-[11px] text-slate-500">
                  Complete at least one mock interview to unlock comparative insights between your resume and live interview performance.
                </p>
                <Link to="/mock-interview" className="block pt-1">
                  <Button size="sm" variant="primary" fullWidth icon={Video}>
                    Start Interview
                  </Button>
                </Link>
              </div>
            ) : overview.interviews_completed > 0 ? (
              <div className="p-4 bg-slate-50 rounded-xl text-xs text-slate-600 space-y-2 border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800">Interview Average:</span>
                  <Badge variant="primary" size="sm">{overview.average_score_percentage}%</Badge>
                </div>
                <p className="text-[11px] text-slate-500">
                  Upload and analyze your resume to compare how well your interview scores align with your ATS match.
                </p>
                <Link to="/resume-analyzer" className="block pt-1">
                  <Button size="sm" variant="outline" fullWidth icon={FileText}>
                    Analyze Resume
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="p-4 bg-slate-50 rounded-xl text-xs text-slate-500 text-center space-y-2 border border-dashed border-slate-200">
                <p>Analyze your resume and complete a mock interview session to unlock comparative alignment insights.</p>
                <div className="flex justify-center gap-2 pt-1">
                  <Link to="/resume-analyzer">
                    <Button size="sm" variant="outline">Upload Resume</Button>
                  </Link>
                  <Link to="/mock-interview">
                    <Button size="sm" variant="primary">Start Session</Button>
                  </Link>
                </div>
              </div>
            )}
          </Card>

          {/* Quick Actions Card */}
          <Card title="Quick Actions" subtitle="Jump straight into prep modes" icon={Sparkles}>
            <div className="space-y-2.5">
              <Link to="/mock-interview" className="block">
                <div className="p-3 rounded-xl border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/40 transition-all flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                      <Video className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-slate-900 group-hover:text-indigo-600">
                        Start Mock Interview
                      </h4>
                      <p className="text-[11px] text-slate-500">Technical, HR, or Mixed session</p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600" />
                </div>
              </Link>

              <Link to="/resume-analyzer" className="block">
                <div className="p-3 rounded-xl border border-slate-200 hover:border-emerald-400 hover:bg-emerald-50/40 transition-all flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-slate-900 group-hover:text-emerald-600">
                        Analyze Resume
                      </h4>
                      <p className="text-[11px] text-slate-500">Scan skills & ATS score</p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600" />
                </div>
              </Link>

              <Link to="/performance" className="block">
                <div className="p-3 rounded-xl border border-slate-200 hover:border-blue-400 hover:bg-blue-50/40 transition-all flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
                      <BarChart3 className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-slate-900 group-hover:text-blue-600">
                        Full Performance Analytics
                      </h4>
                      <p className="text-[11px] text-slate-500">Skills, strengths, and filters</p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600" />
                </div>
              </Link>
            </div>
          </Card>
        </div>
      </div>

      {/* Real Recent Activities Feed */}
      <div>
        <Card
          title="Recent Activity"
          subtitle="Real actions logged from your interview sessions and resume reviews"
          icon={Calendar}
          headerAction={
            <Link to="/interview-history">
              <Button size="sm" variant="ghost" icon={ArrowRight} iconPosition="right">
                View All History
              </Button>
            </Link>
          }
        >
          {recentActivities.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {recentActivities.map((act) => {
                const isInterview = act.activity_type === 'interview_completed';
                const isResume = act.activity_type === 'resume_analyzed';
                const isQSet = act.activity_type === 'question_set_generated';

                const IconComponent = isInterview ? Video : isResume ? FileText : HelpCircle;
                const iconColor = isInterview
                  ? 'bg-indigo-100 text-indigo-700'
                  : isResume
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-emerald-100 text-emerald-700';

                const formattedDate = act.date
                  ? new Date(act.date).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })
                  : 'Recently';

                return (
                  <div
                    key={act.id}
                    className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 px-3 rounded-xl transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-9 h-9 rounded-xl ${iconColor} flex items-center justify-center shrink-0`}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-xs font-bold text-slate-900">{act.title}</h4>
                          <span className="text-[10px] text-slate-400">• {formattedDate}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">{act.description}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-end sm:self-center">
                      {act.score !== null && act.score !== undefined && (
                        <Badge
                          variant={act.score >= 80 || (act.score <= 10 && act.score >= 8) ? 'success' : act.score >= 60 || (act.score <= 10 && act.score >= 6) ? 'primary' : 'warning'}
                          size="sm"
                        >
                          {act.score <= 10 ? `${act.score} / 10` : `${act.score}%`}
                        </Badge>
                      )}
                      {isInterview && (
                        <Link to="/interview-history">
                          <Button size="xs" variant="ghost">Report</Button>
                        </Link>
                      )}
                      {isResume && (
                        <Link to="/resume-analyzer">
                          <Button size="xs" variant="ghost">View</Button>
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-12 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
              <Calendar className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-700">No recent activity recorded yet.</p>
              <p className="text-[11px] text-slate-400 mt-0.5 max-w-sm mx-auto">
                Generate question banks, complete mock interviews, or analyze your resume to populate your activity feed.
              </p>
              <div className="flex justify-center gap-2 mt-4">
                <Link to="/mock-interview">
                  <Button size="sm" variant="primary" icon={Video}>
                    Start Interview
                  </Button>
                </Link>
                <Link to="/resume-analyzer">
                  <Button size="sm" variant="outline" icon={FileText}>
                    Analyze Resume
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
