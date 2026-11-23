import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import {
  Lock,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Check,
  X,
  KeyRound,
  ArrowLeft,
} from 'lucide-react';
import Button from '../components/Button';
import Input from '../components/Input';
import { resetPassword } from '../services/api';

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Password criteria verification
  const hasMinLength = newPassword.length >= 8;
  const hasUppercase = /[A-Z]/.test(newPassword);
  const hasLowercase = /[a-z]/.test(newPassword);
  const hasNumber = /\d/.test(newPassword);
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const isPasswordValid = hasMinLength && hasUppercase && hasLowercase && hasNumber;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');
    const newErrors = {};

    if (!token) {
      setApiError('Missing password reset token. Please request a new reset link.');
      return;
    }

    if (!newPassword) {
      newErrors.newPassword = 'New password is required';
    } else if (!isPasswordValid) {
      newErrors.newPassword = 'Password does not meet the security requirements';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Confirmation password is required';
    } else if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setIsLoading(true);

    try {
      await resetPassword(token, newPassword);
      setIsSuccess(true);
    } catch (err) {
      console.error('Password reset error:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setApiError(detail);
      } else if (Array.isArray(detail) && detail.length > 0) {
        setApiError(detail[0]?.msg || 'Validation failed. Please check your password.');
      } else {
        setApiError('Unable to reset password. The link may have expired or is invalid.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // If token is completely absent from URL
  if (!token && !isSuccess) {
    return (
      <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-6 bg-white p-8 sm:p-10 rounded-3xl border border-slate-200/90 shadow-xl shadow-slate-100 text-center">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-amber-100 items-center justify-center text-amber-600 shadow-sm">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 font-heading">
            Missing Reset Link Token
          </h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            This password reset link is invalid because no security token was provided.
            Please request a fresh reset link from the forgot password page.
          </p>
          <div className="pt-2 flex flex-col gap-2.5">
            <Link to="/forgot-password">
              <Button variant="primary" size="md" fullWidth>
                Request New Reset Link
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="ghost" size="sm" fullWidth>
                Back to Sign In
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 bg-white p-8 sm:p-10 rounded-3xl border border-slate-200/90 shadow-xl shadow-slate-100">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-indigo-600 items-center justify-center text-white shadow-md shadow-indigo-100">
            <KeyRound className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 font-heading">
            Set New Password
          </h2>
          <p className="text-xs text-slate-500">
            Choose a strong, unique password to secure your InterviewAI account
          </p>
        </div>

        {/* Success State */}
        {isSuccess ? (
          <div className="space-y-6 text-center">
            <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-2xl space-y-2">
              <div className="flex flex-col items-center gap-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
                <h3 className="font-bold text-emerald-900 text-base font-heading">
                  Password Reset Successfully!
                </h3>
                <p className="text-emerald-800 text-xs">
                  Your password has been securely updated. You can now sign in using your new credentials.
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={() => navigate('/login', { state: { message: 'Password reset successfully! Please sign in.' } })}
              icon={ArrowRight}
              iconPosition="right"
            >
              Sign In to Your Account
            </Button>
          </div>
        ) : (
          <>
            {/* API Error Alert */}
            {apiError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl space-y-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{apiError}</span>
                </div>
                {(apiError.includes('expired') || apiError.includes('Invalid')) && (
                  <div className="pt-1">
                    <Link
                      to="/forgot-password"
                      className="text-xs font-semibold text-rose-800 underline underline-offset-2 hover:text-rose-900"
                    >
                      Request a new password reset link &rarr;
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* Reset Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="New Password"
                id="new-password"
                type={showNewPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => {
                  setNewPassword(e.target.value);
                  if (errors.newPassword) setErrors((prev) => ({ ...prev, newPassword: '' }));
                }}
                error={errors.newPassword}
                icon={Lock}
                endIcon={showNewPassword ? EyeOff : Eye}
                onEndIconClick={() => setShowNewPassword(!showNewPassword)}
                required
                autoComplete="new-password"
                autoFocus
              />

              <Input
                label="Confirm New Password"
                id="confirm-password"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (errors.confirmPassword) setErrors((prev) => ({ ...prev, confirmPassword: '' }));
                }}
                error={errors.confirmPassword}
                icon={Lock}
                endIcon={showConfirmPassword ? EyeOff : Eye}
                onEndIconClick={() => setShowConfirmPassword(!showConfirmPassword)}
                required
                autoComplete="new-password"
              />

              {/* Password Requirements Checklist */}
              <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-2 text-xs">
                <span className="font-semibold text-slate-700 block text-[11px] uppercase tracking-wider">
                  Password Requirements:
                </span>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className={`flex items-center gap-1.5 ${hasMinLength ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                    {hasMinLength ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <div className="w-1.5 h-1.5 rounded-full bg-slate-300 ml-1 mr-1" />}
                    <span>8+ characters</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasUppercase ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                    {hasUppercase ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <div className="w-1.5 h-1.5 rounded-full bg-slate-300 ml-1 mr-1" />}
                    <span>1 uppercase letter</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasLowercase ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                    {hasLowercase ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <div className="w-1.5 h-1.5 rounded-full bg-slate-300 ml-1 mr-1" />}
                    <span>1 lowercase letter</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasNumber ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                    {hasNumber ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <div className="w-1.5 h-1.5 rounded-full bg-slate-300 ml-1 mr-1" />}
                    <span>1 number</span>
                  </div>
                </div>
                {confirmPassword && (
                  <div className={`pt-1 text-[11px] flex items-center gap-1.5 ${passwordsMatch ? 'text-emerald-600 font-medium' : 'text-rose-500'}`}>
                    {passwordsMatch ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <X className="w-3.5 h-3.5 text-rose-500" />}
                    <span>{passwordsMatch ? 'Passwords match' : 'Passwords do not match'}</span>
                  </div>
                )}
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                loading={isLoading}
                disabled={isLoading || !isPasswordValid || !passwordsMatch}
                icon={ArrowRight}
                iconPosition="right"
              >
                {isLoading ? 'Resetting password...' : 'Update Password'}
              </Button>
            </form>

            {/* Back to Sign In */}
            <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 font-semibold text-indigo-600 hover:text-indigo-700 hover:underline"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Sign In</span>
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ResetPasswordPage;
