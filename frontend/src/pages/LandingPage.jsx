import React from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Video,
  Sparkles,
  BarChart3,
  Briefcase,
  Compass,
  ArrowRight,
  CheckCircle2,
  Star,
  Users,
  Code2,
  Terminal,
  Cpu,
  Layers,
  Database,
  Brain,
  ShieldCheck,
  ChevronRight,
  Play,
  Mic,
} from 'lucide-react';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';
import { supportedRoles } from '../utils/mockData';

const LandingPage = () => {
  const features = [
    {
      icon: FileText,
      title: 'AI Resume Analysis',
      description: 'Analyze your resume and identify strengths, weaknesses and skill gaps.',
      color: 'indigo',
    },
    {
      icon: Video,
      title: 'AI Mock Interviews',
      description: 'Practice realistic technical and HR interviews with timed question banks.',
      color: 'blue',
    },
    {
      icon: Mic,
      title: 'Voice Interviews & STT',
      description: 'Speak your answers naturally using live browser Speech-to-Text with instant AI scoring.',
      color: 'purple',
    },
    {
      icon: Sparkles,
      title: 'Smart AI Feedback',
      description: 'Receive multi-dimensional scoring and model answer outlines on your answers.',
      color: 'amber',
    },
    {
      icon: BarChart3,
      title: 'Performance Tracking',
      description: 'Track your chronological scores and identify weak areas across roles.',
      color: 'emerald',
    },
    {
      icon: Compass,
      title: 'Personalized Roadmap',
      description: 'Get actionable recommendations aligned with your target job role.',
      color: 'rose',
    },
  ];

  const steps = [
    {
      number: '01',
      title: 'Upload Resume',
      description: 'Submit your resume in PDF format to detect skills, ATS readiness, and domain gaps.',
    },
    {
      number: '02',
      title: 'Choose Job Role',
      description: 'Select your target job title, seniority level, and interview focus (Technical or HR).',
    },
    {
      number: '03',
      title: 'Take AI Interview',
      description: 'Answer contextual questions generated specifically for your background and chosen role.',
    },
    {
      number: '04',
      title: 'Improve With AI Feedback',
      description: 'Receive scoring on clarity, technical accuracy, and tailored action plans to get hired.',
    },
  ];

  const roleIcons = {
    'software-dev': Code2,
    'frontend-dev': Layers,
    'backend-dev': Database,
    'fullstack-dev': Terminal,
    'python-dev': Terminal,
    'java-dev': Cpu,
    'data-analyst': BarChart3,
    'aiml-engineer': Brain,
  };

  return (
    <div className="space-y-24 lg:space-y-32 pb-16">
      {/* Hero Section */}
      <section className="relative pt-12 lg:pt-20 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-200/80 text-indigo-700 text-xs font-semibold shadow-2xs">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Next-Gen AI Interview Preparation</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight font-heading leading-[1.15]">
              Prepare Smarter. <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-600">
                Interview Better.
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-slate-600 font-normal leading-relaxed max-w-2xl mx-auto">
              Practice realistic interviews, analyze your resume, and get personalized
              AI-powered feedback to improve your chances of getting hired.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <Link to="/mock-interview" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  variant="primary"
                  icon={ArrowRight}
                  iconPosition="right"
                  className="w-full sm:w-auto shadow-md shadow-indigo-100"
                >
                  Start Mock Interview
                </Button>
              </Link>
              <Link to="/resume-analyzer" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  variant="outline"
                  icon={FileText}
                  className="w-full sm:w-auto"
                >
                  Analyze My Resume
                </Button>
              </Link>
            </div>

            {/* Social proof pills */}
            <div className="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 font-medium">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ATS Resume Parsing
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                Adaptive Technical Questions
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                Actionable Feedback Metrics
              </span>
            </div>
          </div>

          {/* Hero Visual: SaaS Dashboard Mockup using rich UI components */}
          <div className="mt-12 sm:mt-16 max-w-5xl mx-auto">
            <div className="relative rounded-2xl sm:rounded-3xl p-2 sm:p-4 bg-gradient-to-b from-slate-200/80 via-slate-100/50 to-white border border-slate-200/80 shadow-2xl shadow-slate-200">
              <div className="bg-white rounded-xl sm:rounded-2xl border border-slate-200/90 overflow-hidden shadow-xs">
                {/* Mock Window Top Bar */}
                <div className="bg-slate-50 px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-400"></span>
                    <span className="w-3 h-3 rounded-full bg-amber-400"></span>
                    <span className="w-3 h-3 rounded-full bg-emerald-400"></span>
                    <span className="ml-2 text-xs font-mono text-slate-400 hidden sm:inline">
                      interviewai.app/live-session
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                      AI Interrogator Active
                    </span>
                  </div>
                </div>

                {/* Mock Content Interface */}
                <div className="p-4 sm:p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 bg-slate-50/40">
                  {/* Left: Active Mock Question Simulation */}
                  <div className="lg:col-span-7 space-y-4">
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                      <div className="flex items-center justify-between mb-3">
                        <Badge variant="primary" size="sm">
                          Question 3 of 10 • Technical
                        </Badge>
                        <span className="text-xs text-slate-400 font-mono">03:42 elapsed</span>
                      </div>
                      <h4 className="text-sm sm:text-base font-semibold text-slate-900 leading-snug">
                        "Can you explain the difference between optimistic concurrency control and pessimistic locking in distributed transactions?"
                      </h4>
                      <div className="mt-4 p-3.5 bg-slate-50 rounded-lg border border-slate-100">
                        <p className="text-xs text-slate-500 font-mono leading-relaxed">
                          Candidate answer submitted. AI evaluates: Technical Depth (92%), Communication Structure (88%), Edge Case Consideration (84%).
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 bg-white rounded-xl border border-slate-200 text-center">
                        <span className="text-xs text-slate-500 block">Overall Score</span>
                        <span className="text-xl font-bold text-indigo-600">89%</span>
                      </div>
                      <div className="p-3 bg-white rounded-xl border border-slate-200 text-center">
                        <span className="text-xs text-slate-500 block">ATS Score</span>
                        <span className="text-xl font-bold text-emerald-600">94%</span>
                      </div>
                      <div className="p-3 bg-white rounded-xl border border-slate-200 text-center">
                        <span className="text-xs text-slate-500 block">Confidence</span>
                        <span className="text-xl font-bold text-blue-600">High</span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Real-time Feedback & Skills Radar */}
                  <div className="lg:col-span-5 space-y-4">
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                          AI Instant Evaluation
                        </span>
                        <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                          Top 10%
                        </span>
                      </div>

                      <div className="space-y-2.5 pt-1">
                        <div>
                          <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                            <span>System Architecture</span>
                            <span>92%</span>
                          </div>
                          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                            <div className="bg-indigo-600 h-full rounded-full w-[92%]"></div>
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                            <span>Clarity & STAR Method</span>
                            <span>86%</span>
                          </div>
                          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                            <div className="bg-emerald-500 h-full rounded-full w-[86%]"></div>
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                            <span>Problem Solving Speed</span>
                            <span>88%</span>
                          </div>
                          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                            <div className="bg-blue-500 h-full rounded-full w-[88%]"></div>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                        <span className="text-xs text-slate-500">Target Role:</span>
                        <span className="text-xs font-semibold text-slate-800">
                          Full Stack Developer
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="primary" size="sm" className="mb-3">
            Comprehensive Capabilities
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight font-heading">
            Everything You Need to Prepare for Your Next Interview
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-600">
            A cohesive suite of intelligent preparation tools engineered to turn nervous candidates into confident top performers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-8 hover:shadow-lg hover:border-slate-300 transition-all duration-200 group"
              >
                <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">
                  {idx + 1}. {feature.title}
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="bg-slate-900 py-20 text-white rounded-3xl mx-4 sm:mx-6 lg:mx-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 bg-indigo-950/70 border border-indigo-800 px-3 py-1 rounded-full">
              Seamless Process
            </span>
            <h2 className="mt-4 text-3xl sm:text-4xl font-bold tracking-tight font-heading text-white">
              How It Works
            </h2>
            <p className="mt-3 text-slate-400 text-sm sm:text-base">
              Four straightforward steps to systematically elevate your interview readiness.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            {steps.map((step) => (
              <div
                key={step.number}
                className="relative bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 hover:border-indigo-500/50 transition-colors"
              >
                <div className="text-3xl font-extrabold text-indigo-400 font-mono mb-4">
                  {step.number}
                </div>
                <h3 className="text-base font-semibold text-white mb-2">
                  {step.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Target Roles Section */}
      <section id="roles" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="purple" size="sm" className="mb-3">
            Role-Based Tracks
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight font-heading">
            Targeted Role Tracks
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-600">
            Tailored question banks and rubrics designed by senior hiring managers across key tech domains.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {supportedRoles.map((role) => {
            const Icon = roleIcons[role.id] || Code2;
            return (
              <div
                key={role.id}
                className="bg-white border border-slate-200/90 rounded-2xl p-6 hover:shadow-md hover:border-indigo-200 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 flex items-center justify-center mb-4 group-hover:bg-indigo-50 group-hover:text-indigo-600 group-hover:border-indigo-100 transition-colors">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-2">
                    {role.title}
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed mb-4">
                    {role.description}
                  </p>
                </div>
                <div>
                  <div className="flex flex-wrap gap-1.5 pt-3 border-t border-slate-100">
                    {role.popularSkills.map((sk) => (
                      <span
                        key={sk}
                        className="text-[11px] font-medium bg-slate-50 text-slate-600 border border-slate-200/60 px-2 py-0.5 rounded-md"
                      >
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative rounded-3xl bg-gradient-to-r from-indigo-700 via-indigo-600 to-purple-700 p-8 sm:p-14 text-white text-center shadow-xl overflow-hidden">
          {/* Subtle background glow */}
          <div className="absolute -top-24 -right-24 w-72 h-72 bg-white/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />

          <div className="relative max-w-2xl mx-auto space-y-6">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight font-heading text-white">
              Your Next Interview Starts Here.
            </h2>
            <p className="text-base sm:text-lg text-indigo-100 font-normal leading-relaxed">
              Build confidence, practice smarter, and become interview-ready.
            </p>
            <div className="pt-2">
              <Link to="/register">
                <Button
                  size="lg"
                  className="bg-white text-indigo-700 hover:bg-slate-100 focus:ring-white border-0 shadow-lg font-semibold"
                  icon={ArrowRight}
                  iconPosition="right"
                >
                  Start Preparing
                </Button>
              </Link>
            </div>
            <p className="text-xs text-indigo-200/80">
              No credit card required • Instant access to Phase 1 mock experience
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
