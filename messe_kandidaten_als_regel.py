# -*- coding: utf-8 -*-
"""Die fuenf Kandidaten, jeder als REGEL gerechnet (30.08.2026).

Ruft `messe_regel_wirksamkeit.bericht()` fuer jeden Kandidaten auf. Die
Merkmale werden hier gebaut, die Wirksamkeitsrechnung liegt dort - so gilt
fuer alle derselbe Massstab.

## Die Kandidaten und ihre Datenlage

  1 TURNOVER    Volumen / Umlaufmenge         66 Symbole (Umlaufmenge noetig)
  2 AMIHUD      |Rendite| / Umsatz            523 Symbole - nur Kursdaten
  3 MOMENTUM    12 Monate ohne den letzten    523 Symbole - nur Kursdaten
  4 FUNDING     Niveau, Querschnitt           290 Symbole - KONTROLLE, muss
                                              +0,024 R reproduzieren
  5 OI / MC     ⚠️ NICHT MESSBAR - Binance liefert Open Interest nur 30 Tage
                rueckwirkend (geprueft 30.08.), eine eigene Reihe gibt es
                erst seit 14.07. und sie ist unterbrochen
  6 VOLA-PRAEMIE ⚠️ NICHT OHNE WEITERES - implizite Volatilitaet gibt es bei
                Deribit nur fuer BTC und ETH; zwei Symbole sind kein
                Querschnitt

## ⚠️ Kandidat 4 ist die eingebaute Kontrolle

Funding ist bereits als Regel gerechnet (+0,0242 R). Weicht das Ergebnis hier
ab, stimmt etwas am gemeinsamen Werkzeug nicht - dann gilt kein Befund dieses
Laufs.

---

# ERWEITERUNG 31.08.2026 — DIE HORIZONTACHSE (Umbau Schritt 1)

⚠️ DIESER ABSCHNITT IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Warum

Der Umbau gibt jedem Asset mehrere ZELLEN aus (Instrument x Strategie). Die
drei tragenden Beitraege sind aber alle auf **H20** gemessen - zwanzig
Handelstage. Fuer `hebel x einstieg` ist das die falsche Geometrie:

    Nutzervorgabe 31.08.   Hebel ist ein kurzfristiger Trade, 1-20 Tage
    System plante          mindestziel_zeitraum_tage_geschaetzt 1,2-2,1 Tage

⚠️ **NICHT gemessen wird die realisierte Haltedauer.** Aus 188 echten
Bitpanda-Positionen liesse sich ein Median von 0,29 Tagen ableiten - aber das
sind 11 Symbole, davon TAO allein 84, und es ist NUTZERVERHALTEN. Wer das
misst, misst, wann jemand ausgestiegen ist, nicht ob die Empfehlung trug.
Fallstrick F5 im Umsetzungsplan.

## Vorab festgelegt - was als Befund gilt

    traegt auf H       Regelwirkung > 0 UND ausserhalb des Placebo-Bandes
                       UND die Positivkontrolle findet den gepflanzten Effekt
    traegt NICHT       sonst
    ⚠️ nicht uebertragbar  traegt auf H20, aber nicht auf H1..H5
                           -> dann darf der Beitrag fuer `hebel` NICHT
                              registriert werden (Fallstrick F4:
                              "leeres Feld als Erlaubnis lesen")

## ⚠️ DER SUCHPREIS — EINE Zelle entscheidet, nicht achtzehn

Sechs Horizonte mal drei Beitraege sind **18 Zellen**. Frei durchsucht waere
die Huerde +20,5 Punkte, eine vorab benannte kostet +10,2 (Methodik 2.49).
Deshalb wird sie hier benannt, VOR dem Lauf:

    ENTSCHEIDEND IST  H2

Begruendung aus den Daten, nicht aus Bequemlichkeit: das System plante
`mindestziel_zeitraum_tage_geschaetzt` = **1,2 bis 2,1 Tage** (Median der
1.998 Hebel-Signale). H2 ist der Horizont, auf dem die Empfehlung wirken
sollte.

Die uebrigen fuenf Horizonte sind **Robustheitspruefung, keine Suche**:
traegt der Beitrag, muss er ueber H1..H20 einen STETIGEN Verlauf zeigen.
Ein Beitrag, der nur bei H3 auftaucht und bei H2 und H5 verschwindet, ist
Rauschen - egal wie gross die Zahl ist.

## Trennschaerfe - vorab geprueft, nicht angenommen

Gemessen am 31.08. VOR dem Lauf: der Interquartilsabstand von `in_r`
**innerhalb eines Kalendertags** (das ist die Groesse, auf der der
Rangvergleich arbeitet):

    H1   0,38 R      H5   0,87 R      H20  1,85 R

Bei H1 ist die Trennschaerfe rund ein Fuenftel von H20. Sie ist vorhanden,
aber ein Effekt muss dort entsprechend groesser sein, um aus dem
Placebo-Band zu ragen. **Ein Nullbefund bei H1 ist deshalb kein Beweis
gegen den Beitrag** - er ist zuerst ein Hinweis auf fehlende Maechtigkeit
(vgl. [[project_messwerkzeuge_auf_kleiner_basis]]).

⚠️ Die Streuung ueber ALLE Tage (8,97 bei H1 bis 102 bei H20) ist durch die
bekannten Token-Umstellungen aufgeblaeht - 14 von 523 Reihen, LUNA Faktor
177.400. Der Median ist robust, die Streuung nicht; deshalb steht hier der
Interquartilsabstand.

## Die Kontrolle bleibt die Kontrolle

Funding muss bei **H20 weiterhin +0,0242 R** liefern. Weicht das ab, gilt kein
Befund dieses Laufs - unabhaengig davon, was die kurzen Horizonte zeigen.

    python messe_kandidaten_als_regel.py --horizonte 1,2,3,5,10,20
"""
import statistics as st
import sys
from zlib import crc32 as _crc32

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_regel_wirksamkeit as W

