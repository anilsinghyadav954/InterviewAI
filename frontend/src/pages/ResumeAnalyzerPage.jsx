import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  TrendingUp,
  X,
  FileCheck,
  Award,
  History,
  Trash2,
  Eye,
  RefreshCw,
  Clock,
  Layers,
  ChevronRight,
  Lightbulb,
  AlertCircle,
} from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Select from '../components/Select';
import Badge from '../components/Badge';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';
import { supportedRoles } from '../utils/mockData';
import { useAuth } from '../context/AuthContext';
import {
  analyzeResume,
  getResumeHistory,
  getResumeAnalysisById,
  deleteResumeAnalysis,
} from '../services/api';

const ResumeAnalyzerPage = () => {
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState('analyzer'); // 'analyzer' | 'history'
  const [targetRole, setTargetRole] = useState(user?.target_role || 'Full Stack Developer');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState('');
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const roleOptions = supportedRoles.map((r) => r.title);

  // Load history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const data = await getResumeHistory();
      setHistoryList(data);
    } catch (err) {
      console.warn('Failed to fetch resume history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    setErrorMessage('');

    const ext = file.name.toLowerCase();
    if (!ext.endsWith('.pdf') && !ext.endsWith('.txt')) {
      setErrorMessage('Please select a valid PDF (.pdf) or text (.txt) document.');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setErrorMessage('File exceeds the 5MB size limit. Please upload a smaller file.');
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please select or upload a resume file first.');
      return;
    }

    setErrorMessage('');
    setIsAnalyzing(true);
    setAnalysisStep('Reading & extracting text from PDF...');

    const timer1 = setTimeout(() => {
      setAnalysisStep('Evaluating ATS parsability & detecting skill taxonomy...');
    }, 1200);

    const timer2 = setTimeout(() => {
      setAnalysisStep('Querying AI model for role match, strengths & gaps...');
    }, 2500);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('job_role', targetRole);

      const result = await analyzeResume(formData);
      setCurrentAnalysis(result);
      setSuccessMessage('Resume analyzed and report saved to history successfully!');
      setTimeout(() => setSuccessMessage(null), 4000);

      // Refresh history list
      fetchHistory();
    } catch (err) {
      console.error('Analysis error:', err);
      const detail = err.response?.data?.detail;
      setErrorMessage(
        typeof detail === 'string'
          ? detail
          : 'Failed to analyze resume. Please check the document format and try again.'
      );
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setIsAnalyzing(false);
      setAnalysisStep('');
    }
  };

  const handleViewHistoryItem = async (id) => {
    setErrorMessage('');
    try {
      const fullDoc = await getResumeAnalysisById(id);
      setCurrentAnalysis(fullDoc);
      setActiveTab('analyzer');
      window.scrollTo({ top: 400, behavior: 'smooth' });
    } catch (err) {
      console.error('Failed to load analysis record:', err);
      setErrorMessage('Unable to retrieve this report. It may have been deleted.');
    }
  };

  const handleDeleteHistoryItem = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this resume audit from history?')) {
      return;
    }

    try {
      await deleteResumeAnalysis(id);
      setHistoryList((prev) => prev.filter((item) => item.id !== id));
      if (currentAnalysis && currentAnalysis.id === id) {
        setCurrentAnalysis(null);
      }
    } catch (err) {
      console.error('Delete error:', err);
      setErrorMessage('Failed to delete history item.');
    }
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'text-emerald-600 bg-emerald-50 text-emerald-700 border-emerald-200';
    if (score >= 65) return 'text-indigo-600 bg-indigo-50 text-indigo-700 border-indigo-200';
    return 'text-amber-600 bg-amber-50 text-amber-700 border-amber-200';
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="sm">
              Phase 3 AI Intelligence
            </Badge>
            <span className="text-xs text-slate-400">• PDF Parser & LLM Evaluation</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
            AI Resume Analyzer & ATS Auditor
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Extract text from PDF resumes, run deep LLM competency evaluations, benchmark against your target role, and track audit history.
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center p-1 bg-slate-100/80 rounded-xl border border-slate-200 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('analyzer')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all cursor-pointer ${
              activeTab === 'analyzer'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>Analyzer</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all cursor-pointer ${
              activeTab === 'history'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <History className="w-4 h-4 text-slate-500" />
            <span>Audit History</span>
            {historyList.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-[10px]">
                {historyList.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-2xl flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage('')}
            className="text-rose-400 hover:text-rose-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-2xl flex items-center gap-2.5 shadow-xs">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* TAB 1: RESUME ANALYZER UPLOAD & RESULTS */}
      {activeTab === 'analyzer' && (
        <div className="space-y-8">
          {/* Upload Box Card */}
          <Card title="Upload Resume Document" subtitle="Select your target job role and upload your PDF" icon={UploadCloud}>
            <form onSubmit={handleAnalyze} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="Target Role to Benchmark Against"
                  options={roleOptions}
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  required
                />
                <div>
                  <label className="block text-xs font-semibold text-slate-700 tracking-wide mb-1.5">
                    Evaluation Engine
                  </label>
                  <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-700 flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                      <span>Python PDF Extraction + AI LLM Evaluation</span>
                    </span>
                    <Badge variant="primary" size="sm">Active</Badge>
                  </div>
                </div>
              </div>

              {/* Drag & Drop Area */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all group ${
                  isDragging
                    ? 'border-indigo-500 bg-indigo-50/50'
                    : 'border-slate-200 hover:border-indigo-400 bg-slate-50/50 hover:bg-indigo-50/20'
                }`}
              >
                <input
                  type="file"
                  id="resume-upload"
                  accept=".pdf,.txt"
                  onChange={(e) => handleFileSelect(e.target.files?.[0])}
                  className="hidden"
                />
                <label
                  htmlFor="resume-upload"
                  className="cursor-pointer flex flex-col items-center justify-center space-y-3"
                >
                  <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-center text-indigo-600 group-hover:scale-105 transition-transform">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">
                      <span className="text-indigo-600 underline underline-offset-2">Click to choose a file</span> or drag and drop here
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      PDF (.pdf) or Text (.txt) • Maximum allowed size: 5MB
                    </p>
                  </div>
                </label>

                {/* Selected File Chip */}
                {selectedFile && (
                  <div className="mt-4 inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-slate-200 shadow-xs text-xs font-medium text-slate-800">
                    <FileCheck className="w-4 h-4 text-emerald-600" />
                    <span className="font-semibold">{selectedFile.name}</span>
                    <span className="text-slate-400">({formatFileSize(selectedFile.size)})</span>
                    <button
                      type="button"
                      onClick={() => setSelectedFile(null)}
                      className="ml-2 p-0.5 text-slate-400 hover:text-rose-600 transition-colors"
                      title="Remove file"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>

              {/* Action and Loading Status */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
                <div className="text-xs text-slate-500">
                  {isAnalyzing ? (
                    <div className="flex items-center gap-2 text-indigo-600 font-medium">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>{analysisStep}</span>
                    </div>
                  ) : (
                    <span>
                      Results will be stored in your private history and mapped to role competencies.
                    </span>
                  )}
                </div>

                <Button
                  type="submit"
                  size="md"
                  variant="primary"
                  loading={isAnalyzing}
                  disabled={!selectedFile || isAnalyzing}
                  icon={Sparkles}
                >
                  {isAnalyzing ? 'Analyzing Resume...' : 'Analyze Resume'}
                </Button>
              </div>
            </form>
          </Card>

          {/* Analysis Results View */}
          {currentAnalysis && (
            <div className="space-y-6 pt-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="success" size="sm">
                      Audit Complete
                    </Badge>
                    <span className="text-xs text-slate-400">
                      • {formatDate(currentAnalysis.created_at)}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 font-heading">
                    {currentAnalysis.filename}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Benchmarked for:{' '}
                    <strong className="text-indigo-600">{currentAnalysis.job_role}</strong>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    icon={UploadCloud}
                    onClick={() => {
                      setSelectedFile(null);
                      window.scrollTo({ top: 100, behavior: 'smooth' });
                    }}
                  >
                    Upload Another
                  </Button>
                </div>
              </div>

              {/* Candidate Summary if present */}
              {currentAnalysis.extracted_summary && (
                <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100 text-xs text-indigo-900 flex items-start gap-3">
                  <Lightbulb className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block mb-0.5 text-indigo-950">
                      Profile Executive Summary
                    </span>
                    <p className="leading-relaxed text-indigo-900/90">
                      {currentAnalysis.extracted_summary}
                    </p>
                  </div>
                </div>
              )}

              {/* 1. Scorecards Grid: Overall Score, ATS Score, Detected Skills, Missing Skills */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Overall Score */}
                <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs text-center flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      Overall Score
                    </span>
                    <div className="text-4xl font-extrabold text-indigo-600">
                      {currentAnalysis.overall_score}
                      <span className="text-base text-slate-400 font-normal">/100</span>
                    </div>
                  </div>
                  <span
                    className={`inline-block mt-3 text-xs font-semibold px-2.5 py-1 rounded-full border ${getScoreColorClass(
                      currentAnalysis.overall_score
                    )}`}
                  >
                    {currentAnalysis.overall_score >= 80
                      ? 'Competitive'
                      : currentAnalysis.overall_score >= 65
                      ? 'Solid Foundation'
                      : 'Needs Optimization'}
                  </span>
                </div>

                {/* ATS Score */}
                <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs text-center flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      ATS-style Score
                    </span>
                    <div className="text-4xl font-extrabold text-emerald-600">
                      {currentAnalysis.ats_score}
                      <span className="text-base text-slate-400 font-normal">%</span>
                    </div>
                  </div>
                  <span className="inline-block mt-3 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                    {currentAnalysis.ats_score >= 80 ? 'High Parsability' : 'Moderate Parsability'}
                  </span>
                </div>

                {/* Detected Skills */}
                <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs text-center flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      Detected Skills
                    </span>
                    <div className="text-4xl font-extrabold text-blue-600">
                      {currentAnalysis.detected_skills?.length || 0}
                    </div>
                  </div>
                  <span className="inline-block mt-3 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-1 rounded-full">
                    Verified In Document
                  </span>
                </div>

                {/* Missing Skills */}
                <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs text-center flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      Missing Skills
                    </span>
                    <div className="text-4xl font-extrabold text-amber-600">
                      {currentAnalysis.missing_skills?.length || 0}
                    </div>
                  </div>
                  <span className="inline-block mt-3 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
                    Target Role Gaps
                  </span>
                </div>
              </div>

              {/* 2. Job Match Card */}
              {currentAnalysis.job_match && (
                <Card
                  title={`Job Match Alignment: ${currentAnalysis.job_role}`}
                  subtitle="Algorithmic assessment of candidate skills mapped to industry job prerequisites"
                  icon={TrendingUp}
                >
                  <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-bold text-slate-900">
                          {currentAnalysis.job_match.percentage}%
                        </span>
                        <Badge
                          variant={
                            currentAnalysis.job_match.percentage >= 80
                              ? 'success'
                              : currentAnalysis.job_match.percentage >= 65
                              ? 'primary'
                              : 'warning'
                          }
                          size="md"
                        >
                          {currentAnalysis.job_match.match_level}
                        </Badge>
                      </div>
                      <span className="text-xs text-slate-500">
                        Based on core and secondary technical requirements
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200/80">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          currentAnalysis.job_match.percentage >= 80
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-500'
                            : currentAnalysis.job_match.percentage >= 65
                            ? 'bg-gradient-to-r from-indigo-500 to-blue-500'
                            : 'bg-gradient-to-r from-amber-500 to-orange-500'
                        }`}
                        style={{ width: `${currentAnalysis.job_match.percentage}%` }}
                      />
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed pt-1">
                      {currentAnalysis.job_match.summary}
                    </p>
                  </div>
                </Card>
              )}

              {/* 3. Skills Breakdown: Detected vs Missing Skills */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Detected Skills */}
                <Card
                  title="Detected Skills"
                  subtitle={`Found ${currentAnalysis.detected_skills?.length || 0} technical keywords`}
                  icon={CheckCircle2}
                >
                  <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto pr-1">
                    {currentAnalysis.detected_skills?.length > 0 ? (
                      currentAnalysis.detected_skills.map((skill) => (
                        <span
                          key={skill}
                          className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-600 shrink-0" />
                          {skill}
                        </span>
                      ))
                    ) : (
                      <p className="text-xs text-slate-400">No major tech keywords identified.</p>
                    )}
                  </div>
                </Card>

                {/* Missing Skills */}
                <Card
                  title="Missing Skills"
                  subtitle={`Key proficiencies sought for ${currentAnalysis.job_role}`}
                  icon={AlertTriangle}
                >
                  <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto pr-1">
                    {currentAnalysis.missing_skills?.length > 0 ? (
                      currentAnalysis.missing_skills.map((skill) => (
                        <span
                          key={skill}
                          className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200"
                        >
                          <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-amber-600 shrink-0" />
                          {skill}
                        </span>
                      ))
                    ) : (
                      <p className="text-xs text-emerald-600 font-medium">
                        Awesome! All core role skills detected in your resume.
                      </p>
                    )}
                  </div>
                </Card>
              </div>

              {/* 4. Strengths & Weaknesses */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Strengths */}
                <Card
                  title="Resume Strengths"
                  subtitle="High-impact attributes boosting ATS parsability"
                  icon={Award}
                >
                  <ul className="space-y-3 text-xs text-slate-700">
                    {currentAnalysis.strengths?.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{item}</span>
                      </li>
                    ))}
                  </ul>
                </Card>

                {/* Weaknesses */}
                <Card
                  title="Weaknesses & Gaps"
                  subtitle="Issues flagged during automated screening"
                  icon={TrendingUp}
                >
                  <ul className="space-y-3 text-xs text-slate-700">
                    {currentAnalysis.weaknesses?.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5">
                        <span className="w-4 h-4 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                          !
                        </span>
                        <span className="leading-relaxed">{item}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>

              {/* 5. Actionable Recommendations */}
              {currentAnalysis.recommendations && currentAnalysis.recommendations.length > 0 && (
                <Card
                  title="Actionable Recommendations"
                  subtitle="Concrete steps to increase interview callback conversion"
                  icon={Lightbulb}
                >
                  <div className="space-y-3">
                    {currentAnalysis.recommendations.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-3"
                      >
                        <span className="w-6 h-6 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <p className="text-xs text-slate-700 leading-relaxed">{step}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: AUDIT HISTORY */}
      {activeTab === 'history' && (
        <Card
          title="Past Resume Audits"
          subtitle="Review past resume evaluations, track score changes, and reload detailed reports"
          icon={History}
        >
          {isLoadingHistory ? (
            <div className="py-12 flex items-center justify-center">
              <Loading size="md" text="Loading your resume audit history..." />
            </div>
          ) : historyList.length === 0 ? (
            <EmptyState
              title="No Resume Audits Recorded Yet"
              description="Upload your resume document in the Analyzer tab to generate your first ATS assessment and save it here."
              actionLabel="Go to Analyzer"
              onAction={() => setActiveTab('analyzer')}
            />
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-3">Document</th>
                    <th className="py-3 px-3">Target Role</th>
                    <th className="py-3 px-3">Overall Score</th>
                    <th className="py-3 px-3">ATS Score</th>
                    <th className="py-3 px-3">Date</th>
                    <th className="py-3 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {historyList.map((item) => (
                    <tr
                      key={item.id}
                      onClick={() => handleViewHistoryItem(item.id)}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-3">
                        <div className="flex items-center gap-2.5">
                          <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
                          <span className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                            {item.filename}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3 text-slate-700 font-medium">
                        {item.job_role}
                      </td>
                      <td className="py-3.5 px-3">
                        <span className="inline-flex items-center font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
                          {item.overall_score}/100
                        </span>
                      </td>
                      <td className="py-3.5 px-3">
                        <span className="inline-flex items-center font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">
                          {item.ats_score}%
                        </span>
                      </td>
                      <td className="py-3.5 px-3 text-slate-400">
                        {formatDate(item.created_at)}
                      </td>
                      <td className="py-3.5 px-3 text-right">
                        <div className="inline-flex items-center gap-2">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewHistoryItem(item.id);
                            }}
                            className="p-1.5 rounded-lg text-indigo-600 hover:bg-indigo-50 transition-colors"
                            title="View Full Report"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleDeleteHistoryItem(e, item.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                            title="Delete Record"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default ResumeAnalyzerPage;
