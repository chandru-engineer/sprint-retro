import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def _send_email(to_email: str, subject: str, body: str, *, log_context: str) -> bool:
    if not settings.SMTP_HOST:
        logger.info("SMTP not configured; skipping email send to %s (subject=%s)", to_email, subject)
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM or settings.SMTP_USERNAME
    message["To"] = to_email
    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(message["From"], [to_email], message.as_string())
        logger.info("Email sent to %s (%s)", to_email, log_context)
        return True
    except Exception:
        logger.exception("Failed to send email to %s (%s)", to_email, log_context)
        return False


_PURPLE = "#6750a4"
_PURPLE_DARK = "#4f3d8f"
_INK = "#1c1b1f"
_MUTED = "#6b6673"
_SURFACE = "#f6f2fa"
_BORDER = "#e4dcf1"


def _wrap_email(*, preheader: str, heading: str, body_html: str) -> str:
    """Shared MD3-styled shell for every outgoing email. Table-based layout
    with inline styles for compatibility across email clients."""
    logo_url = f"{settings.FRONTEND_URL}/logo.svg"
    return f"""
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_SURFACE};padding:32px 16px;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <tr>
    <td align="center">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;">
        <tr>
          <td align="center" style="padding-bottom:24px;">
            <table role="presentation" cellpadding="0" cellspacing="0">
              <tr>
                <td style="vertical-align:middle;">
                  <img src="{logo_url}" width="28" height="28" alt="" style="display:block;border-radius:8px;" />
                </td>
                <td style="vertical-align:middle;padding-left:10px;">
                  <span style="font-size:16px;font-weight:700;color:{_INK};letter-spacing:-0.01em;">{settings.APP_NAME}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#ffffff;border:1px solid {_BORDER};border-radius:28px;padding:36px 32px;box-shadow:0 2px 24px rgba(103,80,164,0.08);">
            <h1 style="margin:0 0 18px;font-size:21px;line-height:1.3;color:{_INK};font-weight:700;">{heading}</h1>
            <div style="font-size:15px;line-height:1.65;color:{_INK};">
              {body_html}
            </div>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding-top:28px;">
            <p style="margin:0;font-size:12px;color:{_MUTED};">
              Sent by {settings.APP_NAME}. If you weren't expecting this email, you can safely ignore it.
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""


def _button(url: str, label: str) -> str:
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin:22px 0 4px;">
      <tr>
        <td style="border-radius:999px;background:{_PURPLE};">
          <a href="{url}" style="display:inline-block;padding:12px 26px;font-size:14px;font-weight:600;
             color:#ffffff;text-decoration:none;border-radius:999px;">{label}</a>
        </td>
      </tr>
    </table>
    """


def _info_row(label: str, value: str) -> str:
    return f"""
    <tr>
      <td style="padding:6px 0;font-size:13px;color:{_MUTED};width:120px;vertical-align:top;">{label}</td>
      <td style="padding:6px 0;font-size:14px;color:{_INK};font-weight:500;">{value}</td>
    </tr>
    """


def _build_invitation_body(user_name: str, retro) -> str:
    retro_url = f"{settings.FRONTEND_URL}/retros/{retro.id}/form"
    info_rows = "".join(
        [
            _info_row("Project", retro.project.name),
            _info_row("Team", retro.team.name),
            _info_row("Sprint", retro.sprint_name),
            _info_row("Retro Meeting", f"{retro.retro_date} at {retro.retro_time}"),
        ]
    )
    body = f"""
    <p style="margin:0 0 14px;">Hi {user_name},</p>
    <p style="margin:0 0 18px;">You've been invited to the <strong>{retro.sprint_name} Retrospective</strong>.
    Share your achievements, learnings, and ideas for the team before the meeting.</p>
    <table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;background:{_SURFACE};
       border-radius:16px;padding:14px 18px;margin:0 0 6px;">
      {info_rows}
    </table>
    {_button(retro_url, "Open Retrospective")}
    """
    return _wrap_email(
        preheader=f"You're invited to the {retro.sprint_name} retrospective",
        heading="You're invited to a retrospective 📋",
        body_html=body,
    )


