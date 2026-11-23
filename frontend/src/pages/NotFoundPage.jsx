import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft, Home, HelpCircle } from 'lucide-react';
import Button from '../components/Button';

const NotFoundPage = () => {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mx-auto shadow-sm">
          <Bot className="w-8 h-8" />
        </div>

        <div>
          <span className="text-5xl font-extrabold text-indigo-600 font-mono tracking-tight">
            404
          </span>
          <h1 className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
            Page Not Found
          </h1>
          <p className="mt-3 text-sm text-slate-500 leading-relaxed">
            The page you are looking for doesn't exist or has been moved. Check the URL or navigate back to the home dashboard.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link to="/">
            <Button size="md" variant="primary" icon={Home}>
              Back to Home
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button size="md" variant="outline">
              Go to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
