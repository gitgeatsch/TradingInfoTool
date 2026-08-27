# Der rote Faden — wo wir stehen und was zusammenhängt

**Angelegt 27.08.2026.** Nutzerauftrag: *„Nach der Teilumsetzung bringe die
Punkte und Pläne in Zusammenhang, damit wir einen roten Faden haben."*

---

## 0. Das Ziel in einem Satz

> **Ein System, das bei hohem Potential ein begründetes Handelssignal erzeugt —
> statt 190 Signale am Tag nach der Uhr.**

**Die drei Vorgaben, die das schärfen** (Nutzer, 25.–27.08.):

| | |
|---|---|
| ⚠️ **Der Takt darf nie Signalgeber sein** | er begrenzt, er erzeugt nicht |
| **Ein guter Trade ist Potential, nicht Gebührendeckung** | zwei Ebenen, die sich nie überschneiden |
| **Wir bewerten nicht Assets, sondern Zeitpunkte** | auch ein Shitcoin hat Potential |

---

## 1. Wo der Weg herkommt — der Ausgangszustand

| | gemessen |
|---|---|
| Signale je Tag | **190** über 44 Symbole = **4,3 je Symbol** |
| davon ERÖFFNEN | **0** (Stand 24.08.) |
| Trichterverluste an Bremsen ohne Qualitätsaussage | **79 %** (`anlass` 1.252 · `wiederholung` 445) |
| offene Signale je Position | bis zu **21** (BIO), 17 (BTC) |
| Durchsatz gegen Cooldown-Obergrenze | 63 % |

**Die Diagnose:** Der Scheduler ist der Auslöser, der Cooldown die Bremse.
Beide sagen nichts über Qualität.

---

## 2. Was heute gebaut wurde — und wie es zusammenhängt

```
   ZIEL: Signal bei hohem Potential

   ┌─────────────────────────────────────────────────────────┐
   │  1  POSITION statt Signal        agent/positionsfuehrung │  ✔ gebaut
   │     44 statt 266 Führungen, Break-Even sichtbar          │  ✘ kein Aufrufer
   ├─────────────────────────────────────────────────────────┤
   │  2  STRATEGIE je Position        agent/handelsauftrag    │  ✔ existiert
   │     einstieg / swing / akkumulation + Paar-Matrix        │  ⚠️ nie gesetzt
   ├─────────────────────────────────────────────────────────┤
   │  3  AUSLÖSER statt Takt          Ausloeser_und_Begr…     │  ⚠️ 11/20 Zellen
   │     K1 Lage · K2 Vorfilter · V1 These · V3 Greed · V4    │  ✘ nicht gebaut
   ├─────────────────────────────────────────────────────────┤
   │  4  POTENTIAL als Auswahl        agent/potential         │  ✔ gebaut
   │     quote × CRV − (1 − quote), gebührenfrei              │  ⚠️ 1 Beitrag
   └─────────────────────────────────────────────────────────┘
```

**Die vier greifen ineinander:** Ohne (1) erzeugt jeder Auslöser 21 Meldungen
statt einer. Ohne (2) greifen weder Paar-Matrix noch die GUI-Schalter des
Nutzers. Ohne (3) bleibt die Uhr der Auslöser. Ohne (4) kann das System zwei
Handlungen nicht gegeneinander abwägen.

---

## 3. Was fertig ist — belastbar

| | Baustein | Beleg |
|---|---|---|
| ✔ | **Positionsführung** | 44 statt 266, Break-Even, −6.544 € Gesamtstand; Staking abgezogen |
| ✔ | **Potentialmaß** | 6 Tests bestanden, Zwei-Ebenen-Trennung nachgewiesen (+0,135 R gegen −0,365 R) |
| ✔ | **Kern-Auswahl** | BTC/ETH/SOL — der GUI-Schalter nennt sie seit Wochen |
| ✔ | **Takt fachlich egal** | 2–14 Tage unter 0,2 % Unterschied; nur Mindestgebühr zählt |
| ✔ | **V1-Datenlage** | 262 von 266 Signalen tragen den Widerlegungspreis, Spanne je Position **Faktor 1,00–1,02** |
| ✔ | **Ein Ausschluss** | weit über dem 200-Schnitt kaufen: −11,2 Punkte, 3/3 Jahre |
| ✔ | **Modulkarte** | `zeige_modulkarte.py` — 160 Module, gegen dreifaches Neuerfinden |
| ✔ | **Methodik 2.80** | Prüfliste zwischen Ergebnis und Deutung |

