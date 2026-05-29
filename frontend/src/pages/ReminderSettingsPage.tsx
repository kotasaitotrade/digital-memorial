import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";
import type { AxiosError } from "axios";

const GREEN = "#1a5c38";

interface ReminderSetting {
  id: number;
  enabled: boolean;
  review_month: number;
  notify_incomplete: boolean;
  notify_trusted: boolean;
  email: string | null;
  updated_at: string | null;
}

const MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];

export default function ReminderSettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [setting, setSetting] = useState<ReminderSetting | null>(null);
  const [saved, setSaved] = useState(false);
  const [emailInput, setEmailInput] = useState("");
  const [testSending, setTestSending] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  useEffect(() => {
    api.get("/reminder-settings").then((r) => {
      setSetting(r.data);
      setEmailInput(r.data.email || "");
    });
  }, []);

  const update = async (patch: Partial<ReminderSetting>) => {
    const r = await api.put("/reminder-settings", patch);
    setSetting(r.data);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const toggle = (field: keyof ReminderSetting, val: boolean) => {
    setSetting((p) => p ? { ...p, [field]: val } : p);
    update({ [field]: val });
  };

  const sendTestEmail = async () => {
    setTestSending(true);
    setTestResult(null);
    try {
      const r = await api.post("/reminder-settings/test-send");
      setTestResult(`✅ テストメールを ${r.data.sent_to} に送信しました`);
    } catch (e) {
      const err = e as AxiosError<{ detail: string }>;
      setTestResult(`❌ 送信失敗: ${err.response?.data?.detail ?? "不明なエラー"}`);
    } finally {
      setTestSending(false);
    }
  };

  if (!setting) return <div style={{ textAlign: "center", padding: "4rem", color: "#6b6b6b" }}>読み込み中...</div>;

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f0" }}>
      <header style={{ background: GREEN, padding: "0 1.5rem", height: "3.5rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Link to="/shukatsu" style={{ color: "white", textDecoration: "none", fontWeight: 700, fontSize: "1.1rem" }}>
          ← Digital Memorial
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span style={{ color: "rgba(255,255,255,0.85)", fontSize: "0.85rem" }}>{user?.name}</span>
          <button onClick={() => { logout(); navigate("/login"); }}
            style={{ background: "rgba(255,255,255,0.2)", border: "none", color: "white", padding: "0.3rem 0.8rem", borderRadius: "4px", cursor: "pointer", fontSize: "0.85rem" }}>
            ログアウト
          </button>
        </div>
      </header>

      <main style={{ maxWidth: "700px", margin: "0 auto", padding: "2rem 1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div>
            <h1 style={{ color: GREEN, fontSize: "1.6rem", margin: 0 }}>🔔 リマインダー設定</h1>
            <p style={{ color: "#666", margin: "0.4rem 0 0", fontSize: "0.9rem" }}>終活情報の年次見直しや未完了タスクをメールでお知らせします</p>
          </div>
          {saved && <span style={{ color: GREEN, fontWeight: 600, fontSize: "0.9rem" }}>✓ 保存しました</span>}
        </div>

        {/* 通知のオン/オフ */}
        <section style={{ background: "white", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2 style={{ color: GREEN, fontSize: "1.1rem", margin: 0 }}>メール通知</h2>
              <p style={{ color: "#666", fontSize: "0.85rem", margin: "0.25rem 0 0" }}>すべての通知メールのオン/オフを切り替えます</p>
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
              <div
                onClick={() => toggle("enabled", !setting.enabled)}
                style={{
                  width: "48px", height: "26px", borderRadius: "13px",
                  background: setting.enabled ? GREEN : "#ccc",
                  position: "relative", cursor: "pointer", transition: "background 0.2s",
                }}>
                <div style={{
                  position: "absolute", top: "3px",
                  left: setting.enabled ? "25px" : "3px",
                  width: "20px", height: "20px", borderRadius: "50%",
                  background: "white", transition: "left 0.2s",
                }} />
              </div>
              <span style={{ fontWeight: 600, color: setting.enabled ? GREEN : "#888" }}>
                {setting.enabled ? "ON" : "OFF"}
              </span>
            </label>
          </div>
        </section>

        <div style={{ opacity: setting.enabled ? 1 : 0.4, pointerEvents: setting.enabled ? "all" : "none" }}>
          {/* 通知先メール */}
          <section style={{ background: "white", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
            <h2 style={{ color: GREEN, fontSize: "1.1rem", marginTop: 0 }}>通知先メールアドレス</h2>
            <p style={{ color: "#666", fontSize: "0.85rem", marginBottom: "1rem" }}>未設定の場合はアカウントのメールアドレスに送信します</p>
            <div style={{ display: "flex", gap: "0.75rem" }}>
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder={user?.email || "メールアドレス"}
                style={{ flex: 1, padding: "0.6rem", border: "1px solid #ccc", borderRadius: "6px", fontSize: "0.95rem" }}
              />
              <button
                onClick={() => update({ email: emailInput || null })}
                style={{ background: GREEN, color: "white", border: "none", padding: "0.6rem 1.2rem", borderRadius: "6px", cursor: "pointer", fontWeight: 600 }}>
                保存
              </button>
            </div>
          </section>

          {/* 年次見直しリマインダー */}
          <section style={{ background: "white", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
            <h2 style={{ color: GREEN, fontSize: "1.1rem", marginTop: 0 }}>年次見直しリマインダー</h2>
            <p style={{ color: "#666", fontSize: "0.85rem", marginBottom: "1rem" }}>毎年この月に「内容を見直しましょう」というメールをお送りします</p>
            <select
              value={setting.review_month}
              onChange={(e) => update({ review_month: Number(e.target.value) })}
              style={{ padding: "0.6rem 1rem", border: "1px solid #ccc", borderRadius: "6px", fontSize: "0.95rem", background: "white" }}>
              {MONTHS.map((m, i) => (
                <option key={i + 1} value={i + 1}>{m}</option>
              ))}
            </select>
            <p style={{ color: "#888", fontSize: "0.82rem", marginTop: "0.5rem" }}>
              毎年 {MONTHS[setting.review_month - 1]} に通知します
            </p>
          </section>

          {/* 詳細通知設定 */}
          <section style={{ background: "white", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
            <h2 style={{ color: GREEN, fontSize: "1.1rem", marginTop: 0 }}>詳細通知設定</h2>
            {[
              { field: "notify_incomplete" as const, label: "未完了タスクのリマインダー", desc: "チェックリストで未完了のタスクを定期的にお知らせします" },
              { field: "notify_trusted" as const, label: "信頼者確認メール", desc: "登録した信頼者が有効かどうかを年に1度確認するメールを送ります" },
            ].map((item) => (
              <div key={item.field} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem 0", borderBottom: "1px solid #f0f0f0" }}>
                <div>
                  <div style={{ fontWeight: 600, color: "#222", fontSize: "0.95rem" }}>{item.label}</div>
                  <div style={{ color: "#888", fontSize: "0.82rem", marginTop: "0.2rem" }}>{item.desc}</div>
                </div>
                <div
                  onClick={() => toggle(item.field, !setting[item.field])}
                  style={{
                    width: "44px", height: "24px", borderRadius: "12px", flexShrink: 0,
                    background: setting[item.field] ? GREEN : "#ccc",
                    position: "relative", cursor: "pointer", transition: "background 0.2s",
                  }}>
                  <div style={{
                    position: "absolute", top: "2px",
                    left: setting[item.field] ? "22px" : "2px",
                    width: "20px", height: "20px", borderRadius: "50%",
                    background: "white", transition: "left 0.2s",
                  }} />
                </div>
              </div>
            ))}
          </section>
        </div>

        {/* テスト送信 */}
        <div style={{ background: "#f0f7f4", border: "1px solid #b2dfdb", borderRadius: "8px", padding: "1rem 1.25rem" }}>
          <strong style={{ color: "#2e7d32", fontSize: "0.9rem" }}>📧 メール送信テスト</strong>
          <p style={{ margin: "0.5rem 0 0.75rem", color: "#555", fontSize: "0.85rem", lineHeight: 1.6 }}>
            現在の設定でリマインダーメールが届くか確認できます。登録済みのメールアドレスに即座に送信されます。
          </p>
          <button
            onClick={sendTestEmail}
            disabled={testSending}
            style={{ background: GREEN, color: "white", border: "none", padding: "0.5rem 1.25rem", borderRadius: "6px", cursor: testSending ? "not-allowed" : "pointer", fontSize: "0.9rem", opacity: testSending ? 0.7 : 1 }}>
            {testSending ? "送信中..." : "テストメールを送信"}
          </button>
          {testResult && (
            <p style={{ marginTop: "0.6rem", fontSize: "0.85rem", color: testResult.startsWith("✅") ? "#2e7d32" : "#c62828" }}>
              {testResult}
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
