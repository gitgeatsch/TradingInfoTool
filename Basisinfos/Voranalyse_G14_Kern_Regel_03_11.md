# Voranalyse G14: Kern-Regel und „Kern immer zugelassen“ (03.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) G14 · Vorlauf: [`Voranalyse_Kern_Regel_Bau_25_10.md`](Voranalyse_Kern_Regel_Bau_25_10.md) (§7 K-4, §8 gebaut) · Spot §12.6–§12.11

Nutzer 03.11.: *„Ok, G14-Voranalyse angehen“* · *„prüfen gegenprüfen und doku“*

⚠️ **Nur Voranalyse.** Nichts wird gebaut, bevor du entschieden hast.

## 1. Was G14 heute noch ist — der Plan-Eintrag ist veraltet

Im Gesamtplan steht: *„Kern-Regel E-69 (BTC/ETH/SOL immer zugelassen) beschlossen, nicht gebaut“*. Das ist **überholt**:

| Datum | Entscheidung | Inhalt |
|---|---|---|
| 06.10. | **E-69** | Aufbau 70/20/10 mit Ausgleich über die Raten; K1-Hinweis (Überhitzung kippt) und Rückkauf-Hinweis in einer Klima-Ampel. Bau „mit dem Spot-Betrieb“ |
| 25.10. | Nutzerregel | *„btc und eth und sol sollen auch regel0 und hebel nutzen können!!!“* — Kern ist für REGEL0, Hebel und Spot **immer zugelassen**; die Altcoin-Spot-Regeln gelten nicht für ihn |
| 26.10. | **E-148** | *„bin noch nicht bei 70/20/10 … aktuell einmal pro Monat einen kleinen Betrag pro Asset, (b) nur K-4“* ⇒ **Raten-Mail, Ausgleich über die Raten und Klima-Ampel/K1 werden NICHT gebaut** (Bau-Voranalyse B-1/B-2 entfallen). Der Aufbau ist dein eigener Sparplan |
| 26.10. | **E-152** | **K-4 gebaut**: `agent/kernwerte.py` (eine Liste), keine Spot-Zelle der alten Kette für den Kern, Hebel/REGEL0 unberührt. NB-Kontrolle **K-K4-1 erfüllt 27.10.** |
| 27.10. / 03.11. | E-164 / E-166 | alte Kette fest stillgelegt, ihre Jobs überspringen sich — K-4 ist damit eine zweite Absicherung |

⇒ **Vom beschlossenen Bau ist nichts mehr offen.** Offen ist nur die Frage, ob die **Zulassung des Kerns** im neuen Betrieb **belegt** und **abgesichert** ist.

## 2. Ist der Kern im heutigen Betrieb zugelassen? (Fakt)

| Strang | Belegt | Beleg |
|---|---|---|
| **REGEL0** | ✔ **ja** | Betriebsrechnung Dez. 2025–Okt. 2026 (G7 §10, `data/_g7/regel0/f_einstiege_betrieb_mit_stufe_schalter.csv`): **103** der 20.069 Einstiege sind Kern (BTC 36, SOL 36, ETH 31), Stufe 5 ×76 / 3 ×27, **alle mit Schalter an** — also mailbar |
| **Hebel** | ✔ ja | Der Hebel kommt aus der REGEL0 (E-36/E-140); die Hebelmail hängt am Schalter `asset_hebel_settings.hebel_pruefung_erlaubt` (`regel0_stundenlauf._hebel_schalter`). NB-Diagnose 01.11.: **BTC 1, ETH 1, SOL 1** (25 von 44 Werten an). H15 führt echte Positionen ohne Schalterabfrage |
| **Spot** | ✔ gewollt ohne Kaufvorschlag | B1/B3/B4 nehmen den Kern aus (`spot_mitnahme.KERN` = `kernwerte.KERN`); alte Kette stillgelegt; Aufbau per Sparplan (E-148). Bestand, G/V, Anzeige bleiben |
| Zuordnung Binance ↔ Bitpanda | ✔ | BTC/ETH/SOL stehen **nicht** in `symbol_zuordnung.csv` (dort nur Ausnahmen, darunter die gesperrten) ⇒ kein `gesperrt`, Name 1:1 |

## 3. Wo die Zulassung NICHT abgesichert ist (Lücken)

