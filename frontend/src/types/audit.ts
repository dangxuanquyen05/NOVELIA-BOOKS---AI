/**
 * Audit and Governance TypeScript interfaces for Novelia Books.
 */

export interface AuditLogItem {
  id: number;
  user_id?: number | null;
  user_email?: string | null;
  user_role?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  old_values?: Record<string, unknown> | null;
  new_values?: Record<string, unknown> | null;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  limit: number;
}

export interface AIActionLogItem {
  id: number;
  conversation_id?: number | null;
  user_id?: number | null;
  user_email?: string | null;
  user_role: string;
  tool_name: string;
  input_arguments: Record<string, unknown>;
  execution_status: string;
  confirmation_token?: string | null;
  is_confirmed: boolean;
  output_summary?: string | null;
  execution_duration_ms?: number | null;
  created_at: string;
}

export interface AIActionLogListResponse {
  items: AIActionLogItem[];
  total: number;
  page: number;
  limit: number;
}

export interface EmailStatusResponse {
  provider: string;
  is_mock: boolean;
  status: string;
  details: Record<string, unknown>;
}
