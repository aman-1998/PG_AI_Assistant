import React, { useEffect, useRef, useState } from "react";
import { Box, Paper, Typography, Avatar, IconButton, Tooltip } from "@mui/material";
import PersonIcon from "@mui/icons-material/Person";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ToolCallBadge from "./ToolCallBadge";
import type { DisplayMessage } from "../pages/Chat";

interface Props {
  messages: DisplayMessage[];
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard API unavailable/denied - ignore
    }
  };

  return (
    <Box sx={{ my: 1, borderRadius: 1, overflow: "hidden", bgcolor: "grey.900" }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          px: 1.5,
          py: 0.5,
          bgcolor: "grey.800",
        }}
      >
        <Typography
          sx={{ fontSize: "0.7rem", fontFamily: "monospace", color: "grey.400", textTransform: "uppercase", letterSpacing: 0.5 }}
        >
          {language || "text"}
        </Typography>
        <Tooltip title={copied ? "Copied!" : "Copy code"}>
          <IconButton size="small" onClick={handleCopy} aria-label="Copy code" sx={{ color: "grey.400", p: 0.25 }}>
            {copied ? <CheckIcon sx={{ fontSize: 16 }} /> : <ContentCopyIcon sx={{ fontSize: 16 }} />}
          </IconButton>
        </Tooltip>
      </Box>
      <Box
        component="pre"
        sx={{ m: 0, p: 1.5, overflowX: "auto", fontSize: "0.85rem", color: "grey.100", fontFamily: "monospace" }}
      >
        {code}
      </Box>
    </Box>
  );
}

const markdownComponents = {
  table: ({ node, ref, ...props }: any) => (
    <Box sx={{ overflowX: "auto", my: 1 }}>
      <Box
        component="table"
        sx={{
          borderCollapse: "collapse",
          width: "max-content",
          minWidth: "100%",
          fontSize: "0.875rem",
          "& th, & td": {
            border: "1px solid",
            borderColor: "divider",
            p: 0.75,
            textAlign: "left",
            whiteSpace: "nowrap",
          },
          "& th": {
            bgcolor: "action.hover",
            fontWeight: 600,
          },
        }}
        {...props}
      />
    </Box>
  ),
  // react-markdown v9+ no longer passes an `inline` prop to the `code`
  // renderer, so block vs. inline must be inferred: fenced blocks carry a
  // `language-xxx` className (from ```lang) and/or contain a newline, while
  // genuine inline `code` spans (function/column names, etc.) never do.
  code: ({ node, ref, className, children, ...props }: any) => {
    const codeText = String(children).replace(/\n$/, "");
    const isBlock = /language-/.test(className || "") || codeText.includes("\n");
    if (isBlock) {
      const language = /language-(\w+)/.exec(className || "")?.[1] ?? "";
      return <CodeBlock language={language} code={codeText} />;
    }
    return (
      <Box
        component="code"
        sx={{ bgcolor: "action.hover", px: 0.5, py: 0.15, borderRadius: 0.5, fontFamily: "monospace", fontSize: "0.85em" }}
        {...props}
      >
        {children}
      </Box>
    );
  },
  // CodeBlock already renders its own <pre>; avoid double-wrapping in a
  // default, unstyled <pre> tag from react-markdown.
  pre: ({ children }: any) => <>{children}</>,
  // Tool-generated images (e.g. the ER diagram tool's download_url) render as
  // ![alt](url) markdown - bound their width to the bubble and open full size
  // in a new tab on click, since raw <img> would otherwise overflow.
  img: ({ node, ref, ...props }: any) => (
    <Box
      component="img"
      onClick={() => window.open(props.src, "_blank", "noopener,noreferrer")}
      sx={{ maxWidth: "100%", height: "auto", borderRadius: 1, my: 1, cursor: "pointer", display: "block" }}
      {...props}
    />
  ),
  p: ({ node, ref, ...props }: any) => <Typography variant="body1" component="p" sx={{ m: 0, mb: 1 }} {...props} />,
  ul: ({ node, ref, ...props }: any) => <Box component="ul" sx={{ m: 0, mb: 1, pl: 3 }} {...props} />,
  ol: ({ node, ref, ...props }: any) => <Box component="ol" sx={{ m: 0, mb: 1, pl: 3 }} {...props} />,
};

export default function ChatWindow({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Box sx={{ flexGrow: 1, overflowY: "auto", p: 2 }}>
      {messages.map((msg, idx) => (
        <Box key={idx} display="flex" gap={1} mb={2} flexDirection={msg.role === "user" ? "row-reverse" : "row"}>
          <Avatar sx={{ bgcolor: msg.role === "user" ? "primary.main" : "secondary.main" }}>
            {msg.role === "user" ? <PersonIcon /> : <SmartToyIcon />}
          </Avatar>
          <Paper
            variant="outlined"
            sx={{
              p: 1.5,
              maxWidth: msg.role === "user" ? "75%" : "92%",
              minWidth: 0,
              bgcolor: msg.role === "user" ? "primary.50" : "background.paper",
            }}
          >
            {msg.toolStatuses?.map((label, i) => (
              <ToolCallBadge key={i} label={label} />
            ))}
            {msg.role === "user" ? (
              <Typography variant="body1" component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", m: 0 }}>
                {msg.content}
              </Typography>
            ) : msg.content ? (
              <Box sx={{ "& > *:last-child": { mb: 0 } }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {msg.content}
                </ReactMarkdown>
              </Box>
            ) : (
              <Typography variant="body1" sx={{ m: 0 }}>
                {msg.streaming ? "..." : ""}
              </Typography>
            )}
          </Paper>
        </Box>
      ))}
      <div ref={bottomRef} />
    </Box>
  );
}
