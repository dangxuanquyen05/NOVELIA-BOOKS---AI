/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../services/authApi';
import { User } from '../types/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, phone?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('novelia_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  // Initialize session from stored token
  useEffect(() => {
    async function initSession() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const profile = await authApi.getProfile(token);
        setUser(profile);
      } catch {
        // Token expired or invalid
        localStorage.removeItem('novelia_token');
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    initSession();
  }, [token]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await authApi.login({ email, password });
      localStorage.setItem('novelia_token', resp.access_token);
      setToken(resp.access_token);
      const profile = await authApi.getProfile(resp.access_token);
      setUser(profile);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Đăng nhập không thành công';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string, phone?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await authApi.register({
        email,
        password,
        full_name: fullName,
        phone,
      });
      // Automatically log in after registration
      await login(email, password);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Đăng ký không thành công';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await authApi.logout(token);
      } catch {
        // Continue clearing local state even if server logout errored
      }
    }
    localStorage.removeItem('novelia_token');
    setToken(null);
    setUser(null);
  };

  const refreshProfile = async () => {
    if (!token) return;
    try {
      const profile = await authApi.getProfile(token);
      setUser(profile);
    } catch {
      // Ignored
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        refreshProfile,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useSafeAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: async () => {},
      register: async () => {},
      logout: async () => {},
      refreshProfile: async () => {},
      clearError: () => {},
    };
  }
  return context;
};

