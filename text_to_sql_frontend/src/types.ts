export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  chat_history_retention_days: number;
  max_chat_sessions: number;
}

export const CHAT_HISTORY_RETENTION_MIN_DAYS = 1;
export const CHAT_HISTORY_RETENTION_MAX_DAYS = 60;

export const MAX_CHAT_SESSIONS_MIN = 1;
export const MAX_CHAT_SESSIONS_MAX = 20;

export interface DatabaseConnection {
  id: number;
  alias: string;
  host: string;
  port: number;
  db_name: string;
  username: string;
  sslmode: string;
  is_active: boolean;
  last_checked_at?: string | null;
  last_check_status?: string | null;
  created_at: string;
}

export interface DatabaseMetrics {
  cpu_usage_approx_pct?: number | null;
  cpu_usage_note: string;
  memory_cache_hit_ratio_pct?: number | null;
  memory_usage_note: string;
  disk_io_blocks_read_per_sec?: number | null;
  disk_io_buffers_written_per_sec?: number | null;
  disk_io_note: string;
  disk_usage_bytes?: number | null;
  active_connections?: number | null;
  fetched_at: string;
}

export type LLMProvider = "openai" | "anthropic" | "gemini" | "azure_openai" | "bedrock" | "local" | "groq";

export interface LLMConfig {
  id: number;
  alias: string;
  provider: LLMProvider;
  model_name: string;
  base_url?: string | null;
  region?: string | null;
  api_version?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ChatSession {
  id: number;
  database_connection_id: number;
  llm_config_id: number;
  title?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  intent?: string | null;
  created_at: string;
}

export interface ToolCall {
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output?: string | null;
}

export interface UploadedFile {
  id: string;
  filename: string;
  file_type: string;
  size_kb: number;
  status: "processing" | "ready" | "failed" | string;
  chunk_count: number;
  created_at?: string;
}

export interface Feedback {
  id: number;
  message: string;
  rating?: number | null;
  created_at: string;
}

