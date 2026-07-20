import React, { useState } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Paper,
  Rating,
  Stack,
  Link as MuiLink,
  Grid2 as Grid,
  Avatar,
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import MailOutlineIcon from "@mui/icons-material/MailOutline";
import StarIcon from "@mui/icons-material/Star";
import GitHubIcon from "@mui/icons-material/GitHub";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import PhoneIcon from "@mui/icons-material/Phone";
import { apiClient, getErrorMessage } from "../api/client";

const SUPPORT_EMAIL = "mishraamankpa@gmail.com";
const DEVELOPER_GITHUB_USER = "aman-1998";
const DEVELOPER_GITHUB_URL = "https://github.com/aman-1998";
const DEVELOPER_LINKEDIN_URL = "https://www.linkedin.com/in/aman-opentext/";
const DEVELOPER_PHOTO_URL = "/developer-photo.jpg";
const DEVELOPER_PHONE = "9123703426";
const FEEDBACK_MESSAGE_MAX_LENGTH = 4000;

export default function ContactFeedback() {
  const [message, setMessage] = useState("");
  const [rating, setRating] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!message.trim()) {
      setError("Please write a message before sending your feedback.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/feedback", { message: message.trim(), rating });
      setSubmitted(true);
      setMessage("");
      setRating(null);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to send feedback. Please try again."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" mb={3}>
        Contact & Feedback
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper
            variant="outlined"
            sx={{
              p: 3,
              mb: 3,
              borderRadius: 3,
              background: (theme) => alpha(theme.palette.info.main, 0.06),
            }}
          >
            <Stack direction="row" spacing={1.5} alignItems="center">
              <MailOutlineIcon color="primary" />
              <Box>
                <Typography variant="subtitle1" fontWeight={600}>
                  Get in touch
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Have a question, found a bug, or want a new feature? Email us at{" "}
                  <MuiLink href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</MuiLink>, or use the form below to send us
                  feedback directly.
                </Typography>
              </Box>
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ p: 3 }} component="form" onSubmit={handleSubmit}>
            <Typography variant="subtitle1" gutterBottom>
              Share your feedback
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={2}>
              Tell us what's working well and what isn't. A star rating is optional.
            </Typography>

            <Box display="flex" alignItems="center" gap={1.5} mb={2}>
              <Typography variant="body2" color="text.secondary">
                Your rating (optional):
              </Typography>
              <Rating
                value={rating}
                onChange={(_, newValue) => setRating(newValue)}
                emptyIcon={<StarIcon style={{ opacity: 0.3 }} fontSize="inherit" />}
              />
            </Box>

            <TextField
              fullWidth
              multiline
              minRows={4}
              maxRows={10}
              label="Your feedback"
              placeholder="Write your feedback here..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              inputProps={{ maxLength: FEEDBACK_MESSAGE_MAX_LENGTH }}
              helperText={`${message.length}/${FEEDBACK_MESSAGE_MAX_LENGTH}`}
            />

            <Box display="flex" justifyContent="flex-end" mt={2}>
              <Button type="submit" variant="contained" disabled={submitting}>
                {submitting ? "Sending..." : "Send feedback"}
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
            {submitted && !error && (
              <Alert severity="success" sx={{ mt: 2 }}>
                Thanks! Your feedback has been sent.
              </Alert>
            )}
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, height: "100%" }}>
            <Stack direction="column" spacing={1.5} alignItems="center" textAlign="center" mb={2}>
              <Avatar src={DEVELOPER_PHOTO_URL} alt="Aman" sx={{ width: 180, height: 180, fontSize: "3.2rem" }}>
                AM
              </Avatar>
              <Box>
                <Typography variant="subtitle1" fontWeight={600}>
                  Developer Contact
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Aman Mishra
                </Typography>
              </Box>
            </Stack>

            <Typography variant="body2" color="text.secondary" mb={2}>
              This app is built and maintained by an individual developer. Reach out directly for
              bug reports, feature requests, or general questions.
            </Typography>

            <Stack spacing={1.5}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <MailOutlineIcon fontSize="small" color="action" />
                <Typography variant="body2">
                  <MuiLink href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</MuiLink>
                </Typography>
              </Stack>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <PhoneIcon fontSize="small" color="action" />
                <Typography variant="body2">
                  <MuiLink href={`tel:+91${DEVELOPER_PHONE}`}>
                    🇮🇳 +91 {DEVELOPER_PHONE.slice(0, 5)} {DEVELOPER_PHONE.slice(5)}
                  </MuiLink>
                </Typography>
              </Stack>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <GitHubIcon fontSize="small" color="action" />
                <Typography variant="body2">
                  <MuiLink href={DEVELOPER_GITHUB_URL} target="_blank" rel="noopener noreferrer">
                    {DEVELOPER_GITHUB_USER}
                  </MuiLink>
                </Typography>
              </Stack>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <LinkedInIcon fontSize="small" color="action" />
                <Typography variant="body2">
                  <MuiLink href={DEVELOPER_LINKEDIN_URL} target="_blank" rel="noopener noreferrer">
                    linkedin.com/in/aman-opentext
                  </MuiLink>
                </Typography>
              </Stack>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
