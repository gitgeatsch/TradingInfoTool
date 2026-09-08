# -*- coding: utf-8 -*-
"""IST JEDES ASSET SAUBER AUFGENOMMEN? — die Meldeluecke (08.09.2026)

## Warum es das gibt

Nutzerhinweis 08.09., woertlich: *„Neues Asset wird in der Watchlist
aufgenommen oder neuer Coin-Bestand Spot — es müssen die Daten zur
Bewertung für das Asset vorhanden sein bzw. das Asset in der Ablaufkette
sauber aufgenommen werden."*

**Beim Nachsehen war es kein Beispiel, sondern der Ist-Zustand:**

    ACHT gehaltene Krypto-Positionen haben KEINE Messreihe
    ASTER · BRETT · CANTON · KAS · MON · MORPHO · SUPRA · VSN

    ⚠️ CANTON hat `rolle = core` - ein Kernwert ohne jede Kursreihe.
    ⚠️ SECHS davon haben Historie in der Produktions-DB (KAS 1.686
       Zeilen, MORPHO 1.243, BRETT 854, SUPRA 631, ASTER 585, MON 501) -
       sie wurde nur nie in die Messbasis uebernommen.

**Und nichts hat es gemeldet.** Im ganzen Baum gab es keine Pruefung
darauf, und `agent/datenfrische.py` erwaehnt `messdaten` kein einziges
Mal - die Messbasis wurde nie ueberwacht.

## Die drei Lebenszyklus-Faelle, die der Nutzer benannt hat

    NEU            Asset kommt in Watchlist oder Bestand
                   -> hat es eine Messreihe? einen Beitrag?
    FAELLT WEG     Asset verlaesst Watchlist und Bestand
                   -> ⚠️ KEIN Fehler. P6 verlangt ausdruecklich, dass die
                      Messbasis BREITER ist als das Portfolio. Nur
                      berichtet, nie bemaengelt.
    AENDERT SICH   Symbolwechsel, Token-Umstellung, Reihe bricht ab
                   -> endet die Reihe lange vor dem Rest?

## ⚠️ Was diese Datei NICHT tut

Sie laedt nichts nach und repariert nichts. Sie **meldet**. Das Nachladen
ist eine eigene Entscheidung - `lade_messreihen.py` gibt es dafuer.

    python pruefe_neuaufnahme.py
"""
from __future__ import annotations

import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MESS = "data/messdaten.db"
PROD = "data/tradinginfotool.db"

# ⚠️⚠️ DIE AUSNAHMEN STEHEN HIER MIT GRUND - nicht im Code versteckt.
# Eine Ausnahme ohne Begruendung ist eine stille Luecke; genau die soll
# diese Datei ja finden.
AUSNAHMEN = {
    "EURCV": "Cash-Aequivalent (`ist_cash_aequivalent=True`), kein zu "
             "bewertender Coin - braucht einen PREIS fuer die Cash-Quote, "
             "aber keine Bewertung. `asset_schalter.py` behandelt es "
             "gesondert (Nutzerhinweis 08.09.)",
    "VSN": "Nutzerentscheidung 08.09., woertlich: 'vsn ist nicht "
           "relevant'. Es hat weder in der Messbasis noch in der "
           "Produktion eine Kursreihe; eine Bewertung ist damit "
           "ohnehin nicht moeglich",
}
# Ab wieviel Tagen gilt eine Assetklasse in der Messbasis als veraltet?
# ⚠️ Setzung, keine Messung. Krypto handelt durchgehend, ein Rueckstand
# von mehr als einer Woche ist dort nicht erklaerbar.
FRISCHE_GRENZE_TAGE = 7


def _lies():
    """Watchlist, Bestaende, Messreihen und Beitragsquellen - roh."""
    import config
    wl = {}
    for a in config.get_watchlist():
        s = str(getattr(a, "symbol", "") or "").upper()
        if s:
            wl[s] = {"klasse": str(getattr(a, "assetklasse", "") or "").lower(),
                     "rolle": str(getattr(a, "rolle", "") or ""),
                     "cash": bool(getattr(a, "ist_cash_aequivalent", False))}
    c = sqlite3.connect("file:%s?mode=ro" % PROD, uri=True)
    best = {r[0].upper() for r in
            c.execute("SELECT symbol FROM holdings WHERE quantity > 0")}
    prod = {r[0].upper(): r[1] for r in c.execute(
        "SELECT symbol, COUNT(*) FROM price_history_ohlc GROUP BY symbol")}
    c.close()
    m = sqlite3.connect("file:%s?mode=ro" % MESS, uri=True)
    mess = {r[0].upper(): r[1] for r in
            m.execute("SELECT symbol, assetklasse FROM messreihen")}
    # ⚠️⚠️ DER STATUS ENTSCHEIDET, OB "ALT" EIN MANGEL IST (08.09.2026).
    # Ein EINGESTELLTES Paar handelt nicht mehr - seine Reihe ist
    # VOLLSTAENDIG, nicht veraltet. Die erste Fassung zaehlte alle 174
    # eingestellten Krypto-Reihen als Mangel und haette das Paket
    # dauerhaft rot gehalten fuer etwas, das kein Fehler ist.
    status = {r[0].upper(): r[1] for r in
              m.execute("SELECT symbol, status FROM messreihen_status")}
    letzte = {}
    for sym, kl, tag in m.execute(
            "SELECT symbol, assetklasse, MAX(date) FROM price_history_ohlc "
            "GROUP BY symbol, assetklasse"):
        letzte[(sym.upper(), kl)] = tag
    m.close()
    return wl, best, prod, mess, letzte, status


