"""GDELT-ROHDATEN PROBETAG (Voranalyse_GDELT_Rohdaten_07_11.md §2, Nutzer 07.11.2026: *„Probetag laden“*).

    python -X utf8 Basisinfos/Rechenkern_02_10/gdelt_rohdaten_probetag.py --laden       # 96 GKG-Dateien vom 03.11.2026 nach data/_gdelt_roh
    python -X utf8 Basisinfos/Rechenkern_02_10/gdelt_rohdaten_probetag.py --auswerten   # -> gdelt_rohdaten_probetag.txt

Kriterien vorab (§2): R1 ≤ 500 MB und ≤ 15 min · R2 ≥ 100 Artikel je Ton · R3 |roh − API| ≤ 1,0 bei ≥ 3 von 4 Tönen.
Die Dateien werden nur als Daten gelesen (zipfile + Textzerlegung), nie ausgeführt.
"""
import csv
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
TAG = "20261103"
ORDNER = os.path.join(PROJ, "data", "_gdelt_roh", "2026-11-03")
AUS = os.path.join(HIER, "gdelt_rohdaten_probetag.txt")
PROBE = "K:/My Drive/Claude_Austauschordner/GDELT_Probe/gdelt_probe_T440.jsonl"
URL = "http://data.gdeltproject.org/gdeltv2/%s.gkg.csv.zip"
KOPF = {"User-Agent": "TradingInfoTool-Probetag"}
csv.field_size_limit(2 ** 31 - 1)
TXT = []

# Treffer je Ton (§2) - Textstellen klein geschrieben; Themen groß
TEXT = {"krypto": re.compile(r"bitcoin|cryptocurrenc"),
        "fed": re.compile(r"federal[ -]reserve"),
        "aktien": re.compile(r"stock[ -]market"),
        "konflikt": re.compile(r"\bwar\b|sanction|tariff")}
THEMA = {"krypto": re.compile(r"BITCOIN|CRYPTO"), "fed": None, "aktien": re.compile(r"ECON_STOCKMARKET"),
         "konflikt": re.compile(r"ARMEDCONFLICT|SANCTION|TARIFF")}
TITEL = re.compile(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.S)


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def namen():
    return ["%s%02d%02d00" % (TAG, h, m) for h in range(24) for m in (0, 15, 30, 45)]


def laden():
    os.makedirs(ORDNER, exist_ok=True)
    t0 = time.time()
    fehl = []
    for n in namen():
        ziel = os.path.join(ORDNER, n + ".gkg.csv.zip")
        if os.path.exists(ziel) and os.path.getsize(ziel) > 0:
            continue
        for versuch in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(URL % n, headers=KOPF), timeout=120) as r:
                    daten = r.read()
                with open(ziel + ".teil", "wb") as f:
                    f.write(daten)
                os.replace(ziel + ".teil", ziel)
                break
            except Exception as e:  # noqa: BLE001
                if versuch == 2:
                    fehl.append((n, str(e)[:80]))
                time.sleep(5)
        time.sleep(1)
    groesse = sum(os.path.getsize(os.path.join(ORDNER, f)) for f in os.listdir(ORDNER) if f.endswith(".zip"))
    print("geladen %d Dateien, %.1f MB, %.0f s, fehlend %d %s" % (
        len([f for f in os.listdir(ORDNER) if f.endswith(".zip")]), groesse / 1e6, time.time() - t0, len(fehl), fehl[:5]))


def api_werte():
    v = {}
    for z in open(PROBE, encoding="utf-8"):
        if not z.strip():
            continue
        x = json.loads(z)
        if x.get("art") == "abruf" and x.get("punkte"):
            for d, w in x["punkte"]:
                v.setdefault(x["ton"], {})[d[:8]] = w
    return {t: v.get(t, {}).get(TAG) for t in TEXT}


