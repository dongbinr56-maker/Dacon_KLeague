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
        <div className="video-wrap">
          <video src={downloadUrl} controls width="100%" />
          <canvas className="overlay" aria-label="overlay" />
        </div>
      ) : (
        <div className="placeholder">라이브 입력은 브라우저에서 직접 재생하지 않고 상태/알림만 표시합니다.</div>
      )}
      <style jsx>{`
        .video-panel {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 12px;
        }
        .video-wrap {
          position: relative;
        }
        .overlay {
          position: absolute;
          inset: 0;
          pointer-events: none;
          border: 1px dashed #cbd5e1;
        }
        .placeholder {
          height: 320px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f8fafc;
          color: #475569;
          border: 1px dashed #cbd5e1;
          border-radius: 8px;
        }
      `}</style>
    </div>
  );
}
