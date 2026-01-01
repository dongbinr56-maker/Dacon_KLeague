"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import UploadDropzone, { UploadState } from "../components/UploadDropzone";
import { SessionPayload, UploadResponse, createSession, listGames, listSessions, uploadVideo } from "../lib/api";

interface SessionSummary {
  id: string;
  source_type: string;
  status: string;
}

export default function StartScreen() {
  const router = useRouter();
  const [mode, setMode] = useState<"file" | "rtsp" | "event_log">("event_log");
  const [rtspUrl, setRtspUrl] = useState("");
  const [fps, setFps] = useState(25);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [uploadState, setUploadState] = useState<UploadState>("IDLE");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [games, setGames] = useState<{ game_id: string; home_team?: string; away_team?: string; match_date?: string }[]>([]);
  const [selectedGame, setSelectedGame] = useState<string>("");
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(5);
  const [gameLoadError, setGameLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    refreshSessions();
    preloadGames();
  }, []);

  const refreshSessions = async () => {
    try {
      const data = await listSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error(err);
    }
  };

  const preloadGames = async () => {
    try {
      const res = await listGames();
      setGames(res.games || []);
      if (res.games && res.games.length > 0) {
        setSelectedGame(res.games[0].game_id);
      }
    } catch (err: any) {
      setGameLoadError(err?.message || "Track2 game 목록을 불러오지 못했습니다");
    }
  };

  const createSessionAndGo = async (payload: SessionPayload) => {
    setIsLoading(true);
    try {
      const session = await createSession(payload);
      router.push(`/sessions/${session.id}`);
    } catch (err: any) {
      console.error(err);
      setIsLoading(false);
    }
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
    if (!rtspUrl.trim()) return;
    await createSessionAndGo({ source_type: "rtsp", mode: "live", rtsp_url: rtspUrl, fps });
  };

  const handleCreateEventLog = async () => {
    if (!selectedGame) return;
    await createSessionAndGo({
      source_type: "event_log",
      mode: "offline_realtime",
      game_id: selectedGame,
      playback_speed: playbackSpeed,
    });
  };

  const getStatusBadge = (status: string) => {
    const statusLower = status?.toLowerCase() || "unknown";
    const statusMap: Record<string, { label: string; class: string }> = {
      running: { label: "실행 중", class: "badge-success" },
      connecting: { label: "연결 중", class: "badge-warning" },
      created: { label: "생성됨", class: "badge-neutral" },
      stopped: { label: "중지됨", class: "badge-neutral" },
      lost: { label: "연결 끊김", class: "badge-danger" },
    };
    const statusInfo = statusMap[statusLower] || { label: status || "알 수 없음", class: "badge-neutral" };
    return <span className={`badge ${statusInfo.class}`}>{statusInfo.label}</span>;
  };

  return (
    <main className="page">
      <header className="header animate-fade-in">
        <div className="header-content">
          <h1 className="title">K리그 전술 분석</h1>
          <p className="subtitle">AI 기반 실시간 경기 분석 및 전술 피드백 시스템</p>
        </div>
      </header>

      <section className="main-section animate-fade-in">
        <div className="section-header">
          <h2 className="section-title">입력 소스 선택</h2>
          <div className="section-divider"></div>
        </div>

        <div className="mode-grid">
          {/* Event Log Option */}
          <div className={`mode-card ${mode === "event_log" ? "active" : ""}`}>
            <div className="mode-header" onClick={() => setMode("event_log")}>
              <input
                type="radio"
                name="mode"
                checked={mode === "event_log"}
                onChange={() => setMode("event_log")}
                className="mode-radio"
              />
              <div className="mode-info">
                <div className="mode-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 3v18h18" />
                    <path d="M7 12l4-4 4 4 4-4" />
                  </svg>
                </div>
                <div>
                  <h3 className="mode-title">이벤트 로그</h3>
                  <p className="mode-desc">Track2 데이터 기반 오프라인 분석</p>
                </div>
              </div>
            </div>
            {mode === "event_log" && (
              <div className="mode-content animate-slide-in">
                {gameLoadError ? (
                  <div className="error-message">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    {gameLoadError}
                  </div>
                ) : (
                  <>
                    <div className="form-group">
                      <label className="form-label">경기 선택</label>
                      <select
                        value={selectedGame}
                        onChange={(e) => setSelectedGame(e.target.value)}
                        className="select"
                        disabled={isLoading}
                      >
                        {games.map((g) => (
                          <option key={g.game_id} value={g.game_id}>
                            {g.game_id}
                            {g.home_team && ` · ${g.home_team} vs ${g.away_team || ""}`}
                            {g.match_date && ` · ${g.match_date}`}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">
                        재생 속도: <span className="speed-value">{playbackSpeed}x</span>
                      </label>
                      <div className="slider-container">
                        <input
                          type="range"
                          min={1}
                          max={60}
                          value={playbackSpeed}
                          onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                          className="slider"
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                    <button
                      className="btn btn-primary btn-block"
                      onClick={handleCreateEventLog}
                      disabled={!selectedGame || isLoading}
                    >
                      {isLoading ? (
                        <>
                          <span className="spinner"></span>
                          생성 중
                        </>
                      ) : (
                        "세션 생성"
                      )}
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

          {/* File Upload Option */}
          <div className={`mode-card ${mode === "file" ? "active" : ""}`}>
            <div className="mode-header" onClick={() => setMode("file")}>
              <input
                type="radio"
                name="mode"
                checked={mode === "file"}
                onChange={() => setMode("file")}
                className="mode-radio"
              />
              <div className="mode-info">
                <div className="mode-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </div>
                <div>
                  <h3 className="mode-title">파일 업로드</h3>
                  <p className="mode-desc">MP4 비디오 파일 분석</p>
                </div>
              </div>
            </div>
            {mode === "file" && (
              <div className="mode-content animate-slide-in">
                <UploadDropzone
                  disabled={uploadState === "UPLOADING" || isLoading}
                  status={uploadState}
                  error={uploadError}
                  onFiles={handleUpload}
                />
              </div>
            )}
          </div>

          {/* RTSP Option */}
          <div className={`mode-card ${mode === "rtsp" ? "active" : ""}`}>
            <div className="mode-header" onClick={() => setMode("rtsp")}>
              <input
                type="radio"
                name="mode"
                checked={mode === "rtsp"}
                onChange={() => setMode("rtsp")}
                className="mode-radio"
              />
              <div className="mode-info">
                <div className="mode-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="23 7 16 12 23 17 23 7" />
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
                  </svg>
                </div>
                <div>
                  <h3 className="mode-title">라이브 스트림</h3>
                  <p className="mode-desc">RTSP 실시간 분석</p>
                </div>
              </div>
            </div>
            {mode === "rtsp" && (
              <div className="mode-content animate-slide-in">
                <div className="form-group">
                  <label className="form-label">RTSP URL</label>
                  <input
                    type="text"
                    value={rtspUrl}
                    onChange={(e) => setRtspUrl(e.target.value)}
                    placeholder="rtsp://example.com/stream"
                    className="input"
                    disabled={isLoading}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">FPS</label>
                  <input
                    type="number"
                    min={1}
                    max={60}
                    value={fps}
                    onChange={(e) => setFps(Number(e.target.value))}
                    className="input"
                    disabled={isLoading}
                  />
                </div>
                <button
                  className="btn btn-primary btn-block"
                  onClick={handleCreateRtsp}
                  disabled={!rtspUrl.trim() || isLoading}
                >
                  {isLoading ? (
                    <>
                      <span className="spinner"></span>
                      생성 중
                    </>
                  ) : (
                    "세션 생성"
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="sessions-section animate-fade-in">
        <div className="section-header">
          <h2 className="section-title">최근 세션</h2>
          <button className="btn btn-secondary btn-sm" onClick={refreshSessions}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
            새로고침
          </button>
        </div>
        <div className="section-divider"></div>

        {sessions.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
            </div>
            <p className="empty-text">아직 생성된 세션이 없습니다</p>
          </div>
        ) : (
          <div className="sessions-list">
            {sessions.map((s) => (
              <div key={s.id} className="session-item" onClick={() => router.push(`/sessions/${s.id}`)}>
                <div className="session-info">
                  <div className="session-id font-mono">{s.id.slice(0, 8)}...</div>
                  <div className="session-meta">
                    <span className="session-type">{s.source_type}</span>
                    <span className="session-separator">·</span>
                    {getStatusBadge(s.status)}
                  </div>
                </div>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(`/sessions/${s.id}`);
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      <style jsx>{`
        .page {
          max-width: 1400px;
          margin: 0 auto;
          padding: var(--space-8) var(--space-6);
          min-height: 100vh;
        }

        .header {
          text-align: center;
          margin-bottom: var(--space-16);
        }

        .header-content {
          max-width: 800px;
          margin: 0 auto;
        }

        .title {
          font-size: var(--text-4xl);
          font-weight: 800;
          margin-bottom: var(--space-4);
          background: linear-gradient(135deg, var(--gray-50) 0%, var(--gray-300) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: -0.03em;
        }

        .subtitle {
          font-size: var(--text-lg);
          color: var(--gray-400);
          font-weight: 400;
        }

        .main-section,
        .sessions-section {
          margin-bottom: var(--space-12);
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-6);
        }

        .section-title {
          font-size: var(--text-2xl);
          font-weight: 700;
          color: var(--gray-100);
          letter-spacing: -0.02em;
        }

        .section-divider {
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
          margin-bottom: var(--space-8);
        }

        .mode-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: var(--space-6);
        }

        .mode-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-xl);
          padding: var(--space-6);
          transition: all var(--transition-base);
          cursor: pointer;
        }

        .mode-card:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.2);
          transform: translateY(-2px);
        }

        .mode-card.active {
          background: rgba(255, 255, 255, 0.08);
          border-color: var(--accent);
          box-shadow: 0 0 0 1px var(--accent), var(--shadow-xl);
        }

        .mode-header {
          display: flex;
          align-items: flex-start;
          gap: var(--space-4);
          margin-bottom: var(--space-4);
        }

        .mode-radio {
          margin-top: var(--space-1);
          width: 20px;
          height: 20px;
          cursor: pointer;
          accent-color: var(--accent);
        }

        .mode-info {
          display: flex;
          gap: var(--space-4);
          flex: 1;
        }

        .mode-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-lg);
          color: var(--accent);
          flex-shrink: 0;
        }

        .mode-title {
          font-size: var(--text-lg);
          font-weight: 700;
          margin-bottom: var(--space-1);
          color: var(--gray-100);
        }

        .mode-desc {
          font-size: var(--text-sm);
          color: var(--gray-400);
        }

        .mode-content {
          margin-top: var(--space-4);
          padding-top: var(--space-4);
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .form-group {
          margin-bottom: var(--space-5);
        }

        .form-label {
          display: block;
          font-size: var(--text-sm);
          font-weight: 600;
          color: var(--gray-300);
          margin-bottom: var(--space-2);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .speed-value {
          color: var(--accent);
          font-weight: 700;
        }

        .slider-container {
          margin-top: var(--space-3);
        }

        .slider {
          width: 100%;
          height: 6px;
          border-radius: var(--radius-full);
          background: rgba(255, 255, 255, 0.1);
          outline: none;
          -webkit-appearance: none;
          cursor: pointer;
        }

        .slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: var(--radius-full);
          background: var(--accent);
          cursor: pointer;
          box-shadow: var(--shadow-md);
          transition: all var(--transition-base);
        }

        .slider::-webkit-slider-thumb:hover {
          transform: scale(1.1);
          box-shadow: var(--shadow-lg);
        }

        .btn-block {
          width: 100%;
          margin-top: var(--space-4);
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-4);
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: var(--radius-md);
          color: var(--danger-light);
          font-size: var(--text-sm);
        }

        .error-message svg {
          flex-shrink: 0;
        }

        .sessions-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
        }

        .session-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--space-5);
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-lg);
          cursor: pointer;
          transition: all var(--transition-base);
        }

        .session-item:hover {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(255, 255, 255, 0.2);
          transform: translateX(4px);
        }

        .session-info {
          flex: 1;
        }

        .session-id {
          font-size: var(--text-sm);
          font-weight: 700;
          color: var(--gray-100);
          margin-bottom: var(--space-2);
        }

        .session-meta {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--text-xs);
          color: var(--gray-400);
        }

        .session-type {
          text-transform: capitalize;
        }

        .session-separator {
          color: var(--gray-600);
        }

        .empty-state {
          text-align: center;
          padding: var(--space-16) var(--space-8);
          color: var(--gray-500);
        }

        .empty-icon {
          margin-bottom: var(--space-4);
          color: var(--gray-600);
        }

        .empty-text {
          font-size: var(--text-sm);
          color: var(--gray-500);
        }

        @media (max-width: 768px) {
          .page {
            padding: var(--space-6) var(--space-4);
          }

          .title {
            font-size: var(--text-3xl);
          }

          .mode-grid {
            grid-template-columns: 1fr;
          }

          .section-header {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--space-4);
          }
        }
      `}</style>
    </main>
  );
}
