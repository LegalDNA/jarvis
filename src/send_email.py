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
    # Keep raw UTF-8 bytes; mark headers appropriately.
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

    # Root container
    msg = MIMEMultipart('mixed')
    # UTF-8 headers (important if subject has ‘—’, accents, etc.)
    msg['From'] = formataddr((str(Header("", 'utf-8')), GMAIL_ADDRESS))
    msg['To'] = formataddr((str(Header("", 'utf-8')), RECIPIENT_EMAIL))
    msg['Subject'] = str(Header(subject, 'utf-8'))

    # Pretty digest (HTML + optional plaintext)
    alt = MIMEMultipart('alternative')
    if text_body:
        alt.attach(MIMEText(text_body, 'plain', 'utf-8'))
    alt.attach(MIMEText(html_body, 'html', 'utf-8'))
    msg.attach(alt)

    # Inline calendar invites
    for (fname, data) in invites:
        _attach_calendar_invite(msg, fname, data)

    # Optional attachments (e.g., combined .ics)
    for (fname, data, mime) in attachments:
        _attach_file(msg, fname, data, mime)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.set_debuglevel(1)
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            # Send as bytes to avoid any implicit ASCII encoding
            server.sendmail(GMAIL_ADDRESS, [RECIPIENT_EMAIL], msg.as_bytes())
        print("[EMAIL] Sent successfully.")
    except Exception as e:
        print(f"[EMAIL] ERROR sending email: {e}")
