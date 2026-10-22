/**
 * TypeScript types for Shopping Cart, Wishlist, Reviews, and Inventory Management.
 */

export interface CartItem {
  id: number;
  book_id: number;
  book_title: string;
  book_isbn: string;
  book_sku: string;
  cover_image_url: string;
  unit_price: number | string;
  original_price: number | string;
  discount_percent: number;
  quantity: number;
  subtotal: number | string;
  available_stock: number;
  is_available: boolean;
}

export interface Cart {
  id: number;
  user_id: number;
  items: CartItem[];
  total_items: number;
  subtotal_amount: number | string;
  has_stock_issues: boolean;
  updated_at: string;
}

export interface WishlistItem {
  id: number;
  book_id: number;
  book_title: string;
  book_isbn: string;
  book_sku: string;
  cover_image_url: string;
  price: number | string;
  original_price: number | string;
  is_in_stock: boolean;
  available_stock: number;
  added_at: string;
}

export interface Wishlist {
  id: number;
  user_id: number;
  name: string;
  items: WishlistItem[];
  total_items: number;
  created_at: string;
}

export interface Review {
  id: number;
  book_id: number;
  user_id: number;
  user_name: string;
  rating: number;
  title?: string | null;
  comment: string;
  is_verified_purchase: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface BookReviewSummary {
  average_rating: number;
  total_reviews: number;
  rating_distribution: Record<string, number>;
  reviews: Review[];
}

export interface InventoryItem {
  id: number;
  book_id: number;
  book_title: string;
  book_isbn: string;
  book_sku: string;
  cover_image_url: string;
  physical_stock: number;
  reserved_stock: number;
  available_stock: number;
  low_stock_threshold: number;
  is_low_stock: boolean;
  updated_at: string;
}

export interface InventoryTransaction {
  id: number;
  inventory_id: number;
  transaction_type: string;
  quantity_change: number;
  balance_after: number;
  reference_code?: string | null;
  reason?: string | null;
  staff_user_id?: number | null;
  created_at: string;
}

export interface PaginatedInventory {
  items: InventoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  low_stock_count: number;
}

export interface OrderItemSnapshot {
  id: number;
  book_id?: number | null;
  book_title_snapshot: string;
  book_isbn_snapshot: string;
  book_sku_snapshot: string;
  price_at_purchase: number | string;
  quantity: number;
  subtotal: number | string;
  created_at: string;
}

export type OrderStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'PROCESSING'
  | 'SHIPPING'
  | 'COMPLETED'
  | 'CANCELLED';

export interface Order {
  id: number;
  order_code: string;
  user_id: number;
  subtotal_amount: number | string;
  shipping_fee: number | string;
  discount_amount: number | string;
  total_amount: number | string;
  status: OrderStatus;
  recipient_name: string;
  recipient_phone: string;
  shipping_province: string;
  shipping_district: string;
  shipping_ward: string;
  shipping_street_address: string;
  shipping_formatted_address?: string | null;
  shipping_latitude?: number | null;
  shipping_longitude?: number | null;
  customer_notes?: string | null;
  staff_notes?: string | null;
  cancelled_reason?: string | null;
  payment_method?: string | null;
  payment_status?: string | null;
  payment_url?: string | null;
  shipment_carrier?: string | null;
  shipment_tracking_code?: string | null;
  shipment_status?: string | null;
  items: OrderItemSnapshot[];
  created_at: string;
  updated_at: string;
}

export interface CheckoutPayload {
  recipient_name: string;
  recipient_phone: string;
  shipping_province: string;
  shipping_district: string;
  shipping_ward: string;
  shipping_street_address: string;
  shipping_formatted_address?: string | null;
  shipping_latitude?: number | null;
  shipping_longitude?: number | null;
  customer_notes?: string;
  coupon_code?: string;
  payment_method: string;
  idempotency_key?: string;
}

export interface CouponValidationResult {
  is_valid: boolean;
  code: string;
  discount_type?: 'PERCENTAGE' | 'FIXED_AMOUNT' | null;
  discount_value?: number | string | null;
  discount_amount: number | string;
  min_order_value?: number | string | null;
  message: string;
}

export interface PaginatedOrders {
  items: Order[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
