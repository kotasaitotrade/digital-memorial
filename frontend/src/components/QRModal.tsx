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
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const qrUrl = `/uploads/qr/${memorial.slug}.png`;
  const publicUrl = `${window.location.origin}/m/${memorial.slug}`;

  return (
    <div
      ref={overlayRef}
      style={s.overlay}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div style={s.modal}>
        {/* 閉じるボタン */}
        <button style={s.closeBtn} onClick={onClose} aria-label="閉じる">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 2l12 12M14 2L2 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>

        {/* ヘッダー */}
        <div style={s.modalHeader}>
          <h2 style={s.modalTitle}>{memorial.name}</h2>
          <p style={s.modalSub}>墓誌QRコード</p>
        </div>

        {/* QRコード */}
        <div style={s.qrSection}>
          <div style={s.qrFrame}>
            <p style={s.qrScanText}>SCAN TO REMEMBER</p>
            <img src={qrUrl} alt="QRコード" style={s.qrImg} />
            <p style={s.qrName}>{memorial.name}</p>
            {memorial.death_date && <p style={s.qrDate}>{memorial.death_date}</p>}
          </div>
        </div>

        {/* URL */}
        <div style={s.urlSection}>
          <p style={s.urlLabel}>アクセスURL</p>
          <div style={s.urlBox}>
            <span style={s.urlText}>{publicUrl}</span>
            <button style={s.copyBtn} onClick={() => navigator.clipboard.writeText(publicUrl)}>コピー</button>
          </div>
        </div>

        {/* アクション */}
        <div style={s.actions}>
          <a href={qrUrl} download={`qr_${memorial.name}.png`} style={s.downloadBtn}>
            ⬇ ダウンロード
          </a>
          <button style={s.printBtn} onClick={() => window.open(`/memorials/${memorial.id}/print-qr`, "_blank")}>
            🖨 印刷用ページ
          </button>
        </div>

        <p style={s.hint}>
          このQRコードをプレートに印刷することで、スマートフォンから墓誌ページにアクセスできます。
        </p>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed", inset: 0,
    background: "rgba(17,24,39,0.6)",
    backdropFilter: "blur(4px)",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 1000, padding: "1rem",
  },
  modal: {
    background: "var(--white)",
    borderRadius: "var(--radius-lg)",
    boxShadow: "var(--shadow-lg)",
    width: "100%", maxWidth: 440,
    padding: "2rem",
    position: "relative",
    display: "flex", flexDirection: "column", gap: "1.25rem",
  },
  closeBtn: {
    position: "absolute", top: "1rem", right: "1rem",
    background: "var(--gray-100)", border: "none",
    borderRadius: "50%", width: 32, height: 32,
    display: "flex", alignItems: "center", justifyContent: "center",
    cursor: "pointer", color: "var(--gray-500)",
  },
  modalHeader: { textAlign: "center" },
  modalTitle: { fontFamily: "var(--font-serif)", fontSize: "1.3rem", fontWeight: 700, marginBottom: "0.2rem" },
  modalSub: { fontSize: "0.82rem", color: "var(--gray-500)" },

  qrSection: { display: "flex", justifyContent: "center" },
  qrFrame: {
    background: "var(--white)",
    border: "2px solid var(--sand-300)",
    borderRadius: "var(--radius-md)",
    padding: "1.25rem",
    textAlign: "center",
    display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem",
    boxShadow: "var(--shadow-sm)",
  },
  qrScanText: { fontSize: "0.6rem", letterSpacing: "0.2em", color: "var(--gray-500)", textTransform: "uppercase" as const },
  qrImg: { width: 180, height: 180, display: "block" },
  qrName: { fontFamily: "var(--font-serif)", fontSize: "0.9rem", fontWeight: 700 },
  qrDate: { fontSize: "0.72rem", color: "var(--gray-500)" },

  urlSection: {},
  urlLabel: { fontSize: "0.75rem", color: "var(--gray-500)", marginBottom: "0.4rem" },
  urlBox: { display: "flex", alignItems: "center", gap: "0.5rem", background: "var(--sand-100)", borderRadius: "var(--radius-sm)", padding: "0.5rem 0.75rem" },
  urlText: { flex: 1, fontSize: "0.78rem", color: "var(--green-800)", wordBreak: "break-all" },
  copyBtn: { padding: "0.25rem 0.6rem", background: "var(--green-800)", color: "#fff", border: "none", borderRadius: 4, fontSize: "0.72rem", cursor: "pointer", flexShrink: 0 },

  actions: { display: "flex", gap: "0.75rem" },
  downloadBtn: {
    flex: 1, padding: "0.7rem",
    background: "var(--green-800)", color: "#fff",
    borderRadius: "var(--radius-sm)", fontSize: "0.88rem",
    textAlign: "center", fontWeight: 500,
  },
  printBtn: {
    flex: 1, padding: "0.7rem",
    background: "var(--white)", color: "var(--green-800)",
    border: "2px solid var(--green-800)", borderRadius: "var(--radius-sm)",
    fontSize: "0.88rem", cursor: "pointer", fontWeight: 500,
  },

  hint: { fontSize: "0.75rem", color: "var(--gray-500)", textAlign: "center", lineHeight: 1.6 },
};
