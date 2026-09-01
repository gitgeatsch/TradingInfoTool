# -*- coding: utf-8 -*-
"""H-1: Trennt eine Groesse STEIL-KURZ von FLACH-LANG? (01.09.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Die Frage - und warum sie NICHT die aus 5.2 ist

`Anforderungen_Umbau_28_08.md` 5.2 formulierte H-1 als: *„Ein gehebelter
Trade mit engem Stop traegt sich rechnerisch nicht, bevor er begonnen hat.
Das waere zu messen."*

⚠️ **Diese Frage ist erstens beantwortet und zweitens die falsche.**

**Beantwortet:** Die Kopplung zwischen Stopabstand und Tragfaehigkeit steht
seit dem 22.08. je Signal in der Mail - *„bei 5 % Stop liegt der Breakeven
schon zum Referenzsatz bei 37,3 %, der Trade traegt mit -4,0 Punkten nicht"*.
Dazu: 06.08. (unter 2 % zerstoererisch), Kapitel 104/105 (Schichtung nach
Stopabstand in fuenf Fuenfteln), S5 (Boden am 18.08.), RM-1b (Untergrenze
5 % am 31.08.).

**Die falsche:** *„Traegt es sich?"* ist eine WIRTSCHAFTLICHKEITSfrage. Nach
der stehenden Vorgabe darf sie die Bewertung nicht entscheiden - *„Bewertung
neutral, Gebuehren nur als Text"*. Sie kann also nie das Kriterium sein, das
Hebel von Spot trennt.

**Nutzerkorrektur 01.09., woertlich:** *„Den Hebel haben wir erst wieder
aufgenommen als Strategie mit einem klaren Ziel, welches unterscheiden soll,
ob zum Zeitpunkt der Bewertung und Signalgenerierung die bessere Wahl ist -
da unterschiedliche Indikatoren, Zeitraeume und zu erwartender Anstieg
relevant sind: **Hebel steil-kurz, Spot flach-lang**."*

## ⚠️⚠️ WARUM DER HORIZONT DER EINZIGE LEGITIME UNTERSCHIED IST

R ist definiert als `Nominal x stop_rel`. Der Ertrag in R ist damit
`Kursbewegung / stop_rel` - **der Hebel kuerzt sich heraus**:

    Einsatz 1.000 EUR, Stop 5 %, Kurs +4 %
    Hebel 1   Nominal 1.000   Risiko   50   Gewinn   40   = 0,800 R
    Hebel 3   Nominal 3.000   Risiko  150   Gewinn  120   = 0,800 R
    Hebel 5   Nominal 5.000   Risiko  250   Gewinn  200   = 0,800 R

**Gebuehrenfrei sind Hebel und Spot dasselbe Geschaeft.** Genau deshalb
liefert `potential.rechne` fuer beide dieselbe Zahl (+0,119100 R) - das ist
kein Fehler in der Bewertung, sondern Arithmetik.

Es bleiben drei moegliche Unterschiede:

    1  Gebuehren/Finanzierung   -> per Regel NICHT in der Bewertung
    2  der HORIZONT             -> genau die Nutzeraussage: kurz gegen lang
    3  Kapitalbindung           -> Portfoliofrage ("System bemisst den Trade,
                                   Nutzer das Portfolio", 15.08.)

**Also ist Weg 2 der einzige, auf dem die Bewertung das Instrument ueberhaupt
waehlen KANN.** Diese Messung prueft, ob er begehbar ist.

## Die Zielgroesse - vorab festgelegt

Je Anker i, in R (Einheit: mittlere Tagesspanne der letzten 14 Tage):

    R_kurz = (c[i+K] - c[i]) / spanne[i]      K = 3   (Hebel-Haltedauer 1-3 Tage)
    R_lang = (c[i+L] - c[i]) / spanne[i]      L = 20  (Spot-Horizont)

⚠️ **KEINE BARRIERE, KEIN ZIEL.** Gemessen wird das POTENTIAL, nicht die
Zielerreichung - *„Ziel vor Stop faellt per Konstruktion auf 1/(1+CRV)"*
(stehende Vorgabe). Kein Stop, kein Ziel, keine Gebuehr.

**Die Entscheidung, um die es geht:**

    Hebel waehlen  ->  man verdient R_kurz
    Spot waehlen   ->  man verdient R_lang

Gebuehrenfrei ist die richtige Wahl also schlicht: **welches R ist groesser?**

## Was gemessen wird - WIRKSAMKEIT, nicht Merkmal

Stehende Vorgabe: *„Wirksamkeit statt Merkmalsmessung - sonst misst du wieder
nur unser System."* Deshalb nicht *„korreliert die Groesse mit der Form?"*,
sondern:

    Basis (Status quo)  immer lang       -> Ertrag = R_lang
    Regel               oberstes Fuenftel der Kennzahl je Kalendertag
                        -> nimm R_kurz, sonst R_lang
    Vergleich 1         gegen die Basis
    Vergleich 2         gegen QUOTENGLEICHEN Zufall (dieselbe Trefferzahl
                        je Tag, zufaellig gezogen) - Methodik 2.93

⚠️ **TAGESKLAMMER.** Raenge werden JE KALENDERTAG gebildet, nie gepoolt.
Gepoolt beantwortet man die Marktphasenfrage: in einem Abwaertsmarkt ist
der kurze Horizont fast immer besser, und das haette nichts mit der Groesse
zu tun. (`Beitrag.klammer="tag"`, Vorgabe seit 31.08.)

## Vorab festgelegt - was als Befund gilt

    TRAEGT     Regelertrag > Basisertrag
               UND ausserhalb des Placebo-Bandes (zirkulaere Versaetze)
               UND beide Historienhaelften gleiches Vorzeichen
               UND die Positivkontrolle schlaegt an - AN BEIDEN HORIZONTEN
    NULL       sonst

⚠️ **DIE POSITIVKONTROLLE GEHOERT AN JEDEN HORIZONT.** Am 01.09. gemessen:
bei H20 versagte sie in einer frueheren Messung, womit die dortigen
Nullbefunde untermaechtig und nicht widerlegend waren. Ohne bestandene
Positivkontrolle ist ein Nullbefund hier **kein Ergebnis**.

## Die Kandidaten - vorab benannt, keine freie Suche

    funding        tragender Beitrag (H20), Terminmarkt
    turnover       tragender Beitrag (H20)
    schnitt50      31.08. als Beitrag gefallen - hier andere FRAGE
    vola           ATR relativ zum eigenen Median: die naheliegendste
                   Vermutung fuer "steil"
    momentum_kurz  Rendite der letzten 3 Tage - laeuft die Bewegung schon?
    spanne_aus     Abstand zum 20-Tage-Hoch
    zufall         ⚠️ KONTROLLGROESSE, muss NICHT tragen

**Sechs echte Kandidaten, eine Zelle je Kandidat, vorab benannt.**
Suchpreis nach 2.49: 6 Zellen, nicht 300. Wer hier nachtraeglich einen
siebten Kandidaten dazunimmt, muss den Preis neu rechnen.

## ⚠️ Was diese Messung NICHT beantwortet

* **Ob sich der Hebel lohnt.** Das ist die Gebuehrenfrage und gehoert in die
  Mail. Selbst wenn eine Groesse traegt, kann die Finanzierung den Vorsprung
  auffressen - das ist danach zu rechnen, nicht davor.
* **Terminmarktgroessen.** OI und OI-Divergenz liegen als Historie auf dem
  NOTEBOOK (lokal nur 227 Zeilen). Diese Messung laeuft auf Kursreihen -
  wenn hier schon etwas traegt, ist der Weg begehbar; wenn nicht, ist der
  Terminmarkt der naechste Versuch, nicht der Beweis des Gegenteils.

## Aufwand

    Datenquelle   data/messdaten.db (523 Reihen), rein lokal
    API           KEINE - kein CoinGecko-, kein LLM-Kontingent
    Dauer         geschaetzt 2-5 Minuten

    python messe_form_kurz_gegen_lang.py
"""
import sys
from collections import Counter

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_eigenschaft_beitrag as B                          # noqa: E402
import messe_bewertungskennzahl as M                           # noqa: E402

