import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  X,
  Send,
  Sparkles,
  ShoppingBag,
  Package,
  Truck,
  RotateCcw,
  ChevronRight,
  Plus,
  ShieldAlert,
  CheckCircle2,
  BarChart3,
  Boxes,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCommerce } from '../context/CommerceContext';
import { confirmAIAction, fetchAIHealth, sendAIChat } from '../services/aiApi';
import {
  AIBookItem,
  AIHealthStatus,
  AIMessageItem,
  AIOrderItem,
} from '../types/ai';

interface NoveliaAIAssistantProps {
  onSelectBook?: (bookId: number) => void;
}

const DEFAULT_SUGGESTIONS = [
  '📚 Gợi ý sách kinh tế nổi bật',
  '🔍 Tìm sách kỹ năng dưới 150k',
  '📦 Kiểm tra đơn hàng của tôi',
  '🚚 Phí vận chuyển và giao hàng',
];

const ADMIN_SUGGESTIONS = [
  '📊 Báo cáo doanh thu & KPI',
  '📦 Tồn kho toàn hệ thống',
  '⚠️ Danh sách sách sắp hết hàng',
  '📋 Tra cứu đơn hàng gần đây',
];

export const NoveliaAIAssistant: React.FC<NoveliaAIAssistantProps> = ({ onSelectBook }) => {
  const { token, isAuthenticated, user } = useAuth();
  const { addToCart, openCart, refreshCart } = useCommerce();

  const isStaffOrAdmin = Boolean(
    user?.roles && user.roles.some((r: string) => ['STAFF', 'ADMIN'].includes(r.toUpperCase()))
  );

  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [sessionUuid, setSessionUuid] = useState<string>(() => {
    return localStorage.getItem('novelia_ai_session_uuid') || `nvl_sess_${Date.now()}`;
  });
  const [health, setHealth] = useState<AIHealthStatus | null>(null);
  const [messages, setMessages] = useState<AIMessageItem[]>([
    {
      id: 'welcome',
      sender: 'ASSISTANT',
      content: isStaffOrAdmin
        ? 'Dạ chào Quản trị viên! Em là Novelia AI Admin Copilot — Trợ lý vận hành thông minh của NOVELIA BOOKS.\n\nEm có thể hỗ trợ tra cứu KPI doanh thu, kiểm tra tồn kho toàn hệ thống, tìm đơn hàng, hoặc tạo bản xem trước sửa giá sách / điều chỉnh kho.'
        : 'Dạ chào Quý khách! Em là Novelia AI — Chuyên viên tư vấn sách và hỗ trợ mua sắm thông minh của NOVELIA BOOKS.\n\nEm có thể giúp Quý khách tìm sách theo ngân sách, kiểm tra tồn kho thời gian thực, thêm sách vào giỏ hoặc tra cứu đơn hàng cá nhân.',
      created_at: new Date().toISOString(),
    },
  ]);
  const [inputValue, setInputValue] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>(
    isStaffOrAdmin ? ADMIN_SUGGESTIONS : DEFAULT_SUGGESTIONS
  );
  const [addingBookId, setAddingBookId] = useState<number | null>(null);
  const [confirmedTokens, setConfirmedTokens] = useState<Set<string>>(new Set());
  const [confirmingToken, setConfirmingToken] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Load AI Provider Health
  useEffect(() => {
    fetchAIHealth()
      .then((data) => setHealth(data))
      .catch(() => {
        setHealth({
          status: 'UNAVAILABLE',
          provider: 'unknown',
          model: 'offline',
          is_configured: false,
          details: 'Không thể kết nối đến máy chủ AI backend.',
        });
      });
  }, []);

  // Save session UUID
  useEffect(() => {
    localStorage.setItem('novelia_ai_session_uuid', sessionUuid);
  }, [sessionUuid]);

  // Scroll to bottom when messages update
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    setErrorNotice(null);
    setInputValue('');

    const userMsg: AIMessageItem = {
      id: `usr_${Date.now()}`,
      sender: 'USER',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const resp = await sendAIChat(token, text, sessionUuid);
      setSessionUuid(resp.session_uuid);

      const assistantMsg: AIMessageItem = {
        id: `asst_${Date.now()}`,
        sender: 'ASSISTANT',
        content: resp.message,
        structured_payload: resp.structured_payload,
        created_at: resp.created_at,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      if (resp.suggested_prompts && resp.suggested_prompts.length > 0) {
        setSuggestedPrompts(resp.suggested_prompts);
      }

      // If cart was modified by backend tool, trigger commerce cart refresh
      if (resp.structured_payload?.cart_update?.success) {
        refreshCart();
      }
    } catch (err: unknown) {
      const errText = err instanceof Error ? err.message : 'Không thể kết nối tới máy chủ AI';
      setErrorNotice(errText);
      const fallbackMsg: AIMessageItem = {
        id: `err_${Date.now()}`,
        sender: 'ASSISTANT',
        content: `⚠️ Đã xảy ra lỗi: ${errText}. Quý khách vui lòng thử lại sau ít phút hoặc sử dụng thanh tìm kiếm trực tiếp.`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAdd = async (bookId: number) => {
    if (!isAuthenticated) {
      setErrorNotice('Quý khách vui lòng đăng nhập để thêm sách vào giỏ hàng.');
      return;
    }
    setAddingBookId(bookId);
    try {
      await addToCart(bookId, 1);
      const confirmMsg: AIMessageItem = {
        id: `cart_add_${Date.now()}`,
        sender: 'ASSISTANT',
        content: '🎉 Đã thêm sản phẩm vào giỏ hàng thành công! Quý khách có thể mở giỏ hàng để tiến hành thanh toán.',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, confirmMsg]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Không thể thêm vào giỏ hàng.';
      setErrorNotice(msg);
    } finally {
      setAddingBookId(null);
    }
  };

  useEffect(() => {
    if (isStaffOrAdmin) {
      setSuggestedPrompts(ADMIN_SUGGESTIONS);
    } else {
      setSuggestedPrompts(DEFAULT_SUGGESTIONS);
    }
  }, [isStaffOrAdmin]);

  const handleConfirmAction = async (confirmToken: string) => {
    setConfirmingToken(confirmToken);
    setErrorNotice(null);
    try {
      const res = await confirmAIAction(token, confirmToken);
      setConfirmedTokens((prev) => new Set(prev).add(confirmToken));
      const ackMsg: AIMessageItem = {
        id: `ack_${Date.now()}`,
        sender: 'ASSISTANT',
        content: `✅ **Xác nhận thực thi thành công**:\n${res.message}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, ackMsg]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Lỗi khi xác nhận thao tác.';
      setErrorNotice(msg);
    } finally {
      setConfirmingToken(null);
    }
  };

  const handleClearSession = () => {
    const newUuid = `nvl_sess_${Date.now()}`;
    setSessionUuid(newUuid);
    setMessages([
      {
        id: 'welcome',
        sender: 'ASSISTANT',
        content: isStaffOrAdmin
          ? 'Phiên làm việc Admin Copilot đã được làm mới. Quản trị viên cần hỗ trợ số liệu nào tiếp theo ạ?'
          : 'Cuộc trò chuyện đã được làm mới. Em có thể hỗ trợ gì cho Quý khách hôm nay ạ?',
        created_at: new Date().toISOString(),
      },
    ]);
    setSuggestedPrompts(isStaffOrAdmin ? ADMIN_SUGGESTIONS : DEFAULT_SUGGESTIONS);
  };

  const renderStatusBadge = () => {
    if (isStaffOrAdmin) {
      return (
        <span className="novelia-ai-badge novelia-ai-badge-admin">
          <ShieldAlert size={12} />
          Admin Copilot
        </span>
      );
    }
    if (!health) return null;
    if (health.status === 'CONFIGURED') {
      return (
        <span className="novelia-ai-badge novelia-ai-badge-gemini">
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#34D399', display: 'inline-block' }} />
          Gemini AI
        </span>
      );
    }
    if (health.status === 'MOCK_READY') {
      return (
        <span className="novelia-ai-badge novelia-ai-badge-mock">
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#38BDF8', display: 'inline-block' }} />
          Novelia AI (Mock)
        </span>
      );
    }
    return (
      <span className="novelia-ai-badge novelia-ai-badge-fallback">
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#FBBF24', display: 'inline-block' }} />
        Chế độ Fallback Ngoại tuyến
      </span>
    );
  };

  const renderInlineMarkdown = (text: string) => {
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*.*?\*\*|\[.*?\]\(.*?\))/g;
    let lastIdx = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIdx) {
        parts.push(text.substring(lastIdx, match.index));
      }
      const token = match[0];
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={match.index} style={{ fontWeight: 700, color: '#FDE68A' }}>
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('[') && token.includes('](')) {
        const linkMatch = token.match(/\[(.*?)\]\((.*?)\)/);
        if (linkMatch) {
          parts.push(
            <a
              key={match.index}
              href={linkMatch[2]}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#F59E0B', textDecoration: 'underline', fontWeight: 600 }}
            >
              {linkMatch[1]}
            </a>
          );
        }
      }
      lastIdx = regex.lastIndex;
    }
    if (lastIdx < text.length) {
      parts.push(text.substring(lastIdx));
    }
    return parts;
  };

  const renderFormattedContent = (content: string, onAction: (query: string) => void) => {
    const lines = content.split('\n');
    return lines.map((line, lIdx) => {
      // 1. Choice card: [choice:Title|Desc|Icon](query) or [choice:Title|Desc](query)
      const choiceMatch = line.match(/^\[choice:([^|]+)\|([^|]+)(?:\|([^\]]+))?\]\(([^)]+)\)$/);
      if (choiceMatch) {
        const title = choiceMatch[1].trim();
        const desc = choiceMatch[2].trim();
        const icon = (choiceMatch[3] || '⚡').trim();
        const query = choiceMatch[4].trim();
        return (
          <button
            key={lIdx}
            type="button"
            onClick={() => onAction(query)}
            className="novelia-ai-choice-card"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
              <div className="novelia-ai-choice-icon">
                {icon}
              </div>
              <div className="novelia-ai-choice-content">
                <div className="novelia-ai-choice-title">
                  {title}
                </div>
                <div className="novelia-ai-choice-desc">
                  {desc}
                </div>
              </div>
            </div>
            <div className="novelia-ai-choice-arrow">
              <ChevronRight size={16} />
            </div>
          </button>
        );
      }

      // 2. Button card: [button:Label](query)
      const buttonMatch = line.match(/^\[button:([^\]]+)\]\(([^)]+)\)$/);
      if (buttonMatch) {
        const label = buttonMatch[1].trim();
        const query = buttonMatch[2].trim();
        return (
          <button
            key={lIdx}
            type="button"
            onClick={() => onAction(query)}
            className="novelia-ai-action-btn"
          >
            <span>{label}</span>
            <ChevronRight size={13} />
          </button>
        );
      }

      // 3. Image: ![Alt](url)
      const imgMatch = line.match(/!\[(.*?)\]\(([^)]+)\)/);
      if (imgMatch) {
        const alt = imgMatch[1];
        const url = imgMatch[2];
        return (
          <div key={lIdx} className="novelia-ai-qr-wrap">
            <div className="novelia-ai-qr-card">
              <img src={url} alt={alt} />
            </div>
            {alt && <div className="novelia-ai-qr-caption">{alt}</div>}
          </div>
        );
      }

      // 4. Regular line
      return (
        <div key={lIdx} style={{ minHeight: line.trim() === '' ? 8 : 16 }}>
          {renderInlineMarkdown(line)}
        </div>
      );
    });
  };

  return (
    <>
      {/* Floating Trigger Button V3 */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Mở Trợ lý Novelia AI"
        className="novelia-ai-trigger-fab-v3"
        title="Novelia AI Assistant"
      >
        <div className="novelia-ai-fab-circle">
          <Bot size={22} className="novelia-ai-fab-icon" />
          <span className="novelia-ai-pulse-dot" />
        </div>
        <span className="novelia-ai-fab-caption">
          Novelia AI
        </span>
      </button>

      {/* Floating Chat Modal */}
      {isOpen && (
        <div className="novelia-ai-modal">
          {/* Header */}
          <div className="novelia-ai-header">
            <div className="novelia-ai-brand">
              <div className="novelia-ai-avatar">
                <Bot size={22} />
              </div>
              <div className="novelia-ai-title-group">
                <div className="novelia-ai-header-title">
                  <span>Novelia AI Assistant</span>
                  {renderStatusBadge()}
                </div>
                <div className="novelia-ai-header-sub">Tư vấn chọn sách &amp; tra cứu đơn hàng</div>
              </div>
            </div>

            <div className="novelia-ai-header-actions">
              <button
                onClick={handleClearSession}
                title="Làm mới cuộc trò chuyện"
                className="novelia-ai-icon-btn"
              >
                <RotateCcw size={15} />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Thu nhỏ"
                className="novelia-ai-icon-btn"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="novelia-ai-messages">
            {messages.map((msg, idx) => (
              <div
                key={msg.id || idx}
                className={`novelia-ai-turn ${msg.sender === 'USER' ? 'user' : 'assistant'}`}
              >
                {msg.sender === 'ASSISTANT' && (
                  <div className="novelia-ai-msg-avatar">
                    <Sparkles size={14} />
                  </div>
                )}

                <div
                  className={msg.sender === 'USER' ? 'novelia-ai-bubble-user' : 'novelia-ai-bubble-assistant'}
                >
                  {msg.sender === 'USER' ? (
                    <p style={{ margin: 0, whiteSpace: 'pre-line' }}>{msg.content}</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {renderFormattedContent(msg.content, (query) => handleSendMessage(query))}
                    </div>
                  )}

                  {/* Structured Books Widget */}
                  {msg.structured_payload?.books && msg.structured_payload.books.length > 0 && (
                    <div className="novelia-ai-widget-sec">
                      <div className="novelia-ai-widget-title" style={{ color: '#FBBF24' }}>
                        <ShoppingBag size={14} /> Tác phẩm phù hợp:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {msg.structured_payload.books.map((b: AIBookItem) => (
                          <div key={b.id} className="novelia-ai-book-card">
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                              {b.cover_image_url ? (
                                <img
                                  src={b.cover_image_url}
                                  alt={b.title}
                                  className="novelia-ai-book-thumb"
                                />
                              ) : (
                                <div className="novelia-ai-book-thumb-empty">Bìa</div>
                              )}
                              <div className="novelia-ai-book-info">
                                <div className="novelia-ai-book-name">{b.title}</div>
                                <div className="novelia-ai-book-author">{b.primary_author || 'Nhiều tác giả'}</div>
                                <div className="novelia-ai-book-price">
                                  {b.price.toLocaleString('vi-VN')} đ
                                </div>
                              </div>
                            </div>

                            <div className="novelia-ai-book-actions">
                              <button
                                onClick={() => handleQuickAdd(b.id)}
                                disabled={addingBookId === b.id}
                                className="novelia-ai-add-cart-btn"
                              >
                                <Plus size={12} />
                                {addingBookId === b.id ? 'Đang thêm...' : 'Thêm giỏ'}
                              </button>
                              {onSelectBook && (
                                <button
                                  onClick={() => onSelectBook(b.id)}
                                  className="novelia-ai-detail-link"
                                >
                                  Chi tiết <ChevronRight size={12} />
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Structured Orders Widget */}
                  {msg.structured_payload?.orders && msg.structured_payload.orders.length > 0 && (
                    <div className="novelia-ai-widget-sec">
                      <div className="novelia-ai-widget-title" style={{ color: '#38BDF8' }}>
                        <Package size={14} /> Đơn hàng gần đây:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {msg.structured_payload.orders.map((o: AIOrderItem) => (
                          <div
                            key={o.order_code}
                            style={{
                              padding: '8px 10px',
                              borderRadius: 10,
                              background: 'rgba(10, 18, 41, 0.9)',
                              border: '1px solid rgba(255, 255, 255, 0.08)',
                              fontSize: '0.74rem'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#FBBF24' }}>{o.order_code}</span>
                              <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: '0.66rem', fontWeight: 600, background: 'rgba(255, 255, 255, 0.06)', color: '#FDE68A' }}>
                                {o.status}
                              </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8', fontSize: '0.68rem', marginTop: 4 }}>
                              <span>{o.item_count} cuốn • {o.total_amount.toLocaleString('vi-VN')} đ</span>
                              <span>{o.created_at}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Structured Tracking Widget */}
                  {msg.structured_payload?.tracking && (
                    <div className="novelia-ai-widget-sec">
                      <div className="novelia-ai-widget-title" style={{ color: '#34D399' }}>
                        <Truck size={14} /> Vận đơn {msg.structured_payload.tracking.order_code}:
                      </div>
                      <div style={{ padding: '10px', borderRadius: 10, background: 'rgba(10, 18, 41, 0.9)', border: '1px solid rgba(16, 185, 129, 0.3)', fontSize: '0.74rem', display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94A3B8' }}>Đơn vị vận chuyển:</span>
                          <span style={{ fontWeight: 700, color: '#34D399' }}>{msg.structured_payload.tracking.carrier}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94A3B8' }}>Mã vận đơn:</span>
                          <span style={{ fontFamily: 'monospace', color: '#FBBF24' }}>{msg.structured_payload.tracking.tracking_code || 'Đang cập nhật'}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94A3B8' }}>Trạng thái:</span>
                          <span style={{ color: '#FDE68A', fontWeight: 600 }}>{msg.structured_payload.tracking.shipment_status}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Structured Cart Update Widget */}
                  {msg.structured_payload?.cart_update && (
                    <div className="novelia-ai-widget-sec" style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.74rem', color: '#34D399', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <ShoppingBag size={14} /> {msg.structured_payload.cart_update.message}
                      </span>
                      <button
                        onClick={openCart}
                        className="novelia-ai-action-btn"
                        style={{ margin: 0, padding: '4px 10px' }}
                      >
                        Xem giỏ hàng
                      </button>
                    </div>
                  )}

                  {/* Two-Phase Confirmation Widget */}
                  {msg.structured_payload?.confirmation && (
                    <div className="novelia-ai-widget-sec">
                      <div className="novelia-ai-confirm-box">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, color: '#FBBF24' }}>
                          <ShieldAlert size={14} /> Xác nhận thao tác Quản trị viên (Two-Phase Gate)
                        </div>
                        <div style={{ color: '#E2E8F0' }}>
                          {msg.structured_payload.confirmation.message}
                        </div>
                        <div style={{ padding: 8, borderRadius: 6, background: 'rgba(0,0,0,0.4)', fontFamily: 'monospace', fontSize: '0.68rem', display: 'flex', flexDirection: 'column', gap: 3 }}>
                          {msg.structured_payload.confirmation.action_type === 'ADJUST_INVENTORY' && (
                            <>
                              <div>Biến động: <span style={{ color: '#FBBF24', fontWeight: 700 }}>{(msg.structured_payload.confirmation.preview?.delta ?? 0) > 0 ? `+${msg.structured_payload.confirmation.preview?.delta}` : msg.structured_payload.confirmation.preview?.delta} cuốn</span></div>
                              <div>Tồn vật lý: {msg.structured_payload.confirmation.preview?.current_physical_stock} ➔ <span style={{ color: '#34D399', fontWeight: 700 }}>{msg.structured_payload.confirmation.preview?.proposed_physical_stock} cuốn</span></div>
                              <div>Tồn khả dụng: {msg.structured_payload.confirmation.preview?.current_available_stock} ➔ <span style={{ color: '#34D399', fontWeight: 700 }}>{msg.structured_payload.confirmation.preview?.proposed_available_stock} cuốn</span></div>
                              <div>Lý do: <span style={{ color: '#94A3B8' }}>{msg.structured_payload.confirmation.preview?.reason}</span></div>
                            </>
                          )}
                          {msg.structured_payload.confirmation.action_type === 'UPDATE_BOOK' && (
                            <>
                              <div>Tựa đề: <span style={{ color: '#FDE68A' }}>{msg.structured_payload.confirmation.preview?.proposed_title}</span></div>
                              <div>Giá bán mới: <span style={{ color: '#34D399', fontWeight: 700 }}>{Number(msg.structured_payload.confirmation.preview?.proposed_price ?? 0).toLocaleString('vi-VN')} đ</span> (Cũ: {Number(msg.structured_payload.confirmation.preview?.current_price ?? 0).toLocaleString('vi-VN')} đ)</div>
                              <div>Trạng thái: <span style={{ color: '#FBBF24' }}>{msg.structured_payload.confirmation.preview?.proposed_status}</span></div>
                            </>
                          )}
                          {msg.structured_payload.confirmation.action_type === 'CREATE_COUPON' && (
                            <>
                              <div>Mã giảm giá: <span style={{ color: '#FBBF24', fontWeight: 700 }}>{msg.structured_payload.confirmation.preview?.code}</span></div>
                              <div>Mức giảm: <span style={{ color: '#34D399', fontWeight: 700 }}>{msg.structured_payload.confirmation.preview?.discount_percent}%</span> (Tối đa: {Number(msg.structured_payload.confirmation.preview?.max_discount_amount ?? 0).toLocaleString('vi-VN')} đ)</div>
                              <div>Thời hạn: <span style={{ color: '#CBD5E1' }}>{msg.structured_payload.confirmation.preview?.duration_days} ngày</span></div>
                            </>
                          )}
                          <div style={{ paddingTop: 4, borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '0.64rem', color: '#64748B' }}>
                            Token: <code style={{ color: '#FBBF24' }}>{msg.structured_payload.confirmation.confirmation_token}</code>
                          </div>
                        </div>

                        {confirmedTokens.has(msg.structured_payload.confirmation.confirmation_token) ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#34D399', fontWeight: 700, fontSize: '0.72rem', background: 'rgba(16,185,129,0.15)', padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(16,185,129,0.3)' }}>
                            <CheckCircle2 size={14} /> Đã xác nhận &amp; lưu chính thức vào cơ sở dữ liệu
                          </div>
                        ) : (
                          <button
                            onClick={() => handleConfirmAction(msg.structured_payload!.confirmation!.confirmation_token)}
                            disabled={confirmingToken === msg.structured_payload.confirmation.confirmation_token}
                            className="novelia-ai-confirm-exec-btn"
                          >
                            {confirmingToken === msg.structured_payload.confirmation.confirmation_token ? (
                              <>
                                <Sparkles size={14} /> Đang kiểm tra &amp; thực thi...
                              </>
                            ) : (
                              <>
                                <CheckCircle2 size={14} /> Xác nhận thực thi thay đổi ngay
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Sales Summary Widget */}
                  {msg.structured_payload?.sales_summary && (
                    <div className="novelia-ai-widget-sec">
                      <div className="novelia-ai-widget-title" style={{ color: '#38BDF8' }}>
                        <BarChart3 size={14} /> Báo cáo Doanh thu &amp; KPI (MySQL):
                      </div>
                      <div className="novelia-ai-stats-grid">
                        <div>
                          <div className="novelia-ai-stat-lbl">Doanh thu phát sinh:</div>
                          <div className="novelia-ai-stat-val gold">{msg.structured_payload.sales_summary.total_revenue.toLocaleString('vi-VN')} đ</div>
                        </div>
                        <div>
                          <div className="novelia-ai-stat-lbl">Đã thực thu (PAID):</div>
                          <div className="novelia-ai-stat-val green">{msg.structured_payload.sales_summary.collected_revenue.toLocaleString('vi-VN')} đ</div>
                        </div>
                        <div>
                          <div className="novelia-ai-stat-lbl">Đơn hàng hợp lệ:</div>
                          <div className="novelia-ai-stat-val">{msg.structured_payload.sales_summary.valid_orders_count} đơn</div>
                        </div>
                        <div>
                          <div className="novelia-ai-stat-lbl">Giá trị TB đơn:</div>
                          <div className="novelia-ai-stat-val">{msg.structured_payload.sales_summary.average_order_value.toLocaleString('vi-VN')} đ</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Inventory Summary Widget */}
                  {msg.structured_payload?.inventory_summary && (
                    <div className="novelia-ai-widget-sec">
                      <div className="novelia-ai-widget-title" style={{ color: '#60A5FA' }}>
                        <Boxes size={14} /> Tổng quan kho hàng:
                      </div>
                      <div className="novelia-ai-stats-grid">
                        <div>
                          <div className="novelia-ai-stat-lbl">Tổng đầu sách:</div>
                          <div className="novelia-ai-stat-val">{msg.structured_payload.inventory_summary.total_books} đầu sách</div>
                        </div>
                        <div>
                          <div className="novelia-ai-stat-lbl">Tồn khả dụng:</div>
                          <div className="novelia-ai-stat-val green">{msg.structured_payload.inventory_summary.total_available_stock.toLocaleString('vi-VN')} cuốn</div>
                        </div>
                        <div>
                          <div className="novelia-ai-stat-lbl">Tồn vật lý:</div>
                          <div className="novelia-ai-stat-val">{msg.structured_payload.inventory_summary.total_physical_stock.toLocaleString('vi-VN')} cuốn</div>
                        </div>
                        <div>
                          <div className="novelia-ai-stat-lbl">Cảnh báo sắp hết:</div>
                          <div className="novelia-ai-stat-val rose">{msg.structured_payload.inventory_summary.low_stock_count} sách</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Low Stock Alerts Widget */}
                  {msg.structured_payload?.low_stock && (
                    <div className="novelia-ai-widget-sec">
                      <div className="novelia-ai-widget-title" style={{ color: '#FB7185' }}>
                        <AlertTriangle size={14} /> Sách chạm ngưỡng cảnh báo ({msg.structured_payload.low_stock.count}):
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {msg.structured_payload.low_stock.low_stock_books.map((b) => (
                          <div
                            key={b.book_id}
                            style={{
                              padding: '6px 8px',
                              borderRadius: 8,
                              background: 'rgba(10, 18, 41, 0.9)',
                              border: '1px solid rgba(244, 63, 94, 0.3)',
                              fontSize: '0.68rem',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center'
                            }}
                          >
                            <span style={{ fontWeight: 600, color: '#F1F5F9', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 160 }}>{b.title}</span>
                            <span style={{ color: '#FB7185', fontWeight: 700 }}>Khả dụng: {b.available_stock} (Kho: {b.physical_stock})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="novelia-ai-turn assistant">
                <div className="novelia-ai-msg-avatar">
                  <Sparkles size={14} />
                </div>
                <div className="novelia-ai-loading-box">
                  <span>Novelia AI đang suy nghĩ</span>
                  <span className="novelia-ai-loading-dot" />
                  <span className="novelia-ai-loading-dot" />
                  <span className="novelia-ai-loading-dot" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Error Notice Banner */}
          {errorNotice && (
            <div className="novelia-ai-error-banner">
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{errorNotice}</span>
              <button
                onClick={() => setErrorNotice(null)}
                style={{ background: 'none', border: 'none', color: '#FECDD3', cursor: 'pointer', padding: 0, display: 'flex' }}
                aria-label="Đóng thông báo lỗi"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {/* Quick Suggestions Chips */}
          <div className="novelia-ai-chips-bar">
            {suggestedPrompts.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(prompt)}
                disabled={isLoading}
                className="novelia-ai-chip"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Footer */}
          <div className="novelia-ai-footer" style={{ flexDirection: 'column', gap: 6 }}>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
            >
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Hỏi về sách, tồn kho, đơn hàng, ship..."
                maxLength={1000}
                disabled={isLoading}
                className="novelia-ai-input"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="novelia-ai-send-btn"
                aria-label="Gửi tin nhắn"
              >
                <Send size={16} />
              </button>
            </form>
            <div className="novelia-ai-footer-note" style={{ width: '100%' }}>
              <span>Novelia AI • Đối thoại thương mại &amp; Tra cứu an toàn</span>
              <span>{inputValue.length}/1000</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
