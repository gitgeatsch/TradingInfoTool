# -*- coding: utf-8 -*-
"""Aendert die kleinere Grundgesamtheit das FUENFTEL - und bei wie vielen?

⚠️ DIE FRAGE IST MESSBAR, NICHT ZU ENTSCHEIDEN (Nutzerhinweis 20.09.2026:
*„du kommst hier immer mit einer Entscheidung zur Grundgesamtheit auf mich
zu, ist das eine Entscheidung ...?"*). Ich hatte sie dreimal als Entscheidung
vorgelegt - das ist ein Verstoss gegen die eigene Prueffrage ,BEWERTUNG oder
FAKT`.

DER AUFBAU. Zweimal dieselbe Rechnung mit dem ECHTEN Produktionscode
(`marktrang.schnitt_werte`, `_rang`, `_fuenftel`), nur mit verschiedener
Messdatei:

    VOLL     data/messdaten.db      - die volle Messbasis am Desktop
    BETRIEB  nb_messdaten.db        - die Betriebskopie, wie sie das
                                      Notebook baut (500 Tage, nur TRADING)

Gezaehlt wird, bei wie vielen Werten sich das FUENFTEL aendert - denn mit
dem Fuenftel rechnet die Bewertung, nicht mit dem Rohwert.

⚠️ EINSCHRAENKUNG, die dazugehoert: die Ergaenzung aus der Produktions-DB
nimmt hier die DESKTOP-Datei. Am Notebook steht dort eine andere - die
Struktur der Frage ist dieselbe, die Symbolmenge leicht verschieden.

Nur lesend. Zwei Binance-Preisabrufe.
"""
from __future__ import annotations

import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
import os

os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR
import extract_notebook_diagnose as X

# ⚠️ Der Pfad der Betriebskopie ist ein ARGUMENT, keine Nachbarschaft:
# sie liegt am Notebook unter `data/`, hier beim Nachbau irgendwo.
#   python messe_grundgesamtheit.py <pfad-zur-betriebskopie>
BETRIEB = (sys.argv[1] if len(sys.argv) > 1
           else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "nb_messdaten.db"))


def lauf(datei: str) -> dict:
    MR.SCHNITT_MESSDB = datei
    MR.MESSBASIS["schnitt"] = (datei, MR.MESSBASIS["schnitt"][1])
    MR._SCHNITT_ZWISCHEN.pop("werte", None)
    MR._MESSBASIS_ZWISCHEN.pop("schnitt", None)
    w = MR.schnitt_werte()
    r = MR._rang(w)
    return {"werte": w, "rang": r,
            "fuenftel": {s: MR._fuenftel(r.get(s)) for s in w}}


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("AENDERT DIE KLEINERE GRUNDGESAMTHEIT DAS FUENFTEL?")
    print("=" * 100)
    if not os.path.exists(BETRIEB):
        print("  !! %s fehlt - erst die Betriebskopie bauen" % BETRIEB)
        return 1

    voll = lauf("data/messdaten.db")
    betr = lauf(BETRIEB)
    print("  VOLL    %4d Werte im Rang" % len(voll["werte"]))
    print("  BETRIEB %4d Werte im Rang" % len(betr["werte"]))
    gemeinsam = sorted(set(voll["werte"]) & set(betr["werte"]))
    print("  gemeinsam: %d · nur VOLL: %d · nur BETRIEB: %d"
          % (len(gemeinsam), len(set(voll["werte"]) - set(betr["werte"])),
             len(set(betr["werte"]) - set(voll["werte"]))))

    # ---- 1  Ueber ALLE gemeinsamen Werte ------------------------------
    dreher = [s for s in gemeinsam
              if voll["fuenftel"][s] != betr["fuenftel"][s]]
    print()
    print("  %s" % ("-" * 96))
    print("  (1) UEBER ALLE %d GEMEINSAMEN WERTE" % len(gemeinsam))
    print("      Fuenftel geaendert: %d von %d = %.1f %%"
          % (len(dreher), len(gemeinsam),
             100.0 * len(dreher) / max(1, len(gemeinsam))))

    # ---- 2  Ueber die Werte, um die es geht ---------------------------
    try:
        d = X.lies()
        kette = [z["symbol"] for z in
                 d["terminmarkt_und_umlaufmenge"]["leser"]["je_wert"]]
    except Exception as exc:                                 # noqa: BLE001
        print("      (Kettenwerte nicht lesbar: %s)" % exc)
        kette = []
    in_beiden = [s for s in kette if s in voll["fuenftel"]
                 and s in betr["fuenftel"]]
    kd = [s for s in in_beiden
          if voll["fuenftel"][s] != betr["fuenftel"][s]]
    print()
    print("  (2) UEBER DIE %d KRYPTOWERTE DER KETTE (%d davon im Rang)"
          % (len(kette), len(in_beiden)))
    print("      Fuenftel geaendert: %d von %d" % (len(kd), len(in_beiden)))
    if kd:
        print()
        print("      %-10s %-10s %-10s %s" % ("Symbol", "VOLL", "BETRIEB",
                                              "Abstand zum Schnitt"))
        for s in kd:
            print("      %-10s %-10s %-10s %+.4f"
                  % (s, voll["fuenftel"][s], betr["fuenftel"][s],
                     voll["werte"][s]))

    # ---- 3  Das Urteil ------------------------------------------------
    print()
    print("  %s" % ("=" * 96))
    if not in_beiden:
        print("  ⚠️ KEIN URTEIL - keine Kettenwerte im Rang")
    elif not kd:
        print("  ➔ ✔✔ KEINE ENTSCHEIDUNG NOETIG: bei KEINEM der %d "
              "Kettenwerte aendert sich" % len(in_beiden))
        print("     das Fuenftel. Die kleinere Grundgesamtheit ist fuer die "
              "Bewertung folgenlos.")
    else:
        print("  ➔ ⚠️ %d von %d Kettenwerten wechseln das Fuenftel - die "
              "Grundgesamtheit" % (len(kd), len(in_beiden)))
        print("     ist NICHT folgenlos. Jetzt ist es eine Entscheidung.")
    print()
    print("  ⚠️ Die Ergaenzung aus der Produktions-DB stammt hier vom "
          "DESKTOP - am Notebook")
    print("     steht dort eine andere Datei. Struktur gleich, Symbolmenge "
          "leicht verschieden.")
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
