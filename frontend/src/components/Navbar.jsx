import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bot, Menu, X, ArrowRight, Sparkles } from 'lucide-react';
import Button from './Button';

const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { name: 'Home', href: '/' },
    { name: 'Features', href: '/#features' },
    { name: 'How It Works', href: '/#how-it-works' },
    { name: 'Roles', href: '/#roles' },
    { name: 'Login', href: '/login' },
  ];

  const handleScroll = (href) => {
    setMobileMenuOpen(false);
    if (href.startsWith('/#')) {
      const id = href.replace('/#', '');
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 bg-white/90 backdrop-blur-md transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white shadow-sm shadow-indigo-200 group-hover:scale-105 transition-transform">
              <Bot className="w-5 h-5" />
            </div>
            <div className="flex items-center">
              <span className="text-xl font-bold tracking-tight text-slate-900 font-heading">
                Interview<span className="text-indigo-600">AI</span>
              </span>
              <span className="ml-2 text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100 px-1.5 py-0.5 rounded-full uppercase tracking-wider">
                AI Powered
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((item) => (
              <a
                key={item.name}
                href={item.href}
                onClick={(e) => {
                  if (item.href.startsWith('/#') && location.pathname === '/') {
                    e.preventDefault();
                    handleScroll(item.href);
                  }
                }}
                className={`text-sm font-medium transition-colors ${location.pathname === item.href
                    ? 'text-indigo-600 font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                  }`}
              >
                {item.name}
              </a>
            ))}
          </nav>

          {/* Primary CTA and Login */}
          <div className="hidden md:flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/mock-interview">
              <Button
                variant="primary"
                size="sm"
                icon={ArrowRight}
                iconPosition="right"
              >
                Start Interview
              </Button>
            </Link>
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex md:hidden items-center">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-6 space-y-3 shadow-lg">
          <div className="flex flex-col space-y-1">
            {navLinks.map((item) => (
              <a
                key={item.name}
                href={item.href}
                onClick={(e) => {
                  if (item.href.startsWith('/#') && location.pathname === '/') {
                    e.preventDefault();
                    handleScroll(item.href);
                  } else {
                    setMobileMenuOpen(false);
                  }
                }}
                className="px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 hover:text-indigo-600"
              >
                {item.name}
              </a>
            ))}
          </div>
          <div className="pt-3 border-t border-slate-100 flex flex-col gap-2">
            <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="outline" size="md" fullWidth>
                Sign In
              </Button>
            </Link>
            <Link to="/mock-interview" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="primary" size="md" fullWidth icon={ArrowRight} iconPosition="right">
                Start Interview
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
