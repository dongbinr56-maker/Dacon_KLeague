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

  return (
    <div
      className={`dropzone ${isDragging ? "dragging" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <p>여기로 파일을 Drag & Drop 하거나 아래 버튼으로 선택하세요.</p>
      <input
        type="file"
        accept="video/*"
        onChange={(e) => onFiles(e.target.files)}
        disabled={disabled}
      />
      <div className="upload-status">
        상태: {status}
        {error && <span className="error">{error}</span>}
      </div>
      <style jsx>{`
        .dropzone {
          border: 2px dashed #cbd5e1;
          border-radius: 10px;
          padding: 16px;
          text-align: center;
          background: #f8fafc;
          transition: background 0.2s ease;
        }
        .dropzone.dragging {
          background: #e0f2fe;
        }
        .upload-status {
          margin-top: 8px;
          font-size: 0.9rem;
          color: #475569;
        }
        .error {
          color: #b91c1c;
          margin-left: 8px;
        }
        input[type="file"] {
          margin-top: 10px;
        }
      `}</style>
    </div>
  );
}