RUECKBLICK = 21          # Standardfenster fuer Amihud
MIND_JE_TAG = 12


SCHNITT_FENSTER = 200          # wie in `messe_schnittabstand_beitrag.py`


def lade_terminmarkt(db: str = "data/terminmarkt_historie.db") -> dict:
    """Die Terminmarkt-Tagesreihen aus dem Binance-Archiv (H-4c, 01.09.2026).

    ⚠️ DER STAND AM TAGESENDE, nicht der Mittelwert. Open Interest ist ein
    BESTAND; der Wert um 23:00 ist der Zustand des Tages. Dieselbe
    Begruendung wie beim Import (Methodik 2.85, die Form der Groesse).

    Rueckgabe: {kandidat: {SYMBOL: {datum: wert}}} - die Form, die `baue`
    als `zusatz` erwartet.

    ⚠️ ALLE KANDIDATEN SIND QUERSCHNITTSGROESSEN. Das ist keine Bequem-
    lichkeit, sondern N-13b (01.09.2026): die elf Werte ohne Binance-
    Perpetual sind die JUENGEREN (Median-Alter 496 gegen 1.113 Tage), und
    eine Zeitreihen-Groesse waere bei einem neu aufgenommenen Wert 250 Tage
    lang blind. Ein Querschnittsrang traegt ab Tag 1.
    """
    import sqlite3
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    # ⚠️ DIE TAGESTABELLE ZUERST (01.09.2026 abends). `terminmarkt_tag`
    # traegt die MESSBASIS - 100 Symbole ueber 1.733 Tage, davon nur zehn
    # aus der Watchlist. `terminmarkt` (stuendlich) traegt dagegen die 32
    # Watchlist-Werte, und genau darauf war H-4c untermaechtig (F-167:
    # "Watchlist statt Messbasis").
    #
    # Beide werden gelesen und zusammengefuehrt; wo beide einen Tag haben,
    # gewinnt die Tagestabelle - sie ist die breitere Grundlage.
    roh: dict = {}
    for sym, stunde, oi, oiw, topk, _tops, konten, taker in c.execute(
            "SELECT symbol, stunde, oi, oi_wert, top_konten_verh, "
            "top_summe_verh, konten_verh, taker_verh FROM terminmarkt "
            "ORDER BY symbol, stunde"):
        roh.setdefault(str(sym).upper(), {})[str(stunde)[:10]] = (
            oi, oiw, topk, konten, taker)
    try:
        for sym, tg, oi, oiw, topk, _tops, konten, taker in c.execute(
                "SELECT symbol, tag, oi, oi_wert, top_konten_verh, "
                "top_summe_verh, konten_verh, taker_verh FROM terminmarkt_tag "
                "ORDER BY symbol, tag"):
            roh.setdefault(str(sym).upper(), {})[str(tg)[:10]] = (
                oi, oiw, topk, konten, taker)
    except Exception:                                        # noqa: BLE001
        pass
    c.close()

    aus = {k: {} for k in ("oi_aenderung", "oi_wert", "long_bias",
                           "top_bias", "taker_bias")}
    for sym, je_tag in roh.items():
        tage = sorted(je_tag)
        for i, d in enumerate(tage):
            oi, oiw, topk, konten, taker = je_tag[d]
            # ⚠️ VERAENDERUNG, nicht Rohwert: der OI-Betrag ist zwischen
            # Assets nicht vergleichbar (BTC gegen BIO), seine relative
            # Aenderung schon. Form der Groesse, 2.85.
            if i and oi and je_tag[tage[i - 1]][0]:
                v = je_tag[tage[i - 1]][0]
                if v > 0:
                    aus["oi_aenderung"].setdefault(sym, {})[d] = oi / v - 1.0
            if oiw:
                aus["oi_wert"].setdefault(sym, {})[d] = float(oiw)
            # ⚠️ ROHWERT bei den Verhaeltnissen - sie SIND schon ein
            # Verhaeltnis und damit ueber Assets vergleichbar.
            for name, w in (("long_bias", konten), ("top_bias", topk),
                            ("taker_bias", taker)):
                if w is not None:
                    aus[name].setdefault(sym, {})[d] = float(w)
    return aus


