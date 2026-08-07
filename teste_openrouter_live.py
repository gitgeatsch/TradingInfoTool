"""Live-Test OpenRouter gegen Z.ai auf DENSELBEN Faktensaetzen (07.08.2026).

ZWECK: eine Ja/Nein-Entscheidung, BEVOR Geld fliesst und BEVOR etwas in den
Produktivbetrieb kommt. Vier Fragen, in dieser Reihenfolge - die spaeteren
lohnen sich nur, wenn die frueheren tragen:

  1. ERREICHBARKEIT  Antwortet der :free-Endpunkt ueberhaupt? Die Privacy-
                     Schalter nehmen Endpunkte aus dem Routing ("publish
                     prompts" ist bewusst aus), das kann genau dieses Modell
                     betreffen.
  2. FORMAT          Kommt gueltiges JSON in UNSEREM Schema? An dieser
                     Anforderung ist Groqs 8B strukturell gescheitert - ein
                     Modell, das gut klingt, aber `bewertung` weglaesst, ist
                     fuer die Pipeline wertlos.
  3. TEMPO           Wie lange dauert ein Call? Die Gegenpruefung laeuft im
                     Hintergrund-Thread, aber 90 s je Signal waeren zu viel.
  4. URTEIL          Stimmen die Konsistenz-Urteile mit Z.ai ueberein - und wo
                     nicht? DAS ist der eigentliche Wert. Ein Anbieter, der
                     zwar antwortet, aber systematisch anders urteilt, ist
                     keine Redundanz, sondern eine zweite Meinung ohne
                     Grundlage.

LAEUFT GEGEN EINE DB-KOPIE, nie gegen die Produktiv-DB (stehende Vorgabe). Die
Faktensaetze sind ECHT - aus gespeicherten Signalen geladen, nicht erfunden:
ein Test mit ausgedachten Fakten prueft den Parser, nicht das Modell.

AUFRUF:
    python teste_openrouter_live.py            # 8 Faelle, beide Anbieter
    python teste_openrouter_live.py 20         # mehr Faelle
    python teste_openrouter_live.py 5 nur-or   # nur OpenRouter (spart Z.ai-Kontingent)

KOSTEN: keine. Der Client weist jede Modell-ID ohne ':free' ab. Das freie
Tageskontingent liegt ohne Aufladung bei 50 Anfragen - ein Lauf mit 8 Faellen
verbraucht 8 davon.
"""
import json
import os
import pathlib
import shutil
import sys
import time
from collections import Counter

SCRATCH = pathlib.Path(os.environ.get("TEMP", ".")) / "tit_openrouter_test.db"
ANZAHL = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8
NUR_OPENROUTER = "nur-or" in sys.argv

shutil.copy("data/tradinginfotool.db", SCRATCH)
import database.db as db
db.DB_PATH = SCRATCH
conn = db.get_connection()

from agent.krypto.gegenpruefung import baue_fakten, pruefe_konsistenz

api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("FEHLT: OPENROUTER_API_KEY nicht in der Umgebung. In die .env eintragen "
          "und die Shell neu starten.")
    sys.exit(1)

from api.openrouter import DEFAULT_MODEL, OpenRouterClient
or_client = OpenRouterClient(api_key=api_key)

zai_key = os.environ.get("ZAI_API_KEY")
zai_client = None
if zai_key and not NUR_OPENROUTER:
    from api.zai import ZaiClient
    zai_client = ZaiClient(api_key=zai_key)

# ECHTE Faelle: Signale mit Begruendungstext, neueste zuerst.
zeilen = conn.execute(
    "SELECT symbol, action, confidence_pct, short_reasoning, created_at "
    "FROM signals WHERE short_reasoning IS NOT NULL AND length(short_reasoning) > 80 "
    "ORDER BY created_at DESC LIMIT ?", (ANZAHL,)
).fetchall()
if len(zeilen) < ANZAHL:
    zeilen = list(zeilen) + list(conn.execute(
        "SELECT symbol, action, confidence_pct, short_reasoning, created_at "
        "FROM hebel_signals WHERE short_reasoning IS NOT NULL "
        "AND length(short_reasoning) > 80 ORDER BY created_at DESC LIMIT ?",
        (ANZAHL - len(zeilen),)).fetchall())

print(f"Modell: {DEFAULT_MODEL}")
print(f"Faelle: {len(zeilen)} echte Signale aus der DB-Kopie")
print(f"Vergleich mit Z.ai: {'ja' if zai_client else 'nein'}\n")
if not zeilen:
    print("Keine Signale mit Begruendungstext in der Kopie - Test nicht moeglich.")
    sys.exit(1)

PFLICHTFELDER = ("bewertung",)


def _bewerte(antwort, dauer, fehler):
    if fehler is not None:
        return {"ok": False, "grund": str(fehler)[:120], "dauer": dauer, "urteil": None}
    if antwort is None:
        return {"ok": False, "grund": "kein Ergebnis (None)", "dauer": dauer, "urteil": None}
    fehlend = [f for f in PFLICHTFELDER if f not in antwort]
    if fehlend:
        return {"ok": False, "grund": f"Pflichtfeld fehlt: {fehlend}", "dauer": dauer,
                "urteil": None}
    return {"ok": True, "grund": None, "dauer": dauer, "urteil": antwort.get("bewertung")}


