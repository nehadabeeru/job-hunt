"""Notification delivery. V1 channels: browser (pull-based) + email (SMTP).
Adding Telegram/Discord/Slack/SMS later = add a function here and a channel name."""
import logging
import smtplib
from email.message import EmailMessage

from .config import settings

log = logging.getLogger("jobradar.notify")


def send_email_alert(alert, job):
    if not (settings.SMTP_HOST and settings.ALERT_EMAIL_TO):
        log.info("email alert skipped (SMTP not configured) job=%s", job.title)
        return
    msg = EmailMessage()
    msg["Subject"] = f"Job Radar · {job.match_score:.0f}% match · {job.title}"
    msg["From"] = settings.SMTP_USER or "jobradar@localhost"
    msg["To"] = settings.ALERT_EMAIL_TO
    msg.set_content(
        f"{job.title}\nScore: {job.match_score:.0f}%\nLocation: {job.location}\nApply: {job.apply_url}\n"
    )
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
    except Exception:
        log.exception("email alert failed")
