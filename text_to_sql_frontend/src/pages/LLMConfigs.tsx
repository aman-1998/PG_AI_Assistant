import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  IconButton,
  CircularProgress,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { apiClient, getErrorMessage } from "../api/client";
import LLMConfigForm from "../components/LLMConfigForm";
import type { LLMConfig } from "../types";

export default function LLMConfigs() {
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<LLMConfig | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<LLMConfig[]>("/llm-configs");
      setConfigs(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  const handleDeleteClick = (cfg: LLMConfig) => {
    setError(null);
    setDeleteTarget(cfg);
  };

  const handleDeleteCancel = () => {
    setDeleteTarget(null);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    setError(null);
    try {
      await apiClient.delete(`/llm-configs/${deleteTarget.id}`);
      setDeleteTarget(null);
      loadConfigs();
    } catch (err) {
      setError(getErrorMessage(err, "Could not delete this LLM model"));
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  const handleAddClick = () => {
    setEditingConfig(null);
    setFormOpen(true);
  };

  const handleEditClick = (cfg: LLMConfig) => {
    setEditingConfig(cfg);
    setFormOpen(true);
  };

  const handleFormClose = () => {
    setFormOpen(false);
    setEditingConfig(null);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">LLM Model Configurations</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddClick}>
          Add Model
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <CircularProgress />
      ) : configs.length === 0 ? (
        <Typography color="text.secondary">
          No LLM models configured yet. Add one before starting a chat.
        </Typography>
      ) : (
        <List>
          {configs.map((cfg) => (
            <ListItem
              key={cfg.id}
              divider
              secondaryAction={
                <>
                  <IconButton edge="end" onClick={() => handleEditClick(cfg)} sx={{ mr: 1 }}>
                    <EditIcon />
                  </IconButton>
                  <IconButton edge="end" onClick={() => handleDeleteClick(cfg)}>
                    <DeleteIcon />
                  </IconButton>
                </>
              }
            >
              <ListItemText
                primary={
                  <>
                    {cfg.alias} <Chip size="small" label={cfg.provider} sx={{ ml: 1 }} />
                  </>
                }
                secondary={cfg.model_name}
              />
            </ListItem>
          ))}
        </List>
      )}

      <LLMConfigForm open={formOpen} onClose={handleFormClose} onSaved={loadConfigs} initialData={editingConfig} />

      <Dialog open={Boolean(deleteTarget)} onClose={handleDeleteCancel}>
        <DialogTitle>Delete LLM model?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete <strong>{deleteTarget?.alias}</strong>? This will also permanently
            delete any chat sessions (and their messages) that used this model. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deleting}>
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained" disabled={deleting}>
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
