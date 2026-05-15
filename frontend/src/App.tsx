import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import MemorialFormPage from "./pages/MemorialFormPage";
import EditMemorialPage from "./pages/EditMemorialPage";
import PublicMemorialPage from "./pages/PublicMemorialPage";
import PrintQRPage from "./pages/PrintQRPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ textAlign: "center", padding: "4rem", color: "#6b6b6b" }}>読み込み中...</div>;
  return user ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/m/:slug" element={<PublicMemorialPage />} />
      <Route
        path="/dashboard"
        element={<PrivateRoute><DashboardPage /></PrivateRoute>}
      />
      <Route
        path="/memorials/new"
        element={<PrivateRoute><MemorialFormPage /></PrivateRoute>}
      />
      <Route
        path="/memorials/:id/edit"
        element={<PrivateRoute><EditMemorialPage /></PrivateRoute>}
      />
      <Route
        path="/memorials/:id/print-qr"
        element={<PrivateRoute><PrintQRPage /></PrivateRoute>}
      />
      <Route path="/" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
}
