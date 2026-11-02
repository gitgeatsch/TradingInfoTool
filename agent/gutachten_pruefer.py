# -*- coding: utf-8 -*-
"""Prüfer v2 — die FAKTENTREUE eines Sicht-Gutachtens (G7 Stufe 0a, Voranalyse_G7_Messplan_02_11.md G7-5, Nutzer 02.11.: *„a/a/a,
Stufe 0 bauen – prüfen, gegenprüfen und doku“*).

Warum ein neuer Prüfer: Z-1 (``gegenpruefer_rollen.pruefe_zahlendeckung``) hält jede genannte Zahl gegen ALLE Zahlen der Eingabe
(±0,55). Bei ~170 Zahlen je Sicht-Eingabe deckt fast jeder Wert irgendeinen anderen — gemessen erkennt er ~40 % gepflanzter Fehler und
einen falschen Bezug zu 1 % (g7_voranalyse.txt, Teil E). Dazu zerlegt seine Zahlenerkennung große Zahlen (71211.95 -> 712, 11.95).

Hier dagegen nennt das Gutachten je Treiber den SCHLÜSSEL dessen, worauf es sich stützt, und der Prüfer vergleicht mit GENAU DIESEM:

    {"schluessel": "S1.dvol.BTC", "wert": 53.3, "rang": 37, "klasse": "normal", "aussage": "..."}   Zustand (zustaende.Zustand)
    {"ereignis": "<Beleg-Link>", "typ": "hack_exploit", "aussage": "..."}                           Ereignis (A1, am Stichtag bekannt)
    {"termin": "fomc", "tag": "2026-03-18", "aussage": "..."}                                       Termin (S8)

Regeln (alle gezählt, nichts verworfen — wie Z-1: ein Wächter, der selbst verwirft, macht seine Wirkung unsichtbar):
  * Schlüssel / Beleg / Termin-Art muss in der EINGABE DIESER SICHT stehen
  * ``wert`` gilt, wenn er der angezeigte Wert ist oder eine RUNDUNG davon (2–8 bedeutsame Stellen oder auf so viele Nachkommastellen,
    wie das Modell schreibt) — sonst nicht. Keine absolute Toleranz: 55,9 statt 53,3 ist falsch, 53 ist gerundet
  * ``rang`` muss gleich sein (ganzzahlig), ``klasse`` gleich, ``typ`` gleich dem A1-Typ, ``tag`` gleich dem Termintag
  * eine ZAHL IM FREITEXT (aussage, kippt_wenn, gegenargument, zustand_text) muss eine Rundung des ECHTEN Werts oder Rangs eines in
    DIESEM Gutachten genannten (vorhandenen) Zustands sein, oder der Horizont; sonst „Zahl ohne Beleg“

⚠️ Gelesen wird nur, was übergeben wird (Zustände, Ereignisse). Kein Netz, keine Datenbank.
"""
from __future__ import annotations

import json
import re

ZAHL = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)?(?![\w])")    # 71211.95 bleibt EINE Zahl (anders als Z-1 _ZAHL)
FREITEXT = ("aussage", "kippt_wenn", "gegenargument", "zustand_text", "wirkung_text")
HARMLOS = {0.0, 1.0}                                            # „1 Tag“, „0“ - tragen keine Aussage über einen Wert


def schluessel(z) -> str:
    """Eindeutiger Schlüssel eines Zustands: Sicht.Quelle.Symbol (z. B. S1.dvol.BTC) — geprüft eindeutig über alle 38 Zustände."""
    return "%s.%s.%s" % (z.sicht, z.quelle, z.symbol)


def angezeigt(z) -> float | None:
    """Der WERT, wie die Zeile ihn zeigt (erste Zahl nach dem Namen) — Breite 0,28 steht dort als 28 %, Funding als -0.00307 %."""
    if z.rang is None or z.name not in z.satz:
        return None
    m = ZAHL.search(z.satz.split(z.name, 1)[1])
    return float(m.group().replace(",", ".")) if m else None


def _stellen(x) -> int:
    t = repr(float(x)) if not isinstance(x, str) else x.replace(",", ".")
    if "e" in t.lower():
        return 10
    return len(t.split(".")[1].rstrip("0")) if "." in t else 0


def ist_rundung(gesagt, echt: float) -> bool:
    """Ist ``gesagt`` der Wert ``echt`` oder eine zulässige Rundung davon?"""
    try:
        g = float(str(gesagt).replace(",", "."))
    except (TypeError, ValueError):
        return False
    if echt is None:
        return False
    if abs(g - echt) <= 1e-9 * max(1.0, abs(echt)):
        return True
    for k in range(1, 9):                                          # bedeutsame Stellen (71000 aus 71211,95; 53 aus 53,3)
        # eine EINZIGE bedeutsame Stelle gilt nur unter 10 (100 aus 100,36 ist die Rundung auf DREI Stellen, nicht auf eine -
        # Selbsttest 02.11.: der erste Bau brach hier bei k = 1 ab und meldete 100 aus 100,36 als falsch)
        if abs(float("%.*g" % (k, echt)) - g) <= 1e-9 * max(1.0, abs(g)) and (k >= 2 or abs(echt) < 10):
            return True
    d = _stellen(gesagt)                                           # so viele Nachkommastellen, wie das Modell schreibt
    return d < 10 and abs(round(echt, d) - g) <= 1e-9 * max(1.0, abs(g))


