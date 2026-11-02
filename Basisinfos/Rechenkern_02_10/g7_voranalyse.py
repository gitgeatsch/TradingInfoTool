"""G7 VORANALYSE — Messplan Faktentreue und Wert der Sichten (Nutzer 02.11.2026: „ja, starte mit der Voranalyse G7 – prüfen, gegenprüfen
und doku“). NUR LESEND, OHNE NETZ, ohne LLM. Misst, was der Messplan wissen muss, BEVOR er festgelegt wird:

  A  Messbarkeit: Blöcke je Rückspiel-Zeitraum und Horizont nach messnorm._block (max(15, 3 H), < 20 Blöcke = KEIN BEFUND)
  B  Zielgröße „Einbruch“: wie oft, in wie vielen unabhängigen Episoden und Blöcken (BTC und Breite der 127 REGEL0-Werte)
  C  Takt (Fütterung §5) am echten Modul: wie viele Sicht-Gutachten entstehen je Tag und Sicht, mit welchem Prompt-Umfang
  D  Finales LLM: REGEL0-Einstiege je Zeitraum (Referenz kern48jbz, Menge „bestand“)
  E  SELBSTTEST des bestehenden Treue-Prüfers Z-1 (agent/gegenpruefer_rollen.pruefe_zahlendeckung) an ECHTEN Eingaben
     (zustaende.text): je Fehlerart 1.000 gepflanzte Fälle, dazu korrekte Wiedergaben als Fehlalarm-Probe

    python g7_voranalyse.py            -> g7_voranalyse.txt
"""
import json
import math
import re
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
import messnorm  # noqa: E402
from agent import ereignisse as EV  # noqa: E402
from agent import gegenpruefer_rollen as Z1  # noqa: E402
from agent import zustaende as Z  # noqa: E402

