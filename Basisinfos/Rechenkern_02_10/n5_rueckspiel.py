"""N5 - Rueckspiel der LLM-Fassung 0.2 (E-80) auf den EINGEFRORENEN N4-Ankern (Voranalyse_Schritt7 §23.20; Nutzer 07.10.2026:
*Ja, pruefen und gegenpruefen* - Rueckspiel statt Schatten im Betrieb, §23.19/§23.20).

    python Basisinfos/Rechenkern_02_10/n5_rueckspiel.py lauf --warte-auf-n4   # startet, sobald N4 beendet ist; setzt fort; wartet aufs Kontingent
    python Basisinfos/Rechenkern_02_10/n5_rueckspiel.py stand                 # Fortschritt, Kontingent - OHNE Trennzahlen
    python Basisinfos/Rechenkern_02_10/n5_rueckspiel.py lauf --ablage <wegwerf> --platzhalter zufall|orakel --kein-warten   # Pruefung

DERSELBE LAEUFER WIE N4 (n4_rueckspiel: Wiederanlauf, Herzschlag-Sperre, Fassungsriegel, Kontingent je Schluessel, Platzhalter),
mit diesen Abweichungen - VORAB FESTGELEGT 07.10.2026, vor dem ersten Aufruf:
  Fassung      0.2 aus dem EINGEFRORENEN Katalog Basisinfos/regel0_llm_0_2_n5.yaml (Prompt 0.2, Lage zur Signalstunde). Ohne Produktion
               (rueckblickend gibt es `open_interest_snapshot` nicht) -> KEIN Terminmarkt-Satz; alles andere wie im Betrieb
  Anker        DIESELBE Entwicklungsmenge in DERSELBEN Reihenfolge wie N4 (pos gleich) -> gepaarter Vergleich 0.2 gegen 0.1e
  Reihenfolge  N4 friert die Eingabe mit sort_keys ein - bei 0.2 stuende der weite Rahmen dann VOR der Lage zur Signalstunde. N5 stellt
               vor jedem Aufruf die Reihenfolge des Betriebs her (geplant, lage_zur_signalstunde, lage_des_werts)
  Plan         K_a (50 Anker, Raten von Wert und Monat - die neuen Bitcoin-Angaben koennten das Datum verraten) -> ENTSCHEID_K nur aus K_a
               (K_b entfaellt: es prueft das WISSEN des Modells ueber benannte Anker, und das ist dasselbe Modell wie in N4, dort bestanden)
               -> T (1.000 Anker, 5 Stimmen) mit den Zwischenentscheiden von N4 (250/500/750, Kandidat D) -> R_v (Anker 0-99, die BLOECKE
               vertauscht: weiter Rahmen zuerst; F3). R_w entfaellt (Rauschboden desselben Modells in N4 gemessen)
  Kontingent   gezaehlt wird die Summe aus N5 UND N4 je Schluessel und Pazifik-Tag (dieselben Schluessel) - sonst rechnete jeder fuer
               sich mit dem vollen Deckel und der NB-Pruefblock (Schluessel 1) ginge leer aus
  Start        mit --warte-auf-n4 erst, wenn N4 'ende' in seiner Ablage hat (R_v von N4 ist die Grundlage von W3)
  Ablage       data/_n5/n5_ablage.db (eigene Ablage, eigenes Log data/_n5/n4_lauf.log - der Name kommt aus dem N4-Laeufer)
Auswertung: n5_auswertung.py (vorab festgelegt, dort beschrieben).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import n4_rueckspiel as N      # noqa: E402  (setzt sys.path und das Arbeitsverzeichnis)
import n4_auswertung as A      # noqa: E402

PROJ = N.PROJ
ABLAGE_N5 = os.path.join(PROJ, "data", "_n5", "n5_ablage.db")
N4_ABLAGE = os.path.join(PROJ, "data", "_n4", "n4_ablage.db")
KATALOG_N5 = os.path.join(os.path.dirname(HIER), "regel0_llm_0_2_n5.yaml")
N_RV = 100
REIHE = ("geplant", "lage_zur_signalstunde", "lage_des_werts")
_N4 = {"pfad": N4_ABLAGE}


def betriebsreihenfolge(e: dict) -> dict:
    """Die Reihenfolge des Betriebs (F3) - unabhaengig davon, wie die eingefrorene Eingabe sortiert ist; unbekannte Schluessel danach."""
    return {**{k: e[k] for k in REIHE if k in e}, **{k: v for k, v in e.items() if k not in REIHE}}


def variante5(teil: str, e: dict, zeile) -> dict:
    e = betriebsreihenfolge(e)
    if teil == "R_v":                                        # die BLOECKE vertauscht: der weite Rahmen vor der Lage zur Signalstunde
        return {k: e[k] for k in ("geplant", "lage_des_werts", "lage_zur_signalstunde", *[x for x in e if x not in REIHE]) if k in e}
    return e


def plan5(c) -> list:
    n = c.execute("SELECT COUNT(*) FROM eingabe").fetchone()[0]
    p = [("K_a", i, 1) for i in range(min(N.N_KA, n))]
    p += [("ENTSCHEID_K", None, 0)]
    for i in range(0, n):
        if i in N.BLICKE:
            p.append(("ENTSCHEID_T%d" % i, None, 0))
        p.append(("T", i, N.STIMMEN))
    p += [("R_v", i, N.STIMMEN) for i in range(min(N_RV, n))]
    return p


def n4_verbraucht(s: int, tag: str) -> int:
    if not os.path.exists(_N4["pfad"]):
        return 0
    c = sqlite3.connect("file:%s?mode=ro" % _N4["pfad"].replace("\\", "/"), uri=True, timeout=30)
    try:
        z = c.execute("SELECT n, erschoepft FROM kontingent WHERE schluessel=? AND tag=?", (s, tag)).fetchone()
    except sqlite3.Error:
        z = None
    finally:
        c.close()
    if z and z[1]:
        return 10 ** 6                                       # N4 hat den Schluessel heute erschoepft gesehen
    return int(z[0]) if z else 0


def frei5(c, s) -> int:
    tag = N.pazifik_tag()
    z = c.execute("SELECT n, erschoepft FROM kontingent WHERE schluessel=? AND tag=?", (s, tag)).fetchone()
    if z and z[1]:
        return 0
    return max(0, N.DECKEL[s] - (z[0] if z else 0) - n4_verbraucht(s, tag))


_entscheide_n4 = A.entscheide


def entscheide5(c, name: str) -> dict:
    """ENTSCHEID_K nur aus K_a (gleiche Schwellen wie N4: Kuerzel >= 2 oder Monat+Jahr >= 6 von 50); die T-Blicke wie N4."""
    if name != "ENTSCHEID_K":
        return _entscheide_n4(c, name)
    import pandas as pd
    roh = pd.read_sql("SELECT s.pos, s.roh, e.symbol, e.signalstunde FROM stimme s JOIN eingabe e ON e.pos = s.pos WHERE s.teil='K_a'", c)
    kz_t = zt = 0
    for r in roh.itertuples():
        try:
            a = json.loads(r.roh)
            a = json.loads(a) if isinstance(a, str) else a
        except Exception:                                    # noqa: BLE001
            continue
        kz_t += str(a.get("kuerzel") or "").upper().replace("USDT", "") == r.symbol.upper()
        zt += str(a.get("jahr")) == r.signalstunde[:4] and str(a.get("monat")).zfill(2) == r.signalstunde[5:7]
    kz = {"kuerzel_treffer": int(kz_t), "zeit_treffer": int(zt), "gefragt": len(roh)}
    if kz_t >= 2 or zt >= 6:
        return {"ergebnis": "STOP-KONTAMINATION (Asset oder Zeitraum erkannt) - P2b: nur noch vorwaerts", "kennzahlen": kz}
    return {"ergebnis": "WEITER (Kontaminationsprobe K_a bestanden)", "kennzahlen": kz}


def einbauen(n4_ablage: str | None = None) -> None:
    """Die N5-Abweichungen in den N4-Laeufer setzen (vor N.lauf)."""
    N.KATALOG_PFAD = KATALOG_N5
    N.plan = plan5
    N.variante = variante5
    N.frei = frei5
    A.entscheide = entscheide5
    if n4_ablage:
        _N4["pfad"] = n4_ablage


def n4_beendet(pfad: str) -> bool:
    if not os.path.exists(pfad):
        return False
    c = sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=30)
    try:
        return c.execute("SELECT 1 FROM meta WHERE k='ende'").fetchone() is not None
    finally:
        c.close()


def stand5(ablage: str) -> int:
    einbauen()
    N.STIMMEN = N.STIMMEN
    r = N.stand(ablage)
    print("  (N5: K_b und R_w gibt es hier nicht; R_v = Bloecke vertauscht, Anker 0-%d) · N4 beendet: %s" % (N_RV - 1, n4_beendet(_N4["pfad"])))
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("befehl", choices=("lauf", "stand"))
    ap.add_argument("--ablage", default=ABLAGE_N5)
    ap.add_argument("--n4-ablage", default=N4_ABLAGE)
    ap.add_argument("--platzhalter", choices=("zufall", "orakel"))
    ap.add_argument("--kein-warten", action="store_true")
    ap.add_argument("--warte-auf-n4", action="store_true")
    ap.add_argument("--max-aufrufe", type=int)
    x = ap.parse_args()
    if os.path.abspath(x.ablage) in (os.path.abspath(N4_ABLAGE), os.path.abspath(N.ABLAGE_VORGABE)):
        raise SystemExit("N5 nie in die N4-Ablage")
    if x.platzhalter and os.path.abspath(x.ablage) == os.path.abspath(ABLAGE_N5):
        raise SystemExit("Platzhalter-Laeufe nie in die echte N5-Ablage - bitte --ablage <Wegwerfpfad>")
    einbauen(x.n4_ablage)
    if x.befehl == "stand":
        sys.exit(stand5(x.ablage))
    if not n4_beendet(x.n4_ablage):
        if not x.warte_auf_n4:
            raise SystemExit("N4 ist noch nicht beendet (%s) - N5 startet erst danach (--warte-auf-n4 wartet)" % x.n4_ablage)
        print("N5 wartet auf das Ende von N4 (%s) ..." % x.n4_ablage, flush=True)
        while not n4_beendet(x.n4_ablage):
            time.sleep(int(os.environ.get("N5_WARTE_S", "600")))
        print("N4 ist beendet - N5 startet", flush=True)
    sys.exit(N.lauf(x.ablage, x.platzhalter, x.kein_warten, x.max_aufrufe))
