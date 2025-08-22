import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL

def send_email(subject: str, html_body: str, text_body: str = None):
    # Visibility on whether email is enabled
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and RECIPIENT_EMAIL):
        print("[EMAIL] Disabled: missing one of GMAIL_ADDRESS / GMAIL_APP_PASSWORD / RECIPIENT_EMAIL")
        print(f"[EMAIL] GMAIL_ADDRESS set? {bool(GMAIL_ADDRESS)} | APP_PASSWORD set? {bool(GMAIL_APP_PASSWORD)} | RECIPIENT set? {bool(RECIPIENT_EMAIL)}")
        return

    print(f"[EMAIL] Preparing message to {RECIPIENT_EMAIL} with subject: {subject}")

    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject

    if text_body:
        msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.set_debuglevel(1)  # Log SMTP conversation (credentials are not printed)
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [RECIPIENT_EMAIL], msg.as_string())
        print("[EMAIL] Sent successfully.")
    except Exception as e:
        print(f"[EMAIL] ERROR sending email: {e}")
        # Don't crash the whole job; just log the failure
