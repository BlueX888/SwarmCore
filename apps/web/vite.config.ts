import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          "react-vendor": ["react", "react-dom", "react-router"],
          xyflow: ["@xyflow/react"],
          query: ["@tanstack/react-query"],
        },
      },
    },
  },
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", rewrite: (p) => p.replace(/^\/api/, "") },
      "/internal": { target: "http://127.0.0.1:8091" },
    },
  },
  test: { include: ["src/**/*.test.{ts,tsx}"], environment: "jsdom", setupFiles: ["./src/test/setup.ts"] },
});
