import React, { useEffect, useState, useCallback } from 'react';
import {
  ShieldAlert,
  Bot,
  Mail,
  User,
  Filter,
  Eye,
  X,
  RefreshCw,
  Lock,
} from 'lucide-react';
import { useSafeAuth } from '../context/AuthContext';
import {
  fetchAIActionLogs,
  fetchAuditLogs,
  fetchEmailStatus,
} from '../services/auditApi';
import {
  AIActionLogItem,
  AuditLogItem,
  EmailStatusResponse,
} from '../types/audit';

export const AdminAuditView: React.FC = () => {
  const { token } = useSafeAuth();

  const [activeTab, setActiveTab] = useState<'SYSTEM' | 'AI'>('SYSTEM');
  const [emailStatus, setEmailStatus] = useState<EmailStatusResponse | null>(null);

  // System Audit State
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditTotal, setAuditTotal] = useState<number>(0);
  const [auditActionFilter, setAuditActionFilter] = useState<string>('');
  const [auditPage, setAuditPage] = useState<number>(1);
  const [auditLoading, setAuditLoading] = useState<boolean>(false);

  // AI Action Log State
  const [aiLogs, setAiLogs] = useState<AIActionLogItem[]>([]);
  const [aiTotal, setAiTotal] = useState<number>(0);
  const [aiToolFilter, setAiToolFilter] = useState<string>('');
  const [aiPage, setAiPage] = useState<number>(1);
  const [aiLoading, setAiLoading] = useState<boolean>(false);

  // Detail Modal State
  const [selectedAudit, setSelectedAudit] = useState<AuditLogItem | null>(null);
  const [selectedAiAction, setSelectedAiAction] = useState<AIActionLogItem | null>(null);

  const loadEmailStatus = useCallback(async () => {
    try {
      const res = await fetchEmailStatus(token);
      setEmailStatus(res);
    } catch (err) {
      console.error('Failed to load email status:', err);
    }
  }, [token]);

  const loadAuditLogs = useCallback(async () => {
    setAuditLoading(true);
    try {
      const res = await fetchAuditLogs(token, {
        action: auditActionFilter || undefined,
        page: auditPage,
        limit: 15,
      });
      setAuditLogs(res.items);
      setAuditTotal(res.total);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setAuditLoading(false);
    }
  }, [token, auditActionFilter, auditPage]);

  const loadAiLogs = useCallback(async () => {
    setAiLoading(true);
    try {
      const res = await fetchAIActionLogs(token, {
        tool_name: aiToolFilter || undefined,
        page: aiPage,
        limit: 15,
      });
      setAiLogs(res.items);
      setAiTotal(res.total);
    } catch (err) {
      console.error('Failed to load AI action logs:', err);
    } finally {
      setAiLoading(false);
    }
  }, [token, aiToolFilter, aiPage]);

  useEffect(() => {
    loadEmailStatus();
  }, [loadEmailStatus]);

  useEffect(() => {
    if (activeTab === 'SYSTEM') {
      loadAuditLogs();
    } else {
      loadAiLogs();
    }
  }, [activeTab, loadAuditLogs, loadAiLogs]);

  const formatDateTime = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + d.toLocaleDateString('vi-VN');
    } catch {
      return iso;
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-audit-view">
      {/* Top Banner: Email Provider & Realism Status */}
      <div className="audit-panel-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-100">Cổng Dịch Vụ Email & Thông Báo</h4>
              <span
                data-testid="email-provider-badge"
                className={`text-[10px] font-extrabold px-2 py-0.5 rounded-md border ${
                  emailStatus?.is_mock
                    ? 'bg-amber-950/40 text-amber-300 border-amber-500/40'
                    : 'bg-emerald-950/40 text-emerald-300 border-emerald-500/40'
                }`}
              >
                {emailStatus?.is_mock ? 'MOCK ADAPTER (Môi trường phát triển)' : `LIVE SMTP (${emailStatus?.provider})`}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {emailStatus?.is_mock
                ? 'Hệ thống đang chạy Mock Email an toàn trong bộ nhớ; không gửi email thật ra internet.'
                : 'Kết nối SMTP hoạt động với cơ chế thử lại tự động và bảo vệ giao dịch.'}
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            loadEmailStatus();
            activeTab === 'SYSTEM' ? loadAuditLogs() : loadAiLogs();
          }}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-amber-300 text-xs font-semibold rounded-xl border border-slate-700 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Làm mới</span>
        </button>
      </div>

      {/* Main Tabs */}
      <div className="flex border-b border-slate-800 gap-4">
        <button
          data-testid="tab-system-audit"
          onClick={() => setActiveTab('SYSTEM')}
          className={`pb-3 px-1 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'SYSTEM'
              ? 'border-amber-400 text-amber-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Nhật Ký Kiểm Toán Hệ Thống ({auditTotal})</span>
        </button>

        <button
          data-testid="tab-ai-actions"
          onClick={() => setActiveTab('AI')}
          className={`pb-3 px-1 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'AI'
              ? 'border-amber-400 text-amber-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Bot className="w-4 h-4" />
          <span>Nhật Ký AI Copilot Traces ({aiTotal})</span>
        </button>
      </div>

      {/* TAB 1: SYSTEM AUDIT */}
      {activeTab === 'SYSTEM' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Filter className="w-3.5 h-3.5" />
              <span>Lọc theo thao tác:</span>
            </div>
            <select
              value={auditActionFilter}
              onChange={(e) => {
                setAuditActionFilter(e.target.value);
                setAuditPage(1);
              }}
              className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:border-amber-500"
            >
              <option value="">Tất cả thao tác</option>
              <option value="ORDER_CREATED">ORDER_CREATED</option>
              <option value="ORDER_STATUS_UPDATE">ORDER_STATUS_UPDATE</option>
              <option value="ORDER_CANCELLED">ORDER_CANCELLED</option>
              <option value="USER_ROLE_CHANGE">USER_ROLE_CHANGE</option>
              <option value="USER_STATUS_CHANGE">USER_STATUS_CHANGE</option>
              <option value="COUPON_CREATE">COUPON_CREATE</option>
              <option value="COUPON_TOGGLE">COUPON_TOGGLE</option>
              <option value="SHIPMENT_EVENT">SHIPMENT_EVENT</option>
            </select>
          </div>

          {/* Audit Logs Table */}
          <div className="audit-panel-card">
            <div className="overflow-x-auto">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Thời gian</th>
                    <th>Người thực hiện</th>
                    <th>Hành động</th>
                    <th>Đối tượng</th>
                    <th>Mã thực thể</th>
                    <th className="text-right">Chi tiết</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {auditLoading ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-slate-500">
                        Đang tải nhật ký kiểm toán...
                      </td>
                    </tr>
                  ) : auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-slate-500">
                        Không có dữ liệu nhật ký kiểm toán phù hợp.
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-900/40 transition-colors">
                        <td className="p-3.5 whitespace-nowrap text-slate-400">
                          {formatDateTime(log.created_at)}
                        </td>
                        <td className="p-3.5">
                          <div className="flex items-center gap-1.5">
                            <User className="w-3.5 h-3.5 text-slate-500" />
                            <span className="font-semibold text-slate-200">
                              {log.user_email || 'Hệ thống tự động'}
                            </span>
                            {log.user_role && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] bg-slate-800 text-amber-300 border border-slate-700">
                                {log.user_role}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-3.5">
                          <span className="font-mono text-amber-300 font-bold">
                            {log.action}
                          </span>
                        </td>
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                            {log.entity_type}
                          </span>
                        </td>
                        <td className="p-3.5 font-mono text-slate-400">
                          {log.entity_id || '—'}
                        </td>
                        <td className="p-3.5 text-right">
                          <button
                            onClick={() => setSelectedAudit(log)}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 hover:text-amber-200 transition-colors inline-flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Xem</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: AI ACTIONS */}
      {activeTab === 'AI' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Filter className="w-3.5 h-3.5" />
              <span>Lọc theo công cụ AI:</span>
            </div>
            <select
              value={aiToolFilter}
              onChange={(e) => {
                setAiToolFilter(e.target.value);
                setAiPage(1);
              }}
              className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:border-amber-500"
            >
              <option value="">Tất cả công cụ</option>
              <option value="get_sales_summary">get_sales_summary</option>
              <option value="get_inventory_summary">get_inventory_summary</option>
              <option value="find_low_stock_books">find_low_stock_books</option>
              <option value="prepare_book_update">prepare_book_update</option>
              <option value="prepare_inventory_adjustment">prepare_inventory_adjustment</option>
              <option value="draft_promotion">draft_promotion</option>
            </select>
          </div>

          {/* AI Logs Table */}
          <div className="audit-panel-card">
            <div className="overflow-x-auto">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Thời gian</th>
                    <th>Người gọi</th>
                    <th>Công cụ AI</th>
                    <th>Trạng thái</th>
                    <th>Xác nhận Gate</th>
                    <th>Thời gian chạy</th>
                    <th className="text-right">Chi tiết</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {aiLoading ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">
                        Đang tải nhật ký AI Copilot...
                      </td>
                    </tr>
                  ) : aiLogs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">
                        Không có dữ liệu nhật ký AI Copilot.
                      </td>
                    </tr>
                  ) : (
                    aiLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-900/40 transition-colors">
                        <td className="p-3.5 whitespace-nowrap text-slate-400">
                          {formatDateTime(log.created_at)}
                        </td>
                        <td className="p-3.5">
                          <span className="font-semibold text-slate-200">
                            {log.user_email || 'Ẩn danh'}
                          </span>
                          <span className="ml-1.5 px-1.5 py-0.5 rounded text-[9px] bg-slate-800 text-amber-300">
                            {log.user_role}
                          </span>
                        </td>
                        <td className="p-3.5 font-mono text-amber-300 font-bold">
                          {log.tool_name}
                        </td>
                        <td className="p-3.5">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                              log.execution_status === 'SUCCESS'
                                ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30'
                                : log.execution_status === 'CONFIRMATION_REQUIRED'
                                ? 'bg-amber-950/40 text-amber-300 border-amber-500/30'
                                : 'bg-rose-950/40 text-rose-300 border-rose-500/30'
                            }`}
                          >
                            {log.execution_status}
                          </span>
                        </td>
                        <td className="p-3.5">
                          {log.confirmation_token ? (
                            <span className="text-[10px] text-slate-400">
                              {log.is_confirmed ? 'Đã commit' : 'Chờ xác nhận'}
                            </span>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="p-3.5 font-mono text-slate-400">
                          {log.execution_duration_ms ? `${log.execution_duration_ms} ms` : '—'}
                        </td>
                        <td className="p-3.5 text-right">
                          <button
                            onClick={() => setSelectedAiAction(log)}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 hover:text-amber-200 transition-colors inline-flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Xem</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Audit Log Detail */}
      {selectedAudit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl bg-slate-900 border border-amber-500/30 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="font-bold text-sm text-slate-100">
                  Chi Tiết Nhật Ký #{selectedAudit.id} — {selectedAudit.action}
                </h3>
              </div>
              <button
                onClick={() => setSelectedAudit(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-4 text-xs">
              {/* Privacy protection badge */}
              <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 flex items-center gap-2 text-[11px]">
                <Lock className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  Bảo vệ dữ liệu nhạy cảm: Mọi thông tin xác thực, mật khẩu, token và thông tin thẻ đều được tự động che chắn (Redacted) trước khi lưu.
                </span>
              </div>

              <div>
                <span className="text-slate-400 block mb-1">Dữ liệu mới (New Values):</span>
                <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-amber-300/90 overflow-x-auto">
                  {JSON.stringify(selectedAudit.new_values, null, 2) || 'Không có'}
                </pre>
              </div>

              {selectedAudit.old_values && (
                <div>
                  <span className="text-slate-400 block mb-1">Dữ liệu cũ (Old Values):</span>
                  <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400 overflow-x-auto">
                    {JSON.stringify(selectedAudit.old_values, null, 2)}
                  </pre>
                </div>
              )}

              <div className="pt-2 border-t border-slate-800 flex justify-between text-[11px] text-slate-500">
                <span>IP: {selectedAudit.ip_address || '127.0.0.1'}</span>
                <span>{formatDateTime(selectedAudit.created_at)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: AI Action Log Detail */}
      {selectedAiAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl bg-slate-900 border border-amber-500/30 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-amber-400" />
                <h3 className="font-bold text-sm text-slate-100">
                  Chi Tiết Lệnh AI #{selectedAiAction.id} — {selectedAiAction.tool_name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedAiAction(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-4 text-xs">
              <div>
                <span className="text-slate-400 block mb-1">Tham số đầu vào (Input Arguments):</span>
                <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-amber-300 overflow-x-auto">
                  {JSON.stringify(selectedAiAction.input_arguments, null, 2)}
                </pre>
              </div>

              {selectedAiAction.output_summary && (
                <div>
                  <span className="text-slate-400 block mb-1">Tóm tắt kết quả (Output Summary):</span>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 leading-relaxed">
                    {selectedAiAction.output_summary}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
