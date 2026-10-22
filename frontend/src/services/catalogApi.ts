/**
 * Catalog API Service handling all storefront queries, filters, and product details.
 */

import { getApiBaseUrl } from './api';
import {
  Author,
  BookDetail,
  BookFilterState,
  BookSummary,
  Category,
  PaginatedBooks,
  Publisher,
} from '../types/catalog';

export function formatVND(amount: number | string): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '0 ₫';
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(num);
}

export async function fetchBooks(
  filters: Partial<BookFilterState> = {}
): Promise<PaginatedBooks> {
  const baseUrl = getApiBaseUrl();
  const params = new URLSearchParams();

  if (filters.query?.trim()) params.append('query', filters.query.trim());
  if (filters.category_slug) params.append('category_slug', filters.category_slug);
  if (filters.category_id) params.append('category_id', String(filters.category_id));
  if (filters.author_id) params.append('author_id', String(filters.author_id));
  if (filters.publisher_id) params.append('publisher_id', String(filters.publisher_id));
  if (filters.min_price !== undefined) params.append('min_price', String(filters.min_price));
  if (filters.max_price !== undefined) params.append('max_price', String(filters.max_price));
  if (filters.cover_type) params.append('cover_type', filters.cover_type);
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.page) params.append('page', String(filters.page));
  if (filters.page_size) params.append('page_size', String(filters.page_size));

  const queryString = params.toString();
  const url = `${baseUrl}/api/v1/catalog/books${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Lỗi tải danh mục sách: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  if (!data || !Array.isArray(data.items)) {
    return { items: [], total: 0, page: 1, page_size: 12, total_pages: 0 };
  }
  return data;
}

export async function fetchBookDetail(
  slugOrId: string | number
): Promise<BookDetail> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/api/v1/catalog/books/${slugOrId}`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Sách này không tồn tại hoặc đã ngừng kinh doanh.');
    }
    throw new Error(`Lỗi tải chi tiết sách: ${response.status}`);
  }

  return response.json();
}

export async function fetchFeaturedBooks(limit: number = 8): Promise<BookSummary[]> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/api/v1/catalog/books/featured?limit=${limit}`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    return [];
  }

  const data = await response.json();
  return Array.isArray(data) ? data : [];
}

export async function fetchRelatedBooks(
  bookId: number,
  limit: number = 4
): Promise<BookSummary[]> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(
    `${baseUrl}/api/v1/catalog/books/${bookId}/related?limit=${limit}`,
    {
      headers: { Accept: 'application/json' },
    }
  );

  if (!response.ok) {
    return [];
  }

  const data = await response.json();
  return Array.isArray(data) ? data : [];
}

export async function fetchCategories(asTree: boolean = true): Promise<Category[]> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(
    `${baseUrl}/api/v1/catalog/categories?as_tree=${asTree}`,
    {
      headers: { Accept: 'application/json' },
    }
  );

  if (!response.ok) {
    return [];
  }

  const data = await response.json();
  return Array.isArray(data) ? data : [];
}


export async function fetchAuthors(query?: string): Promise<Author[]> {
  const baseUrl = getApiBaseUrl();
  const q = query ? `?query=${encodeURIComponent(query)}` : '';
  const response = await fetch(`${baseUrl}/api/v1/catalog/authors${q}`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Lỗi tải tác giả: ${response.status}`);
  }

  return response.json();
}

export async function fetchPublishers(): Promise<Publisher[]> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/api/v1/catalog/publishers`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Lỗi tải nhà xuất bản: ${response.status}`);
  }

  return response.json();
}
