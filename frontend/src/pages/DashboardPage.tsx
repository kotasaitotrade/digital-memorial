import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";
import QRModal from "../components/QRModal";
import type { Memorial } from "../types";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [memorials, setMemorials] = useState<Memorial[]>([]);
  const [qrTarget, setQrTarget] = useState<Memorial | null>(null);

  useEffect(() => {
    api.get("/memorials").then((res) => setMemorials(res.data));
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm("この墓誌を削除しますか？")) return;
    await api.delete(`/memorials/${id}`);
    setMemorials((prev) => prev.filter((m) => m.id !== id));
  };

  return (
    <div style={s.page}>
      {/* ヘッダー */}
      <header style={s.header}>
        <div style={s.headerInner}>
          <div style={s.headerLeft}>
            <span style={s.headerLogo}>Digital Memorial</span>
          </div>
          <div style={s.headerRight}>
            <span style={s.headerUser}>{user?.name}</span>
            <button style={s.logoutBtn} onClick={() => { logout(); navigate("/login"); }}>
              ログアウト
            </button>
          </div>
        </div>
      </header>

      <main style={s.main}>
        {/* タイトル行 */}
        <div style={s.titleRow}>
          <div>
            <h1 style={s.pageTitle}>墓誌一覧</h1>
            <p style={s.pageSub}>{memorials.length}件の墓誌が登録されています</p>
          </div>
          <Link to="/memorials/new" style={s.newBtn}>
            <span style={{ fontSize: "1.1rem", lineHeight: 1 }}>＋</span> 新規作成
          </Link>
        </div>

        {memorials.length === 0 ? (
          <div style={s.empty}>
            <div style={s.emptyIcon}>🕊️</div>
            <h2 style={s.emptyTitle}>まだ墓誌が登録されていません</h2>
            <p style={s.emptyDesc}>最初の墓誌を作成して、大切な方の記憶を残しましょう。</p>
            <Link to="/memorials/new" style={s.newBtn}>墓誌を作成する</Link>
          </div>
        ) : (
          <div style={s.grid}>
            {memorials.map((m) => (
              <MemorialCard
                key={m.id}
                memorial={m}
                onQR={() => setQrTarget(m)}
                onDelete={() => handleDelete(m.id)}
              />
            ))}
          </div>
        )}
      </main>

      {qrTarget && <QRModal memorial={qrTarget} onClose={() => setQrTarget(null)} />}
    </div>
  );
}

