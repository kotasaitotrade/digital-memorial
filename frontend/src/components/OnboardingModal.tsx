import { useState } from "react";

const STEPS = [
  {
    icon: "📋",
    title: "エンディングノート",
    desc: "医療・葬儀の希望、家族へのメッセージ、デジタル資産の処理方法などを記録できます。自動保存で書きかけの心配なし。",
    link: "/ending-note",
    linkLabel: "エンディングノートを書く",
  },
  {
    icon: "⚖️",
    title: "相続計画",
    desc: "家族構成と財産を入力すると、法定相続分・遺留分・相続税概算を自動計算します。民法の複雑なケース（代襲相続・半血兄弟）にも対応。",
    link: "/estate",
    linkLabel: "相続計画を作成する",
  },
  {
    icon: "🪦",
    title: "デジタル墓誌",
    desc: "故人のプロフィール・写真・家族からのメッセージをQRコードでいつでも閲覧できます。パスワード保護にも対応。",
    link: "/memorials/new",
    linkLabel: "墓誌を作成する",
  },
];

interface Props {
  onClose: () => void;
}

export default function OnboardingModal({ onClose }: Props) {
  const [step, setStep] = useState(0);

  const isLast = step === STEPS.length - 1;
  const current = STEPS[step];

  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.modal} onClick={(e) => e.stopPropagation()}>
        <div style={s.header}>
          <span style={s.logoText}>Digital Memorial へようこそ</span>
          <button style={s.closeBtn} onClick={onClose}>✕</button>
        </div>

        <div style={s.stepIndicator}>
          {STEPS.map((_, i) => (
            <div key={i} style={{ ...s.dot, ...(i === step ? s.dotActive : i < step ? s.dotDone : {}) }} />
          ))}
        </div>

        <div style={s.body}>
          <div style={s.icon}>{current.icon}</div>
          <h2 style={s.title}>{current.title}</h2>
          <p style={s.desc}>{current.desc}</p>
        </div>

        <div style={s.footer}>
          {step > 0 && (
            <button style={s.prevBtn} onClick={() => setStep((n) => n - 1)}>← 戻る</button>
          )}
          <div style={{ flex: 1 }} />
          {isLast ? (
            <button style={s.primaryBtn} onClick={onClose}>始める →</button>
          ) : (
            <button style={s.primaryBtn} onClick={() => setStep((n) => n + 1)}>次へ →</button>
          )}
        </div>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  overlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem" },
  modal: { background: "#fff", borderRadius: 12, boxShadow: "0 20px 60px rgba(0,0,0,0.25)", maxWidth: 480, width: "100%", overflow: "hidden" },
  header: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1.1rem 1.5rem", borderBottom: "1px solid #f0f0f0" },
  logoText: { fontFamily: "Georgia, serif", fontSize: "0.95rem", fontWeight: 700, color: "#14532d" },
  closeBtn: { background: "none", border: "none", fontSize: "1rem", cursor: "pointer", color: "#9ca3af", padding: "0.2rem" },
  stepIndicator: { display: "flex", gap: "0.4rem", justifyContent: "center", padding: "1rem 0 0" },
  dot: { width: 8, height: 8, borderRadius: "50%", background: "#e5e7eb", transition: "background 0.2s" },
  dotActive: { background: "#16a34a", transform: "scale(1.25)" },
  dotDone: { background: "#86efac" },
  body: { padding: "1.5rem 2rem 1rem", textAlign: "center" as const },
  icon: { fontSize: "3rem", marginBottom: "0.75rem" },
  title: { fontSize: "1.2rem", fontWeight: 700, color: "#1f2937", marginBottom: "0.75rem" },
  desc: { fontSize: "0.9rem", color: "#6b7280", lineHeight: 1.7 },
  footer: { display: "flex", alignItems: "center", padding: "1rem 1.5rem 1.5rem", gap: "0.75rem" },
  prevBtn: { padding: "0.6rem 1.1rem", background: "transparent", border: "1.5px solid #d1d5db", borderRadius: 8, fontSize: "0.88rem", cursor: "pointer", color: "#6b7280" },
  primaryBtn: { padding: "0.65rem 1.5rem", background: "#16a34a", color: "#fff", border: "none", borderRadius: 8, fontSize: "0.9rem", fontWeight: 600, cursor: "pointer" },
};