def eingabe(zustaende: list, ereignisse=None, sicht: str | None = None) -> dict:
    """Was der Prüfer gegen die Antwort hält: je Schlüssel Wert, Rang, Klasse; je Beleg der A1-Typ; je Termin-Art der Tag."""
    z_ = {schluessel(z): z for z in zustaende if sicht is None or z.sicht == sicht}
    ev = {}
    if ereignisse is not None and len(ereignisse):
        x = ereignisse if sicht is None else ereignisse[ereignisse.sicht == sicht]
        ev = {b: t for b, t in zip(x.beleg, x.typ)}
    termine = {z.symbol: (z.stand or "")[:10] for z in z_.values() if z.quelle == "termin"}
    return {"zustand": {k: (angezeigt(z), None if z.rang is None else int(round(z.rang)), z.klasse) for k, z in z_.items()
                        if z.quelle != "termin"},
            "ereignis": ev, "termin": termine}


def pruefe(gutachten: dict, ein: dict) -> dict:
    """-> {"geprueft": n, "verstoesse": [{"art", "wo", "grund"}], "ok": bool}. Gezählt, nicht verworfen."""
    v, n, belegt = [], 0, []
    horizont = gutachten.get("horizont_t")
    for i, t in enumerate(gutachten.get("treiber") or []):
        wo = "treiber %d" % (i + 1)
        if not isinstance(t, dict):
            v.append({"art": "form", "wo": wo, "grund": "kein Objekt"})
            continue
        if "schluessel" in t:
            k = t["schluessel"]
            n += 1
            if k not in ein["zustand"]:
                v.append({"art": "schluessel", "wo": wo, "grund": "Zustand %r steht nicht in der Eingabe dieser Sicht" % k})
                continue
            w, r, kl = ein["zustand"][k]
            belegt += [x for x in (w, None if r is None else float(r)) if x is not None]   # die ECHTEN Werte des genannten Zustands
            if "wert" in t:
                n += 1
                if not ist_rundung(t["wert"], w):
                    v.append({"art": "wert", "wo": wo, "grund": "%s: %s genannt, die Eingabe zeigt %s" % (k, t["wert"], w)})
            if "rang" in t:
                n += 1
                try:
                    g = float(str(t["rang"]).strip().lstrip("Pp"))
                    ok = r is not None and g == round(g) and int(g) == r
                except (TypeError, ValueError):
                    ok = False
                if not ok:
                    v.append({"art": "rang", "wo": wo, "grund": "%s: Rang %s genannt, die Eingabe zeigt P%s" % (k, t["rang"], r)})
            if "klasse" in t:
                n += 1
                if t["klasse"] != kl:
                    v.append({"art": "klasse", "wo": wo, "grund": "%s: Klasse %r genannt, die Eingabe zeigt %r" % (k, t["klasse"], kl)})
        elif "ereignis" in t:
            n += 1
            b = t["ereignis"]
            if b not in ein["ereignis"]:
                v.append({"art": "ereignis", "wo": wo, "grund": "Beleg %r steht nicht unter den Ereignissen dieser Sicht" % str(b)[:80]})
            elif "typ" in t and t["typ"] != ein["ereignis"][b]:
                n += 1
                v.append({"art": "ereignis_typ", "wo": wo, "grund": "Typ %r genannt, A1 sagt %r" % (t["typ"], ein["ereignis"][b])})
        elif "termin" in t:
            n += 1
            a = t["termin"]
            if a not in ein["termin"]:
                v.append({"art": "termin", "wo": wo, "grund": "Termin %r steht nicht in der Eingabe" % a})
            elif "tag" in t and str(t["tag"])[:10] != ein["termin"][a]:
                v.append({"art": "termin_tag", "wo": wo, "grund": "%s am %s genannt, die Eingabe sagt %s" % (a, t["tag"], ein["termin"][a])})
        else:
            v.append({"art": "form", "wo": wo, "grund": "weder schluessel noch ereignis noch termin"})
    texte = [(f, gutachten.get(f)) for f in FREITEXT] + [("treiber %d" % (i + 1), t.get("aussage"))
                                                         for i, t in enumerate(gutachten.get("treiber") or []) if isinstance(t, dict)]
    for wo, txt in texte:
        for m in ZAHL.findall(str(txt or "")):
            x = float(m.replace(",", "."))
            if abs(x) in HARMLOS or (horizont is not None and x == horizont):
                continue
            n += 1
            if not any(ist_rundung(m, b) for b in belegt):
                v.append({"art": "zahl_ohne_beleg", "wo": wo, "grund": "Zahl %s im Text ist keinem belegten Wert zuzuordnen" % m})
    return {"geprueft": n, "verstoesse": v, "ok": not v}


def satz(ergebnis: dict) -> str:
    """Eine Zeile für Protokoll und Statusseite."""
    if ergebnis["ok"]:
        return "Faktentreue: %d Angaben geprüft, alle belegt" % ergebnis["geprueft"]
    return "Faktentreue: %d von %d Angaben NICHT belegt — %s" % (
        len(ergebnis["verstoesse"]), ergebnis["geprueft"], "; ".join(x["grund"] for x in ergebnis["verstoesse"][:3]))


def als_json(ergebnis: dict) -> str:
    return json.dumps(ergebnis, ensure_ascii=False)
