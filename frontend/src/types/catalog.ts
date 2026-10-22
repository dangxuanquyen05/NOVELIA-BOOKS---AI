/**
 * TypeScript types for Book Catalog, Filtering, Categories, and Storefront.
 */

export interface Publisher {
  id: number;
  name: string;
  slug: string;
  contact_info?: string | null;
  address?: string | null;
  website?: string | null;
  created_at: string;
}

export interface Author {
  id: number;
  name: string;
  slug: string;
  bio?: string | null;
  avatar_url?: string | null;
  birth_year?: number | null;
  nationality?: string | null;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  parent_id?: number | null;
  display_order: number;
  created_at: string;
  book_count?: number;
  subcategories?: Category[];
}

export interface BookAuthor {
  author_id: number;
  name: string;
  slug: string;
  is_primary: boolean;
  order_index: number;
}

export interface BookCategory {
  category_id: number;
  name: string;
  slug: string;
}

export interface BookImage {
  id: number;
  image_url: string;
  alt_text?: string | null;
  display_order: number;
  is_cover: boolean;
}

export interface BookSummary {
  id: number;
  isbn: string;
  sku: string;
  title: string;
  slug: string;
  price: string | number;
  original_price: string | number;
  discount_percent: number;
  cover_image_url: string;
  cover_type: 'PAPERBACK' | 'HARDCOVER' | string;
  status: 'ACTIVE' | 'DRAFT' | 'OUT_OF_STOCK' | 'DISCONTINUED' | string;
  primary_author?: string | null;
  authors: BookAuthor[];
  categories: BookCategory[];
  stock_available: number;
  is_in_stock: boolean;
  created_at: string;
}

export interface BookDetail extends BookSummary {
  publisher?: Publisher | null;
  page_count?: number | null;
  dimension?: string | null;
  weight_grams: number;
  description?: string | null;
  sample_text?: string | null;
  published_date?: string | null;
  images: BookImage[];
  updated_at: string;
}

export interface BookFilterState {
  query?: string;
  category_slug?: string;
  category_id?: number;
  author_id?: number;
  publisher_id?: number;
  min_price?: number;
  max_price?: number;
  cover_type?: string;
  sort_by?: 'newest' | 'price_asc' | 'price_desc' | 'title_asc' | 'title_desc' | 'discount_desc' | string;
  page: number;
  page_size: number;
}

export interface PaginatedBooks {
  items: BookSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
