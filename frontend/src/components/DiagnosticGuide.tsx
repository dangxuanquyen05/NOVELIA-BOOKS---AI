import React, { useState } from 'react';
import { Terminal, Copy, Check, AlertTriangle, ShieldCheck } from 'lucide-react';

export const DiagnosticGuide: React.FC = () => {
  const [copied, setCopied] = useState(false);

  const sqlCommands = `-- ==============================================================================
-- NOVELIA BOOKS — DATABASE SETUP SCRIPT (Run in MySQL Workbench)
-- ==============================================================================

-- 1. Create development and isolated testing databases
CREATE DATABASE IF NOT EXISTS novelia_books
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS novelia_books_test
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2. (Optional/Recommended) Create a dedicated application user instead of root
-- Replace 'YourStrongPassword123!' with your desired password
-- CREATE USER IF NOT EXISTS 'novelia_app'@'localhost' IDENTIFIED BY 'YourStrongPassword123!';
-- GRANT ALL PRIVILEGES ON novelia_books.* TO 'novelia_app'@'localhost';
-- GRANT ALL PRIVILEGES ON novelia_books_test.* TO 'novelia_app'@'localhost';
-- FLUSH PRIVILEGES;

-- 3. Verify databases created
SHOW DATABASES LIKE 'novelia_%';`;

  const handleCopy = () => {
    navigator.clipboard.writeText(sqlCommands);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="hero-card" style={{ marginTop: '2.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Terminal size={22} color="var(--accent-gold)" />
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#FFFFFF' }}>
            Hướng dẫn Thiết lập MySQL Workbench (Database Setup)
          </h2>
        </div>
        <button
          onClick={handleCopy}
          className="refresh-btn"
          style={{ padding: '0.45rem 1rem', fontSize: '0.8rem', background: 'rgba(255, 255, 255, 0.08)', color: '#FFF' }}
          type="button"
          aria-label="Copy SQL script"
        >
          {copied ? <Check size={16} color="var(--status-success)" /> : <Copy size={16} />}
          {copied ? 'Đã sao chép!' : 'Sao chép mã SQL'}
        </button>
      </div>

      <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '1rem', lineHeight: '1.6' }}>
        Nếu endpoint kiểm tra database báo trạng thái <span style={{ color: 'var(--status-error)', fontWeight: 600 }}>Unhealthy</span> hoặc <span style={{ color: 'var(--status-warning)', fontWeight: 600 }}>Access Denied</span>, hãy mở <strong>MySQL Workbench</strong>, kết nối tới MySQL Server cục bộ (port 3306) và chạy đoạn mã SQL dưới đây. Sau đó cập nhật thông tin tương ứng vào file <code>backend/.env</code>.
      </p>

      <pre className="code-block" style={{ maxHeight: '280px', overflowY: 'auto' }}>
        {sqlCommands}
      </pre>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginTop: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '0.6rem', background: 'rgba(0,0,0,0.2)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <AlertTriangle size={18} color="var(--status-warning)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <strong style={{ color: '#FFF' }}>Nguyên tắc an toàn dữ liệu:</strong> Không commit file <code>.env</code> chứa mật khẩu thực tế lên Git repo. Luôn sử dụng <code>.env.example</code> làm mẫu.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', background: 'rgba(0,0,0,0.2)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <ShieldCheck size={18} color="var(--accent-blue)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <strong style={{ color: '#FFF' }}>Không dùng SQLite trong test:</strong> Database <code>novelia_books_test</code> được tách biệt để phục vụ Pytest tích hợp theo chuẩn kiến trúc.
          </div>
        </div>
      </div>
    </section>
  );
};