| # | Lücke | Folge | Schwere |
|---|---|---|---|
| **L1** | Der Hebel-Schalter des Kerns ist ein **gewöhnlicher Klick**: Watchlist-Knopf (`ui/app.py:1003`) und Hebel-Reiter (`ui/hebel_tab.py:490`) schalten ihn ohne Rückfrage um | ein versehentlicher Klick nimmt BTC, ETH oder SOL **still** aus allen REGEL0-/Hebelmails; Statusseite und Diagnose zeigen nur die Liste der Schalter, keine Warnung | mittel |
| **L2** | Kern-Listen neben `agent/kernwerte.KERN`: Kopien in `agent/ereignisse.py:124`, `ui/bestand_tab.py:41` (dazu Listen anderer Bedeutung: `db._DCA_ERLAUBT_DEFAULT_SYMBOLS`, `akkumulationslage.OHNE_BELEG`, Rückfallmengen in `assetklassen`) | *Kopien laufen auseinander*; heute gleich. ⚠️ **Keine** davon steuert REGEL0 oder Hebel — die REGEL0 kennt überhaupt keine Kern-Liste; ein Auseinanderlaufen träfe nur Ereignisse und Anzeige | niedrig |
| **L3** | Das Suite-Paket `Kernwerte` prüft nur die **alte** Kette (Zellen, Rückfall). Dass der **neue** Betrieb den Kern führt — im Universum, nicht `gesperrt` in `symbol_zuordnung.csv`, Schalter an —, prüft **keine** Prüfung | eine künftige Grundgesamtheits- oder Sperrlisten-Änderung könnte den Kern still herausnehmen (vgl. *Die Grundgesamtheit ist keine Stellschraube*) | mittel |
| **L4** *(Gegenprüfung)* | `regel0_stundenlauf._hebel_schalter` fängt jeden Lesefehler ab und gibt `{}` zurück — **ohne Logzeile**. Dann werden alle Signale dieser Stunde mit `hebel_schalter` NULL abgelegt; die Mail wählt nur `hebel_schalter=1` und der Verpasst-Vermerk ebenso (`regel0_mail.py:411/422`) ⇒ **still verloren**, auch kein *verpasst* | trifft **alle** Werte, nicht nur den Kern; selten (WAL), aber unsichtbar. ✔ selbst nachgelesen | mittel |

*(Weitere Wege aus der Gegenprüfung, alle nicht kernspezifisch und heute ohne Befund: §6.)*

## 4. Optionen (eine Entscheidung, mit Alternativen)

| | Umfang | Folge |
|---|---|---|
| **a) Absichern als Fakt + Rückfrage (Vorschlag)** | ① GUI: Ausschalten eines **Kernwerts** nur nach Rückfrage *„BTC ist Kernwert – REGEL0/Hebel für ihn wirklich aus?“* (beide Knöpfe, ein Helfer) · ② Statusseite (Kontrollen-Karte) + Diagnose: **Warnzeile**, sobald ein Kern-Schalter aus ist **oder fehlt** · ③ die zwei Kopien verweisen auf `kernwerte.KERN` · ④ Suite: am Helfer geprüft, dass der Kern im REGEL0-Universum steht, in `symbol_zuordnung.csv` nicht `gesperrt` ist und ohne Zeile nicht still verschwindet · ⑤ **L4:** ein Lesefehler der Schalter wird **geloggt** und als Datenausfall gemeldet (bestehender Weg), statt still `{}` | Du behältst die Hand am Schalter; ein Versehen fällt sofort auf. Kein Eingriff in die REGEL0-Rechnung; ⑤ betrifft alle Werte |
| b) Harte Sperre | wie a), dazu: der Code behandelt den Kern-Schalter **immer** als an (Klick wirkungslos) | erzwingt die Regel, nimmt dir aber den Schalter — auch für den Fall, dass du einen Kernwert bewusst pausieren willst |
| c) Nur Doku | G14 als erledigt markieren (E-148/E-152), nichts bauen | Lücken L1–L3 bleiben |

**Empfehlung: a).** Die Regel *„kein Filter darf den Kern ausschließen“* richtet sich gegen **System**-Filter; deine eigene Entscheidung bleibt deine — sie soll nur nicht **versehentlich** fallen. b) wäre der Schritt, falls du den Schalter für den Kern nie brauchst.

**NB:** Betriebscode (GUI, Statusseite) ⇒ ins **Bündel G8**, nicht einzeln.

**Gesamtplan:** G14 wird von *„beschlossen, nicht gebaut“* auf den Stand oben berichtigt — unabhängig von a/b/c.

## 5. Gegenprüfung dieser Voranalyse

- ✔ Selbst gelesen: E-68/E-69/E-148/E-150/E-152; Bau-Voranalyse Kern-Regel §1–§8; `agent/kernwerte.py`; Schreibwege `db.set_hebel_pruefung_erlaubt` (nur `ui/app.py:1003`, `ui/hebel_tab.py:490`) und die Vorgabe beim Geradeziehen (`database/db.py:1726`: neue Krypto-Werte **an**); `regel0_stundenlauf._hebel_schalter`/`_binance_zu_bitpanda`; Suite-Paket `Kernwerte`; `nb_kontrollen.yaml` K-K4-1 (erfüllt 27.10.).
- ✔ Daten: Betriebsrechnung G7 §10 (103 Kern-Einstiege, Schalter an); NB-Diagnose 01.11. (`hebel_pruefung_toggles`: BTC/ETH/SOL = 1).
- Unabhängige Gegenprüfung (ohne meinen Befund, Auftrag: *jeden* Ausschluss- oder Drosselweg für den Kern in REGEL0/Hebel finden): §6.

