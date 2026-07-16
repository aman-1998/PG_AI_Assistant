import React from "react";
import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import { AppBar, Toolbar, Typography, Button, Box, Container } from "@mui/material";
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

function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <Box>
      <AppBar position="static" color="primary">
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Text-to-SQL Postgres Chat
          </Typography>
          {user && (
            <>
              <Button color="inherit" component={Link} to="/connections">
                Databases
              </Button>
              <Button color="inherit" component={Link} to="/llm-configs">
                LLM Models
              </Button>
              <Button color="inherit" component={Link} to="/documentation">
                Documentation
              </Button>
              <Button color="inherit" component={Link} to="/settings">
                Settings
              </Button>
              <Button
                color="inherit"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
              >
                Logout ({user.email})
              </Button>
            </>
          )}
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {children}
      </Container>
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
            <Layout>
              <DatabaseConnections />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/llm-configs"
        element={
          <ProtectedRoute>
            <Layout>
              <LLMConfigs />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat/:connectionId"
        element={
          <ProtectedRoute>
            <Layout>
              <Chat />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/documentation"
        element={
          <ProtectedRoute>
            <Layout>
              <Documentation />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <Settings />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/connections" replace />} />
    </Routes>
  );
}
