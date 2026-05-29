"""
メール送信サービス
smtplib を使用してメールを送信する。
.env に SMTP_HOST 等を設定しない場合はコンソール出力（開発モード）にフォールバック。
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from ..config import settings

logger = logging.getLogger(__name__)


def _build_message(to: str, subject: str, body_html: str, body_text: str = "") -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Date"] = formatdate(localtime=True)
    if body_text:
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    return msg


def send_email(to: str, subject: str, body_html: str, body_text: str = "") -> bool:
    """メールを送信する。SMTP未設定時はログ出力のみ。"""
    if not settings.smtp_host:
        logger.info("[DEV EMAIL] To=%s Subject=%s\n%s", to, subject, body_text or body_html)
        return True
    try:
        msg = _build_message(to, subject, body_html, body_text)
        if settings.smtp_use_ssl:
            conn = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)
        else:
            conn = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
            if settings.smtp_use_tls:
                conn.starttls()
        if settings.smtp_user and settings.smtp_password:
            conn.login(settings.smtp_user, settings.smtp_password)
        conn.sendmail(settings.smtp_from, [to], msg.as_bytes())
        conn.quit()
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


# ─── テンプレート ─────────────────────────────────────────────

def _wrap(title: str, content: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><style>
body{{font-family:'Hiragino Sans',sans-serif;background:#f5f5f5;margin:0;padding:20px}}
.card{{background:#fff;max-width:600px;margin:0 auto;border-radius:12px;padding:32px;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
h2{{color:#2d6a4f;margin-top:0}}.btn{{display:inline-block;background:#2d6a4f;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;margin-top:16px}}
.footer{{color:#999;font-size:12px;margin-top:24px;border-top:1px solid #eee;padding-top:16px}}
</style></head>
<body><div class="card"><h2>{title}</h2>{content}
<div class="footer">このメールは Digital Memorial から自動送信されました。心当たりがない場合は無視してください。</div>
</div></body></html>"""


def make_verification_email(name: str, verify_url: str) -> tuple[str, str, str]:
    """信頼者メールアドレス確認メール"""
    subject = "【Digital Memorial】メールアドレスの確認をお願いします"
    html = _wrap("メールアドレス確認のお願い", f"""
<p>{name} 様</p>
<p>あなたはデジタル遺品管理サービス「Digital Memorial」の信頼者として登録されました。</p>
<p>下記のボタンをクリックしてメールアドレスを確認してください。</p>
<a class="btn" href="{verify_url}">メールアドレスを確認する</a>
<p style="margin-top:16px;color:#666;font-size:13px">リンクの有効期限は72時間です。</p>""")
    text = f"{name} 様\n\nDigital Memorial の信頼者として登録されました。\n以下のURLでメールアドレスを確認してください:\n{verify_url}"
    return subject, html, text


def make_deadman_alert_email(owner_name: str, person_name: str, unlock_url: str) -> tuple[str, str, str]:
    """デッドマンスイッチ発動通知"""
    subject = f"【Digital Memorial】{owner_name} さんのデジタル遺品確認のご連絡"
    html = _wrap("デジタル遺品アクセスのご案内", f"""
<p>{person_name} 様</p>
<p><strong>{owner_name}</strong> さんが設定されたデジタル遺品管理の連絡先として登録されています。</p>
<p>一定期間ログインが確認されなかったため、あなたに通知が送信されました。</p>
<p>下記のボタンから解除申請を行うことができます。</p>
<a class="btn" href="{unlock_url}">デジタル遺品の解除申請を行う</a>""")
    text = f"{person_name} 様\n\n{owner_name} さんのデジタル遺品管理の解除申請ページ:\n{unlock_url}"
    return subject, html, text


def make_reminder_email(user_name: str, review_month: int, incomplete_count: int) -> tuple[str, str, str]:
    """年次見直しリマインダー"""
    subject = "【Digital Memorial】エンディングノートの年次見直しのご案内"
    items = f"<li>未完了のチェックリスト項目: {incomplete_count} 件</li>" if incomplete_count else ""
    html = _wrap("エンディングノート 年次見直しのご案内", f"""
<p>{user_name} 様</p>
<p>毎年 {review_month} 月恒例の「エンディングノート見直しリマインダー」です。</p>
<p>大切な情報が最新の状態か、ぜひご確認ください。</p>
<ul>{items}<li>信頼者の情報が変わっていないか</li><li>財産・負債の情報が最新か</li></ul>
<a class="btn" href="{settings.base_url}/dashboard">Digital Memorial を開く</a>""")
    text = f"{user_name} 様\n\nエンディングノート見直しリマインダーです。\n{settings.base_url}/dashboard"
    return subject, html, text


def make_scheduled_message_email(recipient_name: str, subject: str, body: str) -> tuple[str, str, str]:
    """予約追悼メッセージ"""
    mail_subject = subject
    html = _wrap(subject, f"""
<p>{recipient_name} 様</p>
<div style="white-space:pre-wrap;line-height:1.8">{body}</div>""")
    text = f"{recipient_name} 様\n\n{body}"
    return mail_subject, html, text


def make_reminder_trusted_email(user_name: str, person_name: str, person_email: str) -> tuple[str, str, str]:
    """信頼者への年次確認メール"""
    subject = f"【Digital Memorial】{user_name} さんの信頼者としての登録確認"
    html = _wrap("信頼者登録の年次確認", f"""
<p>{person_name} 様</p>
<p>あなたは <strong>{user_name}</strong> さんの Digital Memorial に信頼者として登録されています。</p>
<p>連絡先（{person_email}）が最新であることをお知らせする年次確認メールです。</p>
<p>問題がない場合はこのメールを無視してください。変更が必要な場合は登録者にご連絡ください。</p>""")
    text = f"{person_name} 様\n\n{user_name} さんの信頼者として登録されています。\n年次確認メールです。"
    return subject, html, text
