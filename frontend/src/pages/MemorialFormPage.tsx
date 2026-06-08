import { Link } from "react-router-dom";
import api from "../lib/api";
import MemorialForm, { type FormValues } from "../components/MemorialForm";

export default function MemorialFormPage() {
  const handleSave = async (form: FormValues) => {
    const res = await api.post("/memorials", {
      name: form.name,
      birth_date: form.birth_date || undefined,
      death_date: form.death_date || undefined,
      biography: form.biography || undefined,
      message: form.message || undefined,
      is_public: form.is_public,
      password: form.password || undefined,
    });
    return res.data;
  };

  return (
    <div style={s.page}>
      <header style={s.header}>
        <div style={s.headerInner}>
          <Link to="/dashboard" style={s.back}>← ダッシュボードへ戻る</Link>
          <h1 style={s.title}>新規墓誌作成</h1>
        </div>
      </header>
      <main style={s.main}>
        <MemorialForm onSave={handleSave} />
      </main>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--sand-100)" },
  header: { background: "var(--white)", borderBottom: "1px solid var(--sand-300)", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 760, margin: "0 auto", padding: "0 2rem", height: 60, display: "flex", alignItems: "center", gap: "1.5rem" },
  back: { fontSize: "0.85rem", color: "var(--gray-500)" },
  title: { fontFamily: "var(--font-serif)", fontSize: "1.1rem", fontWeight: 700 },
  main: { maxWidth: 760, margin: "0 auto", padding: "2rem" },
};
