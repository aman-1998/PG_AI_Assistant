import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  updateChatRetentionDays: (days: number) => Promise<void>;
  updateMaxChatSessions: (count: number) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Auto-logout after this long with no user activity (mouse/keyboard/touch/scroll).
const IDLE_TIMEOUT_MS = 60 * 60 * 1000; // 1 hour
const LAST_ACTIVITY_KEY = "last_activity_at";
// mousemove excluded — hovering cursor without clicking should not reset the timer
const ACTIVITY_EVENTS = ["mousedown", "keydown", "scroll", "touchstart"] as const;
const IDLE_CHECK_INTERVAL_MS = 30 * 1000;
const ACTIVITY_WRITE_THROTTLE_MS = 5 * 1000;

function markActivity() {
  localStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()));
}

function isIdleExpired(): boolean {
  const lastActivity = Number(localStorage.getItem(LAST_ACTIVITY_KEY));
  if (!lastActivity) return false;
  return Date.now() - lastActivity >= IDLE_TIMEOUT_MS;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    // If the tab/browser was closed (or just left open) for longer than the
    // idle window, don't silently resume the session on reload.
    if (isIdleExpired()) {
      localStorage.removeItem("access_token");
      localStorage.removeItem(LAST_ACTIVITY_KEY);
      setIsLoading(false);
      return;
    }
    apiClient
      .get<User>("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setIsLoading(false));
  }, []);

  // While logged in, track activity and auto-logout after IDLE_TIMEOUT_MS of
  // inactivity (checked periodically, since a user can idle without ever
  // triggering another event).
  useEffect(() => {
    if (!user) return;

    markActivity();
    let lastWrite = Date.now();
    const handleActivity = () => {
      const now = Date.now();
      if (now - lastWrite > ACTIVITY_WRITE_THROTTLE_MS) {
        lastWrite = now;
        markActivity();
      }
    };
    ACTIVITY_EVENTS.forEach((evt) => window.addEventListener(evt, handleActivity));

    const intervalId = window.setInterval(() => {
      if (isIdleExpired()) {
        logout();
      }
    }, IDLE_CHECK_INTERVAL_MS);

    return () => {
      ACTIVITY_EVENTS.forEach((evt) => window.removeEventListener(evt, handleActivity));
      window.clearInterval(intervalId);
    };
  }, [user]);

  const login = async (email: string, password: string) => {
    const res = await apiClient.post("/auth/login", { email, password });
    localStorage.setItem("access_token", res.data.access_token);
    markActivity();
    const me = await apiClient.get<User>("/auth/me");
    setUser(me.data);
  };

  const signup = async (email: string, password: string, fullName?: string) => {
    const res = await apiClient.post("/auth/signup", { email, password, full_name: fullName });
    localStorage.setItem("access_token", res.data.access_token);
    markActivity();
    const me = await apiClient.get<User>("/auth/me");
    setUser(me.data);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem(LAST_ACTIVITY_KEY);
    setUser(null);
  };

  const updateChatRetentionDays = async (days: number) => {
    const res = await apiClient.patch<User>("/auth/me/chat-retention", { chat_history_retention_days: days });
    setUser(res.data);
  };

  const updateMaxChatSessions = async (count: number) => {
    const res = await apiClient.patch<User>("/auth/me/max-chat-sessions", { max_chat_sessions: count });
    setUser(res.data);
  };

  const value = useMemo(
    () => ({ user, isLoading, login, signup, logout, updateChatRetentionDays, updateMaxChatSessions }),
    [user, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
