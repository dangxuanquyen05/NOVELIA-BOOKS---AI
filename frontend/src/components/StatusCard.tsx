import React from 'react';
import { CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react';

interface StatusCardProps {
  title: string;
  endpoint: string;
  icon: React.ReactNode;
  loading: boolean;
  isHealthy: boolean;
  statusText: string;
  message: string;
  latencyMs: number | null;
  lastChecked: Date | null;
  details?: Record<string, unknown>;
  error?: string | null;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  endpoint,
  icon,
  loading,
  isHealthy,
  statusText,
  message,
  latencyMs,
  lastChecked,
  details,
  error,
}) => {
  const getBadgeClass = () => {
    if (loading) return 'badge-loading';
    if (isHealthy) return 'badge-success';
    return 'badge-error';
  };

  const getStatusIcon = () => {
    if (loading) return <Loader2 size={14} className="spin-icon" />;
    if (isHealthy) return <CheckCircle2 size={14} />;
    return <XCircle size={14} />;
  };

  return (
    <article className="status-card" data-testid={`status-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="card-header">
        <div className="service-identity">
          <div className="service-icon">{icon}</div>
          <div>
            <h3 className="service-name">{title}</h3>
            <span className="service-target">{endpoint}</span>
          </div>
        </div>
        <div className={`badge ${getBadgeClass()}`}>
          {getStatusIcon()}
          <span>{statusText}</span>
        </div>
      </div>

      <div className="card-metrics">
        <div className="metric-item">
          <span className="metric-label">Độ trễ (Latency)</span>
          <span className="metric-value">
            {latencyMs !== null ? `${latencyMs} ms` : '—'}
          </span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Kiểm tra lúc</span>
          <span className="metric-value">
            {lastChecked ? lastChecked.toLocaleTimeString() : 'Chưa kiểm tra'}
          </span>
        </div>
      </div>

      <p className="card-body-text">{message}</p>

      {error && (
        <div className="diagnostic-box" style={{ borderColor: 'rgba(239, 68, 68, 0.35)', background: 'rgba(239, 68, 68, 0.08)' }}>
          <div className="diagnostic-title" style={{ color: 'var(--status-error)' }}>
            <AlertCircle size={16} />
            <span>Chi tiết chẩn đoán lỗi</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#FECACA', lineHeight: '1.4' }}>
            {error}
          </p>
        </div>
      )}

      {details && Object.keys(details).length > 0 && !error && (
        <div className="diagnostic-box">
          <div className="diagnostic-title">
            <span>Thông tin môi trường xác thực</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', fontSize: '0.78rem' }}>
            {Object.entries(details).map(([key, value]) => (
              <div key={key} style={{ background: 'rgba(0,0,0,0.2)', padding: '0.4rem 0.6rem', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', textTransform: 'capitalize' }}>{key}</span>
                <span style={{ color: '#FFF', fontWeight: 600 }}>{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  );
};
