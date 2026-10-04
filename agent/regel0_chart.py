"""Das Chart zum REGEL0-Signal (Schritt 7, Voranalyse_Schritt7 Par. 20.6, E-50 N-f; Nutzer 03.10.2026: *"in Produktion mit eMail und Charts"*).

Ein Bild, zwei Leser: die Signalmail (eingebettet, `send_notification_email(inline_images=...)`) und der Hebel-Tab.

    Stundenkurs der letzten Tage vor dem Signal bis heute (hoechstens bis zum Ausstieg)
    Signal (Schluss der Signalstunde), EINSTIEG (Schluss der Folgestunde), AUSSTIEG (24 h danach)
    Liquidationsgrenze je Stufe ueber die Haltedauer - die gewaehlte kraeftig, die anderen duenn
    Marken (Widerstand/Unterstuetzung), sobald der Trader-Erbauer sie liefert

⚠️ LIEST NUR die Stundenkurse (mode=ro). Kein Netz, keine Produktion.
⚠️ Die Liquidationsgrenze ist DIESELBE Formel wie in der Messung der Hebelstufe (`messe_k6_hebelstufe.liq_schwelle`, Marge 0,09,
Finanzierung 0,0018 je Stunde und 24 h) - hier nachgebildet, damit die App nicht die schweren Messmodule laedt; die Wache
`--paket Regel0Betrieb` haelt beide gleich. Bezug ist der Kurs zur Signalstunde (der Einstiegskurs steht erst eine Stunde spaeter fest).
"""
from __future__ import annotations

import io
import os
import sqlite3
from datetime import datetime, timedelta, timezone

MARGE = 0.09          # wie agent/regel0_rechnung.py MARGE
FIN = 0.0018          # wie messe_k6_hebelstufe.FIN (Finanzierung je 24 h als Anteil)
STUFEN = (5, 3, 2)    # wie messe_k6_hebelstufe.STUFEN
TAGE_VORHER = 5


def liq_schwelle(L: int, m: float, s: float) -> float:
    """Liquidationspreis / Einstieg nach s Stunden (Long) - Nachbildung von messe_k6_hebelstufe.liq_schwelle."""
    return (1.0 - 1.0 / L + (s / 24.0) * FIN) / (1.0 - m)


