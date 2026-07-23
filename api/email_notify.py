"""E-Mail-Benachrichtigung (U-8, 2026-07-12, siehe Basisinfos/Regelwerksmanual.md
Kap. 12) - smtplib (Python-Standardbibliothek), keine neue Abhaengigkeit.

Bewusst Gmail fest verdrahtet (smtp.gmail.com), nicht konfigurierbar - die
konzeptionelle Vorentscheidung (2026-07-11) war ein eigener "Robot"-Gmail-Account
mit App-Passwort statt eines vollen SMTP-/Mail-API-Dienstes. Ein generischer
SMTP-Host waere hier ueberdimensioniert.

P-8: fehlen Absender/App-Passwort in der Umgebung, bleibt die Funktion komplett
deaktiviert (kein Fehler, nur ein Info-Log) - Kernfunktionen der App duerfen nie
von einem optionalen Benachrichtigungs-Kanal abhaengen."""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_TIMEOUT_SECONDS = 15

_INLINE_IMAGE_CID = "liquiditaetszonen-chart"


def send_notification_email(
    subject: str, body: str, empfaenger: str, inline_image_png: bytes | None = None,
) -> bool:
    """Best-effort - faengt JEDE Exception selbst ab (P-10: ein E-Mail-Fehlschlag
    darf niemals den eigentlichen Fehlerpfad ueberdecken oder die App zum Absturz
    bringen, egal ob es sich um einen Start-Fehler oder einen Job-Ausfall handelt,
    ueber den gerade benachrichtigt werden soll). Gibt zurueck, ob der Versand
    geklappt hat - Aufrufer koennen das fuer eigene Zwecke nutzen (z.B. Cooldown-
    Zeitstempel nur bei Erfolg aktualisieren), muessen es aber nicht auswerten.

    `inline_image_png` (2026-07-23, Nutzer-Wunsch: Liquiditaetszonen-Grafik auch
    in der E-Mail, nicht nur in der App) - optional, None bewahrt fuer alle
    bestehenden Aufrufer den bisherigen reinen Text-Pfad unveraendert (kein
    Regressionsrisiko fuer Job-Ausfall-/Cash-Veto-Mails etc., die kein Bild
    mitgeben). Ist ein PNG uebergeben, wird eine multipart/related-Mail mit
    Text-Alternative (Fallback fuer Clients ohne HTML/Bilder) UND eingebettetem
    Inline-Bild gebaut - kein Anhang, direkt im Mailtext sichtbar."""
    absender = os.environ.get("GMAIL_ABSENDER_ADRESSE")
    app_passwort = os.environ.get("GMAIL_APP_PASSWORT")
    if not absender or not app_passwort:
        logger.info("E-Mail-Benachrichtigung: kein Absender/App-Passwort gesetzt - übersprungen (P-8)")
        return False

    try:
        if inline_image_png is None:
            msg = MIMEText(body, "plain", "utf-8")
        else:
            msg = MIMEMultipart("related")
            alternative = MIMEMultipart("alternative")
            alternative.attach(MIMEText(body, "plain", "utf-8"))
            html_body = "<pre style=\"font-family: monospace;\">" + (
                body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            ) + f"</pre><img src=\"cid:{_INLINE_IMAGE_CID}\" alt=\"Liquiditätszonen-Grafik\">"
            alternative.attach(MIMEText(html_body, "html", "utf-8"))
            msg.attach(alternative)
            bild = MIMEImage(inline_image_png, "png")
            bild.add_header("Content-ID", f"<{_INLINE_IMAGE_CID}>")
            bild.add_header("Content-Disposition", "inline", filename="liquiditaetszonen.png")
            msg.attach(bild)
        msg["Subject"] = subject
        msg["From"] = absender
        msg["To"] = empfaenger
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.starttls()
            server.login(absender, app_passwort)
            server.sendmail(absender, [empfaenger], msg.as_string())
        logger.info("E-Mail-Benachrichtigung an %s gesendet: %s", empfaenger, subject)
        return True
    except Exception:
        logger.exception("E-Mail-Benachrichtigung fehlgeschlagen")
        return False
