import logging
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.config import settings

logger = logging.getLogger("app.mail")


def send_mail(to: str, subject: str, body: str) -> None:
    """Envoie un mail via le relais Postfix local (Postfix -> Brevo, déjà
    authentifié SPF/DKIM/DMARC pour tranevat.fr) — même mécanisme que le
    backend de contact du site vitrine."""
    msg = EmailMessage()
    msg["From"] = settings.sender_email
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="tranevat.fr")
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
        "— Mickaël Tavenart, Accompagnement numérique"
    )
    send_mail(to, subject, body)


def send_password_reset_email(to: str, name: str, reset_url: str) -> None:
    subject = "Réinitialisation de votre mot de passe — AccompFlow"
    body = (
        f"Bonjour {name},\n\n"
        "Une demande de réinitialisation de mot de passe a été faite pour votre compte AccompFlow.\n"
        f"Choisissez un nouveau mot de passe via ce lien :\n{reset_url}\n\n"
        "Ce lien expire dans 1 heure et ne peut être utilisé qu'une fois.\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce mail : votre mot de passe reste inchangé.\n\n"
        "— Mickaël Tavenart, Accompagnement numérique"
    )
    send_mail(to, subject, body)
