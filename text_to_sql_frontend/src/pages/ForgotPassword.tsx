import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  InputAdornment,
  CircularProgress,
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import DataObjectIcon from "@mui/icons-material/DataObject";
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
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      sx={{
        background: "linear-gradient(135deg, #1d4ed8 0%, #2563eb 45%, #0ea5e9 100%)",
        p: 2,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          p: 4,
          width: 400,
          borderRadius: 3,
          boxShadow: "0 20px 45px rgba(15, 23, 42, 0.25)",
        }}
      >
        <Box display="flex" flexDirection="column" alignItems="center" mb={3}>
          <Box
            display="flex"
            alignItems="center"
            justifyContent="center"
            sx={{
              width: 52,
              height: 52,
              borderRadius: 2.5,
              mb: 1.5,
              background: "linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 100%)",
              color: "common.white",
            }}
          >
            <DataObjectIcon />
          </Box>
          <Typography variant="h5" fontWeight={600}>
            Forgot password
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Enter your account email and we'll send you a link to reset your password.
          </Typography>
        </Box>
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
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <EmailOutlinedIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
            }}
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={submitting}
            sx={{
              mt: 2.5,
              py: 1.1,
              textTransform: "none",
              fontWeight: 600,
              fontSize: "1rem",
              borderRadius: 2,
              background: "linear-gradient(90deg, #1d4ed8 0%, #2563eb 55%, #0ea5e9 100%)",
              boxShadow: `0 8px 20px ${alpha("#2563eb", 0.35)}`,
              "&:hover": {
                background: "linear-gradient(90deg, #1e40af 0%, #1d4ed8 55%, #0284c7 100%)",
              },
            }}
          >
            {submitting ? <CircularProgress size={22} color="inherit" /> : "Send reset link"}
          </Button>
        </form>
        <Typography variant="body2" mt={3} textAlign="center" color="text.secondary">
          <Link to="/login">Back to login</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