## 6. Ergebnis der unabhängigen Gegenprüfung

**Bestätigt:** L1, L3 und die Zahlen (103 Kern-Einstiege: BTC 36, ETH 31, SOL 36). Dazu live in der NB-Ablage 03.–14.10.: je ein Signal ETH (09.10.), BTC (10.10.), SOL (10.10.), Schalter 1, Stufe 5, **alle gemailt**, Kursabgleich ±0,0 %.

**Neu:** L4 (oben, selbst nachgelesen) und L2 präzisiert (keine Liste steuert REGEL0).

**Nicht kernspezifisch, heute ohne Befund** (zur Einordnung, nicht Teil der Entscheidung):

| Weg | Wirkung | Einordnung |
|---|---|---|
| Abruffehler beim Nachladen (`regel0_nachlader.py:182-186`) | ab 2 h Ausfall ist das Signal weg; gemeldet erst ab > 10 % veralteter Werte | trifft jeden Wert gleich |
| Kerzenlücke bei Binance | 240 h lückenloser Vorlauf nötig ⇒ ~10 T kein Signal | trifft jeden Wert gleich |
| Kursabgleich Bitpanda/Binance > 5 % | Mail gesperrt, aber **mit** Meldungsmail | nicht still; Kern live ±0,0 % |
| `sperre_ab_richtwert` | nur Vermerk im Text, keine Sperre der Mail | heute `false` |
| BTC nicht im RSI-/ATR-Training | BTC läuft über den Restpfad, Mail-Vermerk *„BTC: nicht nachgewiesen“* | Inhalt, kein Gate; BTC nie Stufe 0 |

**Ist der Kern auffällig selten?** Nein. Median 35 Einstiege je Symbol (Quartile 31/39); Kern 36/31/36, Anteil 0,51 % bei 0,47 % der Symbole; unter den Einstiegen mit Schalter an 11,4 % bei 12 % der eingeschalteten Werte. Januar 2026 ohne Kern-Einstieg ist marktweit (nur 223 Einstiege). Die Häufigkeit bestimmen Ruhe 48 h und Ersteintritt, nicht die Volatilität.

**H15:** ohne Symbol-, Kern- oder Schalterfilter (`hebelfuehrung.py:494-545`), läuft vor der Sperre der alten Kette ⇒ für den Kern sicher.

**Urteil zur Frage *„Kern immer zugelassen?“*:** heute **ja**, belegt in Code, Rechnung und Live-Ablage — aber nur, weil die Daten stimmen und eine Schalterzeile 1 trägt. **Abgesichert** ist es nicht (L1, L3, L4). Daher die Entscheidung §4.

## 7. GEBAUT — Weg a (03.11.2026; Nutzer: *„Ok a – bauen, prüfen, gegenprüfen und doku"*, E-167)

