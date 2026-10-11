"""Hebel Schritt B (P11, O36, 11.10.2026): die Bitpanda-Hebel-Wallets gegen die offenen ``hebel_positions`` - NUR LESEND.

Nutzer 11.10.: *"ja Buendelung ist ok"* (Voranalyse Plan Schritt 53 G-T).

WARUM: ``hebel_positions`` baut der Importer aus der alten API (``importer/bitpanda_margin_positions.py``). Er behandelt eine
TEILschliessung als Vollschluss (Befund 2.679) - danach fehlen Restmenge und Restkredit, die H15-Liquidation laege zu tief (unsichere
Seite), die REGEL0-Erinnerung entfiele. Bitpanda selbst fuehrt die Wahrheit in zwei Wallets je Konto:

    margin-trading         je Asset die gehaltene Hebelmenge          <->  Summe positionsmenge der offenen Positionen je Symbol
    margin-trading-credit  der Kredit (negativ, auf dem EURCV-Asset)  <->  Summe kreditbetrag_eur aller offenen Positionen

Beide liegen schon in der Datenbank (``bitpanda_wallet_saldo`` aus dem Bestands-Job, ``bitpanda_katalog`` fuer ID -> Symbol) - kein
Netz. Diese Wache MELDET nur; die Korrektur des Importers ist ein Schreiber in die Produktion und eigenes Paket (P11b).

ZEITVERSATZ: Wallet-Salden kommen alle 30 min (Bestands-Job, neue API), Positionen alle 15 min (Hebel-Sync, alte API). Eine
Abweichung zaehlt deshalb erst, wenn sie in ZWEI Laeufen hintereinander besteht (``bestaetigt``).
"""
from __future__ import annotations

TOL_MENGE_REL = 1e-6      # Mengen sind exakt (8 Nachkommastellen); relativ, damit Rundung bei grossen Mengen nicht meldet
TOL_MENGE_ABS = 1e-8
TOL_KREDIT_EUR = 1.0      # Kredit in EUR; Bitpanda fuehrt ihn auf den Cent, der Importer summiert Buchungen


def _gleich_menge(a: float, b: float) -> bool:
    return abs(a - b) <= max(TOL_MENGE_ABS, TOL_MENGE_REL * max(abs(a), abs(b)))


def pruefe(conn) -> dict:
    """Vergleich je Symbol und fuer den Kredit. Rueckgabe {'zeilen': [...], 'kredit': {...}, 'ok': bool, 'abweichungen': [schluessel]}.
    Liest nur. Fehlt eine Tabelle, steht ``fehlt`` drin (kein Fehler nach aussen, der Aufrufer zeigt es)."""
    tab = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("bitpanda_wallet_saldo", "hebel_positions", "bitpanda_katalog"):
        if t not in tab:
            return {"fehlt": t, "zeilen": [], "kredit": None, "ok": None, "abweichungen": []}
    sym = {aid: s for aid, s in conn.execute("SELECT asset_id, symbol FROM bitpanda_katalog")}
    wallet, wallet_zeit = {}, {}
    kredit_wallet, kredit_zeit = 0.0, None
    for aid, owner, saldo, zeit in conn.execute(
            "SELECT asset_id, wallet_owner, saldo, zeitpunkt FROM bitpanda_wallet_saldo WHERE wallet_owner IN "
            "('margin-trading', 'margin-trading-credit')"):
        if owner == "margin-trading-credit":
            kredit_wallet += float(saldo or 0)
            kredit_zeit = max(filter(None, (kredit_zeit, zeit))) if (kredit_zeit or zeit) else None
            continue
        s = sym.get(aid, aid)
        wallet[s] = wallet.get(s, 0.0) + float(saldo or 0)
        wallet_zeit[s] = max(filter(None, (wallet_zeit.get(s), zeit))) if (wallet_zeit.get(s) or zeit) else None
    pos, pos_kredit = {}, 0.0
    for s, menge, kredit in conn.execute(
            "SELECT symbol, positionsmenge, kreditbetrag_eur FROM hebel_positions WHERE geschlossen_am IS NULL"):
        pos.setdefault(s, []).append(menge)
        pos_kredit += float(kredit or 0)
    zeilen, abw = [], []
    for s in sorted(set(pos) | {k for k, v in wallet.items() if abs(v) > TOL_MENGE_ABS}):
        mengen = pos.get(s, [])
        w = wallet.get(s, 0.0)
        if any(m is None for m in mengen):
            art = "positionsmenge fehlt"
        elif not mengen:
            art = "Wallet ohne Position"
        elif w == 0 and mengen:
            art = "Position ohne Wallet"
        else:
            art = "ok" if _gleich_menge(w, sum(mengen)) else "Menge weicht ab"
        p = sum(m for m in mengen if m is not None) if mengen else 0.0
        zeilen.append({"symbol": s, "wallet": w, "position": p, "positionen": len(mengen), "art": art, "wallet_zeit": wallet_zeit.get(s)})
        if art != "ok":
            abw.append("menge:%s" % s)
    k_ok = abs(-kredit_wallet - pos_kredit) <= TOL_KREDIT_EUR
    kredit = {"wallet": kredit_wallet, "positionen": pos_kredit, "ok": k_ok, "wallet_zeit": kredit_zeit}
    if not k_ok:
        abw.append("kredit")
    return {"zeilen": zeilen, "kredit": kredit, "ok": not abw, "abweichungen": abw}


