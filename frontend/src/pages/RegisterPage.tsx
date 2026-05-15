import { useState, FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await axios.post("/auth/register", { name, email, password });
      navigate("/login");
    } catch {
      setError("登録に失敗しました。メールアドレスが既に使用されている可能性があります");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>新規登録</h1>
        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>お名前</label>
          <input style={styles.input} type="text" value={name} onChange={(e) => setName(e.target.value)} required />
          <label style={styles.label}>メールアドレス</label>
          <input style={styles.input} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <label style={styles.label}>パスワード</label>
          <input style={styles.input} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.button} type="submit">登録する</button>
        </form>
        <p style={styles.link}>
          既にアカウントをお持ちの方は <Link to="/login">ログイン</Link>
        </p>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--color-bg)" },
  card: { background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "2.5rem", width: "100%", maxWidth: 400 },
  title: { fontSize: "1.6rem", fontWeight: 700, marginBottom: "2rem", textAlign: "center" },
  form: { display: "flex", flexDirection: "column", gap: "0.75rem" },
  label: { fontSize: "0.85rem", color: "var(--color-text-muted)" },
  input: { padding: "0.6rem 0.75rem", border: "1px solid var(--color-border)", borderRadius: 4, fontSize: "1rem" },
  button: { marginTop: "0.5rem", padding: "0.75rem", background: "var(--color-primary)", color: "#fff", border: "none", borderRadius: 4, fontSize: "1rem" },
  error: { color: "var(--color-error)", fontSize: "0.85rem" },
  link: { marginTop: "1.5rem", textAlign: "center", fontSize: "0.85rem", color: "var(--color-text-muted)" },
};
