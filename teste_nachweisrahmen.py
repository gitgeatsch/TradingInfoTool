"""Der Nachweisrahmen aus Stufe 3, gegen ein Modell mit BEKANNTEM Verhalten.

WARUM MIT EINEM NACHGEBILDETEN MODELL. Ein Messrahmen, den man zum ersten Mal
gegen echte LLM-Antworten faehrt, misst beides zugleich: das Modell UND den
eigenen Aufbau. Am 09.08. ist genau das dreimal an einem Tag passiert - der
teuerste Fehler der Session (Methodik-Nachtrag 09.08., Punkt 4). Hier steht das
Verhalten des "Modells" vorher fest, also ist jede Abweichung ein Fehler im
Rahmen.

Jeder Fall bildet eine Lage nach, die im Betrieb vorkommt UND die der Rahmen
unterscheiden koennen muss:

  A  Fakt ohne Wirkung          -> IM RAUSCHEN
  B  Fakt macht es schlechter   -> TENDENZ, Richtung verschlechtert
  C  Fakt macht es besser       -> TENDENZ, Richtung verbessert
  D  Fakt kostet Signale        -> DISQUALIFIZIERT (Waechter vor Bilanz)
  E  zu wenige Faelle           -> UNGEMESSEN, KEIN Negativbefund
  F  Transportfehler            -> ungemessen, faelscht keine Quote
  G  SHORT-Vorschlaege          -> werden bewertet, nicht verworfen
"""
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone

import database.db as db
from database.models import OhlcPoint

import bewerte_fakt_wirkung as nw

fehler = []


def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)


# --- Kursreihen: eine steigende und eine fallende ---------------------------
db.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "t.db"
conn = db.get_connection()
db.init_db(conn)
JETZT = datetime.now(timezone.utc).isoformat()
heute = datetime.now(timezone.utc).date()
TAGE = [(heute - timedelta(days=39 - i)).isoformat() for i in range(40)]


def schreibe(symbol, closes):
    db.upsert_ohlc_points(conn, [
        OhlcPoint(symbol=symbol, currency="USD", date=d, open=c, high=c * 1.03,
                  low=c * 0.97, close=c, volume=1.0, fetched_at=JETZT)
        for d, c in zip(TAGE, closes)])


# MEHRERE Symbole, nicht eines. Der Cluster-Bootstrap zieht Symbole (Methodik
# 2.5: "die effektive Stichprobengroesse ist die Anzahl distinkter Symbole") -
# eine Fixture mit einem einzigen Symbol koennte gar kein Intervall bilden und
# haette den Rahmen faelschlich als kaputt erscheinen lassen. Sechs steigende
# Symbole bilden die reale Lage nach: 122 Faelle auf 12 Symbolen.
RAUF_SYMBOLE = [f"RAUF{i}" for i in range(6)]
for _j, _sym in enumerate(RAUF_SYMBOLE):
    schreibe(_sym, [100.0 + i * (1.5 + 0.2 * _j) for i in range(40)])
schreibe("RUNTER", [100.0 - i * 1.5 for i in range(40)])  # faellt deutlich
from agent.krypto.backward_tracking import lade_kursreihen
REIHEN = lade_kursreihen(conn)

FAELLE_RAUF = [{"fakten": {"kurs": 100.0, "extra": {"wert": 1}},
                "symbol": RAUF_SYMBOLE[i % len(RAUF_SYMBOLE)],
                "created_at": TAGE[0]} for i in range(12)]


def _antwort(entry, stop, ziel, action="ERÖFFNEN"):
    return {"action": action,
            "entry": {"usd_von": entry, "usd_bis": entry},
            "stop_loss": {"usd_von": stop, "usd_bis": stop},
            "take_profit": {"usd_von": ziel, "usd_bis": ziel}}


# --- A) Ein Fakt ohne Wirkung ------------------------------------------------
def ohne_wirkung(fakten):
    return _antwort(100.0, 95.0, 115.0)


