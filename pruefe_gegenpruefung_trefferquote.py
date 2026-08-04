"""Punkt (a): Erkennt der Konsistenzpruefer echte Widersprueche? (2026-08-04)

DIE FRAGE ist nicht, ob Z.ais Urteil den Handelsausgang vorhersagt - das
waere eine Kategorienverwechslung, LLM2 ist ein Konsistenzpruefer und kein
Prognosemodell. Die Frage ist, ob es tut, wofuer es gebaut wurde:
widerspricht die Kurzbegruendung des Primaermodells den harten Fakten?

DAS MESSPROBLEM. Es gibt keine unabhaengige Wahrheit darueber, welche echten
Signale einen Widerspruch enthielten - Z.ais eigenes Urteil kann nicht sein
eigener Massstab sein. Nachtraeglich von Hand zu urteilen waere subjektiv und
bei 599 Faellen nicht durchfuehrbar.

DIE LOESUNG: WIDERSPRUECHE EINBAUEN. Zu einem echten Signal wird die
Begruendung gezielt so verfaelscht, dass sie einem bestimmten harten Fakt
widerspricht. Damit ist die Wahrheit bekannt, und zwei Groessen werden
messbar:

    TREFFERQUOTE   von den eingebauten Widerspruechen: wie viele erkannt?
    FEHLALARMQUOTE von den unveraenderten Begruendungen: wie viele faelschlich
                   als Widerspruch gemeldet?

Beide zusammen. Eine Trefferquote allein ist wertlos - ein Pruefer, der
IMMER "widerspruch" sagt, haette 100 % davon.

DIE VERFAELSCHUNGEN sind bewusst unterschiedlich schwer. Ein Pruefer, der nur
die plumpen findet, ist etwas anderes als einer, der auch feine erkennt - und
diese Abstufung ist die eigentlich nuetzliche Information.

`zai_client` ist austauschbar, damit die Auswertung mit einem nachgebildeten
Pruefer geprueft werden kann, bevor echtes Kontingent fliesst (selbsttest()).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

from agent.krypto.gegenpruefung import pruefe_konsistenz


@dataclass
class Verfaelschung:
    """Ein eingebauter Widerspruch mit bekannter Wahrheit."""

    name: str
    schwere: str            # "plump" | "mittel" | "fein"
    fakt_pfad: str          # welcher Fakt widersprochen wird
    text: str               # die verfaelschte Begruendung


# Die Faelle beziehen sich auf Fakten, die in JEDEM Hebel-Signal stehen -
# sonst waere der Widerspruch keiner, sondern eine Aussage ueber etwas
# Unbekanntes.
VERFAELSCHUNGEN = [
    Verfaelschung(
        "Regime umgedreht", "plump", "regime.wert",
        "Das Marktregime ist klar bullisch und stuetzt einen Long-Einstieg "
        "ohne Vorbehalte."),
    Verfaelschung(
        "Richtung gegen die Zonen", "plump", "zonen",
        "Ich erwarte fallende Kurse, deshalb liegt das Kursziel unter dem "
        "Einstieg."),
    Verfaelschung(
        "Funding-Rate umgedreht", "mittel", "antizyklisch.funding_rate_extrem",
        "Die Funding-Rate ist neutral und gibt keinen Hinweis auf eine "
        "einseitige Positionierung."),
    Verfaelschung(
        "Konfluenz behauptet", "mittel", "technische_analyse.confluence",
        "Alle technischen Indikatoren zeigen einheitlich in dieselbe "
        "Richtung, es gibt keinen Widerspruch."),
    Verfaelschung(
        "Trend gegen BTC", "fein", "regime.btc_trend",
        "Der uebergeordnete Bitcoin-Trend laeuft aufwaerts und traegt die "
        "These mit."),
    Verfaelschung(
        "Stop-Abstand falsch benannt", "fein", "zonen",
        "Der Stop liegt sehr eng am Einstieg, das Risiko je Position ist "
        "dadurch minimal."),
]


def messe(zai_client, faelle: list[tuple[dict, str]],
          verfaelschungen: list[Verfaelschung] = None) -> dict:
    """faelle = [(fakten, echte_begruendung), ...] aus realen Signalen."""
    verfaelschungen = verfaelschungen or VERFAELSCHUNGEN
    treffer: dict[str, list[bool]] = {}
    fehlalarm: list[bool] = []

    for fakten, begruendung in faelle:
        # Arm 1: unveraendert - jede Meldung ist ein Fehlalarm
        erg = pruefe_konsistenz(zai_client, fakten, begruendung)
        if erg is not None:
            fehlalarm.append(erg["urteil"] == "widerspruch")
        # Arm 2: je Verfaelschung ein eingebauter Widerspruch
        for v in verfaelschungen:
            erg = pruefe_konsistenz(zai_client, fakten, v.text)
            if erg is not None:
                treffer.setdefault(v.name, []).append(
                    erg["urteil"] == "widerspruch")

    def quote(werte):
        return (sum(werte) / len(werte)) if werte else None

    je_schwere: dict[str, list[bool]] = {}
    for v in verfaelschungen:
        je_schwere.setdefault(v.schwere, []).extend(treffer.get(v.name, []))

    return {
        "n_faelle": len(faelle),
        "fehlalarmquote": quote(fehlalarm),
        "n_fehlalarm": len(fehlalarm),
        "je_verfaelschung": {v.name: (v.schwere, quote(treffer.get(v.name, [])),
                                      len(treffer.get(v.name, [])))
                             for v in verfaelschungen},
        "je_schwere": {s: quote(w) for s, w in je_schwere.items()},
        "trefferquote_gesamt": quote([x for w in treffer.values() for x in w]),
    }


def bericht(e: dict) -> str:
    z = [f"{e['n_faelle']} echte Signale, {len(e['je_verfaelschung'])} Verfaelschungen"]
    fa = e["fehlalarmquote"]
    z.append(f"  FEHLALARMQUOTE (unveraenderte Begruendung faelschlich "
             f"gemeldet): {fa*100:.1f} %  (n={e['n_fehlalarm']})"
             if fa is not None else "  FEHLALARMQUOTE: keine Daten")
    tq = e["trefferquote_gesamt"]
    z.append(f"  TREFFERQUOTE gesamt: {tq*100:.1f} %" if tq is not None
             else "  TREFFERQUOTE: keine Daten")
    z.append("")
    z.append(f"  {'Verfaelschung':32s} {'Schwere':9s} {'erkannt':>9s} {'n':>4s}")
    for name, (schwere, q, n) in e["je_verfaelschung"].items():
        z.append(f"  {name:32s} {schwere:9s} "
                 f"{(f'{q*100:.0f} %' if q is not None else '-'):>9s} {n:4d}")
    z.append("")
    for s in ("plump", "mittel", "fein"):
        q = e["je_schwere"].get(s)
        if q is not None:
            z.append(f"  Schwere {s:7s}: {q*100:5.1f} % erkannt")
    return "\n".join(z)


def urteil(e: dict) -> str:
    tq, fa = e["trefferquote_gesamt"], e["fehlalarmquote"]
    if tq is None or fa is None:
        return "unbestimmt - zu wenig Daten"
    if fa > 0.5:
        return ("UNBRAUCHBAR: meldet auch bei unveraenderten Begruendungen "
                f"in {fa*100:.0f} % der Faelle Widerspruch - die Trefferquote "
                "sagt dann nichts aus")
    if tq < 0.5:
        return (f"SCHWACH: findet nur {tq*100:.0f} % der eingebauten "
                "Widersprueche")
    if tq >= 0.8 and fa <= 0.2:
        return (f"BRAUCHBAR: {tq*100:.0f} % erkannt bei {fa*100:.0f} % "
                "Fehlalarm")
    return (f"BEDINGT: {tq*100:.0f} % erkannt, {fa*100:.0f} % Fehlalarm - "
            "je nach Verwendung zu wenig trennscharf")


# --- Selbsttest mit nachgebildetem Pruefer ---------------------------------
def selbsttest() -> int:
    class Nachbau:
        """Ein Z.ai-Ersatz mit bekanntem Verhalten."""

        def __init__(self, erkennt: set[str], falschmeldung: float = 0.0):
            self.erkennt, self.falschmeldung, self.i = erkennt, falschmeldung, 0

        def chat(self, messages, **_kw):
            import json as j
            inhalt = j.loads(messages[-1]["content"])
            text = inhalt["begruendungstext"]
            passt = any(v.text == text and v.schwere in self.erkennt
                        for v in VERFAELSCHUNGEN)
            self.i += 1
            if not passt and self.falschmeldung:
                passt = (self.i % max(1, int(1 / self.falschmeldung))) == 0
            return j.dumps({"urteil": "widerspruch" if passt else "konsistent",
                            "kurzbegruendung": "test"})

    fakten = {"regime": {"wert": "baer", "btc_trend": "abwärts"},
              "antizyklisch": {"funding_rate_extrem": True},
              "technische_analyse": {"confluence": {"gesamttendenz": "gemischt"}}}
    faelle = [(fakten, "Baerisches Regime, Funding extrem, Konfluenz gemischt.")
              for _ in range(5)]

    fehler = []
    print("=== Selbsttest mit nachgebildetem Pruefer ===")
    for name, client, erwartet in (
        ("perfekt (erkennt alles, kein Fehlalarm)",
         Nachbau({"plump", "mittel", "fein"}), "BRAUCHBAR"),
        ("nur plumpe Widersprueche",
         Nachbau({"plump"}), "SCHWACH"),
        ("Dauermelder (sagt fast immer widerspruch)",
         Nachbau({"plump", "mittel", "fein"}, falschmeldung=0.9), "UNBRAUCHBAR"),
    ):
        e = messe(client, faelle)
        u = urteil(e)
        print()
        print(f"--- {name} ---")
        print(bericht(e))
        print(f"  -> {u}")
        ok = u.startswith(erwartet)
        print(f"  {'OK  ' if ok else 'FEHL'}  erwartet: {erwartet}")
        if not ok:
            fehler.append(name)

    print()
    if fehler:
        print(f"FEHLGESCHLAGEN: {fehler}")
        return 1
    print("Verfahren trennt brauchbare von unbrauchbaren Pruefern.")
    print("Der echte Lauf braucht den Z.ai-Schluessel (Notebook).")
    return 0


if __name__ == "__main__":
    raise SystemExit(selbsttest())
