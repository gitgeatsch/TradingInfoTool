# -*- coding: utf-8 -*-
"""G-c: hat Rolle G mit ihrem Einwand recht? (03.09.2026)

## Der Anlass

Nutzerauftrag: *„mit G-c weitermachen — prüfen und gegenprüfen."* Aus dem
Plan (01.09.): *„Die Trefferbilanz von G führen. Je Widerspruch wird der
Ausgang mitgeschrieben: hatte G recht? Erst danach ist die Frage ‚soll G
sperren dürfen?' überhaupt beantwortbar. Maßstab: der QUOTENGLEICHE
ZUFALL, nicht das Bauchgefühl."*

## ⚠️ Warum das KEINE neue Tabelle braucht

Anders als `risk_veto` (das ein Signal VERHINDERT und deshalb einen
simulierten Schatten-Ausgang braucht, `veto_outcome_status`) verhindert
Gs Einwand NICHTS. Das Signal, zu dem G urteilt, geht real hinaus und hat
einen echten Ausgang (`outcome_status`) - auf DERSELBEN Zeile. G-c ist
deshalb eine reine MESSUNG auf vorhandenen Daten, keine Schema-Änderung.

## Die Vorabfestlegung

    Frage       Sagt Gs Einwand-Urteil den tatsaechlichen Ausgang eines
                EINSTIEGS-Signals voraus?
    Ankermenge  Rollen-Kette, KAUFEN/NACHKAUFEN/EROEFFNEN, `einwand_liegt_
                vor()` in (True, False) UND outcome_status aufgeloest
                (TP oder SL) - `unklar` traegt kein gerichtetes Urteil
                und bleibt aussen vor
    Groesse     TP-Quote bei "kein Einwand" MINUS TP-Quote bei "Einwand"
                (erwartungsgemaess POSITIV, wenn G etwas beitraegt)
    Kontrolle   QUOTENGLEICHER ZUFALL (2.93): je Kalendertag werden die
                ja/nein-Etiketten UNTER DEN AN DIESEM TAG VORHANDENEN
                FAELLEN zufaellig neu verteilt, bei GLEICHER Anzahl je
                Label wie am echten Tag - nie gegen die Gesamtquote
    Streuung    CLUSTER-BOOTSTRAP UEBER TAGE (nicht Bloecke wie bei den
                R-Ertragsmessungen - hier sind es diskrete TP/SL-
                Ereignisse ohne ueberlappende Fenster, der plain Cluster-
                Bootstrap ueber Tage ist die passende Form)

    ⚠️ BEDINGUNG, VOR DEM LAUF GESETZT: G traegt, wenn die echte
       Differenz nach Abzug des quotengleichen Zufalls-Mittelwerts UEBER
       NULL liegt UND das 90-%-Bootstrap-Band die Null nicht einschliesst.

    ⚠️ AUFLOESUNGSGRENZE VORAB BENANNT: bei ~55 Faellen (Stand 03.09.) ist
       nur ein GROSSER Effekt ueberhaupt sichtbar. Ein "nicht traegt"
       heisst hier moeglicherweise nur "noch zu wenige Faelle", nicht
       "G traegt nachweislich nicht".

## ⚠️ Was diese Messung NICHT tut

Sie sperrt nichts, sie schaltet nichts um. G bleibt eine Gegenpruefung,
keine Trichterstufe (Nutzerentscheidung 31.08., Abschnitt 8.3). Das
Ergebnis ist eine Zahl fuer eine SPAETERE Entscheidung.

    python messe_g_trefferbilanz.py [--selbsttest] [--db PFAD]
"""
import argparse
import collections
import sqlite3
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MISCHUNGEN = 10          # 2.104: eine einzelne Ziehung ist kein Nullpunkt
BOOTSTRAP = 2000
BAND = 0.90               # 90 %, weil die Fallzahl klein ist - siehe Kopf


def lade(db) -> dict:
    """{tag: [(einwand: bool, tp: bool), ...]} - nur EINSTIEG, aufgeloest."""
    from agent.zweite_meinung import einwand_liegt_vor
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    c.row_factory = sqlite3.Row
    je_tag = collections.defaultdict(list)
    for r in c.execute(
            "SELECT created_at, zai_gegenpruefung_urteil, outcome_status "
            "FROM signals WHERE quelle_kette='rollen' "
            "AND action IN ('KAUFEN','NACHKAUFEN','EROEFFNEN') "
            "AND outcome_status IN ('take_profit_erreicht',"
            "'stop_loss_erreicht')"):
        ev = einwand_liegt_vor(r["zai_gegenpruefung_urteil"])
        if ev is None:
            continue
        tp = r["outcome_status"] == "take_profit_erreicht"
        je_tag[r["created_at"][:10]].append((ev, tp))
    return dict(je_tag)