n = nw.nachweisrahmen(ohne_wirkung, FAELLE_RAUF, "extra.wert", REIHEN)
pruefe("A1 wirkungsloser Fakt landet IM RAUSCHEN", n.urteil == "IM RAUSCHEN", n.urteil)
pruefe("A2 alle drei Arme wurden bewertet",
       min(len(n.a1.r_werte), len(n.a2.r_werte), len(n.b.r_werte)) == 12,
       f"{len(n.a1.r_werte)}/{len(n.a2.r_werte)}/{len(n.b.r_werte)}")

# --- B) Ein Fakt, dessen Fehlen zu engeren Stops fuehrt ----------------------
# Ohne den Fakt setzt das Modell den Stop enger - der Kurs stoppt es dann aus,
# obwohl er letztlich steigt. Das ist genau die Frage aus Kapitel 9: engere
# Stops sind eine Stellgroesse, das ERGEBNIS sagt, ob sie gut sind.
def enger_ohne_fakt(fakten):
    hat = "wert" in fakten.get("extra", {})
    return _antwort(100.0, 95.0 if hat else 99.0, 115.0)


n = nw.nachweisrahmen(enger_ohne_fakt, FAELLE_RAUF, "extra.wert", REIHEN)
pruefe("B1 Fakt-Entfernung verschlechtert -> TENDENZ erkannt",
       n.urteil.startswith("TENDENZ") and "verschlechtert" in n.urteil, n.urteil)
pruefe("B2 die Wirkung ist negativ", n.wirkung_r is not None and n.wirkung_r < 0,
       f"{n.wirkung_r}")

# --- C) Gegenrichtung: das Entfernen verbessert ------------------------------
def weiter_ohne_fakt(fakten):
    hat = "wert" in fakten.get("extra", {})
    return _antwort(100.0, 99.0 if hat else 95.0, 115.0)


n = nw.nachweisrahmen(weiter_ohne_fakt, FAELLE_RAUF, "extra.wert", REIHEN)
pruefe("C1 Gegenrichtung wird ebenso erkannt",
       n.urteil.startswith("TENDENZ") and "verbessert" in n.urteil, n.urteil)

# --- D) Der EROEFFNEN-Waechter hat VORRANG ----------------------------------
# Ohne den Fakt haelt das Modell fast immer - und vermeidet dadurch Verluste.
# Die R-Bilanz sieht damit BESSER aus. Genau das darf nicht als Erfolg gelten.
RUNTER_SYMBOLE = [f"RUNTER{i}" for i in range(4)]
for _j, _sym in enumerate(RUNTER_SYMBOLE):
    schreibe(_sym, [100.0 - i * (1.2 + 0.2 * _j) for i in range(40)])
REIHEN = lade_kursreihen(conn)
FAELLE_RUNTER = [{"fakten": {"kurs": 100.0, "extra": {"wert": 1}},
                  "symbol": RUNTER_SYMBOLE[i % len(RUNTER_SYMBOLE)],
                  "created_at": TAGE[0]} for i in range(12)]


def haelt_ohne_fakt(fakten):
    hat = "wert" in fakten.get("extra", {})
    if not hat and haelt_ohne_fakt.zaehler[0] % 4 != 0:
        haelt_ohne_fakt.zaehler[0] += 1
        return {"action": "HALTEN"}
    haelt_ohne_fakt.zaehler[0] += 1
    return _antwort(100.0, 95.0, 115.0)


haelt_ohne_fakt.zaehler = [0]
n = nw.nachweisrahmen(haelt_ohne_fakt, FAELLE_RUNTER, "extra.wert", REIHEN)
pruefe("D1 Signalverlust disqualifiziert, trotz besserer R-Bilanz",
       n.urteil == "DISQUALIFIZIERT", n.urteil)
pruefe("D2 der Einbruch wird beziffert",
       n.eroeffnen_einbruch_pp is not None and n.eroeffnen_einbruch_pp >= 10,
       f"{n.eroeffnen_einbruch_pp:.1f} pp" if n.eroeffnen_einbruch_pp else "-")

