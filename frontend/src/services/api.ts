import { BackendHealthResponse, DatabaseHealthResponse } from '../types/health';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function fetchBackendHealth(): Promise<{
  data: BackendHealthResponse;
  latencyMs: number;
}> {
  const startTime = performance.now();
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    headers: { Accept: 'application/json' },
  });

  const latencyMs = Math.round(performance.now() - startTime);

  if (!response.ok) {
    throw new Error(`Máy chủ backend phản hồi mã lỗi: ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Phản hồi backend không phải định dạng JSON hợp lệ (Mã: ${response.status})`);
  }

  const data: BackendHealthResponse = await response.json();
  return { data, latencyMs };
}

export async function fetchDatabaseHealth(): Promise<{
  data: DatabaseHealthResponse;
  latencyMs: number;
  isHealthy: boolean;
}> {
  const startTime = performance.now();
  const response = await fetch(`${API_BASE_URL}/api/v1/health/database`, {
    headers: { Accept: 'application/json' },
  });

  const latencyMs = Math.round(performance.now() - startTime);
  const contentType = response.headers.get('content-type') || '';

  let data: DatabaseHealthResponse;
  if (contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = {
      status: 'unhealthy',
      database: 'novelia_books',
      message: `Máy chủ phản hồi mã ${response.status}: ${response.statusText || 'Lỗi cổng kết nối'}`,
      details: { status: 'error', error_type: 'NonJsonResponse' },
      timestamp: new Date().toISOString(),
    };
  }

  if (response.status === 200 && data.status === 'healthy') {
    return { data, latencyMs, isHealthy: true };
  }

  return { data, latencyMs, isHealthy: false };
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}
