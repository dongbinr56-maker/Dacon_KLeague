"use client";

import { useEffect, useRef, useState } from "react";

import {
  SessionPayload,
  UploadResponse,
  createSession,
  listSessions,
  uploadVideo,
} from "../lib/api";

type UploadState = "IDLE" | "UPLOADING" | "DONE" | "ERROR";

interface Session {
  id: string;
  source_type: string;
  mode: string;
  status: string;
  download_url?: string | null;
}

export default function StartScreen() {
  const [mode, setMode] = useState<"file" | "rtsp">("file");
  const [rtspUrl, setRtspUrl] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [uploadState, setUploadState] = useState<UploadState>("IDLE");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [lastUpload, setLastUpload] = useState<UploadResponse | null>(null);
  const dropRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    refreshSessions();
  }, []);

  const refreshSessions = async () => {
    try {
      const data = await listSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploadState("UPLOADING");
    setUploadError(null);
    try {
      const uploaded = await uploadVideo(file);
      setLastUpload(uploaded);
      setUploadState("DONE");
      await createSessionAndGo({ source_type: "file", mode: "offline_realtime", file_id: uploaded.file_id });
    } catch (err: any) {
      setUploadState("ERROR");
      setUploadError(err?.message || "업로드에 실패했습니다");
    }
  };

  const createSessionAndGo = async (payload: SessionPayload) => {
    const session = await createSession(payload);
    window.location.href = `/sessions/${session.id}`;
  };

  const onDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    await handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <main className="page">
      <section className="card">
        <h1>입력 소스 선택</h1>
        <div className="radio-group">
          <label>
            <input
              type="radio"
              name="mode"
              value="file"
              checked={mode === "file"}
              onChange={() => setMode("file")}
            />
            업로드/파일 기반 (Offline-RealTime)
          </label>
          <label>
            <input
              type="radio"
              name="mode"
              value="rtsp"
              checked={mode === "rtsp"}
              onChange={() => setMode("rtsp")}
            />
            라이브 RTSP (Live)
          </label>
        </div>

        {mode === "file" ? (
          <div className="upload-box" onDrop={onDrop} onDragOver={onDragOver} ref={dropRef}>
            <p>여기로 파일을 Drag & Drop 하거나 아래 버튼으로 선택하세요.</p>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => handleFiles(e.target.files)}
              disabled={uploadState === "UPLOADING"}
            />
            <div className="upload-status">
              상태: {uploadState}
              {uploadError && <span className="error">{uploadError}</span>}
            </div>
          </div>
        ) : (
          <div className="form">
            <label className="input-row">
              RTSP URL
              <input value={rtspUrl} onChange={(e) => setRtspUrl(e.target.value)} placeholder="rtsp://..." />
            </label>
            <button
              disabled={!rtspUrl}
              onClick={() =>
                createSessionAndGo({ source_type: "rtsp", mode: "live", rtsp_url: rtspUrl, fps: 25, buffer_ms: 300 })
              }
            >
              세션 생성
            </button>
          </div>
        )}
      </section>

      <section className="card">
        <h2>최근 세션</h2>
        <button className="link" onClick={refreshSessions}>
          새로고침
        </button>
        <ul className="session-list">
          {sessions.map((s) => (
            <li key={s.id}>
              <div>
                <strong>{s.id}</strong> · {s.source_type} · {s.status}
              </div>
              <div className="actions">
                <a className="link" href={`/sessions/${s.id}`}>
                  이동
                </a>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <style jsx>{`
        .page {
          max-width: 960px;
          margin: 0 auto;
          padding: 24px;
          font-family: Inter, system-ui, -apple-system, sans-serif;
        }
        .card {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 16px;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        }
        .radio-group {
          display: flex;
          gap: 16px;
          margin-bottom: 12px;
        }
        .upload-box {
          border: 2px dashed #cbd5e1;
          border-radius: 10px;
          padding: 16px;
          text-align: center;
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
        .form {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .input-row {
          display: flex;
          flex-direction: column;
          gap: 6px;
          font-size: 0.95rem;
        }
        .input-row input {
          border: 1px solid #cbd5e1;
          border-radius: 8px;
          padding: 8px 10px;
        }
        button {
          background: #0ea5e9;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 10px 14px;
          cursor: pointer;
        }
        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .session-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .session-list li {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 12px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          background: #f8fafc;
        }
        .link {
          color: #0f172a;
          text-decoration: underline;
          background: none;
          border: none;
          cursor: pointer;
          padding: 0;
        }
      `}</style>
    </main>
  );
}
