export type SessionWsEvent =
  | { type: "status"; payload: any }
  | { type: "alert"; payload: any };

export function connectSessionWs(
  sessionId: string,
  onStatus: (status: any) => void,
  onAlert: (alert: any) => void,
  onError?: (err: Event) => void
) {
  const wsBase = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api").replace(
    /^http/,
    "ws"
  );
  let attempts = 0;
  const maxAttempts = 5;

  let ws: WebSocket | null = null;

  const connect = () => {
    attempts += 1;
    ws = new WebSocket(`${wsBase}/ws/sessions/${sessionId}`);

    ws.onmessage = (event) => {
      const data: SessionWsEvent = JSON.parse(event.data);
      if (data.type === "status") onStatus(data.payload);
      if (data.type === "alert") onAlert(data.payload);
    };

    ws.onclose = (ev) => {
      if (attempts < maxAttempts) {
        setTimeout(connect, 1000);
      }
      onError?.(ev);
    };

    ws.onerror = (ev) => {
      onError?.(ev);
    };
  };

  connect();

  return () => {
    attempts = maxAttempts;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  };
}
