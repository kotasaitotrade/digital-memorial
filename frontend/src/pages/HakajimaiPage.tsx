import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";

type CheckItem  = { key: string; category: string; label: string; is_done: boolean };
type CostItem   = { key: string; label: string; amount: number; min: number; max: number; note: string };
type GraveInfo  = { cemetery_name: string; address: string; temple_name: string; 住職名: string; temple_phone: string; stone_shop_name: string; stone_shop_phone: string; annual_fee: string; built_year: string; notes: string };

type Plan = {
  id: number;
  kuyou_method: string;
  kuyou_detail: string;
  message_to_family: string;
  checklist_items: CheckItem[];
  cost_items: CostItem[];
  sect: string;
  grave_info: GraveInfo;
};

const KUYOU_OPTIONS = [
  { value: "永代供養墓", icon: "🏛️", desc: "寺院・霊園が永代にわたって供養" },
  { value: "合祀墓",     icon: "🤝", desc: "他の方と一緒に納骨（費用が安い）" },
  { value: "散骨",       icon: "🌊", desc: "海・山などに粉骨して散布" },
  { value: "手元供養",   icon: "🏠", desc: "自宅で手元に置いて供養" },
  { value: "納骨堂",     icon: "🗄️", desc: "施設内のロッカー式スペース" },
  { value: "その他",     icon: "✏️", desc: "上記以外の方法" },
];

const SECTS = ["（宗派未設定）","浄土宗","浄土真宗（本願寺派）","浄土真宗（大谷派）","曹洞宗","臨済宗","真言宗","天台宗","日蓮宗","禅宗","神道","その他"];

// 宗派別のポイント
const SECT_HINTS: Record<string, string[]> = {
  "浄土宗":           ["閉眼供養では「魂抜き」「お性根抜き」と呼びます", "念仏（南無阿弥陀仏）を唱えながら行う場合があります", "お布施の目安: 3〜5万円"],
  "浄土真宗（本願寺派）": ["「魂抜き」は行わず「遷仏法要」と呼びます", "浄土真宗では「魂が宿る」という概念がないため作法が異なります", "お布施の目安: 3〜5万円"],
  "浄土真宗（大谷派）": ["「遷仏法要」を行います", "本山（東本願寺）への分骨を検討する場合があります"],
  "曹洞宗":           ["閉眼供養では「閉眼法要」「お精根抜き」と呼びます", "禅宗のため読経の時間が長い場合があります", "お布施の目安: 3〜10万円"],
  "真言宗":           ["閉眼供養では「魂抜き供養」を行います", "密教系のため独特の作法があります", "お布施の目安: 5〜10万円"],
  "日蓮宗":           ["「お精根抜き」の読経を行います", "戒名（法号）は「院日○○信士/信女」の形式", "お布施の目安: 3〜10万円"],
  "神道":             ["神道では「魂抜き」ではなく「鎮魂祭」を行います", "神職（神主）に依頼します", "玉串料の目安: 3〜5万円"],
};

