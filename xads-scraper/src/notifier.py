import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _table_rows(entries: list[dict], cols: list[tuple[str, str]]) -> str:
    rows_html = ""
    for e in entries:
        cells = "".join(
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{e.get(key,'N/A')}</td>"
            for label, key in cols
        )
        rows_html += f"<tr>{cells}</tr>"
    return rows_html


def _build_html(new_competitions: list[dict], new_jobs: list[dict]) -> str:
    today = date.today().strftime("%d %b %Y")
    total = len(new_competitions) + len(new_jobs)

    comp_cols = [
        ("Name", "name"), ("Category", "category"), ("Deadline", "deadline"),
        ("Prize", "prize_reward"), ("Link", "apply_link"),
    ]
    job_cols = [
        ("Name", "name"), ("Company", "organizer"), ("Deadline", "deadline"),
        ("Reward", "prize_reward"), ("Link", "apply_link"),
    ]

    def table(entries: list[dict], cols: list[tuple[str, str]]) -> str:
        if not entries:
            return "<p style='color:#888'>None found this run.</p>"
        headers = "".join(
            f"<th style='padding:8px 10px;background:#2d2d2d;color:#fff;text-align:left'>{lbl}</th>"
            for lbl, _ in cols
        )
        return (
            f"<table style='border-collapse:collapse;width:100%;font-size:13px'>"
            f"<tr>{headers}</tr>"
            f"{_table_rows(entries, cols)}"
            f"</table>"
        )

    return f"""
<html><body style='font-family:Arial,sans-serif;max-width:900px;margin:auto;color:#333'>
  <h2 style='color:#1a56cc'>🏆 Xads Competition Tracker — {total} new entries ({today})</h2>

  <h3>New Competitions / Incubators / Accelerators ({len(new_competitions)})</h3>
  {table(new_competitions, comp_cols)}

  <h3 style='margin-top:32px'>New Jobs & Placement Competitions ({len(new_jobs)})</h3>
  {table(new_jobs, job_cols)}

  <p style='margin-top:32px;color:#888;font-size:12px'>
    This is automated. Next scan in 3 days.<br>
    View full tracker: <a href='https://docs.google.com/spreadsheets/d/14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E'>
    Google Sheet</a>
  </p>
</body></html>
"""


def send_notification(new_competitions: list[dict], new_jobs: list[dict]) -> None:
    smtp_email = os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    notify_emails_raw = os.environ.get(
        "NOTIFY_EMAILS",
        "soma.charan@mastersunion.org,Hitesh.kalwani@mastersunion.org",
    )

    if not smtp_email or not smtp_password:
        print("  Email skipped — SMTP_EMAIL / SMTP_PASSWORD not set")
        return

    total = len(new_competitions) + len(new_jobs)
    if total == 0:
        print("  No new entries — skipping email")
        return

    recipients = [e.strip() for e in notify_emails_raw.split(",") if e.strip()]
    today = date.today().strftime("%d %b %Y")
    subject = f"🏆 Xads: {total} new competitions found — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(_build_html(new_competitions, new_jobs), "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, recipients, msg.as_string())
        print(f"  Email sent to {recipients}")
    except smtplib.SMTPException as exc:
        print(f"  Email failed: {exc}")
