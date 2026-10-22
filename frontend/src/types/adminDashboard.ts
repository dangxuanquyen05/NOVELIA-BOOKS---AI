/**
 * TypeScript definitions for Phase 7 Admin Dashboard, KPIs, and Governance.
 */

export interface DashboardKpiSummary {
  total_revenue: string | number;
  collected_revenue: string | number;
  has_cost_data: boolean;
  profit_note: string;
  total_orders: number;
  valid_orders_count: number;
  average_order_value: string | number;
  total_books: number;
  low_stock_count: number;
  total_customers: number;
  total_staff: number;
  active_coupons_count: number;
}

export interface RevenueTimelinePoint {
  date_label: string;
  revenue: string | number;
  collected_cash: string | number;
  order_count: number;
}

export interface OrderStatusCount {
  status: string;
  label: string;
  count: number;
  percentage: number;
  total_amount: string | number;
}

export interface TopSellingBook {
  book_id: number;
  title: string;
  isbn: string;
  sku?: string;
  cover_image_url?: string | null;
  units_sold?: number;
  total_quantity_sold?: number;
  total_sales?: string | number;
  total_revenue?: string | number;
  current_stock?: number;
}

export interface LowStockAlertItem {
  book_id: number;
  title: string;
  isbn: string;
  sku: string;
  available_stock: number;
  physical_stock: number;
  reserved_stock: number;
  low_stock_threshold: number;
  is_out_of_stock?: boolean;
}

export interface RecentActivityItem {
  id: string;
  activity_type: "ORDER" | "INVENTORY" | "USER" | "PROMOTION" | string;
  title: string;
  description: string;
  severity?: "info" | "warning" | "success" | "danger" | string;
  badge_type?: string;
  timestamp?: string;
  created_at?: string;
  reference_id?: string | number | null;
}

export interface AdminDashboardSummaryResponse {
  kpis: DashboardKpiSummary;
  timeline: RevenueTimelinePoint[];
  status_breakdown: OrderStatusCount[];
  top_selling_books: TopSellingBook[];
  low_stock_alerts: LowStockAlertItem[];
  recent_activities: RecentActivityItem[];
  filter_period: string;
}

export interface AdminCategoryItem {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  parent_id?: number | null;
  display_order: number;
  books_count: number;
  created_at: string;
}

export interface AdminCategoryCreatePayload {
  name: string;
  slug?: string;
  description?: string;
  parent_id?: number | null;
  display_order?: number;
}

export interface AdminCategoryUpdatePayload {
  name?: string;
  slug?: string;
  description?: string;
  parent_id?: number | null;
  display_order?: number;
}

export interface AdminAuthorItem {
  id: number;
  name: string;
  slug: string;
  bio?: string | null;
  avatar_url?: string | null;
  birth_year?: number | null;
  nationality?: string | null;
  books_count: number;
  created_at: string;
}

export interface AdminAuthorCreatePayload {
  name: string;
  slug?: string;
  bio?: string;
  avatar_url?: string;
  birth_year?: number;
  nationality?: string;
}

export interface AdminPublisherItem {
  id: number;
  name: string;
  slug: string;
  contact_info?: string | null;
  address?: string | null;
  website?: string | null;
  books_count: number;
  created_at: string;
}

export interface AdminPublisherCreatePayload {
  name: string;
  slug?: string;
  contact_info?: string;
  address?: string;
  website?: string;
}

export interface AdminUserItem {
  id: number;
  email: string;
  full_name: string;
  phone?: string | null;
  is_active: boolean;
  roles: string[];
  orders_count: number;
  total_spent: string | number;
  created_at: string;
}

export interface AdminUserListResponse {
  items: AdminUserItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminCouponItem {
  id: number;
  code: string;
  description?: string | null;
  discount_type: "PERCENT" | "FIXED";
  discount_value: string | number;
  min_order_value: string | number;
  max_discount_value?: string | number | null;
  usage_limit?: number | null;
  used_count: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  total_discount_given: string | number;
  created_at: string;
}

export interface AdminCouponCreatePayload {
  code: string;
  description?: string;
  discount_type: "PERCENT" | "FIXED";
  discount_value: number;
  min_order_value?: number;
  max_discount_value?: number;
  usage_limit?: number;
  start_date: string;
  end_date: string;
  is_active?: boolean;
}