# --- E) Zu wenige Faelle: UNGEMESSEN, kein Negativbefund ---------------------
n = nw.nachweisrahmen(ohne_wirkung, FAELLE_RAUF[:3], "extra.wert", REIHEN)
pruefe("E1 unter dem Mindest-n lautet das Urteil UNGEMESSEN",
       n.urteil == "UNGEMESSEN", n.urteil)
pruefe("E2 und es wird ausdruecklich als KEIN Negativbefund benannt",
       "KEIN Negativbefund" in n.begruendung)

# --- F) Transportfehler faelschen keine Quote --------------------------------
def mit_transportfehlern(fakten):
    mit_transportfehlern.n[0] += 1
    if mit_transportfehlern.n[0] % 3 == 0:
        raise nw.TransportFehler("429")
    return _antwort(100.0, 95.0, 115.0)


mit_transportfehlern.n = [0]
bilanz = nw.bewerte_arm("T", mit_transportfehlern, FAELLE_RAUF, REIHEN, 14)
pruefe("F1 Transportfehler werden getrennt gezaehlt", bilanz.transportfehler == 4,
       f"{bilanz.transportfehler}")
pruefe("F2 sie stehen NICHT im Nenner der EROEFFNEN-Quote",
       bilanz.entscheidungen == 8 and bilanz.eroeffnen_quote == 1.0,
       f"Nenner {bilanz.entscheidungen}, Quote {bilanz.eroeffnen_quote}")

# --- G) SHORT wird bewertet, nicht verworfen ---------------------------------
# messe_prompt_nebeneffekte._zonen_kennwerte gibt bei SHORT (None, None) und
# verwirft den Fall stillschweigend. Genau das darf hier nicht passieren.
short = _antwort(100.0, 105.0, 85.0)
z = nw.zonen_aus_antwort(short)
pruefe("G1 SHORT-Zonen werden erkannt", z is not None and z["ist_short"] is True)
pruefe("G2 Stop liegt oberhalb, Ziel unterhalb",
       z and z["stop"] == 105.0 and z["ziel"] == 85.0)
pruefe("G3 CRV wird richtig herum gerechnet", z and abs(z["crv"] - 3.0) < 1e-9,
       f"{z['crv'] if z else '-'}")

from messe_prompt_nebeneffekte import _zonen_kennwerte
pruefe("G4 Gegenprobe: das alte Verfahren verwirft denselben Fall",
       _zonen_kennwerte(short) == (None, None), str(_zonen_kennwerte(short)))

# Und ein SHORT auf der fallenden Reihe muss einen echten R-Wert liefern.
faelle_short = [{"fakten": {"kurs": 100.0, "extra": {"wert": 1}},
                 "symbol": "RUNTER", "created_at": TAGE[0]} for _ in range(6)]
bilanz = nw.bewerte_arm("S", lambda f: short, faelle_short, REIHEN, 20)
pruefe("G5 SHORT auf fallender Reihe wird bewertet",
       len(bilanz.r_werte) == 6 and bilanz.mittel_r is not None,
       f"{len(bilanz.r_werte)} bewertet, Mittel {bilanz.mittel_r}")
pruefe("G6 und der SHORT gewinnt dort auch", (bilanz.mittel_r or 0) > 0,
       f"{bilanz.mittel_r:+.2f} R" if bilanz.mittel_r else "-")

# --- H) Der Massstab ist CRV-Breakeven, nicht 50 % ---------------------------
pruefe("H1 Breakeven wird als 1/(1+CRV) ausgewiesen",
       abs((bilanz.breakeven_quote or 0) - 0.25) < 1e-9,
       f"{bilanz.breakeven_quote}")

