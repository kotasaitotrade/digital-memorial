import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // すべてのAPIリクエストは /api プレフィックスで統一
      "/api": "http://localhost:8000",
      // アップロードファイルの静的配信
      "/uploads": "http://localhost:8000",
    },
  },
});
