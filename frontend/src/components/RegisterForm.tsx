import React, { useState } from 'react';
import { UserPlus, Mail, Lock, User, Phone, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { register, error, clearError } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError(null);

    if (!fullName.trim() || !email.trim() || !password) {
      setLocalError('Vui lòng điền đầy đủ các thông tin bắt buộc');
      return;
    }

    if (password.length < 8) {
      setLocalError('Mật khẩu phải có độ dài tối thiểu 8 ký tự');
      return;
    }

    if (password !== confirmPassword) {
      setLocalError('Xác nhận mật khẩu không khớp');
      return;
    }

    setSubmitting(true);
    try {
      await register(email, password, fullName, phone.trim() || undefined);
    } catch {
      // Handled in context
    } finally {
      setSubmitting(false);
    }
  };

  const displayError = localError || error;

  return (
    <div className="auth-card">
      <div className="auth-header">
        <div className="auth-icon-badge">
          <UserPlus size={24} />
        </div>
        <h2 className="auth-title">Đăng Ký Thành Viên</h2>
        <p className="auth-subtitle">Trở thành thành viên cộng đồng độc giả Novelia Books</p>
      </div>

      {displayError && (
        <div className="alert-box alert-error" role="alert">
          <AlertCircle size={18} className="alert-icon" />
          <span>{displayError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label className="form-label" htmlFor="register-name">Họ và tên *</label>
          <div className="input-wrapper">
            <User size={18} className="input-icon" />
            <input
              id="register-name"
              type="text"
              className="form-input"
              placeholder="Nguyễn Văn A"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={submitting}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="register-email">Địa chỉ Email *</label>
          <div className="input-wrapper">
            <Mail size={18} className="input-icon" />
            <input
              id="register-email"
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
          <label className="form-label" htmlFor="register-phone">Số điện thoại (tùy chọn)</label>
          <div className="input-wrapper">
            <Phone size={18} className="input-icon" />
            <input
              id="register-phone"
              type="tel"
              className="form-input"
              placeholder="0912 345 678"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={submitting}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="register-password">Mật khẩu (tối thiểu 8 ký tự) *</label>
          <div className="input-wrapper">
            <Lock size={18} className="input-icon" />
            <input
              id="register-password"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              required
              minLength={8}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="register-confirm">Xác nhận mật khẩu *</label>
          <div className="input-wrapper">
            <Lock size={18} className="input-icon" />
            <input
              id="register-confirm"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={submitting}
              required
              minLength={8}
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
              <span>Đang tạo tài khoản...</span>
            </>
          ) : (
            <>
              <UserPlus size={18} />
              <span>Đăng ký tài khoản</span>
            </>
          )}
        </button>
      </form>

      <div className="auth-footer">
        <span>Đã có tài khoản?</span>
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="link-btn"
        >
          Đăng nhập ngay
        </button>
      </div>
    </div>
  );
};
