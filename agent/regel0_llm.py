"""Die LLM-Ebene der REGEL0 - Sofortfassung 0.1 (E-50, E-51, E-52; Voranalyse_Schritt7 Par. 20, 20.10, 20.11).

Rollenmodell M3 (Startfassung, anpassbar ueber Basisinfos/regel0_llm.yaml):

    MARKT        *Spricht das Umfeld fuer oder gegen einen gehebelten 24-h-LONG in Krypto?*  - Leitmaerkte, Makro, Stimmung
                 (Datenschicht der alten Rolle A: rollen_eingabe.baue_lagebild_eingabe), KEIN Asset. Neu nur bei geaenderten
                 Fakten (Pruefsumme) - gegen 16 % Eigenrauschen bei gleichen Fakten (L-4)
    TRADER       *Spricht die eigene Kurs- und Volumenlage DIESES Werts fuer oder gegen den geplanten Handel?* - ANONYM (kein
                 Name, kein Datum, kein absoluter Kurs), Bausteine aus agent/lagebeschreibung (R-T1 bis R-T12) auf 24-h-Kerzen,
                 die mit der Signalstunde enden. KEIN Markt (bleibt exklusiv und messbar), KEIN rsi (Eingang der REGEL0)
                 AB 0.2 (07.10.2026, E-80): davor die LAGE ZUR SIGNALSTUNDE aus Stundenkerzen - Umsatzklasse, Fall 6/24 h, Docht,
                 Kapitulation, Markpreis-Praemie, Bitcoin 24 h/7 T, Terminmarkt (nur Werte in open_interest_snapshot). Definitionen
                 wie die A2-Messung (Par. 23.18: einzeln trennt keiner), neutral, Vorwaertstest. N4 bleibt auf 0.1e (eigener Katalog)
    ENTSCHEIDER  *Bestaetigst du diesen Handel?* - aus den ERGEBNISSEN von Markt und Trader, keine Rohdaten. Gesamturteil
                 bestaetigt / mit Vorbehalt / Einwand. Er kippt NICHTS (F2): die REGEL0 hat schon entschieden

Aus der REGEL0 bekommen die Rollen NUR den geplanten Handel (LONG, Hebel, Einstieg, Ausstieg nach 24 h) - nicht deren
Bewertung (v-dach, rsi, Normal, Liquidationsgefahr, Trefferquote): R-T4 Selbstauskunft, Anker (C12), Echo (R-R2). Par. 20.2.

Was aus dem ersten Bau uebernommen ist (Par. 20.4): keine Konfidenz, kein Betrag/Hebel/Stop vom Modell, keine "unklar"-Option
(C5: 93 % -> 3 %), keine Vorsichtssprache, keine Persona, Begruendung und Gegengrund getrennt (C18), Urteil nie geraten,
Ausfall ist nicht Zustimmung, Temperatur 0, JSON als json_object (D5), Zahlendeckung gezaehlt statt verworfen (Z1).

⚠️ SOFORTFASSUNG, UNGEMESSEN (E-52): Die Mail sagt das. Die gemessene Fassung kommt nach Rueckspiel (N4) und Bestaetigung (P3).
⚠️ Schreibt NUR in die REGEL0-Ablage (Tabelle `pruefung`, ueber agent/regel0_ablage); liest die Produktion nur (mode=ro).
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import numpy as np

import agent.regel0_ablage as AB

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KATALOG = os.path.join(HIER, "Basisinfos", "regel0_llm.yaml")
VORGABE = {
    "fassung": "0.2-sofort", "modell": "gemini-3.5-flash-lite", "temperatur": 0.0, "mail_block": True, "schatten": True,
    "zeitgrenze_s": 120,
    "stimmen": 5,
    "tageslimit_aufrufe": 150, "max_signale_je_lauf": 6, "lauf_zeitgrenze_s": 600, "ausfall_schwelle": 3,
    "rollen": {"markt": {"an": True, "nur_auskunft": True}, "trader": {"an": True, "bausteine": ["struktur", "lange_sicht", "marken", "schwankung",
                                                                        "volumen"], "signal": []},
               "entscheider": {"an": False, "eingaenge": ["trader"]}},
}
URTEILE_PRUEFER = ("stuetzt", "neutral", "spricht_dagegen")
URTEILE_ENTSCHEIDER = ("bestaetigt", "mit_vorbehalt", "einwand")
WORT = {"stuetzt": "stützt", "neutral": "neutral", "spricht_dagegen": "spricht dagegen", "uneinig": "uneinig",
        "bestaetigt": "bestätigt", "mit_vorbehalt": "mit Vorbehalt", "einwand": "Einwand"}
MAX_BELEGE = 6


# ---------------------------------------------------------------------------- Rollenkatalog
def lade(pfad: str | None = None) -> dict:
    """Der Rollenkatalog - fehlt die Datei oder ein Schluessel, gilt die Vorgabe (und fuer `rollen` je Rolle)."""
    w = json.loads(json.dumps(VORGABE))
    try:
        import yaml
        with open(pfad or KATALOG, encoding="utf-8") as f:
            roh = yaml.safe_load(f) or {}
    except Exception:                                        # noqa: BLE001
        roh = {}
    for k, v in roh.items():
        if k == "rollen" and isinstance(v, dict):
            for rolle, eig in v.items():
                if rolle in w["rollen"] and isinstance(eig, dict):
                    w["rollen"][rolle].update(eig)
        elif k in w:
            w[k] = v
    return w


# ---------------------------------------------------------------------------- der Plan (fuer alle Rollen gleich)
def _t(txt: str) -> datetime:
    return datetime.strptime(txt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def stufe_von(r: dict) -> int:
    for k in ("stufe", "stufe_vorlaeufig"):
        if r.get(k) is not None:
            return int(r[k])
    return 0


def plan_text(r: dict) -> str:
    """Der geplante Handel - das EINZIGE, was die Rollen aus der REGEL0 erfahren (Par. 20.2: MUSS). Ohne Datum, ohne Kurs.

    ⚠️ 0.1b (P1, 03.10.2026): der Plan nennt, WORAUF der Kauf setzt - eine Gegenbewegung nach einem Rueckgang. In 0.1 fehlte
    das; die Rollen beurteilten einen TRENDhandel und sagten bei 9 von 10 Ankern *spricht dagegen* (eine Konstante, R-T6),
    waehrend sie die Gegenbewegung selbst als Gegengrund nannten. Das ist Teil des Plans, keine Bewertung der REGEL0 (keine
    Zahl, keine Guete). Der Hebel bleibt genannt, ohne Bewertung des Risikos: das rechnet die REGEL0 (C11)."""
    s = stufe_von(r)
    return ("Geplant ist ein Kauf (LONG) auf eine Gegenbewegung nach einem Rueckgang, mit Hebel %d-fach: Einstieg zum "
            "Schlusskurs der naechsten Stunde, Ausstieg genau 24 Stunden danach. Hebel und Risiko werden gesondert gerechnet; "
            "zu beurteilen ist nur, ob die Gegenbewegung in diesen 24 Stunden traegt." % s)


# ---------------------------------------------------------------------------- Trader: 24-h-Kerzen und anonyme Saetze
def _stunden(ordner: str, symbol: str, ab: datetime, bis: datetime) -> list:
    q = ("SELECT stunde, high, low, close, volumen FROM stundenkurse WHERE symbol=? AND stunde >= ? AND stunde <= ? "
         "ORDER BY stunde")
    arg = (symbol, ab.strftime("%Y-%m-%d %H:%M"), bis.strftime("%Y-%m-%d %H:%M"))
    for name in ("stundenkurse.db", "stundenkurse_alle.db"):
        p = os.path.join(ordner, name)
        if not os.path.exists(p):
            continue
        c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
        try:
            rows = c.execute(q, arg).fetchall()
        except sqlite3.Error:
            rows = []
        finally:
            c.close()
        if rows:
            return rows
    return []


def tageskerzen(ordner: str, symbol: str, ende: datetime, tage: int = 300) -> dict | None:
    """24-h-Kerzen, die mit `ende` (Schluss der Signalstunde) enden - die juengste ist damit immer VOLLSTAENDIG und es gibt
    keinen Vorgriff. Eine Kerze braucht mindestens 20 ihrer 24 Stunden, sonst endet die Reihe dort (lieber kurz als falsch)."""
    rows = _stunden(ordner, symbol, ende - timedelta(days=tage, hours=1), ende - timedelta(hours=1))
    if not rows:
        return None
    eimer: dict[int, list] = {}
    for st, hi, lo, cl, vol in rows:
        k = int(((ende - (_t(st) + timedelta(hours=1))).total_seconds()) // 86400)   # 0 = die juengsten 24 h
        eimer.setdefault(k, []).append((st, hi, lo, cl, vol or 0.0))
    kerzen = []
    for k in range(0, tage):
        e = eimer.get(k)
        if not e or len(e) < 20:
            break
        e.sort()
        kerzen.append((max(x[1] for x in e), min(x[2] for x in e), e[-1][3], sum(x[4] for x in e)))
    if len(kerzen) < 30:
        return None
    kerzen.reverse()                                          # aelteste zuerst, wie die Bausteine es erwarten
    h, l, c, v = (np.array([x[i] for x in kerzen], dtype=float) for i in range(4))
    return {"h": h, "l": l, "c": c, "v": v, "i": len(c) - 1}


def _atr_reihe(h, l, c, n: int = 14) -> np.ndarray:
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        out[i] = float(np.mean(tr[i - n:i]))
    return out


def trader_saetze(k: dict, bausteine: list) -> list:
    """Die Lage des Werts als anonyme Aussagen (R-T1 bis R-T12) - ohne Name, Datum oder absoluten Kurs."""
    from agent import lagebeschreibung as LB
    from agent import schreibweise as S
    from agent.marktlage import _einordnung
    h, l, c, v, i = k["h"], k["l"], k["c"], k["v"], k["i"]
    atr_r = _atr_reihe(h, l, c)
    atr = float(atr_r[i]) if np.isfinite(atr_r[i]) else 0.0
    aus = ["Eine Schwankungsbreite ist hier die durchschnittliche Spanne eines 24-Stunden-Abschnitts der letzten 14 Abschnitte; "
           "ein Tag ist ein 24-Stunden-Abschnitt, der mit der juengsten vollen Stunde endet."]
    if "struktur" in bausteine:
        aus += LB._struktur(c, h, l, i)
    if "bewegung" in bausteine:
        aus += LB._bewegung(c, i)
    if "lange_sicht" in bausteine and atr > 0:
        # 0.1b: der weite Rahmen ohne die kurzen Fenster (5/20 Tage und 20/50-Tage-Schnitt spiegeln den rsi, R-R2)
        teile = []
        if i >= 60:
            teile.append("ueber 60 Tage %s %%" % S.de(100.0 * (c[i] / c[i - 60] - 1.0), 1, True))
        if i + 1 >= 200:
            d = (c[i] - float(np.mean(c[i - 199:i + 1]))) / atr
            teile.append("%s Schwankungsbreiten %s dem 200-Tage-Schnitt" % (S.de(abs(d), 1), "ueber" if d >= 0 else "unter"))
        if teile:
            aus.append("In der langen Sicht steht der Kurs " + ", ".join(teile) + ".")
        else:
            aus.append("Fuer die lange Sicht (60 Tage, 200-Tage-Schnitt) reicht die Historie nicht (%d Tage)." % (i + 1))
    if "marken" in bausteine and atr > 0:
        w = LB.niveaus_werte(c, h, l, i, atr, 1.0, 1.0)

        def _satz(m: dict, oben: bool) -> str:
            # das Datum der letzten Beruehrung bleibt bewusst weg (anonym)
            zusatz = "; seitdem per Schlusskurs durchbrochen" if m.get("gefegt") else ""
            return ("Die naechste %s liegt %s Schwankungsbreiten %s (%d-mal beruehrt: %d-mal nach unten gedreht, %d-mal gehalten%s)."
                    % ("Widerstandsmarke" if oben else "Unterstuetzungsmarke", S.de(m["abstand_atr"], 1),
                       "hoeher" if oben else "tiefer", m["beruehrungen"], m["nach_unten_gedreht"], m["gehalten"], zusatz))
        if w.get("widerstand"):
            aus.append(_satz(w["widerstand"], True))
        if w.get("unterstuetzung"):
            aus.append(_satz(w["unterstuetzung"], False))
        if not w.get("widerstand") and not w.get("unterstuetzung"):
            aus.append("Im Umkreis von %s Schwankungsbreiten liegt keine markante Marke." % S.de(LB.NIVEAU_MIN_ABSTAND_ATR, 1))
    if "schnitte" in bausteine and atr > 0:
        teile, fehlt = [], []
        for n in (20, 50, 200):
            if i + 1 >= n:
                sma = float(np.mean(c[i + 1 - n:i + 1]))
                d = (c[i] - sma) / atr
                teile.append("%s Schwankungsbreiten %s dem %d-Tage-Schnitt" % (S.de(abs(d), 1), "ueber" if d >= 0 else "unter", n))
            else:
                fehlt.append(n)
        if teile:
            aus.append("Der Kurs steht " + ", ".join(teile) + ".")
        if fehlt:
            aus.append("Fuer den %s-Tage-Schnitt reicht die Historie nicht (%d Tage)." % ("- und ".join(str(x) for x in fehlt), i + 1))
    if "schwankung" in bausteine and atr > 0:
        rel = atr_r / c
        hist = rel[max(14, i - 249):i + 1]
        hist = hist[np.isfinite(hist)]
        if len(hist) >= 60:
            p = int(round(100.0 * float(np.mean(hist <= rel[i]))))
            aus.append("Die Schwankungsbreite liegt im %d. Perzentil der letzten %d Tage - %s." % (p, len(hist), _einordnung(p)))
    if "volumen" in bausteine:
        aus += LB._volumen(c, v, i, True)
    return aus


# ---------------------------------------------------------------------------- Trader ab 0.2: die Lage ZUR SIGNALSTUNDE (A2, E-80)
# ⚠️ 0.2 (07.10.2026, Nutzer: *die neuen Kandidaten und Quellen als LLM-Rollenbeitrag sofort in Prod, messen und vorwaerts pruefen*).
# Die Kandidaten N-a bis N-f aus A2 (Voranalyse_Schritt7 Par. 23.15/23.18). EINZELN trennt keiner innerhalb der REGEL0-Signale
# (Par. 23.18) - sie stehen hier, weil das LLM sie VERBINDEN koennte und nur der Vorwaertstest das zeigt. Deshalb:
#   * DIESELBEN Definitionen wie a2_messung.merkmale_je_symbol (sonst rechnet der Vorwaertstest etwas anderes ab als gemessen)
#   * NEUTRAL formuliert, KEINE gemessene Richtung (F2/F4) - sonst wiederholt das LLM nur eine Regel (Echo)
#   * Terminmarkt nur aus der Produktion (`open_interest_snapshot`, rund 40 Werte, Lesegrenze 2 h); sonst steht der Satz nicht da
#   * Kaeuferanteil (N-g) fehlt am NB (keine Quelle im Betrieb) - nicht enthalten
SIGNAL_BAUSTEINE = ("liquiditaet", "fall", "docht", "kapitulation", "praemie", "btc", "terminmarkt")
LIQ_KLASSEN = ((1e6, "unter 1 Mio. USD"), (5e6, "1 bis 5 Mio. USD"), (20e6, "5 bis 20 Mio. USD"), (100e6, "20 bis 100 Mio. USD"),
               (float("inf"), "ueber 100 Mio. USD"))
TERMIN_LESEGRENZE_H = 2.0


def _reihe_stunden(ordner: str, dateien: tuple, tabelle: str, spalten: str, symbol: str, ab: datetime, bis: datetime) -> dict:
    """{stunde-Text: Zeile} aus ALLEN Dateien (die Basis-Assets liegen in der ersten, die zusaetzlichen in *_alle) - erste gewinnt."""
    q = "SELECT stunde, %s FROM %s WHERE symbol=? AND stunde >= ? AND stunde <= ?" % (spalten, tabelle)
    arg = (symbol, ab.strftime("%Y-%m-%d %H:%M"), bis.strftime("%Y-%m-%d %H:%M"))
    aus: dict = {}
    for name in dateien:
        p_ = os.path.join(ordner, name)
        if not os.path.exists(p_):
            continue
        c = sqlite3.connect("file:%s?mode=ro" % p_.replace("\\", "/"), uri=True, timeout=10)
        try:
            for z in c.execute(q, arg).fetchall():
                aus.setdefault(z[0], z[1:])
        except sqlite3.Error:
            pass
        finally:
            c.close()
    return aus


def signal_werte(r: dict, ordner: str, db: str | None = None) -> dict:
    """Die Zahlen zur Signalstunde t (nur Kerzen bis einschliesslich t) - Definitionen wie a2_messung.merkmale_je_symbol."""
    t = _t(r["signalstunde"]).replace(tzinfo=None)
    sym = r["symbol"]
    k = _reihe_stunden(ordner, ("stundenkurse.db", "stundenkurse_alle.db"), "stundenkurse", "high, low, close, volumen", sym,
                       t - timedelta(hours=24 * 15 + 30 * 24 + 6), t)
    s_ = lambda d: d.strftime("%Y-%m-%d %H:%M")          # noqa: E731
    w: dict = {}
    z = k.get(s_(t))
    if not z or z[2] is None:
        return w
    c_t = float(z[2])

    def spanne(te):                                      # (Hoch - Tief) der 24 Stunden bis te / Schluss te; luecklos
        zz = [k.get(s_(te - timedelta(hours=j))) for j in range(24)]
        if not all(zz) or not zz[0][2]:
            return None
        return (max(x[0] for x in zz) - min(x[1] for x in zz)) / float(zz[0][2])
    sp = [spanne(t - timedelta(hours=24 * i)) for i in range(1, 15)]
    sp = [x for x in sp if x is not None]
    atr = float(np.mean(sp)) if len(sp) >= 10 else None
    v24 = [k.get(s_(t - timedelta(hours=j))) for j in range(24)]
    if all(v24):
        w["umsatz_usd_24h"] = float(sum((x[3] or 0.0) * (x[2] or 0.0) for x in v24))
    for n_, name in ((6, "fall6"), (24, "fall24")):
        z0 = k.get(s_(t - timedelta(hours=n_)))
        if z0 and z0[2] and atr:
            w[name + "_pct"] = c_t / float(z0[2]) - 1.0
            w[name] = w[name + "_pct"] / atr
    if z[0] is not None and z[1] is not None and z[0] > z[1]:
        w["docht"] = (c_t - float(z[1])) / (float(z[0]) - float(z[1]))
    v6 = [k.get(s_(t - timedelta(hours=j))) for j in range(6)]
    if all(v6):
        bl = []
        for b in range(120):                              # 6-h-Bloecke der 720 Stunden davor, endend t-6, t-12, ...
            e = [k.get(s_(t - timedelta(hours=6 + 6 * b + j))) for j in range(6)]
            if all(e):
                bl.append(sum(x[3] or 0.0 for x in e))
        if len(bl) >= 100:
            m6 = float(np.median(bl))
            if m6 > 0:
                w["kapitulation"] = sum(x[3] or 0.0 for x in v6) / m6
    mk = _reihe_stunden(ordner, ("markpreis_historie.db", "markpreis_alle.db"), "markpreis", "close", sym, t, t).get(s_(t))
    if mk and mk[0]:
        w["praemie"] = float(mk[0]) / c_t - 1.0
    if sym != "BTC":
        b = _reihe_stunden(ordner, ("stundenkurse.db", "stundenkurse_alle.db"), "stundenkurse", "close", "BTC",
                           t - timedelta(hours=168), t)
        for n_, name in ((24, "btc24"), (168, "btc168")):
            b0, b1 = b.get(s_(t - timedelta(hours=n_))), b.get(s_(t))
            if b0 and b1 and b0[0]:
                w[name] = float(b1[0]) / float(b0[0]) - 1.0
    if db and os.path.exists(str(db)):
        w.update(_terminmarkt(sym, t + timedelta(hours=1), str(db)))
    return w


def _terminmarkt(sym: str, ende: datetime, db: str) -> dict:
    """Funding, Anteil Long-Konten und OI-Aenderung 24 h aus `open_interest_snapshot` (Binance) - der juengste Stand vor `ende`,
    hoechstens TERMIN_LESEGRENZE_H alt; der Vergleich 24 h davor hoechstens 1 h daneben."""
    c = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True, timeout=10)
    try:
        q = ("SELECT fetched_at, open_interest, funding_rate, long_account_pct FROM open_interest_snapshot WHERE symbol=? AND "
             "exchange='binance' AND fetched_at <= ? AND fetched_at >= ? ORDER BY fetched_at DESC LIMIT 1")
        iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%S")   # noqa: E731
        jetzt = c.execute(q, (sym, iso(ende), iso(ende - timedelta(hours=TERMIN_LESEGRENZE_H)))).fetchone()
        if not jetzt:
            return {}
        w = {}
        if jetzt[2] is not None:
            w["funding"] = float(jetzt[2])
        if jetzt[3] is not None:
            w["long_konten_pct"] = float(jetzt[3])
        t0 = datetime.strptime(jetzt[0][:19], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=24)
        vor = c.execute(q, (sym, iso(t0 + timedelta(hours=1)), iso(t0 - timedelta(hours=1)))).fetchone()
        if vor and vor[1] and jetzt[1] is not None:
            w["oi24"] = float(jetzt[1]) / float(vor[1]) - 1.0
        return w
    except sqlite3.Error:
        return {}
    finally:
        c.close()


def signal_saetze(w: dict, bausteine: list) -> list:
    """Die Zahlen zur Signalstunde als neutrale Saetze - ohne Wertwort, ohne gemessene Richtung (F2/F4)."""
    from agent import schreibweise as S
    aus = []
    if "liquiditaet" in bausteine and "umsatz_usd_24h" in w:
        klasse = next(txt for grenze, txt in LIQ_KLASSEN if w["umsatz_usd_24h"] < grenze)
        aus.append("Umsatz der letzten 24 Stunden: %s." % klasse)
    if "fall" in bausteine and "fall6" in w and "fall24" in w:
        aus.append("Kursaenderung bis zur Signalstunde: ueber 6 Stunden %s %% (%s Tagesspannen), ueber 24 Stunden %s %% (%s Tagesspannen). "
                   "Eine Tagesspanne ist hier das Mittel der Spannen (Hoch minus Tief) der 14 vorangegangenen 24-Stunden-Abschnitte."
                   % (S.de(100 * w["fall6_pct"], 1, True), S.de(w["fall6"], 2, True), S.de(100 * w["fall24_pct"], 1, True),
                      S.de(w["fall24"], 2, True)))
    if "docht" in bausteine and "docht" in w:
        aus.append("Die Signalstunde schloss bei %s %% ihrer Spanne (0 %% = Stundentief, 100 %% = Stundenhoch)." % S.de(100 * w["docht"], 0))
    if "kapitulation" in bausteine and "kapitulation" in w:
        aus.append("Der Umsatz der letzten 6 Stunden liegt beim %s-fachen des mittleren 6-Stunden-Umsatzes der 30 Tage davor (Median)."
                   % S.de(w["kapitulation"], 2))
    if "praemie" in bausteine and "praemie" in w:
        aus.append("Der Markpreis am Terminmarkt liegt %s %% %s dem Kassakurs." % (S.de(abs(100 * w["praemie"]), 3),
                                                                                  "ueber" if w["praemie"] >= 0 else "unter"))
    if "btc" in bausteine and "btc24" in w and "btc168" in w:
        aus.append("Bitcoin bis zur Signalstunde: ueber 24 Stunden %s %%, ueber 7 Tage %s %%." % (
            S.de(100 * w["btc24"], 1, True), S.de(100 * w["btc168"], 1, True)))
    if "terminmarkt" in bausteine:
        teile = []
        if "funding" in w:
            teile.append("Finanzierungssatz (Funding) %s %% je Abrechnung" % S.de(100 * w["funding"], 4, True))
        if "long_konten_pct" in w:
            teile.append("Anteil der Konten mit Long-Position %s %%" % S.de(w["long_konten_pct"], 1))
        if "oi24" in w:
            teile.append("offene Positionen (Open Interest) ueber 24 Stunden %s %%" % S.de(100 * w["oi24"], 1, True))
        if teile:
            aus.append("Am Terminmarkt: " + "; ".join(teile) + ".")
    return aus


def trader_eingabe(r: dict, ordner: str, katalog: dict, db: str | None = None) -> dict | None:
    """Ab 0.2 (F3): zuerst der Plan (die Wette), dann die Lage ZUR SIGNALSTUNDE, der weite Rahmen zuletzt. Ohne `signal` im
    Katalog (0.1e, N4) genau die alte Eingabe."""
    k = tageskerzen(ordner, r["symbol"], _t(r["signalstunde"]) + timedelta(hours=1))
    if k is None:
        return None
    sig = list(katalog["rollen"]["trader"].get("signal") or [])
    aus = {"geplant": plan_text(r)}
    if sig:
        saetze = signal_saetze(signal_werte(r, ordner, db), sig)
        if saetze:
            aus["lage_zur_signalstunde"] = saetze
    aus["lage_des_werts"] = trader_saetze(k, katalog["rollen"]["trader"].get("bausteine") or [])
    return aus


# ---------------------------------------------------------------------------- Markt: die Datenschicht der alten Rolle A
_REIHEN = {}


def markt_eingabe(r: dict, db: str) -> dict | None:
    """Leitmaerkte, Makro, Stimmung zum letzten VOLLEN Tag vor der Signalstunde (kein Vorgriff, Betrieb = Rueckspiel)."""
    # ⚠️ ALLES AUS EINER DATENBANK (03.10.2026): `rollen_eingabe.baue_lagebild_eingabe` liest Stimmung und Makro immer aus dem
    # Standardpfad - im Rueckspiel kaemen dann Kurse aus der Kopie und Makro aus einer anderen Datei. Deshalb hier dieselben
    # Bausteine (beschreibe_marktlage, lade_stimmung, lade_makro), aber jeder mit `db`.
    from agent import rollen_eingabe as RE
    from agent.marktlage import beschreibe_marktlage
    from backtest_llm1_historisch import lade_reihen_aus_db
    db = str(db).replace("\\", "/")
    tag = ((_t(r["signalstunde"]) + timedelta(hours=1)) - timedelta(days=1)).strftime("%Y-%m-%d")
    schl = (db, datetime.now().strftime("%Y-%m-%d %H"))
    if schl not in _REIHEN:
        _REIHEN.clear()
        _REIHEN[schl] = (lade_reihen_aus_db(db), RE.lade_stimmung(db), RE.lade_makro(db))
    reihen, stimmung, makro = _REIHEN[schl]
    # ⚠️ ZEITPUNKTTREUE (03.10.2026, Vorbereitung N4): `makro_historie_monat` fuehrt den LAUFENDEN Monat (Teilmonat, z. B. S&P
    # 2026-10). In einer spaeteren Sicherung stuende fuer einen Anker vom 13.09. schon der Monatsschluss September - ein Vorgriff von
    # bis zu einem Monat. Deshalb Monatswerte nur aus ABGESCHLOSSENEN Monaten (< Ankermonat) - im Betrieb UND im Rueckspiel gleich.
    if isinstance(makro, dict) and isinstance(makro.get("monatsreihen"), dict):
        grenze_m = tag[:7]
        makro = dict(makro, monatsreihen={f: {m: v for m, v in (d or {}).items() if m < grenze_m}
                                          for f, d in makro["monatsreihen"].items()})
    try:
        saetze = list(beschreibe_marktlage(reihen, tag, stimmung, makro))
    except Exception:                                        # noqa: BLE001
        return None
    if not saetze:
        return None
    return {"geplant": plan_text({"stufe": stufe_von(r)}).replace("mit Hebel", "in Krypto mit Hebel"), "marktlage": saetze}


# ---------------------------------------------------------------------------- Prompts (Fassung 0.1-sofort)
_SCHLUSS_PRUEFER = """Antworte AUSSCHLIESSLICH mit JSON:
{"belege": [{"fakt": "<kurz, mit dem Wert>", "richtung": "dafuer|dagegen|neutral"}],
 "urteil": "stuetzt|neutral|spricht_dagegen",
 "begruendung": "<ein Satz>",
 "gegengrund": "<der staerkste Grund gegen dein Urteil>"}"""

_SCHRITTE_PRUEFER = """DEINE AUFGABE, in dieser Reihenfolge:

