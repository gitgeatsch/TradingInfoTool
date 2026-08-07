"""Prueft die Hedge-Risikofaktoren (W2) und die Zonenwache (07.08.2026).

DER ANLASS FUER DIE ZONENWACHE, am Export gemessen: 9 von 11 auswertbaren
Hedge-Kaufsignalen hatten Stop UEBER und Ziel UNTER dem Einstieg - bei einer
KAUFEN-Empfehlung. Das Modell denkt in der Marktrichtung ("der Index soll
fallen") statt in der Instrumentenrichtung ("wir kaufen ein inverses Produkt,
das steigt, wenn der Index faellt").
"""
from types import SimpleNamespace

from agent.hedge.pipeline import _pruefe_hedge_zonen, compute_risikofaktoren_hedge

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

def regime(vix=None, baer=False):
    return SimpleNamespace(vix_wert=vix, equities_baermarkt_aktiv=baer)

EXPOSURE = {"aktuelle_hedge_abdeckung_prozent": 12.0,
            "ziel_hedge_abdeckung_max_prozent": 30.0}

print("A) ZONENWACHE - der echte Fall aus dem Betrieb")
# DBPK 06.08.: Entry 0,1217 / Stop 0,1565 / Ziel 0,0870
verdreht = {"action": "NACHKAUFEN",
            "entry": {"usd_von": 0.1217}, "stop_loss": {"usd_von": 0.1565},
            "take_profit": {"usd_von": 0.0870}}
hinweis = _pruefe_hedge_zonen(verdreht)
pruefe("A1 verdrehte Zonen erkannt", hinweis is not None, (hinweis or "")[:70])
pruefe("A2 Zonen verworfen", verdreht["stop_loss"] == {} and verdreht["take_profit"] == {})
pruefe("A3 Empfehlung bleibt bestehen", verdreht["action"] == "NACHKAUFEN")
pruefe("A4 Entry bleibt erhalten", verdreht["entry"]["usd_von"] == 0.1217)

# 3QSS 06.08. 17:02 war korrekt: Entry 1,4338 / Stop 1,2166 / Ziel 1,7380
korrekt = {"action": "NACHKAUFEN",
           "entry": {"usd_von": 1.4338}, "stop_loss": {"usd_von": 1.2166},
           "take_profit": {"usd_von": 1.7380}}
pruefe("A5 korrekte Zonen bleiben unangetastet",
       _pruefe_hedge_zonen(korrekt) is None
       and korrekt["stop_loss"]["usd_von"] == 1.2166)

# HALTEN wird nicht geprueft - dort sind Zonen ohnehin gegenstandslos
halten = {"action": "HALTEN", "entry": {"usd_von": 1.0},
          "stop_loss": {"usd_von": 2.0}, "take_profit": {"usd_von": 0.5}}
pruefe("A6 HALTEN wird nicht geprueft", _pruefe_hedge_zonen(halten) is None)

# Fehlende Zonen sind kein Fehlerfall
leer = {"action": "KAUFEN", "entry": {}, "stop_loss": {}, "take_profit": {}}
pruefe("A7 fehlende Zonen ohne Absturz", _pruefe_hedge_zonen(leer) is None)

print("\nB) RISIKOFAKTOREN - die umgekehrte Wirkrichtung")
def namen(f):
    return [x.name for x in f]

f_teuer = compute_risikofaktoren_hedge("NACHKAUFEN", EXPOSURE, regime(vix=32.0), 20.0, 3.0, False)
pruefe("B1 hoher VIX = teure Versicherung (negativ)",
       "Versicherung ist teuer (VIX)" in namen(f_teuer)
       and next(x for x in f_teuer if "teuer" in x.name).bewertung == "negativ")

f_guenstig = compute_risikofaktoren_hedge("NACHKAUFEN", EXPOSURE, regime(vix=13.0), 20.0, 3.0, False)
pruefe("B2 niedriger VIX = guenstige Versicherung (POSITIV)",
       next((x.bewertung for x in f_guenstig if "guenstig" in x.name), None) == "positiv")

f_baer = compute_risikofaktoren_hedge("NACHKAUFEN", EXPOSURE, regime(vix=20.0, baer=True), 20.0, 3.0, False)
pruefe("B3 laufender Baerenmarkt = spaet dran (negativ), nicht positiv",
       next((x.bewertung for x in f_baer if "Einbruch" in x.name), None) == "negativ")

f_bull = compute_risikofaktoren_hedge("NACHKAUFEN", EXPOSURE, regime(vix=20.0), 65.0, 3.0, False)
pruefe("B4 hohe Bull-Wahrscheinlichkeit ist das Gegenszenario",
       "Gegenszenario Aufwaertsmarkt" in namen(f_bull))

pruefe("B5 Volatilitaets-Drag bei gehebeltem Produkt",
       "Volatilitaets-Drag" in namen(f_teuer))

voll = {"aktuelle_hedge_abdeckung_prozent": 27.0, "ziel_hedge_abdeckung_max_prozent": 30.0}
f_voll = compute_risikofaktoren_hedge("NACHKAUFEN", voll, regime(vix=20.0), 20.0, 3.0, False)
pruefe("B6 fast volle Abdeckung warnt vor Ueberhedge",
       "Absicherung weitgehend aufgebaut" in namen(f_voll))
f_leer = compute_risikofaktoren_hedge("NACHKAUFEN", EXPOSURE, regime(vix=20.0), 20.0, 3.0, False)
pruefe("B7 bei 12 von 30 % keine Ueberhedge-Warnung",
       "Absicherung weitgehend aufgebaut" not in namen(f_leer))

f_halten = compute_risikofaktoren_hedge("HALTEN", EXPOSURE, regime(vix=32.0), 20.0, 3.0, True)
pruefe("B8 bei HALTEN nur der Kontextfaktor",
       len(f_halten) == 1 and f_halten[0].ist_kontext,
       str(namen(f_halten)))

f_zonen = compute_risikofaktoren_hedge("NACHKAUFEN", EXPOSURE, regime(vix=20.0), 20.0, 3.0,
                                       False, zonen_hinweis="Zonen verworfen: Test")
pruefe("B9 verworfene Zonen erscheinen als Faktor", "Zonen unbrauchbar" in namen(f_zonen))
f_zonen_halten = compute_risikofaktoren_hedge("HALTEN", EXPOSURE, regime(), None, None, False,
                                              zonen_hinweis="Zonen verworfen: Test")
pruefe("B10 auch bei HALTEN sichtbar", "Zonen unbrauchbar" in namen(f_zonen_halten))

print("\nC) KEIN LEERER ABSCHNITT MEHR IN DER MAIL")
from ui.formatting import risikofaktoren_hinweis
sig = SimpleNamespace(symbol="3QSS", action="NACHKAUFEN", original_action="NACHKAUFEN")
pruefe("C1 mit Faktoren wird der Text durchgereicht",
       risikofaktoren_hinweis(sig, "▼ Volatilitaets-Drag: ...") == "▼ Volatilitaets-Drag: ...")
pruefe("C2 ohne Faktoren weiterhin ehrlicher Hinweis",
       "Absicherungs" in risikofaktoren_hinweis(sig, ""))

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
