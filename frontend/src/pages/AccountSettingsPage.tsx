import { useState, useEffect, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";

interface ActivityLogEntry {
  id: number;
  action: string;
  detail: string | null;
  created_at: string | null;
}

// フォントサイズ設定をCSSへ反映するユーティリティ
export function applyFontSize(size: string) {
  const map: Record<string, string> = {
    small: "14px", medium: "16px", large: "19px", xlarge: "22px",
  };
  document.documentElement.style.setProperty("--base-font-size", map[size] ?? "16px");
}

export default function AccountSettingsPage() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();

  // ─── パスワード変更 ───
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPwConfirm, setNewPwConfirm] = useState("");
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [pwSaving, setPwSaving] = useState(false);

  // ─── フォントサイズ / かんたんモード ───
  const [fontSize, setFontSize] = useState(user?.font_size ?? "medium");
  const [simpleMode, setSimpleMode] = useState(user?.simple_mode ?? false);
  const [prefSaving, setPrefSaving] = useState(false);
  const [prefMsg, setPrefMsg] = useState<{ ok: boolean; text: string } | null>(null);

  // ─── 活動ログ ───
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [logLoading, setLogLoading] = useState(false);
  const [showLog, setShowLog] = useState(false);

  // ─── 2FA ───
  const [totpSetupData, setTotpSetupData] = useState<{ totp_secret: string; qr_data_url: string } | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [totpMsg, setTotpMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [totpDisablePw, setTotpDisablePw] = useState("");
  const [totpDisableCode, setTotpDisableCode] = useState("");
  const [showTotpSetup, setShowTotpSetup] = useState(false);

  // ─── エクスポート ───
  const [exporting, setExporting] = useState(false);
  const [exportCsv, setExportCsv] = useState(false);

  // ─── 退会 ───
  const [deletePw, setDeletePw] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteMsg, setDeleteMsg] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (user) {
      setFontSize(user.font_size ?? "medium");
      setSimpleMode(user.simple_mode ?? false);
      applyFontSize(user.font_size ?? "medium");
    }
  }, [user]);

  // フォントサイズ変更時に即時プレビュー
  useEffect(() => {
    applyFontSize(fontSize);
  }, [fontSize]);

  // ─── パスワード変更 ───
  const handlePasswordChange = async (e: FormEvent) => {
    e.preventDefault();
    if (newPw !== newPwConfirm) { setPwMsg({ ok: false, text: "新しいパスワードが一致しません" }); return; }
    if (newPw.length < 8) { setPwMsg({ ok: false, text: "パスワードは8文字以上にしてください" }); return; }
    setPwSaving(true); setPwMsg(null);
    try {
      await api.patch("/auth/password", { current_password: currentPw, new_password: newPw });
      setPwMsg({ ok: true, text: "パスワードを変更しました" });
      setCurrentPw(""); setNewPw(""); setNewPwConfirm("");
    } catch (err: any) {
      setPwMsg({ ok: false, text: err?.response?.data?.detail ?? "変更に失敗しました" });
    } finally { setPwSaving(false); }
  };

  // ─── 設定保存 ───
  const handleSavePreferences = async () => {
    setPrefSaving(true); setPrefMsg(null);
    try {
      await api.patch("/auth/preferences", { font_size: fontSize, simple_mode: simpleMode });
      applyFontSize(fontSize);
      if (refreshUser) await refreshUser();
      setPrefMsg({ ok: true, text: "設定を保存しました" });
    } catch {
      setPrefMsg({ ok: false, text: "保存に失敗しました" });
    } finally { setPrefSaving(false); }
  };

  // ─── 活動ログ読み込み ───
  const handleLoadLog = async () => {
    setLogLoading(true);
    try {
      const res = await api.get("/auth/activity-log?limit=30");
      setActivityLog(res.data);
      setShowLog(true);
    } catch { /* ignore */ } finally { setLogLoading(false); }
  };

  // ─── 2FA セットアップ ───
  const handleTotpSetup = async () => {
    try {
      const res = await api.post("/auth/totp/setup");
      setTotpSetupData(res.data);
      setShowTotpSetup(true);
      setTotpMsg(null);
    } catch (err: any) {
      setTotpMsg({ ok: false, text: err?.response?.data?.detail ?? "セットアップに失敗" });
    }
  };

  const handleTotpVerify = async () => {
    try {
      await api.post("/auth/totp/verify", { code: totpCode });
      if (refreshUser) await refreshUser();
      setTotpMsg({ ok: true, text: "2段階認証を有効化しました" });
      setShowTotpSetup(false); setTotpCode("");
    } catch (err: any) {
      setTotpMsg({ ok: false, text: err?.response?.data?.detail ?? "コードが正しくありません" });
    }
  };

  const handleTotpDisable = async () => {
    try {
      await api.post("/auth/totp/disable", { password: totpDisablePw, code: totpDisableCode });
      if (refreshUser) await refreshUser();
      setTotpMsg({ ok: true, text: "2段階認証を無効化しました" });
      setTotpDisablePw(""); setTotpDisableCode("");
    } catch (err: any) {
      setTotpMsg({ ok: false, text: err?.response?.data?.detail ?? "無効化に失敗しました" });
    }
  };

  // ─── エクスポート ───
  const handleExport = async (type: "json" | "csv") => {
    type === "json" ? setExporting(true) : setExportCsv(true);
    try {
      const url = type === "csv" ? "/auth/export/csv" : "/auth/export";
      const res = await api.get(url, { responseType: "blob" });
      const blobUrl = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = type === "csv" ? "digital-memorial-export.csv" : "digital-memorial-export.json";
      a.click();
      URL.revokeObjectURL(blobUrl);
    } catch { /* ignore */ } finally {
      type === "json" ? setExporting(false) : setExportCsv(false);
    }
  };

  // ─── 退会 ───
  const handleDeleteAccount = async (e: FormEvent) => {
    e.preventDefault();
    setDeleting(true); setDeleteMsg("");
    try {
      await api.delete("/auth/me", { data: { password: deletePw } });
      logout(); navigate("/login");
    } catch (err: any) {
      setDeleteMsg(err?.response?.data?.detail ?? "削除に失敗しました");
    } finally { setDeleting(false); }
  };

  const ACTION_LABELS: Record<string, string> = {
    login: "ログイン", change_password: "パスワード変更", export_data: "データエクスポート",
    update_preferences: "設定変更", enable_2fa: "2FA有効化", disable_2fa: "2FA無効化",
    update_ending_note: "エンディングノート更新", create_estate: "相続計画作成",
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
        {/* プロフィール */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>プロフィール</h2>
          <div style={s.infoRow}><span style={s.infoLabel}>名前</span><span>{user?.name}</span></div>
          <div style={s.infoRow}><span style={s.infoLabel}>メールアドレス</span><span>{user?.email}</span></div>
          <div style={s.infoRow}>
            <span style={s.infoLabel}>最終ログイン</span>
            <span style={{ fontSize: "0.85rem", color: "var(--gray-500)" }}>
              {user?.last_login_at ? new Date(user.last_login_at).toLocaleString("ja-JP") : "記録なし"}
            </span>
          </div>
          <div style={s.infoRow}>
            <span style={s.infoLabel}>2段階認証</span>
            <span style={{ fontSize: "0.85rem", color: user?.totp_enabled ? "#16a34a" : "var(--gray-500)", fontWeight: 600 }}>
              {user?.totp_enabled ? "有効" : "無効"}
            </span>
          </div>
        </div>

        {/* 表示設定（渡辺博・田中幸子・藤田美香 要望） */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>表示設定</h2>
          <p style={s.helpText}>文字サイズやモードを変更して使いやすく調整できます。</p>

          <div style={s.field}>
            <label style={s.label}>文字サイズ</label>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              {[
                { value: "small", label: "小" },
                { value: "medium", label: "標準" },
                { value: "large", label: "大" },
                { value: "xlarge", label: "特大" },
              ].map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setFontSize(value)}
                  style={{
                    ...s.sizeBtn,
                    ...(fontSize === value ? s.sizeBtnActive : {}),
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "1rem" }}>
            <div>
              <div style={s.label}>かんたんモード</div>
              <div style={{ fontSize: "0.78rem", color: "var(--gray-500)" }}>必要最低限の項目だけ表示します</div>
            </div>
            <div
              onClick={() => setSimpleMode(!simpleMode)}
              style={{
                width: 44, height: 24, borderRadius: 12, cursor: "pointer",
                background: simpleMode ? "var(--green-700)" : "var(--gray-300)",
                position: "relative", transition: "background 0.2s",
              }}
            >
              <div style={{
                position: "absolute", top: 2, left: simpleMode ? 22 : 2,
                width: 20, height: 20, borderRadius: "50%", background: "#fff",
                transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,.3)",
              }} />
            </div>
          </div>

          {prefMsg && <div style={prefMsg.ok ? s.successBox : s.errorBox}>{prefMsg.text}</div>}
          <div style={{ ...s.actions, marginTop: "1rem" }}>
            <button style={{ ...s.btn, ...(prefSaving ? s.btnDisabled : {}) }} onClick={handleSavePreferences} disabled={prefSaving}>
              {prefSaving ? "保存中..." : "設定を保存する"}
            </button>
          </div>
        </div>

        {/* パスワード変更 */}
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

        {/* 2段階認証（中村美代 要望） */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>2段階認証（2FA）</h2>
          <p style={s.helpText}>認証アプリ（Google Authenticator等）を使って、ログインをより安全にします。</p>

          {totpMsg && <div style={{ ...(totpMsg.ok ? s.successBox : s.errorBox), marginBottom: "1rem" }}>{totpMsg.text}</div>}

          {!user?.totp_enabled ? (
            <>
              {!showTotpSetup ? (
                <button style={s.btn} onClick={handleTotpSetup}>2段階認証を設定する</button>
              ) : totpSetupData && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <p style={s.helpText}>認証アプリでQRコードをスキャンしてください。</p>
                  <img src={totpSetupData.qr_data_url} alt="TOTP QR" style={{ width: 180, height: 180, border: "1px solid var(--sand-300)" }} />
                  <p style={{ fontSize: "0.78rem", color: "var(--gray-500)" }}>
                    手動入力用シークレット: <code style={{ background: "var(--sand-100)", padding: "2px 6px", borderRadius: 4 }}>{totpSetupData.totp_secret}</code>
                  </p>
                  <div style={s.field}>
                    <label style={s.label}>認証アプリの6桁のコードを入力</label>
                    <input style={{ ...s.input, letterSpacing: "0.2em", width: 160 }} type="text" maxLength={6} value={totpCode} onChange={(e) => setTotpCode(e.target.value)} placeholder="000000" />
                  </div>
                  <div style={s.actions}>
                    <button style={{ ...s.cancelBtn }} onClick={() => setShowTotpSetup(false)}>キャンセル</button>
                    <button style={s.btn} onClick={handleTotpVerify} disabled={totpCode.length < 6}>有効化する</button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div style={s.successBox}>2段階認証は現在有効です</div>
              <div style={s.field}>
                <label style={s.label}>無効化するにはパスワードとコードを入力</label>
                <input style={s.input} type="password" placeholder="パスワード" value={totpDisablePw} onChange={(e) => setTotpDisablePw(e.target.value)} />
                <input style={{ ...s.input, marginTop: "0.4rem", letterSpacing: "0.2em" }} type="text" maxLength={6} placeholder="認証コード" value={totpDisableCode} onChange={(e) => setTotpDisableCode(e.target.value)} />
              </div>
              <button style={{ ...s.btn, background: "#dc2626" }} onClick={handleTotpDisable}>2段階認証を無効化</button>
            </div>
          )}
        </div>

        {/* 活動ログ（井上剛 要望） */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>活動ログ</h2>
          <p style={s.helpText}>いつ何の操作をしたか確認できます。不審なログインの検出に役立ちます。</p>
          {!showLog ? (
            <button style={{ ...s.btn, background: "#4b5563" }} onClick={handleLoadLog} disabled={logLoading}>
              {logLoading ? "読み込み中..." : "活動ログを表示する（直近30件）"}
            </button>
          ) : (
            <div>
              <div style={{ maxHeight: 300, overflowY: "auto", border: "1px solid var(--sand-300)", borderRadius: 6 }}>
                {activityLog.length === 0 ? (
                  <div style={{ padding: "1rem", color: "var(--gray-500)", fontSize: "0.85rem" }}>ログなし</div>
                ) : activityLog.map((log) => (
                  <div key={log.id} style={{ padding: "0.6rem 1rem", borderBottom: "1px solid var(--sand-200)", display: "flex", gap: "1rem", fontSize: "0.82rem" }}>
                    <span style={{ color: "var(--gray-500)", width: 140, flexShrink: 0 }}>
                      {log.created_at ? new Date(log.created_at).toLocaleString("ja-JP") : "-"}
                    </span>
                    <span style={{ fontWeight: 600 }}>{ACTION_LABELS[log.action] ?? log.action}</span>
                    {log.detail && <span style={{ color: "var(--gray-500)" }}>{log.detail}</span>}
                  </div>
                ))}
              </div>
              <button style={{ ...s.cancelBtn, marginTop: "0.5rem" }} onClick={() => setShowLog(false)}>閉じる</button>
            </div>
          )}
        </div>

        {/* リマインダー設定へのリンク */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>リマインダー・通知設定</h2>
          <p style={s.helpText}>終活の定期リマインドや、デッドマンスイッチの通知間隔を設定できます。</p>
          <a href="/settings/reminders" style={{ ...s.btn, display: "inline-block", textDecoration: "none", padding: "0.6rem 1.25rem", fontSize: "0.88rem" }}>
            🔔 リマインダー設定を開く →
          </a>
        </div>

        {/* データエクスポート（中村美代 要望） */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>データエクスポート</h2>
          <p style={s.helpText}>すべてのデータをダウンロードできます。サービス変更時の引き継ぎにご利用ください。</p>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <button style={{ ...s.btn, background: "#2563eb" }} onClick={() => handleExport("json")} disabled={exporting}>
              {exporting ? "エクスポート中..." : "JSONでダウンロード"}
            </button>
            <button style={{ ...s.btn, background: "#16a34a" }} onClick={() => handleExport("csv")} disabled={exportCsv}>
              {exportCsv ? "エクスポート中..." : "CSVでダウンロード"}
            </button>
          </div>
        </div>

        {/* アカウント削除 */}
        <div style={{ ...s.card, ...s.dangerCard }}>
          <h2 style={{ ...s.cardTitle, color: "#dc2626" }}>アカウント削除</h2>
          <p style={s.dangerText}>アカウントを削除すると、すべてのデータが完全に削除されます。この操作は取り消せません。</p>
          {!deleteConfirm ? (
            <button style={s.dangerBtn} onClick={() => setDeleteConfirm(true)}>アカウントを削除する</button>
          ) : (
            <form onSubmit={handleDeleteAccount} style={s.form}>
              <div style={s.field}>
                <label style={s.label}>パスワードを入力して確認</label>
                <input style={s.input} type="password" value={deletePw} onChange={(e) => setDeletePw(e.target.value)} required placeholder="現在のパスワード" />
              </div>
              {deleteMsg && <div style={s.errorBox}>{deleteMsg}</div>}
              <div style={s.actions}>
                <button type="button" style={s.cancelBtn} onClick={() => { setDeleteConfirm(false); setDeletePw(""); setDeleteMsg(""); }}>キャンセル</button>
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
  cardTitle: { fontSize: "0.95rem", fontWeight: 700, marginBottom: "0.5rem", color: "var(--gray-800)" },
  helpText: { fontSize: "0.82rem", color: "var(--gray-500)", marginBottom: "1rem", lineHeight: 1.6 },
  infoRow: { display: "flex", gap: "1rem", padding: "0.5rem 0", borderBottom: "1px solid var(--sand-200)", fontSize: "0.9rem", alignItems: "center" },
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
  sizeBtn: { padding: "0.45rem 1rem", border: "1.5px solid var(--gray-300)", borderRadius: 6, fontSize: "0.85rem", background: "var(--white)", cursor: "pointer", color: "var(--gray-700)" },
  sizeBtnActive: { background: "var(--green-800)", color: "#fff", border: "1.5px solid var(--green-800)" },
};
