import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import App from '../src/App';

describe('NOVELIA BOOKS — Frontend System Health Monitor', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders application branding and header elements', async () => {
    global.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () =>
          Promise.resolve({
            status: 'healthy',
            service: 'novelia-books-backend',
            version: '1.0.0',
            environment: 'development',
            timestamp: new Date().toISOString(),
          }),
      })
    );

    render(<App />);

    expect(screen.getByText('NOVELIA BOOKS')).toBeInTheDocument();
    expect(screen.getByText(/Phase 1-3: Foundation & Auth RBAC/i)).toBeInTheDocument();
    expect(screen.getByText(/Hướng dẫn Thiết lập MySQL Workbench/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('ONLINE / HEALTHY')).toBeInTheDocument();
    });
  });

  it('displays HEALTHY states when backend and database succeed', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/health/database')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              status: 'healthy',
              database: 'novelia_books',
              message: 'Database query executed successfully',
              details: { database: 'novelia_books', status: 'connected' },
              timestamp: new Date().toISOString(),
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () =>
          Promise.resolve({
            status: 'healthy',
            service: 'novelia-books-backend',
            version: '1.0.0',
            environment: 'development',
            timestamp: new Date().toISOString(),
          }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('ONLINE / HEALTHY')).toBeInTheDocument();
      expect(screen.getByText('CONNECTED / HEALTHY')).toBeInTheDocument();
    });
  });

  it('displays ERROR state when database returns 503 without leaking credentials', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/health/database')) {
        return Promise.resolve({
          ok: false,
          status: 503,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              status: 'unhealthy',
              database: 'novelia_books',
              message: 'Unable to connect to MySQL database server',
              details: { database: 'novelia_books', status: 'disconnected', error_type: 'OperationalError' },
              timestamp: new Date().toISOString(),
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () =>
          Promise.resolve({
            status: 'healthy',
            service: 'novelia-books-backend',
            version: '1.0.0',
            environment: 'development',
            timestamp: new Date().toISOString(),
          }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('ONLINE / HEALTHY')).toBeInTheDocument();
      expect(screen.getByText('UNHEALTHY / ACCESS DENIED')).toBeInTheDocument();
      expect(screen.getAllByText('Unable to connect to MySQL database server').length).toBeGreaterThanOrEqual(1);
    });

    // Ensure zero secrets or actual connection string leaked in the database status card
    const card = screen.getByTestId('status-card-mysql-database');
    const cardText = card.textContent?.toLowerCase() || '';
    expect(cardText).not.toContain('mysql+pymysql');
    expect(cardText).not.toContain('password');
    expect(cardText).not.toContain('root:');
  });

  it('displays OFFLINE state when backend network call fails', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network connection refused on port 8000'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('OFFLINE')).toBeInTheDocument();
      expect(screen.getAllByText(/Network connection refused/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('handles non-JSON error responses gracefully (e.g. 502 HTML Bad Gateway)', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/health/database')) {
        return Promise.resolve({
          ok: false,
          status: 502,
          statusText: 'Bad Gateway',
          headers: new Headers({ 'content-type': 'text/html' }),
          text: () => Promise.resolve('<html><body>502 Bad Gateway</body></html>'),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () =>
          Promise.resolve({
            status: 'healthy',
            service: 'novelia-books-backend',
            version: '1.0.0',
            environment: 'development',
            timestamp: new Date().toISOString(),
          }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('ONLINE / HEALTHY')).toBeInTheDocument();
      expect(screen.getByText('UNHEALTHY / ACCESS DENIED')).toBeInTheDocument();
      expect(screen.getAllByText(/502/).length).toBeGreaterThanOrEqual(1);
    });
  });
});
