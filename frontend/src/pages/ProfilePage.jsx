import React, { useState, useEffect } from 'react';
import {
  User,
  Mail,
  GraduationCap,
  Briefcase,
  Code2,
  Calendar,
  Camera,
  Save,
  CheckCircle2,
  AlertCircle,
  X,
  Plus,
} from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import Select from '../components/Select';
import Badge from '../components/Badge';
import Loading from '../components/Loading';
import { supportedRoles } from '../utils/mockData';
import { useAuth } from '../context/AuthContext';
import { getCurrentUser, updateProfile } from '../services/api';

const ProfilePage = () => {
  const { user: authUser, updateUser } = useAuth();

  const [profile, setProfile] = useState({
    full_name: authUser?.full_name || '',
    email: authUser?.email || '',
    college: authUser?.college || '',
    degree: authUser?.degree || '',
    branch: authUser?.branch || '',
    graduation_year: authUser?.graduation_year || '',
    skills: authUser?.skills || [],
    target_role: authUser?.target_role || 'Full Stack Developer',
  });

  const [newSkill, setNewSkill] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch actual authenticated user data from backend on mount
  useEffect(() => {
    let isMounted = true;
    const loadProfile = async () => {
      try {
        const data = await getCurrentUser();
        if (isMounted) {
          setProfile({
            full_name: data.full_name || '',
            email: data.email || '',
            college: data.college || '',
            degree: data.degree || '',
            branch: data.branch || '',
            graduation_year: data.graduation_year || '',
            skills: data.skills || [],
            target_role: data.target_role || 'Full Stack Developer',
          });
          updateUser(data);
        }
      } catch (err) {
        console.error('Failed to load profile data:', err);
        // Fallback to authUser in context if available
        if (authUser && isMounted) {
          setProfile({
            full_name: authUser.full_name || '',
            email: authUser.email || '',
            college: authUser.college || '',
            degree: authUser.degree || '',
            branch: authUser.branch || '',
            graduation_year: authUser.graduation_year || '',
            skills: authUser.skills || [],
            target_role: authUser.target_role || 'Full Stack Developer',
          });
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadProfile();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleAddSkill = (e) => {
    e.preventDefault();
    const trimmed = newSkill.trim();
    if (trimmed && !profile.skills.includes(trimmed)) {
      setProfile((prev) => ({
        ...prev,
        skills: [...prev.skills, trimmed],
      }));
      setNewSkill('');
    }
  };

  const handleRemoveSkill = (skillToRemove) => {
    setProfile((prev) => ({
      ...prev,
      skills: prev.skills.filter((s) => s !== skillToRemove),
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setIsSaving(true);

    try {
      const payload = {
        full_name: profile.full_name.trim(),
        college: profile.college.trim(),
        degree: profile.degree.trim(),
        branch: profile.branch.trim(),
        graduation_year: String(profile.graduation_year).trim(),
        skills: profile.skills,
        target_role: profile.target_role,
      };

      const updated = await updateProfile(payload);
      setProfile((prev) => ({
        ...prev,
        ...updated,
      }));
      updateUser(updated);

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Profile update error:', err);
      const detail = err.response?.data?.detail;
      setErrorMessage(
        typeof detail === 'string'
          ? detail
          : 'Failed to save profile changes. Please try again.'
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <Loading size="lg" text="Loading candidate profile..." />
      </div>
    );
  }

  // Ensure target role options include current target_role if not in list
  const roleOptions = supportedRoles.map((r) => r.title);
  if (profile.target_role && !roleOptions.includes(profile.target_role)) {
    roleOptions.unshift(profile.target_role);
  }

  const initialLetter = (profile.full_name || 'U').charAt(0).toUpperCase();

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="sm">
              Candidate Profile
            </Badge>
            <span className="text-xs text-slate-400">• Authenticated Candidate</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 font-heading">
            Student & Career Profile
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage your academic credentials, career aspirations, and foundational competencies.
          </p>
        </div>

        {saveSuccess && (
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Changes saved successfully!
          </div>
        )}

        {errorMessage && (
          <div className="flex items-center gap-2 text-xs font-semibold text-rose-700 bg-rose-50 px-3 py-1.5 rounded-xl border border-rose-200">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            {errorMessage}
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Card / Avatar banner */}
        <Card>
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className="relative group">
              <div className="w-24 h-24 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center text-3xl font-bold shadow-md shadow-indigo-100 ring-4 ring-white">
                {initialLetter}
              </div>
              <button
                type="button"
                className="absolute -bottom-2 -right-2 p-2 rounded-xl bg-slate-900 text-white shadow-xs hover:bg-slate-800 transition-colors cursor-pointer"
                title="Change Avatar"
              >
                <Camera className="w-4 h-4" />
              </button>
            </div>

            <div className="text-center sm:text-left space-y-1">
              <h2 className="text-xl font-bold text-slate-900 font-heading">
                {profile.full_name || 'Candidate Name'}
              </h2>
              <p className="text-xs text-slate-500">{profile.email || 'candidate@example.com'}</p>
              <div className="pt-2 flex flex-wrap items-center justify-center sm:justify-start gap-2">
                <Badge variant="primary" size="sm">
                  {profile.target_role || 'Target Role'}
                </Badge>
                <Badge variant="neutral" size="sm">
                  Class of {profile.graduation_year || 'N/A'}
                </Badge>
              </div>
            </div>
          </div>
        </Card>

        {/* Personal & Academic Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card title="Personal Information" icon={User}>
            <div className="space-y-4">
              <Input
                label="Full Name"
                value={profile.full_name}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                icon={User}
                required
              />
              <Input
                label="Email Address (Read-only)"
                type="email"
                value={profile.email}
                disabled
                icon={Mail}
                className="opacity-75 cursor-not-allowed"
              />
              <Select
                label="Target Job Role"
                options={roleOptions}
                value={profile.target_role}
                onChange={(e) => setProfile({ ...profile, target_role: e.target.value })}
                required
              />
            </div>
          </Card>

          <Card title="Academic Information" icon={GraduationCap}>
            <div className="space-y-4">
              <Input
                label="College / University"
                value={profile.college}
                onChange={(e) => setProfile({ ...profile, college: e.target.value })}
                icon={GraduationCap}
                required
              />
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Degree"
                  value={profile.degree}
                  onChange={(e) => setProfile({ ...profile, degree: e.target.value })}
                  required
                />
                <Input
                  label="Graduation Year"
                  value={profile.graduation_year}
                  onChange={(e) => setProfile({ ...profile, graduation_year: e.target.value })}
                  icon={Calendar}
                  required
                />
              </div>
              <Input
                label="Branch / Major"
                value={profile.branch}
                onChange={(e) => setProfile({ ...profile, branch: e.target.value })}
                required
              />
            </div>
          </Card>
        </div>

        {/* Skills Section */}
        <Card title="Skills & Competencies" subtitle="Add technologies and concepts you wish to be tested on" icon={Code2}>
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/80"
                >
                  <span>{skill}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(skill)}
                    className="ml-2 hover:text-indigo-900 focus:outline-none cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>

            <div className="flex gap-2 pt-2">
              <input
                type="text"
                placeholder="e.g., Docker, GraphQL, System Design..."
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill(e);
                  }
                }}
                className="flex-1 px-3.5 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              />
              <Button
                type="button"
                size="sm"
                variant="outline"
                icon={Plus}
                onClick={handleAddSkill}
              >
                Add Skill
              </Button>
            </div>
          </div>
        </Card>

        <div className="flex justify-end pt-2">
          <Button
            type="submit"
            size="md"
            variant="primary"
            icon={Save}
            loading={isSaving}
            disabled={isSaving}
          >
            {isSaving ? 'Saving Changes...' : 'Save Profile Changes'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ProfilePage;
