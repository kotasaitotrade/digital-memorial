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

  if (!memorial) return <div style={{ textAlign: "center", padding: "4rem" }}>読み込み中...</div>;

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <Link to="/dashboard" style={styles.back}>← 戻る</Link>
        <h1 style={styles.title}>{memorial.name} の編集</h1>
      </header>
      <main style={styles.main}>
        <MemorialForm
          initial={memorial}
          memorialId={memorial.id}
          onSave={handleSave}
        />
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--color-bg)" },
  header: { background: "var(--color-surface)", borderBottom: "1px solid var(--color-border)", padding: "1rem 2rem", display: "flex", alignItems: "center", gap: "1rem" },
  back: { color: "var(--color-text-muted)", fontSize: "0.9rem" },
  title: { fontSize: "1.2rem", fontWeight: 700 },
  main: { maxWidth: 680, margin: "0 auto", padding: "2rem" },
};
