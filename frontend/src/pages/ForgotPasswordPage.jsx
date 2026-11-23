import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Mail, KeyRound, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';
import Button from '../components/Button';
import Input from '../components/Input';
import { forgotPassword } from '../services/api';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [apiError, setApiError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');
    setError('');

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError('Email address is required');
      return;
    }

    if (!/\S+@\S+\.\S+/.test(trimmedEmail)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      const response = await forgotPassword(trimmedEmail.toLowerCase());
      setIsSubmitted(true);
      setSuccessMessage(
        response.message ||
          'If an account exists for this email, a password reset link has been sent.'
      );
    } catch (err) {
      console.error('Forgot password error:', err);
      if (err.response?.status === 429) {
        setApiError('Too many password reset requests. Please wait a minute before trying again.');
      } else {
        const detail = err.response?.data?.detail;
        if (typeof detail === 'string') {
          setApiError(detail);
        } else {
          // Even on unexpected error, keep message generic to prevent enumeration
          setApiError('Unable to process your request at this moment. Please try again later.');
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 bg-white p-8 sm:p-10 rounded-3xl border border-slate-200/90 shadow-xl shadow-slate-100">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-indigo-600 items-center justify-center text-white shadow-md shadow-indigo-100">
            <KeyRound className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 font-heading">
            Forgot Password?
          </h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Enter your registered email address and we'll send you a secure link to reset your password.
          </p>
        </div>

        {/* Success Alert Banner */}
        {isSubmitted && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-2xl space-y-2">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-emerald-900 text-sm">Reset Link Dispatched</p>
                <p className="text-emerald-800 mt-1">{successMessage}</p>
              </div>
            </div>
            <div className="pt-2 border-t border-emerald-200/60 flex items-center gap-1.5 text-[11px] text-emerald-700">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Link expires in 20 minutes for security</span>
            </div>
          </div>
        )}

        {/* API Error Alert */}
        {apiError && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{apiError}</span>
          </div>
        )}

        {/* Form */}
        {!isSubmitted ? (
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Registered Email Address"
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (error) setError('');
              }}
              error={error}
              icon={Mail}
              required
              autoComplete="email"
              autoFocus
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={isLoading}
              disabled={isLoading}
              icon={ArrowRight}
              iconPosition="right"
            >
              {isLoading ? 'Sending reset link...' : 'Send Reset Link'}
            </Button>
          </form>
        ) : (
          <div className="space-y-4">
            <p className="text-xs text-slate-500 text-center">
              Didn't receive an email? Check your spam folder or try again in a few moments.
            </p>
            <Button
              variant="outline"
              size="md"
              fullWidth
              onClick={() => {
                setIsSubmitted(false);
                setEmail('');
                setSuccessMessage('');
              }}
            >
              Try another email address
            </Button>
          </div>
        )}

        {/* Back to Login Link */}
        <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 font-semibold text-indigo-600 hover:text-indigo-700 hover:underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Sign In</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
