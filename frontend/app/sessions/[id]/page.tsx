"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { getSession, startSession, stopSession } from "../../../lib/api";
import { connectSessionWs } from "../../../lib/ws";

interface AlertPayload {
  id: string;
  pattern_type: string;
  severity: string;
  claim_text: string;
  recommendation_text: string;
  risk_text: string;
  evidence: {
    clips: string[];
    overlays: string[];
    metrics: Record<string, { name: string; value: number; unit?: string }>;
  };
}

interface Session {
  id: string;
  status: string;
  source_type: string;
  mode: string;
  download_url?: string | null;
}

interface Props {
  params: { id: string };
}

export default function SessionPage({ params }: Props) {
  const { id } = params;
  const [session, setSession] = useState<Session | null>(null);
  const [alerts, setAlerts] = useState<AlertPayload[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [patternFilter, setPatternFilter] = useState<string>("ALL");
  const alertIds = useRef<Set<string>>(new Set());
  const wsCleanup = useRef<(() => void) | null>(null);

  useEffect(() => {
    loadSession();
    return () => {
      if (wsCleanup.current) wsCleanup.current();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadSession = async () => {
    try {
      const data = await getSession(id);
      setSession(data);
      connectWs();
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

  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      const severityOk = severityFilter === "ALL" || a.severity === severityFilter.toLowerCase();
      const patternOk = patternFilter === "ALL" || a.pattern_type === patternFilter;
      return severityOk && patternOk;
    });
  }, [alerts, severityFilter, patternFilter]);

  const start = async () => {
    await startSession(id);
    await loadSession();
  };

  const stop = async () => {
    await stopSession(id);
    await loadSession();
  };

  return (
    <main className="layout">
      <section className="video-panel">
        <div className="video-wrap">
          {session?.download_url ? (
            <>
              <video src={session.download_url} controls width="100%" />
              <canvas className="overlay" aria-label="overlay" />
            </>
          ) : (
            <div className="placeholder">Live 입력 또는 다운로드 URL 없음</div>
          )}
        </div>
      </section>

      <section className="sidebar">
        <div className="status-row">
          <span className={`badge status-${session?.status?.toLowerCase() || "unknown"}`}>
            {session?.status || "-"}
          </span>
          <div className="actions">
            <button onClick={start} disabled={session?.status === "RUNNING"}>
              Start
            </button>
            <button onClick={stop} disabled={session?.status === "STOPPED"}>
              Stop
            </button>
          </div>
        </div>

        <div className="filters">
          <label>
            Severity
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
              <option>ALL</option>
              <option>LOW</option>
              <option>MEDIUM</option>
              <option>HIGH</option>
            </select>
          </label>
          <label>
            Pattern
            <select value={patternFilter} onChange={(e) => setPatternFilter(e.target.value)}>
              <option>ALL</option>
              <option>build_up_bias</option>
            </select>
          </label>
        </div>

        <div className="alerts">
          <h3>Alerts</h3>
          <ul>
            {filteredAlerts.map((a) => (
              <li key={a.id} className={`alert severity-${a.severity}`}>
                <div className="alert-head">
                  <span className="pattern">{a.pattern_type}</span>
                  <span className="sev">{a.severity}</span>
                </div>
                <div className="claim">{a.claim_text}</div>
                <div className="evidence">
                  {a.evidence?.clips?.length > 0 && (
                    <div>
                      Clips:
                      <ul>
                        {a.evidence.clips.map((c) => (
                          <li key={c}>
                            <a href={c} target="_blank" rel="noreferrer">
                              {c}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {a.evidence?.overlays?.length > 0 && (
                    <div>
                      Overlays:
                      <ul>
                        {a.evidence.overlays.map((c) => (
                          <li key={c}>
                            <a href={c} target="_blank" rel="noreferrer">
                              {c}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {a.evidence?.metrics && Object.keys(a.evidence.metrics).length > 0 && (
                    <div className="metrics">
                      Metrics:
                      <div className="metric-grid">
                        {Object.entries(a.evidence.metrics).map(([key, metric]) => (
                          <div key={key} className="metric-card">
                            <div className="metric-name">{metric.name}</div>
                            <div className="metric-value">
                              {metric.value} {metric.unit || ""}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <style jsx>{`
        .layout {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 16px;
          padding: 20px;
          font-family: Inter, system-ui, -apple-system, sans-serif;
        }
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
        .sidebar {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .status-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 12px;
        }
        .badge {
          padding: 6px 10px;
          border-radius: 999px;
          font-weight: 600;
          font-size: 0.9rem;
        }
        .status-running {
          background: #dcfce7;
          color: #166534;
        }
        .status-connecting {
          background: #e0f2fe;
          color: #075985;
        }
        .status-lost {
          background: #fee2e2;
          color: #991b1b;
        }
        .status-stopped {
          background: #e2e8f0;
          color: #475569;
        }
        .actions button {
          margin-left: 6px;
          padding: 8px 10px;
          border-radius: 8px;
          border: none;
          background: #0ea5e9;
          color: white;
          cursor: pointer;
        }
        .actions button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .filters {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          background: #fff;
          padding: 12px;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
        }
        select {
          padding: 6px 8px;
          border-radius: 8px;
          border: 1px solid #cbd5e1;
        }
        .alerts {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 12px;
          max-height: 70vh;
          overflow: auto;
        }
        .alerts ul {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .alert {
          border: 1px solid #e2e8f0;
          border-radius: 10px;
          padding: 10px;
          background: #f8fafc;
        }
        .alert-head {
          display: flex;
          justify-content: space-between;
          font-weight: 600;
        }
        .evidence ul {
          margin: 4px 0 0;
          padding-left: 16px;
        }
        .metric-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: 8px;
        }
        .metric-card {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 8px;
        }
        .metric-name {
          font-size: 0.85rem;
          color: #475569;
        }
        .metric-value {
          font-weight: 700;
        }
        .severity-medium {
          border-color: #fbbf24;
        }
        .severity-high {
          border-color: #ef4444;
        }
        .severity-low {
          border-color: #22c55e;
        }
      `}</style>
    </main>
  );
}
