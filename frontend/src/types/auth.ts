export interface User {
  id: number;
  email: string;
  full_name: string;
  phone?: string | null;
  is_active: boolean;
  roles: string[];
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  roles: string[];
}

export interface Address {
  id: number;
  user_id: number;
  recipient_name: string;
  phone: string;
  province_code: string;
  province_name: string;
  district_code: string;
  district_name: string;
  ward_code: string;
  ward_name: string;
  street_address: string;
  formatted_address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  place_id?: string | null;
  source_provider?: string | null;
  confidence?: number | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface AddressCreatePayload {
  recipient_name: string;
  phone: string;
  province_code: string;
  province_name: string;
  district_code: string;
  district_name: string;
  ward_code: string;
  ward_name: string;
  street_address: string;
  formatted_address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  place_id?: string | null;
  source_provider?: string | null;
  confidence?: number | null;
  is_default: boolean;
}

export interface ReverseGeocodeResult {
  province_name: string;
  province_code: string;
  district_name: string;
  district_code: string;
  ward_name: string;
  ward_code: string;
  street_address: string;
  formatted_address: string;
  latitude: number;
  longitude: number;
  place_id?: string | null;
  confidence: number;
  level: string;
  source_provider: string;
  is_mock: boolean;
}

export interface MapConfig {
  provider: string;
  is_mock: boolean;
  has_api_key: boolean;
  default_lat: number;
  default_lng: number;
  tile_url: string;
  attribution: string;
}

