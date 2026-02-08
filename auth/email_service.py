# auth/email_service.py
from utils.mail import send_email
from utils.templates import (
    template_verification_email,
    template_hr_verification_email,
)

def _get_base_url():
    """
    Base URL used inside email links.
    You are not using secrets.toml, so we fall back to localhost.
    If deployed later, you can change this to your deployed URL.
    """
    return "http://localhost:8501"


# -------------------- VERIFY EMAIL (CANDIDATE) --------------------
def send_verification_email(to_email: str, name: str, token: str):
    base_url = _get_base_url()
    verification_link = f"{base_url}/?page=verify_email&token={token}"

    html = template_verification_email(name, verification_link)
    ok = send_email(to_email, "Verify your TrustHire account", html)

    if not ok:
        raise Exception("SMTP send failed (check Gmail SMTP / app password)")


# -------------------- VERIFY EMAIL (HR) --------------------
def send_hr_verification_email(to_email: str, name: str, token: str):
    base_url = _get_base_url()
    verification_link = f"{base_url}/?page=verify_email&token={token}"

    html = template_hr_verification_email(name, verification_link)
    ok = send_email(to_email, "Your HR account is approved ✅ Verify email", html)

    if not ok:
        raise Exception("SMTP send failed (check Gmail SMTP / app password)")


# -------------------- RESET PASSWORD --------------------
def send_reset_password_email(to_email: str, name: str, reset_token: str):
    base_url = _get_base_url()
    reset_link = f"{base_url}/?page=reset_password&token={reset_token}"

    html = f"""
    <h2 style="color:#2d6cdf;margin-bottom:10px;">Reset Your Password</h2>
    <p>Hello <strong>{name}</strong>,</p>
    <p>We received a request to reset your TrustHire password.</p>

    <p>
        <a href="{reset_link}"
           style="display:inline-block; padding:10px 14px; background:#2d6cdf; color:white;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Reset Password
        </a>
    </p>

    <p style="margin-top:10px;">If the button doesn’t work, use this link:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>

    <p style="color:#777;font-size:12px;">
        If you didn’t request this, you can ignore this email.
    </p>
    """

    ok = send_email(to_email, "Reset your TrustHire password", html)
    if not ok:
        raise Exception("SMTP send failed (check Gmail SMTP / app password)")
