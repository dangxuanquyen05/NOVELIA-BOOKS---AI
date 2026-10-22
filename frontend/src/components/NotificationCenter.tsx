import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Bell,
  CheckCheck,
  ShoppingBag,
  Truck,
  Tag,
  Info,
  X,
  ChevronRight,
} from 'lucide-react';
import { useSafeAuth } from '../context/AuthContext';
import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsAsRead,
  markNotificationAsRead,
} from '../services/notificationApi';
import { NotificationItem, NotificationType } from '../types/notification';

interface NotificationCenterProps {
  onNavigateToOrder?: (orderCode: string) => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  onNavigateToOrder,
}) => {
  const { token, isAuthenticated } = useSafeAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [filterType, setFilterType] = useState<'ALL' | 'UNREAD'>('ALL');
  const [loading, setLoading] = useState(false);
  const [markingAll, setMarkingAll] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Poll or load unread count
  const loadUnreadCount = useCallback(async () => {
    if (!token || !isAuthenticated) {
      setUnreadCount(0);
      return;
    }
    try {
      const res = await fetchUnreadCount(token);
      setUnreadCount(res.unread_count);
    } catch {
      // Quietly ignore background poll error
    }
  }, [token, isAuthenticated]);

  const loadNotifications = useCallback(async () => {
    if (!token || !isAuthenticated) return;
    setLoading(true);
    try {
      const isReadFilter = filterType === 'UNREAD' ? false : undefined;
      const res = await fetchNotifications(token, isReadFilter, undefined, 1, 20);
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  }, [token, isAuthenticated, filterType]);

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [loadUnreadCount]);

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [isOpen, loadNotifications]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleToggle = () => {
    if (!isAuthenticated) {
      alert('Quý khách vui lòng đăng nhập để xem thông báo.');
      return;
    }
    setIsOpen(!isOpen);
  };

  const handleMarkAsRead = async (id: number, referenceLink?: string | null) => {
    try {
      await markNotificationAsRead(token, id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));

      if (referenceLink && onNavigateToOrder && referenceLink.startsWith('/orders/')) {
        const orderCode = referenceLink.replace('/orders/', '');
        setIsOpen(false);
        onNavigateToOrder(orderCode);
      }
    } catch (err) {
      console.error('Error marking as read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await markAllNotificationsAsRead(token);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Error marking all read:', err);
    } finally {
      setMarkingAll(false);
    }
  };

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'ORDER':
        return <ShoppingBag className="w-4 h-4 text-amber-400" />;
      case 'SHIPPING':
        return <Truck className="w-4 h-4 text-emerald-400" />;
      case 'PROMOTION':
        return <Tag className="w-4 h-4 text-rose-400" />;
      default:
        return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + ' ' + date.toLocaleDateString('vi-VN');
    } catch {
      return isoString;
    }
  };

  return (
    <div className="relative" ref={dropdownRef} data-testid="notification-center">
      {/* Bell Button */}
      <button
        onClick={handleToggle}
        aria-label="Thông báo"
        className="relative p-2 rounded-xl text-slate-300 hover:text-amber-400 hover:bg-slate-800/60 transition-all border border-transparent hover:border-slate-700/50"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span
            data-testid="unread-badge"
            className="absolute top-1 right-1 min-w-[18px] h-[18px] px-1 bg-amber-500 text-slate-950 text-[10px] font-extrabold rounded-full flex items-center justify-center shadow-lg shadow-amber-500/50 animate-pulse"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Popover */}
      {isOpen && (
        <div
          data-testid="notification-dropdown"
          className="absolute right-0 mt-3 w-80 sm:w-96 rounded-2xl bg-slate-900 border border-amber-500/30 shadow-2xl z-50 overflow-hidden flex flex-col max-h-[500px]"
        >
          {/* Header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm text-slate-100">Thông báo</span>
              {unreadCount > 0 && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  {unreadCount} mới
                </span>
              )}
            </div>

            <div className="flex items-center gap-1.5">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  disabled={markingAll}
                  className="text-[11px] text-slate-400 hover:text-amber-300 transition-colors flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-slate-800/60 disabled:opacity-50"
                  title="Đánh dấu tất cả đã đọc"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  <span>Đã đọc hết</span>
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800/60"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="px-4 py-2 border-b border-slate-800/80 bg-slate-950/40 flex gap-2 text-xs">
            <button
              onClick={() => setFilterType('ALL')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                filterType === 'ALL'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Tất cả
            </button>
            <button
              onClick={() => setFilterType('UNREAD')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                filterType === 'UNREAD'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Chưa đọc {unreadCount > 0 ? `(${unreadCount})` : ''}
            </button>
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto divide-y divide-slate-800/60 flex-1">
            {loading && notifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                Đang tải thông báo...
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                {filterType === 'UNREAD'
                  ? 'Tuyệt vời! Bạn không có thông báo chưa đọc nào.'
                  : 'Hộp thư thông báo hiện đang trống.'}
              </div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleMarkAsRead(item.id, item.reference_link)}
                  className={`p-3.5 transition-colors cursor-pointer flex items-start gap-3 hover:bg-slate-800/50 ${
                    !item.is_read ? 'bg-amber-950/15' : ''
                  }`}
                >
                  <div className="p-2 rounded-xl bg-slate-800 border border-slate-700/60 mt-0.5 shrink-0">
                    {getIcon(item.notification_type)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h4
                        className={`text-xs font-semibold truncate ${
                          !item.is_read ? 'text-amber-200 font-bold' : 'text-slate-200'
                        }`}
                      >
                        {item.title}
                      </h4>
                      {!item.is_read && (
                        <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {item.message}
                    </p>
                    <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                      <span>{formatTime(item.created_at)}</span>
                      {item.reference_link && (
                        <span className="text-amber-400/80 hover:text-amber-300 flex items-center gap-0.5">
                          <span>Chi tiết</span>
                          <ChevronRight className="w-3 h-3" />
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
