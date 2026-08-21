const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const chatApi = {
  listSessions: () => request("/api/sessions"),

  createSession: () =>
    request("/api/sessions", { method: "POST" }),

  getSession: (sessionId) => request(`/api/sessions/${sessionId}`),

  deleteSession: (sessionId) =>
    request(`/api/sessions/${sessionId}`, { method: "DELETE" }),

  sendMessage: (message, sessionId) =>
    request("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    }),

  getSection: (sectionNumber) => request(`/api/sections/${sectionNumber}`),
};