import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// `process` is available in Vite's Node config context; declared here to avoid
// pulling in @types/node just for cwd().
declare const process: { cwd(): string };

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const port = Number(env.FRONTEND_PORT) || 5173;
  return {
    plugins: [react()],
    server: { port },
    preview: { port },
  };
});