KURZ = 3
LANG = 20
RUECKBLICK = 60
MIN_JE_TAG = 15
# Tagessprung, ab dem ein Anker als Datenbruch gilt (2.89, wie messe_zielregel)
BRUCH = 5.0
SAAT = 20260901

# ⚠️ Vorab benannt. Jeder zusaetzliche Kandidat aendert den Suchpreis (2.49).
#
# H-4b ergaenzt drei FUNDING-EXTREMA (01.09.2026). Nutzervorgabe: *„Bevor
# wir wieder nur das eigene System messen, sollte eigentlich schon bekannt
# sein, was wir suchen."* Was die Literatur zum Krypto-Terminmarkt als
# kurzfristig aussagekraeftig fuehrt, ist nicht das NIVEAU des Funding,
# sondern sein EXTREM: eine ueberfuellte Positionierung, die sich
# aufloesen muss. Genau das misst `funding` heute NICHT - dort steht der
# Querschnittsrang gegen die anderen Werte desselben Tages.
KANDIDATEN = ("vola", "momentum_kurz", "spanne_aus", "schnitt50",
              "funding", "turnover",
              # H-4b: das Extrem gegen die EIGENE Geschichte
              "funding_extrem", "funding_perzentil", "funding_persistenz",
              # ---- S-1: die etablierten TREND/RANGE-Masse (01.09.2026) ----
              # ⚠️ Nutzervorgabe: *„Wir wollen ja nichts erfinden, sondern
              # auf bestehende Standards aufbauen."* Alle vier stammen aus
              # der Standardliteratur, keines ist eine eigene Konstruktion:
              #
              #   er_rueck    Effizienz-Ratio rueckwaerts (Kaufman 1995) -
              #               DIE Persistenzfrage: sagt der Trendzustand
              #               der letzten 20 Tage den der naechsten 20?
              #   adx         Average Directional Index (Wilder 1978) -
              #               das kanonische "gibt es ueberhaupt einen
              #               Trend"; unter 20-25 gilt als trendlos
              #   choppiness  Choppiness Index - Weg gegen Spanne, in dB
              #   varianzverh Varianzverhaeltnis (Lo/MacKinlay 1988) - die
              #               akademisch strenge Form: waechst die Varianz
              #               linear mit der Zeit (Zufallspfad), langsamer
              #               (rueckkehrend = seitwaerts) oder schneller
              #               (trendend)?
              "er_rueck", "adx", "choppiness", "varianzverh",
              "zufall")