def _t(txt: str) -> datetime:
    return datetime.strptime(txt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def reihe(ordner: str, symbol: str, ab: datetime, bis: datetime) -> list:
    """[(Ende der Stunde UTC, close)] - zuerst die Messbasis-Datei, sonst stundenkurse_alle.db (dort fehlen die Messbasis-Assets)."""
    q = "SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= ? AND stunde <= ? ORDER BY stunde"
    arg = (symbol, ab.strftime("%Y-%m-%d %H:%M"), bis.strftime("%Y-%m-%d %H:%M"))
    for name in ("stundenkurse.db", "stundenkurse_alle.db"):
        p = os.path.join(ordner, name)
        if not os.path.exists(p):
            continue
        c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
        try:
            rows = c.execute(q, arg).fetchall()
        except sqlite3.Error:
            rows = []
        finally:
            c.close()
        if rows:
            return [(_t(s) + timedelta(hours=1), float(k)) for s, k in rows if k is not None]
    return []


def stufe_von(r: dict) -> int:
    for k in ("stufe", "stufe_vorlaeufig"):
        if r.get(k) is not None:
            return int(r[k])
    return 0


def daten(r: dict, ordner: str, jetzt: datetime | None = None, tage: int = TAGE_VORHER) -> dict | None:
    """Was das Bild zeigt, ohne das Bild - damit die Suite es pruefen kann. None, wenn keine Kurse da sind."""
    jetzt = jetzt or datetime.now(timezone.utc)
    sig_ende = _t(r["signalstunde"]) + timedelta(hours=1)
    ein = _t(r["einstieg"]) + timedelta(hours=1)
    aus = _t(r["ausstieg"]) + timedelta(hours=1)
    bis = min(jetzt, aus)
    kurse = reihe(ordner, r["symbol"], sig_ende - timedelta(days=tage), bis - timedelta(hours=1))
    if not kurse:
        return None
    # 04.10.2026 (Nutzer: *USD statt Euro*): liegt EUR je USD dieses Assets vor (Bitpanda-Ticker beim Versand, regel0_mail),
    # zeigt das Bild EUR - Binance-USDT mal dieses Verhaeltnis. Ohne (Hebel-Tab, Ticker weg) bleibt es USDT und sagt das.
    fx = r.get("eur_je_usd")
    if fx:
        kurse = [(t, k * float(fx)) for t, k in kurse]
    ref = (r["kurs"] * float(fx or 1.0)) if r.get("kurs") else next((k for t, k in reversed(kurse) if t <= sig_ende), kurse[-1][1])
    gew = stufe_von(r)
    liq = {}
    for L in STUFEN:
        pts = [(ein + timedelta(hours=s), ref * liq_schwelle(L, MARGE, s)) for s in range(0, 25)]
        liq[L] = pts
    ein_kurs = next((k for t, k in kurse if t == ein), None)
    return {"kurse": kurse, "signal": sig_ende, "einstieg": ein, "ausstieg": aus, "ref": float(ref), "einstieg_kurs": ein_kurs,
            "stufe": gew, "liq": liq, "name": r.get("bitpanda") or r["symbol"], "waehrung": "EUR" if fx else "USDT"}


def _zahl(x: float) -> str:
    """Deutsche Schreibweise mit sinnvollen Stellen (Kurse von 0,000012 bis 100.000)."""
    import math
    if x and abs(x) < 1:
        stellen = max(2, 3 - int(math.floor(math.log10(abs(x)))))      # vier gueltige Stellen, ohne Exponent
        t = ("%.*f" % (stellen, x)).rstrip("0").rstrip(".")
    else:
        t = "%.2f" % x if abs(x) < 1000 else "%.0f" % x
    ganz, _, rest = t.partition(".")
    if abs(x) >= 1000:
        ganz = "{:,}".format(int(float(ganz))).replace(",", ".")
    return ganz + ("," + rest if rest else "")


def bild(r: dict, ordner: str, jetzt: datetime | None = None, marken: list | None = None, breite: float = 9.0,
         hoehe: float = 4.4) -> bytes | None:
    """PNG-Bytes oder None (keine Kurse). ``marken``: [(preis, 'Widerstand'|'Unterstuetzung', beruehrungen)]."""
    d = daten(r, ordner, jetzt)
    if d is None:
        return None
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, ax = plt.subplots(figsize=(breite, hoehe), dpi=100)
    try:
        xs = [t.astimezone().replace(tzinfo=None) for t, _k in d["kurse"]]
        ys = [k for _t2, k in d["kurse"]]
        ax.plot(xs, ys, color="#1f4e79", linewidth=1.3,
                label="Stundenkurs (Binance, in EUR umgerechnet)" if d["waehrung"] == "EUR" else "Stundenkurs (Binance, USDT)")
        # Die Achse folgt dem KURS: Liquidationsgrenzen liegen 12-45 % tiefer und wuerden den Verlauf sonst zu einem Strich
        # zusammendruecken (erstes Probebild 03.10.). Gezeichnet wird eine Grenze nur, wenn sie im sichtbaren Bereich liegt;
        # alle drei stehen mit Preis und Abstand im Kasten unten.
        lo, hi = min(ys + [d["ref"]]), max(ys + [d["ref"]])
        rand = (hi - lo) * 0.08 or hi * 0.01
        ax.set_ylim(lo - rand, hi + rand)
        kasten = []
        for L, pts in d["liq"].items():
            gew = (L == d["stufe"])
            preis = pts[0][1]
            kasten.append("%s%dx: %s (%s %%)" % ("▶ " if gew else "", L, _zahl(preis),
                                                 ("%+.1f" % (100.0 * (preis / d["ref"] - 1.0))).replace(".", ",")))
            # ⚠️ 04.10.2026 (QNT 3x): gezeichnet war die NICHT gewaehlte 5x-Linie, die gewaehlte 3x lag unter dem Ausschnitt und
            # fehlte. Jetzt: nur die GEWAEHLTE Stufe, und liegt sie ausserhalb, steht sie als Hinweis am unteren Rand.
            if not gew:
                continue
            if lo - rand <= preis <= hi + rand:
                ax.plot([t.astimezone().replace(tzinfo=None) for t, _ in pts], [p for _, p in pts], color="#c0392b",
                        linewidth=2.0, linestyle="-", label="Liquidation %dx (gewählt)" % L)
            else:
                ax.text(0.01, 0.02, "▼ Liquidation %dx bei %s %s (%s %%) - unterhalb des Ausschnitts" % (
                    L, _zahl(preis), d["waehrung"], ("%+.1f" % (100.0 * (preis / d["ref"] - 1.0))).replace(".", ",")),
                    transform=ax.transAxes, ha="left", va="bottom", fontsize=8, color="#c0392b",
                    bbox=dict(boxstyle="round", facecolor="white", edgecolor="#c0392b", alpha=0.9))
        ax.text(0.99, 0.97, "Liquidation je Stufe, ab Kurs zur Signalstunde %s %s" % (_zahl(d["ref"]), d["waehrung"]) + chr(10)
                + "   ".join(kasten),
                transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color="#c0392b",
                bbox=dict(boxstyle="round", facecolor="white", edgecolor="#c0392b", alpha=0.9))
        ax.axvline(d["signal"].astimezone().replace(tzinfo=None), color="#7f8c8d", linewidth=0.8, linestyle="--")
        ax.axvline(d["einstieg"].astimezone().replace(tzinfo=None), color="#27ae60", linewidth=1.2)
        ax.axvline(d["ausstieg"].astimezone().replace(tzinfo=None), color="#8e44ad", linewidth=1.2)
        y_ein = d["einstieg_kurs"] if d["einstieg_kurs"] is not None else d["ref"]
        ax.plot([d["einstieg"].astimezone().replace(tzinfo=None)], [y_ein], marker="^", color="#27ae60", markersize=9,
                label="Einstieg %s%s" % (d["einstieg"].astimezone().strftime("%d.%m. %H:%M"),
                                         "" if d["einstieg_kurs"] is not None else " (geplant)"))
        ax.plot([], [], color="#8e44ad", linewidth=1.2, label="Ausstieg %s (24 h)" % d["ausstieg"].astimezone().strftime("%d.%m. %H:%M"))
        ax.plot([], [], color="#7f8c8d", linewidth=0.8, linestyle="--", label="Signal (Ende der Signalstunde)")
        for preis, art, n in (marken or []):
            ax.axhline(preis, color="#e67e22" if art.startswith("W") else "#16a085", linewidth=0.7, alpha=0.8)
            ax.text(xs[0], preis, " %s (%dx berührt)" % (art, n), fontsize=7, va="bottom",
                    color="#e67e22" if art.startswith("W") else "#16a085")
        ax.set_title("%s · REGEL0 LONG %s · Kurse in %s · Zeiten in Ortszeit" % (
            d["name"], ("%dx" % d["stufe"]) if d["stufe"] else "kein Handel", d["waehrung"]), fontsize=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.\n%H:%M"))
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: _zahl(v)))     # 04.10.: deutsche Achse (0,031 statt 0.031)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7, loc="upper left", ncol=2, framealpha=0.85)
        fig.tight_layout()
        puffer = io.BytesIO()
        fig.savefig(puffer, format="png", facecolor="white")
        return puffer.getvalue()
    finally:
        plt.close(fig)
