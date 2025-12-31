export const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";

export interface UploadResponse {
  file_id: string;
  storage_url: string;
  download_url: string;
  filename: string;
  size_bytes: number;
}

export interface SessionPayload {
  source_type: "file" | "rtsp" | "webcam";
  mode: "offline_realtime" | "live";
  fps?: number;
  buffer_ms?: number;
  file_id?: string;
  path?: string;
  rtsp_url?: string;
  device_id?: number;
}

export async function uploadVideo(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${apiBase}/uploads`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function createSession(payload: SessionPayload) {
  const res = await fetch(`${apiBase}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function startSession(id: string) {
  const res = await fetch(`${apiBase}/sessions/${id}/start`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start session");
  return res.json();
}

export async function stopSession(id: string) {
  const res = await fetch(`${apiBase}/sessions/${id}/stop`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to stop session");
  return res.json();
}

export async function getSession(id: string) {
  const res = await fetch(`${apiBase}/sessions/${id}`);
  if (!res.ok) throw new Error("Session not found");
  return res.json();
}

export async function listSessions() {
  const res = await fetch(`${apiBase}/sessions`);
  if (!res.ok) throw new Error("Failed to list sessions");
  return res.json();
}
