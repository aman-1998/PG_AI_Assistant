import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
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
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import DataObjectIcon from "@mui/icons-material/DataObject";
import { apiClient, getErrorMessage } from "../api/client";

const gradientBoxSx = {
  background: "linear-gradient(135deg, #1d4ed8 0%, #2563eb 45%, #0ea5e9 100%)",
  p: 2,
};

const paperSx = {
  p: 4,
  width: 400,
  borderRadius: 3,
  boxShadow: "0 20px 45px rgba(15, 23, 42, 0.25)",
};

function BrandHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
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
        {title}
      </Typography>
      {subtitle && (
        <Typography variant="body2" color="text.secondary" textAlign="center">
          {subtitle}
        </Typography>
      )}
    </Box>
  );
}

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/auth/reset-password", { token, new_password: newPassword });
      setMessage("Password reset successfully. Redirecting to login...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err: any) {
      setError(getErrorMessage(err, "Could not reset password"));
    } finally {
      setSubmitting(false);
    }
  };

  if (!token) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" sx={gradientBoxSx}>
        <Paper elevation={0} sx={paperSx}>
          <BrandHeader title="Reset password" />
          <Alert severity="error">Missing or invalid reset link.</Alert>
          <Typography variant="body2" mt={3} textAlign="center" color="text.secondary">
            <Link to="/forgot-password">Request a new reset link</Link>
          </Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" sx={gradientBoxSx}>
      <Paper elevation={0} sx={paperSx}>
        <BrandHeader title="Reset password" />
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
            label="New password"
            type="password"
            fullWidth
            margin="normal"
            helperText="At least 8 characters"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockOutlinedIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            label="Retype new password"
            type="password"
            fullWidth
            margin="normal"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={confirmPassword.length > 0 && confirmPassword !== newPassword}
            helperText={confirmPassword.length > 0 && confirmPassword !== newPassword ? "Passwords do not match" : " "}
            required
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockOutlinedIcon fontSize="small" color="action" />
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
            {submitting ? <CircularProgress size={22} color="inherit" /> : "Reset password"}
          </Button>
        </form>
      </Paper>
    </Box>
  );
}
