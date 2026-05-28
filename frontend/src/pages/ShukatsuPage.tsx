import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../hooks/useAuth";
import type { ChecklistItem } from "../types";

const CATEGORIES = ["相続", "遺言", "医療", "葬儀", "デジタル", "人間関係", "ペット", "思い出"];
const PRIORITY_COLOR: Record<string, string> = {
  必須: "#dc2626",
  推奨: "#d97706",
  任意: "#6b7280",
};

function StarRating({ stars }: { stars: number }) {
  return (
    <span style={{ letterSpacing: 2, fontSize: "1rem" }}>
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} style={{ color: i < stars ? "#f59e0b" : "#d1d5db" }}>★</span>
      ))}
    </span>
  );
}

export default function ShukatsuPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>("すべて");

  useEffect(() => {
    api.get("/checklist").then((r) => {
      const data = r.data;
      setItems(Array.isArray(data) ? data : (data.items ?? []));
    });
  }, []);

  const toggle = async (task_key: string, current: boolean) => {
    await api.post("/checklist/toggle", { task_key, is_completed: !current });
    setItems((prev) =>
      prev.map((it) =>
        it.task_key === task_key ? { ...it, is_completed: !current } : it
      )
    );
  };

  const completed = items.filter((i) => i.is_completed).length;
  const total = items.length;
  const score = total ? Math.round((completed / total) * 100) : 0;

  const filtered =
    activeCategory === "すべて"
      ? items
      : items.filter((i) => i.category === activeCategory);

  return (
    <div style={s.page}>
      <header style={s.header}>
        <div style={s.headerInner}>
          <div style={s.headerLeft}>
            <Link to="/dashboard" style={s.backLink}>← 墓誌一覧</Link>
            <span style={s.headerLogo}>終活ノート</span>
          </div>
          <div style={s.headerRight}>
            <span style={s.headerUser}>{user?.name}</span>
            <button style={s.logoutBtn} onClick={() => { logout(); navigate("/login"); }}>
              ログアウト
            </button>
          </div>
        </div>
      </header>

      <main style={s.main}>
        {/* スコアカード */}
        <div style={s.scoreCard}>
          <div style={s.scoreLeft}>
            <div style={s.scoreTitle}>終活準備スコア</div>
            <div style={s.scoreNum}>{score}<span style={s.scorePct}>%</span></div>
            <div style={s.scoreDesc}>{completed} / {total} 項目完了</div>
          </div>
          <div style={s.scoreRight}>
            <div style={s.gauge}>
              <svg viewBox="0 0 120 120" style={{ width: 120, height: 120 }}>
                <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="10" />
                <circle
                  cx="60" cy="60" r="50" fill="none"
                  stroke={score >= 80 ? "#1a5c38" : score >= 50 ? "#d97706" : "#dc2626"}
                  strokeWidth="10"
                  strokeDasharray={`${(score / 100) * 314} 314`}
                  strokeLinecap="round"
                  transform="rotate(-90 60 60)"
                />
                <text x="60" y="65" textAnchor="middle" fontSize="22" fontWeight="bold" fill="#1a1a1a">{score}%</text>
              </svg>
            </div>
          </div>
        </div>

        {/* クイックリンク */}
        <div style={{ ...s.quickLinks, gridTemplateColumns: "repeat(3, 1fr)" }}>
          <Link to="/estate" style={s.quickCard}>
            <div style={s.quickIcon}>⚖️</div>
            <div style={s.quickLabel}>相続の棚卸し</div>
          </Link>
          <Link to="/ending-note" style={s.quickCard}>
            <div style={s.quickIcon}>📋</div>
            <div style={s.quickLabel}>エンディングノート</div>
          </Link>
          <Link to="/dashboard" style={s.quickCard}>
            <div style={s.quickIcon}>🕊️</div>
            <div style={s.quickLabel}>墓誌の管理</div>
          </Link>
          <Link to="/digital-key" style={s.quickCard}>
            <div style={s.quickIcon}>🔐</div>
            <div style={s.quickLabel}>デジタル遺品鍵</div>
          </Link>
          <Link to="/settings/reminders" style={s.quickCard}>
            <div style={s.quickIcon}>🔔</div>
            <div style={s.quickLabel}>リマインダー設定</div>
          </Link>
          <Link to="/account" style={s.quickCard}>
            <div style={s.quickIcon}>👤</div>
            <div style={s.quickLabel}>アカウント設定</div>
          </Link>
        </div>

        {/* チェックリスト */}
        <div style={s.section}>
          <h2 style={s.sectionTitle}>終活チェックリスト</h2>

          {/* カテゴリフィルター */}
          <div style={s.tabs}>
            {["すべて", ...CATEGORIES].map((cat) => (
              <button
                key={cat}
                style={{ ...s.tab, ...(activeCategory === cat ? s.tabActive : {}) }}
                onClick={() => setActiveCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* リスト */}
          <div style={s.list}>
            {filtered.map((item) => (
              <div
                key={item.task_key}
                style={{ ...s.listItem, ...(item.is_completed ? s.listItemDone : {}) }}
              >
                <button
                  style={{ ...s.checkbox, ...(item.is_completed ? s.checkboxDone : {}) }}
                  onClick={() => toggle(item.task_key, item.is_completed)}
                >
                  {item.is_completed && <span style={s.checkmark}>✓</span>}
                </button>
                <div style={s.itemBody}>
                  <div style={{ ...s.itemLabel, ...(item.is_completed ? s.itemLabelDone : {}) }}>
                    {item.label}
                  </div>
                  <div style={s.itemMeta}>
                    <span style={s.categoryBadge}>{item.category}</span>
                    <span style={{ ...s.priorityBadge, color: PRIORITY_COLOR[item.priority] }}>
                      {item.priority}
                    </span>
                    <StarRating stars={item.stars ?? 0} />
                  </div>
                </div>
                {!item.is_completed && (
                  <Link to={item.link} style={s.goBtn}>入力する →</Link>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 免責事項 */}
        <div style={s.disclaimer}>
          ※ 本サービスの相続計算・法的情報は参考情報です。正確な判断には弁護士・司法書士・税理士にご相談ください。
        </div>
      </main>
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
  scoreCard: { background: "#fff", borderRadius: 12, padding: "1.5rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center", boxShadow: "0 1px 4px rgba(0,0,0,.07)", marginBottom: "1.5rem" },
  scoreLeft: {},
  scoreTitle: { fontSize: "0.85rem", color: "#6b7280", marginBottom: 4 },
  scoreNum: { fontSize: "3rem", fontWeight: 800, color: GREEN, lineHeight: 1 },
  scorePct: { fontSize: "1.5rem", fontWeight: 600 },
  scoreDesc: { fontSize: "0.85rem", color: "#6b7280", marginTop: 6 },
  scoreRight: {},
  gauge: {},
  quickLinks: { display: "grid", gap: "1rem", marginBottom: "2rem" },
  quickCard: { background: "#fff", borderRadius: 10, padding: "1.25rem", textAlign: "center" as const, textDecoration: "none", boxShadow: "0 1px 4px rgba(0,0,0,.07)", transition: "box-shadow 0.2s", border: `2px solid transparent` },
  quickIcon: { fontSize: "2rem", marginBottom: 8 },
  quickLabel: { fontSize: "0.9rem", fontWeight: 600, color: "#1a1a1a" },
  section: { background: "#fff", borderRadius: 12, padding: "1.5rem", boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  sectionTitle: { fontSize: "1.1rem", fontWeight: 700, color: "#1a1a1a", marginBottom: "1rem", marginTop: 0 },
  tabs: { display: "flex", gap: "0.4rem", flexWrap: "wrap" as const, marginBottom: "1rem" },
  tab: { fontSize: "0.8rem", padding: "0.3rem 0.75rem", border: "1px solid #e5e7eb", borderRadius: 20, background: "#fff", cursor: "pointer", color: "#374151" },
  tabActive: { background: GREEN, color: "#fff", borderColor: GREEN },
  list: { display: "flex", flexDirection: "column" as const, gap: "0.5rem" },
  listItem: { display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem 1rem", borderRadius: 8, border: "1px solid #f3f4f6", background: "#fafafa" },
  listItemDone: { background: "#f0fdf4", borderColor: "#bbf7d0" },
  checkbox: { width: 24, height: 24, borderRadius: "50%", border: `2px solid #d1d5db`, background: "#fff", cursor: "pointer", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" },
  checkboxDone: { background: GREEN, borderColor: GREEN },
  checkmark: { color: "#fff", fontSize: "0.75rem", fontWeight: 700 },
  itemBody: { flex: 1 },
  itemLabel: { fontSize: "0.9rem", fontWeight: 500, color: "#1a1a1a" },
  itemLabelDone: { color: "#9ca3af", textDecoration: "line-through" },
  itemMeta: { display: "flex", gap: "0.5rem", marginTop: 3 },
  categoryBadge: { fontSize: "0.7rem", background: "#f3f4f6", color: "#6b7280", padding: "1px 6px", borderRadius: 10 },
  priorityBadge: { fontSize: "0.7rem", fontWeight: 600 },
  goBtn: { fontSize: "0.8rem", color: GREEN, textDecoration: "none", whiteSpace: "nowrap" as const, flexShrink: 0 },
  disclaimer: { marginTop: "1.5rem", fontSize: "0.75rem", color: "#9ca3af", textAlign: "center" as const, lineHeight: 1.6 },
};
