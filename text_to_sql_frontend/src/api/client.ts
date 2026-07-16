import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8010";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Extracts a plain, user-readable message from an API error response.
 *
 * FastAPI's `detail` field can be a plain string (HTTPException), an array of
 * Pydantic validation-error objects (422 responses), a single error object,
 * or missing entirely (network failure) - never render any of those raw
 * shapes directly in the UI.
 */
export function getErrorMessage(err: unknown, fallback: string): string {
  const anyErr = err as any;
  const detail = anyErr?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item;
        const loc = Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : undefined;
        const msg = typeof item?.msg === "string" ? item.msg : "Invalid value";
        return loc ? `${loc}: ${msg}` : msg;
      })
      .filter(Boolean);
    if (messages.length > 0) return messages.join("; ");
  }

  if (detail && typeof detail === "object" && typeof (detail as any).msg === "string") {
    return (detail as any).msg;
  }

  if (!anyErr?.response) {
    return "Could not reach the server. Please check your connection and try again.";
  }

  return fallback;
}
