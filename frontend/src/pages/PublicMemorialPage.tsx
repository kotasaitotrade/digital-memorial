import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import type { MemorialPublic } from "../types";
import { API_BASE } from "../lib/config";

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
      const res = await axios.get(`${API_BASE}/api/m/${slug}`, { params });
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

  useEffect(() => {
    if (memorial) {
      document.title = `${memorial.name} | Digital Memorial`;
    } else {
      document.title = "Digital Memorial";
    }
    return () => { document.title = "Digital Memorial"; };
  }, [memorial]);

  // キーボードで lightbox を閉じる
  useEffect(() => {
    if (!lightbox) return;
    const fn = (e: KeyboardEvent) => { if (e.key === "Escape") setLightbox(null); };
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [lightbox]);

  if (loading) {
    return (
      <div style={s.center}>
        <div style={s.loadingDot} />
      </div>
    );
  }

  if (notFound) {
    return (
      <div style={s.center}>
        <div style={s.notFound}>
          <p style={s.notFoundIcon}>🕊️</p>
          <h2 style={s.notFoundTitle}>墓誌が見つかりません</h2>
          <p style={s.notFoundDesc}>URLをご確認ください</p>
        </div>
      </div>
    );
  }

  if (needPassword) {
    return (
      <div style={s.center}>
        <div style={s.pwCard}>
          <div style={s.pwIcon}>🔒</div>
          <h2 style={s.pwTitle}>パスワードが必要です</h2>
          <p style={s.pwDesc}>この墓誌はパスワードで保護されています</p>
          <input
            style={{ ...s.pwInput, ...(pwError ? { borderColor: "var(--red)" } : {}) }}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="パスワードを入力"
            onKeyDown={(e) => e.key === "Enter" && fetchMemorial(password)}
            autoFocus
          />
          {pwError && <p style={s.pwErrorMsg}>パスワードが正しくありません</p>}
          <button style={s.pwBtn} onClick={() => fetchMemorial(password)}>アクセスする</button>
        </div>
      </div>
    );
  }

  if (!memorial) return null;

  const images = memorial.media.filter((m) => m.media_type === "image");
  const videos = memorial.media.filter((m) => m.media_type === "video");

  // アルバム名でグルーピング（未設定はデフォルトグループへ）
  const albumGroups: Record<string, typeof images> = {};
  images.forEach((m) => {
    const key = m.album_name || "__default__";
    if (!albumGroups[key]) albumGroups[key] = [];
    albumGroups[key].push(m);
  });
  const albumKeys = Object.keys(albumGroups).sort((a, b) =>
    a === "__default__" ? 1 : b === "__default__" ? -1 : a.localeCompare(b, "ja")
  );

  return (
    <>
      <div style={s.page}>
        {/* ヒーロー */}
        <div style={s.hero}>
          <div style={s.heroOverlay} />
          <div style={s.heroContent}>
            <p style={s.heroEyebrow}>In Loving Memory</p>
            <h1 style={s.heroName}>{memorial.name}</h1>
            {(memorial.birth_date || memorial.death_date) && (
              <p style={s.heroDates}>
                {[memorial.birth_date, memorial.death_date].filter(Boolean).join(" 〜 ")}
              </p>
            )}
          </div>
          <div style={s.heroBottom}>
            <div style={s.heroLine} />
          </div>
        </div>

        <div style={s.container}>

          {/* 略歴 */}
          {memorial.biography && (
            <section style={s.section}>
              <SectionTitle>略歴</SectionTitle>
              <p style={s.bodyText}>{memorial.biography}</p>
            </section>
          )}

          {/* 写真ギャラリー */}
          {images.length > 0 && (
            <section style={s.section}>
              <SectionTitle>思い出</SectionTitle>
              {albumKeys.map((key) => {
                const group = albumGroups[key];
                const isDefault = key === "__default__";
                const hasMultipleAlbums = albumKeys.length > 1 || !isDefault;
                return (
                  <div key={key} style={hasMultipleAlbums && !isDefault ? s.albumGroup : {}}>
                    {!isDefault && <h3 style={s.albumTitle}>{key}</h3>}
                    <div style={{ ...s.gallery, ...(group.length === 1 ? s.gallerySingle : {}) }}>
                      {group.map((m) => (
                        <div
                          key={m.id}
                          style={s.galleryItem}
                          onClick={() => setLightbox(m.file_path)}
                          role="button"
                          tabIndex={0}
                        >
                          <img src={m.file_path} alt={m.caption ?? ""} style={s.galleryImg} loading="lazy" />
                          <div style={s.galleryOverlay}>
                            <span style={s.galleryZoom}>🔍</span>
                          </div>
                          {(m.caption || m.taken_at || m.location || m.episode) && (
                            <div style={s.galleryMeta}>
                              {m.caption && <p style={s.galleryCaption}>{m.caption}</p>}
                              {(m.taken_at || m.location) && (
                                <p style={s.gallerySubMeta}>
                                  {[m.taken_at, m.location].filter(Boolean).join(" · ")}
                                </p>
                              )}
                              {m.episode && <p style={s.galleryEpisode}>{m.episode}</p>}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </section>
          )}

          {/* 動画 */}
          {videos.length > 0 && (
            <section style={s.section}>
              <SectionTitle>動画の思い出</SectionTitle>
              <div style={s.videoGrid}>
                {videos.map((v) => (
                  <div key={v.id} style={s.videoCard}>
                    <video
                      src={v.file_path}
                      controls
                      preload="metadata"
                      style={s.videoEl}
                    />
                    {(v.caption || v.taken_at || v.location) && (
                      <div style={s.galleryMeta}>
                        {v.caption && <p style={s.galleryCaption}>{v.caption}</p>}
                        {(v.taken_at || v.location) && (
                          <p style={s.gallerySubMeta}>
                            {[v.taken_at, v.location].filter(Boolean).join(" · ")}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* メッセージ */}
          {memorial.message && (
            <section style={s.section}>
              <SectionTitle>ご家族より</SectionTitle>
              <blockquote style={s.blockquote}>
                <span style={s.quoteIcon}>"</span>
                <p style={s.quoteText}>{memorial.message}</p>
              </blockquote>
            </section>
          )}
        </div>

        <footer style={s.footer}>
          <div style={s.footerLogo}>Digital Memorial</div>
          <p style={s.footerTagline}>故人の記憶を、永遠に</p>
        </footer>
      </div>

      {/* ライトボックス */}
      {lightbox && (
        <div style={s.lightboxOverlay} onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="" style={s.lightboxImg} />
          <button style={s.lightboxClose} onClick={() => setLightbox(null)} aria-label="閉じる">✕</button>
        </div>
      )}
    </>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 style={{ fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.2em", color: "var(--gray-500)", textTransform: "uppercase" as const, marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: "0.75rem" }}>{children}<span style={{ flex: 1, height: 1, background: "var(--sand-300)" }} /></h2>;
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--sand-100)", fontFamily: "var(--font-serif)" },

  center: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--sand-100)" },
  loadingDot: { width: 12, height: 12, borderRadius: "50%", background: "var(--green-700)", animation: "pulse 1.2s ease-in-out infinite" },

  notFound: { textAlign: "center" },
  notFoundIcon: { fontSize: "3rem", marginBottom: "1rem" },
  notFoundTitle: { fontFamily: "var(--font-serif)", fontSize: "1.3rem", fontWeight: 700, marginBottom: "0.5rem" },
  notFoundDesc: { color: "var(--gray-500)", fontSize: "0.9rem" },

  hero: {
    position: "relative",
    minHeight: "55vh",
    background: "linear-gradient(160deg, var(--green-900) 0%, var(--green-800) 60%, var(--green-700) 100%)",
    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    overflow: "hidden",
  },
  heroOverlay: { position: "absolute", inset: 0, background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.3) 100%)" },
  heroContent: { position: "relative", textAlign: "center", color: "#fff", padding: "3rem 2rem 2rem" },
  heroEyebrow: { fontSize: "0.72rem", letterSpacing: "0.3em", color: "rgba(255,255,255,0.55)", marginBottom: "1.5rem", textTransform: "uppercase" as const },
  heroName: { fontFamily: "var(--font-serif)", fontSize: "clamp(2.5rem,6vw,4rem)", fontWeight: 300, letterSpacing: "0.08em", marginBottom: "1rem", lineHeight: 1.2 },
  heroDates: { fontSize: "1rem", color: "rgba(255,255,255,0.65)", letterSpacing: "0.05em" },
  heroBottom: { position: "relative", width: "100%", display: "flex", justifyContent: "center", paddingBottom: "2rem" },
  heroLine: { width: 48, height: 2, background: "rgba(255,255,255,0.3)" },

  container: { maxWidth: 760, margin: "0 auto", padding: "3.5rem 2rem 2rem" },
  videoGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1.25rem" },
  videoCard: { borderRadius: "var(--radius-md)", overflow: "hidden", background: "var(--white)", boxShadow: "var(--shadow-sm)" },
  videoEl: { width: "100%", display: "block", maxHeight: 260, background: "#000", objectFit: "contain" as const },
  section: { marginBottom: "3.5rem" },

  bodyText: { fontSize: "1rem", lineHeight: 2.1, whiteSpace: "pre-wrap" as const, color: "var(--gray-700)" },
  blockquote: { background: "var(--white)", borderLeft: "3px solid var(--green-700)", borderRadius: "0 var(--radius-md) var(--radius-md) 0", padding: "1.5rem 1.75rem", boxShadow: "var(--shadow-sm)" },
  quoteIcon: { display: "block", fontFamily: "Georgia", fontSize: "3rem", color: "var(--green-400)", lineHeight: 0.8, marginBottom: "0.75rem" },
  quoteText: { fontSize: "1rem", lineHeight: 2.0, color: "var(--gray-700)", whiteSpace: "pre-wrap" as const },

  gallery: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.75rem" },
  gallerySingle: { gridTemplateColumns: "1fr", maxWidth: 480 },
  galleryItem: { position: "relative", overflow: "hidden", borderRadius: "var(--radius-md)", cursor: "pointer", background: "var(--sand-200)" },
  galleryImg: { width: "100%", aspectRatio: "1", objectFit: "cover", display: "block", transition: "transform 0.3s ease" },
  galleryOverlay: { position: "absolute", inset: 0, background: "rgba(0,0,0,0)", display: "flex", alignItems: "center", justifyContent: "center", transition: "background 0.2s ease" },
  galleryZoom: { fontSize: "1.5rem", opacity: 0, transition: "opacity 0.2s" },
  galleryMeta: { position: "absolute", bottom: 0, left: 0, right: 0, padding: "0.4rem 0.5rem 0.5rem", background: "linear-gradient(transparent, rgba(0,0,0,0.65))" },
  galleryCaption: { fontSize: "0.75rem", color: "#fff", textAlign: "center", margin: 0 },
  gallerySubMeta: { fontSize: "0.65rem", color: "rgba(255,255,255,0.75)", textAlign: "center", margin: "0.15rem 0 0" },
  galleryEpisode: { fontSize: "0.68rem", color: "rgba(255,255,255,0.7)", textAlign: "center", margin: "0.15rem 0 0", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as const, overflow: "hidden" },
  albumGroup: { marginBottom: "2rem" },
  albumTitle: { fontSize: "0.85rem", fontWeight: 600, color: "var(--gray-600)", letterSpacing: "0.05em", marginBottom: "0.75rem", borderLeft: "3px solid var(--green-700)", paddingLeft: "0.6rem" },

  footer: { textAlign: "center", padding: "3rem 2rem 4rem", borderTop: "1px solid var(--sand-300)", marginTop: "1rem" },
  footerLogo: { fontFamily: "var(--font-serif)", fontSize: "1rem", fontWeight: 700, color: "var(--green-900)", marginBottom: "0.3rem" },
  footerTagline: { fontSize: "0.78rem", color: "var(--gray-500)", letterSpacing: "0.05em" },

  pwCard: { background: "var(--white)", borderRadius: "var(--radius-lg)", boxShadow: "var(--shadow-lg)", padding: "2.5rem 2rem", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem", maxWidth: 380, width: "90%" },
  pwIcon: { fontSize: "2.5rem" },
  pwTitle: { fontFamily: "var(--font-serif)", fontSize: "1.2rem", fontWeight: 700 },
  pwDesc: { fontSize: "0.85rem", color: "var(--gray-500)" },
  pwInput: { padding: "0.7rem 0.9rem", border: "1.5px solid var(--gray-300)", borderRadius: "var(--radius-sm)", fontSize: "1rem", width: "100%", outline: "none" },
  pwErrorMsg: { fontSize: "0.8rem", color: "var(--red)" },
  pwBtn: { padding: "0.75rem", background: "var(--green-800)", color: "#fff", border: "none", borderRadius: "var(--radius-sm)", fontSize: "1rem", cursor: "pointer", width: "100%", fontWeight: 500 },

  lightboxOverlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.92)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2000, cursor: "pointer" },
  lightboxImg: { maxWidth: "92vw", maxHeight: "92vh", objectFit: "contain", borderRadius: "var(--radius-sm)" },
  lightboxClose: { position: "fixed", top: "1.25rem", right: "1.25rem", background: "rgba(255,255,255,0.15)", border: "none", color: "#fff", width: 36, height: 36, borderRadius: "50%", fontSize: "1rem", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" },
};
