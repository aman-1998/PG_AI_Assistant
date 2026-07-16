import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  IconButton,
  Button,
  Box,
  LinearProgress,
  Tooltip,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import ChatIcon from "@mui/icons-material/Chat";
import DeleteIcon from "@mui/icons-material/Delete";
import { apiClient, getErrorMessage } from "../api/client";
import type { DatabaseConnection, DatabaseMetrics } from "../types";

function formatBytes(bytes?: number | null): string {
  if (bytes === undefined || bytes === null) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex++;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

export default function DatabaseCard({
  connection,
  onDeleted,
}: {
  connection: DatabaseConnection;
  onDeleted?: () => void;
}) {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<DatabaseMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await apiClient.delete(`/database-connections/${connection.id}`);
      setDeleteOpen(false);
      onDeleted?.();
    } catch (err: any) {
      setError(getErrorMessage(err, "Could not delete database connection"));
      setDeleteOpen(false);
    } finally {
      setDeleting(false);
    }
  };

  const refreshMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<DatabaseMetrics>(`/database-connections/${connection.id}/metrics`);
      setMetrics(res.data);
    } catch (err: any) {
      setError(getErrorMessage(err, "Could not fetch metrics"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connection.id]);

  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="h6">{connection.alias}</Typography>
            <Typography variant="body2" color="text.secondary">
              {connection.host}:{connection.port}/{connection.db_name}
            </Typography>
          </Box>
          <Box>
            <Tooltip title="Refresh metrics (approximate, Postgres-native stats)">
              <span>
                <IconButton onClick={refreshMetrics} disabled={loading}>
                  {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="Remove database">
              <IconButton onClick={() => setDeleteOpen(true)} color="error">
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Box mt={1}>
          <Chip
            size="small"
            label={connection.last_check_status === "ok" ? "Reachable" : connection.last_check_status || "Unknown"}
            color={connection.last_check_status === "ok" ? "success" : "default"}
          />
        </Box>

        {error && (
          <Typography variant="body2" color="error" mt={1}>
            {error}
          </Typography>
        )}

        {metrics && (
          <Box mt={2}>
            <Typography variant="caption" color="text.secondary">
              CPU usage (approx.)
            </Typography>
            <Tooltip title={`${(metrics.cpu_usage_approx_pct ?? 0).toFixed(1)}%`} placement="top" arrow>
              <LinearProgress
                variant="determinate"
                value={Math.min(metrics.cpu_usage_approx_pct ?? 0, 100)}
                sx={{ mb: 1 }}
              />
            </Tooltip>
            <Typography variant="caption" color="text.secondary">
              Memory cache hit ratio (approx.)
            </Typography>
            <Tooltip title={`${(metrics.memory_cache_hit_ratio_pct ?? 0).toFixed(1)}%`} placement="top" arrow>
              <LinearProgress
                variant="determinate"
                color="secondary"
                value={Math.min(metrics.memory_cache_hit_ratio_pct ?? 0, 100)}
                sx={{ mb: 1 }}
              />
            </Tooltip>
            <Typography variant="body2">
              Disk I/O (approx.): {metrics.disk_io_blocks_read_per_sec ?? 0} blocks read/s,{" "}
              {metrics.disk_io_buffers_written_per_sec ?? 0} buffers written/s
            </Typography>
            <Typography variant="body2">Disk usage: {formatBytes(metrics.disk_usage_bytes)}</Typography>
            <Typography variant="body2">Active connections: {metrics.active_connections ?? "-"}</Typography>
          </Box>
        )}
      </CardContent>
      <CardActions>
        <Button startIcon={<ChatIcon />} onClick={() => navigate(`/chat/${connection.id}`)}>
          Chat
        </Button>
      </CardActions>

      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>Remove database?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will remove "{connection.alias}" ({connection.host}:{connection.port}/{connection.db_name}) from your
            account. This does not affect the actual database, only this saved connection.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)} disabled={deleting}>
            Cancel
          </Button>
          <Button onClick={handleDelete} color="error" disabled={deleting}>
            {deleting ? <CircularProgress size={20} /> : "Remove"}
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}
