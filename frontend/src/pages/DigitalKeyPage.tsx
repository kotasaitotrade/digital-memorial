import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";

const GREEN = "#1a5c38";

interface TrustedPerson {
  id: number;
  name: string;
  email: string;
  access_scope: string[];
  access_token: string;
  has_requested: boolean;
  requested_at: string | null;
  email_verified: boolean;
  created_at: string;
}

interface DigitalKey {
  id: number;
  unlock_condition: string;
  is_unlocked: boolean;
  unlocked_at: string | null;
  notes: string | null;
  trusted_persons: TrustedPerson[];
}

const ACCESS_SCOPE_LABELS: Record<string, string> = {
  all: "すべてのデータ",
  estate: "相続情報のみ",
  ending_note: "エンディングノートのみ",
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

  useEffect(() => {
    api.get("/digital-key").then((r) => setKey(r.data));
  }, []);

  const updateCondition = async (val: string) => {
    setSaving(true);
    const r = await api.patch("/digital-key", { unlock_condition: val });
    setKey(r.data);
    setSaving(false);
  };

  const updateNotes = async (val: string) => {
    const r = await api.patch("/digital-key", { notes: val });
    setKey(r.data);
  };

  const addPerson = async () => {
    if (!form.name || !form.email) return;
    const r = await api.post("/digital-key/trusted-persons", form);
    setKey((prev) => prev ? { ...prev, trusted_persons: [...prev.trusted_persons, r.data] } : prev);
    setForm({ name: "", email: "", access_scope: ["all"] });
    setShowForm(false);
  };

  const deletePerson = async (id: number) => {
    if (!confirm("この信頼者を削除しますか？")) return;
    await api.delete(`/digital-key/trusted-persons/${id}`);
    setKey((prev) => prev ? { ...prev, trusted_persons: prev.trusted_persons.filter((p) => p.id !== id) } : prev);
  };

  const copyToken = (person: TrustedPerson) => {
    const url = `${window.location.origin}/unlock/${person.id}?token=${person.access_token}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(person.id);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  if (!key) return <div style={{ textAlign: "center", padding: "4rem", color: "#6b6b6b" }}>読み込み中...</div>;

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f0" }}>
      {/* ヘッダー */}
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

      <main style={{ maxWidth: "760px", margin: "0 auto", padding: "2rem 1rem" }}>
        <h1 style={{ color: GREEN, fontSize: "1.6rem", marginBottom: "0.5rem" }}>🔐 デジタル遺品鍵</h1>
        <p style={{ color: "#555", marginBottom: "2rem", lineHeight: 1.7 }}>
          死後に信頼者（家族など）があなたの終活データにアクセスできるよう、あらかじめ受取人と解除条件を設定します。
          信頼者には解除キーURLを共有してください。
        </p>

        {key.is_unlocked && (
          <div style={{ background: "#fff3cd", border: "1px solid #ffc107", borderRadius: "8px", padding: "1rem 1.5rem", marginBottom: "2rem" }}>
            <strong>🔓 開錠済み</strong>
            <p style={{ margin: "0.25rem 0 0", fontSize: "0.9rem", color: "#856404" }}>
              {key.unlocked_at ? new Date(key.unlocked_at).toLocaleString("ja-JP") : ""} に開錠されました。
              信頼者がデータにアクセスできる状態です。
            </p>
          </div>
        )}

        {/* 開錠条件 */}
        <section style={{ background: "white", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
          <h2 style={{ color: GREEN, fontSize: "1.1rem", marginTop: 0 }}>開錠条件</h2>
          <p style={{ color: "#666", fontSize: "0.9rem", marginBottom: "1rem" }}>何名の信頼者が申請したら開錠するかを設定します。</p>
          {saving && <span style={{ color: "#888", fontSize: "0.8rem" }}>保存中...</span>}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {[
              { value: "one_request", label: "1名の申請で開錠", desc: "信頼者のうち1名が申請すれば即座に開錠します" },
              { value: "two_requests", label: "2名以上の申請で開錠", desc: "2名以上が申請して初めて開錠します（不正防止）" },
            ].map((opt) => (
              <label key={opt.value} style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem", cursor: "pointer", padding: "0.75rem 1rem", borderRadius: "8px", border: `2px solid ${key.unlock_condition === opt.value ? GREEN : "#e0e0e0"}`, background: key.unlock_condition === opt.value ? "#f0f7f4" : "white" }}>
                <input type="radio" name="unlock" value={opt.value} checked={key.unlock_condition === opt.value} onChange={() => updateCondition(opt.value)} style={{ marginTop: "2px" }} />
                <div>
                  <div style={{ fontWeight: 600, color: "#222" }}>{opt.label}</div>
                  <div style={{ fontSize: "0.82rem", color: "#666" }}>{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>

          <label style={{ display: "block", marginTop: "1.25rem" }}>
            <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "#444" }}>メモ・備考</span>
            <textarea
              defaultValue={key.notes || ""}
              onBlur={(e) => updateNotes(e.target.value)}
              rows={3}
              style={{ width: "100%", marginTop: "0.5rem", padding: "0.6rem", border: "1px solid #ccc", borderRadius: "6px", fontSize: "0.9rem", resize: "vertical", boxSizing: "border-box" }}
              placeholder="信頼者への伝言・注意事項など"
            />
          </label>
        </section>

        {/* 信頼者一覧 */}
        <section style={{ background: "white", borderRadius: "12px", padding: "1.5rem", marginBottom: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ color: GREEN, fontSize: "1.1rem", margin: 0 }}>信頼者（受取人） {key.trusted_persons.length}/3</h2>
            {key.trusted_persons.length < 3 && (
              <button onClick={() => setShowForm(true)} style={{ background: GREEN, color: "white", border: "none", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.9rem" }}>
                + 追加
              </button>
            )}
          </div>
          <p style={{ color: "#666", fontSize: "0.85rem", marginBottom: "1rem" }}>
            解除キーURLを信頼者に共有してください。信頼者はそのURLにアクセスするだけで開錠を申請できます。
          </p>

          {key.trusted_persons.length === 0 && (
            <div style={{ textAlign: "center", padding: "2rem", color: "#aaa", fontSize: "0.9rem" }}>
              まだ信頼者が登録されていません
            </div>
          )}

          {key.trusted_persons.map((p) => (
            <div key={p.id} style={{ border: "1px solid #e8e8e8", borderRadius: "8px", padding: "1rem", marginBottom: "0.75rem", background: p.has_requested ? "#f0f7f4" : "white" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                <div>
                  <span style={{ fontWeight: 700, color: "#222" }}>{p.name}</span>
                  <span style={{ color: "#666", fontSize: "0.85rem", marginLeft: "0.75rem" }}>{p.email}</span>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  {p.has_requested && <span style={{ background: "#d4edda", color: "#155724", fontSize: "0.75rem", padding: "0.2rem 0.6rem", borderRadius: "12px" }}>申請済み</span>}
                  <button onClick={() => deletePerson(p.id)} style={{ background: "none", border: "1px solid #ddd", color: "#e74c3c", padding: "0.2rem 0.6rem", borderRadius: "4px", cursor: "pointer", fontSize: "0.8rem" }}>削除</button>
                </div>
              </div>
              <div style={{ fontSize: "0.82rem", color: "#666", marginBottom: "0.5rem" }}>
                アクセス範囲: {p.access_scope.map((s) => ACCESS_SCOPE_LABELS[s] || s).join("・")}
              </div>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <button onClick={() => setTokenVisible((prev) => ({ ...prev, [p.id]: !prev[p.id] }))} style={{ background: "#f0f0f0", border: "none", padding: "0.3rem 0.7rem", borderRadius: "4px", cursor: "pointer", fontSize: "0.82rem" }}>
                  {tokenVisible[p.id] ? "URLを隠す" : "解除キーURLを表示"}
                </button>
                <button onClick={() => copyToken(p)} style={{ background: copied === p.id ? GREEN : "#e8f5e9", border: "none", padding: "0.3rem 0.7rem", borderRadius: "4px", cursor: "pointer", fontSize: "0.82rem", color: copied === p.id ? "white" : GREEN }}>
                  {copied === p.id ? "コピー済み!" : "URLをコピー"}
                </button>
              </div>
              {tokenVisible[p.id] && (
                <div style={{ marginTop: "0.5rem", background: "#f8f8f8", padding: "0.6rem", borderRadius: "6px", fontSize: "0.78rem", wordBreak: "break-all", color: "#333", fontFamily: "monospace" }}>
                  {`${window.location.origin}/unlock/${p.id}?token=${p.access_token}`}
                </div>
              )}
            </div>
          ))}

          {showForm && (
            <div style={{ border: `2px solid ${GREEN}`, borderRadius: "8px", padding: "1.25rem", marginTop: "1rem", background: "#f0f7f4" }}>
              <h3 style={{ margin: "0 0 1rem", color: GREEN, fontSize: "1rem" }}>信頼者を追加</h3>
              <div style={{ display: "grid", gap: "0.75rem" }}>
                <label>
                  <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>名前</span>
                  <input value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} style={{ display: "block", width: "100%", marginTop: "0.25rem", padding: "0.5rem", border: "1px solid #ccc", borderRadius: "6px", boxSizing: "border-box" }} placeholder="山田 太郎" />
                </label>
                <label>
                  <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>メールアドレス</span>
                  <input type="email" value={form.email} onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))} style={{ display: "block", width: "100%", marginTop: "0.25rem", padding: "0.5rem", border: "1px solid #ccc", borderRadius: "6px", boxSizing: "border-box" }} placeholder="taro@example.com" />
                </label>
                <label>
                  <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>アクセス範囲</span>
                  <select value={form.access_scope[0]} onChange={(e) => setForm((p) => ({ ...p, access_scope: [e.target.value] }))} style={{ display: "block", width: "100%", marginTop: "0.25rem", padding: "0.5rem", border: "1px solid #ccc", borderRadius: "6px", boxSizing: "border-box" }}>
                    <option value="all">すべてのデータ</option>
                    <option value="estate">相続情報のみ</option>
                    <option value="ending_note">エンディングノートのみ</option>
                  </select>
                </label>
              </div>
              <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
                <button onClick={addPerson} style={{ background: GREEN, color: "white", border: "none", padding: "0.5rem 1.5rem", borderRadius: "6px", cursor: "pointer", fontWeight: 600 }}>登録</button>
                <button onClick={() => { setShowForm(false); setForm({ name: "", email: "", access_scope: ["all"] }); }} style={{ background: "white", border: "1px solid #ccc", padding: "0.5rem 1.5rem", borderRadius: "6px", cursor: "pointer" }}>キャンセル</button>
              </div>
            </div>
          )}
        </section>

        {/* 使い方ガイド */}
        <section style={{ background: "#fffde7", border: "1px solid #f9c74f", borderRadius: "12px", padding: "1.5rem" }}>
          <h2 style={{ color: "#7a6000", fontSize: "1rem", margin: "0 0 0.75rem" }}>📖 使い方</h2>
          <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "#5a4500", fontSize: "0.88rem", lineHeight: 1.8 }}>
            <li>信頼者（家族など）を最大3名登録します</li>
            <li>解除キーURLをコピーして、信頼者に伝えておきます（メール・メモなど）</li>
            <li>あなたが亡くなった後、信頼者がそのURLにアクセスして申請します</li>
            <li>設定した条件（1名 or 2名以上）を満たすと自動的に開錠されます</li>
            <li>開錠後、信頼者はあなたの終活データを閲覧できます（読み取り専用）</li>
          </ol>
        </section>
      </main>
    </div>
  );
}