// 離檀テンプレート
const TEMPLATES = [
  {
    title: "最初の相談電話（宗教者への連絡）",
    body: `お世話になっております。檀家の[あなたの名前]と申します。
このたびお墓のことでご相談がございまして、お電話いたしました。

実は、諸般の事情により、お墓を移転させていただくことを検討しております。
つきましては、一度ご住職にお目にかかってご相談させていただけないでしょうか。

ご都合のよろしい日時をお教えいただけますでしょうか。
よろしくお願いいたします。`
  },
  {
    title: "石材店への見積もり依頼",
    body: `お世話になっております。[あなたの名前]と申します。
[墓地名・住所]にあるお墓の墓じまいを検討しております。

以下についてお見積もりをいただけますでしょうか。
・墓石の撤去・処分
・遺骨の取り出し補助
・墓地の原状回復（更地にする）

墓石の大きさはおよそ[サイズ]です。
ご都合のよろしい日に現地を見ていただくことは可能でしょうか。
どうぞよろしくお願いいたします。`
  },
  {
    title: "役所への改葬許可申請 問い合わせ",
    body: `お世話になっております。[あなたの名前]と申します。
[墓地名・住所]にあるお墓について、改葬を検討しております。

改葬許可申請について確認させてください。
・申請に必要な書類を教えていただけますか？
・窓口はこちらの担当でよろしいでしょうか？
・申請から許可までどのくらいかかりますか？

お忙しいところ恐れ入りますが、よろしくお願いいたします。`
  },
  {
    title: "家族への墓じまい提案（メール・LINE用）",
    body: `みんなに相談があります。

お墓のことですが、私が元気なうちに整理しておきたいと思っています。
[理由: 遠方で管理が難しい / 費用の負担 / 後継ぎがいない など]

具体的には[供養方法]を考えています。費用は[金額]くらいかかる見込みです。

みんなの意見を聞かせてください。都合のよいときに話し合いの場を設けられれば幸いです。`
  },
];

const CATEGORY_ORDER = ["準備", "行政", "供養", "工事", "改葬先"];

const TABS = [
  { id: "method",    label: "供養方法" },
  { id: "grave",     label: "お墓の情報" },
  { id: "checklist", label: "手続き" },
  { id: "cost",      label: "費用" },
  { id: "template",  label: "テンプレート" },
  { id: "message",   label: "家族へ" },
] as const;
type TabId = typeof TABS[number]["id"];

