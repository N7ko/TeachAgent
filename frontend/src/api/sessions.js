import { API_BASE, request } from "./http";

async function readServerEvents(response, onEvent) {
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? "请求失败");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame
        .split("\n")
        .find((item) => item.startsWith("data: "));
      if (!line) continue;
      onEvent(JSON.parse(line.slice(6)));
    }
  }
}

export function createSession(topic) {
  return request("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ topic }),
  });
}

export function submitSessionAnswer(sessionId, answer) {
  return request(`/api/sessions/${sessionId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
}

export async function createSessionStream(topic, onEvent) {
  const response = await fetch(`${API_BASE}/api/sessions/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic }),
  });
  await readServerEvents(response, onEvent);
}

export async function submitSessionAnswerStream(sessionId, answer, onEvent) {
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/answer/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  });
  await readServerEvents(response, onEvent);
}
