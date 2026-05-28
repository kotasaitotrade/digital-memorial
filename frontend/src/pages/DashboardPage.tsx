import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";
import QRModal from "../components/QRModal";
import OnboardingModal from "../components/OnboardingModal";

const ONBOARDING_KEY = "dm_onboarding_done";
import type { Memorial, ChecklistItem } from "../types";

// ヘルプツールチップ（渡辺博 要望）
function HelpTip({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  return (
    <span style={{ position: "relative", display: "inline-block", marginLeft: "0.3rem" }}>
      <span
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        style={{ cursor: "help", fontSize: "0.78rem", color: "var(--gray-400)", border: "1px solid var(--gray-300)", borderRadius: "50%", width: 18, height: 18, display: "inline-flex", alignItems: "center", justifyContent: "center" }}
      >?</span>
      {show && (
        <span style={{ position: "absolute", bottom: "calc(100% + 6px)", left: "50%", transform: "translateX(-50%)", background: "rgba(0,0,0,.8)", color: "#fff", padding: "0.4rem 0.65rem", borderRadius: 6, fontSize: "0.75rem", whiteSpace: "normal", zIndex: 999, maxWidth: 220, wordBreak: "break-all" } as any}>
          {text}
        </span>
      )}
    </span>
  );
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showOnboarding, setShowOnboarding] = useState(() => !localStorage.getItem(ONBOARDING_KEY));
  const [memorials, setMemorials] = useState<Memorial[]>([]);
  const [qrTarget, setQrTarget] = useState<Memorial | null>(null);
  const [todoItems, setTodoItems] = useState<ChecklistItem[]>([]);
  const [allChecklistItems, setAllChecklistItems] = useState<ChecklistItem[]>([]);
  const [estatePlanCount, setEstatePlanCount] = useState(0);
  const [showPriorityOnly, setShowPriorityOnly] = useState(false);

  const isSimple = user?.simple_mode ?? false;

  const dismissOnboarding = () => {
    localStorage.setItem(ONBOARDING_KEY, "1");
    setShowOnboarding(false);
  };

  useEffect(() => {
    api.get("/memorials").then((res) => setMemorials(res.data));
    api.get("/checklist").then((r) => {
      const data = r.data;
      const all = Array.isArray(data) ? data : (data.items ?? []);
      setAllChecklistItems(all);
      setTodoItems(all.filter((i: ChecklistItem) => !i.is_completed));
    });
    api.get("/estate-plans").then((r) => setEstatePlanCount(r.data.length)).catch(() => {});
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm("この墓誌を削除しますか？")) return;
    await api.delete(`/memorials/${id}`);
    setMemorials((prev) => prev.filter((m) => m.id !== id));
  };

  const priorityTodos = todoItems.filter((i) => i.stars >= 4);
  const displayTodos = showPriorityOnly ? priorityTodos : todoItems.slice(0, 5);
  const checklistTotal = allChecklistItems.length;
  const checklistDone = allChecklistItems.filter((i) => i.is_completed).length;
  const completionPct = checklistTotal > 0 ? Math.round((checklistDone / checklistTotal) * 100) : 0;

  return (
    <div style={s.page}>
      {showOnboarding && <OnboardingModal onClose={dismissOnboarding} />}
      {/* ヘッダー */}
      <header style={s.header}>
        <div style={s.headerInner}>
          <div style={s.headerLeft}>
            <span style={s.headerLogo}>Digital Memorial</span>
          </div>
          <div style={s.headerRight}>
            <span style={s.headerUser}>{user?.name}</span>
            <Link to="/account" style={s.settingsLink}>設定</Link>
            <button style={s.logoutBtn} onClick={() => { logout(); navigate("/login"); }}>
              ログアウト
            </button>
          </div>
        </div>
      </header>

      <main style={s.main}>
        {/* 終活ノートバナー */}
        <Link to="/shukatsu" style={s.shukatsuBanner}>
          <span style={{ fontSize: "1.3rem" }}>📋</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>終活ノートを開く</div>
            {!isSimple && <div style={{ fontSize: "0.78rem", opacity: 0.85 }}>相続の棚卸し・エンディングノート・チェックリスト</div>}
          </div>
          <span style={{ marginLeft: "auto", fontSize: "1.1rem" }}>→</span>
        </Link>

        {/* クイックスタッツ */}
        {!isSimple && (
          <div style={s.statsRow}>
            {[
              { label: "墓誌", value: memorials.length, unit: "件", to: "#memorials", icon: "🪦" },
              { label: "相続計画", value: estatePlanCount, unit: "件", to: "/estate", icon: "📊" },
              { label: "終活完了率", value: completionPct, unit: "%", to: "/shukatsu", icon: "✅", progress: completionPct },
            ].map(({ label, value, unit, to, icon, progress }) => (
              <Link key={label} to={to} style={s.statCard}>
                <span style={s.statIcon}>{icon}</span>
                <div style={s.statBody}>
                  <div style={s.statLabel}>{label}</div>
                  <div style={s.statValue}>{value}<span style={s.statUnit}>{unit}</span></div>
                  {progress !== undefined && (
                    <div style={s.progressBar}>
                      <div style={{ ...s.progressFill, width: `${progress}%` }} />
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* 完了率に応じたコーチングメッセージ */}
        {!isSimple && checklistTotal > 0 && (
          <div style={{
            background: completionPct >= 80 ? "#f0faf3" : completionPct >= 40 ? "#fffbeb" : "#fef2f2",
            border: `1px solid ${completionPct >= 80 ? "var(--green-400)" : completionPct >= 40 ? "#fcd34d" : "#fca5a5"}`,
            borderRadius: 10, padding: "0.85rem 1.1rem", marginBottom: "1.25rem",
            display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.875rem",
          }}>
            <span style={{ fontSize: "1.25rem", flexShrink: 0 }}>
              {completionPct >= 80 ? "🎉" : completionPct >= 40 ? "💪" : "🌱"}
            </span>
            <div>
              <span style={{ fontWeight: 600, color: completionPct >= 80 ? "var(--green-800)" : completionPct >= 40 ? "#92400e" : "#991b1b" }}>
                {completionPct >= 80 ? "素晴らしい！終活の準備がよく進んでいます" : completionPct >= 40 ? "着実に前進中！引き続き終活を進めましょう" : "終活の第一歩を踏み出しましょう"}
              </span>
              <span style={{ color: "#6b7280", marginLeft: "0.4rem" }}>
                {completionPct >= 80 ? "— 残り項目を確認して完成させましょう" : completionPct >= 40 ? `— あと${checklistTotal - checklistDone}項目が未完了です` : "— まずは「終活ノートを開く」からスタート"}
              </span>
            </div>
          </div>
        )}

        {/* 次のおすすめアクション（最優先の未完了タスク） */}
        {!isSimple && todoItems.length > 0 && completionPct < 100 && (() => {
          const top = todoItems[0];
          return (
            <Link to={top.link} style={s.nextActionCard}>
              <div style={s.nextActionLeft}>
                <span style={s.nextActionBadge}>次のおすすめアクション</span>
                <div style={s.nextActionLabel}>{top.label}</div>
              </div>
              <span style={s.nextActionArrow}>→</span>
            </Link>
          );
        })()}

        {/* かんたんモード時のクイックアクション（田中幸子・藤田美香 要望） */}
        {isSimple && (
          <div style={s.quickActions}>
            <div style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.75rem", color: "var(--gray-700)" }}>
              かんたんメニュー
              <HelpTip text="よく使う機能をまとめました。設定で通常モードに戻せます。" />
            </div>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              {[
                { to: "/ending-note", label: "エンディングノート", icon: "📝" },
                { to: "/estate", label: "相続計画", icon: "🏠" },
                { to: "/digital-key", label: "デジタル遺品", icon: "🔑" },
                { to: "/account", label: "設定", icon: "⚙️" },
              ].map(({ to, label, icon }) => (
                <Link key={to} to={to} style={s.quickBtn}>
                  <span style={{ fontSize: "1.4rem" }}>{icon}</span>
                  <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>{label}</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* 未完了タスク（佐藤健一・藤田美香 要望） */}
        {todoItems.length > 0 && (
          <div style={s.todoCard}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
              <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--gray-800)" }}>
                未完了タスク
                <HelpTip text="終活の準備で残っている項目です。クリックしてページへ移動できます。" />
                <span style={{ marginLeft: "0.5rem", fontSize: "0.78rem", color: "var(--gray-500)" }}>（{todoItems.length}件）</span>
              </div>
              <button
                onClick={() => setShowPriorityOnly(!showPriorityOnly)}
                style={{
                  padding: "0.25rem 0.7rem", fontSize: "0.75rem", cursor: "pointer",
                  background: showPriorityOnly ? "var(--green-800)" : "var(--white)",
                  color: showPriorityOnly ? "#fff" : "var(--gray-700)",
                  border: "1.5px solid var(--gray-300)", borderRadius: 20,
                }}
              >
                {showPriorityOnly ? "✓ 重要のみ表示中" : "重要のみ表示"}
              </button>
            </div>
            {displayTodos.length === 0 ? (
              <div style={{ fontSize: "0.85rem", color: "var(--gray-500)" }}>重要な未完了タスクはありません</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                {displayTodos.map((item) => (
                  <Link
                    key={item.task_key}
                    to={item.link}
                    style={{
                      display: "flex", alignItems: "center", gap: "0.6rem",
                      padding: "0.5rem 0.75rem", borderRadius: 6, textDecoration: "none",
                      background: "var(--sand-100)", color: "var(--gray-700)", fontSize: "0.85rem",
                    }}
                  >
                    <span style={{ fontSize: "0.65rem", fontWeight: 700, padding: "2px 6px", borderRadius: 4, background: item.stars >= 5 ? "#fee2e2" : item.stars >= 4 ? "#fef3c7" : "#f3f4f6", color: item.stars >= 5 ? "#dc2626" : item.stars >= 4 ? "#92400e" : "#6b7280" }}>
                      {item.priority}
                    </span>
                    {item.label}
                    <span style={{ marginLeft: "auto", fontSize: "0.8rem", color: "var(--gray-400)" }}>→</span>
                  </Link>
                ))}
                {!showPriorityOnly && todoItems.length > 5 && (
                  <Link to="/shukatsu" style={{ fontSize: "0.8rem", color: "var(--green-700)", textDecoration: "none", padding: "0.3rem 0.75rem" }}>
                    すべて見る（{todoItems.length}件）→
                  </Link>
                )}
              </div>
            )}
          </div>
        )}

        {/* 墓誌一覧（かんたんモード時は非表示オプション） */}
        <div style={s.titleRow}>
          <div>
            <h1 style={s.pageTitle}>
              墓誌一覧
              <HelpTip text="「墓誌（ぼし）」とは、故人の情報や思い出を記録するデジタルのお墓のプロフィールです。" />
            </h1>
            <p style={s.pageSub}>{memorials.length}件の墓誌が登録されています</p>
          </div>
          <Link to="/memorials/new" style={s.newBtn}>
            <span style={{ fontSize: "1.1rem", lineHeight: 1 }}>＋</span> 新規作成
          </Link>
        </div>

        {memorials.length === 0 ? (
          <div style={s.empty}>
            <div style={s.emptyIcon}>🕊️</div>
            <h2 style={s.emptyTitle}>まだ墓誌が登録されていません</h2>
            <p style={s.emptyDesc}>最初の墓誌を作成して、大切な方の記憶を残しましょう。</p>
            <Link to="/memorials/new" style={s.newBtn}>墓誌を作成する</Link>
          </div>
        ) : (
          <div style={s.grid}>
            {memorials.map((m) => (
              <MemorialCard key={m.id} memorial={m} onQR={() => setQrTarget(m)} onDelete={() => handleDelete(m.id)} />
            ))}
          </div>
        )}
      </main>

      {qrTarget && <QRModal memorial={qrTarget} onClose={() => setQrTarget(null)} />}
    </div>
  );
}

function MemorialCard({ memorial: m, onQR, onDelete }: { memorial: Memorial; onQR: () => void; onDelete: () => void }) {
  const [hover, setHover] = useState(false);
  return (
    <div style={{ ...s.card, ...(hover ? s.cardHover : {}) }} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>
      <div style={s.cardThumbWrap}>
        {m.media.length > 0 ? (
          <img src={m.media[0].file_path} alt={m.name} style={s.cardThumb} />
        ) : (
          <div style={s.cardThumbFallback}>
            <span style={s.cardThumbInitial}>{m.name[0]}</span>
          </div>
        )}
        <div style={{ ...s.publicBadge, ...(m.is_public ? s.publicBadgeOpen : s.publicBadgeLocked) }}>
          {m.is_public ? "公開" : "🔒 非公開"}
        </div>
      </div>
      <div style={s.cardBody}>
        <h3 style={s.cardName}>{m.name}</h3>
        {m.birth_date && m.death_date && <p style={s.cardDates}>{m.birth_date} 〜 {m.death_date}</p>}
        {m.biography && <p style={s.cardBio}>{m.biography.slice(0, 55)}{m.biography.length > 55 && "…"}</p>}
        {(m.view_count ?? 0) > 0 && <p style={s.viewCount}>👁 {m.view_count}回閲覧</p>}
      </div>
      <div style={s.cardFooter}>
        <a href={`/m/${m.slug}`} target="_blank" rel="noreferrer" style={s.btnView}>閲覧</a>
        <Link to={`/memorials/${m.id}/edit`} style={s.btnEdit}>編集</Link>
        {m.qr_code_path && <button style={s.btnQr} onClick={onQR}>QRコード</button>}
        <button style={s.btnDelete} onClick={onDelete}>削除</button>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--sand-100)" },
  header: { background: "var(--white)", borderBottom: "1px solid var(--sand-300)", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 1100, margin: "0 auto", padding: "0 2rem", height: 60, display: "flex", alignItems: "center", justifyContent: "space-between" },
  headerLeft: {},
  headerLogo: { fontFamily: "var(--font-serif)", fontSize: "1.05rem", fontWeight: 700, color: "var(--green-900)", letterSpacing: "0.04em" },
  headerRight: { display: "flex", alignItems: "center", gap: "1rem" },
  headerUser: { fontSize: "0.85rem", color: "var(--gray-500)" },
  settingsLink: { fontSize: "0.82rem", color: "var(--gray-500)", textDecoration: "none" },
  logoutBtn: { padding: "0.35rem 0.85rem", background: "transparent", border: "1.5px solid var(--gray-300)", borderRadius: 6, fontSize: "0.82rem", color: "var(--gray-700)", transition: "all var(--transition)", cursor: "pointer" },
  main: { maxWidth: 1100, margin: "0 auto", padding: "2.5rem 2rem" },
  shukatsuBanner: { display: "flex", alignItems: "center", gap: "0.75rem", background: "linear-gradient(135deg, #1a5c38, #2d7a4f)", color: "#fff", borderRadius: 10, padding: "0.85rem 1.25rem", textDecoration: "none", marginBottom: "1.25rem", boxShadow: "0 2px 6px rgba(26,92,56,.25)" },
  quickActions: { background: "var(--white)", borderRadius: 10, padding: "1.25rem", boxShadow: "var(--shadow-sm)", marginBottom: "1.25rem" },
  quickBtn: { display: "flex", flexDirection: "column", alignItems: "center", gap: "0.3rem", padding: "0.75rem 1rem", background: "var(--sand-100)", borderRadius: 8, textDecoration: "none", color: "var(--gray-700)", minWidth: 80 },
  statsRow: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem", marginBottom: "1.25rem" },
  statCard: { background: "var(--white)", borderRadius: 10, padding: "0.9rem 1rem", boxShadow: "var(--shadow-sm)", display: "flex", alignItems: "center", gap: "0.75rem", textDecoration: "none", color: "inherit", border: "1px solid var(--sand-300)", transition: "box-shadow var(--transition)" },
  statIcon: { fontSize: "1.5rem", flexShrink: 0 },
  statBody: { flex: 1, minWidth: 0 },
  statLabel: { fontSize: "0.72rem", color: "var(--gray-500)", marginBottom: "0.15rem" },
  statValue: { fontSize: "1.35rem", fontWeight: 700, color: "var(--green-900)", lineHeight: 1.2 },
  statUnit: { fontSize: "0.72rem", fontWeight: 400, color: "var(--gray-500)", marginLeft: "0.15rem" },
  progressBar: { marginTop: "0.3rem", height: 4, background: "var(--sand-200)", borderRadius: 2, overflow: "hidden" },
  progressFill: { height: "100%", background: "var(--green-700)", borderRadius: 2, transition: "width 0.5s ease" },
  nextActionCard: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", background: "var(--white)", border: "2px solid var(--green-400)", borderRadius: 10, padding: "0.9rem 1.1rem", marginBottom: "1.25rem", textDecoration: "none", boxShadow: "0 2px 6px rgba(116,198,157,.2)", transition: "box-shadow var(--transition)" },
  nextActionLeft: { flex: 1 },
  nextActionBadge: { display: "inline-block", fontSize: "0.67rem", fontWeight: 700, color: "var(--green-800)", background: "var(--green-100)", borderRadius: 10, padding: "2px 8px", marginBottom: "0.3rem", letterSpacing: "0.03em" },
  nextActionLabel: { fontSize: "0.9rem", fontWeight: 600, color: "var(--gray-800)" },
  nextActionArrow: { fontSize: "1.2rem", color: "var(--green-700)", flexShrink: 0 },
  todoCard: { background: "var(--white)", borderRadius: 10, padding: "1.25rem", boxShadow: "var(--shadow-sm)", marginBottom: "1.25rem", border: "1px solid var(--sand-300)" },
  titleRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2rem" },
  pageTitle: { fontFamily: "var(--font-serif)", fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.2rem" },
  pageSub: { fontSize: "0.85rem", color: "var(--gray-500)" },
  newBtn: { display: "inline-flex", alignItems: "center", gap: "0.4rem", padding: "0.6rem 1.25rem", background: "var(--green-800)", color: "var(--white)", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", fontWeight: 500 },
  empty: { textAlign: "center", padding: "5rem 2rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem" },
  emptyIcon: { fontSize: "3rem", marginBottom: "0.5rem" },
  emptyTitle: { fontFamily: "var(--font-serif)", fontSize: "1.2rem", fontWeight: 700 },
  emptyDesc: { fontSize: "0.9rem", color: "var(--gray-500)", marginBottom: "0.5rem" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.25rem" },
  card: { background: "var(--white)", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-sm)", overflow: "hidden", display: "flex", flexDirection: "column", transition: "box-shadow var(--transition), transform var(--transition)" },
  cardHover: { boxShadow: "var(--shadow-md)", transform: "translateY(-2px)" },
  cardThumbWrap: { position: "relative", height: 180, background: "var(--sand-200)", overflow: "hidden" },
  cardThumb: { width: "100%", height: "100%", objectFit: "cover" },
  cardThumbFallback: { width: "100%", height: "100%", background: "linear-gradient(135deg, var(--green-900), var(--green-700))", display: "flex", alignItems: "center", justifyContent: "center" },
  cardThumbInitial: { fontFamily: "var(--font-serif)", fontSize: "4rem", color: "rgba(255,255,255,0.6)", fontWeight: 300 },
  publicBadge: { position: "absolute", top: 10, right: 10, padding: "0.2rem 0.6rem", borderRadius: 20, fontSize: "0.72rem", fontWeight: 500 },
  publicBadgeOpen: { background: "rgba(45,106,79,0.9)", color: "#fff" },
  publicBadgeLocked: { background: "rgba(0,0,0,0.55)", color: "#fff" },
  cardBody: { padding: "1.1rem 1.25rem", flex: 1 },
  cardName: { fontFamily: "var(--font-serif)", fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.3rem" },
  cardDates: { fontSize: "0.78rem", color: "var(--gray-500)", marginBottom: "0.5rem" },
  cardBio: { fontSize: "0.82rem", color: "var(--gray-500)", lineHeight: 1.6 },
  viewCount: { fontSize: "0.75rem", color: "var(--gray-400)", marginTop: "0.4rem" },
  cardFooter: { padding: "0.75rem 1.25rem", borderTop: "1px solid var(--sand-200)", display: "flex", gap: "0.5rem", flexWrap: "wrap" },
  btnView: { padding: "0.3rem 0.8rem", background: "var(--green-800)", color: "#fff", borderRadius: 6, fontSize: "0.78rem", fontWeight: 500 },
  btnEdit: { padding: "0.3rem 0.8rem", background: "var(--sand-200)", color: "var(--gray-700)", borderRadius: 6, fontSize: "0.78rem" },
  btnQr: { padding: "0.3rem 0.8rem", background: "var(--gray-100)", color: "var(--gray-700)", borderRadius: 6, fontSize: "0.78rem", border: "none", cursor: "pointer" },
  btnDelete: { padding: "0.3rem 0.8rem", background: "transparent", border: "1px solid #FECACA", color: "var(--red)", borderRadius: 6, fontSize: "0.78rem", cursor: "pointer", marginLeft: "auto" },
};