# ⚠️ DIE ZIELGROESSE IST WAEHLBAR (H-4a, 01.09.2026).
#
#   signiert       R_kurz - R_lang       (H-1, gemessen: kein Befund)
#   frontloading   |R_kurz| / (|R_kurz| + |R_rest|)
#
# Die Umformulierung kommt aus der Praxis, nicht aus einer Vermutung:
# **alles, was der Terminmarkt zuverlaessig vorhersagt, ist AUSMASS und
# TEMPO - nicht die Richtung.** Funding-Extrema, OI-Aufbau und
# Volatilitaets-Clustering sagen etwas darueber, WIE GROSS und WIE SCHNELL
# eine Bewegung wird; keines davon sagt, WOHIN.
#
# ⚠️ H-1 hat beides vermischt. `R_kurz - R_lang` ist vorzeichenbehaftet und
# beantwortet damit die Richtungsfrage mit - die niemand beantworten kann.
# Die literaturkonforme Frage lautet: **welcher Anteil der Bewegung faellt
# in die ersten Tage?** Die Richtung liefert weiterhin die bestehende
# Bewertung; der Hebel-Schalter liefert nur das Tempo.
#
# Die Form ist bewusst ein ANTEIL, kein Quotient `|R_kurz|/|R_lang|`:
# der waere unbrauchbar, sobald `R_lang` nahe null liegt. Der Anteil ist
# auf [0,1] beschraenkt und hat nur dann keinen Nenner, wenn sich
# ueberhaupt nichts bewegt hat.
#   seitwaerts     -ER_vor  =  - |Netto| / Summe(|Tagesbewegungen|)
#
# ⚠️ DAS SEITWAERTS-MASS IST NICHT ERFUNDEN. Es ist die
# EFFIZIENZ-RATIO nach Kaufman (Adaptive Moving Average, 1995) - das
# etablierteste parameterarme Mass fuer "Trend oder Seitwaerts":
#
#     ER = |Kurs(t+N) - Kurs(t)| / Summe der taeglichen |Aenderungen|
#
# Sie liegt zwischen 0 und 1. **1 heisst: der ganze zurueckgelegte Weg
# ging in EINE Richtung** (reiner Trend). **0 heisst: der Kurs steht am
# Ende dort, wo er begann** - der ganze Weg war Hin und Her. Genau das
# ist Seitwaerts.
#
# ⚠️ Der Massstab dafuer ist NICHT null, sondern der Zufallspfad. Bei
# einem reinen Zufallspfad ist E|Netto| ~ sigma*sqrt(N) und die Summe der
# Betraege ~ N*sigma*sqrt(2/pi), also ER ~ 1/(0,798*sqrt(N)) = 0,280 bei
# N=20. Alles darunter ist SEITWAERTSER als der Zufall.
#
# Das Vorzeichen ist umgedreht (`-ER`), damit "oberstes Fuenftel" wie bei
# den anderen Zielen "am meisten davon" heisst - hier also am meisten
# Seitwaerts.
ZIEL = "signiert"


def lade_zusatz():
    """Funding und Umlaufmenge - dieselben Quellen wie die Produktion."""
    import sqlite3
    aus = {}
    for name, db, tab, spalte in (
            ("funding", "data/funding_historie.db", "funding", "wert"),
            ("menge", "data/onchain_historie.db", "splycur", "wert")):
        je = {}
        try:
            c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
            for sym, tag, w in c.execute(
                    "SELECT symbol, datum, %s FROM %s" % (spalte, tab)):
                if w is not None:
                    je.setdefault(str(sym).upper(), {})[str(tag)[:10]] = float(w)
            c.close()
        except Exception as exc:                             # noqa: BLE001
            print("  ⚠️ %s nicht ladbar (%s)" % (name, type(exc).__name__))
        aus[name] = je
    return aus


