# utils/mail.py
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# ----------------------------------
# HARDCODED EMAIL CONFIG (DEV ONLY)
# ----------------------------------

SENDER_EMAIL = "trusthiresystem@gmail.com"
APP_PASSWORD = "fkjyqvfdppiaowxo"   # no spaces

# ----------------------------------

def send_email(to, subject, html_body):

    if not to or "@" not in to:
        logging.warning(f"Invalid recipient email: {to}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"TrustHire <{SENDER_EMAIL}>"
        msg["To"] = to

        msg.attach(MIMEText("HTML email required", "plain"))
        msg.attach(MIMEText(_wrap_html(html_body), "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to, msg.as_string())

        logging.info(f"Email sent → {to}")
        return True

    except Exception:
        logging.exception("SMTP FAILED")
        return False


def _wrap_html(content):
    return f"""
    <html>
    <body style="font-family:Arial;background:#fafafa;padding:20px;">
      <div style="max-width:600px;margin:auto;background:white;
                  padding:30px;border-radius:10px">
        <h2 style="color:#2d6cdf">TrustHire</h2>
        {content}
        <hr>
        <small>This is an automated email</small>
      </div>
    </body>
    </html>
    """
