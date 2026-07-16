import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Box, Paper, TextField, Button, Typography, Alert } from "@mui/material";
import { apiClient, getErrorMessage } from "../api/client";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const res = await apiClient.post("/auth/forgot-password", { email });
      setMessage(res.data?.message || "If an account with that email exists, a password reset link has been sent.");
    } catch (err: any) {
      setError(getErrorMessage(err, "Could not process the request"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
      <Paper sx={{ p: 4, width: 380 }} elevation={3}>
        <Typography variant="h5" mb={2}>
          Forgot password
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Enter your account email and we'll send you a link to reset your password.
        </Typography>
        {message && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <form onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} disabled={submitting}>
            Send reset link
          </Button>
        </form>
        <Typography variant="body2" mt={2}>
          <Link to="/login">Back to login</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
