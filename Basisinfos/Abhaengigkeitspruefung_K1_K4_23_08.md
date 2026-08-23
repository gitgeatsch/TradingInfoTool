# Abhängigkeitsprüfung vor K1–K4 — und zwei Funde an bereits Gebautem

*Nutzervorgabe 23.08.: „bevor wir hier bauen — sind das Teile des ursprünglichen
Plans? Wenn nein, muss dies mit diesem abgeglichen sein und **vorab über alle
Aktionen und Abhängigkeiten geprüft** sowie die **Auswirkungen bewertet**
werden."*

> **Die Prüfung war nötig, und sie hat zwei Defekte an A1 gefunden — beide an
> Code, der bereits gebaut ist.** Einer ist behoben, einer ist eine
> Entscheidung.

---

## 1. ⚠️ Fund 1 — A1 nahm den gesamten Bestand aus der Kette

**Gemessen, nicht befürchtet:**

| Gruppe | Bestand | gewählt | ⚠️ **nicht mehr beurteilt** |
|---|---:|---|---:|
| krypto | 15 | HYPE, MORPHO | **14 von 15** |
| etf | 7 | CEBS | **6 von 7** |
| aktien | 2 | PLTR | 1 von 2 |
| **gesamt** | **24** | | ⚠️ **21** |

**Warum:** `_sende_ausstieg` hängt **innerhalb** von `_ein_asset` hinter dem
Urteil. Wer die Auswahl nicht passiert, kommt nie zum Urteil — **und damit
hätte die gesamte Verkaufsseite geschwiegen.**

⚠️ **Und es stand in meinem eigenen Dokument:** *„Bestand ist nicht Teil von
A1 — das ist die Verkaufsfrage."* Die Konsequenz habe ich nicht gezogen: **was
nicht Teil der Auswahl ist, darf von ihr auch nicht gesperrt werden.**

**✔ Behoben:** wer Bestand hat, passiert die Auswahl-Stufe immer. Bei ihm
lautet die Frage nicht *„kaufen?"*, sondern *„halten oder verkaufen?"*.

---

## 2. ⚠️ Fund 2 — die Leerlaufwache und A1 arbeiten gegeneinander

**Die Mechanik:** `LEERLAUF_ABBRUCH = 8` — acht Modellaufrufe in Folge ohne
Signal halten den Lauf an. Gebaut als Deadloop-Bremse, und richtig so.

**Die Warteschlange stellt den Bestand nach vorn** (Nutzerentscheidung: *„bei
einer Position, die er hält, steht täglich eine echte Entscheidung an"*).

> ⚠️ **Beides zusammen:** ein Lauf beginnt mit den Bestandspositionen. Ein
> HALTEN erzeugt **kein Signal** — also zählt jede gehaltene Position als
> Leerlauf. **Sind acht davon fällig, hält der Lauf an, bevor die zwei
> ausgewählten Kandidaten überhaupt gefragt werden.**

**Im Probelauf ist genau das passiert:** *„8 Aufrufe in Folge ohne Ergebnis —
Lauf angehalten"*, hinein 8 von 41.

**Das ist die Umkehrung dessen, wofür A1 gebaut ist:** die Einstiegsseite
verstummt, obwohl sie gerade erst eine Begründung bekommen hat.

### Warum es vorher nicht auffiel

Vor A1 unterlag der Bestand demselben Cooldown wie alles andere — es kamen
selten viele Positionen in einem Lauf zusammen. **Erst die
Bestandsausnahme aus Fund 1 macht die Häufung möglich.**

### ⚠️ Die Behebung ist eine ENTSCHEIDUNG, keine Reparatur

Ich ändere eine Sicherheitsmechanik nicht im Vorbeigehen. Drei Wege:

| | was | Wirkung |
|---|---|---|
| **L1** | Die Wache zählt **nur Nicht-Bestand** | ein HALTEN auf einer gehaltenen Position ist eine **gültige Antwort**, kein Leerlauf. ⚠️ Die Bremse verliert dort ihre Wirkung |
| **L2** | Kandidaten **vor** den Bestand stellen | widerspricht Ihrer Reihenfolgeentscheidung („Bestand zuerst") |
| **L3** | `LEERLAUF_ABBRUCH` anheben | verschiebt das Problem, löst es nicht |

**Meine Empfehlung: L1.** Die Bremse wurde gegen einen Deadloop gebaut — gegen
ein Modell, das *auf alles* NICHTS_TUN sagt. Ein HALTEN auf einer Position, die
man hält, ist der **erwartete Normalfall** und kein Zeichen einer kaputten
Kette. **Aber es ist Ihre Entscheidung.**

---

## 3. Abgleich mit dem ursprünglichen Plan — je Punkt

| | was | im Plan? | Abhängigkeiten | Auswirkung |
|---|---|---|---|---|
| **K1** | Trichter in die Auswahl | ⚠️ **NEIN** | — | ⚠️ **und meine eigene Messung spricht dagegen:** der Trichter misst die **Schwankungsbreite** („wie weit"). „Rang nach Trichterbreite" ist damit fast „Rang nach Volatilität" — und `volatilitaet` trug heute früh **nicht** (−0,073 / −0,207). **Vor jedem Bau zu messen** |
| **K2** | Auswahl je Strategie | ✔ **ja** — Konzept §10, Reparaturliste **D1**, Gesamtplan **G2** | ⚠️ **blockiert durch S-1** (Kette trägt `akkumulation` nicht); Hebel-Arm ohne Gegenstand (Median 1,10) | groß: zwei Ranglisten, zwei Aufträge je Gruppe |
| **K3** | Bestand getrennt | ✔ **ja**, aber als **B1/B2/B3** (Verkaufsseite), nicht als Teil der Auswahl | — | ⚠️ **war der Fund oben — jetzt behoben und damit dringlicher, nicht erledigt**: die Verkaufsseite schreibt weiter einen 17-Zeichen-Stummel |
| **K4** | Quote als Obergrenze | ⚠️ **nein** — aber eine Korrektur **innerhalb** von A1 | keine | klein; ändert die Zahl der Beurteilten, nicht die Mechanik |

---

## 4. Was daraus für die Reihenfolge folgt

| | | Begründung |
|---|---|---|
| **1** | ⚠️ **L1 entscheiden** (Leerlaufwache) | **ohne sie ist A1 nicht ausrollbar** — der Lauf bricht ab, bevor die Auswahl greift |
| **2** | **B1/B2** (Verkaufsseite) | durch Fund 1 bestätigt: der Bestand ist jetzt **immer** in der Kette, und dort steht ein 17-Zeichen-Stummel |
| **3** | **K4** | klein, innerhalb A1, behebt die von Ihnen benannte Zwangswirkung |
| **4** | **K1 messen** (nicht bauen) | die Vermutung steht gegen eine eigene Messung |
| **5** | **K2** | erst nach S-1 |

⚠️ **K3 ist nicht mehr offen als Auswahlfrage** — er war ein Defekt und ist
behoben. Offen bleibt die **Verkaufsseite selbst** (B1/B2/B3).

---

## 5. Der Zustand nach dieser Prüfung

**Suite 1.633 alle bestanden · freie Namen 0 · `simuliere_kette` 3 Gruppen,
5 Signale, 6 Mails, 0 Fehler.**

⚠️ Eine bestehende Prüfung musste mitgezogen werden: Paket B1 erwartete, dass
nur die Gewählten zum Urteil kommen. **Seit der Bestandsausnahme stimmt das
nicht mehr, und zwar absichtlich** — die Erwartung folgt jetzt der Regel
„gewählt **oder** im Bestand".
