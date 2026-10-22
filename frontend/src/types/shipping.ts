/**
 * TypeScript types for Phase 8 Logistics & Shipping Integration.
 */

export interface ShipmentEvent {
  id: number;
  status: string;
  description: string;
  location?: string | null;
  occurred_at: string;
}

export interface ShipmentDetail {
  id: number;
  order_id: number;
  order_code: string;
  carrier: string;
  tracking_code?: string | null;
  status: string;
  status_label: string;
  shipping_fee: string | number;
  estimated_delivery_date?: string | null;
  dispatched_at?: string | null;
  delivered_at?: string | null;
  recipient_name: string;
  recipient_phone: string;
  shipping_address: string;
  events: ShipmentEvent[];
  created_at: string;
}

export interface ShipmentDispatchPayload {
  carrier: 'GHN' | 'GHTK' | 'MOCK';
  weight: number;
  length?: number;
  width?: number;
  height?: number;
  required_note?: 'CHOXEMHANGKHONGTHU' | 'CHOTHUHANG' | 'KHONGCHOXEMHANG';
  staff_notes?: string;
}

export interface ShipmentTrackingLookup {
  tracking_code: string;
  order_code: string;
  carrier: string;
  status: string;
  status_label: string;
  estimated_delivery_date?: string | null;
  delivered_at?: string | null;
  events: ShipmentEvent[];
}

export interface ShippingProviderStatus {
  carrier: string;
  environment: string;
  is_live_ready: boolean;
  status_text: string;
  api_url: string;
  notes: string;
}
