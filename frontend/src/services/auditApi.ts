/**
 * API client for System Audit Trails and AI Action Logs.
 */

import {
  AIActionLogListResponse,
  AuditLogListResponse,
  EmailStatusResponse,
} from '../types/audit';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export async function fetchAuditLogs(
  token: string | null,
  filters?: {
    action?: string;
    entity_type?: string;
    entity_id?: string;
    page?: number;
    limit?: number;
  }
): Promise<AuditLogListResponse> {
  const params = new URLSearchParams();
  if (filters?.action) params.append('action', filters.action);
  if (filters?.entity_type) params.append('entity_type', filters.entity_type);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.limit) params.append('limit', String(filters.limit));

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/audit/logs?${params.toString()}`, {
    method: 'GET',
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể tải nhật ký kiểm toán.');
  }

  return res.json();
}

export async function fetchAIActionLogs(
  token: string | null,
  filters?: {
    tool_name?: string;
    execution_status?: string;
    user_role?: string;
    page?: number;
    limit?: number;
  }
): Promise<AIActionLogListResponse> {
  const params = new URLSearchParams();
  if (filters?.tool_name) params.append('tool_name', filters.tool_name);
  if (filters?.execution_status) params.append('execution_status', filters.execution_status);
  if (filters?.user_role) params.append('user_role', filters.user_role);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.limit) params.append('limit', String(filters.limit));

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/audit/ai-actions?${params.toString()}`, {
    method: 'GET',
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể tải nhật ký AI Copilot.');
  }

  return res.json();
}

export async function fetchEmailStatus(token: string | null): Promise<EmailStatusResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/audit/email-status`, {
    method: 'GET',
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể kiểm tra trạng thái email.');
  }

  return res.json();
}
