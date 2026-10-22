/**
 * API client methods for BookMatch AI personalized recommendations.
 */

import { getApiBaseUrl } from './api';
import {
  BaselineComparisonResponse,
  BookMatchResponse,
  BookRecommendationItem,
  RecommendationEventCreate,
} from '../types/recommendation';

const API_BASE = getApiBaseUrl();

/**
 * Fetch personalized recommendations (or cold-start for guests/new users).
 */
export async function fetchPersonalizedRecommendations(
  token?: string | null,
  limit: number = 6,
  categorySlug?: string
): Promise<BookMatchResponse> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (categorySlug) {
    params.append('category_slug', categorySlug);
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/api/v1/recommendations/personalized?${params.toString()}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể tải gợi ý cá nhân hóa từ BookMatch AI.');
  }

  return response.json();
}

/**
 * Fetch unpersonalized popularity baseline recommendations for evaluation comparison.
 */
export async function fetchBaselineRecommendations(limit: number = 6): Promise<BookRecommendationItem[]> {
  const response = await fetch(`${API_BASE}/api/v1/recommendations/baseline?limit=${limit}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error('Không thể tải danh sách gợi ý baseline.');
  }

  return response.json();
}

/**
 * Fetch comparison metrics between BookMatch AI and popularity baseline.
 */
export async function fetchRecommendationEvaluation(
  token?: string | null
): Promise<BaselineComparisonResponse> {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/api/v1/recommendations/evaluation`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error('Không thể tải báo cáo đánh giá chất lượng gợi ý.');
  }

  return response.json();
}

/**
 * Log user interaction event (telemetry).
 */
export async function sendRecommendationEvent(
  token: string | null | undefined,
  event: RecommendationEventCreate
): Promise<Record<string, unknown>> {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/api/v1/recommendations/events`, {
    method: 'POST',
    headers,
    body: JSON.stringify(event),
  });

  if (!response.ok) {
    console.warn('Failed to log recommendation event');
  }

  return response.json().catch(() => ({}));
}
