"""Prueft das klassenspezifische Kostenmodell (07.08.2026).

DER FEHLER, DEN ES BEHEBT. Bis hierher galt EIN Satz fuer die gesamte
Spot-Familie: 1 % je Seite, 2 % Roundtrip - bei 5 % Stop also 0,40 R. Recherche
(Handelsblatt, Finanzfuchs) zeigt: bei Bitpanda kosten Aktien und ETFs **1 EUR
FIX je Trade** plus Spread, Krypto dagegen 0,99-2,49 % im Kurs.

DAS STRUKTURELLE PROBLEM: eine fixe Gebuehr bricht die Eigenschaft, auf der die
R-Rechnung beruht - der Einsatz kuerzt sich nicht mehr heraus. Genau das prueft
dieser Test: bei den boersengehandelten Klassen MUESSEN die Kosten mit der
Positionsgroesse fallen, bei Krypto und Hebel NICHT.
"""
from agent.krypto.backward_tracking import (
    _KOSTEN_REFERENZ_POSITION_EUR, TIER_HEDGE, kosten_in_r,
)

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

STOP = 0.05

print("A) BOERSE - Kosten haengen an der Positionsgroesse")
k300 = kosten_in_r(STOP, "aktien", 10.0, position_eur=300)
k1000 = kosten_in_r(STOP, "aktien", 10.0, position_eur=1000)
k2000 = kosten_in_r(STOP, "aktien", 10.0, position_eur=2000)
pruefe("A1 groessere Position = geringere Kosten in R",
       k300["kosten_r"] > k1000["kosten_r"] > k2000["kosten_r"],
       f"{k300['kosten_r']:.3f} > {k1000['kosten_r']:.3f} > {k2000['kosten_r']:.3f}")
pruefe("A2 300 EUR liegt deutlich unter dem alten Pauschalwert 0,400",
       k300["kosten_r"] < 0.30, f"{k300['kosten_r']:.3f}")
pruefe("A3 2.000 EUR kostet nur noch einen Bruchteil",
       k2000["kosten_r"] < 0.15, f"{k2000['kosten_r']:.3f}")

# Die Fixgebuehr muss exakt eingehen: 2 EUR auf 1000 EUR = 0,2 % + 0,5 % Spread
erwartet = (2.0 / 1000.0 + 2 * 0.0025) / STOP
pruefe("A4 Rechnung exakt nachvollziehbar",
       abs(k1000["kosten_r"] - erwartet) < 1e-9, f"{k1000['kosten_r']:.4f} = {erwartet:.4f}")

ohne = kosten_in_r(STOP, "aktien", 10.0)
mit_ref = kosten_in_r(STOP, "aktien", 10.0, position_eur=_KOSTEN_REFERENZ_POSITION_EUR)
pruefe("A5 ohne Angabe wird die Referenzgroesse genommen",
       abs(ohne["kosten_r"] - mit_ref["kosten_r"]) < 1e-9,
       f"Referenz {_KOSTEN_REFERENZ_POSITION_EUR:.0f} EUR")
pruefe("A6 und das steht in der Begruendung", "Referenzgroesse" in ohne["basis"])

print("\nB) KRYPTO - prozentual, Positionsgroesse irrelevant")
c300 = kosten_in_r(STOP, "krypto", 10.0, position_eur=300)
c2000 = kosten_in_r(STOP, "krypto", 10.0, position_eur=2000)
pruefe("B1 Positionsgroesse aendert nichts",
       abs(c300["kosten_r"] - c2000["kosten_r"]) < 1e-12, f"{c300['kosten_r']:.3f}")
pruefe("B2 Bitpanda-Spread wird benannt", "Bitpanda-Krypto" in c300["basis"])

print("\nC) HEBEL - unveraendert, an echten Positionen belegt")
h = kosten_in_r(STOP, "hebel", 10.0, hebel=3.0)
pruefe("C1 Hebel weiterhin belegt", h["belegt"] is True, h["basis"][:50])
pruefe("C2 Hebel unabhaengig von der Positionsgroesse",
       abs(h["kosten_r"] - kosten_in_r(STOP, "hebel", 10.0, hebel=3.0,
                                       position_eur=5000)["kosten_r"]) < 1e-12)
pruefe("C3 Wert unveraendert gegenueber vorher", abs(h["kosten_r"] - 0.28) < 0.001,
       f"{h['kosten_r']:.3f}")

print("\nD) HEDGE - laufende ETP-Gebuehr kommt dazu")
h10 = kosten_in_r(STOP, TIER_HEDGE, 10.0, position_eur=500)
h180 = kosten_in_r(STOP, TIER_HEDGE, 180.0, position_eur=500)
pruefe("D1 laengeres Halten kostet mehr",
       h180["kosten_r"] > h10["kosten_r"],
       f"10 Tage {h10['kosten_r']:.3f} -> 180 Tage {h180['kosten_r']:.3f}")
pruefe("D2 bei einer gewoehnlichen Aktie NICHT",
       abs(kosten_in_r(STOP, "aktien", 180.0, position_eur=500)["kosten_r"]
           - kosten_in_r(STOP, "aktien", 10.0, position_eur=500)["kosten_r"]) < 1e-12)
pruefe("D3 ETP-Gebuehr wird benannt", "ETP" in h180["basis"], h180["basis"][-40:])

print("\nE) EHRLICHKEIT DER ANNAHMEN")
pruefe("E1 Boerse als unbelegt gekennzeichnet", ohne["belegt"] is False)
pruefe("E2 Krypto als unbelegt gekennzeichnet", c300["belegt"] is False)
pruefe("E3 nur Hebel ist belegt", h["belegt"] is True)
pruefe("E4 Positionsgroesse wird zurueckgemeldet",
       k1000["position_eur"] == 1000 and c300["position_eur"] is None,
       "Krypto meldet keine - sie waere dort bedeutungslos")

print("\nF) ROBUSTHEIT")
pruefe("F1 ohne Stop-Abstand kein Ergebnis",
       kosten_in_r(None, "aktien", 10.0, position_eur=500)["kosten_r"] is None)
pruefe("F2 Positionsgroesse 0 faellt auf die Referenz zurueck",
       abs(kosten_in_r(STOP, "aktien", 10.0, position_eur=0)["kosten_r"]
           - ohne["kosten_r"]) < 1e-12)
pruefe("F3 unbekannter Tier faellt auf Krypto-Logik",
       kosten_in_r(STOP, "voellig_neu", 10.0)["kosten_r"] is not None)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