def send_invitation_email(to_email: str, user_name: str, retro) -> bool:
    subject = f"You're invited: {retro.sprint_name} Retrospective"
    body = _build_invitation_body(user_name, retro)
    return _send_email(to_email, subject, body, log_context=f"retro invitation retro_id={retro.id}")


def send_otp_email(to_email: str, user_name: str, code: str) -> bool:
    subject = f"Your {settings.APP_NAME} sign-in code"
    spaced_code = " ".join(code)
    body = f"""
    <p style="margin:0 0 14px;">Hi {user_name},</p>
    <p style="margin:0 0 20px;">Here's your one-time sign-in code:</p>
    <table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;">
      <tr>
        <td align="center" style="background:{_SURFACE};border:1px dashed {_PURPLE};border-radius:16px;padding:20px;">
          <span style="font-size:32px;font-weight:700;letter-spacing:10px;color:{_PURPLE_DARK};font-family:'Courier New',monospace;">{spaced_code}</span>
        </td>
      </tr>
    </table>
    <p style="margin:20px 0 0;font-size:13px;color:{_MUTED};">
      This code expires in 10 minutes. If you didn't request this, you can safely ignore this email.
    </p>
    """
    html = _wrap_email(preheader=f"Your sign-in code is {code}", heading="Your sign-in code 🔐", body_html=body)
    sent = _send_email(to_email, subject, html, log_context="login OTP")
    if not sent and not settings.SMTP_HOST:
        # No delivery channel configured at all (e.g. local dev). There's no
        # other way to get the code, so surface it in the server log — never
        # do this once SMTP is actually configured.
        logger.info("DEV MODE (no SMTP configured): sign-in code for %s is %s", to_email, code)
    return sent


def send_new_account_invite_email(to_email: str, user_name: str, org_name: str) -> bool:
    """A brand-new account created by an org admin. There's no password to
    send — they'll sign in with a one-time code like everyone else."""
    login_url = f"{settings.FRONTEND_URL}/login"
    subject = f"You've been invited to {org_name} on {settings.APP_NAME}"
    body = f"""
    <p style="margin:0 0 14px;">Hi {user_name},</p>
    <p style="margin:0 0 14px;"><strong>{org_name}</strong> has invited you to {settings.APP_NAME}.</p>
    <p style="margin:0;">There's no password to remember — enter your email
    (<strong>{to_email}</strong>) on the login page and we'll send you a one-time code to sign in.</p>
    {_button(login_url, f"Open {settings.APP_NAME}")}
    """
    html = _wrap_email(
        preheader=f"{org_name} has invited you to {settings.APP_NAME}",
        heading=f"Welcome to {org_name} 🎉",
        body_html=body,
    )
    return _send_email(to_email, subject, html, log_context=f"new account invite org={org_name}")


def send_existing_account_org_invite_email(to_email: str, user_name: str, org_name: str) -> bool:
    """An existing account being added to another organization."""
    login_url = f"{settings.FRONTEND_URL}/login"
    subject = f"You've been added to {org_name} on {settings.APP_NAME}"
    body = f"""
    <p style="margin:0 0 14px;">Hi {user_name},</p>
    <p style="margin:0 0 14px;"><strong>{org_name}</strong> has added you to their {settings.APP_NAME} organization.</p>
    <p style="margin:0;">Log in the same way you always do — enter your email and we'll send a one-time code.
    If you belong to more than one organization, you'll be asked which one to enter afterward.</p>
    {_button(login_url, f"Open {settings.APP_NAME}")}
    """
    html = _wrap_email(
        preheader=f"{org_name} has added you on {settings.APP_NAME}",
        heading=f"You're now part of {org_name} 🤝",
        body_html=body,
    )
    return _send_email(to_email, subject, html, log_context=f"existing account org invite org={org_name}")
