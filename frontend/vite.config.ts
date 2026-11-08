import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "..", "CYBERSRS_");
  const backendPort = Number(env.CYBERSRS_BACKEND_PORT);
  const frontendPort = Number(env.CYBERSRS_FRONTEND_PORT);
  if (!backendPort || !frontendPort)
    throw new Error("Configure ports in the project .env");
  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: frontendPort,
      strictPort: true,
      proxy: { "/api": `http://127.0.0.1:${backendPort}` },
    },
  };
});