export default function HakajimaiPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [plan, setPlan]     = useState<Plan | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("method");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved]   = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  useEffect(() => {
    api.get("/hakajimai").then((r) => setPlan(r.data));
  }, []);

  const save = useCallback(async (patch: Partial<Plan>) => {
    if (!plan) return;
    setSaving(true);
    const updated = { ...plan, ...patch };
    const r = await api.put("/hakajimai", {
      kuyou_method:      updated.kuyou_method,
      kuyou_detail:      updated.kuyou_detail,
      message_to_family: updated.message_to_family,
      checklist_items:   updated.checklist_items,
      cost_items:        updated.cost_items,
      sect:              updated.sect,
      grave_info:        updated.grave_info,
    });
    setPlan(r.data);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }, [plan]);

  const toggleCheck = (key: string) => {
    if (!plan) return;
    const items = plan.checklist_items.map((it) =>
      it.key === key ? { ...it, is_done: !it.is_done } : it
    );
    save({ checklist_items: items });
  };

  const updateCost = (key: string, amount: number) => {
    if (!plan) return;
    const items = plan.cost_items.map((it) =>
      it.key === key ? { ...it, amount } : it
    );
    setPlan({ ...plan, cost_items: items });
  };

  const updateGrave = (field: keyof GraveInfo, value: string) => {
    if (!plan) return;
    setPlan({ ...plan, grave_info: { ...plan.grave_info, [field]: value } });
  };

  const copyTemplate = (idx: number, body: string) => {
    navigator.clipboard.writeText(body);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  if (!plan) return <div style={s.loading}>読み込み中...</div>;

  const doneCount  = plan.checklist_items.filter((i) => i.is_done).length;
  const totalCount = plan.checklist_items.length;
  const totalCost  = plan.cost_items.reduce((sum, it) => sum + (it.amount || 0), 0);
  const minCost    = plan.cost_items.reduce((sum, it) => sum + (it.min || 0), 0);
  const maxCost    = plan.cost_items.reduce((sum, it) => sum + (it.max || 0), 0);

  const grouped: Record<string, CheckItem[]> = {};
  for (const cat of CATEGORY_ORDER) grouped[cat] = [];
  for (const item of plan.checklist_items) {
    if (!grouped[item.category]) grouped[item.category] = [];
    grouped[item.category].push(item);
  }

  const sectHints = SECT_HINTS[plan.sect] ?? [];

  return (
    <div style={s.page}>
      <div style={s.header}>
        <button onClick={() => navigate("/dashboard")} style={s.back}>← ダッシュボード</button>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          {saving && <span style={s.badge("#6b7280")}>保存中...</span>}
          {saved  && <span style={s.badge("#16a34a")}>保存済み ✓</span>}
          <button onClick={() => { logout(); navigate("/login"); }} style={s.logoutBtn}>ログアウト</button>
        </div>
      </div>

      <div style={s.container}>
        <h1 style={s.title}>⛩️ 墓じまい計画</h1>
        <p style={s.subtitle}>お墓の今後についての希望を整理し、大切な家族に伝えましょう。</p>

        {/* タブ */}
        <div style={s.tabs}>
          {TABS.map((tab) => {
            const extra = tab.id === "checklist" ? ` (${doneCount}/${totalCount})` : "";
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                style={{ ...s.tab, ...(activeTab === tab.id ? s.tabActive : {}) }}>
                {tab.label}{extra}
              </button>
            );
          })}
        </div>

        {/* ── 供養方法 ── */}
        {activeTab === "method" && (
          <div>
            <p style={s.sectionDesc}>希望する供養方法を選んでください。</p>
            <div style={s.methodGrid}>
              {KUYOU_OPTIONS.map((opt) => (
                <button key={opt.value} onClick={() => save({ kuyou_method: opt.value })}
                  style={{ ...s.methodCard, ...(plan.kuyou_method === opt.value ? s.methodCardActive : {}) }}>
                  <span style={{ fontSize: "2rem" }}>{opt.icon}</span>
                  <span style={s.methodLabel}>{opt.value}</span>
                  <span style={s.methodDesc}>{opt.desc}</span>
                </button>
              ))}
            </div>
            {plan.kuyou_method === "その他" && (
              <div style={{ marginTop: "1rem" }}>
                <label style={s.label}>具体的な方法を記入</label>
                <textarea style={s.textarea} rows={3} value={plan.kuyou_detail}
                  onChange={(e) => setPlan({ ...plan, kuyou_detail: e.target.value })}
                  onBlur={() => save({ kuyou_detail: plan.kuyou_detail })}
                  placeholder="例: 樹木葬、宇宙葬、散骨と手元供養を組み合わせる など" />
              </div>
            )}
            {plan.kuyou_method && plan.kuyou_method !== "その他" && (
              <div style={s.selectedBanner}>選択中: <strong>{plan.kuyou_method}</strong></div>
            )}

            {/* 宗派選択 */}
            <div style={{ marginTop: "1.5rem" }}>
              <label style={s.label}>宗派（任意）</label>
              <select style={s.select} value={plan.sect}
                onChange={(e) => save({ sect: e.target.value })}>
                {SECTS.map((s2) => <option key={s2} value={s2 === "（宗派未設定）" ? "" : s2}>{s2}</option>)}
              </select>
              {sectHints.length > 0 && (
                <div style={s.hintBox}>
                  <p style={s.hintTitle}>🔔 {plan.sect} の手続きポイント</p>
                  {sectHints.map((h, i) => <p key={i} style={s.hintItem}>・{h}</p>)}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── お墓の情報 ── */}
        {activeTab === "grave" && (
          <div>
            <p style={s.sectionDesc}>現在のお墓の情報を記録しておきましょう。家族が手続きを進める際の大切な手がかりになります。</p>
            <div style={s.graveGrid}>
              {([
                ["cemetery_name", "墓地・霊園名",     "〇〇市営霊園"],
                ["address",       "墓地の住所",        "〇〇県〇〇市〇〇町1-1"],
                ["temple_name",   "菩提寺名",          "〇〇寺"],
                ["住職名",        "住職のお名前",       "〇〇 〇〇 様"],
                ["temple_phone",  "寺院・霊園の電話",  "000-0000-0000"],
                ["stone_shop_name","石材店名",         "〇〇石材店"],
                ["stone_shop_phone","石材店の電話",    "000-0000-0000"],
                ["annual_fee",    "年間管理費",         "例: 10,000円"],
                ["built_year",    "墓石建立年",         "例: 1980年"],
              ] as [keyof GraveInfo, string, string][]).map(([field, label, ph]) => (
                <div key={field}>
                  <label style={s.label}>{label}</label>
                  <input style={s.input} type="text" placeholder={ph}
                    value={(plan.grave_info as Record<string, string>)[field] ?? ""}
                    onChange={(e) => updateGrave(field, e.target.value)}
                    onBlur={() => save({ grave_info: plan.grave_info })} />
                </div>
              ))}
              <div style={{ gridColumn: "1/-1" }}>
                <label style={s.label}>備考・メモ</label>
                <textarea style={s.textarea} rows={3}
                  value={plan.grave_info.notes}
                  onChange={(e) => updateGrave("notes", e.target.value)}
                  onBlur={() => save({ grave_info: plan.grave_info })}
                  placeholder="その他、引き継いでほしい情報を自由に" />
              </div>
            </div>
          </div>
        )}

        {/* ── 手続きチェックリスト ── */}
        {activeTab === "checklist" && (
          <div>
            <p style={s.sectionDesc}>墓じまいに必要な手続きを順番に進めましょう。</p>
            <div style={s.progressBar}>
              <div style={{ ...s.progressFill, width: `${totalCount ? (doneCount / totalCount) * 100 : 0}%` }} />
            </div>
            <p style={{ textAlign: "center", fontSize: "0.85rem", color: "#6b7280", margin: "0.5rem 0 1.5rem" }}>
              {doneCount} / {totalCount} 完了
            </p>
            {CATEGORY_ORDER.filter((cat) => grouped[cat]?.length > 0).map((cat) => (
              <div key={cat} style={{ marginBottom: "1.5rem" }}>
                <h3 style={s.catLabel}>{cat}</h3>
                {grouped[cat].map((item) => (
                  <label key={item.key} style={s.checkRow}>
                    <input type="checkbox" checked={item.is_done} onChange={() => toggleCheck(item.key)}
                      style={{ width: 18, height: 18, accentColor: "#1a5c38", cursor: "pointer" }} />
                    <span style={{ ...s.checkLabel, ...(item.is_done ? s.checkDone : {}) }}>{item.label}</span>
                  </label>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* ── 費用シミュレーター ── */}
        {activeTab === "cost" && (
          <div>
            <p style={s.sectionDesc}>各費用の金額を実態に合わせて編集できます。</p>
            <div style={s.costTable}>
              {plan.cost_items.map((item) => (
                <div key={item.key} style={s.costRow}>
                  <div style={{ flex: 1 }}>
                    <div style={s.costLabel}>{item.label}</div>
                    <div style={s.costNote}>{item.note}</div>
                    <div style={s.costRange}>
                      最安 {(item.min || 0).toLocaleString()}円 〜 最高 {(item.max || 0).toLocaleString()}円
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                    <input type="number" value={item.amount}
                      onChange={(e) => updateCost(item.key, Number(e.target.value))}
                      onBlur={() => save({ cost_items: plan.cost_items })}
                      style={s.costInput} min={0} step={1000} />
                    <span style={{ color: "#6b7280", fontSize: "0.85rem" }}>円</span>
                  </div>
                </div>
              ))}
            </div>
            <div style={s.totalRow}>
              <div>
                <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>最安見込み: {minCost.toLocaleString()}円 〜 最高: {maxCost.toLocaleString()}円</div>
                <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#1a5c38" }}>あなたの目安: {totalCost.toLocaleString()} 円</div>
              </div>
            </div>
          </div>
        )}

        {/* ── テンプレート集 ── */}
        {activeTab === "template" && (
          <div>
            <p style={s.sectionDesc}>菩提寺・石材店・家族への連絡に使えるテンプレートです。コピーして自由に編集してください。</p>
            {TEMPLATES.map((tpl, idx) => (
              <div key={idx} style={s.tplCard}>
                <div style={s.tplHeader}>
                  <span style={s.tplTitle}>{tpl.title}</span>
                  <button style={{ ...s.copyBtn, ...(copiedIdx === idx ? s.copyBtnDone : {}) }}
                    onClick={() => copyTemplate(idx, tpl.body)}>
                    {copiedIdx === idx ? "✓ コピー済み" : "📋 コピー"}
                  </button>
                </div>
                <pre style={s.tplBody}>{tpl.body}</pre>
              </div>
            ))}
          </div>
        )}

        {/* ── 家族へのメッセージ ── */}
        {activeTab === "message" && (
          <div>
            <p style={s.sectionDesc}>墓じまいについて、家族へ伝えたいことを書いておきましょう。供養方法の理由や気持ちなど自由に記入できます。</p>
            <textarea style={{ ...s.textarea, minHeight: 240 }}
              value={plan.message_to_family}
              onChange={(e) => setPlan({ ...plan, message_to_family: e.target.value })}
              onBlur={() => save({ message_to_family: plan.message_to_family })}
              placeholder={"例: 先祖代々のお墓を守るのは大変だと思うので、永代供養にしてもらえると助かります。\n費用については生命保険で賄えるように準備してあります。\nみんなが楽になることを優先してください。"} />
            <p style={{ fontSize: "0.8rem", color: "#9ca3af", marginTop: "0.5rem" }}>入力欄をクリックすると自動保存されます</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── スタイル ──────────────────────────────────────────────
const s = {
  page:      { minHeight: "100vh", background: "#f8faf8", fontFamily: "sans-serif" },
  loading:   { display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", color: "#6b7280" },
  header:    { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem 1.25rem", background: "#fff", borderBottom: "1px solid #e5e7eb", position: "sticky" as const, top: 0, zIndex: 10 },
  back:      { background: "none", border: "none", color: "#1a5c38", cursor: "pointer", fontSize: "0.9rem", fontWeight: 600 },
  badge:     (bg: string) => ({ background: bg, color: "#fff", padding: "0.2rem 0.6rem", borderRadius: 9999, fontSize: "0.78rem", fontWeight: 600 }),
  logoutBtn: { background: "none", border: "1px solid #d1d5db", color: "#6b7280", borderRadius: 6, padding: "0.3rem 0.7rem", cursor: "pointer", fontSize: "0.85rem" },
  container: { maxWidth: 680, margin: "0 auto", padding: "1.5rem 1rem 3rem" },
  title:     { fontSize: "1.5rem", fontWeight: 700, color: "#1a3a28", margin: 0 },
  subtitle:  { color: "#6b7280", fontSize: "0.9rem", marginTop: "0.4rem", marginBottom: "1.5rem" },
  tabs:      { display: "flex", gap: "0.15rem", marginBottom: "1.5rem", borderBottom: "2px solid #e5e7eb", paddingBottom: 0, flexWrap: "wrap" as const },
  tab:       { background: "none", border: "none", padding: "0.55rem 0.75rem", cursor: "pointer", color: "#6b7280", fontSize: "0.85rem", fontWeight: 500, borderBottom: "2px solid transparent", marginBottom: -2 },
  tabActive: { color: "#1a5c38", borderBottomColor: "#1a5c38", fontWeight: 700 },
  sectionDesc: { color: "#6b7280", fontSize: "0.88rem", marginBottom: "1.25rem" },
  methodGrid:  { display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.75rem" },
  methodCard:  { display: "flex", flexDirection: "column" as const, alignItems: "center", gap: "0.4rem", padding: "1rem 0.75rem", border: "2px solid #e5e7eb", borderRadius: 12, background: "#fff", cursor: "pointer", transition: "all 0.15s" },
  methodCardActive: { borderColor: "#1a5c38", background: "#f0f9f4", boxShadow: "0 0 0 3px rgba(26,92,56,.15)" },
  methodLabel: { fontWeight: 700, color: "#1a3a28", fontSize: "0.95rem" },
  methodDesc:  { color: "#6b7280", fontSize: "0.78rem", textAlign: "center" as const },
  selectedBanner: { marginTop: "1rem", padding: "0.75rem 1rem", background: "#f0f9f4", border: "1px solid #a7d7b9", borderRadius: 8, color: "#1a5c38", fontSize: "0.9rem" },
  select:    { width: "100%", padding: "0.6rem 0.75rem", border: "1px solid #d1d5db", borderRadius: 8, fontSize: "0.9rem", background: "#fff", marginBottom: "0.75rem" },
  hintBox:   { background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 8, padding: "0.75rem 1rem" },
  hintTitle: { fontWeight: 700, color: "#92400e", fontSize: "0.88rem", margin: "0 0 0.4rem" },
  hintItem:  { color: "#78350f", fontSize: "0.85rem", margin: "0.2rem 0" },
  graveGrid: { display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.75rem" },
  label:     { display: "block", fontWeight: 600, color: "#374151", marginBottom: "0.3rem", fontSize: "0.88rem" },
  input:     { width: "100%", padding: "0.6rem 0.75rem", border: "1px solid #d1d5db", borderRadius: 8, fontSize: "0.9rem", boxSizing: "border-box" as const },
  textarea:  { width: "100%", padding: "0.75rem", border: "1px solid #d1d5db", borderRadius: 8, fontSize: "0.9rem", lineHeight: 1.6, resize: "vertical" as const, boxSizing: "border-box" as const },
  progressBar: { height: 8, background: "#e5e7eb", borderRadius: 9999, overflow: "hidden" },
  progressFill: { height: "100%", background: "#1a5c38", borderRadius: 9999, transition: "width 0.3s" },
  catLabel:  { fontSize: "0.78rem", fontWeight: 700, color: "#6b7280", textTransform: "uppercase" as const, letterSpacing: "0.05em", margin: "0 0 0.5rem", borderLeft: "3px solid #1a5c38", paddingLeft: "0.5rem" },
  checkRow:  { display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.6rem 0.75rem", background: "#fff", borderRadius: 8, marginBottom: "0.4rem", cursor: "pointer" },
  checkLabel: { fontSize: "0.9rem", color: "#1a3a28" },
  checkDone:  { textDecoration: "line-through" as const, color: "#9ca3af" },
  costTable: { display: "flex", flexDirection: "column" as const, gap: "0.5rem" },
  costRow:   { display: "flex", alignItems: "center", gap: "1rem", padding: "0.75rem 1rem", background: "#fff", borderRadius: 8 },
  costLabel: { fontWeight: 600, color: "#1a3a28", fontSize: "0.9rem" },
  costNote:  { color: "#9ca3af", fontSize: "0.75rem", marginTop: "0.1rem" },
  costRange: { color: "#6b7280", fontSize: "0.75rem", marginTop: "0.15rem" },
  costInput: { width: 110, padding: "0.35rem 0.5rem", border: "1px solid #d1d5db", borderRadius: 6, fontSize: "0.9rem", textAlign: "right" as const },
  totalRow:  { padding: "1rem", marginTop: "0.75rem", background: "#f0f9f4", border: "1px solid #a7d7b9", borderRadius: 8 },
  tplCard:   { background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, marginBottom: "1rem", overflow: "hidden" },
  tplHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem 1rem", background: "#f9fafb", borderBottom: "1px solid #e5e7eb" },
  tplTitle:  { fontWeight: 700, color: "#1a3a28", fontSize: "0.9rem" },
  copyBtn:   { background: "#1a5c38", color: "#fff", border: "none", borderRadius: 6, padding: "0.3rem 0.75rem", cursor: "pointer", fontSize: "0.82rem", fontWeight: 600 },
  copyBtnDone: { background: "#16a34a" },
  tplBody:   { padding: "1rem", fontSize: "0.85rem", color: "#374151", whiteSpace: "pre-wrap" as const, lineHeight: 1.7, margin: 0, fontFamily: "inherit" },
};
