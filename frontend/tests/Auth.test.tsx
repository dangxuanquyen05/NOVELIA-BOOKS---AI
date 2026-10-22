import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { LoginForm } from '../src/components/LoginForm';
import { RegisterForm } from '../src/components/RegisterForm';
import { ProfileView } from '../src/components/ProfileView';
import { AddressBookView } from '../src/components/AddressBookView';
import { AuthProvider } from '../src/context/AuthContext';
import * as authApiModule from '../src/services/authApi';

describe('NOVELIA BOOKS — Phase 3 Auth & RBAC Frontend Components', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('LoginForm Component', () => {
    it('renders login fields and submit button', () => {
      const handleSwitch = vi.fn();
      render(
        <AuthProvider>
          <LoginForm onSwitchToRegister={handleSwitch} />
        </AuthProvider>
      );

      expect(screen.getByLabelText(/Địa chỉ Email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^Mật khẩu/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument();
    });

    it('triggers switch to register callback when clicking link', () => {
      const handleSwitch = vi.fn();
      render(
        <AuthProvider>
          <LoginForm onSwitchToRegister={handleSwitch} />
        </AuthProvider>
      );

      fireEvent.click(screen.getByRole('button', { name: /Đăng ký ngay/i }));
      expect(handleSwitch).toHaveBeenCalledTimes(1);
    });

    it('shows error when submitting empty credentials', async () => {
      render(
        <AuthProvider>
          <LoginForm onSwitchToRegister={vi.fn()} />
        </AuthProvider>
      );

      const form = screen.getByRole('button', { name: /Đăng nhập/i }).closest('form')!;
      fireEvent.submit(form);
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('displays server error alert on invalid credentials', async () => {
      vi.spyOn(authApiModule.authApi, 'login').mockRejectedValue(
        new Error('Email hoặc mật khẩu không chính xác')
      );

      render(
        <AuthProvider>
          <LoginForm onSwitchToRegister={vi.fn()} />
        </AuthProvider>
      );

      fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
        target: { value: 'wrong@novelia.vn' },
      });
      fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
        target: { value: 'wrongpass123' },
      });
      fireEvent.click(screen.getByRole('button', { name: /Đăng nhập/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email hoặc mật khẩu không chính xác');
      });
    });
  });

  describe('RegisterForm Component', () => {
    it('validates password minimum length (8 chars)', async () => {
      render(
        <AuthProvider>
          <RegisterForm onSwitchToLogin={vi.fn()} />
        </AuthProvider>
      );

      fireEvent.change(screen.getByLabelText(/Họ và tên/i), {
        target: { value: 'Nguyễn Văn A' },
      });
      fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
        target: { value: 'vana@novelia.vn' },
      });
      fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
        target: { value: 'short' },
      });
      fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu/i), {
        target: { value: 'short' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Đăng ký tài khoản/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/tối thiểu 8 ký tự/i);
      });
    });

    it('validates password and confirm password match', async () => {
      render(
        <AuthProvider>
          <RegisterForm onSwitchToLogin={vi.fn()} />
        </AuthProvider>
      );

      fireEvent.change(screen.getByLabelText(/Họ và tên/i), {
        target: { value: 'Nguyễn Văn A' },
      });
      fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
        target: { value: 'vana@novelia.vn' },
      });
      fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
        target: { value: 'Password123@' },
      });
      fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu/i), {
        target: { value: 'DifferentPassword123@' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Đăng ký tài khoản/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/không khớp/i);
      });
    });

    it('displays duplicate email error from backend', async () => {
      vi.spyOn(authApiModule.authApi, 'register').mockRejectedValue(
        new Error('Email đã được sử dụng bởi một tài khoản khác')
      );

      render(
        <AuthProvider>
          <RegisterForm onSwitchToLogin={vi.fn()} />
        </AuthProvider>
      );

      fireEvent.change(screen.getByLabelText(/Họ và tên/i), {
        target: { value: 'Nguyễn Văn A' },
      });
      fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
        target: { value: 'existing@novelia.vn' },
      });
      fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
        target: { value: 'Password123@' },
      });
      fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu/i), {
        target: { value: 'Password123@' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Đăng ký tài khoản/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/Email đã được sử dụng/i);
      });
    });
  });

  describe('ProfileView Component', () => {
    it('renders authenticated user information and roles correctly', async () => {
      localStorage.setItem('novelia_token', 'mock_jwt_token');

      vi.spyOn(authApiModule.authApi, 'getProfile').mockResolvedValue({
        id: 10,
        email: 'customer@novelia.vn',
        full_name: 'Trần Thị B',
        phone: '0901234567',
        is_active: true,
        roles: ['CUSTOMER'],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      render(
        <AuthProvider>
          <ProfileView />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Trần Thị B')).toBeInTheDocument();
        expect(screen.getByText('CUSTOMER')).toBeInTheDocument();
        expect(screen.getByDisplayValue('customer@novelia.vn')).toBeDisabled();
      });
    });
  });

  describe('AddressBookView Component', () => {
    it('renders address cards and default indicator', async () => {
      localStorage.setItem('novelia_token', 'mock_jwt_token');

      vi.spyOn(authApiModule.authApi, 'getProfile').mockResolvedValue({
        id: 10,
        email: 'customer@novelia.vn',
        full_name: 'Trần Thị B',
        is_active: true,
        roles: ['CUSTOMER'],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      vi.spyOn(authApiModule.authApi, 'listAddresses').mockResolvedValue([
        {
          id: 1,
          user_id: 10,
          recipient_name: 'Trần Thị B',
          phone: '0901234567',
          province_name: 'TP. Hồ Chí Minh',
          province_code: '79',
          district_name: 'Quận 1',
          district_code: '760',
          ward_name: 'Phường Bến Nghé',
          ward_code: '26734',
          street_address: '123 Đường Lê Lợi',
          is_default: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ]);

      render(
        <AuthProvider>
          <AddressBookView />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('123 Đường Lê Lợi')).toBeInTheDocument();
        expect(screen.getByText('Mặc định')).toBeInTheDocument();
      });
    });
  });
});