def baue(reihen, zusatz):
    """Je Kalendertag die Anker mit ALLEN Kandidaten und BEIDEN Horizonten.

    ⚠️ EIN Durchlauf fuer alle Kandidaten, nicht einer je Kandidat. Sonst
    stuenden verschiedene Kandidaten auf verschieden vielen Ankern, und ihre
    Regelertraege waeren nicht vergleichbar.
    """
    rng = np.random.default_rng(SAAT)
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh], float)
        h = np.array([z[2] for z in roh], float)
        t_ = np.array([z[3] for z in roh], float)
        v = np.array([z[4] for z in roh], float)
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        f_je = (zusatz.get("funding") or {}).get(sym.upper()) or {}
        m_je = (zusatz.get("menge") or {}).get(sym.upper()) or {}
        # ⚠️⚠️ DATENBRUECHE ENTFERNEN - Punkt 4 der Checkliste 2.91, und ich
        # habe ihn im ersten Anlauf uebersprungen (01.09.2026).
        #
        # In `messdaten.db` stehen Token-Umstellungen als Kurssprung: LUNA
        # Faktor 177.400, COCOS 1.295, DREP 108 - 14 von 523 Reihen. Sie
        # verfaelschen JEDE Mittelwertmessung; 0,1 % der Anker trugen dort
        # einmal 187 % eines Mittelwerts.
        #
        # Die Signatur war im ersten Lauf deutlich sichtbar und ich habe sie
        # zunaechst nicht als solche gelesen: `mean(d) = -1,02` gegen
        # `median(d) = +0,16`. Ein Mittelwert, der weit auf der anderen
        # Seite des Medians liegt, ist fast immer ein Datenbruch.
        #
        # CHIRURGISCH, nicht reihenweise (Vorlage `messe_zielregel`): nur
        # Anker fallen weg, deren VORWAERTSFENSTER einen Sprung enthaelt -
        # die uebrige Historie derselben Reihe bleibt nutzbar.
        verh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (verh > BRUCH) | (verh < 1.0 / BRUCH)
        # ---- S-1: die vier Trend/Range-Masse, alle NACHLAUFEND ----------
        _d = np.abs(np.diff(c, prepend=c[0]))
        _weg20 = np.convolve(_d, np.ones(20), "full")[:len(c)]
        _rend = np.diff(np.log(np.maximum(c, 1e-12)), prepend=0.0)
        # ADX nach Wilder: gerichtete Bewegung gegen die wahre Spanne
        _uh = np.diff(h, prepend=h[0])
        _dt = -np.diff(t_, prepend=t_[0])
        _pdm = np.where((_uh > _dt) & (_uh > 0), _uh, 0.0)
        _ndm = np.where((_dt > _uh) & (_dt > 0), _dt, 0.0)
        _tr = np.maximum(h - t_, np.maximum(np.abs(h - np.roll(c, 1)),
                                            np.abs(t_ - np.roll(c, 1))))
        _tr[0] = h[0] - t_[0]
        _k14 = np.ones(14)
        _str = np.convolve(_tr, _k14, "full")[:len(c)]
        _sp = np.convolve(_pdm, _k14, "full")[:len(c)]
        _sn = np.convolve(_ndm, _k14, "full")[:len(c)]
        _pdi = 100 * _sp / np.maximum(_str, 1e-12)
        _ndi = 100 * _sn / np.maximum(_str, 1e-12)
        _dx = 100 * np.abs(_pdi - _ndi) / np.maximum(_pdi + _ndi, 1e-12)
        _adx = np.convolve(_dx, np.ones(14) / 14, "full")[:len(c)]
        # ⚠️⚠️ DER NENNER DARF NICHT DER KANDIDAT SEIN (01.09.2026).
        #
        # Die erste Fassung normierte mit `breite[i]` - der Tagesspanne AM
        # ANKER. Damit stand `vola` (= breite[i]/Median) im NENNER der
        # Zielgroesse, und die Mitlaeuferpruefung zeigte prompt, was das
        # anrichtet:
        #
        #     vola-Fuenftel   mean(d)     median|d|    Streuung von d
        #        0            -2,3850       1,8168        220,50
        #        4            +0,0395       1,4195          3,05
        #
        # |d| faellt monoton, weil ein grosser Nenner die Differenz gegen
        # null staucht - und da mean(d) stark NEGATIV ist, sieht Stauchung
        # wie Gewinn aus. Der Befund "vola traegt (+0,0960 R)" war damit
        # MECHANISCH, keine Trennschaerfe.
        #
        # ⚠️ Und der untere Rand war zusaetzlich giftig: bei winziger
        # Tagesspanne explodiert die R-Rechnung (Streuung 220 gegen 3).
        #
        # JETZT: ein NACHLAUFENDER Median ueber 250 Tage als Nenner - je
        # Asset gleitend, aber unabhaengig davon, was am Anker passiert.
        # Nachlaufend, nicht ueber die ganze Reihe: ein Median ueber alles
        # kennt die Zukunft.
        for i in range(max(RUECKBLICK + 40, 260), len(c) - LANG):
            fenster = breite[i - 250:i]
            fenster = fenster[np.isfinite(fenster) & (fenster > 0)]
            if len(fenster) < 100:
                continue
            nenner = float(np.median(fenster))
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or nenner <= 0:
                continue
            # das Vorwaertsfenster reicht bis LANG - genau so weit muss es
            # bruchfrei sein, denn `r_lang` liest bis dorthin.
            if bruch[i:i + LANG].any():
                continue
            e = {"sym": sym,
                 "r_kurz": float((c[i + KURZ] - c[i]) / nenner),
                 "r_lang": float((c[i + LANG] - c[i]) / nenner)}
            # ⚠️ DER REST DES WEGES, nicht der Gesamtweg: `r_rest` ist die
            # Bewegung NACH dem kurzen Fenster. Sonst stuende `r_kurz` in
            # Zaehler UND Nenner, und der Anteil waere per Konstruktion
            # nach oben verzerrt - dieselbe Falle wie der Nenner oben.
            e["r_rest"] = float((c[i + LANG] - c[i + KURZ]) / nenner)
            # ---- SEITWAERTS: die Effizienz-Ratio VORWAERTS ----------
            # ⚠️ Sie ist die ZIELGROESSE, nicht der Kandidat: sie misst,
            # was TATSAECHLICH passiert ist. Vorhergesagt werden soll sie
            # von den Kandidaten weiter unten, die nur Vergangenes sehen.
            _weg_ges = float(np.abs(np.diff(c[i:i + LANG + 1])).sum())
            if _weg_ges > 1e-12:
                _er = abs(float(c[i + LANG] - c[i])) / _weg_ges
                # negativ, damit "oberstes Fuenftel" = "am seitwaertsesten"
                e["seitwaerts"] = float(-_er)
                e["er_vor"] = float(_er)
            _weg = abs(e["r_kurz"]) + abs(e["r_rest"])
            e["frontloading"] = float(abs(e["r_kurz"]) / _weg) if _weg > 1e-9 else None
            # ---- die Kandidaten -------------------------------------
            # ⚠️ `vola` ist jetzt echt unabhaengig vom Nenner: sie
            # vergleicht die HEUTIGE Spanne mit demselben nachlaufenden
            # Median, der den Nenner bildet - der Quotient steht also
            # NEBEN der Zielgroesse, nicht in ihr.
            e["vola"] = float(r / nenner)
            # ---- S-1: die vier etablierten Masse, alle nur rueckwaerts --
            _w = float(_weg20[i])
            if _w > 1e-12:
                e["er_rueck"] = float(-abs(c[i] - c[i - 20]) / _w)
                # Choppiness: hoher Wert = viel Weg bei wenig Spanne
                _sp20 = float(np.max(h[i - 20:i]) - np.min(t_[i - 20:i]))
                if _sp20 > 1e-12:
                    e["choppiness"] = float(np.log10(_w / _sp20)
                                            / np.log10(20.0))
            # ADX: NIEDRIG heisst trendlos - Vorzeichen umgedreht, damit
            # "oberstes Fuenftel" auch hier "am seitwaertsesten" heisst.
            if np.isfinite(_adx[i]):
                e["adx"] = float(-_adx[i])
            # Varianzverhaeltnis: <1 rueckkehrend/seitwaerts, >1 trendend.
            _r1 = _rend[i - 100:i]
            if len(_r1) == 100 and _r1.std() > 1e-12:
                _r5 = _r1.reshape(20, 5).sum(axis=1)
                e["varianzverh"] = float(-(_r5.var() / (5.0 * _r1.var())))
            if c[i - KURZ] > 0:
                e["momentum_kurz"] = float(c[i] / c[i - KURZ] - 1.0)
            hoch = np.max(c[i - 20:i + 1])
            if hoch > 0:
                e["spanne_aus"] = float(c[i] / hoch - 1.0)
            m50 = c[i - 50:i].mean() if i >= 50 else np.nan
            if np.isfinite(m50) and m50 > 0:
                e["schnitt50"] = float(c[i] / m50 - 1.0)
            fw = f_je.get(tage[i])
            if fw is not None:
                e["funding"] = float(fw)
                # ---- H-4b: das Extrem gegen die EIGENE Geschichte ----
                # ⚠️ NACHLAUFEND, nie ueber die ganze Reihe. Ein Perzentil
                # ueber alles kennt die Zukunft.
                hist = [f_je.get(d) for d in tage[max(0, i - 250):i]]
                hist = [x for x in hist if x is not None]
                if len(hist) >= 100:
                    ha = np.array(hist, float)
                    med = float(np.median(ha))
                    mad = float(np.median(np.abs(ha - med)))
                    if mad > 1e-12:
                        # ABSTAND VOM EIGENEN NORMALZUSTAND, vorzeichenlos:
                        # ueberfuellt ist ueberfuellt, in beide Richtungen.
                        e["funding_extrem"] = float(abs(fw - med) / mad)
                    e["funding_perzentil"] = float((ha < fw).mean())
                # WIE LANGE steht das Vorzeichen schon? Eine Positionierung,
                # die seit Wochen einseitig ist, ist der Lehrbuchfall.
                lauf = 0
                for d in reversed(tage[max(0, i - 60):i + 1]):
                    x = f_je.get(d)
                    if x is None or (x > 0) != (fw > 0):
                        break
                    lauf += 1
                e["funding_persistenz"] = float(lauf)
            mw = m_je.get(tage[i])
            if mw and mw > 0:
                e["turnover"] = float(v[i] / mw)
            e["zufall"] = float(rng.random())
            je_tag.setdefault(tage[i], []).append(e)
    return {t: z for t, z in je_tag.items() if len(z) >= MIN_JE_TAG}