def baue(reihen, art, zusatz=None, horizont=None):
    """Anker je Kalendertag mit dem gewuenschten Merkmal."""
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        v = np.array([z[4] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        umsatz = v * c
        rendite = np.zeros(len(c))
        rendite[1:] = np.abs(c[1:] / np.maximum(c[:-1], 1e-12) - 1.0)
        extra = (zusatz or {}).get(sym.upper())
        # ⚠️ DER HORIZONT IST JETZT EIN PARAMETER (31.08.2026). Vorher stand
        # hier `W.HORIZONT` fest auf 20 - fuer den Hebel die falsche
        # Geometrie. Die Vorgabe bleibt W.HORIZONT, damit jeder bestehende
        # Aufruf unveraendert dasselbe rechnet.
        _h = int(horizont or W.HORIZONT)
        # ---- N-17c: DIE FRONTLOADING-KANDIDATEN, HIER NACHGEZOGEN --------
        #
        # ⚠️ WARUM SIE HIER STEHEN UND NICHT IN `messe_form_kurz_gegen_lang`
        # (04.09.2026). Beide Module bauen Anker, aber mit VERSCHIEDENEM
        # R-Nenner: dort ein nachlaufender 250-Tage-Median der Breite, hier
        # `breite[i]` selbst. Die registrierten Beitragstabellen (Funding,
        # Turnover, OI) stehen alle auf DIESER Konvention - `rechne_*_
        # beitrag.py` liest ausschliesslich aus `baue()`.
        #
        # Eine Beitragstabelle fuer die Frontloading-Kandidaten muesste also
        # entweder hier gebaut werden oder in einer zweiten Kopie der
        # Fuenftel-Rechnung mit fremdem Nenner enden - und waere dann mit
        # den bestehenden Stufen NICHT vergleichbar. Additiv ergaenzt; kein
        # bestehendes `art` ist angefasst.
        _vorab_vola = _vorab_rsi = None
        if art == "vola":
            # dieselbe Form wie `messe_form_kurz_gegen_lang`: heutige Breite
            # gegen den eigenen nachlaufenden Normalzustand
            _vorab_vola = np.full(len(c), np.nan)
            for _j in range(260, len(c)):
                _f = breite[_j - 250:_j]
                _f = _f[np.isfinite(_f) & (_f > 0)]
                if len(_f) >= 100 and np.isfinite(breite[_j]):
                    _vorab_vola[_j] = breite[_j] / float(np.median(_f))
        elif art == "rsi":
            # RSI(14) nach Wilder - dieselbe Convolve-Form wie dort
            _d = np.diff(c, prepend=c[0])
            _g = np.convolve(np.where(_d > 0, _d, 0.0), np.ones(14),
                             "full")[:len(c)] / 14.0
            _l = np.convolve(np.where(_d < 0, -_d, 0.0), np.ones(14),
                             "full")[:len(c)] / 14.0
            _vorab_rsi = 100.0 - 100.0 / (1.0 + _g / np.maximum(_l, 1e-12))
        start = 260 if art in ("momentum", "vola") else RUECKBLICK + 40
        for i in range(start, len(c) - _h):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            wert = None
            if art == "amihud":
                u = umsatz[i - RUECKBLICK:i]
                rr = rendite[i - RUECKBLICK:i]
                gut = u > 0
                if gut.sum() >= RUECKBLICK // 2:
                    wert = float(np.mean(rr[gut] / u[gut]) * 1e9)
            elif art == "momentum":
                if c[i - 252] > 0:
                    wert = float(c[i - 21] / c[i - 252] - 1.0)
            elif art == "turnover":
                menge = (extra or {}).get(tage[i])
                if menge and menge > 0:
                    wert = float(v[i] / menge)
            elif art == "funding":
                wert = (extra or {}).get(tage[i])
            elif art in ("oi_aenderung", "long_bias", "top_bias",
                         "taker_bias"):
                # H-4c: die Terminmarkt-Groessen, alle als Querschnitt
                wert = (extra or {}).get(tage[i])
            elif art == "oi_je_umsatz":
                # ⚠️ VERHAELTNIS: Hebelaufbau JE LIQUIDITAET. Der reine
                # OI-Betrag ist zwischen Assets nicht vergleichbar; sein
                # Verhaeltnis zum Tagesumsatz schon - und genau das nennt
                # die Praxisliteratur als Mass fuer Ueberhebelung.
                _oiw = (extra or {}).get(tage[i])
                _umsatz = float(v[i]) * float(c[i]) if c[i] else 0.0
                if _oiw and _umsatz > 0:
                    wert = float(_oiw) / _umsatz
            # ---- N-17c: die vier nachgezogenen Kandidaten ---------------
            elif art == "vola":
                _w = _vorab_vola[i]
                if np.isfinite(_w):
                    wert = float(_w)
            elif art == "rsi":
                _w = _vorab_rsi[i]
                if np.isfinite(_w):
                    wert = float(_w)
            elif art == "momentum_kurz":
                # ⚠️ DREI TAGE - dasselbe kurze Fenster wie `FL.KURZ`, nicht
                # das 12-Monats-`momentum` oben. Zwei verschiedene Groessen
                # mit aehnlichem Namen; die Verwechslung waere ein
                # Namensschatten (T4c).
                if c[i - 3] > 0:
                    wert = float(c[i] / c[i - 3] - 1.0)
            elif art == "funding_extrem":
                # ⚠️ NACHLAUFEND, nie ueber die ganze Reihe - ein Perzentil
                # ueber alles kennt die Zukunft. Identische Form wie in
                # `messe_form_kurz_gegen_lang`: Abstand vom eigenen
                # Normalzustand in MAD, VORZEICHENLOS.
                _fw = (extra or {}).get(tage[i])
                if _fw is not None:
                    _hi = [(extra or {}).get(d) for d in tage[max(0, i - 250):i]]
                    _hi = [x for x in _hi if x is not None]
                    if len(_hi) >= 100:
                        _ha = np.array(_hi, float)
                        _med = float(np.median(_ha))
                        _mad = float(np.median(np.abs(_ha - _med)))
                        if _mad > 1e-12:
                            wert = float(abs(_fw - _med) / _mad)
            elif art == "zufall":
                # ⚠️ DIE KONTROLLGROESSE. Sie MUSS eine flache Tabelle
                # liefern; tut sie es nicht, traegt das VERFAHREN und kein
                # Befund des Laufs gilt. Saat aus Symbol+Datum, damit der
                # Wert reproduzierbar und nicht laufabhaengig ist.
                #
                # ⚠️ NICHT `hash()` - der ist fuer Strings pro Prozess
                # randomisiert (PYTHONHASHSEED), die Kontrollgroesse waere
                # dann bei jedem Lauf eine andere und ein Fehlalarm nicht
                # nachvollziehbar. `crc32` ist stabil.
                wert = float(np.random.default_rng(
                    _crc32(("%s|%s" % (sym, tage[i])).encode())).random())
            elif art == "schnitt50":
                # ⚠️ NUTZERIDEE 31.08.: *"Was ist mit dem 50-Schnitt bzw.
                # Abstand - haben wir diesen gemessen?"* Nein. Gemessen
                # wurde der 200er (am 31.08. gefallen, bei keinem Horizont
                # trennbar). Der 50er kommt im System nur als MARKTBREITE
                # vor ("18 von 51 Coins ueber ihrer 50-Tage-Linie"), nie
                # als eigener Abstand je Asset.
                #
                # ⚠️ VORAB BENANNT, warum gerade 50 und keine freie Suche
                # ueber 20/50/100: der Handelshorizont liegt bei 1 bis 20
                # Tagen, der 200er misst die Lage im Jahrestrend. Der 50er
                # ist die naechstliegende Skala OBERHALB des Horizonts -
                # nah genug fuer die Lage, weit genug gegen das
                # Tagesrauschen. EINE Zelle, vorab benannt (Suchpreis 2.49).
                #
                # ⚠️ UND DIE EHRLICHE ERWARTUNG: der 200er traegt nicht,
                # Amihud nicht, Momentum nicht - alle drei aus derselben
                # Quelle. Der Grundbefund vom 10.08. lautet "die
                # Information steckt nicht in den Kursdaten". Ein
                # Nullbefund waere die Regel, kein Ausreisser.
                if i >= 50:
                    _m50 = c[i - 50:i].mean()
                    if _m50 > 0:
                        wert = float(c[i] / _m50 - 1.0)
            elif art == "schnitt":
                # ⚠️ DER DRITTE TRAGENDE BEITRAG HAT HIER GEFEHLT
                # (31.08.2026). Er wurde in `messe_schnittabstand_beitrag.py`
                # gemessen, stand aber nie in dieser Kandidatenliste - und
                # damit lief er nie ueber DENSELBEN Massstab wie Funding und
                # Turnover. Genau dafuer ist diese Datei da.
                if i >= SCHNITT_FENSTER:
                    _m = c[i - SCHNITT_FENSTER:i].mean()
                    if _m > 0:
                        wert = float(c[i] / _m - 1.0)
            if wert is None or not np.isfinite(wert):
                continue
            je_tag.setdefault(tage[i], []).append(
                {"sym": sym, "kennzahl": wert,
                 "in_r": float((c[i + _h] - c[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_JE_TAG}


def horizontlauf(reihen, menge, funding, horizonte):
    """Die drei TRAGENDEN Beitraege ueber mehrere Horizonte (31.08.2026).

    ⚠️ NUR die drei registrierten - Amihud und Momentum sind gemessen und
    tragen nicht; sie hier mitzurechnen hiesse, die Zellenzahl und damit den
    Suchpreis zu erhoehen, ohne dass eine Entscheidung daran haengt
    (Methodik 2.49).
    """
    rng = np.random.default_rng(20260831)
    fertig = {}
    for h in horizonte:
        print()
        print("#" * 92)
        print("# HORIZONT H%d" % h)
        print("#" * 92)
        for art, klar, oben in (("funding", "FUNDING-Rang", True),
                                ("turnover", "TURNOVER-Rang", True),
                                ("schnitt", "ABSTAND ZUM 200-SCHNITT", True),
                                ("schnitt50", "ABSTAND ZUM 50-SCHNITT", True)):
            extra = {"funding": funding, "turnover": menge}.get(art)
            je_tag = baue(reihen, art, extra, horizont=h)
            if not je_tag:
                print("  H%-3d %-26s zu wenige Anker" % (h, klar))
                continue
            e = W.bericht("H%d %s" % (h, klar), je_tag, oben, rng,
                          mit_positivkontrolle=(h == horizonte[0]))
            fertig[(h, art)] = e
    return fertig


def geschichtet(je_tag, schicht_je_tag, faecher=5, mische=None):
    """Die Regel WITHIN den Faechern einer zweiten Groesse (02.09.2026).

    ⚠️ WOFUER. Pruefliste 2.80, Frage 1: *ist der Kandidat ein Mitlaeufer?*
    `oi_aenderung` und `funding` kommen beide vom Terminmarkt derselben
    Boerse. Traegt die OI-Regel nur deshalb, weil sie nebenbei hohes Funding
    aussortiert, ist sie kein eigener Beitrag - sie ist Funding mit Umweg.

    Der Test haelt Funding fest: je Kalendertag werden die Werte zuerst nach
    der SCHICHT in Fuenftel sortiert, und die OI-Regel sperrt dann das
    oberste Fuenftel INNERHALB jedes Faches. Ueber alle Faecher hinweg ist
    die Funding-Verteilung der Gesperrten damit dieselbe wie die der
    Behaltenen. Was uebrig bleibt, kann Funding nicht mehr erklaeren.

    ⚠️ Der Preis: die Faecher sind klein (ein Fuenftel eines Tages). Ein
    Fach mit weniger als drei Behaltenen wird uebersprungen, sonst misst man
    Einzelwerte. Das Band wird dadurch breiter - ein Nullbefund hier ist
    schwaecher als ein Nullbefund oben.
    """
    aus = {}
    for tag, z in je_tag.items():
        s = schicht_je_tag.get(tag)
        if not s:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        sw = np.array([s.get(x["sym"], np.nan) for x in z], float)
        gut = np.isfinite(sw)
        if gut.sum() < MIND_JE_TAG:
            continue
        w, y, sw = w[gut], y[gut], sw[gut]
        fach = np.minimum((W.rang(sw) * faecher).astype(int), faecher - 1)
        frei = np.ones(len(w), bool)
        genutzt = np.zeros(len(w), bool)
        for f in range(faecher):
            m = fach == f
            if m.sum() < 4:
                continue
            r = W.rang(w[m])
            if mische is not None:
                r = mische.permutation(r)
            lok = r < W.GRENZE
            if lok.sum() < 3 or (~lok).sum() < 1:
                continue
            idx = np.flatnonzero(m)
            frei[idx] = lok
            genutzt[idx] = True
        if genutzt.sum() < MIND_JE_TAG or frei[genutzt].sum() < 3:
            continue
        aus[tag] = float(np.median(y[genutzt & frei]) - np.median(y[genutzt]))
    return aus


def mitlaeufer():
    """H-4c Gegenpruefung: ist `oi_aenderung` nur Funding mit Umweg?"""
    reihen = B.lade()
    rng = np.random.default_rng(20260902)
    funding = F.lade_funding()
    tm = lade_terminmarkt()

    oi = baue(reihen, "oi_aenderung", tm["oi_aenderung"], horizont=20)
    fu = baue(reihen, "funding", funding, horizont=20)
    # gemeinsame Anker: nur Tage und Symbole, die BEIDE Groessen haben
    fu_je_tag = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in fu.items()}
    oi_je_tag = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in oi.items()}
    gem_oi, gem_fu = {}, {}
    for t, z in oi.items():
        s = fu_je_tag.get(t) or {}
        a = [x for x in z if x["sym"] in s]
        if len(a) >= MIND_JE_TAG:
            gem_oi[t] = a
            gem_fu[t] = [x for x in fu[t] if x["sym"] in {y["sym"] for y in a}]
    n = sum(len(z) for z in gem_oi.values())
    print("#" * 92)
    print("# H-4c GEGENPRUEFUNG — ist `oi_aenderung` nur Funding mit Umweg?")
    print("#" * 92)
    print("  gemeinsame Basis: %d Anker · %d Symbole · %d Kalendertage"
          % (n, len({x["sym"] for z in gem_oi.values() for x in z}),
             len(gem_oi)))

    # ---- 1: messen die beiden ueberhaupt Verschiedenes? -----------------
    ks = []
    for t, z in gem_oi.items():
        s = fu_je_tag[t]
        a = W.rang([x["kennzahl"] for x in z])
        b = W.rang([s[x["sym"]] for x in z])
        if len(a) > 3:
            ks.append(float(np.corrcoef(a, b)[0, 1]))
    print("  Rangkorrelation je Tag: Median %+.3f   Mittel %+.3f   "
          "|rho| > 0,3 an %.1f %% der Tage"
          % (np.median(ks), np.mean(ks),
             100 * np.mean(np.abs(ks) > 0.3)))
    print()
    print("  ⚠️ Eine niedrige Korrelation allein entlastet NICHT - sie sagt")
    print("     nur, dass die Rangfolgen verschieden sind, nicht dass die")
    print("     WIRKUNG verschieden ist. Deshalb der Schichtentest:")

    W.bericht("A  oi_aenderung auf der GEMEINSAMEN Basis", gem_oi, True, rng,
              mit_positivkontrolle=False)
    W.bericht("B  funding auf derselben Basis", gem_fu, True, rng,
              mit_positivkontrolle=False)

    block = max(90, W.HORIZONT * 3)
    print()
    print("=" * 92)
    print("C  oi_aenderung INNERHALB der Funding-Fuenftel  —  Funding festgehalten")
    print("=" * 92)
    d = geschichtet(gem_oi, fu_je_tag)
    M.urteil_tage("  NETTO (die Wirkung)", d, rng, block)
    M.urteil_tage("  Negativkontrolle", geschichtet(gem_oi, fu_je_tag,
                                                    mische=rng), rng, block)
    print()
    print("=" * 92)
    print("D  UMGEKEHRT: funding INNERHALB der OI-Fuenftel  —  OI festgehalten")
    print("=" * 92)
    d2 = geschichtet(gem_fu, oi_je_tag)
    M.urteil_tage("  NETTO (die Wirkung)", d2, rng, block)
    M.urteil_tage("  Negativkontrolle", geschichtet(gem_fu, oi_je_tag,
                                                    mische=rng), rng, block)
    # ---- E: BEIDE REGELN ZUSAMMEN - die Zahl, an der die Entscheidung haengt
    print()
    print("=" * 92)
    print("E  BEIDE REGELN ZUSAMMEN  —  gesperrt wird, wer in EINEM der beiden")
    print("   obersten Fuenftel liegt")
    print("=" * 92)
    beide, allein_f, anteil_b, anteil_f = {}, {}, [], []
    for tag, z in gem_oi.items():
        s = fu_je_tag[tag]
        y = np.array([x["in_r"] for x in z], float)
        ro = W.rang([x["kennzahl"] for x in z])
        rf = W.rang([s[x["sym"]] for x in z])
        frei_b = (ro < W.GRENZE) & (rf < W.GRENZE)
        frei_f = rf < W.GRENZE
        if frei_b.sum() < 3 or (~frei_b).sum() < 1:
            continue
        beide[tag] = float(np.median(y[frei_b]) - np.median(y))
        allein_f[tag] = float(np.median(y[frei_f]) - np.median(y))
        anteil_b.append(float((~frei_b).mean()))
        anteil_f.append(float((~frei_f).mean()))
    print("  gesperrt: Funding allein %.1f %%   beide zusammen %.1f %%"
          % (100 * st.mean(anteil_f), 100 * st.mean(anteil_b)))
    print("  ⚠️ Waeren die Regeln deckungsgleich, blieben es 20,6 %; waeren sie")
    print("     voellig unabhaengig, waeren es 36,8 %. Der Istwert sagt, wieviel")
    print("     die zweite Regel ueberhaupt NEUES sperrt.")
    M.urteil_tage("  Funding allein", allein_f, rng, block)
    M.urteil_tage("  BEIDE zusammen", beide, rng, block)
    print()
    print("  LESART: traegt C, ist `oi_aenderung` ein EIGENER Beitrag und")
    print("  kein Mitlaeufer. Faellt C und traegt D, war es Funding.")
    print("  Tragen beide, sind es zwei Beitraege - dann verlangt R-R9 eine")
    print("  Neukalibrierung der Schwelle, bevor irgendetwas eingebaut wird.")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--terminmarkt", action="store_true",
                    help="H-4c: die fuenf Terminmarkt-Kandidaten")
    ap.add_argument("--mitlaeufer", action="store_true",
                    help="H-4c Gegenpruefung: oi_aenderung gegen funding")
    ap.add_argument("--horizonte", default="",
                    help="z.B. 1,2,3,5,10,20 - loest den Horizontlauf aus")
    a = ap.parse_args()

    if getattr(a, "mitlaeufer", False):
        mitlaeufer()
        return

    reihen = B.lade()
    rng = np.random.default_rng(20260830)
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    funding = F.lade_funding()

    if getattr(a, "terminmarkt", False):
        # ---- H-4c: DIE TERMINMARKT-GROESSEN (01.09.2026) ---------------
        #
        # ⚠️ VORABFESTLEGUNG. Fuenf Kandidaten, vorab benannt, alle als
        # QUERSCHNITT (N-13b - eine Zeitreihen-Groesse waere bei neu
        # aufgenommenen Werten 250 Tage blind):
        #
        #   oi_aenderung   Veraenderung des Open Interest zum Vortag
        #   oi_je_umsatz   OI-Wert je Tagesumsatz - Hebelaufbau je
        #                  Liquiditaet, das Mass der Praxisliteratur
        #   long_bias      count_long_short_ratio - alle Konten
        #   top_bias       count_toptrader_long_short_ratio - die Grossen
        #   taker_bias     sum_taker_long_short_vol_ratio - das Volumen
        #
        # Suchpreis 2.49: FUENF Zellen, vorab benannt. Ein sechster
        # Kandidat aendert den Preis.
        #
        # ⚠️ Basis: 27 der 32 Terminmarkt-Symbole liegen in `messdaten.db`.
        # Das ist knapp ueber dem Mindestquerschnitt von 15 - die Baender
        # werden entsprechend breit sein, und ein Nullbefund ist hier eher
        # untermaechtig als widerlegend.
        tm = lade_terminmarkt()
        print("#" * 92)
        print("# KONTROLLE ZUERST — Funding bei H20 muss +0,0242 R reproduzieren")
        print("#" * 92)
        W.bericht("KONTROLLE FUNDING H20",
                  baue(reihen, "funding", funding, horizont=20),
                  True, rng, mit_positivkontrolle=False)
        for art, quelle in (("oi_aenderung", tm["oi_aenderung"]),
                            ("oi_je_umsatz", tm["oi_wert"]),
                            ("long_bias", tm["long_bias"]),
                            ("top_bias", tm["top_bias"]),
                            ("taker_bias", tm["taker_bias"])):
            W.bericht("H-4c %s" % art,
                      baue(reihen, art, quelle, horizont=20), True, rng)
        return

    if a.horizonte:
        hs = [int(x) for x in a.horizonte.split(",") if x.strip()]
        # ⚠️ DIE KONTROLLE ZUERST, UND ZWAR BEI H20. Weicht Funding dort von
        # +0,0242 R ab, gilt kein Befund dieses Laufs - egal was die kurzen
        # Horizonte zeigen.
        print("#" * 92)
        print("# KONTROLLE — Funding bei H20 muss +0,0242 R reproduzieren")
        print("#" * 92)
        W.bericht("KONTROLLE FUNDING H20",
                  baue(reihen, "funding", funding, horizont=20),
                  True, rng, mit_positivkontrolle=False)
        horizontlauf(reihen, menge, funding, hs)
        return

    print("#" * 92)
    print("# KONTROLLE ZUERST — Funding muss +0,0242 R reproduzieren")
    print("#" * 92)
    W.bericht("4 FUNDING (Kontrolle)", baue(reihen, "funding", funding),
              True, rng, mit_positivkontrolle=False)

    W.bericht("2 AMIHUD-ILLIQUIDITAET  |Rendite| / Umsatz",
              baue(reihen, "amihud"), True, rng)
    print()
    print("  ⚠️ Gegenrichtung, weil die Literatur eine Praemie fuer ILLIQUIDE")
    print("     Werte behauptet - dann muesste man die LIQUIDEN sperren:")
    W.bericht("2b AMIHUD, Gegenrichtung", baue(reihen, "amihud"), False, rng,
              mit_positivkontrolle=False)

    W.bericht("3 MOMENTUM 12-1", baue(reihen, "momentum"), False, rng)
    W.bericht("1 TURNOVER  Volumen / Umlaufmenge",
              baue(reihen, "turnover", menge), True, rng)

    print()
    print("#" * 92)
    print("# NICHT MESSBAR — und warum")
    print("#" * 92)
    print("  5 OI / Marktkapitalisierung  Binance liefert Open Interest nur")
    print("     30 Tage rueckwirkend (geprueft). Eigene Reihe: 219 Zeilen,")
    print("     36 Symbole, unterbrochen seit 19.07.2026.")
    print("  6 Volatilitaets-Risikopraemie  implizite Volatilitaet nur fuer")
    print("     BTC und ETH (Deribit) - zwei Symbole sind kein Querschnitt.")


if __name__ == "__main__":
    main()
