import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/auth": "http://localhost:8000",
      "/memorials": "http://localhost:8000",
      "/m": "http://localhost:8000",
      "/uploads": "http://localhost:8000",
    },
  },
});
