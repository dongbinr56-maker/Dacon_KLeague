"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import AlertsPanel from "../../../components/AlertsPanel";
import VideoWithOverlay from "../../../components/VideoWithOverlay";
import { Alert, Session, getAlerts, getSession, startSession, stopSession } from "../../../lib/api";
import { connectSessionWs } from "../../../lib/ws";

interface Props {
  params: { id: string };
}

export default function SessionPage({ params }: Props) {
  const { id } = params;
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [patternFilter, setPatternFilter] = useState<string>("ALL");
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const alertIds = useRef<Set<string>>(new Set());
  const wsCleanup = useRef<(() => void) | null>(null);

  useEffect(() => {
    loadSession();
    loadAlerts();
    connectWs();
    return () => {
      if (wsCleanup.current) wsCleanup.current();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadSession = async () => {
    try {
      const data = await getSession(id);
      setSession(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadAlerts = async () => {
    try {
      const data = await getAlerts(id);
      const newIds = new Set(alertIds.current);
      data.alerts.forEach((a) => newIds.add(a.id));
      alertIds.current = newIds;
      setAlerts(data.alerts.sort((a, b) => (b.ts_end || 0) - (a.ts_end || 0)));
    } catch (err) {
      console.error(err);
    }
  };

  const connectWs = () => {
    if (wsCleanup.current) wsCleanup.current();
    wsCleanup.current = connectSessionWs(
      id,
      (status) => setSession((prev) => (prev ? { ...prev, status: status.status } : prev)),
      (alert) => {
        if (alertIds.current.has(alert.id)) return;
        alertIds.current.add(alert.id);
        setAlerts((prev) => [alert, ...prev]);
      }
    );
  };

  const start = async () => {
    setIsLoading(true);
    try {
      await startSession(id);
      await loadSession();
    } finally {
      setIsLoading(false);
    }
  };

  const stop = async () => {
    setIsLoading(true);
    try {
      await stopSession(id);
      await loadSession();
    } finally {
      setIsLoading(false);
    }
  };

  const selectedAlert = useMemo(() => alerts.find((a) => a.id === selectedAlertId) || null, [alerts, selectedAlertId]);

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
    <main className="session-page">
      <header className="page-header">
        <button className="btn btn-secondary" onClick={() => router.push("/")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          돌아가기
        </button>
        <div className="header-info">
          <h1 className="page-title">세션 분석</h1>
          {session && getStatusBadge(session.status)}
        </div>
      </header>

      <div className="layout">
        <section className="left-panel">
          <div className="card video-section">
            <div className="section-header">
              <h2 className="section-title">비디오 플레이어</h2>
            </div>
            <VideoWithOverlay downloadUrl={session?.download_url} sourceType={session?.source_type || "file"} />
          </div>

          <div className="card controls-section">
            <div className="section-header">
              <h3 className="section-title">세션 제어</h3>
            </div>
            <div className="controls-grid">
              <button
                className="btn btn-primary"
                onClick={start}
                disabled={session?.status === "RUNNING" || isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="spinner"></span>
                    처리 중
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                    시작
                  </>
                )}
              </button>
              <button
                className="btn btn-outline"
                onClick={stop}
                disabled={session?.status === "STOPPED" || isLoading}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="6" y="6" width="12" height="12" />
                </svg>
                중지
              </button>
            </div>
          </div>
        </section>

        <section className="right-panel">
          <AlertsPanel
            alerts={alerts}
            selectedId={selectedAlertId}
            severityFilter={severityFilter}
            patternFilter={patternFilter}
            onSeverityChange={setSeverityFilter}
            onPatternChange={setPatternFilter}
            onSelect={setSelectedAlertId}
          />

          {selectedAlert && (
            <div className="card evidence-section animate-fade-in">
              <div className="section-header">
                <h3 className="section-title">상세 분석 결과</h3>
              </div>

              <div className="evidence-content">
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="summary-label">패턴 유형</span>
                    <span className="summary-value">
                      {selectedAlert.pattern_type === "will_have_shot" 
                        ? "10초 내 슈팅" 
                        : selectedAlert.pattern_type}
                    </span>
                  </div>
                  {selectedAlert.pattern_type === "will_have_shot" && 
                   selectedAlert.evidence?.metrics?.shot_probability !== undefined && (
                    <div className="summary-item">
                      <span className="summary-label">예측 확률</span>
                      <span className="summary-value">
                        {(selectedAlert.evidence.metrics.shot_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                  <div className="summary-item">
                    <span className="summary-label">심각도</span>
                    <span className={`summary-value severity-${selectedAlert.severity}`}>
                      {selectedAlert.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">시간</span>
                    <span className="summary-value font-mono">
                      {selectedAlert.ts_start?.toFixed(1)}s - {selectedAlert.ts_end?.toFixed(1)}s
                    </span>
                  </div>
                </div>

                <div className="divider"></div>

                <div className="text-blocks">
                  <div className="text-block">
                    <div className="text-header">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12.01" y2="8" />
                      </svg>
                      <h4 className="text-title">발견 사항</h4>
                    </div>
                    <p className="text-content">{selectedAlert.claim_text}</p>
                  </div>

                  <div className="text-block">
                    <div className="text-header">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                      </svg>
                      <h4 className="text-title">권장 사항</h4>
                    </div>
                    <p className="text-content">{selectedAlert.recommendation_text}</p>
                  </div>

                  <div className="text-block">
                    <div className="text-header">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                      <h4 className="text-title">위험도</h4>
                    </div>
                    <p className="text-content">{selectedAlert.risk_text}</p>
                  </div>
                </div>

                {selectedAlert.evidence?.metrics && Object.keys(selectedAlert.evidence.metrics).length > 0 && (
                  <>
                    <div className="divider"></div>
                    <div className="metrics-section">
                      <h4 className="metrics-title">주요 지표</h4>
                      <div className="metrics-grid">
                        {Object.entries(selectedAlert.evidence.metrics).map(([key, metric]) => (
                          <div key={key} className="metric-card">
                            <div className="metric-label">{metric.name}</div>
                            <div className="metric-value">
                              {typeof metric.value === "number" ? metric.value.toFixed(2) : metric.value}
                              {metric.unit && <span className="metric-unit">{metric.unit}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                <div className="divider"></div>

                <div className="evidence-links">
                  {selectedAlert.evidence?.clips?.length > 0 && (
                    <div className="links-group">
                      <h4 className="links-title">비디오 클립</h4>
                      <div className="links-list">
                        {selectedAlert.evidence.clips.map((c, idx) => (
                          <a key={idx} href={c} target="_blank" rel="noreferrer" className="evidence-link">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polygon points="5 3 19 12 5 21 5 3" />
                            </svg>
                            클립 {idx + 1}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedAlert.evidence?.overlays?.length > 0 && (
                    <div className="links-group">
                      <h4 className="links-title">오버레이 이미지</h4>
                      <div className="links-list">
                        {selectedAlert.evidence.overlays.map((c, idx) => (
                          <a key={idx} href={c} target="_blank" rel="noreferrer" className="evidence-link">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                              <circle cx="8.5" cy="8.5" r="1.5" />
                              <polyline points="21 15 16 10 5 21" />
                            </svg>
                            이미지 {idx + 1}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>

      <style jsx>{`
        .session-page {
          min-height: 100vh;
          padding: var(--space-8) var(--space-6);
        }

        .page-header {
          max-width: 1400px;
          margin: 0 auto var(--space-12) auto;
          display: flex;
          align-items: center;
          gap: var(--space-6);
        }

        .header-info {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          flex: 1;
        }

        .page-title {
          font-size: var(--text-3xl);
          font-weight: 800;
          color: var(--gray-50);
          letter-spacing: -0.03em;
        }

        .layout {
          max-width: 1400px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: var(--space-8);
        }

        .left-panel,
        .right-panel {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .section-header {
          margin-bottom: var(--space-6);
        }

        .section-title {
          font-size: var(--text-lg);
          font-weight: 700;
          color: var(--gray-100);
          letter-spacing: -0.02em;
        }

        .video-section {
          min-height: 400px;
        }

        .controls-section {
          background: rgba(255, 255, 255, 0.03);
        }

        .controls-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-4);
        }

        .evidence-section {
          margin-top: var(--space-6);
        }

        .evidence-content {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: var(--space-4);
        }

        .summary-item {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
          padding: var(--space-4);
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-lg);
        }

        .summary-label {
          font-size: var(--text-xs);
          font-weight: 600;
          color: var(--gray-400);
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        .summary-value {
          font-size: var(--text-base);
          font-weight: 700;
          color: var(--gray-100);
        }

        .summary-value.severity-high {
          color: var(--danger-light);
        }

        .summary-value.severity-medium {
          color: var(--warning-light);
        }

        .summary-value.severity-low {
          color: var(--success-light);
        }

        .text-blocks {
          display: flex;
          flex-direction: column;
          gap: var(--space-5);
        }

        .text-block {
          padding: var(--space-5);
          background: rgba(255, 255, 255, 0.03);
          border-left: 3px solid var(--accent);
          border-radius: var(--radius-lg);
        }

        .text-header {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          margin-bottom: var(--space-3);
        }

        .text-header svg {
          color: var(--accent);
          flex-shrink: 0;
        }

        .text-title {
          font-size: var(--text-sm);
          font-weight: 700;
          color: var(--gray-200);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .text-content {
          font-size: var(--text-sm);
          color: var(--gray-300);
          line-height: 1.7;
        }

        .metrics-section {
          padding: var(--space-5);
          background: rgba(59, 130, 246, 0.05);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: var(--radius-lg);
        }

        .metrics-title {
          font-size: var(--text-sm);
          font-weight: 700;
          color: var(--gray-200);
          margin-bottom: var(--space-4);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: var(--space-3);
        }

        .metric-card {
          padding: var(--space-4);
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-lg);
          text-align: center;
          transition: all var(--transition-base);
        }

        .metric-card:hover {
          background: rgba(255, 255, 255, 0.08);
          transform: translateY(-2px);
        }

        .metric-label {
          font-size: var(--text-xs);
          font-weight: 600;
          color: var(--gray-400);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: var(--space-2);
        }

        .metric-value {
          font-size: var(--text-xl);
          font-weight: 800;
          color: var(--info-light);
          display: flex;
          align-items: baseline;
          justify-content: center;
          gap: var(--space-1);
        }

        .metric-unit {
          font-size: var(--text-xs);
          font-weight: 400;
          color: var(--gray-500);
        }

        .evidence-links {
          display: flex;
          flex-direction: column;
          gap: var(--space-5);
        }

        .links-group {
          padding: var(--space-5);
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-lg);
        }

        .links-title {
          font-size: var(--text-sm);
          font-weight: 700;
          color: var(--gray-200);
          margin-bottom: var(--space-4);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .links-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .evidence-link {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-4);
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: var(--radius-md);
          text-decoration: none;
          color: var(--gray-200);
          font-size: var(--text-sm);
          font-weight: 600;
          transition: all var(--transition-base);
        }

        .evidence-link:hover {
          background: rgba(233, 69, 96, 0.1);
          border-color: var(--accent);
          color: var(--accent-light);
          transform: translateX(4px);
        }

        .evidence-link svg {
          flex-shrink: 0;
        }

        @media (max-width: 1024px) {
          .layout {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 768px) {
          .session-page {
            padding: var(--space-6) var(--space-4);
          }

          .page-header {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--space-4);
          }

          .page-title {
            font-size: var(--text-2xl);
          }

          .summary-grid {
            grid-template-columns: 1fr;
          }

          .metrics-grid {
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          }
        }
      `}</style>
    </main>
  );
}
