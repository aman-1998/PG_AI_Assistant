import React, { useEffect, useState } from "react";
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
import type { LLMConfig, LLMProvider } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initialData?: LLMConfig | null;
}

const PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "gemini", label: "Google Gemini" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "bedrock", label: "AWS Bedrock" },
];

const DEFAULT_FORM = {
  alias: "",
  provider: "openai" as LLMProvider,
  model_name: "",
  api_key: "",
  secret_key: "",
  base_url: "",
  region: "",
  api_version: "",
};

export default function LLMConfigForm({ open, onClose, onSaved, initialData }: Props) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const isEditing = Boolean(initialData);

  useEffect(() => {
    if (!open) return;
    setError(null);
    if (initialData) {
      setForm({
        alias: initialData.alias,
        provider: initialData.provider,
        model_name: initialData.model_name,
        api_key: "",
        secret_key: "",
        base_url: initialData.base_url || "",
        region: initialData.region || "",
        api_version: initialData.api_version || "",
      });
    } else {
      setForm(DEFAULT_FORM);
    }
  }, [open, initialData]);

  const handleChange = (field: keyof typeof DEFAULT_FORM) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      if (initialData) {
        const payload: Record<string, unknown> = {
          alias: form.alias,
          model_name: form.model_name,
          base_url: form.base_url || null,
          region: form.region || null,
          api_version: form.api_version || null,
        };
        if (form.api_key) payload.api_key = form.api_key;
        if (form.secret_key) payload.secret_key = form.secret_key;
        await apiClient.put(`/llm-configs/${initialData.id}`, payload);
      } else {
        await apiClient.post("/llm-configs", form);
      }
      onSaved();
      onClose();
      setForm(DEFAULT_FORM);
    } catch (err: any) {
      setError(getErrorMessage(err, "Could not save LLM configuration"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEditing ? "Edit LLM Model" : "Configure LLM Model"}</DialogTitle>
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
          <Grid size={{ xs: 12 }}>
            <TextField
              select
              label="Provider"
              fullWidth
              value={form.provider}
              disabled={isEditing}
              helperText={isEditing ? "Provider can't be changed - delete and re-add to switch providers" : undefined}
              onChange={(e) => setForm((prev) => ({ ...prev, provider: e.target.value as LLMProvider }))}
            >
              {PROVIDERS.map((p) => (
                <MenuItem key={p.value} value={p.value}>
                  {p.label}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField
              label="Model name / deployment name"
              fullWidth
              value={form.model_name}
              onChange={handleChange("model_name")}
              required
              helperText="e.g. gpt-4o, claude-3-5-sonnet-20241022, gemini-1.5-pro, anthropic.claude-3-sonnet"
            />
          </Grid>

          {form.provider !== "bedrock" && (
            <Grid size={{ xs: 12 }}>
              <TextField
                label="API key"
                type="password"
                fullWidth
                value={form.api_key}
                onChange={handleChange("api_key")}
                helperText={isEditing ? "Leave blank to keep the existing key" : undefined}
              />
            </Grid>
          )}

          {form.provider === "bedrock" && (
            <>
              <Grid size={{ xs: 6 }}>
                <TextField
                  label="AWS access key ID"
                  fullWidth
                  value={form.api_key}
                  onChange={handleChange("api_key")}
                  helperText={isEditing ? "Leave blank to keep existing" : undefined}
                />
              </Grid>
              <Grid size={{ xs: 6 }}>
                <TextField
                  label="AWS secret access key"
                  type="password"
                  fullWidth
                  value={form.secret_key}
                  onChange={handleChange("secret_key")}
                  helperText={isEditing ? "Leave blank to keep existing" : undefined}
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField label="AWS region" fullWidth value={form.region} onChange={handleChange("region")} />
              </Grid>
            </>
          )}

          {form.provider === "azure_openai" && (
            <>
              <Grid size={{ xs: 8 }}>
                <TextField
                  label="Azure endpoint (base URL)"
                  fullWidth
                  value={form.base_url}
                  onChange={handleChange("base_url")}
                />
              </Grid>
              <Grid size={{ xs: 4 }}>
                <TextField
                  label="API version"
                  fullWidth
                  value={form.api_version}
                  onChange={handleChange("api_version")}
                  placeholder="2024-06-01"
                />
              </Grid>
            </>
          )}
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={submitting}>
          {isEditing ? "Save Changes" : "Save"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