def auswerten():
    t0 = time.time()
    dateien = sorted(f for f in os.listdir(ORDNER) if f.endswith(".zip"))
    mb = sum(os.path.getsize(os.path.join(ORDNER, f)) for f in dateien) / 1e6
    summe = {t: [0, 0.0, 0, 0.0] for t in TEXT}           # n_text_oder_thema, Summe Ton, n_nur_text, Summe nur Text
    alle = [0, 0.0]
    zeilen_kaputt = 0
    for f in dateien:
        with zipfile.ZipFile(os.path.join(ORDNER, f)) as z:
            for name in z.namelist():
                with z.open(name) as roh:
                    for zeile in io.TextIOWrapper(roh, encoding="utf-8", errors="replace"):
                        s = zeile.rstrip("\n").split("\t")
                        if len(s) < 27:
                            zeilen_kaputt += 1
                            continue
                        try:
                            ton = float(s[15].split(",")[0])
                        except ValueError:
                            zeilen_kaputt += 1
                            continue
                        alle[0] += 1
                        alle[1] += ton
                        m = TITEL.search(s[26])
                        text = " ".join((m.group(1) if m else "", s[4], s[23], s[13], s[14])).lower()
                        themen = s[7] + ";" + s[8]
                        for t in TEXT:
                            tt = bool(TEXT[t].search(text))
                            th = bool(THEMA[t].search(themen)) if THEMA[t] else False
                            if tt or th:
                                summe[t][0] += 1
                                summe[t][1] += ton
                            if tt:
                                summe[t][2] += 1
                                summe[t][3] += ton
    dauer = time.time() - t0
    api = api_werte()
    p("GDELT-ROHDATEN PROBETAG · %s · Tag 03.11.2026 · Vorabfestlegung Voranalyse_GDELT_Rohdaten_07_11.md §2" % time.strftime("%Y-%m-%d %H:%M"))
    p("Dateien %d von 96 · komprimiert %.1f MB · Artikel %d (Ton im Mittel %.2f) · kaputte Zeilen %d · Auswertung %.0f s" % (
        len(dateien), mb, alle[0], alle[1] / max(1, alle[0]), zeilen_kaputt, dauer))
    r1 = mb <= 500 and dauer <= 15 * 60 and len(dateien) >= 90
    p("R1 Machbarkeit (≤ 500 MB und ≤ 15 min): %s · Hochrechnung 335 Tage %.0f GB · 2021-03..2026-10 (≈ 2.070 Tage) %.0f GB" % (
        "erfüllt" if r1 else "VERFEHLT", mb * 335 / 1e3, mb * 2070 / 1e3))
    r2 = r3 = 0
    p("%-9s %8s %8s %8s %8s %8s %s" % ("Ton", "Artikel", "Ton roh", "API", "Abstand", "nur Text", "(Artikel / Ton)"))
    for t in TEXT:
        n, s, n2, s2 = summe[t]
        roh = s / n if n else float("nan")
        roh2 = s2 / n2 if n2 else float("nan")
        a = api[t]
        ab = abs(roh - a) if a is not None and n else float("nan")
        r2 += n >= 100
        r3 += ab <= 1.0
        p("%-9s %8d %8.2f %8s %8.2f %8d / %.2f" % (t, n, roh, "%.2f" % a if a is not None else "–", ab, n2, roh2))
    p("R2 Treffer (≥ 100 je Ton): %d von 4 · %s" % (r2, "erfüllt" if r2 == 4 else "VERFEHLT"))
    p("R3 Nähe (|roh − API| ≤ 1,0 bei ≥ 3 von 4): %d von 4 · %s" % (r3, "erfüllt" if r3 >= 3 else "VERFEHLT"))
    if not r1:
        u = "WEG TOT (R1)"
    elif r2 == 4 and r3 >= 3:
        u = "GANGBAR — nächster Schritt 14-Tage-Abgleich (eigene Frage)"
    elif r3 < 3:
        u = "PRAKTISCH TOT (R3: eigene Reihe ist nicht die gemessene)"
    else:
        u = "OFFEN (R2 verfehlt)"
    p("URTEIL: %s" % u)
    open(AUS, "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if "--laden" in sys.argv:
        laden()
    elif "--auswerten" in sys.argv:
        auswerten()
    else:
        print(__doc__)
