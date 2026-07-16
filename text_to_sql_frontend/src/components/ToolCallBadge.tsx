import React from "react";
import { Chip } from "@mui/material";
import BuildCircleIcon from "@mui/icons-material/BuildCircle";

export default function ToolCallBadge({ label }: { label: string }) {
  return <Chip size="small" icon={<BuildCircleIcon />} label={label} sx={{ mb: 1 }} />;
}
