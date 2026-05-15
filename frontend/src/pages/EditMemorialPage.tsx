import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../lib/api";
import MemorialForm, { type FormValues } from "../components/MemorialForm";
import type { Memorial } from "../types";

export default function EditMemorialPage() {
  const { id } = useParams<{ id: string }>();
  const [memorial, setMemorial] = useState<Memorial | null>(null);

  useEffect(() => {
    api.get(`/memorials/${id}`).then((res) => setMemorial(res.data));
  }, [id]);

  const handleSave = async (form: FormValues) => {
    const payload: Record<string, unknown> = {
      name: form.name,
      birth_date: form.birth_date || undefined,
      death_date: form.death_date || undefined,
      biography: form.biography || undefined,
      message: form.message || undefined,
      is_public: form.is_public,
    };
    if (form.password) payload.password = form.password;
    const res = await api.put(`/memorials/${id}`, payload);
    setMemorial(res.data);
    return res.data;
  };

  if (!memorial) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--gray-500)" }}>
        読み込み中...
      </div>
    );
  }

  return (
    <div style={s.page}>
      <header style={s.header}>
        <div style={s.headerInner}>
          <Link to="/dashboard" style={s.back}>← ダッシュボードへ戻る</Link>
          <div>
            <h1 style={s.title}>{memorial.name}</h1>
            <span style={s.subtitle}>墓誌を編集</span>
          </div>
        </div>
      </header>
      <main style={s.main}>
        <MemorialForm initial={memorial} memorialId={memorial.id} onSave={handleSave} />
      </main>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--sand-100)" },
  header: { background: "var(--white)", borderBottom: "1px solid var(--sand-300)", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 760, margin: "0 auto", padding: "0 2rem", height: 64, display: "flex", alignItems: "center", gap: "1.5rem" },
  back: { fontSize: "0.85rem", color: "var(--gray-500)", flexShrink: 0 },
  title: { fontFamily: "var(--font-serif)", fontSize: "1.05rem", fontWeight: 700 },
  subtitle: { fontSize: "0.78rem", color: "var(--gray-500)" },
  main: { maxWidth: 760, margin: "0 auto", padding: "2rem" },
};
