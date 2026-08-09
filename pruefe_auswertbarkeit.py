"""Kann die Messung ihre Frage ueberhaupt noch beantworten? (2026-08-09)

DER ANLASS (Nutzer, 09.08.): *"messe dazwischen nicht ob es laeuft sondern ob
der output passt."* Genau daran ist der Wirkungslauf gescheitert. Die
Zwischenmeldungen sagten "15 von 36 Ankern, null Fehler" - das sah gesund aus,
waehrend die entscheidenden LONG-Zellen laengst bei n=3 standen und die Frage
schon nicht mehr beantwortbar war. Der Lauf lief danach noch zweieinhalb
Stunden weiter und produzierte ein Ergebnis, das die Gegenpruefung sofort
kassierte.

DER UNTERSCHIED, um den es geht:

    DURCHSATZ      "laeuft es noch?"       - Anker, Fehler, Sekunden je Fall
    AUSWERTBARKEIT "kommt etwas heraus?"   - reichen die Zellen fuer die Frage?

Das Zweite ist billig zu pruefen und haette hier drei Stunden gespart.

DIE HOCHRECHNUNG ist der Kern. Nach fuenf von sechsunddreissig Ankern sind
kleine Zellen normal - entscheidend ist, ob sie bis zum Ende gross genug
WERDEN. Diese Datei rechnet den bisherigen Anteil auf die geplante Ankerzahl
hoch und schlaegt Alarm, wenn die Hochrechnung unter der Mindestgroesse
bleibt. Am 09.08. haette sie nach fuenf Ankern gemeldet: LONG-Anteil 8 %,
hochgerechnet 3 Faelle, Mindestgroesse 8 - nicht erreichbar.

    from pruefe_auswertbarkeit import pruefe_auswertbarkeit
    urteil = pruefe_auswertbarkeit(ergebnis, grundlinie="A1", geplant=36,
                                   bisher=nr, richtungen_noetig=True)
    if not urteil.tragfaehig:
        print(urteil.bericht()); return 3
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_ZELLE = 8
MIN_SYMBOLE = 5


@dataclass
class Urteil:
    tragfaehig: bool
    zeilen: list[str] = field(default_factory=list)

    def bericht(self) -> str:
        kopf = ("  AUSWERTBARKEIT: tragfaehig" if self.tragfaehig
                else "  ABBRUCH - die Messung kann ihre Frage nicht beantworten")
        return "\n".join([kopf] + [f"    {z}" for z in self.zeilen])


def _gepaarte_schluessel(a: list[dict], b: list[dict],
                         richtung: str | None = None) -> tuple[int, int]:
    """Wie viele Faelle und Symbole haben BEIDE Arme gemeinsam?

    Auf der Schnittmenge, nicht je Arm - genau der Fehler, der am 09.08. zwei
    Mittelwerte ueber verschiedene Fallmengen als 'gepaarte Differenz'
    ausgewiesen hat."""
    def menge(zeilen):
        return {(z["symbol"], z["datum"]): z for z in zeilen
                if richtung is None or z.get("richtung") == richtung}
    ma, mb = menge(a), menge(b)
    gemeinsam = set(ma) & set(mb)
    return len(gemeinsam), len({s for s, _ in gemeinsam})


def pruefe_auswertbarkeit(ergebnis: dict[str, list[dict]], *, grundlinie: str,
                          geplant: int, bisher: int,
                          richtungen_noetig: bool = False,
                          pflichtfelder: tuple = ("konfidenz",),
                          min_zelle: int = MIN_ZELLE,
                          min_symbole: int = MIN_SYMBOLE) -> Urteil:
    """`bisher` ist die Zahl der bereits abgearbeiteten Anker."""
    zeilen: list[str] = []
    tragfaehig = True
    if bisher <= 0:
        return Urteil(True, ["noch keine Anker - keine Aussage moeglich"])

    basis = ergebnis.get(grundlinie) or []
    if not basis:
        return Urteil(False, [f"Grundlinienarm '{grundlinie}' ist leer"])

    faktor = geplant / bisher

    leer = [a for a, z in ergebnis.items() if not z]
    if leer:
        return Urteil(False, [f"Arme ohne jede Zeile: {leer}"])

    # 1) Pflichtfelder JE ARM pruefen, nicht global.
    #
    #    Der Test hat das aufgedeckt: faellt EIN Arm vollstaendig aus, liegt
    #    die globale Quote bei genau 50 % und eine globale Schwelle greift
    #    nicht - obwohl der Vergleich mit diesem Arm bereits unmoeglich ist.
    #    Ein Mittelwert ueber Arme verdeckt genau den Fall, um den es geht.
    for feld in pflichtfelder:
        for arm, z_arm in ergebnis.items():
            if not z_arm:
                continue
            fehlend = sum(1 for z in z_arm if z.get(feld) is None)
            if fehlend / len(z_arm) > 0.5:
                tragfaehig = False
                zeilen.append(f"{arm}: Feld '{feld}' fehlt in {fehlend} von "
                              f"{len(z_arm)} Zeilen - daran haengt die "
                              f"Fragestellung")

    # 2) Gepaarte Gesamtzellen je Arm
    for arm in ergebnis:
        if arm == grundlinie:
            continue
        n, sym = _gepaarte_schluessel(basis, ergebnis[arm])
        hoch = int(n * faktor)
        if hoch < min_zelle or int(sym * faktor) < min_symbole:
            tragfaehig = False
            zeilen.append(f"{arm}: gepaart {n} Faelle / {sym} Symbole, "
                          f"hochgerechnet {hoch}/{int(sym * faktor)} - "
                          f"Minimum {min_zelle}/{min_symbole}")

    # 3) Richtungszellen - der Fall vom 09.08. Sie entstehen nur, wenn das
    #    Modell die Richtung waehlt; ein Anbieterwechsel kann sie ausloeschen.
    if richtungen_noetig:
        for richtung in ("LONG", "SHORT"):
            schlechteste = None
            for arm in ergebnis:
                if arm == grundlinie:
                    continue
                n, sym = _gepaarte_schluessel(basis, ergebnis[arm], richtung)
                if schlechteste is None or n < schlechteste[1]:
                    schlechteste = (arm, n, sym)
            if schlechteste is None:
                continue
            arm, n, sym = schlechteste
            hoch = int(n * faktor)
            if hoch < min_zelle:
                tragfaehig = False
                zeilen.append(
                    f"{richtung}-Zellen zu duenn (schwaechster Arm {arm}: "
                    f"{n} gepaart, hochgerechnet {hoch}, Minimum {min_zelle}). "
                    f"Die Richtungsaussage wird NICHT erreichbar sein.")
            elif hoch < min_zelle * 2:
                zeilen.append(f"{richtung}-Zellen knapp: hochgerechnet {hoch} "
                              f"- Richtungsaussage wird schwach bleiben")

    if tragfaehig and not zeilen:
        zeilen.append(f"alle Zellen hochgerechnet ueber dem Minimum "
                      f"({min_zelle} Faelle / {min_symbole} Symbole)")
    return Urteil(tragfaehig, zeilen)
