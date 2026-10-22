import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { NoveliaAIAssistant } from '../src/components/NoveliaAIAssistant';
import { AuthProvider } from '../src/context/AuthContext';
import { CommerceProvider } from '../src/context/CommerceContext';
import * as aiApi from '../src/services/aiApi';
import { AIChatResponse, AIHealthStatus } from '../src/types/ai';

const mockLocalStorage: Record<string, string> = {};

beforeEach(() => {
  vi.restoreAllMocks();
  Object.keys(mockLocalStorage).forEach((k) => delete mockLocalStorage[k]);
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation((k) => mockLocalStorage[k] || null);
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation((k, v) => {
    mockLocalStorage[k] = v;
  });
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation((k) => {
    delete mockLocalStorage[k];
  });
  Element.prototype.scrollIntoView = vi.fn();
});

const mockHealth: AIHealthStatus = {
  status: 'MOCK_READY',
  provider: 'mock',
  model: 'mock-gpt-v1',
  is_configured: true,
  details: 'Mock AI Provider đang sẵn sàng phục vụ.',
};

const renderAssistant = (onSelectBook = vi.fn()) => {
  return render(
    <AuthProvider>
      <CommerceProvider>
        <NoveliaAIAssistant onSelectBook={onSelectBook} />
      </CommerceProvider>
    </AuthProvider>
  );
};

describe('NoveliaAIAssistant Component (Phase 9)', () => {
  it('renders floating trigger button with Novelia AI branding', async () => {
    vi.spyOn(aiApi, 'fetchAIHealth').mockResolvedValueOnce(mockHealth);

    renderAssistant();

    await waitFor(() => {
      const triggerBtn = screen.getByLabelText('Mở Trợ lý Novelia AI');
      expect(triggerBtn).toBeInTheDocument();
      expect(screen.getByText(/Novelia AI/i)).toBeInTheDocument();
    });
  });

  it('opens chat window on click and displays greeting with health status badge', async () => {
    vi.spyOn(aiApi, 'fetchAIHealth').mockResolvedValueOnce(mockHealth);

    renderAssistant();

    const triggerBtn = screen.getByLabelText('Mở Trợ lý Novelia AI');
    fireEvent.click(triggerBtn);

    expect(screen.getByText('Novelia AI Assistant')).toBeInTheDocument();
    expect(screen.getByText(/Chuyên viên tư vấn sách và hỗ trợ mua sắm/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Novelia AI (Mock)')).toBeInTheDocument();
    });
  });

  it('sends user message and displays AI response', async () => {
    vi.spyOn(aiApi, 'fetchAIHealth').mockResolvedValueOnce(mockHealth);

    const mockResponse: AIChatResponse = {
      session_uuid: 'nvl_sess_test',
      message: 'Dạ, Novelia Books xin gợi ý cuốn sách Đắc Nhân Tâm!',
      suggested_prompts: ['📚 Xem sách kinh tế khác'],
      created_at: new Date().toISOString(),
    };
    const sendSpy = vi.spyOn(aiApi, 'sendAIChat').mockResolvedValueOnce(mockResponse);

    renderAssistant();

    // Open chat
    fireEvent.click(screen.getByLabelText('Mở Trợ lý Novelia AI'));

    const input = screen.getByPlaceholderText(/Hỏi về sách, tồn kho, đơn hàng, ship.../i);
    fireEvent.change(input, { target: { value: 'Gợi ý sách hay' } });

    // Submit form
    const form = input.closest('form')!;
    fireEvent.submit(form);

    expect(screen.getByText('Gợi ý sách hay')).toBeInTheDocument();

    await waitFor(() => {
      expect(sendSpy).toHaveBeenCalled();
      expect(screen.getByText(/Novelia Books xin gợi ý cuốn sách Đắc Nhân Tâm!/i)).toBeInTheDocument();
    });
  });

  it('clicking suggested prompt triggers immediate message send', async () => {
    vi.spyOn(aiApi, 'fetchAIHealth').mockResolvedValueOnce(mockHealth);

    const mockResponse: AIChatResponse = {
      session_uuid: 'nvl_sess_test',
      message: 'Dạ, đây là các tựa sách kinh tế tiêu biểu:',
      suggested_prompts: [],
      created_at: new Date().toISOString(),
    };
    const sendSpy = vi.spyOn(aiApi, 'sendAIChat').mockResolvedValueOnce(mockResponse);

    renderAssistant();

    fireEvent.click(screen.getByLabelText('Mở Trợ lý Novelia AI'));

    const chip = screen.getByText('📚 Gợi ý sách kinh tế nổi bật');
    fireEvent.click(chip);

    await waitFor(() => {
      expect(sendSpy).toHaveBeenCalledWith(null, '📚 Gợi ý sách kinh tế nổi bật', expect.any(String));
      expect(screen.getByText(/đây là các tựa sách kinh tế tiêu biểu/i)).toBeInTheDocument();
    });
  });

  it('renders structured book recommendations and triggers book selection callback', async () => {
    vi.spyOn(aiApi, 'fetchAIHealth').mockResolvedValueOnce(mockHealth);
    const onSelectBookMock = vi.fn();

    const mockResponse: AIChatResponse = {
      session_uuid: 'nvl_sess_test',
      message: 'Novelia Books tìm thấy tác phẩm này:',
      suggested_prompts: [],
      structured_payload: {
        books: [
          {
            id: 42,
            title: 'Chiến Tranh Tiền Tệ',
            slug: 'chien-tranh-tien-te',
            price: 135000,
            primary_author: 'Song Hongbing',
            cover_image_url: 'https://images.unsplash.com/money.jpg',
            available_stock: 15,
            is_in_stock: true,
          },
        ],
      },
      created_at: new Date().toISOString(),
    };
    vi.spyOn(aiApi, 'sendAIChat').mockResolvedValueOnce(mockResponse);

    renderAssistant(onSelectBookMock);

    fireEvent.click(screen.getByLabelText('Mở Trợ lý Novelia AI'));

    const input = screen.getByPlaceholderText(/Hỏi về sách/i);
    fireEvent.change(input, { target: { value: 'Sách kinh tế' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText('Chiến Tranh Tiền Tệ')).toBeInTheDocument();
      expect(screen.getByText('Song Hongbing')).toBeInTheDocument();
      expect(screen.getByText('135.000 đ')).toBeInTheDocument();
    });

    // Click "Chi tiết"
    const detailBtn = screen.getByText(/Chi tiết/i);
    fireEvent.click(detailBtn);
    expect(onSelectBookMock).toHaveBeenCalledWith(42);
  });
});
