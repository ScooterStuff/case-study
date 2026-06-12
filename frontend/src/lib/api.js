// SSE client for the backend /chat stream (fetch + ReadableStream parsing).
// Event vocabulary mirrors backend/app/agent.py: token / tool_start /
// tool_end (with name+args+summary) / tool_error / ui_block / trace / done.
const BASE = process.env.REACT_APP_API_BASE || "";

export async function streamChat(sessionId, message, handlers, signal) {
  const resp = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
    signal,
  });
  if (!resp.ok || !resp.body) {
    throw new Error(`backend error (${resp.status})`);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let event = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep incomplete tail
    for (const raw of lines) {
      const line = raw.trim();
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:") && line !== "data:") {
        let data;
        try {
          data = JSON.parse(line.slice(5));
        } catch {
          continue;
        }
        handlers[event]?.(data);
      }
    }
  }
}

export function getSessionId() {
  let id = localStorage.getItem("ps_session_id");
  if (!id) {
    id = `web-${crypto.randomUUID ? crypto.randomUUID() : Date.now()}`;
    localStorage.setItem("ps_session_id", id);
  }
  return id;
}

export function newSession() {
  localStorage.removeItem("ps_session_id");
  return getSessionId();
}
