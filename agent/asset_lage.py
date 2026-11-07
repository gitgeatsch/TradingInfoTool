"""G19 B2/B4 — der Fakt-Sammler der Asset-Karte und sein Job-Lauf (E-171, 07.11.2026; Fassung 2 nach der Code-Gegenpruefung).

Je Bestand, je REGEL0-Signal und je offener Hebelposition alle FAKTEN mit Quelle, Stand und Zustand — dazu einmal die Fakten zum
ganzen Markt. Das ist Ebene 1 des Ebenenmodells (Datenbasis_Schichten_Sichten_28_10.md §1) und die spaetere Eingabe des Abwaegungs-LLM
(Fuetterung_Satzform_31_10.md §4, Block 2/3). KEINE Bewertung, kein Urteilswort, kein Signal (Ausweichregel E-169). Gemessene Saetze
der Mailzeilen (z. B. "in Gegenwind-Phasen fiel BTC ...", "geprueft an zwei Zyklen", Freigabe-Rhythmus) werden NICHT uebernommen -
sie sind Befunde, keine Fakten (Gegenpruefung Nr. 7); die Befund-Karte kommt erst mit B3.

Vorgaben (Voranalyse_G19_Dashboard_Bau_07_11.md):
- ⚠️ NUR LESEN. Jede Datei wird nur ``mode=ro`` geoeffnet, und nur wenn sie existiert (sonst entstuende eine leere Datei). Die
  schreibenden Oeffner ``regel0_ablage.oeffne``, ``binance_ankuendigungen.oeffne/mailteile_aus_ablage``, ``spot_upbit.oeffne``,
  ``season_ampel.oeffne`` und ``db.get_connection`` werden NIE benutzt (§4.2, §4.4).
- ⚠️ KEIN NETZ im Sammler. Die Termine (FRED) holt der Job und uebergibt sie.
- ⚠️ EIN DATENORDNER fuer alle Leser (§4.4) - sonst laese ein Pruefstand gegen Kopien teils die echten Dateien.
- ⚠️ DREI ZUSTAENDE je Angabe (§4.3): ``ok`` · ``leer`` (abgefragt, nichts da) · ``nicht abgefragt`` (Quelle fehlt, unlesbar, oder das
  Asset liegt nicht im Pruefkreis der Quelle - z. B. Upbit nur L-Bestaende, Binance-Ankuendigungen nur Krypto). Ein Lesefehler wird
  zu ``nicht abgefragt``, nie zum Abbruch des Laufs.
- Hebel: nur Liquidation, Abstand, Naehe-Stufe, Haltedauer. ``stop_eur``/``empfehlung`` haengen an der angehaltenen Rollen-Kette.
- Bestand = frei + gestakt; das Ergebnis steht "zum Kurs (Stand ...)", nie "realisiert".
- Der Job (``lauf``) schreibt nur ``<ordner>/asset_lage.db``. Wie bei jedem Job: ``job_laeufe`` (Scheduler-Listener) und - beim
  FRED-Abruf der Termine - ``api_health_status`` in der Produktion; der Zwischenspeicher von ``termin_fakt`` behaelt einen
  Fehlschlag des Jobs NICHT (sonst zeigte die REGEL0-Mail den ganzen Tag "nicht abgefragt", Gegenpruefung Nr. 9).
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

OK, LEER, NICHT = "ok", "leer", "nicht abgefragt"
PROD_NAME = "tradinginfotool.db"
SIGNAL_NAME = "regel0_signale.db"
SPOT_NAME = "spot_betrieb.db"
MAKRO_NAME = "makro_lage.json"
SICHTEN_REL = os.path.join("_sichten", "sichten.db")
FMT = "%Y-%m-%d %H:%M"
KRYPTO_GRUPPEN = ("coin", "token")                      # bitpanda_katalog.gruppe


# ══ Grundbausteine ═════════════════════════════════════════════════════════════════════════════════════════════════════════
def ro(pfad: str, zeilen: bool = False) -> sqlite3.Connection | None:
    """``mode=ro`` - oder None, wenn die Datei fehlt (nie anlegen)."""
    if not pfad or not os.path.isfile(pfad):
        return None
    c = sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=5)
    if zeilen:
        c.row_factory = sqlite3.Row
    return c


def _hat(c, tabelle: str) -> bool:
    return bool(c is not None and c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabelle,)).fetchone())


def _zeit(s) -> datetime | None:
    if s is None or s == "":
        return None
    if isinstance(s, datetime):
        d = s
    else:
        try:
            d = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00").replace(" ", "T", 1)[:32])
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _ende(signalstunde: str) -> datetime:
    return datetime.strptime(signalstunde, FMT).replace(tzinfo=timezone.utc) + timedelta(hours=1)


def fakt(schluessel: str, satz: str, quelle: str, *, wert=None, stand=None, zustand: str = OK, jetzt: datetime | None = None,
         bezug: str | None = None) -> dict:
    """Eine Angabe - immer mit Quelle, Stand und Zustand (Ue3, SF5). ``alter_h`` = Stunden zwischen Stand und Kartenzeit; ``bezug`` =
    Signalstunde, wenn die Angabe nur fuer DIESES Signal gilt (Ankuendigung zum Signalende, Kurs zur Signalstunde)."""
    st = _zeit(stand)
    alter = round((jetzt - st).total_seconds() / 3600, 1) if (st is not None and jetzt is not None) else None
    if zustand == NICHT and "NICHT ABGEFRAGT" not in satz:
        satz = "⚠ NICHT ABGEFRAGT (kein Nein): " + satz
    return {"schluessel": schluessel, "wert": wert, "satz": satz, "quelle": quelle, "stand": None if stand is None else str(stand),
            "alter_h": alter, "zustand": zustand, "kennzeichen": "Fakt", "bezug": bezug}


def _de(x: float, n: int = 1) -> str:
    return ("%.*f" % (n, x)).replace(".", ",")


def _preis(x: float) -> str:
    return _de(x, 6 if x < 1 else 2)


def _uhr(s) -> str:
    d = _zeit(s)
    return d.strftime("%d.%m. %H:%M") if d else str(s)


# ══ Welche Assets eine Karte bekommen (§4.1) ═══════════════════════════════════════════════════════════════════════════════
def _zuordnung() -> dict:
    from agent import betriebslage as BL
    return BL.zuordnung_bitpanda()                              # Bitpanda -> Binance (None = gesperrt), ohne Eintrag dasselbe Kuerzel


def signale_am(sig_c, tag: str, bis: datetime | None = None) -> list | None:
    """ALLE Signale des UTC-Tages (nicht nur hebel_schalter = 1), deren Signalstunde vor ``bis`` geschlossen hat (im Betrieb
    ohnehin so; im Pruefstand auf einer spaeteren Kopie waere alles danach ein Vorgriff). None = nicht abgefragt."""
    if not _hat(sig_c, "signal"):
        return None
    sp = ("symbol", "signalstunde", "einstieg", "ausstieg", "stufe_vorlaeufig", "stufe", "hebel_schalter", "bitpanda", "kurs",
          "kurs_markt", "mail_signal_am", "endgueltig_am")
    da = {r[1] for r in sig_c.execute('PRAGMA table_info("signal")')}
    sp = [s for s in sp if s in da]
    rows = sig_c.execute("SELECT %s FROM signal WHERE substr(signalstunde,1,10)=? ORDER BY signalstunde, symbol" % ", ".join(sp),
                         (tag,)).fetchall()
    aus = [dict(zip(sp, r)) for r in rows]
    if bis is not None:
        aus = [s for s in aus if _ende(s["signalstunde"]) <= bis]
    return aus


def assets(bestaende: dict, signale: list | None, hebel: list | None, zu: dict | None = None) -> list:
    """Bestaende ∪ Signale ∪ Hebel. Kartenschluessel = Bitpanda-Symbol; ein Signal ohne Bitpanda-Gegenstueck behaelt das
    Binance-Symbol und bekommt den Vermerk ``ohne_bitpanda``."""
    zu = _zuordnung() if zu is None else zu
    rueck = {}
    for bp, bn in zu.items():
        if bn:
            rueck.setdefault(bn, bp)
    karten: dict = {}

    def neu(k, bitpanda, binance):
        return karten.setdefault(k, {"schluessel": k, "bitpanda": bitpanda, "binance": binance, "anlass": [], "signale": [],
                                     "hebel": [], "ohne_bitpanda": bitpanda is None})

    for bp in sorted(bestaende):
        neu(bp, bp, zu.get(bp, bp))["anlass"].append("bestand")
    for s in signale or []:
        bp = (s.get("bitpanda") or "").strip() or rueck.get(s["symbol"]) or None
        k = neu(bp or s["symbol"], bp, s["symbol"])
        if "signal" not in k["anlass"]:
            k["anlass"].append("signal")
        k["signale"].append(s)
    for h in hebel or []:
        k = neu(h["symbol"], h["symbol"], zu.get(h["symbol"], h["symbol"]))
        if "hebel" not in k["anlass"]:
            k["anlass"].append("hebel")
        k["hebel"].append(h)
    return list(karten.values())


# ══ Markt - einmal oben (§4.2) ═════════════════════════════════════════════════════════════════════════════════════════════
def _season(ordner: str, jetzt: datetime) -> dict:
    q = "spot_betrieb.db/ampel_tag"
    try:
        from agent import season_ampel as SA
        if not os.path.isfile(os.path.join(ordner, SPOT_NAME)):
            return fakt("season", "Season-Ampel: Ablage fehlt", q, zustand=NICHT, jetzt=jetzt)
        u = SA.uebersicht(ordner)
        if u.get("zustand") not in ("ok", "veraltet") or not u.get("stufe"):
            return fakt("season", "Season-Ampel: kein Stand", q, zustand=NICHT, jetzt=jetzt)
        bed = " · ".join("%s %s %s" % (n, w, "✔" if an else "✗") for n, w, an, _ in (u.get("bedingungen") or []))
        satz = "Season-Ampel %s%s (%s von 3: %s) · Stand %s%s" % (
            u.get("stufe_name") or u["stufe"], (" seit %s" % u["seit"]) if u.get("seit") else "", u.get("stand"), bed,
            u.get("datum"), " ⚠ VERALTET" if u["zustand"] == "veraltet" else "")
        return fakt("season", satz, q, wert={"stufe": u["stufe"], "seit": u.get("seit")}, stand=u.get("datum"), jetzt=jetzt)
    except Exception as exc:                                     # noqa: BLE001
        return fakt("season", "Season-Ampel nicht lesbar (%s)" % type(exc).__name__, q, zustand=NICHT, jetzt=jetzt)


def _makro(ordner: str, jetzt: datetime) -> list:
    p = os.path.join(ordner, MAKRO_NAME)
    try:
        from agent import makro_lage as ML
        d = ML.lade(p) if os.path.isfile(p) else None
        if d is None:
            return [fakt("makro", "Makro-Lage: Ablage fehlt", MAKRO_NAME, zustand=NICHT, jetzt=jetzt),
                    fakt("gesamtmarkt", "Gesamtmarkt: Ablage fehlt", MAKRO_NAME, zustand=NICHT, jetzt=jetzt)]
        s = ML.stand(d)
        if s["zustand"] not in ("ok", "veraltet"):
            mk = fakt("makro", "Makro-Lage: kein Stand", MAKRO_NAME, zustand=NICHT, jetzt=jetzt)
        else:
            tr = ML.treiber(d, "kurz")
            mk = fakt("makro", "Makro-Lage lang %s · kurz %s%s · Stand %s%s" % (s["lang"], s["kurz"], (" (%s)" % ", ".join(tr)) if tr else "",
                                                                                 s.get("stand"), " ⚠ VERALTET" if s["zustand"] == "veraltet" else ""),
                      MAKRO_NAME, wert={"lang": s["lang"], "kurz": s["kurz"], "treiber": tr}, stand=s.get("stand"), jetzt=jetzt)
        gz = ML.zustand_gesamtmarkt(d)
        gm = (fakt("gesamtmarkt", "Gesamtmarkt " + ML.zeile_gesamtmarkt(d), MAKRO_NAME, stand=(d.get("gesamtmarkt") or {}).get("stand"),
                   jetzt=jetzt) if gz != "fehlt" else fakt("gesamtmarkt", "Gesamtmarkt: kein Stand", MAKRO_NAME, zustand=NICHT, jetzt=jetzt))
        return [mk, gm]
    except Exception as exc:                                     # noqa: BLE001
        return [fakt("makro", "Makro-Lage nicht lesbar (%s)" % type(exc).__name__, MAKRO_NAME, zustand=NICHT, jetzt=jetzt),
                fakt("gesamtmarkt", "Gesamtmarkt nicht lesbar (%s)" % type(exc).__name__, MAKRO_NAME, zustand=NICHT, jetzt=jetzt)]


def termin_fakt(termine: dict | None, jetzt: datetime) -> dict:
    """``termine`` = Ergebnis von ``termine_holen`` (vom Job) oder None. Fehlt auch nur EINE Art, gibt es kein 'leer' (kein Nein)."""
    q = "FRED/Fed-Liste (Job)"
    if termine is None:
        return fakt("termine", "Termine (FOMC, CPI, Arbeitsmarkt): nicht übergeben", q, zustand=NICHT, jetzt=jetzt)
    from agent.termin_fakt import NAME
    t = termine.get("termine") or []
    teile = ["%s %s UTC" % (NAME.get(e["art"], e["art"]), _uhr(e["utc"])) for e in t]
    fehlt = termine.get("nicht_abgefragt") or []
    satz = ("Termine nächste 7 Tage: " + " · ".join(teile)) if teile else "kein US-Inflations-, Arbeitsmarkt- oder Zinstermin in 7 Tagen"
    if termine.get("fehler"):
        satz = "Termine: Abruf gescheitert (%s)" % termine["fehler"]
    if fehlt:
        satz += " · ⚠ NICHT ABGEFRAGT (kein Nein): " + ", ".join(NAME.get(a, a) for a in fehlt)
    z = OK if teile else (NICHT if (fehlt or termine.get("fehler")) else LEER)
    return fakt("termine", satz, q, wert=[{"art": e["art"], "utc": str(e["utc"])} for e in t], stand=termine.get("geholt"), zustand=z,
                jetzt=jetzt)


def _sichten(ordner: str, jetzt: datetime) -> list:
    p = os.path.join(ordner, SICHTEN_REL)
    if not os.path.isfile(p):
        return [fakt("sichten", "Sicht-Zustände: sichten.db fehlt (am NB erst mit G8b)", SICHTEN_REL, zustand=NICHT, jetzt=jetzt)]
    try:
        from agent import zustaende as Z
        zs = Z.zustaende(jetzt.replace(tzinfo=None), Z.Ablage(p))
        aus = [fakt("sicht:%s:%s" % (z.sicht, z.name), ("● " if z.auffaellig else "") + z.satz, SICHTEN_REL, wert=z.mass_wert, stand=z.stand,
                    zustand=OK if (z.mass_wert is not None or z.stand) else LEER, jetzt=jetzt) for z in zs]
        return aus or [fakt("sichten", "Sicht-Zustände: keine", SICHTEN_REL, zustand=LEER, jetzt=jetzt)]
    except Exception as exc:                                     # noqa: BLE001
        return [fakt("sichten", "Sicht-Zustände nicht lesbar (%s)" % type(exc).__name__, SICHTEN_REL, zustand=NICHT, jetzt=jetzt)]


def markt(ordner: str, jetzt: datetime, termine: dict | None, mit_sichten: bool = True) -> list:
    aus = [_season(ordner, jetzt)] + _makro(ordner, jetzt) + [termin_fakt(termine, jetzt)]
    return aus + (_sichten(ordner, jetzt) if mit_sichten else [])


# ══ Je Asset (§4.2) ════════════════════════════════════════════════════════════════════════════════════════════════════════
def _kurse(prod_c, k, jetzt) -> list:
    """EUR-Kurs aus ``price_cache`` (Watchlist-Werte, Quelle ``price_cache``). Ohne ihn je Signal der Binance-Kurs zur Signalstunde
    (``signal.kurs``, Paar ``<symbol>USDT``, Quelle ``regel0_signale.db/signal.kurs``) - getrennt gezaehlt, nie als EUR."""
    kurs = stand = None
    if prod_c is not None and k["bitpanda"] is not None:
        try:
            from agent.positionsfuehrung import kurs_mit_stand
            kurs, stand = kurs_mit_stand(prod_c, k["bitpanda"])
        except Exception:                                        # noqa: BLE001
            return [fakt("kurs", "Kurs nicht lesbar", "price_cache", zustand=NICHT, jetzt=jetzt)]
    if kurs is not None:
        return [fakt("kurs", "Kurs %s EUR (Stand %s UTC)" % (_preis(kurs), _uhr(stand)), "price_cache", wert=kurs, stand=stand, jetzt=jetzt)]
    aus = [fakt("kurs", "Kurs zur Signalstunde %s UTC: %s USDT (Binance %s; kein EUR-Kurs, Wert nicht in der Watchlist)"
                % (s["signalstunde"][5:], _preis(float(s["kurs"])), s.get("kurs_markt") or "spot"), "regel0_signale.db/signal.kurs",
                stand=s["signalstunde"], jetzt=jetzt, bezug=s["signalstunde"]) for s in k["signale"] if s.get("kurs")]
    if aus:
        return aus
    if prod_c is None:
        return [fakt("kurs", "Kurs: Produktions-DB fehlt", "price_cache", zustand=NICHT, jetzt=jetzt)]
    return [fakt("kurs", "Kurs: keiner bekannt", "price_cache", zustand=LEER, jetzt=jetzt)]


def _bestand(h, kurs_fakt: dict, sync_stand, jetzt) -> dict:
    if h is None:
        return fakt("bestand", "kein Bestand", "holdings", wert=0.0, zustand=LEER, stand=sync_stand, jetzt=jetzt)
    from importer.bitpanda_avg_cost import compute_cost_basis_view
    kurs = kurs_fakt["wert"] if kurs_fakt.get("quelle") == "price_cache" else None
    menge = float(h.quantity or 0) + float(h.staked_quantity or 0)
    v = compute_cost_basis_view(h, kurs, menge=menge)            # Bestand = frei + gestakt
    teile = ["Bestand %s (frei %s, gestakt %s)" % (_de(menge, 6), _de(float(h.quantity or 0), 6), _de(float(h.staked_quantity or 0), 6))]
    if v.effective_avg_price_eur is not None:
        teile.append("Einstand %s EUR (%s)" % (_preis(v.effective_avg_price_eur), v.source))
    if v.pl_pct is not None:
        teile.append("Ergebnis zum Kurs %s%s %% (Kurs-Stand %s UTC)" % ("+" if v.pl_pct >= 0 else "", _de(v.pl_pct, 1), _uhr(kurs_fakt.get("stand"))))
    if v.unknown_quantity:
        teile.append("davon ohne Einstand %s" % _de(v.unknown_quantity, 6))
    teile.append("Bitpanda-Abgleich %s UTC" % _uhr(sync_stand) if sync_stand else "Bitpanda-Abgleich: Stand unbekannt")
    return fakt("bestand", " · ".join(teile), "holdings", stand=sync_stand, jetzt=jetzt,
                wert={"menge": menge, "frei": float(h.quantity or 0), "gestakt": float(h.staked_quantity or 0),
                      "einstand_eur": v.effective_avg_price_eur, "ergebnis_pct": v.pl_pct, "wert_eur": v.current_value_eur})


def _signale(k, jetzt) -> list:
    aus = []
    for s in k["signale"]:
        st = s.get("stufe") if s.get("stufe") is not None else s.get("stufe_vorlaeufig")
        teile = ["REGEL0-Signal %s UTC" % s["signalstunde"], "Stufe %s%s" % (st, "" if s.get("stufe") is not None else " (vorläufig)"),
                 "Einstieg %s · Ausstieg %s UTC" % (s.get("einstieg"), s.get("ausstieg")),
                 "Hebel-Schalter %s" % ("an" if s.get("hebel_schalter") else "aus")]
        if s.get("mail_signal_am"):
            teile.append("gemailt %s" % s["mail_signal_am"])
        aus.append(fakt("regel0_signal", " · ".join(teile), "regel0_signale.db/signal", wert=s,
                        stand=s.get("endgueltig_am") or s["signalstunde"], jetzt=jetzt, bezug=s["signalstunde"]))
    return aus


def _hebel(positionen: list, jetzt) -> list:
    aus = []
    for t in positionen:
        teile = ["Hebelposition %s %sx" % (t.get("richtung"), _de(float(t.get("hebel") or 0), 1))]
        if t.get("liquidation_eur"):
            teile.append("Liquidation etwa %s EUR" % _preis(t["liquidation_eur"]))
        ab = t.get("abstand_liquidation")
        if ab is not None:
            teile.append("Abstand %s %%" % _de(100.0 * ab, 1) if ab >= 0 else "⚠ Kurs JENSEITS der geschätzten Liquidation")
        if t.get("nahe_stufe"):
            teile.append("unter der Warnstufe %s %%" % _de(100.0 * float(t["nahe_stufe"]), 0))
        if t.get("haltedauer_text"):
            teile.append(t["haltedauer_text"])
        if t.get("wallet_hinweis"):
            teile.append(t["wallet_hinweis"])
        w = {x: t.get(x) for x in ("richtung", "hebel", "liquidation_eur", "abstand_liquidation", "nahe_stufe", "haltedauer_text")}
        aus.append(fakt("hebel", " · ".join(teile), "hebel_positions + Wallet (hebelfuehrung.lade)", wert=w, stand=t.get("kurs_stand"), jetzt=jetzt))
    return aus


def _ankuendigung(sig_c, k, krypto: bool, lauf_stand, jetzt) -> list:
    q = "regel0_signale.db/ankuendigung_ereignis"
    if not krypto or not k["binance"]:
        return [fakt("ankuendigung", "Binance-Ankündigungen: %s" % ("kein Krypto-Wert" if not krypto else "Binance-Zuordnung gesperrt"),
                     q, zustand=NICHT, jetzt=jetzt)]
    if sig_c is None or not _hat(sig_c, "ankuendigung_ereignis"):
        return [fakt("ankuendigung", "Binance-Ankündigungen: Ablage fehlt", q, zustand=NICHT, jetzt=jetzt)]
    try:
        from agent import binance_ankuendigungen as BA
        aus = []
        # Bezugszeitpunkt (Voranalyse §3.3): je Signal das Ende der Signalstunde (bezug); sonst die Kartenzeit
        bez = [(_ende(s["signalstunde"]), s["signalstunde"]) for s in k["signale"]] or [(jetzt, None)]
        for ende, b in bez:
            ev = BA.aktive(sig_c, k["binance"], ende)
            if not ev:
                aus.append(fakt("ankuendigung", "keine aktive Binance-Ankündigung (bis %s UTC; letzter Abruf %s UTC)" % (ende.strftime("%d.%m. %H:%M"),
                                _uhr(lauf_stand)), q, zustand=LEER, wert=[], stand=lauf_stand, jetzt=jetzt, bezug=b))
                continue
            teile = ["%s seit %s (%s)" % (x["art"], datetime.fromtimestamp(x["release_ms"] / 1000, timezone.utc).strftime("%d.%m."),
                                          (x.get("titel") or "")[:90]) for x in ev]
            aus.append(fakt("ankuendigung", "Binance: " + " · ".join(teile), q, stand=lauf_stand, jetzt=jetzt, bezug=b,
                            wert=[{"art": x["art"], "release_ms": x["release_ms"], "code": x["code"]} for x in ev]))
        return aus
    except Exception as exc:                                     # noqa: BLE001
        return [fakt("ankuendigung", "Binance-Ankündigungen nicht lesbar (%s)" % type(exc).__name__, q, zustand=NICHT, jetzt=jetzt)]


def _upbit(spot_c, k, im_kreis: bool, lauf_stand, jetzt) -> dict:
    q = "spot_betrieb.db/upbit_fall"
    if not im_kreis:
        return fakt("upbit", "Upbit: nicht im Prüfkreis (nur L-Bestände: Krypto-Bestand ohne Kern und Stablecoins)", q, zustand=NICHT, jetzt=jetzt)
    if spot_c is None or not _hat(spot_c, "upbit_fall"):
        return fakt("upbit", "Upbit: Ablage fehlt", q, zustand=NICHT, jetzt=jetzt)
    try:
        rows = spot_c.execute("SELECT kuerzel, utc, status, mail_am FROM upbit_fall WHERE symbol=? ORDER BY utc DESC", (k["bitpanda"],)).fetchall()
    except sqlite3.Error as exc:
        return fakt("upbit", "Upbit nicht lesbar (%s)" % type(exc).__name__, q, zustand=NICHT, jetzt=jetzt)
    if not rows:
        return fakt("upbit", "kein Upbit-Listing-Fall (letzter Abruf %s UTC)" % _uhr(lauf_stand), q, wert=[], zustand=LEER, stand=lauf_stand,
                    jetzt=jetzt)
    teile = ["Upbit-Listing %s am %s, Status %s" % (r[0], str(r[1])[:16], r[2]) for r in rows[:3]]
    return fakt("upbit", " · ".join(teile), q, wert=[list(r) for r in rows], stand=lauf_stand, jetzt=jetzt)


def _verwaesserung(ordner, reihen, zusatz, k, krypto: bool, jetzt) -> dict:
    q = "umlaufmenge_cg.db + verw_universum"
    if not krypto:
        return fakt("verwaesserung", "Verwässerung: kein Krypto-Wert", q, zustand=NICHT, jetzt=jetzt)
    if reihen is None:
        return fakt("verwaesserung", "Verwässerung: Umlaufmenge fehlt", q, zustand=NICHT, jetzt=jetzt)
    from agent import verwaesserung as VW
    f = VW.fakt(ordner, k["bitpanda"] or k["binance"], heute=jetzt.date(), reihen=reihen, zusatz=zusatz)
    if "hat_reihe" not in f:                                     # VW.fakt hat eine Ausnahme abgefangen
        return fakt("verwaesserung", f.get("text") or "Verwässerung nicht lesbar", q, zustand=NICHT, jetzt=jetzt)
    satz = VW.text(f)                                            # ohne den Freigabe-Rhythmus: der ist ein gemessener Satz (Nr. 7)
    if f.get("heute") is None:
        return fakt("verwaesserung", satz, q, zustand=LEER, jetzt=jetzt)
    return fakt("verwaesserung", satz, q, wert={x: f.get(x) for x in ("heute", "fuenftel", "klasse", "stichtag", "q_stichtag", "zusatz")},
                stand=f.get("stichtag"), jetzt=jetzt)


def _meta(prod_c, schluessel: str):
    try:
        r = prod_c.execute("SELECT value FROM meta WHERE key=?", (schluessel,)).fetchone()
        return r[0] if r else None
    except sqlite3.Error:
        return None


def _letzter(c, tabelle: str, spalte: str = "am"):
    try:
        if not _hat(c, tabelle):
            return None
        r = c.execute('SELECT MAX("%s") FROM "%s"' % (spalte, tabelle)).fetchone()
        return r[0] if r else None
    except sqlite3.Error:
        return None


def _krypto_menge(prod_c) -> set | None:
    try:
        return {r[0] for r in prod_c.execute("SELECT DISTINCT symbol FROM bitpanda_katalog WHERE gruppe IN (%s)"
                                             % ",".join("?" * len(KRYPTO_GRUPPEN)), KRYPTO_GRUPPEN)}
    except sqlite3.Error:
        return None


def _stablecoins() -> set:
    """Cash-Aequivalente der Grundliste (config.yaml, ``ist_cash_aequivalent``) - abgeleitet, nicht aufgezaehlt; liest keine DB."""
    try:
        from config import load_config
        return {e["symbol"] for e in (load_config().get("watchlist") or []) if e.get("ist_cash_aequivalent")}
    except Exception:                                            # noqa: BLE001
        return set()


# ══ Zusammen ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def sammle(ordner: str, jetzt: datetime | None = None, *, prod_pfad: str | None = None, termine: dict | None = None,
           tag: str | None = None, nur_signale: set | None = None, mit_sichten: bool = True, nahe_grenze: float | None = None) -> dict:
    """Alle Karten eines Laufs. ``ordner`` = Datenordner (Betrieb: ``regel0_nachlader.DATEN_VORGABE``), ``prod_pfad`` Vorgabe
    ``<ordner>/tradinginfotool.db``. ``nur_signale`` = Menge ``(symbol, signalstunde)``: nur diese Signalkarten (Stundenlauf) - sie
    tragen dieselben Asset-Fakten wie im Tageslauf (Bestand, Hebel), nur ohne den Markt-Block.
    -> {'jetzt', 'tag', 'markt': [fakt], 'karten': [{asset..., 'fakten': [fakt]}], 'zustaende': {quelle: {zustand: n}}}"""
    jetzt = (jetzt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    tag = tag or jetzt.strftime("%Y-%m-%d")
    prod_c = ro(prod_pfad or os.path.join(ordner, PROD_NAME), zeilen=True)
    sig_c = ro(os.path.join(ordner, SIGNAL_NAME))
    spot_c = ro(os.path.join(ordner, SPOT_NAME))
    extra = []
    try:
        from agent.kernwerte import KERN
        bestaende, hebel, prod_fehler = {}, None, None
        sync = _meta(prod_c, "bitpanda_holdings_synced_at") if prod_c is not None else None
        krypto = _krypto_menge(prod_c) if prod_c is not None else None
        if prod_c is not None:
            try:
                from database import db as DBM
                bestaende = {h.symbol: h for h in DBM.get_all_holdings(prod_c) if float(h.quantity or 0) + float(h.staked_quantity or 0) > 0}
            except sqlite3.Error as exc:
                prod_fehler = "%s: %s" % (type(exc).__name__, exc)
            try:
                from agent import hebelfuehrung as HF
                if nahe_grenze is None:
                    try:
                        nahe_grenze = __import__("agent.regel0_groesse", fromlist=["lade"]).lade()["liquidations_warnung_abstand"]
                    except Exception:                            # noqa: BLE001
                        nahe_grenze = None
                hebel = HF.lade(prod_c, jetzt=jetzt, daten=ordner, nahe_grenze=nahe_grenze)
            except Exception:                                    # noqa: BLE001
                hebel = None
        try:
            signale = signale_am(sig_c, tag, bis=jetzt) if sig_c is not None else None
        except sqlite3.Error as exc:
            signale = None
            extra.append(fakt("regel0_signale", "REGEL0-Signale nicht lesbar (%s)" % type(exc).__name__, SIGNAL_NAME, zustand=NICHT, jetzt=jetzt))
        if signale is None and not extra:
            extra.append(fakt("regel0_signale", "REGEL0-Signale: Ablage fehlt", SIGNAL_NAME, zustand=NICHT, jetzt=jetzt))
        if nur_signale is not None:
            signale = [s for s in (signale or []) if (s["symbol"], s["signalstunde"]) in nur_signale]
        hebel_je = {}
        for h in hebel or []:
            hebel_je.setdefault(h["symbol"], []).append(h)
        try:
            from agent import verwaesserung as VW
            reihen, zusatz = VW.alle_reihen(ordner) if os.path.isfile(os.path.join(ordner, "umlaufmenge_cg.db")) else (None, set())
        except Exception:                                        # noqa: BLE001
            reihen, zusatz = None, set()
        a_stand = _letzter(sig_c, "ankuendigung_lauf")
        u_stand = _letzter(spot_c, "upbit_lauf")
        stable = _stablecoins()
        karten = []
        liste = assets({} if nur_signale is not None else bestaende, signale, [] if nur_signale is not None else hebel)
        for k in liste:
            bp = k["bitpanda"]
            ist_krypto = bool(k["signale"]) or krypto is None or bp in krypto   # ein REGEL0-Signal ist immer ein Binance-Krypto-Wert
            f = _kurse(prod_c, k, jetzt)
            eur = next((x for x in f if x["quelle"] == "price_cache"), {"wert": None, "quelle": None, "stand": None})
            if prod_c is None or prod_fehler:
                f.append(fakt("bestand", "Bestand: %s" % (prod_fehler or "Produktions-DB fehlt"), "holdings", zustand=NICHT, jetzt=jetzt))
            else:
                f.append(_bestand(bestaende.get(bp) if bp else None, eur, sync, jetzt))
            f += _signale(k, jetzt)
            if prod_c is not None and hebel is None:
                f.append(fakt("hebel", "Hebelpositionen nicht lesbar", "hebelfuehrung.lade", zustand=NICHT, jetzt=jetzt))
            else:
                f += _hebel(hebel_je.get(bp, []) if bp else [], jetzt)
            f += _ankuendigung(sig_c, k, ist_krypto, a_stand, jetzt)
            im_kreis = bool(bp and bp in bestaende and ist_krypto and bp not in KERN and bp not in stable)
            f.append(_upbit(spot_c, k, im_kreis, u_stand, jetzt))
            f.append(_verwaesserung(ordner, reihen, zusatz, k, ist_krypto, jetzt))
            if k["ohne_bitpanda"]:
                f.append(fakt("zuordnung", "kein Bitpanda-Gegenstück zu %s (Karte unter dem Binance-Symbol)" % k["binance"],
                              "symbol_zuordnung.csv", zustand=LEER, jetzt=jetzt))
            karten.append(dict(k, fakten=f))
        m = (markt(ordner, jetzt, termine, mit_sichten=mit_sichten) if nur_signale is None else []) + extra
        zust: dict = {}
        for x in m + [y for k in karten for y in k["fakten"]]:
            q = x["schluessel"].split(":")[0] + (":signal" if x["quelle"] == "regel0_signale.db/signal.kurs" else "")
            zust.setdefault(q, Counter())[x["zustand"]] += 1
        return {"jetzt": jetzt.isoformat(timespec="seconds"), "tag": tag, "markt": m, "karten": karten,
                "zustaende": {q: dict(c) for q, c in zust.items()}}
    finally:
        for c in (prod_c, sig_c, spot_c):
            if c is not None:
                c.close()


def text(erg: dict, je_karte: int | None = None) -> str:
    """Lesbare Fassung (Pruefung, Diagnose) - keine Anzeige im Betrieb (E-171)."""
    z = ["ASSET-LAGE %s · %d Karten · nur Fakten (E-171)" % (erg["jetzt"], len(erg["karten"])), "", "── Markt ──"]
    z += ["  [%s] %s" % (f["zustand"], f["satz"]) for f in erg["markt"] if not f["schluessel"].startswith("sicht:")]
    n_s = sum(1 for f in erg["markt"] if f["schluessel"].startswith("sicht:"))
    if n_s:
        z.append("  [ok] %d Sicht-Zustände" % n_s)
    for k in erg["karten"][:je_karte] if je_karte else erg["karten"]:
        z += ["", "── %s · %s ──" % (k["schluessel"], ", ".join(k["anlass"]))]
        z += ["  [%s] %s" % (f["zustand"], f["satz"]) for f in k["fakten"]]
    z += ["", "Zustände je Quelle: " + " · ".join("%s %s" % (q, c) for q, c in sorted(erg["zustaende"].items()))]
    return "\n".join(z)


# ══ B4: Ablage und Lauf (E-171) - schreibt NUR <ordner>/asset_lage.db ══════════════════════════════════════════════════════
ABLAGE_NAME = "asset_lage.db"
NACHGEHOLT_H = 2.0          # Signalkarte spaeter als 2 h nach Schluss der Signalstunde -> 'nachgeholt' (nie in eine Wertmessung)
_SPERRE = threading.Lock()  # Tages- und Stundenlauf schreiben nie gleichzeitig


def oeffne_ablage(ordner: str) -> sqlite3.Connection:
    """Die EIGENE Ablage - die einzige Datei, in die dieses Modul schreibt."""
    c = sqlite3.connect(os.path.join(ordner, ABLAGE_NAME), timeout=30)
    c.execute("CREATE TABLE IF NOT EXISTS lauf (id INTEGER PRIMARY KEY AUTOINCREMENT, am TEXT, art TEXT, karten INTEGER, "
              "zustaende TEXT, fehler TEXT, sekunden REAL, grund TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS karte (id INTEGER PRIMARY KEY AUTOINCREMENT, lauf INTEGER, am TEXT, schluessel TEXT, "
              "bitpanda TEXT, binance TEXT, anlass TEXT, symbol TEXT, signalstunde TEXT, nachgeholt INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS fakt (karte INTEGER, schluessel TEXT, zustand TEXT, satz TEXT, wert TEXT, quelle TEXT, "
              "stand TEXT, alter_h REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS markt (lauf INTEGER, schluessel TEXT, zustand TEXT, satz TEXT, wert TEXT, quelle TEXT, "
              "stand TEXT, alter_h REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS termin (geholt TEXT PRIMARY KEY, inhalt TEXT)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS karte_signal ON karte (symbol, signalstunde) WHERE signalstunde IS NOT NULL")
    c.commit()
    return c


def _json(x) -> str | None:
    return None if x is None else json.dumps(x, ensure_ascii=False, default=str)


def termine_holen(jetzt: datetime, fred_key: str | None = None) -> dict:
    """Die naechsten 7 Tage (FRED + feste Fed-Liste) - der EINZIGE Netzzugriff, und er liegt im Job, nicht im Sammler. Ein
    Fehlschlag bleibt NICHT im Tagesspeicher von ``termin_fakt`` (der dient auch der REGEL0-Mail)."""
    from agent import termin_fakt as TF
    vorher = set(TF._SPEICHER)
    try:
        d = TF.termine(jetzt, jetzt + timedelta(days=7), fred_key)
    finally:
        for k in set(TF._SPEICHER) - vorher:
            if not TF._SPEICHER[k][1]:
                TF._SPEICHER.pop(k, None)
    d["geholt"] = jetzt.isoformat(timespec="seconds")
    return d


def _vorhandene(c_ablage) -> set:
    return {tuple(r) for r in c_ablage.execute("SELECT symbol, signalstunde FROM karte WHERE signalstunde IS NOT NULL")}


def offene_signale(ordner: str, c_ablage, jetzt: datetime) -> set | None:
    """(symbol, signalstunde) von gestern und heute (UTC) ohne Karte - ueber den SCHLUESSEL, nicht ueber die Uhrzeit (G19 §5.1).
    Ein Lesefehler (Sperre, Timeout) gibt None: dann bleibt alles offen und der naechste Lauf holt nach."""
    sig = ro(os.path.join(ordner, SIGNAL_NAME))
    if sig is None:
        return None
    try:
        alle = set()
        for tag in ((jetzt - timedelta(days=1)).strftime("%Y-%m-%d"), jetzt.strftime("%Y-%m-%d")):
            for s in signale_am(sig, tag, bis=jetzt) or []:
                alle.add((s["symbol"], s["signalstunde"]))
    except sqlite3.Error:
        return None
    finally:
        sig.close()
    return alle - _vorhandene(c_ablage)


def schreibe(c, erg: dict, art: str, sekunden: float, fehler: str | None = None, grund: str | None = None) -> int:
    """Ein Lauf ins Protokoll - auch einer ohne Karten. Je Signal eine eigene Karte (Schluessel symbol + signalstunde, EINDEUTIG:
    ein Signal, das schon eine Karte hat, bekommt keine zweite - der Tageslauf laeuft nach Stundenlaeufen, Gegenpruefung Nr. 1);
    ein Asset ohne (neues) Signal eine Karte ohne Signalschluessel. Angaben mit ``bezug`` gehen nur auf die Karte IHRES Signals."""
    jetzt = _zeit(erg["jetzt"]) if erg.get("jetzt") else datetime.now(timezone.utc)
    da = _vorhandene(c)
    lauf_id = c.execute("INSERT INTO lauf (am, art, karten, zustaende, fehler, sekunden, grund) VALUES (?,?,?,?,?,?,?)",
                        (jetzt.isoformat(timespec="seconds"), art, 0, _json(erg.get("zustaende")), fehler, round(sekunden, 2), grund)).lastrowid
    for f in erg.get("markt", []):
        c.execute("INSERT INTO markt VALUES (?,?,?,?,?,?,?,?)",
                  (lauf_id, f["schluessel"], f["zustand"], f["satz"], _json(f["wert"]), f["quelle"], f["stand"], f["alter_h"]))
    n = 0
    for k in erg.get("karten", []):
        neu = [s for s in k["signale"] if (s["symbol"], s["signalstunde"]) not in da]
        ziele = [(s["symbol"], s["signalstunde"]) for s in neu]
        if not ziele and (set(k["anlass"]) - {"signal"} or not k["signale"]):
            ziele = [(None, None)]                               # Bestand/Hebel ohne neues Signal: eine Karte ohne Signalschluessel
        for sym, sst in ziele:
            nach = int((jetzt - _ende(sst)).total_seconds() / 3600 > NACHGEHOLT_H) if sst else None
            kid = c.execute("INSERT INTO karte (lauf, am, schluessel, bitpanda, binance, anlass, symbol, signalstunde, nachgeholt) "
                            "VALUES (?,?,?,?,?,?,?,?,?)", (lauf_id, jetzt.isoformat(timespec="seconds"), k["schluessel"], k["bitpanda"],
                                                           k["binance"], ",".join(k["anlass"]), sym, sst, nach)).lastrowid
            n += 1
            for f in k["fakten"]:
                if f.get("bezug") and f["bezug"] != sst:
                    continue                                   # gehoert zu einem anderen Signal dieses Assets
                c.execute("INSERT INTO fakt VALUES (?,?,?,?,?,?,?,?)",
                          (kid, f["schluessel"], f["zustand"], f["satz"], _json(f["wert"]), f["quelle"], f["stand"], f["alter_h"]))
    c.execute("UPDATE lauf SET karten=? WHERE id=?", (n, lauf_id))
    c.commit()
    return lauf_id


def _summe(teile: list) -> dict:
    z: dict = {}
    for t in teile:
        for q, w in t["zustaende"].items():
            for k, n in w.items():
                z.setdefault(q, {}).setdefault(k, 0)
                z[q][k] += n
    return z


def lauf(ordner: str, art: str = "tag", jetzt: datetime | None = None, *, prod_pfad: str | None = None, termine: dict | None = None,
         holen: bool = True, fred_key: str | None = None) -> dict:
    """Ein Lauf des Jobs. ``art`` = 'tag' (alle Karten, taeglich) oder 'signal' (nur Signale ohne Karte, stuendlich). JEDER Lauf steht
    im Protokoll (auch 0 Karten, mit Grund; ein Fehler in ``lauf.fehler``). Schreibt NUR ``<ordner>/asset_lage.db``.
    Pruefstand: ``termine`` uebergeben oder ``holen=False`` - dann kein Netz."""
    if art not in ("tag", "signal"):
        raise ValueError("art muss 'tag' oder 'signal' sein")
    jetzt = (jetzt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    t0 = time.time()
    if art == "tag" and termine is None and holen:               # vor der Sperre: der Abruf kann dauern
        try:
            termine = termine_holen(jetzt, fred_key)
        except Exception as exc:                                 # noqa: BLE001
            termine = {"termine": [], "nicht_abgefragt": ["cpi", "nfp", "fomc"], "fehler": type(exc).__name__,
                       "geholt": jetzt.isoformat(timespec="seconds")}
    with _SPERRE:
        c = oeffne_ablage(ordner)
        try:
            erg, grund, fehler = {"jetzt": jetzt.isoformat(timespec="seconds"), "markt": [], "karten": [], "zustaende": {}}, None, None
            try:
                if art == "tag":
                    if termine is not None and holen:
                        c.execute("INSERT OR REPLACE INTO termin VALUES (?,?)", (termine["geholt"], _json(termine)))
                    erg = sammle(ordner, jetzt, prod_pfad=prod_pfad, termine=termine)
                else:
                    offen = offene_signale(ordner, c, jetzt)
                    if offen is None:
                        grund = "Signale nicht lesbar - nichts als erledigt vermerkt, naechster Lauf holt nach"
                    elif not offen:
                        grund = "keine neuen Signale"
                    else:
                        teile = [sammle(ordner, jetzt, prod_pfad=prod_pfad, tag=tg, nur_signale={x for x in offen if x[1][:10] == tg})
                                 for tg in sorted({sst[:10] for _, sst in offen})]
                        erg = {"jetzt": teile[0]["jetzt"], "markt": [m for t in teile for m in t["markt"]],
                               "karten": [k for t in teile for k in t["karten"]], "zustaende": _summe(teile)}
            except Exception as exc:                             # noqa: BLE001
                fehler = "%s: %s" % (type(exc).__name__, exc)
            lid = schreibe(c, erg, art, time.time() - t0, fehler=fehler, grund=grund)
            n = c.execute("SELECT karten FROM lauf WHERE id=?", (lid,)).fetchone()[0]
            aus = {"art": art, "lauf": lid, "karten": n, "zustaende": erg["zustaende"], "sekunden": round(time.time() - t0, 1)}
            if grund:
                aus["grund"] = grund
            if fehler:
                aus["fehler"] = fehler
            return aus
        finally:
            c.close()


def stand(ordner: str, jetzt: datetime | None = None) -> dict:
    """Fuer die Diagnose (K-AL-1/K-AL-2): letzter Lauf je Art mit Alter, Karten, Zustaenden, Grund und Fehler; Laeufe mit Fehler in
    24 h; Verzug der Signalkarten (nur Stundenlaeufe, ohne nachgeholte). Nur lesend."""
    jetzt = (jetzt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    p = os.path.join(ordner, ABLAGE_NAME)
    c = ro(p)
    if c is None:
        return {"zustand": "fehlt", "datei": ABLAGE_NAME}
    try:
        aus: dict = {"zustand": "ok"}
        for art in ("tag", "signal"):
            r = c.execute("SELECT am, karten, zustaende, fehler, sekunden, grund FROM lauf WHERE art=? ORDER BY id DESC LIMIT 1", (art,)).fetchone()
            if r:
                aus[art] = {"am": r[0], "alter_h": round((jetzt - _zeit(r[0])).total_seconds() / 3600, 1), "karten": r[1],
                            "zustaende": json.loads(r[2] or "{}"), "fehler": r[3], "sekunden": r[4], "grund": r[5]}
        aus["laeufe"] = c.execute("SELECT COUNT(*) FROM lauf").fetchone()[0]
        aus["fehler_24h"] = c.execute("SELECT COUNT(*) FROM lauf WHERE fehler IS NOT NULL AND am >= ?",
                                      ((jetzt - timedelta(hours=24)).isoformat(timespec="seconds"),)).fetchone()[0]
        aus["karten_gesamt"] = c.execute("SELECT COUNT(*) FROM karte").fetchone()[0]
        aus["signalkarten_nachgeholt"] = c.execute("SELECT COUNT(*) FROM karte WHERE nachgeholt=1").fetchone()[0]
        verz = c.execute("SELECT k.signalstunde, k.am FROM karte k JOIN lauf l ON l.id = k.lauf WHERE l.art = 'signal' "
                         "AND k.signalstunde IS NOT NULL AND COALESCE(k.nachgeholt, 0) = 0 ORDER BY k.id DESC LIMIT 200").fetchall()
        if verz:
            m = sorted((_zeit(am) - _ende(s)).total_seconds() / 60 for s, am in verz)
            aus["signalkarte_verzug_min"] = {"median": round(m[len(m) // 2], 1), "max": round(m[-1], 1), "n": len(m)}
        return aus
    finally:
        c.close()
