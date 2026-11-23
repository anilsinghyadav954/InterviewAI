import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  loginUser as apiLogin,
  registerUser as apiRegister,
  getCurrentUser as apiGetCurrentUser,
} from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Restore authenticated session on mount or token change
  const restoreSession = useCallback(async () => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }

    try {
      const userData = await apiGetCurrentUser();
      setUser(userData);
      setToken(storedToken);
    } catch (error) {
      console.warn('Session restoration failed or token expired:', error?.response?.status || error);
      localStorage.removeItem('token');
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  // Handle candidate login
  const login = async (credentials) => {
    setLoading(true);
    try {
      const data = await apiLogin(credentials);
      // data: { access_token, token_type, user: { id, full_name, email } }
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);

      // Fetch full profile (academic details, skills, target role)
      try {
        const fullProfile = await apiGetCurrentUser();
        setUser(fullProfile);
      } catch {
        setUser(data.user);
      }

      return data;
    } finally {
      setLoading(false);
    }
  };

  // Handle candidate registration
  const register = async (userData) => {
    return await apiRegister(userData);
  };

  // Clear authentication session
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  // Reusable helper to update current user state locally (e.g., after profile edit)
  const updateUser = (updatedFields) => {
    setUser((prev) => (prev ? { ...prev, ...updatedFields } : prev));
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: Boolean(token && user),
    login,
    register,
    logout,
    updateUser,
    restoreSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