def zeile(erg: dict) -> str:
    """Die eine Logzeile (Kennzeile fuer die Kontrolle K-HW-1) und Zeile in Teilexport/Statusseite."""
    if erg.get("fehlt"):
        return "Hebel-Wallet-Abgleich: Tabelle %s fehlt - nicht pruefbar" % erg["fehlt"]
    teile = ["%s %s" % (z["symbol"], "ok" if z["art"] == "ok" else "%s (Wallet %.8g / Position %.8g)" % (z["art"], z["wallet"], z["position"]))
             for z in erg["zeilen"]]
    k = erg["kredit"]
    teile.append("Kredit %s" % ("ok" if k["ok"] else "weicht ab (Wallet %.2f / Positionen %.2f EUR)" % (-k["wallet"], k["positionen"])))
    return "Hebel-Wallet-Abgleich: " + (" · ".join(teile) if teile else "keine Hebelposition, keine Hebel-Wallet")


_VORHER: set = set()


def bestaetigt(erg: dict, vorher: set | None = None) -> list:
    """Abweichungen, die schon im VORIGEN Lauf bestanden (Zeitversatz der beiden Quellen). Merkt sich den Lauf im Prozess -
    nach einem Neustart zaehlt der erste Lauf als 'vorher' (frueheste Meldung im zweiten Lauf, ~15 min)."""
    global _VORHER
    alt = _VORHER if vorher is None else vorher
    jetzt = set(erg.get("abweichungen") or [])
    if vorher is None:
        _VORHER = jetzt
    return sorted(jetzt & alt)


def mail(erg: dict, schluessel: list) -> tuple:
    """(Betreff, Text) - eine Handlung (E-91): was nicht passt, was zu tun ist."""
    namen = [s.split(":", 1)[1] for s in schluessel if s.startswith("menge:")] + (["Kredit"] if "kredit" in schluessel else [])
    betreff = "Hebelposition passt nicht zu Bitpanda: %s" % ", ".join(namen)
    z = ["WAS ZU TUN IST", "  In Bitpanda die Hebelposition(en) %s ansehen - die gespeicherte Position stimmt nicht mit Bitpanda ueberein." %
         ", ".join(namen),
         "  Bis zur Klaerung sind Liquidationspreis und Hebelfuehrung (H15) dieser Position(en) NICHT verlaesslich.", "",
         "WAS NICHT PASST"]
    for x in erg["zeilen"]:
        if x["art"] != "ok":
            z.append("  %-8s %s - Bitpanda-Wallet %.8g, gespeicherte Position(en) %.8g (%d)" % (x["symbol"], x["art"], x["wallet"], x["position"],
                                                                                           x["positionen"]))
    k = erg["kredit"]
    if not k["ok"]:
        z.append("  Kredit   Bitpanda %.2f EUR, gespeicherte Positionen %.2f EUR" % (-k["wallet"], k["positionen"]))
    z += ["", "WARUM", "  Haeufigste Ursache: eine TEILschliessung, die der Importer als Vollschluss bucht (Befund 2.679).",
          "  Die Korrektur des Importers ist vorbereitet (P11b) und wird mit dir abgestimmt.", "",
          "TECHNIK", "  Abgleich alle 15 min im Hebel-Job, gemeldet erst nach zwei Laeufen in Folge; Sperrfrist 6 h je Abweichung.",
          "  " + zeile(erg)]
    return betreff, "\n".join(z)
