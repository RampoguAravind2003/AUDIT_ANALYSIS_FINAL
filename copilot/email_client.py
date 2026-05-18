"""Outlook email client for NIAT Copilot escalation workflows."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _get_cfg(key: str, default: str = "") -> str:
    """Read from st.secrets first, then environment variables."""
    try:
        import streamlit as _st
        if key in _st.secrets:
            return str(_st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    is_html: bool = False,
    cc_emails: list[str] | None = None,
) -> dict:
    """
    Send an email via SMTP (Office365/Outlook).

    Configuration via environment variables or secrets.toml:
        OUTLOOK_SENDER_EMAIL    – sender address
        OUTLOOK_SENDER_PASSWORD – app password or account password
        OUTLOOK_SMTP_SERVER     – defaults to smtp.office365.com
        OUTLOOK_SMTP_PORT       – defaults to 587

    If credentials are not configured the email is logged (mock mode).
    """
    sender = _get_cfg("OUTLOOK_SENDER_EMAIL")
    password = _get_cfg("OUTLOOK_SENDER_PASSWORD")
    smtp_server = _get_cfg("OUTLOOK_SMTP_SERVER", "smtp.office365.com")
    smtp_port = int(_get_cfg("OUTLOOK_SMTP_PORT", "587"))

    # ── Mock mode ──────────────────────────────────────────────────────────────
    if not sender or not password:
        mock_info = {
            "status": "mock",
            "to": to_emails,
            "cc": cc_emails or [],
            "subject": subject,
            "body_preview": body[:200] + ("…" if len(body) > 200 else ""),
            "note": (
                "Real email not sent. Add OUTLOOK_SENDER_EMAIL and "
                "OUTLOOK_SENDER_PASSWORD to .streamlit/secrets.toml to enable."
            ),
        }
        print(f"[COPILOT EMAIL MOCK] To={to_emails} Subject={subject}")
        return mock_info

    # ── Real send ──────────────────────────────────────────────────────────────
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(to_emails)
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))

        recipients = to_emails + (cc_emails or [])
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())

        return {
            "status": "success",
            "message": f"Email sent to {', '.join(to_emails)}",
            "to": to_emails,
            "subject": subject,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def build_escalation_email_html(
    university: str,
    batch: str,
    semester: str,
    critical_metrics: list[str],
    warning_metrics: list[str],
    metric_details: dict,
    notes: str = "",
) -> str:
    """Build a styled HTML escalation email body."""
    rows_html = ""
    status_color = {"good": "#059669", "warning": "#d97706", "critical": "#dc2626"}

    for key, detail in metric_details.items():
        color = status_color.get(detail.get("status", "good"), "#334155")
        rows_html += (
            f"<tr>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #f1f5f9'>{detail['label']}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #f1f5f9;font-weight:700;color:{color}'>"
            f"{detail['value']}%</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #f1f5f9;text-transform:uppercase;"
            f"font-size:0.8rem;font-weight:700;color:{color}'>{detail.get('status','—')}</td>"
            f"</tr>"
        )

    overall_color = "#dc2626" if critical_metrics else ("#d97706" if warning_metrics else "#059669")
    overall_label = "CRITICAL" if critical_metrics else ("WARNING" if warning_metrics else "GOOD")

    notes_section = ""
    if notes:
        notes_section = f"<p style='margin:16px 0 0 0;color:#475569'><strong>Notes:</strong> {notes}</p>"

    return f"""
<html><body style='font-family:Inter,Arial,sans-serif;color:#1e293b;max-width:700px;margin:0 auto'>
  <div style='background:linear-gradient(135deg,#1e1b4b,#4338ca);padding:28px 32px;border-radius:12px 12px 0 0'>
    <h1 style='color:#fff;margin:0;font-size:1.4rem'>NIAT Academic Operations — Escalation Alert</h1>
    <p style='color:#c7d2fe;margin:6px 0 0 0'>{batch} · {semester}</p>
  </div>
  <div style='background:#fff;border:1px solid #e2e8f0;border-top:none;padding:28px 32px;border-radius:0 0 12px 12px'>
    <div style='display:flex;align-items:center;gap:12px;margin-bottom:20px'>
      <span style='font-size:1.1rem;font-weight:700'>{university}</span>
      <span style='background:{overall_color};color:#fff;padding:3px 10px;border-radius:999px;
                  font-size:0.78rem;font-weight:700;text-transform:uppercase'>{overall_label}</span>
    </div>
    <table style='width:100%;border-collapse:collapse;font-size:0.92rem'>
      <thead>
        <tr style='background:#f8fafc'>
          <th style='padding:8px 12px;text-align:left;color:#64748b;font-weight:600'>Metric</th>
          <th style='padding:8px 12px;text-align:left;color:#64748b;font-weight:600'>Value</th>
          <th style='padding:8px 12px;text-align:left;color:#64748b;font-weight:600'>Status</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    {notes_section}
    <p style='margin:24px 0 0 0;font-size:0.8rem;color:#94a3b8'>
      Generated by NIAT AI Academic Operations Copilot · This is an automated alert.
    </p>
  </div>
</body></html>
"""
