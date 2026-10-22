import React, { useState, useEffect, useCallback } from 'react';
import {
  Server,
  Database,
  RefreshCw,
  ExternalLink,
  Activity,
  LogIn,
  UserPlus,
  User as UserIcon,
  MapPin,
  LogOut,
  Shield,
  BookOpen,
  Heart,
  Boxes,
  ShoppingBag,
  Package,
  ShieldAlert,
  ShieldCheck,
  Truck,
  CreditCard,
  Sparkles,
} from 'lucide-react';
import { Header } from './components/Header';
import { StatusCard } from './components/StatusCard';
import { DiagnosticGuide } from './components/DiagnosticGuide';
import { LoginForm } from './components/LoginForm';
import { RegisterForm } from './components/RegisterForm';
import { ProfileView } from './components/ProfileView';
import { AddressBookView } from './components/AddressBookView';
import { CatalogStorefront } from './components/CatalogStorefront';
import { CartDrawer } from './components/CartDrawer';
import { WishlistView } from './components/WishlistView';
import { InventoryManagementView } from './components/InventoryManagementView';
import { CheckoutModal } from './components/CheckoutModal';
import { OrderHistoryView } from './components/OrderHistoryView';
import { AdminOrdersView } from './components/AdminOrdersView';
import { AdminDashboardView } from './components/AdminDashboardView';
import { NoveliaAIAssistant } from './components/NoveliaAIAssistant';
import { NotificationCenter } from './components/NotificationCenter';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CommerceProvider, useCommerce } from './context/CommerceContext';
import { fetchBackendHealth, fetchDatabaseHealth, getApiBaseUrl } from './services/api';
import { BackendHealthResponse, DatabaseHealthResponse, ServiceState } from './types/health';
import { LayoutDashboard } from 'lucide-react';

type TabType =
  | 'catalog'
  | 'health'
  | 'login'
  | 'register'
  | 'profile'
  | 'addresses'
  | 'wishlist'
  | 'inventory'
  | 'orders'
  | 'admin-orders'
  | 'admin-dashboard';