| Teil | Ort | Wirkung |
|---|---|---|
| **Rückfrage** | `agent/kernwerte.rueckfrage`; `ui/app.py` `_toggle_hebel_pruefung_erlaubt`, `ui/hebel_tab.py` `_umschalten` | Einen **Kernwert ausschalten** geht nur nach *„… ist ein Kernwert … Wirklich ausschalten?"* (Vorgabe *Nein*). Einschalten und Nicht-Kern bleiben ohne Frage. Der Schalter bleibt beim Nutzer |
| **Warnzeile** | `agent/kernwerte.luecke`; `betriebslage.neuaufnahme_und_abgleich` → `kern_luecke` (Schalter **aus oder fehlt**, dazu *„X ohne REGEL0-Daten"*) | Statusseite Betriebskarte **rot**; Teilexport *„Kernwerte ohne REGEL0/Hebel"*; Diagnose `kern_hebel_luecke` (dieselbe Rechnung, Rückfall nur Schalter mit Vermerk) |
| **L4** | `regel0_stundenlauf._hebel_schalter` → `SCHALTER_FEHLER`; `betrieb_lauf` → `meldung` + Feld `schalter_fehler`; `background.regel0_meldung_art` | Ein Lesefehler der Schalter ist eine **Fehlermail** über den bestehenden REGEL0-Weg (*„Hebel-Schalter nicht lesbar … KEINE Signalmail"*), nicht mehr still. Fehlende Datei (Probe am Desktop) bleibt still |
| **Eine Liste** | `agent/ereignisse.py`, `ui/bestand_tab.py` | lesen `kernwerte.KERN` |

**Prüfung am Seiteneffekt** `Rechenkern_02_10/pruefe_g14.py` **11/11** (`pruefe_g14.txt`), im Suite-Paket **Kernwerte**:
- G1 Rückfrage-Regel.
- G2 **beide echten Knopf-Handler** ohne Fenster, auf einer Speicher-DB: *Nein* lässt an, *Ja* schaltet aus, Einschalten und LINK ohne Frage. G3 **Mutationsprobe**: ohne die Regel ungefragt aus.
- G4/G5 Warnzeile: ETH aus + SOL ohne Zeile ⇒ `['ETH','SOL']`, alle an ⇒ `[]`, BTC ohne Daten ⇒ Vermerk; Statusseite reicht durch und zeigt rot.
- G6 Kern in `symbol_zuordnung.csv` nicht gesperrt und im REGEL0-Datenbestand (Desktop).
- G7/G8 L4 **am echten `betrieb_lauf`**: kaputte Schalterdatei ⇒ Meldung, Art *fehler* (Fehlermail), Signal mit Schalter NULL abgelegt; gute Datei ⇒ Art *keine*, Schalter 1.
- G9 eine Liste. G11 Diagnose rechnet wie die Statusseite. G10 Standard-DB sha256 (`.db`/`-wal`) unverändert.

**Gegenprüfung** (unabhängig, nur Diff gelesen): kein schwerer Befund.

| Befund | Schwere | erledigt |
|---|---|---|
| G8 prüfte L4 nur über die **Textreihenfolge** — eine vertauschte Zeile wäre grün geblieben | mittel | G8 läuft jetzt den **echten** `betrieb_lauf` mit kaputter Schalterdatei |
| Bleibender Lesefehler ⇒ etwa **stündlich** eine Fehlermail (Cooldown 60 min) | mittel | **bewusst so gelassen**: dasselbe Muster wie *„Datenbasis veraltet"*; solange der Fehler besteht, geht für **keinen** Wert eine Signalmail raus — das soll nicht leise werden |
| Diagnose prüfte nur den Schalter, nicht die Daten | niedrig | Diagnose nutzt dieselbe Rechnung wie die Statusseite (G11) |
| Datenprüfung ohne Groß-/Kleinschreibung | niedrig | vereinheitlicht |
| `MIN_STUNDEN ={` (Leerzeichen) | kosmetisch | korrigiert |
| `pruefe_s74/s75` ersetzen `_hebel_schalter` — ein alter Fehler könnte dort im selben Prozess durchsickern | niedrig | im Betrieb ausgeschlossen (eigener Prozess je Stunde, Liste wird je Aufruf geleert); vermerkt |

**Volle Suite** zuerst **1 rot**, durch diesen Bau: Die Diagnose-Konsole muss ASCII sein (NB: CP1252), meine neue Zeile trug *„⛔"* ⇒ durch *„!!"* ersetzt. Endstand: §7 unten.

**NB:** mit dem Bündel G8, Kontrolle **K-G14-1**.

**Endstand der vollen Suite (03.11., 08:25):** 3.494 Prüfungen, **1 rot, nicht durch G14**: `Regel0Betrieb` *R-R11-1* (der Rechenkern trifft die Betriebsreferenz zeilengleich). Die Nachrechnung 2024-01..2026-08 ergibt seit diesem Lauf **10.735 statt 10.732** Einstiege (6 Zeilen in 2025: CVC, CFX, PENDLE, BANANA, TURBO, BRETT).

Belegt, dass G14 nicht die Ursache ist:
- **Derselbe Code** (sauberer Checkout HEAD ohne G14) **und der Stand vom 27.10.** (`037c6df7`) ergeben jetzt ebenfalls 10.735.
- Alle 9 Suite-Läufe 30.10.–03.11. 08:08 ergaben 10.732.
- Die Rechnung liest laut Audit-Hook nur `stundenkurse.db`, `stundenkurse_alle.db` und `kern48jbz_gruppe_bestand.csv`. Zeitstempel 25.09. / 01.10. / 01.10., keine WAL-Datei.
- Ein Thread statt mehrerer (OpenBLAS) und feste Hash-Seeds ändern nichts: Die Rechnung ist jetzt deterministisch 10.735.
- Python-Installation unverändert.

Prüfsummen am 03.11. (sha256, Anfang): `stundenkurse.db` 52d287c67bd6fe99 · `stundenkurse_alle.db` 2298688661872660 · Gruppe e84d782b87ca9009 · Referenz 942999ada5888c0a.

**Ursache offen** ⇒ Gesamtplan **G17**.
