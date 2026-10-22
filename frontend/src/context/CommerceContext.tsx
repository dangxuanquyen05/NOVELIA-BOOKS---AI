/* eslint-disable react-refresh/only-export-components */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { useAuth } from './AuthContext';
import { Cart, Wishlist } from '../types/commerce';
import * as commerceApi from '../services/commerceApi';

interface CommerceContextType {
  cart: Cart | null;
  wishlist: Wishlist | null;
  cartCount: number;
  wishlistCount: number;
  cartLoading: boolean;
  cartError: string | null;
  isCartOpen: boolean;
  openCart: () => void;
  closeCart: () => void;
  isCheckoutOpen: boolean;
  openCheckout: () => void;
  closeCheckout: () => void;
  addToCart: (bookId: number, quantity?: number) => Promise<void>;
  updateCartQuantity: (bookId: number, quantity: number) => Promise<void>;
  removeFromCart: (bookId: number) => Promise<void>;
  clearCart: () => Promise<void>;
  addToWishlist: (bookId: number) => Promise<void>;
  removeFromWishlist: (bookId: number) => Promise<void>;
  isInWishlist: (bookId: number) => boolean;
  moveWishlistToCart: (bookId: number) => Promise<void>;
  refreshCart: () => Promise<void>;
  refreshWishlist: () => Promise<void>;
}

const CommerceContext = createContext<CommerceContextType | undefined>(undefined);

export const CommerceProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { token, isAuthenticated } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [wishlist, setWishlist] = useState<Wishlist | null>(null);
  const [cartLoading, setCartLoading] = useState<boolean>(false);
  const [cartError, setCartError] = useState<string | null>(null);
  const [isCartOpen, setIsCartOpen] = useState<boolean>(false);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState<boolean>(false);

  const refreshCart = useCallback(async () => {
    if (!token || !isAuthenticated) {
      setCart(null);
      return;
    }
    setCartLoading(true);
    setCartError(null);
    try {
      const data = await commerceApi.fetchCart(token);
      setCart(data);
    } catch (err) {
      setCartError(err instanceof Error ? err.message : 'Không thể tải giỏ hàng');
    } finally {
      setCartLoading(false);
    }
  }, [token, isAuthenticated]);

  const refreshWishlist = useCallback(async () => {
    if (!token || !isAuthenticated) {
      setWishlist(null);
      return;
    }
    try {
      const data = await commerceApi.fetchWishlist(token);
      setWishlist(data);
    } catch {
      // Ignored for non-blocking wishlist
    }
  }, [token, isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated && token) {
      refreshCart();
      refreshWishlist();
    } else {
      setCart(null);
      setWishlist(null);
    }
  }, [isAuthenticated, token, refreshCart, refreshWishlist]);

  const addToCart = async (bookId: number, quantity: number = 1) => {
    if (!token || !isAuthenticated) {
      throw new Error('Vui lòng đăng nhập để thêm sách vào giỏ hàng.');
    }
    setCartLoading(true);
    try {
      const updated = await commerceApi.addToCart(token, bookId, quantity);
      setCart(updated);
      setIsCartOpen(true);
    } finally {
      setCartLoading(false);
    }
  };

  const updateCartQuantity = async (bookId: number, quantity: number) => {
    if (!token || !isAuthenticated) return;
    setCartLoading(true);
    try {
      const updated = await commerceApi.updateCartItemQuantity(token, bookId, quantity);
      setCart(updated);
    } finally {
      setCartLoading(false);
    }
  };

  const removeFromCart = async (bookId: number) => {
    if (!token || !isAuthenticated) return;
    setCartLoading(true);
    try {
      const updated = await commerceApi.removeFromCart(token, bookId);
      setCart(updated);
    } finally {
      setCartLoading(false);
    }
  };

  const clearCart = async () => {
    if (!token || !isAuthenticated) return;
    setCartLoading(true);
    try {
      const updated = await commerceApi.clearCart(token);
      setCart(updated);
    } finally {
      setCartLoading(false);
    }
  };

  const addToWishlist = async (bookId: number) => {
    if (!token || !isAuthenticated) {
      throw new Error('Vui lòng đăng nhập để lưu sách vào mục yêu thích.');
    }
    const updated = await commerceApi.addToWishlist(token, bookId);
    setWishlist(updated);
  };

  const removeFromWishlist = async (bookId: number) => {
    if (!token || !isAuthenticated) return;
    const updated = await commerceApi.removeFromWishlist(token, bookId);
    setWishlist(updated);
  };

  const isInWishlist = (bookId: number): boolean => {
    if (!wishlist || !wishlist.items) return false;
    return wishlist.items.some((i) => i.book_id === bookId);
  };

  const moveWishlistToCart = async (bookId: number) => {
    if (!token || !isAuthenticated) return;
    const updatedCart = await commerceApi.moveWishlistToCart(token, bookId);
    setCart(updatedCart);
    await refreshWishlist();
    setIsCartOpen(true);
  };

  const cartCount = cart ? cart.total_items : 0;
  const wishlistCount = wishlist ? wishlist.total_items : 0;

  return (
    <CommerceContext.Provider
      value={{
        cart,
        wishlist,
        cartCount,
        wishlistCount,
        cartLoading,
        cartError,
        isCartOpen,
        openCart: () => setIsCartOpen(true),
        closeCart: () => setIsCartOpen(false),
        isCheckoutOpen,
        openCheckout: () => {
          setIsCartOpen(false);
          setIsCheckoutOpen(true);
        },
        closeCheckout: () => setIsCheckoutOpen(false),
        addToCart,
        updateCartQuantity,
        removeFromCart,
        clearCart,
        addToWishlist,
        removeFromWishlist,
        isInWishlist,
        moveWishlistToCart,
        refreshCart,
        refreshWishlist,
      }}
    >
      {children}
    </CommerceContext.Provider>
  );
};

export const useCommerce = (): CommerceContextType => {
  const context = useContext(CommerceContext);
  if (!context) {
    throw new Error('useCommerce must be used within a CommerceProvider');
  }
  return context;
};

export const useSafeCommerce = (): CommerceContextType => {
  const context = useContext(CommerceContext);
  if (!context) {
    return {
      cart: null,
      wishlist: null,
      cartCount: 0,
      wishlistCount: 0,
      cartLoading: false,
      cartError: null,
      isCartOpen: false,
      openCart: () => {},
      closeCart: () => {},
      isCheckoutOpen: false,
      openCheckout: () => {},
      closeCheckout: () => {},
      addToCart: async () => {},
      updateCartQuantity: async () => {},
      removeFromCart: async () => {},
      clearCart: async () => {},
      addToWishlist: async () => {},
      removeFromWishlist: async () => {},
      isInWishlist: () => false,
      moveWishlistToCart: async () => {},
      refreshCart: async () => {},
      refreshWishlist: async () => {},
    };
  }
  return context;
};

