"use client";

import { useMemo } from "react";

import { Alert } from "../lib/api";

interface Props {
  alerts: Alert[];
  selectedId?: string | null;
  severityFilter: string;
  patternFilter: string;
  onSeverityChange: (value: string) => void;
  onPatternChange: (value: string) => void;
  onSelect: (alertId: string) => void;
}

export default function AlertsPanel({
  alerts,
  selectedId,
  severityFilter,
  patternFilter,
  onSeverityChange,
  onPatternChange,
  onSelect,
}: Props) {
  const filtered = useMemo(() => {
    return alerts.filter((a) => {
      const sevOk = severityFilter === "ALL" || a.severity === severityFilter.toLowerCase();
      const patternOk = patternFilter === "ALL" || a.pattern_type === patternFilter;
      return sevOk && patternOk;
    });
  }, [alerts, patternFilter, severityFilter]);

  const selectedAlert = filtered.find((a) => a.id === selectedId) || alerts.find((a) => a.id === selectedId);
  const patternOptions = useMemo(() => {
    const unique = Array.from(new Set(alerts.map((a) => a.pattern_type)));
    return ["ALL", ...unique];
  }, [alerts]);

  return (
    <div className="panel">
      <div className="filters">
        <label>
          Severity
          <select value={severityFilter} onChange={(e) => onSeverityChange(e.target.value)}>
            <option>ALL</option>
            <option>LOW</option>
            <option>MEDIUM</option>
            <option>HIGH</option>
          </select>
        </label>
        <label>
          Pattern
          <select value={patternFilter} onChange={(e) => onPatternChange(e.target.value)}>
            {patternOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="alerts">
        <h3>Alerts</h3>
        <ul>
          {filtered.map((a) => (
            <li
              key={a.id}
              className={`alert severity-${a.severity}${selectedId === a.id ? " selected" : ""}`}
              onClick={() => onSelect(a.id)}
            >
              <div className="alert-head">
                <span className="pattern">{a.pattern_type}</span>
                <span className="sev">{a.severity}</span>
              </div>
              <div className="claim">{a.claim_text}</div>
            </li>
          ))}
        </ul>
      </div>
      {selectedAlert && (
        <div className="evidence">
          <h4>Evidence</h4>
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
      <style jsx>{`
        .panel {
          display: flex;
          flex-direction: column;
          gap: 12px;
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
          max-height: 40vh;
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
          cursor: pointer;
        }
        .alert.selected {
          border-color: #0ea5e9;
        }
        .alert-head {
          display: flex;
          justify-content: space-between;
          font-weight: 600;
        }
        .evidence {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 12px;
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
    </div>
  );
}
