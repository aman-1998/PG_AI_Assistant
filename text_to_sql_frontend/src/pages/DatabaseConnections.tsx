import React, { useEffect, useState } from "react";
import { Box, Typography, Button, Grid2 as Grid, CircularProgress } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { apiClient } from "../api/client";
import DatabaseCard from "../components/DatabaseCard";
import DatabaseConnectionForm from "../components/DatabaseConnectionForm";
import type { DatabaseConnection } from "../types";

export default function DatabaseConnections() {
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);

  const loadConnections = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<DatabaseConnection[]>("/database-connections");
      setConnections(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConnections();
  }, []);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Your PostgreSQL Databases</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setFormOpen(true)}>
          Import Database
        </Button>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : connections.length === 0 ? (
        <Typography color="text.secondary">
          No databases imported yet. Click "Import Database" to connect your first PostgreSQL database.
        </Typography>
      ) : (
        <Grid container spacing={2}>
          {connections.map((conn) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={conn.id}>
              <DatabaseCard connection={conn} onDeleted={loadConnections} />
            </Grid>
          ))}
        </Grid>
      )}

      <DatabaseConnectionForm open={formOpen} onClose={() => setFormOpen(false)} onCreated={loadConnections} />
    </Box>
  );
}