def _ziel(x):
    """Die Zielgroesse eines Ankers - je nach `ZIEL`.

    ⚠️ EINE Stelle. Waere sie an zwei Stellen gerechnet, liefen die
    Kandidatenmessung und die Positivkontrolle auf verschiedenen Groessen -
    und die Kontrolle pruefte etwas anderes als das Ergebnis.
    """
    if ZIEL == "frontloading":
        return x.get("frontloading")
    if ZIEL == "seitwaerts":
        return x.get("seitwaerts")
    return x["r_kurz"] - x["r_lang"]


ANTEIL = 0.20     # oberstes Fuenftel - dieselbe Quote wie `messe_regel_wirksamkeit`


def wahl_je_tag(je_tag, kandidat, mische=None, pflanze=None, richtung="oben"):
    """⚠️ EINE WAHL-REGEL, KEINE SPERR-REGEL - und das ist der Unterschied.

    `messe_regel_wirksamkeit.bericht` misst *„kein Einstieg im obersten
    Fuenftel"*: eine Groesse wird BENUTZT, um etwas WEGZULASSEN, und die
    Wirkung ist, was der Rest mehr bringt.

    Hier ist die Frage eine andere: fuer das oberste Fuenftel soll der KURZE
    Horizont GEWAEHLT werden, fuer den Rest bleibt es beim langen. Die
    Wirkung ist der Mehrertrag gegenueber *„immer lang"*:

        Wirkung(Tag) = Mittel ueber die Gewaehlten von (R_kurz - R_lang)
                       x Anteil der Gewaehlten

    ⚠️ **Der Anteil gehoert in die Zahl** (stehende Vorgabe *„Wirksamkeit
    statt Merkmalsmessung - die Haeufigkeit gehoert immer dazu"*). Eine
    Regel, die auf 2 % der Anker +1,0 R holt, ist nicht so gut wie eine, die
    auf 20 % der Anker +0,2 R holt - dieselbe Merkmalszahl, andere Wirkung.

    `mische` = Negativkontrolle (Kennzahl je Tag gemischt, Ertraege bleiben).
    `pflanze` = Positivkontrolle (den Gewaehlten wird ein echter Vorteil
    zugelegt); beides mit derselben Mechanik wie im Schwestermodul.
    """
    aus = {}
    for tag, z in je_tag.items():
        zeilen = [x for x in z if kandidat in x and x.get(kandidat) is not None
                  and _ziel(x) is not None]
        if len(zeilen) < MIN_JE_TAG:
            continue
        kz = np.array([float(x[kandidat]) for x in zeilen])
        d = np.array([_ziel(x) for x in zeilen])
        if mische is not None:
            kz = kz[mische.permutation(len(kz))]
        k = max(1, int(round(len(zeilen) * ANTEIL)))
        # oberstes Fuenftel der Kennzahl
        # ⚠️ BEIDE RICHTUNGEN (Audit 4, 01.09.2026). Bis hierher wurde
        # IMMER das oberste Fuenftel gewaehlt. Ein Kandidat, dessen Aussage
        # am unteren Rand sitzt - ein Bollinger-Squeeze etwa ist NIEDRIGE
        # Volatilitaet -, war damit strukturell unsichtbar. Gefunden hat es
        # nicht die Suite, sondern die Faktorliste des Nutzers.
        gewaehlt = (np.argsort(-kz)[:k] if richtung == "oben"
                    else np.argsort(kz)[:k])
        vorteil = d[gewaehlt]
        if pflanze:
            vorteil = vorteil + float(pflanze)
        # ⚠️⚠️ GEGEN DEN QUOTENGLEICHEN ZUFALL, NICHT GEGEN NULL (01.09.2026).
        #
        # Die erste Fassung rechnete `vorteil.mean() * anteil` und liess das
        # Vertrauensband gegen NULL pruefen. Das war falsch, und die eigene
        # Negativkontrolle hat es gezeigt: sie lag systematisch bei -0,10
        # bis -0,14 R statt bei null.
        #
        # Der Grund ist arithmetisch. `mean(R_kurz - R_lang)` ist ueber alle
        # Anker **-0,58 R** - der lange Horizont verdient im Schnitt mehr.
        # Eine BELIEBIGE 20-%-Auswahl bringt damit 0,2 x (-0,58) = -0,116 R.
        # Gegen null gemessen sieht deshalb JEDE Regel schlecht aus, und die
        # schlechteste sieht am schlechtesten aus - gemessen wurde die
        # Marktphase, nicht die Trennschaerfe.
        #
        # Methodik 2.93 sagt genau das: *„Jede Schwelle, jeder Filter, jede
        # Auswahl wird gegen eine QUOTENGLEICHE Zufallsauswahl gemessen -
        # nie gegen die Gesamtmenge."* Ich hatte es in die Vorabfestlegung
        # geschrieben und dann nicht gerechnet.
        #
        # ⚠️ Der Erwartungswert einer zufaelligen k-Teilmenge IST der
        # Mittelwert aller - exakt, ohne Ziehen. Deshalb genuegt die
        # Differenz; ein Ziehungsverfahren waere nur zusaetzliches Rauschen.
        aus[tag] = float((vorteil.mean() - d.mean()) * (k / len(zeilen)))
    return aus


