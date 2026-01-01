"use client";

interface Props {
  downloadUrl?: string | null;
  sourceType: string;
}

export default function VideoWithOverlay({ downloadUrl, sourceType }: Props) {
  const isFile = sourceType === "file";

  return (
    <div className="video-panel">
      {isFile && downloadUrl ? (
        <div className="video-container">
          <div className="video-wrapper">
            <video src={downloadUrl} controls className="video-player" preload="metadata" />
            <canvas className="overlay" aria-label="overlay" />
          </div>
          <div className="video-info">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <span className="info-text">비디오 위에 분석 오버레이가 표시됩니다</span>
          </div>
        </div>
      ) : (
        <div className="placeholder">
          <div className="placeholder-content">
            <div className="placeholder-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <polygon points="23 7 16 12 23 17 23 7" />
                <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
              </svg>
            </div>
            <h3 className="placeholder-title">라이브 스트림 모드</h3>
            <p className="placeholder-text">
              라이브 입력은 브라우저에서 직접 재생하지 않고
              <br />
              실시간 상태 및 알림만 표시합니다
            </p>
            <div className="placeholder-features">
              <div className="feature-item">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10" />
                  <polyline points="1 20 1 14 7 14" />
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                </svg>
                <span>실시간 분석</span>
              </div>
              <div className="feature-item">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                <span>즉시 알림</span>
              </div>
              <div className="feature-item">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                </svg>
                <span>저지연 처리</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .video-panel {
          width: 100%;
        }

        .video-container {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .video-wrapper {
          position: relative;
          width: 100%;
          background: #000;
          border-radius: var(--radius-lg);
          overflow: hidden;
          box-shadow: var(--shadow-xl);
        }

        .video-player {
          width: 100%;
          height: auto;
          display: block;
          max-height: 70vh;
        }

        .overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          border: 2px dashed rgba(233, 69, 96, 0.5);
          border-radius: var(--radius-lg);
        }

        .video-info {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-4);
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: var(--radius-lg);
        }

        .video-info svg {
          color: var(--info-light);
          flex-shrink: 0;
        }

        .info-text {
          font-size: var(--text-sm);
          color: var(--gray-300);
          font-weight: 500;
        }

        .placeholder {
          min-height: 400px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.03);
          border: 2px dashed rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-xl);
          padding: var(--space-12);
        }

        .placeholder-content {
          text-align: center;
          max-width: 500px;
        }

        .placeholder-icon {
          margin-bottom: var(--space-6);
          color: var(--gray-500);
        }

        .placeholder-title {
          font-size: var(--text-xl);
          font-weight: 700;
          color: var(--gray-200);
          margin-bottom: var(--space-4);
          letter-spacing: -0.02em;
        }

        .placeholder-text {
          font-size: var(--text-sm);
          color: var(--gray-400);
          line-height: 1.7;
          margin-bottom: var(--space-8);
        }

        .placeholder-features {
          display: flex;
          justify-content: center;
          gap: var(--space-6);
          flex-wrap: wrap;
        }

        .feature-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-5);
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-lg);
          min-width: 120px;
          transition: all var(--transition-base);
        }

        .feature-item:hover {
          background: rgba(255, 255, 255, 0.06);
          transform: translateY(-2px);
        }

        .feature-item svg {
          color: var(--accent);
        }

        .feature-item span {
          font-size: var(--text-xs);
          font-weight: 600;
          color: var(--gray-300);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        @media (max-width: 768px) {
          .placeholder {
            min-height: 300px;
            padding: var(--space-8);
          }

          .placeholder-icon {
            margin-bottom: var(--space-4);
          }

          .placeholder-title {
            font-size: var(--text-lg);
          }

          .placeholder-features {
            gap: var(--space-4);
          }

          .feature-item {
            min-width: 100px;
            padding: var(--space-4);
          }
        }
      `}</style>
    </div>
  );
}
