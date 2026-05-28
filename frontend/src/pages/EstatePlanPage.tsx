import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";
import type { EstatePlan, FamilyMember, Asset, InheritanceCalculation, HeirResult } from "../types";

const REL_LABELS: Record<string, string> = {
  spouse: "配偶者", child: "子", grandchild: "孫（代襲）",
  parent: "親", grandparent: "祖父母", sibling: "兄弟姉妹", nephew_niece: "甥・姪（代襲）",
};
const ASSET_TYPE_LABELS: Record<string, string> = {
  real_estate: "不動産", bank_account: "預貯金", securities: "有価証券",
  life_insurance: "生命保険金", retirement: "退職金", other: "その他資産", debt: "負債",
};

// ─────────────────────────────────────────────────
// メインページ（相続計画一覧）
// ─────────────────────────────────────────────────
export default function EstatePlanListPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [plans, setPlans] = useState<EstatePlan[]>([]);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("自分の相続計画");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  useEffect(() => {
    api.get("/estate-plans").then((r) => setPlans(r.data));
  }, []);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    const r = await api.post("/estate-plans", { title: newTitle.trim() });
    navigate(`/estate/${r.data.id}/family`);
  };
  const handleDelete = async (id: number) => {
    if (!confirm("この相続計画を削除しますか？")) return;
    await api.delete(`/estate-plans/${id}`);
    setPlans((p) => p.filter((x) => x.id !== id));
  };
  const startEdit = (plan: EstatePlan) => {
    setEditingId(plan.id);
    setEditingTitle(plan.title);
  };
  const saveEdit = async (id: number) => {
    if (!editingTitle.trim()) return;
    const r = await api.patch(`/estate-plans/${id}`, { title: editingTitle.trim() });
    setPlans((p) => p.map((x) => x.id === id ? r.data : x));
    setEditingId(null);
  };

  return (
    <div style={s.page}>
      <Header user={user} logout={() => { logout(); navigate("/login"); }} />
      <main style={s.main}>
        <div style={s.titleRow}>
          <div>
            <h1 style={s.pageTitle}>相続の棚卸し</h1>
            <p style={s.pageSub}>家族構成を入力して、法定相続人と相続分を確認しましょう</p>
          </div>
          <button style={s.primaryBtn} onClick={() => setCreating(true)}>＋ 新規作成</button>
        </div>

        {creating && (
          <div style={s.createBox}>
            <input
              style={s.input} value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="計画名（例：自分の相続計画）"
            />
            <button style={s.primaryBtn} onClick={handleCreate}>作成して開始</button>
            <button style={s.ghostBtn} onClick={() => setCreating(false)}>キャンセル</button>
          </div>
        )}

        {plans.length === 0 && !creating ? (
          <div style={s.empty}>
            <div style={{ fontSize: "3rem", marginBottom: 12 }}>⚖️</div>
            <p style={{ color: "#6b7280" }}>相続計画がありません。「新規作成」から始めましょう。</p>
          </div>
        ) : (
          <div style={s.cardGrid}>
            {plans.map((plan) => (
              <div key={plan.id} style={s.card}>
                {editingId === plan.id ? (
                  <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                    <input
                      data-testid="rename-input"
                      style={{ ...s.input, flex: 1, padding: "0.35rem 0.6rem", fontSize: "0.9rem" }}
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") saveEdit(plan.id); if (e.key === "Escape") setEditingId(null); }}
                      autoFocus
                    />
                    <button style={s.primaryBtn} onClick={() => saveEdit(plan.id)}>保存</button>
                    <button style={s.ghostBtn} onClick={() => setEditingId(null)}>✕</button>
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <div style={s.cardTitle}>{plan.title}</div>
                    <button style={s.iconBtn} onClick={() => startEdit(plan)} title="名前を変更">✏️</button>
                  </div>
                )}
                <div style={s.cardMeta}>
                  家族: {plan.family_members.length}名 ／ 財産: {plan.assets.length}件
                </div>
                <div style={s.cardMeta}>更新: {new Date(plan.updated_at ?? plan.created_at).toLocaleDateString("ja-JP")}</div>
                <div style={s.cardActions}>
                  <Link to={`/estate/${plan.id}/family`} style={s.actionBtn}>家族構成</Link>
                  <Link to={`/estate/${plan.id}/assets`} style={s.actionBtn}>財産</Link>
                  <Link to={`/estate/${plan.id}/result`} style={{ ...s.actionBtn, ...s.actionBtnPrimary }}>結果を見る</Link>
                  <button style={s.deleteBtn} onClick={() => handleDelete(plan.id)}>削除</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 家族構成入力ページ
// ─────────────────────────────────────────────────
export function FamilyInputPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { planId } = useParams<{ planId: string }>();
  const [members, setMembers] = useState<Partial<FamilyMember>[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get(`/estate-plans/${planId}/family`).then((r) => {
      if (r.data.length > 0) {
        // parent_member_id は DB ID で保存されているが、ドロップダウンは配列インデックスを使う。
        // ロード時に DB ID → インデックスへ変換する。
        const loaded: Partial<FamilyMember>[] = r.data;
        const withIdx = loaded.map((m) => {
          if (m.parent_member_id != null) {
            const parentIdx = loaded.findIndex((p) => p.id === m.parent_member_id);
            return { ...m, parent_member_id: parentIdx >= 0 ? parentIdx : undefined };
          }
          return m;
        });
        setMembers(withIdx);
      }
    });
  }, [planId]);

  const addMember = (rel: FamilyMember["relationship"]) => {
    setMembers((p) => [...p, {
      relationship: rel, name: "", is_alive: true,
      is_adopted: false, is_half_blood: false,
      has_renounced: false, is_disqualified: false,
    }]);
  };
  const update = (idx: number, key: string, val: unknown) => {
    setMembers((p) => p.map((m, i) => i === idx ? { ...m, [key]: val } : m));
  };
  const remove = (idx: number) => setMembers((p) => p.filter((_, i) => i !== idx));

  const save = async () => {
    setSaving(true);
    await api.post(`/estate-plans/${planId}/family`, { members });
    setSaving(false);
    navigate(`/estate/${planId}/assets`);
  };

  const byRel = (rel: string) => members.map((m, i) => ({ m, i })).filter(({ m }) => m.relationship === rel);

  return (
    <div style={s.page}>
      <Header user={user} logout={() => { logout(); navigate("/login"); }} backTo={`/estate`} backLabel="← 相続計画一覧" />
      <main style={s.main}>
        <div style={s.wizardHeader}>
          <div style={{ ...s.wizardStep, ...s.wizardStepActive }}>① 家族構成</div>
          <div style={s.wizardArrow}>→</div>
          <div style={s.wizardStep}>② 財産の棚卸し</div>
          <div style={s.wizardArrow}>→</div>
          <div style={s.wizardStep}>③ 計算結果</div>
        </div>

        <h2 style={s.pageTitle}>家族構成を入力してください</h2>

        {/* 配偶者 */}
        <Section title="配偶者">
          {byRel("spouse").length === 0 ? (
            <button style={s.addMemberBtn} onClick={() => addMember("spouse")}>＋ 配偶者を追加</button>
          ) : byRel("spouse").map(({ m, i }) => (
            <MemberRow key={i} m={m} idx={i} onUpdate={update} onRemove={remove} showHalfBlood={false} showAdopted={false} />
          ))}
        </Section>

        {/* 子 */}
        <Section title="お子様">
          {byRel("child").map(({ m, i }) => (
            <MemberRow key={i} m={m} idx={i} onUpdate={update} onRemove={remove} showAdopted={true} showHalfBlood={false} />
          ))}
          <button style={s.addMemberBtn} onClick={() => addMember("child")}>＋ 子どもを追加</button>
        </Section>

        {/* 孫（代襲） */}
        {byRel("child").some(({ m }) => !m.is_alive || m.is_disqualified) && (
          <Section title="孫（代襲相続）" note="亡くなった・欠格のお子様がいる場合に入力">
            {byRel("grandchild").map(({ m, i }) => (
              <MemberRow key={i} m={m} idx={i} onUpdate={update} onRemove={remove} showAdopted={false} showHalfBlood={false}
                parentOptions={byRel("child").map(({ m: pm, i: pi }) => ({ id: pi, name: pm.name || `子${pi + 1}` }))}
              />
            ))}
            <button style={s.addMemberBtn} onClick={() => addMember("grandchild")}>＋ 孫を追加</button>
          </Section>
        )}

        {/* 親 */}
        <Section title="ご両親" note="お子様がいない場合に相続人になります">
          {byRel("parent").map(({ m, i }) => (
            <MemberRow key={i} m={m} idx={i} onUpdate={update} onRemove={remove} showAdopted={false} showHalfBlood={false} />
          ))}
          <button style={s.addMemberBtn} onClick={() => addMember("parent")}>＋ 親を追加</button>
        </Section>

        {/* 祖父母 */}
        <Section title="祖父母" note="親が全員お亡くなりの場合に相続人になります">
          {byRel("grandparent").map(({ m, i }) => (
            <MemberRow key={i} m={m} idx={i} onUpdate={update} onRemove={remove} showAdopted={false} showHalfBlood={false} />
          ))}
          <button style={s.addMemberBtn} onClick={() => addMember("grandparent")}>＋ 祖父母を追加</button>
        </Section>

        {/* 兄弟姉妹 */}
        <Section title="ご兄弟姉妹" note="お子様・ご両親ともにいない場合に相続人になります">
          {byRel("sibling").map(({ m, i }) => (
            <MemberRow key={i} m={m} idx={i} onUpdate={update} onRemove={remove} showAdopted={false} showHalfBlood={true} />
          ))}
          <button style={s.addMemberBtn} onClick={() => addMember("sibling")}>＋ 兄弟姉妹を追加</button>
        </Section>

        <div style={s.btnRow}>
          <button style={s.primaryBtn} onClick={save} disabled={saving}>
            {saving ? "保存中..." : "保存して次へ（財産の棚卸し）→"}
          </button>
        </div>
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 財産入力ページ
// ─────────────────────────────────────────────────
export function AssetInputPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { planId } = useParams<{ planId: string }>();
  const [assets, setAssets] = useState<Partial<Asset>[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get(`/estate-plans/${planId}/assets`).then((r) => {
      if (r.data.length > 0) setAssets(r.data);
    });
  }, [planId]);

  const add = (type: Asset["asset_type"]) => {
    setAssets((p) => [...p, { asset_type: type, name: "", estimated_value: 0, is_deemed_estate: false }]);
  };
  const update = (idx: number, key: string, val: unknown) => {
    setAssets((p) => p.map((a, i) => i === idx ? { ...a, [key]: val } : a));
  };
  const remove = (idx: number) => setAssets((p) => p.filter((_, i) => i !== idx));
  const save = async () => {
    setSaving(true);
    await api.post(`/estate-plans/${planId}/assets`, { assets });
    setSaving(false);
    navigate(`/estate/${planId}/result`);
  };

  const totalAssets = assets.filter(a => (a.estimated_value ?? 0) > 0).reduce((s, a) => s + (a.estimated_value ?? 0), 0);
  const totalDebts = assets.filter(a => (a.estimated_value ?? 0) < 0).reduce((s, a) => s + (a.estimated_value ?? 0), 0);
  const netEstate = totalAssets + totalDebts;

  return (
    <div style={s.page}>
      <Header user={user} logout={() => { logout(); navigate("/login"); }} backTo={`/estate/${planId}/family`} backLabel="← 家族構成" />
      <main style={s.main}>
        <div style={s.wizardHeader}>
          <div style={s.wizardStep}>① 家族構成</div>
          <div style={s.wizardArrow}>→</div>
          <div style={{ ...s.wizardStep, ...s.wizardStepActive }}>② 財産の棚卸し</div>
          <div style={s.wizardArrow}>→</div>
          <div style={s.wizardStep}>③ 計算結果</div>
        </div>

        <h2 style={s.pageTitle}>財産・負債を入力してください</h2>
        <p style={s.pageSub}>おおよその金額で構いません。正確な評価は専門家にご相談ください。</p>

        {/* 資産 */}
        {["real_estate", "bank_account", "securities", "life_insurance", "retirement", "other"].map((type) => {
          const typeAssets = assets.map((a, i) => ({ a, i })).filter(({ a }) => a.asset_type === type);
          return (
            <Section key={type} title={`${ASSET_TYPE_LABELS[type]}`}>
              {typeAssets.map(({ a, i }) => (
                <AssetRow key={i} a={a} idx={i} onUpdate={update} onRemove={remove} />
              ))}
              <button style={s.addMemberBtn} onClick={() => add(type as Asset["asset_type"])}>
                ＋ {ASSET_TYPE_LABELS[type]}を追加
              </button>
            </Section>
          );
        })}

        {/* 負債 */}
        <Section title="負債（住宅ローン・借入金など）">
          {assets.map((a, i) => ({ a, i })).filter(({ a }) => a.asset_type === "debt").map(({ a, i }) => (
            <AssetRow key={i} a={a} idx={i} onUpdate={update} onRemove={remove} isDebt />
          ))}
          <button style={s.addMemberBtn} onClick={() => add("debt")}>＋ 負債を追加</button>
        </Section>

        {/* 合計 */}
        <div style={s.totalBox}>
          <div style={s.totalRow}><span>資産合計</span><span style={{ color: "#1a5c38" }}>{totalAssets.toLocaleString()}円</span></div>
          <div style={s.totalRow}><span>負債合計</span><span style={{ color: "#dc2626" }}>{Math.abs(totalDebts).toLocaleString()}円</span></div>
          <div style={{ ...s.totalRow, fontWeight: 700, fontSize: "1.1rem", borderTop: "1px solid #e5e7eb", paddingTop: 8 }}>
            <span>正味遺産額</span>
            <span style={{ color: netEstate >= 0 ? "#1a5c38" : "#dc2626" }}>{netEstate.toLocaleString()}円</span>
          </div>
        </div>

        <div style={s.btnRow}>
          <button style={s.primaryBtn} onClick={save} disabled={saving}>
            {saving ? "保存中..." : "保存して計算結果を見る →"}
          </button>
        </div>
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 計算結果ページ
// ─────────────────────────────────────────────────
// 相続税の簡易計算（法定相続分課税方式）
function calcInheritanceTax(taxableBase: number, heirCount: number): number {
  if (taxableBase <= 0) return 0;
  // 各相続人の取得額仮定（均等割り）
  const perHeir = taxableBase / Math.max(heirCount, 1);
  const taxPerHeir = (amount: number): number => {
    if (amount <= 10_000_000)    return amount * 0.10;
    if (amount <= 30_000_000)    return amount * 0.15 -   500_000;
    if (amount <= 50_000_000)    return amount * 0.20 - 2_000_000;
    if (amount <= 100_000_000)   return amount * 0.30 - 7_000_000;
    if (amount <= 200_000_000)   return amount * 0.40 - 17_000_000;
    if (amount <= 300_000_000)   return amount * 0.45 - 27_000_000;
    if (amount <= 600_000_000)   return amount * 0.50 - 42_000_000;
    return amount * 0.55 - 72_000_000;
  };
  return Math.round(taxPerHeir(perHeir) * Math.max(heirCount, 1));
}

function AssetPieChart({ assets }: { assets: Asset[] }) {
  const COLORS = ["#16a34a","#2563eb","#d97706","#dc2626","#7c3aed","#0891b2","#64748b"];
  const positiveAssets = assets.filter((a) => a.asset_type !== "debt" && a.estimated_value > 0);
  const total = positiveAssets.reduce((s, a) => s + a.estimated_value, 0);
  if (total <= 0 || positiveAssets.length === 0) return null;

  const cx = 90, cy = 90, r = 75;
  let startAngle = -Math.PI / 2;
  const slices = positiveAssets.map((a, i) => {
    const angle = (a.estimated_value / total) * 2 * Math.PI;
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    startAngle += angle;
    const x2 = cx + r * Math.cos(startAngle);
    const y2 = cy + r * Math.sin(startAngle);
    const large = angle > Math.PI ? 1 : 0;
    return { path: `M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2} Z`, color: COLORS[i % COLORS.length], label: ASSET_TYPE_LABELS[a.asset_type] ?? a.name, pct: Math.round((a.estimated_value / total) * 100) };
  });

  return (
    <div style={{ display: "flex", gap: "1.5rem", alignItems: "center", flexWrap: "wrap" as const }}>
      <svg width={180} height={180} style={{ flexShrink: 0 }}>
        {slices.map((sl, i) => <path key={i} d={sl.path} fill={sl.color} stroke="#fff" strokeWidth={1.5} />)}
      </svg>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
        {slices.map((sl, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.82rem" }}>
            <div style={{ width: 12, height: 12, borderRadius: 2, background: sl.color, flexShrink: 0 }} />
            <span style={{ color: "var(--gray-700)" }}>{sl.label}</span>
            <span style={{ color: "var(--gray-500)", marginLeft: "auto" }}>{sl.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function EstateResultPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { planId } = useParams<{ planId: string }>();
  const [result, setResult] = useState<InheritanceCalculation | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);

  useEffect(() => {
    Promise.all([
      api.get(`/estate-plans/${planId}/calculate`),
      api.get(`/estate-plans/${planId}`),
    ]).then(([calcRes, planRes]) => {
      setResult(calcRes.data);
      setAssets(planRes.data.assets ?? []);
    });
  }, [planId]);

  if (!result) return <div style={{ padding: "4rem", textAlign: "center" as const }}>計算中...</div>;

  return (
    <div style={s.page}>
      <Header user={user} logout={() => { logout(); navigate("/login"); }} backTo={`/estate/${planId}/assets`} backLabel="← 財産の棚卸し" />
      <main style={s.main}>
        <div style={s.wizardHeader}>
          <div style={s.wizardStep}>① 家族構成</div>
          <div style={s.wizardArrow}>→</div>
          <div style={s.wizardStep}>② 財産の棚卸し</div>
          <div style={s.wizardArrow}>→</div>
          <div style={{ ...s.wizardStep, ...s.wizardStepActive }}>③ 計算結果</div>
        </div>

        {result.message ? (
          <div style={s.warningBox}>{result.message}</div>
        ) : (
          <>
            <div style={s.resultSummary}>
              <div style={s.resultItem}><div style={s.resultLabel}>相続人の順位</div><div style={s.resultValue}>{result.order_label}</div></div>
              <div style={s.resultItem}><div style={s.resultLabel}>正味遺産額</div><div style={s.resultValue}>{result.estate_value.toLocaleString()}円</div></div>
              <div style={s.resultItem}><div style={s.resultLabel}>相続税基礎控除</div><div style={s.resultValue}>{result.basic_deduction.toLocaleString()}円</div></div>
              {result.estate_value > result.basic_deduction && (
                <div style={s.resultItem}>
                  <div style={s.resultLabel}>相続税概算額（試算）</div>
                  <div style={{ ...s.resultValue, color: "#dc2626" }}>
                    約 {calcInheritanceTax(result.estate_value - result.basic_deduction, result.heirs.length).toLocaleString()}円
                  </div>
                </div>
              )}
            </div>

            {assets.length > 0 && (
              <Section title="資産の内訳">
                <AssetPieChart assets={assets} />
              </Section>
            )}

            <Section title="法定相続人と相続分">
              <div style={s.heirTable}>
                <div style={s.heirTableHeader}>
                  <span>相続人</span><span>続柄</span><span>法定相続分</span><span>取得金額（概算）</span><span>遺留分</span>
                </div>
                {result.heirs.map((h) => (
                  <HeirRow key={h.id} heir={h} />
                ))}
              </div>
            </Section>

            {result.estate_value < 0 && (
              <div style={s.warningBox}>⚠️ 負債が資産を上回っています（債務超過: {Math.abs(result.estate_value).toLocaleString()}円）。相続放棄も選択肢の一つです。弁護士・司法書士にご相談ください。</div>
            )}
            {result.estate_value >= 0 && result.estate_value <= result.basic_deduction && (
              <div style={s.infoBox}>✅ 正味遺産額が基礎控除（{result.basic_deduction.toLocaleString()}円）以内のため、相続税の申告は不要の可能性があります。</div>
            )}
            {result.estate_value > result.basic_deduction && (
              <div style={s.warningBox}>⚠️ 正味遺産額が基礎控除を超えています。相続税の申告が必要になる可能性があります。税理士にご相談ください。</div>
            )}

            <Section title="遺留分について">
              <p style={s.noteText}>遺言書を作成する場合でも、配偶者・子・直系尊属には遺留分（最低限受け取れる権利）があります。兄弟姉妹・甥姪には遺留分はありません。</p>
              {result.heirs.filter(h => h.has_reserved_right).map(h => (
                <div key={h.id} style={s.reservedRow}>
                  <span style={{ fontWeight: 600 }}>{h.name}</span>
                  <span>遺留分: {h.reserved_fraction}（{h.reserved_percent?.toFixed(1)}%）</span>
                  {result.estate_value > 0 && <span style={{ color: "#dc2626" }}>最低 {h.reserved_amount.toLocaleString()}円</span>}
                </div>
              ))}
            </Section>
          </>
        )}

        <div style={s.disclaimer}>
          ※ 本計算は民法の一般的な規定に基づく参考情報です。特別受益・寄与分・遺産分割協議等により異なる場合があります。正確な判断は専門家にご相談ください。
        </div>

        <div style={s.btnRow}>
          <Link to={`/estate/${planId}/family`} style={{ ...s.primaryBtn, background: "#64748b", marginRight: "1rem" }}>← 家族構成を修正する</Link>
          <Link to="/shukatsu" style={s.primaryBtn}>チェックリストに戻る</Link>
        </div>
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 共通コンポーネント
// ─────────────────────────────────────────────────

function Header({ user, logout, backTo, backLabel }: { user: any; logout: () => void; backTo?: string; backLabel?: string }) {
  return (
    <header style={s.header}>
      <div style={s.headerInner}>
        <div style={s.headerLeft}>
          {backTo && <Link to={backTo} style={s.backLink}>{backLabel ?? "← 戻る"}</Link>}
          <span style={s.headerLogo}>相続の棚卸し</span>
        </div>
        <div style={s.headerRight}>
          <span style={s.headerUser}>{user?.name}</span>
          <button style={s.logoutBtn} onClick={logout}>ログアウト</button>
        </div>
      </div>
    </header>
  );
}

function Section({ title, note, children }: { title: string; note?: string; children: React.ReactNode }) {
  return (
    <div style={s.sectionBox}>
      <div style={s.sectionHead}>
        <span style={s.sectionTitle2}>{title}</span>
        {note && <span style={s.sectionNote}>{note}</span>}
      </div>
      {children}
    </div>
  );
}

function MemberRow({ m, idx, onUpdate, onRemove, showAdopted, showHalfBlood, parentOptions }: {
  m: Partial<FamilyMember>; idx: number;
  onUpdate: (i: number, k: string, v: unknown) => void;
  onRemove: (i: number) => void;
  showAdopted: boolean; showHalfBlood: boolean;
  parentOptions?: { id: number; name: string }[];
}) {
  return (
    <div style={s.memberRow}>
      <input style={{ ...s.input, flex: 2 }} placeholder="名前" value={m.name ?? ""} onChange={(e) => onUpdate(idx, "name", e.target.value)} />
      <label style={s.checkLabel}>
        <input type="checkbox" checked={m.is_alive ?? true} onChange={(e) => onUpdate(idx, "is_alive", e.target.checked)} />
        存命
      </label>
      <label style={s.checkLabel}>
        <input type="checkbox" checked={m.has_renounced ?? false} onChange={(e) => onUpdate(idx, "has_renounced", e.target.checked)} />
        相続放棄
      </label>
      <label style={s.checkLabel}>
        <input type="checkbox" checked={m.is_disqualified ?? false} onChange={(e) => onUpdate(idx, "is_disqualified", e.target.checked)} />
        欠格・廃除
      </label>
      {showAdopted && (
        <label style={s.checkLabel}>
          <input type="checkbox" checked={m.is_adopted ?? false} onChange={(e) => onUpdate(idx, "is_adopted", e.target.checked)} />
          養子
        </label>
      )}
      {showHalfBlood && (
        <label style={s.checkLabel}>
          <input type="checkbox" checked={m.is_half_blood ?? false} onChange={(e) => onUpdate(idx, "is_half_blood", e.target.checked)} />
          半血
        </label>
      )}
      {parentOptions && (
        <select style={s.select} value={m.parent_member_id ?? ""} onChange={(e) => onUpdate(idx, "parent_member_id", e.target.value !== "" ? Number(e.target.value) : undefined)}>
          <option value="">代襲元を選択</option>
          {parentOptions.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      )}
      <button style={s.removeBtn} onClick={() => onRemove(idx)}>✕</button>
    </div>
  );
}

function AssetRow({ a, idx, onUpdate, onRemove, isDebt }: {
  a: Partial<Asset>; idx: number;
  onUpdate: (i: number, k: string, v: unknown) => void;
  onRemove: (i: number) => void;
  isDebt?: boolean;
}) {
  return (
    <div style={s.memberRow}>
      <input style={{ ...s.input, flex: 2 }} placeholder="名称（例：自宅）" value={a.name ?? ""} onChange={(e) => onUpdate(idx, "name", e.target.value)} />
      <input
        style={{ ...s.input, flex: 1 }} type="number" placeholder="金額（円）"
        value={Math.abs(a.estimated_value ?? 0) || ""}
        onChange={(e) => {
          const v = Number(e.target.value);
          onUpdate(idx, "estimated_value", isDebt ? -v : v);
        }}
      />
      <span style={{ fontSize: "0.85rem", color: "#6b7280" }}>円</span>
      {!isDebt && (
        <label style={s.checkLabel}>
          <input type="checkbox" checked={a.is_deemed_estate ?? false} onChange={(e) => onUpdate(idx, "is_deemed_estate", e.target.checked)} />
          みなし相続財産
        </label>
      )}
      <button style={s.removeBtn} onClick={() => onRemove(idx)}>✕</button>
    </div>
  );
}

function HeirRow({ heir }: { heir: HeirResult }) {
  return (
    <div style={s.heirTableRow}>
      <span style={{ fontWeight: 600 }}>{heir.name}</span>
      <span>{REL_LABELS[heir.relationship] ?? heir.relationship}</span>
      <span style={{ fontWeight: 700, color: "#1a5c38" }}>{heir.share_fraction}（{heir.share_percent.toFixed(1)}%）</span>
      <span>{heir.share_amount > 0 ? `${heir.share_amount.toLocaleString()}円` : "—"}</span>
      <span style={{ fontSize: "0.8rem", color: heir.has_reserved_right ? "#dc2626" : "#9ca3af" }}>
        {heir.has_reserved_right ? `${heir.reserved_fraction}（${heir.reserved_percent?.toFixed(1)}%）` : "なし"}
      </span>
    </div>
  );
}

const GREEN = "#1a5c38";
const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "#f8fafb", fontFamily: "sans-serif" },
  header: { background: "#fff", borderBottom: "1px solid #e5e7eb", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 900, margin: "0 auto", padding: "0 1.5rem", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" },
  headerLeft: { display: "flex", alignItems: "center", gap: "1rem" },
  backLink: { fontSize: "0.85rem", color: "#6b7280", textDecoration: "none" },
  headerLogo: { fontSize: "1.1rem", fontWeight: 700, color: GREEN },
  headerRight: { display: "flex", alignItems: "center", gap: "0.75rem" },
  headerUser: { fontSize: "0.9rem", color: "#374151" },
  logoutBtn: { fontSize: "0.8rem", padding: "0.3rem 0.8rem", border: "1px solid #d1d5db", borderRadius: 6, background: "#fff", cursor: "pointer" },
  main: { maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" },
  titleRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" },
  pageTitle: { fontSize: "1.4rem", fontWeight: 700, color: "#1a1a1a", margin: "0 0 4px" },
  pageSub: { fontSize: "0.9rem", color: "#6b7280", margin: 0 },
  primaryBtn: { background: GREEN, color: "#fff", border: "none", borderRadius: 8, padding: "0.6rem 1.25rem", fontSize: "0.9rem", fontWeight: 600, cursor: "pointer", textDecoration: "none", display: "inline-block" },
  ghostBtn: { background: "#fff", color: "#374151", border: "1px solid #d1d5db", borderRadius: 8, padding: "0.6rem 1.25rem", fontSize: "0.9rem", cursor: "pointer" },
  createBox: { background: "#fff", borderRadius: 10, padding: "1rem", marginBottom: "1.5rem", display: "flex", gap: "0.75rem", alignItems: "center", boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  empty: { textAlign: "center" as const, padding: "4rem", background: "#fff", borderRadius: 12 },
  cardGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem" },
  card: { background: "#fff", borderRadius: 10, padding: "1.25rem", boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  cardTitle: { fontSize: "1rem", fontWeight: 700, color: "#1a1a1a", marginBottom: 6 },
  cardMeta: { fontSize: "0.8rem", color: "#6b7280", marginBottom: 4 },
  cardActions: { display: "flex", gap: "0.5rem", marginTop: 12, flexWrap: "wrap" as const },
  actionBtn: { fontSize: "0.8rem", padding: "0.3rem 0.75rem", border: "1px solid #d1d5db", borderRadius: 6, background: "#fff", cursor: "pointer", textDecoration: "none", color: "#374151" },
  actionBtnPrimary: { background: GREEN, color: "#fff", border: "none" },
  deleteBtn: { fontSize: "0.8rem", padding: "0.3rem 0.75rem", border: "1px solid #fca5a5", borderRadius: 6, background: "#fff", cursor: "pointer", color: "#dc2626" },
  iconBtn: { background: "none", border: "none", cursor: "pointer", padding: "0 2px", fontSize: "0.85rem", opacity: 0.6 },
  wizardHeader: { display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" as const },
  wizardStep: { fontSize: "0.85rem", color: "#9ca3af", padding: "0.3rem 0.75rem", borderRadius: 20, border: "1px solid #e5e7eb" },
  wizardStepActive: { color: GREEN, borderColor: GREEN, fontWeight: 600 },
  wizardArrow: { color: "#d1d5db" },
  sectionBox: { background: "#fff", borderRadius: 10, padding: "1.25rem", marginBottom: "1rem", boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  sectionHead: { display: "flex", alignItems: "baseline", gap: "0.75rem", marginBottom: 12 },
  sectionTitle2: { fontSize: "1rem", fontWeight: 700, color: "#1a1a1a" },
  sectionNote: { fontSize: "0.78rem", color: "#9ca3af" },
  memberRow: { display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: 8, flexWrap: "wrap" as const },
  input: { padding: "0.45rem 0.7rem", border: "1px solid #d1d5db", borderRadius: 6, fontSize: "0.9rem", outline: "none" },
  select: { padding: "0.45rem 0.7rem", border: "1px solid #d1d5db", borderRadius: 6, fontSize: "0.85rem", background: "#fff" },
  checkLabel: { display: "flex", alignItems: "center", gap: 4, fontSize: "0.8rem", color: "#374151", cursor: "pointer", whiteSpace: "nowrap" as const },
  removeBtn: { fontSize: "0.8rem", color: "#9ca3af", background: "none", border: "none", cursor: "pointer", padding: "0.2rem 0.4rem" },
  addMemberBtn: { fontSize: "0.85rem", color: GREEN, background: "#f0fdf4", border: `1px dashed ${GREEN}`, borderRadius: 6, padding: "0.4rem 1rem", cursor: "pointer", marginTop: 4 },
  btnRow: { display: "flex", justifyContent: "flex-end", marginTop: "1.5rem" },
  totalBox: { background: "#f9fafb", borderRadius: 10, padding: "1rem 1.5rem", marginBottom: "1rem", border: "1px solid #e5e7eb" },
  totalRow: { display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: "0.95rem" },
  resultSummary: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", marginBottom: "1.5rem" },
  resultItem: { background: "#fff", borderRadius: 10, padding: "1rem", textAlign: "center" as const, boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  resultLabel: { fontSize: "0.78rem", color: "#6b7280", marginBottom: 4 },
  resultValue: { fontSize: "1rem", fontWeight: 700, color: "#1a1a1a" },
  heirTable: { display: "flex", flexDirection: "column" as const, gap: "0.5rem" },
  heirTableHeader: { display: "grid", gridTemplateColumns: "1fr 1fr 1.5fr 1.5fr 1.5fr", gap: "0.5rem", fontSize: "0.78rem", color: "#6b7280", fontWeight: 600, padding: "0.5rem 0.75rem" },
  heirTableRow: { display: "grid", gridTemplateColumns: "1fr 1fr 1.5fr 1.5fr 1.5fr", gap: "0.5rem", fontSize: "0.88rem", padding: "0.6rem 0.75rem", background: "#f9fafb", borderRadius: 6, alignItems: "center" },
  noteText: { fontSize: "0.85rem", color: "#6b7280", lineHeight: 1.7, margin: "0 0 12px" },
  reservedRow: { display: "flex", gap: "1rem", alignItems: "center", padding: "0.5rem 0.75rem", background: "#fef2f2", borderRadius: 6, marginBottom: 6, fontSize: "0.88rem" },
  infoBox: { background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "0.75rem 1rem", fontSize: "0.88rem", color: "#166534", marginBottom: "1rem" },
  warningBox: { background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: 8, padding: "0.75rem 1rem", fontSize: "0.88rem", color: "#92400e", marginBottom: "1rem" },
  disclaimer: { marginTop: "1.5rem", fontSize: "0.75rem", color: "#9ca3af", textAlign: "center" as const, lineHeight: 1.6 },
};