---

## 4. ⚠️ Was heute gestorben ist — und was das bedeutet

| | Befund | Todesursache |
|---|---|---|
| 1 | Lage-Staffelung trägt | falsche Kontrolle — verliert **−8,3 %** gegen konstante Quote |
| 2 | Tief Gefallene fallen weiter | keine Basisrate |
| 3 | Umsatz trennt tot von lebendig | widerlegt |
| 4 | Buckel bei leicht unter dem Schnitt | Marktphase |

⚠️ **Damit gibt es für den Kern KEINE belegte positive Kaufregel.** Die
Kandidaten sind erschöpft: Fear ist ausgeschlossen (151 Tage am Stück),
„nie teurer als zuletzt" verstummt, die Lage-Staffelung ist gescheitert,
„Boden gehalten" wurde nie gebaut.

**Was bleibt, sind Ausschlüsse** — nicht kaufen, wenn teuer. Das passt zum
Gesamtbefund des Projekts und ist keine Niederlage, aber es heißt: **Der Kern
wird vorerst nach Zeittakt akkumuliert, nicht nach Auslöser.**

---

## 5. ⚠️ Drei Schiefstände, die heute aufgedeckt wurden

**Alle drei sind vom selben Typ: beim Umbau verlorene Funktionalität, die in
der Doku als fertig steht.**

| | was in der Doku steht | tatsächlich |
|---|---|---|
| **Spot-Verkaufs-Roadmap** | *„vollständig abgeschlossen"* (01.08.) | alle vier Schritte hängen an der alten Kette · `halte_kriterium`: **1 von 266** |
| **Strategien** | `handelsauftrag.py` seit 12.08. vollständig | `strategie` in **0 von 7.294** gesetzt |
| **Tranchen** | AZ-4 gebaut, GUI-Schalter da | Rollen-Kette kennt sie **nicht** |

**Gegenmittel gebaut:** `zeige_modulkarte.py` + Methodik 2.80 Punkt 6.

---

## 6. Die Reihenfolge — was worauf wartet

```
JETZT MÖGLICH, ohne Vorbedingung
  A  strategie setzen (Kern → akkumulation)      → schaltet GUI-Schalter scharf,
                                                    beendet Trailing auf Spot
  B  Positionsführung anschließen                 → 83 % weniger Prüfungen
  C  V1 als Ausstieg                              → Datenlage vollständig

WARTET AUF EINE ENTSCHEIDUNG DES NUTZERS
  D  Zielallokation je Stufe                      → ohne sie rechnet V4 nicht
  E  Hebel: Krücke (beides melden) oder warten?   → braucht D nicht
  F  Cooldown/Job-Takt                            → 190/Tag ist die Ausgangslage

WARTET AUF MESSUNG
  G  H über ein CRV-Raster                        → erst dann Spot gegen Hebel
  H  V3 (Greed-Teilverkauf) Wirkung               → Daten da, ungemessen
  I  Auswertung Vorfilter-Schatten                → ~19.09.2026
  J  Lebendigkeit / TVL                           → ab 18.09.2026
  K  Terminmarkt-Wirkung (OI, Funding)            → ab 22.10.2026 / 11.03.2027
```

⚠️ **A, B und C sind unabhängig voneinander und von allem anderen.** Sie
bringen das System in einen Zustand mit weniger und begründeten Meldungen,
ohne dass die Potentialfrage geklärt sein muss.

---

## 7. Der ehrlichste Satz zum Stand

**Das System kann nach diesem Tag besser sagen, was es NICHT weiß.** Es hat
eine Positionssicht, ein Potentialmaß mit ausgewiesenen Grenzen, eine
Auslöser-Matrix mit sichtbaren Lücken und eine Prüfliste, die vier falsche
Befunde an einem Tag gefunden hat.

⚠️ **Was es nicht hat, ist ein zweiter tragender Beitrag.** Das Potentialmaß
rechnet heute im Wesentlichen „trifft H zu?" — und H läuft bis 19.09. im
Schatten. **Jede weitere Verfeinerung der Auswahl scheitert daran, nicht an
der Mechanik.**

Verwandt: `Ausloeser_und_Begruendungen_27_08.md` ·
`Befund_Lage_27_08.md` · `Entscheidung_Kern_Staffelung_27_08.md` (widerrufen) ·
`Bestandsaufnahme_Positionsfuehrung_26_08.md` ·
`Test_und_Verifikationsmethodik.md` 2.80
