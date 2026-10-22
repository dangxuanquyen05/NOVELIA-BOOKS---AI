import React, { useState, useRef, useEffect } from 'react';
import {
  BookOpen,
  ShoppingBag,
  Heart,
  Search,
  User as UserIcon,
  ChevronDown,
  Menu,
  X,
  LogOut,
  Package,
  MapPin,
  LayoutDashboard,
  Boxes,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { useCommerce } from '../context/CommerceContext';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  onOpenWishlist?: () => void;
  onNavigateTab?: (tab: string) => void;
  activeTab?: string;
  onSearch?: (query: string) => void;
  initialSearchQuery?: string;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenWishlist,
  onNavigateTab,
  activeTab = 'catalog',
  onSearch,
  initialSearchQuery = '',
}) => {
  const { cartCount, wishlistCount, openCart } = useCommerce();
  const { user, isAuthenticated, logout } = useAuth();

  const [searchVal, setSearchVal] = useState(initialSearchQuery);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [categoriesDropdownOpen, setCategoriesDropdownOpen] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const userDropdownRef = useRef<HTMLDivElement>(null);
  const categoriesDropdownRef = useRef<HTMLDivElement>(null);

  const isStaffOrAdmin =
    user?.roles?.some((r) => r === 'STAFF' || r === 'ADMIN') ?? false;

  // Sync search input if prop changes
  useEffect(() => {
    setSearchVal(initialSearchQuery);
  }, [initialSearchQuery]);

  // Click outside listener for dropdowns
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        userDropdownRef.current &&
        !userDropdownRef.current.contains(event.target as Node)
      ) {
        setUserDropdownOpen(false);
      }
      if (
        categoriesDropdownRef.current &&
        !categoriesDropdownRef.current.contains(event.target as Node)
      ) {
        setCategoriesDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchVal.trim());
    } else if (onNavigateTab) {
      onNavigateTab('catalog');
    }
  };

  const navigateTo = (tab: string) => {
    if (onNavigateTab) {
      onNavigateTab(tab);
    }
    setUserDropdownOpen(false);
    setCategoriesDropdownOpen(false);
    setMobileDrawerOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    setUserDropdownOpen(false);
    setMobileDrawerOpen(false);
    if (onNavigateTab) {
      onNavigateTab('login');
    }
  };

  return (
    <header className="storefront-header-v3" role="banner">
      <div className="storefront-header-inner">
        {/* Mobile Hamburger Toggle */}
        <button
          type="button"
          className="storefront-mobile-menu-toggle"
          onClick={() => setMobileDrawerOpen(true)}
          aria-label="Mở menu điều hướng"
        >
          <Menu size={22} />
        </button>

        {/* Brand Logo & Slogan */}
        <div
          className="storefront-brand-block"
          onClick={() => navigateTo('catalog')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter') navigateTo('catalog');
          }}
          title="NOVELIA BOOKS — Trang chủ"
        >
          <div className="brand-logo-icon-box" aria-hidden="true">
            <BookOpen size={24} className="brand-logo-icon" />
          </div>
          <div className="brand-titles">
            <h1 className="brand-main-title">NOVELIA BOOKS</h1>
            <span className="brand-tagline">Books for a better tomorrow</span>
          </div>
        </div>

        {/* Center Navigation Links (Desktop) */}
        <nav className="storefront-nav-desktop" aria-label="Thanh điều hướng chính">
          <button
            type="button"
            className={`storefront-nav-link ${activeTab === 'catalog' ? 'is-active' : ''}`}
            onClick={() => navigateTo('catalog')}
          >
            Trang chủ
          </button>

          <button
            type="button"
            className={`storefront-nav-link ${activeTab === 'catalog' ? 'is-active' : ''}`}
            onClick={() => navigateTo('catalog')}
          >
            Cửa hàng
          </button>

          {/* Categories Dropdown */}
          <div className="storefront-nav-dropdown-wrap" ref={categoriesDropdownRef}>
            <button
              type="button"
              className="storefront-nav-link dropdown-trigger"
              onClick={() => setCategoriesDropdownOpen((prev) => !prev)}
              aria-expanded={categoriesDropdownOpen}
            >
              <span>Danh mục</span>
              <ChevronDown
                size={14}
                className={`dropdown-chevron ${categoriesDropdownOpen ? 'rotate' : ''}`}
              />
            </button>

            {categoriesDropdownOpen && (
              <div className="storefront-dropdown-menu categories-menu">
                <div className="dropdown-menu-header">Khám phá theo chủ đề</div>
                <button
                  type="button"
                  className="dropdown-menu-item"
                  onClick={() => navigateTo('catalog')}
                >
                  <BookOpen size={15} />
                  <span>Văn học &amp; Tiểu thuyết</span>
                </button>
                <button
                  type="button"
                  className="dropdown-menu-item"
                  onClick={() => navigateTo('catalog')}
                >
                  <Sparkles size={15} />
                  <span>Kinh tế &amp; Quản trị</span>
                </button>
                <button
                  type="button"
                  className="dropdown-menu-item"
                  onClick={() => navigateTo('catalog')}
                >
                  <BookOpen size={15} />
                  <span>Kỹ năng sống &amp; Phát triển</span>
                </button>
                <button
                  type="button"
                  className="dropdown-menu-item"
                  onClick={() => navigateTo('catalog')}
                >
                  <BookOpen size={15} />
                  <span>Tâm lý học &amp; Khoa học</span>
                </button>
                <button
                  type="button"
                  className="dropdown-menu-item"
                  onClick={() => navigateTo('catalog')}
                >
                  <BookOpen size={15} />
                  <span>Lịch sử &amp; Triết học</span>
                </button>
              </div>
            )}
          </div>

          <button
            type="button"
            className="storefront-nav-link"
            onClick={() => navigateTo('catalog')}
          >
            Tác giả
          </button>

          <button
            type="button"
            className="storefront-nav-link"
            onClick={() => navigateTo('catalog')}
          >
            Nhà xuất bản
          </button>

          <button
            type="button"
            className="storefront-nav-link"
            onClick={() => navigateTo('catalog')}
          >
            Blog
          </button>
        </nav>

        {/* Global Search Bar (Desktop) */}
        <form
          className="storefront-header-search"
          onSubmit={handleSearchSubmit}
          role="search"
        >
          <Search size={16} className="search-input-icon" />
          <input
            type="text"
            className="search-input-field"
            placeholder="Tìm kiếm sách, tác giả, thể loại, ISBN..."
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            aria-label="Tìm kiếm sách"
          />
        </form>

        {/* Header Right Actions: Wishlist, Cart, User Account */}
        <div className="storefront-header-actions">
          {/* Wishlist Button */}
          <button
            type="button"
            className="storefront-action-icon-btn"
            onClick={() => {
              if (onOpenWishlist) onOpenWishlist();
              else navigateTo('wishlist');
            }}
            title="Tác phẩm yêu thích"
            aria-label="Tác phẩm yêu thích"
          >
            <Heart size={20} className={wishlistCount > 0 ? 'text-accent' : ''} />
            {wishlistCount > 0 && (
              <span className="storefront-action-badge">{wishlistCount}</span>
            )}
          </button>

          {/* Cart Button */}
          <button
            type="button"
            className="storefront-action-icon-btn"
            onClick={openCart}
            title="Mở giỏ hàng"
            aria-label="Giỏ hàng"
          >
            <ShoppingBag size={20} />
            {cartCount > 0 && (
              <span className="storefront-action-badge">{cartCount}</span>
            )}
          </button>

          {/* User Account / Profile Menu */}
          {isAuthenticated && user ? (
            <div className="storefront-user-wrap" ref={userDropdownRef}>
              <button
                type="button"
                className="storefront-user-pill-btn"
                onClick={() => setUserDropdownOpen((prev) => !prev)}
                aria-expanded={userDropdownOpen}
                aria-label="Tài khoản người dùng"
              >
                <div className="user-avatar-circle">
                  <UserIcon size={16} />
                </div>
                <div className="user-name-column">
                  <span className="user-full-name">{user.full_name}</span>
                  <span className="user-role-label">
                    {isStaffOrAdmin ? 'Quản trị viên' : 'Khách hàng'}
                  </span>
                </div>
                <ChevronDown size={14} className="user-chevron" />
              </button>

              {userDropdownOpen && (
                <div className="storefront-dropdown-menu user-menu">
                  <div className="user-dropdown-header">
                    <span className="user-header-name">{user.full_name}</span>
                    <span className="user-header-email">{user.email}</span>
                  </div>

                  <div className="dropdown-divider" />

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => navigateTo('profile')}
                  >
                    <UserIcon size={15} />
                    <span>Hồ sơ cá nhân</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => navigateTo('orders')}
                  >
                    <Package size={15} />
                    <span>Đơn hàng của tôi</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => navigateTo('addresses')}
                  >
                    <MapPin size={15} />
                    <span>Sổ địa chỉ</span>
                  </button>

                  {isStaffOrAdmin && (
                    <>
                      <div className="dropdown-divider" />
                      <div className="dropdown-menu-header">Bảng quản trị</div>
                      <button
                        type="button"
                        className="dropdown-menu-item admin-link"
                        onClick={() => navigateTo('admin-dashboard')}
                      >
                        <LayoutDashboard size={15} />
                        <span>Bảng điều hành</span>
                      </button>
                      <button
                        type="button"
                        className="dropdown-menu-item"
                        onClick={() => navigateTo('inventory')}
                      >
                        <Boxes size={15} />
                        <span>Quản trị kho</span>
                      </button>
                      <button
                        type="button"
                        className="dropdown-menu-item"
                        onClick={() => navigateTo('admin-orders')}
                      >
                        <ShieldAlert size={15} />
                        <span>Quản trị đơn</span>
                      </button>
                    </>
                  )}

                  <div className="dropdown-divider" />

                  <button
                    type="button"
                    className="dropdown-menu-item logout-item"
                    onClick={handleLogout}
                  >
                    <LogOut size={15} />
                    <span>Đăng xuất</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="storefront-guest-actions">
              <button
                type="button"
                className="guest-login-btn"
                onClick={() => navigateTo('login')}
              >
                Đăng nhập
              </button>
              <button
                type="button"
                className="guest-register-btn"
                onClick={() => navigateTo('register')}
              >
                Đăng ký
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileDrawerOpen && (
        <div
          className="storefront-mobile-drawer-backdrop"
          onClick={() => setMobileDrawerOpen(false)}
        >
          <div
            className="storefront-mobile-drawer"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mobile-drawer-header">
              <div className="mobile-drawer-brand">
                <BookOpen size={20} className="brand-logo-icon" />
                <span className="brand-main-title">NOVELIA BOOKS</span>
              </div>
              <button
                type="button"
                className="mobile-drawer-close"
                onClick={() => setMobileDrawerOpen(false)}
                aria-label="Đóng menu"
              >
                <X size={20} />
              </button>
            </div>

            {/* Mobile Search */}
            <form
              className="mobile-drawer-search"
              onSubmit={handleSearchSubmit}
            >
              <Search size={16} className="search-input-icon" />
              <input
                type="text"
                placeholder="Tìm sách, tác giả, ISBN..."
                value={searchVal}
                onChange={(e) => setSearchVal(e.target.value)}
              />
            </form>

            <nav className="mobile-drawer-nav">
              <button
                type="button"
                className="mobile-nav-link"
                onClick={() => navigateTo('catalog')}
              >
                Trang chủ
              </button>
              <button
                type="button"
                className="mobile-nav-link"
                onClick={() => navigateTo('catalog')}
              >
                Cửa hàng sách
              </button>
              <button
                type="button"
                className="mobile-nav-link"
                onClick={() => {
                  if (onOpenWishlist) onOpenWishlist();
                  else navigateTo('wishlist');
                }}
              >
                Tác phẩm yêu thích ({wishlistCount})
              </button>
              {isAuthenticated ? (
                <>
                  <button
                    type="button"
                    className="mobile-nav-link"
                    onClick={() => navigateTo('orders')}
                  >
                    Đơn hàng của tôi
                  </button>
                  <button
                    type="button"
                    className="mobile-nav-link"
                    onClick={() => navigateTo('profile')}
                  >
                    Hồ sơ cá nhân
                  </button>
                  <button
                    type="button"
                    className="mobile-nav-link"
                    onClick={() => navigateTo('addresses')}
                  >
                    Sổ địa chỉ
                  </button>
                  {isStaffOrAdmin && (
                    <button
                      type="button"
                      className="mobile-nav-link admin-nav"
                      onClick={() => navigateTo('admin-dashboard')}
                    >
                      Bảng điều hành Quản trị
                    </button>
                  )}
                  <button
                    type="button"
                    className="mobile-nav-link logout-nav"
                    onClick={handleLogout}
                  >
                    Đăng xuất
                  </button>
                </>
              ) : (
                <div className="mobile-drawer-auth-btns">
                  <button
                    type="button"
                    className="guest-login-btn full-w"
                    onClick={() => navigateTo('login')}
                  >
                    Đăng nhập
                  </button>
                  <button
                    type="button"
                    className="guest-register-btn full-w"
                    onClick={() => navigateTo('register')}
                  >
                    Đăng ký tài khoản
                  </button>
                </div>
              )}
            </nav>
          </div>
        </div>
      )}
    </header>
  );
};
