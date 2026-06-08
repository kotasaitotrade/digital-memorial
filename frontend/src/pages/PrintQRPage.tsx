import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../lib/api";
import type { Memorial } from "../types";

export default function PrintQRPage() {
  const { id } = useParams<{ id: string }>();
  const [memorial, setMemorial] = useState<Memorial | null>(null);

  useEffect(() => {
    api.get(`/memorials/${id}`).then((res) => {
      setMemorial(res.data);
      setTimeout(() => window.print(), 800);
    });
  }, [id]);

  if (!memorial) return <div style={{ textAlign: "center", padding: "2rem" }}>読み込み中...</div>;

  const publicUrl = `${window.location.origin}/m/${memorial.slug}`;

  return (
    <div style={styles.page}>
      <style>{`
        @media print {
          body { margin: 0; }
          .no-print { display: none !important; }
        }
      `}</style>

      <div className="no-print" style={styles.toolbar}>
        <button style={styles.printBtn} onClick={() => window.print()}>印刷する</button>
        <button style={styles.closeBtn} onClick={() => window.close()}>閉じる</button>
      </div>

      {/* A4サイズに複数のQRカードを印刷 */}
      <div style={styles.grid}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} style={styles.card}>
            <div style={styles.cardHeader}>
              <span style={styles.scanText}>SCAN TO REMEMBER</span>
            </div>
            <img
              src={`/uploads/qr/${memorial.slug}.png`}
              alt="QR"
              style={styles.qrImg}
            />
            <div style={styles.cardFooter}>
              <p style={styles.name}>{memorial.name}</p>
              {memorial.death_date && <p style={styles.date}>{memorial.death_date}</p>}
              <p style={styles.url}>{publicUrl}</p>
            </div>
          </div>
        ))}
      </div>

      <p className="no-print" style={styles.hint}>
        A4用紙に6枚分のQRカードが印刷されます。切り取ってプレートに貼付してください。
      </p>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    background: "#fff", minHeight: "100vh", padding: "1rem",
    fontFamily: "'Hiragino Mincho ProN', 'Yu Mincho', Georgia, serif",
  },
  toolbar: {
    display: "flex", gap: "0.75rem", marginBottom: "1.5rem",
    justifyContent: "center",
  },
  printBtn: {
    padding: "0.6rem 1.5rem", background: "#4a6741", color: "#fff",
    border: "none", borderRadius: 6, fontSize: "1rem", cursor: "pointer",
  },
  closeBtn: {
    padding: "0.6rem 1.5rem", background: "#fff", color: "#6b6b6b",
    border: "1px solid #e0ddd8", borderRadius: 6, fontSize: "1rem", cursor: "pointer",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "1rem",
    maxWidth: 700,
    margin: "0 auto",
  },
  card: {
    border: "2px dashed #ccc", borderRadius: 8,
    padding: "0.75rem", textAlign: "center",
    display: "flex", flexDirection: "column", alignItems: "center",
    gap: "0.5rem",
  },
  cardHeader: { width: "100%" },
  scanText: {
    fontSize: "0.6rem", letterSpacing: "0.1em",
    color: "#6b6b6b", fontFamily: "sans-serif",
  },
  qrImg: { width: 120, height: 120 },
  cardFooter: { width: "100%" },
  name: { fontSize: "0.85rem", fontWeight: 700, marginBottom: "0.1rem" },
  date: { fontSize: "0.7rem", color: "#6b6b6b", marginBottom: "0.1rem" },
  url: {
    fontSize: "0.5rem", color: "#9b9b9b",
    wordBreak: "break-all", fontFamily: "monospace",
  },
  hint: {
    textAlign: "center", color: "#6b6b6b", fontSize: "0.85rem",
    marginTop: "1.5rem",
  },
};