ZEITRAEUME = {"2025 (gpt-oss)": ("2025-01-01", "2025-11-30"), "Dez. 2025 – Okt. 2026 (Gemini)": ("2025-12-01", "2026-10-31")}
REF = os.path.join(PROJ, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv")
SAAT = 20261102
ZAHL = re.compile(r"[-+]?\d+(?:\.\d+)?")      # die Satzform schreibt Punkt als Dezimalzeichen, ohne Tausenderpunkt
AUS = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    AUS.append(s)


def tage(a, b):
    return (pd.Timestamp(b) - pd.Timestamp(a)).days + 1


# ── A ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def teil_a():
    p("A  MESSBARKEIT — Blöcke nach messnorm._block (max(15, 3 H)); unter 20 Blöcken KEIN BEFUND")
    p("   %-34s %6s  %s" % ("Zeitraum", "Tage", "  ".join("H=%-2d" % h for h in (1, 3, 5, 7, 10, 14))))
    zr = dict(ZEITRAEUME)
    zr["beide zusammen"] = ("2025-01-01", "2026-10-31")
    for k, (a, b) in zr.items():
        n = tage(a, b)
        p("   %-34s %6d  %s" % (k, n, "  ".join("%4d%s" % (n // messnorm._block(h), "✖" if n // messnorm._block(h) < 20 else " ")
                                              for h in (1, 3, 5, 7, 10, 14))))


# ── B ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def kurse():
    c = sqlite3.connect("file:%s?mode=ro" % EV.ABLAGE.replace("\\", "/"), uri=True)
    btc = pd.read_sql("SELECT datum, wert FROM reihe WHERE quelle='kurs' AND symbol='BTC'", c).groupby("datum").wert.last()
    c.close()
    syms = sorted(set(pd.read_csv(REF, sep=";").symbol))
    teile = []
    for db in ("stundenkurse.db", "stundenkurse_alle.db"):              # Messbasis (116 der 127) + Bewertung (der Rest)
        d = sqlite3.connect("file:%s?mode=ro" % os.path.join(PROJ, "data", db).replace("\\", "/"), uri=True)
        q = "SELECT symbol, substr(stunde,1,10) tag, close FROM stundenkurse WHERE stunde >= '2024-09-01' AND substr(stunde,12,2)='23' " \
            "AND symbol IN (%s)" % ",".join("?" * len(syms))
        teile.append(pd.read_sql(q, d, params=syms))
        d.close()
    S = pd.concat(teile).drop_duplicates(["symbol", "tag"]).pivot_table(index="tag", columns="symbol", values="close")
    btc.index = pd.to_datetime(btc.index)
    S.index = pd.to_datetime(S.index)
    return btc.sort_index(), S.sort_index()


def einbrueche(r1: pd.Series, H: int, k: float = 2.0) -> pd.Series:
    """Tag T ist Einbruch-Tag, wenn der Ertrag T -> T+H unter -k Sigma * sqrt(H) liegt; Sigma aus den 60 Tagen VOR T."""
    sig = r1.rolling(60).std().shift(1)
    rH = r1[::-1].rolling(H).sum()[::-1].shift(-1)          # Summe der Log-Erträge T+1..T+H = Ertrag Schluss T -> Schluss T+H
    return (rH <= -k * sig * math.sqrt(H)) & sig.notna() & rH.notna()


def teil_b():
    p("\nB  ZIELGRÖSSE „EINBRUCH“ — Ertrag Schluss T -> T+H unter -2 Sigma·√H (Sigma: 60 T davor); BTC und Median der 127 REGEL0-Werte")
    btc, S = kurse()
    r_btc = np.log(btc).diff()
    r_breit = np.log(S).diff().median(axis=1, skipna=True)
    n_ = S.notna().sum(axis=1).loc["2025-01-01":]
    p("   Breite: im Mittel %.0f von 127 Werten je Tag mit Kurs (ab 2025), letzter Tag mit >= 100 Werten %s (Desktop-Daten)" % (
        n_.mean(), n_[n_ >= 100].index.max().date()))
    p("   %-34s %-6s %3s %8s %9s %18s" % ("Zeitraum", "Reihe", "H", "Tage", "Episoden", "Blöcke mit Einbruch"))
    for k, (a, b) in ZEITRAEUME.items():
        for name, r in (("BTC", r_btc), ("Breite", r_breit)):
            for H in (1, 3, 7):
                e = einbrueche(r, H).loc[a:b]
                tg = e[e].index
                epi = 1 + int((np.diff(tg.values).astype("timedelta64[D]").astype(int) > H).sum()) if len(tg) else 0
                bl = messnorm._block(H)
                nb = tage(a, b) // bl
                mit = len({(t - pd.Timestamp(a)).days // bl for t in tg if (t - pd.Timestamp(a)).days // bl < nb})
                p("   %-34s %-6s %3d %4d/%-3d %9d %10d von %d" % (k, name, H, len(tg), int(e.notna().sum()), epi, mit, nb))


# ── C ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def teil_c():
    p("\nC  TAKT (Fütterung §5) am echten Modul: neues Gutachten, wenn ein Zustand der Sicht die KLASSE wechselt (gegen den Vortag), ein "
      "Ereignis der Sicht eintrifft (A1, bekannt im letzten Tag) oder das letzte 7 T alt ist")
    A = Z.Ablage()
    E = EV.lade()
    wl = Z._watchlist_krypto()
    p("   A1-Ereignisse in sichten.db: %d (davon Nachrichten %d — der Volllauf läuft, die Nachrichten-Ereignisse fehlen noch) · Watchlist "
      "HEUTE %d Krypto-Werte (⚠ nicht die damalige)" % (len(E), int((E.quelle == "nachricht").sum()), len(wl)))
    sichten = ("S1", "S2", "S3", "S4", "S7", "S8")
    for k, (a, b) in ZEITRAEUME.items():
        vor = {s: None for s in sichten}
        alter = {s: 99 for s in sichten}
        n = {s: 0 for s in sichten}
        grund = {s: {"klasse": 0, "ereignis": 0, "alter": 0} for s in sichten}
        zeichen = {s: [] for s in sichten}
        for T in pd.date_range(a, b, freq="D"):
            Ts = T.strftime("%Y-%m-%d")
            L = Z.zustaende(Ts, A)
            ev = EV.am(E, Ts, tage=1, assets=wl)
            ev7 = EV.am(E, Ts, assets=wl)
            for s in sichten:
                key = tuple((z.name, z.klasse if s != "S8" else z.stand) for z in L if z.sicht == s)
                neu_ev = int((ev.sicht == s).sum())
                warum = "klasse" if (vor[s] is not None and key != vor[s]) else "ereignis" if neu_ev else \
                    "alter" if alter[s] >= 7 else None
                if warum:
                    n[s] += 1
                    grund[s][warum] += 1
                    alter[s] = 0
                    zeichen[s].append(sum(len(z.satz) for z in L if z.sicht == s) + sum(len(x) for x in EV.zeilen(ev7, s, Ts)))
                else:
                    alter[s] += 1
                vor[s] = key
        nt = tage(a, b)
        p("   %s — %d Tage" % (k, nt))
        ges_n = ges_tok = 0
        for s in sichten:
            tok = np.mean(zeichen[s]) / 3.75 if zeichen[s] else 0
            ges_n += n[s]
            ges_tok += n[s] * (tok + 1500)
            p("     %s: %4d Gutachten (%.0f %% der Tage) · Anlass Klasse %d, Ereignis %d, Alter %d · Eingabe ≈ %.0f Token (Zustände + "
              "Ereignisse)" % (s, n[s], 100 * n[s] / nt, grund[s]["klasse"], grund[s]["ereignis"], grund[s]["alter"], tok))
        p("     zusammen %d Gutachten ≈ %.1f Mio. Token (je Gutachten + 1.500 für Anweisung und Antwort, geschätzt) · je Tag %.1f Aufrufe"
          % (ges_n, ges_tok / 1e6, ges_n / nt))


# ── D ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def teil_d():
    p("\nD  FINALES LLM — REGEL0-Einstiege (Referenz kern48jbz, Menge bestand; endet 2026-08-31)")
    e = pd.read_csv(REF, sep=";")
    e["z"] = pd.Timestamp("2020-01-01") + pd.to_timedelta(e.stunde, unit="h")
    for k, (a, b) in ZEITRAEUME.items():
        x = e[(e.z >= a) & (e.z < pd.Timestamp(b) + pd.Timedelta(days=1))]
        t = x.groupby(x.z.dt.date).size()
        p("   %-34s %5d Einstiege an %3d Tagen (Median %.0f je Tag, höchstens %d) · %d Werte · ≈ %.1f Mio. Token bei 3.000 + 500 je Aufruf, "
          "A4 Gegenanwalt noch einmal so viel" % (k, len(x), len(t), t.median(), t.max(), x.symbol.nunique(), len(x) * 3500 / 1e6))
    p("   ⚠ Dez. 2025 – Okt. 2026: die Referenz reicht nur bis 2026-08-31 — Sep./Okt. sind neu zu rechnen")


# ── E ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _fmt(v: float) -> str:
    """Wie die Satzform: drei bedeutsame Stellen."""
    return "%.3g" % v if abs(v) < 1000 else "%.0f" % v


def angezeigt(z) -> float | None:
    """Die Zahl, die die Zeile als WERT zeigt (erste Zahl nach dem Namen) - nicht der Rohwert (Breite 0,28 wird als 28 %% gezeigt).
    Stufen (Season) und Termine haben keinen Rang und keinen Wert in diesem Sinn."""
    if z.rang is None or z.name not in z.satz:
        return None
    m = ZAHL.search(z.satz.split(z.name, 1)[1])
    return float(m.group().replace(",", ".")) if m else None


def teil_e():
    p("\nE  SELBSTTEST DES TREUE-PRÜFERS Z-1 an ECHTEN Eingaben (zustaende.text an 30 Tagen, Dez. 2025 – Okt. 2026), je Art 1.000 Fälle")
    p("   Z-1 prüft, ob jede genannte Zahl IRGENDWO in der Eingabe steht (Toleranz ±%.2f absolut, harmlos: %s)" % (
        Z1.TOLERANZ, sorted(Z1._HARMLOS)))
    rng = np.random.default_rng(SAAT)
    A = Z.Ablage()
    E = EV.lade()
    tage_ = pd.date_range("2025-12-01", "2026-10-31", freq="D")
    tag = sorted(rng.choice(len(tage_), 30, replace=False))
    falle = []
    for i in tag:
        T = tage_[i].strftime("%Y-%m-%d")
        txt = Z.text(T, A, ereignisse=E)
        L = [z for z in Z.zustaende(T, A) if z.sicht != "S8" and angezeigt(z) is not None]
        falle.append((txt, L))
    p("   ⚠ ZAHLENERKENNUNG von Z-1 (_ZAHL) zerlegt große Zahlen: %s" % "; ".join(
        "%s -> %s" % (t, Z1._zahlen(t)) for t in ("71211.95", "2061501", "5808")))
    zahlen = [len(set(Z1._zahlen(t))) for t, _ in falle]
    p("   verschiedene Zahlen je Eingabe: Median %d (%d–%d) — gegen DIESE Menge wird jede genannte Zahl gehalten" % (
        int(np.median(zahlen)), min(zahlen), max(zahlen)))

    def erkannt(txt, beleg):
        return Z1.pruefe_zahlendeckung({"lage": "", "belege": [beleg]}, txt)["verstoss"]

    def lauf(art, bau, n=1000):
        k = m = 0
        for _ in range(n):
            txt, L = falle[rng.integers(len(falle))]
            z = L[rng.integers(len(L))]
            b = bau(z, L)
            if b is None:
                continue
            m += 1
            k += erkannt(txt, b)
        return k, m

    def falsch(d):
        def f(z, L):
            w = angezeigt(z)
            v = _fmt(w * (1 + d * rng.choice([-1, 1])))
            return None if float(v) == w else "%s %s" % (z.name, v)
        return f

    zeilen = []
    for d in (0.01, 0.05, 0.20, 0.50, 1.00):
        zeilen.append(("Wert verfälscht um ±%.0f %%" % (100 * d), lauf("w", falsch(d))))
    zeilen.append(("Rang verfälscht um ±10 (P14 -> P24)", lauf("r", lambda z, L: None if z.rang is None else "%s P%d" % (
        z.name, int(round(z.rang)) + int(rng.choice([-10, 10]))))))
    zeilen.append(("Wert eines ANDEREN Zustands genannt (falscher Bezug)", lauf("b", lambda z, L: "%s %s" % (
        z.name, _fmt(angezeigt([y for y in L if y is not z][rng.integers(len(L) - 1)]))))))
    zeilen.append(("frei erfundene Zahl (log-gleichverteilt 0,001–100.000)", lauf("e", lambda z, L: "%s %s" % (
        z.name, _fmt(10 ** rng.uniform(-3, 5))))))
    p("   %-58s %s" % ("gepflanzter Fehler", "erkannt"))
    for name, (k, m) in zeilen:
        p("   %-58s %4d/%d = %.0f %%" % (name, k, m, 100 * k / m))
    p("   %-58s %s" % ("KORREKTE Wiedergabe (darf NICHT anschlagen)", "Fehlalarm"))
    rund = [("wie in der Eingabe", lambda v: _fmt(v)), ("auf 1 Nachkommastelle", lambda v: "%.1f" % v),
            ("ganzzahlig gerundet", lambda v: "%.0f" % v), ("deutsches Komma (53,3)", lambda v: _fmt(v).replace(".", ",")),
            ("Tausenderpunkt (71.212), nur Werte ≥ 1.000", lambda v: None if abs(v) < 1000 else f"{v:,.0f}".replace(",", ".")),
            ("in Tausend/Mrd. umgerechnet (83,5 Tsd.)", lambda v: None if abs(v) < 1000 else ("%.1f Tsd." % (v / 1000)).replace(".", ","))]
    for name, f in rund:
        k, m = lauf("f", lambda z, L, f=f: None if f(angezeigt(z)) is None else "%s %s" % (z.name, f(angezeigt(z))))
        p("   %-58s %4d/%d = %.0f %%" % (name, k, m, 100 * k / m))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    teile = sys.argv[1:] or ["a", "b", "c", "d", "e"]
    for t in teile:
        {"a": teil_a, "b": teil_b, "c": teil_c, "d": teil_d, "e": teil_e}[t]()
    if teile == ["a", "b", "c", "d", "e"]:
        open(os.path.join(HIER, "g7_voranalyse.txt"), "w", encoding="utf-8").write("\n".join(AUS) + "\n")


if __name__ == "__main__":
    main()
