import { useState, FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

export default function MemorialFormPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    birth_date: "",
    death_date: "",
    biography: "",
    message: "",
    is_public: true,
    password: "",
  });
  const [error, setError] = useState("");

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const token = localStorage.getItem("token");
      const payload = {
        ...form,
        password: form.password || undefined,
        birth_date: form.birth_date || undefined,
        death_date: form.death_date || undefined,
        biography: form.biography || undefined,
        message: form.message || undefined,
      };
      await axios.post("/memorials", payload, { headers: { Authorization: `Bearer ${token}` } });
      navigate("/dashboard");
    } catch {
      setError("作成に失敗しました");
    }
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <Link to="/dashboard" style={styles.back}>← 戻る</Link>
        <h1 style={styles.title}>新規墓誌作成</h1>
      </header>

      <main style={styles.main}>
        <form onSubmit={handleSubmit} style={styles.form}>
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>故人の情報</h2>
            <label style={styles.label}>お名前 *</label>
            <input style={styles.input} type="text" value={form.name} onChange={set("name")} required placeholder="例：山田 太郎" />
            <div style={styles.row}>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>生年月日</label>
                <input style={styles.input} type="text" value={form.birth_date} onChange={set("birth_date")} placeholder="例：1930年5月3日" />
              </div>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>命日</label>
                <input style={styles.input} type="text" value={form.death_date} onChange={set("death_date")} placeholder="例：2020年10月15日" />
              </div>
            </div>
            <label style={styles.label}>略歴・プロフィール</label>
            <textarea style={styles.textarea} value={form.biography} onChange={set("biography")} rows={5} placeholder="故人の人生・エピソードをご記入ください" />
            <label style={styles.label}>遺族からのメッセージ</label>
            <textarea style={styles.textarea} value={form.message} onChange={set("message")} rows={3} placeholder="故人へのメッセージや、訪れた方へのご挨拶" />
          </section>

          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>公開設定</h2>
            <label style={styles.checkLabel}>
              <input type="checkbox" checked={form.is_public} onChange={(e) => setForm((p) => ({ ...p, is_public: e.target.checked }))} />
              公開する（QRコードでアクセス可能）
            </label>
            {!form.is_public && (
              <>
                <label style={styles.label}>アクセスパスワード</label>
                <input style={styles.input} type="password" value={form.password} onChange={set("password")} placeholder="パスワードを設定してください" />
              </>
            )}
          </section>

          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.submit} type="submit">墓誌を作成する</button>
        </form>
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
  form: { display: "flex", flexDirection: "column", gap: "1.5rem" },
  section: { background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "1.5rem", display: "flex", flexDirection: "column", gap: "0.75rem" },
  sectionTitle: { fontSize: "1rem", fontWeight: 700, marginBottom: "0.25rem" },
  label: { fontSize: "0.85rem", color: "var(--color-text-muted)" },
  input: { padding: "0.6rem 0.75rem", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem", width: "100%" },
  textarea: { padding: "0.6rem 0.75rem", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem", width: "100%", resize: "vertical" },
  row: { display: "flex", gap: "1rem" },
  checkLabel: { display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.9rem" },
  error: { color: "var(--color-error)", fontSize: "0.85rem" },
  submit: { padding: "0.85rem", background: "var(--color-primary)", color: "#fff", border: "none", borderRadius: 4, fontSize: "1rem", fontWeight: 700 },
};