def pruefe(still: bool = False) -> list:
    """Gibt die Liste der MAENGEL zurueck - leer heisst sauber."""
    def sag(*a):
        if not still:
            print(*a)

    wl, best, prod, mess, letzte, status = _lies()
    maengel = []

    sag("=" * 96)
    sag("IST JEDES ASSET SAUBER AUFGENOMMEN?")
    sag("=" * 96)
    sag("  Watchlist %d · Bestaende %d · Messreihen %d"
        % (len(wl), len(best), len(mess)))

    # ---- FALL 1: NEU - ohne Messreihe ---------------------------------
    zu_pruefen = {}
    for s in set(wl) | best:
        e = wl.get(s) or {}
        if e.get("klasse") != "krypto":
            continue            # Nicht-Krypto hat eine eigene Messbasis
        if e.get("cash") or s in AUSNAHMEN:
            continue
        zu_pruefen[s] = e
    ohne = sorted(s for s in zu_pruefen if s not in mess)
    sag("")
    sag("  1  NEU — Krypto in Watchlist/Bestand OHNE Messreihe")
    if not ohne:
        sag("     ✔ keines")
    for s in ohne:
        e = zu_pruefen[s]
        gehalten = s in best
        ph = prod.get(s, 0)
        sag("     %-10s rolle=%-9s %s · Produktions-Historie %d Zeilen%s"
            % (s, e.get("rolle") or "—",
               "GEHALTEN" if gehalten else "nur Watchlist", ph,
               "  -> nur uebernehmen" if ph >= 200 else "  ⚠️ auch dort keine"))
        if gehalten:
            # ⚠️ ZWEI VERSCHIEDENE URSACHEN, und die erste Fassung warf sie
            # zusammen: nach der Uebernahme vom 08.09. meldete sie bei
            # ASTER und MON weiter "die Daten sind da, nur nicht
            # uebernommen" - dabei sind sie ZU KURZ. Die Zeilenzahl in
            # USD entscheidet, nicht die Gesamtzahl (EUR zaehlt mit).
            _usd = 0
            try:
                _c = sqlite3.connect("file:%s?mode=ro" % PROD, uri=True)
                _usd = _c.execute(
                    "SELECT COUNT(DISTINCT date) FROM price_history_ohlc "
                    "WHERE UPPER(symbol)=? AND currency='USD'", (s,)
                ).fetchone()[0]
                _c.close()
            except Exception:                                # noqa: BLE001
                pass
            if _usd == 0:
                grund = "auch in der Produktion KEINE Kursreihe"
            elif _usd < 400:
                grund = ("nur %d USD-Tage - unter der 400er-Grenze. Das "
                         "ist eine DATENLAGE-Grenze, keine "
                         "Nachlaessigkeit" % _usd)
            else:
                grund = ("%d USD-Tage vorhanden - `uebernehme_messreihen.py` "
                         "kann sie holen" % _usd)
            maengel.append("%s ist GEHALTEN, hat aber keine Messreihe "
                           "(rolle=%s) - %s"
                           % (s, e.get("rolle") or "?", grund))
    if AUSNAHMEN:
        sag("     ⚠️ Ausgenommen mit Grund: %s" % ", ".join(AUSNAHMEN))

    # ---- FALL 2: FAELLT WEG - nur berichtet ---------------------------
    verwaist = sorted(s for s, k in mess.items()
                      if k == "krypto" and s not in wl and s not in best)
    sag("")
    sag("  2  FAELLT WEG — in der Messbasis, aber weder Watchlist noch Bestand")
    sag("     %d Symbole. ⚠️ DAS IST KEIN MANGEL: P6 verlangt, dass die"
        % len(verwaist))
    sag("        Messbasis BREITER ist als das Portfolio. Nur berichtet.")

    # ---- FALL 3: AENDERT SICH - Frische je Klasse ---------------------
    import datetime as _d
    heute = _d.date.today()
    sag("")
    sag("  3  AENDERT SICH — wie frisch ist die Messbasis je Klasse?")
    je_klasse, eingestellt_je = {}, {}
    for (sym, kl), tag in letzte.items():
        if status.get(sym) == "eingestellt":
            eingestellt_je[kl] = eingestellt_je.get(kl, 0) + 1
            continue        # ⚠️ vollstaendig, nicht veraltet
        je_klasse.setdefault(kl, []).append(tag)
    # ⚠️⚠️ NICHT DAS MAXIMUM. Die erste Fassung nahm `max(letzter Tag)` je
    # Klasse - und meldete "krypto 1 Tag alt", weil SECHS nachgeladene
    # Reihen bis zum 07.09. reichen, waehrend 342 am 21.08. enden. Eine
    # einzige frische Reihe laesst die ganze Klasse frisch aussehen.
    # Gemessen wird deshalb der MEDIAN und der Anteil der veralteten.
    sag("     ⚠️ Nur HANDELNDE Reihen. Eingestellte sind vollstaendig,")
    sag("        nicht veraltet - sie werden getrennt ausgewiesen.")
    sag("     %-12s %8s %12s %10s %13s %11s"
        % ("Klasse", "handelnd", "Median-Tag", "Alter Med.", "veraltet",
           "eingestellt"))
    for kl in sorted(je_klasse):
        tage = sorted(je_klasse[kl])
        med = tage[len(tage) // 2]
        try:
            alter = (heute - _d.date.fromisoformat(med[:10])).days
        except ValueError:
            alter = -1
        veraltet = 0
        for t in tage:
            try:
                if (heute - _d.date.fromisoformat(t[:10])).days > FRISCHE_GRENZE_TAGE:
                    veraltet += 1
            except ValueError:
                veraltet += 1
        anteil = 100.0 * veraltet / max(1, len(tage))
        sag("     %-12s %8d %12s %8d T %6d (%3.0f %%) %11d%s"
            % (kl, len(tage), med, alter, veraltet, anteil,
               eingestellt_je.get(kl, 0),
               "  ⚠️ VERALTET" if alter > FRISCHE_GRENZE_TAGE else ""))
        if alter > FRISCHE_GRENZE_TAGE:
            maengel.append(
                "Messbasis `%s`: die MEDIAN-Reihe ist %d Tage alt (%s), "
                "%d von %d Reihen (%.0f %%) sind aelter als %d Tage"
                % (kl, alter, med, veraltet, len(tage), anteil,
                   FRISCHE_GRENZE_TAGE))

    # ---- FALL 4: gehalten, aber ohne jeden BEITRAG --------------------
    sag("")
    sag("  4  BEITRAGSLAGE der gehaltenen Krypto-Positionen")
    try:
        import messe_bewertungskennzahl as MB
        import messe_funding_niveau as F
        import messe_kandidaten_als_regel as K
        hat = ({s.upper() for s in F.lade_funding()}
               | {s.upper() for s in MB.reihe("data/onchain_historie.db",
                                              "splycur")}
               | {s.upper() for s in K.lade_terminmarkt()["oi_aenderung"]})
    except Exception as exc:                                 # noqa: BLE001
        sag("     ⚠️ Beitragsquellen nicht lesbar: %s" % str(exc)[:60])
        hat = None
    if hat is not None:
        gehalten_kry = sorted(s for s in best
                              if (wl.get(s) or {}).get("klasse") == "krypto"
                              and s not in AUSNAHMEN)
        ohne_b = [s for s in gehalten_kry if s not in hat]
        sag("     %d gehaltene Krypto-Werte · davon OHNE jeden Beitrag: %d"
            % (len(gehalten_kry), len(ohne_b)))
        if ohne_b:
            sag("     %s" % ", ".join(ohne_b))
            sag("     ⚠️ EINORDNUNG (Nutzervorgabe 07.09.): bei Meme- und")
            sag("        Smallcap-Werten ist eine fehlende Bewertung")
            sag("        UNKRITISCH. Kritisch waere sie bei Kernwerten.")
        kern = [s for s in ohne_b if (wl.get(s) or {}).get("rolle") == "core"]
        if kern:
            maengel.append("KERNWERTE ohne jeden Beitrag: %s"
                           % ", ".join(kern))

    sag("")
    sag("=" * 96)
    if maengel:
        sag("  ⚠️⚠️ %d MANGEL:" % len(maengel))
        for x in maengel:
            sag("     - %s" % x)
    else:
        sag("  ✔✔ Kein Mangel.")
    return maengel


if __name__ == "__main__":
    sys.exit(1 if pruefe() else 0)