def _quote(faelle, einwand_wert):
    tp = [tp for ev, tp in faelle if ev == einwand_wert]
    return (sum(tp) / len(tp)) if tp else None


def differenz(je_tag) -> float | None:
    """TP-Quote(kein Einwand) - TP-Quote(Einwand), GEPOOLT ueber alle Tage.

    ⚠️ NICHT je Tag gemittelt - die meisten Tage haben nur 0-3 Faelle,
    "je Tag" waere hier zu duenn. Gepoolt, mit dem Tag als Cluster-Einheit
    im Bootstrap (unten) - das haelt die Tageskorrelation im
    Konfidenzintervall fest, ohne die Punktschaetzung selbst zu verduennen.
    """
    alle = [x for z in je_tag.values() for x in z]
    q_nein = _quote(alle, False)
    q_ja = _quote(alle, True)
    if q_nein is None or q_ja is None:
        return None
    return q_nein - q_ja


def quotengleicher_zufall(je_tag, rng) -> float:
    """EINE Mischung: die ja/nein-Etiketten unter allen Faellen neu
    verteilen, bei gleicher GESAMTZAHL je Label wie in Wirklichkeit.

    ⚠️⚠️ GEPOOLT, NICHT JE TAG - Abweichung von 2.93, mit Grund. Meine
    erste Fassung mischte je Kalendertag (wie bei den R-Ertragsmessungen
    ueblich) - beim Selbsttest fiel auf, dass die Kontrolle weit von Null
    abwich (+0,22 bei einem echten Effekt von +0,50), obwohl sie ein
    Nullmodell sein soll.

    URSACHE: bei G-c sind die meisten Tage mit 0-2 Faellen besetzt -
    `rng.shuffle` an einer Liste mit einem Element aendert NICHTS. Ein
    Drittel der Tage in den echten Daten hat nur einen Fall. Die
    Tagesklammer setzt voraus, dass an JEDEM Tag genug Auswahl zum Mischen
    besteht (bei den R-Ertragsmessungen: viele Assets desselben Tages) -
    das ist bei Gs Urteilen nicht der Fall, weil G JEDES eintreffende
    Signal beurteilt, nicht aus einem groesseren Pool auswaehlt.

    Die Tagesklammer wehrt hier auch nichts ab, was es abzuwehren gibt:
    sie schuetzt davor, einen Wert gegen ANDERE Tage zu vergleichen. Hier
    werden zwei Gruppen (Einwand/kein Einwand) INNERHALB desselben
    Datensatzes verglichen - ein Tag mit gutem Marktumfeld hebt beide
    Gruppen anteilig gleich. Was die Tageskorrelation stattdessen
    braucht, ist eine korrekte STREUUNG - die liefert der Cluster-
    Bootstrap unten, ueber Tage, unveraendert."""
    alle = [x for z in je_tag.values() for x in z]
    labels = [ev for ev, _tp in alle]
    rng.shuffle(labels)
    gemischt = {"_gepoolt": [(lab, tp) for lab, (_ev, tp) in zip(labels, alle)]}
    return differenz(gemischt)


def cluster_bootstrap(je_tag, rng, n=BOOTSTRAP):
    """Tage MIT ZURUECKLEGEN ziehen - haelt die Tagesstruktur (wie viele
    Faelle, welche Marktlage) je Ziehung intakt."""
    tage = list(je_tag.keys())
    aus = []
    for _ in range(n):
        gezogen = rng.choice(len(tage), size=len(tage), replace=True)
        stich = {}
        for i, idx in enumerate(gezogen):
            stich[f"{tage[idx]}#{i}"] = je_tag[tage[idx]]
        d = differenz(stich)
        if d is not None:
            aus.append(d)
    return np.array(aus)


