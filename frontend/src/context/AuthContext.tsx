import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import axios from "axios";
import type { User } from "../types";
import { API_BASE } from "../lib/config";
import { applyFontSize } from "../pages/AccountSettingsPage";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    const token = localStorage.getItem("token");
    if (!token) { setLoading(false); return; }
    try {
      const res = await axios.get(`${API_BASE}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
      setUser(res.data);
      applyFontSize(res.data.font_size ?? "medium");
    } catch {
      localStorage.removeItem("token");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUser(); }, []);

  const login = async (email: string, password: string) => {
    const params = new URLSearchParams({ username: email, password });
    const res = await axios.post(`${API_BASE}/api/auth/login`, params);
    localStorage.setItem("token", res.data.access_token);
    const me = await axios.get(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${res.data.access_token}` },
    });
    setUser(me.data);
    applyFontSize(me.data.font_size ?? "medium");
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
