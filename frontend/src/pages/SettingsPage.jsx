import React, { useState } from 'react';
import {
  Settings,
  User,
  Shield,
  Sliders,
  Bell,
  Sun,
  Moon,
  Lock,
  Eye,
  EyeOff,
  CheckCircle2,
  Save,
} from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import Select from '../components/Select';
import Badge from '../components/Badge';
import { useAuth } from '../context/AuthContext';
import { mockUser } from '../utils/mockData';

const SettingsPage = () => {
  const { user } = useAuth();
  const [name, setName] = useState(user?.full_name || mockUser.name);
  const [email, setEmail] = useState(user?.email || mockUser.email);
  const [interviewMode, setInterviewMode] = useState('text');
  const [feedbackDepth, setFeedbackDepth] = useState('comprehensive');
  const [theme, setTheme] = useState('light');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  const handleSaveAccount = (e) => {
    e.preventDefault();
    setStatusMessage('Account settings updated.');
    setTimeout(() => setStatusMessage(null), 3000);
  };

  const handleSavePreferences = (e) => {
    e.preventDefault();
    setStatusMessage('Preferences saved.');
    setTimeout(() => setStatusMessage(null), 3000);
  };

  const handleUpdatePassword = (e) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) {
      alert('Please fill out all password fields.');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      alert('New passwords do not match.');
      return;
    }
    setStatusMessage('Password updated successfully.');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmNewPassword('');
    setTimeout(() => setStatusMessage(null), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="sm">
              Configuration
            </Badge>
            <span className="text-xs text-slate-400">• Phase 1 UI</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
            Application Settings
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Control your account information, mock interview preferences, and security settings.
          </p>
        </div>

        {statusMessage && (
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {statusMessage}
          </div>
        )}
      </div>

      <div className="space-y-6">
        {/* Section 1: Account Settings */}
        <Card title="Account Settings" subtitle="Personal details associated with your candidate record" icon={User}>
          <form onSubmit={handleSaveAccount} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Full Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <Input
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="flex justify-end pt-2">
              <Button type="submit" size="sm" variant="primary" icon={Save}>
                Save Account
              </Button>
            </div>
          </form>
        </Card>

        {/* Section 2: Preferences */}
        <Card title="Preferences" subtitle="Customize interview feedback and appearance" icon={Sliders}>
          <form onSubmit={handleSavePreferences} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 tracking-wide mb-2">
                Interview Input Mode
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setInterviewMode('text')}
                  className={`p-3 rounded-xl border text-left text-xs transition-all cursor-pointer ${
                    interviewMode === 'text'
                      ? 'border-indigo-600 bg-indigo-50/70 font-semibold text-indigo-900'
                      : 'border-slate-200 hover:border-slate-300 text-slate-700'
                  }`}
                >
                  <p className="font-semibold text-slate-900">Text Responses (Default)</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Type and edit answers in code/markdown editors.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setInterviewMode('voice')}
                  className={`p-3 rounded-xl border text-left text-xs transition-all cursor-pointer ${
                    interviewMode === 'voice'
                      ? 'border-indigo-600 bg-indigo-50/70 font-semibold text-indigo-900'
                      : 'border-slate-200 hover:border-slate-300 text-slate-700'
                  }`}
                >
                  <p className="font-semibold text-slate-900">Voice & Microphone (Future Phase)</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Real-time speech-to-text with conversational pacing.
                  </p>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 tracking-wide mb-2">
                Theme Preference
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setTheme('light')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium border cursor-pointer ${
                    theme === 'light'
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-700 font-semibold'
                      : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Sun className="w-4 h-4" />
                  Light Mode
                </button>
                <button
                  type="button"
                  onClick={() => setTheme('dark')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium border cursor-pointer ${
                    theme === 'dark'
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-700 font-semibold'
                      : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Moon className="w-4 h-4" />
                  Dark Mode (Coming in Phase 2)
                </button>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" size="sm" variant="primary" icon={Save}>
                Save Preferences
              </Button>
            </div>
          </form>
        </Card>

        {/* Section 3: Security */}
        <Card title="Security & Authentication" subtitle="Manage your login credentials" icon={Shield}>
          <form onSubmit={handleUpdatePassword} className="space-y-4 max-w-md">
            <Input
              label="Current Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              icon={Lock}
              endIcon={showPassword ? EyeOff : Eye}
              onEndIconClick={() => setShowPassword(!showPassword)}
            />

            <Input
              label="New Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              icon={Lock}
            />

            <Input
              label="Confirm New Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              icon={Lock}
            />

            <div className="pt-2">
              <Button type="submit" size="sm" variant="secondary" icon={Lock}>
                Update Password
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default SettingsPage;
