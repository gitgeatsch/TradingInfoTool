"""Die Statusseite darf ihre teuren Aggregate nicht je Abruf neu rechnen.

ANLASS (09.08., Betriebsvorfall). Das Notebook stand dauerhaft bei ~94 % CPU,
`python.exe` allein bei 70,9 %, ohne einen einzigen Fehler im Log. Ursache war
kein Defekt, sondern Arbeit: `remote/server.py` ruft die Seite alle zwei
Sekunden ab (`setInterval(refreshStatus, 2000)`), und `build_status()` rechnete
dabei jedes Mal alles neu - gemessen 1,39 s je Abruf am Desktop, auf dem
Notebook ein Vielfaches davon. Sobald ein Abruf laenger dauert als der Takt,
ueberlappen die Anfragen und verstaerken sich gegenseitig.

WAS DIESER TEST SICHERT, und warum jeder Punkt eine Gegenprobe hat:

  A  Zwischenspeicher greift             - mit Gegenprobe OHNE Cache
  B  Frist laeuft ab                     - alte Werte bleiben nicht ewig stehen
  C  Gleichzeitige Abrufe rechnen EINMAL - das ist der eigentliche Fix
  D  Fehler-Pause verhindert den Kreis   - mit Gegenprobe OHNE Pause

Punkt C ist der Kern: ein reiner Zwischenspeicher ohne Sperre haette den
Vorfall NICHT verhindert. Waehrend die erste Berechnung laeuft, ist der Cache
noch leer - ohne Sperre startet jede eintreffende Anfrage ihre eigene.

Punkt D bildet den 06.08. nach: dort erzeugte eine dauerhaft scheiternde
Berechnung 1.085 Fehlschlaege, weil `wert` auf None blieb und damit nie als
frisch galt.

Jeder Waechter laeuft gegen den KAPUTTEN Zustand (Methodik-Nachtrag 09.08.,
Punkt 5) - ein Test, der nur auf sauberem Code besteht, beweist nichts.
"""
import threading
import time

import remote.status as rs

fehler = []


def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)


# --- A) Der Zwischenspeicher greift, und ohne ihn greift er nicht -----------
rs.leere_aggregat_cache()
aufrufe = {"n": 0}


def teuer():
    aufrufe["n"] += 1
    return {"wert": aufrufe["n"]}


for _ in range(5):
    rs._zwischengespeichert("test_a", teuer)
pruefe("A1 fuenf Abrufe -> eine Berechnung", aufrufe["n"] == 1, f"{aufrufe['n']}x gerechnet")

# Gegenprobe: dieselbe Funktion OHNE Zwischenspeicher. Zeigt sie hier nicht 5,
# misst der Test seinen eigenen Aufbau statt der Sache.
aufrufe["n"] = 0
for _ in range(5):
    teuer()
pruefe("A2 Gegenprobe ohne Cache -> fuenf Berechnungen", aufrufe["n"] == 5,
       f"{aufrufe['n']}x gerechnet")

# --- B) Die Frist laeuft ab -------------------------------------------------
rs.leere_aggregat_cache()
aufrufe["n"] = 0
rs._zwischengespeichert("test_b", teuer, sekunden=0.05)
time.sleep(0.08)
rs._zwischengespeichert("test_b", teuer, sekunden=0.05)
pruefe("B1 nach Ablauf der Frist wird neu gerechnet", aufrufe["n"] == 2,
       f"{aufrufe['n']}x gerechnet")

# --- C) Gleichzeitige Abrufe rechnen EINMAL ---------------------------------
# Der eigentliche Vorfall: 2-Sekunden-Takt, Rechenzeit darueber. Die langsame
# Funktion haelt hier 0,3 s, waehrend zehn "Anfragen" gleichzeitig eintreffen.
rs.leere_aggregat_cache()
langsam_n = {"n": 0}


def langsam():
    langsam_n["n"] += 1
    time.sleep(0.3)
    return "fertig"