1. BELEGE. Gehe die Angaben durch und notiere bis zu sechs Beobachtungen, die fuer oder gegen den geplanten Handel sprechen, \
je mit dem Wert, auf den sie sich stuetzen. Erfinde nichts; was nicht dasteht, ist kein Argument.

2. URTEIL. Waehle GENAU EINES: stuetzt (die Angaben sprechen insgesamt dafuer, dass die Gegenbewegung in den 24 Stunden \
traegt), neutral (ein Teil spricht dafuer, ein Teil dagegen) oder spricht_dagegen.

3. BEGRUENDUNG. Ein Satz, der dein Urteil traegt - ohne Einschraenkung im Nachsatz.

4. GEGENGRUND. Der staerkste Grund gegen dein Urteil, klar benannt. Er entwertet dein Urteil nicht; er gehoert dazu."""

SYSTEM_MARKT = ("Du beurteilst das Umfeld der Maerkte fuer einen geplanten Handel in Krypto: einen Kauf auf eine "
                "Gegenbewegung nach einem Rueckgang, gehalten fuer 24 Stunden. Du bekommst Angaben zu "
                "Leitmaerkten, Makro und Anlegerstimmung, jeweils im Vergleich zur eigenen Vergangenheit. Ein einzelnes "
                "Wertpapier siehst du nicht.\n\n" + _SCHRITTE_PRUEFER + "\n\n" + _SCHLUSS_PRUEFER)

SYSTEM_TRADER = ("Du beurteilst einen geplanten Handel - einen Kauf auf eine Gegenbewegung nach einem Rueckgang, "
                 "gehalten fuer 24 Stunden - anhand der Kurs- und Volumenlage EINES Werts. Name und Datum "
                 "erfaehrst du bewusst nicht; alle Angaben sind relativ zur eigenen Vergangenheit des Werts.\n\n"
                 + _SCHRITTE_PRUEFER + "\n\n" + _SCHLUSS_PRUEFER)

SYSTEM_ENTSCHEIDER = """Zwei Pruefer haben denselben geplanten Handel unabhaengig voneinander beurteilt: einer das Umfeld der \
Maerkte, einer die Kurs- und Volumenlage des Werts selbst. Du bekommst ihre Urteile, Belege und Gegengruende, nicht die \
Rohdaten.

