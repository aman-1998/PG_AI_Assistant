import { API_BASE_URL } from "../api/client";

export interface ChatStreamEvent {
  type: "session" | "reply_chunk" | "status" | "tool_done" | "done" | "error";
  [key: string]: unknown;
}

interface StreamChatArgs {
  connectionId: number;
  message: string;
  llmConfigId: number;
  sessionId: number | null;
  intent?: string | null;
  onEvent: (event: ChatStreamEvent) => void;
  signal?: AbortSignal;
}

/**
 * Consumes the backend's SSE stream (POST /chat/{connectionId}/stream). Plain
 * EventSource doesn't support POST bodies, so this reads the fetch() response
 * stream manually and splits on the "data: ...\n\n" SSE frame boundary.
 */
export async function streamChat({
  connectionId,
  message,
  llmConfigId,
  sessionId,
  intent,
  onEvent,
  signal,
}: StreamChatArgs): Promise<void> {
  const token = localStorage.getItem("access_token");
  const response = await fetch(`${API_BASE_URL}/chat/${connectionId}/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message, llm_config_id: llmConfigId, session_id: sessionId, intent }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat stream request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const dataLine = frame.split("\n").find((line) => line.startsWith("data:"));
      if (dataLine) {
        const json = dataLine.slice("data:".length).trim();
        try {
          onEvent(JSON.parse(json));
        } catch {
          // ignore malformed frame
        }
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
}
