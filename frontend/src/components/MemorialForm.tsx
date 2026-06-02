import { useState, FormEvent, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../lib/api";
import type { Memorial } from "../types";

interface Props {
  initial?: Partial<Memorial>;
  memorialId?: number;
  onSave: (data: FormValues) => Promise<Memorial>;
}

export interface FormValues {
  name: string;
  birth_date: string;
  death_date: string;
  biography: string;
  message: string;
  is_public: boolean;
  password: string;
}

export default function MemorialForm({ initial, memorialId, onSave }: Props) {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState<FormValues>({
    name: initial?.name ?? "",
    birth_date: initial?.birth_date ?? "",
    death_date: initial?.death_date ?? "",
    biography: initial?.biography ?? "",
    message: initial?.message ?? "",
    is_public: initial?.is_public ?? true,
    password: "",
  });

  const [mediaList, setMediaList] = useState(initial?.media ?? []);
  const [captions, setCaptions] = useState<Record<number, string>>(
    Object.fromEntries((initial?.media ?? []).map((m) => [m.id, m.caption ?? ""]))
  );
  const [albumMeta, setAlbumMeta] = useState<Record<number, { album_name: string; taken_at: string; location: string; episode: string; media_is_public: boolean; }>>(
    Object.fromEntries((initial?.media ?? []).map((m) => [m.id, { album_name: m.album_name ?? "", taken_at: m.taken_at ?? "", location: m.location ?? "", episode: m.episode ?? "", media_is_public: m.media_is_public !== false }]))
  );
  const [expandedMedia, setExpandedMedia] = useState<Record<number, boolean>>({});
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [savedId, setSavedId] = useState<number | null>(memorialId ?? null);
  const [successMsg, setSuccessMsg] = useState("");

  const set = (key: keyof FormValues) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const result = await onSave(form);
      setSavedId(result.id);
      if (!memorialId) {
        navigate(`/memorials/${result.id}/edit`, { replace: true });
      } else {
        setSuccessMsg("保存しました");
        setTimeout(() => setSuccessMsg(""), 3000);
      }
    } catch {
      setError("保存に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!savedId || !e.target.files?.length) return;
    setUploading(true);
    try {
      for (const file of Array.from(e.target.files)) {
        const fd = new FormData();
        fd.append("file", file);
        const res = await api.post(`/memorials/${savedId}/media`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        const newMedia = res.data;
      setMediaList((prev) => [...prev, newMedia]);
      setCaptions((prev) => ({ ...prev, [newMedia.id]: newMedia.caption ?? "" }));
      setAlbumMeta((prev) => ({ ...prev, [newMedia.id]: { album_name: "", taken_at: "", location: "", episode: "", media_is_public: true } }));
      }
    } catch {
      setError("写真のアップロードに失敗しました");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteMedia = async (mediaId: number) => {
    if (!savedId) return;
    await api.delete(`/memorials/${savedId}/media/${mediaId}`);
    setMediaList((prev) => prev.filter((m) => m.id !== mediaId));
    setCaptions((prev) => { const n = { ...prev }; delete n[mediaId]; return n; });
  };

  const handleMediaMetaBlur = async (mediaId: number) => {
    if (!savedId) return;
    const meta = albumMeta[mediaId] ?? {};
    await api.patch(`/memorials/${savedId}/media/${mediaId}`, {
      caption: captions[mediaId] ?? "",
      album_name: meta.album_name,
      taken_at: meta.taken_at,
      location: meta.location,
      episode: meta.episode,
      media_is_public: meta.media_is_public ?? true,
    });
  };

  return (
    <form onSubmit={handleSubmit} style={s.form}>

      {/* 基本情報 */}
      <Section title="故人の情報" icon="👤">
        <div style={s.field}>
          <label style={s.label}>お名前 <span style={s.required}>*</span></label>
          <input style={s.input} type="text" value={form.name} onChange={set("name")} required placeholder="例：山田 太郎" />
        </div>

        <div style={s.row}>
          <div style={s.field}>
            <label style={s.label}>生年月日</label>
            <input style={s.input} type="text" value={form.birth_date} onChange={set("birth_date")} placeholder="例：1930年5月3日" />
          </div>
          <div style={s.field}>
            <label style={s.label}>命日</label>
            <input style={s.input} type="text" value={form.death_date} onChange={set("death_date")} placeholder="例：2020年10月15日" />
          </div>
        </div>

        <div style={s.field}>
          <label style={s.label}>略歴・プロフィール</label>
          <textarea style={{ ...s.input, ...s.textarea }} value={form.biography} onChange={set("biography")} rows={5} placeholder="故人の人生・エピソードをご記入ください" />
        </div>

        <div style={s.field}>
          <label style={s.label}>ご家族からのメッセージ</label>
          <textarea style={{ ...s.input, ...s.textarea }} value={form.message} onChange={set("message")} rows={3} placeholder="故人へのメッセージや、訪れた方へのご挨拶" />
        </div>
      </Section>

      {/* 写真 */}
      <Section title="写真・思い出" icon="🖼️">
        {!savedId ? (
          <div style={s.uploadHint}>
            <span style={s.uploadHintIcon}>ℹ️</span>
            <span>先に基本情報を保存してから写真をアップロードできます</span>
          </div>
        ) : (
          <>
            <button type="button" style={s.uploadBtn} onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              {uploading ? (
                <><span style={s.spinner}>⟳</span> アップロード中…</>
              ) : (
                <><span>＋</span> 写真を追加</>
              )}
            </button>
            <input ref={fileInputRef} type="file" accept="image/*,video/*" multiple hidden onChange={handleFileChange} />

            {mediaList.length > 0 && (
              <div style={s.mediaGrid}>
                {mediaList.map((m) => (
                  <div key={m.id} style={s.mediaItem}>
                    <img src={m.file_path} alt={m.caption ?? ""} style={s.mediaThumb} />
                    <button
                      type="button"
                      style={s.mediaDeleteBtn}
                      onClick={() => handleDeleteMedia(m.id)}
                      title="削除"
                      aria-label="削除"
                    >✕</button>
                    <button
                      type="button"
                      style={s.mediaEditBtn}
                      onClick={() => setExpandedMedia((prev) => ({ ...prev, [m.id]: !prev[m.id] }))}
                      title="詳細編集"
                    >{expandedMedia[m.id] ? "▲" : "✎"}</button>
                    <input
                      type="text"
                      value={captions[m.id] ?? ""}
                      onChange={(e) => setCaptions((prev) => ({ ...prev, [m.id]: e.target.value }))}
                      onBlur={() => handleMediaMetaBlur(m.id)}
                      placeholder="キャプションを追加"
                      style={s.captionInput}
                    />
                    {expandedMedia[m.id] && (
                      <div style={s.metaExpand}>
                        <input type="text" placeholder="アルバム名（例：家族旅行）" style={s.metaInput}
                          value={albumMeta[m.id]?.album_name ?? ""}
                          onChange={(e) => setAlbumMeta((prev) => ({ ...prev, [m.id]: { ...prev[m.id], album_name: e.target.value } }))}
                          onBlur={() => handleMediaMetaBlur(m.id)} />
                        <input type="text" placeholder="撮影日（例：2010-04-01）" style={s.metaInput}
                          value={albumMeta[m.id]?.taken_at ?? ""}
                          onChange={(e) => setAlbumMeta((prev) => ({ ...prev, [m.id]: { ...prev[m.id], taken_at: e.target.value } }))}
                          onBlur={() => handleMediaMetaBlur(m.id)} />
                        <input type="text" placeholder="撮影場所（例：東京タワー）" style={s.metaInput}
                          value={albumMeta[m.id]?.location ?? ""}
                          onChange={(e) => setAlbumMeta((prev) => ({ ...prev, [m.id]: { ...prev[m.id], location: e.target.value } }))}
                          onBlur={() => handleMediaMetaBlur(m.id)} />
                        <textarea placeholder="エピソード・思い出" style={s.metaTextarea}
                          value={albumMeta[m.id]?.episode ?? ""}
                          onChange={(e) => setAlbumMeta((prev) => ({ ...prev, [m.id]: { ...prev[m.id], episode: e.target.value } }))}
                          onBlur={() => handleMediaMetaBlur(m.id)} rows={2} />
                        <button
                          type="button"
                          style={{ ...s.metaPublicBtn, ...(albumMeta[m.id]?.media_is_public !== false ? s.metaPublicBtnOn : s.metaPublicBtnOff) }}
                          onClick={() => {
                            const next = !(albumMeta[m.id]?.media_is_public !== false);
                            setAlbumMeta((prev) => ({ ...prev, [m.id]: { ...prev[m.id], media_is_public: next } }));
                            api.patch(`/memorials/${savedId}/media/${m.id}`, { media_is_public: next });
                          }}
                        >
                          {albumMeta[m.id]?.media_is_public !== false ? "🌐 公開中" : "🔒 非公開"}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {mediaList.length === 0 && (
              <div style={s.mediaEmpty}>
                写真はまだ登録されていません
              </div>
            )}
          </>
        )}
      </Section>

      {/* 公開設定 */}
      <Section title="公開設定" icon="🔒">
        <label style={s.toggleRow}>
          <div style={{ ...s.toggle, ...(form.is_public ? s.toggleOn : s.toggleOff) }} onClick={() => setForm((p) => ({ ...p, is_public: !p.is_public }))}>
            <div style={{ ...s.toggleThumb, ...(form.is_public ? s.toggleThumbOn : {}) }} />
          </div>
          <span style={s.toggleLabel}>
            {form.is_public ? "公開（QRコードでアクセス可能）" : "非公開（パスワード保護）"}
          </span>
        </label>

        {!form.is_public && (
          <div style={s.field}>
            <label style={s.label}>アクセスパスワード</label>
            <input style={s.input} type="password" value={form.password} onChange={set("password")} placeholder={memorialId ? "変更しない場合は空欄" : "パスワードを設定"} />
          </div>
        )}
      </Section>

      {/* エラー・成功 */}
      {error && <div style={s.errorBox}><span>⚠</span> {error}</div>}
      {successMsg && <div style={s.successBox}><span>✓</span> {successMsg}</div>}

      {/* ボタン */}
      <div style={s.actions}>
        <button type="button" style={s.cancelBtn} onClick={() => navigate("/dashboard")}>
          キャンセル
        </button>
        <button type="submit" style={{ ...s.submitBtn, ...(saving ? s.submitBtnDisabled : {}) }} disabled={saving}>
          {saving ? "保存中..." : memorialId ? "変更を保存" : "墓誌を作成する →"}
        </button>
      </div>
    </form>
  );
}

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div style={sec.wrap}>
      <div style={sec.header}>
        <span style={sec.icon}>{icon}</span>
        <h2 style={sec.title}>{title}</h2>
      </div>
      <div style={sec.body}>{children}</div>
    </div>
  );
}

const sec: Record<string, React.CSSProperties> = {
  wrap: { background: "var(--white)", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-sm)", overflow: "hidden" },
  header: { padding: "1rem 1.5rem", borderBottom: "1px solid var(--sand-200)", display: "flex", alignItems: "center", gap: "0.6rem", background: "var(--sand-100)" },
  icon: { fontSize: "1.1rem" },
  title: { fontSize: "0.9rem", fontWeight: 600, color: "var(--gray-700)", letterSpacing: "0.02em" },
  body: { padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" },
};

const s: Record<string, React.CSSProperties> = {
  form: { display: "flex", flexDirection: "column", gap: "1.25rem" },

  field: { display: "flex", flexDirection: "column", gap: "0.4rem" },
  label: { fontSize: "0.8rem", fontWeight: 500, color: "var(--gray-700)" },
  required: { color: "var(--red)" },
  row: { display: "flex", gap: "1rem" },

  input: { padding: "0.65rem 0.9rem", border: "1.5px solid var(--gray-300)", borderRadius: "var(--radius-sm)", fontSize: "0.95rem", outline: "none", background: "var(--white)", width: "100%" },
  textarea: { resize: "vertical" as const },

  uploadHint: { display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem 1rem", background: "var(--sand-100)", borderRadius: "var(--radius-sm)", fontSize: "0.85rem", color: "var(--gray-500)" },
  uploadHintIcon: { fontSize: "1rem" },
  uploadBtn: { display: "inline-flex", alignItems: "center", gap: "0.4rem", padding: "0.6rem 1.1rem", background: "var(--sand-200)", border: "1.5px dashed var(--gray-300)", borderRadius: "var(--radius-sm)", fontSize: "0.88rem", cursor: "pointer", alignSelf: "flex-start", color: "var(--gray-700)", transition: "background var(--transition)" },
  spinner: { display: "inline-block", animation: "spin 1s linear infinite" },

  mediaGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: "0.75rem" },
  mediaItem: { position: "relative", borderRadius: "var(--radius-sm)", overflow: "hidden" },
  mediaThumb: { width: "100%", aspectRatio: "1", objectFit: "cover", display: "block" },
  mediaDeleteBtn: { position: "absolute", top: 5, right: 5, width: 24, height: 24, background: "rgba(0,0,0,0.55)", color: "#fff", border: "none", borderRadius: "50%", fontSize: "0.65rem", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" },
  mediaEditBtn: { position: "absolute", top: 5, right: 34, width: 24, height: 24, background: "rgba(0,0,0,0.45)", color: "#fff", border: "none", borderRadius: "50%", fontSize: "0.7rem", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" },
  mediaEmpty: { fontSize: "0.85rem", color: "var(--gray-500)", textAlign: "center", padding: "1rem" },
  captionInput: { width: "100%", padding: "0.3rem 0.4rem", fontSize: "0.72rem", border: "1px solid var(--sand-300)", borderRadius: "0 0 var(--radius-sm) var(--radius-sm)", background: "rgba(255,255,255,0.9)", outline: "none", boxSizing: "border-box" as const },
  metaExpand: { padding: "0.4rem", background: "#f8f7f4", borderTop: "1px solid var(--sand-300)", display: "flex", flexDirection: "column" as const, gap: "0.3rem" },
  metaInput: { width: "100%", padding: "0.25rem 0.4rem", fontSize: "0.7rem", border: "1px solid var(--sand-300)", borderRadius: "4px", background: "#fff", outline: "none", boxSizing: "border-box" as const },
  metaTextarea: { width: "100%", padding: "0.25rem 0.4rem", fontSize: "0.7rem", border: "1px solid var(--sand-300)", borderRadius: "4px", background: "#fff", outline: "none", resize: "none" as const, boxSizing: "border-box" as const },
  metaPublicBtn: { width: "100%", padding: "0.25rem 0.4rem", fontSize: "0.7rem", border: "1px solid var(--sand-300)", borderRadius: "4px", cursor: "pointer", fontWeight: 500, transition: "all 0.15s" },
  metaPublicBtnOn: { background: "#f0faf3", color: "var(--green-800)", borderColor: "var(--green-400)" },
  metaPublicBtnOff: { background: "#f3f4f6", color: "var(--gray-600)", borderColor: "var(--gray-300)" },

  toggleRow: { display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer" },
  toggle: { width: 44, height: 24, borderRadius: 12, position: "relative", transition: "background var(--transition)", cursor: "pointer", flexShrink: 0 },
  toggleOn: { background: "var(--green-700)" },
  toggleOff: { background: "var(--gray-300)" },
  toggleThumb: { position: "absolute", top: 3, left: 3, width: 18, height: 18, borderRadius: "50%", background: "#fff", transition: "transform var(--transition)", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" },
  toggleThumbOn: { transform: "translateX(20px)" },
  toggleLabel: { fontSize: "0.9rem", color: "var(--gray-700)", userSelect: "none" },

  errorBox: { background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: "var(--radius-sm)", padding: "0.75rem 1rem", fontSize: "0.85rem", color: "var(--red)", display: "flex", alignItems: "center", gap: "0.5rem" },
  successBox: { background: "#F0FAF3", border: "1px solid var(--green-400)", borderRadius: "var(--radius-sm)", padding: "0.75rem 1rem", fontSize: "0.85rem", color: "var(--green-800)", display: "flex", alignItems: "center", gap: "0.5rem" },

  actions: { display: "flex", gap: "0.75rem", justifyContent: "flex-end", paddingTop: "0.5rem" },
  cancelBtn: { padding: "0.7rem 1.5rem", background: "transparent", border: "1.5px solid var(--gray-300)", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", color: "var(--gray-700)", cursor: "pointer" },
  submitBtn: { padding: "0.7rem 1.75rem", background: "var(--green-800)", color: "#fff", border: "none", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", fontWeight: 600, cursor: "pointer", transition: "background var(--transition)" },
  submitBtnDisabled: { background: "var(--gray-300)", cursor: "not-allowed" },
};
