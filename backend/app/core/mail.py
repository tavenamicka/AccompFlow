import logging
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.config import settings

logger = logging.getLogger("app.mail")


def send_mail(to: str, subject: str, body: str) -> None:
    """Envoie un mail via le relais SMTP configuré (SMTP_HOST/SMTP_PORT),
    déjà authentifié SPF/DKIM/DMARC pour votre domaine d'envoi."""
    msg = EmailMessage()
    msg["From"] = settings.sender_email
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=settings.sender_email.split("@")[-1])
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)
    except OSError:
        logger.exception("Échec d'envoi du mail à %s", to)
        raise


def send_invitation_email(to: str, name: str, invitation_url: str) -> None:
    subject = "Votre invitation — AccompFlow"
    body = (
        f"Bonjour {name},\n\n"
        "Un espace client vous a été créé sur AccompFlow.\n"
        f"Créez votre mot de passe et accédez à votre espace via ce lien :\n{invitation_url}\n\n"
        "Ce lien expire dans 7 jours.\n\n"
        f"— {settings.admin_name}"
    )
    send_mail(to, subject, body)