DEINE AUFGABE: Waege beide Sichten gegeneinander ab und sage, ob du den geplanten Handel bestaetigst. Waehle GENAU EINES: \
bestaetigt, mit_vorbehalt oder einwand. Fehlt eine der beiden Sichten, urteile mit der vorhandenen und sage das.

Dann ein Satz Begruendung - ohne Einschraenkung im Nachsatz - und der staerkste Gegengrund in einem eigenen Feld.

Antworte AUSSCHLIESSLICH mit JSON:
{"urteil": "bestaetigt|mit_vorbehalt|einwand",
 "begruendung": "<ein Satz>",
 "gegengrund": "<der staerkste Grund gegen dein Urteil>"}"""

# 0.1d (K-b): sieht der Entscheider NUR den Trader, bekommt er einen Prompt, der genau das sagt - der Zwei-Pruefer-Text haette
# ihn bei jedem Aufruf *eine Sicht fehlt* melden lassen.
SYSTEM_ENTSCHEIDER_EIN = """Ein Pruefer hat einen geplanten Handel anhand der Kurs- und Volumenlage des Werts beurteilt. Du bekommst \
sein Urteil, seine Belege und seinen Gegengrund, nicht die Rohdaten.

DEINE AUFGABE: Waege seine Belege und seinen Gegengrund gegeneinander ab und sage, ob du den geplanten Handel bestaetigst. \
Waehle GENAU EINES: bestaetigt, mit_vorbehalt oder einwand.

