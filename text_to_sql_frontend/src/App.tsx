import React from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  Avatar,
  Divider,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import { alpha, type Breakpoint } from "@mui/material/styles";
import StorageIcon from "@mui/icons-material/Storage";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import SettingsIcon from "@mui/icons-material/Settings";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import LogoutIcon from "@mui/icons-material/Logout";
import DataObjectIcon from "@mui/icons-material/DataObject";
import { useAuth } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import DatabaseConnections from "./pages/DatabaseConnections";
import LLMConfigs from "./pages/LLMConfigs";
import Chat from "./pages/Chat";
import Documentation from "./pages/Documentation";
import Settings from "./pages/Settings";
import ContactFeedback from "./pages/ContactFeedback";

const NAV_ITEMS = [
  { to: "/connections", label: "Databases", icon: <StorageIcon fontSize="small" /> },
  { to: "/llm-configs", label: "LLM Models", icon: <SmartToyIcon fontSize="small" /> },
  { to: "/documentation", label: "Documentation", icon: <MenuBookIcon fontSize="small" /> },
  { to: "/settings", label: "Settings", icon: <SettingsIcon fontSize="small" /> },
  { to: "/feedback", label: "Feedback", icon: <ChatBubbleOutlineIcon fontSize="small" /> },
];

function NavLink({ to, label, icon }: { to: string; label: string; icon: React.ReactNode }) {
  const location = useLocation();
  const active = location.pathname === to || (to !== "/connections" && location.pathname.startsWith(to));

  return (
    <Button
      component={Link}
      to={to}
      startIcon={icon}
      sx={{
        color: "common.white",
        textTransform: "none",
        fontWeight: active ? 600 : 500,
        px: 1.75,
        py: 0.75,
        borderRadius: 999,
        bgcolor: active ? alpha("#ffffff", 0.18) : "transparent",
        "&:hover": { bgcolor: alpha("#ffffff", active ? 0.24 : 0.1) },
        transition: "background-color 0.15s ease",
      }}
    >
      {label}
    </Button>
  );
}

function Layout({
  children,
  maxWidth = "lg",
}: {
  children: React.ReactNode;
  maxWidth?: Breakpoint | false;
}) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [logoutConfirmOpen, setLogoutConfirmOpen] = React.useState(false);

  const handleLogoutConfirmed = () => {
    setLogoutConfirmOpen(false);
    logout();
    navigate("/login");
  };

  return (
    <Box>
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          background: "linear-gradient(90deg, #1d4ed8 0%, #2563eb 55%, #0ea5e9 100%)",
          boxShadow: "0 2px 10px rgba(15, 23, 42, 0.18)",
        }}
      >
        <Toolbar sx={{ gap: 1.5, minHeight: 64 }}>
          <Box display="flex" alignItems="center" gap={1} sx={{ flexGrow: 1, minWidth: 0 }}>
            <Box
              display="flex"
              alignItems="center"
              justifyContent="center"
              sx={{ width: 34, height: 34, borderRadius: 2, bgcolor: alpha("#ffffff", 0.15) }}
            >
              <DataObjectIcon fontSize="small" />
            </Box>
            <Typography variant="h6" noWrap sx={{ fontWeight: 600, letterSpacing: 0.2 }}>
              PG AI Assistant
            </Typography>
          </Box>
          {user && (
            <>
              <Box display="flex" alignItems="center" gap={0.5}>
                {NAV_ITEMS.map((item) => (
                  <NavLink key={item.to} to={item.to} label={item.label} icon={item.icon} />
                ))}
              </Box>
              <Divider orientation="vertical" flexItem sx={{ borderColor: alpha("#ffffff", 0.25), mx: 1, my: 1.5 }} />
              <Box display="flex" alignItems="center" gap={1}>
                <Avatar sx={{ width: 30, height: 30, fontSize: "0.85rem", bgcolor: alpha("#ffffff", 0.22) }}>
                  {user.email[0]?.toUpperCase()}
                </Avatar>
                <Typography variant="body2" sx={{ display: { xs: "none", md: "block" }, opacity: 0.9 }} noWrap>
                  {user.email}
                </Typography>
                <Tooltip title="Logout">
                  <IconButton
                    size="small"
                    onClick={() => setLogoutConfirmOpen(true)}
                    sx={{ color: "common.white", "&:hover": { bgcolor: alpha("#ffffff", 0.15) } }}
                  >
                    <LogoutIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </>
          )}
        </Toolbar>
      </AppBar>
      <Container maxWidth={maxWidth} sx={{ py: 3, px: maxWidth === false ? { xs: 2, sm: 3 } : undefined }}>
        {children}
      </Container>

      <Dialog open={logoutConfirmOpen} onClose={() => setLogoutConfirmOpen(false)}>
        <DialogTitle>Log out?</DialogTitle>
        <DialogContent>
          <DialogContentText>Are you sure you want to log out of PG AI Assistant?</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogoutConfirmOpen(false)}>Cancel</Button>
          <Button onClick={handleLogoutConfirmed} color="error" variant="contained">
            Logout
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route
        path="/connections"
        element={
          <ProtectedRoute>
            <Layout maxWidth={false}>
              <DatabaseConnections />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/llm-configs"
        element={
          <ProtectedRoute>
            <Layout maxWidth={false}>
              <LLMConfigs />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat/:connectionId"
        element={
          <ProtectedRoute>
            <Layout maxWidth={false}>
              <Chat />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/documentation"
        element={
          <ProtectedRoute>
            <Layout maxWidth={false}>
              <Documentation />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Layout maxWidth={false}>
              <Settings />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/feedback"
        element={
          <ProtectedRoute>
            <Layout maxWidth={false}>
              <ContactFeedback />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/connections" replace />} />
    </Routes>
  );
}
