/**
 * API client for Novelia AI Assistant endpoints.
 */

import { getApiBaseUrl } from './api';
import { AIChatResponse, AIConfirmResponse, AIHealthStatus, AIMessageItem } from '../types/ai';

export async function sendAIChat(
  token: string | null,
  message: string,
  sessionUuid?: string
): Promise<AIChatResponse> {
  const baseUrl = getApiBaseUrl();
  const headers: HeadersInit = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${baseUrl}/api/v1/ai/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      session_uuid: sessionUuid,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi AI Assistant (${res.status})`);
  }

  return res.json();
}

export async function fetchAIHealth(): Promise<AIHealthStatus> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/ai/health`, {
    headers: { Accept: 'application/json' },
  });

  if (!res.ok) {
    throw new Error(`Lỗi kiểm tra AI Health (${res.status})`);
  }

  return res.json();
}

export async function fetchAIConversationHistory(
  token: string | null,
  sessionUuid: string
): Promise<AIMessageItem[]> {
  const baseUrl = getApiBaseUrl();
  const headers: HeadersInit = {
    Accept: 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${baseUrl}/api/v1/ai/conversations/${encodeURIComponent(sessionUuid)}`, {
    headers,
  });

  if (!res.ok) {
    return [];
  }

  return res.json();
}

export async function confirmAIAction(
  token: string | null,
  confirmationToken: string
): Promise<AIConfirmResponse> {
  const baseUrl = getApiBaseUrl();
  const headers: HeadersInit = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${baseUrl}/api/v1/ai/confirm`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      confirmation_token: confirmationToken,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi xác nhận hành động (${res.status})`);
  }

  return res.json();
}

