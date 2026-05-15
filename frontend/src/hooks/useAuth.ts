import { useState, useEffect } from "react";
import axios from "axios";
import type { User } from "../types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    axios
      .get("/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const params = new URLSearchParams({ username: email, password });
    const res = await axios.post("/auth/login", params);
    localStorage.setItem("token", res.data.access_token);
    const me = await axios.get("/auth/me", {
      headers: { Authorization: `Bearer ${res.data.access_token}` },
    });
    setUser(me.data);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return { user, loading, login, logout };
}
