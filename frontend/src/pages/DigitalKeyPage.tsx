import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { autoCheck } from "../lib/autoCheck";
import { useAuth } from "../hooks/useAuth";

const G = "#1a5c38";
const G2 = "#2d7a4f";

interface TrustedPerson {
  id: number; name: string; email: string; access_scope: string[];
  access_token: string; has_requested: boolean; requested_at: string | null;
  email_verified: boolean; created_at: string;
}
interface DigitalKey {
  id: number; unlock_condition: string; is_unlocked: boolean;
  unlocked_at: string | null; notes: string | null;
  trusted_persons: TrustedPerson[];
  deadman_enabled: boolean; deadman_interval_days: number; last_checkin_at: string | null;
}

const SCOPE_LABELS: Record<string, string> = {
  all: "すべてのデータ", estate: "相続情報のみ", ending_note: "エンディングノートのみ",
};

export default function DigitalKeyPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [key, setKey] = useState<DigitalKey | null>(null);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", access_scope: ["all"] });
  const [tokenVisible, setTokenVisible] = useState<Record<number, boolean>>({});
  const [copied, setCopied] = useState<number | null>(null);
  const [checkinDone, setCheckinDone] = useState(false);
  const [activeSection, setActiveSection] = useState<"condition" | "deadman" | "persons">("persons");

  useEffect(() => { api.get("/digital-key").then((r) => setKey(r.data)); }, []);

  const updateCondition = async (val: string) => {
    setSaving(true);
    const r = await api.patch("/digital-key", { unlock_condition: val });
    setKey(r.data); setSaving(false);
  };
  const updateNotes = async (val: string) => {
    const r = await api.patch("/digital-key", { notes: val }); setKey(r.data);
  };
  const addPerson = async () => {
    if (!form.name || !form.email) return;
    const r = await api.post("/digital-key/trusted-persons", form);
    setKey((p) => p ? { ...p, trusted_persons: [...p.trusted_persons, r.data] } : p);
    setForm({ name: "", email: "", access_scope: ["all"] }); setShowForm(false);
  };
  const deletePerson = async (id: number) => {
    if (!confirm("この信頼者を削除しますか？")) return;
    await api.delete(`/digital-key/trusted-persons/${id}`);
    setKey((p) => p ? { ...p, trusted_persons: p.trusted_persons.filter((x) => x.id !== id) } : p);
  };
  const doCheckin = async () => {
    await api.post("/digital-key/checkin");
    const r = await api.get("/digital-key"); setKey(r.data);
    setCheckinDone(true); setTimeout(() => setCheckinDone(false), 3000);
  };
  const updateDeadman = async (enabled: boolean, days?: number) => {
    const r = await api.patch("/digital-key", { deadman_enabled: enabled, ...(days !== undefined ? { deadman_interval_days: days } : {}) });
    setKey(r.data); if (enabled) autoCheck("digital_key_set");
  };
  const copyToken = (person: TrustedPerson) => {
    const url = `${window.location.origin}/unlock/${person.id}?token=${person.access_token}`;
    navigator.clipboard.writeText(url).then(() => { setCopied(person.id); setTimeout(() => setCopied(null), 2000); });
  };

  if (!key) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0d1f14" }}>
      <div style={{ color: "#a7d7b9", fontSize: "0.9rem" }}>読み込み中...</div>
    </div>
  );

  const daysSince = key.last_checkin_at ? Math.floor((Date.now() - new Date(key.last_checkin_at).getTime()) / 86400000) : null;
  const daysLeft = daysSince !== null ? key.deadman_interval_days - daysSince : null;
  const isOverdue = daysLeft !== null && daysLeft <= 0;
  const isUrgent = daysLeft !== null && daysLeft <= 7 && !isOverdue;
  const setupScore = [
    key.trusted_persons.length > 0,
    key.unlock_condition !== "",
    key.deadman_enabled,
    key.trusted_persons.some((p) => p.email_verified),
  ].filter(Boolean).length;

  return (
    <div style={{ minHeight: "100vh", background: "#f3f6f4", fontFamily: "sans-serif" }}>

      {/* ── ヘッダー ── */}
      <header style={{ background: `linear-gradient(135deg, #0d1f14 0%, ${G} 100%)`, padding: "0 1.5rem", position: "sticky", top: 0, zIndex: 20 }}>
        <div style={{ maxWidth: 760, margin: "0 auto", height: "3.5rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Link to="/shukatsu" style={{ color: "rgba(255,255,255,0.8)", textDecoration: "none", fontSize: "0.88rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            ← 終活ノート
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span style={{ color: "rgba(255,255,255,0.6)", fontSize: "0.82rem" }}>{user?.name}</span>
            <button onClick={() => { logout(); navigate("/login"); }}
              style={{ background: "rgba(255,255,255,0.12)", border: "1px solid rgba(255,255,255,0.2)", color: "rgba(255,255,255,0.85)", padding: "0.3rem 0.85rem", borderRadius: 6, cursor: "pointer", fontSize: "0.82rem" }}>
              ログアウト
            </button>
          </div>
        </div>
      </header>

      {/* ── ヒーロー ── */}
      <div style={{ background: `linear-gradient(135deg, #0d1f14 0%, ${G} 100%)`, paddingBottom: "2.5rem" }}>
        <div style={{ maxWidth: 760, margin: "0 auto", padding: "2rem 1.5rem 0" }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.6rem" }}>
                <span style={{ fontSize: "2rem" }}>🔐</span>
                <h1 style={{ color: "#fff", fontSize: "1.5rem", fontWeight: 800, margin: 0 }}>デジタル遺品鍵</h1>
                {key.is_unlocked
                  ? <span style={{ background: "#fbbf24", color: "#78350f", fontSize: "0.75rem", fontWeight: 700, padding: "0.2rem 0.7rem", borderRadius: 9999 }}>🔓 開錠済み</span>
                  : <span style={{ background: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.9)", fontSize: "0.75rem", fontWeight: 600, padding: "0.2rem 0.7rem", borderRadius: 9999 }}>🔒 施錠中</span>}
              </div>
              <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.88rem", lineHeight: 1.7, margin: 0, maxWidth: 480 }}>
                あなたが亡くなった後、信頼者が終活データにアクセスできるよう事前に設定する機能です。
              </p>
            </div>

            {/* セットアップスコア */}
            <div style={{ background: "rgba(255,255,255,0.1)", borderRadius: 12, padding: "0.9rem 1.25rem", minWidth: 130, textAlign: "center" }}>
              <div style={{ fontSize: "2rem", fontWeight: 800, color: "#fff", lineHeight: 1 }}>{setupScore}<span style={{ fontSize: "1rem", color: "rgba(255,255,255,0.5)" }}>/4</span></div>
              <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.6)", marginTop: "0.3rem" }}>設定完了</div>
              <div style={{ display: "flex", gap: "0.3rem", justifyContent: "center", marginTop: "0.5rem" }}>
                {[0,1,2,3].map((i) => (
                  <div key={i} style={{ width: 22, height: 4, borderRadius: 2, background: i < setupScore ? "#4ade80" : "rgba(255,255,255,0.2)" }} />
                ))}
              </div>
            </div>
          </div>

          {/* 開錠済みバナー */}
          {key.is_unlocked && (
            <div style={{ marginTop: "1.25rem", background: "#fef3c7", border: "1px solid #fbbf24", borderRadius: 10, padding: "0.85rem 1.25rem", color: "#92400e", fontSize: "0.88rem" }}>
              <strong>🔓 開錠済み</strong> — {key.unlocked_at ? new Date(key.unlocked_at).toLocaleString("ja-JP") : ""} に開錠されました。信頼者がデータにアクセスできる状態です。
            </div>
          )}

          {/* デッドマン警告 */}
          {key.deadman_enabled && isOverdue && (
            <div style={{ marginTop: "1rem", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 10, padding: "0.85rem 1.25rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem" }}>
              <span style={{ color: "#dc2626", fontWeight: 700, fontSize: "0.88rem" }}>⚠️ 生存確認が {Math.abs(daysLeft!)}日超過しています — 信頼者へ通知済みの可能性があります</span>
              <button onClick={doCheckin} style={{ background: "#dc2626", color: "#fff", border: "none", padding: "0.4rem 1rem", borderRadius: 7, cursor: "pointer", fontWeight: 700, fontSize: "0.85rem", whiteSpace: "nowrap" }}>
                {checkinDone ? "✓ 確認済み" : "今すぐ確認"}
              </button>
            </div>
          )}
          {key.deadman_enabled && isUrgent && (
            <div style={{ marginTop: "1rem", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 10, padding: "0.85rem 1.25rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem" }}>
              <span style={{ color: "#92400e", fontWeight: 600, fontSize: "0.88rem" }}>🕐 生存確認の期限まであと <strong>{daysLeft}日</strong></span>
              <button onClick={doCheckin} style={{ background: "#d97706", color: "#fff", border: "none", padding: "0.4rem 1rem", borderRadius: 7, cursor: "pointer", fontWeight: 700, fontSize: "0.85rem", whiteSpace: "nowrap" }}>
                {checkinDone ? "✓ 確認済み" : "今すぐ確認"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── コンテンツ ── */}
      <main style={{ maxWidth: 760, margin: "-1.5rem auto 0", padding: "0 1rem 3rem", position: "relative", zIndex: 1 }}>

        {/* セクションタブ */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem" }}>
          {([
            { id: "persons",   icon: "👥", label: "信頼者" },
            { id: "condition", icon: "🔑", label: "開錠条件" },
            { id: "deadman",   icon: "⏰", label: "生存確認" },
          ] as const).map((tab) => (
            <button key={tab.id} onClick={() => setActiveSection(tab.id)}
              style={{ flex: 1, padding: "0.7rem", borderRadius: 10, border: "none", cursor: "pointer", fontWeight: 600, fontSize: "0.88rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.2rem",
                background: activeSection === tab.id ? G : "#fff",
                color: activeSection === tab.id ? "#fff" : "#374151",
                boxShadow: activeSection === tab.id ? `0 4px 14px rgba(26,92,56,.35)` : "0 1px 4px rgba(0,0,0,.08)",
              }}>
              <span style={{ fontSize: "1.1rem" }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── 信頼者セクション ── */}
        {activeSection === "persons" && (
          <div style={card}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
              <div>
                <h2 style={sectionTitle}>信頼者（受取人）</h2>
                <p style={sectionDesc}>解除キーURLを受け取る家族・友人を最大3名登録します</p>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span style={{ fontSize: "0.82rem", color: "#6b7280" }}>{key.trusted_persons.length} / 3名</span>
                {key.trusted_persons.length < 3 && (
                  <button onClick={() => setShowForm(true)}
                    style={{ background: G, color: "#fff", border: "none", padding: "0.45rem 1.1rem", borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: "0.88rem" }}>
                    + 追加
                  </button>
                )}
              </div>
            </div>

            {/* フロー説明 */}
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", overflowX: "auto" }}>
              {[
                { step: "1", text: "信頼者を登録" },
                { step: "2", text: "URLを共有" },
                { step: "3", text: "申請・開錠" },
                { step: "4", text: "データ閲覧" },
              ].map((s, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexShrink: 0 }}>
                  <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#f0f9f4", border: `2px solid ${G}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.78rem", fontWeight: 700, color: G }}>{s.step}</div>
                  <span style={{ fontSize: "0.8rem", color: "#374151", whiteSpace: "nowrap" }}>{s.text}</span>
                  {i < 3 && <span style={{ color: "#d1d5db", fontSize: "0.9rem" }}>›</span>}
                </div>
              ))}
            </div>

            {key.trusted_persons.length === 0 && !showForm && (
              <div style={{ textAlign: "center", padding: "2.5rem 1rem", color: "#9ca3af" }}>
                <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>👤</div>
                <p style={{ fontSize: "0.9rem", margin: 0 }}>まだ信頼者が登録されていません</p>
              </div>
            )}

            {key.trusted_persons.map((p) => (
              <div key={p.id} style={{ border: `1px solid ${p.has_requested ? "#a7d7b9" : "#e5e7eb"}`, borderRadius: 10, padding: "1rem 1.25rem", marginBottom: "0.75rem", background: p.has_requested ? "#f0f9f4" : "#fff" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontWeight: 700, color: "#111", fontSize: "1rem" }}>{p.name}</div>
                    <div style={{ color: "#6b7280", fontSize: "0.83rem", marginTop: "0.15rem" }}>{p.email}</div>
                    <div style={{ color: "#6b7280", fontSize: "0.8rem", marginTop: "0.3rem" }}>
                      アクセス範囲: <span style={{ color: G, fontWeight: 600 }}>{p.access_scope.map((s) => SCOPE_LABELS[s] || s).join("・")}</span>
                    </div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.4rem" }}>
                    {p.email_verified
                      ? <span style={badge("#dcfce7", "#166534")}>✅ メール確認済み</span>
                      : <span style={badge("#fef3c7", "#92400e")}>⏳ 未確認</span>}
                    {p.has_requested && <span style={badge("#dbeafe", "#1e40af")}>申請済み</span>}
                    <button onClick={() => deletePerson(p.id)} style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "0.8rem", padding: "0.1rem 0.3rem" }}>削除</button>
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.85rem" }}>
                  <button onClick={() => setTokenVisible((prev) => ({ ...prev, [p.id]: !prev[p.id] }))}
                    style={{ background: "#f3f4f6", border: "none", padding: "0.35rem 0.85rem", borderRadius: 7, cursor: "pointer", fontSize: "0.82rem", color: "#374151" }}>
                    {tokenVisible[p.id] ? "URLを隠す" : "解除キーを表示"}
                  </button>
                  <button onClick={() => copyToken(p)}
                    style={{ background: copied === p.id ? G : "#f0f9f4", border: `1px solid ${copied === p.id ? G : "#a7d7b9"}`, padding: "0.35rem 0.85rem", borderRadius: 7, cursor: "pointer", fontSize: "0.82rem", color: copied === p.id ? "#fff" : G, fontWeight: 600 }}>
                    {copied === p.id ? "✓ コピー済み" : "📋 URLをコピー"}
                  </button>
                </div>
                {tokenVisible[p.id] && (
                  <div style={{ marginTop: "0.65rem", background: "#1e293b", padding: "0.65rem 0.85rem", borderRadius: 8, fontSize: "0.75rem", wordBreak: "break-all", color: "#94d5b2", fontFamily: "monospace" }}>
                    {`${window.location.origin}/unlock/${p.id}?token=${p.access_token}`}
                  </div>
                )}
              </div>
            ))}

            {showForm && (
              <div style={{ border: `2px solid ${G}`, borderRadius: 12, padding: "1.25rem", marginTop: "1rem", background: "#f0f9f4" }}>
                <h3 style={{ margin: "0 0 1rem", color: G, fontSize: "1rem" }}>信頼者を追加</h3>
                <div style={{ display: "grid", gap: "0.75rem" }}>
                  <label>
                    <span style={fieldLabel}>名前</span>
                    <input value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                      style={fieldInput} placeholder="山田 太郎" />
                  </label>
                  <label>
                    <span style={fieldLabel}>メールアドレス</span>
                    <input type="email" value={form.email} onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                      style={fieldInput} placeholder="taro@example.com" />
                  </label>
                  <label>
                    <span style={fieldLabel}>アクセス範囲</span>
                    <select value={form.access_scope[0]} onChange={(e) => setForm((p) => ({ ...p, access_scope: [e.target.value] }))} style={fieldInput}>
                      <option value="all">すべてのデータ</option>
                      <option value="estate">相続情報のみ</option>
                      <option value="ending_note">エンディングノートのみ</option>
                    </select>
                  </label>
                </div>
                <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
                  <button onClick={addPerson} style={{ background: G, color: "#fff", border: "none", padding: "0.55rem 1.5rem", borderRadius: 8, cursor: "pointer", fontWeight: 700, fontSize: "0.9rem" }}>登録する</button>
                  <button onClick={() => { setShowForm(false); setForm({ name: "", email: "", access_scope: ["all"] }); }}
                    style={{ background: "#fff", border: "1px solid #d1d5db", padding: "0.55rem 1.25rem", borderRadius: 8, cursor: "pointer", color: "#374151", fontSize: "0.9rem" }}>キャンセル</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── 開錠条件セクション ── */}
        {activeSection === "condition" && (
          <div style={card}>
            <h2 style={sectionTitle}>開錠条件</h2>
            <p style={sectionDesc}>何名の信頼者が申請したら開錠するかを設定します</p>
            {saving && <span style={{ color: "#9ca3af", fontSize: "0.8rem" }}>保存中...</span>}

            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
              {[
                { value: "one_request",  icon: "⚡", label: "1名の申請で開錠", desc: "信頼者のうち1名が申請すれば即座に開錠" },
                { value: "two_requests", icon: "🛡️", label: "2名以上の申請で開錠", desc: "2名以上が申請して初めて開錠（不正アクセス防止）" },
              ].map((opt) => (
                <label key={opt.value} onClick={() => updateCondition(opt.value)}
                  style={{ display: "flex", alignItems: "center", gap: "1rem", cursor: "pointer", padding: "1rem 1.25rem", borderRadius: 10,
                    border: `2px solid ${key.unlock_condition === opt.value ? G : "#e5e7eb"}`,
                    background: key.unlock_condition === opt.value ? "#f0f9f4" : "#fff" }}>
                  <span style={{ fontSize: "1.5rem" }}>{opt.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: key.unlock_condition === opt.value ? G : "#111", fontSize: "0.95rem" }}>{opt.label}</div>
                    <div style={{ fontSize: "0.82rem", color: "#6b7280", marginTop: "0.2rem" }}>{opt.desc}</div>
                  </div>
                  <div style={{ width: 20, height: 20, borderRadius: "50%", border: `2px solid ${key.unlock_condition === opt.value ? G : "#d1d5db"}`, background: key.unlock_condition === opt.value ? G : "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    {key.unlock_condition === opt.value && <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#fff" }} />}
                  </div>
                </label>
              ))}
            </div>

            <label>
              <span style={fieldLabel}>メモ・備考（信頼者への伝言など）</span>
              <textarea defaultValue={key.notes || ""} onBlur={(e) => updateNotes(e.target.value)} rows={4}
                style={{ ...fieldInput, resize: "vertical" as const, lineHeight: 1.6 }}
                placeholder="信頼者への注意事項、データの場所、パスワードのヒントなど" />
            </label>
          </div>
        )}

        {/* ── 生存確認スイッチセクション ── */}
        {activeSection === "deadman" && (
          <div style={card}>
            <h2 style={sectionTitle}>⏰ 生存確認スイッチ</h2>
            <p style={sectionDesc}>設定した日数ログインがなかった場合、信頼者へ自動通知します</p>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem 1.25rem", background: "#f9fafb", borderRadius: 10, marginBottom: "1.25rem" }}>
              <div>
                <div style={{ fontWeight: 600, color: "#111", fontSize: "0.95rem" }}>デッドマンスイッチを有効化</div>
                <div style={{ fontSize: "0.78rem", color: "#6b7280", marginTop: "0.2rem" }}>
                  {key.last_checkin_at ? `最後の確認: ${new Date(key.last_checkin_at).toLocaleString("ja-JP")}` : "まだ生存確認を行っていません"}
                </div>
              </div>
              <div onClick={() => updateDeadman(!key.deadman_enabled)}
                style={{ width: 48, height: 26, borderRadius: 13, cursor: "pointer", background: key.deadman_enabled ? G : "#d1d5db", position: "relative", transition: "background 0.2s", flexShrink: 0 }}>
                <div style={{ position: "absolute", top: 3, left: key.deadman_enabled ? 25 : 3, width: 20, height: 20, borderRadius: "50%", background: "#fff", transition: "left 0.2s", boxShadow: "0 1px 4px rgba(0,0,0,.25)" }} />
              </div>
            </div>

            {key.deadman_enabled && (
              <>
                <div style={{ marginBottom: "1.25rem" }}>
                  <div style={fieldLabel}>未ログイン通知までの日数</div>
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
                    {[30, 60, 90, 180, 365].map((d) => (
                      <button key={d} onClick={() => updateDeadman(true, d)}
                        style={{ padding: "0.45rem 1rem", borderRadius: 8, border: `2px solid ${key.deadman_interval_days === d ? G : "#e5e7eb"}`,
                          background: key.deadman_interval_days === d ? G : "#fff",
                          color: key.deadman_interval_days === d ? "#fff" : "#374151",
                          cursor: "pointer", fontSize: "0.88rem", fontWeight: key.deadman_interval_days === d ? 700 : 400 }}>
                        {d}日
                      </button>
                    ))}
                  </div>
                </div>

                {daysLeft !== null && (
                  <div style={{ padding: "1rem 1.25rem", borderRadius: 10, marginBottom: "1.25rem",
                    background: isOverdue ? "#fef2f2" : isUrgent ? "#fffbeb" : "#f0f9f4",
                    border: `1px solid ${isOverdue ? "#fca5a5" : isUrgent ? "#fde68a" : "#a7d7b9"}` }}>
                    <div style={{ fontWeight: 700, fontSize: "1.1rem", color: isOverdue ? "#dc2626" : isUrgent ? "#d97706" : G }}>
                      {isOverdue ? `⚠️ ${Math.abs(daysLeft)}日 超過` : `残り ${daysLeft} 日`}
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: "0.3rem" }}>
                      {isOverdue ? "信頼者へ通知済みの可能性があります" : `次の通知まで ${daysLeft} 日あります`}
                    </div>
                  </div>
                )}

                <button onClick={doCheckin}
                  style={{ width: "100%", padding: "0.9rem", background: checkinDone ? "#16a34a" : G, color: "#fff", border: "none", borderRadius: 10, cursor: "pointer", fontWeight: 700, fontSize: "1rem",
                    boxShadow: `0 4px 14px rgba(26,92,56,.35)`, transition: "all 0.2s" }}>
                  {checkinDone ? "✓ 生存確認完了！" : "✅ 今日の生存確認を行う"}
                </button>
                <p style={{ textAlign: "center", fontSize: "0.78rem", color: "#9ca3af", marginTop: "0.65rem" }}>
                  ボタンを押すと確認日時がリセットされます
                </p>
              </>
            )}

            {!key.deadman_enabled && (
              <div style={{ textAlign: "center", padding: "2rem", color: "#9ca3af" }}>
                <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>⏸️</div>
                <p style={{ fontSize: "0.88rem", margin: 0 }}>スイッチを有効にすると、一定期間ログインがない場合に<br />信頼者へ自動通知されます</p>
              </div>
            )}
          </div>
        )}

        {/* 使い方ガイド */}
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1.25rem 1.5rem", marginTop: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.85rem" }}>
            <span>📖</span>
            <span style={{ fontWeight: 700, color: "#374151", fontSize: "0.9rem" }}>使い方ガイド</span>
          </div>
          <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "#6b7280", fontSize: "0.84rem", lineHeight: 1.9 }}>
            <li>信頼者（家族など）を最大3名登録する</li>
            <li>解除キーURLをコピーして信頼者に伝える（メール・メモなど）</li>
            <li>あなたが亡くなった後、信頼者がURLにアクセスして申請する</li>
            <li>設定した条件を満たすと自動的に開錠され、データを閲覧できる（読み取り専用）</li>
          </ol>
        </div>
      </main>
    </div>
  );
}

// ── 共通スタイル ───────────────────────────────────────────
const card: React.CSSProperties = { background: "#fff", borderRadius: 16, padding: "1.5rem", boxShadow: "0 2px 12px rgba(0,0,0,.06)" };
const sectionTitle: React.CSSProperties = { color: G, fontSize: "1.1rem", fontWeight: 800, margin: "0 0 0.25rem" };
const sectionDesc: React.CSSProperties = { color: "#6b7280", fontSize: "0.85rem", margin: "0 0 1.25rem", lineHeight: 1.6 };
const fieldLabel: React.CSSProperties = { display: "block", fontSize: "0.85rem", fontWeight: 600, color: "#374151", marginBottom: "0.35rem" };
const fieldInput: React.CSSProperties = { display: "block", width: "100%", padding: "0.6rem 0.85rem", border: "1px solid #d1d5db", borderRadius: 8, fontSize: "0.9rem", boxSizing: "border-box", fontFamily: "sans-serif" };
const badge = (bg: string, color: string): React.CSSProperties => ({ background: bg, color, fontSize: "0.73rem", fontWeight: 600, padding: "0.2rem 0.6rem", borderRadius: 9999, whiteSpace: "nowrap" });
