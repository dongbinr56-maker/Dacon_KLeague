"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import UploadDropzone, { UploadState } from "../components/UploadDropzone";
import { SessionPayload, UploadResponse, createSession, listSessions, uploadVideo } from "../lib/api";

interface SessionSummary {
  id: string;
  source_type: string;
  status: string;
}

export default function StartScreen() {
  const router = useRouter();
  const [mode, setMode] = useState<"file" | "rtsp">("file");
  const [rtspUrl, setRtspUrl] = useState("");
  const [fps, setFps] = useState(25);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [uploadState, setUploadState] = useState<UploadState>("IDLE");
  const [uploadError, setUploadError] = useState<string | null>(null);

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

  const createSessionAndGo = async (payload: SessionPayload) => {
    const session = await createSession(payload);
    router.push(`/sessions/${session.id}`);
  };

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploadState("UPLOADING");
    setUploadError(null);
    try {
      const uploaded: UploadResponse = await uploadVideo(file);
      setUploadState("DONE");
      await createSessionAndGo({ source_type: "file", mode: "offline_realtime", fps: 25, file_id: uploaded.file_id });
    } catch (err: any) {
      setUploadState("ERROR");
      setUploadError(err?.message || "업로드에 실패했습니다");
    }
  };

  const handleCreateRtsp = async () => {
    await createSessionAndGo({ source_type: "rtsp", mode: "live", rtsp_url: rtspUrl, fps });
  };

  return (
    <main className="page">
      <section className="card">
        <h1>입력 소스 선택</h1>
        <div className="card-grid">
          <div className="card-inner">
            <div className="card-head">
              <label>
                <input type="radio" name="mode" checked={mode === "file"} onChange={() => setMode("file")} />
                업로드/파일 분석 (Offline-RealTime)
              </label>
            </div>
            {mode === "file" && (
              <UploadDropzone disabled={uploadState === "UPLOADING"} status={uploadState} error={uploadError} onFiles={handleUpload} />
            )}
          </div>
          <div className="card-inner">
            <div className="card-head">
              <label>
                <input type="radio" name="mode" checked={mode === "rtsp"} onChange={() => setMode("rtsp")} />
                RTSP 라이브 (Live)
              </label>
            </div>
            {mode === "rtsp" && (
              <div className="form">
                <label className="input-row">
                  RTSP URL
                  <input value={rtspUrl} onChange={(e) => setRtspUrl(e.target.value)} placeholder="rtsp://..." />
                </label>
                <label className="input-row">
                  FPS (기본 25)
                  <input type="number" value={fps} onChange={(e) => setFps(Number(e.target.value))} />
                </label>
                <button disabled={!rtspUrl} onClick={handleCreateRtsp}>
                  세션 생성
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="header-row">
          <h2>최근 세션</h2>
          <button className="link" onClick={refreshSessions}>
            새로고침
          </button>
        </div>
        <ul className="session-list">
          {sessions.map((s) => (
            <li key={s.id}>
              <div>
                <strong>{s.id}</strong> · {s.source_type} · {s.status}
              </div>
              <div className="actions">
                <button className="link" onClick={() => router.push(`/sessions/${s.id}`)}>
                  이동
                </button>
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
        .card-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
        }
        .card-inner {
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 12px;
          background: #f8fafc;
        }
        .card-head {
          font-weight: 600;
          margin-bottom: 10px;
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
        .header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
      `}</style>
    </main>
  );
}
