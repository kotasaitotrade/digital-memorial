import { useState, FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch {
      setError("メールアドレスまたはパスワードが正しくありません");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.root}>
      {/* 左パネル */}
      <div style={s.left}>
        <div style={s.leftInner}>
          <div style={s.logo}>Digital Memorial</div>
          <h1 style={s.tagline}>故人の記憶を、<br />永遠に残す場所。</h1>
          <p style={s.desc}>
            QRコードひとつで、大切な人の物語を<br />
            いつでも・どこからでも届けます。
          </p>
          <div style={s.features}>
            {["墓誌ページの作成・管理", "QRコード自動生成", "写真・略歴・メッセージ", "パスワード保護対応"].map((f) => (
              <div key={f} style={s.featureItem}>
                <span style={s.featureDot} />
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 右パネル */}
      <div style={s.right}>
        <div style={s.formCard}>
          <h2 style={s.formTitle}>ログイン</h2>
          <p style={s.formSub}>アカウントにサインインしてください</p>

          <form onSubmit={handleSubmit} style={s.form}>
            <div style={s.field}>
              <label style={s.label} htmlFor="login-email">メールアドレス</label>
              <input
                id="login-email"
                style={s.input}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                autoComplete="email"
              />
            </div>
            <div style={s.field}>
              <label style={s.label} htmlFor="login-password">パスワード</label>
              <input
                id="login-password"
                style={s.input}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div style={s.errorBox}>
                <span>⚠</span> {error}
              </div>
            )}

            <button style={{ ...s.btn, ...(loading ? s.btnDisabled : {}) }} type="submit" disabled={loading}>
              {loading ? "ログイン中..." : "ログイン"}
            </button>
          </form>

          <p style={s.switchText}>
            アカウントをお持ちでない方は{" "}
            <Link to="/register" style={s.switchLink}>新規登録</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  root: { display: "flex", minHeight: "100vh" },

  left: {
    flex: "0 0 46%",
    background: "linear-gradient(160deg, var(--green-900) 0%, var(--green-700) 100%)",
    display: "flex", alignItems: "center", justifyContent: "center",
    padding: "3rem",
  },
  leftInner: { maxWidth: 380, color: "var(--white)" },
  logo: { fontSize: "0.8rem", letterSpacing: "0.2em", color: "rgba(255,255,255,0.6)", marginBottom: "2rem", textTransform: "uppercase" },
  tagline: { fontFamily: "var(--font-serif)", fontSize: "2.2rem", fontWeight: 700, lineHeight: 1.4, marginBottom: "1.25rem" },
  desc: { fontSize: "0.95rem", color: "rgba(255,255,255,0.75)", lineHeight: 1.8, marginBottom: "2rem" },
  features: { display: "flex", flexDirection: "column", gap: "0.65rem" },
  featureItem: { display: "flex", alignItems: "center", gap: "0.65rem", fontSize: "0.88rem", color: "rgba(255,255,255,0.85)" },
  featureDot: { width: 6, height: 6, borderRadius: "50%", background: "var(--green-400)", flexShrink: 0 },

  right: {
    flex: 1,
    display: "flex", alignItems: "center", justifyContent: "center",
    padding: "2rem",
    background: "var(--sand-100)",
  },
  formCard: {
    width: "100%", maxWidth: 420,
    background: "var(--white)",
    borderRadius: "var(--radius-lg)",
    padding: "2.5rem",
    boxShadow: "var(--shadow-lg)",
  },
  formTitle: { fontFamily: "var(--font-serif)", fontSize: "1.6rem", fontWeight: 700, marginBottom: "0.35rem" },
  formSub: { fontSize: "0.875rem", color: "var(--gray-500)", marginBottom: "2rem" },

  form: { display: "flex", flexDirection: "column", gap: "1.1rem" },
  field: { display: "flex", flexDirection: "column", gap: "0.4rem" },
  label: { fontSize: "0.8rem", fontWeight: 500, color: "var(--gray-700)", letterSpacing: "0.03em" },
  input: {
    padding: "0.7rem 0.9rem",
    border: "1.5px solid var(--gray-300)",
    borderRadius: "var(--radius-sm)",
    fontSize: "0.95rem",
    outline: "none",
    transition: "border-color var(--transition)",
    background: "var(--white)",
  },
  errorBox: {
    background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: "var(--radius-sm)",
    padding: "0.7rem 1rem", fontSize: "0.85rem", color: "var(--red)",
    display: "flex", alignItems: "center", gap: "0.5rem",
  },
  btn: {
    marginTop: "0.4rem",
    padding: "0.8rem",
    background: "var(--green-800)",
    color: "var(--white)",
    border: "none",
    borderRadius: "var(--radius-sm)",
    fontSize: "0.95rem",
    fontWeight: 500,
    letterSpacing: "0.03em",
    transition: "background var(--transition)",
  },
  btnDisabled: { background: "var(--gray-300)", cursor: "not-allowed" },

  switchText: { marginTop: "1.5rem", textAlign: "center", fontSize: "0.85rem", color: "var(--gray-500)" },
  switchLink: { color: "var(--green-700)", fontWeight: 500 },
};
