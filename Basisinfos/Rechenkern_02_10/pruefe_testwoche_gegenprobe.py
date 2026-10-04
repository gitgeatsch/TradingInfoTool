"""Gegenprobe zu pruefe_testwoche.py: eine kuenstliche Ablage erfuellt alle Bedingungen - dann je EIN eingebauter Fehler, der genau
SEINE Bedingung rot machen muss (eine Abnahmeprobe, die nicht fehlschlagen kann, ist keine). Wegwerf-Ablage, kein Netz."""
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "Basisinfos", "Rechenkern_02_10"))
import agent.regel0_ablage as AB
import pruefe_testwoche as PT

V = datetime(2026, 10, 3, 6, 0)
F = "%Y-%m-%d %H:%M"
ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info and not bed else ""))


def bau(fehler=None):
    d = tempfile.mkdtemp(prefix="r0_tw_")
    c = AB.oeffne(d)
    for i in range(49):
        h = V + timedelta(hours=i)
        if fehler == "stunde" and i == 10:
            continue
        c.execute("INSERT INTO lauf (jetzt, gerechnet_am, sekunden, pakete, aktiv, frisch, veraltet, veraltet_liste, nicht_im_handel, neu, "
                  "endgueltig, meldung) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (h.strftime(F), h.strftime(F), 2000 if (fehler == "lang" and i == 20) else (628 if i == 0 else 160), "2026-10",
                   635, 634 if (fehler == "alt" and i == 5) else 635, 1 if (fehler == "alt" and i == 5) else 0,
                   "XYZ" if (fehler == "alt" and i == 5) else "", 0, 0, 0, ""))
    sh = V + timedelta(hours=3)
    ein, aus = sh + timedelta(hours=1), sh + timedelta(hours=25)
    mail = (sh + timedelta(hours=1, minutes=9)) if fehler != "spaet" else (ein + timedelta(hours=1, minutes=5))
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, stufe_vorlaeufig, stufe, hebel_schalter, bitpanda, "
              "mail_signal_am, mail_signal_stufe, mail_korrektur_am, mail_erinnerung_am, erinnerung_entfallen_am) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              ("KAIA", sh.strftime(F), ein.strftime(F), aus.strftime(F), 5, 3, 1, "KAIA",
               None if fehler == "ohne_mail" else mail.strftime(F), 5, None if fehler == "korrektur" else mail.strftime(F),
               (aus + timedelta(hours=1, minutes=9)).strftime(F) if fehler == "beides" else None,
               None if fehler == "keins" else (aus + timedelta(hours=1, minutes=9)).strftime(F)))
    if fehler != "ohne_trader":
        c.execute("INSERT INTO pruefung (symbol, signalstunde, rolle, fassung, urteil, gefragt, tag_pazifik, aufrufe) VALUES (?,?,?,?,?,?,?,?)",
                  ("KAIA", sh.strftime(F), "trader", "0.1e-sofort", "neutral", 1, "2026-10-03", 151 if fehler == "kontingent" else 5))
    c.commit(); c.close()
    return os.path.join(d, AB.ABLAGE_NAME)


def rot(e):
    return sorted(k.split()[0] for k, (b, _t) in e["bedingungen"].items() if not b)


print("Gegenprobe pruefe_testwoche - jede Bedingung kann fehlschlagen")
e = PT.auswerten(bau(), bis=(V + timedelta(hours=48)).strftime(F))
pruefe("saubere Ablage: alle Bedingungen gruen", rot(e) == [], rot(e))
for fehler, soll in (("stunde", ["T1"]), ("alt", ["T2"]), ("lang", ["T3"]), ("ohne_mail", ["F1"]), ("spaet", ["F2"]),
                     ("korrektur", ["F3"]), ("keins", ["F4"]), ("beides", ["F4"]), ("ohne_trader", ["L1"]), ("kontingent", ["L1"])):
    e = PT.auswerten(bau(fehler), bis=(V + timedelta(hours=48)).strftime(F))
    r = rot(e)
    # ohne Mail faellt auch die faellige Erinnerung nicht an - F1 ist der Befund, L1 folgt (kein gemailtes Signal ohne Pruefung)
    pruefe("Fehler *%s* macht genau %s rot" % (fehler, "/".join(soll)), set(soll) <= set(r) and set(r) <= set(soll) | {"L1"}, r)
e = PT.auswerten(bau(), bis=(V + timedelta(hours=48)).strftime(F))
pruefe("Trainingslauf (erster Lauf, 628 s) zaehlt nicht als zu lang; verlorene Stunde wird mit der SIGNALstunde genannt",
       e["bedingungen"]["T3 Laufzeit"][0] and "verlorene Signalstunden: 03.10. 15:00" in
       PT.auswerten(bau("stunde"), bis=(V + timedelta(hours=48)).strftime(F))["bedingungen"]["T1 jede Stunde gerechnet"][1])
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)))