ergebnisse = []
for i, zeile in enumerate(zeilen, 1):
    # baue_fakten() nimmt die Einzelwerte, keinen conn - die Indikatoren stehen
    # im gespeicherten Signal. Was fehlt, bleibt None; die Funktion ist darauf
    # ausgelegt (der Gegenpruefungs-Faktensatz ist bewusst luecken-tolerant).
    fakten = baue_fakten(
        zeile["symbol"], zeile["action"], zeile["confidence_pct"],
        rsi=None, trend_label=None, regime=None, funding_rate_stunde=None,
        confluence_bullish=0, confluence_bearish=0, confluence_neutral=0,
        optionsmarkt_skew=None,
    )
    text = zeile["short_reasoning"]
    zeile_ergebnis = {"symbol": zeile["symbol"], "action": zeile["action"]}

    for name, client in (("openrouter", or_client), ("zai", zai_client)):
        if client is None:
            continue
        start = time.monotonic()
        fehler = None
        antwort = None
        try:
            antwort = pruefe_konsistenz(client, fakten, text)
        except Exception as exc:  # noqa: BLE001
            fehler = exc
        zeile_ergebnis[name] = _bewerte(antwort, time.monotonic() - start, fehler)

    ergebnisse.append(zeile_ergebnis)
    o = zeile_ergebnis.get("openrouter", {})
    z = zeile_ergebnis.get("zai", {})
    print(f"{i:>2}. {zeile['symbol']:<10} {zeile['action']:<12} "
          f"OR: {'OK ' if o.get('ok') else 'FEHL'} {o.get('urteil') or o.get('grund', '')[:40]:<28} "
          f"{o.get('dauer', 0):>5.1f}s"
          + (f"   Zai: {'OK ' if z.get('ok') else 'FEHL'} {str(z.get('urteil') or '')[:16]:<16} "
             f"{z.get('dauer', 0):>5.1f}s" if z else ""))

print("\n" + "=" * 74)
o_ok = [e["openrouter"] for e in ergebnisse if e.get("openrouter", {}).get("ok")]
o_alle = [e["openrouter"] for e in ergebnisse if "openrouter" in e]
print(f"1) ERREICHBARKEIT + 2) FORMAT: {len(o_ok)} von {len(o_alle)} Aufrufen lieferten "
      f"gueltiges Schema")
if len(o_ok) < len(o_alle):
    for g, n in Counter(e["grund"] for e in o_alle if not e["ok"]).most_common():
        print(f"     {n}x  {g}")
if o_ok:
    d = sorted(e["dauer"] for e in o_ok)
    print(f"3) TEMPO: Median {d[len(d)//2]:.1f} s, langsamster {d[-1]:.1f} s")

vergleichbar = [e for e in ergebnisse
                if e.get("openrouter", {}).get("ok") and e.get("zai", {}).get("ok")]
if vergleichbar:
    gleich = sum(1 for e in vergleichbar if e["openrouter"]["urteil"] == e["zai"]["urteil"])
    print(f"4) URTEIL: {gleich} von {len(vergleichbar)} Faellen stimmen mit Z.ai ueberein")
    for e in vergleichbar:
        if e["openrouter"]["urteil"] != e["zai"]["urteil"]:
            print(f"     {e['symbol']:<10} OR='{e['openrouter']['urteil']}'  "
                  f"Zai='{e['zai']['urteil']}'")
    print("\n   Abweichungen sind NICHT automatisch ein Fehler - sie sind der Anlass,")
    print("   sich die beiden Begruendungen anzusehen. Wer recht hat, entscheidet der Fall.")
else:
    print("4) URTEIL: kein Vergleich moeglich (Z.ai nicht gelaufen oder keine gueltigen Paare)")

print("\nENTSCHEIDUNGSHILFE")
if len(o_ok) == 0:
    print("  NEIN. Der Endpunkt liefert nichts Verwertbares - vermutlich ist das Modell")
    print("  ueber die Privacy-Einstellungen nicht erreichbar. Anderes :free-Modell in")
    print("  api/openrouter.py::DEFAULT_MODEL probieren, NICHT den Schalter umlegen.")
elif len(o_ok) < len(o_alle) * 0.8:
    print(f"  UNKLAR. Nur {len(o_ok)}/{len(o_alle)} brauchbar - fuer eine Gegenpruefung zu")
    print("  unzuverlaessig. Anderes Modell testen, bevor ueber Geld geredet wird.")
else:
    print("  JA, technisch tragfaehig. Naechster Schritt ist die Frage, ob OpenRouter")
    print("  Z.ai ERSETZT oder ERGAENZT - dafuer ist Punkt 4 der Massstab, nicht das Tempo.")

conn.close()
try:
    SCRATCH.unlink()
except Exception:
    pass
