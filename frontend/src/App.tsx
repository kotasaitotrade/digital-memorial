import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import MemorialFormPage from "./pages/MemorialFormPage";
import EditMemorialPage from "./pages/EditMemorialPage";
import PublicMemorialPage from "./pages/PublicMemorialPage";
import PrintQRPage from "./pages/PrintQRPage";
import ShukatsuPage from "./pages/ShukatsuPage";
import EstatePlanListPage, { FamilyInputPage, AssetInputPage, EstateResultPage } from "./pages/EstatePlanPage";
import EndingNotePage from "./pages/EndingNotePage";
import AccountSettingsPage from "./pages/AccountSettingsPage";
import WillSimulatorPage from "./pages/WillSimulatorPage";
import DigitalKeyPage from "./pages/DigitalKeyPage";
import ReminderSettingsPage from "./pages/ReminderSettingsPage";
import UnlockPage from "./pages/UnlockPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ textAlign: "center", padding: "4rem", color: "#6b6b6b" }}>読み込み中...</div>;
  return user ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Routes>
      {/* 認証 */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* 公開 */}
      <Route path="/m/:slug" element={<PublicMemorialPage />} />
      <Route path="/unlock/:personId" element={<UnlockPage />} />

      {/* 墓誌管理 */}
      <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
      <Route path="/memorials/new" element={<PrivateRoute><MemorialFormPage /></PrivateRoute>} />
      <Route path="/memorials/:id/edit" element={<PrivateRoute><EditMemorialPage /></PrivateRoute>} />
      <Route path="/memorials/:id/print-qr" element={<PrivateRoute><PrintQRPage /></PrivateRoute>} />

      {/* 終活 */}
      <Route path="/shukatsu" element={<PrivateRoute><ShukatsuPage /></PrivateRoute>} />
      <Route path="/estate" element={<PrivateRoute><EstatePlanListPage /></PrivateRoute>} />
      <Route path="/estate/:planId/family" element={<PrivateRoute><FamilyInputPage /></PrivateRoute>} />
      <Route path="/estate/:planId/assets" element={<PrivateRoute><AssetInputPage /></PrivateRoute>} />
      <Route path="/estate/:planId/result" element={<PrivateRoute><EstateResultPage /></PrivateRoute>} />
      <Route path="/estate/:planId/will" element={<PrivateRoute><WillSimulatorPage /></PrivateRoute>} />
      <Route path="/ending-note" element={<PrivateRoute><EndingNotePage /></PrivateRoute>} />

      <Route path="/account" element={<PrivateRoute><AccountSettingsPage /></PrivateRoute>} />
      <Route path="/digital-key" element={<PrivateRoute><DigitalKeyPage /></PrivateRoute>} />
      <Route path="/settings/reminders" element={<PrivateRoute><ReminderSettingsPage /></PrivateRoute>} />

      <Route path="/" element={<Navigate to="/dashboard" />} />
      <Route path="*" element={
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: "1rem", background: "#f5f5f0" }}>
          <p style={{ fontSize: "3rem" }}>🕊️</p>
          <h1 style={{ fontSize: "1.3rem", fontWeight: 700 }}>ページが見つかりません</h1>
          <p style={{ color: "#888", fontSize: "0.9rem" }}>URLをご確認ください</p>
          <a href="/dashboard" style={{ color: "#1a5c38", fontWeight: 600, fontSize: "0.9rem" }}>ダッシュボードへ戻る</a>
        </div>
      } />
    </Routes>
  );
}
