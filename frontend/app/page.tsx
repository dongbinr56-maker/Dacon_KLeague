\"use client\";

import { useEffect, useState } from "react";

interface Session {
  id: string;
  source_type: string;
  mode: string;
  status: string;
  fps: number;
  source_uri: string;
}

interface Alert {
  id: string;
  pattern_type: string;
  severity: string;
  claim_text: string;
  recommendation_text: string;
  risk_text: string;
}

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";

export default function HomePage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [mode, setMode] = useState("file");
  const [rtspUrl, setRtspUrl] = useState("");
  const [filePath, setFilePath] = useState("");
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const fetchSessions = async () => {
    const res = await fetch(`${apiBase}/sessions`);
    const data = await res.json();
    setSessions(data.sessions || []);
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const createSession = async () => {
    const payload: any = {
      source_type: mode,
      mode: mode === "file" ? "offline_realtime" : "live",
      fps: 25,
    };
    if (mode === "file") {
      payload.path = filePath;
    } else {
      payload.rtsp_url = rtspUrl;
    }

    const res = await fetch(`${apiBase}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const session = await res.json();
    setSelectedSession(session.id);
    await fetchSessions();
  };

  const startSession = async (id: string) => {
    await fetch(`${apiBase}/sessions/${id}/start`, { method: "POST" });
    await fetchSessions();
    subscribeWs(id);
  };

  const subscribeWs = (id: string) => {
    const ws = new WebSocket(`${apiBase.replace("http", "ws")}/ws/sessions/${id}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "alert") {
        setAlerts((prev) => [...prev, data.payload]);
      }
    };
  };

  return (
    <div style={{ padding: 24, fontFamily: "Inter, sans-serif" }}>
      <h1>고정캠 전술 피드백 데모</h1>
      <section style={{ marginBottom: 16 }}>
        <h2>입력 소스 선택</h2>
        <div>
          <label>
            <input
              type="radio"
              name="mode"
              value="file"
              checked={mode === "file"}
              onChange={() => setMode("file")}
            />
            업로드/파일 재생
          </label>
          <label style={{ marginLeft: 12 }}>
            <input
              type="radio"
              name="mode"
              value="rtsp"
              checked={mode === "rtsp"}
              onChange={() => setMode("rtsp")}
            />
            라이브 RTSP
          </label>
        </div>
        {mode === "file" ? (
          <div style={{ marginTop: 8 }}>
            <input
              placeholder="/path/to/video.mp4"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              style={{ width: 320 }}
            />
          </div>
        ) : (
          <div style={{ marginTop: 8 }}>
            <input
              placeholder="rtsp://..."
              value={rtspUrl}
              onChange={(e) => setRtspUrl(e.target.value)}
              style={{ width: 320 }}
            />
          </div>
        )}
        <button style={{ marginTop: 8 }} onClick={createSession}>
          세션 생성
        </button>
      </section>

      <section style={{ marginBottom: 16 }}>
        <h2>세션 목록</h2>
        <ul>
          {sessions.map((s) => (
            <li key={s.id}>
              <strong>{s.id}</strong> - {s.source_type} - {s.status}
              <button style={{ marginLeft: 8 }} onClick={() => startSession(s.id)}>
                시작
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>알림(placeholder)</h2>
        <ul>
          {alerts.map((a) => (
            <li key={a.id}>
              <strong>{a.pattern_type}</strong> [{a.severity}] - {a.claim_text}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
