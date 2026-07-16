import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid2 as Grid,
  MenuItem,
  Alert,
} from "@mui/material";
import { apiClient, getErrorMessage } from "../api/client";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const SSL_MODES = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"];

export default function DatabaseConnectionForm({ open, onClose, onCreated }: Props) {
  const [form, setForm] = useState({
    alias: "",
    host: "",
    port: 5432,
    db_name: "",
    username: "",
    password: "",
    sslmode: "prefer",
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = field === "port" ? Number(e.target.value) : e.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await apiClient.post("/database-connections", form);
      onCreated();
      onClose();
      setForm({ alias: "", host: "", port: 5432, db_name: "", username: "", password: "", sslmode: "prefer" });
    } catch (err: any) {
      setError(getErrorMessage(err, "Could not import database"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Import PostgreSQL Database</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Grid container spacing={2} sx={{ mt: 0.5 }}>
          <Grid size={{ xs: 12 }}>
            <TextField label="Alias / Nickname" fullWidth value={form.alias} onChange={handleChange("alias")} required />
          </Grid>
          <Grid size={{ xs: 8 }}>
            <TextField label="Host" fullWidth value={form.host} onChange={handleChange("host")} required />
          </Grid>
          <Grid size={{ xs: 4 }}>
            <TextField label="Port" type="number" fullWidth value={form.port} onChange={handleChange("port")} required />
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField label="Database name" fullWidth value={form.db_name} onChange={handleChange("db_name")} required />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField label="Username" fullWidth value={form.username} onChange={handleChange("username")} required />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField
              label="Password"
              type="password"
              fullWidth
              value={form.password}
              onChange={handleChange("password")}
              required
            />
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField select label="SSL mode" fullWidth value={form.sslmode} onChange={handleChange("sslmode")}>
              {SSL_MODES.map((mode) => (
                <MenuItem key={mode} value={mode}>
                  {mode}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={submitting}>
          Import
        </Button>
      </DialogActions>
    </Dialog>
  );
}
