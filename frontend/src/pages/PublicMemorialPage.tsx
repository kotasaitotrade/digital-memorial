import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import type { MemorialPublic } from "../types";

export default function PublicMemorialPage() {
  const { slug } = useParams<{ slug: string }>();
  const [memorial, setMemorial] = useState<MemorialPublic | null>(null);
  const [password, setPassword] = useState("");
  const [needPassword, setNeedPassword] = useState(false);
  const [pwError, setPwError] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lightbox, setLightbox] = useState<string | null>(null);

  const fetchMemorial = async (pw?: string) => {
    setLoading(true);
    setPwError(false);
    try {
      const params = pw ? { password: pw } : {};
      const res = await axios.get(`/m/${slug}`, { params });
      setMemorial(res.data);
      setNeedPassword(false);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setNeedPassword(true);
        if (pw) setPwError(true);
      } else {
        setNotFound(true);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMemorial(); }, [slug]);

  if (loading) return <div style={styles.center}><span style={styles.loadingText}>読み込み中...</span></div>;
  if (notFound) return <div style={styles.center}><p>墓誌が見つかりません</p></div>;

  if (needPassword) {
    return (
      <div style={styles.center}>
        <div style={styles.pwCard}>
          <div style={styles.pwIcon}>🔒</div>
          <h2 style={styles.pwTitle}>パスワードが必要です</h2>
          <p style={styles.pwDesc}>この墓誌はパスワードで保護されています</p>
          <input
            style={{ ...styles.pwInput, ...(pwError ? styles.pwInputError : {}) }}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="パスワードを入力"
            onKeyDown={(e) => e.key === "Enter" && fetchMemorial(password)}
          />
          {pwError && <p style={styles.pwErrorMsg}>パスワードが正しくありません</p>}
          <button style={styles.pwBtn} onClick={() => fetchMemorial(password)}>アクセスする</button>
        </div>
      </div>
    );
  }

  if (!memorial) return null;

  const images = memorial.media.filter((m) => m.media_type === "image");

  return (
    <>
      <div style={styles.page}>
        {/* ヒーロー */}
        <div style={styles.hero}>
          <div style={styles.heroInner}>
            <p style={styles.heroLabel}>In Loving Memory</p>
            <h1 style={styles.heroName}>{memorial.name}</h1>
            {(memorial.birth_date || memorial.death_date) && (
              <p style={styles.heroDates}>
                {[memorial.birth_date, memorial.death_date].filter(Boolean).join(" 〜 ")}
              </p>
            )}
            <div style={styles.heroDivider} />
          </div>
        </div>

        <div style={styles.container}>
          {/* 略歴 */}
          {memorial.biography && (
            <section style={styles.section}>
              <h2 style={styles.sectionTitle}>略歴</h2>
              <p style={styles.bodyText}>{memorial.biography}</p>
            </section>
          )}

          {/* 写真ギャラリー */}
          {images.length > 0 && (
            <section style={styles.section}>
              <h2 style={styles.sectionTitle}>思い出</h2>
              <div style={styles.gallery}>
                {images.map((m) => (
                  <div key={m.id} style={styles.galleryItem} onClick={() => setLightbox(m.file_path)}>
                    <img src={m.file_path} alt={m.caption ?? ""} style={styles.galleryImg} />
                    {m.caption && <p style={styles.galleryCaption}>{m.caption}</p>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* メッセージ */}
          {memorial.message && (
            <section style={styles.section}>
              <h2 style={styles.sectionTitle}>ご家族より</h2>
              <blockquote style={styles.blockquote}>{memorial.message}</blockquote>
            </section>
          )}
        </div>

        <footer style={styles.footer}>
          <p style={styles.footerText}>Digital Memorial</p>
          <p style={styles.footerSub}>故人の記憶を、永遠に</p>
        </footer>
      </div>

      {/* ライトボックス */}
      {lightbox && (
        <div style={styles.lightboxOverlay} onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="" style={styles.lightboxImg} />
        </div>
      )}
    </>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--color-bg)", fontFamily: "'Hiragino Mincho ProN', 'Yu Mincho', Georgia, serif" },
  center: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" },
  loadingText: { color: "var(--color-text-muted)" },

  hero: { background: "linear-gradient(160deg, #2c3e2d 0%, #4a6741 100%)", color: "#fff", padding: "5rem 2rem 4rem" },
  heroInner: { maxWidth: 680, margin: "0 auto", textAlign: "center" },
  heroLabel: { fontSize: "0.78rem", letterSpacing: "0.25em", color: "rgba(255,255,255,0.65)", marginBottom: "1.25rem", textTransform: "uppercase" as const },
  heroName: { fontSize: "clamp(2rem, 5vw, 3rem)", fontWeight: 700, marginBottom: "0.75rem", letterSpacing: "0.06em" },
  heroDates: { fontSize: "1rem", color: "rgba(255,255,255,0.75)", marginBottom: "2rem" },
  heroDivider: { width: 48, height: 2, background: "rgba(255,255,255,0.4)", margin: "0 auto" },

  container: { maxWidth: 720, margin: "0 auto", padding: "3rem 2rem" },
  section: { marginBottom: "3rem" },
  sectionTitle: { fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.18em", color: "var(--color-text-muted)", textTransform: "uppercase" as const, marginBottom: "1.25rem", paddingBottom: "0.5rem", borderBottom: "1px solid var(--color-border)" },
  bodyText: { fontSize: "1rem", lineHeight: 2.0, whiteSpace: "pre-wrap" as const, color: "var(--color-text)" },
  blockquote: { borderLeft: "3px solid var(--color-primary)", paddingLeft: "1.25rem", fontSize: "1rem", lineHeight: 2.0, color: "var(--color-text)", fontStyle: "italic", whiteSpace: "pre-wrap" as const },

  gallery: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "0.75rem" },
  galleryItem: { cursor: "pointer", overflow: "hidden", borderRadius: 6 },
  galleryImg: { width: "100%", aspectRatio: "1", objectFit: "cover", display: "block", transition: "transform 0.2s", borderRadius: 6 },
  galleryCaption: { fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "0.3rem", textAlign: "center" },

  footer: { textAlign: "center", padding: "3rem 2rem", borderTop: "1px solid var(--color-border)" },
  footerText: { fontSize: "0.9rem", fontWeight: 700, color: "var(--color-text-muted)" },
  footerSub: { fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "0.25rem" },

  pwCard: { background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 12, padding: "2.5rem 2rem", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem", maxWidth: 360, width: "90%" },
  pwIcon: { fontSize: "2rem" },
  pwTitle: { fontSize: "1.2rem", fontWeight: 700 },
  pwDesc: { fontSize: "0.85rem", color: "var(--color-text-muted)" },
  pwInput: { padding: "0.65rem 0.75rem", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem", width: "100%" },
  pwInputError: { borderColor: "var(--color-error)" },
  pwErrorMsg: { fontSize: "0.8rem", color: "var(--color-error)" },
  pwBtn: { padding: "0.7rem 2rem", background: "var(--color-primary)", color: "#fff", border: "none", borderRadius: 6, fontSize: "1rem", cursor: "pointer", width: "100%" },

  lightboxOverlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.9)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2000, cursor: "pointer" },
  lightboxImg: { maxWidth: "90vw", maxHeight: "90vh", objectFit: "contain", borderRadius: 4 },
};
