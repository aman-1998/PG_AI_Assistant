import React, { useEffect, useRef, useState } from "react";
import { useParams, Link as RouterLink } from "react-router-dom";
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Link,
  Snackbar,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import StopIcon from "@mui/icons-material/Stop";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import { apiClient, getErrorMessage } from "../api/client";
import ChatWindow from "../components/ChatWindow";
import ChatSidebar from "../components/ChatSidebar";
import UploadedDocsDialog from "../components/UploadedDocsDialog";
import { streamChat, ChatStreamEvent } from "../hooks/useChatStream";
import type { ChatMessage, ChatSession, DatabaseConnection, LLMConfig } from "../types";

export interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  toolStatuses?: string[];
}

export default function Chat() {
  const { connectionId } = useParams<{ connectionId: string }>();
  const [connection, setConnection] = useState<DatabaseConnection | null>(null);
  const [llmConfigs, setLlmConfigs] = useState<LLMConfig[]>([]);
  const [selectedLlmConfigId, setSelectedLlmConfigId] = useState<number | "">("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [uploadsOpen, setUploadsOpen] = useState(false);
  const [uploadingPaste, setUploadingPaste] = useState(false);
  const [pasteStatus, setPasteStatus] = useState<{ severity: "success" | "error"; message: string } | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!connectionId) return;
    setLoading(true);
    Promise.all([
      apiClient.get<DatabaseConnection>(`/database-connections/${connectionId}`),
      apiClient.get<LLMConfig[]>("/llm-configs"),
      apiClient.get<ChatSession[]>("/chat/sessions"),
    ])
      .then(async ([connRes, configsRes, sessionsRes]) => {
        setConnection(connRes.data);
        setLlmConfigs(configsRes.data);
        if (configsRes.data.length > 0) {
          setSelectedLlmConfigId(configsRes.data[0].id);
        }

        // Resume the most recent chat session for this connection (if any) so
        // that reloading the page doesn't silently drop prior context.
        const connectionSessions = sessionsRes.data
          .filter((s) => s.database_connection_id === Number(connectionId))
          .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
        setSessions(connectionSessions);
        const existing = connectionSessions[0];
        if (existing) {
          const messagesRes = await apiClient.get<ChatMessage[]>(`/chat/sessions/${existing.id}/messages`);
          setSessionId(existing.id);
          setMessages(messagesRes.data.map((m) => ({ role: m.role, content: m.content })));
        } else {
          setSessionId(null);
          setMessages([]);
        }
      })
      .finally(() => setLoading(false));
  }, [connectionId]);

  const refreshSessions = async () => {
    if (!connectionId) return;
    const sessionsRes = await apiClient.get<ChatSession[]>("/chat/sessions");
    const connectionSessions = sessionsRes.data
      .filter((s) => s.database_connection_id === Number(connectionId))
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    setSessions(connectionSessions);
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
  };

  const handleSelectSession = async (session: ChatSession) => {
    if (session.id === sessionId || sending) return;
    setLoading(true);
    try {
      const messagesRes = await apiClient.get<ChatMessage[]>(`/chat/sessions/${session.id}/messages`);
      setSessionId(session.id);
      setMessages(messagesRes.data.map((m) => ({ role: m.role, content: m.content })));
    } finally {
      setLoading(false);
    }
  };

  const handleRenameSession = async (session: ChatSession, title: string) => {
    try {
      const res = await apiClient.patch<ChatSession>(`/chat/sessions/${session.id}`, { title });
      setSessions((prev) => prev.map((s) => (s.id === session.id ? res.data : s)));
    } catch (err) {
      setPasteStatus({ severity: "error", message: getErrorMessage(err, "Failed to rename chat.") });
    }
  };

  const handleDeleteSession = async (session: ChatSession) => {
    try {
      await apiClient.delete(`/chat/sessions/${session.id}`);
      setSessions((prev) => prev.filter((s) => s.id !== session.id));
      if (session.id === sessionId) {
        setSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      setPasteStatus({ severity: "error", message: getErrorMessage(err, "Failed to delete chat.") });
    }
  };

  const handlePaste = async (e: React.ClipboardEvent<HTMLDivElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    const imageItem = Array.from(items).find(
      (item) => item.kind === "file" && item.type.startsWith("image/")
    );
    if (!imageItem) return; // not an image paste, let normal text paste happen

    e.preventDefault();
    if (!connectionId) return;
    if (!selectedLlmConfigId) {
      setPasteStatus({ severity: "error", message: "Select an LLM model before pasting a screenshot." });
      return;
    }

    const blob = imageItem.getAsFile();
    if (!blob) return;

    const extension = imageItem.type.split("/")[1] || "png";
    const file = new File([blob], `pasted-screenshot-${Date.now()}.${extension}`, { type: imageItem.type });

    setUploadingPaste(true);
    setPasteStatus(null);
    const formData = new FormData();
    formData.append("llm_config_id", String(selectedLlmConfigId));
    formData.append("file", file);

    try {
      await apiClient.post(`/database-connections/${connectionId}/uploads`, formData);
      setPasteStatus({ severity: "success", message: "Screenshot uploaded. Open Uploads to check its status." });
    } catch (err: any) {
      setPasteStatus({
        severity: "error",
        message: getErrorMessage(err, "Failed to upload pasted screenshot."),
      });
    } finally {
      setUploadingPaste(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !connectionId || !selectedLlmConfigId) return;
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "", streaming: true, toolStatuses: [] }]);
    setSending(true);
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await streamChat({
        connectionId: Number(connectionId),
        message: userMessage,
        llmConfigId: Number(selectedLlmConfigId),
        sessionId,
        signal: controller.signal,
        onEvent: (event: ChatStreamEvent) => {
          setMessages((prev) => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            const last = { ...updated[lastIdx] };

            if (event.type === "session") {
              setSessionId(event.session_id as number);
            } else if (event.type === "reply_chunk") {
              last.content += event.content as string;
            } else if (event.type === "status") {
              last.toolStatuses = [...(last.toolStatuses || []), event.label as string];
            } else if (event.type === "done") {
              last.content = (event.reply as string) || last.content;
              last.streaming = false;
            } else if (event.type === "error") {
              last.content = `Error: ${event.message}`;
              last.streaming = false;
            }

            updated[lastIdx] = last;
            return updated;
          });
        },
      });
    } catch (err) {
      if (controller.signal.aborted) {
        // User clicked Stop - keep whatever partial reply already streamed in
        // rather than replacing it with a failure message.
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          const last = { ...updated[lastIdx] };
          last.streaming = false;
          last.content = last.content || "(Stopped)";
          updated[lastIdx] = last;
          return updated;
        });
      } else {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: "Failed to reach the chat service.",
            streaming: false,
          };
          return updated;
        });
      }
    } finally {
      abortControllerRef.current = null;
      setSending(false);
      // The turn just persisted may have created a new session (with its
      // title derived from this message) or bumped an existing session's
      // updated_at - refresh the sidebar list to reflect that.
      refreshSessions();
    }
  };

  const handleStop = () => {
    abortControllerRef.current?.abort();
  };

  if (loading) return <CircularProgress />;

  return (
    <Box display="flex" gap={2} height="calc(100vh - 130px)">
      <ChatSidebar
        sessions={sessions}
        activeSessionId={sessionId}
        onSelect={handleSelectSession}
        onNewChat={handleNewChat}
        onRename={handleRenameSession}
        onDelete={handleDeleteSession}
        disabled={sending}
      />
      <Box display="flex" flexDirection="column" flexGrow={1} minWidth={0}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            {connection?.alias} ({connection?.db_name})
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel>LLM Model</InputLabel>
              <Select
                label="LLM Model"
                value={selectedLlmConfigId}
                onChange={(e) => setSelectedLlmConfigId(e.target.value as number)}
              >
                {llmConfigs.map((cfg) => (
                  <MenuItem key={cfg.id} value={cfg.id}>
                    {cfg.alias} ({cfg.provider})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        {llmConfigs.length === 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            You need to add an LLM model before you can chat. Go to{" "}
            <Link component={RouterLink} to="/llm-configs">
              LLM Configs
            </Link>{" "}
            to add one.
          </Alert>
        )}

        <Paper variant="outlined" sx={{ flexGrow: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <ChatWindow messages={messages} />
          <Box display="flex" gap={1} p={2} borderTop="1px solid #eee" alignItems="flex-end">
            <IconButton color="primary" onClick={() => setUploadsOpen(true)} sx={{ mb: 0.5 }} title="Uploads">
              <AttachFileIcon />
            </IconButton>
            <TextField
              fullWidth
              multiline
              minRows={1}
              maxRows={8}
              placeholder='e.g. "list all tables in public schema" or paste a screenshot (Ctrl+V)'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              onPaste={handlePaste}
              disabled={sending || !selectedLlmConfigId}
              sx={{ "& textarea": { overflowY: "auto" } }}
            />
            <IconButton
              color="primary"
              onClick={sending ? handleStop : handleSend}
              disabled={!sending && (!input.trim() || !selectedLlmConfigId)}
              sx={{ mb: 0.5 }}
              title={sending ? "Stop generating" : "Send"}
            >
              {sending ? <StopIcon /> : <SendIcon />}
            </IconButton>
            {uploadingPaste && <CircularProgress size={24} sx={{ alignSelf: "center" }} />}
          </Box>
        </Paper>
      </Box>

      {connectionId && (
        <UploadedDocsDialog
          open={uploadsOpen}
          onClose={() => setUploadsOpen(false)}
          connectionId={Number(connectionId)}
          llmConfigId={selectedLlmConfigId}
        />
      )}

      <Snackbar
        open={!!pasteStatus}
        autoHideDuration={5000}
        onClose={() => setPasteStatus(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        {pasteStatus ? (
          <Alert severity={pasteStatus.severity} onClose={() => setPasteStatus(null)} sx={{ width: "100%" }}>
            {pasteStatus.message}
          </Alert>
        ) : undefined}
      </Snackbar>
    </Box>
  );
}
