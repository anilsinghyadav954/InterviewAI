import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, Mail, Globe, Share2, MessageSquare } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-white border-t border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand Info */}
          <div className="md:col-span-1 space-y-4">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <Bot className="w-4 h-4" />
              </div>
              <span className="text-lg font-bold tracking-tight text-slate-900 font-heading">
                Interview<span className="text-indigo-600">AI</span>
              </span>
            </Link>
            <p className="text-sm text-slate-500 leading-relaxed">
              AI-powered interview preparation for the next generation of professionals.
            </p>
            <div className="flex items-center gap-3 pt-2 text-slate-400">
              <a
                href="#globe"
                onClick={(e) => e.preventDefault()}
                aria-label="Website"
                className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center hover:text-slate-900 hover:border-slate-300 transition-colors"
              >
                <Globe className="w-4 h-4" />
              </a>
              <a
                href="#community"
                onClick={(e) => e.preventDefault()}
                aria-label="Community"
                className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center hover:text-indigo-600 hover:border-indigo-300 transition-colors"
              >
                <MessageSquare className="w-4 h-4" />
              </a>
              <a
                href="#share"
                onClick={(e) => e.preventDefault()}
                aria-label="Share"
                className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center hover:text-sky-600 hover:border-sky-300 transition-colors"
              >
                <Share2 className="w-4 h-4" />
              </a>
              <a
                href="#contact"
                onClick={(e) => e.preventDefault()}
                aria-label="Email"
                className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center hover:text-indigo-600 hover:border-indigo-300 transition-colors"
              >
                <Mail className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 mb-4">
              Product
            </h4>
            <ul className="space-y-2.5 text-sm text-slate-600">
              <li>
                <a href="/#features" className="hover:text-indigo-600 transition-colors">
                  Features
                </a>
              </li>
              <li>
                <Link to="/mock-interview" className="hover:text-indigo-600 transition-colors">
                  Mock Interview
                </Link>
              </li>
              <li>
                <Link to="/resume-analyzer" className="hover:text-indigo-600 transition-colors">
                  Resume Analyzer
                </Link>
              </li>
              <li>
                <Link to="/performance" className="hover:text-indigo-600 transition-colors">
                  Performance
                </Link>
              </li>
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 mb-4">
              Company
            </h4>
            <ul className="space-y-2.5 text-sm text-slate-600">
              <li>
                <a href="#about" onClick={(e) => e.preventDefault()} className="hover:text-indigo-600 transition-colors">
                  About
                </a>
              </li>
              <li>
                <a href="#contact" onClick={(e) => e.preventDefault()} className="hover:text-indigo-600 transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 mb-4">
              Legal
            </h4>
            <ul className="space-y-2.5 text-sm text-slate-600">
              <li>
                <a href="#privacy" onClick={(e) => e.preventDefault()} className="hover:text-indigo-600 transition-colors">
                  Privacy
                </a>
              </li>
              <li>
                <a href="#terms" onClick={(e) => e.preventDefault()} className="hover:text-indigo-600 transition-colors">
                  Terms
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} InterviewAI Inc. All rights reserved. Phase 1 Prototype.</p>
          <div className="flex items-center gap-6">
            <span className="inline-flex items-center gap-1.5 text-emerald-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              FastAPI Backend Connected
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
