import { useEffect, useRef } from "react";
import type { Memorial } from "../types";

interface Props {
  memorial: Memorial;
  onClose: () => void;
}

export default function QRModal({ memorial, onClose }: Props) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const qrUrl = `/uploads/qr/${memorial.slug}.png`;
  const publicUrl = `${window.location.origin}/m/${memorial.slug}`;

  const handleDownload = () => {
    const a = document.createElement("a");
    a.href = qrUrl;
    a.download = `qr_${memorial.name}.png`;
    a.click();
  };

  const handlePrint = () => {
    window.open(`/memorials/${memorial.id}/print-qr`, "_blank");
  };

  return (
    <div
      ref={overlayRef}
      style={styles.overlay}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div style={styles.modal}>
        <button style={styles.closeBtn} onClick={onClose}>✕</button>

        <h2 style={styles.title}>{memorial.name}</h2>
        <p style={styles.subtitle}>墓誌QRコード</p>

        <div style={styles.qrWrapper}>
          <img src={qrUrl} alt="QRコード" style={styles.qrImg} />
        </div>

        <p style={styles.urlLabel}>アクセスURL</p>
        <p style={styles.url}>{publicUrl}</p>

        <div style={styles.actions}>
          <button style={styles.downloadBtn} onClick={handleDownload}>
            ダウンロード
          </button>
          <button style={styles.printBtn} onClick={handlePrint}>
            印刷用ページ
          </button>
        </div>

        <p style={styles.hint}>
          このQRコードをプレートに印刷することで、<br />
          スマートフォンから墓誌ページにアクセスできます。
        </p>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
  },
  modal: {
    background: "#fff", borderRadius: 12, padding: "2rem",
    width: "100%", maxWidth: 420, position: "relative", textAlign: "center",
  },
  closeBtn: {
    position: "absolute", top: "1rem", right: "1rem",
    background: "none", border: "none", fontSize: "1.2rem", cursor: "pointer", color: "#6b6b6b",
  },
  title: { fontSize: "1.3rem", fontWeight: 700, marginBottom: "0.25rem" },
  subtitle: { color: "#6b6b6b", fontSize: "0.85rem", marginBottom: "1.5rem" },
  qrWrapper: {
    background: "#fff", border: "2px solid #e0ddd8", borderRadius: 8,
    padding: "1rem", display: "inline-block", marginBottom: "1.25rem",
  },
  qrImg: { width: 200, height: 200, display: "block" },
  urlLabel: { fontSize: "0.75rem", color: "#6b6b6b", marginBottom: "0.25rem" },
  url: {
    fontSize: "0.8rem", color: "#4a6741", background: "#f5f5f0",
    padding: "0.5rem", borderRadius: 4, wordBreak: "break-all", marginBottom: "1.5rem",
  },
  actions: { display: "flex", gap: "0.75rem", justifyContent: "center", marginBottom: "1.25rem" },
  downloadBtn: {
    padding: "0.65rem 1.25rem", background: "#4a6741", color: "#fff",
    border: "none", borderRadius: 6, fontSize: "0.9rem", cursor: "pointer",
  },
  printBtn: {
    padding: "0.65rem 1.25rem", background: "#fff", color: "#4a6741",
    border: "2px solid #4a6741", borderRadius: 6, fontSize: "0.9rem", cursor: "pointer",
  },
  hint: { fontSize: "0.78rem", color: "#9b9b9b", lineHeight: 1.6 },
};
