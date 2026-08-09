"""Selbsttest fuer den CRV-Bezug der Trefferquote - mit Gegenkontrollen.

GEAENDERT AM 09.08. an zwei Stellen, die zusammengehoeren:

    compute_win_rate_fact()   liefert jetzt Median-CRV, Breakeven und Abstand
    hebel_risk_gate.py        bewertet gegen den Abstand statt gegen feste 30/60

WARUM BEIDE ZUSAMMEN. Nur eine zu aendern erzeugt zwei widerspruechliche
Rahmungen derselben Zahl im selben System: der Prompt saegte "16 % gegen 26,7 %
Breakeven", das Gate saegte "negativ, Punkt".

    python teste_trefferquote_bezug.py
"""
from __future__ import annotations

import sqlite3
import sys

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


def _db(zeilen):
    """Temporaere DB mit genau den uebergebenen Hebel-Signalen."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # `richtung` MUSS in der Testtabelle stehen - sonst bleibt `je_richtung`
    # leer und die Gegenkontrolle G4g laeuft ins Nichts, ohne dass es
    # auffaellt. Genau dieser leere Lauf ist am 09.08. passiert.
    conn.execute("""CREATE TABLE hebel_signals (
        symbol TEXT, outcome_status TEXT, richtung TEXT,
        entry_usd_von REAL, entry_usd_bis REAL,
        stop_loss_usd_von REAL, stop_loss_usd_bis REAL,
        take_profit_usd_von REAL, take_profit_usd_bis REAL)""")
    conn.executemany(
        "INSERT INTO hebel_signals VALUES (?,?,?,?,?,?,?,?,?)", zeilen)
    return conn


def _long(sym, status, crv, richtung="LONG"):
    """LONG mit Entry 100, Stop 90 (Risiko 10), Ziel so, dass CRV stimmt."""
    return (sym, status, richtung, 100.0, 100.0, 90.0, 90.0,
            100 + 10 * crv, 100 + 10 * crv)


from agent.krypto.backward_tracking import compute_win_rate_fact  # noqa: E402

print("A  Breakeven wird aus dem tatsaechlichen CRV abgeleitet")

# 4 Signale mit CRV 2,0 -> Breakeven 33,3 %; 1 Treffer von 4 = 25 % -> -8,3 pp
f = compute_win_rate_fact(_db([
    _long("A", "take_profit_erreicht", 2.0),
    _long("B", "stop_loss_erreicht", 2.0),
    _long("C", "stop_loss_erreicht", 2.0),
    _long("D", "stop_loss_erreicht", 2.0),
]), "hebel")
pruefe("A1 Median-CRV erkannt", abs(f["crv_median"] - 2.0) < 1e-6, str(f["crv_median"]))
pruefe("A2 Breakeven = 1/(1+CRV) = 33,3 %",
       abs(f["breakeven_trefferquote_pct"] - 33.3) < 0.1,
       str(f["breakeven_trefferquote_pct"]))
pruefe("A3 Abstand = 25,0 - 33,3 = -8,3 pp",
       abs(f["vorsprung_vor_breakeven_pp"] + 8.3) < 0.2,
       str(f["vorsprung_vor_breakeven_pp"]))

# GEGENKONTROLLE: bei CRV 4,0 ist der Breakeven 20 % - DIESELBE Trefferquote
# von 25 % ist dort ein VORSPRUNG. Ohne diesen Test koennte die Funktion den
# Breakeven konstant liefern und A2 bestuende trotzdem.
f4 = compute_win_rate_fact(_db([
    _long("A", "take_profit_erreicht", 4.0),
    _long("B", "stop_loss_erreicht", 4.0),
    _long("C", "stop_loss_erreicht", 4.0),
    _long("D", "stop_loss_erreicht", 4.0),
]), "hebel")
pruefe("A3g Gegenkontrolle: gleiche Quote, CRV 4,0 -> Breakeven 20 %, "
       "Abstand POSITIV",
       abs(f4["breakeven_trefferquote_pct"] - 20.0) < 0.1
       and f4["vorsprung_vor_breakeven_pp"] > 0,
       f"Breakeven {f4['breakeven_trefferquote_pct']}, "
       f"Abstand {f4['vorsprung_vor_breakeven_pp']:+.1f}")

print("\nB  Ueberholte Signale werden ausgewiesen, nicht verschwiegen")
f = compute_win_rate_fact(_db([
    _long("A", "take_profit_erreicht", 2.0),
    _long("B", "stop_loss_erreicht", 2.0),
    _long("C", "ueberholt_durch_neuere_analyse", 2.0),
    _long("D", "ueberholt_durch_neuere_analyse", 2.0),
]), "hebel")
pruefe("B1 ueberholte zaehlen NICHT in die Quote",
       f["anzahl_ausgewertete_signale"] == 2, str(f["anzahl_ausgewertete_signale"]))
pruefe("B2 werden aber ausgewiesen", f["nicht_enthalten_ueberholt"] == 2,
       str(f["nicht_enthalten_ueberholt"]))
pruefe("B3 und im Hinweis genannt", "ersetzt" in f["hinweis"])

print("\nC  Gate-Bewertung haengt am Abstand, nicht an fester Schwelle")
from agent.krypto import hebel_risk_gate as G  # noqa: E402


def bewertung_fuer(quote, breakeven, vorsprung, anzahl=94):
    """Nur den Trefferquoten-Zweig, aber ueber die ECHTE Produktivfunktion.

    Bewusst kein Nachbau des Zweigs: eine zweite Fassung derselben Logik
    driftet garantiert weg, und dann prueft der Test seinen eigenen Nachbau.
    Alle uebrigen Parameter sind neutral gesetzt, damit nur dieser eine
    Faktor entsteht, an dem es hier haengt.
    """
    fak = G.compute_risikofaktoren_hebel(
        richtung="LONG", regime="baer", confidence_pct=None, crv=None,
        gegenszenario_pct=None, gegenszenario_schwelle=None,
        crv_knapp_schwelle_relativ=None, retail_long_bias_extreme=None,
        long_account_pct=None, trade_thesis_typ=None,
        historische_erfolgsquote={
            "anzahl_ausgewertete_signale": anzahl, "trefferquote_pct": quote,
            "breakeven_trefferquote_pct": breakeven,
            "vorsprung_vor_breakeven_pp": vorsprung})
    for f in fak:
        if "Trefferquote" in f.name:
            return f.bewertung
    return None


# 25 % bei Breakeven 33,3 -> unter Breakeven -> negativ
pruefe("C1 unter dem Breakeven -> negativ",
       bewertung_fuer(25.0, 33.3, -8.3) == "negativ",
       str(bewertung_fuer(25.0, 33.3, -8.3)))
# GEGENKONTROLLE: DIESELBE Quote von 25 %, aber Breakeven 20 -> darueber
pruefe("C1g Gegenkontrolle: gleiche Quote 25 %, Breakeven 20 -> NICHT negativ",
       bewertung_fuer(25.0, 20.0, +5.0) != "negativ",
       str(bewertung_fuer(25.0, 20.0, +5.0)))
pruefe("C2 deutlich ueber dem Breakeven -> positiv",
       bewertung_fuer(45.0, 20.0, +25.0) == "positiv",
       str(bewertung_fuer(45.0, 20.0, +25.0)))
# Rueckfall: ohne die neuen Felder gilt die alte feste Schwelle
pruefe("C3 ohne Breakeven-Feld greift die alte Schwelle (kein Ausfall)",
       bewertung_fuer(25.0, None, None) == "negativ")
pruefe("C3g Gegenkontrolle: alte Schwelle bewertet 65 % als positiv",
       bewertung_fuer(65.0, None, None) == "positiv")

print("\nC2  AUSGANGSWERT bei null eigenen Signalen")

leer = compute_win_rate_fact(_db([]), "hebel")
pruefe("C2.1 der Fakt faellt NICHT mehr weg", leer is not None)
pruefe("C2.2 Breakeven aus der CRV-Pflichtgrenze (33,3 % bei CRV 2,0)",
       leer and abs(leer["breakeven_trefferquote_pct"] - 33.3) < 0.1,
       str(leer["breakeven_trefferquote_pct"]) if leer else "-")
pruefe("C2.3 Gewicht ist EXAKT 0 - der Wert behauptet nichts",
       leer["gewicht"] == 0.0)
pruefe("C2.4 KEINE erfundene Trefferquote", leer["trefferquote_pct"] is None)
pruefe("C2.5 als nicht belastbar gekennzeichnet", leer["belastbar"] is False)
pruefe("C2.6 der Hinweis sagt ausdruecklich, dass es keine Messung ist",
       "KEINE Messung" in leer["hinweis"])

# GEGENKONTROLLE 1: sobald EIN Signal da ist, kommt der Breakeven aus den
# DATEN, nicht mehr aus der Konstanten. Sonst waere der Ausgangswert klebrig.
mit_daten = compute_win_rate_fact(_db([
    _long("A", "take_profit_erreicht", 4.0),
    _long("B", "stop_loss_erreicht", 4.0),
]), "hebel")
pruefe("C2.6g Gegenkontrolle: mit Daten kommt der Breakeven aus dem "
       "gemessenen CRV, nicht aus der Konstanten",
       abs(mit_daten["breakeven_trefferquote_pct"] - 20.0) < 0.1
       and mit_daten["gewicht"] > 0,
       f"{mit_daten['breakeven_trefferquote_pct']} bei Gewicht "
       f"{mit_daten['gewicht']}")

# GEGENKONTROLLE 2: die gespiegelte Konstante darf nicht von der Quelle
# abdriften. Genau dafuer steht der Kommentar an der Codestelle.
from agent.krypto.backward_tracking import _CRV_MINIMUM  # noqa: E402
from agent.krypto.risk_gate import CRV_MINIMUM  # noqa: E402
pruefe("C2.7g Gegenkontrolle: die gespiegelte CRV-Grenze stimmt mit der "
       "Quelle ueberein", _CRV_MINIMUM == CRV_MINIMUM,
       f"{_CRV_MINIMUM} gegen {CRV_MINIMUM}")

print("\nD  Die echte Produktionszahl bleibt eine Tatsache")
pruefe("D1 absolute Quote wird NICHT geschoent",
       compute_win_rate_fact(_db([
           _long("A", "take_profit_erreicht", 2.0),
           _long("B", "stop_loss_erreicht", 2.0),
           _long("C", "stop_loss_erreicht", 2.0),
           _long("D", "stop_loss_erreicht", 2.0),
       ]), "hebel")["trefferquote_pct"] == 25.0)

print("\nE  Systemguete: Basislinie und Unsicherheit werden DURCHGEREICHT")
from agent.krypto import backward_tracking as BT  # noqa: E402

VOLL = {"hebel": {"real": {
    "anzahl_bewertet": 133, "expectancy_r": -0.14864, "sqn": -1.0632,
    "sqn_einordnung": "kaum handelbar", "profit_factor": 0.7967,
    "basislinie_erwartungswert_r": -0.0937, "signalbeitrag_r": -0.0549,
    "basislinie_anzahl": 958, "aufloesungsquote": 0.7037,
    "expectancy_ci_unten": -0.4072, "expectancy_ci_oben": 0.1471}}}


def guete(daten):
    """Ueber die ECHTE Funktion, nur compute_systemguete() ersetzt."""
    alt = BT.compute_systemguete
    BT.compute_systemguete = lambda *a, **kw: daten
    try:
        return BT.systemguete_kontext_fuer_prompt(conn=None)
    finally:
        BT.compute_systemguete = alt


f = guete(VOLL)
pruefe("E1 Basislinie durchgereicht",
       abs(f["basislinie_erwartungswert_r"] + 0.094) < 0.001,
       str(f["basislinie_erwartungswert_r"]))
pruefe("E2 Signalbeitrag durchgereicht",
       abs(f["signalbeitrag_r"] + 0.055) < 0.001, str(f["signalbeitrag_r"]))
pruefe("E3 Vertrauensbereich durchgereicht",
       f["erwartungswert_ci"] == [-0.407, 0.147], str(f["erwartungswert_ci"]))
pruefe("E4 die ROHE Zahl bleibt unveraendert an erster Stelle",
       abs(f["erwartungswert_r"] + 0.149) < 0.001, str(f["erwartungswert_r"]))
pruefe("E5 Lesehilfe erklaert die Basislinie",
       "MECHANISCHEN" in f["lesehilfe"] and "signalbeitrag_r" in f["lesehilfe"])

# GEGENKONTROLLE: fehlen die Basislinienfelder (aeltere Auswertung), muessen
# die neuen Schluessel None sein - NICHT geraten und nicht weggelassen. Ohne
# diesen Test koennte die Funktion Ersatzwerte erfinden und E1-E3 bestuenden.
OHNE = {"hebel": {"real": {k: v for k, v in VOLL["hebel"]["real"].items()
                           if not k.startswith(("basislinie", "signalbeitrag",
                                                "expectancy_ci"))}}}
f2 = guete(OHNE)
pruefe("E5g Gegenkontrolle: ohne Basislinie -> None statt Ersatzwert",
       f2["basislinie_erwartungswert_r"] is None
       and f2["signalbeitrag_r"] is None
       and f2["erwartungswert_ci"] is None,
       f"{f2['basislinie_erwartungswert_r']} / {f2['signalbeitrag_r']} / "
       f"{f2['erwartungswert_ci']}")
pruefe("E6g Gegenkontrolle: der Fakt faellt dadurch NICHT aus",
       f2["erwartungswert_r"] is not None and f2["anzahl_ausgewerteter_trades"] == 133)
# Und die Sperre gegen zu duenne Datenbasis muss weiter greifen.
DUENN = {"hebel": {"real": {**VOLL["hebel"]["real"], "anzahl_bewertet": 12}}}
# GEAENDERT am 09.08.: der Fakt faellt unter 30 Trades NICHT mehr weg, sondern
# wird als vorlaeufig geliefert. Grund (Nutzer): *"es soll einen Ausgangswert
# geben und dann kalibrieren"* - eine harte Schwelle auf einer glatten Groesse
# ist dieselbe Klippe wie beim Regime. Die Schrumpfung macht eine duenne Zahl
# selbst harmlos: bei n=12 liegt das Gewicht bei 0,19.
f3 = guete(DUENN)
pruefe("E7 unter 30 Trades wird der Fakt VORLAEUFIG geliefert, nicht verworfen",
       f3 is not None and f3["belastbar"] is False,
       f"belastbar={f3['belastbar'] if f3 else None}")
pruefe("E8 und er sagt ausdruecklich, dass er vorlaeufig ist",
       f3 and f3["vorlaeufig_hinweis"] and "VORLAEUFIG" in f3["vorlaeufig_hinweis"])
pruefe("E8g Gegenkontrolle: ueber der Schwelle KEIN Vorlaeufig-Vermerk",
       guete(VOLL)["belastbar"] is True
       and guete(VOLL)["vorlaeufig_hinweis"] is None)
# Und die untere Grenze bleibt: ohne einen einzigen Trade gibt es nichts.
# GEAENDERT am 09.08.: auch bei null Trades wird jetzt ein Ausgangswert
# geliefert statt None - siehe Abschnitt H. Hier bleibt die Zusicherung, dass
# dabei KEIN Messwert erfunden wird.
LEER = {"hebel": {"real": {**VOLL["hebel"]["real"], "anzahl_bewertet": 0}}}
_leer = guete(LEER)
pruefe("E9 bei NULL Trades kommt ein Ausgangswert, kein None",
       _leer is not None and _leer["gewicht"] == 0.0)
pruefe("E9g Gegenkontrolle: dabei wird KEIN Erwartungswert erfunden",
       _leer["erwartungswert_r"] is None, str(_leer["erwartungswert_r"]))

print("\nF  Der ANKER der Schrumpfung - Null waere falsch")
f = guete(VOLL)

pruefe("F1 Erwartungswert liegt zwischen roh und BASISLINIE (nicht Null)",
       -0.149 - 1e-6 <= f["erwartungswert_gewichtet"] <= -0.094 + 1e-6,
       f"{f['erwartungswert_gewichtet']:+.4f} zwischen roh -0.149 und "
       f"Basislinie {f['basislinie_erwartungswert_r']}")
pruefe("F2 Signalbeitrag liegt zwischen roh und NULL (er ist eine Differenz)",
       -0.055 - 1e-6 <= f["signalbeitrag_gewichtet"] <= 1e-6,
       f"{f['signalbeitrag_gewichtet']:+.4f}")
pruefe("F3 die kategoriale Zwillingsform ist vorhanden",
       f["einordnung"] == "unter der Basislinie", str(f["einordnung"]))
pruefe("F3b das Vertrauensintervall wird als Ja/Nein ausgewiesen, nicht nur "
       "als zwei Zahlen", f["ci_enthaelt_null"] is True,
       str(f["ci_enthaelt_null"]))

# DIE ENTSCHEIDENDE GEGENKONTROLLE (Nutzer-Einwand 09.08.: "Null ist
# schwachsinn"). Mit Anker 0 saehe das System BESSER aus als der Markt
# zulaesst - ein mechanischer Einstieg verliert 0,094 R. Der Test stellt
# sicher, dass die Umsetzung genau das NICHT tut.
from agent.krypto.backward_tracking import schrumpfe_zu_neutral  # noqa: E402
mit_null = schrumpfe_zu_neutral(-0.14864, 133, 0.0)
pruefe("F3g Gegenkontrolle: Anker Null wuerde beschoenigen - und wird "
       "NICHT verwendet",
       mit_null["gewichtet"] > f["erwartungswert_gewichtet"] + 0.01,
       f"Anker 0 ergaebe {mit_null['gewichtet']:+.4f} statt "
       f"{f['erwartungswert_gewichtet']:+.4f}")
pruefe("F4 die ROHEN Werte bleiben unveraendert daneben stehen",
       f["erwartungswert_r"] == -0.149 and f["signalbeitrag_r"] == -0.055)

# GEAENDERT am 09.08.: ohne Basislinie wird jetzt gegen NULL geschrumpft
# ("kein Vorteil angenommen") statt gar nicht. Vorher stand hier `is None` -
# der Test hat die Verhaltensaenderung korrekt gefangen. Der Anker wird
# benannt, damit erkennbar bleibt, welcher gilt.
f2 = guete(OHNE)
pruefe("F4g ohne Basislinie: Anker faellt auf Null zurueck, wird aber BENANNT",
       f2["erwartungswert_anker"] == "null_kein_vorteil"
       and f2["erwartungswert_gewichtet"] is not None,
       f"{f2['erwartungswert_anker']} -> {f2['erwartungswert_gewichtet']}")

print("\nH  SYSTEMGUETE: Ausgangswert auch ohne Basislinie")

h0 = guete({"hebel": {"real": {"anzahl_bewertet": 0}}})
pruefe("H1 der Fakt faellt bei n=0 NICHT mehr weg", h0 is not None)
pruefe("H2 Anker ist die Null, und das steht ausdruecklich da",
       h0["erwartungswert_anker"] == "null_kein_vorteil"
       and h0["erwartungswert_gewichtet"] == 0.0,
       f"{h0['erwartungswert_anker']} -> {h0['erwartungswert_gewichtet']}")
pruefe("H3 Gewicht 0 - der Wert behauptet nichts", h0["gewicht"] == 0.0)
pruefe("H4 KEIN erfundener Erwartungswert", h0["erwartungswert_r"] is None)
pruefe("H5 der Hinweis sagt, dass es keine Messung ist",
       "KEINE Messung" in (h0["vorlaeufig_hinweis"] or ""))

h1 = guete({"hebel": {"real": {"anzahl_bewertet": 40, "expectancy_r": -0.20,
                               "sqn": -1.0, "profit_factor": 0.8}}})
pruefe("H6 mit Trades aber ohne Basislinie -> Anker Null, Gewicht > 0",
       h1["erwartungswert_anker"] == "null_kein_vorteil" and h1["gewicht"] > 0,
       f"{h1['erwartungswert_anker']}, Gewicht {h1['gewicht']}")

# GEGENKONTROLLE: WO eine Basislinie existiert, MUSS sie der Anker sein -
# sonst waere der Rueckfall zum Regelfall geworden und wuerde beschoenigen.
hv = guete(VOLL)
pruefe("H6g Gegenkontrolle: mit Basislinie ist SIE der Anker, nicht die Null",
       hv["erwartungswert_anker"] == "basislinie",
       str(hv["erwartungswert_anker"]))
pruefe("H7g Gegenkontrolle: der Anker wird BENANNT - ohne dieses Feld waere "
       "nicht erkennbar, welcher gilt",
       "erwartungswert_anker" in h0 and "erwartungswert_anker" in hv)
pruefe("H8g Gegenkontrolle: negatives n liefert weiterhin None",
       guete({"hebel": {"real": {"anzahl_bewertet": -1}}}) is None)

print("\nG  STRUKTUR - flach, selbsterklaerend, keine Doppelungen")
q = compute_win_rate_fact(_db([
    _long("A", "take_profit_erreicht", 2.0),
    _long("B", "stop_loss_erreicht", 2.0),
    _long("C", "stop_loss_erreicht", 2.0),
    _long("D", "stop_loss_erreicht", 2.0),
]), "hebel")


def _tiefe(obj, d=1):
    """Verschachtelungstiefe, Listen zaehlen NICHT als Ebene.

    Eine Liste gleichfoermiger flacher Saetze ist eine Tabelle, keine
    Verschachtelung - genau die Form, die dieses Projekt bevorzugt."""
    if isinstance(obj, list):
        return max((_tiefe(v, d) for v in obj), default=d - 1)
    if not isinstance(obj, dict) or not obj:
        return d - 1
    return max((_tiefe(v, d + 1) for v in obj.values()
                if isinstance(v, (dict, list))), default=d)


pruefe("G1 Trefferquote hoechstens ZWEI Ebenen tief", _tiefe(q) <= 2,
       f"Tiefe {_tiefe(q)}")
pruefe("G2 Systemguete hoechstens ZWEI Ebenen tief", _tiefe(f) <= 2,
       f"Tiefe {_tiefe(f)}")
pruefe("G3 kein `geschrumpft`-Unterobjekt mehr (war 3 Ebenen tief)",
       "geschrumpft" not in q and "erwartungswert_geschrumpft" not in f)
pruefe("G4 `belastbar` in BEIDEN Zweigen - auch bei n=0",
       "belastbar" in q and "belastbar" in compute_win_rate_fact(_db([]), "hebel"))
# GEGENKONTROLLE: die Felder sind nicht nur flach, sondern auch VOLLSTAENDIG -
# jede Richtung muss fuer sich lesbar sein, ohne Nachschlagen im Elternblock.
pruefe("G4h Wache: die Richtungs-Gegenkontrolle hat ueberhaupt Faelle",
       bool(q.get("je_richtung")), str(q.get("je_richtung")))
for d in (q.get("je_richtung") or []):
    ri = d.get("richtung")
    fehlend = [k for k in ("trefferquote_pct", "breakeven_trefferquote_pct",
                           "vorsprung_vor_breakeven_pp", "gewicht",
                           "einordnung") if k not in d]
    pruefe(f"G4g Gegenkontrolle: {ri} ist fuer sich lesbar", not fehlend,
           f"fehlend {fehlend}")

print("\n" + "=" * 66)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