# --- I) Mit ECHTEM Rauschen - sonst ist die Rauschgrenze nie geprueft --------
#
# Die Faelle A-H fahren ein deterministisches Modell. Der Rauschboden ist dort
# exakt 0,000 R, und "IM RAUSCHEN" in Fall A besteht deshalb DEGENERIERT: bei
# Rauschen 0 und Wirkung 0 ist die Bedingung |Wirkung| <= Rauschen trivial wahr.
# Dieselbe Falle wie bei temperature=0,0 (Methodik-Nachtrag 09.08., Punkt 1) -
# dort war der A/A'-Abgleich 100 %, und jede Abweichung sah signifikant aus.
#
# Hier streut das Modell deshalb reproduzierbar um den Stop-Abstand. Nur so ist
# die Grenze zwischen "Rauschen" und "Wirkung" ueberhaupt geprueft.
def _streuung(i, breite):
    """Reproduzierbarer Pseudo-Zufall - ohne random, damit der Test stabil ist."""
    return ((i * 2654435761) % 1000) / 1000.0 * breite - breite / 2.0


def rauschend(breite, versatz):
    zaehler = [0]

    def modell(fakten):
        i = zaehler[0]
        zaehler[0] += 1
        hat = "wert" in fakten.get("extra", {})
        stop = 95.0 + _streuung(i, breite) + (0.0 if hat else versatz)
        return _antwort(100.0, stop, 115.0)

    return modell


# KEIN Effekt, nur Rauschen -> darf keinen Alarm ausloesen. Das ist die
# entscheidende Eigenschaft: der gepaarte Vergleich ist maechtiger als ein
# Mittelwertvergleich und findet schon kleine SYSTEMATISCHE Versaetze. Genau
# deshalb muss geprueft werden, dass er bei Abwesenheit eines Effekts still
# bleibt - ein empfindliches Verfahren ohne diese Gegenprobe waere gefaehrlich.
n = nw.nachweisrahmen(rauschend(breite=6.0, versatz=0.0), FAELLE_RAUF,
                      "extra.wert", REIHEN)
pruefe("I1 reines Rauschen ohne Effekt loest KEINEN Alarm aus",
       n.urteil == "IM RAUSCHEN",
       f"{n.urteil} (Rauschen {n.rauschboden_r:.3f}, Wirkung {n.wirkung_r:+.3f})")
pruefe("I2 der Rauschboden ist diesmal NICHT null - die Grenze wurde gepruefT",
       (n.rauschboden_r or 0) > 0.01, f"{n.rauschboden_r:.3f} R")

# Derselbe Aufbau, aber der Effekt uebersteigt das Rauschen deutlich.
n = nw.nachweisrahmen(rauschend(breite=1.0, versatz=4.5), FAELLE_RAUF,
                      "extra.wert", REIHEN)
pruefe("I3 grosser Effekt bei schmalem Rauschen wird als TENDENZ erkannt",
       n.urteil.startswith("TENDENZ"),
       f"{n.urteil} (Rauschen {n.rauschboden_r:.3f}, Wirkung {n.wirkung_r:+.3f})")

# --- J) Der Cluster-Bootstrap ist konservativer als der naive ---------------
# Die Werte muessen sich ZWISCHEN den Clustern unterscheiden - sonst ist jede
# Ziehung gleich und die Breite null. Genau das war der erste Entwurf.
werte = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5]
viele = [f"S{i}" for i in range(12)]          # 12 Cluster, je 1 Wert
wenige = ["A"] * 6 + ["B"] * 6                 # 2 Cluster, je 6 Werte
cu_v, co_v = nw._cluster_bootstrap(werte, viele)
cu_w, co_w = nw._cluster_bootstrap(werte, wenige)
pruefe("J1 wenige Cluster ergeben ein BREITERES Intervall",
       (co_w - cu_w) > (co_v - cu_v),
       f"2 Cluster {co_w - cu_w:.3f} gegen 12 Cluster {co_v - cu_v:.3f}")
pruefe("J2 ein einzelnes Cluster liefert kein Intervall",
       nw._cluster_bootstrap(werte, ["A"] * 12) == (None, None))
pruefe("J3 zwei Laeufe liefern dasselbe Intervall (reproduzierbar)",
       nw._cluster_bootstrap(werte, viele) == (cu_v, co_v))

print()
print(nw.bericht(nw.nachweisrahmen(enger_ohne_fakt, FAELLE_RAUF, "extra.wert", REIHEN)))
print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
raise SystemExit(1 if fehler else 0)
