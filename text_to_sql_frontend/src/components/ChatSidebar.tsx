import React, { useState } from "react";
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  TextField,
  Button,
  Divider,
  Typography,
} from "@mui/material";
import AddCommentIcon from "@mui/icons-material/AddComment";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import type { ChatSession } from "../types";

interface Props {
  sessions: ChatSession[];
  activeSessionId: number | null;
  onSelect: (session: ChatSession) => void;
  onNewChat: () => void;
  onRename: (session: ChatSession, title: string) => void;
  onDelete: (session: ChatSession) => void;
  disabled?: boolean;
}

function sessionLabel(session: ChatSession): string {
  if (session.title && session.title.trim()) return session.title;
  return `Chat - ${new Date(session.created_at).toLocaleString()}`;
}

export default function ChatSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNewChat,
  onRename,
  onDelete,
  disabled,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");

  const startEditing = (session: ChatSession) => {
    setEditingId(session.id);
    setEditValue(sessionLabel(session));
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditValue("");
  };

  const commitEditing = (session: ChatSession) => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== sessionLabel(session)) {
      onRename(session, trimmed);
    }
    cancelEditing();
  };

  const handleDelete = (session: ChatSession) => {
    if (window.confirm(`Delete "${sessionLabel(session)}"? This cannot be undone.`)) {
      onDelete(session);
    }
  };

  return (
    <Box
      sx={{
        width: 260,
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        height: "100%",
        overflow: "hidden",
      }}
    >
      <Box sx={{ p: 1.5 }}>
        <Button fullWidth variant="outlined" startIcon={<AddCommentIcon />} onClick={onNewChat} disabled={disabled}>
          New Chat
        </Button>
      </Box>
      <Divider />
      <Box sx={{ flexGrow: 1, overflowY: "auto" }}>
        {sessions.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
            No previous chats yet.
          </Typography>
        ) : (
          <List dense disablePadding>
            {sessions.map((session) => {
              const isEditing = editingId === session.id;
              return (
                <Box
                  key={session.id}
                  sx={{
                    position: "relative",
                    "&:hover .session-actions": { visibility: isEditing ? "hidden" : "visible" },
                  }}
                >
                  {isEditing ? (
                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, px: 1.5, py: 1 }}>
                      <TextField
                        size="small"
                        fullWidth
                        autoFocus
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            commitEditing(session);
                          } else if (e.key === "Escape") {
                            e.preventDefault();
                            cancelEditing();
                          }
                        }}
                      />
                      <IconButton size="small" onClick={() => commitEditing(session)}>
                        <CheckIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={cancelEditing}>
                        <CloseIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  ) : (
                    <ListItemButton
                      selected={session.id === activeSessionId}
                      onClick={() => onSelect(session)}
                      sx={{ py: 1, pr: 9 }}
                    >
                      <ListItemText
                        primary={sessionLabel(session)}
                        primaryTypographyProps={{ noWrap: true, fontSize: "0.875rem" }}
                      />
                      <ListItemSecondaryAction
                        className="session-actions"
                        sx={{ visibility: "hidden", display: "flex", gap: 0.5 }}
                      >
                        <IconButton
                          size="small"
                          edge="end"
                          disabled={disabled}
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditing(session);
                          }}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          edge="end"
                          disabled={disabled}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(session);
                          }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItemButton>
                  )}
                </Box>
              );
            })}
          </List>
        )}
      </Box>
    </Box>
  );
}
