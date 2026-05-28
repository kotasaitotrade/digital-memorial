import { useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";

export default function AccountSettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPwConfirm, setNewPwConfirm] = useState("");
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [pwSaving, setPwSaving] = useState(false);

  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await api.get("/auth/export", { responseType: "json" });
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "digital-memorial-export.json"; a.click();
      URL.revokeObjectURL(url);
    } catch {
      /* ignore */
    } finally {
      setExporting(false);
    }
  };

  const [deletePw, setDeletePw] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteMsg, setDeleteMsg] = useState("");
  const [deleting, setDeleting] = useState(false);

  const handlePasswordChange = async (e: FormEvent) => {
    e.preventDefault();
    if (newPw !== newPwConfirm) { setPwMsg({ ok: false, text: "新しいパスワードが一致しません" }); return; }
    if (newPw.length < 8) { setPwMsg({ ok: false, text: "パスワードは8文字以上にしてください" }); return; }
    setPwSaving(true);
    setPwMsg(null);
    try {
      await api.patch("/auth/password", { current_password: currentPw, new_password: newPw });
      setPwMsg({ ok: true, text: "パスワードを変更しました" });
      setCurrentPw(""); setNewPw(""); setNewPwConfirm("");
    } catch (err: any) {
      setPwMsg({ ok: false, text: err?.response?.data?.detail ?? "変更に失敗しました" });
    } finally {
      setPwSaving(false);
    }
  };

  const handleDeleteAccount = async (e: FormEvent) => {
    e.preventDefault();
    setDeleting(true);
    setDeleteMsg("");
    try {
      await api.delete("/auth/me", { data: { password: deletePw } });
      logout();
      navigate("/login");
    } catch (err: any) {
      setDeleteMsg(err?.response?.data?.detail ?? "削除に失敗しました");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div style={s.page}>
      <header style={s.header}>
        <div style={s.headerInner}>
          <Link to="/dashboard" style={s.back}>← ダッシュボードへ戻る</Link>
          <h1 style={s.title}>アカウント設定</h1>
        </div>
      </header>

      <main style={s.main}>
        {/* Profile info */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>プロフィール</h2>
          <div style={s.infoRow}><span style={s.infoLabel}>名前</span><span>{user?.name}</span></div>
          <div style={s.infoRow}><span style={s.infoLabel}>メールアドレス</span><span>{user?.email}</span></div>
        </div>

        {/* Password change */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>パスワード変更</h2>
          <form onSubmit={handlePasswordChange} style={s.form}>
            <div style={s.field}>
              <label style={s.label}>現在のパスワード</label>
              <input style={s.input} type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} required autoComplete="current-password" />
            </div>
            <div style={s.field}>
              <label style={s.label}>新しいパスワード（8文字以上）</label>
              <input style={s.input} type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} required autoComplete="new-password" />
            </div>
            <div style={s.field}>
              <label style={s.label}>新しいパスワード（確認）</label>
              <input style={s.input} type="password" value={newPwConfirm} onChange={(e) => setNewPwConfirm(e.target.value)} required autoComplete="new-password" />
            </div>
            {pwMsg && <div style={pwMsg.ok ? s.successBox : s.errorBox}>{pwMsg.text}</div>}
            <div style={s.actions}>
              <button type="submit" style={{ ...s.btn, ...(pwSaving ? s.btnDisabled : {}) }} disabled={pwSaving}>
                {pwSaving ? "変更中..." : "パスワードを変更する"}
              </button>
            </div>
          </form>
        </div>

        {/* Data export */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>データエクスポート</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--gray-600)", marginBottom: "1rem", lineHeight: 1.6 }}>
            墓誌・エンディングノート・相続計画など、すべてのデータをJSONファイルとしてダウンロードできます。
          </p>
          <button type="button" style={{ ...s.btn, background: "#2563eb" }} onClick={handleExport} disabled={exporting}>
            {exporting ? "エクスポート中..." : "JSONでダウンロード"}
          </button>
        </div>

        {/* Account delete */}
        <div style={{ ...s.card, ...s.dangerCard }}>
          <h2 style={{ ...s.cardTitle, color: "#dc2626" }}>アカウント削除</h2>
          <p style={s.dangerText}>アカウントを削除すると、すべてのデータ（墓誌・エンディングノート・相続計画）が完全に削除されます。この操作は取り消せません。</p>

          {!deleteConfirm ? (
            <button type="button" style={s.dangerBtn} onClick={() => setDeleteConfirm(true)}>
              アカウントを削除する
            </button>
          ) : (
            <form onSubmit={handleDeleteAccount} style={s.form}>
              <div style={s.field}>
                <label style={s.label}>パスワードを入力して確認</label>
                <input style={s.input} type="password" value={deletePw} onChange={(e) => setDeletePw(e.target.value)} required placeholder="現在のパスワード" />
              </div>
              {deleteMsg && <div style={s.errorBox}>{deleteMsg}</div>}
              <div style={s.actions}>
                <button type="button" style={s.cancelBtn} onClick={() => { setDeleteConfirm(false); setDeletePw(""); setDeleteMsg(""); }}>
                  キャンセル
                </button>
                <button type="submit" style={{ ...s.dangerBtn, ...(deleting ? s.btnDisabled : {}) }} disabled={deleting}>
                  {deleting ? "削除中..." : "完全に削除する"}
                </button>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--sand-100)" },
  header: { background: "var(--white)", borderBottom: "1px solid var(--sand-300)", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 640, margin: "0 auto", padding: "0 2rem", height: 64, display: "flex", alignItems: "center", gap: "1.5rem" },
  back: { fontSize: "0.85rem", color: "var(--gray-500)", textDecoration: "none", flexShrink: 0 },
  title: { fontFamily: "var(--font-serif)", fontSize: "1.05rem", fontWeight: 700 },
  main: { maxWidth: 640, margin: "0 auto", padding: "2rem", display: "flex", flexDirection: "column", gap: "1.25rem" },
  card: { background: "var(--white)", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-sm)", padding: "1.5rem" },
  dangerCard: { border: "1.5px solid #fecaca" },
  cardTitle: { fontSize: "0.95rem", fontWeight: 700, marginBottom: "1rem", color: "var(--gray-800)" },
  infoRow: { display: "flex", gap: "1rem", padding: "0.5rem 0", borderBottom: "1px solid var(--sand-200)", fontSize: "0.9rem" },
  infoLabel: { color: "var(--gray-500)", width: 140, flexShrink: 0 },
  form: { display: "flex", flexDirection: "column", gap: "0.9rem" },
  field: { display: "flex", flexDirection: "column", gap: "0.35rem" },
  label: { fontSize: "0.8rem", fontWeight: 500, color: "var(--gray-700)" },
  input: { padding: "0.65rem 0.9rem", border: "1.5px solid var(--gray-300)", borderRadius: "var(--radius-sm)", fontSize: "0.95rem", outline: "none", background: "var(--white)" },
  actions: { display: "flex", gap: "0.75rem", justifyContent: "flex-end" },
  btn: { padding: "0.65rem 1.5rem", background: "var(--green-800)", color: "#fff", border: "none", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", fontWeight: 600, cursor: "pointer" },
  btnDisabled: { background: "var(--gray-300)", cursor: "not-allowed" },
  cancelBtn: { padding: "0.65rem 1.25rem", background: "transparent", border: "1.5px solid var(--gray-300)", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", color: "var(--gray-700)", cursor: "pointer" },
  dangerBtn: { padding: "0.65rem 1.5rem", background: "#dc2626", color: "#fff", border: "none", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", fontWeight: 600, cursor: "pointer" },
  dangerText: { fontSize: "0.85rem", color: "var(--gray-600)", marginBottom: "1rem", lineHeight: 1.6 },
  successBox: { background: "#F0FAF3", border: "1px solid var(--green-400)", borderRadius: "var(--radius-sm)", padding: "0.65rem 1rem", fontSize: "0.85rem", color: "var(--green-800)" },
  errorBox: { background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: "var(--radius-sm)", padding: "0.65rem 1rem", fontSize: "0.85rem", color: "#dc2626" },
};