def selbsttest():
    """⚠️ Die Kontrolle ist der erste Verdaechtige - erst Kunstdaten."""
    print("=" * 74)
    print("SELBSTTEST — zwei Welten mit bekannter Antwort")
    print("=" * 74)
    for name, staerke in (("Welt 1: G traegt WIRKLICH", 0.25),
                          ("Welt 2: reines Rauschen", 0.0)):
        rng = np.random.default_rng(4)
        je_tag = {}
        for d in range(400):
            tag = "2025-%02d-%02d" % (d // 28 + 1, d % 28 + 1)
            n = rng.integers(0, 4)
            faelle = []
            for _ in range(n):
                ev = bool(rng.integers(0, 2))
                p_tp = 0.5 - (staerke if ev else -staerke)
                faelle.append((ev, bool(rng.random() < p_tp)))
            if faelle:
                je_tag[tag] = faelle
        echt = differenz(je_tag)
        nullwerte = [quotengleicher_zufall(je_tag, np.random.default_rng(100 + s))
                    for s in range(MISCHUNGEN)]
        bereinigt = echt - float(np.mean(nullwerte))
        boot = cluster_bootstrap(je_tag, np.random.default_rng(7))
        unten = float(np.quantile(boot, (1 - BAND) / 2))
        traegt = bereinigt > 0 and unten > float(np.mean(nullwerte))
        print("  %s" % name)
        print("     echte Differenz %+.4f · Zufall %+.4f · bereinigt %+.4f"
              % (echt, float(np.mean(nullwerte)), bereinigt))
        print("     Band-Unterkante %+.4f · traegt: %s"
              % (unten, "JA" if traegt else "NEIN"))
        erwartet = staerke > 0
        print("     erwartet: %s -> %s\n"
              % ("traegt" if erwartet else "traegt NICHT",
                 "✔" if traegt == erwartet else "✖ DER TEST TAUGT NICHT"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selbsttest", action="store_true")
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()
    if a.selbsttest:
        selbsttest()
        return 0

    je_tag = lade(a.db)
    n_faelle = sum(len(z) for z in je_tag.values())
    n_tage = len(je_tag)
    print("Grundlage: %d Faelle an %d Kalendertagen" % (n_faelle, n_tage))
    if n_faelle < 20:
        print("⚠️ Zu wenige Faelle fuer irgendein Urteil - abgebrochen.")
        return 1

    q_ja = _quote([x for z in je_tag.values() for x in z], True)
    q_nein = _quote([x for z in je_tag.values() for x in z], False)
    n_ja = sum(1 for z in je_tag.values() for ev, _ in z if ev)
    n_nein = sum(1 for z in je_tag.values() for ev, _ in z if not ev)
    print()
    print("  Einwand (ja)     n=%3d  TP-Quote %.1f %%" % (n_ja, 100 * q_ja))
    print("  kein Einwand     n=%3d  TP-Quote %.1f %%" % (n_nein, 100 * q_nein))

    echt = differenz(je_tag)
    rng = np.random.default_rng(7)
    nullwerte = [quotengleicher_zufall(je_tag, np.random.default_rng(500 + s))
                for s in range(MISCHUNGEN)]
    zufall_mittel = float(np.mean(nullwerte))
    zufall_streuung = float(np.std(nullwerte))
    bereinigt = echt - zufall_mittel

    boot = cluster_bootstrap(je_tag, rng)
    unten = float(np.quantile(boot, (1 - BAND) / 2))
    oben = float(np.quantile(boot, 1 - (1 - BAND) / 2))

    print()
    print("=" * 74)
    print("DIE MESSUNG")
    print("=" * 74)
    print("  echte Differenz (kein Einwand - Einwand)      %+.4f" % echt)
    print("  quotengleicher Zufall (%d Mischungen)          %+.4f ± %.4f"
          % (MISCHUNGEN, zufall_mittel, zufall_streuung))
    print("  bereinigt                                     %+.4f" % bereinigt)
    print("  %d%%-Band (Cluster-Bootstrap ueber Tage)        [%+.4f .. %+.4f]"
          % (int(BAND * 100), unten, oben))

    print()
    print("=" * 74)
    print("URTEIL nach der vorab gesetzten Bedingung")
    print("=" * 74)
    traegt = bereinigt > 0 and unten > zufall_mittel
    if n_faelle < 100:
        print("  ⚠️ AUFLOESUNGSGRENZE: n=%d ist klein - nur ein GROSSER "
              "Effekt waere hier ueberhaupt sichtbar." % n_faelle)
    if traegt:
        print("  -> ✔ G TRAEGT auf dieser Datenlage: der Einwand sagt einen")
        print("     schlechteren Ausgang voraus, ueber den quotengleichen")
        print("     Zufall hinaus.")
    else:
        print("  -> ○ NICHT NACHWEISBAR auf dieser Datenlage.")
        print("     Das ist KEIN 'G traegt nicht' - bei n=%d ist das Band" % n_faelle)
        print("     zu breit, um das zu entscheiden. G-c bleibt eine")
        print("     laufende Messung, keine einmalige Antwort.")
    print()
    print("  ⚠️ G bleibt eine Gegenpruefung, keine Trichterstufe (8.3).")
    print("     Diese Zahl ist die Grundlage fuer eine SPAETERE")
    print("     Entscheidung, nicht die Entscheidung selbst.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
