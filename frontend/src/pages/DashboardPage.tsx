import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../hooks/useAuth";
import QRModal from "../components/QRModal";
import type { Memorial } from "../types";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [memorials, setMemorials] = useState<Memorial[]>([]);
  const [qrTarget, setQrTarget] = useState<Memorial | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    axios
      .get("/memorials", { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => setMemorials(res.data));
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm("この墓誌を削除しますか？")) return;
    const token = localStorage.getItem("token");
    await axios.delete(`/memorials/${id}`, { headers: { Authorization: `Bearer ${token}` } });
    setMemorials((prev) => prev.filter((m) => m.id !== id));
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.logo}>Digital Memorial</h1>
        <div style={styles.headerRight}>
          <span style={styles.userName}>{user?.name}</span>
          <button style={styles.logoutBtn} onClick={() => { logout(); navigate("/login"); }}>ログアウト</button>
        </div>
      </header>

      <main style={styles.main}>
        <div style={styles.titleRow}>
          <h2 style={styles.pageTitle}>墓誌一覧</h2>
          <Link to="/memorials/new" style={styles.newBtn}>+ 新規作成</Link>
        </div>

        {memorials.length === 0 ? (
          <div style={styles.empty}>
            <p>まだ墓誌が登録されていません</p>
            <Link to="/memorials/new" style={styles.newBtn}>最初の墓誌を作成する</Link>
          </div>
        ) : (
          <div style={styles.grid}>
            {memorials.map((m) => (
              <div key={m.id} style={styles.card}>
                <div style={styles.cardBody}>
                  <h3 style={styles.cardName}>{m.name}</h3>
                  {m.birth_date && m.death_date && (
                    <p style={styles.cardDates}>{m.birth_date} 〜 {m.death_date}</p>
                  )}
                  {m.biography && <p style={styles.cardBio}>{m.biography.slice(0, 60)}...</p>}
                </div>
                <div style={styles.cardFooter}>
                  <a href={`/m/${m.slug}`} target="_blank" rel="noreferrer" style={styles.viewBtn}>閲覧</a>
                  {m.qr_code_path && (
                    <button style={styles.qrBtn} onClick={() => setQrTarget(m)}>QRコード</button>
                  )}
                  <button style={styles.deleteBtn} onClick={() => handleDelete(m.id)}>削除</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {qrTarget && <QRModal memorial={qrTarget} onClose={() => setQrTarget(null)} />}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--color-bg)" },
  header: { background: "var(--color-surface)", borderBottom: "1px solid var(--color-border)", padding: "1rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" },
  logo: { fontSize: "1.2rem", fontWeight: 700 },
  headerRight: { display: "flex", alignItems: "center", gap: "1rem" },
  userName: { fontSize: "0.9rem", color: "var(--color-text-muted)" },
  logoutBtn: { padding: "0.35rem 0.75rem", background: "transparent", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "0.85rem" },
  main: { maxWidth: 900, margin: "0 auto", padding: "2rem" },
  titleRow: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" },
  pageTitle: { fontSize: "1.3rem", fontWeight: 700 },
  newBtn: { padding: "0.5rem 1rem", background: "var(--color-primary)", color: "#fff", borderRadius: 4, fontSize: "0.9rem" },
  empty: { textAlign: "center", padding: "4rem", color: "var(--color-text-muted)", display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "1rem" },
  card: { background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, overflow: "hidden" },
  cardBody: { padding: "1.25rem" },
  cardName: { fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.35rem" },
  cardDates: { fontSize: "0.85rem", color: "var(--color-text-muted)", marginBottom: "0.5rem" },
  cardBio: { fontSize: "0.85rem", color: "var(--color-text-muted)" },
  cardFooter: { padding: "0.75rem 1.25rem", borderTop: "1px solid var(--color-border)", display: "flex", gap: "0.5rem" },
  viewBtn: { padding: "0.3rem 0.75rem", background: "var(--color-primary)", color: "#fff", borderRadius: 4, fontSize: "0.8rem" },
  qrBtn: { padding: "0.3rem 0.75rem", background: "#6b7280", color: "#fff", borderRadius: 4, fontSize: "0.8rem", border: "none", cursor: "pointer" },
  deleteBtn: { padding: "0.3rem 0.75rem", background: "transparent", border: "1px solid var(--color-error)", color: "var(--color-error)", borderRadius: 4, fontSize: "0.8rem" },
};
