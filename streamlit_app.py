"""Digital Memorial — Streamlit フロントエンド"""
import os
import sys
import uuid
from pathlib import Path

import streamlit as st

# backend パッケージを import できるようにパスを追加
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.memorial import Memorial, MemorialMedia
from app.services.auth import get_password_hash, pwd_context
from app.config import settings

Base.metadata.create_all(bind=engine)
os.makedirs("uploads", exist_ok=True)

# ── ページ設定 ────────────────────────────────────────────────
st.set_page_config(
    page_title="Digital Memorial",
    page_icon="🕊️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── グローバル CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;700&family=Noto+Sans+JP:wght@400;500&display=swap');

/* ベース */
.stApp { background: #f5f0eb !important; font-family: 'Noto Sans JP', sans-serif; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 720px !important; }

/* ナビバー */
.nav-bar {
    background: white;
    padding: 0.9rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.5rem;
}
.nav-logo { font-family: 'Noto Serif JP', serif; font-weight: 700; color: #1a3a2a; font-size: 1rem; }

/* ヒーローセクション（公開ページ） */
.hero {
    background: linear-gradient(160deg, #1a3a2a 0%, #2d5a3d 60%, #3d7a50 100%);
    padding: 3.5rem 2rem 2.5rem;
    text-align: center; color: white;
    margin: -1rem -1rem 2rem;
}
.hero-eyebrow { font-size: 0.68rem; letter-spacing: 0.3em; opacity: 0.55; text-transform: uppercase; margin-bottom: 1.25rem; }
.hero-name { font-family: 'Noto Serif JP', serif; font-size: clamp(2rem, 6vw, 3.5rem); font-weight: 300; letter-spacing: 0.08em; margin-bottom: 0.75rem; line-height: 1.2; }
.hero-dates { font-size: 0.95rem; opacity: 0.65; letter-spacing: 0.05em; }

/* カード */
.memorial-card {
    background: white; border-radius: 12px;
    padding: 1.25rem 1.4rem; margin-bottom: 0.25rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-left: 4px solid #2d5a3d;
}
.card-name { font-family: 'Noto Serif JP', serif; font-size: 1.15rem; font-weight: 700; color: #1a1a1a; margin-bottom: 0.2rem; }
.card-dates { font-size: 0.78rem; color: #999; margin-bottom: 0.4rem; }
.card-bio { font-size: 0.83rem; color: #666; line-height: 1.75; }
.badge-pub { background: #d1fae5; color: #065f46; font-size: 0.68rem; padding: 2px 7px; border-radius: 99px; font-weight: 600; }
.badge-prv { background: #fee2e2; color: #991b1b; font-size: 0.68rem; padding: 2px 7px; border-radius: 99px; font-weight: 600; }

/* フォーム */
.form-section { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.2em; color: #999; text-transform: uppercase; border-bottom: 1px solid #e0d8cc; padding-bottom: 0.4rem; margin: 1.75rem 0 1rem; }

/* 公開ページ */
.pub-section-title { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.2em; color: #999; text-transform: uppercase; border-bottom: 1px solid #e0d8cc; padding-bottom: 0.4rem; margin: 2rem 0 1rem; }
.pub-body { font-size: 1rem; line-height: 2.1; white-space: pre-wrap; color: #444; }
.pub-blockquote { background: white; border-left: 3px solid #2d5a3d; border-radius: 0 8px 8px 0; padding: 1.5rem 1.75rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.pub-quote-mark { font-family: Georgia; font-size: 2.5rem; color: #3d7a50; line-height: 0.8; margin-bottom: 0.5rem; }
.pub-quote-text { font-size: 1rem; line-height: 2; color: #555; white-space: pre-wrap; }

/* ログインカード */
.login-card { background: white; border-radius: 16px; padding: 2.5rem 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }

/* フッター */
.site-footer { text-align: center; padding: 2.5rem 1rem 3.5rem; border-top: 1px solid #e0d8cc; margin-top: 2rem; }

/* ボタン上書き */
.stButton > button { border-radius: 8px !important; font-weight: 500 !important; }

/* モバイル調整 */
@media (max-width: 600px) {
    .hero { padding: 2.5rem 1rem 2rem; margin: -1rem -1rem 1.5rem; }
    .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; }
    .login-card { padding: 1.75rem 1.25rem; }
}
</style>
""", unsafe_allow_html=True)

# ── DB ────────────────────────────────────────────────────────
def _db():
    return SessionLocal()

# ── 認証ヘルパー ──────────────────────────────────────────────
def is_logged_in() -> bool:
    return bool(st.session_state.get("user_id"))

def current_uid() -> int | None:
    return st.session_state.get("user_id")

def _login(user: User):
    st.session_state.user_id = user.id
    st.session_state.user_name = user.name

def _logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ── ナビゲーション ────────────────────────────────────────────
def goto(page: str, **kw):
    if "history" not in st.session_state:
        st.session_state.history = []
    cur = st.session_state.get("page")
    if cur and cur != page:
        st.session_state.history.append(cur)
    st.session_state.page = page
    for k, v in kw.items():
        st.session_state[k] = v
    st.rerun()

def go_back(default: str = "dashboard"):
    hist = st.session_state.get("history", [])
    prev = hist.pop() if hist else default
    st.session_state.page = prev
    st.rerun()

# ── ナビバー ─────────────────────────────────────────────────
def _navbар(show_back: bool = False, back_label: str = "← 戻る"):
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if show_back and st.button(back_label, key="nav_back_btn"):
            go_back()
    with c2:
        st.markdown('<div style="text-align:center;padding:0.3rem 0;font-family:\'Noto Serif JP\',serif;font-weight:700;color:#1a3a2a;">🕊️ Digital Memorial</div>', unsafe_allow_html=True)
    with c3:
        if is_logged_in():
            if st.button("ログアウト", key="nav_logout_btn"):
                _logout()

# ── 写真パスをディスクパスに変換 ──────────────────────────────
def _disk_path(file_path: str) -> str:
    """DB に保存されたパス（URL or 相対パス）をディスク上のパスに変換"""
    if file_path.startswith("http"):
        import urllib.parse
        return urllib.parse.urlparse(file_path).path.lstrip("/")
    return file_path.lstrip("/")

# ── QRコードURL生成 ───────────────────────────────────────────
def _public_url(slug: str) -> str:
    base = st.secrets.get("BASE_URL", settings.base_url).rstrip("/")
    return f"{base}/?slug={slug}"

def _generate_qr(slug: str) -> str:
    import qrcode
    os.makedirs("uploads/qr", exist_ok=True)
    img = qrcode.make(_public_url(slug))
    path = f"uploads/qr/{slug}.png"
    img.save(path)
    return path

# ════════════════════════════════════════════════════════════════
#  ページ：ログイン
# ════════════════════════════════════════════════════════════════
def page_login():
    st.markdown('<div style="max-width:400px;margin:3rem auto 0;">', unsafe_allow_html=True)
    st.markdown("""
    <div class="login-card">
        <div style="text-align:center;margin-bottom:1.75rem;">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">🕊️</div>
            <div style="font-family:'Noto Serif JP',serif;font-size:1.4rem;font-weight:700;color:#1a3a2a;">Digital Memorial</div>
            <div style="color:#999;font-size:0.82rem;margin-top:0.3rem;">故人の記憶を、永遠に</div>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("メールアドレス", placeholder="example@email.com")
        password = st.text_input("パスワード", type="password", placeholder="パスワード")
        submitted = st.form_submit_button("ログイン", use_container_width=True, type="primary")

    if submitted:
        db = _db()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user and pwd_context.verify(password, user.hashed_password):
                _login(user)
                st.session_state.page = "dashboard"
                st.session_state.history = []
                st.rerun()
            else:
                st.error("メールアドレスまたはパスワードが正しくありません")
        finally:
            db.close()

    st.markdown("</div>", unsafe_allow_html=True)  # login-card

    st.markdown('<div style="text-align:center;margin-top:1rem;">', unsafe_allow_html=True)
    if st.button("アカウントを新規登録", use_container_width=True):
        goto("register")
    st.markdown("</div></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
#  ページ：新規登録
# ════════════════════════════════════════════════════════════════
def page_register():
    _navbар(show_back=True, back_label="← ログインに戻る")
    st.markdown('<div style="max-width:400px;margin:1rem auto 0;">', unsafe_allow_html=True)
    st.markdown('<h2 style="font-family:\'Noto Serif JP\',serif;font-size:1.2rem;font-weight:700;color:#1a3a2a;margin-bottom:1.25rem;">新規アカウント登録</h2>', unsafe_allow_html=True)

    with st.form("reg_form"):
        name = st.text_input("お名前", placeholder="田中 一郎")
        email = st.text_input("メールアドレス", placeholder="example@email.com")
        password = st.text_input("パスワード（6文字以上）", type="password")
        submitted = st.form_submit_button("登録する", use_container_width=True, type="primary")

    if submitted:
        if not all([name, email, password]):
            st.error("すべての項目を入力してください")
        elif len(password) < 6:
            st.error("パスワードは6文字以上で設定してください")
        else:
            db = _db()
            try:
                if db.query(User).filter(User.email == email).first():
                    st.error("このメールアドレスはすでに登録されています")
                else:
                    user = User(email=email, name=name, hashed_password=get_password_hash(password))
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    _login(user)
                    st.session_state.page = "dashboard"
                    st.session_state.history = []
                    st.rerun()
            finally:
                db.close()

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
#  ページ：ダッシュボード
# ════════════════════════════════════════════════════════════════
def page_dashboard():
    _navbар()

    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown(f'<h1 style="font-family:\'Noto Serif JP\',serif;font-size:1.25rem;font-weight:700;color:#1a3a2a;margin:0;">あなたの墓誌</h1>', unsafe_allow_html=True)
    with col_btn:
        if st.button("＋ 新規作成", use_container_width=True, type="primary"):
            goto("new_memorial")

    db = _db()
    try:
        memorials = (db.query(Memorial)
                     .filter(Memorial.owner_id == current_uid())
                     .order_by(Memorial.created_at.desc())
                     .all())
    finally:
        db.close()

    st.markdown("<br>", unsafe_allow_html=True)

    if not memorials:
        st.markdown("""
        <div style="text-align:center;padding:4rem 1rem;color:#aaa;">
            <div style="font-size:3rem;margin-bottom:1rem;">🕊️</div>
            <div style="font-size:1rem;color:#666;margin-bottom:0.4rem;">まだ墓誌が登録されていません</div>
            <div style="font-size:0.83rem;">「新規作成」から故人の墓誌を作成してください</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for m in memorials:
        badge = '<span class="badge-pub">公開中</span>' if m.is_public else '<span class="badge-prv">非公開</span>'
        dates = " 〜 ".join(filter(None, [m.birth_date or "", m.death_date or ""])) or "—"
        bio = (m.biography[:70] + "…") if m.biography and len(m.biography) > 70 else (m.biography or "")

        st.markdown(f"""
        <div class="memorial-card">
            <div class="card-name">{m.name} &nbsp;{badge}</div>
            <div class="card-dates">{dates}</div>
            <div class="card-bio">{bio}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("👁 表示", key=f"view_{m.id}", use_container_width=True):
                goto("view_memorial", slug=m.slug)
        with c2:
            if st.button("✏️ 編集", key=f"edit_{m.id}", use_container_width=True):
                goto("edit_memorial", memorial_id=m.id)
        with c3:
            if st.button("📱 QR", key=f"qr_{m.id}", use_container_width=True):
                goto("show_qr", memorial_id=m.id)
        with c4:
            if st.button("🗑 削除", key=f"del_{m.id}", use_container_width=True):
                st.session_state[f"confirm_del_{m.id}"] = True

        if st.session_state.get(f"confirm_del_{m.id}"):
            st.warning(f"「{m.name}」を削除しますか？この操作は元に戻せません。")
            y, n = st.columns(2)
            with y:
                if st.button("削除する", key=f"yes_{m.id}", type="primary", use_container_width=True):
                    db2 = _db()
                    try:
                        db2.query(Memorial).filter(Memorial.id == m.id, Memorial.owner_id == current_uid()).delete()
                        db2.commit()
                    finally:
                        db2.close()
                    st.session_state.pop(f"confirm_del_{m.id}", None)
                    st.rerun()
            with n:
                if st.button("キャンセル", key=f"no_{m.id}", use_container_width=True):
                    st.session_state.pop(f"confirm_del_{m.id}", None)
                    st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #ece5db;margin:0.75rem 0 1rem;'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
#  ページ：墓誌作成 / 編集フォーム
# ════════════════════════════════════════════════════════════════
def page_memorial_form(edit: bool = False):
    _navbар(show_back=True)

    memorial_id = st.session_state.get("memorial_id") if edit else None
    memorial = None
    existing_media = []

    if edit and memorial_id:
        db = _db()
        try:
            memorial = (db.query(Memorial)
                        .filter(Memorial.id == memorial_id, Memorial.owner_id == current_uid())
                        .first())
            if memorial:
                existing_media = list(memorial.media)
        finally:
            db.close()

    if edit and not memorial:
        st.error("墓誌が見つかりません")
        if st.button("← ダッシュボードに戻る"):
            goto("dashboard")
        return

    title = "墓誌を編集" if edit else "新しい墓誌を作成"
    st.markdown(f'<h1 style="font-family:\'Noto Serif JP\',serif;font-size:1.25rem;font-weight:700;color:#1a3a2a;margin-bottom:0.25rem;">{title}</h1>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── 基本情報 ──
    st.markdown('<div class="form-section">基本情報</div>', unsafe_allow_html=True)
    name = st.text_input("故人の氏名 *", value=memorial.name if memorial else "", placeholder="例：山田 太郎")
    c1, c2 = st.columns(2)
    with c1:
        birth_date = st.text_input("生年月日", value=memorial.birth_date or "" if memorial else "", placeholder="1940-04-15")
    with c2:
        death_date = st.text_input("没年月日", value=memorial.death_date or "" if memorial else "", placeholder="2023-11-30")
    biography = st.text_area("略歴", value=memorial.biography or "" if memorial else "", placeholder="昭和〇年、○○県生まれ。...", height=160)
    message = st.text_area("ご家族よりのメッセージ", value=memorial.message or "" if memorial else "", placeholder="いつも笑顔で...", height=110)

    # ── 写真 ──
    st.markdown('<div class="form-section">思い出の写真</div>', unsafe_allow_html=True)

    if existing_media:
        st.markdown("**登録済みの写真**")
        cols = st.columns(min(len(existing_media), 3))
        for i, med in enumerate(existing_media):
            dp = _disk_path(med.file_path)
            with cols[i % 3]:
                if os.path.exists(dp):
                    st.image(dp, use_container_width=True)
                if med.caption:
                    st.caption(med.caption)
                if st.button("✕ 削除", key=f"del_med_{med.id}", use_container_width=True):
                    db2 = _db()
                    try:
                        obj = db2.query(MemorialMedia).filter(MemorialMedia.id == med.id).first()
                        if obj:
                            if os.path.exists(dp):
                                os.remove(dp)
                            db2.delete(obj)
                            db2.commit()
                    finally:
                        db2.close()
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "写真を追加（JPG・PNG、複数選択可）",
        type=["jpg", "jpeg", "png", "gif"],
        accept_multiple_files=True,
    )
    captions = []
    if uploaded:
        for i, f in enumerate(uploaded):
            cap = st.text_input(f"キャプション（{f.name}）", key=f"cap_{i}", placeholder="写真の説明（任意）")
            captions.append(cap)

    # ── 公開設定 ──
    st.markdown('<div class="form-section">公開設定</div>', unsafe_allow_html=True)
    is_public = st.toggle("一般公開する", value=memorial.is_public if memorial else True)
    new_pw = ""
    if not is_public:
        new_pw = st.text_input("アクセスパスワード", type="password", placeholder="閲覧者が入力するパスワード")
        st.caption("パスワードを知っている人だけが閲覧できます")

    # ── ボタン ──
    st.markdown("<br>", unsafe_allow_html=True)
    save_col, cancel_col = st.columns(2)
    with save_col:
        save = st.button("💾 保存する", type="primary", use_container_width=True)
    with cancel_col:
        if st.button("キャンセル", use_container_width=True):
            go_back()

    if save:
        if not name.strip():
            st.error("故人の氏名は必須です")
            return

        db = _db()
        try:
            if edit:
                m = db.query(Memorial).filter(Memorial.id == memorial_id, Memorial.owner_id == current_uid()).first()
                m.name = name.strip()
                m.birth_date = birth_date.strip() or None
                m.death_date = death_date.strip() or None
                m.biography = biography.strip() or None
                m.message = message.strip() or None
                m.is_public = is_public
                if not is_public and new_pw:
                    m.password_hash = get_password_hash(new_pw)
                elif is_public:
                    m.password_hash = None
                db.commit()
                saved = m
            else:
                saved = Memorial(
                    owner_id=current_uid(),
                    name=name.strip(),
                    birth_date=birth_date.strip() or None,
                    death_date=death_date.strip() or None,
                    biography=biography.strip() or None,
                    message=message.strip() or None,
                    is_public=is_public,
                    password_hash=get_password_hash(new_pw) if not is_public and new_pw else None,
                )
                db.add(saved)
                db.commit()
                db.refresh(saved)
                saved.qr_code_path = _generate_qr(saved.slug)
                db.commit()

            # 写真を保存
            for i, uf in enumerate(uploaded or []):
                udir = f"uploads/media/{saved.id}"
                os.makedirs(udir, exist_ok=True)
                fname = f"{uuid.uuid4().hex}_{uf.name}"
                fpath = f"{udir}/{fname}"
                with open(fpath, "wb") as fp:
                    fp.write(uf.read())
                cap = captions[i] if i < len(captions) else ""
                db.add(MemorialMedia(
                    memorial_id=saved.id,
                    file_path=fpath,
                    media_type="image",
                    caption=cap or None,
                ))
            db.commit()
        finally:
            db.close()

        st.success("保存しました！")
        import time; time.sleep(0.8)
        goto("dashboard")

# ════════════════════════════════════════════════════════════════
#  ページ：QRコード表示
# ════════════════════════════════════════════════════════════════
def page_show_qr():
    _navbар(show_back=True)

    mid = st.session_state.get("memorial_id")
    if not mid:
        st.error("墓誌が見つかりません")
        return

    db = _db()
    try:
        m = db.query(Memorial).filter(Memorial.id == mid, Memorial.owner_id == current_uid()).first()
    finally:
        db.close()

    if not m:
        st.error("墓誌が見つかりません")
        return

    st.markdown(f'<h2 style="font-family:\'Noto Serif JP\',serif;font-size:1.2rem;font-weight:700;color:#1a3a2a;text-align:center;margin-bottom:1.5rem;">📱 {m.name} さんのQRコード</h2>', unsafe_allow_html=True)

    pub_url = _public_url(m.slug)

    # QR が存在しない or 内容が古い場合は再生成
    qr_path = m.qr_code_path if m.qr_code_path and os.path.exists(m.qr_code_path) else _generate_qr(m.slug)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(qr_path, use_container_width=True)

    st.markdown(f'<p style="text-align:center;font-size:0.75rem;color:#999;margin:0.5rem 0 1.5rem;word-break:break-all;">{pub_url}</p>', unsafe_allow_html=True)
    st.caption("このQRコードを印刷して墓石や位牌に貼ってください")

    with open(qr_path, "rb") as f:
        st.download_button(
            "⬇ QRコードをダウンロード",
            data=f,
            file_name=f"qr_{m.slug}.png",
            mime="image/png",
            use_container_width=True,
        )

# ════════════════════════════════════════════════════════════════
#  ページ：公開墓誌（閲覧専用）
# ════════════════════════════════════════════════════════════════
def page_view_memorial():
    slug = st.session_state.get("slug") or st.query_params.get("slug", "")

    if not slug:
        st.error("URLが正しくありません")
        return

    db = _db()
    try:
        m = db.query(Memorial).filter(Memorial.slug == slug).first()

        if not m:
            st.markdown("""
            <div style="text-align:center;padding:5rem 1rem;">
                <div style="font-size:3rem;">🕊️</div>
                <h2 style="font-family:'Noto Serif JP',serif;font-size:1.3rem;font-weight:700;">墓誌が見つかりません</h2>
                <p style="color:#999;font-size:0.85rem;">URLをご確認ください</p>
            </div>
            """, unsafe_allow_html=True)
            return

        # ── パスワード認証 ──
        if not m.is_public:
            verified_key = f"pw_ok_{slug}"
            if not st.session_state.get(verified_key):
                st.markdown('<div style="max-width:360px;margin:4rem auto;">', unsafe_allow_html=True)
                st.markdown("""
                <div style="text-align:center;margin-bottom:1.5rem;">
                    <div style="font-size:2.5rem;">🔒</div>
                    <h3 style="font-family:'Noto Serif JP',serif;font-size:1.15rem;font-weight:700;">パスワードが必要です</h3>
                    <p style="color:#999;font-size:0.82rem;">この墓誌はパスワードで保護されています</p>
                </div>
                """, unsafe_allow_html=True)
                pw_input = st.text_input("パスワード", type="password", label_visibility="collapsed", placeholder="パスワードを入力してください")
                if st.button("アクセスする", use_container_width=True, type="primary"):
                    if m.password_hash and pwd_context.verify(pw_input, m.password_hash):
                        st.session_state[verified_key] = True
                        st.rerun()
                    else:
                        st.error("パスワードが正しくありません")
                st.markdown("</div>", unsafe_allow_html=True)
                return

        # ── ヒーロー ──
        dates = " 〜 ".join(filter(None, [m.birth_date or "", m.death_date or ""]))
        st.markdown(f"""
        <div class="hero">
            <div class="hero-eyebrow">In Loving Memory</div>
            <div class="hero-name">{m.name}</div>
            {f'<div class="hero-dates">{dates}</div>' if dates else ''}
        </div>
        """, unsafe_allow_html=True)

        # 管理者がログイン中なら戻るボタン
        if is_logged_in() and st.session_state.get("history"):
            if st.button("← ダッシュボードに戻る"):
                go_back("dashboard")

        # ── 略歴 ──
        if m.biography:
            st.markdown('<div class="pub-section-title">略歴</div>', unsafe_allow_html=True)
            st.markdown(f'<p class="pub-body">{m.biography}</p>', unsafe_allow_html=True)

        # ── 写真 ──
        images = [med for med in m.media if med.media_type == "image"]
        if images:
            st.markdown('<div class="pub-section-title">思い出</div>', unsafe_allow_html=True)
            ncols = min(len(images), 3)
            cols = st.columns(ncols)
            for i, img in enumerate(images):
                dp = _disk_path(img.file_path)
                with cols[i % ncols]:
                    if os.path.exists(dp):
                        st.image(dp, use_container_width=True)
                    if img.caption:
                        st.caption(img.caption)

        # ── メッセージ ──
        if m.message:
            st.markdown('<div class="pub-section-title">ご家族より</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="pub-blockquote">
                <div class="pub-quote-mark">"</div>
                <p class="pub-quote-text">{m.message}</p>
            </div>
            """, unsafe_allow_html=True)

        # ── フッター ──
        st.markdown("""
        <div class="site-footer">
            <div style="font-family:'Noto Serif JP',serif;font-size:0.95rem;font-weight:700;color:#1a3a2a;">Digital Memorial</div>
            <p style="font-size:0.75rem;color:#aaa;letter-spacing:0.05em;margin-top:0.3rem;">故人の記憶を、永遠に</p>
        </div>
        """, unsafe_allow_html=True)

    finally:
        db.close()

# ════════════════════════════════════════════════════════════════
#  メインルーター
# ════════════════════════════════════════════════════════════════
def main():
    # URLパラメータで公開ページに直接アクセス
    params = st.query_params
    if "slug" in params and st.session_state.get("page") != "view_memorial":
        st.session_state.page = "view_memorial"
        st.session_state.slug = params["slug"]

    # ページ初期化
    if "page" not in st.session_state:
        st.session_state.page = "dashboard" if is_logged_in() else "login"

    # 認証ガード
    private_pages = {"dashboard", "new_memorial", "edit_memorial", "show_qr"}
    if st.session_state.page in private_pages and not is_logged_in():
        st.session_state.page = "login"

    pg = st.session_state.page
    if pg == "login":          page_login()
    elif pg == "register":     page_register()
    elif pg == "dashboard":    page_dashboard()
    elif pg == "new_memorial": page_memorial_form(edit=False)
    elif pg == "edit_memorial": page_memorial_form(edit=True)
    elif pg == "show_qr":      page_show_qr()
    elif pg == "view_memorial": page_view_memorial()
    else:
        st.session_state.page = "login"
        st.rerun()

main()
