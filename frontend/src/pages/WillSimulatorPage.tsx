import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";
import type { EstatePlan, InheritanceCalculation, HeirResult } from "../types";

const GREEN = "#1a5c38";

interface WillDraft {
  estate_plan_id: number;
  allocations: Record<string, number>;
  memo: string | null;
}

export default function WillSimulatorPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { planId } = useParams<{ planId: string }>();
  const [calc, setCalc] = useState<InheritanceCalculation | null>(null);
  const [plan, setPlan] = useState<EstatePlan | null>(null);
  const [allocations, setAllocations] = useState<Record<string, number>>({});
  const [memo, setMemo] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get(`/estate-plans/${planId}/calculate`),
      api.get(`/estate-plans/${planId}`),
      api.get(`/estate-plans/${planId}/will`),
    ]).then(([calcRes, planRes, willRes]) => {
      const calcData: InheritanceCalculation = calcRes.data;
      setCalc(calcData);
      setPlan(planRes.data);
      const willData: WillDraft = willRes.data;
      if (willData && Object.keys(willData.allocations || {}).length > 0) {
        setAllocations(willData.allocations);
      } else {
        const initial: Record<string, number> = {};
        calcData.heirs.forEach((h: HeirResult) => {
          initial[String(h.id)] = h.share_amount;
        });
        setAllocations(initial);
      }
      setMemo(willData.memo || "");
    });
  }, [planId]);

  const estateValue = calc?.estate_value ?? 0;
  const totalAllocated = Object.values(allocations).reduce((s, v) => s + (v || 0), 0);
  const totalDiff = totalAllocated - estateValue;
  const isBalanced = Math.abs(totalDiff) < 1000;

  const violations = (() => {
    if (!calc) return [];
    return calc.heirs
      .filter((h) => h.has_reserved_right && h.reserved_amount > 0)
      .filter((h) => (allocations[String(h.id)] || 0) < h.reserved_amount)
      .map((h) => ({ name: h.name, reserved: h.reserved_amount, allocated: allocations[String(h.id)] || 0 }));
  })();

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/estate-plans/${planId}/will`, { allocations, memo });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handlePrint = async () => {
    await handleSave();
    setTimeout(() => window.print(), 400);
  };

  if (!calc || !plan) {
    return <div style={{ padding: "4rem", textAlign: "center" as const }}>読み込み中...</div>;
  }

  const today = new Date().toLocaleDateString("ja-JP", { year: "numeric", month: "long", day: "numeric" });

  return (
    <div style={s.page}>
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          .print-only { display: block !important; }
          header { display: none !important; }
          @page { margin: 2cm; }
        }
        .print-only { display: none; }
      ` }} />

      <header style={s.header}>
        <div style={s.headerInner}>
          <div style={s.headerLeft}>
            <Link to={`/estate/${planId}/result`} style={s.backLink}>← 計算結果</Link>
            <span style={s.headerLogo}>自筆遺言書シミュレーター</span>
          </div>
          <div style={s.headerRight}>
            <span style={s.headerUser}>{user?.name}</span>
            <button style={s.logoutBtn} onClick={() => { logout(); navigate("/login"); }}>ログアウト</button>
          </div>
        </div>
      </header>

      <main style={s.main}>
        {/* ウィザードステップ */}
        <div style={s.wizardHeader} className="no-print">
          <div style={s.wizardStep}>① 家族構成</div>
          <div style={s.wizardArrow}>→</div>
          <div style={s.wizardStep}>② 財産の棚卸し</div>
          <div style={s.wizardArrow}>→</div>
          <div style={s.wizardStep}>③ 計算結果</div>
          <div style={s.wizardArrow}>→</div>
          <div style={{ ...s.wizardStep, ...s.wizardStepActive }}>④ 遺言書シミュレーター</div>
        </div>

        <div style={s.intro} className="no-print">
          法定相続分と比較しながら希望配分を設定できます。
          遺留分（法律で保障された最低限の取得割合）を下回ると警告します。
          設定後「テンプレート印刷」でPDF出力できます。
        </div>

        {/* 配分入力テーブル */}
        <div style={s.sectionBox} className="no-print">
          <div style={s.sectionHead}>
            <span style={s.sectionTitle}>希望配分の設定</span>
            <span style={{ fontSize: "0.82rem", color: "#6b7280" }}>正味遺産額: {estateValue.toLocaleString()}円</span>
          </div>

          <div style={s.tableWrap}>
            <div style={s.tableHeader}>
              <span>相続人</span>
              <span>法定相続分</span>
              <span>希望配分額（円）</span>
              <span>遺留分</span>
              <span>状態</span>
            </div>
            {calc.heirs.map((h) => {
              const key = String(h.id);
              const allocated = allocations[key] ?? h.share_amount;
              const ok = !h.has_reserved_right || allocated >= h.reserved_amount;
              return (
                <div key={h.id} style={{ ...s.tableRow, ...(ok ? {} : s.tableRowWarn) }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{h.name}</div>
                    <div style={{ fontSize: "0.78rem", color: "#6b7280" }}>{h.relationship}</div>
                  </div>
                  <div>
                    <div>{h.share_fraction}</div>
                    <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>{h.share_amount.toLocaleString()}円</div>
                  </div>
                  <div>
                    <input
                      type="number"
                      style={s.amountInput}
                      value={allocated || ""}
                      min={0}
                      onChange={(e) => setAllocations((p) => ({ ...p, [key]: Math.max(0, Number(e.target.value)) }))}
                    />
                  </div>
                  <div style={{ fontSize: "0.82rem" }}>
                    {h.has_reserved_right ? (
                      <span style={{ color: "#dc2626" }}>
                        {h.reserved_fraction}<br />最低 {h.reserved_amount.toLocaleString()}円
                      </span>
                    ) : (
                      <span style={{ color: "#9ca3af" }}>なし</span>
                    )}
                  </div>
                  <div>
                    {ok
                      ? <span style={s.okBadge}>✓ OK</span>
                      : <span style={s.warnBadge}>⚠ 不足</span>
                    }
                  </div>
                </div>
              );
            })}
          </div>

          {/* 合計チェック */}
          <div style={{ ...s.totalCheck, ...(isBalanced ? s.totalCheckOk : s.totalCheckWarn) }}>
            <span>配分合計: {totalAllocated.toLocaleString()}円</span>
            <span>遺産総額: {estateValue.toLocaleString()}円</span>
            <span>
              {isBalanced
                ? "✓ 合計一致"
                : `差額: ${Math.abs(totalDiff).toLocaleString()}円 ${totalDiff > 0 ? "超過" : "不足"}`}
            </span>
          </div>

          {/* 遺留分侵害警告 */}
          {violations.length > 0 && (
            <div style={s.violationBox}>
              <strong>⚠ 遺留分侵害の警告</strong>
              {violations.map((v) => (
                <div key={v.name} style={{ marginTop: 4 }}>
                  {v.name}: 最低 {v.reserved.toLocaleString()}円 必要 → 現在 {v.allocated.toLocaleString()}円（
                  {(v.reserved - v.allocated).toLocaleString()}円 不足）
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 付言事項 */}
        <div style={s.sectionBox} className="no-print">
          <div style={s.sectionHead}>
            <span style={s.sectionTitle}>付言事項（遺言者からのメッセージ）</span>
          </div>
          <textarea
            style={s.textarea}
            rows={4}
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            placeholder="家族へのメッセージ、遺言の理由など（任意）"
          />
        </div>

        {/* 操作ボタン */}
        <div style={s.btnRow} className="no-print">
          <button style={{ ...s.primaryBtn, background: "#64748b" }} onClick={handleSave} disabled={saving}>
            {saving ? "保存中..." : saved ? "✓ 保存しました" : "💾 配分を保存"}
          </button>
          <button style={{ ...s.primaryBtn, background: "#0891b2" }} onClick={() => setShowPreview((p) => !p)}>
            {showPreview ? "📄 プレビューを閉じる" : "📄 遺言書テキストをプレビュー"}
          </button>
          <button style={s.primaryBtn} onClick={handlePrint} disabled={saving}>
            🖨 遺言書テンプレートを印刷
          </button>
          <Link to={`/estate/${planId}/result`} style={{ ...s.primaryBtn, background: "#64748b" }}>← 計算結果に戻る</Link>
        </div>

        {/* 遺言書テキストプレビュー */}
        {showPreview && (
          <div style={{ ...s.sectionBox, border: "2px solid #1a5c38" }} className="no-print">
            <div style={s.sectionHead}>
              <span style={s.sectionTitle}>📄 遺言書テキスト（自動生成）</span>
              <span style={{ fontSize: "0.78rem", color: "#9ca3af" }}>印刷時はこの内容が出力されます</span>
            </div>
            <div style={{ fontFamily: "serif", lineHeight: 2.2, padding: "1rem", background: "#fffde7", borderRadius: 8, fontSize: "0.93rem" }}>
              <p style={{ textAlign: "center" as const, fontSize: "1.3rem", letterSpacing: "0.5em", fontWeight: 700, marginBottom: "0.5rem" }}>遺 言 書</p>
              <p style={{ textAlign: "center" as const, color: "#888", fontSize: "0.8rem", marginBottom: "1.5rem" }}>（自筆証書遺言 参考テンプレート）</p>
              <p>遺言者 <strong>{user?.name}</strong> は、以下の通り遺言する。</p>
              <p style={{ fontWeight: 700, marginTop: "1rem" }}>第一条　財産の分配</p>
              {calc.heirs.map((h, i) => {
                const allocated = allocations[String(h.id)] ?? h.share_amount;
                return <p key={h.id}>{i + 1}.&nbsp;{h.name}（{h.relationship}）に、遺産の中から金{allocated.toLocaleString()}円を相続させる。</p>;
              })}
              {memo && (
                <>
                  <p style={{ fontWeight: 700, marginTop: "1rem" }}>付言事項</p>
                  <p style={{ whiteSpace: "pre-wrap" as const }}>{memo}</p>
                </>
              )}
              <div style={{ marginTop: "2rem" }}>
                <p>{today}</p>
                <p>遺言者　住所：＿＿＿＿＿＿＿＿＿＿＿＿＿＿</p>
                <p>　　　　氏名：{user?.name}　㊞</p>
                <p>　　　　生年月日：＿＿＿＿＿年＿＿月＿＿日</p>
              </div>
            </div>
          </div>
        )}

        {/* 法的手続きの案内 */}
        <div style={{ ...s.sectionBox, background: "#fffde7", border: "1px solid #ffc107" }} className="no-print">
          <h2 style={{ ...s.sectionTitle, color: "#7a6000", marginBottom: "1rem" }}>⚖️ 自筆証書遺言の有効要件</h2>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {[
              { icon: "✍️", title: "全文自筆で書くこと", desc: "パソコン・代筆は無効。財産目録のみPC作成可（各ページに署名・押印が必要）" },
              { icon: "📅", title: "日付を自書すること", desc: "「令和○年○月○日」と具体的に記載。「○月吉日」などは無効" },
              { icon: "🖊️", title: "氏名を自書すること", desc: "フルネームを自筆で署名する" },
              { icon: "🔏", title: "押印すること", desc: "認印でも可だが実印が望ましい" },
            ].map((item) => (
              <div key={item.title} style={{ display: "flex", gap: "0.75rem", padding: "0.75rem", background: "white", borderRadius: 8, border: "1px solid #f0e68c" }}>
                <span style={{ fontSize: "1.3rem", flexShrink: 0 }}>{item.icon}</span>
                <div>
                  <div style={{ fontWeight: 700, color: "#5a4000", fontSize: "0.9rem" }}>{item.title}</div>
                  <div style={{ color: "#6b6b6b", fontSize: "0.82rem", marginTop: 2 }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: "1rem", padding: "0.75rem 1rem", background: "#fff8e1", borderRadius: 8, fontSize: "0.85rem", color: "#5a4000", lineHeight: 1.7 }}>
            <strong>📌 法務局への保管制度：</strong>
            自筆証書遺言は法務局（遺言書保管所）に預けることができます（手数料3,900円）。紛失・改ざんを防ぎ、家庭裁判所の検認手続きが不要になります。<br />
            <strong>💡 より確実な遺言書には：</strong>
            公正証書遺言の作成をお勧めします。証人2名と公証人立会のもと作成し、原本が公証役場に保管されます。費用は遺産額に応じて異なります。<br />
            <strong>👨‍⚖️ 専門家への相談：</strong>
            弁護士・司法書士・行政書士・公証役場にご相談ください。
          </div>
        </div>

        {/* ─── 印刷テンプレート（@media print でのみ表示）─── */}
        <div className="print-only">
          <div style={s.printWrap}>
            <h1 style={s.printTitle}>遺 言 書</h1>
            <p style={s.printSubNote}>（自筆証書遺言 参考テンプレート）</p>

            <p style={s.printPara}>
              遺言者 <strong>{user?.name}</strong> は、以下の通り遺言する。
            </p>

            <h2 style={s.printH2}>第一条　財産の分配</h2>
            {calc.heirs.map((h, i) => {
              const allocated = allocations[String(h.id)] ?? h.share_amount;
              return (
                <p key={h.id} style={s.printPara}>
                  {i + 1}.&nbsp;{h.name}（{h.relationship}）に、遺産の中から
                  金{allocated.toLocaleString()}円を相続させる。
                </p>
              );
            })}

            {memo && (
              <>
                <h2 style={s.printH2}>付言事項</h2>
                <p style={{ ...s.printPara, whiteSpace: "pre-wrap" as const }}>{memo}</p>
              </>
            )}

            <div style={s.printSig}>
              <p style={s.printPara}>{today}</p>
              <p style={s.printPara}>遺言者　住所：&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;</p>
              <p style={s.printPara}>　　　　氏名：{user?.name}&emsp;&emsp;&emsp;&emsp;㊞</p>
              <p style={s.printPara}>　　　　生年月日：&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;</p>
            </div>

            <div style={s.printCaution}>
              <strong>【重要注意事項】</strong>
              <p style={{ margin: "4px 0" }}>これはシミュレーション用のテンプレートであり、法的効力はありません。</p>
              <p style={{ margin: "4px 0" }}>自筆証書遺言として有効にするには、①全文自筆で書くこと、②日付を自書すること、③氏名を自書すること、④押印することが必要です（財産目録のみPC作成可）。</p>
              <p style={{ margin: "4px 0" }}>法的に有効な遺言書の作成には、弁護士・司法書士・公証役場にご相談ください。</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "#f8fafb", fontFamily: "sans-serif" },
  header: { background: "#fff", borderBottom: "1px solid #e5e7eb", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 960, margin: "0 auto", padding: "0 1.5rem", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" },
  headerLeft: { display: "flex", alignItems: "center", gap: "1rem" },
  backLink: { fontSize: "0.85rem", color: "#6b7280", textDecoration: "none" },
  headerLogo: { fontSize: "1.05rem", fontWeight: 700, color: GREEN },
  headerRight: { display: "flex", alignItems: "center", gap: "0.75rem" },
  headerUser: { fontSize: "0.9rem", color: "#374151" },
  logoutBtn: { fontSize: "0.8rem", padding: "0.3rem 0.8rem", border: "1px solid #d1d5db", borderRadius: 6, background: "#fff", cursor: "pointer" },
  main: { maxWidth: 960, margin: "0 auto", padding: "2rem 1.5rem" },
  wizardHeader: { display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" as const },
  wizardStep: { padding: "0.35rem 0.85rem", borderRadius: 20, border: "1px solid #e5e7eb", fontSize: "0.82rem", color: "#6b7280", background: "#fff" },
  wizardStepActive: { background: GREEN, color: "#fff", borderColor: GREEN, fontWeight: 600 },
  wizardArrow: { color: "#9ca3af", fontSize: "0.85rem" },
  intro: { background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, padding: "0.85rem 1.25rem", marginBottom: "1.5rem", fontSize: "0.88rem", color: "#166534", lineHeight: 1.7 },
  sectionBox: { background: "#fff", borderRadius: 12, padding: "1.5rem 2rem", marginBottom: "1.5rem", boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  sectionHead: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" },
  sectionTitle: { fontSize: "1rem", fontWeight: 700, color: "#1a1a1a" },
  tableWrap: { display: "flex", flexDirection: "column" as const },
  tableHeader: {
    display: "grid", gridTemplateColumns: "1.6fr 1fr 1.5fr 1fr 0.8fr",
    gap: "0.5rem", padding: "0.5rem 0.75rem",
    fontSize: "0.78rem", fontWeight: 600, color: "#6b7280",
    background: "#f9fafb", borderRadius: 8, marginBottom: 4,
  },
  tableRow: {
    display: "grid", gridTemplateColumns: "1.6fr 1fr 1.5fr 1fr 0.8fr",
    gap: "0.5rem", padding: "0.7rem 0.75rem", alignItems: "center",
    borderBottom: "1px solid #f3f4f6", fontSize: "0.88rem",
  },
  tableRowWarn: { background: "#fef2f2" },
  amountInput: {
    width: "100%", padding: "0.4rem 0.6rem",
    border: "1px solid #d1d5db", borderRadius: 7, fontSize: "0.88rem", outline: "none",
  },
  okBadge: { padding: "0.2rem 0.55rem", borderRadius: 20, background: "#dcfce7", color: "#166534", fontSize: "0.75rem", fontWeight: 600, whiteSpace: "nowrap" as const },
  warnBadge: { padding: "0.2rem 0.55rem", borderRadius: 20, background: "#fee2e2", color: "#dc2626", fontSize: "0.75rem", fontWeight: 600, whiteSpace: "nowrap" as const },
  totalCheck: { display: "flex", justifyContent: "space-between", padding: "0.7rem 1rem", borderRadius: 8, marginTop: "0.75rem", fontSize: "0.88rem", fontWeight: 600, flexWrap: "wrap" as const, gap: "0.5rem" },
  totalCheckOk: { background: "#dcfce7", color: "#166534" },
  totalCheckWarn: { background: "#fef3c7", color: "#92400e" },
  violationBox: { marginTop: "0.75rem", padding: "0.9rem 1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: "0.86rem", color: "#dc2626", lineHeight: 1.7 },
  textarea: { width: "100%", padding: "0.6rem 0.75rem", border: "1px solid #d1d5db", borderRadius: 7, fontSize: "0.9rem", outline: "none", boxSizing: "border-box" as const, resize: "vertical" as const, fontFamily: "sans-serif" },
  btnRow: { display: "flex", gap: "0.75rem", flexWrap: "wrap" as const },
  primaryBtn: { display: "inline-block", background: GREEN, color: "#fff", border: "none", borderRadius: 8, padding: "0.65rem 1.4rem", fontSize: "0.88rem", cursor: "pointer", textDecoration: "none", fontWeight: 600 },
  // 印刷テンプレート
  printWrap: { fontFamily: "serif", padding: "2rem", maxWidth: 680, margin: "0 auto", lineHeight: 2.2 },
  printTitle: { textAlign: "center" as const, fontSize: "1.8rem", letterSpacing: "0.6em", margin: "0 0 0.3rem", fontWeight: 700 },
  printSubNote: { textAlign: "center" as const, color: "#6b7280", fontSize: "0.82rem", marginBottom: "2rem" },
  printH2: { fontSize: "1rem", borderBottom: "1px solid #1a1a1a", paddingBottom: 3, marginTop: "1.5rem", marginBottom: "0.75rem" },
  printPara: { margin: "0.5rem 0", fontSize: "0.93rem" },
  printSig: { marginTop: "3rem", marginBottom: "2rem" },
  printCaution: { marginTop: "2rem", fontSize: "0.75rem", color: "#6b7280", background: "#f9fafb", padding: "0.9rem 1rem", borderRadius: 8, lineHeight: 1.7, borderTop: "1px solid #e5e7eb" },
};
