"""Gate und Bewertung muessen dieselbe Zonenkante nehmen (2026-08-09, Variante A).

DER DEFEKT. Eine Preiszone hat zwei Kanten. `_zonen_absolut()` - die Quelle des
CRV, das ueber die Mindestgrenze 2,0 entscheidet - spiegelt bei SHORT auf die
`_bis`-Kante: Stop weiter weg, Ziel naeher, beides konservativ. Die
Outcome-Tracker nahmen ueber `_threshold()` fuer BEIDE Richtungen die
`_von`-Kante. Damit genehmigte das System einen Trade nach der einen Rechnung
und bewertete ihn nach einer anderen.

Bei LONG fallen beide zusammen - deshalb ist es nie aufgefallen, und deshalb
prueft dieser Test SHORT und LONG getrennt.

ECHTER FALL (NEAR, hebel_signals id=407):

    entry 1,91   stop_von 1,96 / stop_bis 2,09   ziel_von 1,61 / ziel_bis 1,78

    Gate:          risiko 0,18   chance 0,13   ->  CRV   0,72
    Tracker (alt): risiko 0,05   chance 0,30   ->  R    +6,00

Bei einem CRV von 0,72 sind +6,00 R nicht erreichbar. Die Zahl war ein Artefakt.

DIE ZWEITE, SCHWERERE HAELFTE betrifft nicht die Zahl, sondern den Handel: mit
der nahen Kante loeste der Stop eines SHORT frueher aus als das Risiko, das bei
der Positionsgroesse eingeplant war. Gemessen ueber 128 auswertbare SHORT-Zeilen
verschiebt die Korrektur die Summe von -44,69 R auf -59,91 R - die alte
Konvention hat den Schatten-Arm geschmeichelt.
"""
from agent.krypto.backward_tracking import _threshold, _zonen_absolut, _zonen_schwelle

fehler = []


def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)


class Zeile(dict):
    """Verhaelt sich beim Feldzugriff wie eine sqlite3.Row."""
    def __getitem__(self, k):
        if k not in self:
            raise IndexError(k)
        return dict.__getitem__(self, k)


# Der echte Fall aus der Produktion.
NEAR = Zeile(
    entry_usd_von=1.88, entry_usd_bis=1.94,
    stop_loss_usd_von=1.96, stop_loss_usd_bis=2.09,
    take_profit_usd_von=1.61, take_profit_usd_bis=1.78,
)

# --- A) SHORT: die Schwelle folgt jetzt dem Gate ----------------------------
z = _zonen_absolut(NEAR)
pruefe("A1 der Fall wird als SHORT erkannt", z["ist_short"] is True)
pruefe("A2 Gate rechnet mit stop_bis", abs(z["stop"] - 2.09) < 1e-9, f"{z['stop']}")
pruefe("A3 Gate rechnet mit ziel_bis", abs(z["ziel"] - 1.78) < 1e-9, f"{z['ziel']}")

s_stop = _zonen_schwelle(1.96, 2.09, None, ist_short=True)
s_ziel = _zonen_schwelle(1.61, 1.78, None, ist_short=True)
pruefe("A4 Tracker nimmt bei SHORT dieselbe Stop-Kante wie das Gate",
       abs(s_stop - z["stop"]) < 1e-9, f"{s_stop} gegen {z['stop']}")
pruefe("A5 Tracker nimmt bei SHORT dieselbe Ziel-Kante wie das Gate",
       abs(s_ziel - z["ziel"]) < 1e-9, f"{s_ziel} gegen {z['ziel']}")

# GEGENPROBE gegen den kaputten Zustand: die alte Funktion muss abweichen.
# Taete sie es nicht, wuerde dieser Test nichts pruefen.
a_stop = _threshold(1.96, None)
a_ziel = _threshold(1.61, None)
pruefe("A6 Gegenprobe: die alte Kante weicht bei SHORT ab",
       abs(a_stop - z["stop"]) > 0.1 and abs(a_ziel - z["ziel"]) > 0.1,
       f"alt {a_stop}/{a_ziel} gegen neu {s_stop}/{s_ziel}")

# Und der Kern: das erreichbare R darf das CRV nicht uebersteigen.
crv = z["crv"]
r_max_neu = (z["entry"] - s_ziel) / (s_stop - z["entry"])
r_max_alt = (z["entry"] - a_ziel) / (a_stop - z["entry"])
pruefe("A7 erreichbares R entspricht jetzt dem CRV", abs(r_max_neu - crv) < 1e-9,
       f"R_max {r_max_neu:.2f} bei CRV {crv:.2f}")
pruefe("A8 Gegenprobe: alt war das erreichbare R ein Vielfaches des CRV",
       r_max_alt > crv * 5, f"R_max_alt {r_max_alt:.2f} bei CRV {crv:.2f}")

# --- B) LONG bleibt unveraendert --------------------------------------------
# Wichtig: die Aenderung darf NUR SHORT betreffen. Waere LONG mitbetroffen,
# waeren saemtliche bisherigen Auswertungen entwertet.
LONG = Zeile(
    entry_usd_von=100.0, entry_usd_bis=102.0,
    stop_loss_usd_von=95.0, stop_loss_usd_bis=97.0,
    take_profit_usd_von=115.0, take_profit_usd_bis=120.0,
)
zl = _zonen_absolut(LONG)
pruefe("B1 der Fall wird als LONG erkannt", zl["ist_short"] is False)
pruefe("B2 Stop-Kante bei LONG unveraendert",
       _zonen_schwelle(95.0, 97.0, None, False) == _threshold(95.0, None) == zl["stop"],
       f"{_zonen_schwelle(95.0, 97.0, None, False)}")
pruefe("B3 Ziel-Kante bei LONG unveraendert",
       _zonen_schwelle(115.0, 120.0, None, False) == _threshold(115.0, None) == zl["ziel"],
       f"{_zonen_schwelle(115.0, 120.0, None, False)}")

# --- C) Rueckfall-Kette ------------------------------------------------------
# Bestandszeilen fuehren teils nur eine Kante oder nur den alten Punktwert.
# Faellt die Kette aus, wuerden solche Zeilen still zu 'nicht_anwendbar'.
pruefe("C1 fehlende _bis-Kante faellt bei SHORT auf _von zurueck",
       _zonen_schwelle(1.96, None, None, True) == 1.96)
pruefe("C2 fehlende _von-Kante faellt bei LONG auf _bis zurueck",
       _zonen_schwelle(None, 97.0, None, False) == 97.0)
pruefe("C3 ohne beide Kanten greift der alte Punktwert",
       _zonen_schwelle(None, None, 42.0, True) == 42.0)
pruefe("C4 ohne jeden Wert bleibt None",
       _zonen_schwelle(None, None, None, True) is None)

# --- D) Beide Tracker-Dateien benutzen die neue Kante ------------------------
# Die Hebel-Seite traegt 134 der 167 aufgeloesten SHORT-Zeilen. Ein Fix, der nur
# in einer der beiden Dateien landet, waere schlimmer als keiner - dann
# rechneten die Arme untereinander verschieden.
import pathlib

for datei, mindestens in (("agent/krypto/backward_tracking.py", 3),
                          ("agent/krypto/hebel_backward_tracking.py", 2)):
    text = pathlib.Path(datei).read_text(encoding="utf-8")
    n = text.count("_zonen_schwelle(")
    pruefe(f"D  {datei} nutzt die richtungsbewusste Kante", n >= mindestens,
           f"{n} Vorkommen")

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
raise SystemExit(1 if fehler else 0)
