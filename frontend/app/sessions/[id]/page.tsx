"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import AlertsPanel from "../../../components/AlertsPanel";
import VideoWithOverlay from "../../../components/VideoWithOverlay";
import { Alert, Session, getAlerts, getSession, startSession, stopSession } from "../../../lib/api";
import { connectSessionWs } from "../../../lib/ws";

interface Props {
  params: { id: string };
}

export default function SessionPage({ params }: Props) {
  const { id } = params;
  const [session, setSession] = useState<Session | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [patternFilter, setPatternFilter] = useState<string>("ALL");
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
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
    await startSession(id);
    await loadSession();
  };

  const stop = async () => {
    await stopSession(id);
    await loadSession();
  };

  const selectedAlert = useMemo(() => alerts.find((a) => a.id === selectedAlertId) || null, [alerts, selectedAlertId]);

  return (
    <main className="layout">
      <section className="left">
        <VideoWithOverlay downloadUrl={session?.download_url} sourceType={session?.source_type || "file"} />
      </section>

      <section className="right">
        <div className="status-row">
          <span className={`badge status-${session?.status?.toLowerCase() || "unknown"}`}>{session?.status || "-"}</span>
          <div className="actions">
            <button onClick={start} disabled={session?.status === "RUNNING"}>
              Start
            </button>
            <button onClick={stop} disabled={session?.status === "STOPPED"}>
              Stop
            </button>
          </div>
        </div>

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
          <div className="evidence-panel">
            <h3>Evidence Detail</h3>
            {selectedAlert.evidence?.clips?.length > 0 && (
              <div>
                Clips:
                <ul>
                  {selectedAlert.evidence.clips.map((c) => (
                    <li key={c}>
                      <a href={c} target="_blank" rel="noreferrer">
                        {c}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {selectedAlert.evidence?.overlays?.length > 0 && (
              <div>
                Overlays:
                <ul>
                  {selectedAlert.evidence.overlays.map((c) => (
                    <li key={c}>
                      <a href={c} target="_blank" rel="noreferrer">
                        {c}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {selectedAlert.evidence?.metrics && Object.keys(selectedAlert.evidence.metrics).length > 0 && (
              <div className="metrics">
                <div className="metric-grid">
                  {Object.entries(selectedAlert.evidence.metrics).map(([key, metric]) => (
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
        )}
      </section>

      <style jsx>{`
        .layout {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 16px;
          padding: 20px;
          font-family: Inter, system-ui, -apple-system, sans-serif;
        }
        .left {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .right {
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
        .evidence-panel {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 12px;
        }
        .evidence-panel ul {
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
      `}</style>
    </main>
  );
}
