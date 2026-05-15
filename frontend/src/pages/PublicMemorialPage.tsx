import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import type { MemorialPublic } from "../types";

export default function PublicMemorialPage() {
  const { slug } = useParams<{ slug: string }>();
  const [memorial, setMemorial] = useState<MemorialPublic | null>(null);
  const [password, setPassword] = useState("");
  const [needPassword, setNeedPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchMemorial = async (pw?: string) => {
    setLoading(true);
    try {
      const params = pw ? { password: pw } : {};
      const res = await axios.get(`/m/${slug}`, { params });
      setMemorial(res.data);
      setNeedPassword(false);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setNeedPassword(true);
      } else {
        setError("墓誌が見つかりません");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMemorial(); }, [slug]);

  if (loading) return <div style={styles.center}>読み込み中...</div>;
  if (error) return <div style={styles.center}>{error}</div>;

  if (needPassword) {
    return (
      <div style={styles.center}>
        <div style={styles.pwCard}>
          <p style={{ marginBottom: "1rem" }}>この墓誌はパスワードで保護されています</p>
          <input style={styles.input} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="パスワード" />
          <button style={styles.btn} onClick={() => fetchMemorial(password)}>アクセス</button>
        </div>
      </div>
    );
  }

  if (!memorial) return null;

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.hero}>
          <h1 style={styles.name}>{memorial.name}</h1>
          {(memorial.birth_date || memorial.death_date) && (
            <p style={styles.dates}>
              {memorial.birth_date && <span>{memorial.birth_date}</span>}
              {memorial.birth_date && memorial.death_date && <span> 〜 </span>}
              {memorial.death_date && <span>{memorial.death_date}</span>}
            </p>
          )}
          <div style={styles.divider} />
        </div>

        {memorial.biography && (
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>略歴</h2>
            <p style={styles.body}>{memorial.biography}</p>
          </section>
        )}

        {memorial.media.length > 0 && (
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>思い出</h2>
            <div style={styles.mediaGrid}>
              {memorial.media.map((m) => (
                <div key={m.id}>
                  {m.media_type === "image" && (
                    <img src={`/uploads/${m.file_path}`} alt={m.caption || ""} style={styles.mediaImg} />
                  )}
                  {m.caption && <p style={styles.caption}>{m.caption}</p>}
                </div>
              ))}
            </div>
          </section>
        )}

        {memorial.message && (
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>ご家族より</h2>
            <p style={styles.body}>{memorial.message}</p>
          </section>
        )}

        <footer style={styles.footer}>
          <p>Digital Memorial</p>
        </footer>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--color-bg)" },
  container: { maxWidth: 720, margin: "0 auto", padding: "3rem 2rem" },
  hero: { textAlign: "center", marginBottom: "3rem" },
  name: { fontSize: "2.2rem", fontWeight: 700, marginBottom: "0.5rem", letterSpacing: "0.05em" },
  dates: { color: "var(--color-text-muted)", marginBottom: "1.5rem" },
  divider: { width: 60, height: 2, background: "var(--color-primary)", margin: "0 auto" },
  section: { marginBottom: "2.5rem" },
  sectionTitle: { fontSize: "1rem", fontWeight: 700, color: "var(--color-text-muted)", letterSpacing: "0.1em", marginBottom: "1rem", textTransform: "uppercase" as const },
  body: { fontSize: "1rem", lineHeight: 2, whiteSpace: "pre-wrap" as const },
  mediaGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem" },
  mediaImg: { width: "100%", borderRadius: 4, objectFit: "cover" as const },
  caption: { fontSize: "0.8rem", color: "var(--color-text-muted)", marginTop: "0.35rem", textAlign: "center" },
  footer: { textAlign: "center", color: "var(--color-text-muted)", fontSize: "0.8rem", marginTop: "4rem", paddingTop: "2rem", borderTop: "1px solid var(--color-border)" },
  center: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" },
  pwCard: { background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "2rem", textAlign: "center", display: "flex", flexDirection: "column", gap: "1rem" },
  input: { padding: "0.6rem 0.75rem", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem" },
  btn: { padding: "0.6rem 1.5rem", background: "var(--color-primary)", color: "#fff", border: "none", borderRadius: 4, fontSize: "1rem" },
};