function MemorialCard({ memorial: m, onQR, onDelete }: { memorial: Memorial; onQR: () => void; onDelete: () => void }) {
  const [hover, setHover] = useState(false);

  return (
    <div
      style={{ ...s.card, ...(hover ? s.cardHover : {}) }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {/* サムネイル */}
      <div style={s.cardThumbWrap}>
        {m.media.length > 0 ? (
          <img src={m.media[0].file_path} alt={m.name} style={s.cardThumb} />
        ) : (
          <div style={s.cardThumbFallback}>
            <span style={s.cardThumbInitial}>{m.name[0]}</span>
          </div>
        )}
        <div style={{ ...s.publicBadge, ...(m.is_public ? s.publicBadgeOpen : s.publicBadgeLocked) }}>
          {m.is_public ? "公開" : "🔒 非公開"}
        </div>
      </div>

      {/* 本文 */}
      <div style={s.cardBody}>
        <h3 style={s.cardName}>{m.name}</h3>
        {m.birth_date && m.death_date && (
          <p style={s.cardDates}>{m.birth_date} 〜 {m.death_date}</p>
        )}
        {m.biography && (
          <p style={s.cardBio}>{m.biography.slice(0, 55)}{m.biography.length > 55 && "…"}</p>
        )}
      </div>

      {/* フッター */}
      <div style={s.cardFooter}>
        <a href={`/m/${m.slug}`} target="_blank" rel="noreferrer" style={s.btnView}>
          閲覧
        </a>
        <Link to={`/memorials/${m.id}/edit`} style={s.btnEdit}>編集</Link>
        {m.qr_code_path && (
          <button style={s.btnQr} onClick={onQR}>QRコード</button>
        )}
        <button style={s.btnDelete} onClick={onDelete}>削除</button>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--sand-100)" },

  header: { background: "var(--white)", borderBottom: "1px solid var(--sand-300)", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 1100, margin: "0 auto", padding: "0 2rem", height: 60, display: "flex", alignItems: "center", justifyContent: "space-between" },
  headerLeft: {},
  headerLogo: { fontFamily: "var(--font-serif)", fontSize: "1.05rem", fontWeight: 700, color: "var(--green-900)", letterSpacing: "0.04em" },
  headerRight: { display: "flex", alignItems: "center", gap: "1rem" },
  headerUser: { fontSize: "0.85rem", color: "var(--gray-500)" },
  logoutBtn: { padding: "0.35rem 0.85rem", background: "transparent", border: "1.5px solid var(--gray-300)", borderRadius: 6, fontSize: "0.82rem", color: "var(--gray-700)", transition: "all var(--transition)" },

  main: { maxWidth: 1100, margin: "0 auto", padding: "2.5rem 2rem" },

  titleRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2rem" },
  pageTitle: { fontFamily: "var(--font-serif)", fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.2rem" },
  pageSub: { fontSize: "0.85rem", color: "var(--gray-500)" },

  newBtn: {
    display: "inline-flex", alignItems: "center", gap: "0.4rem",
    padding: "0.6rem 1.25rem",
    background: "var(--green-800)", color: "var(--white)",
    borderRadius: "var(--radius-sm)", fontSize: "0.9rem", fontWeight: 500,
    transition: "background var(--transition)",
  },

  empty: { textAlign: "center", padding: "5rem 2rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem" },
  emptyIcon: { fontSize: "3rem", marginBottom: "0.5rem" },
  emptyTitle: { fontFamily: "var(--font-serif)", fontSize: "1.2rem", fontWeight: 700 },
  emptyDesc: { fontSize: "0.9rem", color: "var(--gray-500)", marginBottom: "0.5rem" },

  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.25rem" },

  card: {
    background: "var(--white)",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-sm)",
    overflow: "hidden",
    display: "flex", flexDirection: "column",
    transition: "box-shadow var(--transition), transform var(--transition)",
  },
  cardHover: { boxShadow: "var(--shadow-md)", transform: "translateY(-2px)" },

  cardThumbWrap: { position: "relative", height: 180, background: "var(--sand-200)", overflow: "hidden" },
  cardThumb: { width: "100%", height: "100%", objectFit: "cover" },
  cardThumbFallback: { width: "100%", height: "100%", background: "linear-gradient(135deg, var(--green-900), var(--green-700))", display: "flex", alignItems: "center", justifyContent: "center" },
  cardThumbInitial: { fontFamily: "var(--font-serif)", fontSize: "4rem", color: "rgba(255,255,255,0.6)", fontWeight: 300 },

  publicBadge: { position: "absolute", top: 10, right: 10, padding: "0.2rem 0.6rem", borderRadius: 20, fontSize: "0.72rem", fontWeight: 500 },
  publicBadgeOpen: { background: "rgba(45,106,79,0.9)", color: "#fff" },
  publicBadgeLocked: { background: "rgba(0,0,0,0.55)", color: "#fff" },

  cardBody: { padding: "1.1rem 1.25rem", flex: 1 },
  cardName: { fontFamily: "var(--font-serif)", fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.3rem" },
  cardDates: { fontSize: "0.78rem", color: "var(--gray-500)", marginBottom: "0.5rem" },
  cardBio: { fontSize: "0.82rem", color: "var(--gray-500)", lineHeight: 1.6 },

  cardFooter: { padding: "0.75rem 1.25rem", borderTop: "1px solid var(--sand-200)", display: "flex", gap: "0.5rem", flexWrap: "wrap" },

  btnView: { padding: "0.3rem 0.8rem", background: "var(--green-800)", color: "#fff", borderRadius: 6, fontSize: "0.78rem", fontWeight: 500 },
  btnEdit: { padding: "0.3rem 0.8rem", background: "var(--sand-200)", color: "var(--gray-700)", borderRadius: 6, fontSize: "0.78rem" },
  btnQr: { padding: "0.3rem 0.8rem", background: "var(--gray-100)", color: "var(--gray-700)", borderRadius: 6, fontSize: "0.78rem", border: "none", cursor: "pointer" },
  btnDelete: { padding: "0.3rem 0.8rem", background: "transparent", border: "1px solid #FECACA", color: "var(--red)", borderRadius: 6, fontSize: "0.78rem", cursor: "pointer", marginLeft: "auto" },
};