ergebnisse = []
threads = [threading.Thread(
    target=lambda: ergebnisse.append(rs._zwischengespeichert("test_c", langsam)))
    for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
pruefe("C1 zehn gleichzeitige Abrufe -> eine Berechnung", langsam_n["n"] == 1,
       f"{langsam_n['n']}x gerechnet")
pruefe("C2 alle zehn bekommen das Ergebnis", ergebnisse == ["fertig"] * 10,
       f"{len(ergebnisse)} Ergebnisse")

# Gegenprobe: ohne Sperre wuerden alle zehn rechnen.
langsam_n["n"] = 0
threads = [threading.Thread(target=langsam) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
pruefe("C3 Gegenprobe ohne Sperre -> zehn Berechnungen", langsam_n["n"] == 10,
       f"{langsam_n['n']}x gerechnet")

# --- D) Fehler-Pause verhindert den Neustart-Kreis ---------------------------
import agent.krypto.backward_tracking as bt

versuche = {"n": 0}
original = bt.compute_systemguete


def kaputt(conn, watchlist=None, *a, **k):
    versuche["n"] += 1
    raise RuntimeError("simulierter Dauerfehler wie am 06.08.")


def _warte_auf_ruhe():
    for _ in range(100):
        if not rs._SYSTEMGUETE_CACHE["laeuft"]:
            return
        time.sleep(0.02)


bt.compute_systemguete = kaputt
try:
    # MIT Pause: 20 Statusabrufe, wie sie in 40 Sekunden Seitenlauf anfallen
    rs._SYSTEMGUETE_CACHE.update({"stand": 0.0, "wert": None, "laeuft": False,
                                  "fehler_stand": 0.0})
    versuche["n"] = 0
    for _ in range(20):
        rs._get_systemguete(None, [])
        _warte_auf_ruhe()
    mit_pause = versuche["n"]
    pruefe("D1 dauerhafter Fehler -> genau EIN Versuch trotz 20 Abrufen",
           mit_pause == 1, f"{mit_pause} Versuche")

    # Gegenprobe: Pause auf 0 - das ist exakt der Zustand vor dem Fix.
    alt = rs._SYSTEMGUETE_FEHLER_PAUSE_SEKUNDEN
    rs._SYSTEMGUETE_FEHLER_PAUSE_SEKUNDEN = 0
    rs._SYSTEMGUETE_CACHE.update({"stand": 0.0, "wert": None, "laeuft": False,
                                  "fehler_stand": 0.0})
    versuche["n"] = 0
    for _ in range(20):
        rs._get_systemguete(None, [])
        _warte_auf_ruhe()
    ohne_pause = versuche["n"]
    rs._SYSTEMGUETE_FEHLER_PAUSE_SEKUNDEN = alt
    pruefe("D2 Gegenprobe ohne Pause -> ein Versuch JE Abruf (der 06.08.-Kreis)",
           ohne_pause == 20, f"{ohne_pause} Versuche")

    # Und die Pause darf den Erfolgsfall nicht blockieren.
    bt.compute_systemguete = lambda conn, watchlist=None, *a, **k: {"ok": True}
    rs._SYSTEMGUETE_CACHE.update({"stand": 0.0, "wert": None, "laeuft": False,
                                  "fehler_stand": 0.0})
    rs._get_systemguete(None, [])
    _warte_auf_ruhe()
    pruefe("D3 nach dem Fix wird wieder ein Wert geliefert",
           rs._SYSTEMGUETE_CACHE["wert"] == {"ok": True},
           str(rs._SYSTEMGUETE_CACHE["wert"]))
finally:
    bt.compute_systemguete = original
    rs.leere_aggregat_cache()

# --- E) DER WAECHTER: kein Getter darf unbemerkt ungecacht sein -------------
#
# Das ist der eigentliche Schutz. A bis D sichern, dass der Zwischenspeicher
# funktioniert - E sichert, dass ihn niemand vergisst. Am 07.08. kamen drei
# Karten an einem Tag dazu, keine fuer sich auffaellig, zusammen schoben sie
# den Abruf ueber die Schwelle. Genau das kann ab jetzt nicht mehr passieren,
# ohne dass dieser Test rot wird.
alle = [n for n in dir(rs) if n.startswith("_get_")]
pruefe("E1 es gibt ueberhaupt Getter zu pruefen (Leerlauf-Wache)", len(alle) >= 20,
       f"{len(alle)} gefunden")

unversorgt = []
for name in alle:
    fn = getattr(rs, name)
    if not callable(fn):
        continue
    if getattr(fn, "_ist_gecacht", False):
        continue
    if name in rs._LIVE_GETTER:
        continue
    unversorgt.append(name)
pruefe("E2 jeder Getter ist entweder @_gecacht oder in _LIVE_GETTER",
       not unversorgt, ", ".join(unversorgt) if unversorgt else "alle versorgt")

# Gegenprobe: ein frisch dazugekommener Getter MUSS auffallen. Ohne diese
# Zeile wuerde E2 auch bestehen, wenn die Pruefung selbst nichts finden kann.
rs._get_frisch_erfundene_karte = lambda conn: {"neu": True}
try:
    neu_unversorgt = [
        n for n in dir(rs)
        if n.startswith("_get_") and callable(getattr(rs, n))
        and not getattr(getattr(rs, n), "_ist_gecacht", False)
        and n not in rs._LIVE_GETTER
    ]
    pruefe("E3 Gegenprobe: eine neue, unversorgte Karte wird erkannt",
           neu_unversorgt == ["_get_frisch_erfundene_karte"],
           ", ".join(neu_unversorgt))
finally:
    del rs._get_frisch_erfundene_karte

# _LIVE_GETTER darf keine Namen fuehren, die es nicht mehr gibt - sonst
# schuetzt der Waechter eine Karte, die laengst umbenannt wurde.
verwaist = [n for n in rs._LIVE_GETTER if not hasattr(rs, n)]
pruefe("E4 _LIVE_GETTER enthaelt keine verwaisten Namen",
       not verwaist, ", ".join(verwaist) if verwaist else "keine")

# --- F) Die Laufzeit-Wache meldet sich ---------------------------------------
import logging

gefangen = []


class _Sammler(logging.Handler):
    def emit(self, record):
        gefangen.append(record.getMessage())


rs.logger.addHandler(_Sammler())
alt_schwelle = rs._BUILD_STATUS_WARNSCHWELLE_SEKUNDEN
alt_roh = rs._build_status_roh
try:
    rs._build_status_roh = lambda *a, **k: (time.sleep(0.05), "status")[1]

    rs._BUILD_STATUS_WARNSCHWELLE_SEKUNDEN = 10.0
    gefangen.clear()
    rs.build_status(None, [], None)
    pruefe("F1 unterhalb der Schwelle wird nicht gewarnt", not gefangen,
           f"{len(gefangen)} Meldungen")

    rs._BUILD_STATUS_WARNSCHWELLE_SEKUNDEN = 0.01
    gefangen.clear()
    rs.build_status(None, [], None)
    pruefe("F2 oberhalb der Schwelle wird gewarnt", len(gefangen) == 1,
           gefangen[0][:60] if gefangen else "keine Meldung")
finally:
    rs._build_status_roh = alt_roh
    rs._BUILD_STATUS_WARNSCHWELLE_SEKUNDEN = alt_schwelle

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
raise SystemExit(1 if fehler else 0)
