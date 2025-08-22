import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr

from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL

def _attach_calendar_invite(msg: MIMEMultipart, fname: str, data: bytes):
    """
    Attach a single inline calendar invite (METHOD:REQUEST).
    Gmail/Apple will render native Add-to-Calendar UI.
    """
    part = MIMEBase('text', 'calendar', name=fname)
    # keep raw bytes; mark headers so clients treat it as an invite
    part.set_payload(data)
    part.add_header('Content-Type', f'text/calendar; method=REQUEST; charset=UTF-8; name="{fname}"')
    part.add_header('Content-Disposition', f'inline; filename="{fname}"')
    part.add_header('Content-Transfer-Encoding', '8bit')
    part.add_header('Content-Class', 'urn:content-classes:calendarmessage')
    msg.attach(part)

def _attach_file(msg: MIMEMultipart, fname: str, data: bytes, mime: str):
    maintype, subtype = mime.split('/', 1)
    part = MIMEBase(maintype, subtype, name=fname)
    part.set_payload(data)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{fname}"')
    part.add_header('Content-Type', f'{mime}; charset=UTF-8')
    msg.attach(part)

def send_email(subject: str, html_body: str, text_body: str = None, attachments=None, invites=None):
    """
    attachments: list of (filename, bytes, mime)
    invites: list of (filename, bytes) where bytes is iCalendar (METHOD:REQUEST)
    """
    attachments = attachments or []
    invites = invites or []

    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and RECIPIENT_EMAIL):
        print("[EMAIL] Disabled: missing one of GMAIL_ADDRESS / GMAIL_APP_PASSWORD / RECIPIENT_EMAIL")
        print(f"[EMAIL] GMAIL_ADDRESS set? {bool(GMAIL_ADDRESS)} | APP_PASSWORD set? {bool(GMAIL_APP_PASSWORD)} | RECIPIENT set? {bool(RECIPIENT_EMAIL)}")
        return

    print(f"[EMAIL] Preparing message to {RECIPIENT_EMAIL} with subject: {subject}")

    # Outer container
    msg = MIMEMultipart('mixed')

    # Ensure UTF-8 headers (prevents 'ascii' codec errors on em-dash, accents, etc.)
    msg['From'] = formataddr((str(Header("", 'utf-8')), GMAIL_ADDRESS))
    msg['To'] = formataddr((str(Header("", 'utf-8')), RECIPIENT_EMAIL))
    msg['Subject'] = str(Header(subject, 'utf-8'))

    # Pretty digest (HTML + optional plaintext) in alternative part
    alt = MIMEMultipart('alternative')
    if text_body:
        alt.attach(MIMEText(text_body, 'plain', 'utf-8'))
    alt.attach(MIMEText(html_body, 'html', 'utf-8'))
    msg.attach(alt)

    # Inline calendar invites (Gmail/Apple-native “Add to Calendar” UI)
    for (fname, data) in invites or []:
        _attach_calendar_invite(msg, fname, data)

    # Optional regular attachments (e.g., combined .ics backup)
    for (fname, data, mime) in attachments or []:
        _attach_file(msg, fname, data, mime)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.set_debuglevel(1)  # log SMTP convo
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            # Use as_string() now that headers are UTF-8 encoded
            server.sendmail(GMAIL_ADDRESS, [RECIPIENT_EMAIL], msg.as_string())
        print("[EMAIL] Sent successfully.")
    except Exception as e:
        print(f"[EMAIL] ERROR sending email: {e}")
