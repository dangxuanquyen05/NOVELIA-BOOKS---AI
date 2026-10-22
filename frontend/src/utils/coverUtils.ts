/**
 * NOVELIA BOOKS — Editorial Cover Utilities
 * Generates an SVG fallback book cover with gold foil border & serif typography.
 */
export const generateFallbackCover = (title: string, author?: string | null): string => {
  const safeTitle = (title || 'Tác Phẩm Tuyển Chọn').slice(0, 45);
  const safeAuthor = (author || 'NOVELIA BOOKS').slice(0, 30);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 600" width="100%" height="100%">
    <defs>
      <linearGradient id="bookCoverGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#1A2538"/>
        <stop offset="50%" stop-color="#24324A"/>
        <stop offset="100%" stop-color="#0E1726"/>
      </linearGradient>
      <linearGradient id="goldBorder" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#E5A869"/>
        <stop offset="50%" stop-color="#C27D38"/>
        <stop offset="100%" stop-color="#8C531E"/>
      </linearGradient>
    </defs>
    <rect width="400" height="600" fill="url(#bookCoverGrad)"/>
    <rect x="20" y="20" width="360" height="560" fill="none" stroke="url(#goldBorder)" stroke-width="2" rx="4"/>
    <rect x="26" y="26" width="348" height="548" fill="none" stroke="rgba(194, 125, 56, 0.4)" stroke-width="1" rx="2"/>
    <line x1="42" y1="0" x2="42" y2="600" stroke="rgba(0,0,0,0.35)" stroke-width="3"/>
    <line x1="44" y1="0" x2="44" y2="600" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
    <text x="200" y="95" font-family="Georgia,serif" font-size="12" font-weight="700" fill="#C27D38" text-anchor="middle" letter-spacing="3">NOVELIA BOOKS</text>
    <circle cx="200" cy="125" r="12" fill="none" stroke="#C27D38" stroke-width="1.5"/>
    <text x="200" y="130" font-family="Georgia,serif" font-size="12" fill="#C27D38" text-anchor="middle">✦</text>
    <foreignObject x="45" y="170" width="310" height="230">
      <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;align-items:center;justify-content:center;height:100%;text-align:center;padding:12px;">
        <h2 style="font-family:Georgia,serif;font-size:22px;color:#FAF8F5;margin:0;line-height:1.4;font-weight:700;">${safeTitle}</h2>
      </div>
    </foreignObject>
    <line x1="120" y1="425" x2="280" y2="425" stroke="url(#goldBorder)" stroke-width="1"/>
    <text x="200" y="465" font-family="system-ui,sans-serif" font-size="13" fill="#D1D5DB" text-anchor="middle" font-weight="500">${safeAuthor}</text>
    <text x="200" y="535" font-family="system-ui,sans-serif" font-size="10" fill="#9CA3AF" text-anchor="middle" letter-spacing="2">ẤN BẢN XUẤT BẢN ĐẶC BIỆT</text>
  </svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
};
