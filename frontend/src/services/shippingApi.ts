/**
 * API client for Phase 8 Logistics, Carrier Integrations, and Tracking.
 */

import { getApiBaseUrl } from './api';
import {
  ShipmentDetail,
  ShipmentDispatchPayload,
  ShipmentTrackingLookup,
  ShippingProviderStatus,
} from '../types/shipping';

function authHeaders(token: string): HeadersInit {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export async function dispatchOrder(
  token: string,
  orderCode: string,
  payload: ShipmentDispatchPayload
): Promise<ShipmentDetail> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/shipping/orders/${encodeURIComponent(orderCode)}/dispatch`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tạo vận đơn: ${res.status}`);
  }
  return res.json();
}

export async function fetchOrderTracking(
  token: string,
  orderCode: string
): Promise<ShipmentDetail> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/shipping/orders/${encodeURIComponent(orderCode)}/tracking`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tra cứu vận đơn: ${res.status}`);
  }
  return res.json();
}

export async function lookupPublicTracking(
  trackingCode: string
): Promise<ShipmentTrackingLookup> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/shipping/track/${encodeURIComponent(trackingCode)}`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Không tìm thấy mã vận đơn: ${res.status}`);
  }
  return res.json();
}

export async function cancelShipment(
  token: string,
  orderCode: string
): Promise<{ message: string; status: string }> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(
    `${baseUrl}/api/v1/shipping/orders/${encodeURIComponent(orderCode)}/cancel-shipment`,
    {
      method: 'POST',
      headers: authHeaders(token),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi hủy vận đơn: ${res.status}`);
  }
  return res.json();
}

export async function fetchShippingProvidersStatus(): Promise<ShippingProviderStatus[]> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/shipping/providers/status`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Lỗi kiểm tra trạng thái nhà vận chuyển: ${res.status}`);
  }
  return res.json();
}