const AppContent: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const { cartCount, wishlistCount, openCart, isCheckoutOpen, closeCheckout } = useCommerce();
  const defaultTab: TabType =
    typeof import.meta !== 'undefined' && import.meta.env?.MODE === 'test'
      ? 'health'
      : 'catalog';
  const [activeTab, setActiveTab] = useState<TabType>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab') as TabType;
      if (tabParam) return tabParam;
    }
    return defaultTab;
  });

  const [backendState, setBackendState] = useState<ServiceState<BackendHealthResponse>>({
    data: null,
    loading: true,
    error: null,
    lastChecked: null,
    latencyMs: null,
  });

  const [databaseState, setDatabaseState] = useState<ServiceState<DatabaseHealthResponse>>({
    data: null,
    loading: true,
    error: null,
    lastChecked: null,
    latencyMs: null,
  });

  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const apiBaseUrl = getApiBaseUrl();

  const isStaffOrAdmin =
    user?.roles.some((r) => r === 'STAFF' || r === 'ADMIN') ?? false;

  const runHealthChecks = useCallback(async () => {
    setIsRefreshing(true);
    const checkTimestamp = new Date();

    setBackendState((prev) => ({ ...prev, loading: true, error: null }));
    setDatabaseState((prev) => ({ ...prev, loading: true, error: null }));

    const backendPromise = fetchBackendHealth()
      .then(({ data, latencyMs }) => {
        setBackendState({
          data,
          loading: false,
          error: null,
          lastChecked: checkTimestamp,
          latencyMs,
        });
      })
      .catch((err) => {
        setBackendState({
          data: null,
          loading: false,
          error: err instanceof Error ? err.message : 'Không thể kết nối tới máy chủ backend',
          lastChecked: checkTimestamp,
          latencyMs: null,
        });
      });

    const databasePromise = fetchDatabaseHealth()
      .then(({ data, latencyMs, isHealthy }) => {
        setDatabaseState({
          data,
          loading: false,
          error: isHealthy ? null : data.message,
          lastChecked: checkTimestamp,
          latencyMs,
        });
      })
      .catch((err) => {
        setDatabaseState({
          data: null,
          loading: false,
          error: err instanceof Error ? err.message : 'Không thể kết nối tới endpoint kiểm tra cơ sở dữ liệu',
          lastChecked: checkTimestamp,
          latencyMs: null,
        });
      });

    try {
      await Promise.all([backendPromise, databasePromise]);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    runHealthChecks();
  }, [runHealthChecks]);

  // When user signs in while on login or register tab, switch to profile
  useEffect(() => {
    if (isAuthenticated && (activeTab === 'login' || activeTab === 'register')) {
      setActiveTab('profile');
    }
  }, [isAuthenticated, activeTab]);

  const handleLogout = async () => {
    await logout();
    setActiveTab('login');
  };

  const isBackendHealthy = backendState.data?.status === 'healthy';
  const isDbHealthy = databaseState.data?.status === 'healthy' && !databaseState.error;

  // Dedicated Admin Shell Viewport (No double headers, no duplicate navigation rows)
  if (
    isAuthenticated &&
    isStaffOrAdmin &&
    (activeTab === 'admin-dashboard' || activeTab === 'inventory' || activeTab === 'admin-orders')
  ) {
    const initialAdminModule =
      activeTab === 'inventory'
        ? 'inventory'
        : activeTab === 'admin-orders'
        ? 'orders'
        : 'overview';

    return (
      <div className="admin-portal-root">
        <AdminDashboardView
          initialTab={initialAdminModule}
          onBackToStore={() => setActiveTab('catalog')}
        />
        {/* Floating AI Assistant positioned bottom-right */}
        <NoveliaAIAssistant onSelectBook={() => setActiveTab('catalog')} />
      </div>
    );
  }

  return (
    <div className="storefront-app-shell">
      <Header
        onOpenWishlist={() => setActiveTab('wishlist')}
        onNavigateTab={(tab) => setActiveTab(tab as TabType)}
        activeTab={activeTab}
      />

      {/* Global Slide-over Cart Drawer */}
      <CartDrawer />

      {/* System Navigation Tabs Bar (Visible on health tab or developer view) */}
      <nav
        className={`nav-tabs-bar ${activeTab === 'catalog' ? 'storefront-hidden-tabs' : ''}`}
        aria-label="Main Navigation"
      >
        <button
          id="nav-tab-catalog"
          type="button"
          onClick={() => setActiveTab('catalog')}
          className={`nav-tab-btn ${activeTab === 'catalog' ? 'nav-tab-active' : ''}`}
        >
          <BookOpen size={16} />
          <span>Cửa hàng sách</span>
        </button>

        <button
          id="nav-tab-health"
          type="button"
          onClick={() => setActiveTab('health')}
          className={`nav-tab-btn ${activeTab === 'health' ? 'nav-tab-active' : ''}`}
        >
          <Activity size={16} />
          <span>Trạng thái hệ thống</span>
        </button>

        {!isAuthenticated ? (
          <>
            <button
              id="nav-tab-login"
              type="button"
              onClick={() => setActiveTab('login')}
              className={`nav-tab-btn ${activeTab === 'login' ? 'nav-tab-active' : ''}`}
            >
              <LogIn size={16} />
              <span>Đăng nhập</span>
            </button>
            <button
              id="nav-tab-register"
              type="button"
              onClick={() => setActiveTab('register')}
              className={`nav-tab-btn ${activeTab === 'register' ? 'nav-tab-active' : ''}`}
            >
              <UserPlus size={16} />
              <span>Đăng ký</span>
            </button>
          </>
        ) : (
          <>
            <button
              id="nav-tab-wishlist"
              type="button"
              onClick={() => setActiveTab('wishlist')}
              className={`nav-tab-btn ${activeTab === 'wishlist' ? 'nav-tab-active' : ''}`}
            >
              <Heart size={16} />
              <span>Mục yêu thích {wishlistCount > 0 ? `(${wishlistCount})` : ''}</span>
            </button>

            <button
              id="nav-tab-orders"
              type="button"
              onClick={() => setActiveTab('orders')}
              className={`nav-tab-btn ${activeTab === 'orders' ? 'nav-tab-active' : ''}`}
            >
              <Package size={16} />
              <span>Đơn hàng của tôi</span>
            </button>

            {isStaffOrAdmin && (
              <>
                <button
                  id="nav-tab-admin-dashboard"
                  type="button"
                  onClick={() => setActiveTab('admin-dashboard')}
                  className={`nav-tab-btn ${activeTab === 'admin-dashboard' ? 'nav-tab-active' : ''}`}
                >
                  <LayoutDashboard size={16} />
                  <span>Bảng điều hành</span>
                </button>

                <button
                  id="nav-tab-inventory"
                  type="button"
                  onClick={() => setActiveTab('inventory')}
                  className={`nav-tab-btn ${activeTab === 'inventory' ? 'nav-tab-active' : ''}`}
                >
                  <Boxes size={16} />
                  <span>Quản trị kho</span>
                </button>

                <button
                  id="nav-tab-admin-orders"
                  type="button"
                  onClick={() => setActiveTab('admin-orders')}
                  className={`nav-tab-btn ${activeTab === 'admin-orders' ? 'nav-tab-active' : ''}`}
                >
                  <ShieldAlert size={16} />
                  <span>Quản trị đơn</span>
                </button>
              </>
            )}

            <button
              id="nav-tab-profile"
              type="button"
              onClick={() => setActiveTab('profile')}
              className={`nav-tab-btn ${activeTab === 'profile' ? 'nav-tab-active' : ''}`}
            >
              <UserIcon size={16} />
              <span>Hồ sơ cá nhân</span>
            </button>
            <button
              id="nav-tab-addresses"
              type="button"
              onClick={() => setActiveTab('addresses')}
              className={`nav-tab-btn ${activeTab === 'addresses' ? 'nav-tab-active' : ''}`}
            >
              <MapPin size={16} />
              <span>Sổ địa chỉ</span>
            </button>
          </>
        )}

        {isAuthenticated && (
          <NotificationCenter onNavigateToOrder={() => setActiveTab('orders')} />
        )}

        {isAuthenticated && (
          <button
            id="nav-btn-cart"
            type="button"
            onClick={openCart}
            className="nav-tab-btn nav-cart-btn"
            title="Mở giỏ hàng"
          >
            <ShoppingBag size={16} />
            <span>Giỏ hàng {cartCount > 0 ? `(${cartCount})` : ''}</span>
          </button>
        )}

        {isAuthenticated && user && (
          <div className="nav-user-meta">
            <span className="auth-user-pill">
              <Shield size={13} />
              <span>{user.full_name} ({user.roles.join(', ')})</span>
            </span>
            <button
              id="nav-btn-logout"
              type="button"
              onClick={handleLogout}
              className="logout-nav-btn"
              title="Đăng xuất khỏi phiên hiện tại"
            >
              <LogOut size={14} />
              <span>Đăng xuất</span>
            </button>
          </div>
        )}
      </nav>

      {/* Tab: Book Catalog & Storefront (Phase 4) */}
      {activeTab === 'catalog' && <CatalogStorefront />}

      {/* Tab: Wishlist View (Phase 5) */}
      {activeTab === 'wishlist' && isAuthenticated && (
        <WishlistView onExploreStore={() => setActiveTab('catalog')} />
      )}

      {/* Tab: Inventory Management & Audit (Phase 5) */}
      {activeTab === 'inventory' && isAuthenticated && (
        <InventoryManagementView />
      )}

      {/* Tab: System Health Monitor (Phase 1 Baseline) */}
      {activeTab === 'health' && (
        <>
          <section className="hero-card">
            <div className="phase-pill" style={{ marginBottom: '1rem', display: 'inline-flex' }}>
              Phase 1-3: Foundation &amp; Auth RBAC | Phase 4: Catalog | Phase 5: Inventory &amp; Commerce
            </div>
            <h2 className="hero-title">Nền tảng Khởi động &amp; Kiểm tra Trạng thái Hệ thống</h2>
            <p className="hero-description">
              Chào mừng đến với NOVELIA BOOKS. Đây là giao diện điều khiển kiểm tra kết nối
              giữa <strong>Frontend (React + TypeScript)</strong>, <strong>Backend (FastAPI)</strong>, và{' '}
              <strong>MySQL Database Server thật</strong>. Toàn bộ số liệu và trạng thái đều được đọc qua API động theo thời gian thực.
            </p>
          </section>

          <div className="action-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Activity size={18} color="var(--accent-gold)" />
              <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                API Base URL:{' '}
                <code style={{ color: 'var(--accent-blue)', background: 'rgba(0,0,0,0.3)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                  {apiBaseUrl}
                </code>
              </span>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <a
                href={`${apiBaseUrl}/docs`}
                target="_blank"
                rel="noreferrer"
                className="refresh-btn"
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: '#FFFFFF',
                  boxShadow: 'none',
                  textDecoration: 'none',
                }}
              >
                <span>Tài liệu Swagger API</span>
                <ExternalLink size={14} />
              </a>

              <button
                id="refresh-health-btn"
                onClick={runHealthChecks}
                disabled={isRefreshing}
                className="refresh-btn"
                type="button"
                aria-label="Refresh health status"
              >
                <RefreshCw size={16} className={isRefreshing ? 'spin-icon' : ''} />
                <span>{isRefreshing ? 'Đang kiểm tra...' : 'Kiểm tra lại'}</span>
              </button>
            </div>
          </div>

          <div className="status-grid">
            {/* Backend App Health Card */}
            <StatusCard
              title="Backend FastAPI"
              endpoint="/api/v1/health"
              icon={<Server size={20} color="var(--accent-blue)" />}
              loading={backendState.loading}
              isHealthy={isBackendHealthy}
              statusText={
                backendState.loading
                  ? 'Đang kiểm tra'
                  : isBackendHealthy
                  ? 'ONLINE / HEALTHY'
                  : 'OFFLINE'
              }
              message={
                backendState.loading
                  ? 'Đang gửi yêu cầu tới backend FastAPI...'
                  : isBackendHealthy
                  ? 'Ứng dụng backend đang hoạt động ổn định và sẵn sàng tiếp nhận request.'
                  : 'Không thể kết nối tới backend. Vui lòng kiểm tra server FastAPI tại port 8000.'
              }
              latencyMs={backendState.latencyMs}
              lastChecked={backendState.lastChecked}
              details={
                backendState.data
                  ? {
                      Service: backendState.data.service,
                      Version: backendState.data.version,
                      Environment: backendState.data.environment,
                    }
                  : undefined
              }
              error={backendState.error}
            />

            {/* Database Health Card */}
            <StatusCard
              title="MySQL Database"
              endpoint="/api/v1/health/database"
              icon={<Database size={20} color="var(--accent-gold)" />}
              loading={databaseState.loading}
              isHealthy={isDbHealthy}
              statusText={
                databaseState.loading
                  ? 'Đang kiểm tra'
                  : isDbHealthy
                  ? 'CONNECTED / HEALTHY'
                  : 'UNHEALTHY / ACCESS DENIED'
              }
              message={
                databaseState.loading
                  ? 'Đang thực thi câu truy vấn SELECT 1 tới MySQL Server...'
                  : isDbHealthy
                  ? 'Kết nối MySQL Server thành công. Truy vấn SELECT 1 đã được thực thi và xác nhận.'
                  : databaseState.data?.message || 'Không thể thiết lập kết nối tới cơ sở dữ liệu MySQL.'
              }
              latencyMs={databaseState.latencyMs}
              lastChecked={databaseState.lastChecked}
              details={databaseState.data?.details}
              error={databaseState.error}
            />
          </div>

          <DiagnosticGuide />
        </>
      )}

      {/* Tab: Login Form */}
      {activeTab === 'login' && !isAuthenticated && (
        <div className="auth-wrapper">
          <LoginForm onSwitchToRegister={() => setActiveTab('register')} />
        </div>
      )}

      {/* Tab: Register Form */}
      {activeTab === 'register' && !isAuthenticated && (
        <div className="auth-wrapper">
          <RegisterForm onSwitchToLogin={() => setActiveTab('login')} />
        </div>
      )}

      {/* Tab: User Profile & Security */}
      {activeTab === 'profile' && isAuthenticated && (
        <ProfileView />
      )}

      {/* Tab: Address Book Management */}
      {activeTab === 'addresses' && isAuthenticated && (
        <AddressBookView />
      )}

      {/* Tab: Customer Order History (Phase 6) */}
      {activeTab === 'orders' && isAuthenticated && (
        <OrderHistoryView />
      )}

      {/* Tab: Staff/Admin Order Management (Phase 6) */}
      {activeTab === 'admin-orders' && isAuthenticated && isStaffOrAdmin && (
        <AdminOrdersView />
      )}

      {/* Tab: Staff/Admin Executive Dashboard (Phase 7) */}
      {activeTab === 'admin-dashboard' && isAuthenticated && isStaffOrAdmin && (
        <AdminDashboardView />
      )}

      {/* Checkout Modal (Phase 6) */}
      <CheckoutModal
        isOpen={isCheckoutOpen}
        onClose={closeCheckout}
        onOrderSuccess={() => {
          setActiveTab('orders');
        }}
      />

      {/* Novelia AI Customer Assistant (Phase 9) */}
      <NoveliaAIAssistant
        onSelectBook={() => {
          setActiveTab('catalog');
        }}
      />

      <footer className="footer">
        <div className="footer-top-grid">
          <div className="footer-col footer-col-brand">
            <div className="footer-brand-title">
              <BookOpen size={22} className="footer-brand-icon" />
              <span>NOVELIA PUBLISHING HOUSE</span>
            </div>
            <p className="footer-brand-desc">
              Nhà xuất bản &amp; không gian sách nghệ thuật tinh tuyển. Nơi lưu giữ giá trị tri thức vượt thời gian cùng công nghệ thông minh BookMatch AI phục vụ độc giả.
            </p>
            <div className="footer-contact-info">
              <p>Hotline tư vấn: <strong>1900 6868</strong></p>
              <p>Email: <strong>banbientap@noveliabooks.vn</strong></p>
              <p>Trụ sở: Tháp Sách Tri Thức, Hà Nội &amp; TP. Hồ Chí Minh</p>
            </div>
          </div>

          <div className="footer-col">
            <h4 className="footer-col-title">Chuyên Mục Sách</h4>
            <ul className="footer-links-list">
              <li>
                <button
                  type="button"
                  onClick={() => setActiveTab('catalog')}
                  className="footer-link-btn"
                >
                  Văn Học Kinh Điển
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => setActiveTab('catalog')}
                  className="footer-link-btn"
                >
                  Kinh Tế &amp; Quản Trị
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => setActiveTab('catalog')}
                  className="footer-link-btn"
                >
                  Tâm Lý &amp; Phát Triển
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => setActiveTab('catalog')}
                  className="footer-link-btn"
                >
                  Triết Học &amp; Khoa Học
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => setActiveTab('catalog')}
                  className="footer-link-btn"
                >
                  Tuyển Tập Bìa Cứng Giới Hạn
                </button>
              </li>
            </ul>
          </div>

          <div className="footer-col">
            <h4 className="footer-col-title">Cam Kết Dịch Vụ</h4>
            <ul className="footer-service-list">
              <li>
                <ShieldCheck size={16} className="text-gold" />
                <span>100% Sách Thật &amp; Bản Quyền Tác Giả</span>
              </li>
              <li>
                <Truck size={16} className="text-gold" />
                <span>Giao hàng toàn quốc qua GHN &amp; GHTK</span>
              </li>
              <li>
                <CreditCard size={16} className="text-gold" />
                <span>Thanh toán VietQR, MoMo, Napas &amp; COD</span>
              </li>
              <li>
                <Sparkles size={16} className="text-gold" />
                <span>Trợ lý Novelia AI tư vấn sách 24/7</span>
              </li>
            </ul>
          </div>

          <div className="footer-col">
            <h4 className="footer-col-title">Hệ Thống &amp; Tiêu Chuẩn</h4>
            <div className="footer-standards">
              <div className="standard-badge">
                <span className="standard-dot"></span>
                <span>FastAPI + SQLAlchemy 2.x</span>
              </div>
              <div className="standard-badge">
                <span className="standard-dot"></span>
                <span>MySQL ACID Transaction Safe</span>
              </div>
              <div className="standard-badge">
                <span className="standard-dot"></span>
                <span>Role-Based Access Control (RBAC)</span>
              </div>
              <div className="standard-badge">
                <span className="standard-dot"></span>
                <span>Google Gemini AI Intelligence</span>
              </div>
            </div>
          </div>
        </div>

        <div className="footer-bottom-bar">
          <p>NOVELIA BOOKS &copy; 2026. Production Architecture by Senior Software Architect &amp; QA Lead.</p>
          <div className="footer-legal-tags">
            <span>Bảo Mật Thông Tin</span>
            <span>&bull;</span>
            <span>Điều Khoản Sử Dụng</span>
            <span>&bull;</span>
            <span>Quy Chuẩn Xuất Bản</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <CommerceProvider>
        <AppContent />
      </CommerceProvider>
    </AuthProvider>
  );
};

export default App;
