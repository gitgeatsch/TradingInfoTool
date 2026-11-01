# -*- coding: utf-8 -*-
"""EBENE 1 — die Zustände der Sichten als Sätze (Fütterung §1 SF1–SF9, §6 Schritt 3; Voranalyse_Zustaende_Modul_01_11.md, Nutzer 01.11.:
*„a, bauen – prüfen, gegenprüfen und doku“*).

EIN Rechenweg für live und Rückspiel (SF8, Ü8): je Stichtag T entstehen die Zeilen aus ``data/_sichten/sichten.db`` mit dem
damals gültigen Jahrgang. Nur lesend, ohne Netz, nie die Produktions-DB.

    from agent import zustaende as Z
    a = Z.Ablage()                                  # einmal laden
    liste = Z.zustaende("2026-10-29", a)            # 35 Sicht-Zustände + S8 Termine, strukturiert
    print(Z.text("2026-10-29", a))                  # die Zeilen wie in der Probe

⚠️⚠️ JAHRGANG (Z1, 01.11.): ein Jahrgang gilt von ``bekannt_ab`` bis einschließlich ``bis`` + 1 Tag. ``bekannt_ab`` ist der FOLGETAG
der Veröffentlichung, ``bis`` der letzte Tag vor der nächsten — deren Zeile ist also erst am Tag ``bis`` + 2 bekannt. Die Probe ließ
den alten am Tag ``bis`` + 1 fallen: an 59 von 333 Rückspiel-Tagen fehlten M2/NFCI, am 24.02.2026 war M2 leer. Nachgewiesen: alle
99.080 Wechsel liegen genau bei ``bis`` + 2 T 00:00.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as pd

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABLAGE = os.path.join(PROJ, "data", "_sichten", "sichten.db")
JAHRE = 5                                     # SF7: ein Fenster für alle, wie K1–K9
SICHTEN = ("S1", "S2", "S3", "S4", "S7", "S8")
# [U] Shutdown der US-Regierung 01.10.–12.11.2025: die BLS-Termine (CPI, Arbeitsmarkt) wurden verschoben und neu angesetzt; FRED
# kennt nur den Termin, der stattfand, nicht seit wann er feststand (Voranalyse Z7). Diese tragen ⚠. Die Fed ist keine Bundes-
# behoerde im Shutdown-Sinn - FOMC fand planmaessig statt (Liste in agent.cycles), daher ohne ⚠.
SHUTDOWN_2025 = ("2025-10-01", "2026-01-31")
SHUTDOWN_ARTEN = ("cpi", "nfp")

# Einheit "anteil" = Bruch, angezeigt in % (Basis, Prämie); FRED-Zinsen kommen schon in %.
# Die LESART sagt, was HÖHER heißt - beschreibend, nie wertend (Ü2).
# Maß: "niveau" · "abstand200" (Preise: Abstand zum 200-T-Schnitt, 200 ZEILEN - bei Aktien Handelstage, Z9) · "jahr" (Mengen gegen
# Vorjahr) · "tage30" (Krypto-Mengen über 30 Kalendertage, Nutzer 01.11. „1a“) · "stufe" (Kategorie ohne Rang, V5)
DEFINITIONEN = [
    # S1 (Ergänzung 01.11.2026, Voranalyse_S1_Ergaenzung_01_11.md)
    ("S1", "kurs", "BTC", "BTC", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S1", "kurs", "ETH", "ETH", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S1", "breite", "TOP50", "Breite (Anteil der Top 50, die über 90 T besser liefen als BTC)", "niveau", "anteil",
     "höher = mehr Altcoins laufen besser als BTC"),
    ("S1", "season", "STUFE", "Season-Ampel", "stufe", "", ""),
    ("S1", "dvol", "BTC", "DVOL BTC (Optionsmarkt)", "niveau", "", "höher = Optionsmarkt erwartet größere Schwankung"),
    ("S1", "dvol", "ETH", "DVOL ETH (Optionsmarkt)", "niveau", "", "höher = Optionsmarkt erwartet größere Schwankung"),
    ("S1", "stablecoins", "USD", "Stablecoin-Angebot", "tage30", "Mrd. USD", "höher = mehr Stablecoins als vor 30 Tagen"),
    ("S1", "funding", "BTC", "Funding BTC (Mittel je Zahlung)", "niveau", "anteil", "höher = Long-Seite zahlt mehr für ihren Hebel"),
    ("S1", "funding", "ETH", "Funding ETH (Mittel je Zahlung)", "niveau", "anteil", "höher = Long-Seite zahlt mehr für ihren Hebel"),
    ("S1", "oi", "BTC", "Offene Positionen BTC", "tage30", "BTC", "höher = mehr Hebel-Positionen offen als vor 30 Tagen"),
    ("S1", "oi", "ETH", "Offene Positionen ETH", "tage30", "ETH", "höher = mehr Hebel-Positionen offen als vor 30 Tagen"),
    ("S1", "basis_quartal", "BTC", "Basis Quartalsfuture BTC", "niveau", "anteil", "höher = Terminkäufer zahlen mehr Aufschlag"),
    ("S1", "basis_quartal", "ETH", "Basis Quartalsfuture ETH", "niveau", "anteil", "höher = Terminkäufer zahlen mehr Aufschlag"),
    ("S1", "coinbase_praemie", "BTC", "Coinbase-Prämie BTC", "niveau", "anteil", "höher = US-Käufer zahlen mehr als der Rest der Welt"),
    ("S1", "coinbase_praemie", "ETH", "Coinbase-Prämie ETH", "niveau", "anteil", "höher = US-Käufer zahlen mehr als der Rest der Welt"),
    ("S1", "gdelt_ton", "krypto", "Nachrichtenton Krypto (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
    ("S2", "fred", "NETTO", "Netto-Liquidität Fed (Bilanz − TGA − RRP)", "jahr", "Mrd. USD", "höher = mehr Zentralbankgeld im Umlauf als vor einem Jahr"),
    ("S2", "fred", "M2SL", "Geldmenge M2", "jahr", "Mrd. USD", "höher = Geldmenge wächst schneller"),
    ("S2", "fred", "DFII10", "Realzins 10 J", "niveau", "%", "höher = teureres Geld nach Inflation"),
    ("S2", "fred", "DGS2", "Rendite 2 J", "niveau", "%", "höher = Markt erwartet höhere Leitzinsen"),
    ("S2", "fred", "T10Y2Y", "Zinskurve 10 J − 2 J", "niveau", "Pp", "höher = steilere Kurve"),
    ("S2", "gdelt_ton", "fed", "Nachrichtenton Fed (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
    ("S3", "yfinance", "^GSPC", "S&P 500", "abstand200", "", "höher = weiter über dem eigenen Schnitt"),
    ("S3", "yfinance", "^NDX", "Nasdaq 100", "abstand200", "", "höher = weiter über dem eigenen Schnitt"),
    ("S3", "yfinance", "SOXX", "Halbleiter (SOXX)", "abstand200", "", "höher = weiter über dem eigenen Schnitt"),
    ("S3", "yfinance", "^VIX", "VIX", "niveau", "", "höher = Aktienmarkt erwartet größere Schwankung"),
    ("S3", "yfinance", "^MOVE", "MOVE (Anleihe-Schwankung)", "niveau", "", "höher = Anleihemarkt erwartet größere Schwankung"),
    # 01.11.: BAA10Y statt BAMLH0A0HYM2 - den führt FRED (ICE-Lizenz) nur ab 10/2023 (SF7)
    ("S3", "fred", "BAA10Y", "Kreditaufschlag Baa − 10 J", "niveau", "Pp", "höher = Kreditgeber verlangen mehr für Risiko"),
    ("S3", "fred", "NFCI", "Finanzlage NFCI", "niveau", "", "höher = straffere Finanzierungsbedingungen"),
    ("S3", "gdelt_ton", "aktien", "Nachrichtenton Aktienmarkt (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
    ("S4", "yfinance", "DX-Y.NYB", "Dollar-Index DXY", "abstand200", "", "höher = Dollar stärker als im eigenen Schnitt"),
    ("S4", "yfinance", "GC=F", "Gold", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S4", "yfinance", "BZ=F", "Öl Brent", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S4", "yfinance", "HG=F", "Kupfer", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S7", "gdelt_ton", "konflikt", "Nachrichtenton Krieg/Sanktionen/Zölle (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
]
NETTO_TEILE = ("WALCL", "WTREGEN", "RRPONTSYD")   # WALCL und WTREGEN in Mio. USD, RRPONTSYD in Mrd. USD


@dataclass
class Zustand:
    sicht: str
    quelle: str
    symbol: str
    name: str
    mass: str
    satz: str                        # die Zeile ohne ● (SF1)
    auffaellig: bool                 # SF3/SF6: Rang <= P20 oder >= P80
    klasse: str | None = None        # SF3 - bei der Stufe deren Name, bei Terminen None (Takt §5 vergleicht sie)
    rang: float | None = None
    mass_wert: float | None = None   # Wert des Maßes (Niveau, Abstand, Veränderung)
    wert: float | None = None        # letzter Rohwert
    stand: str | None = None         # SF5
    alter_t: int | None = None       # Tage zwischen Stand und Stichtag (SF9)
    fenster_j: float = 0.0           # 0 bei Lücke (zählt wie ein kurzes Fenster)
    kennzeichen: str = ""


def _T(T) -> str:
    """Stichtag als ISO-UTC-Text; ein reines Datum heißt 00:00 UTC."""
    t = pd.Timestamp(T)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    return t.strftime("%Y-%m-%dT%H:%M:%S+00:00")


class Ablage:
    """``sichten.db`` einmal geladen (``mode=ro``). ``df`` statt Pfad nur für Prüfungen."""

    def __init__(self, pfad: str = ABLAGE, df: pd.DataFrame | None = None):
        if df is None:
            if os.path.basename(pfad) == "tradinginfotool.db":
                raise SystemExit("zustaende liest NIE die Produktions-DB")
            c = sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)
            try:
                df = pd.read_sql("SELECT quelle, symbol, datum, wert, bekannt_ab, bis FROM reihe", c)
            finally:
                c.close()
        df = df.copy()
        # Z1: der alte Jahrgang gilt, bis der nächste BEKANNT ist
        df["gilt_bis"] = (pd.to_datetime(df.bis) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
        self.gruppen = {k: g for k, g in df.groupby(["quelle", "symbol"])}
        self._alter: dict = {}

    def stand_am(self, quelle: str, symbol: str, T: str) -> pd.Series:
        """Je Beobachtungstag der am Stichtag gültige Jahrgang (SF8, Z1)."""
        g = self.gruppen.get((quelle, symbol))
        if g is None:
            return pd.Series(dtype=float)
        x = g[(g.bekannt_ab <= T) & (g.gilt_bis.isna() | (g.gilt_bis >= T[:10]))]
        return x.sort_values("bekannt_ab").groupby("datum").last().wert.sort_index()

    def reihe(self, quelle: str, symbol: str, T: str) -> pd.Series:
        if symbol == "NETTO":
            w, g, r = (self.stand_am("fred", k, T) for k in NETTO_TEILE)
            if not len(w) or not len(g):
                return pd.Series(dtype=float)
            tage = pd.date_range(min(w.index.min(), g.index.min()), T[:10])
            f = lambda s: s.set_axis(pd.to_datetime(s.index)).reindex(tage).ffill()   # noqa: E731
            n = (f(w) / 1000 - f(g) / 1000 - f(r).fillna(0)).dropna()
            n = n[n.index.isin(pd.to_datetime(w.index))]
            return n.set_axis(n.index.strftime("%Y-%m-%d"))
        s = self.stand_am(quelle, symbol, T)
        return s / 1e9 if quelle == "stablecoins" else s          # DefiLlama in USD, angezeigt in Mrd. USD

    def alter_reihe(self, quelle: str, symbol: str) -> pd.Series:
        """SF9: je Kalendertag d das Alter der jüngsten Beobachtung, die am Tag d (00:00) bekannt war - für die ganze Reihe."""
        k = (quelle, NETTO_TEILE[0] if symbol == "NETTO" else symbol)
        if k not in self._alter:
            g = self.gruppen.get(k)
            if g is None or not len(g):
                self._alter[k] = pd.Series(dtype=float)
            else:
                erst = g.groupby("datum").bekannt_ab.min()
                bek = pd.to_datetime(erst.values, utc=True).tz_convert(None)
                tag = bek.normalize() + pd.to_timedelta((bek != bek.normalize()).astype(int), unit="D")   # bekannt am Tag (00:00)
                obs = pd.Series(pd.to_datetime(erst.index), index=tag).groupby(level=0).max().cummax()
                idx = pd.date_range(obs.index.min(), obs.index.max() + pd.Timedelta(days=4000), freq="D")
                o = obs.reindex(idx).ffill()
                self._alter[k] = pd.Series((idx - pd.DatetimeIndex(o.values)).days, index=idx)
        return self._alter[k]


def klasse(p: float) -> str:
    return ("sehr tief" if p <= 5 else "tief" if p <= 20 else "normal" if p < 80 else "hoch" if p < 95 else "sehr hoch")


def _veraltet(ablage: Ablage, quelle: str, symbol: str, stand: pd.Timestamp, t: pd.Timestamp, jahre: int) -> tuple[int, str]:
    """SF9: ⚠, wenn das Alter am Stichtag über dem 99. Perzentil der EIGENEN Alter im Fenster liegt (Z4) - abgeleitet, nicht
    aufgezählt. Live ein Quellenausfall, im Rückspiel eine Datenlücke; beides darf die Sicht nicht für heutig halten."""
    alter = int((t - stand).days)
    a = ablage.alter_reihe(quelle, symbol)
    f = a[(a.index >= t - pd.DateOffset(years=jahre)) & (a.index < t)]
    if len(f) < 30:
        return alter, ""
    p99 = int(np.ceil(f.quantile(0.99)))
    return alter, (" ⚠ Stand %d T alt (üblich ≤ %d T)" % (alter, p99) if alter > p99 else "")


def _stufe(d, s: pd.Series, T: str, ablage: Ablage, jahre: int) -> Zustand:
    """Kategorie: Stufe und seit wann - kein Rang, kein ● (Voranalyse_S1 V5)."""
    from api.sichten_quellen import SEASON_CODE
    from agent.season_ampel import NAME
    sicht, q, sym, name = d[:4]
    s.index = pd.to_datetime(s.index)
    t = pd.Timestamp(T[:10])
    s = s[s.index < t]
    if s.empty:
        return Zustand(sicht, q, sym, name, "stufe", "[%s] %s: KEINE Werte vor dem Stichtag ⚠ · Fakt" % (sicht, name), False)
    code = s.iloc[-1]
    # nie gewechselt: seit Beginn der Reihe (die Probe nannte hier den LETZTEN Tag - 01.11. vom Paket gefunden)
    seit = s.index[0] if (s != code).sum() == 0 else s[s != code].index[-1] + pd.Timedelta(days=1)
    st = next(k for k, v in SEASON_CODE.items() if v == code)
    alter, alt = _veraltet(ablage, q, sym, s.index[-1], t, jahre)
    satz = "[%s] %s: %s seit %s (Stufe, kein Rang) · Stand %s%s · Fakt" % (sicht, name, NAME[st], seit.strftime("%Y-%m-%d"),
                                                                          s.index[-1].strftime("%Y-%m-%d"), alt)
    return Zustand(sicht, q, sym, name, "stufe", satz, False, klasse=NAME[st], wert=float(code), stand=s.index[-1].strftime("%Y-%m-%d"),
                   alter_t=alter, fenster_j=float(jahre), kennzeichen=alt.strip())


def zustand(d, ablage: Ablage, T, jahre: int = JAHRE) -> Zustand:
    """Ein Zustand am Stichtag - die Rechnung der Probe, dazu Z2 (leere Reihe in JEDEM Maß) und SF9."""
    T = _T(T)
    sicht, q, sym, name, mass, einheit, lesart = d
    s = ablage.reihe(q, sym, T).copy()
    if mass == "stufe":
        return _stufe(d, s, T, ablage, jahre)
    leer = Zustand(sicht, q, sym, name, mass, "[%s] %s: KEINE Werte vor dem Stichtag ⚠ · Fakt" % (sicht, name), False)
    s.index = pd.to_datetime(s.index)
    t = pd.Timestamp(T[:10])
    s = s[s.index < t]
    if s.empty:                                                          # Z2: vor jedem Maß, nicht erst danach
        return leer
    if mass == "tage30":
        x = (s / s.shift(30, freq="D").reindex(s.index) - 1) * 100       # 30 KALENDERtage, nicht 30 Zeilen
    elif mass == "abstand200":
        m = s.rolling(200, min_periods=150).mean()
        x = (s / m - 1) * 100
    elif mass == "jahr":
        v = s.reindex(pd.date_range(s.index.min(), s.index.max())).ffill()
        x = (v / v.shift(365) - 1) * 100
        x = x[x.index.isin(s.index)]
    else:
        x = s * (100 if einheit == "anteil" else 1)
    x = x.dropna()
    if x.empty:                                                          # nie still: eine leere Reihe ist ein Befund
        return leer
    fenster = x[x.index >= t - pd.DateOffset(years=jahre)]
    jetzt, datum = x.iloc[-1], x.index[-1].strftime("%Y-%m-%d")
    p = (fenster < jetzt).mean() * 100 + (fenster == jetzt).mean() * 50
    ab = fenster.index.min()
    j = (t - ab).days / 365.25
    v20 = x[x.index <= x.index[-1] - pd.Timedelta(days=28)]
    rich = "" if v20.empty else " · vor 4 Wochen %+.3g" % v20.iloc[-1]
    if mass == "abstand200":
        wert = "%s %.2f%s, %+.1f %% zum 200-T-Schnitt" % (name, s.iloc[-1], (" " + einheit) if einheit else "", jetzt)
    elif mass == "jahr":
        wert = "%s %.0f %s, %+.1f %% gegen Vorjahr" % (name, s.iloc[-1], einheit, jetzt)
    elif mass == "tage30":
        wert = "%s %.0f %s, %+.1f %% gegen vor 30 Tagen" % (name, s.iloc[-1], einheit, jetzt)
    else:
        wert = ("%s %.3g %s" % (name, jetzt, "%" if einheit == "anteil" else einheit)).rstrip()
    knapp = " ⚠ Fenster nur %.1f J" % j if j < jahre - 0.2 else ""
    abst = fenster.index.to_series().diff().dt.days.dropna()
    if len(abst) and abst.max() > max(10, 5 * abst.median()):   # ein Loch im Fenster ist so schlimm wie ein kurzes Fenster
        knapp += " ⚠ Lücke %d T ab %s" % (abst.max(), (abst.idxmax() - pd.Timedelta(days=int(abst.max()))).strftime("%Y-%m-%d"))
    alter, alt = _veraltet(ablage, q, sym, s.index[-1], t, jahre)
    kl = klasse(p)
    satz = "[%s] %s · Rang P%.0f der letzten %.1f J (ab %s) = %s (%s)%s · Stand %s%s%s · Fakt" % (
        sicht, wert, p, j, ab.strftime("%Y-%m"), kl, lesart, rich, datum, knapp, alt)
    return Zustand(sicht, q, sym, name, mass, satz, kl != "normal", klasse=kl, rang=float(p), mass_wert=float(jetzt),
                   wert=float(s.iloc[-1]), stand=datum, alter_t=alter, fenster_j=(0.0 if "Lücke" in knapp else j),
                   kennzeichen=(knapp + alt).strip())


def termine(ablage: Ablage, T) -> list[Zustand]:
    """S8: je Art der NÄCHSTE am Stichtag bekannte Termin - Fakt mit gemessenem Faktor (``termin_fakt``), kein Rang."""
    from agent import termin_fakt as TF
    T = _T(T)
    t = pd.Timestamp(T)
    aus = []
    for art in ("fomc", "cpi", "nfp"):
        s = ablage.stand_am("termin", art, T)
        zuk = s[pd.to_datetime(s.values, unit="s", utc=True) > t] if len(s) else s
        name = TF.NAME[art]
        if not len(zuk):
            aus.append(Zustand("S8", "termin", art, name, "termin",
                               "[S8] %s: kein Termin bekannt ⚠ · Fakt" % name, False))
            continue
        tag, sek = zuk.index[0], zuk.iloc[0]
        u = pd.Timestamp(int(sek), unit="s", tz="UTC")
        in_t = (u - t).total_seconds() / 86400
        kz = " ⚠ im Shutdown-Zeitraum 2025 verschoben - ob am Stichtag schon bekannt, ist offen" \
            if art in SHUTDOWN_ARTEN and SHUTDOWN_2025[0] <= tag <= SHUTDOWN_2025[1] else ""
        satz = ("[S8] %s %s UTC, in %.1f T · BTC bewegt sich in den 2 h ab dem Termin im Mittel %s× so stark wie sonst zur selben "
                "Uhrzeit (über 24 h %s×; %s)%s · Fakt" % (name, u.strftime("%Y-%m-%d %H:%M"), in_t,
                                                          TF._komma(TF.FAKTOR_2H[art]), TF._komma(TF.FAKTOR_24H), TF.MESSLAGE, kz))
        aus.append(Zustand("S8", "termin", art, name, "termin", satz, False, wert=float(in_t), stand=tag, kennzeichen=kz.strip()))
    return aus


def zustaende(T, ablage: Ablage | None = None, jahre: int = JAHRE) -> list[Zustand]:
    """Alle Zustände der Sichten S1–S4, S7 und die Termine S8 am Stichtag ``T``."""
    ablage = ablage or Ablage()
    return [zustand(d, ablage, T, jahre) for d in DEFINITIONEN] + termine(ablage, T)


def zeilen(liste: list[Zustand], sicht: str) -> list[str]:
    """Die Zeilen EINER Sicht für den Prompt (SF1, ● nach SF3/SF6)."""
    return [("● " if z.auffaellig else "  ") + z.satz for z in liste if z.sicht == sicht]


def _watchlist_krypto() -> list[str]:
    try:
        import config as C
        return [w.symbol.upper() for w in C.get_watchlist() if w.assetklasse == "krypto"]
    except Exception:                                          # noqa: BLE001
        return []


def text(T, ablage: Ablage | None = None, jahre: int = JAHRE, pfad: str = ABLAGE, ereignisse: pd.DataFrame | None = None,
         assets: list | None = None) -> str:
    """Alle Sichten als Block - Form der Probe (Kopf, je Sicht, Zusammenfassung). Je Sicht nach den Zuständen die EREIGNISSE aus A1
    (``agent.ereignisse``, Fütterung §3), am Stichtag bekannt und höchstens 7 T alt. ``assets`` = wessen Asset-Ereignisse an S7 gehen
    (Vorgabe: die Watchlist von HEUTE - ⚠ im Rückspiel nicht die damalige, offener Punkt in der Doku)."""
    from agent import ereignisse as EV
    T = _T(T)
    liste = zustaende(T, ablage, jahre)
    rang = [z for z in liste if z.sicht != "S8"]
    E = EV.lade(pfad) if ereignisse is None else ereignisse
    ev = EV.am(E, T, assets=_watchlist_krypto() if assets is None else assets)
    aus = ["FÜTTERUNG — PROBE DER SATZFORM (Ü1) · Stichtag %s · Einordnung %d J · nur lesend %s" % (T, jahre, pfad), ""]
    for sicht in SICHTEN:
        aus.append("── %s ──" % sicht)
        aus += ["  " + z for z in zeilen(liste, sicht)]
        aus += ["  " + z for z in EV.zeilen(ev, sicht, T)]
    n = sum(len(z.satz) for z in rang)
    aus += ["", "● = auffällig (Rang ≤ P20 oder ≥ P80) · %d von %d Zuständen auffällig · %d mit kürzerem Fenster als %d J" % (
        sum(z.auffaellig for z in rang), len(rang), sum(z.fenster_j < jahre - 0.2 for z in rang), jahre),
        "Zeichen gesamt: %d (≈ %d Token bei 3,5–4 Zeichen je Token)" % (n, n / 3.75),
        "S8 Termine: %d Zeilen, %d Zeichen" % (sum(z.sicht == "S8" for z in liste), sum(len(z.satz) for z in liste if z.sicht == "S8")),
        "Ereignisse (A1, %d T): %d Meldungen in %d Zeilen" % (EV.FENSTER_T, len(ev), sum(len(EV.zeilen(ev, s, T)) for s in SICHTEN))]
    return "\n".join(aus)
