import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SmartAddressPicker } from '../src/components/SmartAddressPicker';
import { AddressBookView } from '../src/components/AddressBookView';
import { AuthProvider } from '../src/context/AuthContext';
import { authApi } from '../src/services/authApi';
import { Address, ReverseGeocodeResult } from '../src/types/auth';

const mockResolvedAddress: ReverseGeocodeResult = {
  province_name: 'Hà Nội',
  province_code: '01',
  district_name: 'Quận Cầu Giấy',
  district_code: '005',
  ward_name: 'Phường Dịch Vọng',
  ward_code: '00184',
  street_address: 'Số 12, ngõ 158 Đường Cầu Giấy',
  formatted_address: 'Số 12, ngõ 158 Đường Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Hà Nội',
  latitude: 21.0285,
  longitude: 105.7896,
  place_id: 'VM_TEST_01',
  confidence: 0.95,
  level: 'house_number',
  source_provider: 'VIETMAP',
  is_mock: false,
};

const mockSavedAddress: Address = {
  id: 1,
  user_id: 10,
  recipient_name: 'Nguyễn Văn An',
  phone: '0987654321',
  province_name: 'Hà Nội',
  province_code: '01',
  district_name: 'Quận Cầu Giấy',
  district_code: '005',
  ward_name: 'Phường Dịch Vọng',
  ward_code: '00184',
  street_address: 'Số 12, ngõ 158 Đường Cầu Giấy',
  formatted_address: 'Số 12, ngõ 158 Đường Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Hà Nội',
  latitude: 21.0285,
  longitude: 105.7896,
  place_id: 'VM_TEST_01',
  source_provider: 'VIETMAP',
  confidence: 0.95,
  is_default: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe('Smart Address Auto-Detection (Frontend)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders Option A (Sử dụng vị trí hiện tại) and Option B (Chọn trên bản đồ)', () => {
    render(
      <SmartAddressPicker
        token="test-token"
        initialRecipientName="Nguyễn Văn An"
        initialPhone="0987654321"
        onSaveAddress={vi.fn()}
      />,
    );

    expect(screen.getByText('Sử dụng vị trí hiện tại')).toBeInTheDocument();
    expect(screen.getByText('Chọn trên bản đồ')).toBeInTheDocument();
    expect(screen.getByText('Địa chỉ nhận hàng')).toBeInTheDocument();
  });

  it('handles Geolocation success: retrieves GPS coordinates, calls reverse-geocode, and displays recognized address card', async () => {
    vi.spyOn(authApi, 'reverseGeocode').mockResolvedValueOnce({
      status: 'success',
      provider: 'VIETMAP',
      is_mock: false,
      address: mockResolvedAddress,
    });

    const mockGetCurrentPosition = vi.fn().mockImplementation((success) => {
      success({
        coords: {
          latitude: 21.0285,
          longitude: 105.7896,
          accuracy: 10,
        },
      });
    });

    // Mock navigator.geolocation
    Object.defineProperty(global.navigator, 'geolocation', {
      value: {
        getCurrentPosition: mockGetCurrentPosition,
      },
      writable: true,
      configurable: true,
    });

    render(
      <SmartAddressPicker
        token="test-token"
        initialRecipientName="Nguyễn Văn An"
        initialPhone="0987654321"
        onSaveAddress={vi.fn()}
      />,
    );

    const gpsBtn = screen.getByText('Sử dụng vị trí hiện tại');
    fireEvent.click(gpsBtn);

    await waitFor(() => {
      expect(mockGetCurrentPosition).toHaveBeenCalled();
      expect(authApi.reverseGeocode).toHaveBeenCalledWith('test-token', 21.0285, 105.7896);
    });

    await waitFor(() => {
      expect(screen.getByText('Địa chỉ được hệ thống nhận diện')).toBeInTheDocument();
      expect(screen.getByText('Số 12, ngõ 158 Đường Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Hà Nội')).toBeInTheDocument();
      expect(screen.getByText('Tự động điền từ vị trí của bạn')).toBeInTheDocument();
      expect(screen.getByText(/Độ chính xác: 95%/i)).toBeInTheDocument();
    });
  });

  it('handles Geolocation permission denied gracefully without crash', async () => {
    const mockGetCurrentPosition = vi.fn().mockImplementation((_, error) => {
      error({
        code: 1, // PERMISSION_DENIED
        PERMISSION_DENIED: 1,
        message: 'User denied Geolocation',
      });
    });

    Object.defineProperty(global.navigator, 'geolocation', {
      value: {
        getCurrentPosition: mockGetCurrentPosition,
      },
      writable: true,
      configurable: true,
    });

    render(
      <SmartAddressPicker
        token="test-token"
        initialRecipientName="Nguyễn Văn An"
        initialPhone="0987654321"
        onSaveAddress={vi.fn()}
      />,
    );

    const gpsBtn = screen.getByText('Sử dụng vị trí hiện tại');
    fireEvent.click(gpsBtn);

    await waitFor(() => {
      expect(screen.getByText(/Bạn đã từ chối quyền truy cập vị trí trên trình duyệt/i)).toBeInTheDocument();
    });
  });

  it('handles Geolocation timeout error gracefully', async () => {
    const mockGetCurrentPosition = vi.fn().mockImplementation((_, error) => {
      error({
        code: 3, // TIMEOUT
        TIMEOUT: 3,
        message: 'Geolocation timed out',
      });
    });

    Object.defineProperty(global.navigator, 'geolocation', {
      value: {
        getCurrentPosition: mockGetCurrentPosition,
      },
      writable: true,
      configurable: true,
    });

    render(
      <SmartAddressPicker
        token="test-token"
        initialRecipientName="Nguyễn Văn An"
        initialPhone="0987654321"
        onSaveAddress={vi.fn()}
      />,
    );

    const gpsBtn = screen.getByText('Sử dụng vị trí hiện tại');
    fireEvent.click(gpsBtn);

    await waitFor(() => {
      expect(screen.getByText(/Yêu cầu định vị quá thời gian chờ/i)).toBeInTheDocument();
    });
  });

  it('submits auto-filled address payload when user clicks Save', async () => {
    const saveMock = vi.fn().mockResolvedValue(undefined);

    vi.spyOn(authApi, 'reverseGeocode').mockResolvedValueOnce({
      status: 'success',
      provider: 'VIETMAP',
      is_mock: false,
      address: mockResolvedAddress,
    });

    Object.defineProperty(global.navigator, 'geolocation', {
      value: {
        getCurrentPosition: (success: (pos: unknown) => void) => {
          success({ coords: { latitude: 21.0285, longitude: 105.7896 } });
        },
      },
      writable: true,
      configurable: true,
    });

    render(
      <SmartAddressPicker
        token="test-token"
        initialRecipientName="Nguyễn Văn An"
        initialPhone="0987654321"
        onSaveAddress={saveMock}
        submitButtonText="Lưu địa chỉ"
      />,
    );

    // Click GPS detection
    fireEvent.click(screen.getByText('Sử dụng vị trí hiện tại'));

    await waitFor(() => {
      expect(screen.getByText('Địa chỉ được hệ thống nhận diện')).toBeInTheDocument();
    });

    // Click submit
    const submitBtn = screen.getByRole('button', { name: /Lưu địa chỉ/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(saveMock).toHaveBeenCalledWith(
        expect.objectContaining({
          recipient_name: 'Nguyễn Văn An',
          phone: '0987654321',
          province_name: 'Hà Nội',
          ward_name: 'Phường Dịch Vọng',
          street_address: 'Số 12, ngõ 158 Đường Cầu Giấy',
          latitude: 21.0285,
          longitude: 105.7896,
        }),
      );
    });
  });

  it('displays existing saved address with GPS badge in AddressBookView', async () => {
    vi.spyOn(authApi, 'listAddresses').mockResolvedValueOnce([mockSavedAddress]);

    // Mock localStorage auth token
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'novelia_token') return 'mock-jwt-token';
      return null;
    });

    render(
      <AuthProvider>
        <AddressBookView />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText('Sổ Địa Chỉ Nhận Hàng')).toBeInTheDocument();
      expect(screen.getByText('Số 12, ngõ 158 Đường Cầu Giấy')).toBeInTheDocument();
      expect(screen.getByText(/Tọa độ GPS: 21.0285, 105.7896/i)).toBeInTheDocument();
    });
  });
});
