import React, { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
  Typography,
  Alert,
  CircularProgress,
  Box,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import DeleteIcon from "@mui/icons-material/Delete";
import { apiClient, getErrorMessage } from "../api/client";
import type { UploadedFile } from "../types";

const ACCEPTED_EXTENSIONS = ".sql,.txt,.png,.jpg,.jpeg,.gif,.webp";

interface Props {
  open: boolean;
  onClose: () => void;
  connectionId: number;
  llmConfigId: number | "";
}

function statusColor(status: string): "default" | "success" | "warning" | "error" {
  if (status === "ready") return "success";
  if (status === "processing") return "warning";
  if (status === "failed") return "error";
  return "default";
}

export default function UploadedDocsDialog({ open, onClose, connectionId, llmConfigId }: Props) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<UploadedFile[]>(`/database-connections/${connectionId}/uploads`);
      setFiles(res.data);
    } catch {
      setError("Failed to load uploaded files.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      setError(null);
      loadFiles();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, connectionId]);

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !llmConfigId) return;

    setError(null);
    setUploading(true);
    const formData = new FormData();
    formData.append("llm_config_id", String(llmConfigId));
    formData.append("file", file);

    try {
      await apiClient.post(`/database-connections/${connectionId}/uploads`, formData);
      await loadFiles();
    } catch (err: any) {
      setError(getErrorMessage(err, "Upload failed."));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (fileId: string) => {
    try {
      await apiClient.delete(`/database-connections/${connectionId}/uploads/${fileId}`);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch {
      setError("Failed to delete file.");
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Uploaded Docs (.sql files &amp; images)</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Upload a <code>.sql</code> schema file or an image (ER diagram / schema screenshot) to give
          the documentation agent extra business context for this database connection. Images are
          described by your selected LLM model at upload time.
        </Typography>

        {!llmConfigId && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            Select an LLM model in the chat toolbar before uploading.
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Button
          variant="outlined"
          startIcon={uploading ? <CircularProgress size={16} /> : <UploadFileIcon />}
          disabled={!llmConfigId || uploading}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading ? "Uploading..." : "Upload file"}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          hidden
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleFileSelected}
        />

        <Box mt={2}>
          {loading ? (
            <CircularProgress size={20} />
          ) : files.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No files uploaded yet.
            </Typography>
          ) : (
            <List dense>
              {files.map((f) => (
                <ListItem
                  key={f.id}
                  divider
                  secondaryAction={
                    <IconButton edge="end" onClick={() => handleDelete(f.id)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  }
                >
                  <ListItemText
                    primary={
                      <>
                        {f.filename} <Chip size="small" label={f.status} color={statusColor(f.status)} sx={{ ml: 1 }} />
                      </>
                    }
                    secondary={`${f.file_type.toUpperCase()} · ${f.size_kb} KB · ${f.chunk_count} chunks`}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
