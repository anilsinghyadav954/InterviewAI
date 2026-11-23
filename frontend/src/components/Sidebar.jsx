import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Video,
  FileText,
  HelpCircle,
  BarChart3,
  History,
  User,
  Settings,
  LogOut,
  Bot,
  Sparkles,
  ChevronRight,
  X,
  Mic,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const navItems = [
    { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Mock Interview', href: '/mock-interview', icon: Video, badge: 'AI' },
    { name: 'Voice Interview', href: '/voice-interview', icon: Mic, badge: 'Voice' },
    { name: 'Resume Analyzer', href: '/resume-analyzer', icon: FileText },
    { name: 'Practice Questions', href: '/dashboard#practice', icon: HelpCircle },
    { name: 'Performance', href: '/performance', icon: BarChart3 },
    { name: 'Interview History', href: '/interview-history', icon: History },
    { name: 'Profile', href: '/profile', icon: User },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const displayName = user?.full_name || 'Candidate';
  const targetRole = user?.target_role || 'Full Stack Candidate';
  const initialLetter = displayName.charAt(0).toUpperCase();

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`
          fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-slate-200/80 flex flex-col justify-between transition-transform duration-200 ease-in-out
          lg:translate-x-0 lg:static lg:z-auto
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Top: Logo & Close on mobile */}
        <div>
          <div className="h-16 px-6 border-b border-slate-100 flex items-center justify-between">
            <NavLink to="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
                <Bot className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold tracking-tight text-slate-900 font-heading">
                  Interview<span className="text-indigo-600">AI</span>
                </span>
                <span className="text-[10px] text-slate-400 font-medium -mt-1">
                  Candidate Portal
                </span>
              </div>
            </NavLink>
            <button
              type="button"
              onClick={onClose}
              className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5 overflow-y-auto max-h-[calc(100vh-14rem)]">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={onClose}
                  className={({ isActive }) => `
                    flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group
                    ${
                      isActive
                        ? 'bg-indigo-50/80 text-indigo-700 shadow-xs'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }
                  `}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-4 h-4 transition-colors`}
                    />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-indigo-100 text-indigo-700">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Bottom User Card & Real Authenticated Logout */}
        <div className="p-4 border-t border-slate-100">
          <NavLink
            to="/profile"
            className="p-3 rounded-xl bg-slate-50 hover:bg-indigo-50/40 border border-slate-100 flex items-center gap-3 mb-2 transition-colors group block"
            title="View candidate profile"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-100 border border-indigo-200 text-indigo-700 flex items-center justify-center font-bold text-sm shrink-0">
              {initialLetter}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-900 truncate group-hover:text-indigo-600 transition-colors">
                {displayName}
              </p>
              <p className="text-[11px] text-slate-500 truncate">
                {targetRole}
              </p>
            </div>
          </NavLink>

          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3.5 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-700 transition-colors cursor-pointer group"
          >
            <LogOut className="w-4 h-4 text-slate-400 group-hover:text-rose-600 transition-colors" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
