"""Prueft die Darstellung der Info-E-Mails (2026-08-06).

ZWEI NUTZER-BEOBACHTUNGEN, beide bestaetigt:

  1. "die farbliche Kennzeichnung ist nicht ueberall vorhanden" - die
     HTML-Fassung wurde nur gebaut, wenn die Mail ein BILD enthielt. Hedge-Mails
     haben nie eines (keine technische Analyse -> keine Grafik) und kamen
     deshalb immer unformatiert an.
  2. "es werden keine strukturierten Risikofaktoren mehr uebermittelt" - kein
     Datenverlust, sondern eine irrefuehrende Meldung: derselbe Satz stand fuer
     "es gibt nichts zu berichten" und fuer "die Daten fehlen".
"""
from types import SimpleNamespace

from api.email_notify import send_notification_email
from ui.formatting import render_detail_html, risikofaktoren_hinweis

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

BEISPIEL = """Aktion: NACHKAUFEN
Regime: baer

--- 1. MATHEMATISCH BERECHNET ---
Entry: 1,40-1,45 EUR

--- 3. KONKLUSION (RISIKOFAKTOREN) ---
(▲ unterstützt die Empfehlung · ● neutral · ▼ Warnsignal/Risiko)

▼ Konfidenz 45%: Niedrige Konfidenz.
● Fazit: mit vorbehalt - Die Datenlage spricht für eine moderate Erhöhung.
▲ Z.ai eigene Richtungseinschätzung: SHORT (stimmt überein)
"""

print("A) FARBE - HTML-Fassung unabhaengig von Bildern")
html = render_detail_html(BEISPIEL)
pruefe("A1 Abschnitts-Kopfzeile bekommt einen Style",
       'KONKLUSION' in html and html.count('<span style=') >= 4)
pruefe("A2 Fazit-Zeile getrennt gestylt (nur das Wort 'Fazit:' unterstrichen)",
       'Fazit:' in html and 'underline' in html)
pruefe("A3 Risikofaktor-Zeilen eingefaerbt",
       html.count('color:') >= 3, f"{html.count('color:')} Farbangaben")

# Der eigentliche Fund: mit UND ohne Bilder muss dieselbe HTML-Fassung entstehen.
# send_notification_email() baut die Mail; ohne Zugangsdaten bricht es vor dem
# Versand ab, deshalb wird hier die Bauphase isoliert nachgestellt.
import api.email_notify as en
gebaut = {}
class _FakeSMTP:
    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): pass
    def login(self, *a): pass
    def sendmail(self, absender, an, text): gebaut["text"] = text

import os
os.environ.setdefault("GMAIL_ABSENDER_ADRESSE", "test@example.invalid")
os.environ.setdefault("GMAIL_APP_PASSWORT", "test")
en.smtplib.SMTP = _FakeSMTP

send_notification_email("Test ohne Bild", BEISPIEL, "empfaenger@example.invalid")
ohne_bild = gebaut.get("text", "")
pruefe("A4 Mail OHNE Bild enthaelt eine HTML-Fassung",
       "text/html" in ohne_bild, "war frueher reiner Text")
pruefe("A5 Mail OHNE Bild enthaelt die Textfassung als Alternative",
       "text/plain" in ohne_bild)
# MIMEText kodiert utf-8 base64 - fuer die Inhaltspruefung muss dekodiert werden
import email as _email
def _html_teil(roh: str) -> str:
    nachricht = _email.message_from_string(roh)
    for teil in nachricht.walk():
        if teil.get_content_type() == "text/html":
            return teil.get_payload(decode=True).decode("utf-8")
    return ""

html_ohne_bild = _html_teil(ohne_bild)
pruefe("A6 color-scheme-Meta auch ohne Bild gesetzt (Gmail-Dark-Mode)",
       "color-scheme" in html_ohne_bild)
pruefe("A6b Formatierung ist im HTML-Teil wirklich drin",
       "KONKLUSION" in html_ohne_bild and "color:" in html_ohne_bild,
       f"{html_ohne_bild.count('color:')} Farbangaben")

gebaut.clear()
send_notification_email("Test mit Bild", BEISPIEL, "empfaenger@example.invalid",
                        inline_images=[{"png": b"\x89PNG\r\n\x1a\n", "alt": "x",
                                        "filename": "x.png"}])
mit_bild = gebaut.get("text", "")
pruefe("A7 Mail MIT Bild weiterhin vollstaendig",
       "text/html" in mit_bild and "image/png" in mit_bild)

print("\nB) RISIKOFAKTOREN - die Meldung nennt jetzt den Grund")
faelle = [
    ("HALTEN ohne Veto", SimpleNamespace(symbol="BTC", action="HALTEN",
                                         original_action="HALTEN"), "KAUFIDEE"),
    ("VERKAUFEN", SimpleNamespace(symbol="ETH", action="VERKAUFEN",
                                  original_action="VERKAUFEN"), "KAUFIDEE"),
    ("Hedge-Instrument", SimpleNamespace(symbol="3QSS", action="NACHKAUFEN",
                                         original_action="NACHKAUFEN"), "Absicherungs"),
    ("Kaufidee ohne Daten", SimpleNamespace(symbol="SOL", action="KAUFEN",
                                            original_action="KAUFEN"), "verfügbar"),
]
for name, sig, erwartet in faelle:
    text = risikofaktoren_hinweis(sig, "")
    pruefe(f"B{faelle.index((name, sig, erwartet))+1} {name}", erwartet in text, text[:78])

pruefe("B5 vorhandene Faktoren bleiben unveraendert",
       risikofaktoren_hinweis(SimpleNamespace(symbol="BTC", action="KAUFEN",
                                              original_action="KAUFEN"),
                              "▼ Konfidenz 45%") == "▼ Konfidenz 45%")
pruefe("B6 die drei Faelle sind unterscheidbar",
       len({risikofaktoren_hinweis(s, "") for _, s, _ in faelle}) == 4)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
