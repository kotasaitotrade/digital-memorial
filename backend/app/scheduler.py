"""
APScheduler によるバックグラウンドジョブ
- デッドマンスイッチ監視（毎時）
- 年次見直しリマインダー（毎日）
- 信頼者年次確認メール（毎年）
"""
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def check_deadman_switches() -> None:
    """デッドマンスイッチ：last_checkin_at が interval_days を超えた場合に信頼者へ通知"""
    from .database import SessionLocal
    from .models.shukatsu import DigitalKey
    from .models.auth import User
    from .services.email import send_email, make_deadman_alert_email
    from .config import settings

    db = SessionLocal()
    try:
        keys = db.query(DigitalKey).filter(
            DigitalKey.deadman_enabled == True,
            DigitalKey.is_unlocked == False,
        ).all()
        now = datetime.now(timezone.utc)
        for key in keys:
            checkin = key.last_checkin_at
            if checkin is None:
                checkin = key.created_at
            if checkin is None:
                continue
            if checkin.tzinfo is None:
                checkin = checkin.replace(tzinfo=timezone.utc)
            elapsed_days = (now - checkin).days
            if elapsed_days < key.deadman_interval_days:
                continue
            # タイムアウト：信頼者全員に通知
            owner = db.query(User).filter(User.id == key.user_id).first()
            if not owner:
                continue
            owner_name = owner.name or owner.email
            for person in key.trusted_persons:
                if not person.email:
                    continue
                unlock_url = (
                    f"{settings.base_url}/unlock"
                    f"?person_id={person.id}&token={person.access_token}"
                )
                subj, html, text = make_deadman_alert_email(owner_name, person.name, unlock_url)
                send_email(person.email, subj, html, text)
                logger.info(
                    "Deadman alert sent: owner=%s person=%s elapsed=%d days",
                    owner_name, person.name, elapsed_days,
                )
    except Exception as exc:
        logger.error("check_deadman_switches error: %s", exc)
    finally:
        db.close()


def send_annual_reminders() -> None:
    """毎日実行：今日が review_month の 1 日ならリマインダーメールを送信"""
    from .database import SessionLocal
    from .models.shukatsu import ReminderSetting, ShukatsuCheckItem
    from .models.auth import User
    from .services.email import send_email, make_reminder_email

    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc)
        if today.day != 1:
            return
        settings_list = db.query(ReminderSetting).filter(
            ReminderSetting.enabled == True,
            ReminderSetting.review_month == today.month,
        ).all()
        for setting in settings_list:
            user = db.query(User).filter(User.id == setting.user_id).first()
            if not user:
                continue
            to_email = setting.email or user.email
            user_name = user.name or user.email
            incomplete = db.query(ShukatsuCheckItem).filter(
                ShukatsuCheckItem.user_id == user.id,
                ShukatsuCheckItem.is_done == False,
            ).count()
            subj, html, text = make_reminder_email(user_name, setting.review_month, incomplete)
            send_email(to_email, subj, html, text)
            logger.info("Annual reminder sent to %s", to_email)
    except Exception as exc:
        logger.error("send_annual_reminders error: %s", exc)
    finally:
        db.close()


def send_trusted_person_annual_check() -> None:
    """毎年1月1日：信頼者確認メールを全ユーザーへ送信（notify_trusted が有効な場合）"""
    from .database import SessionLocal
    from .models.shukatsu import ReminderSetting, DigitalKey
    from .models.auth import User
    from .services.email import send_email, make_reminder_trusted_email

    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc)
        if not (today.month == 1 and today.day == 1):
            return
        settings_list = db.query(ReminderSetting).filter(
            ReminderSetting.enabled == True,
            ReminderSetting.notify_trusted == True,
        ).all()
        for setting in settings_list:
            user = db.query(User).filter(User.id == setting.user_id).first()
            if not user:
                continue
            key = db.query(DigitalKey).filter(DigitalKey.user_id == user.id).first()
            if not key:
                continue
            user_name = user.name or user.email
            for person in key.trusted_persons:
                if not person.email:
                    continue
                subj, html, text = make_reminder_trusted_email(user_name, person.name, person.email)
                send_email(person.email, subj, html, text)
                logger.info("Trusted person check sent to %s", person.email)
    except Exception as exc:
        logger.error("send_trusted_person_annual_check error: %s", exc)
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
    # デッドマンスイッチ監視：毎時0分
    _scheduler.add_job(check_deadman_switches, CronTrigger(minute=0), id="deadman_check", replace_existing=True)
    # 年次リマインダー：毎日午前9時
    _scheduler.add_job(send_annual_reminders, CronTrigger(hour=9, minute=0), id="annual_reminder", replace_existing=True)
    # 信頼者年次確認：毎日午前9時（内部で1/1判定）
    _scheduler.add_job(send_trusted_person_annual_check, CronTrigger(hour=9, minute=0), id="trusted_check", replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started (deadman_check, annual_reminder, trusted_check)")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
