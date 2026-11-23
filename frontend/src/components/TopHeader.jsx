import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, Bell, Search, Video } from 'lucide-react';
import Button from './Button';
import { healthCheck } from '../services/api';
import { useAuth } from '../context/AuthContext';

const TopHeader = ({ onMenuClick }) => {
  const { user } = useAuth();
  const [apiOnline, setApiOnline] = useState(null);

  useEffect(() => {
    let isMounted = true;
    healthCheck()
      .then(() => {
        if (isMounted) setApiOnline(true);
      })
      .catch(() => {
        if (isMounted) setApiOnline(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const displayName = user?.full_name || 'Candidate';
  const initialLetter = displayName.charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
      {/* Left: Mobile hamburger & search */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          type="button"
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="relative w-full hidden sm:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search roles, questions, or topics..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200/80 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* Right: API indicator, notifications, new interview CTA & Avatar */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Backend health status badge */}
        <div
          title={
            apiOnline === true
              ? 'FastAPI Backend is connected (localhost:8000)'
              : apiOnline === false
              ? 'FastAPI Backend offline'
              : 'Checking backend...'
          }
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border bg-slate-50 text-slate-600 border-slate-200"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              apiOnline === true
                ? 'bg-emerald-500 animate-pulse'
                : apiOnline === false
                ? 'bg-amber-400'
                : 'bg-slate-400'
            }`}
          />
          <span>{apiOnline ? 'API Connected' : 'Connecting...'}</span>
        </div>

        {/* Notifications */}
        <button
          type="button"
          className="relative p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-600"></span>
        </button>

        {/* CTA */}
        <Link to="/mock-interview">
          <Button size="sm" variant="primary" icon={Video}>
            <span className="hidden sm:inline">New Interview</span>
            <span className="sm:hidden">Start</span>
          </Button>
        </Link>

        {/* User avatar displaying actual authenticated user */}
        <Link
          to="/profile"
          className="flex items-center gap-2.5 pl-2 border-l border-slate-200 group"
          title={`Signed in as ${displayName}`}
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 text-white flex items-center justify-center text-xs font-bold ring-2 ring-white shadow-xs group-hover:ring-indigo-300 transition-all">
            {initialLetter}
          </div>
          <span className="hidden lg:inline text-xs font-semibold text-slate-700 max-w-[120px] truncate group-hover:text-indigo-600 transition-colors">
            {displayName}
          </span>
        </Link>
      </div>
    </header>
  );
};

export default TopHeader;
