import React, { useState } from 'react';
import { User as UserIcon, Shield, Lock, KeyRound, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/authApi';

export const ProfileView: React.FC = () => {
  const { user, token, refreshProfile } = useAuth();

  // Profile update form state
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Password change form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  if (!user || !token) {
    return null;
  }

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileSuccess(null);
    setProfileError(null);

    try {
      await authApi.updateProfile(token, {
        full_name: fullName.trim() || undefined,
        phone: phone.trim() || undefined,
      });
      await refreshProfile();
      setProfileSuccess('Cập nhật thông tin hồ sơ thành công!');
    } catch (err: unknown) {
      setProfileError(err instanceof Error ? err.message : 'Không thể cập nhật hồ sơ');
    } finally {
      setProfileSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordSaving(true);
    setPasswordSuccess(null);
    setPasswordError(null);

    if (newPassword.length < 8) {
      setPasswordError('Mật khẩu mới phải có tối thiểu 8 ký tự');
      setPasswordSaving(false);
      return;
    }

    if (newPassword !== confirmNewPassword) {
      setPasswordError('Xác nhận mật khẩu mới không khớp');
      setPasswordSaving(false);
      return;
    }

    try {
      const resp = await authApi.changePassword(token, {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess(resp.message || 'Đổi mật khẩu thành công!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (err: unknown) {
      setPasswordError(err instanceof Error ? err.message : 'Đổi mật khẩu không thành công');
    } finally {
      setPasswordSaving(false);
    }
  };

  return (
    <div className="profile-container">
      {/* Account Overview Header Card */}
      <div className="account-overview-card">
        <div className="user-avatar-large">
          <UserIcon size={40} />
        </div>
        <div className="user-overview-meta">
          <div className="user-name-row">
            <h2 className="user-display-name">{user.full_name}</h2>
            <div className="role-tags-list">
              {user.roles.map((r) => (
                <span
                  key={r}
                  className={`role-badge ${r === 'ADMIN' ? 'role-admin' : r === 'STAFF' ? 'role-staff' : 'role-customer'}`}
                >
                  <Shield size={12} />
                  <span>{r}</span>
                </span>
              ))}
            </div>
          </div>
          <p className="user-email-text">{user.email}</p>
          <p className="user-joined-text">
            Thành viên từ: {new Date(user.created_at).toLocaleDateString('vi-VN')}
          </p>
        </div>
      </div>

      <div className="profile-forms-grid">
        {/* Form 1: Edit Profile */}
        <div className="settings-box">
          <div className="settings-header">
            <UserIcon size={20} className="text-gold" />
            <h3>Thông Tin Cá Nhân</h3>
          </div>

          {profileSuccess && (
            <div className="alert-box alert-success" role="alert">
              <CheckCircle2 size={16} />
              <span>{profileSuccess}</span>
            </div>
          )}

          {profileError && (
            <div className="alert-box alert-error" role="alert">
              <AlertCircle size={16} />
              <span>{profileError}</span>
            </div>
          )}

          <form onSubmit={handleUpdateProfile} className="auth-form">
            <div className="form-group">
              <label className="form-label" htmlFor="edit-name">Họ và tên</label>
              <input
                id="edit-name"
                type="text"
                className="form-input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                disabled={profileSaving}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="edit-phone">Số điện thoại</label>
              <input
                id="edit-phone"
                type="tel"
                className="form-input"
                placeholder="0912 345 678"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={profileSaving}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="readonly-email">Email (Không thể thay đổi)</label>
              <input
                id="readonly-email"
                type="email"
                className="form-input readonly-input"
                value={user.email}
                disabled
              />
            </div>

            <button type="submit" className="submit-btn" disabled={profileSaving}>
              {profileSaving ? (
                <>
                  <Loader2 size={16} className="spin-icon" />
                  <span>Đang lưu...</span>
                </>
              ) : (
                <span>Lưu thông tin</span>
              )}
            </button>
          </form>
        </div>

        {/* Form 2: Change Password */}
        <div className="settings-box">
          <div className="settings-header">
            <KeyRound size={20} className="text-gold" />
            <h3>Đổi Mật Khẩu</h3>
          </div>

          {passwordSuccess && (
            <div className="alert-box alert-success" role="alert">
              <CheckCircle2 size={16} />
              <span>{passwordSuccess}</span>
            </div>
          )}

          {passwordError && (
            <div className="alert-box alert-error" role="alert">
              <AlertCircle size={16} />
              <span>{passwordError}</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="auth-form">
            <div className="form-group">
              <label className="form-label" htmlFor="old-password">Mật khẩu hiện tại</label>
              <div className="input-wrapper">
                <Lock size={16} className="input-icon" />
                <input
                  id="old-password"
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  disabled={passwordSaving}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="new-password">Mật khẩu mới (tối thiểu 8 ký tự)</label>
              <div className="input-wrapper">
                <Lock size={16} className="input-icon" />
                <input
                  id="new-password"
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={passwordSaving}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="confirm-new-password">Xác nhận mật khẩu mới</label>
              <div className="input-wrapper">
                <Lock size={16} className="input-icon" />
                <input
                  id="confirm-new-password"
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={passwordSaving}
                />
              </div>
            </div>

            <button type="submit" className="submit-btn" disabled={passwordSaving}>
              {passwordSaving ? (
                <>
                  <Loader2 size={16} className="spin-icon" />
                  <span>Đang cập nhật...</span>
                </>
              ) : (
                <span>Đổi mật khẩu</span>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
