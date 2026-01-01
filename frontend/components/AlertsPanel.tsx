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

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case "high":
        return "severity-high";
      case "medium":
        return "severity-medium";
      case "low":
        return "severity-low";
      default:
        return "";
    }
  };

  const getPatternLabel = (patternType: string) => {
    const labels: Record<string, string> = {
      will_have_shot: "10초 내 슈팅",
      build_up_bias: "빌드업 편향",
      transition_risk: "전환 위험",
      final_third_pressure: "파이널서드 압박",
    };
    return labels[patternType] || patternType;
  };

  return (
    <div className="panel card">
      <div className="panel-header">
        <h2 className="panel-title">알림 패널</h2>
        {filtered.length > 0 && (
          <span className="badge-count">{filtered.length}</span>
        )}
      </div>

      <div className="filters">
        <label className="filter-group">
          <span className="filter-label">심각도</span>
          <select
            value={severityFilter}
            onChange={(e) => onSeverityChange(e.target.value)}
            className="select"
          >
            <option value="ALL">전체</option>
            <option value="HIGH">높음</option>
            <option value="MEDIUM">중간</option>
            <option value="LOW">낮음</option>
          </select>
        </label>
        <label className="filter-group">
          <span className="filter-label">패턴</span>
          <select
            value={patternFilter}
            onChange={(e) => onPatternChange(e.target.value)}
            className="select"
          >
            {patternOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt === "ALL" ? "전체" : opt}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="alerts-container">
        {filtered.length === 0 ? (
          <div className="empty-alerts">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <p className="empty-text">필터 조건에 맞는 알림이 없습니다</p>
          </div>
        ) : (
          <div className="alerts-list">
            {filtered.map((a) => (
              <div
                key={a.id}
                className={`alert-item ${selectedId === a.id ? "selected" : ""} ${getSeverityColor(a.severity)}`}
                onClick={() => onSelect(a.id)}
              >
                <div className="alert-header">
                  <div className="alert-badges">
                    <span className="pattern-badge">{getPatternLabel(a.pattern_type)}</span>
                    <span className={`severity-badge ${getSeverityColor(a.severity)}`}>
                      {a.severity.toUpperCase()}
                    </span>
                  </div>
                  {a.ts_end && (
                    <span className="alert-time font-mono">{a.ts_end.toFixed(1)}s</span>
                  )}
                </div>
                <div className="alert-content">
                  <p className="alert-claim">{a.claim_text}</p>
                  {a.pattern_type === "will_have_shot" && a.evidence?.metrics?.["shot_probability"] && (
                    <p className="alert-probability">
                      예측 확률: {(a.evidence.metrics["shot_probability"].value * 100).toFixed(1)}%
                    </p>
                  )}
                </div>
                {selectedId === a.id && (
                  <div className="alert-indicator">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span>선택됨</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .panel {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .panel-title {
          font-size: var(--text-lg);
          font-weight: 700;
          color: var(--gray-100);
          letter-spacing: -0.02em;
        }

        .badge-count {
          padding: var(--space-1) var(--space-3);
          background: var(--accent);
          color: white;
          border-radius: var(--radius-full);
          font-size: var(--text-xs);
          font-weight: 700;
        }

        .filters {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-4);
        }

        .filter-group {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .filter-label {
          font-size: var(--text-xs);
          font-weight: 600;
          color: var(--gray-400);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .alerts-container {
          flex: 1;
          min-height: 300px;
          max-height: 60vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .alerts-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
          overflow-y: auto;
          padding-right: var(--space-2);
        }

        .alert-item {
          padding: var(--space-4);
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-left: 3px solid transparent;
          border-radius: var(--radius-lg);
          cursor: pointer;
          transition: all var(--transition-base);
          position: relative;
        }

        .alert-item:hover {
          background: rgba(255, 255, 255, 0.06);
          transform: translateX(4px);
        }

        .alert-item.selected {
          background: rgba(233, 69, 96, 0.1);
          border-color: var(--accent);
          box-shadow: 0 0 0 1px var(--accent), var(--shadow-lg);
        }

        .alert-item.severity-high {
          border-left-color: var(--danger);
        }

        .alert-item.severity-medium {
          border-left-color: var(--warning);
        }

        .alert-item.severity-low {
          border-left-color: var(--success);
        }

        .alert-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: var(--space-3);
          gap: var(--space-2);
        }

        .alert-badges {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-2);
          flex: 1;
        }

        .pattern-badge,
        .severity-badge {
          padding: var(--space-1) var(--space-2);
          border-radius: var(--radius-md);
          font-size: var(--text-xs);
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .pattern-badge {
          background: rgba(255, 255, 255, 0.1);
          color: var(--gray-300);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .severity-badge.severity-high {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger-light);
          border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .severity-badge.severity-medium {
          background: rgba(245, 158, 11, 0.1);
          color: var(--warning-light);
          border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .severity-badge.severity-low {
          background: rgba(16, 185, 129, 0.1);
          color: var(--success-light);
          border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .alert-time {
          font-size: var(--text-xs);
          color: var(--gray-500);
          font-weight: 600;
          white-space: nowrap;
        }

        .alert-content {
          margin-top: var(--space-2);
        }

        .alert-claim {
          font-size: var(--text-sm);
          color: var(--gray-300);
          line-height: 1.6;
          margin: 0;
        }

        .alert-probability {
          font-size: var(--text-xs);
          color: var(--accent);
          font-weight: 600;
          margin-top: var(--space-2);
          margin-bottom: 0;
        }

        .alert-indicator {
          margin-top: var(--space-3);
          padding-top: var(--space-3);
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          font-size: var(--text-xs);
          font-weight: 600;
          color: var(--accent);
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }

        .empty-alerts {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-16) var(--space-8);
          color: var(--gray-500);
          text-align: center;
        }

        .empty-icon {
          margin-bottom: var(--space-4);
          color: var(--gray-600);
        }

        .empty-text {
          font-size: var(--text-sm);
          color: var(--gray-500);
        }
      `}</style>
    </div>
  );
}
