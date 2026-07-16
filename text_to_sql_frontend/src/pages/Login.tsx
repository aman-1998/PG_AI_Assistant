import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
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
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import DataObjectIcon from "@mui/icons-material/DataObject";
import { getErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/connections");
    } catch (err: any) {
      setError(getErrorMessage(err, "Login failed"));
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
            Welcome back
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Log in to PG AI Assistant
          </Typography>
        </Box>
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
          <TextField
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockOutlinedIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
            }}
          />
          <Box display="flex" justifyContent="flex-end" mt={0.5}>
            <Link to="/forgot-password" style={{ fontSize: "0.875rem" }}>
              Forgot password?
            </Link>
          </Box>
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
            {submitting ? <CircularProgress size={22} color="inherit" /> : "Log in"}
          </Button>
        </form>
        <Typography variant="body2" mt={3} textAlign="center" color="text.secondary">
          No account? <Link to="/signup">Sign up</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