def bericht_wahl(name, je_tag, kandidat, rng, mit_positivkontrolle=True,
                 richtung="oben"):
    """Dieselbe Berichtsform wie das Schwestermodul - EIN Statistikkern."""
    zeilen = [x for z in je_tag.values() for x in z if kandidat in x]
    syms = len({x["sym"] for x in zeilen})
    print()
    print("=" * 92)
    print("%s  —  REGEL: %s %d %% der Kennzahl gewaehlt  [Ziel %s]"
          % (name, "oberstes" if richtung == "oben" else "unterstes",
             round(ANTEIL * 100), ZIEL))
    print("=" * 92)
    d = wahl_je_tag(je_tag, kandidat, richtung=richtung)
    if len(d) < 60:
        print("  zu wenige Tage (%d) - uebersprungen" % len(d))
        return None
    print("  %d Anker · %d Symbole · %d Kalendertage" % (len(zeilen), syms, len(d)))
    block = max(90, LANG * 3)
    echt = M.urteil_tage("  NETTO (die Wirkung)", d, rng, block)
    M.urteil_tage("  Negativkontrolle",
                  wahl_je_tag(je_tag, kandidat, mische=rng, richtung=richtung),
                  rng, block)
    tage = sorted(d)
    mitte = tage[len(tage) // 2]
    h1 = M.urteil_tage("    erste Haelfte",
                       {t: v for t, v in d.items() if t < mitte}, rng, block)
    h2 = M.urteil_tage("    zweite Haelfte",
                       {t: v for t, v in d.items() if t >= mitte}, rng, block)
    if mit_positivkontrolle:
        for s in (0.02, 0.05):
            M.urteil_tage("  Positivkontrolle %+.2f R" % s,
                          wahl_je_tag(je_tag, kandidat, pflanze=s,
                                      richtung=richtung), rng, block)
    # ⚠️ BEIDE HAELFTEN GLEICHES VORZEICHEN ist Teil der Vorabfestlegung.
    haelften_einig = (h1 and h2
                      and (h1["mittel"] > 0) == (h2["mittel"] > 0))
    return {"echt": echt, "haelften_einig": bool(haelften_einig)}


def grundlage(je_tag):
    """Wie oft ist der kurze Horizont ueberhaupt besser? Die Basisrate."""
    alle = [x for z in je_tag.values() for x in z]
    if ZIEL == "frontloading":
        fl = np.array([x["frontloading"] for x in alle
                       if x.get("frontloading") is not None])
        print()
        print("=" * 96)
        print("DIE GRUNDLAGE — wieviel der Bewegung faellt in die ersten %d Tage?"
              % KURZ)
        print("=" * 96)
        print()
        print("  %d Anker mit Frontloading, %d Kalendertage" % (len(fl), len(je_tag)))
        print("  Anteil |R_kurz| / (|R_kurz| + |R_rest|):")
        print("     Median %.3f   Mittel %.3f" % (np.median(fl), fl.mean()))
        # ⚠️ DIE ERWARTUNG BEI EINEM ZUFALLSPFAD, damit die Zahl einen
        # Massstab hat: |Weg| waechst mit der Wurzel der Zeit, also
        # sqrt(3)/(sqrt(3)+sqrt(17)) = 0,296.
        erw = np.sqrt(KURZ) / (np.sqrt(KURZ) + np.sqrt(LANG - KURZ))
        print("     Erwartung auf einem reinen Zufallspfad: %.3f" % erw)
        print("     Anteil der Anker ueber dieser Erwartung: %.1f %%"
              % (100 * (fl > erw).mean()))
        print()
        print("  ⚠️ Ein Wert ueber der Erwartung heisst: die Bewegung war")
        print("     FRONTLASTIG - genau die Lage, in der ein kurzer Horizont")
        print("     (und damit der Hebel) ueberhaupt Sinn ergibt.")
        return float((fl > erw).mean())
    besser = sum(1 for x in alle if x["r_kurz"] > x["r_lang"])
    d = np.array([x["r_kurz"] - x["r_lang"] for x in alle])
    print()
    print("=" * 96)
    print("DIE GRUNDLAGE — wie oft ist STEIL-KURZ ueberhaupt die bessere Wahl?")
    print("=" * 96)
    print()
    print("  %d Anker, %d Kalendertage" % (len(alle), len(je_tag)))
    print("  kurzer Horizont (H%d) besser als langer (H%d): %d von %d = %.1f %%"
          % (KURZ, LANG, besser, len(alle), 100 * besser / max(len(alle), 1)))
    print("  Differenz R_kurz - R_lang:  Median %+.4f R   Mittel %+.4f R"
          % (np.median(d), d.mean()))
    print()
    print("  ⚠️ DAS IST DIE BASISRATE, gegen die jede Regel antreten muss.")
    print("     Waere sie 50 %%, waere die Wahl eine Muenze und jede Trennung")
    print("     wertvoll. Liegt sie weit darunter, ist SPOT die Vorgabe und")
    print("     der Hebel braucht einen Grund, nicht umgekehrt.")

    # ⚠️ JE KALENDERTAG, nicht gepoolt - sonst antwortet die Marktphase.
    je = []
    for tag, z in sorted(je_tag.items()):
        je.append(sum(1 for x in z if x["r_kurz"] > x["r_lang"]) / len(z))
    je = np.array(je)
    print()
    print("  Je Kalendertag: Median %.1f %%, Spanne %.1f %% .. %.1f %%"
          % (100 * np.median(je), 100 * je.min(), 100 * je.max()))
    print("  Tage, an denen KURZ ueberwiegt: %d von %d (%.1f %%)"
          % ((je > 0.5).sum(), len(je), 100 * (je > 0.5).mean()))
    print()
    print("  ⚠️ Eine breite Streuung JE TAG heisst: die Wahl haengt am TAG,")
    print("     nicht am Wert - und dann waere ein Lagemerkmal der Kandidat,")
    print("     kein Assetmerkmal. Eine enge Streuung heisst das Gegenteil.")
    return besser / max(len(alle), 1)


def positivkontrolle(je_tag, rng):
    """⚠️ PFLICHT - und hier an BEIDEN Horizonten.

    Konstruiert eine Groesse, die die Antwort KENNT (mit Rauschen). Schlaegt
    sie nicht an, ist das Verfahren an diesem Horizont blind, und jeder
    Nullbefund daneben ist untermaechtig statt widerlegend.
    """
    print()
    print("=" * 96)
    print("POSITIVKONTROLLE — kann das Verfahren hier ueberhaupt etwas finden?")
    print("=" * 96)
    # ⚠️ ALS ZUSAETZLICHER KANDIDAT, nicht als eigener Pfad. Die Kunstgroesse
    # laeuft durch DIESELBE Funktion wie die echten Kandidaten - sonst
    # pruefte sie Code, den die echten nie durchlaufen.
    for z in je_tag.values():
        for x in z:
            wahr = _ziel(x)
            if wahr is None:
                continue
            # 50 % Signal, 50 % Rauschen: stark genug zum Finden, nicht so
            # stark, dass auch eine kaputte Rechnung es faende.
            x["_kunst"] = wahr + rng.normal(0.0, max(abs(wahr), 1e-9))
    return bericht_wahl("KUNSTGROESSE (kennt die Antwort)", je_tag,
                        "_kunst", rng, mit_positivkontrolle=False)


def selbsttest():
    """⚠️ DAS PRUEFWERKZEUG GEGEN KUNSTDATEN - VOR dem teuren Lauf.

    Stehende Vorgabe: *„Die KONTROLLE ist der erste Verdaechtige - vier
    Messfehler an einem Tag, alle in der Messanlage. Pruefwerkzeug gegen
    Kunstdaten VOR dem teuren Lauf."*

    Gebaut werden Tage mit drei Groessen, deren Antwort ich KENNE:

        `gut`     korreliert mit (R_kurz - R_lang)  -> MUSS gefunden werden
        `blind`   reines Rauschen                   -> darf NICHT tragen
        `invers`  negativ korreliert                -> muss UMGEKEHRT sein

    Faellt eine der drei Erwartungen, misst das Werkzeug etwas anderes als
    es behauptet, und der echte Lauf waere wertlos.
    """
    rng = np.random.default_rng(4711)
    je_tag = {}
    for tg in range(2000):
        tag = "T%05d" % tg
        z = []
        for s in range(30):
            d = float(rng.normal(0.0, 1.0))      # der wahre Vorteil in R
            z.append({"sym": "S%02d" % s,
                      "r_kurz": d, "r_lang": 0.0, "r_rest": -d,
                      "frontloading": float(abs(d) / (abs(d) + 1.0)),
                      "seitwaerts": d})
        je_tag[tag] = z

    # ⚠️⚠️ DIE KUNSTGROESSEN WERDEN AUS DER TATSAECHLICHEN ZIELGROESSE
    # GEBAUT (01.09.2026) - nicht aus `d`.
    #
    # Der erste Anlauf setzte `invers = -d + Rauschen`. Bei ZIEL=signiert
    # ist das richtig. Bei ZIEL=frontloading ist es FALSCH: dort waechst
    # die Zielgroesse mit |d|, und eine Groesse, die mit -d korreliert,
    # waehlt genauso grosse |d| aus wie eine, die mit +d korreliert -
    # beide erscheinen als TRAEGT. Der Selbsttest meldete prompt
    # "invers erwartet UMGEKEHRT, bekommen TRAEGT".
    #
    # Das war kein Fehler des Verfahrens, sondern meiner Kunstwelt. Jetzt
    # sind die drei Groessen per Konstruktion richtig, egal welches Ziel
    # gewaehlt ist - sie haengen an `_ziel(x)` selbst.
    for z in je_tag.values():
        for x in z:
            y = _ziel(x)
            rausch = max(abs(y), 1e-9) * 0.8
            x["gut"] = y + rng.normal(0.0, rausch)
            x["invers"] = -y + rng.normal(0.0, rausch)
            x["blind"] = float(rng.normal())

    print("=" * 96)
    print("SELBSTTEST DES MESSWERKZEUGS — Kunstdaten mit bekannter Antwort")
    print("=" * 96)

    def urteil(k):
        """⚠️ DAS ZUSAMMENGESETZTE Urteil, nicht das rohe Band.

        Der erste Anlauf pruefte `echt["urteil"]` allein - und `blind`
        (reines Rauschen) feuerte prompt mit [-0,0162 .. -0,0016]. Das ist
        KEIN Fehler: ein 95-%-Band irrt sich per Konstruktion in einem von
        zwanzig Faellen. Genau deshalb steht in der Vorabfestlegung
        "UND beide Historienhaelften gleiches Vorzeichen" - und genau das
        muss der Selbsttest pruefen, weil es das ist, was das Skript
        spaeter meldet.
        """
        e = bericht_wahl(k, je_tag, k, rng, mit_positivkontrolle=False)
        if not e or not e.get("echt"):
            return "—", None
        s = e["echt"]
        if s["traegt"] and e["haelften_einig"]:
            return "TRAEGT", s
        if s["oben"] < 0 and e["haelften_einig"]:
            return "UMGEKEHRT", s
        return "null", s

    erwartet = {"gut": "TRAEGT", "blind": "null", "invers": "UMGEKEHRT"}
    ok = True
    for k, soll in erwartet.items():
        ist, s = urteil(k)
        gut = (ist == soll)
        ok = ok and gut
        print("  -> %-8s erwartet %-10s bekommen %-10s %s"
              % (k, soll, ist, "✔" if gut else "⚠️ FEHLSCHLAG"))

    # ⚠️ UND DIE FEHLALARMQUOTE, gemessen statt angenommen. Sie ist die
    # Zahl, die beim echten Lauf ueber sieben Kandidaten zaehlt: bei einem
    # 95-%-Band ist etwa einer von zwanzig ein Zufallstreffer.
    print()
    print("  Fehlalarmquote des zusammengesetzten Urteils (20 reine Rauschgroessen):")
    treffer = 0
    for i in range(20):
        for z in je_tag.values():
            for x in z:
                x["_rausch"] = float(rng.normal())
        e = bericht_wahl("  rausch %02d" % i, je_tag, "_rausch", rng,
                         mit_positivkontrolle=False)
        s = (e or {}).get("echt")
        if s and e["haelften_einig"] and (s["traegt"] or s["oben"] < 0):
            treffer += 1
    print()
    print("  -> %d von 20 reinen Rauschgroessen wurden faelschlich als Befund"
          % treffer)
    print("     gemeldet. Erwartet sind 0-2; mehr hiesse, das Verfahren")
    print("     erzeugt Befunde aus dem Nichts.")
    if treffer > 2:
        ok = False
        print("  ⚠️⚠️ ZU VIELE FEHLALARME.")
    print()
    if ok:
        print("  ✔ Das Werkzeug findet, was da ist, und nichts, was nicht da ist.")
    else:
        print("  ⚠️⚠️ SELBSTTEST GESCHEITERT - der echte Lauf waere wertlos.")
    return ok


def main():
    global ZIEL
    for a in sys.argv[1:]:
        if a.startswith("--ziel="):
            ZIEL = a.split("=", 1)[1]
    if ZIEL not in ("signiert", "frontloading", "seitwaerts"):
        raise SystemExit("--ziel muss signiert, frontloading oder "
                         "seitwaerts sein")
    print("ZIELGROESSE: %s" % ZIEL)
    if "--selbsttest" in sys.argv:
        raise SystemExit(0 if selbsttest() else 1)
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    zusatz = lade_zusatz()
    print("%d Reihen, Funding %d Symbole, Umlaufmenge %d Symbole"
          % (len(reihen), len(zusatz.get("funding") or {}),
             len(zusatz.get("menge") or {})))

    je_tag = baue(reihen, zusatz)
    if not je_tag:
        raise SystemExit("keine Anker - Abbruch")

    basis = grundlage(je_tag)

    # ---- Abdeckung je Kandidat, BEVOR gerechnet wird -------------------
    alle = [x for z in je_tag.values() for x in z]
    print()
    print("  Abdeckung je Kandidat:")
    for k in KANDIDATEN:
        n = sum(1 for x in alle if k in x)
        print("     %-14s %7d von %d Ankern (%.1f %%)"
              % (k, n, len(alle), 100 * n / len(alle)))

    rng = np.random.default_rng(SAAT)
    pk = positivkontrolle(je_tag, rng)

    print()
    print("=" * 96)
    print("DIE KANDIDATEN — Regel: oberstes Fuenftel -> KURZ, sonst LANG")
    print("=" * 96)
    print()
    print("  ⚠️ Gemessen wird der MEHRERTRAG gegen eine quotengleiche")
    print("     ZUFALLSauswahl derselben Groesse (2.93) - nicht gegen null.")
    print("     Der lange Horizont verdient im Schnitt %+.3f R mehr; gegen"
          % 0.0)
    print("     null gemessen saehe jede Regel schlecht aus.")
    ergebnisse = {}
    for k in KANDIDATEN:
        marke = " ⚠️ KONTROLLGROESSE" if k == "zufall" else ""
        # ⚠️ BEIDE RICHTUNGEN - siehe Audit 4.
        for wo in ("oben", "unten"):
            ergebnisse[(k, wo)] = bericht_wahl(
                "%s%s [%s]" % (k, marke, wo), je_tag, k, rng, richtung=wo)

    # ---- Zusammenfassung -----------------------------------------------
    print()
    print("=" * 96)
    print("BEFUND")
    print("=" * 96)
    print()
    print("  Basisrate: der kurze Horizont war in %.1f %% der Faelle besser."
          % (100 * basis))
    print()
    if not pk:
        print("  ⚠️⚠️ DIE POSITIVKONTROLLE HAT NICHT ANGESCHLAGEN.")
        print("     Damit ist JEDER Nullbefund unten untermaechtig, nicht")
        print("     widerlegend. Das Verfahren ist an dieser Geometrie blind.")
    print()
    print("  Kandidat            Rtg   Wirkung      Vertrauensband        Haelften  URTEIL")
    kontrolle_traegt = False
    for k, wo in [(a, b) for a in KANDIDATEN for b in ("oben", "unten")]:
        e = ergebnisse.get((k, wo))
        if not e or not e.get("echt"):
            print("  %-18s %-5s  —  zu duenn" % (k, wo))
            continue
        s = e["echt"]
        # ⚠️ DAS VORAB FESTGELEGTE URTEIL, nicht ein nachtraeglich
        # zurechtgelegtes: Band ueber null UND beide Haelften einig.
        traegt = s["traegt"] and e["haelften_einig"]
        if k == "zufall" and s["traegt"]:
            kontrolle_traegt = True
        print("  %-18s %-5s %+.4f  [%+.4f .. %+.4f]  %-8s %s"
              % (k, wo, s["mittel"], s["unten"], s["oben"],
                 "einig" if e["haelften_einig"] else "uneins",
                 "✔ TRAEGT" if traegt else "✖ null"))
    print()
    if kontrolle_traegt:
        print("  ⚠️⚠️ DIE KONTROLLGROESSE `zufall` TRAEGT - dann traegt das")
        print("     VERFAHREN, nicht der Kandidat. ALLE Befunde oben sind")
        print("     damit ungueltig, auch die positiven.")
    else:
        print("  ✔ Die Kontrollgroesse `zufall` traegt nicht - das Verfahren")
        print("     erzeugt keinen Vorteil aus dem Nichts.")


if __name__ == "__main__":
    main()
