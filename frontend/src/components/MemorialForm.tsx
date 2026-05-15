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
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [savedId, setSavedId] = useState<number | null>(memorialId ?? null);

  const set = (key: keyof FormValues) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const result = await onSave(form);
      setSavedId(result.id);
      if (!memorialId) {
        // 新規作成後、編集ページに移動してメディアをアップロードできるように
        navigate(`/memorials/${result.id}/edit`, { replace: true });
      }
    } catch {
      setError("保存に失敗しました");
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
        setMediaList((prev) => [...prev, res.data]);
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
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      {/* 基本情報 */}
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
        <textarea style={styles.textarea} value={form.biography} onChange={set("biography")} rows={5}
          placeholder="故人の人生・エピソードをご記入ください" />

        <label style={styles.label}>ご家族からのメッセージ</label>
        <textarea style={styles.textarea} value={form.message} onChange={set("message")} rows={3}
          placeholder="故人へのメッセージや、訪れた方へのご挨拶" />
      </section>

      {/* 写真 */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>写真・思い出</h2>

        {!savedId && (
          <p style={styles.hint}>先に基本情報を保存してから写真をアップロードできます。</p>
        )}

        {savedId && (
          <>
            <button type="button" style={styles.uploadBtn} onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              {uploading ? "アップロード中..." : "写真を追加"}
            </button>
            <input ref={fileInputRef} type="file" accept="image/*,video/*" multiple hidden onChange={handleFileChange} />

            {mediaList.length > 0 && (
              <div style={styles.mediaGrid}>
                {mediaList.map((m) => (
                  <div key={m.id} style={styles.mediaItem}>
                    <img src={m.file_path} alt={m.caption ?? ""} style={styles.mediaThumb} />
                    <button type="button" style={styles.mediaDelete} onClick={() => handleDeleteMedia(m.id)}>✕</button>
                    {m.caption && <p style={styles.mediaCaption}>{m.caption}</p>}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </section>

      {/* 公開設定 */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>公開設定</h2>

        <label style={styles.checkLabel}>
          <input type="checkbox" checked={form.is_public}
            onChange={(e) => setForm((p) => ({ ...p, is_public: e.target.checked }))} />
          公開する（QRコードでアクセス可能）
        </label>

        {!form.is_public && (
          <>
            <label style={styles.label}>アクセスパスワード</label>
            <input style={styles.input} type="password" value={form.password} onChange={set("password")}
              placeholder="パスワードを設定してください" />
            <p style={styles.hint}>パスワードを変更しない場合は空欄にしてください</p>
          </>
        )}
      </section>

      {error && <p style={styles.error}>{error}</p>}

      <div style={styles.actions}>
        <button type="button" style={styles.cancelBtn} onClick={() => navigate("/dashboard")}>キャンセル</button>
        <button type="submit" style={styles.submitBtn}>
          {memorialId ? "変更を保存" : "墓誌を作成する"}
        </button>
      </div>
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  form: { display: "flex", flexDirection: "column", gap: "1.5rem" },
  section: { background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "1.5rem", display: "flex", flexDirection: "column", gap: "0.75rem" },
  sectionTitle: { fontSize: "1rem", fontWeight: 700, marginBottom: "0.25rem" },
  label: { fontSize: "0.85rem", color: "var(--color-text-muted)" },
  input: { padding: "0.6rem 0.75rem", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem", width: "100%" },
  textarea: { padding: "0.6rem 0.75rem", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem", width: "100%", resize: "vertical" },
  row: { display: "flex", gap: "1rem" },
  checkLabel: { display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.9rem" },
  hint: { fontSize: "0.8rem", color: "var(--color-text-muted)" },
  error: { color: "var(--color-error)", fontSize: "0.85rem" },
  actions: { display: "flex", gap: "0.75rem", justifyContent: "flex-end" },
  cancelBtn: { padding: "0.75rem 1.5rem", background: "transparent", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem", cursor: "pointer" },
  submitBtn: { padding: "0.75rem 1.5rem", background: "var(--color-primary)", color: "#fff", border: "none", borderRadius: 4, fontSize: "1rem", fontWeight: 700, cursor: "pointer" },
  uploadBtn: { padding: "0.6rem 1.25rem", background: "#f0f0eb", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "0.9rem", cursor: "pointer", alignSelf: "flex-start" },
  mediaGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: "0.75rem", marginTop: "0.5rem" },
  mediaItem: { position: "relative" },
  mediaThumb: { width: "100%", aspectRatio: "1", objectFit: "cover", borderRadius: 4 },
  mediaDelete: { position: "absolute", top: 4, right: 4, background: "rgba(0,0,0,0.6)", color: "#fff", border: "none", borderRadius: "50%", width: 22, height: 22, fontSize: "0.7rem", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" },
  mediaCaption: { fontSize: "0.72rem", color: "var(--color-text-muted)", marginTop: 2, textAlign: "center" },
};
