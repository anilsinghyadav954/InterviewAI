import React, { useState, useEffect } from 'react';
import {
  Award,
  TrendingUp,
  BarChart3,
  Cpu,
  MessageSquare,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Filter,
  Calendar,
  Briefcase,
  Layers,
  RefreshCw,
  FileText,
  HelpCircle,
  Video,
  Target,
  Sparkles,
  Check,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import Card from '../components/Card';
import StatCard from '../components/StatCard';
import Badge from '../components/Badge';
import Button from '../components/Button';
import {
  getPerformanceOverview,
  getPerformanceTrend,
  getSkillPerformance,
  getCategoryPerformance,
  getRolePerformance,
  getInterviewTypePerformance,
  getPerformanceInsights,
} from '../services/api';

const PerformancePage = () => {
  // Filter states
  const [timeRange, setTimeRange] = useState('all'); // '7d' | '30d' | '90d' | 'all'
  const [interviewType, setInterviewType] = useState('All'); // 'All' | 'Technical' | 'HR' | 'Mixed'
  const [selectedRole, setSelectedRole] = useState('All');

  // Loading & Error states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states
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
  const [skillsData, setSkillsData] = useState([]);
  const [categoriesData, setCategoriesData] = useState([]);
  const [rolesData, setRolesData] = useState([]);
  const [typesData, setTypesData] = useState([]);
  const [insights, setInsights] = useState({
    strengths: [],
    weak_areas: [],
    recommendations: [],
    resume_interview_comparison: null,
  });

  useEffect(() => {
    fetchPerformanceData();
  }, [timeRange, interviewType, selectedRole]);

  const fetchPerformanceData = async () => {
    setIsLoading(true);
    setError(null);

    const params = {};
    if (timeRange && timeRange !== 'all') params.time_range = timeRange;
    if (interviewType && interviewType !== 'All') params.interview_type = interviewType;
    if (selectedRole && selectedRole !== 'All') params.target_role = selectedRole;

    try {
      const [
        ovRes,
        trendRes,
        skillsRes,
        catsRes,
        rolesRes,
        typesRes,
        insightsRes,
      ] = await Promise.allSettled([
        getPerformanceOverview(params),
        getPerformanceTrend(params),
        getSkillPerformance(params),
        getCategoryPerformance(params),
        getRolePerformance({ time_range: params.time_range, interview_type: params.interview_type }),
        getInterviewTypePerformance({ time_range: params.time_range, target_role: params.target_role }),
        getPerformanceInsights(params),
      ]);

      if (ovRes.status === 'fulfilled' && ovRes.value) {
        setOverview(ovRes.value);
      }
      if (trendRes.status === 'fulfilled' && Array.isArray(trendRes.value)) {
        setTrendData(
          trendRes.value.map((item, idx) => ({
            date: item.date || `Int ${idx + 1}`,
            score: item.score_percentage || Math.round(item.score * 10),
            rawScore: item.score,
            role: item.role,
            type: item.interview_type,
          }))
        );
      }
      if (skillsRes.status === 'fulfilled' && Array.isArray(skillsRes.value)) {
        setSkillsData(skillsRes.value);
      }
      if (catsRes.status === 'fulfilled' && Array.isArray(catsRes.value)) {
        setCategoriesData(catsRes.value);
      }
      if (rolesRes.status === 'fulfilled' && Array.isArray(rolesRes.value)) {
        setRolesData(rolesRes.value);
      }
      if (typesRes.status === 'fulfilled' && Array.isArray(typesRes.value)) {
        setTypesData(typesRes.value);
      }
      if (insightsRes.status === 'fulfilled' && insightsRes.value) {
        setInsights(insightsRes.value);
      }
    } catch (err) {
      console.error('Failed to load performance analytics:', err);
      setError('Unable to load some performance metrics. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Distinct roles for filter dropdown (from practicing user roles)
  const availableRoles = ['All', ...Array.from(new Set(rolesData.map((r) => r.role)))];

  // 7 Core Performance Dimension StatCards (Section 2)
  const dimensionCards = [
    {
      label: 'Overall Interview Score',
      value: overview.has_data ? `${overview.average_score_percentage}%` : 'No data',
      change: overview.has_data ? `${overview.average_score} / 10 avg` : 'Complete an interview',
      trend: overview.average_score_percentage >= 70 ? 'up' : 'neutral',
      icon: Award,
      color: 'indigo',
      subtitle: `${overview.interviews_completed} evaluated session${overview.interviews_completed === 1 ? '' : 's'}`,
    },
    {
      label: 'Latest Resume Score',
      value: overview.latest_resume_score > 0 ? `${overview.latest_resume_score}%` : 'Not analyzed',
      change: overview.latest_resume_score > 0 ? 'ATS Compatibility' : 'Upload resume',
      trend: overview.latest_resume_score >= 70 ? 'up' : 'neutral',
      icon: FileText,
      color: 'purple',
      subtitle: 'Evaluated against job target',
    },
    {
      label: 'Technical Accuracy',
      value: overview.has_data && overview.technical_score > 0 ? `${Math.round(overview.technical_score * 10)}%` : 'No data',
      change: overview.technical_score > 0 ? `${overview.technical_score} / 10` : 'Not evaluated',
      trend: overview.technical_score >= 7.0 ? 'up' : 'neutral',
      icon: Cpu,
      color: 'emerald',
      subtitle: 'Factual correctness & depth',
    },
    {
      label: 'Communication',
      value: overview.has_data && overview.communication_score > 0 ? `${Math.round(overview.communication_score * 10)}%` : 'No data',
      change: overview.communication_score > 0 ? `${overview.communication_score} / 10` : 'Not evaluated',
      trend: overview.communication_score >= 7.0 ? 'up' : 'neutral',
      icon: MessageSquare,
      color: 'blue',
      subtitle: 'Structure, pacing & tone',
    },
    {
      label: 'Relevance',
      value: overview.has_data && overview.relevance_score > 0 ? `${Math.round(overview.relevance_score * 10)}%` : 'No data',
      change: overview.relevance_score > 0 ? `${overview.relevance_score} / 10` : 'Not evaluated',
      trend: overview.relevance_score >= 7.0 ? 'up' : 'neutral',
      icon: Target,
      color: 'amber',
      subtitle: 'Direct answer alignment',
    },
    {
      label: 'Completeness',
      value: overview.has_data && overview.completeness_score > 0 ? `${Math.round(overview.completeness_score * 10)}%` : 'No data',
      change: overview.completeness_score > 0 ? `${overview.completeness_score} / 10` : 'Not evaluated',
      trend: overview.completeness_score >= 7.0 ? 'up' : 'neutral',
      icon: CheckCircle2,
      color: 'teal',
      subtitle: 'Coverage of key points',
    },
    {
      label: 'Clarity',
      value: overview.has_data && overview.clarity_score > 0 ? `${Math.round(overview.clarity_score * 10)}%` : 'No data',
      change: overview.clarity_score > 0 ? `${overview.clarity_score} / 10` : 'Not evaluated',
      trend: overview.clarity_score >= 7.0 ? 'up' : 'neutral',
      icon: Sparkles,
      color: 'rose',
      subtitle: 'Articulate phrasing & flow',
    },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Header & Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="sm">
              Phase 6 Analytics
            </Badge>
            <span className="text-xs text-slate-400">• Authenticated Candidate Telemetry</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
            Performance Analytics & Competency Reports
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Real performance telemetry derived from completed mock interview evaluations and resume scans.
          </p>
        </div>

        <Button
          size="sm"
          variant="outline"
          icon={RefreshCw}
          onClick={fetchPerformanceData}
          disabled={isLoading}
        >
          {isLoading ? 'Updating...' : 'Refresh Data'}
        </Button>
      </div>

      {/* Interactive Filters Bar (Section 18) */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <Filter className="w-4 h-4 text-indigo-600" />
          <span>Filters:</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 flex-1 md:max-w-2xl">
          {/* Time Range Filter */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Time Range
            </label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-colors"
            >
              <option value="all">All Time</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>

          {/* Interview Type Filter */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Interview Type
            </label>
            <select
              value={interviewType}
              onChange={(e) => setInterviewType(e.target.value)}
              className="w-full text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-colors"
            >
              <option value="All">All Types</option>
              <option value="Technical">Technical</option>
              <option value="HR">HR / Behavioral</option>
              <option value="Mixed">Mixed</option>
            </select>
          </div>

          {/* Target Role Filter */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Target Role
            </label>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="w-full text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-colors"
            >
              {availableRoles.map((role) => (
                <option key={role} value={role}>
                  {role === 'All' ? 'All Roles' : role}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between">
          <span>{error}</span>
          <Button size="sm" variant="outline" onClick={fetchPerformanceData}>Retry</Button>
        </div>
      )}

      {/* Section 2: 7 Performance Overview Metric Cards */}
      <div>
        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">
          Performance Overview
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {dimensionCards.slice(0, 4).map((metric) => (
            <StatCard
              key={metric.label}
              label={metric.label}
              value={metric.value}
              change={metric.change}
              trend={metric.trend}
              icon={metric.icon}
              color={metric.color}
              subtitle={metric.subtitle}
            />
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
          {dimensionCards.slice(4).map((metric) => (
            <StatCard
              key={metric.label}
              label={metric.label}
              value={metric.value}
              change={metric.change}
              trend={metric.trend}
              icon={metric.icon}
              color={metric.color}
              subtitle={metric.subtitle}
            />
          ))}
        </div>
      </div>

      {/* Section 3: Score Trend (Recharts Line Chart) */}
      <Card
        title="Score Trajectory Over Time"
        subtitle="Chronological performance across evaluated mock interview sessions"
        icon={TrendingUp}
      >
        <div className="h-80 w-full pt-4">
          {isLoading ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              <RefreshCw className="w-5 h-5 animate-spin mr-2 text-indigo-500" />
              Loading score trajectory...
            </div>
          ) : trendData.length >= 2 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={trendData}
                margin={{ top: 10, right: 20, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis
                  dataKey="date"
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
                    backgroundColor: '#0f172a',
                    borderRadius: '12px',
                    border: 'none',
                    color: '#ffffff',
                    fontSize: '12px',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                  }}
                  formatter={(val, name, item) => [
                    `${val}% (${item.payload.rawScore} / 10)`,
                    `${item.payload.role || 'Role'} • ${item.payload.type || 'Type'}`,
                  ]}
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  wrapperStyle={{ paddingBottom: '12px', fontSize: '11px' }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  name="Interview Score (%)"
                  stroke="#4f46e5"
                  strokeWidth={3}
                  dot={{ r: 5, fill: '#4f46e5', stroke: '#ffffff', strokeWidth: 2 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : trendData.length === 1 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50/70 rounded-2xl border border-dashed border-slate-200">
              <div className="w-14 h-14 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xl mb-2">
                {trendData[0].score}%
              </div>
              <h4 className="text-sm font-bold text-slate-800">
                Single Session Recorded: {trendData[0].score}% ({trendData[0].rawScore} / 10)
              </h4>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Completed for {trendData[0].role} ({trendData[0].type}). Complete at least 2 sessions to render the trajectory line chart.
              </p>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50/70 rounded-2xl border border-dashed border-slate-200">
              <Award className="w-10 h-10 text-slate-300 mb-2" />
              <h4 className="text-sm font-bold text-slate-700">No interviews completed yet.</h4>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Score trends will automatically visualize here once you complete and evaluate candidate answers in a mock interview.
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Grid: Section 4 (Skill Performance) + Section 5 (Category Performance) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Section 4: Skill Performance (Horizontal progress bars) (7 cols) */}
        <div className="lg:col-span-7">
          <Card
            title="Skill Competency Breakdown"
            subtitle="Aggregated topic performance from evaluated interview questions"
            icon={BarChart3}
          >
            {isLoading ? (
              <div className="py-12 text-center text-xs text-slate-400">Loading skills...</div>
            ) : skillsData.length > 0 ? (
              <div className="space-y-4 pt-2">
                {skillsData.map((item, idx) => {
                  const pct = item.score_percentage || Math.round(item.score * 10);
                  const isHigh = pct >= 80;
                  const isMid = pct >= 65;

                  return (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-800">{item.skill}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-slate-400">
                            {item.questions_count} question{item.questions_count === 1 ? '' : 's'}
                          </span>
                          <span
                            className={`font-bold font-mono text-xs ${
                              isHigh ? 'text-emerald-600' : isMid ? 'text-indigo-600' : 'text-amber-600'
                            }`}
                          >
                            {pct}%
                          </span>
                        </div>
                      </div>

                      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isHigh ? 'bg-emerald-500' : isMid ? 'bg-indigo-600' : 'bg-amber-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(5, pct))}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-10 text-center text-xs text-slate-400">
                No skill data available for this filter. Complete interviews with evaluated questions to populate skills.
              </div>
            )}
          </Card>
        </div>

        {/* Section 5: Category Performance (5 cols) */}
        <div className="lg:col-span-5">
          <Card
            title="Category Performance"
            subtitle="Domain accuracy across question types"
            icon={Layers}
          >
            {isLoading ? (
              <div className="py-12 text-center text-xs text-slate-400">Loading categories...</div>
            ) : categoriesData.length > 0 ? (
              <div className="space-y-3 pt-2">
                {categoriesData.map((cat, idx) => {
                  const pct = cat.score_percentage || Math.round(cat.score * 10);
                  const isHigh = pct >= 80;

                  return (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl border border-slate-200/90 bg-slate-50/50 flex items-center justify-between"
                    >
                      <div>
                        <h4 className="text-xs font-bold text-slate-900">{cat.category}</h4>
                        <span className="text-[10px] text-slate-400">
                          {cat.questions_count} evaluated question{cat.questions_count === 1 ? '' : 's'}
                        </span>
                      </div>
                      <div className="text-right">
                        <span
                          className={`text-sm font-extrabold ${
                            isHigh ? 'text-emerald-600' : 'text-indigo-600'
                          }`}
                        >
                          {pct}%
                        </span>
                        <span className="text-[10px] text-slate-400 block font-mono">
                          {cat.score} / 10
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-10 text-center text-xs text-slate-400">
                No category data available yet.
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Grid: Section 6 (Interview Type) + Section 7 (Job Role) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Section 6: Interview Type Analytics */}
        <Card
          title="Interview Type Analytics"
          subtitle="Performance across Technical, HR, and Mixed rounds"
          icon={Video}
        >
          {typesData.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              {typesData.map((t, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200/90 bg-white text-center space-y-1 shadow-2xs"
                >
                  <Badge variant={t.type === 'HR' ? 'purple' : 'primary'} size="sm">
                    {t.type}
                  </Badge>
                  <span className="text-xl font-bold text-slate-900 block mt-2">
                    {t.score_percentage}%
                  </span>
                  <span className="text-[10px] text-slate-400 block font-mono">
                    Avg: {t.average_score} / 10
                  </span>
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                    <span>Sessions: <strong>{t.interviews_count}</strong></span>
                    <span>Best: <strong>{t.best_score}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">
              No interview type statistics available yet.
            </div>
          )}
        </Card>

        {/* Section 7: Job Role Analytics */}
        <Card
          title="Job Role Analytics"
          subtitle="Performance segmented by practiced target role"
          icon={Briefcase}
        >
          {rolesData.length > 0 ? (
            <div className="space-y-3 pt-2">
              {rolesData.map((r, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-slate-200/90 bg-white flex items-center justify-between hover:border-indigo-200 transition-colors"
                >
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">{r.role}</h4>
                    <span className="text-[10px] text-slate-400">
                      {r.interviews_count} completed session{r.interviews_count === 1 ? '' : 's'}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-indigo-600">
                      {r.score_percentage}%
                    </span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      Avg: {r.average_score} / 10
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">
              Only roles you have practiced will appear here.
            </div>
          )}
        </Card>
      </div>

      {/* Grid: Section 8 (Strengths), Section 9 (Weak Areas), Section 10 (Recommendations) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Section 8: Strengths */}
        <Card title="Top Strengths" icon={CheckCircle2}>
          {insights.strengths && insights.strengths.length > 0 ? (
            <ul className="space-y-2 text-xs pt-1">
              {insights.strengths.map((str, idx) => (
                <li
                  key={idx}
                  className="p-3 rounded-xl bg-emerald-50/80 border border-emerald-100 text-emerald-900 flex items-start gap-2"
                >
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">{str}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-6 text-center text-xs text-slate-400">
              Complete interview questions to detect your top demonstrated strengths.
            </div>
          )}
        </Card>

        {/* Section 9: Areas for Improvement (Weak Areas) */}
        <Card title="Needs Improvement" icon={AlertTriangle}>
          {insights.weak_areas && insights.weak_areas.length > 0 ? (
            <ul className="space-y-2 text-xs pt-1">
              {insights.weak_areas.map((wk, idx) => (
                <li
                  key={idx}
                  className="p-3 rounded-xl bg-amber-50/80 border border-amber-100 text-amber-900 flex items-start gap-2"
                >
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">{wk}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-6 text-center text-xs text-slate-400">
              No critical weak areas identified for this data range.
            </div>
          )}
        </Card>

        {/* Section 10: Improvement Recommendations */}
        <Card title="Actionable Recommendations" icon={Lightbulb}>
          {insights.recommendations && insights.recommendations.length > 0 ? (
            <ul className="space-y-2 text-xs pt-1">
              {insights.recommendations.map((rec, idx) => (
                <li
                  key={idx}
                  className="p-3 rounded-xl bg-indigo-50/80 border border-indigo-100 text-indigo-900 flex items-start gap-2"
                >
                  <Lightbulb className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-6 text-center text-xs text-slate-400">
              Recommendations will automatically appear once practice sessions are recorded.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default PerformancePage;
