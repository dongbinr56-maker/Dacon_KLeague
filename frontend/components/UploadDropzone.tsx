"use client";

import React, { useCallback, useState } from "react";

export type UploadState = "IDLE" | "UPLOADING" | "DONE" | "ERROR";

interface Props {
  disabled?: boolean;
  status: UploadState;
  error?: string | null;
  onFiles: (files: FileList | null) => Promise<void> | void;
}

export default function UploadDropzone({ disabled, status, error, onFiles }: Props) {
  const [isDragging, setDragging] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    async (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (disabled) return;
      setDragging(false);
      await onFiles(e.dataTransfer.files);
    },
    [disabled, onFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (disabled) return;
    setDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleClick = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [disabled]);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      await onFiles(e.target.files);
    },
    [onFiles]
  );

  return (
    <div
      className={`dropzone ${isDragging ? "dragging" : ""} ${status === "UPLOADING" ? "uploading" : ""} ${status === "DONE" ? "done" : ""} ${status === "ERROR" ? "error" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*"
        onChange={handleFileChange}
        disabled={disabled}
        className="file-input"
      />

      <div className="dropzone-content">
        {status === "UPLOADING" ? (
          <>
            <div className="upload-icon">
              <div className="spinner"></div>
            </div>
            <p className="dropzone-text">업로드 중</p>
            <p className="dropzone-hint">잠시만 기다려주세요</p>
          </>
        ) : status === "DONE" ? (
          <>
            <div className="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <p className="dropzone-text">업로드 완료</p>
            <p className="dropzone-hint">세션이 생성되었습니다</p>
          </>
        ) : status === "ERROR" ? (
          <>
            <div className="upload-icon error">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <p className="dropzone-text">업로드 실패</p>
            {error && <p className="dropzone-error">{error}</p>}
          </>
        ) : (
          <>
            <div className="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p className="dropzone-text">
              {isDragging ? "여기에 놓으세요" : "파일을 드래그하거나 클릭하세요"}
            </p>
            <p className="dropzone-hint">MP4 비디오 파일만 지원됩니다</p>
            <button
              className="btn btn-primary"
              onClick={(e) => {
                e.stopPropagation();
                handleClick();
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              파일 선택
            </button>
          </>
        )}
      </div>

      <style jsx>{`
        .dropzone {
          position: relative;
          border: 2px dashed rgba(255, 255, 255, 0.2);
          border-radius: var(--radius-xl);
          padding: var(--space-12);
          text-align: center;
          background: rgba(255, 255, 255, 0.03);
          transition: all var(--transition-base);
          cursor: pointer;
          min-height: 240px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .dropzone:hover:not(.uploading):not(.done):not(.error) {
          border-color: rgba(255, 255, 255, 0.4);
          background: rgba(255, 255, 255, 0.05);
          transform: scale(1.01);
        }

        .dropzone.dragging {
          border-color: var(--accent);
          background: rgba(233, 69, 96, 0.1);
          border-style: solid;
          transform: scale(1.02);
          box-shadow: 0 0 0 4px rgba(233, 69, 96, 0.1);
        }

        .dropzone.uploading {
          border-color: var(--info);
          background: rgba(59, 130, 246, 0.05);
          cursor: wait;
        }

        .dropzone.done {
          border-color: var(--success);
          background: rgba(16, 185, 129, 0.05);
        }

        .dropzone.error {
          border-color: var(--danger);
          background: rgba(239, 68, 68, 0.05);
        }

        .file-input {
          position: absolute;
          width: 0;
          height: 0;
          opacity: 0;
          pointer-events: none;
        }

        .dropzone-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-4);
          width: 100%;
        }

        .upload-icon {
          margin-bottom: var(--space-2);
          color: var(--gray-400);
          transition: color var(--transition-base);
        }

        .dropzone.dragging .upload-icon,
        .dropzone:hover:not(.uploading):not(.done):not(.error) .upload-icon {
          color: var(--accent);
        }

        .upload-icon.error {
          color: var(--danger);
        }

        .dropzone.done .upload-icon {
          color: var(--success);
        }

        .dropzone-text {
          font-size: var(--text-lg);
          font-weight: 700;
          color: var(--gray-200);
          margin: 0;
        }

        .dropzone-hint {
          font-size: var(--text-sm);
          color: var(--gray-500);
          margin: 0;
        }

        .dropzone-error {
          font-size: var(--text-sm);
          color: var(--danger-light);
          font-weight: 600;
          margin: var(--space-2) 0 0 0;
          padding: var(--space-3) var(--space-4);
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: var(--radius-md);
        }

        .dropzone .btn {
          margin-top: var(--space-4);
        }
      `}</style>
    </div>
  );
}
