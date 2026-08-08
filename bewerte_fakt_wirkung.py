"""Nachweisrahmen je Fakt - Fakten-Entscheidungsmappe Kapitel 9, Stufe 3.

WAS HIER DAZUKOMMT, UND WARUM ES DER GANZE PUNKT IST. `messe_prompt_nebeneffekte`
misst seit dem 04.08. sauber, OB ein Fakt das Verhalten aendert: Uneinigkeit in
der `action`, Konfidenzverschiebung, Stop-Abstand, CRV - jeweils gegen den
Rauschboden aus zwei identischen Armen. Alles davon sind STELLGROESSEN.

Kapitel 9 benennt die Luecke in einem Satz:

    "Es fehlt der Bewerter, der aus einer geaenderten Entscheidung ein Ergebnis
     macht."

Der Befund vom 05./06.08. lautete "das Modell waehlt engere Stops". Ob engere
Stops hier BESSER sind, sagt diese Messung nicht. Dieses Modul schliesst das:
jede Arm-Antwort wird gegen die echte Kurshistorie bewertet (`simuliere_signal`,
abgenommen am 09.08. mit 97,0 % - auf dichten Reihen 100,0 %), und verglichen
wird in R.

VIER REGELN, DIE VOR DEM LAUF FESTSTEHEN MUESSEN. Sie sind Parameter von
`nachweisrahmen()` und werden mit dem Ergebnis zusammen ausgegeben - eine
Entscheidungsregel, die man nach dem Blick auf die Zahlen waehlt, ist keine.

  1. EROEFFNEN-WAECHTER, mit VORRANG vor jeder Ergebnisbilanz. Bricht die
     EROEFFNEN-Quote gegenueber A um mehr als `eroeffnen_einbruch_pp` ein, ist
     der Fakt disqualifiziert - unabhaengig davon, wie gut die R-Bilanz
     aussieht. Grund: bei einer Grundmenge aus ueberwiegend Verlierern ist
     Nichthandeln immer punktbest. Am 09.08. haette dieser Waechter allein
     16 pp der Signale gerettet (siehe Methodik-Nachtrag 09.08., Punkt 2).
  2. RAUSCHBODEN. Der Abstand A1<->A2 ist das Eigenrauschen. Nur was darueber
     hinausgeht, zaehlt. Ohne den zweiten identischen Arm ist jede Zahl
     unbrauchbar - real belegt, siehe Nachtrag 09.08., Punkt 1.
  3. MINDEST-n FUER "TENDENZ": `mindest_bewertbar` (Vorgabe 5). Darunter faellt
     das Wort nicht. Und eine Tendenz zaehlt nur, wenn sie beim Aufstocken
     HAELT ODER WAECHST - zweimal unabhaengig belegt, dass kleine Stichproben
     Scheinbefunde in der erwarteten Richtung erzeugen.
  4. MASSSTAB IST CRV-BREAKEVEN, nicht der Muenzwurf. Bei asymmetrischen Zielen
     ist 50 % kein neutraler Punkt: bei CRV 3,27 waeren 50 % bereits +1,14 R.
     Verglichen wird gegen `1/(1+CRV)` je Arm.

TRANSPORT- UND FORMFEHLER WERDEN GETRENNT (Nachtrag 09.08., Punkt 3). Ein 429
oder Timeout ist UNGEMESSEN, nicht widerlegt, und geht in keinen Nenner ein.
`provider` signalisiert das ueber eine Exception; Formfehler (kein verwertbares
JSON) zaehlen dagegen als HALTEN, weil die Pipeline sie real so behandelt -
`hebel_pipeline.py` schreibt bei `AnalystResponseInvalid` ein HALTEN-Signal.

RICHTUNGSBEWUSST, ANDERS ALS BISHER. `messe_prompt_nebeneffekte._zonen_kennwerte`
rechnet `risiko = entry - stop` und gibt bei SHORT `(None, None)` zurueck - es
verwirft also **jeden SHORT-Vorschlag stillschweigend**. Dieses Modul leitet die
Richtung aus der Zonenlage ab und spiegelt die Kanten wie `_zonen_absolut()`
(Entscheidung 09.08., "Variante A": Gate und Bewertung nehmen dieselbe Kante).

OHNE LLM PRUEFBAR. `provider` ist eine Funktion (fakten) -> antwort. `selbsttest()`
faehrt den ganzen Rahmen gegen ein nachgebildetes Modell mit bekanntem Verhalten,
inklusive der Faelle, die schiefgehen sollen - bevor echtes Kontingent brennt.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Callable

from agent.krypto.backward_tracking import simuliere_signal
from messe_prompt_nebeneffekte import _entferne_pfad


class TransportFehler(Exception):
    """Der Anbieter war nicht erreichbar - ungemessen, NICHT widerlegt."""


@dataclass
class ArmBilanz:
    name: str
    eroeffnet: int = 0
    gehalten: int = 0
    formfehler: int = 0
    transportfehler: int = 0
    r_werte: list[float] = field(default_factory=list)
    crvs: list[float] = field(default_factory=list)
    nicht_bewertbar: int = 0

    @property
    def entscheidungen(self) -> int:
        """Nenner der EROEFFNEN-Quote. Transportfehler gehoeren NICHT hinein."""
        return self.eroeffnet + self.gehalten + self.formfehler

    @property
    def eroeffnen_quote(self) -> float | None:
        n = self.entscheidungen
        return None if n == 0 else self.eroeffnet / n

    @property
    def summe_r(self) -> float:
        return sum(self.r_werte)

    @property
    def mittel_r(self) -> float | None:
        return statistics.mean(self.r_werte) if self.r_werte else None

    @property
    def breakeven_quote(self) -> float | None:
        """1/(1+CRV) ueber die tatsaechlich eroeffneten Vorschlaege."""
        if not self.crvs:
            return None
        return statistics.mean(1.0 / (1.0 + c) for c in self.crvs)

    @property
    def trefferquote(self) -> float | None:
        if not self.r_werte:
            return None
        return sum(1 for r in self.r_werte if r > 0) / len(self.r_werte)


@dataclass
class Nachweis:
    fakt: str
    a1: ArmBilanz
    a2: ArmBilanz
    b: ArmBilanz
    rauschboden_r: float | None
    wirkung_r: float | None
    eroeffnen_einbruch_pp: float | None
    urteil: str
    begruendung: str


def zonen_aus_antwort(antwort: dict) -> dict | None:
    """Zonen einer LLM-Antwort als Eingabe fuer `simuliere_signal()`.

    Richtung aus der Zonenlage (Ziel unter Entry = SHORT), Kanten gespiegelt wie
    in `_zonen_absolut()`: bei SHORT der FERNE Stop und das NAHE Ziel, bei LONG
    umgekehrt. Damit rechnet der Nachweis auf derselben Konvention wie Gate und
    Outcome-Tracker (Entscheidung 09.08.).

    None, wenn die Antwort keine handelbaren Zonen enthaelt - das ist der
    Normalfall bei HALTEN und kein Fehler."""
    try:
        e = antwort["entry"]
        entry = (e["usd_von"] + e["usd_bis"]) / 2.0
        s_von, s_bis = antwort["stop_loss"]["usd_von"], antwort["stop_loss"]["usd_bis"]
        t_von, t_bis = antwort["take_profit"]["usd_von"], antwort["take_profit"]["usd_bis"]
    except (KeyError, TypeError, ZeroDivisionError):
        return None
    if not entry or entry <= 0 or None in (s_von, s_bis, t_von, t_bis):
        return None
    ist_short = t_von < entry
    stop, ziel = (s_bis, t_bis) if ist_short else (s_von, t_von)
    risiko = (stop - entry) if ist_short else (entry - stop)
    chance = (entry - ziel) if ist_short else (ziel - entry)
    if risiko <= 0 or chance <= 0:
        return None
    return {"entry": entry, "stop": stop, "ziel": ziel, "risiko": risiko,
            "ist_short": ist_short, "crv": chance / risiko}


def _ist_eroeffnung(antwort: dict) -> bool:
    return str(antwort.get("action", "")).upper() in {"ERÖFFNEN", "EROEFFNEN",
                                                      "KAUFEN", "NACHKAUFEN",
                                                      "VERKAUFEN"}


def bewerte_arm(name: str, provider: Callable[[dict], dict],
                faelle: list[dict], reihen: dict, horizont: int) -> ArmBilanz:
    """Ein Arm ueber alle Faelle: fragen, Zonen lesen, gegen den Kurs bewerten.

    `faelle` sind dicts mit `fakten`, `symbol`, `created_at`."""
    bilanz = ArmBilanz(name=name)
    for fall in faelle:
        try:
            antwort = provider(fall["fakten"])
        except TransportFehler:
            bilanz.transportfehler += 1
            continue
        if not isinstance(antwort, dict) or "action" not in antwort:
            # Formfehler. Die Pipeline schreibt in diesem Fall real ein HALTEN
            # (hebel_pipeline.py faengt AnalystResponseInvalid) - also wird es
            # hier genauso gezaehlt, statt den Fall verschwinden zu lassen.
            bilanz.formfehler += 1
            continue
        if not _ist_eroeffnung(antwort):
            bilanz.gehalten += 1
            continue
        bilanz.eroeffnet += 1
        z = zonen_aus_antwort(antwort)
        reihe = reihen.get(fall["symbol"])
        if z is None or not reihe:
            bilanz.nicht_bewertbar += 1
            continue
        sim = simuliere_signal(z, reihe, str(fall["created_at"])[:10], horizont,
                               voller_horizont_noetig=False)
        if sim is None:
            bilanz.nicht_bewertbar += 1
            continue
        bilanz.r_werte.append(sim["r"])
        bilanz.crvs.append(z["crv"])
    return bilanz


def nachweisrahmen(provider: Callable[[dict], dict], faelle: list[dict],
                   fakt_pfad: str, reihen: dict, *,
                   horizont: int = 14,
                   eroeffnen_einbruch_pp: float = 10.0,
                   mindest_bewertbar: int = 5) -> Nachweis:
    """Drei Arme, alle drei gegen den Kurs bewertet.

    A1 und A2 sehen IDENTISCHE Fakten, B sieht sie ohne `fakt_pfad`. Die
    Entscheidungsregel steht in den Parametern und wird mit ausgegeben."""
    a1 = bewerte_arm("A1", provider, faelle, reihen, horizont)
    a2 = bewerte_arm("A2", provider, faelle, reihen, horizont)
    ohne = [{**f, "fakten": _entferne_pfad(f["fakten"], fakt_pfad)} for f in faelle]
    b = bewerte_arm("B", provider, ohne, reihen, horizont)

    m1, m2, mb = a1.mittel_r, a2.mittel_r, b.mittel_r
    rauschboden = abs(m1 - m2) if (m1 is not None and m2 is not None) else None
    # Wirkung gegen den MITTELWERT beider A-Arme - ein einzelner Arm waere
    # selbst nur eine Ziehung aus dem Rauschen.
    wirkung = None
    if mb is not None and m1 is not None and m2 is not None:
        wirkung = mb - (m1 + m2) / 2.0

    q_a = None
    if a1.eroeffnen_quote is not None and a2.eroeffnen_quote is not None:
        q_a = (a1.eroeffnen_quote + a2.eroeffnen_quote) / 2.0
    einbruch = None
    if q_a is not None and b.eroeffnen_quote is not None:
        einbruch = (q_a - b.eroeffnen_quote) * 100.0

    # --- Entscheidung, in fester Reihenfolge --------------------------------
    if einbruch is not None and einbruch >= eroeffnen_einbruch_pp:
        urteil, grund = "DISQUALIFIZIERT", (
            f"EROEFFNEN-Quote bricht um {einbruch:.1f} pp ein "
            f"(Grenze {eroeffnen_einbruch_pp:.1f} pp). Der Waechter hat Vorrang "
            f"vor jeder Ergebnisbilanz - das Ziel sind MEHR Signale.")
    elif min(len(a1.r_werte), len(a2.r_werte), len(b.r_werte)) < mindest_bewertbar:
        urteil, grund = "UNGEMESSEN", (
            f"Zu wenige bewertbare Faelle (A1 {len(a1.r_werte)}, A2 "
            f"{len(a2.r_werte)}, B {len(b.r_werte)}; noetig {mindest_bewertbar} "
            f"je Arm). Kein Urteil - und ausdruecklich KEIN Negativbefund.")
    elif wirkung is None or rauschboden is None:
        urteil, grund = "UNGEMESSEN", "Kein Mittelwert in mindestens einem Arm."
    elif abs(wirkung) <= rauschboden:
        urteil, grund = "IM RAUSCHEN", (
            f"Wirkung {wirkung:+.3f} R liegt innerhalb des Eigenrauschens "
            f"{rauschboden:.3f} R (A1 gegen A2). Nicht unterscheidbar von zwei "
            f"identischen Laeufen.")
    else:
        richtung = "verschlechtert" if wirkung < 0 else "verbessert"
        urteil, grund = f"TENDENZ: Fakt {richtung} das Ergebnis", (
            f"Wirkung {wirkung:+.3f} R gegen Rauschboden {rauschboden:.3f} R. "
            f"Gilt NUR als Tendenz: sie muss beim Aufstocken der Stichprobe "
            f"halten oder wachsen, nicht schrumpfen.")

    return Nachweis(fakt=fakt_pfad, a1=a1, a2=a2, b=b,
                    rauschboden_r=rauschboden, wirkung_r=wirkung,
                    eroeffnen_einbruch_pp=einbruch,
                    urteil=urteil, begruendung=grund)


def bericht(n: Nachweis) -> str:
    z = [f"FAKT: {n.fakt}", ""]
    z.append(f"  {'Arm':4} {'eroeffnet':>9} {'gehalten':>9} {'Form':>5} "
             f"{'Transp':>7} {'bewertet':>9} {'Mittel R':>9} {'Treffer':>8} {'Breakeven':>10}")
    for arm in (n.a1, n.a2, n.b):
        m = "-" if arm.mittel_r is None else f"{arm.mittel_r:+.3f}"
        t = "-" if arm.trefferquote is None else f"{arm.trefferquote:.1%}"
        be = "-" if arm.breakeven_quote is None else f"{arm.breakeven_quote:.1%}"
        z.append(f"  {arm.name:4} {arm.eroeffnet:>9} {arm.gehalten:>9} "
                 f"{arm.formfehler:>5} {arm.transportfehler:>7} "
                 f"{len(arm.r_werte):>9} {m:>9} {t:>8} {be:>10}")
    z.append("")
    if n.rauschboden_r is not None:
        z.append(f"  Rauschboden (A1 gegen A2): {n.rauschboden_r:.3f} R")
    if n.wirkung_r is not None:
        z.append(f"  Wirkung (B gegen A):       {n.wirkung_r:+.3f} R")
    if n.eroeffnen_einbruch_pp is not None:
        z.append(f"  EROEFFNEN-Einbruch:        {n.eroeffnen_einbruch_pp:+.1f} pp")
    z.append("")
    z.append(f"  URTEIL: {n.urteil}")
    z.append(f"          {n.begruendung}")
    return "\n".join(z)
