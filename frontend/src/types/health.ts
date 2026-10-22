export interface BackendHealthResponse {
  status: 'healthy' | 'unhealthy';
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface DatabaseHealthDetails {
  [key: string]: unknown;
  database?: string;
  host?: string;
  port?: number;
  status?: string;
  error_type?: string;
}

export interface DatabaseHealthResponse {
  status: 'healthy' | 'unhealthy';
  database: string;
  message: string;
  details: DatabaseHealthDetails;
  timestamp: string;
}

export interface ServiceState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastChecked: Date | null;
  latencyMs: number | null;
}