Dann ein Satz Begruendung - ohne Einschraenkung im Nachsatz - und der staerkste Gegengrund in einem eigenen Feld.

Antworte AUSSCHLIESSLICH mit JSON:
{"urteil": "bestaetigt|mit_vorbehalt|einwand",
 "begruendung": "<ein Satz>",
 "gegengrund": "<der staerkste Grund gegen dein Urteil>"}"""

# 0.2 (F3): sagt, was die zwei Teile der Lage sind - OHNE eine Richtung zu verraten (F4)
SYSTEM_TRADER_02 = ("Du beurteilst einen geplanten Handel - einen Kauf auf eine Gegenbewegung nach einem Rueckgang, "
                    "gehalten fuer 24 Stunden - anhand der Lage EINES Werts. Name und Datum erfaehrst du bewusst nicht. "
                    "'lage_zur_signalstunde' beschreibt die Stunden bis zum Signal (Kurs, Umsatz, Terminmarkt, Bitcoin), "
                    "'lage_des_werts' den weiteren Rahmen ueber Tage und Monate, relativ zur eigenen Vergangenheit des Werts. "
                    "Gewichte die Angaben selbst; keine Angabe ist fuer sich ein Ausschluss.\n\n"
                    + _SCHRITTE_PRUEFER + "\n\n" + _SCHLUSS_PRUEFER)

SYSTEM = {"markt": SYSTEM_MARKT, "trader": SYSTEM_TRADER, "entscheider": SYSTEM_ENTSCHEIDER}


def system_fuer(rolle: str, katalog: dict) -> str:
    """Der Prompt einer Rolle in DIESER Fassung (0.1d: Entscheider mit nur einem Eingang)."""
    if rolle == "entscheider" and list((katalog.get("rollen") or {}).get("entscheider", {}).get("eingaenge") or []) == ["trader"]:
        return SYSTEM_ENTSCHEIDER_EIN
    if rolle == "trader" and (katalog.get("rollen") or {}).get("trader", {}).get("signal"):
        return SYSTEM_TRADER_02
    return SYSTEM[rolle]


def pruefsumme(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------- Validierung (Form korrigieren, Sinn nie raten)
class AntwortUngueltig(ValueError):
    pass


def _wort(x) -> str:
    t = str(x or "").strip().lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace(" ", "_").replace("-", "_")
    return t


def validiere(rolle: str, a) -> dict:
    """Das Urteil wird NIE geraten: nur die genannten Woerter (nach Gross-/Kleinschreibung, Umlaut, Leerzeichen). Sonst ungueltig.
    Belege: hoechstens sechs, unbrauchbare fallen weg und werden vermerkt."""
    if not isinstance(a, dict):
        raise AntwortUngueltig("keine JSON-Struktur")
    erlaubt = URTEILE_ENTSCHEIDER if rolle == "entscheider" else URTEILE_PRUEFER
    u = _wort(a.get("urteil"))
    if u not in erlaubt:
        raise AntwortUngueltig("Urteil %r nicht in %s" % (a.get("urteil"), "/".join(erlaubt)))
    aus = {"urteil": u, "begruendung": str(a.get("begruendung") or "").strip()[:400],
           "gegengrund": str(a.get("gegengrund") or "").strip()[:400], "korrekturen": []}
    if rolle != "entscheider":
        belege = []
        for b in (a.get("belege") or []):
            if isinstance(b, dict) and str(b.get("fakt") or "").strip():
                ri = _wort(b.get("richtung"))
                belege.append({"fakt": str(b["fakt"]).strip()[:240], "richtung": ri if ri in ("dafuer", "dagegen", "neutral") else "neutral"})
        if len(belege) > MAX_BELEGE:
            aus["korrekturen"].append("%d Belege, gekuerzt auf %d" % (len(belege), MAX_BELEGE))
            belege = belege[:MAX_BELEGE]
        if not belege:
            aus["korrekturen"].append("keine Belege geliefert")
        aus["belege"] = belege
    if not aus["begruendung"]:
        aus["korrekturen"].append("keine Begruendung geliefert")
    return aus


def zahlendeckung(antwort: dict, eingabe: dict) -> list:
    """Z-1 der Treuepruefung: Zahlen der Belege, die in der Eingabe NICHT stehen - gezaehlt, nicht verworfen."""
    from agent import gegenpruefer_rollen as Z1
    quelle = json.dumps(eingabe, ensure_ascii=False)
    da = Z1._zahlen(quelle)
    text = " ".join([b["fakt"] for b in antwort.get("belege") or []] + [antwort.get("begruendung") or ""])
    return [z for z in Z1._zahlen(text) if abs(z) not in Z1._HARMLOS and not any(abs(z - x) <= Z1.TOLERANZ for x in da)]


def anonym_verletzt(eingabe: dict, r: dict) -> list:
    """Wird der Wert erkennbar? Name, Bitpanda-Name, Jahreszahl oder der Kurs der Signalstunde im Eingabetext."""
    import re
    text = json.dumps(eingabe, ensure_ascii=False)
    funde = []
    for n in {str(r.get("symbol") or ""), str(r.get("bitpanda") or "")}:
        if len(n) >= 2 and re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(n), text):
            funde.append("Name %s" % n)
    if re.search(r"\b20[12]\d\b", text):
        funde.append("Jahreszahl")
    k = r.get("kurs")
    if k:
        for form in {("%.6g" % k), ("%.2f" % k).replace(".", ",")}:
            if len(form) >= 4 and form in text:
                funde.append("Kurs %s" % form)
    return funde


# ---------------------------------------------------------------------------- kein Ressourcen- und Abfragestau
def _pazifik_tag() -> str:
    """Der Tagesschluessel, an dem Google das Kontingent zuruecksetzt (wie api.gemini._kontingent_tag)."""
    try:
        from api.gemini import _kontingent_tag
        return _kontingent_tag()
    except Exception:                                        # noqa: BLE001
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class Umlauf:
    """Die Grenzen EINES Stundenlaufs (Nutzer 03.10.: *damit es keinen Ressourcen- und Abfragestau gibt*).

    Die Lehren aus dem ersten Bau, die hier greifen:
      - Gemini: 500 je Tag und MODELL, ein Topf fuer Desktop und NB, dazu eine Burst-Grenze (429). Der Client drosselt je
        Minute und prueft das Tagesbudget vor jedem Aufruf - deshalb DERSELBE Client wie die Spot-Kette, keine zweite Drossel.
      - Ausfaelle ohne Ausweichen (2.454-gemini, 34 x HTTP 503): nach ``ausfall_schwelle`` Fehlern in Folge fragt der Lauf nicht mehr.
      - Warteschlange laenger als der Hauptfaden (G19, 85 von 159 ohne Rolle G): hier KEIN Nebenfaden - alles nacheinander, mit
        Zeitgrenze je Signal und je Lauf; was nicht drankommt, bekommt einen Vermerk, die Mail geht trotzdem (P-8).
      - Das eigene Tageslimit schuetzt die Spot-Kette, die auf 3.5 ausweicht, wenn 3.1 erschoepft ist. Gezaehlt wird in der
        REGEL0-Ablage (Tabelle pruefung) - kein Schreiben in die Produktion."""

    def __init__(self, katalog: dict, client=None, ablage: str | None = None):
        self.k = katalog
        self.client = client
        self.ablage = ablage
        self.start = time.time()
        self.signale = 0
        self.fehler_in_folge = 0
        self.aufrufe = 0

    def heute_gefragt(self) -> int:
        if not self.ablage:
            return 0
        try:
            c = AB.oeffne(self.ablage)
            try:
                return int(c.execute("SELECT COALESCE(SUM(COALESCE(aufrufe, 1)), 0) FROM pruefung WHERE tag_pazifik=? AND gefragt=1",
                                     (_pazifik_tag(),)).fetchone()[0])
            finally:
                c.close()
        except Exception:                                    # noqa: BLE001
            return 0

    def gesperrt(self) -> str | None:
        if self.fehler_in_folge >= int(self.k.get("ausfall_schwelle") or 3):
            return "%d Fehler in Folge - der Lauf fragt nicht mehr" % self.fehler_in_folge
        if time.time() - self.start > float(self.k.get("lauf_zeitgrenze_s") or 600):
            return "Zeitgrenze des Laufs erreicht"
        if self.signale > int(self.k.get("max_signale_je_lauf") or 6):
            return "mehr als %s Signale in diesem Lauf" % self.k.get("max_signale_je_lauf")
        if self.heute_gefragt() >= int(self.k.get("tageslimit_aufrufe") or 150):
            return "Tageslimit des Blocks (%s Aufrufe) erreicht" % self.k.get("tageslimit_aufrufe")
        st = getattr(self.client, "budget_status", None)
        if st is not None:
            try:
                if st(self.k["modell"]).get("erschoepft"):
                    return "Tagesbudget von %s erschoepft" % self.k["modell"]
            except Exception:                                # noqa: BLE001
                pass
        return None

    def gebucht(self, ok: bool) -> None:
        self.aufrufe += 1
        self.fehler_in_folge = 0 if ok else self.fehler_in_folge + 1


# ---------------------------------------------------------------------------- Aufruf
def frage(client, modell: str, system: str, eingabe: dict, temperatur: float = 0.0) -> dict:
    roh = client.chat([{"role": "system", "content": system},
                       {"role": "user", "content": json.dumps(eingabe, ensure_ascii=False)}],
                      model=modell, temperature=temperatur, response_format={"type": "json_object"})
    text = roh if isinstance(roh, str) else str(roh)
    a, e = text.find("{"), text.rfind("}")
    if a < 0 or e < a:
        raise AntwortUngueltig("keine JSON-Struktur: %s" % text[:160])
    return json.loads(text[a:e + 1])


# ---------------------------------------------------------------------------- Ablage
def _schluessel(r: dict) -> tuple:
    return (r["symbol"], r["signalstunde"])


def _merke(c, r: dict, rolle: str, katalog: dict, eingabe: dict | None, ergebnis: dict | None, roh: dict | None,
           sekunden: float, fehler: str | None, deckung: list | None = None, gefragt: bool = False,
           aufrufe: int = 1) -> None:
    ein = json.dumps(eingabe, ensure_ascii=False) if eingabe is not None else None
    c.execute("INSERT OR REPLACE INTO pruefung (symbol, signalstunde, rolle, fassung, modell, prompt_pruefsumme, eingabe_pruefsumme, "
              "eingabe, antwort, urteil, ergebnis, sekunden, fehler, ungedeckt, am, gefragt, tag_pazifik, aufrufe) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (r["symbol"], r["signalstunde"], rolle, katalog["fassung"], katalog["modell"], pruefsumme(system_fuer(rolle, katalog)),
               pruefsumme(ein) if ein else None, ein, json.dumps(roh, ensure_ascii=False) if roh is not None else None,
               (ergebnis or {}).get("urteil"), json.dumps(ergebnis, ensure_ascii=False) if ergebnis is not None else None,
               round(sekunden, 2), fehler, json.dumps(deckung) if deckung else None,
               datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), 1 if gefragt else 0, _pazifik_tag(),
               int(aufrufe) if gefragt else 0))
    c.commit()


def _markt_aus_ablage(c, katalog: dict, eingabe_summe: str) -> dict | None:
    """R-2: gleiche Fakten, gleiches Urteil - eine fruehere Markt-Antwort derselben Fassung auf dieselbe Eingabe wird wiederverwendet."""
    z = c.execute("SELECT ergebnis FROM pruefung WHERE rolle='markt' AND fassung=? AND prompt_pruefsumme=? AND eingabe_pruefsumme=? "
                  "AND ergebnis IS NOT NULL ORDER BY am DESC LIMIT 1", (katalog["fassung"], pruefsumme(SYSTEM_MARKT), eingabe_summe)).fetchone()
    return json.loads(z[0]) if z else None


# ---------------------------------------------------------------------------- der Ablauf je Signal
def pruefe_signal(r: dict, client, ordner_ablage: str, ordner_daten: str, db: str, katalog: dict | None = None,
                  zeitgrenze_s: float | None = None, umlauf: "Umlauf | None" = None) -> dict:
    """{rolle: {urteil, begruendung, gegengrund, belege?, quelle} | {"fehlt": grund}} - scheitert NIE (P-8).
    ``umlauf``: die Grenzen des Stundenlaufs (EIN Umlauf fuer alle Signale einer Stunde); ohne ihn gilt ein eigener."""
    katalog = katalog or lade()
    umlauf = umlauf or Umlauf(katalog, client, ordner_ablage)
    umlauf.signale += 1
    grenze = time.time() + float(zeitgrenze_s if zeitgrenze_s is not None else katalog.get("zeitgrenze_s") or 90)
    rollen = katalog["rollen"]
    aus: dict = {}
    c = AB.oeffne(ordner_ablage)
    try:
        def _rolle(name: str, eingabe: dict | None, wiederverwenden: bool = False) -> None:
            if not rollen.get(name, {}).get("an"):
                return
            if eingabe is None:
                aus[name] = {"fehlt": "keine Eingabe (Daten fehlen)"}
                _merke(c, r, name, katalog, None, None, None, 0.0, "keine Eingabe")
                return
            summe = pruefsumme(json.dumps(eingabe, ensure_ascii=False))
            if wiederverwenden:
                alt = _markt_aus_ablage(c, katalog, summe)
                if alt:
                    aus[name] = dict(alt, quelle="wiederverwendet (gleiche Fakten)")
                    return
            if client is None:
                aus[name] = {"fehlt": "kein Sprachmodell verfuegbar"}
                return
            if time.time() > grenze:
                aus[name] = {"fehlt": "Zeitgrenze erreicht"}
                return
            sperre = umlauf.gesperrt()
            if sperre:
                aus[name] = {"fehlt": sperre}
                _merke(c, r, name, katalog, eingabe, None, None, 0.0, "nicht gefragt: " + sperre)
                return
            # ⚠️ 0.1c (P1, 03.10.2026): SELBSTKONSISTENZ. Bei identischer Eingabe und Temperatur 0 waren nur 15 von 23
            # Wiederholungen gleich (65 %, Ziel 90 %; vgl. E14: 30 % Kippen bei t = 0). Deshalb `stimmen` Aufrufe je Rolle und
            # das MEHRHEITSurteil; ohne Mehrheit steht *uneinig* da - ein Fakt ueber das Modell, kein geratenes Urteil.
            t0 = time.time()
            n_st = max(1, int(katalog.get("stimmen") or 1))
            gueltig, rohe, fehler_letzt = [], [], None
            for _ in range(n_st):
                if _ and (umlauf.gesperrt() or time.time() > grenze):
                    break
                try:
                    roh = frage(client, katalog["modell"], system_fuer(name, katalog), eingabe, float(katalog.get("temperatur") or 0.0))
                    umlauf.gebucht(True)
                    rohe.append(roh)
                    gueltig.append(validiere(name, roh))
                except AntwortUngueltig as exc:
                    fehler_letzt = "Antwort ungueltig: %s" % str(exc)[:160]
                except Exception as exc:                     # noqa: BLE001
                    umlauf.gebucht(False)
                    fehler_letzt = "%s: %s" % (type(exc).__name__, str(exc)[:160])
                    break
            if not gueltig:
                aus[name] = {"fehlt": fehler_letzt or "keine gueltige Antwort"}
                _merke(c, r, name, katalog, eingabe, None, rohe or None, time.time() - t0, aus[name]["fehlt"], gefragt=True,
                       aufrufe=len(rohe) or 1)
                return
            zahl = {}
            for g_ in gueltig:
                zahl[g_["urteil"]] = zahl.get(g_["urteil"], 0) + 1
            best, k = max(zahl.items(), key=lambda x: x[1])
            if k * 2 > len(gueltig) or len(gueltig) == 1:
                erg = dict(next(g_ for g_ in gueltig if g_["urteil"] == best))
            else:
                erg = dict(gueltig[0], urteil="uneinig")
            erg["stimmen"] = [g_["urteil"] for g_ in gueltig]
            deck = zahlendeckung(erg, eingabe) if name != "entscheider" else []
            aus[name] = dict(erg, quelle="neu")
            _merke(c, r, name, katalog, eingabe, erg, rohe, time.time() - t0, None, deck, gefragt=True, aufrufe=len(rohe))

        try:
            ein_m = markt_eingabe(r, db)
        except Exception:                                    # noqa: BLE001
            ein_m = None
        _rolle("markt", ein_m, wiederverwenden=True)
        try:
            ein_t = trader_eingabe(r, ordner_daten, katalog, db)
        except Exception:                                    # noqa: BLE001
            ein_t = None
        if ein_t is not None and anonym_verletzt(ein_t, r):
            aus["trader"] = {"fehlt": "Eingabe nicht anonym (%s) - nicht gefragt" % ", ".join(anonym_verletzt(ein_t, r))}
        else:
            _rolle("trader", ein_t)
        if rollen.get("entscheider", {}).get("an"):
            sichten = {}
            for e in rollen["entscheider"].get("eingaenge") or []:
                x = aus.get(e)
                if x and "urteil" in x:
                    sichten[e] = {k: x[k] for k in ("urteil", "begruendung", "gegengrund", "belege") if k in x}
                else:
                    sichten[e] = "keine Auskunft"
            if all(v == "keine Auskunft" for v in sichten.values()):
                aus["entscheider"] = {"fehlt": "keine der beiden Sichten liegt vor"}
            else:
                ein_e = {"geplant": plan_text(r), "lage_des_werts": sichten.get("trader", "keine Auskunft")}
                if "markt" in sichten:
                    ein_e["umfeld_der_maerkte"] = sichten["markt"]
                if anonym_verletzt(ein_e, r):
                    aus["entscheider"] = {"fehlt": "Eingabe nicht anonym - nicht gefragt"}
                else:
                    _rolle("entscheider", ein_e)
    finally:
        c.close()
    return aus


def mail_zeilen(ergebnis: dict, katalog: dict | None = None) -> list:
    """Der Block PRUEFUNG fuer die Signalmail - Auskunft, loest nichts aus; ein Ausfall steht grau da, nie als Zustimmung."""
    katalog = katalog or lade()
    z = ["PRUEFUNG DURCH DIE ROLLEN  (Fassung %s, %s - Auskunft, loest nichts aus)" % (
        katalog["fassung"], "SOFORTFASSUNG, UNGEMESSEN" if "sofort" in str(katalog["fassung"]) else "gemessen"), ""]
    for rolle, titel in (("markt", "Markt"), ("trader", "Trader"), ("entscheider", "Entscheider")):
        x = ergebnis.get(rolle)
        if x is None:
            continue
        if "urteil" not in x:
            z.append("  %-12s (keine Auskunft: %s)" % (titel, x.get("fehlt", "?")))
            continue
        if rolle == "markt" and katalog["rollen"].get("markt", {}).get("nur_auskunft"):
            # 0.1d: das Umfeld als BESCHREIBUNG - ohne Urteilswort, weil es ueber alle Phasen dasselbe sagte (R-T6)
            z.append("  %-12s %-16s %s" % ("Umfeld", "(Auskunft)", x.get("begruendung") or ""))
            if x.get("gegengrund"):
                z.append("  %-12s %-16s Gegengrund: %s" % ("", "", x["gegengrund"]))
            continue
        st = x.get("stimmen") or []
        # 0.1e: bei fuenf Stimmen die Auszaehlung statt der Liste - *neutral (4 von 5)*; ohne Mehrheit jede Stufe mit Zahl
        if len(set(st)) <= 1:
            einig = ""
        elif x["urteil"] != "uneinig":
            einig = " (%d von %d)" % (st.count(x["urteil"]), len(st))
        else:
            einig = " (%s)" % ", ".join("%d %s" % (st.count(s_), WORT.get(s_, s_)) for s_ in sorted(set(st), key=st.index))
        z.append("  %-12s %-16s %s" % (titel, WORT.get(x["urteil"], x["urteil"]) + einig, x.get("begruendung") or ""))
        if x.get("gegengrund"):
            z.append("  %-12s %-16s Gegengrund: %s" % ("", "", x["gegengrund"]))
    if katalog["rollen"].get("markt", {}).get("nur_auskunft") and "markt" in ergebnis:
        z.append("  (Umfeld nur als Beschreibung: es urteilte im Kalibrierlauf ueber 2025 und 2026 zu 85 % gleich - P1, 03.10.)")
    if not katalog["rollen"].get("entscheider", {}).get("an"):
        # 0.1e (E-53): mit nur dem Trader als Eingang war er ein Echo (39 von 40) - ausgesetzt, nicht gestrichen
        z.append("  (Entscheider ausgesetzt: er wiederholte den Trader in 39 von 40 Faellen - E-53, Neupruefung mit dem Rueckspiel)")
    z += ["", "  Messstand: noch nicht gemessen (Sofortfassung E-52/E-53; die gemessene Fassung folgt nach Rueckspiel und Bestaetigung)."]
    return z


def _erster_satz(text: str, grenze: int = 220) -> str:
    t = " ".join(str(text or "").split())
    for trenner in (". ", "! ", "? "):
        i = t.find(trenner)
        if 0 < i < grenze:
            return t[:i + 1]
    return t if len(t) <= grenze else t[:grenze].rsplit(" ", 1)[0] + " …"


def mail_teile(ergebnis: dict, katalog: dict | None = None) -> dict:
    """O25 (04.10.2026): die Rollen fuer die neue REGEL0-Mail getrennt in KURZ (eine Zeile je Rolle, Abschnitt Einschaetzung)
    und LANG (der ganze Block wie bisher, Abschnitt Begruendung). Ein Ausfall steht als *keine Auskunft*, nie als Zustimmung."""
    katalog = katalog or lade()
    kurz, detail = [], []
    for rolle, titel in (("trader", "Trader"), ("markt", "Umfeld"), ("entscheider", "Entscheider")):
        x = ergebnis.get(rolle)
        if x is None:
            continue
        if "urteil" not in x:
            kurz.append((titel, "keine Auskunft (%s)" % x.get("fehlt", "?")))
            detail.append((titel, "keine Auskunft (%s)" % x.get("fehlt", "?"), "", ""))
            continue
        if rolle == "markt" and katalog["rollen"].get("markt", {}).get("nur_auskunft"):
            kurz.append((titel, "%s (nur Beschreibung)" % _erster_satz(x.get("begruendung"))))
            detail.append((titel, "nur Beschreibung", x.get("begruendung") or "", x.get("gegengrund") or ""))
            continue
        st = x.get("stimmen") or []
        if len(st) <= 1:
            einig = ""
        elif x["urteil"] != "uneinig":
            einig = " (%d von %d)" % (st.count(x["urteil"]), len(st))      # auch einstimmig: *(5 von 5)* sagt, wie sicher
        else:
            einig = " (%s)" % ", ".join("%d %s" % (st.count(s_), WORT.get(s_, s_)) for s_ in sorted(set(st), key=st.index))
        kurz.append((titel, "%s%s - %s" % (WORT.get(x["urteil"], x["urteil"]), einig, _erster_satz(x.get("begruendung")))))
        detail.append((titel, "%s%s" % (WORT.get(x["urteil"], x["urteil"]), einig), x.get("begruendung") or "", x.get("gegengrund") or ""))
    lang = mail_zeilen(ergebnis, katalog)
    # fuer die HTML-Fassung: dieselben Saetze gegliedert, dazu die Hinweiszeilen (Fassung, Umfeld, Entscheider, Messstand)
    hinweise = [lang[0].strip()] + [z.strip() for z in lang[1:] if z.strip().startswith(("(", "Messstand"))]
    return {"kurz": kurz, "lang": lang, "detail": detail, "hinweise": hinweise}

