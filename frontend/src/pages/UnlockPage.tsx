import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import api from "../lib/api";

type Status = "loading" | "ready" | "submitting" | "success" | "error";

export default function UnlockPage() {
  const { personId } = useParams<{ personId: string }>();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [status, setStatus] = useState<Status>("loading");
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!personId || !token) {
      setErrorMsg("無効なURLです。解除キーが含まれていません。");
      setStatus("error");
      return;
    }
    setStatus("ready");
  }, [personId, token]);

  const handleRequest = async () => {
    setStatus("submitting");
    try {
      const res = await api.post(`/digital-key/trusted-persons/${personId}/request?token=${encodeURIComponent(token)}`);
      setIsUnlocked(res.data.is_unlocked);
      setStatus("success");
    } catch {
      setErrorMsg("申請に失敗しました。URLが正しいか、またはすでに申請済みの可能性があります。");
      setStatus("error");
    }
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.icon}>🔐</div>
        <h1 style={s.title}>デジタル遺品鍵 解除申請</h1>

        {status === "loading" && (
          <p style={s.desc}>確認中...</p>
        )}

        {status === "ready" && (
          <>
            <p style={s.desc}>
              あなたは「信頼できる人」として登録されています。
              <br />
              この申請を送ると、登録者のデジタル遺品鍵の解除手続きが開始されます。
            </p>
            <div style={s.warning}>
              ⚠️ この申請は取り消せません。本人が亡くなったことを確認した上で申請してください。
            </div>
            <button style={s.btn} onClick={handleRequest}>
              解除申請を送る
            </button>
          </>
        )}

        {status === "submitting" && (
          <p style={s.desc}>申請中...</p>
        )}

        {status === "success" && (
          <div style={s.success}>
            <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>✅</div>
            <p style={{ margin: 0, fontWeight: 600, fontSize: "1.05rem", color: "#15803d" }}>
              申請を受け付けました
            </p>
            {isUnlocked ? (
              <p style={{ margin: "0.75rem 0 0", color: "#374151", fontSize: "0.9rem" }}>
                解除条件が満たされたため、デジタル遺品鍵が開錠されました。
              </p>
            ) : (
              <p style={{ margin: "0.75rem 0 0", color: "#374151", fontSize: "0.9rem" }}>
                他の信頼者の申請が揃い次第、自動的に開錠されます。
              </p>
            )}
          </div>
        )}

        {status === "error" && (
          <div style={s.error}>
            <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>❌</div>
            <p style={{ margin: 0, color: "#dc2626" }}>{errorMsg}</p>
          </div>
        )}
      </div>
    </div>
  );
}

const GREEN = "#1a5c38";

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "#f5f5f0", display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem" },
  card: { background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.1)", maxWidth: 480, width: "100%", padding: "2.5rem 2rem", textAlign: "center" },
  icon: { fontSize: "3rem", marginBottom: "0.75rem" },
  title: { color: GREEN, fontSize: "1.3rem", margin: "0 0 1.25rem" },
  desc: { color: "#374151", lineHeight: 1.7, fontSize: "0.95rem", margin: "0 0 1.25rem" },
  warning: { background: "#fffbeb", border: "1px solid #fcd34d", borderRadius: 8, padding: "0.85rem 1rem", marginBottom: "1.5rem", fontSize: "0.85rem", color: "#92400e", textAlign: "left" },
  btn: { background: GREEN, color: "#fff", border: "none", padding: "0.8rem 2rem", borderRadius: 10, fontSize: "1rem", fontWeight: 700, cursor: "pointer", width: "100%" },
  success: { background: "#f0fdf4", border: "1px solid #86efac", borderRadius: 10, padding: "1.5rem" },
  error: { background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 10, padding: "1.5rem" },
};
