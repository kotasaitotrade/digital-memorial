import { useEffect, useRef, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { autoCheck } from "../lib/autoCheck";
import { useAuth } from "../hooks/useAuth";
import type { EndingNote, BequestItem, DigitalAssetItem, SubscriptionItem, EmergencyContact, PetItem } from "../types";

const TABS = ["医療・介護", "葬儀", "形見分け", "デジタル資産", "緊急連絡先", "ペット", "お気に入り", "家族へのメッセージ", "追悼メッセージ", "ビデオメッセージ"] as const;
type Tab = (typeof TABS)[number];

interface ScheduledMessage {
  id: number;
  recipient_name: string;
  recipient_email: string;
  subject: string;
  body: string;
  is_sent: boolean;
  created_at: string;
}

interface VideoMessage {
  id: number;
  title: string;
  description: string | null;
  file_path: string;
  file_size: number | null;
  duration_seconds: number | null;
  created_at: string;
}

const GREEN = "#1a5c38";

function tabHasContent(tab: Tab, draft: Partial<EndingNote>, note: EndingNote | null, scheduledMessages: ScheduledMessage[], videoMessages: VideoMessage[]): boolean {
  if (!note) return false;
  switch (tab) {
    case "医療・介護": return !!(draft.life_prolonging || draft.cpr || draft.organ_donation || draft.care_location || draft.medications || draft.medical_notes);
    case "葬儀": return !!(draft.funeral_style || draft.funeral_notes || draft.funeral_music || draft.burial_preference || draft.kaimyo_preference);
    case "形見分け": return (note.bequest_items?.length ?? 0) > 0;
    case "デジタル資産": return (note.digital_assets?.length ?? 0) > 0 || (note.subscriptions?.length ?? 0) > 0;
    case "緊急連絡先": return (note.emergency_contacts?.length ?? 0) > 0;
    case "ペット": return (note.pets?.length ?? 0) > 0;
    case "お気に入り": return !!(draft.favorite_music || draft.favorite_movies || draft.favorite_foods);
    case "家族へのメッセージ": return !!(draft.family_message);
    case "追悼メッセージ": return scheduledMessages.length > 0;
    case "ビデオメッセージ": return videoMessages.length > 0;
    default: return false;
  }
}

export default function EndingNotePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [note, setNote] = useState<EndingNote | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("医療・介護");
  const [saving, setSaving] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [, forceUpdate] = useState(0);
  const [draft, setDraft] = useState<Partial<EndingNote>>({});
  const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
  const [videoMessages, setVideoMessages] = useState<VideoMessage[]>([]);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.get("/ending-note").then((r) => { setNote(r.data); setDraft(r.data); });
    api.get("/scheduled-messages").then((r) => setScheduledMessages(r.data));
    api.get("/video-messages").then((r) => setVideoMessages(r.data));
  }, []);

  const updateDraft = (key: keyof EndingNote, val: string) => {
    setDraft((p) => ({ ...p, [key]: val }));
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => autoSave({ [key]: val }), 1000);
  };

  const autoSave = async (partial: Partial<EndingNote>) => {
    setSaving(true);
    const r = await api.put("/ending-note", partial);
    setNote(r.data);
    setSaving(false);
    setLastSavedAt(new Date());
    if ("medical_prolonging" in partial || "medical_no_prolonging" in partial) autoCheck("medical_prolonging_set");
    if ("doctor_name" in partial || "prescription_memo" in partial) autoCheck("medical_doctor_recorded");
    if ("organ_donation" in partial) autoCheck("medical_organ_set");
    if ("funeral_style" in partial || "funeral_scale" in partial) autoCheck("funeral_style_set");
    if ("family_message" in partial && partial.family_message) autoCheck("family_message_written");
  };

  const savedLabel = (() => {
    if (saving) return "保存中...";
    if (!lastSavedAt) return null;
    const sec = Math.round((Date.now() - lastSavedAt.getTime()) / 1000);
    if (sec < 5) return "保存しました";
    if (sec < 60) return `${sec}秒前に保存`;
    return `${Math.floor(sec / 60)}分前に保存`;
  })();

  const refreshNote = () => api.get("/ending-note").then((r) => { setNote(r.data); setDraft(r.data); });

  // 「○秒前に保存」ラベルを毎秒更新
  useEffect(() => {
    if (!lastSavedAt) return;
    const id = setInterval(() => forceUpdate((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, [lastSavedAt]);

  if (!note) return <div style={{ padding: "4rem", textAlign: "center" as const }}>読み込み中...</div>;

  return (
    <div style={s.page}>
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          .print-only { display: block !important; }
          header { display: none !important; }
          @page { margin: 1.5cm; }
        }
        .print-only { display: none; }
      ` }} />
      <header style={s.header}>
        <div style={s.headerInner}>
          <div style={s.headerLeft}>
            <Link to="/shukatsu" style={s.backLink} className="no-print">← 終活ノート</Link>
            <span style={s.headerLogo}>エンディングノート</span>
          </div>
          <div style={s.headerRight}>
            {savedLabel && <span style={saving ? s.savingLabel : s.savedLabel}>{savedLabel}</span>}
            <span style={s.headerUser}>{user?.name}</span>
            <button style={{ ...s.logoutBtn, background: "#0891b2", color: "#fff", border: "none" }} className="no-print" onClick={() => window.print()}>🖨 PDF出力</button>
            <button style={s.logoutBtn} className="no-print" onClick={() => { logout(); navigate("/login"); }}>ログアウト</button>
          </div>
        </div>
      </header>

      <main style={s.main}>
        {/* タブ（画面のみ） */}
        <div style={s.tabBar} className="no-print">
          {TABS.map((tab) => {
            const done = tabHasContent(tab, draft, note, scheduledMessages, videoMessages);
            return (
              <button
                key={tab}
                style={{ ...s.tab, ...(activeTab === tab ? s.tabActive : {}) }}
                onClick={() => setActiveTab(tab)}
              >
                {done && <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: "50%", background: activeTab === tab ? "#fff" : GREEN, marginRight: "0.3rem", verticalAlign: "middle", flexShrink: 0 }} />}
                {tab}
              </button>
            );
          })}
        </div>

        {/* 各セクション（画面のみ） */}
        <div className="no-print">
          {activeTab === "医療・介護" && (
            <MedicalSection draft={draft} onUpdate={updateDraft} />
          )}
          {activeTab === "葬儀" && (
            <FuneralSection draft={draft} note={note} onUpdate={updateDraft} onRefresh={refreshNote} />
          )}
          {activeTab === "形見分け" && (
            <BequestSection items={note.bequest_items} onRefresh={refreshNote} />
          )}
          {activeTab === "デジタル資産" && (
            <DigitalSection items={note.digital_assets} subs={note.subscriptions} onRefresh={refreshNote} />
          )}
          {activeTab === "緊急連絡先" && (
            <ContactSection items={note.emergency_contacts} onRefresh={refreshNote} />
          )}
          {activeTab === "ペット" && (
            <PetSection items={note.pets} onRefresh={refreshNote} />
          )}
          {activeTab === "お気に入り" && (
            <FavoritesSection draft={draft} onUpdate={updateDraft} />
          )}
          {activeTab === "家族へのメッセージ" && (
            <MessageSection draft={draft} onUpdate={updateDraft} />
          )}
          {activeTab === "追悼メッセージ" && (
            <ScheduledMessageSection
              messages={scheduledMessages}
              onRefresh={() => api.get("/scheduled-messages").then((r) => setScheduledMessages(r.data))}
            />
          )}
          {activeTab === "ビデオメッセージ" && (
            <VideoMessageSection
              videos={videoMessages}
              onRefresh={() => api.get("/video-messages").then((r) => setVideoMessages(r.data))}
            />
          )}
        </div>

        {/* 印刷用: 全セクションを一覧表示 */}
        <PrintAllView note={note} draft={draft} userName={user?.name ?? ""} />
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 印刷専用ビュー（@media print でのみ表示）
// ─────────────────────────────────────────────────
function PrintRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div style={{ display: "flex", gap: "1rem", padding: "0.3rem 0", borderBottom: "1px solid #f3f4f6", fontSize: "0.88rem" }}>
      <span style={{ minWidth: 160, color: "#6b7280", flexShrink: 0 }}>{label}</span>
      <span style={{ color: "#1a1a1a", whiteSpace: "pre-wrap" as const }}>{value}</span>
    </div>
  );
}

function PrintSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "1.5rem", pageBreakInside: "avoid" as const }}>
      <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1a5c38", borderBottom: "2px solid #1a5c38", paddingBottom: 4, marginBottom: 8 }}>{title}</h2>
      {children}
    </div>
  );
}

function PrintAllView({ note, draft, userName }: { note: EndingNote; draft: Partial<EndingNote>; userName: string }) {
  const today = new Date().toLocaleDateString("ja-JP", { year: "numeric", month: "long", day: "numeric" });
  return (
    <div className="print-only" style={{ fontFamily: "sans-serif", lineHeight: 1.8 }}>
      <h1 style={{ textAlign: "center" as const, fontSize: "1.4rem", marginBottom: "0.25rem" }}>エンディングノート</h1>
      <p style={{ textAlign: "center" as const, fontSize: "0.85rem", color: "#6b7280", marginBottom: "2rem" }}>{userName}　{today}時点</p>

      <PrintSection title="医療・介護の希望">
        <PrintRow label="延命治療" value={draft.life_prolonging} />
        <PrintRow label="心肺蘇生（CPR）" value={draft.cpr} />
        <PrintRow label="胃ろう・経管栄養" value={draft.tube_feeding} />
        <PrintRow label="臓器提供" value={draft.organ_donation} />
        <PrintRow label="臓器提供詳細" value={draft.organ_donation_detail} />
        <PrintRow label="介護の希望場所" value={draft.care_location} />
        <PrintRow label="かかりつけ医" value={draft.primary_doctor} />
        <PrintRow label="服用中の薬" value={draft.medications} />
        <PrintRow label="その他備考" value={draft.medical_notes} />
      </PrintSection>

      <PrintSection title="葬儀の希望">
        <PrintRow label="葬儀スタイル" value={draft.funeral_style} />
        <PrintRow label="宗教・宗派" value={draft.religion} />
        <PrintRow label="流したい音楽" value={draft.funeral_music} />
        <PrintRow label="お花の希望" value={draft.funeral_flower_type} />
        <PrintRow label="戒名への希望" value={draft.kaimyo_preference} />
        <PrintRow label="会葬者人数目安" value={draft.funeral_guest_limit ? `${draft.funeral_guest_limit}名程度` : undefined} />
        <PrintRow label="埋葬方法" value={draft.burial_preference} />
        <PrintRow label="その他備考" value={draft.funeral_notes} />
      </PrintSection>

      {note.bequest_items.length > 0 && (
        <PrintSection title="形見分けリスト">
          {note.bequest_items.map(it => (
            <div key={it.id} style={{ fontSize: "0.88rem", padding: "0.25rem 0", borderBottom: "1px solid #f3f4f6" }}>
              <strong>{it.item_name}</strong> → {it.recipient}{it.notes ? `　（${it.notes}）` : ""}
            </div>
          ))}
        </PrintSection>
      )}

      {(note.digital_assets.length > 0 || note.subscriptions.length > 0) && (
        <PrintSection title="デジタル資産・サブスクリプション">
          {note.digital_assets.map(it => (
            <div key={it.id} style={{ fontSize: "0.88rem", padding: "0.25rem 0", borderBottom: "1px solid #f3f4f6" }}>
              <strong>{it.service_name}</strong>{it.account ? ` (${it.account})` : ""}
              {it.after_death_instruction ? `　死後処理: ${it.after_death_instruction}` : ""}
            </div>
          ))}
          {note.subscriptions.map(it => (
            <div key={it.id} style={{ fontSize: "0.88rem", padding: "0.25rem 0", borderBottom: "1px solid #f3f4f6" }}>
              <strong>{it.service_name}</strong>
              {it.monthly_fee ? ` 月額${it.monthly_fee.toLocaleString()}円` : ""}
              {it.cancellation_method ? `　解約: ${it.cancellation_method}` : ""}
            </div>
          ))}
        </PrintSection>
      )}

      {note.emergency_contacts.length > 0 && (
        <PrintSection title="緊急連絡先">
          {[...note.emergency_contacts].sort((a, b) => a.priority - b.priority).map(it => (
            <div key={it.id} style={{ fontSize: "0.88rem", padding: "0.25rem 0", borderBottom: "1px solid #f3f4f6" }}>
              <strong>{it.name}</strong>{it.relationship ? ` (${it.relationship})` : ""}
              {it.phone ? `　📞 ${it.phone}` : ""}
              {it.email ? `　✉ ${it.email}` : ""}
            </div>
          ))}
        </PrintSection>
      )}

      {note.pets.length > 0 && (
        <PrintSection title="ペット">
          {note.pets.map(it => (
            <div key={it.id} style={{ fontSize: "0.88rem", padding: "0.4rem 0", borderBottom: "1px solid #f3f4f6" }}>
              <strong>{it.name}</strong>{it.species ? ` (${it.species}${it.breed ? `・${it.breed}` : ""})` : ""}
              {it.microchip_no ? `　チップ: ${it.microchip_no}` : ""}
              {it.caretaker ? `　引き継ぎ先: ${it.caretaker}${it.caretaker_phone ? ` 📞${it.caretaker_phone}` : ""}` : ""}
              {it.vet_name ? `　獣医: ${it.vet_name}${it.vet_phone ? ` 📞${it.vet_phone}` : ""}` : ""}
              {it.vaccine_info ? `　ワクチン: ${it.vaccine_info}` : ""}
              {it.medical_info ? `　医療: ${it.medical_info}` : ""}
            </div>
          ))}
        </PrintSection>
      )}

      {(draft.favorite_music || draft.favorite_movies || draft.favorite_foods) && (
        <PrintSection title="お気に入り・思い出">
          <PrintRow label="好きな音楽" value={draft.favorite_music} />
          <PrintRow label="好きな映画・本" value={draft.favorite_movies} />
          <PrintRow label="好きな食べ物・場所" value={draft.favorite_foods} />
        </PrintSection>
      )}

      {draft.family_message && (
        <PrintSection title="家族へのメッセージ">
          <p style={{ fontSize: "0.9rem", lineHeight: 2, whiteSpace: "pre-wrap" as const }}>{draft.family_message}</p>
        </PrintSection>
      )}

      <p style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "2rem", textAlign: "center" as const }}>
        ※ このドキュメントはデジタル墓誌サービスのエンディングノートから出力されました。
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 医療・介護セクション
// ─────────────────────────────────────────────────
function MedicalSection({ draft, onUpdate }: { draft: Partial<EndingNote>; onUpdate: (k: keyof EndingNote, v: string) => void }) {
  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>医療・介護の希望</h2>
      <p style={s.sectionNote}>もしもの時に、ご家族が判断に迷わないよう、あなたの希望を記録しておきましょう。</p>

      <Field label="延命治療">
        <RadioGroup value={draft.life_prolonging ?? ""} onChange={(v) => onUpdate("life_prolonging", v)}
          options={["希望する", "希望しない", "家族に委ねる"]} />
      </Field>
      <Field label="心肺蘇生（CPR）">
        <RadioGroup value={draft.cpr ?? ""} onChange={(v) => onUpdate("cpr", v)}
          options={["希望する", "希望しない"]} />
      </Field>
      <Field label="胃ろう・経管栄養">
        <RadioGroup value={draft.tube_feeding ?? ""} onChange={(v) => onUpdate("tube_feeding", v)}
          options={["希望する", "希望しない"]} />
      </Field>
      <Field label="臓器提供">
        <RadioGroup value={draft.organ_donation ?? ""} onChange={(v) => onUpdate("organ_donation", v)}
          options={["提供する", "提供しない", "家族に委ねる"]} />
      </Field>
      <Field label="臓器提供の詳細・備考">
        <textarea style={s.textarea} rows={2} value={draft.organ_donation_detail ?? ""} onChange={(e) => onUpdate("organ_donation_detail", e.target.value)} placeholder="提供したい臓器など" />
      </Field>
      <Field label="介護の希望場所">
        <RadioGroup value={draft.care_location ?? ""} onChange={(v) => onUpdate("care_location", v)}
          options={["自宅", "施設", "病院", "家族に委ねる"]} />
      </Field>
      <Field label="かかりつけ医・病院">
        <textarea style={s.textarea} rows={2} value={draft.primary_doctor ?? ""} onChange={(e) => onUpdate("primary_doctor", e.target.value)} placeholder="医師名・病院名・電話番号" />
      </Field>
      <Field label="服用中の薬">
        <textarea style={s.textarea} rows={2} value={draft.medications ?? ""} onChange={(e) => onUpdate("medications", e.target.value)} placeholder="薬の名前・用量・処方医" />
      </Field>
      <Field label="その他・備考">
        <textarea style={s.textarea} rows={3} value={draft.medical_notes ?? ""} onChange={(e) => onUpdate("medical_notes", e.target.value)} placeholder="家族へ伝えたいことなど" />
      </Field>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 葬儀セクション
// ─────────────────────────────────────────────────
function FuneralSection({ draft, note, onUpdate, onRefresh }: {
  draft: Partial<EndingNote>; note: EndingNote;
  onUpdate: (k: keyof EndingNote, v: string) => void;
  onRefresh: () => void;
}) {
  const uploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    const form = new FormData();
    form.append("file", e.target.files[0]);
    await api.post("/ending-note/funeral-photo", form, { headers: { "Content-Type": "multipart/form-data" } });
    onRefresh();
  };

  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>葬儀の希望</h2>
      <Field label="葬儀のスタイル">
        <RadioGroup value={draft.funeral_style ?? ""} onChange={(v) => onUpdate("funeral_style", v)}
          options={["家族葬", "一般葬", "直葬", "自由にしてほしい"]} />
      </Field>
      <Field label="宗教・宗派">
        <input style={s.input} value={draft.religion ?? ""} onChange={(e) => onUpdate("religion", e.target.value)} placeholder="例：仏教（浄土宗）、無宗教など" />
      </Field>
      <Field label="流してほしい音楽・曲">
        <textarea style={s.textarea} rows={2} value={draft.funeral_music ?? ""} onChange={(e) => onUpdate("funeral_music", e.target.value)} placeholder="曲名・アーティスト名など" />
      </Field>
      <Field label="お花の希望（種類・色）">
        <input style={s.input} value={draft.funeral_flower_type ?? ""} onChange={(e) => onUpdate("funeral_flower_type", e.target.value)} placeholder="例：白いユリ・菊、シンプルに白のみ" />
      </Field>
      <Field label="戒名への希望">
        <textarea style={s.textarea} rows={2} value={draft.kaimyo_preference ?? ""} onChange={(e) => onUpdate("kaimyo_preference", e.target.value)} placeholder="例：院号は不要、シンプルな居士でよい など" />
      </Field>
      <Field label="会葬者の人数目安">
        <input style={{ ...s.input, width: 120 }} type="number" value={draft.funeral_guest_limit ?? ""} onChange={(e) => onUpdate("funeral_guest_limit", e.target.value)} placeholder="例：30" />
      </Field>
      <Field label="埋葬方法">
        <RadioGroup value={draft.burial_preference ?? ""} onChange={(v) => onUpdate("burial_preference", v)}
          options={["火葬（一般的）", "土葬", "樹木葬", "散骨", "家族に委ねる"]} />
      </Field>
      <Field label="その他・希望">
        <textarea style={s.textarea} rows={3} value={draft.funeral_notes ?? ""} onChange={(e) => onUpdate("funeral_notes", e.target.value)} placeholder="会場・参列者への要望など" />
      </Field>
      <Field label="遺影に使いたい写真">
        {note.funeral_photo_path && (
          <img src={note.funeral_photo_path} alt="遺影候補" style={{ width: 120, height: 120, objectFit: "cover", borderRadius: 8, marginBottom: 8 }} />
        )}
        <input type="file" accept="image/*" onChange={uploadPhoto} style={{ fontSize: "0.85rem" }} />
      </Field>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 形見分けセクション
// ─────────────────────────────────────────────────
function BequestSection({ items, onRefresh }: { items: BequestItem[]; onRefresh: () => void }) {
  const [form, setForm] = useState({ item_name: "", recipient: "", notes: "" });
  const add = async () => {
    if (!form.item_name || !form.recipient) return;
    await api.post("/ending-note/bequest-items", form);
    setForm({ item_name: "", recipient: "", notes: "" });
    autoCheck("bequest_listed");
    onRefresh();
  };
  const del = async (id: number) => { await api.delete(`/ending-note/bequest-items/${id}`); onRefresh(); };

  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>形見分けリスト</h2>
      <p style={s.sectionNote}>「この物品を誰に渡したいか」を記録しておきましょう。</p>
      {items.map((it) => (
        <div key={it.id} style={s.listCard}>
          <div style={{ flex: 1 }}>
            <span style={s.listCardTitle}>{it.item_name}</span>
            <span style={s.listCardSub}> → {it.recipient}</span>
            {it.notes && <div style={s.listCardNote}>{it.notes}</div>}
          </div>
          <button style={s.delBtn} onClick={() => del(it.id)}>削除</button>
        </div>
      ))}
      <div style={s.addForm}>
        <input style={s.input} placeholder="物品名（例：父の形見の時計）" value={form.item_name} onChange={(e) => setForm({ ...form, item_name: e.target.value })} />
        <input style={s.input} placeholder="渡す相手の名前" value={form.recipient} onChange={(e) => setForm({ ...form, recipient: e.target.value })} />
        <input style={s.input} placeholder="備考（任意）" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <button style={s.addBtn} onClick={add}>追加</button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────
// デジタル資産セクション
// ─────────────────────────────────────────────────
function DigitalSection({ items, subs, onRefresh }: { items: DigitalAssetItem[]; subs: SubscriptionItem[]; onRefresh: () => void }) {
  const [daForm, setDaForm] = useState({ service_name: "", account: "", after_death_instruction: "", notes: "" });
  const [subForm, setSubForm] = useState({ service_name: "", monthly_fee: "", cancellation_method: "", notes: "" });

  const addDigital = async () => {
    if (!daForm.service_name) return;
    await api.post("/ending-note/digital-assets", daForm);
    setDaForm({ service_name: "", account: "", after_death_instruction: "", notes: "" });
    autoCheck("digital_sns_set");
    onRefresh();
  };
  const addSub = async () => {
    if (!subForm.service_name) return;
    await api.post("/ending-note/subscriptions", { ...subForm, monthly_fee: subForm.monthly_fee ? Number(subForm.monthly_fee) : null });
    setSubForm({ service_name: "", monthly_fee: "", cancellation_method: "", notes: "" });
    autoCheck("digital_subscriptions");
    onRefresh();
  };

  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>デジタル資産・SNSアカウント</h2>
      {items.map((it) => (
        <div key={it.id} style={s.listCard}>
          <div style={{ flex: 1 }}>
            <span style={s.listCardTitle}>{it.service_name}</span>
            {it.account && <span style={s.listCardSub}> ({it.account})</span>}
            {it.after_death_instruction && <div style={s.listCardNote}>死後の処理: {it.after_death_instruction}</div>}
          </div>
          <button style={s.delBtn} onClick={async () => { await api.delete(`/ending-note/digital-assets/${it.id}`); onRefresh(); }}>削除</button>
        </div>
      ))}
      <div style={s.addForm}>
        <input style={s.input} placeholder="サービス名（例：X / Instagram）" value={daForm.service_name} onChange={(e) => setDaForm({ ...daForm, service_name: e.target.value })} />
        <input style={s.input} placeholder="アカウント名（任意）" value={daForm.account} onChange={(e) => setDaForm({ ...daForm, account: e.target.value })} />
        <input style={s.input} placeholder="死後の処理方法（例：削除してほしい）" value={daForm.after_death_instruction} onChange={(e) => setDaForm({ ...daForm, after_death_instruction: e.target.value })} />
        <button style={s.addBtn} onClick={addDigital}>追加</button>
      </div>

      <h2 style={{ ...s.sectionTitle, marginTop: "1.5rem" }}>サブスクリプション一覧</h2>
      {subs.map((it) => (
        <div key={it.id} style={s.listCard}>
          <div style={{ flex: 1 }}>
            <span style={s.listCardTitle}>{it.service_name}</span>
            {it.monthly_fee && <span style={s.listCardSub}> 月額 {it.monthly_fee.toLocaleString()}円</span>}
            {it.cancellation_method && <div style={s.listCardNote}>解約方法: {it.cancellation_method}</div>}
          </div>
          <button style={s.delBtn} onClick={async () => { await api.delete(`/ending-note/subscriptions/${it.id}`); onRefresh(); }}>削除</button>
        </div>
      ))}
      <div style={s.addForm}>
        <input style={s.input} placeholder="サービス名（例：Netflix）" value={subForm.service_name} onChange={(e) => setSubForm({ ...subForm, service_name: e.target.value })} />
        <input style={{ ...s.input, width: 120 }} type="number" placeholder="月額（円）" value={subForm.monthly_fee} onChange={(e) => setSubForm({ ...subForm, monthly_fee: e.target.value })} />
        <input style={s.input} placeholder="解約方法" value={subForm.cancellation_method} onChange={(e) => setSubForm({ ...subForm, cancellation_method: e.target.value })} />
        <button style={s.addBtn} onClick={addSub}>追加</button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 緊急連絡先セクション
// ─────────────────────────────────────────────────
function ContactSection({ items, onRefresh }: { items: EmergencyContact[]; onRefresh: () => void }) {
  const [form, setForm] = useState({ name: "", relationship: "", phone: "", email: "", notes: "", priority: 0 });
  const add = async () => {
    if (!form.name) return;
    await api.post("/ending-note/emergency-contacts", form);
    setForm({ name: "", relationship: "", phone: "", email: "", notes: "", priority: 0 });
    autoCheck("contacts_listed");
    onRefresh();
  };

  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>緊急連絡先</h2>
      <p style={s.sectionNote}>もしもの時に連絡してほしい人を登録しておきましょう。</p>
      {[...items].sort((a, b) => a.priority - b.priority).map((it) => (
        <div key={it.id} style={s.listCard}>
          <div style={{ flex: 1 }}>
            <span style={s.listCardTitle}>{it.name}</span>
            {it.relationship && <span style={s.listCardSub}> ({it.relationship})</span>}
            {it.phone && <div style={s.listCardNote}>📞 {it.phone}</div>}
            {it.email && <div style={s.listCardNote}>✉️ {it.email}</div>}
          </div>
          <button style={s.delBtn} onClick={async () => { await api.delete(`/ending-note/emergency-contacts/${it.id}`); onRefresh(); }}>削除</button>
        </div>
      ))}
      <div style={s.addForm}>
        <input style={s.input} placeholder="名前" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input style={s.input} placeholder="続柄（例：長男）" value={form.relationship} onChange={(e) => setForm({ ...form, relationship: e.target.value })} />
        <input style={s.input} placeholder="電話番号" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <input style={s.input} placeholder="メールアドレス" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <button style={s.addBtn} onClick={add}>追加</button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────
// ペットセクション
// ─────────────────────────────────────────────────
const PET_EMPTY = { name: "", species: "", breed: "", microchip_no: "", vaccine_info: "", vet_name: "", vet_phone: "", medical_info: "", personality: "", caretaker: "", caretaker_phone: "", notes: "" };

function PetSection({ items, onRefresh }: { items: PetItem[]; onRefresh: () => void }) {
  const [form, setForm] = useState(PET_EMPTY);
  const add = async () => {
    if (!form.name) return;
    await api.post("/ending-note/pets", form);
    setForm(PET_EMPTY);
    autoCheck("pet_caretaker_set");
    onRefresh();
  };

  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>ペット</h2>
      <p style={s.sectionNote}>大切なペットの引き継ぎ情報を詳しく記録しておきましょう。</p>
      {items.map((it) => (
        <div key={it.id} style={s.listCard}>
          <div style={{ flex: 1 }}>
            <span style={s.listCardTitle}>{it.name}</span>
            {it.species && <span style={s.listCardSub}> {it.species}{it.breed ? `（${it.breed}）` : ""}</span>}
            {it.caretaker && <div style={s.listCardNote}>引き継ぎ先: {it.caretaker}{it.caretaker_phone ? ` 📞${it.caretaker_phone}` : ""}</div>}
            {it.vet_name && <div style={s.listCardNote}>獣医: {it.vet_name}{it.vet_phone ? ` 📞${it.vet_phone}` : ""}</div>}
            {it.vaccine_info && <div style={s.listCardNote}>ワクチン: {it.vaccine_info}</div>}
            {it.microchip_no && <div style={s.listCardNote}>マイクロチップ: {it.microchip_no}</div>}
            {it.medical_info && <div style={s.listCardNote}>医療: {it.medical_info}</div>}
          </div>
          <button style={s.delBtn} onClick={async () => { await api.delete(`/ending-note/pets/${it.id}`); onRefresh(); }}>削除</button>
        </div>
      ))}
      <div style={s.addForm}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
          <input style={s.input} placeholder="ペットの名前 *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input style={s.input} placeholder="種類（例：犬・猫）" value={form.species} onChange={(e) => setForm({ ...form, species: e.target.value })} />
          <input style={s.input} placeholder="品種（例：柴犬）" value={form.breed} onChange={(e) => setForm({ ...form, breed: e.target.value })} />
          <input style={s.input} placeholder="マイクロチップ番号" value={form.microchip_no} onChange={(e) => setForm({ ...form, microchip_no: e.target.value })} />
          <input style={s.input} placeholder="引き継ぎ先の名前" value={form.caretaker} onChange={(e) => setForm({ ...form, caretaker: e.target.value })} />
          <input style={s.input} placeholder="引き継ぎ先の電話番号" value={form.caretaker_phone} onChange={(e) => setForm({ ...form, caretaker_phone: e.target.value })} />
          <input style={s.input} placeholder="かかりつけ獣医の名前" value={form.vet_name} onChange={(e) => setForm({ ...form, vet_name: e.target.value })} />
          <input style={s.input} placeholder="獣医の電話番号" value={form.vet_phone} onChange={(e) => setForm({ ...form, vet_phone: e.target.value })} />
        </div>
        <textarea style={s.textarea} rows={2} placeholder="ワクチン接種情報" value={form.vaccine_info} onChange={(e) => setForm({ ...form, vaccine_info: e.target.value })} />
        <textarea style={s.textarea} rows={2} placeholder="医療情報・持病・アレルギー" value={form.medical_info} onChange={(e) => setForm({ ...form, medical_info: e.target.value })} />
        <textarea style={s.textarea} rows={2} placeholder="性格・特記事項" value={form.personality} onChange={(e) => setForm({ ...form, personality: e.target.value })} />
        <button style={s.addBtn} onClick={add}>追加</button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────
// お気に入りセクション（松本恵子 要望）
// ─────────────────────────────────────────────────
function FavoritesSection({ draft, onUpdate }: { draft: Partial<EndingNote>; onUpdate: (k: keyof EndingNote, v: string) => void }) {
  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>お気に入り・思い出</h2>
      <p style={s.sectionNote}>あなたの好きなもの・大切な思い出を記録しておきましょう。葬儀や追悼の場で参考にしてもらえます。</p>
      <Field label="好きな音楽・曲">
        <textarea style={s.textarea} rows={3} value={draft.favorite_music ?? ""} onChange={(e) => onUpdate("favorite_music", e.target.value)} placeholder="例：ビートルズのLet It Be、演歌・三波春夫など" />
      </Field>
      <Field label="好きな映画・本・テレビ">
        <textarea style={s.textarea} rows={3} value={draft.favorite_movies ?? ""} onChange={(e) => onUpdate("favorite_movies", e.target.value)} placeholder="例：「男はつらいよ」、「坂の上の雲」など" />
      </Field>
      <Field label="好きな食べ物・場所・思い出">
        <textarea style={s.textarea} rows={4} value={draft.favorite_foods ?? ""} onChange={(e) => onUpdate("favorite_foods", e.target.value)} placeholder="例：母の手作りのから揚げ、家族で行った北海道旅行など" />
      </Field>
    </div>
  );
}

// ─────────────────────────────────────────────────
// 家族へのメッセージ
// ─────────────────────────────────────────────────
function MessageSection({ draft, onUpdate }: { draft: Partial<EndingNote>; onUpdate: (k: keyof EndingNote, v: string) => void }) {
  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>家族へのメッセージ</h2>
      <p style={s.sectionNote}>普段なかなか言えない感謝の気持ち、大切な人へ伝えたいことを自由に記録してください。</p>
      <textarea
        style={{ ...s.textarea, minHeight: 300, fontSize: "0.95rem", lineHeight: 1.8 }}
        value={draft.family_message ?? ""}
        onChange={(e) => onUpdate("family_message", e.target.value)}
        placeholder="ここに想いを記録してください..."
      />
    </div>
  );
}

// ─────────────────────────────────────────────────
// 共通 UI 部品
// ─────────────────────────────────────────────────
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={s.fieldWrap}>
      <label style={s.fieldLabel}>{label}</label>
      {children}
    </div>
  );
}

function RadioGroup({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" as const }}>
      {options.map((opt) => (
        <label key={opt} style={{ ...s.radioLabel, ...(value === opt ? s.radioLabelActive : {}) }}>
          <input type="radio" name={opt} checked={value === opt} onChange={() => onChange(opt)} style={{ display: "none" }} />
          {opt}
        </label>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────
// 追悼メッセージセクション
// ─────────────────────────────────────────────────
function ScheduledMessageSection({ messages, onRefresh }: { messages: ScheduledMessage[]; onRefresh: () => void }) {
  const empty = { recipient_name: "", recipient_email: "", subject: "", body: "" };
  const [form, setForm] = useState(empty);
  const [editing, setEditing] = useState<ScheduledMessage | null>(null);
  const [showForm, setShowForm] = useState(false);

  const save = async () => {
    if (!form.recipient_name || !form.recipient_email || !form.subject || !form.body) return;
    if (editing) {
      await api.put(`/scheduled-messages/${editing.id}`, form);
    } else {
      await api.post("/scheduled-messages", form);
    }
    setForm(empty);
    setEditing(null);
    setShowForm(false);
    onRefresh();
  };

  const startEdit = (msg: ScheduledMessage) => {
    setForm({ recipient_name: msg.recipient_name, recipient_email: msg.recipient_email, subject: msg.subject, body: msg.body });
    setEditing(msg);
    setShowForm(true);
  };

  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>追悼メッセージ（予約送信）</h2>
      <p style={s.sectionNote}>
        あなたが亡くなった後、デジタル遺品鍵が開錠されたタイミングで自動的にメールが送信されます。大切な方へのメッセージを事前に作成しておきましょう。
      </p>
      {messages.map((msg) => (
        <div key={msg.id} style={s.listCard}>
          <div style={{ flex: 1 }}>
            <span style={s.listCardTitle}>{msg.subject}</span>
            <span style={s.listCardSub}> → {msg.recipient_name}（{msg.recipient_email}）</span>
            <div style={{ ...s.listCardNote, whiteSpace: "pre-wrap", marginTop: 4 }}>{msg.body.slice(0, 120)}{msg.body.length > 120 ? "..." : ""}</div>
          </div>
          <div style={{ display: "flex", gap: "0.4rem", flexShrink: 0 }}>
            <button style={{ ...s.delBtn, color: "#1a5c38" }} onClick={() => startEdit(msg)}>編集</button>
            <button style={s.delBtn} onClick={async () => { await api.delete(`/scheduled-messages/${msg.id}`); onRefresh(); }}>削除</button>
          </div>
        </div>
      ))}
      {!showForm && (
        <button style={s.addBtn} onClick={() => { setShowForm(true); setEditing(null); setForm(empty); }}>+ メッセージを追加</button>
      )}
      {showForm && (
        <div style={{ marginTop: "1rem", background: "#f0f7f4", borderRadius: 8, padding: "1.25rem", border: "1px solid #b2dfdb" }}>
          <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", color: "#1a5c38" }}>{editing ? "メッセージを編集" : "新しいメッセージを作成"}</h3>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            <input style={s.input} placeholder="宛先の名前（例：山田 一郎）" value={form.recipient_name} onChange={(e) => setForm({ ...form, recipient_name: e.target.value })} />
            <input style={s.input} type="email" placeholder="宛先のメールアドレス" value={form.recipient_email} onChange={(e) => setForm({ ...form, recipient_email: e.target.value })} />
            <input style={s.input} placeholder="件名（例：大切なあなたへ）" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
            <textarea style={{ ...s.textarea, minHeight: 160 }} placeholder="本文を入力してください..." value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} />
          </div>
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
            <button style={s.addBtn} onClick={save}>{editing ? "更新" : "保存"}</button>
            <button style={{ ...s.addBtn, background: "#9ca3af" }} onClick={() => { setShowForm(false); setEditing(null); setForm(empty); }}>キャンセル</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────
// ビデオメッセージセクション
// ─────────────────────────────────────────────────
function VideoMessageSection({ videos, onRefresh }: { videos: VideoMessage[]; onRefresh: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const upload = async () => {
    if (!title || !file) return;
    setUploading(true);
    const form = new FormData();
    form.append("title", title);
    form.append("description", description);
    form.append("file", file);
    await api.post("/video-messages", form, { headers: { "Content-Type": "multipart/form-data" } });
    setTitle(""); setDescription(""); setFile(null);
    setUploading(false);
    onRefresh();
  };

  return (
    <div style={s.sectionWrap}>
      <h2 style={s.sectionTitle}>ビデオメッセージ</h2>
      <p style={s.sectionNote}>大切な人へ残したいビデオメッセージをアップロードして保管できます。デジタル遺品鍵が開錠されると、信頼者が閲覧できます。</p>
      {videos.map((v) => (
        <div key={v.id} style={s.listCard}>
          <div style={{ fontSize: "2rem", flexShrink: 0 }}>🎥</div>
          <div style={{ flex: 1 }}>
            <span style={s.listCardTitle}>{v.title}</span>
            {v.description && <div style={s.listCardNote}>{v.description}</div>}
            <div style={s.listCardNote}>
              {v.file_size ? `${(v.file_size / (1024 * 1024)).toFixed(1)} MB` : ""}
              {v.duration_seconds ? ` · ${Math.floor(v.duration_seconds / 60)}分${v.duration_seconds % 60}秒` : ""}
              {" · " + new Date(v.created_at).toLocaleDateString("ja-JP")}
            </div>
          </div>
          <button style={s.delBtn} onClick={async () => { await api.delete(`/video-messages/${v.id}`); onRefresh(); }}>削除</button>
        </div>
      ))}
      <div style={{ marginTop: "1rem", background: "#f9fafb", borderRadius: 8, padding: "1.25rem", border: "1px solid #e5e7eb" }}>
        <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", color: "#374151" }}>ビデオをアップロード</h3>
        <div style={{ display: "grid", gap: "0.75rem" }}>
          <input style={s.input} placeholder="タイトル（例：家族へのメッセージ）" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input style={s.input} placeholder="説明（任意）" value={description} onChange={(e) => setDescription(e.target.value)} />
          <input type="file" accept="video/*" onChange={(e) => setFile(e.target.files?.[0] || null)} style={{ fontSize: "0.9rem" }} />
        </div>
        <button
          style={{ ...s.addBtn, marginTop: "0.75rem", opacity: uploading || !title || !file ? 0.6 : 1 }}
          onClick={upload}
          disabled={uploading || !title || !file}>
          {uploading ? "アップロード中..." : "アップロード"}
        </button>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "#f8fafb", fontFamily: "sans-serif" },
  header: { background: "#fff", borderBottom: "1px solid #e5e7eb", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 900, margin: "0 auto", padding: "0 1.5rem", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" },
  headerLeft: { display: "flex", alignItems: "center", gap: "1rem" },
  backLink: { fontSize: "0.85rem", color: "#6b7280", textDecoration: "none" },
  headerLogo: { fontSize: "1.1rem", fontWeight: 700, color: GREEN },
  headerRight: { display: "flex", alignItems: "center", gap: "0.75rem" },
  savingLabel: { fontSize: "0.78rem", color: "#9ca3af" },
  savedLabel:  { fontSize: "0.78rem", color: "#6ee7b7" },
  headerUser: { fontSize: "0.9rem", color: "#374151" },
  logoutBtn: { fontSize: "0.8rem", padding: "0.3rem 0.8rem", border: "1px solid #d1d5db", borderRadius: 6, background: "#fff", cursor: "pointer" },
  main: { maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" },
  tabBar: { display: "flex", gap: "0.4rem", flexWrap: "wrap" as const, marginBottom: "1.5rem" },
  tab: { fontSize: "0.85rem", padding: "0.4rem 1rem", border: "1px solid #e5e7eb", borderRadius: 20, background: "#fff", cursor: "pointer", color: "#374151" },
  tabActive: { background: GREEN, color: "#fff", borderColor: GREEN, fontWeight: 600 },
  sectionWrap: { background: "#fff", borderRadius: 12, padding: "1.5rem 2rem", boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  sectionTitle: { fontSize: "1.1rem", fontWeight: 700, color: "#1a1a1a", marginTop: 0, marginBottom: 4 },
  sectionNote: { fontSize: "0.85rem", color: "#6b7280", lineHeight: 1.6, marginBottom: "1.25rem", marginTop: 0 },
  fieldWrap: { marginBottom: "1.25rem" },
  fieldLabel: { display: "block", fontSize: "0.85rem", fontWeight: 600, color: "#374151", marginBottom: 6 },
  input: { padding: "0.5rem 0.75rem", border: "1px solid #d1d5db", borderRadius: 7, fontSize: "0.9rem", outline: "none", width: "100%", boxSizing: "border-box" as const },
  textarea: { padding: "0.6rem 0.75rem", border: "1px solid #d1d5db", borderRadius: 7, fontSize: "0.9rem", outline: "none", width: "100%", boxSizing: "border-box" as const, resize: "vertical" as const, fontFamily: "sans-serif" },
  radioLabel: { fontSize: "0.88rem", padding: "0.4rem 1rem", border: "1px solid #e5e7eb", borderRadius: 20, cursor: "pointer", color: "#374151" },
  radioLabelActive: { background: GREEN, color: "#fff", borderColor: GREEN, fontWeight: 600 },
  listCard: { display: "flex", alignItems: "flex-start", gap: "0.75rem", padding: "0.75rem 1rem", background: "#f9fafb", borderRadius: 8, marginBottom: 8, border: "1px solid #f3f4f6" },
  listCardTitle: { fontWeight: 600, fontSize: "0.9rem", color: "#1a1a1a" },
  listCardSub: { fontSize: "0.85rem", color: "#6b7280" },
  listCardNote: { fontSize: "0.8rem", color: "#6b7280", marginTop: 3 },
  delBtn: { fontSize: "0.78rem", color: "#9ca3af", background: "none", border: "1px solid #e5e7eb", borderRadius: 5, padding: "0.2rem 0.5rem", cursor: "pointer", flexShrink: 0 },
  addForm: { display: "flex", gap: "0.5rem", marginTop: "0.75rem", flexWrap: "wrap" as const, alignItems: "center" },
  addBtn: { background: GREEN, color: "#fff", border: "none", borderRadius: 7, padding: "0.5rem 1.25rem", fontSize: "0.88rem", cursor: "pointer", whiteSpace: "nowrap" as const },
};
