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
  Grid,
  Stack,
  Divider,
  Collapse,
  List,
  ListItem,
  ListItemText,
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
import SpeedIcon from "@mui/icons-material/Speed";
import MemoryIcon from "@mui/icons-material/Memory";
import StorageIcon from "@mui/icons-material/Storage";
import BoltIcon from "@mui/icons-material/Bolt";
import GroupIcon from "@mui/icons-material/Group";
import SwapVertIcon from "@mui/icons-material/SwapVert";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import TableChartIcon from "@mui/icons-material/TableChart";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
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

function formatRelativeTime(iso?: string | null): string {
  if (!iso) return "-";
  const then = new Date(iso).getTime();
  const diffSec = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  return `${diffHr}h ago`;
}

/** Higher-is-worse thresholds (e.g. CPU load, connection pool usage). */
function loadColor(pct: number | null | undefined): "success" | "warning" | "error" {
  const value = pct ?? 0;
  if (value >= 85) return "error";
  if (value >= 60) return "warning";
  return "success";
}

/** Higher-is-better thresholds (e.g. cache hit ratio). */
function healthColor(pct: number | null | undefined): "success" | "warning" | "error" {
  if (pct === null || pct === undefined) return "warning";
  if (pct >= 95) return "success";
  if (pct >= 85) return "warning";
  return "error";
}

function MetricTile({
  icon,
  label,
  value,
  progressPct,
  progressColor,
  tooltip,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  progressPct?: number | null;
  progressColor?: "success" | "warning" | "error";
  tooltip?: string;
}) {
  const content = (
    <Box
      sx={{
        p: 1.25,
        borderRadius: 1.5,
        bgcolor: "action.hover",
        height: "100%",
      }}
    >
      <Stack direction="row" alignItems="center" spacing={0.75} mb={0.5}>
        <Box sx={{ display: "flex", color: "text.secondary" }}>{icon}</Box>
        <Typography variant="caption" color="text.secondary" noWrap>
          {label}
        </Typography>
      </Stack>
      <Typography variant="subtitle2" fontWeight={600}>
        {value}
      </Typography>
      {progressPct !== undefined && (
        <LinearProgress
          variant="determinate"
          color={progressColor}
          value={Math.min(Math.max(progressPct ?? 0, 0), 100)}
          sx={{ mt: 1, height: 6, borderRadius: 3 }}
        />
      )}
    </Box>
  );

  return tooltip ? (
    <Tooltip title={tooltip} placement="top" arrow>
      {content}
    </Tooltip>
  ) : (
    content
  );
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
  const [tablesOpen, setTablesOpen] = useState(false);

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

  const connectionPoolPct =
    metrics?.total_connections != null && metrics?.max_connections
      ? Math.min(100, (metrics.total_connections / metrics.max_connections) * 100)
      : null;

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
            <Stack direction="row" alignItems="center" spacing={0.5} mb={1}>
              <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: 0.5 }}>
                Live metrics
              </Typography>
              <Tooltip
                title={`${metrics.cpu_usage_note} • ${metrics.memory_usage_note} • ${metrics.disk_io_note}`}
                placement="top"
                arrow
              >
                <InfoOutlinedIcon sx={{ fontSize: 14, color: "text.disabled" }} />
              </Tooltip>
            </Stack>

            <Grid container spacing={1}>
              <Grid item xs={6}>
                <MetricTile
                  icon={<SpeedIcon fontSize="small" />}
                  label="CPU load (approx.)"
                  value={`${(metrics.cpu_usage_approx_pct ?? 0).toFixed(1)}%`}
                  progressPct={metrics.cpu_usage_approx_pct}
                  progressColor={loadColor(metrics.cpu_usage_approx_pct)}
                  tooltip={metrics.cpu_usage_note}
                />
              </Grid>
              <Grid item xs={6}>
                <MetricTile
                  icon={<MemoryIcon fontSize="small" />}
                  label="Cache hit ratio"
                  value={
                    metrics.memory_cache_hit_ratio_pct != null
                      ? `${metrics.memory_cache_hit_ratio_pct.toFixed(1)}%`
                      : "-"
                  }
                  progressPct={metrics.memory_cache_hit_ratio_pct}
                  progressColor={healthColor(metrics.memory_cache_hit_ratio_pct)}
                  tooltip={metrics.memory_usage_note}
                />
              </Grid>
              <Grid item xs={6}>
                <MetricTile
                  icon={<GroupIcon fontSize="small" />}
                  label="Connections"
                  value={`${metrics.active_connections ?? 0} active / ${metrics.total_connections ?? "-"}${
                    metrics.max_connections ? ` of ${metrics.max_connections}` : ""
                  }`}
                  progressPct={connectionPoolPct ?? undefined}
                  progressColor={loadColor(connectionPoolPct)}
                  tooltip="Active and total backend connections vs. the server's max_connections limit"
                />
              </Grid>
              <Grid item xs={6}>
                <MetricTile
                  icon={<BoltIcon fontSize="small" />}
                  label="Transactions / sec"
                  value={metrics.transactions_per_sec != null ? metrics.transactions_per_sec.toFixed(1) : "-"}
                  tooltip="Committed + rolled-back transactions per second, sampled over ~1s"
                />
              </Grid>
              <Grid item xs={6}>
                <MetricTile
                  icon={<SwapVertIcon fontSize="small" />}
                  label="Disk I/O (per sec)"
                  value={`${metrics.disk_io_blocks_read_per_sec ?? 0} rd / ${
                    metrics.disk_io_buffers_written_per_sec ?? 0
                  } wr`}
                  tooltip={metrics.disk_io_note}
                />
              </Grid>
              <Grid item xs={6}>
                <MetricTile
                  icon={<StorageIcon fontSize="small" />}
                  label="Disk usage"
                  value={formatBytes(metrics.disk_usage_bytes)}
                  tooltip="Total on-disk size of this database (pg_database_size)"
                />
              </Grid>
            </Grid>

            {metrics.largest_tables.length > 0 && (
              <Box mt={1.5}>
                <Divider sx={{ mb: 1 }} />
                <Box
                  onClick={() => setTablesOpen((v) => !v)}
                  sx={{ display: "flex", alignItems: "center", cursor: "pointer", userSelect: "none" }}
                >
                  <TableChartIcon fontSize="small" sx={{ color: "text.secondary", mr: 0.75 }} />
                  <Typography variant="body2" sx={{ flexGrow: 1 }}>
                    Largest tables
                  </Typography>
                  <ExpandMoreIcon
                    fontSize="small"
                    sx={{
                      color: "text.secondary",
                      transform: tablesOpen ? "rotate(180deg)" : "rotate(0deg)",
                      transition: "transform 0.2s",
                    }}
                  />
                </Box>
                <Collapse in={tablesOpen} timeout="auto" unmountOnExit>
                  <List dense disablePadding sx={{ mt: 0.5 }}>
                    {metrics.largest_tables.slice(0, 10).map((t) => (
                      <ListItem key={t.table_name} disableGutters sx={{ py: 0.25 }}>
                        <ListItemText
                          primaryTypographyProps={{ variant: "body2", noWrap: true, title: t.table_name }}
                          primary={t.table_name}
                        />
                        <Typography variant="body2" color="text.secondary" sx={{ pl: 1, flexShrink: 0 }}>
                          {formatBytes(t.size_bytes)}
                        </Typography>
                      </ListItem>
                    ))}
                  </List>
                </Collapse>
              </Box>
            )}

            <Typography variant="caption" color="text.disabled" display="block" mt={1.5}>
              Updated {formatRelativeTime(metrics.fetched_at)}
            </Typography>
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
