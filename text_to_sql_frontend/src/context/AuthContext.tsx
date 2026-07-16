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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    apiClient
      .get<User>("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await apiClient.post("/auth/login", { email, password });
    localStorage.setItem("access_token", res.data.access_token);
    const me = await apiClient.get<User>("/auth/me");
    setUser(me.data);
  };

  const signup = async (email: string, password: string, fullName?: string) => {
    const res = await apiClient.post("/auth/signup", { email, password, full_name: fullName });
    localStorage.setItem("access_token", res.data.access_token);
    const me = await apiClient.get<User>("/auth/me");
    setUser(me.data);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
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
