import React, { useState } from "react";
import { Box, Typography, TextField, Button, Alert, Paper } from "@mui/material";
import { useAuth } from "../context/AuthContext";
import {
  CHAT_HISTORY_RETENTION_MAX_DAYS,
  CHAT_HISTORY_RETENTION_MIN_DAYS,
  MAX_CHAT_SESSIONS_MAX,
  MAX_CHAT_SESSIONS_MIN,
} from "../types";

export default function Settings() {
  const { user, updateChatRetentionDays, updateMaxChatSessions } = useAuth();
  const [days, setDays] = useState<number>(user?.chat_history_retention_days ?? 30);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [maxSessions, setMaxSessions] = useState<number>(user?.max_chat_sessions ?? 15);
  const [savingSessions, setSavingSessions] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [sessionsSaved, setSessionsSaved] = useState(false);

  const handleSave = async () => {
    setError(null);
    setSaved(false);
    if (days < CHAT_HISTORY_RETENTION_MIN_DAYS || days > CHAT_HISTORY_RETENTION_MAX_DAYS) {
      setError(`Please enter a value between ${CHAT_HISTORY_RETENTION_MIN_DAYS} and ${CHAT_HISTORY_RETENTION_MAX_DAYS}.`);
      return;
    }
    setSaving(true);
    try {
      await updateChatRetentionDays(days);
      setSaved(true);
    } catch {
      setError("Failed to save setting. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMaxSessions = async () => {
    setSessionsError(null);
    setSessionsSaved(false);
    if (maxSessions < MAX_CHAT_SESSIONS_MIN || maxSessions > MAX_CHAT_SESSIONS_MAX) {
      setSessionsError(`Please enter a value between ${MAX_CHAT_SESSIONS_MIN} and ${MAX_CHAT_SESSIONS_MAX}.`);
      return;
    }
    setSavingSessions(true);
    try {
      await updateMaxChatSessions(maxSessions);
      setSessionsSaved(true);
    } catch {
      setSessionsError("Failed to save setting. Please try again.");
    } finally {
      setSavingSessions(false);
    }
  };

  return (
    <Box maxWidth={480}>
      <Typography variant="h5" mb={3}>
        Settings
      </Typography>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Chat History Retention
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          How many days of chat history should be kept and used as context in your conversations
          (max {CHAT_HISTORY_RETENTION_MAX_DAYS} days). Messages older than this are automatically deleted.
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            type="number"
            size="small"
            label="Days"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            inputProps={{ min: CHAT_HISTORY_RETENTION_MIN_DAYS, max: CHAT_HISTORY_RETENTION_MAX_DAYS }}
            sx={{ width: 120 }}
          />
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            Save
          </Button>
        </Box>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {saved && !error && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Saved.
          </Alert>
        )}
      </Paper>

      <Paper variant="outlined" sx={{ p: 3, mt: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Chat Sessions
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          How many chat sessions to keep per database connection (min {MAX_CHAT_SESSIONS_MIN}, max{" "}
          {MAX_CHAT_SESSIONS_MAX}). The oldest chat is automatically removed whenever a new one is started beyond
          this limit.
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            type="number"
            size="small"
            label="Sessions"
            value={maxSessions}
            onChange={(e) => setMaxSessions(Number(e.target.value))}
            inputProps={{ min: MAX_CHAT_SESSIONS_MIN, max: MAX_CHAT_SESSIONS_MAX }}
            sx={{ width: 120 }}
          />
          <Button variant="contained" onClick={handleSaveMaxSessions} disabled={savingSessions}>
            Save
          </Button>
        </Box>
        {sessionsError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {sessionsError}
          </Alert>
        )}
        {sessionsSaved && !sessionsError && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Saved.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
