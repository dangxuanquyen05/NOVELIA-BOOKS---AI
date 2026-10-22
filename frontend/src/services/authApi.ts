import {
  Address,
  AddressCreatePayload,
  MapConfig,
  ReverseGeocodeResult,
  TokenResponse,
  User,
} from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiError extends Error {
  statusCode: number;
  details?: unknown;

  constructor(message: string, statusCode: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'Yêu cầu không thành công';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await res.text() || res.statusText;
    }
    throw new ApiError(errorDetail, res.status);
  }
  return res.json() as Promise<T>;
}

export const authApi = {
  async register(payload: { email: string; password: string; full_name: string; phone?: string }): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<User>(res);
  },

  async login(payload: { email: string; password: string }): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<TokenResponse>(res);
  },

  async getProfile(token: string): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<User>(res);
  },

  async updateProfile(token: string, payload: { full_name?: string; phone?: string }): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<User>(res);
  },

  async changePassword(token: string, payload: { current_password: string; new_password: string }): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<{ message: string }>(res);
  },

  async logout(token: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<{ message: string }>(res);
  },

  // Address endpoints
  async listAddresses(token: string): Promise<Address[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/addresses`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<Address[]>(res);
  },

  async createAddress(token: string, payload: AddressCreatePayload): Promise<Address> {
    const res = await fetch(`${API_BASE_URL}/api/v1/addresses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<Address>(res);
  },

  async updateAddress(token: string, addressId: number, payload: Partial<AddressCreatePayload>): Promise<Address> {
    const res = await fetch(`${API_BASE_URL}/api/v1/addresses/${addressId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<Address>(res);
  },

  async deleteAddress(token: string, addressId: number): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/addresses/${addressId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<{ message: string }>(res);
  },

  // Smart Address & Reverse Geocoding
  async getGeoConfig(token: string): Promise<MapConfig> {
    const res = await fetch(`${API_BASE_URL}/api/v1/addresses/geo/config`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<MapConfig>(res);
  },

  async reverseGeocode(
    token: string,
    lat: number,
    lng: number,
  ): Promise<{ status: string; provider: string; is_mock: boolean; address: ReverseGeocodeResult }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/addresses/reverse-geocode`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ lat, lng }),
    });
    return handleResponse<{ status: string; provider: string; is_mock: boolean; address: ReverseGeocodeResult }>(res);
  },
};
