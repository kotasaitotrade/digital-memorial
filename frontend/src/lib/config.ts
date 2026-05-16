// 開発環境: "" (Viteプロキシ経由 /api/...)
// 本番環境: VITE_API_BASE_URL = "https://digital-memorial-api.onrender.com"
export const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) ?? "";
