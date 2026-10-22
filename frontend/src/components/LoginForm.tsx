import React, { useState } from 'react';
import { LogIn, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface LoginFormProps {
  onSwitchToRegister: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSwitchToRegister }) => {
  const { login, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError(null);

    if (!email.trim() || !password) {
      setLocalError('Vui lòng điền đầy đủ email và mật khẩu');
      return;
    }

    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      // Error is set in AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  const displayError = localError || error;

  return (
    <div className="auth-card">
      <div className="auth-header">
        <div className="auth-icon-badge">
          <LogIn size={24} />
        </div>
        <h2 className="auth-title">Đăng Nhập Tài Khoản</h2>
        <p className="auth-subtitle">Truy cập hệ thống mua sắm và trợ lý BookMatch AI của Novelia Books</p>
      </div>

      {displayError && (
        <div className="alert-box alert-error" role="alert">
          <AlertCircle size={18} className="alert-icon" />
          <span>{displayError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label className="form-label" htmlFor="login-email">Địa chỉ Email</label>
          <div className="input-wrapper">
            <Mail size={18} className="input-icon" />
            <input
              id="login-email"
              type="email"
              className="form-input"
              placeholder="tenban@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={submitting}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="login-password">Mật khẩu</label>
          <div className="input-wrapper">
            <Lock size={18} className="input-icon" />
            <input
              id="login-password"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              required
            />
          </div>
        </div>

        <button
          type="submit"
          className="submit-btn"
          disabled={submitting}
        >
          {submitting ? (
            <>
              <Loader2 size={18} className="spin-icon" />
              <span>Đang xác thực...</span>
            </>
          ) : (
            <>
              <LogIn size={18} />
              <span>Đăng nhập</span>
            </>
          )}
        </button>
      </form>

      <div className="auth-footer">
        <span>Chưa có tài khoản độc giả?</span>
        <button
          type="button"
          onClick={onSwitchToRegister}
          className="link-btn"
        >
          Đăng ký ngay
        </button>
      </div>
    </div>
  );
};
