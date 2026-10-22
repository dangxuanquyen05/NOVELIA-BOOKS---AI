/**
 * Type contracts for Novelia AI Assistant dialogue, tool output payloads, and diagnostics.
 */

export interface AIBookItem {
  id: number;
  title: string;
  slug: string;
  price: number;
  original_price?: number;
  discount_percent?: number;
  primary_author?: string;
  cover_image_url?: string;
  available_stock?: number;
  is_in_stock?: boolean;
}

export interface AIOrderItem {
  order_code: string;
  status: string;
  total_amount: number;
  created_at: string;
  item_count: number;
  payment_method: string;
  payment_status: string;
  carrier?: string;
  tracking_code?: string;
  shipment_status?: string;
}

export interface AITrackingCheckpoint {
  status: string;
  description: string;
  location?: string;
  time: string;
}

export interface AITrackingItem {
  order_code: string;
  order_status: string;
  total_amount: number;
  carrier: string;
  tracking_code?: string;
  shipment_status: string;
  timeline: AITrackingCheckpoint[];
}

export interface AICartUpdate {
  success: boolean;
  book_id: number;
  book_title: string;
  quantity_added: number;
  cart_total_items: number;
  cart_subtotal: number;
  message: string;
}

export interface AIConfirmationPreview {
  book_id?: number;
  book_title?: string;
  current_title?: string;
  proposed_title?: string;
  delta?: number;
  current_physical_stock?: number;
  proposed_physical_stock?: number;
  current_available_stock?: number;
  proposed_available_stock?: number;
  reason?: string;
  proposed_price?: number;
  current_price?: number;
  proposed_status?: string;
  code?: string;
  discount_percent?: number;
  max_discount_amount?: number;
  duration_days?: number;
}

export interface AIConfirmationPayload {
  confirmation_token: string;
  action_type: string;
  preview?: AIConfirmationPreview;
  message: string;
  book_id?: number;
}

export interface AISalesSummaryPayload {
  total_revenue: number;
  collected_revenue: number;
  total_orders: number;
  valid_orders_count: number;
  average_order_value: number;
  total_customers: number;
  profit_note?: string;
}

export interface AIInventorySummaryPayload {
  total_books: number;
  total_physical_stock: number;
  total_reserved_stock: number;
  total_available_stock: number;
  low_stock_count: number;
  out_of_stock_count: number;
}

export interface AILowStockBookItem {
  book_id: number;
  title: string;
  isbn: string;
  sku: string;
  physical_stock: number;
  reserved_stock: number;
  available_stock: number;
  low_stock_threshold: number;
}

export interface AILowStockPayload {
  count: number;
  low_stock_books: AILowStockBookItem[];
}

export interface AIConfirmRequest {
  confirmation_token: string;
}

export interface AIConfirmResponse {
  success: boolean;
  action_type: string;
  message: string;
  details?: Record<string, unknown>;
  executed_at: string;
}

export interface AIStructuredPayload {
  books?: AIBookItem[];
  book?: AIBookItem & { description?: string; publisher?: string; page_count?: number };
  orders?: AIOrderItem[];
  tracking?: AITrackingItem;
  cart_update?: AICartUpdate;
  confirmation?: AIConfirmationPayload;
  sales_summary?: AISalesSummaryPayload;
  inventory_summary?: AIInventorySummaryPayload;
  low_stock?: AILowStockPayload;
  marketing_draft?: Record<string, unknown>;
  is_configured?: boolean;
  status?: string;
}

export interface AIChatRequest {
  message: string;
  session_uuid?: string;
}

export interface AIChatResponse {
  session_uuid: string;
  message: string;
  suggested_prompts: string[];
  structured_payload?: AIStructuredPayload;
  created_at: string;
}

export interface AIMessageItem {
  id?: number | string;
  sender: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  structured_payload?: AIStructuredPayload;
  created_at: string;
}

export interface AIHealthStatus {
  status: string;
  provider: string;
  model: string;
  is_configured: boolean;
  details: string;
}
