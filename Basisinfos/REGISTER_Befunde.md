# REGISTER — DIE BEFUNDE

*Erzeugt aus `bestand.py`. **Nicht von Hand aendern.***

⚠️ **Wofuer:** eine Korrektur findet man in einem chronologischen Dokument nur durch VORWAERTSLESEN. Hier steht bei jedem abgeloesten Befund, **wodurch** und **warum**.

## ✔ WAS GILT

**2.145** — `schnitt` (Abstand zum eigenen 200-Tage-Schnitt) TRAEGT auf der selektierten Menge: +0,1707 R [+0,0723 .. +0,2781] bei 20 %, Trennschaerfe 0,020. Abdeckung 516/516 (100 %), Redundanz gering (r -0,097 zu funding, -0,168 zu turnover). War als ,traegt nicht' abgelehnt

- Quelle: Methodik 2.145 / n59_abgelehnte_auf_selektierter_menge.py

**2.145-turnover5** — ⚠️ `turnover` verliert bei 5 % Auswahlstaerke ALLE Tage (65 Symbole, davon 5 % = 2 Anker). Die Produktionsauswahl IST diese 5 % - sein Beitrag ist bei der tatsaechlichen Auswahlstaerke NICHT messbar

- Quelle: Methodik 2.145

**2.162** — ✔✔ DIE LOESUNG FUER `turnover`: DIE MENGE MUSS ZUR DATENLAGE PASSEN. Kriterium, vorab gesetzt und fuer ALLE Beitraege gleich: die SCHMALSTE Menge, die noch >= 12 Anker je Tag liefert (dieselbe Untergrenze, die `sammle` bereits im Code verwendet). Ergebnis: turnover 50 %, funding 10 %, oi_aenderung 20 %, zufall 5 %. Dort traegt jeder der drei ab 2022 - turnover +0,0598, funding +0,0607, oi_aenderung +0,0446, alle mit Band ohne Null; `zufall` +0,0052 mit Null im Band

- Quelle: Methodik 2.162 / n72_turnover_loesung.py

**2.162-grund** — Der GRUND war nie der Beitrag: `turnover` deckt 66 von 524 Symbolen ab. 20 % davon sind 10,1 Anker je Tag - und N-65 hat gemessen, dass die Statistik bei so kleinen Gruppen fast nur Rauschen ist. Wer alle Beitraege auf 20 % zwingt, misst bei einem von ihnen Rauschen

- Quelle: Methodik 2.162

**2.162-b** — ⚠️ Die DATENQUELLE wurde mitgeprueft und ist in Ordnung (stehende Vorgabe). Der `splycur`-Ausreisser ab 2023 ist XVG - aber eine grosse UMLAUFMENGE macht den Quotienten KLEIN. Die Kennzahl selbst ist stabil ueber alle Jahre (Median 0,003-0,010, P95 0,036-0,079) und geht ohnehin als RANG ein

- Quelle: Methodik 2.162

**2.162-extreme** — Und die Fuenftel zeigen, warum die LIVE-Regel nie betroffen war: die EXTREME sind ueber die Aeren stabil - F0 +0,2314 -> +0,2745, F4 -0,1354 -> -0,1316. Nur die MITTE dreht (F1 +0,5334 -> +0,0375). Die Sperre trifft F4

- Quelle: Methodik 2.162

**2.161** — ✔✔ DIE ZEITSTABILITAET DER LEBENDEN BEITRAEGE - erstmals gemessen. `oi_aenderung` ist der SOLIDESTE: stabil bis 0,05 R (Haelften -0,0038) und traegt in JEDEM Fenster - ganz +0,0296 [+0,0146 .. +0,0443], ab 2022 +0,0296, ab 2024 +0,0287. Praktisch unveraendert ueber die Zeit. `funding` ebenso: stabil bis 0,05 R, traegt ab 2022 (+0,0157) und ab 2024 (+0,0182)

- Quelle: Methodik 2.161 / n70_stabilitaet_der_lebenden.py

**2.161-rr11** — R-R11 erfuellt, BEVOR das behauptet wird: `pruefe_auswahl` reproduziert den registrierten Anker exakt - turnover frei +0,0616 [+0,0185 .. +0,1084] gegen Anker +0,06163 [+0,01851 .. +0,10841]. ⚠️ AUF DER SELEKTIERTEN Menge aber, wo Beitraege zu beurteilen sind (F-212, frageart=beitrag), liegt er bei +0,0865 [-0,0060 .. +0,1696] - das Band schliesst die Null EIN, Urteil 'traegt nicht bis 0,10 R'. Der registrierte Befund stammt von der FREIEN Menge

- Quelle: Methodik 2.161

**2.161-f217** — ⚠️ Das VERSTAERKT F-217 ('funding haelt, turnover NICHT - gegen zwei Nullpunkte') aus einer voellig anderen Richtung: dort war es die Kalibrierung, hier die Zeitachse. Zwei unabhaengige Zugaenge, dasselbe Ergebnis - das ist mehr als eine Wiederholung

- Quelle: Methodik 2.161

**2.161-massstab** — ⚠️ WARUM DIESE MESSUNG UEBERHAUPT KAM: der Test, an dem `schnitt` gescheitert ist, war auf die LIVE laufenden Beitraege nie angewandt worden. Einen Kandidaten an einer Huerde scheitern zu lassen, die die Bestandsbeitraege nie nehmen mussten, waere zweierlei Mass gewesen

- Quelle: Methodik 2.161

**2.171** — ⛔⛔ `hedge` IST STRUKTURELL AUSSERHALB DER BEITRAGSMASCHINERIE - aus DREI unabhaengigen Gruenden, nicht wegen fehlender Daten. Jeder einzelne genuegt

- Quelle: Methodik 2.171 / Bestandsdurchsicht 07.09.

**2.171-zwei** — GRUND 1 - ZWEI INSTRUMENTE. `hedge` kennt DBPK (S&P 500 2x invers) und 3QSS (Nasdaq-100 3x short). `messe_beitrag_auf_auswahl.sammle` verwirft Tage mit weniger als 12 Werten. Zwei Werte sind kein Querschnitt - es gibt nichts zu rangen

- Quelle: Methodik 2.171

**2.171-rekonstruiert** — GRUND 2 - DIE REIHEN SIND REKONSTRUIERT und ihre Grenze steht in der eigenen Dokumentation: `agent/rekonstruktion.py` sagt woertlich, die Reihen taugen 'fuer KURZE Horizonte (Tage bis zwei Wochen)' und 'NICHT fuer Aussagen ueber Monate'. Es fehlen Rollkosten, Gebuehren und beim Hebelprodukt der Wechselkurs. ⚠️ H20 sind VIER Wochen - ausserhalb der benannten Gueltigkeit

- Quelle: Methodik 2.171

**2.171-frage** — GRUND 3 - ES IST EINE ANDERE FRAGE. Das Hedge-Regelwerk (`agent/hedge/analyst.py`) fragt WANN abgesichert wird: Regel 5 nennt `aktien_baermarkt.aktiv`, VIX, DXY, Regel 6 die Makro-Analoge. Das ist eine ZEITREIHEN-Frage. Die Beitragsmaschinerie rangt innerhalb des Tages - sie ist querschnittlich (N-75). Und Regel 3 sagt ausdruecklich: 'das Ziel ist NICHT maximaler Gewinn der Hedge-Position selbst, sondern eine ANGEMESSENE Portfolio-Absicherung' - `bewegung_r` misst also die falsche Groesse

- Quelle: Methodik 2.171

**2.171-aufbau** — WIE `hedge` HEUTE FUNKTIONIERT: es ist KEINE Assetklasse, sondern eine ROLLE - die Instrumente stehen in der Watchlist als `etf`, deshalb hat `price_history_ohlc` keine hedge-Zeile. Deckel: max_abdeckung_anteil 1,0, bull_wahrscheinlichkeit_schwelle 35 % mit Positionsdeckel 0,5. Beide Positionen sind GEHALTEN (3QSS 218,25 · DBPK 1.739,16) und haben Einstandspreise (2,05 bzw. 0,1713 EUR, in `avg_buy_price_manual_eur`)

- Quelle: Methodik 2.171

**2.171-offen** — ⚠️ WAS VON HIER AUS NICHT FESTSTELLBAR IST: ob `hedge` produktiv Signale erzeugt. Die Desktop-Kopie der Produktiv-DB endet Mitte Juli 2026 (`signals` 21.07., `holdings` 19.07.); die laufende Produktion ist das Notebook. Die 0 Hedge-Signale in dieser DB sind deshalb KEIN Befund ueber den Betrieb

- Quelle: Methodik 2.171

**2.171-weg** — WAS `hedge` STATTDESSEN BRAUCHT: ein eigenes Bewertungsverfahren auf der ZEITACHSE - 'wann absichern', gemessen gegen die Regime-Groessen, die das Regelwerk bereits nennt. ⚠️ Das ist dieselbe Frage wie die der MAKRO-Schichter aus N-8: `macro_snapshot` (3.384 Tage) und `makro_historie_monat` (1.184 Monate) haben je Tag EINEN Wert fuer alle Assets - sie koennen kein Querschnittsbeitrag sein, wohl aber ein Regime-Schichter

- Quelle: Methodik 2.171

**2.189** — N-82: die Beitragslage unter BEIDEN Nullregeln, 16 Kandidaten auf allen zulaessigen selektierten Mengen. `zufall` traegt unter KEINER der beiden - der Lauf ist gueltig. 14 von 16 Kandidaten behalten ihr Urteil UNVERAENDERT

- Quelle: n82_beitragslage_beide_nullregeln.py

**2.189-wechsel** — ⚠️ Genau EIN Kandidat wechselt: `funding` von TRAEGT auf NICHT ENTSCHEIDBAR. Er trug nur bei 50 % und dort mit +0,0002 R Abstand. ⚠️ NICHT ENTSCHEIDBAR ist eine Aussage ueber die MESSUNG, nicht ueber `funding` - er ist damit NICHT widerlegt

- Quelle: n82_beitragslage_beide_nullregeln.py

**2.189-beidseitig** — ⚠️ DIE NEUE REGEL IST NICHT STRENGER, SONDERN STABIL - sie bewegt sich in BEIDE Richtungen. `schnitt` bei 10 % kippt umgekehrt, von traegt-nicht auf TRAEGT (null_oben 0,0609 -> 0,0482), weil das Maximum ueber fuenf Ziehungen dort zufaellig HOCH lag. Wer die Regel fuer eine Verschaerfung haelt, hat sie nicht verstanden

- Quelle: n82_beitragslage_beide_nullregeln.py

**2.190** — ✔✔ R-R11 ERFUELLT: der `funding`-Originalbefund vom 30.08. (+0,137 R) stand auf der Menge `frei` - die Mengen-Systematik gab es damals nicht. Auf DIESER Basis nachgemessen traegt er unter BEIDEN Regeln: Abstand +0,0042 (alt) und +0,0044 (neu), 353.892 Anker, 299 Symbole, 39 Bloecke. Der Befund steht

- Quelle: n83_frei_beide_nullregeln.py

**2.190-form** — ✔ UND DIE LIVE-FORM PASST DAZU: `funding` ist als 'Funding-Rang im MARKT' registriert - `frei` beantwortet nach P6/F-212 genau die Marktfrage. Was faellt, ist `funding` als BEITRAG auf der selektierten Menge; die live genutzte Form ist davon unberuehrt

- Quelle: n83_frei_beide_nullregeln.py

**2.191** — ⚠️⚠️ `turnover` KIPPT dagegen auf seiner einzigen Basis `frei`: Abstand +0,0018 (alt) -> -0,0008 (neu), Urteil NICHT TRENNBAR. Auf den selektierten Mengen war er schon vorher nicht entscheidbar. Damit hat `turnover` unter der stabilen Nullregel KEINE Basis mehr, auf der er traegt

- Quelle: n83_frei_beide_nullregeln.py

**2.191-inkonsistenz** — ⚠️⚠️ UND GENAU DORT SCHLAEGT DIE ZWEITE UNSTIMMIGKEIT DURCH (2.188-inkonsistenz): `turnover`s Urteil lautet woertlich 'Wirkung +0,0639 ueber der Trennschaerfe 0,0500 R, aber ...'. Die TRENNSCHAERFE wurde gegen NULL bestimmt, das URTEIL faellt gegen null_oben = 0,0220. Beide Massstaebe in EINEM Satz, und sie widersprechen sich

- Quelle: n83_frei_beide_nullregeln.py

**2.192** — ⚠️ DER STAND DER DREI LIVE GEMESSENEN BEITRAEGE unter der stabilen Nullregel: `schnitt` traegt als BEITRAG (10 % und 20 %, Abstand bis +0,0569) · `funding` traegt als MARKT-Aussage (frei, +0,0044) · `turnover` traegt NIRGENDS mehr. ⚠️ Die Nullregel ist NICHT umgestellt - sie ist nur als Parameter verfuegbar, Vorgabe unveraendert. Das ist eine Nutzerentscheidung

- Quelle: N-82 / N-83 / Nutzervorlage 08.09.

**2.193** — ⚠️ ORDNUNGSFEHLER IN `messnorm.urteil`: die Abfrage `if self.trennschaerfe is None -> KEIN BEFUND` steht VOR `if self.traegt -> TRAEGT`. Ein echtes TRAEGT wird dadurch verdeckt. `Befund.traegt` selbst bleibt korrekt - nur der ausgegebene Satz widerspricht ihm

- Quelle: n84_trennschaerfe_massstab.py

**2.194** — ⚠️⚠️ DIE LEITER DER GEPFLANZTEN STAERKEN ENDET ZU FRUEH: (0,02 · 0,05 · 0,10), waehrend `schnitt` bei 20 % eine Wirkung von +0,1858 hat - fast doppelt so viel wie die groesste Stufe. 'Untermaechtig' war eine Aussage ueber die LEITER, nicht ueber die Anlage

- Quelle: n85_leiter_zu_kurz.py

**2.194-bestand** — ⚠️ Und der eigene Werkzeugkasten widerspricht sich hier: `messnorm_rand.py` benutzt seit jeher die laengere Leiter (0,02 · 0,05 · 0,10 · 0,20), `messnorm.py` und `messnorm_auswahl.py` die kurze

- Quelle: Codelesung 08.09.2026

**2.194-probe** — ✔ DIE LANGE LEITER IST KEIN FREIBRIEF - das war die vorab benannte Probe. Sie holt `schnitt` 10 % und 20 % von KEIN BEFUND auf TRAEGT zurueck, rettet aber `turnover` und `funding`-50 % NICHT: dort bleibt es bei 'traegt nicht bis 0,20/0,40 R'. Und `zufall` traegt unter keiner Leiter

- Quelle: n85_leiter_zu_kurz.py

**2.195** — ⚠️ `traegt` hat sich unter KEINER der drei Aenderungen geaendert (Nullregel ausgenommen): weder die gleichgezogene Trennschaerfe noch die laengere Leiter beruehren es. Beide aendern nur die BEGRUENDUNG - was genau der Zweck der vier Urteile ist

- Quelle: n84 + n85

**2.196** — ⚠️ TURNOVER IST NICHT WIDERLEGT, SONDERN UNENTSCHIEDEN: mit langer Leiter lautet sein Urteil 'traegt nicht bis 0,20 R' auf `frei` und 'bis 0,40 R' bei 50 %. Ausgeschlossen sind also nur Effekte ab 0,20 R - seine gemessene Wirkung betraegt +0,0639. Ueber DIESE Groesse sagt die Anlage nichts

- Quelle: n85_leiter_zu_kurz.py

**2.197** — ✔✔ `funding` AUF `frei` IST DER ROBUSTESTE BEFUND: er traegt unter beiden Nullregeln, unter beiden Trennschaerfe-Massstaeben und unter beiden Leitern - einziger Fall, der ALLE vier Varianten uebersteht, mit einer Trennschaerfe von 0,10 statt 0,40

- Quelle: n83 + n84 + n85

**2.198** — ⚠️ OFFEN UND NICHT VERFOLGT: die Positivkontrolle pflanzt in die GEMISCHTE Welt, deren Band breiter sein kann als das der echten. Dann ueberschaetzt die Trennschaerfe systematisch, was noetig waere - `schnitt` traegt mit Wirkung +0,186 bei ausgewiesener Trennschaerfe 0,40. Dritter Punkt derselben Anlage, bewusst nicht im selben Zug geaendert

- Quelle: n85_leiter_zu_kurz.py

**2.199** — ✔ DER MESSSTANDARD IST GESETZT (08.09.2026, Nutzerentscheidung): NULL_ZIEHUNGEN=40 · NULL_PERZENTIL=90 · TRENNSCHAERFE_GEGEN_NULLPUNKT=True · STAERKEN bis 0,40. Benannt in `messnorm`, von `messnorm_auswahl` und `messnorm_rand` von DORT bezogen, in Klartext ausgebbar (`standardzeile`)

- Quelle: messnorm.py / Methodik 2.188

**2.199-abnahme** — ✔ UND ER WURDE ABGENOMMEN, BEVOR ER STANDARD WURDE: erst neutral parametrisiert und Ziffer fuer Ziffer gegen die Vorgaengerfassung geprueft · dann beide Regeln nebeneinander (N-82: `zufall` unter keiner tragend, 14 von 16 Urteilen unveraendert) · dann R-R11 auf der Originalbasis (N-83) · dann die vorab benannte Probe gegen Gefaelligkeit (N-85)

- Quelle: N-81 bis N-85 / Methodik 2.188

**2.199-waechter** — ✔ Das Pruefpaket `Messstandard` bewacht ihn mit zehn Pruefungen - nicht die WERTE (die duerfen sich begruendet aendern), sondern dass sie benannt, an EINER Stelle und ueberall gleich sind. Alle zehn sind durch MUTATION belegt: Fehler zurueckgebaut, Waechter feuert

- Quelle: pruefe_pakete.py --paket Messstandard

**2.199-rand** — ⚠️ DABEI KAM EIN VIERTES BETROFFENES MODUL HERAUS: `messnorm_rand.py` hatte ALLE DREI Fehler, und zwar in BEIDEN Messfunktionen. Es gehoert zur Normfamilie und war bis dahin nie mitbetrachtet worden - genau die Uneinheitlichkeit, die 2.194 aufgedeckt hat

- Quelle: Codelesung 08.09.2026

**2.199-offen** — ⚠️⚠️ WAS DER STANDARD NICHT LEISTET: er macht die Urteile WIDERSPRUCHSFREI, nicht SCHAERFER. Offen bleiben 2.198 (Positivkontrolle pflanzt in die gemischte Welt), `ZIEHUNGEN`=5 in der Positivkontrolle, ob p90 zum Vertrauensniveau des Bandes passt - und vor allem der SELBSTTEST der ganzen Anlage gegen bekannte Wahrheit (Fehlalarm- UND Fundquote). 'Die Basis steht' waere eine Behauptung, kein Befund

- Quelle: Methodik 2.188 / Expertenurteil 08.09.

**2.200** — ⚠️⚠️ R-R9 GREIFT: die Beitragslage hat sich geaendert, also ist eine Neukalibrierung faellig. Live registriert sind `funding` (Markt-Rang - haelt), `turnover` (Markt-Rang - jetzt unentschieden) und `schnitt` (haelt, und traegt jetzt auf ZWEI Mengen statt einer). ⚠️ `turnover`s Stufen (3,15/0,83/0,22/-1,79/-2,4) stehen auf einer Basis, die keinen tragenden Befund mehr liefert

- Quelle: agent/wahrscheinlichkeit.BEITRAEGE

**2.200-nicht-abraeumen** — ⚠️ ABER `turnover` WIRD NICHT ABGERAEUMT. Sein Urteil lautet 'traegt nicht bis 0,20 R' - ausgeschlossen sind nur Effekte ab 0,20 R, seine Wirkung betraegt +0,0639. Ueber DIESE Groesse sagt die Anlage nichts. Nutzervorgabe, stehend: 'bevor eine Bewertung faellt muessen wir alles unternehmen'. Das verlangt eine bessere Messung, keine Abwertung

- Quelle: Nutzervorgabe / Befund 2.196

**2.201** — ⚠️⚠️⚠️ FEHLER 5 - TRENNSCHAERFE UND WIRKUNG STANDEN AUF ZWEI SKALEN, und `messnorm.urteil` verglich sie miteinander. `trennschaerfe` war die GEPFLANZTE Staerke, `wirkung` die GEMESSENE Groesse. Der Faktor ist (1 - GRENZE) = 20 %: gesenkt werden die oberen 20 %, `median(alle)` verschiebt sich nur um diesen Anteil, `median(frei)` gar nicht

- Quelle: selbsttest_welt.py + Nachmessung 08.09.

**2.201-beleg** — ✔ DREIFACH BELEGT: aus der Definition hergeleitet (20 %) · in der Kunstwelt gemessen (17,8 / 18,7 / 19,3 / 19,7 / 19,5 % ueber fuenf Staerken) · an den ECHTEN Daten nach Abzug des Grundpegels (+0,0145) gemessen: 20,3 / 20,1 / 19,6 / 19,2 % fuer s = 0,05 / 0,10 / 0,20 / 0,40

- Quelle: Nachmessung 08.09.2026

**2.201-loest-2198** — ✔✔ UND ES LOEST BEFUND 2.198 AUF: `schnitt` traegt mit Wirkung +0,186 bei ausgewiesener Trennschaerfe 0,40 - das sah nach Widerspruch aus. Auf der gemessenen Skala betraegt die Trennschaerfe 0,0944, und 0,186 liegt klar darueber. KEIN Widerspruch. Die Vermutung 'die Positivkontrolle pflanzt in die gemischte Welt und ueberschaetzt' war die falsche Spur

- Quelle: Nachmessung 08.09.2026

**2.201-turnover** — ⚠️⚠️ UND ES AENDERT `turnover`s URTEILSKATEGORIE: Wirkung +0,0639 gegen die gemessene Trennschaerfe 0,0456 - die Wirkung liegt UEBER der Aufloesung, das Band schliesst die Null aber ein. Das Urteil lautet jetzt NICHT TRENNBAR statt 'traegt nicht bis 0,20 R'. Er ist unentschieden, und die Anlage sagt das jetzt auch

- Quelle: Nachmessung 08.09.2026

**2.201-satz-war-falsch** — ⚠️ Der Satz 'Effekte ab dieser Groesse sind ausgeschlossen' war damit um Faktor 5 zu schwach. Ausgeschlossen waren nie Effekte ab 0,20 R, sondern ab rund 0,046 R. Jede so begruendete Ablehnung war zu nachsichtig formuliert

- Quelle: messnorm.Befund.urteil

**2.201-rand-hatte-recht** — ⚠️ ZUM DRITTEN MAL AN EINEM TAG: `messnorm_rand.py` trennte beide Skalen SEIT JEHER richtig (`trennschaerfe = mean(werte)`, `trennschaerfe_in_r = s`) - `messnorm` und `messnorm_auswahl` nicht. Erst war es die Leiter (2.194), dann die Nullregel, jetzt die Skala. Das Modul war nie Teil der Normbetrachtung

- Quelle: Codelesung 08.09.2026

**2.202** — ⚠️ DER PRUEFSTAND FUER DEN SELBSTTEST STEHT und hat seinen Vorabtest bestanden: die Nullwelt ist leer (Mittel -0,0011 bei Streuung 0,0019) · die wahre Wirkung je Staerke ist nachgemessen statt angenommen · die Autokorrelation auf Blocklaenge ist mit der echten vergleichbar (+0,032 gegen -0,004, Grenze 0,15)

- Quelle: selbsttest_welt.py

**2.202-nicht-pflanze** — ⚠️⚠️ ENTWURFSREGEL DES PRUEFSTANDES: er benutzt `pflanze` NICHT. Die Welten werden von Grund auf mit der Beziehung gebaut, sonst pruefte der Test den Mechanismus mit sich selbst - und genau dieser Mechanismus stand unter Verdacht. Der Tagesschock ist AR(1), weil unabhaengige Tage keine Bloecke braeuchten und die Fehlalarmquote schmeichelhaft ausfiele

- Quelle: selbsttest_welt.py

**2.203** — ⚠️⚠️ DIE LEHRE AUS DREI FEHLERN AN EINEM TAG: `messnorm_rand.py` hatte jedes Mal recht, weil es aus der Normbetrachtung ausgeklammert war. Daraus die Frage, die vor jeder Normaenderung zu stellen ist: WER GEHOERT NOCH ZUR FAMILIE? Nachgesehen: die Normfamilie ist `messnorm` + `messnorm_auswahl` + `messnorm_rand` - alle drei sind jetzt gleichgezogen

- Quelle: Codedurchsicht 08.09.2026

**2.203-altbestand** — ⚠️⚠️ ABER DREI ALTBESTANDSWERKZEUGE bauen eigene Kontrollen: `messe_beitragssumme.py` (mittelt ueber Ziehungen und weist die Streuung aus - sauber), `n19e_neukalibrierung.py` und `messe_volumenanteil.py`

- Quelle: Codedurchsicht 08.09.2026

**2.203-volumenanteil** — ⚠️⚠️⚠️ `messe_volumenanteil.py` faehrt seine Negativkontrolle mit EINER EINZIGEN Ziehung (`mische=rng`, kein Wiederholen, keine Mehrheitsregel), Positivkontrolle nur bis 0,05. Das verletzt die eigene stehende Vorgabe 'eine Ziehung ist kein Nullpunkt' direkt - und aus diesem Werkzeug stammt der registrierte Befund N-13-1' 'der Volumenanteil traegt'. ⚠️ NICHT nachgemessen (08.09.), nur festgestellt - der Befund steht damit unter Vorbehalt, ist aber NICHT widerlegt

- Quelle: Codedurchsicht 08.09.2026

**2.204** — ✔✔✔ DER SELBSTTEST DER MESSANLAGE GEGEN BEKANNTE WAHRHEIT IST GELAUFEN - zum ersten Mal. 50 Nullwelten und 120 Welten mit bekanntem Effekt, gebaut OHNE `pflanze`, mit AR(1)-Tagesschock und der echten Streuung der Messbasis (IQA 3,073)

- Quelle: selbsttest_messanlage.py / selbsttest_welt.py

**2.204-fehlalarm** — ✔ FEHLALARMQUOTE: 0 von 50 Nullwelten. Sollwert war <= 2,5 % (das Band ist ein 95-%-Band). ⚠️ 0/50 schliesst eine wahre Quote bis rund 6 % NICHT aus (Dreierregel) - 'nicht hoch' ist belegt, 'exakt null' nicht

- Quelle: selbsttest_messanlage.py

**2.204-aufloesung** — ✔ DIE AUFLOESUNG BETRAEGT +0,0293 R (80-%-Fundquote). Die Uebergangszone ist schmal: +0,0104 -> 0 % · +0,0195 -> 30 % · +0,0293 -> 95 % · +0,0363 -> 100 %. Von blind zu sicher in 0,01 R - kein Graubereich

- Quelle: selbsttest_messanlage.py

**2.204-behauptung** — ✔✔ UND DIE ANLAGE SAGT DIE WAHRHEIT UEBER SICH SELBST: sie weist eine Trennschaerfe von +0,0389 aus und findet tatsaechlich ab +0,0293 - sie ist also 25 % BESSER als versprochen, nicht schlechter. Nullbefunde sind damit staerker, als die Anlage selbst ausweist

- Quelle: selbsttest_messanlage.py

**2.204-bestaetigt-2201** — ✔✔ DAMIT IST DIE SKALENKORREKTUR (2.201) UNABHAENGIG BESTAETIGT: vor ihr haette die Anlage 'Trennschaerfe 0,20' behauptet bei einer echten Aufloesung von 0,029 - Faktor 7 daneben. Nach ihr stimmen Behauptung und Wirklichkeit auf 25 % ueberein

- Quelle: selbsttest_messanlage.py

**2.205** — ⚠️⚠️ WAS DER SELBSTTEST UEBER `turnover` SAGT: seine Wirkung (+0,0639) liegt beim 2,2-fachen der Aufloesung (0,0293) - sie ist NICHT zu klein zum Sehen. Dass das Band den Nullpunkt trotzdem einschliesst, heisst die Wirkung ist ueber die BLOECKE instabil. Das ist ein anderer Befund als 'zu schwach' - und er sagt, wo nachzusehen waere

- Quelle: selbsttest_messanlage.py

**2.205-einschraenkung** — ⚠️ EINSCHRAENKUNG, DIE DAZUGEHOERT: die Kunstwelt hat 150 Symbole x 1500 Tage, `turnover` auf `frei` nur 66 Symbole. Die Aufloesungszahl ist deshalb NICHT eins zu eins uebertragbar - der Vergleich ist ein Hinweis, kein Beweis

- Quelle: selbsttest_messanlage.py

**2.206** — ⚠️⚠️ EINE LUECKE IM EIGENEN PRUEFSTAND, VOR DEM ERGEBNIS GEFUNDEN: er zog die Kennzahl jeden Tag neu (Autokorrelation 0). An den echten Daten gemessen: `zufall` -0,001 · `funding` +0,608 · `schnitt` +0,985. Bei `schnitt` stehen an fast allen Tagen DIESELBEN Symbole in der gesperrten Gruppe - ein Pruefstand ohne Beharrlichkeit sagt ueber die beiden TRAGENDEN Beitraege nichts

- Quelle: selbsttest_welt.py

**2.206-gebaut** — ✔ Die Achse ist eingebaut und geprueft: AR(1) je Symbol, eingestellt 0,000/0,610/0,985 -> gemessen -0,007/0,601/0,978. Die Vorgabe bleibt 0, damit die schon gemessenen Zahlen reproduzierbar bleiben

- Quelle: selbsttest_welt.py

**2.207** — ✔✔✔ DIE BEHARRLICHKEIT AENDERT NICHTS: 0 Fehlalarme in 50 Nullwelten bei AK 0,610 (funding-artig) UND 0 in 50 bei AK 0,985 (schnitt-artig). Auch die Streuung der Nullwelten bleibt praktisch gleich (0,0047 / 0,0042 gegen 0,0047 ohne Beharrlichkeit). Die Blockbootstrap faengt sie ab

- Quelle: selbsttest_messanlage.py --ak

**2.207-schaerfer** — ✔✔ DAMIT WIRD DIE AUSSAGE SCHAERFER: 0 Fehlalarme in 150 Nullwelten ueber DREI Beharrlichkeitsstufen. Obere 95-%-Schranke nach der Dreierregel: 2 % - unterhalb des nominalen Sollwerts von 2,5 %. Das ist der erste belastbare Nachweis, dass die Anlage nicht ins Leere feuert

- Quelle: selbsttest_messanlage.py

**2.207-vermutung-falsch** — ⚠️ UND EINE EIGENE VERMUTUNG WAR FALSCH: ich hatte erwartet, die Beharrlichkeit werde die Fehlalarmquote treiben, weil sie weniger unabhaengige Beobachtungen bedeutet. Sie tut es nicht. Die Sorge war berechtigt, das Nachmessen richtig - das Ergebnis entlastet

- Quelle: selbsttest_messanlage.py --ak

**2.208** — ✔ R-R9 IM ENGEREN SINN IST ERFUELLT: die Beitragslage im Code ist unveraendert (funding + turnover), der Fingerabdruck `KALIBRIERT_FUER` stimmt mit `BEITRAEGE` ueberein, und die Kalibrierung reproduziert auf der HEUTIGEN Messbasis praktisch ziffergenau: 0,080 -> 16,5 % Durchlass (31.08. ebenso), Gewinn +0,1316 gegen +0,1324. Basis von 123.465 auf 124.221 Anker gewachsen

- Quelle: messe_schwelle_kalibrierung.py

**2.208-schnitt** — ⚠️⚠️ DABEI KAM HERAUS, DASS `schnitt` NIE WIEDER AUFGENOMMEN WURDE: seine Ruecknahme vom 31.08. ist seit dem 07.09. als ABGELOEST verzeichnet (2.153, kontaminierte Basis - 1.314 Symbole statt Krypto allein), aber im Code steht er weiter auf `zustand=null, stufen=None`. Die Ruecknahme ist gefallen, die Konsequenz daraus nie gezogen

- Quelle: agent/wahrscheinlichkeit.BEITRAEGE / REGISTER_Kandidaten

**2.208-n86** — ✔ N-86 bestaetigt das unabhaengig mit einem ANDEREN Werkzeug: `schnitt` auf `frei` bei H5 +0,0094 gegen +0,0092 der 07.09.-Reproduktion. Und auf der 20-%-Menge traegt er bei FUENF von sechs Horizonten, mit monoton wachsender Wirkung (+0,0130 H1 -> +0,0418 H5 -> +0,1858 H20). Die Ausnahme H10 ist eine Enthaltung, kein Widerspruch

- Quelle: n86_rr9_schnitt_ueber_horizonte.py

**2.208-aber** — ⚠️ ABER `schnitt` KANN TROTZDEM KEIN REGLER SEIN: 2.158 gilt unveraendert - die fuenf Stufen sind ein BUCKEL (+4,07/+5,55/+9,49/+1,71/-4,65, Hochpunkt bei Fuenftel 2), zweimal gemessen. Die Vorabfestlegung verlangt Monotonie. Es gibt also gar keinen Beitragswechsel, fuer den zu kalibrieren waere - der Registerstand 'offen, nicht live' ist richtig

- Quelle: Befund 2.158 / REGISTER_Kandidaten

**2.209** — ⚠️⚠️ EIGENE KORREKTUR: ich habe `turnover` heute auf der VOLLEN Historie gemessen und daraus 'nicht trennbar' geschlossen. Seine registrierte Basis ist aber 50 % AB 2022 (2.162). Das war derselbe R-R11-Verstoss, den ich bei `funding` am selben Tag noch vermieden hatte

- Quelle: n87_rr11_auf_der_eigenen_basis.py

**2.209-reproduziert** — ✔ AUF DER EIGENEN BASIS REPRODUZIEREN DIE WIRKUNGEN FAST ZIFFERGENAU: turnover +0,0608 gegen Anker +0,0598 · oi_aenderung +0,0442 gegen +0,0446 · funding +0,0542 gegen +0,0607. Was sich geaendert hat, ist NICHT der Effekt, sondern das KRITERIUM

- Quelle: n87_rr11_auf_der_eigenen_basis.py

**2.210** — ⚠️⚠️⚠️ FEHLER 6 - DAS KRITERIUM ZAEHLT DIE UNSICHERHEIT DOPPELT. `traegt = unten > null_oben` verlangt, dass die UNTERE Vertrauensgrenze des Effekts die OBERE der Nullwelt ueberschreitet - also zwei 95-%-Baender, die sich nicht ueberlappen. Das entspricht etwa p < 0,005, nicht p < 0,05

- Quelle: Nullpunkt-Zerlegung 08.09.2026

**2.210-beleg** — ✔ DER BELEG: der Nullpunkt hat kaum VERSATZ, aber ein breites BAND. null MITTEL +0,0068 (turnover) / +0,0106 (funding) / +0,0172 (oi_aenderung) / +0,0081 (zufall) - null_oben dagegen +0,0592 / +0,0414 / +0,0495 / +0,0397. `null_oben` ist also im Wesentlichen die obere Vertrauensgrenze EINER Nullwelt, ein Streumass - und die Streuung steckt im Band schon drin

- Quelle: Nullpunkt-Zerlegung 08.09.2026

**2.210-erklaert** — ✔✔ UND ES ERKLAERT ZWEI BISHER UNVERBUNDENE BEOBACHTUNGEN: warum der Selbsttest 0 Fehlalarme in 150 Welten fand (nominal 2,5 % erlaubt - die Anlage ist uebervorsichtig), und warum das dort kaum auffiel: in der Kunstwelt (150 Symbole, 1500 Tage) sind die Baender ENG, die Doppelzaehlung faellt kaum ins Gewicht. Auf den echten schmalen Basen (turnover: 66 Symbole) sind sie BREIT - dort dominiert sie

- Quelle: selbsttest_messanlage.py + Nullpunkt-Zerlegung

**2.210-nicht-geaendert** — ⚠️⚠️ NICHTS DAVON WURDE GEAENDERT. Den Standard zu lockern, weil er den eigenen Beitraegen im Weg steht, waere motiviertes Rechnen. Der saubere Weg ist der, fuer den der Pruefstand gebaut wurde: die Alternative auf Fehlalarm- UND Fundquote messen, BEVOR sie gewaehlt wird

- Quelle: Nutzervorgabe 08.09. / selbsttest_messanlage.py

**2.211** — ⚠️ EINE LUECKE IM KALIBRIERUNGSWERKZEUG, beilaeufig gefunden: `messe_schwelle_kalibrierung.py` liest die Stufen zwar aus der LIVE-Registrierung (keine Kopie), aber nur fuer die zwei fest verdrahteten Merkmale `funding_fuenftel` und `turnover_fuenftel`. Ein DRITTER Beitrag wuerde still ignoriert - und die Kalibrierung waere falsch, ohne dass es auffaellt

- Quelle: messe_schwelle_kalibrierung.py

**2.212** — ⚠️⚠️⚠️ EINSCHRAENKUNG DES SELBSTTESTS VOM 08.09.: die Kunstwelt ist SECHSMAL PRAEZISER als die Wirklichkeit. Bandbreite 0,018 gegen 0,108 beim echten `turnover` auf 50 % ab 2022. Die dort gemessene Aufloesung von +0,0293 R und die 0 Fehlalarme gelten damit fuer eine Welt, die deutlich leichter ist als die echte

- Quelle: selbsttest_kriterien.py / Nachmessung 09.09.

**2.212-diagnose** — ⚠️ DIE URSACHE LIEGT IN DER TAGESREIHE, aus der das Band entsteht: echt 1.692 Tage mit SD 0,3307 und Autokorrelation +0,602 (SD je Block 0,1473) - kuenstlich SD 0,1500, AK1 +0,197, SD je Block 0,0315. Die echte Reihe ist doppelt so streuend UND dreimal so traege

- Quelle: Nachmessung 09.09.2026

**2.212-drei-versuche** — ⚠️ DREI ERKLAERUNGSVERSUCHE, ALLE UNZUREICHEND: Schwankung des Effekts ueber die Tage (selbst beim Fuenffachen nur 0,031) · Ueberlappung der Zielgroesse (H20 teilt 19 von 20 Tagen - brachte nichts, 0,015) · Beharrlichkeit der Kennzahl (turnover +0,669 gemessen). Alle drei zusammen: 0,029 gegen echte 0,108

- Quelle: Nachmessung 09.09.2026

**2.212-abgebrochen** — ⚠️⚠️ UND DANN ABGEBROCHEN, statt weiterzukalibrieren: eine Kunstwelt so lange anzupassen, bis sie passt, ist Probieren - und hinterher nicht mehr auseinanderzuhalten. Die drei Achsen bleiben im Werkzeug (`staerke_streuung`, `ueberlappung`, `kennzahl_ak`), alle mit Vorgabe 0, damit die Zahlen vom 08.09. reproduzierbar bleiben

- Quelle: selbsttest_welt.py

**2.213** — ✔✔ DER BESSERE PRUEFSTAND SIND DIE ECHTEN DATEN SELBST: eine NULLWELT entsteht durch Mischen der Raenge je Kalendertag. Sie hat die echte Streuung, die echte Traegheit und die echte Symbolzahl von selbst, ohne jede Kalibrierung - und enthaelt per Konstruktion keinen Zusammenhang. Jedes 'traegt' darauf ist ein Fehlalarm

- Quelle: selbsttest_kriterien_echt.py

**2.213-erste-zahlen** — ⚠️ UND DER KURZLAUF ZEIGT SOFORT, was die Kunstwelt NIE gezeigt haette (dort 0 % Fehlalarm fuer alle drei): auf `turnover` findet Kriterium A eine Wirkung von +0,0457 in KEINEM Fall, B und C in allen - und auf `funding` erzeugen B und C in 1 von 4 Nullwelten einen Fehlalarm. ⚠️ Acht Welten sind keine Aussage, aber der Aufbau trennt

- Quelle: selbsttest_kriterien_echt.py --klein

**2.213-versatz** — ⚠️ Und er zeigt den Versatz: die Nullwelt auf `funding` 10 % hat eine Wirkung von +0,0164 - in einer Welt OHNE jeden Zusammenhang. Genau diesen Versatz korrigiert `nullpunkt`, und genau deshalb ist 'Band ohne Null' (Kriterium C) zu wenig

- Quelle: selbsttest_kriterien_echt.py --klein

**2.214** — ✔✔✔ DIE DREI KRITERIEN SIND GEGEN BEKANNTE WAHRHEIT GEMESSEN - auf ECHTEN Daten, Nullwelten durch Mischen der Raenge (100 Nullwelten, 36 gepflanzte, zwei Basen). Sollwert 2,5 % Fehlalarme, weil das Band ein 95-%-Band ist

- Quelle: selbsttest_kriterien_echt.py

**2.214-c** — ⚠️⚠️⚠️ KRITERIUM C IST WIDERLEGT: `unten > 0` liefert 22 von 100 Fehlalarmen (22,0 % ± 4,1) gegen einen Sollwert von 2,5 %. Fast ein Viertel der Nullwelten besteht es. ⚠️ DAS IST DAS KRITERIUM AUS BEFUND 2.162 - auf ihm wurden `turnover`, `funding` und `oi_aenderung` auf ihren eigenen Basen als tragend gefuehrt

- Quelle: selbsttest_kriterien_echt.py

**2.214-a** — ⚠️⚠️ KRITERIUM A IST ZU STRENG - und zwar gemessen, nicht nur hergeleitet: 0 von 100 Fehlalarmen, aber es findet eine Wirkung von +0,0448 in KEINEM einzigen von sechs Faellen und +0,0676 nur in vier von sechs. Fundquote insgesamt 58,3 %. ⚠️ `turnover`s echte Wirkung betraegt +0,0608 - sie liegt genau in dem Bereich, den A nicht sieht

- Quelle: selbsttest_kriterien_echt.py

**2.214-b** — ✔✔ KRITERIUM B TRIFFT DAS ZIEL: `unten > max(0, nullpunkt)` liefert 3 von 100 Fehlalarmen (3,0 % ± 1,7) - das Vertrauensband schliesst den Sollwert 2,5 % EIN, es ist davon nicht unterscheidbar. Und die Fundquote betraegt 97,2 % (35 von 36)

- Quelle: selbsttest_kriterien_echt.py

**2.214-warum** — ✔ UND ES PASST ZUR HERLEITUNG (2.210): der Nullpunkt hat einen VERSATZ (Mittel +0,007 bis +0,017, auf `funding`s Nullwelten sogar +0,0139 Wirkung ohne jeden Zusammenhang) - den muss man abziehen, sonst ist C zu locker. Aber seine STREUUNG steckt im Band bereits - wer auch die abzieht, zaehlt doppelt und bekommt A

- Quelle: selbsttest_kriterien_echt.py

**2.214-vorhersage** — ✔ DIE VORHERSAGE STAND VOR DEM LAUF und ist eingetroffen: 'A FA nahe 0, Fundquote bricht ein · B FA um 2,5 %, Fundquote deutlich besser · C FA deutlich ueber 2,5 %'. ⚠️ Und der Ausgang, der den heutigen Standard bestaetigt haette - B mit hoher Fehlalarmquote - war ausdruecklich benannt

- Quelle: selbsttest_kriterien_echt.py

**2.214-nicht-gesetzt** — ⚠️⚠️ NICHTS DAVON IST GESETZT. Der Wechsel von A auf B wuerde Urteile zugunsten der eigenen Beitraege drehen - er gehoert dem Nutzer vorgelegt, wie der Messstandard am 08.09. auch

- Quelle: Nutzerentscheidung offen

**2.215** — ✔ GEGENPRUEFUNG AUF EINER DRITTEN, UNABHAENGIGEN BASIS: `oi_aenderung` 20 % ab 2022 - andere Datenquelle (Terminmarkt statt Kursreihe), andere Menge, 122 statt 64 Symbole. Fehlalarme A 0/50 · B 1/50 = 2,0 % · C 20/50 = 40,0 %. Das Ergebnis ist NICHT basisabhaengig

- Quelle: selbsttest_kriterien_echt.py

**2.215-gesamt** — ✔✔ UEBER ALLE DREI BASEN, 150 Nullwelten: A 0/150 = 0,0 % Fehlalarme bei 63 % Fundquote · B 4/150 = 2,7 % bei 98 % · C 42/150 = 28,0 % bei 100 %. Der Sollwert ist 2,5 %, weil das Band ein 95-%-Band ist

- Quelle: selbsttest_kriterien_echt.py

**2.216** — ✔✔✔ NUTZERENTSCHEIDUNG 09.09.2026: KRITERIUM B IST GESETZT. `messnorm.NULLBEZUG = 'nullpunkt'` - das Urteil prueft gegen den VERSATZ der Nullwelten, nicht gegen ihre STREUUNG. Alternativen bleiben waehlbar ('null_oben', 'null'), damit der frueher Stand reproduzierbar bleibt

- Quelle: messnorm.py / Nutzerentscheidung 09.09.

**2.216-ein-bezug** — ⚠️⚠️ UND URTEIL UND TRENNSCHAERFE LESEN DENSELBEN BEZUG (`messnorm._bezug`). Fehler 2 vom 08.09. war genau das Gegenteil - zwei Massstaebe in EINEM Satz. Wer sie trennt, baut ihn neu ein; deshalb gibt es die Funktion, und deshalb bewacht sie das Pruefpaket

- Quelle: messnorm._bezug / pruefe_pakete --paket Messstandard

**2.216-reproduziert** — ✔ DIE UMSTELLUNG IST SAUBER GEKAPSELT: mit `NULLBEZUG='null_oben'` reproduzieren ALLE ACHT Pruefpunkte den Stand vom 08.09. ziffergenau (schnitt 20 %, funding frei/10 %, turnover frei/50 %, oi_aenderung 20 %, zufall frei/5 %) - Wirkung, Urteil und Trennschaerfe

- Quelle: b_abnahme, Teil 1

**2.217** — ✔✔ DIE BEITRAGSLAGE UNTER B - und die Kontrolle haelt: `schnitt` 20 % +0,1858 TRAEGT · `funding` frei +0,0249 TRAEGT · `turnover` frei +0,0639 TRAEGT · `turnover` 50 % ab 2022 +0,0608 TRAEGT · `funding` 10 % ab 2022 +0,0542 TRAEGT · `oi_aenderung` 20 % ab 2022 +0,0442 TRAEGT. ⚠️ `zufall` traegt WEDER auf `frei` NOCH auf 5 % - B ist nicht 'alles traegt'

- Quelle: b_abnahme, Teil 2

**2.217-trennschaerfe** — ✔ Und die Trennschaerfen liegen jetzt bei 0,010 bis 0,053 statt bei 0,08 bis 0,10 - in der Groessenordnung der gemessenen Aufloesung statt darueber

- Quelle: b_abnahme, Teil 2

**2.218** — ⚠️⚠️ WAS DAMIT NICHT GEMESSEN IST - Nutzerhinweis 09.09., woertlich: *'wir sind noch in der Pruefung und Kalibrierung einzelner Beitraege. Die LEISTUNG DER KETTE ist hier noch nicht beruecksichtigt.'* Alles bisher Gemessene betrifft EINZELNE Beitraege auf ihrer eigenen Basis - nicht, was die Kette als Ganzes daraus macht

- Quelle: Nutzervorgabe 09.09.2026

**2.218-was-fehlt** — ⚠️ Konkret ungemessen: das ZUSAMMENWIRKEN der Beitraege in `potential.rechne` · die Wirkung der Schwelle 0,080 auf die tatsaechlich erzeugten Signale · die Trichterstufen davor (Auswahl, Sperren) · und ob die Kette am Ende besser ist als ihre Teile. Die Kalibrierung 16,5 % Durchlass sagt, wie STRENG die Schwelle ist - nicht, was dabei herauskommt

- Quelle: Nutzervorgabe 09.09.2026 / agent/potential.py

**2.219** — ✔✔ DER GESAMTSTAND UNTER KRITERIUM B - 16 Kandidaten, alle zulaessigen selektierten Mengen, ein Lauf. ⚠️ DIE KONTROLLE HAELT: `zufall` traegt auf KEINER der drei Mengen. Fuenf tragen (funding, turnover, oi_aenderung, vola, schnitt), SIEBEN nicht (oi_je_umsatz, long_bias, top_bias, taker_bias, amihud, rsi, zufall), VIER widersprechen sich (schnitt50, momentum, momentum_kurz, funding_extrem). B laesst nicht alles durch

- Quelle: messe_alle_kandidaten.py

**2.219-schnitt** — ✔ `schnitt` ist der ROBUSTESTE: er traegt auf ALLEN DREI Mengen (10 %, 20 %, 50 %), drei von drei Aussagen. ⚠️ Registrierbar ist er trotzdem nicht - 2.158 gilt unveraendert, seine Stufen sind ein Buckel. Das ist eine Frage der FORM, nicht der Signifikanz

- Quelle: messe_alle_kandidaten.py / Befund 2.158

**2.219-vola** — ⚠️ `vola` TRAEGT NEU - aber nur mit EINER Aussage von drei Mengen, die anderen beiden sind Enthaltungen. Unter dem alten Bezug war er WIDERSPRUCH. Eine einzelne Aussage ist duenn und keine Registrierungsgrundlage; ausserdem gilt 2.143 weiter ('vola traegt KEINE Richtung')

- Quelle: messe_alle_kandidaten.py

**2.220** — ⚠️⚠️⚠️ NOCH VOR DER ERSTEN KETTENMESSUNG GEFUNDEN, durch Nachsehen statt Annehmen: die KETTENMENGE ist keine momentum-selektierte Menge. Von 43 Krypto-Werten passieren 25 die Auswahl, WEIL SIE BESTAND HABEN - nach nichts selektiert; nur 2 kommen von A1 (top-k nach Jahresentwicklung). Die Beitraege sind aber auf den Mengen 5/10/20/50 % belegt, alle nach Momentum verengt

- Quelle: agent/auswahl.py / Kettenplan 09.09.

**2.220-signale** — ⚠️ Und die Signalverteilung bestaetigt es: `NACHKAUFEN` mit 51,7 Mails am Tag hat per Definition Bestand - der groesste Einzelposten der Kette entsteht auf der Menge, auf der die Beitraege NIE gemessen wurden

- Quelle: Kettenplan 09.09. / F-172

**2.220-haltefrage** — ⚠️⚠️ UND EINE ZWEITE, DARAUS FOLGENDE: `agent/auswahl.py` schreibt selbst in die Mail 'bei einer gehaltenen Position lautet die Frage halten oder verkaufen'. Alle Beitraege sind fuer die Lage `instrument=spot, strategie=einstieg` gemessen. Ob sie fuer die HALTEFRAGE gelten, ist nie geprueft worden

- Quelle: agent/auswahl.py / agent/wahrscheinlichkeit.py

**2.220-plan** — ✔ K-1 wurde daraufhin in DREI Teile zerlegt: K-1a auf der A1-Menge (dafuer sind sie gebaut) · K-1b auf der BESTANDS-Menge (dort entstehen die meisten Signale, dort nie gemessen) · K-1c fuer die Haltefrage statt den Einstieg. ⚠️ Das ist bereits ein Befund vor der Messung: die Beitraege werden auf einer Menge angewandt, auf der sie nie geprueft wurden

- Quelle: Kettenplan 09.09.2026

**2.221** — ✔✔ K-1b GEMESSEN: tragen die Beitraege auf einer UNSELEKTIERTEN Menge? Verglichen wurde die Momentum-Auswahl gegen FUENF Zufallsauswahlen gleicher Groesse, alles andere unveraendert. ⚠️ Ein Zufallsausschnitt ist ein STELLVERTRETER - eine Bestands-Historie gibt es nicht (`holdings` 55 Zeilen ohne Zeitachse, `portfolio_wert_historie` leer)

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.221-turnover** — ✔✔ `turnover` IST DER ROBUSTESTE: +0,0608 auf der Momentummenge -> +0,0470 auf Zufallsmengen, 5 von 5 tragen, 3,2-fach ueber der Kontrolle. Sein Beleg haengt NICHT an der Auswahl

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.221-funding** — ✔ `funding` uebertraegt sich auch: +0,0542 -> +0,0320, 4 von 5, 2,2-fach ueber der Kontrolle. ⚠️ Aber die Wirkung faellt um ein Drittel - die Momentum-Auswahl konzentriert den Effekt, macht ihn aber nicht aus

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.222** — ⚠️⚠️⚠️ `schnitt`s WIRKUNG IST ZU VIER FUENFTELN EIN AUSWAHL-ARTEFAKT: +0,1858 auf der Momentummenge -> +0,0366 auf Zufallsmengen, ein Faktor 5. Er traegt zwar weiter (4 von 5, 2,5-fach ueber der Kontrolle), aber die Zahl, die ihn am Vormittag als '6,3-fach ueber der Aufloesung' und 'solidesten' auswies, gilt NUR auf der momentum-verengten Menge

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.222-passt** — ✔ Und es passt zu 2.158-redundanz: `schnitt` und die Auswahl korrelieren mit Spearman +0,704 im vollen Querschnitt. Auf der momentum-verengten Menge misst `schnitt` also teilweise die AUSWAHL mit - genau der Anteil, der auf einer Zufallsmenge wegfaellt

- Quelle: Befund 2.158-redundanz / K-1b

**2.222-rangfolge** — ⚠️⚠️ DIE RANGFOLGE DREHT SICH DAMIT UM. Auf der Menge, auf der die KETTE arbeitet, gilt: `turnover` +0,0470 (3,2x) > `schnitt` +0,0366 (2,5x) > `funding` +0,0320 (2,2x) > `oi_aenderung` +0,0267 (1,8x). Am Vormittag stand `schnitt` mit +0,186 weit vorn

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.223** — ✖ ZURUECKGEZOGEN (2.225) - falsche Basis. War: `oi_aenderung` BRICHT EIN: +0,0442 -> +0,0267, nur 2 von 5 tragen, und das ist nur das 1,8-fache der Kontrolle (die auf Zufallsmengen +0,0146 wirkt). Auf einer unselektierten Menge ist er vom Zufall kaum zu unterscheiden - und er laeuft LIVE als Sperre

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.224** — ⚠️⚠️ EIGENER FEHLER IN DER KONTROLLREGEL, korrigiert: der erste K-1b-Lauf erklaerte sich fuer wertlos, weil `zufall` in 1 von 6 Varianten trug. Die Regel war falsch - Kriterium B HAT eine Fehlalarmquote von 2,7 %, bei sechs Ziehungen sieht man mit 15 % Wahrscheinlichkeit mindestens einen. Eine Kontrolle, die nie feuern darf, verlangt implizit 0 % - also genau das am selben Tag verworfene `null_oben`

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.224-ersatz** — ✔ Die Regel prueft jetzt die WIRKUNG statt der Quote: mit fuenf Ziehungen laesst sich eine Quote ohnehin nicht schaetzen. Massstab ist die Kontrolle auf DERSELBEN Art Menge (+0,0146), und der Kandidat muss sie deutlich uebertreffen

- Quelle: k1b_beitrag_auf_bestandsmenge.py

**2.225** — ✖ ZURUECKGEZOGEN: '`oi_aenderung` bricht ein - vom Zufall kaum zu unterscheiden' (2.223). Die Aussage stand auf der Menge 20 % ab 2022. Seine REGISTRIERUNGSBASIS ist `frei` auf der vollen Historie, und dort traegt er: +0,0126 R [+0,0071 .. +0,0184], 131.869 Anker, 122 Symbole

- Quelle: Nachmessung 09.09.2026

**2.225-reproduziert** — ✔ Der registrierte Wert reproduziert im Rahmen der geaenderten Basis: +0,0145 R auf 126.491 Ankern und 117 Symbolen (02.09.) gegen +0,0126 R auf 131.869 Ankern und 122 Symbolen (heute). Die Messbasis wurde am 08.09. aufgefrischt und um zehn Reihen erweitert

- Quelle: Nachmessung 09.09.2026

**2.225-k1b-trifft-nicht** — ⚠️⚠️ UND DIE K-1b-FRAGE TRIFFT IHN OHNEHIN NICHT - sie ist fuer ihn schon beantwortet. K-1b fragt 'gilt der Beleg auf einer UNSELEKTIERTEN Menge?'. Seine Registrierungsbasis IST die unselektierte Menge (`frei`). Und live wirkt er nur bei EINSTIEG, NICHT bei Bestand - die Bestandsfrage stellt sich fuer ihn gar nicht

- Quelle: REGISTER_Kandidaten / agent/rollen_gate.py

**2.225-dritter-fehler** — ⚠️⚠️⚠️ DRITTER R-R11-FEHLER DERSELBEN KLASSE AN EINEM TAG: `turnover` auf der vollen Historie statt 50 % ab 2022 · `funding` beinahe ebenso (rechtzeitig gefangen) · `oi_aenderung` auf 20 % ab 2022 statt `frei`. Die Ursache ist immer dieselbe: ich messe mehrere Kandidaten in EINEM Lauf auf EINER Menge, statt jeden auf SEINER Basis. ⚠️ Das Kandidatenregister nennt die Basis je Kandidat - es gehoert VOR jeden Lauf geoeffnet, nicht danach

- Quelle: Selbstbefund 09.09.2026

**2.226** — ⚠️ WAS ZU `oi_aenderung` OFFEN BLEIBT: die Wirkung ist mit +0,0126 R die KLEINSTE der vier und nah an der Aufloesung · bei 50 % ab 2022 traegt er NICHT (Band [-0,0005 .. +0,0283]) · der Geltungsbereich ist H20, der Betriebshorizont aber 3-5 Tage, und bei H5 traegt er nicht (+0,00663, 06.09.) · und er wirkt nur auf 10,6 von 174,3 Signalen am Tag. Korrekt belegt, aber wenig wirksam

- Quelle: Nachmessung 09.09. / REGISTER_Kandidaten / F-172

**2.227** — ⚠️⚠️⚠️ DIE URSACHE DER DREI R-R11-FEHLER IST STRUKTURELL: das Feld `Kandidat.basis` ist FREITEXT ('H20 · 2.369 Kalendertage · 290 Symbole') und nennt die MENGE nicht. Die Basis war dokumentiert, aber fuer den Code nicht benutzbar - deshalb wiederholte sich der Fehler

- Quelle: bestand.Kandidat / Selbstbefund 09.09.

**2.227-aufloesung** — ✔✔ UND DABEI KAM DIE AUFLOESUNG HERAUS: ALLE DREI live registrierten Beitraege stehen auf `frei` - dem vollen Tagesquerschnitt. 2.161-rr11 sagt es woertlich fuer `turnover` ('Der registrierte Befund stammt von der FREIEN Menge'), `oi_aenderung`s Ankerzahl bestaetigt es (126.491 ~ frei), und `funding`s Originalbefund vom 30.08. war der Querschnitt je Kalendertag

- Quelle: bestand.py / Nachmessung 09.09.

**2.227-nicht-2162** — ⚠️⚠️ DIE MENGEN AUS BEFUND 2.162 (turnover 50 %, funding 10 %, oi_aenderung 20 %) SIND NICHT DIE REGISTRIERUNGSBASIS - sie stammen aus einer eigenen Messung zur Zeitstabilitaet. Genau diese Verwechslung hat heute N-87 auf die falsche Basis gefuehrt

- Quelle: Befund 2.162 / 2.161-rr11

**2.227-auf-frei** — ✔✔ AUF IHREN ECHTEN REGISTRIERUNGSBASEN TRAGEN UNTER KRITERIUM B ALLE DREI: `funding` frei +0,0249 · `turnover` frei +0,0639 · `oi_aenderung` frei +0,0126. Das ist ein saubereres Bild als das, was N-87 auf den 2.162-Mengen zeigte

- Quelle: Nachmessung 09.09.2026

**2.227-gebaut** — ✔ ABGESTELLT STATT VORGENOMMEN: `Kandidat` hat jetzt `menge` und `fenster` maschinenlesbar, `bestand.messbasis(name)` gibt sie heraus, und zwei Waechter im Paket `Messstandard` erzwingen sie fuer jeden TRAGENDEN Kandidaten - beide durch Mutation belegt

- Quelle: bestand.messbasis / pruefe_pakete --paket Messstandard

**2.228** — ⚠️⚠️ EIN WIDERSPRUCH BLEIBT OFFEN und gehoert in die Kettenpruefung: die drei Beitraege sind auf `frei` registriert - das ist nach P6/F-212 die MARKT-Frage. F-212 verlangt aber, einen BEITRAG auf der SELEKTIERTEN Menge zu beurteilen. 2.161-rr11 hat das schon benannt. Solange das nicht entschieden ist, steht jeder Beitrag auf einer Basis, die eine andere Frage beantwortet als die, fuer die er benutzt wird

- Quelle: Befund 2.161-rr11 / F-212 / Kettenplan

**2.229** — ✔✔✔ K-1w GEMESSEN - die Beitraege auf der WATCHLIST, auf der die Kette wirklich arbeitet (43 Krypto-Werte, davon 39 in der Messbasis). ⚠️ Rang ueber die MESSBASIS, gemessen auf der Watchlist - ueber die Watchlist gerangt dreht das Vorzeichen (REGISTER_Kandidaten). Dafuer bekam `sammle` den Parameter `nur`, der NACH dem Rang verengt

- Quelle: k1w_beitrag_auf_der_watchlist.py

**2.229-funding** — ✔✔ `funding` TRAEGT AUF DER WATCHLIST - und zwar STAERKER: +0,0886 gegen +0,0249 auf der Messbasis, Band [+0,0582 .. +0,1458], 34 Bloecke, Trennschaerfe 0,0775. Genug Macht, echtes Urteil

- Quelle: k1w_beitrag_auf_der_watchlist.py

**2.229-turnover** — ⚠️⚠️ `turnover` IST AUF DER WATCHLIST NICHT MESSBAR - nur 5 Bloecke gegen 20 geforderte, Urteil 'KEIN BEFUND'. ⚠️ Das ist laut Norm eine Aussage ueber die MESSUNG, nicht ueber die Welt. Er deckt 66 Symbole ab, und davon liegen zu wenige in der 43er-Watchlist

- Quelle: k1w_beitrag_auf_der_watchlist.py

**2.229-oi** — ⚠️ `oi_aenderung` IST AUF DER WATCHLIST UNENTSCHIEDEN: Wirkung +0,0146 gegen eine Trennschaerfe von 0,0473 - die Anlage kann dort Effekte dieser Groesse nicht aufloesen. 21 Bloecke, also gerade ueber der Grenze. Kein Nullbefund

- Quelle: k1w_beitrag_auf_der_watchlist.py

**2.229-kontrolle** — ✔ Die Kontrolle haelt: `zufall` traegt auf der Watchlist NICHT (+0,0179, 43 Bloecke, Trennschaerfe 0,0606)

- Quelle: k1w_beitrag_auf_der_watchlist.py

**2.230** — ⚠️⚠️⚠️ DER EIGENTLICHE BEFUND: DIE WATCHLIST IST ZU KLEIN, UM ZWEI DER DREI BEITRAEGE DORT ZU PRUEFEN. `turnover` erreicht 5 von 20 noetigen Bloecken, `oi_aenderung` loest seine eigene Wirkung nicht auf. Nur `funding` hat genug Abdeckung. Das ist keine Aussage GEGEN die beiden - es heisst, dass ihre Wirkung auf der Kettenmenge UNBELEGT ist

- Quelle: k1w_beitrag_auf_der_watchlist.py

**2.230-folge** — ⚠️ WAS DARAUS FOLGT: der Widerspruch aus 2.228 (frei gegen selektiert) laesst sich auf der Watchlist NICHT entscheiden - dafuer fehlen die Daten. Fuer `funding` ist er entschieden (traegt dort, staerker); fuer die anderen beiden bleibt er offen, und zwar aus Datenmangel, nicht aus Uneinigkeit

- Quelle: Befund 2.228 / K-1w

**2.230-anzeigefehler** — ⚠️ Eigener Anzeigefehler dabei gefunden: eine abgeleitete Spalte 'Anker/Tag' zeigte 47,8 bei nur 43 Watchlist-Symbolen - unmoeglich. `n_anker` zaehlt ueber ALLE Tage der Sammlung, `n_tage` nur die, die die Tagesklammer ueberstehen. Die beiden Zahlen sind nicht teilbar; massgeblich sind die BLOECKE

- Quelle: Selbstbefund 09.09.2026

**2.231** — ⚠️⚠️ NUTZEREINWAND 09.09., BERECHTIGT: 'wenn die Watchlist ein Asset ist, sollte es egal sein'. Er hat recht - ich hatte ZWEI Fragen vermischt. 'Traegt die REGEL?' ist eine Aussage ueber die Welt, dafuer ist die MESSBASIS die richtige und staerkere Basis. 'Wirkt sie auf UNSEREN Werten?' ist die Watchlist-Frage. K-1w hat die zweite gemessen und ich habe sie als Antwort auf die erste gelesen

- Quelle: Nutzereinwand 09.09.2026

**2.231-folge** — ⚠️ DAMIT IST K-1w NEU ZU LESEN: auf 43 statt 536 Symbolen werden 92 % der Daten weggeworfen - `turnover`s 5 Bloecke sind ein Befund ueber die MESSANLAGE, nicht ueber `turnover`. Der Messbasis-Befund steht. Uebrig bleibt nur die kleinere Frage, ob die Watchlist systematisch anders ist

- Quelle: Nutzereinwand 09.09.2026 / K-1w

**2.232** — ✔✔✔ DIE MESSMENGE IST EINGEFROREN (Nutzerentscheidung 09.09.): `messmenge.V1`, 536 Symbole, davon 174 EINGESTELLTE Reihen - der Survivorship-Schutz. Keine Auswahl nach Groesse, Liquiditaet oder Leistung. `lade()` liefert genau sie und MELDET, wenn eine Reihe fehlt, statt stillschweigend weniger zu messen

- Quelle: messmenge.py / messe_eigenschaft_beitrag.lade

**2.232-warum** — ⚠️⚠️ DER GRUND IST NICHT ABDECKUNG, SONDERN REPRODUZIERBARKEIT: bis heute war die Messmenge das, was gerade in der Datenbank stand. `oi_aenderung` war auf 117 Symbolen registriert, heute waren es 122 - und der Wert wanderte von +0,0145 auf +0,0126. R-R11 ist nicht durchsetzbar, wenn sich die Basis unter dem Befund wegschiebt

- Quelle: messmenge.py

**2.232-abnahme** — ✔ Abgenommen: die eingefrorene Menge liefert 536 = 536 identisch, und `funding` frei +0,0249 sowie `turnover` frei +0,0639 reproduzieren ziffergenau. Vier Waechter im Paket `Messstandard` halten es fest

- Quelle: pruefe_pakete --paket Messstandard

**2.233** — ✔ DIE TURNOVER-ABDECKUNG IST EINE GRENZE DER QUELLE, NICHT DES ZUSCHNITTS: der Coin-Metrics-Community-Katalog fuehrt fuer `SplyCur` (1d) insgesamt 139 Assets. Davon liegen 66 in unserer Messmenge von 536 - also 12 %. Selbst bei vollstaendiger Abdeckung des Katalogs waeren es 26 %

- Quelle: Katalogabfrage 09.09.2026

**2.233-nicht-brauchbar** — ⚠️⚠️ UND DIE 18 SCHEINBAR GEWINNBAREN SIND NICHT BRAUCHBAR: sie heissen `BNB_ETH`, `USDC_ETH`, `SHIB_ETH`, `MATIC_ETH`, `TRX_ETH` - das sind die Mengen AUF ETHEREUM, nicht die Umlaufmengen. `turnover` ist Umsatz durch Umlaufmenge; wer die Wrapped-Menge einsetzt, misst einen Bruchteil des Tokens auf einer Kette, und die Kennzahl waere STILL falsch

- Quelle: Katalogabfrage 09.09.2026

**2.233-offen** — ⚠️ OFFEN BLEIBT DER WEG UEBER EINE ANDERE QUELLE: CoinGecko fuehrt Umlaufmengen fuer weit mehr Coins. Er ist der einzige, der etwas aendern wuerde - braucht aber eine eigene Pruefung, weil zwei Quellen fuer dieselbe Groesse still auseinanderlaufen koennen (stehende Vorgabe: die Datenquelle mitpruefen)

- Quelle: Nutzerentscheidung offen

**2.234** — ⚠️⚠️⚠️ DIE LAGE WAR BIS ZUM 09.09. NUR EIN ETIKETT: `pruefe_auswahl` hatte `zielgroesse='bewegung_r'` FEST VERDRAHTET und reichte die `lage` nur an den Befund durch. Eine Messung mit `lage=Lage('hebel',...)` haette Spot-Bewegung gemessen und 'Hebel' daraufgeschrieben

- Quelle: messnorm_auswahl.py / Selbstbefund 09.09.

**2.234-zielgroessen** — ⚠️⚠️ UND `ZIELGROESSEN` KANNTE DIE VERBILLIGUNG NICHT, obwohl die Akkumulation seit dem 28.08. mit ihr gemessen wird. Ein Zielgroessenregister, das die laufende Zielgroesse einer Lage nicht kennt, kann nicht verhindern, dass eine Lage mit dem Massstab einer anderen gemessen wird

- Quelle: messnorm.ZIELGROESSEN

**2.234-behoben** — ✔ BEHOBEN: `verbilligung` ist nachgetragen, `ZIELGROESSE_JE_LAGE` ordnet jeder Lage ihr Mass zu (spot/einstieg -> bewegung_r · spot/akkumulation -> verbilligung · hebel/* -> barriere), und `pruefe_auswahl` WEIST AB, wenn beides nicht zusammenpasst

- Quelle: messnorm.py / messnorm_auswahl.py

**2.235** — ⚠️⚠️⚠️ K-1c: DIE AKKUMULATIONSLAGE IST MIT DER BLOCKREGEL NICHT MESSBAR. Alle fuenf Kandidaten - einschliesslich der Kontrolle `zufall` - liefern KEIN BEFUND: 6 bis 10 Bloecke gegen 20 geforderte. Die Ursache ist strukturell: bei H90 betraegt die Blocklaenge 3 x 90 = 270 Tage, fuer 20 Bloecke braeuchte es 5.400 Handelstage - rund 22 Jahre. Der Kryptomarkt hat 2.900

- Quelle: k1c_lagen_eigene_zielgroesse.py

**2.235-nicht-dagegen** — ⚠️ DAS IST KEINE AUSSAGE GEGEN DIE BEITRAEGE. 'Kein Befund' ist laut Norm eine Aussage ueber die MESSUNG. Weder fuer noch gegen - die Anlage kann auf diesem Horizont nicht urteilen

- Quelle: k1c_lagen_eigene_zielgroesse.py

**2.235-eigener-fehler** — ⚠️⚠️ EIGENER FEHLER, sofort korrigiert: die erste Fassung des Skripts las `b.traegt` statt das URTEIL und meldete drei Traeger, waehrend ALLE FUENF 'KEIN BEFUND' lauteten. `traegt` prueft nur 'Band ueber dem Bezugspunkt' und weiss NICHTS von der Blockzahl. Dieselbe Verwechslung wie Fehler 4 vom 08.09. - diesmal an der Norm VORBEI, weil das Skript die Eigenschaft direkt gelesen hat

- Quelle: k1c_lagen_eigene_zielgroesse.py

**2.236** — ⚠️⚠️ WAS DARAUS FOLGT - und es beruehrt die Nutzerwarnung vom 08.09. ('keine unerreichbaren Regeln aufstellen'): 20 Bloecke bei H90 SIND unerreichbar, solange der Kryptomarkt jung ist. Entweder der Horizont oder die Blockregel muss sich aendern - das ist eine ENTWURFSfrage, keine Messfrage. ⚠️ Und `NACHKAUFEN` mit 51,7 Mails am Tag laeuft auf genau dieser Lage

- Quelle: k1c_lagen_eigene_zielgroesse.py / Nutzervorgabe 08.09.

**2.236-hebel** — ⚠️ HEBEL IST NOCH NICHT GEMESSEN, und der Grund gehoert benannt: die vorhandene Barrierenfunktion (`messe_sentiment_je_horizont.barriere`) rechnet mit STOP_ATR = 2,5, die Produktion aber mit max(5 % Kurs, 0,75 x ATR). Sie misst ein ANDERES System. Fuer `hebel x einstieg` braeuchte es die Barriere auf der Produktionsgeometrie - ein eigener Baustein

- Quelle: messe_sentiment_je_horizont.py / Kettenplan

**2.236-neutral** — ✔ NUTZERWARNUNG 09.09. EINGEHALTEN ('fuer Strategie und Bewertung neutral ohne Wirtschaftlichkeit'): die Verbilligung ist reine Kursbewegung - keine Gebuehr, kein Breakeven. Fuer den Hebelpfad gilt dasselbe: `barriere` ist Ziel vor Stop, ebenfalls ohne Kosten. Regel 2

- Quelle: Nutzervorgabe 09.09.2026

**2.237** — ⚠️⚠️ K-1c HEBEL: DER LAUF IST UNGUELTIG - die Kontrolle `zufall` TRAEGT (+0,0007, Band [+0,0002 .. +0,0013], 48 Bloecke). Drei Kandidaten sahen wie Traeger aus (turnover, oi_aenderung, schnitt); keiner davon gilt

- Quelle: k1c_hebel_barriere.py

**2.237-median** — ✔ DER MEDIAN IST BEI BINAEREN DATEN ENTARTET - belegt: bei 0/1-Ausgaengen und zufaelliger Sperrgruppe hat `median(frei) - median(alle)` die Streuung 0,00000 und nur den Wert 0,0. Deshalb konnte `barriere` mit der bisherigen Anlage gar nicht gemessen werden - das war ein echtes Hindernis, kein erfundenes

- Quelle: Kunstprobe 09.09.2026

**2.237-mittel-ok** — ✔ UND DIE MITTEL-STATISTIK IST UNVERZERRT: ueber 4.000 Ziehungen betraegt `mean(frei) - mean(alle)` im Mittel +0,00004 bis +0,00042 bei einer Streuung von 0,0136. Der Fehler liegt also NICHT in der Statistik

- Quelle: Kunstprobe 09.09.2026

**2.238** — ⚠️⚠️⚠️ DER FEHLER LIEGT IM BAND: bei rund 250 Ankern je Tag und 48 Bloecken muesste das Band etwa ±0,0023 breit sein - beobachtet sind ±0,0006, also VIERMAL ZU ENG. Ein zu enges Band laesst jede Winzigkeit 'tragen', und genau das tut `zufall` hier

- Quelle: k1c_hebel_barriere.py / Ueberschlagsrechnung 09.09.

**2.238-klasse** — ⚠️ DAS IST DIESELBE KLASSE WIE FEHLER 6: die EICHUNG DES BANDES auf einem neuen Datentyp war nie geprueft. Der Pruefstand kann es beantworten - Fehlalarmquote der Barrieren-Anlage auf Nullwelten, genau wie am 09.09. fuer den Nullbezug

- Quelle: Selbstbefund 09.09.2026

**2.238-gebaut** — ✔ WAS TROTZDEM STEHT: die Zielgroesse `barriere` ist jetzt BAUBAR - `ZIELGROESSEN` traegt die Statistik je Zielgroesse, `je_tag_wirkung` hat die Mittel-Variante (Vorgabe bleibt Median, Neutralitaetsprobe bestanden), und die Barriere laeuft auf der PRODUKTIONSGEOMETRIE min(25 %, max(5 %, 0,75 x ATR)) mit CRV 2,0 - nicht auf der 2,5er-Variante aus `messe_sentiment_je_horizont`

- Quelle: messnorm.py / pruefe_n31_tagesklammer.py / k1c_hebel_barriere.py

**2.238-auswahl** — ⚠️ Und eine Auswahl gehoert benannt: im Fenster von 20 Tagen loesen sich 94,7 % der Anker, die uebrigen fallen heraus. Das ist verwandt mit den 79 % 'Einstieg nie erreicht' aus K-6 - dort aber viel groesser, weil die Kette eine EINSTIEGSZONE hat, die erst erreicht werden muss

- Quelle: k1c_hebel_barriere.py

**2.239** — ⚠️ EIGENE UEBERVORSICHT, vom Nutzer korrigiert: ich hatte gefragt statt gebaut ('wir bauen doch gerade alles um - verstehe den Grund nicht'). Er hatte recht: eine Barrierenfunktion auf Produktionsgeometrie ist genau die laufende Arbeit, keine Grundsatzentscheidung. ⚠️ Das ECHTE Hindernis lag woanders und war vorher nicht sichtbar - der entartete Median

- Quelle: Nutzereinwand 09.09.2026

**2.240** — ✔✔✔ N-88: `schnitt`s ZEITSTABILITAET IST ENTSCHIEDEN - und zwar GEGEN ihn. Ueber alle fuenf Mengen gemessen dreht sein Haelftenunterschied das Vorzeichen (-0,431 / -0,081 / +0,197 / +0,002 / +0,018) und ist auf ZWEI Mengen TRENNBAR - auf 5 % mit -0,43, auf 20 % mit +0,20. Widerspruechliche signifikante Antworten je nach Menge

- Quelle: n88_schnitt_zeitstabil_neu.py

**2.240-kontrollen** — ✔ UND DIE KONTROLLEN TRENNEN DAS AB: `funding` zeigt ueber alle fuenf Mengen DASSELBE Vorzeichen (+0,060 bis +0,003) und auf KEINER einen trennbaren Unterschied - er ist zeitstabil. `zufall` dreht zwar auch, wird aber NIE trennbar. Nur `schnitt` liefert gegenlaeufige SIGNIFIKANTE Unterschiede

- Quelle: n88_schnitt_zeitstabil_neu.py

**2.240-abbruch** — ⚠️ TEILWEISE ABGELOEST DURCH 2.243 (die Instabilitaet war Kollinearitaet). War: DIE ABBRUCHBEDINGUNG AUS DEM KANDIDATENREGISTER IST DAMIT BESTAETIGT, nicht aufgeloest. 'Unentschieden' (07.09.) war zu freundlich: der Test gibt je nach Menge widerspruechliche SIGNIFIKANTE Antworten, und das ist eine Eigenschaft von `schnitt`, nicht des Verfahrens. Die Sperre ist NICHT baubar

- Quelle: n88_schnitt_zeitstabil_neu.py / REGISTER_Kandidaten

**2.240-standard** — ⚠️ Der neue Messstandard hat daran NICHTS geaendert - richtig so: die Zeitstabilitaet haengt nicht am Nullbezug (dort wird ein UNTERSCHIED gegen null geprueft, keine Wirkung gegen eine gemischte Welt), sondern an der Menge. Die Vorhersage stand vor dem Lauf und ist eingetroffen

- Quelle: n88_schnitt_zeitstabil_neu.py

**2.241** — ✔ REVIEW DER ERLEDIGTEN HEBEL-BEFUNDE (Nutzerauftrag 09.09., keine Doppelmessung sondern Suche nach Showstoppern): KEIN Showstopper beim Kalibrierungsfaktor. `hebel_scheitert_an_der_bewertung` rechnet mit 19,5 % - das ist der ERSATZ F-219, gemessen mit der Invarianz als vorab gesetztem Annahmekriterium (ROH und ANTEIL fielen durch, RANG war exakt invariant). Gefallen war die ALTE Zahl 16,8 %

- Quelle: Review 09.09.2026 / F-219

**2.241-horizont** — ⚠️⚠️ DER EINE ECHTE SHOWSTOPPER IST BEKANNT UND GEMESSEN, nicht uebersehen: die Beitraege sind auf H20 belegt (funding +0,0246, turnover +0,0616), bei H1/H2 aber 6-7x kleiner (+0,0019 / +0,0026). N-17a hat die H2-Kalibrierung vollstaendig durchgemessen (F-203): die beste Schwelle ist praktisch 0,000, r ~ 0,02. ✔ BEWUSST NICHT live registriert - 'eine Schwelle ohne Trennschaerfe waere eine Mengenbremse ohne Qualitaetsaussage'

- Quelle: Review 09.09. / F-185 / F-203 / F-210

**2.241-nur-hebel** — ✔✔ UND ER TRIFFT NUR DEN HEBEL, NICHT SPOT: die 2,0 Tage mediane Dauer (F-202) stammen aus Trades MIT Barrieren. Spot hat nach Nutzerentscheidung vom 03.09. KEINEN Stop - der Ausstieg ist rein bewertungsbasiert, nichts zwingt zum frueher Ausstieg. Fuer `spot x einstieg` ist H20 damit stimmig. Genau deshalb heisst der Befund 'der HEBEL scheitert an der Bewertung' und nicht 'die Bewertung scheitert'

- Quelle: Review 09.09.2026 / F-202 / N-16e

**2.242** — ✔✔✔ N-89 TEIL B: `schnitt`s ZEITINSTABILITAET IST KOLLINEARITAET MIT DER AUSWAHL, nicht seine Eigenschaft. Auf 5 % faellt der Haelftenunterschied von -0,4310 (Momentum, trennbar) auf -0,013 bis +0,005 (fuenf Zufallsauswahlen, KEINE trennbar). Auf 20 % von +0,1973 auf +0,021 bis +0,045, davon 1 von 5 trennbar - bei einem Test mit 18 % Fehlalarmquote das Erwartete

- Quelle: n89_familie_und_schnitt_loesung.py

**2.242-warum** — ✔ DIE ERKLAERUNG PASST ZUM MECHANISMUS: `schnitt` und das Auswahl-Momentum korrelieren mit Spearman +0,704. Auf der Momentumspitze liegen fast alle Werte ueber ihrem eigenen Schnitt - es bleibt kaum Streuung uebrig, und die Messung wird instabil. Je schmaler die Menge, desto staerker: -0,431 bei 5 %, +0,197 bei 20 %, +0,002 bei 50 %

- Quelle: n89 / Befund 2.158-redundanz

**2.242-k1b** — ✔✔ UND ES ERKLAERT K-1b VON DER ANDEREN SEITE: dort brach `schnitt`s Wirkung auf Zufallsmengen von +0,186 auf +0,037 ein (2.222). Beides ist derselbe Mechanismus - auf der Momentummenge misst `schnitt` teilweise die AUSWAHL mit

- Quelle: n89 / Befund 2.222

**2.243** — ⚠️⚠️ DAMIT IST DIE ABBRUCHBEDINGUNG ANDERS ZU LESEN ALS IN 2.240: `schnitt` ist NICHT gefallen - er wurde auf der FALSCHEN Menge geprueft. Auf einer nicht momentum-selektierten Menge ist er zeitstabil. ⚠️ Und die KETTE arbeitet auf genau so einer Menge (ueberwiegend Bestand, nach nichts selektiert - Befund 2.220)

- Quelle: n89_familie_und_schnitt_loesung.py

**2.243-offen** — ⚠️ WAS DAMIT NICHT GELOEST IST: die FORM. Der Buckel (+4,07/+5,55/+9,49/+1,71/-4,65) ist dreimal aufgetreten. ⚠️⚠️ ABER: N-64/N-65 haben die Stufen auf der SELEKTIERTEN Menge gerechnet - wenn `schnitt` dort mit dem Momentum kollinear ist, koennte der Buckel DASSELBE Artefakt sein. Das ist pruefbar und die naechste Frage

- Quelle: Befund 2.158 / n89 / offene Frage

**2.244** — ⚠️ N-89 TEIL A: KEINE VERTRETERIN DER FAMILIE BESTEHT BEIDE HUERDEN. `vola` traegt, ist aber auf 20 % zeitinstabil - GENAU WIE `schnitt`, und beide korrelieren mit 0,703, also vermutlich dieselbe Kollinearitaet. `schnitt50` ist zeitstabil, liefert aber einen WIDERSPRUCH im Gesamtlauf. `rsi` ist auf DREI Mengen zeitinstabil und traegt nicht

- Quelle: n89_familie_und_schnitt_loesung.py

**2.244-amihud** — ⚠️⚠️ `amihud` IST DER EINZIGE MIT SAUBEREM STABILITAETSBILD: nirgends trennbar UND konsistentes Vorzeichen (+0,004 bis +0,029) - besser als die Kontrolle, deren Vorzeichen dreht. ⚠️ Er traegt aber nicht (Gesamtlauf 09.09.: TRAEGT NICHT auf allen drei Mengen). Zeitstabil und wirkungslos ist kein Kandidat - aber es ist ein Grund, ihn nicht abzuschreiben (Befund 2.166-woanders: er misst AUSFUEHRBARKEIT)

- Quelle: n89_familie_und_schnitt_loesung.py

**2.245** — ⚠️⚠️ N-90 IST UNGUELTIG - die KONTROLLE ist wilder als der Kandidat. `zufall` erzeugt auf Zufallsmengen Stufen von -33,89 bis +90,85 Punkten, waehrend die ganze Beitragsskala bei +-5 liegt. Bei rund 9 Ankern je Tag und Fuenftel ist `median(Fuenftel) - median(alle)` zu verrauscht, und die Entzerrung verstaerkt es. Die FORMFRAGE bleibt unbeantwortet

- Quelle: n90_buckel_oder_artefakt.py

**2.245-besetzung** — ✔✔ EINE SACHE IST ABER SAUBER UND BELEGT DIE KOLLINEARITAET ZUM DRITTEN MAL: die BESETZUNG der Fuenftel geht von 1,5 / 2,2 / 3,7 / 8,5 / 29,7 (Momentum) auf 8,7 / 9,0 / 9,3 / 9,4 / 9,2 (zufaellig) - ein zwanzigfaches Ungleichgewicht wird zu perfekter Gleichverteilung. Auf der Momentumspitze liegen fast alle Werte ueber ihrem eigenen Schnitt

- Quelle: n90_buckel_oder_artefakt.py

**2.245-momentum** — ✔ Und der Momentum-Bezugsfall reproduziert N-65 sauber: +3,01 / +5,32 / +9,35 / +2,64 / -4,57 gegen +4,07 / +5,55 / +9,49 / +1,71 / -4,65 - Buckel bei Fuenftel 2, Besetzung 1,5 gegen 29,7. Die kleinen Unterschiede stammen aus der geaenderten Messbasis

- Quelle: n90_buckel_oder_artefakt.py

**2.246** — ✔✔ ALLE OFFENEN PUNKTE VON GESTERN UND HEUTE SIND IM GESAMTPLAN GESAMMELT (Nutzerauftrag 09.09.): A1 bis A7 Messanlage · B1 bis B8 Beitraege · C1 bis C10 Kettenpruefung · D1 bis D6 Datenlage und Betrieb · E1 bis E3 die grosse Planung. Erledigte werden dort durchgestrichen, nicht geloescht - sonst geht verloren, warum etwas einmal offen war

- Quelle: Basisinfos/Gesamtplan_Wo_wir_stehen_28_08.md

**2.247** — ⚠️⚠️ GEGENPROBE ERGAB FUENF EINTRAEGE, DIE ALS OFFEN GEFUEHRT WURDEN OBWOHL ERLEDIGT (Nutzerauftrag 09.09.): `bewertung_hat_keine_instrument_achse` und `die_begruendung_waehlt_nicht_das_instrument` sind seit dem 04.09. als KATEGORIENVERWECHSLUNG aufgeloest · `hebel_hat_eine_bewertung_nie_validiert` ist in der Rahmung erledigt · KEINER von ihnen verwies auf die Aufloesung, und der Index fuehrte alle mit Warnzeichen

- Quelle: Memory-Durchsicht 09.09.2026

**2.247-zwei-andere** — ⚠️ Zwei weitere waren NICHT erledigt, sondern nur ANDERS zu lesen: `hebel_faktisch_kein_hebel` (der Median 1,10 ist die FOLGE der kalibrierten Quote, kein Defekt) und `s1_blockiert_akkumulation` (die Spalte `strategie` existiert inzwischen, wird aber nie gesetzt - alle 118 Signale NULL). Beide nachgezogen statt geschlossen

- Quelle: Memory-Durchsicht 09.09.2026

**2.247-lehre** — ⚠️⚠️ DIE LEHRE: ein aufgeloester Befund loescht die alten Eintraege NICHT automatisch. Wer nur den neuen schreibt, laesst funf alte als offen stehen - und der naechste Blick in den Index zeigt Arbeit, die es nicht mehr gibt. **Beim Aufloesen gehoert der Rueckverweis in die alten Eintraege**

- Quelle: Selbstbefund 09.09.2026

**2.248** — ✔✔ N-91: DAS VERFAHREN IST GEGEN BEKANNTE WAHRHEIT GEEICHT, BEVOR es lief. Auf Kunstdaten (400 Tage x 60 Anker) erkennt es alle drei Formen: monoton (-0,392, beide Haelften -0,21/-0,20) · Buckel (-0,004 GESAMT, aber +0,246/-0,255 in den Haelften) · nichts (-0,015/-0,014/-0,010). ⚠️ Und es zeigt die Falle: ein Buckel liefert eine GESAMT-Rangkorrelation von -0,004 - von 'nichts' NICHT zu unterscheiden. Nur die Haelften trennen sie

- Quelle: n91_rangkorrelation_form.py

**2.249** — ✔✔✔ `schnitt` HAT KEINEN BUCKEL. Ueber die Rangkorrelation je Kalendertag zeigen BEIDE Haelften dasselbe negative Vorzeichen - auf der Momentummenge (-0,0311 / -0,0441) wie auf Zufallsmengen (-0,0155 / -0,0406 und weitere). Der Buckel aus den Fuenfteln war ein ARTEFAKT DER GRUPPENMEDIANE bei ungleicher Besetzung (1,5 gegen 29,7 Anker je Tag)

- Quelle: n91_rangkorrelation_form.py

**2.249-richtung** — ✔ UND DIE RICHTUNG STIMMT MIT DER HYPOTHESE: negativ heisst hoeherer Rang -> schlechteres Ergebnis, also 'tief unter dem eigenen Schnitt ist besser'. Das ist genau die Akkumulationsthese

- Quelle: n91_rangkorrelation_form.py

**2.249-zufall-staerker** — ✔✔ UND AUF ZUFALLSMENGEN IST ER STAERKER: die Gesamtkorrelation ist dort in 4 von 5 Faellen trennbar negativ (-0,043 bis -0,054, Baender ohne null), auf der Momentummenge dagegen nicht (-0,0278). Auch das passt zur Kollinearitaet - auf der Momentumspitze bleibt zu wenig Streuung

- Quelle: n91_rangkorrelation_form.py

**2.250** — ⚠️⚠️ UEBERRASCHUNG: DEN BUCKEL HAT `funding`, nicht `schnitt`. Auf der Momentummenge zeigen seine Haelften GEGENLAEUFIGE und BEIDE TRENNBARE Werte (+0,0541 [+0,022..+0,088] und -0,0268 [-0,049..-0,004]). Auf Zufallsmengen verschwindet er - derselbe Kollinearitaetseffekt, nur bei einem Beitrag, der LIVE laeuft

- Quelle: n91_rangkorrelation_form.py

**2.250-folge** — ⚠️ WAS DARAUS FOLGT: `funding`s Fuenftel-Stufen (+0,82/+1,30/+0,12/-0,54/-1,70) sind NICHT monoton - Fuenftel 1 liegt ueber Fuenftel 0. Das stand immer da und galt als hinnehmbar. Die Rangkorrelation zeigt jetzt, dass es auf der Momentummenge ein TRENNBARER Buckel ist. ⚠️ Ob das die Live-Stufen entwertet, ist eine eigene Frage - sie sind auf `frei` kalibriert, nicht auf 20 %

- Quelle: n91 / agent/wahrscheinlichkeit.BEITRAEGE

**2.250-kontrolle** — ✔ Die Kontrolle sitzt: `zufall` bleibt ueber alle sechs Auswahlen bei +-0,005 bis +-0,011, gegen `schnitt`s -0,03 bis -0,05. Zwei von sechs zeigen 'nur die obere trennbar' mit +0,0074 und -0,0113 - bei sechs Ziehungen und einem 95-%-Band das Erwartete

- Quelle: n91_rangkorrelation_form.py

**2.251** — ✔✔ B9 BEANTWORTET: `funding`s BUCKEL BETRIFFT DIE LIVE-STUFEN NICHT. Er ist auf der 20-%-Menge trennbar (+0,0541 / -0,0268, beide Baender ohne null), auf `frei` aber NICHT - dort hat die untere Haelfte die Null gerade noch im Band (+0,0211 [-0,000 .. +0,042]). ⚠️ Und die Live-Stufen stehen auf `frei`, an der Quelle geprueft: `rechne_funding_beitrag.py` bildet KEINE Auswahl

- Quelle: n92_b9_funding_buckel_auf_frei.py

**2.251-reproduziert** — ✔✔ UND DIE LIVE-STUFEN REPRODUZIEREN EXAKT: +0,77 / +1,40 / +0,22 / -0,64 / -1,75 gegen registriert +0,82 / +1,30 / +0,12 / -0,54 / -1,70. Abweichungen hoechstens 0,10, durch die gewachsene Messbasis erklaert

- Quelle: n92_b9_funding_buckel_auf_frei.py

**2.251-besetzung** — ✔✔ UND DIE URSACHE AUS N-90 LIEGT HIER NICHT VOR: die Fuenftel sind auf `frei` ausgeglichen besetzt (30 / 29 / 30 / 29 / 30). In N-90 standen 1,5 gegen 29,7 Anker - genau das machte die Gruppenmediane dort unbrauchbar. Auf `frei` tragen sie

- Quelle: n92_b9_funding_buckel_auf_frei.py

**2.252** — ⚠️ WAS TROTZDEM STEHT: die NICHT-MONOTONIE ist real und reproduziert - Fuenftel 1 (+1,40) liegt ueber Fuenftel 0 (+0,77). Sie war immer bekannt und galt als hinnehmbar. ⚠️ Die Kontrolle ist uebrigens AUCH nicht monoton (-0,17/+0,07/+0,09/+0,11/-0,10) - bei fuenf verrauschten Punkten ist exakte Monotonie selten zufaellig. Aber `funding`s Spanne ist ZEHNMAL groesser

- Quelle: n92_b9_funding_buckel_auf_frei.py

**2.252-inhaltlich** — ⚠️⚠️ UND SIE IST INHALTLICH MERKWUERDIG: 'zweitbestes Funding schlaegt bestes Funding'. Das koennte heissen, dass EXTREMES Funding ein Warnsignal ist statt des besten Falls - eine eigene Hypothese, die nie geprueft wurde. ⚠️ Nicht Teil von B9, aber notiert

- Quelle: n92_b9_funding_buckel_auf_frei.py / offene Frage

**2.253** — ✔✔ B10: AUF `frei` IST DIE BESETZUNG AUSGEGLICHEN UND DER BUCKEL VERAENDERT. `schnitt` liefert dort +1,28 / +1,59 / +0,28 / -1,19 / -1,96 bei 48/48/47/48/48 Ankern je Fuenftel. N-65 fand auf der 20-%-Menge dagegen +4,07 / +5,55 / +9,49 / +1,71 / -4,65 - einen ausgepraegten HOCHPUNKT IN DER MITTE. Auf `frei` sind nur Fuenftel 0 und 1 vertauscht, danach faellt es sauber

- Quelle: n93_b10_schnitt_stufen_auf_frei.py

**2.253-dieselbe-form** — ✔✔✔ UND ES IST EXAKT DIESELBE FORM WIE BEI `funding`: +0,77 / +1,40 / +0,22 / -0,64 / -1,75, ebenfalls Hochpunkt bei Fuenftel 1. Zwei UNABHAENGIGE Groessen - Funding aus dem Terminmarkt, `schnitt` aus der Kursreihe - zeigen auf `frei` denselben Knick an derselben Stelle

- Quelle: n93_b10_schnitt_stufen_auf_frei.py

**2.253-kontrolle** — ✔ Die Kontrolle trennt sauber: `zufall` hat auf `frei` eine Spanne von 0,28 gegen `schnitt`s 3,55 und `funding`s 3,15 - beide Beitraege liegen ZWOELFFACH darueber

- Quelle: n93_b10_schnitt_stufen_auf_frei.py

**2.253-schaetzer** — ⚠️ DIE GEGENPROBE HAT SICH GELOHNT: bei `schnitt` gehen Median (+1,28) und MITTEL (+62,39) weit auseinander - seine Verteilung hat schwere Raender (536 Symbole gegen `funding`s 300, die zusaetzlichen sind kleinere Coins). Bei `funding` stimmen beide fast ueberein. ⚠️ Auch die Kontrolle wird mit dem Mittel wild (+0,56 / -7,23 / +2,72 / -0,60 / +4,55) - der MEDIAN ist hier richtig

- Quelle: n93_b10_schnitt_stufen_auf_frei.py

**2.254** — ⚠️⚠️⚠️ B10 IST DAMIT KEINE MESSFRAGE MEHR, SONDERN EINE MASSSTABSFRAGE: `schnitt` erfuellt die Monotonie-Vorgabe GENAUSO WENIG wie `funding` - und `funding` laeuft LIVE. Entweder die Vorgabe gilt streng, dann muesste auch `funding` fallen; oder sie gilt nicht streng, dann ist `schnitt` registrierbar (100 % Abdeckung, R-R9 im Gefolge). Das ist eine Nutzerentscheidung

- Quelle: n93_b10_schnitt_stufen_auf_frei.py

**2.254-praezedenz** — ✔ Und das Projekt hat genau diese Lage schon einmal benannt (2.161-massstab): 'Einen Kandidaten an einer Huerde scheitern zu lassen, die die Bestandsbeitraege nie nehmen mussten, waere zweierlei Mass gewesen.' Damals fuehrte es zur Zeitstabilitaetspruefung der LEBENDEN Beitraege - hier fuehrt es zur Monotoniefrage

- Quelle: Befund 2.161-massstab

**2.255** — ⚠️ B11 IST NICHT UNBERUEHRT - Nutzerhinweis 09.09.: 'glaube zu Extremfunding gab es bereits eine Bewertung'. Er hat recht: `funding_extrem` ist ein registrierter Kandidat. ⚠️ ABER er misst eine ANDERE Achse - den Abstand vom EIGENEN Normalzustand in MAD, VORZEICHENLOS, je Symbol. B11 fragt nach der FORM der Querschnitts-Rangskala

- Quelle: messe_kandidaten_als_regel.py / Nutzerhinweis 09.09.

**2.255-teilbeleg** — ⚠️ Trotzdem ist er ein TEILBELEG gegen die B11-These: waere extremes Funding ein Warnsignal, muesste `funding_extrem` es zeigen. Er zeigt im Gesamtlauf WIDERSPRUCH (traegt auf 20 %, nicht auf 50 %), und F-207 haelt fest, dass er die Live-Sperre NICHT verbessert

- Quelle: Befund 2.219 / F-207

**2.255-aber** — ⚠️⚠️ WAS DIE THESE DAGEGEN STUETZT: der Knick sitzt bei `funding` UND bei `schnitt` an DERSELBEN Stelle (Fuenftel 1 ueber Fuenftel 0), auf `frei`, bei zwei unabhaengigen Datenquellen. Das ist schwer als Zufall zu lesen - und es waere eine Aussage ueber den MARKT, keine Messschwaeche

- Quelle: n93_b10_schnitt_stufen_auf_frei.py

**2.256** — ⚠️⚠️⚠️ MEIN VORSCHLAG IST DURCHGEFALLEN: die SPANNE gegen den Nullpunkt trennt NICHT. Auf `frei` bestehen ALLE ACHT Kandidaten - darunter `rsi` (2,16) und `amihud` (1,32), die im Gesamtlauf NICHT tragen. Nur die Kontrolle faellt durch (0,28 gegen p97,5 = 0,70). Ein Kriterium, das jeden durchlaesst, haelt niemanden auf

- Quelle: n94_spanne_statt_monotonie.py

**2.256-grund** — ✔ DER GRUND IST IM NACHHINEIN EINLEUCHTEND: die Spanne misst, ob die Fuenftel AUSEINANDERLIEGEN - nicht, ob sie etwas BEDEUTEN. Auch `rsi` spreizt sich, ohne zu tragen. Spreizung und Wirkung sind zwei verschiedene Dinge

- Quelle: n94_spanne_statt_monotonie.py

**2.257** — ⚠️⚠️ UND DIE GEGENPROBE ZEIGT, WIE SCHIEF DIE MONOTONIE STEHT: von acht Kandidaten sind nur `turnover` und `vola` monoton. SECHS sind es nicht - darunter ZWEI LIVE LAUFENDE (`funding` und `oi_aenderung`). Die Vorgabe wurde nie an den Bestandsbeitraegen geprueft

- Quelle: n94_spanne_statt_monotonie.py

**2.258** — ⚠️ DIE RICHTIGE FRAGE IST EINE ANDERE, und sie braucht kein drittes Kriterium: IST DIE NICHT-MONOTONIE STABIL? Reproduziert 'Fuenftel 1 ueber Fuenftel 0' ueber Haelften und Teilmengen, ist es ein MARKTEFFEKT - dann ist die Stufentabelle richtig und die Monotonie-Vorgabe war falsch. Kippt es, ist es Rauschen und die Vorgabe hat einen Sinn

- Quelle: Vorschlag 09.09.2026

**2.258-beides** — ✔ Und es beantwortet B10 UND B11 in einem Zug: der Knick sitzt bei `funding` und `schnitt` an DERSELBEN Stelle, bei zwei unabhaengigen Datenquellen. Ist er stabil, ist 'das Extrem ist nicht der beste Fall' belegt - und das waere eine Aussage ueber den MARKT

- Quelle: Vorschlag 09.09.2026

**2.259-kontrollen** — ✔ Die Kontrolle ist ueberall sauber: `zufall` zeigt weder bei d01 noch bei d34 einen trennbaren Wert, in keiner Haelfte. Und `schnitt` ist UNTERMAECHTIG - auch sein d34 ist nicht trennbar, also sagt sein d01 nichts. `turnover` zeigt ein trennbares NEGATIVES d01, dessen Haelften aber kippen (+0,021 gegen -0,262)

- Quelle: n95_ist_der_knick_stabil.py

**2.262** — ⚠️⚠️⚠️ DER BETRIEBSABLAUF IST ZWEISTUFIG - und F-212s Messmenge bildet ihn nach. `marktrang.raenge` bildet den Rang ueber die MESSBASIS (536) und liest ihn fuer unsere Symbole nur ab (,DER RANG ENTSTEHT UEBER DEN MARKT'); `auswahl.waehle` nimmt danach k=2 aus der Watchlist nach 250-Tage-Entwicklung - 4,7 %. F-212s ,oberste 5 % nach Momentum' ist damit KEIN Messkonstrukt, sondern eine Nachbildung genau dieser Auswahl, nur auf der Messbasis statt auf der Watchlist. ⚠️ Damit ist der Widerspruch aus 2.228 aufloesbar: die Ableitungsbasis (`frei`) ist die Rangmenge, die Auswahlmenge ist die Bewertungsmenge - zwei verschiedene Rollen, kein Widerspruch

- Quelle: agent/marktrang.py:643 / agent/auswahl.py:70

**2.263** — ⚠️⚠️⚠️ DIE MENGE ENTSCHEIDET DAS URTEIL UEBER DEN KNICK (N-96). `d01` = Fuenftel 1 minus Fuenftel 0 bei `funding`: auf `frei` +0,0402 [-0,0369 .. +0,1159] NICHT trennbar, auf 20 % +0,2069 [+0,0137 .. +0,4304] TRENNBAR - und die Kontrolle ist in BEIDEN Zellen stumm (+0,0139 bzw. +0,0033). Auf `frei` traegt `d34` (+0,0656 [+0,0191 .. +0,1180]), der Aufbau arbeitet dort also; auf 20 % traegt `d34` NICHT (+0,0786), waehrend `d01` traegt. ⚠️⚠️ ES GIBT KEINE MENGE, AUF DER BEIDES ZUSAMMENPASST - und damit keinen Beleg fuer das Zusammenlegen von Stufe 0 und 1

- Quelle: n96_d01_auf_der_selektierten_menge.py

**2.264** — ⚠️⚠️ AUF DER LIVE-MENGE IST DIE FRAGE NICHT BEANTWORTBAR (N-97). Auf der Watchlist (43 Werte, Rang ueber die Messbasis, Verengung NACH dem Rang wie 2.229) hat `d34` nur 2,7 bzw. 2,4 Anker je Fuenftel - KEIN BEFUND, nicht ,traegt nicht'; `d01` hat dort ein Band von ±0,25 R. ⚠️⚠️ Und die Menge, auf der die ENTSCHEIDUNG faellt, sind k=2 Werte pro Tag. Eine fuenfstufige Tabelle laesst sich darauf nicht beurteilen - das ist keine Frage der Sorgfalt, sondern der Datenlage. Nebenbefund: von 43 Watchlist-Werten liegen je Tag 4,2/4,1/~11/2,7/2,4 in den Funding-Fuenfteln - die Stufen -0,54 und -1,70 tragen unter drei Werte je Tag

- Quelle: n97_d01_auf_der_watchlist.py

**2.265** — ⚠️⚠️ ,MONOTON' HIESS NIE STRENG MONOTON. `pruefe_funding_monoton.py:59` prueft mit einer TOLERANZ von 0,02 R (`werte[i] >= werte[i+1] - 0.02`). Die Inversion vom 30.08. betrug 0,002 R - ein Zehntel davon. Der Knick war BEKANNT und bewusst durchgelassen, nicht uebersehen. ⚠️ Die Toleranz steht nirgends in der Registrierung, die schlicht ,monoton ueber fuenf Fuenftel' behauptet - und sie ist die EINZIGE Monotoniepruefung im System; `turnover` hat gar keine. Damit waere das Zusammenlegen keine Fehlerkorrektur, sondern Kosmetik an einer bereits bewerteten Stelle

- Quelle: pruefe_funding_monoton.py:59

**2.266** — ⚠️⚠️⚠️ EIGENER KONSTRUKTIONSFEHLER, VOM CODE GEFANGEN: der erste N-96-Lauf hat ZUERST VERENGT UND DANN GERANGT. Damit entstehen Fuenftel INNERHALB der Kohorte - ein Merkmal, das weder `marktrang.raenge` noch `sammle` berechnet (beide: ,NACH dem Rang verengen, nie davor'). Vorabtest auf Kunstdaten mit korrelierter Auswahl: 0 % gemeinsame Mitglieder in Fuenftel 0. ⚠️ Bei `funding` blieb der Schaden klein (+0,2317 gegen +0,2069), weil seine Momentum-Korrelation +0,002 ist - der Fehler war real, seine Wirkung hier zufaellig gering. ⚠️⚠️ Gefunden hat ihn nicht die Pruefsuite, sondern das Nachlesen im BETRIEBSCODE - dieselbe Lehre wie 2.229

- Quelle: Selbstbefund 09.09.2026 / Befund 2.229

**2.267** — ⚠️⚠️⚠️ K-1a GEMESSEN: KEIN registrierter Beitrag traegt auf der A1-MENGE - und zwar bei KEINEM k (2, 3, 5, 8, 13, 21, alle A1-waehlbaren). `funding` -0,0264 bei k=2 bis +0,0151 bei allen; `turnover` durchgehend negativ (-0,0590 bis -0,0116); `oi_aenderung` +0,0374 bis +0,0220. Alle Baender schliessen den Nullpunkt ein. ⚠️ Die Kontrolle `zufall` traegt bei KEINEM k - 7 von 7 sauber, der Lauf gilt

- Quelle: k1a_beitrag_auf_der_a1_menge.py

**2.267-kein-nullbefund** — ⚠️⚠️ UND DAS IST KEIN NULLBEFUND, sondern fehlende AUFLOESUNG: bei k=2 findet die Anlage nicht einmal einen GEPFLANZTEN Effekt von 0,40 R - Urteil ,KEIN BEFUND (Leiter zu kurz)' bei `funding`, `turnover` UND der Kontrolle. Erst ab k=21 bzw. auf der vollen A1-Menge reicht die Leiter (,traegt nicht bis 0,20'). ⚠️ Die registrierten Beitraege sind damit NICHT widerlegt - sie sind dort nicht pruefbar

- Quelle: k1a_beitrag_auf_der_a1_menge.py

**2.268** — ⚠️⚠️⚠️ `schnitt` SAH BEI k=2 UND k=3 WIE EIN TRAEGER AUS (+0,8697 [+0,1099 .. +1,6776] und +0,4989) - es ist die KOLLINEARITAET aus 2.242. Die Diagnose zeigt es unmittelbar: die Regel sperrt auf der A1-Menge 82,3 % der Gewaehlten statt der definitionsgemaessen 20 %, und `frei` traegt im Schnitt 0,35 Anker JE TAG - weniger als einen. Der Sperranteil faellt 82/75/66/59/49/43/34 mit wachsendem k, die Wirkung spiegelbildlich 0,87/0,50/0,21/0,11/0,04/-0,00/-0,03. ⚠️ Ursache: die A1-Regel waehlt die zwei besten nach 250-Tage-Entwicklung - wer so gestiegen ist, steht ueber seinem eigenen Schnitt. A1 und `schnitt` messen dasselbe

- Quelle: k1a_diagnose_besetzung.py

**2.269** — ⚠️⚠️ DIE REGISTRIERTEN SPERREN FEUERN IM BETRIEB KAUM: auf der Watchlist sperrt `turnover` 1,9 % der Werte (bei k=2: 5,5 %), `funding` 13,2 %, waehrend `oi_aenderung` mit 20,4 % und die Kontrolle mit 20,0 % genau auf dem definitionsgemaessen Fuenftel liegen. ⚠️ Eine Sperre, die zwei von hundert Werten trifft, ist praktisch keine - und sie erklaert, warum die Beitraege laut F-212 auf 1,5 % der Anker wirken. Der Grund ist die Messbasis: `turnover` deckt 66 von 536 Symbolen ab, und die Watchlist liegt in seiner Verteilung unten

- Quelle: k1a_diagnose_besetzung.py

**2.270** — ✔ A1 SPERRT WIRKLICH - am Betriebscode geprueft, nicht angenommen: `rollen_lauf.py:1269` endet mit `return`, wenn ein Symbol nicht in `auswahl['gewaehlt']` steht. ⚠️ ABER NUR OHNE BESTAND (`not _hat_bestand`) - gehaltene Positionen umgehen die Auswahl ganz. Damit ist die Einstiegsmenge bestaetigt k=2 je Tag, und K-1b (Bestandsmenge) ist eine echte zweite Frage, keine Variante derselben

- Quelle: agent/rollen_lauf.py:1269

**2.271** — ⚠️⚠️ 14 VON 43 WATCHLIST-WERTEN SIND HEUTE GAR NICHT A1-WAEHLBAR - ihnen fehlt die Jahreshistorie, und `auswahl.rangliste` ueberspringt Werte mit `len(kerzen) <= 250`: AIOZ, AKT, ASTER, BRETT, CANTON, CAT, GRIFFAIN, HYPE, KAS, MON, MORPHO, PLUME, SUPRA, VSN. ⚠️ Ueber die ganze Historie sind im Schnitt nur 14,0 Werte je Tag waehlbar (33 %), 2026 aber 37,5 (87 %) - wer den Durchschnitt als heutigen Zustand liest, unterschaetzt die Menge um mehr als das Doppelte

- Quelle: k1a_beitrag_auf_der_a1_menge.py

**2.272** — ⚠️ KEIN WIDERSPRUCH ZU 2.229-funding, ABER AUCH KEINE REPRODUKTION (R-R11): K-1w misst `funding` auf der Watchlist mit +0,0886 [+0,0582 .. +0,1458], K-1a auf seiner vollen A1-Menge mit +0,0151 [-0,0101 .. +0,0366]. Zwei Unterschiede, beide meine: anderer SCHAETZER (gepoolt statt Tagesklammer) und andere MENGE (nur A1-waehlbare Symbole statt aller 43). 2.229-funding steht unveraendert - K-1a hat es nicht gemessen

- Quelle: k1a_beitrag_auf_der_a1_menge.py / R-R11

**2.273** — ⚠️⚠️⚠️ DIE DRITTE STRUKTURELLE SPERRE DERSELBEN BAUART: `messnorm_auswahl.pruefe_auswahl` misst unter der TAGESKLAMMER - median(frei) minus median(alle) INNERHALB jedes Tages. Auf der A1-Menge (k=2) bleiben gemessen NULL verwertbare Tage. ⚠️ Zusammen mit A1 (Hebel: Band auf binaeren Daten viermal zu eng) und A2 (Akkumulation: Blockregel bei H90 braeuchte 22 Jahre) steht dreimal dieselbe Aussage: DIE MESSANLAGE REICHT NICHT DORTHIN, WO DAS SYSTEM ENTSCHEIDET. Das ist kein Messfehler, sondern eine Aussage ueber die Datenlage - und die Folge ist eine NUTZERENTSCHEIDUNG: entweder die Kette entscheidet auf breiterer Menge, oder die Bewertung gilt ausdruecklich nur auf einer Stellvertretermenge als validiert

- Quelle: k1a_beitrag_auf_der_a1_menge.py / A1 / A2

**2.274** — ⚠️⚠️⚠️ N-46 IST NICHT GESCHLOSSEN - meine BEGRUENDUNG ist von der eigenen Abbruchbedingung widerlegt. Vorhergesagt war: die Tagesmischung liegt DEUTLICH HOEHER als der Verschub. Gemessen liegt sie durchgehend NIEDRIGER (Faktor 0,2 bis 0,6): amihud +0,0070 gegen +0,0323 · vola +0,0078 gegen +0,0364 · schnitt +0,0154 gegen +0,0571 · rsi +0,0121 gegen +0,0271 · zufall +0,0041 gegen +0,0069. ⚠️ Die Tagesmischung ist damit der GROSSZUEGIGERE Nullpunkt, nicht der zu strenge - genau umgekehrt zu meiner Begruendung

- Quelle: n98_n46_laengs_nullpunkt.py

**2.274-rr11** — ⚠️⚠️ UND DIE AUSGANGSBEOBACHTUNG VON N-46 IST NICHT REPRODUZIERT: sie lautet ,bei `amihud` lieferte die Kontrolle +0,620 gegen einen echten Wert von +0,713'. Gemessen steht amihuds echter Wert bei -0,0445 und die Tagesmischung bei +0,0022 - drei Groessenordnungen daneben, also eine andere Skala und eine andere Messung. **R-R11 ist nicht erfuellt**, und ohne Reproduktion ist der Blocker N-46 weder geloest noch widerlegt

- Quelle: n98_n46_laengs_nullpunkt.py / R-R11

**2.275** — ✔✔ WAS TROTZDEM STEHT - der zirkulaere Verschub ist als Nullmodell BRAUCHBAR, drei von vier Pruefungen sauber. P1 ZENTRIERT: bei `zufall` +0,0034 mit Streuung 0,0026, also nahe null. P2 KONTROLLE: `zufall` traegt unter Verschub NICHT. P3 MACHT: ein gepflanzter Effekt von 0,20 R wird mit +0,0420 [+0,0374 .. +0,0465] gefunden - erwartet waren 0,20 x (1 - GRENZE) = 0,040. ⚠️ Der Treffer ist exakt und bestaetigt nebenbei zum dritten Mal den 20-%%-Skalenfaktor aus Fehler 5

- Quelle: n98_n46_laengs_nullpunkt.py

**2.276** — ⚠️⚠️ DIE ENTSCHEIDUNG ZWISCHEN DEN BEIDEN NULLPUNKTEN HAENGT NICHT AN IHRER HOEHE, sondern an der FEHLALARMQUOTE gegen bekannte Wahrheit. Genau dieses Verfahren hat am 09.09. den Nullbezug entschieden (150 Nullwelten, drei Basen: `nullpunkt` 2,7 %% Fehlalarme bei Soll 2,5 %%, `null_oben` 0 %% aber nur 63 %% Fundquote, `null` 28 %%). Fuer die LAENGS-Achse steht dieser Selbsttest aus - er ist der naechste Schritt von N-46, nicht eine weitere Begruendung

- Quelle: selbsttest_messanlage.py / Befund 2.204

**2.278** — ✔ HERKUNFT SAUBER GETRENNT (Nutzervorgabe 10.09.: ,trennen nach vor und nach dem aktuellen Umbau - Messungen, Dokumente und Code'). N-46 uebernimmt `laengs_rang` und `wirkung` aus `n75` (07.09., VOR dem Standard) - beides DEFINITIONEN, kein Nullmodell. Band, Nullpunkt, Perzentil und Leiter kommen aus `messnorm` (NACH). Der Akkumulationsbefund vom 28.08. dient als VORBILD, nicht als Beleg. ⚠️ Dafuer gibt es jetzt `soll_ist.py`, das die Grenze fuer alle drei Ebenen ausweist: Code 174 von 303 Altbestand · Messungen 356 von 458 ohne vermerkte Basis · Dokumente 48 von 55 vor dem Umbau

- Quelle: soll_ist.py / REGISTER_Werkzeuge

**2.279** — ⚠️⚠️⚠️ DIE HEBELDIAGNOSE IST KORRIGIERT: NICHT ,die Bewertung ist zu schwach', sondern ,sie ist zu GROB'. Ich habe drei Tage lang F-220 zitiert (,nur EINE Lage erreicht 2,60x') - F-220 ist am 06.09. ZURUECKGEZOGEN, und der Kalibrierungsfaktor 19,5 % ist am 05.09. gefallen. Es gilt 2.174-neu: unkalibriert erreichen ZWEI Lagen die Zielzone (funding bestes 3,90x, funding bestes + turnover mittleres 4,56x), und die Abstufung ist ECHT

- Quelle: Befund 2.174 / 2.174-neu

**2.279-zerlegt** — ✔ ,SCHWACH' IST DAMIT ZERLEGT - auf Nutzerfrage 10.09. (,erkennen wir ueberhaupt gute Hebelchancen?'): NIVEAU ✔ ja, zwei Lagen erreichen 2-5x · AUFLOESUNG ⚠️ nein, die Abstufung SPRINGT von 1,02x auf 3,90x, weil die Beitraege Fuenftel sind (2.174-grenzen) · TRENNSCHAERFE ⚠️ NIE GEMESSEN - ob eine hoehere Quote mit einer hoeheren REALEN Trefferquote einhergeht · DECKEL ✔ `hebel_max` = 10 vorhanden. ⚠️⚠️ Wir erkennen ,gut' gegen ,nicht gut', aber nicht ,wie gut'

- Quelle: Befund 2.174-grenzen / Nutzerfrage 10.09.

**2.280** — ⚠️⚠️ A1 IST DAMIT KEINE NACHARBEIT MEHR, SONDERN VORAUSSETZUNG. Die offene Trennschaerfefrage (,geht ein hoeherer Hebel mit einer hoeheren realen Trefferquote einher?') fragt nach BINAEREN Ausgaengen - und genau dort ist unser Band viermal zu eng, weshalb die Kontrolle traegt (2.238). Ohne A1 ist die Frage nicht beantwortbar, mit welcher Simulation auch immer

- Quelle: Befund 2.238 / 2.279-zerlegt

**2.281** — ⚠️⚠️⚠️ DREI FEHLAUSSAGEN AN EINEM TAG AUS DERSELBEN URSACHE: ich habe aus MEMORY-Eintraegen zitiert, ohne im REGISTER gegenzupruefen. (1) ,Der Hebel ist konzeptionell abgeschlossen' - der Eintrag schliesst nur die Instrument-Achse. (2) ,`portfolio_wert_historie` ist LEER' - sie laeuft seit dem 08.05. mit 91 Zeilen, ich las die veraltete Desktop-Kopie. (3) ,Nur EINE Lage erreicht 2,60x' - F-220 ist zurueckgezogen. ⚠️⚠️ Ein Memory-Eintrag ist ein SCHNAPPSCHUSS vom Tag seiner Entstehung; das Register wird ERZEUGT und ist aktuell. Beide sehen beim Lesen gleich verbindlich aus

- Quelle: Selbstbefund 10.09.2026

**2.282** — ✔✔✔ N-46 IST GELOEST - UND ZWAR MIT DEM VORHANDENEN WERKZEUG. Gegen bekannte Wahrheit gemessen (100 Nullwelten je Beharrlichkeit, Soll 2,5 %) arbeiten BEIDE Nullmodelle: Verschub 0,0 %% / 1,0 %%, Tagesmischung 1,0 %% / 4,0 %%. ⚠️⚠️ Damit ist N-46s Praemisse WIDERLEGT - ,die Tagesmischung taugt dort nicht' trifft nicht zu. Kriterium 4 des Vierfachtests (Regel 3 laengs) ist nicht mehr blockiert, und damit auch nicht der Weg zu einem dritten Beitrag

- Quelle: n99_n46b_fehlalarm_laengs.py

**2.282-fund** — ✔✔ UND DIE FUNDQUOTE ENTSCHEIDET KLAR FUER DIE TAGESMISCHUNG - auf SECHS von acht Sprossen besser, auf zwei gleich, nirgends schlechter. Bei 0,985: 0,03 R 20,0 %% gegen 5,0 %% · 0,05 R 50,0 %% gegen 25,0 %% · 0,08 R 90,0 %% gegen 70,0 %%. ⚠️ Das ist exakt das `null_oben`-Muster vom 09.09.: das konservativere Modell hat weniger Fehlalarme und zahlt mit Fundkraft. Dort fiel die Entscheidung genauso - fuer das Modell, das die SOLLQUOTE trifft

- Quelle: n99_n46b_fehlalarm_laengs.py

**2.283** — ⚠️⚠️⚠️ DIE AUFLOESUNGSGRENZE DER LAENGS-ACHSE - und sie entwertet einen eigenen Nebenbefund. Bei hoher Beharrlichkeit (0,985, wie `schnitt`) findet die Anlage einen Effekt von 0,03 R in 20 %%, von 0,05 R in 50 %% und erst ab 0,08 R in 90 %% der Faelle. **Die echten Kandidaten liegen bei 0,02 bis 0,05 R.** ⚠️⚠️ Damit ist N-46as Nebenbefund ,kein Kandidat traegt laengs' (2.277) KEINE Aussage ueber die Welt, sondern UNTERMACHT - genau fuer die beharrlichen Groessen, um die es geht

- Quelle: n99_n46b_fehlalarm_laengs.py

**2.284** — ⚠️⚠️ SELBSTBEFUND: MEIN VERSCHUB-BAU WAR NICHT NOETIG. N-46a hat ein Nullmodell gebaut, um ein Problem zu loesen, das die Messung nicht bestaetigt - die Tagesmischung war die ganze Zeit brauchbar. ⚠️ Die Ursache steht in 2.274-rr11: ich habe N-46s Ausgangsbeobachtung (,amihud: Kontrolle +0,620 gegen echten Wert +0,713') NIE reproduziert, sondern auf ihr gebaut. R-R11 verlangt die Reproduktion VOR dem Bau, nicht nur vor dem Widerruf

- Quelle: Selbstbefund 10.09.2026 / R-R11

**2.285** — ⚠️ EIN VORBEHALT ZUR TAGESMISCHUNG, benannt: bei hoher Beharrlichkeit feuert sie mit 4,0 %% gegen ein Soll von 2,5 %% - das 1,6-fache. Bei niedriger Beharrlichkeit liegt sie mit 1,0 %% darunter. Sie KLAMMERT das Soll also, waehrend der Verschub durchgehend darunter liegt. Fuer beharrliche Groessen ist ein TRAEGT-Urteil damit etwas grosszuegiger, als das Band verspricht - kein Fehler, aber beim naechsten Grenzfall zuerst hier hinsehen

- Quelle: n99_n46b_fehlalarm_laengs.py

**2.286** — ✔✔✔ A2 IST GELOEST - DIE AKKUMULATION IST MESSBAR. Nicht durch eine Aenderung am Horizont, sondern durch einen METHODENWECHSEL: ein PERMUTATIONSTEST (zirkulaerer Verschub) statt eines Bootstrap-Bandes. Er braucht keine Bloecke, weil der Verschub die Abhaengigkeitsstruktur ERHAELT statt sie zu zerschneiden - genau deshalb funktioniert er bei H90, wo 20 Bloecke 5.400 Handelstage braeuchten. ⚠️ N-46b hat das NICHT geloest: dort ging es um den Nullpunkt, hier fehlte das BAND

- Quelle: n101_a2_akkumulation.py

**2.286-schnitt** — ✔✔ `schnitt` TRAEGT FUER DIE AKKUMULATION - der erste gemessene Beitrag fuer diese Lage ueberhaupt: Rangvorsprung +0,0470 gegen ein Nullband [-0,0121 .. +0,0106], p 0,000, auf 481 von 518 Symbolen, Kaufquote 19,3 %%. ⚠️ Das ist STAERKER als `UNTER_SMA` am 28.08. (+0,0283) - und es passt, denn 2.155 haelt fest: `schnitt` und das Akkumulationsmass sind DIESELBE GROESSE

- Quelle: n101_a2_akkumulation.py

**2.287** — ⚠️⚠️⚠️ `funding` UND `oi_aenderung` WIRKEN FUER DIE AKKUMULATION UMGEKEHRT - und das ist KEIN Nullbefund. `funding` -0,0230 gegen [-0,0105 .. +0,0093], p 0,000 · `oi_aenderung` -0,0178 gegen [-0,0075 .. +0,0076], p 0,000. Ihr ,gutes' Fuenftel (wenig Funding, wenig OI-Aufbau) ist systematisch der SCHLECHTERE Kauftag. ⚠️⚠️ Beide sind LIVE als `strategien=('einstieg',)` deklariert und wirken deshalb NICHT auf die Akkumulation - das ist nach diesem Befund ein GLUECK, kein Zufall: wuerden sie dort greifen, liefen sie rueckwaerts

- Quelle: n101_a2_akkumulation.py

**2.288** — ⚠️ `turnover` TRAEGT fuer die Akkumulation (+0,0353, p 0,005) - aber auf nur 49 von 518 Symbolen, und sein Nullband ist mit ±0,022 das breiteste im Lauf. Dieselbe Abdeckungsgrenze wie ueberall (B6: die Umlaufmenge kommt fuer 66 Werte). Ein Befund unter Vorbehalt der Abdeckung, kein tragfaehiger Beitrag

- Quelle: n101_a2_akkumulation.py

**2.289** — ✔✔ R-R11 IST ERFUELLT - die Kontrollen reproduzieren den 28.08.-Stand vor der ersten neuen Aussage: TIEFPUNKT (Positivkontrolle) +0,4245 gegen +0,4242 · WOCHENTAG (Negativkontrolle) -0,0005 gegen -0,0008 · `zufall` +0,0015, p 0,223. ⚠️ Die Aufloesung dieser Zielgroesse betraegt 0,0216 in RANGeinheiten - A9s Grenze (0,08 R) gilt hier NICHT, weil `verbilligung` ein Perzentilrang mit Basisrate 0,500 ist und keine R-Groesse

- Quelle: n101_a2_akkumulation.py

**2.290** — ⚠️⚠️ DREI EIGENE FEHLER BEIM BAU, alle vor dem Lauf gefangen: (1) die Kauftage wurden ueber die Tagesliste aus `K.baue` auf die Kursreihe gemappt - die beginnt aber spaeter (Horizontabschnitt), die Maske waere STILL um einen unbekannten Betrag verschoben gewesen; jetzt kommt die Datumszuordnung aus derselben Abfrage wie die Kurse. (2) Der Verschub zog den Startpunkt des Symbols ab - das ist der dokumentierte 28.08.-Fehler mit umgekehrtem Vorzeichen, jede symbolabhaengige Verschiebung hebt die Gleichzeitigkeit auf. (3) Das Urteil kannte nur TRAEGT/traegt nicht und haette `funding` als Nullbefund ausgewiesen - dieselbe Verwechslung wie Fehler 4 vom 08.09.

- Quelle: Selbstbefund 10.09.2026

**2.291** — ✔ DIE NAHT IST GEBAUT: `Beitrag.instrumente` als vierte Achse neben klassen/strategien/richtungen, Vorgabe LEER = alle. Bitgleich nachgewiesen (Quote 0,37303333333333333 vor und nach dem Umbau), vier Waechter im Paket ,Stufen' - darunter einer, der festhaelt, dass HEUTE kein Beitrag eine Instrumentliste traegt. ⚠️ Der Grund: die Antwort ,gilt fuer alle Instrumente' steckte bis heute in der ABWESENHEIT eines Feldes - derselbe Fehler, den `assetklassen.hebel_handelbar()` schon einmal behoben hat

- Quelle: agent/wahrscheinlichkeit.py / pruefe_pakete --paket Stufen

**2.291-entscheidung** — ⚠️⚠️ FACHLICHE BEWERTUNG 10.09. (Nutzerauftrag): DER HEBEL KOMMT VORERST AUS DEM SPOT-WEG - aber NICHT, weil es dieselbe Frage waere. Es gibt drei belegte Unterschiede: Stop (Hebel ja, Spot nein), Zielgroesse (`barriere` binaer gegen `bewegung_r`), Dauer (2,0 Tage Median gegen H20) und taegliche Finanzierung. Entschieden wurde so, weil (1) eine eigene Hebelbewertung heute NICHT MESSBAR ist (A1), (2) das Aufteilen der Evidenz beide schwaecht - zwei Beitraege auf 1,5 %% der Anker - und (3) `r(q)` nur EINE Quote braucht

- Quelle: Fachliche Bewertung 10.09.2026 / Befund 2.173-hebel

**2.291-ausloeser** — ✔ UND DER AUSLOESER FUER DIE ECHTE TRENNUNG IST BENANNT UND PRUEFBAR: sobald A1 behoben und `barriere` messbar ist, wird gemessen, ob ein Beitrag auf `barriere` ANDERS wirkt als auf `bewegung_r`. Traegt er dort anders, bekommt der Hebel seine eigene Bewertung - sonst nicht. ⚠️ Das ist eine Messfrage mit einem Datum, kein offener Vorbehalt

- Quelle: Fachliche Bewertung 10.09.2026

**2.292** — ⚠️⚠️⚠️ DER VIERFACHTEST IST IN SEINER FASSUNG VOM 05.09. VON NIEMANDEM ZU BESTEHEN. Kriterium 4 (Regel 3 laengs) liefert bei ALLEN fuenf gemessenen Kandidaten UNTERMACHT - einschliesslich der Kontrolle. Das ist der vorab benannte Ausgang: ein Befund ueber die ANLAGE, nicht ueber die Kandidaten. A9 (2.283) ist damit an echten Daten bestaetigt: die Laengs-Achse loest bei 0,02 bis 0,05 R nicht auf, und genau dort liegen alle Kandidaten

- Quelle: n102_vierfachtest.py

**2.292-fehlkonstruktion** — ⚠️⚠️⚠️ UND KRITERIUM 4 IST FALSCH KONSTRUIERT - es muss nicht ausgesetzt, sondern mit dem RICHTIGEN Werkzeug gemessen werden. Es prueft heute mit einem SIGNIFIKANZTEST auf der Laengs-Achse, ob eine Groesse eine verkleidete Asset-Eigenschaft ist. Das richtige Mass steht seit dem 02.09. in Methodik 2.101: die STREUUNGSZERLEGUNG (Asset-Anteil = zwischen / (zwischen + innerhalb)), mit geeichter Skala - fester Wert je Symbol 95,9 %%, Zufall 0,1 %%, turnover 52 %%, volumenanteil roh 73 %% gegen relativ 1 %%. ⚠️⚠️ Das ist BESCHREIBEND, kein Signifikanztest - und deshalb von A9 GAR NICHT betroffen

- Quelle: Methodik 2.101 / Fachliche Bewertung 10.09.2026

**2.292-regel3** — ⚠️ Dazu kommt: CLAUDE.md haelt ausdruecklich fest, dass Regel 3 den QUERSCHNITTSVERGLEICH NICHT VERBIETET. Ein Signifikanztest auf der Laengs-Achse verlangt damit MEHR, als die Regel fordert - Regel 3 verbietet das dauerhafte Asset-Urteil und den Asset-Rang beim Hebel, nicht die Querschnittsmessung

- Quelle: CLAUDE.md Regel 3 / F-227

**2.293** — ✔✔ `schnitt` IST DER EINZIGE ROBUSTE KANDIDAT - und N-73 ist damit das ANTI-HIN-UND-HER-WERKZEUG. Ueber alle zulaessigen Beitragsmengen gemessen: `schnitt` traegt auf 3 von 3 (+0,1830 / +0,1858 / +0,0434), `schnitt50` auf 2 von 3, `vola` auf 1 von 3, `amihud` und `zufall` auf 0 von 3. ⚠️⚠️ DAS PROFIL ,traegt auf einer Menge, auf zweien nicht' IST das Hin und Her - je nach gewaehlter Menge lautet das Urteil anders. `schnitt` hat es nicht. Alle vier Kandidaten haben 100 %% Abdeckung und bestehen Kriterium 2

- Quelle: n102_vierfachtest.py

**2.293-abgrenzung** — ⚠️ ABGRENZUNG, damit daraus kein voreiliger Schluss wird: das hier gemessene Kriterium 2 fragt ,erste gegen zweite Haelfte' (N-68). S-7 hat am 07.09. eine ANDERE Frage gestellt - ,traegt er in den Fenstern ab 2022?'. Mein ,stabil' hebt S-7 NICHT auf

- Quelle: n102_vierfachtest.py / S-7

**2.294** — ⚠️⚠️ DIE LUECKE, DIE VOR JEDER REGISTRIERUNG ZU SCHLIESSEN IST: `funding` und `turnover` sind VOR N-73 registriert worden, auf `frei`. Sie sind NIE ueber alle zulaessigen Mengen geprueft worden. Einen neuen Kandidaten daran zu messen und die Bestandsbeitraege nicht, waere zweierlei Mass - genau der Fehler, der am 07.09. schon einmal gefangen wurde (N-2: ,einen Kandidaten an einer Huerde scheitern zu lassen, die die laufenden Beitraege nie nehmen mussten')

- Quelle: n102_vierfachtest.py / N-73 / N-2

**2.295** — ⚠️ `amihud` LAEUFT LAENGS RUECKWAERTS: -0,0445 [-0,0994 .. -0,0005], das Band schliesst die Null negativ aus. Mein ,untermaechtig'-Etikett verschluckt das - dieselbe Grobheit wie bei A2 am selben Tag, nur umgekehrt. ⚠️ Es passt zu 2.166: er misst Ausfuehrbarkeit, nicht Potential

- Quelle: n102_vierfachtest.py

**2.296** — ✔ DIE KONTROLLE ARBEITET, und das ist der Nachweis, dass der Messstandard tut, wofuer er gesetzt wurde: `zufall` hat bei 20 %% ein Band OHNE Null (+0,0026 .. +0,0321) - und die Norm ueberstimmt es korrekt mit ,traegt nicht bis 0,0346'. Ohne den Nullpunkt waere daraus ein Scheinbefund geworden

- Quelle: n102_vierfachtest.py / Messstandard 08.09.

**2.297** — ✔✔✔ V1: KRITERIUM 4 IST ERFUELLBAR - der Deadlock ist aufgeloest. Mit der STREUUNGSZERLEGUNG (Methodik 2.101) statt eines Signifikanztests bestehen die meisten Kandidaten es in der ROHEN Form: `oi_aenderung` 0,4 %% · `schnitt50` 6,9 %% · `funding` 15,7 %% · `vola` 16,5 %% · `schnitt` 25,4 %% - alle ueberwiegend ZEITPUNKT-Aussagen. Die Skala ist geeicht (FEST 99,9 %%, ZUFALL 0,1 %%), beide Arme auf der Menge des Kandidaten

- Quelle: n103_v1_asset_anteil.py

**2.297-rr11** — ✔ R-R11 ERFUELLT VOR DER ERSTEN NEUEN AUSSAGE: `turnover` roh 51,2 %% gegen die registrierten 52 %% aus F-170. Die Messung reproduziert, also gilt der Lauf

- Quelle: n103_v1_asset_anteil.py / F-170

**2.298** — ⚠️⚠️⚠️ UND DER BEFUND TRIFFT DEN BESTAND, NICHT DIE KANDIDATEN: `turnover` laeuft LIVE und ist zu 51,2 %% eine ASSET-Eigenschaft - er sagt zur Haelfte, WELCHES Asset, nicht WANN. `amihud` liegt mit 70,7 %% noch hoeher, ist aber nicht registriert. ⚠️ Haette ich nur die Kandidaten gemessen, waere `turnover` mit 51 %% durchgelaufen, waehrend ein neuer Kandidat mit demselben Wert gefallen waere - zweierlei Mass, der Fehler von N-2

- Quelle: n103_v1_asset_anteil.py / F-170 / 2.294

**2.299** — ⚠️⚠️⚠️ MEINE EIGENE LOESUNG IST WIDERLEGT - von der eigenen Gegenpruefung. Ich hatte die RELATIVE Form (Standardisierung gegen den eigenen 20-Tage-Schnitt) als Behandlungsvorschlag gefuehrt, weil sie alle Kandidaten unter 1,5 %% bringt. Auf Kunstdaten mit EINGESTELLTEM Asset-Anteil: gebaut 10 %% -> relativ 0,0 %% · gebaut 50 %% -> 0,0 %% · gebaut 90 %% -> 0,0 %%. ⚠️⚠️ Die Standardisierung entfernt das Symbolmittel PER KONSTRUKTION - sie senkt JEDE Groesse auf null und beweist NICHTS

- Quelle: n103_v1_asset_anteil.py / Selbstbefund 10.09.2026

**2.299-folge** — ⚠️ WAS DARAUS FOLGT, und es ist kein Nullbefund: die relative Form bleibt ein moeglicher UMBAU - aber der Nachweis muss dann ueber die WIRKUNG der umgeformten Groesse laufen, nicht ueber ihren Asset-Anteil. Genau so war es beim Volumenanteil: relative Form 1,4 %% Asset-Anteil UND +0,0231 R Wirkung. BEIDES, nicht eines

- Quelle: n103_v1_asset_anteil.py / F-170

**2.300** — ✔✔ `schnitt` BESTEHT KRITERIUM 4 IN DER ROHEN FORM (25,4 %% Asset-Anteil, ueberwiegend Zeitpunkt) - und er ist zugleich der EINZIGE robuste Kandidat aus dem Vierfachtest (3 von 3 Mengen, 2.293) und der erste gemessene Beitrag der Akkumulationslage (2.286-schnitt). ⚠️ Damit besteht er drei der vier Kriterien; Kriterium 3 (unabhaengig von `funding`) steht noch aus

- Quelle: n103_v1_asset_anteil.py / 2.293 / 2.286-schnitt

**2.301** — ⚠️ NEU AUS V1: `turnover`s Asset-Anteil von 51,2 %% ist ein offener Punkt AM BESTAND, kein Grund zum Abschalten. Regel 3 verbietet das dauerhafte Asset-Urteil; 51 %% heisst, dass die HAELFTE der Streuung aus dem Symbol kommt - nicht, dass der Beitrag falsch ist. ⚠️ Er bleibt registriert; zu klaeren ist, ob eine andere FORM (wie beim Volumenanteil) denselben Beitrag mit weniger Asset-Anteil UND erhaltener Wirkung liefert

- Quelle: n103_v1_asset_anteil.py

**2.302** — ✔✔ V7/KRITERIUM 3: `turnover` IST UNABHAENGIG VON `funding` - und das ist das EINZIGE gedeckte Urteil des Laufs. In Funding-Fuenftel geschichtet traegt er in 2 von 5 echten Faechern und in 0 von 5 GEMISCHTEN. Zwei Faecher Unterschied, ueber der Aufloesung. ⚠️ Damit ist die Registrierungsaussage ,zu 92 %% additiv zu Funding' erstmals UNTER DER NORM bestaetigt

- Quelle: n104_v7_kriterium3.py

**2.302-gegenkontrolle** — ✔ UND DIE GEGENKONTROLLE IST DER GRUND, WARUM DAS URTEIL TRAEGT. Dieselbe Schichtung mit GEMISCHTEM Funding - gleiche Fachgroesse, keine Information. Ohne diesen Arm waere jedes ,traegt nicht mehr' wertlos, weil es allein daher kommen koennte, dass ein Fuenftel ein Fuenftel der Anker hat. Die Konstruktion stammt aus `pruefe_n1_schichtung_gegen_partner`

- Quelle: n104_v7_kriterium3.py

**2.303** — ⚠️⚠️ FUER DIE KANDIDATEN IST KRITERIUM 3 MIT DIESEM AUFBAU NICHT ENTSCHEIDBAR - aus DREI verschiedenen Gruenden, und sie sind zu trennen: `vola` traegt ohne Schichtung, aber in 0 von 5 Faechern - echt WIE gemischt, also kostet die SCHICHTUNG (kein Redundanzbefund). `schnitt` und `schnitt50` tragen auf `frei` ohnehin nicht - das ist die MARKT-Frage, nicht ihre Beitragsmenge. `oi_aenderung` liegt mit 2 gegen 3 Faechern auf der Aufloesungsgrenze

- Quelle: n104_v7_kriterium3.py

**2.303-struktur** — ⚠️ DIESELBE STRUKTUR WIE BEI KRITERIUM 4 VOR V1 - aber NICHT dieselbe Ursache. Bei Kriterium 4 war das WERKZEUG falsch (Signifikanztest statt Streuungszerlegung). Hier ist das Werkzeug richtig, es fehlt die MACHT: Schichtung mal schmale Menge laesst zu wenige Anker. Das ist ein Dimensionierungsproblem, kein Konstruktionsfehler

- Quelle: n104_v7_kriterium3.py

**2.304** — ⚠️⚠️ EIGENE UEBERDEUTUNG, VOM ERGEBNIS GEFANGEN: der erste Lauf las `oi_aenderung`s ,2 gegen 3 Fuenftel' als ,`funding` erklaert einen Teil mit'. Bei fuenf Faechern ist EIN Fach die feinste unterscheidbare Einheit - ein Unterschied von einem Fuenftel ist die GRENZE, keine Aussage. ⚠️ Dieselbe Ueberdeutung wie beim Gleichstand in N-46b; dort hat der Vorabtest sie gefangen, hier erst das Ergebnis. Die Aufloesungsgrenze steht jetzt im Werkzeug

- Quelle: n104_v7_kriterium3.py / Selbstbefund 10.09.2026

**2.305** — ⚠️⚠️ UND EINE STILLE VERENGUNG, VOM NUTZER GEFANGEN: ich hatte `schnitt50` aus dem Lauf genommen - aus LAUFZEITgruenden (9 Minuten je Kandidat), nicht aus Sachgruenden. Er steht sachlich gut da: 100 %% Abdeckung, 6,9 %% Asset-Anteil (der zweitbeste Wert nach `oi_aenderung`), stabil, und laut 2.222 die EINZIGE monotone Form - genau das zaehlt beim Schritt FORM. ⚠️ Nachgemessen: dasselbe Bild wie `schnitt` (2 gegen 1 Fach, auf `frei`). Die Kuerzung war trotzdem falsch - sie im Skriptkopf zu vermerken ist nicht dasselbe wie sie zu begruenden

- Quelle: Nutzereinwand 10.09. / n104_v7_kriterium3.py

**2.306** — ⚠️ DER MENGENVORBEHALT, jetzt benannt statt stillschweigend: fuer die REGISTRIERTEN Beitraege (`turnover`, `oi_aenderung`) ist `frei` die Registrierungsbasis - dort richtig. Fuer KANDIDATEN ohne Basis (`schnitt`, `schnitt50`, `vola`) ist `frei` die MARKT-Frage (P6). Behoben werden kann es hier nicht: eine Momentum-Menge UND ein Funding-Fuenftel zugleich liessen rund SECHS Anker je Tag uebrig

- Quelle: n104_v7_kriterium3.py / P6

**2.308** — ⚠️⚠️⚠️ V8 WIDERLEGT MEINEN EIGENEN LOESUNGSWEG AUS 2.307. Mit ZWEI Faechern statt fuenf ist KEIN Urteil mehr gedeckt - mit fuenf war es eines. `turnover` hatte bei fuenf Faechern 2 gegen 0; dieselben Daten liefern bei zwei Faechern 2 gegen 1, und das ist nur EIN Fach Unterschied. ⚠️⚠️ NICHT DIE MACHT WAR DER ENGPASS, SONDERN DIE ZAEHLMETRIK: weniger Faecher geben mehr Anker je Fach, aber die Zaehlung hat dann nur noch drei moegliche Werte (0, 1, 2)

- Quelle: n105_v8_kriterium3_zwei_faecher.py

**2.308-vorfrage** — ✔ WAS V8 TROTZDEM GELOEST HAT: die VORFRAGE. Auf der 20-%%-Menge tragen `schnitt` (+0,1858), `schnitt50` (+0,0698) und `vola` (+0,1332) ohne Schichtung - auf `frei` taten sie das nicht. Der Mengenvorbehalt aus 2.306 ist damit ausgeraeumt, und die Messung ist ueberhaupt erst aussagekraeftig geworden

- Quelle: n105_v8_kriterium3_zwei_faecher.py

**2.309** — ⚠️⚠️⚠️ UND DAS RICHTIGE WERKZEUG LAG DIE GANZE ZEIT VOR - ich habe es wegen eines AUFRUFPARAMETERS verworfen. `messnorm_rand.pruefe_geschichtet` misst die Schichtung als EINEN Befund mit EINEM Band - Nullpunkt, Trennschaerfe und eine eingebaute Positivkontrolle (`pflanze`), die dem Original fehlt. Und `marke=None` gibt die Median-Differenz, also den STANDARDmassstab. ⚠️ Ich habe es abgelehnt, weil der eine Aufrufer, den ich ansah (`pruefe_n1_schichtung_gegen_partner`), `marke=2.0` uebergab - ich habe das Argument eines Aufrufers fuer die Natur des Werkzeugs gehalten

- Quelle: messnorm_rand.py:290 / Selbstbefund 10.09.2026

**2.311** — ✔ KANARIENVOGEL IN V8: `traegt_wirklich()` liest das URTEIL statt der Eigenschaft `traegt`. Bei zwei Faechern auf einer 20-%%-Menge ist die Blockzahl knapp, und `Befund.traegt` weiss nichts davon - genau der Fehler 4 vom 08.09., an dem `k1c_lagen_eigene_zielgroesse` einmal gescheitert ist (drei gemeldete Traeger, waehrend alle fuenf KEIN BEFUND lauteten). Auf Kunstdaten geprueft

- Quelle: n105_v8_kriterium3_zwei_faecher.py

**2.312** — ⚠️⚠️⚠️ V2: `funding` BESTEHT N-73 NICHT - ein LIVE laufender, registrierter Beitrag traegt auf 2 von 3 zulaessigen Beitragsmengen (10 %% +0,0688 TRAEGT · 20 %% +0,0582 NICHT TRENNBAR · 50 %% +0,0313 TRAEGT). Das ist dasselbe Profil wie `schnitt50` - und schwaecher als der Kandidat `schnitt` mit 3 von 3

- Quelle: n106_v2_n73_auf_dem_bestand.py

**2.312-antwort** — ✔✔✔ DAMIT IST DIE ZWEIERLEI-MASS-SORGE AUS 2.294 BEANTWORTET - und zwar UMGEKEHRT zur Erwartung: `schnitt` besteht N-73 BESSER als jeder registrierte Beitrag. Ihn an dieser Huerde zu messen ist nicht unfair - er nimmt sie sauberer als der Bestand. ⚠️ Die Huerde bleibt damit gueltig; sie ist fuer den BESTAND neu zu begruenden, nicht fuer den Kandidaten zu senken

- Quelle: n106_v2_n73_auf_dem_bestand.py / 2.294

**2.313** — ⚠️⚠️ UND EINE LESART, DIE DER BRUCH VERSTECKT: `turnover` besteht mit ,1 von 1' - aber nur, weil bei seiner Abdeckung (66 von 536) UEBERHAUPT NUR EINE Beitragsmenge zulaessig ist (50 %%). ,1 von 1' ist eine SCHWAECHERE Aussage als ,3 von 3'. Der N-73-Bruch haengt daran, wie viele Mengen die Datenlage traegt - wer nur den Bruch liest, haelt einen duennen Beitrag fuer so robust wie einen breiten

- Quelle: n106_v2_n73_auf_dem_bestand.py

**2.314** — ✔ `oi_aenderung` BESTEHT N-73 SAUBER: 2 von 2 (20 %% +0,0464 · 50 %% +0,0211), dazu `frei` +0,0126. ⚠️ Er ist damit der einzige LIVE laufende Beitrag, der die Huerde ohne Einschraenkung nimmt - und er laeuft als SPERRE, nicht als Regler

- Quelle: n106_v2_n73_auf_dem_bestand.py

**2.325-auswahl** — ⚠️⚠️ 2.325 IST ZU BERICHTIGEN, NICHT ZU WIDERRUFEN - und die beiden Teile sind zu trennen: (a) die MESSUNG steht - auf der Momentum-20-%%-Menge ist der Haelftenunterschied +0,1973 [+0,0717 .. +0,3892] nachgewiesen und dreifach reproduziert. (b) die ZUSCHREIBUNG faellt - es ist nicht `schnitt`s Eigenschaft, sondern die der KOLLINEARITAET mit der Auswahl (2.333). ⚠️ FUER DEN VIERFACHTEST AENDERT SICH NICHTS: er ist auf der SELEKTIERTEN Menge definiert (F-212), und dort faellt `schnitt` an Kriterium 2. **2.319 bleibt abgeloest**

- Quelle: n112_v11_gegenpruefung.py / F-212

**2.325-warum-egal** — ✔ UND DIE PRAKTISCHE FOLGE DREHT SICH DADURCH NICHT UM: der Grund gegen `schnitt` als dritten Beitrag ist jetzt 2.335 (er bildet zu vier Fuenfteln die AUSWAHL nach) - ein Grund, der von Kriterium 2 voellig unabhaengig ist und schon seit dem 09.09. im Bestand steht. ⚠️ Wer nur 2.333 liest, koennte meinen, `schnitt` sei rehabilitiert. Ist er nicht - der Einwand ist nur ein anderer geworden, und ein staerkerer

- Quelle: 2.335 / 2.222 / 2.158-redundanz

**2.391** — ✔✔ DIE LANDKARTE DER KETTE - was rechnet, was urteilt, und wo (`Basisinfos/Kette_Landkarte.md`, Nutzerfrage 12.09.). ZWOELF STUFEN, davon SIEBEN VOR dem ersten Modellaufruf - jede von ihnen hat eine eigene Stufe, WEIL sie keinen Aufruf kostet (anlass 16.08., auswahl 23.08., terminmarkt 02.09.). Das Modell wird an Stufe 8 gefragt (`urteil`, Rolle BC, einmal je Asset), Rolle A einmal je Umlauf davor, Z.ai nebenlaeufig danach. ⚠️ KLARSTELLUNG: DER *ENTSCHEIDER* IST KEINE LLM-ROLLE MEHR - Haendler und Entscheider wurden am 10.08. in EINEN Aufruf gelegt (162 Aufrufe taeglich waren nicht tragbar); die gleichnamige STUFE 12 ist gerechnet (`potential.traegt`, Schwelle 0,080 R). GEMESSEN ueber 7 Tage (3.345 Laeufe, 39.471 Zellen hinein, 202 heraus): der haerteste Filter ist die GERECHNETE Entscheiderstufe mit 1.251 von 1.366 (92 %%); davor liegen anlass 12.005, wiederholung 14.187 und auswahl 10.555 - alle ohne Modellaufruf

- Quelle: Basisinfos/Kette_Landkarte.md · gate_durchlaessigkeit NB-Sicherung 12.09.

**2.390** — ✔✔✔ DIE ERSTE ECHTE HEBELMAIL AUS PAKET B - SOL, 12.09.2026 07:39, Modell gemini-3.1-flash-lite. DIE RECHNUNG STIMMT UND IST NACHVOLLZIEHBAR: Trefferquote 34,6 %% bei CRV 2,0 -> halbes Kelly 0,97 %% -> Risiko 0,97 %% von 17.987 EUR = 175 EUR; Aggregat-Deckel 0 von 540 EUR belegt; bei 8,9 %% Stop 1.962 EUR Positionswert / 500 EUR Einsatz = 3,9x; am Stop -174 EUR, am Ziel +349 EUR. Nachgerechnet: Stopabstand (88,14 -> 80,26) = 8,9 %%, Ziel = 2x Stopabstand = 17,9 %%, Liquidation 72,17 EUR ,hinter dem Stop bis etwa Tag 46'. Die Mail nennt die Herleitung in EUR, den Deckel und die Grenze - genau wie gebaut. ⚠️ Der Trade traegt sich nach Gebuehren NICHT (noetig 44,4 %% Standard / 53,3 %% Bitpanda gegen 34,6 %% geschaetzt) - das steht da und sperrt nichts (Regel 2)

- Quelle: Mail SOL 12.09. · GUI Hebel-Reiter

**2.389** — ✔✔ DIE ABNAHME DES ERSTEN UMLAUFS (12.09.2026, aus dem Logfenster des NB-Exports). Neustart 07:08:06, alle Schluessel gefunden, Fernsteuerseite oben. In 17 Minuten ZWEI vollstaendige Umlaeufe ueber ALLE fuenf Ketten - aktien, hedge, krypto (43 von 43 gedeckt), rohstoffe, themen_etf, jeweils scharf. 0 Signale, Mails gehen raus (SMTP arbeitet: Verkaufsvorschlaege und Stop-Nachzieh-Empfehlungen an den Nutzer). Nur 4 Fehler seit dem Neustart, alle vier derselbe bekannte (`marktrang`, messdaten.db - siehe 2.389-log). ✔ UND DER SCHALTER WIRKT WIE GEBAUT: `hebel_screening_job` laeuft weiter alle 15 Minuten und protokolliert ,Screening uebersprungen; Positionsabgleich laeuft weiter' - genau die Trennung aus 2.379-schalter, jetzt im Betrieb belegt

- Quelle: NB-Export 12.09. 07:25 · log_auszug

**2.389-log** — ⚠️⚠️ EIN ABGESPROCHENER ZUSTAND WIRD ALS ERROR PROTOKOLLIERT - 262 MAL IN 72 STUNDEN. `agent.marktrang` meldet bei JEDEM Lauf ,Messbasis schnitt nicht lesbar (data/messdaten.db)' auf ERROR-Ebene; die Datei fehlt am Notebook planmaessig (166 MB, Rollout 02.09.), und `schnitt` ist seit dem 31.08. ohnehin nur noch Anzeige. Von 362 Fehlerzeilen der letzten 72 Stunden sind 262 diese eine. ⚠️ DAS IST DIESELBE KLASSE WIE 2.386: ein geplanter Zustand, als Fehler gemeldet - nur kostet er hier keinen Absturz, sondern die Lesbarkeit des Logs. Wer echte Fehler sucht, sucht sie in einem Rauschen aus Falschmeldungen. ➔ Einmal je Lauf als Hinweis statt bei jedem Symbol als ERROR. ✔ BEHOBEN AM SELBEN TAG (Nutzerentscheidung 12.09.): `marktrang._messbasis_ausfall` unterscheidet, was vorher in einen Topf fiel - FEHLT die Datei, ist der Rang unmoeglich und das ist abgesprochen (EINMAL je Prozess ein Hinweis, danach still); IST sie da und liefert nichts, bleibt es ein Fehler bei JEDEM Lauf. Die Unterscheidung steht an EINER Stelle - die Rangschleife entscheidet sie nicht selbst, sonst laufen zwei Fassungen auseinander. Gegengeprueft an der ECHTEN Funktion mit Log-Mitschnitt (Paket Luecken, drei Pruefungen): hinweis / still / fehler. Erwartete Wirkung am Notebook: 262 der 362 Fehlerzeilen fallen weg

- Quelle: NB-Export 12.09. · agent/marktrang._messbasis_ausfall

**2.388** — ⚠️⚠️ DIE WARTESCHLANGEN DER ALTEN KETTE - 112.775 ZEILEN, DIE NIEMAND MEHR ANFASST (Nutzerbeobachtung 12.09.: *,die Urteile bewegen sich nicht mehr'*). An der frischen NB-Sicherung gezaehlt: `hebel_triggers` 96.000 auf ,neu' OHNE Kandidatenstatus (14.07. bis 12.09.), 14.047 verfallen, 1.699 auf ,llm_generiert' - und die JUENGSTE davon vom 10.08. 04:50. DREI URSACHEN, sauber getrennt: (1) der VERBRAUCHER steht seit 33 Tagen - `llm_generiert` setzt nur die alte Hebel-Pipeline ueber den Budget-Allocator, und die urteilt nicht mehr; die 1.699 sind ein Endstand, kein klemmender Zaehler. (2) Der ERZEUGER lief bis 12.09. 03:28 weiter: das alte Screening legt alle 15 Minuten je Symbol und Richtung eine Zeile an, rund 2.300 am Tag. (3) Der VERFALL kann sie nicht abraeumen - er fasst ausdruecklich nur `ist_kandidat = 1` an. ✔ SEIT 12.09. 07:08 IST DER ERZEUGER AUS (2.384, im Log belegt). ⚠️ NICHT LOESCHEN: die Tabelle ist die Messgrundlage von `messe_allocator_gegen_zufall.py` (ausgewaehlt gegen verfallen) - und die 96.000 Messzeilen duerfen NICHT auf ,verfallen' gesetzt werden, das hiesse dort ,Kandidat, nie ausgewaehlt' und verfaelschte den Vergleich. ➔ Nutzerentscheidung 12.09.: die 1.029 wartenden KANDIDATEN auf ,verfallen' - sie stehen in der Warteliste der Oberflaeche und werden nie mehr verarbeitet. DASSELBE MUSTER beim Marktscan: 4.071 Kandidaten auf ,neu', 10 verworfen, 7 uebernommen - eine Entdeckung, die 4.071 unbearbeitete Vorschlaege erzeugt, hat kein Erkenntnis-, sondern ein Auswahlproblem (stuetzt Schritt 39). ⚠️⚠️ UND ES IST KEIN EINMALIGER ALTBESTAND, SONDERN EIN KREISLAUF: der Rueckstau wurde schon dreimal von Hand geleert - 696 Zeilen am 19.07., 1.077 am 30.08., 1.029 am 12.09. Genau dazu passt, dass `llm_generiert` seit Wochen exakt auf 1.699 steht. ✔ AUSGEFUEHRT 12.09. (Nutzerentscheidung): die 1.029 wartenden Kandidaten stehen auf ,verfallen' (14.047 -> 15.076), `llm_generiert` unberuehrt, die 96.000 Messzeilen unberuehrt. Ruecknahme-Marke: `status_geaendert_am = 2026-09-12T06:22:10.655469+00:00` traegt genau diese 1.029 Zeilen. ➔ WEIL DER RUECKSTAU WIEDERKEHRT, wird die Prognose jetzt GEPRUEFT statt geglaubt: der Export fuehrt den Altbestand mit Zeitstempel, und der Vollcheck fragt (E8), ob die Kette NACH dem letzten Trigger lief - dann ist der alte Erzeuger nachweislich still. In beide Richtungen an einer Testdatei geprueft

- Quelle: NB-Sicherung 12.09. · hebel_triggers · Nutzer 12.09.

**2.387** — ✔✔ DER ROLLOUT AM NOTEBOOK - Paket B laeuft dort (12.09.2026). Pull auf 9f9408c (142 Commits, fast-forward, keine Konflikte, `config.yaml` lokal unveraendert). `ausrollen_paket_b.py`: lesend 2 Punkte offen (Kapital ,alt', Quelle kapital) - genau die vorhergesagten; mit `--nachrechnen` 10 Tage geschrieben, danach 13 Punkte, 0 offen. ⚠️⚠️ DAS KAPITAL WAR NICHT NUR ALT, SONDERN FALSCH: 9.942 -> 17.978 EUR (+81 %%), und das ist KEINE Marktbewegung - die zehn nachgerechneten Tage liegen zwischen 17.612 und 18.742 EUR. Die alte Zeile vom 01.09. fuehrte 32 Symbole und 6 OHNE KURS, die neuen 38 und 0: es fehlten sechs Positionen komplett (die gestakten, P-3). Der Aggregat-Deckel steht damit bei 539 statt 298 EUR - haetten wir nicht nachgerechnet, waere er auf der halben Groesse gelaufen. Schalterstand am Geraet bestaetigt: Hebel aus der Quote AN, altes Hebel-Screening AUS, Marktscan AN. Spalten `instrument`, `verlust_am_stop_eur`, `strategie` vorhanden und LESBAR. ✔ DIE KETTE IST DURCH: Suite 2.179 Pruefungen ALLE BESTANDEN, 5 Bloecke uebersprungen, Exit 0; `--nachweis-paket-b` 17 von 17 Faellen, davon D2 der Kern: der Deckel WANDELT statt zu sperren (frei 30 von 539 EUR -> Spot mit 800 EUR, Cooldown 12 statt 3,5 h), und die Mail begruendet es im Klartext; `finde_freie_namen` 0. ⚠️ EINE ABHAENGIGKEIT, die der Notebook-Lauf selbst benannt hat: der Nachweis rechnet gegen 539 EUR - also gegen die Kapitalbasis, die dieser Rollout ERST HERGESTELLT hat. Mit dem alten Wert waeren es 298 EUR gewesen und der Deckel haette frueher auf Spot zurueckgestuft

- Quelle: ausrollen_paket_b.py am Notebook 12.09.

**2.387-rot** — ⚠️ DIE ZWEI ROTEN DES ERSTEN NOTEBOOK-LAUFS - keine davon ein Fehler des Betriebscodes. (1) Paket Register: zwei Dokumente ohne Standkopf, die es NUR am Notebook gibt (`LLM_BUDGET_ANALYSE_2026-07-15.md`, `LLM_BUDGET_SESSION_2026-07-16.md`, beide unversioniert) - ein Geraeteartefakt, Entscheidung des Nutzers (loeschen oder Kopf ergaenzen). (2) Paket 15: ,die Mail traegt die Kennung des geschriebenen Signals'. ⚠️ NICHT DER CODE - `rollen_lauf` setzt sie direkt nach dem Schreiben. Der aufgezeichnete Client antwortet KAUFEN, die Kette machte daraus einen AUSSTIEG (Ausstiegsempfehlung SCHLIESSEN), es entstand also GAR KEINE Einstiegsmail - 4x NICHTS_TUN, 1x KAUFEN mit Ausstieg. Die Pruefung verlangte eine Kennung an einer Mail, die es in diesem Lauf nicht gab. ➔ Sie haengt jetzt an ihrer Voraussetzung: gibt es eine Asset-Mail, MUSS sie die Kennung tragen; gibt es keine, wird das BENANNT (uebersprungen). Ein gruener Haken ohne Gegenstand waere schlimmer als ein rotes Kreuz. ✔ BEIDE ERLEDIGT: die zwei Juli-Dokumente haben ueber `markiere_dokumente.py` ihren Standkopf mit dem URSPRUENGLICHEN Datum bekommen (2 gesetzt, 48 unveraendert; unversioniert, also nur am Geraet) - danach 2.179 Pruefungen ALLE BESTANDEN. ⚠️ Und das Werkzeug nennt die Einbahnstrasse selbst: das Aenderungsdatum steht jetzt auf heute, die Einstufung kommt ab sofort NUR noch aus dem Kopf

- Quelle: Notebook-Lauf 12.09. · pruefe_pakete Paket 15

**2.386** — ⚠️⚠️⚠️ AM NOTEBOOK STARB DIE GANZE SUITE - 0 von 2.193 Pruefungen, ohne eine einzige ausgegebene Zeile (Rollout 12.09., gefunden im ersten Lauf nach dem Pull). URSACHE: drei ZUSTANDSpruefungen oeffneten `data/messdaten.db` ungeschuetzt - die Datei liegt am Notebook BEWUSST nicht (166 MB, so entschieden beim Rollout 02.09.). `sqlite3.OperationalError` in `paket_assetklassen_trennung`, und weil die Pakete VOR der Ausgabe laufen, fiel damit alles aus. Am Desktop faellt es nie auf, weil die Datei hier liegt - dieselbe Klasse wie `paket_b1` (24.08.), der KeyError vom 02.09. und die `.index()`-Pruefung vom 03.09.: eine Pruefung, die stirbt, prueft nichts mehr. ➔ DRITTE KATEGORIE statt Absturz ODER falschem Rot: `_datei_fehlt()` bucht den Block als UEBERSPRUNGEN, die Schlussausgabe nennt ihn samt Grund. Gegengeprueft: am Desktop unveraendert (Assetklassen 13, Kalibrierung 51, Neuaufnahme 6); mit simuliert fehlender Datei kein Absturz, 7 Pruefungen weniger, 3 Bloecke uebersprungen. ⚠️⚠️ ES WAREN FUENF STELLEN, NICHT DREI - und die vierte fand erst der zweite Notebook-Lauf: `paket_messstandard` ruft `messe_eigenschaft_beitrag.lade()`, und ERST DIESE Funktion oeffnet die Datei (Konstante `DB` im Modul). Gesucht worden war nach `connect(`-Aufrufen IM Pruefcode - eine Suche beweist Abwesenheit nur dort, wo sie gesucht hat. Die fuenfte: `pruefe_neuaufnahme.pruefe()` liest BEIDE Datenbanken und riss das ganze Paket mit (0 statt 6 Pruefungen). ➔ DREI EBENEN statt einer: (a) gezielte Wachen an den vier Bloecken, (b) das Paket Neuaufnahme wird als GANZES uebersprungen - dort ist die Frage ohne Messdatenbank nicht beantwortbar, (c) ein FANGNETZ um jeden Paketaufruf in `main()`: eine planmaessig fehlende Datei wird uebersprungen, JEDER andere Abbruch ist rot und mit Traceback - ein Paket darf die Suite nie wieder mitnehmen. ERWARTUNG AM NOTEBOOK: 2.180 Pruefungen, 4 Bloecke uebersprungen, 0 Rote. ⚠️⚠️ NULL ROTE HEISST DORT NICHT ,alles in Ordnung': alle vier bekannten Roten liegen im Paket Neuaufnahme und sind am Notebook NICHT BEANTWORTBAR. Sie gelten weiter - beantwortet werden sie am Desktop. ⚠️ Und auch dort nur auf dessen Bestandsstand (19.08.): wer ,jede GEHALTENE Position hat eine Messreihe' wirklich pruefen will, braucht Bestand UND Messreihen am selben Ort - das hat heute kein Geraet

- Quelle: pruefe_pakete._datei_fehlt · Fangnetz in main() · Notebook-Laeufe 12.09.

**2.384** — ✔✔✔ SCHARF GESCHALTET MIT DEM ROLLOUT VON PAKET B (Nutzerentscheidungen 12.09.2026). (1) `rollen_kette.hebel_aus_quote.aktiv: true` - ab jetzt entsteht der Hebel aus der Wahrscheinlichkeit r(q) statt aus der Stopgeometrie; die Vorgabe im CODE bleibt AUS, eingeschaltet wird allein in der config.yaml. Voraussetzungen lagen vor: Verteilung simuliert (2.378), E2E gezeigt (2.382), Rollout-Skript geprueft (2.383). (2) `hebel_screening.aktiv: false` - das ALTE Hebel-Screening verbraucht keine Rechenzeit mehr; Positionsabgleich und Hebelfuehrung laufen weiter (2.379-schalter, im Paket Hebelfuehrung gegen den Quelltext geprueft). (3) Der alte MARKTSCAN bleibt AN - siehe 2.385. Die Paketpruefung verlangt jetzt ausdruecklich `aktiv is True` in der config und `False` in der Code-Vorgabe: wer den Schalter zuruecknimmt, sieht es in der Suite

- Quelle: Basisinfos/config.yaml · Nutzerentscheidung 12.09.

**2.385** — ⚠️⚠️ DER ALTE MARKTSCAN HAT KEINEN ERSATZ - meine Empfehlung ,ausschalten' war voreilig und ist zurueckgezogen (Nutzerfrage 12.09.: *,warum sollen wir den Marktscan ausschalten bzw. was ist der Ersatz dafuer?'*). AN DER QUELLE GELESEN: `marktscan_job` (04:00/16:00) ruft `agent/krypto/marktscan.run_scan` - Entdeckung neuer Assets ueber CoinGecko Trending/Top-Gainers, Stufen A-D deterministisch, SEIT 14.07. OHNE Modellaufrufe; er schreibt `marktscan_candidates`, meldet Kaufkandidaten und ,Watchlist heiss' per Mail, entscheidet aber nichts (Aufnahme ueber die GUI). Er kostet CoinGecko-Abrufe, keine LLM-Kontingente. DIE ROLLEN-KETTE BEWERTET NUR DIE WATCHLIST (44 Kryptowerte) - ausserhalb sucht NIEMAND sonst. Ihn abzuschalten hiesse: keine neuen Werte mehr, ohne Ersatz. ⚠️ Zwei Einwaende bleiben: seine Schwellen (Score 70 / 50) sind VORLAEUFIG und nie gegen eigene Daten gemessen, und er meldet auf einer anderen Grundlage als die Kette

- Quelle: agent/krypto/marktscan.py · scheduler/background.marktscan_job · config.yaml marktscan

**2.383** — ✔✔ SCHRITT 24 VORBEREITET - `ausrollen_paket_b.py`, die Vollstaendigkeitspruefung fuer das Notebook (stehende Regel: Gesamtpaket statt Einzelschritte). Prueft Code, config, Schema mit LESEPROBE, Kapital, Datenfrische, Hebel-Schalter und Deckel; `--nachrechnen` schreibt die fehlenden Tage in `portfolio_wert_historie` (2.376-rollout). Getestet gegen eine Kopie der NB-Sicherung 11.09.: ohne Nachrechnen 2 Punkte offen (Kapital ,alt' 9.942 EUR, Quelle kapital ,abruf') - richtig gemeldet; mit Nachrechnen 9 Tage (02.09.-10.09.), Abdeckung je 1,0, Kapital FRISCH 18.213 EUR - derselbe Wert wie in H-1 ueber einen anderen Weg. Der INDEX springt nicht (95,58 -> 95,43), nur der Wert einmal (das Gestakte, 2.375-index). Neue Spalte `verlust_am_stop_eur` angelegt und gelesen; Deckel 546 EUR. SCHUTZSPERRE geprueft (Betriebspfad auf eine Attrappe gelenkt): am Desktop ohne `--db` Abbruch, keine Datei angelegt; als Notebook greift sie nicht. Am NB 24 von 44 Kryptowerten mit Hebel-Schalter. Suite 2193 Pruefungen, 4 bekannte Rote

- Quelle: ausrollen_paket_b.py · NB-Sicherung 11.09. (Kopie)

**2.382** — ✔✔✔ SCHRITT 23 - PAKET B VON ANFANG BIS ENDE NACHGEWIESEN (Befund 2.371: bis dahin nie ein Hebelgeschaeft simuliert). `simuliere_kette.py --nachweis-paket-b` gegen die NB-Sicherung 11.09. 04:48, zwei Kopien (Schalter an / aus), die Attrappe gezielt ueber die Marktraenge gesteuert (Funding 0 + Turnover 0 -> Quote 0,373). 17 Faelle gezeigt: ONDO wird HEBELGESCHAEFT - Zeile instrument ,hebel', 2,1x, Verlust am Stop 125,15 EUR; Mail mit Kopf ,Betrag 500 EUR - Hebel 2,1x', Hebelrechnung samt Aggregat-Satz, Liquidation, Anhang C, Chart als PNG; Hebeltopf 1.500 -> 2.000 EUR, Spot-Topf unveraendert; Cooldown 3,5 h (Spot 12 h). Aggregat im Lauf 170,20 EUR (ZZPLAN: Liquidation vor dem Stop = Eigenkapital 100; ZZOHNESTOP nach B: 70,20), mit dem Signal 295,35. Hebelfuehrung ordnet ZZPLAN SEIN geschriebenes Signal zu (HEBEL SENKEN mit Nachschuss), ZZOHNESTOP KURS FEHLT mit dem B-Hinweis. Derselbe Wert gleich danach: kein Modellaufruf (Anlass). Deckel ausgeschoepft (frei 2,90 EUR): AKT wird SPOT mit 800 EUR, die Mail nennt den Grund, Cooldown 12 h; mit Schalter AUS derselbe Betrag 800 EUR (N-38). BTC laeuft mit zwei Zellen, kein Akkumulationssignal. Kapital der Kopie 9.942 EUR (Stand 01.09., alt) -> Deckel 298 EUR; beim Rollout nachrechnen (2.376-rollout). Erster Lauf 16 von 18: ein Fehler der Pruefung selbst (erwartete frei 30 EUR, wo nur 3 frei waren) und der Befund 2.382-akku-anlass. Suite 2.192 Pruefungen, 4 bekannte Rote

- Quelle: simuliere_kette.py --nachweis-paket-b · NB-Sicherung 11.09. 04:48

**2.382-topf** — ✔ NUTZERENTSCHEIDUNG 11.09. spaet: WIE EMPFOHLEN - fuer Paket B bleibt die Topfregel, sie wird nach dem Rollout neu gefasst (Schritt 28). Der Befund: DER TOPF BEGRENZT PRAKTISCH NIE. `toepfe.belegt_eur` zaehlt nur Einstiege mit `outcome_status IS NULL` - die Zeilen, die die Signalverfolgung noch nicht gesehen hat. Am NB (11.09. 04:48): 5 Zeilen (Hebel 1.500, Spot 1.000 EUR). NICHT gezaehlt: 379 laufende Einstiege (,offen' - Hebelspalte 77 zu 37.500 EUR Tranche, alle Geometrie 1,0-1,5x; Spot 302 zu 144.000 EUR). Beide Lesarten gehen nicht auf: ,offen' mitzuzaehlen sperrte jeden Topf dauerhaft (Signale sind Empfehlungen, keine Positionen), es nicht zu tun macht den Deckel wirkungslos. Fuer den HEBEL begrenzt seit H-5 der Aggregat-Deckel (Positionen + Signale der letzten 24 h) - er ist die Grenze, die greift. Dazu trennt der Topf an der Spalte `hebel`: alte Geometriezeilen 1,2x zaehlen weiter als Hebel. Empfehlung: fuer Paket B nichts aendern, die Topfregel nach dem Rollout neu fassen

- Quelle: NB-Sicherung 11.09. signals · toepfe.belegt_eur

**2.382-liquidation** — ✔ NUTZERENTSCHEIDUNG 11.09. spaet: B MIT DER LIQUIDATIONSREGEL - gebaut und geprueft (Paket Aggregat-Deckel: Eigenschaft ueber 34 Faelle der echten Fuehrung gegen die unabhaengige Tagesformel; die Mutante ohne Regel wird gefangen). Vorgelegt war: VARIANTE B UND DIE LIQUIDATION. B wurde als min(11,7 %% x Positionswert, Eigenkapital) vorgelegt und so gebaut. Fuer eine Position MIT Plan gilt aber: liegt die Liquidation vor dem Stop, zaehlt das Eigenkapital. Dieselbe Regel auf den ANGENOMMENEN Stop, an 185 geschlossenen NB-Positionen (Haltedauer bis zum Schluss, Median 0,31 Tage): bei 56 %% laege die Liquidation davor - die meisten Altpositionen ueber 5x. Median 170 -> 176 EUR, 90 %% 496 -> 609 EUR, allein im Deckel 9,2 -> 14,1 %%. Neue Positionen des Systems sind auf 5x und RM-11 gedeckelt; betroffen waeren vor allem von Hand eroeffnete

- Quelle: NB-Sicherung 11.09. hebel_positions · Nutzer 11.09.

**2.381** — ✔✔ S-4 (c) O1 BEHOBEN - DIE 12 STUNDEN FUER KRYPTO WIRKTEN NICHT. `wiederholung.stunden` nahm den 3,5-h-Takt fuer JEDES letzte Signal mit Hebel ueber 1,0 - und die Geometrie schrieb auf Spot-Signale 1,0-1,5x (am NB 77 offene Zeilen, alle auf Spotbestaenden). Gerechnet mit der echten Funktion: BTC 11.09. 04:47 (Hebel 1,2) war nur bis 08:17 gesperrt. ➔ der kurze Takt gilt erst ab `hebel_ab` (2,0x, die Paket-B-Regel); danach BTC gesperrt bis 16:47 (12 h). Gegenprobe: 1,0 / 1,2 / 1,99 -> 12 h, 2,0 / 3,5 -> 3,5 h

- Quelle: agent/wiederholung.stunden · NB-Sicherung 11.09.

**2.381-spot** — ✔ S-4 (a) NACHWEIS: DER HEBELSCHALTER VERAENDERT DEN SPOT-BETRAG NICHT (N-38). Ueber `rechne()` an 1.436 echten NB-Einstiegen seit 23.08., mit und ohne Schalter: Betrag in ALLEN gleich (800 EUR). 472 davon (32,9 %%) trugen ohne Schalter einen Geometriehebel von 1,2x - mit Schalter reiner Spot: Verlust am Stop 48 -> 40 EUR (Median), der Betreff verliert ,(Hebel)', kein Buchen in den Hebeltopf. Die uebrigen 964 bitgleich. Das ist der Wegfall eines Scheinhebels, keine Aenderung der Spot-Groesse

- Quelle: s4_spot_nachweis.py 11.09. · NB-Sicherung 11.09.

**2.381-mail** — ✔✔ S-4 (b) DIE MAIL GEGLIEDERT - nach dem Vorschlag vom 11.09. (2.372), NICHTS GESTRICHEN. Kopf AUF EINEN BLICK (Zone, Stop, Ziel, Betrag und Hebel, Ergebnis in EUR, Trefferquote, beide Gebuehrenzeilen, Gesamtbild) · WAS DAGEGEN SPRICHT (je eine Zeile: Widerspruch der Gegenpruefung, UNGUENSTIG-Merkmale, Grenzen der Rechnung, Z1) · 1 Bewertung · 2 Rechnung · 3 Lage des Werts · 4 Marktvergleich · 5 Modelle (Urteil; Gegenpruefung mit dem Widerspruch in der Ueberschrift) · 6 Termine und Projekt · ANHANG (A nicht eingerechnet, B die ZWEITE, aeltere Trefferquote als solche benannt, C Liquidationsabstaende). Die zwei Trefferquoten: entschieden wird nach Abschnitt 1 (im Kopf), die Erfahrungsrate steht nur noch im Anhang. Der Kopf LIEST die fertigen Abschnitte (`gesamtbild.saetze/dagegen`) - keine zweite Rechnung. Trennstellen als Konstanten in `wahrscheinlichkeit`. Nachweis: Paket Mailgliederung 12 Pruefungen, darunter die EIGENSCHAFT ,jede uebergebene Zeile steht in der Mail'; Kettensimulation gegen die NB-Kopie baut die ONDO-Mail ueber den echten Weg, ohne neue Luecke. ⚠️ NICHT ERLEDIGT - Feinschliff nach dem Rollout: dieselbe Kursmarke aus drei Modulen (Marken, Weg zum Ziel, Vorfilter) und drei Rangangaben stehen weiter getrennt; die Gebuehren stehen im Kopf und im Anhang B

- Quelle: agent/signal_mail.baue_mail · gesamtbild.dagegen · Paket Mailgliederung · simuliere_kette 11.09.

**2.380-fenster** — ✔ NUTZERENTSCHEIDUNG 11.09.: DAS FENSTER BETRAEGT 24 STUNDEN (vorher gesetzt 3 Tage). `hebelfuehrung.KOPPEL_TAGE = 1.0` - es bestimmt, welches Signal einer Position als Plan gilt, und wie lange ein nicht eroeffnetes Hebelsignal im Aggregat-Deckel Risiko belegt. Laut 2.380-sim macht der Deckel damit rund 32 %% statt 73 %% der Hebelkandidaten zu Spot (Watchlist 2026, 18.213 EUR). Folge: wer spaeter als 24 h nach dem Signal eroeffnet, hat keinen Plan - siehe 2.380-ohne-stop

- Quelle: Nutzerentscheidung 11.09. · 2.380-annahmen

**2.380-ohne-stop** — ✔ NUTZERENTSCHEIDUNG 11.09.: VARIANTE B - eine Position OHNE bekannten Stop zaehlt im Aggregat-Deckel mit einem angenommenen Stop von 11,7 %% ab Einstand (Median der Systemstops, 2.378-gegenpruefung), hoechstens mit dem Eigenkapital (`hebel_aggregat.STOP_ANGENOMMEN`). Variante A (ganzes Eigenkapital) vom Nutzer ABGELEHNT: *,eine Position blockiert alles, das passt nicht zu unserem Vorgehen - initial haben wir angedacht, dass zumindest drei Hebelpositionen offen sein koennen'*. An den 188 echten Positionen: A Median 222 EUR (90 %% 720), allein im Deckel 18 %%, im Median passen 2,5; B Median 166 EUR (90 %% 500), allein 9 %%, im Median passen 3,3. Die Hebelmail sagt es: ,Stop unbekannt - im Aggregat-Deckel angenommen 11,7 %%' und je Position ,Im Deckel X EUR'. Nachweis: Paket Aggregat-Deckel (Eigenschaft ueber 27 Faelle), Mutationstest (A macht 4 Pruefungen rot, B ohne EK-Grenze 1), E2E 2.382. ✔ Dazu die Liquidationsregel (Nutzer 11.09. spaet, 2.382-liquidation): liegt die Liquidation schon vor dem angenommenen Stop, zaehlt das Eigenkapital

- Quelle: NB-Sicherung 11.09. hebel_positions · Nutzer 11.09. · agent/hebel_aggregat.py

**2.380** — ✔✔✔ H-5 GEBAUT - DER AGGREGAT-DECKEL (`agent/hebel_aggregat.py`, Nutzerentscheidung 11.09.: alle Hebelrisiken zusammen hoechstens 3 %% des Kapitals; P-4: die Korrelation gehoert hierher). Offen gezaehlt: Positionen aus `hebel_positions` (Verlust bis zum Plan-Stop, hoechstens das Eigenkapital; ohne bekannten Stop oder mit Liquidation vor dem Stop das Eigenkapital - ⚠️ ohne Stop seit dem Nutzerentscheid Variante B, 2.380-ohne-stop), offene Hebelsignale (nicht aufgeloest, Frist nicht abgelaufen, im Zuordnungsfenster, keiner Position zugeordnet) und die Signale DIESES Laufs. Die Summe unterstellt Korrelation 1. Der Deckel BEGRENZT: ein neuer Trade bekommt hoechstens das freie Restrisiko, faellt er unter 2x, wird er Spot mit dem gewohnten Betrag. Faellt die Abfrage aus: kein Hebel, laut. Neue Signalspalte `verlust_am_stop_eur` (die Tranche in `position_size_eur` ist nicht der gerechnete Betrag), in `models.Signal` und im Export. Nachweis: Paket Aggregat-Deckel 17 Pruefungen, von Hand gerechnet; MUTATIONSTEST - vier eingebaute Fehler, jeder macht Pruefungen rot (7 / 1 / 4 / 4 von 17); NB-Kopie: 0 EUR offen, Deckel 546 EUR; mit zwei kuenstlichen Positionen 158 EUR (57,50 bis zum Stop + 100 Eigenkapital ohne Plan), das Plan-Signal nicht doppelt

- Quelle: agent/hebel_aggregat.py · pruefe_pakete --paket Aggregat-Deckel · Mutationstest und NB-Kopie 11.09.

**2.380-sim** — ⚠️⚠️ WAS DER DECKEL MIT DEN HEBELTRADES TUT - und wie stark es an EINER Annahme haengt. `simuliere_hebelverteilung.py` Abschnitt 3b: Hebelkandidaten der Auswahl je Tag, beste Quote zuerst, jeder belegt sein Risiko W Tage (Signal offen oder Position gehalten). WATCHLIST 2026, 18.213 EUR: W = 1 Tag -> voll 55,9 %% · gekuerzt 11,7 %% · durch den Deckel Spot 32,4 %% · Median 3 Hebeltrades je Tag. W = 3 Tage -> voll 8,0 %% · gekuerzt 19,3 %% · Spot 72,7 %% · Median 1 je Tag. Alle Jahre, 18.213 EUR: W 1 -> Spot 61,0 %%, W 3 -> 84,0 %%. Gegenpruefung G7 (ein nicht greifender Deckel aendert nichts, 500 x 3) und G8 (die Belegung ueberschreitet den Deckel nie) bestanden. ⚠️ Naeherung: Tagesanker, keine Ausstiege vor Ablauf von W, kein Cooldown

- Quelle: simuliere_hebelverteilung.py 11.09. (drei Laeufe)

**2.379-instrument-korrektur** — ⚠️⚠️⚠️ KORREKTUR ZU 2.379 UND 2.379-instrument: die Kette schrieb `signals.instrument` NIE. Die Spalte fuellte erst die Start-Migration mit dem Instrument der GRUPPE - fuer Krypto immer spot (NB: 3.838 spot, 12 absicherung, 0 hebel). Hebelfuehrung und Ausstiegsfuehrung lesen genau diese Spalte - im Betrieb haetten sie nie ein Hebelsignal gefunden. Der E2E-Nachweis aus 2.379 hatte die Zeile VON HAND auf hebel gesetzt und das verdeckt. Die Spalte `hebel` taugt nicht als Ersatz: alle 77 offenen Zeilen mit `hebel` (1,0-1,5x, Geometrie) stehen auf SPOTbestaenden. ➔ `felder_aus_entscheidung` schreibt jetzt instrument hebel fuer ein Hebelgeschaeft aus r(q) oder SHORT, sonst das Instrument des Laufs; die Migration fasst nur leere Zeilen an. Nachweis ueber den ECHTEN Schreibweg (felder + schreibe_signal), Mutationstest: ohne die Korrektur 7 von 17 Pruefungen rot. Topf und Cooldown (Spalte `hebel`) unveraendert

- Quelle: signal_abbildung.felder_aus_entscheidung · NB-Sicherung 11.09. · Paket Aggregat-Deckel

**2.380-akku-schalter** — ⚠️⚠️ KORREKTUR EINES PLANPUNKTS (Nutzerfund 11.09. an der GUI): der Akkumulationsschalter steht fuer BTC, ETH und SOL SEIT LANGEM auf An. `db.get_dca_erlaubt()` liefert ohne Tabellenzeile die Vorgabe {BTC, ETH, SOL}; GUI, `handelsauftrag.strategie_fuer` und `assetklassen._schalter` lesen darueber - richtig. NUR die L1-Pruefung in `soll_ist.py` las die TABELLE (`WHERE dca_erlaubt=1`), und dort steht am NB nur BTC als Zeile. Daraus entstanden der Planpunkt ,ETH und SOL erst mit Paket 2 setzen' und meine Aussage ,am NB nur BTC' - beide falsch. ➔ L1 prueft ueber `get_dca_erlaubt`; Lage, Schritt 24 und 27 berichtigt

- Quelle: database/db.get_dca_erlaubt · soll_ist.py L1 · NB-Sicherung 11.09.

**2.379** — ✔✔✔ H-4 GEBAUT - DIE HEBELFUEHRUNG (`agent/hebelfuehrung.py`). Jede OFFENE Position aus `hebel_positions` (echter Bitpanda-Abgleich) wird mit ihrem Plan verbunden: dem juengsten Rollen-Hebelsignal desselben Symbols und derselben Richtung bis 3 Tage vor der Eroeffnung (gesetzt, nicht gemessen - Signalnummer steht in der Mail). Gefuehrt: Einstand, Tage, Ergebnis vor und nach Finanzierung, Finanzierung bisher und je Tag (Staffel aus `backward_tracking`), Liquidationspreis mit den echten Tagen, der Plan ueber `ausstiegsrechnung.bewerte()`. Empfehlungen nach Dringlichkeit: LIQUIDATION ERREICHT · SCHLIESSEN · HEBEL SENKEN (mit Nachschuss) · KURS FEHLT · STOP NACHZIEHEN · HALTEN. Eigene Mail aus dem Rollen-Lauf, einmal je Zustand und Tag, vermerkt erst NACH dem Versand; die Zeilen stehen zusaetzlich in der Verkaufsmail. Finanzierung = Information, kein Ausloeser (Regel 2); HEBEL SENKEN ist RM-11, keine Bewertung. Nachweis: Paket Hebelfuehrung 31 Pruefungen, Faelle von Hand gerechnet; E2E an der NB-Kopie mit kuenstlicher Position (LINK 5x, Stop 11,5 %%: Tag 1,5 HALTEN bis Tag 3,0 - Tag 3,5 HEBEL SENKEN, Nachschuss 0,48 EUR); `simuliere_kette` bringt die Hebelmail an

- Quelle: agent/hebelfuehrung.py · pruefe_pakete --paket Hebelfuehrung · h4_e2e / simuliere_kette 11.09.

**2.379-rm11** — ⚠️⚠️⚠️ RM-11 WAR FALSCH - bei JEDEM erlaubten Hebel lag die geschaetzte Liquidation VOR dem Stop. `max_safe_hebel` rechnete `(1 - Marge) / Stop` aus der Zeit, als die Marge ein Puffer auf 1/Hebel war (0,175). Am 16.07. bekam dieselbe Zahl in `estimate_liquidation_price` die Bedeutung Wartungsmarge (am echten LINK-Fall kalibriert), am 19.07. wurde sie 0,09 - `max_safe_hebel` wurde nicht nachgezogen. REPRODUZIERT mit den echten Funktionen: Stop 5 %% -> 18,20x erlaubt, Liquidation 3,85 %% UEBER dem Einstieg; 11,7 %% (Betriebsmedian) -> 7,78x, Liquidation 4,24 %% unter dem Einstieg; 16,4 %% -> 5,55x / 9,91 %%; 25 %% -> 3,64x / 20,30 %%. Richtig (Liquidation und Stop gleichgesetzt): 7,38 · 5,09 · 4,18 · 3,15x. Die Pruefung, die das finden sollte, verglich `rechne()` mit `max_safe_hebel()` - die Funktion mit sich selbst. ➔ neu hergeleitet fuer LONG und SHORT, mit Haltetagen; geprueft gegen die EIGENSCHAFT (294 Faelle, Abweichung 2,8e-14). Betrifft auch die alte Kette (`pre_check_hebel`, RM-11 exakt)

- Quelle: hebel_risk_gate.max_safe_hebel · h4_sichtung / h4_pruefung 11.09.

**2.379-liq** — ⚠️⚠️ ZWEI WEITERE STELLEN MIT 1/HEBEL. (1) `rechne()` schrieb `liquidation_etwa_eur = Kurs x (1 - 1/Hebel)` - bei 5x 20 %% unter dem Einstieg, kalibriert 12,1 %%; dazu auf 2 Stellen gerundet, bei Werten um 0,05 EUR wertlos. Jetzt `estimate_liquidation_price` Tag 0, 6 Stellen, und der Rechnungssatz nennt, bis zu welchem Tag die Liquidation hinter dem Stop bleibt. (2) Der Faktentext fuer Rolle BC (`lagebeschreibung._hebelgeometrie`) nannte bei 3/6/10-fach 33/17/10 %% - richtig 27/8/1 %%, beim Hoechsthebel neunmal zu weit. Ein Fakt, den das Modell liest: Prompt-Stand 2026-09-11a. Die Pruefung dazu testete die Identitaet 1-(1-1/h) = 1/h

- Quelle: entscheidungsrechnung.rechne · lagebeschreibung · rolle_trader.PROMPT_STAND

**2.379-instrument** — ⚠️⚠️ DIE AUSSTIEGSFUEHRUNG HAETTE JEDES HEBELSIGNAL DER ROLLEN-KETTE ALS SPOT GEFUEHRT. `compute_ausstiegs_empfehlungen` setzte `ist_hebel` nach der TABELLE (`hebel_signals`); die Rollen-Kette schreibt nach `signals` mit der Spalte `instrument`. Folge: Fuehrung unter (Symbol, spot), gegen den Spotbestand geprueft, und `_fuehrung_zu(..., hebel)` fand nie etwas. Am NB unsichtbar: 0 von 3.859 Zeilen der Rollen-Kette tragen instrument hebel. ➔ die Zeile entscheidet, in beiden Schleifen. E2E an der NB-Kopie: das kuenstliche Signal steht als Hebel UND Bestand; die neun Spotsignale von LINK bleiben Spot (ihre zwei SCHLIESSEN standen schon vorher)

- Quelle: backward_tracking.compute_ausstiegs_empfehlungen · h4_e2e 11.09.

**2.379-schalter** — ⚠️⚠️ `hebel_screening.aktiv: false` HAETTE DIE ROLLEN-KETTE ABGESCHALTET. Der Schalter stand vor einem `return True` am Anfang von `hebel_screening_job` - dahinter liegen der Abgleich der echten Hebelpositionen und der Umlauf der Rollen-Kette. Genau dieser Schalter liegt nahe, wenn die alte Kette beim Rollout stillgelegt wird (offene Frage 2.369): keine Urteile, keine Mails, keine Meldung. ➔ er legt nur noch das Screening still

- Quelle: scheduler/background.hebel_screening_job

**2.378-korrektur** — ⚠️ KORREKTUR ZU 2.378, nach 2.379-rm11 reproduziert (R-R11): ,Liquidationsabstand greift nie' gilt bei 9.942 und 18.213 EUR UNVERAENDERT - dort begrenzt das Kapital den Hebel, bevor RM-11 erreicht wird; alle Zahlen bei 18.213 EUR bitgleich. Bei 30.000 EUR greift das korrigierte RM-11 in 6,4 %% aller Durchgelassenen (Watchlist 2026: 3,7 %%); die Grenze 5x sinkt dort von 19,0 auf 16,0 %% (Watchlist 29,6 auf 26,9 %%). Der Hebelanteil bleibt 79,8 %%

- Quelle: h4_hebelverteilung_voll/_2026/_2026_watchlist.log 11.09.

**2.378** — ✔✔ H-3 - WAS r(q) TUT, UEBER ECHTE ANKER SIMULIERT (`simuliere_hebelverteilung.py`, Standardwerkzeug mit Schaltern). Messmenge V1, 633.672 Anker 2019-2026, 536 Symbole; Bewertung, Stop und Hebel ueber die ECHTEN Funktionen. Durch die Bewertungsschwelle: 113.224 (17,9 %%). BEI 18.213 EUR KAPITAL: Spot 56,3 %% · Hebel 43,7 %% (2x 24,2 · 3x 9,7 · 4x 4,4 · Grenze 5x 5,3 %%); Liquidationsabstand greift NIE. Nach Beitragslage: nur funding 34,0 %% Hebel · funding+turnover 93,6 %% (28,1 %% an der 5x-Grenze) · nur turnover 91,6 %%. Kapital 9.942 EUR: 12,1 %% Hebel; 30.000 EUR: 79,8 %% (19,0 %% an der Grenze). Risiko je Hebeltrade Median 178 EUR bei 18.213 EUR. Ab 2026: Spot 54,0 %% · Hebel 46,0 %%; in der Auswahlmenge (oberste 20 %%) 62,6 %%. NUR WATCHLIST 2026: 39 Werte, 8.606 Anker, 3.694 durch die Schwelle (42,9 %%); Spot 41,6 %% · Hebel 58,4 %% (2x 28,3 · 3x 13,2 · 4x 7,1 · Grenze 5x 9,8 %%); Stop Median 13,7 %% - naeher am Betrieb (11,7 %%); in der Auswahlmenge 77,3 %% Hebel

- Quelle: simuliere_hebelverteilung.py · Laeufe 11.09.

**2.378-stop** — ⚠️⚠️ EIN IRRTUM IM ERSTEN ENTWURF - vom Vorabtest gefangen, nicht vom Lauf. Das Werkzeug rechnete zuerst OHNE Widerlegungspreis und nahm an, er koenne den Stop nur weiter machen. FALSCH: `_stop_abstand` nimmt den Rueckfall 2,5 x ATR nur ohne Widerlegungspreis; mit ihm gilt der Rauschboden max(2 x ATR, 5 %%), der Stop wird ENGER. Am Notebook nennt das Modell ihn in 1.425 von 1.427 Einstiegen. Der Vorabtest ergab Stops um 20 %% gegen echte 7,6 %% - der Abgleich mit den NB-Signalen hat den Fehler gezeigt. Jetzt: Betriebsfall mit Widerlegungspreis im Rauschen, der Fall ohne als Empfindlichkeit

- Quelle: Vorabtest 11.09. · NB-Sicherung 11.09.

**2.378-gegenpruefung** — ✔ GEGENPRUEFUNG, im Werkzeug eingebaut und in jedem Lauf bestanden: G1 Hebel unabhaengig nachgerechnet (2.000 Anker x 3 Kapitalstufen, 0 Abweichungen) · G2 Rohhebel linear im Kapital · G3 mehr Kapital nie weniger Hebel · G4 ATR identisch mit `rollen_eingabe.atr_bis` · G5 Quote je Beitragslage = direkte Bewertung · G6 Stop = `rechne()` mit und ohne Widerlegungspreis. DAZU UNABHAENGIG: die Stopregel des NEUEN Codes auf 1.289 echte NB-Einstiege angewandt, mit deren Widerlegungspreis - Median 11,7 %% (10 %% 5,9 · 90 %% 16,0); ohne Widerlegungspreis 14,6 %%; alter Code am NB 7,7 %%

- Quelle: simuliere_hebelverteilung.py G1-G6 · NB-Sicherung

**2.378-deutung** — ⚠️⚠️ WAS DIE ZAHLEN FUER DAS SCHARFSCHALTEN HEISSEN: (1) die Regel verhaelt sich wie gebaut - Spot, wo die Quote nichts hergibt; Hebel, wo Beitraege tragen; die Grenzen greifen. (2) Die HISTORISCHEN Stops (Median 16,4 %%) sind WEITER als die zu erwartenden des Betriebs (11,7 %%) - im Betrieb entsteht also eher MEHR Hebel als simuliert. (3) Der Hebel haengt stark am KAPITAL (12 %% -> 80 %% zwischen 9.942 und 30.000 EUR) - deshalb war P-3 kein Detail. (4) Die GROBE Stufung (A9) wird sichtbar: wo beide Beitraege vorliegen, landet fast jeder Fall ueber 2x und ein grosser Teil an der Grenze. (5) Ob hoeherer Hebel haeufiger traegt, zeigt die Simulation NICHT (A1). ➔ EMPFEHLUNG: den Schalter erst mit Positionsfuehrung (H-4), Aggregat-Deckel (H-5) und dem E2E-Nachweis (Schritt 23) einschalten - also mit dem Rollout von Paket B, nicht jetzt

- Quelle: Befund 2.378 · Nutzerentscheidung offen

**2.377** — ✔✔✔ H-2 GEBAUT - DER HEBEL ENTSTEHT AUS DER WAHRSCHEINLICHKEIT, wie beauftragt (28.08./05.09./11.09.). `betraege.hebelrechnung`: Risiko = r(q) x Kapital, r(q) = halbes Kelly geklammert 0,50-1,25 %% (N-39); Positionswert = Risiko / Stop; Hebel = Positionswert / 500 EUR. Unter 2x SPOT mit unveraendertem Betrag (N-38); harte Grenze 5x bis zur Trennschaerfe; ohne positive Erwartung (Kelly <= 0) KEIN Hebel, auch nicht die Untergrenze. In der Kette: die Quote wird VOR der Vorabrechnung bestimmt, das Etikett aus r(q) steuert taktische Zelle, Hebel-Schalter und Topf; `rechne()` bekommt Risiko, Einsatz und Grenze. Ohne Kapital oder Quote: kein Hebel, Satz in der Mail, einmal je Lauf im Log. Die Herleitung steht in EUR im Abschnitt DIE RECHNUNG. ⚠️ Schalter `rollen_kette.hebel_aus_quote.aktiv` steht AUS - Schritt 19 simuliert die Hebelverteilung vor dem Scharfschalten

- Quelle: agent/betraege.py · agent/rollen_lauf.py · agent/entscheidungsrechnung.py · config.yaml

**2.377-gegenpruefung** — ⚠️⚠️ DIE GEGENPRUEFUNG HAT EINEN ECHTEN FEHLER IM ERSTEN EINBAU GEFUNDEN. Das Etikett kam aus dem Stop von `dimensioniere` - der kennt die Zielweite 2,5 x ATR nicht. In 20 von 144 Rasterfaellen setzte `rechne()` den Stop weiter (10 statt 8 %%, 20 statt 16 %%), und aus ,Hebel 2,0x' im Etikett wurde 1,6x in der Rechnung - unter der Grenze, ab der es ueberhaupt ein Hebel ist. Dazu deckelt `rechne()` auf den Liquidationsabstand. ➔ Neu: `entscheidungsrechnung.stop_relativ()` und `hebel_sicher()` - dieselbe Stelle, die `rechne()` benutzt; `hebelrechnung` rechnet die Liquidationsgrenze mit. Nachweis: 400 Zufallsfaelle durch BEIDE echten Funktionen, Stop und Etikett und Hebel identisch. Die Formel selbst: 2.000 Zufallsfaelle unabhaengig nachgerechnet, 0 Abweichungen. ✔ KETTE gegen die NB-Kopie, Schalter nur im Speicher an: 1 Signal, 1 Mail, 0 Fehler, keine Quotenabweichung; ONDO-Mail: ,Trefferquote 34,6 %% ... halbes Kelly 0,97 %% ... = 97 EUR' und ,bei 11,9 %% Stop: 813 EUR Positionswert / 500 EUR Einsatz = 1,6x - unter 2,0x, daher Spot mit dem gewohnten Betrag', darunter der Kapitalhinweis (10 Tage alt)

- Quelle: Gegenpruefung 11.09. · pruefe_pakete --paket ,Hebel aus Quote'

**2.377-grenzen** — ⚠️ WAS H-2 NICHT LEISTET, benannt: (1) die TRENNSCHAERFE (steigt die reale Trefferquote mit dem Hebel?) ist weiter ungemessen - A1; bis dahin begrenzen Klammer und 5x. (2) Die Stufung der Quote bleibt grob (Fuenftel, A9). (3) Der Hebel wird auf 0,1x gerundet; das Risiko am Stop kann dadurch um wenige Euro ueber r(q) liegen (gemessen hoechstens rund 1 %%). (4) Der Faktentext der Lagebeschreibung sagt noch ,Welcher Faktor es wird, folgt aus dem Risikobudget und dem gewaehlten Stopabstand' - mit Schalter stimmt das nur halb. Er geht auch an das Modell; geaendert wird er deshalb nicht nebenbei, sondern in Schritt 22 (Mail) mit Blick auf den Prompt. (5) Ein Hebelgeschaeft ist in der Kette noch nicht end-to-end simuliert - Schritt 23. (6) Bei SPOT stehen jetzt zwei Risikozahlen untereinander: 97 EUR aus der Hebelrechnung und ,Am Stop verlieren Sie 95 EUR' aus dem Spot-Betrag - Feinschliff in Schritt 22

- Quelle: Befund 2.377 · A1/A9 · Schritt 22/23

**2.377-pruefung** — ✔ EINE BESTEHENDE PRUEFUNG WURDE BEWUSST ANGEPASST, nicht umgangen: ,beide Rechnungen fragen die Strategie' zaehlte `_HA_HEBEL_OK(strategie)` und erwartete 2. Seit H-2 fragt auch die Hebelrechnung - sonst rechnete sie fuer eine Akkumulation einen Hebel, den beide Rechnungen danach verweigern. Erwartet sind jetzt 3, mit Begruendung

- Quelle: pruefe_pakete Paket ,Zellen'

**2.376** — ✔✔✔ H-1 GEBAUT - DAS KAPITAL IST LESBAR, VOLLSTAENDIG UND UEBERWACHT. (1) P-3 Option A (Nutzerentscheidung 11.09.): `schreibe_tageswert` zaehlt `quantity + staked_quantity`. (2) FORTSCHREIBUNG: ein fehlender Tageskurs wird hoechstens VIER Tage durch den letzten bekannten Schlusskurs ersetzt und im Log genannt; die 80-%%-Wache bleibt und zaehlt danach. (3) LESEPFAD `aktuelles_kapital()`: frisch bis 3 Tage, alt bis 14 (wird verwendet und genannt), darueber NICHT verwendbar - dann keine Hebelrechnung, der Trade wird Spot, mit Satz in Klartext; nie ein stiller Vorgabewert (P-2). (4) UEBERWACHUNG: Quelle `kapital` (Rolle K) in `datenfrische`, Grenze 3 Tage. Zwoelf Pruefungen im neuen Paket ,Kapital', alle durch die echten Funktionen

- Quelle: agent/portfolio_historie.py · agent/datenfrische.py · pruefe_pakete --paket Kapital

**2.376-nb** — ✔✔ GEGEN DIE NB-SICHERUNG (Kopie) NACHGEWIESEN: vorher ,Kapital 9.942 EUR - Stand 01.09., 10 Tage alt, 6 von 32 Werten ohne Kurs'. Nachgerechnet 02.09. bis 10.09.: JEDER Tag geschrieben, Abdeckung 100 %%, 0 ohne Kurs; fortgeschrieben wurden nur Boersentitel (am Wochenende 12, werktags 5 bis 9, hoechstens 3 Tage). Kapital am 10.09.: 18.212,70 EUR ohne Cash. Der Index lief ohne Sprung weiter (01.09. 95,578 -> 02.09. 95,431), obwohl der Wert von 9.942 auf 17.610 EUR stieg - 2.375-index ist damit am echten Bestand bestaetigt. ✔ GEGENPRUEFUNG: unabhaengig per SQL nachgerechnet (juengster EUR-Kurs, sonst USD x EUR/USD des Stichtags, EURCV = 1): 18.212,22 gegen 18.212,70 EUR - 0,48 EUR (0,003 %%) Abweichung, in keiner Rechnung fehlt ein Posten. Die Ursache ist NICHT einzeln aufgeschluesselt; vermutet wird der Wechselkurs bei fortgeschriebenen USD-Kursen (Kette: Kurstag, Nachrechnung: Stichtag)

- Quelle: pruefe_kapital_nb.py (Scratchpad) · NB-Sicherung 11.09.

**2.376-korrektur** — ⚠️ ZWEI MEINER AUSSAGEN IN 2.375 WAREN FALSCH - die Diagnose je Tag hat sie widerlegt: EURCV hat nicht ,keinen Kurs', es ist ein Cash-Aequivalent und zaehlt mit 1,00 EUR; KAIA, SUPRA und BRETT haben EUR-Kurse aus `price_history`, nicht nur USD. Ich hatte nur `price_history_ohlc` abgefragt - die Tabelle, die `_eur_kurse_je_symbol` ausdruecklich als EINE von ZWEI Quellen fuehrt. Die echten Luecken waren ausschliesslich BOERSENTITEL (Wochenende, ein bis drei Tage Nachlauf). Die vorgeschlagene USD-Umrechnung war deshalb unnoetig und ist nicht gebaut

- Quelle: Diagnose 11.09. · agent/portfolio_historie._eur_kurse_je_symbol

**2.376-rollout** — ⚠️ FUER DEN ROLLOUT: am Notebook fehlen Zeilen 02.09. bis zum Rollout. Der Job schreibt danach nur den Vortag - das Kapital ist damit ab dem ersten Morgen frisch, die LUECKE im Verlauf bleibt aber. Einmal nachrechnen mit `schreibe_tageswert(datum=...)` je Tag, sonst meldet die Frischepruefung am Rollout-Tag ,kapital: abruf', bis der erste Lauf geschrieben hat

- Quelle: Rollout-Checkliste

**2.376-log** — ⚠️ UND EIN LOGFEHLER: an verworfenen Tagen formatierte `portfolio_wert_job` `%%.2f` auf None - ein ,Logging error' statt einer Aussage. Die Zeile steht jetzt nur, wenn geschrieben wurde, und nennt die Zahl der fortgeschriebenen Kurse

- Quelle: scheduler/background.portfolio_wert_job

**2.375** — ⚠️⚠️⚠️ H-1 VOR DEM BAU: DAS KAPITAL IST NICHT VERWENDBAR, WIE ES HEUTE GESCHRIEBEN WIRD - zwei Befunde am Notebook (Sicherung 11.09.). (1) ES FEHLT DAS GESTAKTE: `schreibe_tageswert` zaehlt nur `quantity > 0`, nicht `staked_quantity`. Neun Werte liegen NUR gestaked (SOL, TAO, SUI, NEAR, AVAX, HYPE, SEI, BNB, VSN), ETH zu 97 %%. Rund 6.093 EUR fehlen - bei 9.942 EUR ausgewiesenem Wert rund 38 %% des Kapitals ohne Cash. Das ist P-3 (offene Nutzerentscheidung seit 10.09.). (2) ES WIRD SELTEN GESCHRIEBEN: juengste Zeile 01.09., davor 26.08. und 20.08. Der Job LAEUFT (`job_laeufe` 11.09.), verwirft aber die meisten Tage an der Abdeckungswache (80 %%): im Log 62 %% und 75 %%. Ursachen: ETF/ETC ohne Wochenendkurs (CEBS, DBPK, EXH3, VVMX, ISOC), Werte nur mit USD-Reihe (KAIA, SUPRA, BRETT, VST), vier Rohstoff-ETC mit USD-Reihe bis 07.09., EURCV (Stablecoin) ohne Kurs seit 07.08.

- Quelle: NB-Sicherung 11.09. · NB-Log 31.08./01.09./02.09. · agent/portfolio_historie.schreibe_tageswert

**2.375-index** — ✔ WARUM DIE REPARATUR VON P-3 DEN INDEX NICHT SPRINGEN LAESST - und P-3 damit kleiner ist, als seine Begruendung sagt. `index_wert` wird MENGENKONSTANT aus den Mengen des VORTAGS gerechnet (`mengen_json` der Vorzeile, beide Kurse gegen dieselbe Menge). Kommt das Gestakte hinzu, rechnet der erste Tag noch mit der alten Menge, jeder weitere mit der neuen - der Index bekommt keinen Sprung, Z-3 (Drawdown) ist nicht betroffen. Springen wuerde nur `wert_eur`, EINMAL, und genau das ist die Korrektur

- Quelle: agent/portfolio_historie.schreibe_tageswert Z. 1025-1035

**2.375-notify** — ⚠️ UND EIN FEHLER IM FEHLERZWEIG: `portfolio_wert_job` rief `_notify_job_failure` mit EINEM statt zwei Argumenten - der Aufruf warf selbst einen TypeError, die Meldung kam nie an. Behoben, mit Dauerpruefung ueber ALLE Aufrufe

- Quelle: scheduler/background.portfolio_wert_job

**2.374** — ⚠️⚠️⚠️ NUTZERENTSCHEIDUNG 11.09. - PAKET B, UND WARUM DER FRUEHERE PLAN FALSCH WAR. Nutzer: ,meine Prioritaet liegt bei 1 Hebel 2 Spot 3 Akkumulation - zumindest Hebel und Spot muessen sauber funktionieren' und ,ja Paket B, Deckel 5x, Rest wie empfohlen'. Mein Plan stellte den Rollout VOR Hebel und Akkumulation, obwohl die Vorgabe KRYPTO-ZUERST Krypto GESAMT meint und beide Luecken dokumentiert waren (2.174-ist seit 08.09.: ,die Nutzervorgabe ist damit NICHT umgesetzt'; null Beitraege der Akkumulation) - sie waren nur nicht als Showstopper benannt. PAKET B: Akkumulation gesperrt, Portfoliowert, r(q), Hebelverteilung simulieren, Positionsfuehrung Hebel, Aggregat-Deckel 3 %%, Spot sauber, E2E, Rollout. PAKET 2: Akkumulation messen und bauen. Schaetzung rund 7 und 4-5 Arbeitstage, plus/minus 50 %%

- Quelle: Nutzerentscheidung 11.09.2026 · soll_ist Vorgabe PAKET-B

**2.374-rq** — ⚠️⚠️ MEINE EMPFEHLUNG ,r(q) als EINE Regel fuer Spot und Hebel' (11.09.) WAR FALSCH und ist zurueckgezogen. Sie widerspricht der dokumentierten Entscheidung N-38 vom 05.09.: ,Damit trifft der Umbau genau die Hebelseite. Spot bleibt unberuehrt, ohne dass zwei Regeln gebaut werden muessen.' Gefunden erst durch die Recherche auf Nutzerhinweis (,mir fehlt die Info zur Entscheidung'). Der Zirkelbezug aus `config.yaml` (ein Verlustanteil fuer beide) loest sich ueber die Reihenfolge: zuerst die Hebelrechnung, unter 2x Spot mit unveraendertem Betrag

- Quelle: Anforderungen_Umbau_28_08.md N-38 (Z. 2776, 2900-2926) · Recherche 11.09.

**2.374-akku** — ⚠️⚠️ DIE AKKUMULATION IST GESPERRT (Paket B) - und das kehrt einen GEWOLLTEN Zustand um. Die Pruefung ,Kette je Strategie' hielt seit 07.09. ,AKKUMULATION: sie WINKT DURCH, sie sperrt nicht' als Absicht fest, begruendet mit Regel 4. Die Folge (2.370): ueber einen Nachkauf entschied allein das Sprachmodell der Rolle Haendler (Gemini Flash-Lite, Ausweich OpenRouter und Groq). Seit 11.09.: `Potential.lage_gesperrt`, geprueft VOR der Notiz ,nicht vermessen', mit Grund im Trichter; der Einstieg ist unberuehrt; drei neue Pruefungen

- Quelle: agent/potential.py · agent/rollen_lauf.py · pruefe_pakete Kette je Strategie

**2.374-messen** — ✔ EXPERTENURTEIL ZUR NUTZERFRAGE ,alle Messungen fuer Krypto vor dem Umbau?' (11.09.): NEIN, gezielt. ,Messen vor Bauen' gilt fuer BEWERTUNGSBEITRAEGE - deshalb ist das Messpaket Schritt 1 von Paket 2. `r(q)` ist KEIN neuer Beitrag, es verteilt Risiko auf den registrierten Beitraegen. Die fehlende Hebelmessung (steigt die reale Trefferquote mit dem Hebel?) haengt an A1, dauert Wochen und aendert nicht, WAS Paket B baut; bis dahin begrenzen die Klammer 0,50-1,25 %% und die 5x-Grenze. ERGAENZT: vor dem Scharfschalten die Hebelverteilung simulieren (Schritt H-3, Nutzervorgabe 28.08.: ,vorher pruefen und simulieren')

- Quelle: Expertenurteil 11.09.2026

**2.373** — ⚠️ SICHTUNG DER LETZTEN TAGE (Nutzerauftrag 11.09.). Verifiziert und behoben: 2.367 und 2.368. Verifiziert offen: die Rollout-Checkliste nennt noch 2048 Pruefungen und drei Rote (heute 2084 und vier); der alte Marktscan ist in der `config.yaml` des Desktops aktiv (2.369). GEMELDET, noch einzeln zu pruefen: `config.yaml` wird am Notebook ueber die GUI geaendert - vor dem Pull abgleichen · K-6/K-7 fehlen in Schritt 29 · die O-Liste vom 05.09. (O1 Cooldown, O3 Mindeststop, O6, O7) steht nicht im Plan · L4 Short, D-2 CANTON, V3/V4/V6/V10/N17 ohne Schritt · A7 (das Kalibrierwerkzeug kennt nur funding und turnover) · `messdaten.db` fehlt am Notebook, `schnitt` liest daraus

- Quelle: Sichtung 11.09. (Protokoll, soll_ist, Gesamtplan, Register)

**2.372** — ⚠️⚠️ DIE ONDO-MAIL, GEGLIEDERT, ZEIGT FUENF DOPPELUNGEN (Nutzerhinweis 11.09.: ,der Text erschlaegt einen'): (1) dieselbe Kursmarke dreimal, in zwei Einheiten; (2) ZWEI Trefferquoten - 34,6 %% (die Bewertung, nach der entschieden wird) und 34 -> 32 von 100 (die aeltere Erfahrungsrate in EINORDNUNG), dazu zweimal ,noetig' (41,7 %% und 42); (3) die Gebuehren dreimal; (4) drei Rangangaben (1 von 3, 12 von 41, Platz 2/3/3); (5) Liquidationsabstaende in einer Spot-Mail mit Hebel 1,0. Vorschlag: Kopf ,Auf einen Blick' und ,Was dagegen spricht', sechs Abschnitte, Anhang - nichts gestrichen

- Quelle: krypto_spot_ONDO.txt · Mailgliederung_Vorschlag_ONDO

**2.371** — ⚠️⚠️ HEBEL IST KEINE EIGENE LAGE, SONDERN EIN ERGEBNIS DER RECHNUNG - und end-to-end nie nachgewiesen. Krypto laeuft nur als `spot` (`INSTRUMENTE_JE_GRUPPE`); ein Hebelgeschaeft entsteht, wenn Risikobudget und Stopabstand einen Faktor ueber 1,0 ergeben, gedeckelt durch Liquidationsabstand und Hoechsthebel. Die HOEHE kommt aus der Geometrie, NICHT aus der Bewertung (A9/A1/P-1 offen). ⚠️ In keiner Simulation von Schritt 15 entstand ein Signal mit Faktor ueber 1,0 - Mail und Signalzeile eines Hebelgeschaefts sind nicht nachgewiesen. ⚠️ Am Notebook (alter Code): `hebel_signals` endet am 10.08.; seit dem 14.08. traegt KEIN Signal instrument ,hebel', aber 974 Rollen-Signale haben einen Faktor 1,1 bis 10,0 und stehen als ,spot' (971) oder ohne Instrument (3)

- Quelle: agent/assetklassen.py · entscheidungsrechnung · NB-Sicherung 11.09.

**2.370** — ⚠️⚠️⚠️ DIE AKKUMULATION LAEUFT HEUTE OHNE BEWERTUNG DURCH - am Verhalten geprueft: `potential.rechne(strategie=,akkumulation')` liefert vermessen=False und getragen_von=0. Stufe 11 ZAEHLT dann nur und sperrt nicht (Regel 4: nicht nach Datenlage sperren). Folge nach dem Rollout: jede Akkumulationszelle (am Notebook BTC, nach dem GUI-Schalter auch ETH und SOL) entscheidet allein das Modellurteil. ⚠️ Am Notebook gab es bisher KEIN Signal mit Strategie akkumulation, und `dca_erlaubt` steht dort NUR fuer BTC (am Desktop BTC und ETH). Der Zustand ist also neu, nicht alt

- Quelle: agent/potential.py · rollen_lauf Stufe 11 · NB-Sicherung 11.09.

**2.369-fg** — ⚠️ ,DER FEAR & GREED MIT DER BESTEN AUSSAGEKRAFT' IST EINE MESSFRAGE, KEINE AUSWAHL NACH BESCHREIBUNG. Kandidaten: alternative.me - NUR Bitcoin, zur Haelfte Kursdaten, Historie ab 01.02.2018 (bei uns geladen); CoinMarketCap - zehn groesste Werte ohne Stablecoins, dazu implizite Volatilitaet BTC/ETH, Put/Call-Verhaeltnis, Stablecoin-Verhaeltnis und Suchdaten, ohne Schluessel abrufbar, Historie erst ab 20.07.2023 (rund 3,1 Jahre - knapp UNTER der Blockregel 20 x 60 Tage). ⚠️ Der Nutzen haengt daran, was ein Index NEBEN unseren Beitraegen weiss: Momentum und Schwankung decken Trichter und Auswahl ab, Finanzierung und OI sind eigene Beitraege - neu waeren bei CMC nur Optionsmarkt und Stablecoin-Verhaeltnis. Gehoert in R-1/R-3

- Quelle: alternative.me · CMC public-api v3/fear-and-greed/historical (abgefragt 11.09.)

**2.369** — ✔ WOHER DAS REGIME KOMMT UND WO ES WIRKT - aus dem Code gelesen (Nutzerfrage 11.09.). QUELLE: `regime.determine_regime`, gerufen NUR im alten `marktscan_job` (04:00 und 16:00): BTC gegen EMA20/50/200, 30-Tage-Aenderung, Fear & Greed von alternative.me, dazu Liquiditaets-Regime und Zyklus-Risiko. WIRKUNG: nur im ALTEN Marktscan (Kontext-Score, Gewichtsprofil je Regime, Small-Cap-Budget) und als Anzeige (Uebersichtsseite, GUI-Tab). In der ROLLENKETTE: KEINE - nicht in der Bewertung, seit 16.08. nicht im Faktensatz, nicht in der Signalzeile (2.361), nicht in der Mail. Fear & Greed selbst geht nur als Perzentil ohne Etikett in Rolle A. ⚠️ Der alte Marktscan ist in der `config.yaml` des Desktops weiter aktiv und verschickt eigene Mails

- Quelle: agent/krypto/regime.py · background.marktscan_job · config.yaml marktscan.aktiv

**2.368** — ⚠️⚠️⚠️ S-1 HAETTE AM NOTEBOOK AB DEM ERSTEN LAUF ALARM GESCHLAGEN - eigener Baufehler, gefunden bei der Sichtung. Zwei Gruende: (1) am Notebook liegen die drei Messquellen nur als SYMBOLLISTE ohne Datum (`baue_messbasis_paket.py`, Tabelle `_nur_symbolliste`) -> ,fehlt'; (2) die Zwei-Tage-Grenze fuer den Abruf galt auch fuer die von Hand geladene Messbasis -> ,abruf' nach 48 Stunden; am Desktop standen alle drei tatsaechlich darauf. Keine Pruefung sah es, weil alle mit `mit_dateien=False` oder kuenstlichen Urteilen liefen. ➔ Die Symbolliste bekommt das Urteil ,liste' (nicht auffaellig, leer bleibt sie ,fehlt'); Rolle M nutzt ihre eigene Obergrenze von 21 Tagen auch fuer den Abruf; Quellen mit Job bleiben bei zwei Tagen. Fuenf Pruefungen mit ECHTEN Dateien durch die echte `pruefe()`. Desktop jetzt: alle drei ,frisch'

- Quelle: agent/datenfrische.py · pruefe_pakete.py

**2.367** — ⚠️⚠️ DER CHART IN DER MAIL HATTE EINEN EIGENEN, ZWEITEN ZAHLENWEG - Nutzerhinweis 11.09. (,das eMail generiert auch einen Chart - nicht vergessen und pruefen'). Die Simulation baute das Bild, legte es aber nie ab; Schritt 15 hat es damit nicht geprueft. Abgelegt und angesehen: (1) an allen sechs Marken stand ,0' - `f'{wert:,.0f}'` bei ONDO 0,32 EUR, derselbe Fehler wie PLUME am 14.08. im Mailtext; (2) die Preisachse schrieb englisch ,0.38'. Beide behoben (`trade_chart.marke_text` ueber `signal_mail.preis`, `achse` mit Tausenderpunkt und ohne Exponentenschreibweise), drei Dauerpruefungen. Nachweis im neu abgelegten Bild: ,0,3372 5x', Achse ,0,38'

- Quelle: ui/trade_chart.py · simuliere_kette.py

**2.366** — ✔✔✔ DIE HEUTIGEN MAILAENDERUNGEN SIND IN EINER FERTIGEN KRYPTO-MAIL NACHGEWIESEN - nicht nur in Pruefungen. ONDO, gegen die NB-Sicherung, abgelegt unter %%TEMP%%/simuliere_kette_mails: ,Ausgangspunkt: Ziel 2,0-mal so weit wie der Stop' · ,+ Funding-Rang im Markt +1,3 %%' · ,✖  Standard 0,30 %%: ... 0,4 Prozentpunkte ZU WENIG (-0,011 R je Trade = −1,08 EUR)' · die Bewertungsschwelle · der Vorfilter · die Lebendigkeit. Die englischen Dezimalzahlen aus 2.363 sind in Krypto- UND Rohstoff-Mail verschwunden. ⚠️ Nicht nachweisbar in einem normalen Lauf: die S-2-Ausfallzeile (sie erscheint nur bei einem echten Abrufausfall) - dafuer stehen fuenf Dauerpruefungen

- Quelle: simuliere_kette.py · krypto_spot_ONDO.txt

**2.366-minus** — ⚠️ UND EIN SCHOENHEITSFEHLER, DEN ICH AM 11.09. SELBST EINGEBAUT HATTE und erst in der fertigen Mail sah: ,(-0,011 R je Trade = −1,08 EUR)' - Bindestrich und typografisches Minus in EINER Klammer. `_in_eur` schreibt jetzt mit `de(..., vorzeichen=True)` wie die R-Zahl davor. ⚠️ Kein Pruefpaket haette das gefunden - genau dafuer gilt der Grundsatz, dass eine Stufe erst IN DER FERTIGEN MAIL als gebaut gilt

- Quelle: agent/wahrscheinlichkeit._in_eur

**2.362** — ✔✔ SCHRITT 15 - DIE KETTE REISST NICHT, auf dem Datenstand des NOTEBOOKS: `simuliere_kette.py` lief gegen eine Kopie der NB-Sicherung vom 11.09. 04:48 - also genau gegen das alte Schema, auf das der Rollout trifft. Alle fuenf Gruppen durchlaufen, 0 Fehler. Nachgewiesen: der Zellen-Pfad (BTC mit zwei Zellen), Schritt 7 (Positionsfuehrung in der Mail), der Vorfilter-Schatten. Und im gezielten Lauf die erste KRYPTO-Mail end-to-end (ONDO: Trichter vollstaendig, heraus 1)

- Quelle: simuliere_kette.py gegen NB-Sicherung 2026-09-11

**2.362-krypto** — ⚠️ WARUM DER ERSTE LAUF KEINE KRYPTO-MAIL LIEFERTE - und alle Verwerfungen waren richtig: (1) die Simulation nahm die ersten fuenf Werte mit Kursreihe; der einzige Ueberlebende hatte Potential −0,016 R gegen die Schwelle 0,023 R seiner Datenlage. (2) Mit live tragenden Werten (BNB, SEI) verwarf die Kette KAUFEN, weil beide im Bestand sind und die Positionsfuehrung SCHLIESSEN sagt. (3) Die Attrappe gibt die Aktionen REIHUM aus - eine Einstiegsmail entsteht nur, wenn KAUFEN auf einen Wert ohne Bestand faellt. ➔ Mit RENDER/ONDO/KAITO (ohne Bestand, live ueber der Schwelle) kam sie

- Quelle: gate_durchlaessigkeit der Simulationskopie

**2.363** — ⚠️⚠️ ECHTER MAILFEHLER, VON DER SIMULATION GEFUNDEN: `agent/auswahl.py` formatierte an ZWEI Stellen mit `:.1f` - in einer echten Rohstoff-Mail ,Der Rohstoff-Referenzkontrakt steht 11.5 %% ueber seinem eigenen Schnitt', in der Krypto-Mail ,2.7 Prozentpunkte' und ,11.9 %%'. Die zweite Stelle traf JEDE gewaehlte Mail. ➔ Beide auf `schreibweise.de()`; dazu die Sperrbegruendung in `entscheidungsrechnung.py`, die im Trichter steht. Dauerpruefung im Paket Mail - am Verhalten, nicht am Quelltext

- Quelle: agent/auswahl.py / pruefe_pakete.py

**2.364** — ⚠️⚠️ DREI FEHLER IM WERKZEUG SELBST: (1) der Trichter wurde auf 16 Zeilen GEKAPPT - bei vielen Begruendungszeilen fielen die letzten Stufen und ,heraus' aus der Anzeige, und es sah aus wie ein stiller Verlust in der Kette. (2) Die Zahlschreibweise-Luecke nannte nur die Zahl, nicht die ZEILE - und weil der Mailtext nirgends gespeichert wurde, war sie nicht auffindbar. (3) Der Mailtext wurde nur im Speicher geprueft; ob eine Zeile WIRKLICH in der Mail steht, war nachher nicht nachsehbar. Alle drei behoben; fertige Mails liegen jetzt unter %%TEMP%%/simuliere_kette_mails. Dazu ein irrefuehrender Hinweis: `--symbole` umgeht die Vorauswahl der SIMULATION, nicht die Stufe ,beste k' der Kette

- Quelle: simuliere_kette.py

**2.365** — ⚠️ ZWEI EIGENE FEHLER BEIM AUSWERTEN, beide selbst gefunden: (1) ich meldete einen stillen Verlust in der Krypto-Kette - es war die 16-Zeilen-Kappung der Anzeige. (2) Ich meldete einen Widerspruch ,Kette haelt BNB und SEI fuer Bestand, das NB haelt sie nicht' - meine Abfrage pruefte nur `quantity > 0` und uebersah `staked_quantity` (SEI 2.711, BNB 0,159). `rollen_eingabe.bestand()` zaehlt Gestaktes seit dem 17.08. zu Recht mit. Die Kette hatte recht. ⚠️ Derselbe Fehler steckt vermutlich in meiner Zaehlung ,29 Bestaende' aus 2.346

- Quelle: Selbstbefund 11.09.2026

**2.361** — ⚠️⚠️⚠️ DIE ROLLENKETTE SCHREIBT DAS REGIME NICHT MIT: seit dem 14.08. tragen am Notebook 3.872 von 3.883 Signalen `regime = None`, `regime_source` ebenfalls leer. Davor (07.07. bis 14.08., alte Kette) trugen 2.549 Signale ausnahmslos ,baer'. Es gab damit NIE ein zweites Label in den Betriebsdaten - erst gar keines. ⚠️ Jeder Tag nach dem Rollout ohne diese Spalte fehlt spaeter fuer eine Trennung am echten Betrieb

- Quelle: NB-Sicherung 2026-09-11 · signals.regime

**2.361-verstaendnis** — ✔ DAS NUTZERVERSTAENDNIS IST BESTAETIGT, und praezisiert: *,Regime konnte fuer unsere Bewertungsgrundlagen bisher kaum sinnvoll genutzt werden.'* Der Grund ist nicht, dass Regime unwichtig waere, sondern dass es NIE ein brauchbares Regimesignal gab, gegen das man haette messen koennen. **Nicht gemessen ist nicht unwirksam** - dieselbe Klasse wie ,nicht trennbar' gegen ,traegt nicht'. Deshalb Sonderpunkt mit fuenf Arbeitspaketen (R-1 bis R-5), nicht Abschluss

- Quelle: Nutzerhinweis 11.09. / Gesamtplan Sonderpunkt Regime

**2.360** — ✔✔✔ S-3 IST GEBAUT - jeder Job hinterlaesst eine Spur. Von 21 geplanten fuehrten nur SECHS eine Zeile in `job_laeufe`, und die sechs nicht aus Ueberwachungsgruenden: `merke_joblauf` wurde fuer den NACHHOLER gebaut, und nur Jobs mit Nachholbedarf riefen sie. Fuer `refresh_prices`, `refresh_history`, `marktscan`, `hebel_screening` und elf weitere war nach einem Ausfall NICHT feststellbar, wann sie zuletzt liefen - also auch nicht, was gefehlt hat

- Quelle: scheduler/background._log_job_event

**2.360-zentral** — ✔✔ ZENTRAL STATT FUENFZEHN KOPIEN: der Ereignis-Horcher lauscht jetzt zusaetzlich auf EVENT_JOB_EXECUTED - vorher nur auf ERROR und MISSED, also blieb ein Job, der SAUBER lief, unsichtbar. ⚠️ Fuenfzehn Einzelaufrufe von Hand einzustreuen hiesse, beim naechsten neuen Job einen zu vergessen - und genau der waere dann der unsichtbare. Der Horcher sieht jeden Lauf, auch kuenftige. Das Projekt kennt die Lehre: *drei Kopien laufen garantiert auseinander*

- Quelle: scheduler/background.py

**2.360-gegenprobe** — ✔✔ VIER VERHALTEN GEGENGEPRUEFT: ein ERFOLGREICHER Lauf wird vermerkt · ein FEHLGESCHLAGENER NICHT (er ist nicht gelaufen - ihn zu vermerken hiesse, einen Ausfall als Erfolg zu buchen), die Fehlermeldung geht trotzdem raus · OHNE Verbindung stolpert der Horcher nicht (ein Listener, der wirft, stoert den Scheduler bei JEDEM Job) · und er ist auf EVENT_JOB_EXECUTED registriert. ⚠️ Die Gegenprobe wird ROT, sobald man den Zweig abschaltet

- Quelle: pruefe_pakete.py

**2.360-verhalten** — ⚠️ UND DIESMAL PRUEFT DIE PRUEFUNG DAS VERHALTEN, NICHT DEN QUELLTEXT - die Lehre von S-1 vom selben Tag: dort blieb eine Pruefung gruen, die nur nach einem Funktionsnamen im Text suchte; der Aufruf stand noch da und wurde nur nie erreicht. Hier wird der Horcher mit echten Ereignissen gerufen. ⚠️ Die vierte Pruefung (Registrierung) bleibt eine Textpruefung - und zwar bewusst: die drei darueber rufen die Funktion DIREKT und wuerden auch dann gruen bleiben, wenn niemand sie je anschliesst

- Quelle: Selbstbefund 11.09.2026

**2.358** — ✔✔✔ S-1 IST GEBAUT - die drei MESSQUELLEN sind ueberwacht. `funding_historie`, `terminmarkt_historie` und `onchain_historie` standen in KEINER Registratur - also auch nicht in der Frischepruefung, die es seit dem 17.08. gibt. Jetzt in `datenfrische.REGISTRATUR` mit eigener ROLLE ,M'. Am Desktop melden sie sofort: funding 11 Tage, terminmarkt 7, onchain 12 - Urteil ,abruf', also **unser** Fehler, nicht der des Anbieters

- Quelle: agent/datenfrische.py

**2.358-rolle** — ✔ DIE ROLLE ,M' IST DIE WICHTIGE UNTERSCHEIDUNG: A, BC und G speisen PROMPTS - faellt dort etwas aus, urteilt das Modell auf altem Stand. M speist die MESSBASIS, also die Symbolliste, gegen die gerangt wird; die laufenden WERTE kommen aus Live-Abrufen. Ein Ausfall dort blockiert KEINE Signale, macht aber jede Neumessung und Kalibrierung auf altem Stand. ⚠️ Nutzervorgabe 10.09.: *,Aenderungen duerfen die Bewertung nicht blockieren - und schon gar nicht still.'* Blockieren tut hier nichts; das Schweigen faellt weg

- Quelle: agent/datenfrische.py

**2.358-handlung** — ✔✔ UND DER HANDLUNGSBEDARF WIRD GEMELDET, nicht nur geloggt. Nutzervorgabe 11.09.: *,bei Totalausfall besteht Handlungsbedarf - wenn eine ganze Datenquelle oder Bereich ausfaellt sollte nach kritischen Meldungen klar sein dass etwas zu tun ist.'* `_melde_datenfrische` schrieb bis heute NUR ins Log. ⚠️ Eskaliert wird NUR bei ,fehlt' und ,abruf', nicht bei ,daten' - der Kopf von `datenfrische` sagt warum: *,Ein Anbieter, der nichts Neues hat, ist normal. Ein Job, der nicht laeuft, ist es nie.'* Wer auch ,daten' meldet, meldet bald nichts mehr

- Quelle: scheduler/background._melde_datenfrische

**2.358-gruppiert** — ⚠️ UND DIE MELDUNG IST NACH JOB GRUPPIERT, nicht je Quelle: die erste Fassung schrieb 18 Zeilen, und ACHT davon hatten dieselbe Ursache (`externe_reihen` laeuft nicht). **Eine Textwand macht keinen Handlungsbedarf klar, sie verdeckt ihn.** Der JOB ist die Handlungseinheit - wer liest, will wissen, was er anfassen muss. Dasselbe Prinzip wie `signal_mail.ohne_gewohntes`

- Quelle: scheduler/background.py

**2.359** — ⚠️⚠️ ZWEI EIGENE FEHLER BEIM BAUEN, BEIDE VON DER GEGENPROBE GEFANGEN: (1) meine Pruefung suchte `_notify_job_failure(` im QUELLTEXT - schaltet man die Eskalation ab, steht der Aufruf noch da und wird nur nie erreicht. Sie blieb GRUEN. **Derselbe Fehlertyp wie am selben Tag beim Bitgleichheitstest: eine Pruefung, die einen Pfad nicht laeuft, sagt ueber ihn nichts.** Jetzt wird die Funktion mit vier kuenstlichen Lagen gerufen. (2) meine Dateiquellen lesen FESTE Pfade unter `data/` und damit an `conn` vorbei - vier bestehende Pruefungen mit kuenstlicher Datenbank kippten. `mit_dateien=False` ist die ehrliche Zwischenloesung, nicht die schoene

- Quelle: Selbstbefund 11.09.2026

**2.357** — ✔✔✔ S-2 IST GEBAUT - ein Ausfall ist keine Messbasisluecke mehr. Nutzervorgabe 11.09.: *,die API Abfragen und Datensammlungen am Notebook muessen stabil umgesetzt werden, damit ein kurzer Ausfall so wie heute keinen Schaden anrichten kann.'* Faellt der Abruf aus, war das Fuenftel None und die Zeile wurde SCHLICHT WEGGELASSEN - die Mail sah normal aus, nur kuerzer, und die Bewertung war an dem Tag stumm um einen Beitrag aermer

- Quelle: agent/marktrang.py

**2.357-falsch** — ⚠️⚠️ UND BEI TOTALAUSFALL NANNTE DIE MAIL DIE FALSCHE URSACHE: ,er gehoert weder zur Funding- noch zur Umschlag- noch zur Terminmarkt-Messbasis' - auch dann, wenn schlicht das NETZ weg war. **Eine falsche Begruendung ist schlimmer als keine: sie schickt den Leser an die falsche Stelle.** Er haette die Messbasis geprueft, waehrend die Ursache im Abruf lag

- Quelle: agent/marktrang.py

**2.357-daten** — ✔ DIE UNTERSCHEIDUNG STECKTE SCHON IN DEN DATEN, sie wurde nur nicht ausgewertet: `raenge()` setzt `querschnitt_<name>` ERST nach erfolgreichem Abruf und nach der Mindestquerschnittspruefung. Also bedeutet querschnitt == 0 ,der ganze Rang ist heute ausgefallen' und querschnitt > 0 mit fehlendem Fuenftel ,dieser Wert gehoert nicht dazu'. ⚠️ Alle DREI Abbruchstellen in `raenge()` melden bereits ins Log - keine erreichte die MAIL. Genau das ist fail-soft-ist-fail-silent

- Quelle: agent/marktrang.raenge / Analyse 11.09.

**2.357-gegenprobe** — ✔✔ GEGENGEPRUEFT ueber VIER Faelle, mit fuenf Dauerpruefungen im Paket Terminmarkt: NORMAL (keine Ausfallzeile - wo nichts ausgefallen ist, darf nichts gemeldet werden, sonst stumpft die Meldung ab) · TEILAUSFALL (wird genannt UND benennt die Groesse) · MESSBASISLUECKE (bleibt, was sie war - die alte Zeile ist dort richtig) · TOTALAUSFALL (nennt den Ausfall, NICHT die Messbasis). ⚠️ Die Gegenprobe wird ROT, sobald man die Teilausfallzeile abschaltet

- Quelle: pruefe_pakete.py Paket Terminmarkt

**2.351** — ⚠️⚠️⚠️ ANALYSE DER BEWERTUNGSSCHICHT - DER SCHWERSTE FUND, und er ist REPRODUZIERT: `schwelle()` und `schwellenzeile()` ermittelten die QUELLE getrennt. Die eine nahm den Wert, die andere fragte nur, ob der Schluessel existiert. Bei `potential_schwelle_r: 0,02` - Komma statt Punkt, in einem deutschsprachigen Projekt die naheliegendste Verwechslung - liest YAML eine Zeichenkette, `float()` wirft, der Rueckfall greift: wirksam bleibt 0,080, und die Mail meldet trotzdem ,(config.yaml)'. **Der Nutzer haette geglaubt, seine Einstellung wirke**

- Quelle: agent/potential.py / Analyse 11.09.2026

**2.351-warum-schwer** — ⚠️⚠️ WARUM DAS SCHWERER WIEGT ALS EIN GEWOEHNLICHER FEHLER: es trifft genau den Parameter, zu dem der Nutzer am 07.09. sagte - *,so einen Parameter vergesse ich in Kuerze und du auch, die Doku reicht bei so einer zentralen Einstellung nicht.'* Daraufhin entstanden die Steuerbarkeit ueber `config.yaml` und die Mailzeile. **Beide Vorkehrungen waren vorhanden - und genau ihr Zusammenspiel war kaputt.** Die Schwelle entscheidet ueber die ZAHL der Empfehlungen

- Quelle: Nutzerhinweis 07.09. / Analyse 11.09.

**2.351-ursache** — ✔ DIE URSACHE IST DIE ZWEITE ERMITTLUNG, NICHT DER RUECKFALL. Der Rueckfall ist richtig - ohne ihn stuende das System bei einem Tippfehler still. Falsch war, dass niemand davon erfuhr. ➔ `schwelle_und_quelle()` liefert Wert, Quelle UND Stoerung aus EINEM Vorgang; `schwelle()` meldet die Stoerung ins Log, `schwellenzeile()` in die MAIL. Dasselbe Prinzip, das das Projekt schon kennt: *drei Kopien laufen garantiert auseinander*

- Quelle: agent/potential.py

**2.351-gegenprobe** — ✔✔ GEGENGEPRUEFT ueber VIER Faelle, und der gueltige Weg wirkt weiterhin: `0,02` (Komma) -> Code-Vorgabe + Hinweis · `zwei` -> Code-Vorgabe + Hinweis · Schluessel FEHLT -> Code-Vorgabe OHNE Hinweis (das ist der Normalfall) · `0.02` gueltig -> config.yaml, 0,020 wirkt. Acht neue Pruefungen im Paket Kalibrierung halten alle vier fest

- Quelle: pruefe_pakete.py Paket Kalibrierung

**2.352** — ✔ WAS DIE ANALYSE SONST GEFUNDEN HAT - und es spricht FUER die Schicht: das Paket Kalibrierung prueft die Schwelle bereits mit ueber 20 Zeilen (Steuerbarkeit, Mail, Alter, Stufen, R-R9). Die 13 Module ohne Aufrufer sind SAMTLICH erklaert - `remote/server` wird in `main.py:387` in einem Thread gestartet (Fehlalarm der Modulkarte durch dynamischen Import), `szenario_*` ist als Kontrollgroesse in der Pruefsuite gefuehrt, der Rest traegt GESTRICHEN oder ABGELOEST im Kopf

- Quelle: zeige_modulkarte.py --tot / Analyse 11.09.

**2.352-still** — ✔ UND DIE STILLEN AUSFAELLE SIND SORTIERT: von 14 except-Bloecken in der Bewertungsschicht melden die Betriebspfade, und die stillen liegen auf SCHATTENpfaden - `auswahl.marktzustand` sagt im eigenen Docstring *,Schatten, keine Schranke'*, ein stilles None sperrt dort nichts. Die EINE Ausnahme war die Schwelle (2.351)

- Quelle: Analyse 11.09.2026

**2.353** — ⚠️ LESBARE WERTE (Nutzervorgabe 11.09., woertlich: *,ich sollte im Text immer fuer mich lesbare und zuordenbare Werte und Textformulierungen erhalten (kein 2R), EUR Betraege, etc.'*): vier Stellen richtiggestellt - CRV ausgeschrieben (,Ziel 2,0-mal so weit wie der Stop'), die Einheit an die Beitragszahl (+1,3 %%), ,Punkte' -> ,Prozentpunkte', und R bekommt den Eurobetrag daneben (−0,467 R je Trade = −34,99 EUR). ⚠️ DIE ZAHL IN R BLEIBT - nur sie ist ueber Trades vergleichbar

- Quelle: agent/wahrscheinlichkeit.py

**2.353-eur** — ✔ UND DIE UMRECHNUNG HAENGT NICHT AM KAPUTTEN PORTFOLIOWERT: `R` ist der Betrag, der beim Stop verloren geht (`betraege.py`: Risiko in Euro = Einsatz x Verlustanteil). Gebraucht wird nur das Risiko DIESES Trades, und das steht in derselben `rechnung` wie Stop und Ziel. Wichtig, weil `portfolio_wert_historie` am Notebook seit dem 01.09. stillsteht (2.341)

- Quelle: agent/betraege.py / agent/rollen_lauf.py

**2.354** — ⚠️⚠️ EIN ZEICHEN STAND FUER DREI DINGE - und das IST der Nutzerbefund *,schwer abgrenzbare Hinweise, Warnungen und ehrliche Luecken'*: ⚠️ markierte die BEWERTUNG (,kein Beitrag greift hier'), die GEBUEHR (,deckt nicht'} und einen DAUERVORBEHALT (,keine Prognose'). ➔ Die Gebuehrenzeile bekommt ✔/✖. ⚠️ NICHT weggelassen: ,deckt die Gebuehr nicht' ist eine Aussage, kein Schmuck - und Regel 2 verlangt ohnehin, dass Gebuehren nicht in die BEWERTUNG eingehen; ein Warnzeichen legt genau das nahe

- Quelle: agent/wahrscheinlichkeit.py / Nutzerbefund 11.09.

**2.355** — ✔✔ DIE SPERRE GEGEN DAS BEQUEME NEUAUFZEICHNEN: die vier Textaenderungen machten 144 von 432 Bitgleichheitsfaellen rot. Neu aufzeichnen war richtig - aber das ist ein URTEIL, kein Handgriff, und dieselbe Geste koennte beim naechsten Mal eine geaenderte ZAHL mitloeschen. ✔ GEMESSEN: 144 Abweichungen, ALLE unter Text-Schluesseln, NULL unter Zahlen. ➔ `--aufzeichnen` verweigert jetzt den Dienst, wenn sich eine ZAHL geaendert hat, und nennt die Schluessel; `--auch-zahlen` hebt es auf. Beide Richtungen gegengeprueft

- Quelle: pruefe_wahrscheinlichkeit_bitgleich.py

**2.356** — ⚠️ EIGENE KORREKTUR: ich hatte vorgeschlagen, die Zeile ,KEIN gemessener Beitrag greift hier' nach oben zu holen - sie steht bereits an Position 4 von 16, direkt unter der Trefferquote. Regel 1 des Mailvorschlags war schon erfuellt. Nachgemessen statt umgebaut

- Quelle: Selbstbefund 11.09.2026

**2.347** — ⚠️⚠️⚠️ EIGENER VERFAHRENSFEHLER, vom Nutzer gestoppt: ich wollte S-1/S-2/S-3 bauen, ohne `zeige_modulkarte.py` zu benutzen - obwohl sie GENAU gegen diesen Fehler gebaut ist und als stehende Vorgabe im Memory steht (,Vor jeder Ausarbeitung: zeige_modulkarte.py'). Ihr eigener Docstring zitiert den Nutzerbefund woertlich: *,das ist ein problem des projektes dass du immer nur die haelfte der infos bei der ausarbeitung kennst dann bleibt immer etwas liegen'* - und listet sechs Beispiele, darunter ,welche sind Kern?' -> GUI-Schalter nennt BTC/ETH/SOL. **Exakt mein heutiger Fall.** Der Nutzerhinweis lautete: ,ich wuerde auch einen code Review und doku empfehlen damit du keine Funktionen und kritischen Punkte uebersiehst'

- Quelle: zeige_modulkarte.py / Nutzerhinweis 11.09.2026

**2.348** — ✔✔✔ UND DER REVIEW HAT S-1/S-3 DRASTISCH VERKLEINERT: `agent/datenfrische.py` existiert seit dem 17.08. und ist GENAU das Muster, das gebraucht wird. Es unterscheidet ZWEI Alter, und die Unterscheidung ist der ganze Trick: DATENSTAND (juengstes Datum in der Reihe - haengt am ANBIETER, ein hohes Alter kann richtig sein) gegen ABRUFSTAND (wann wir zuletzt erfolgreich nachgesehen haben - haengt an UNS, und ist der eigentliche Gesundheitswert). *,Ein Anbieter, der nichts Neues hat, ist normal. Ein Job, der nicht laeuft, ist es nie.'*

- Quelle: agent/datenfrische.py

**2.348-anlass** — ⚠️ UND SEIN ANLASS IST MEIN BEFUND 2.341, nur einen Monat aelter: am 17.08. stellte sich heraus, dass DREI Rolle-A-Quellen von einem Skript stammten, das ein Mensch von Hand gestartet hatte. Der Docstring: *,Ein fehlender Satz faellt auf; ein alter Satz sieht aus wie ein frischer. Das ist fail-soft-ist-fail-silent in seiner unangenehmsten Form: hier faellt nicht einmal etwas aus. Es steht nur still.'* Genau die Klasse, die ich heute in `portfolio_wert_historie` gefunden habe

- Quelle: agent/datenfrische.py / 2.341

**2.349** — ⚠️⚠️ DIE LUECKE IST PRAEZISE UND KLEIN: die Registratur fuehrt 15 Quellen - alle in der BETRIEBS-DB. Die drei MESSquellen fehlen: `funding_historie.db` (nicht registriert), `onchain_historie.db`/splycur -> turnover (nicht registriert), und `terminmarkt_historie.db` - der Eintrag `terminmarkt` meint eine ANDERE Tabelle (`open_interest_snapshot` via `hebel_screening`). ➔ S-1/S-3 heisst damit NICHT ,ein Ueberwachungssystem bauen', sondern ,drei Zeilen in eine vorhandene Registratur eintragen' - plus eine kleine Erweiterung, weil `datenfrische` heute nur Tabellen der Betriebs-DB kennt und die drei EIGENE Dateien sind

- Quelle: agent/datenfrische.REGISTRATUR

**2.350** — ⚠️ UND NOCH EINE UEBERSEHENE FUNKTION, vom Nutzer genannt (*,wir pruefen auch die Datenquellen und Abfragen auf der Uebersichtsseite'*): `remote/status.py` ist eine Statusseite mit rund VIERZIG Aggregatoren, darunter `_get_api_health`, `_get_coingecko_quota`, `_get_llm_kontingent` und `is_price_stale`. Sie prueft Datenquellen und Kontingente bereits. ⚠️ Ich haette S-1 gebaut, ohne sie zu kennen

- Quelle: remote/status.py

**2.340** — ⚠️⚠️⚠️ L1 IST GRAVIERENDER ALS ANGENOMMEN - am NOTEBOOK steht NUR BTC im DCA-Schalter, nicht einmal ETH. Die Nutzervorgabe nennt BTC, ETH UND SOL. Damit laufen ZWEI VON DREI Kernwerten produktiv nach `einstieg`, also MIT Stop und Trailing - statt als Akkumulation. ⚠️ Die Desktop-Kopie hatte BTC+ETH und verdeckte damit die Haelfte des Problems

- Quelle: NB-Sicherung 2026-09-11 04:48 · asset_dca_settings

**2.341** — ⚠️⚠️ EIN STILLER AUSFALL, LIVE BELEGT: der Job `portfolio_wert` lief am 11.09. um 04:43 - die juengste Zeile in `portfolio_wert_historie` ist aber vom 01.09. Er schreibt nur rund alle SECHS Tage (01.09., 26.08., 20.08.). ⚠️ Und genau diese Tabelle liefert nach Nutzerentscheidung P-5 die BEZUGSGROESSE fuer r x Kapital

- Quelle: NB-Sicherung 2026-09-11 · job_laeufe / portfolio_wert_historie

**2.341-ursache** — ✔ DIE URSACHE IST EINE RICHTIG GEBAUTE SCHRANKE: `MIN_ABDECKUNG_FUER_TAGESWERT = 0,80` - unter 80 %% Kursabdeckung wird NICHTS geschrieben, mit der ausdruecklichen Begruendung *,Lieber eine sichtbare Luecke als ein plausibel aussehender Falschwert.' Die letzte geschriebene Zeile hatte 6 von 32 Symbolen ohne Kurs, also 81 %% - knapp darueber. ⚠️⚠️ DIE SCHRANKE IST RICHTIG, DAS SCHWEIGEN IST DAS PROBLEM: ,sichtbar' ist die Luecke nur fuer den, der in die Tabelle sieht. Zehn Tage ohne Bezugsgroesse, und niemand erfaehrt es

- Quelle: agent/portfolio_historie.py:147

**2.342** — ⚠️ NUR SECHS VON 21 JOBS HINTERLASSEN EINE SPUR: `job_laeufe` fuehrt ausstiegs_empfehlungen, portfolio_wert, externe_reihen, lagebild_reihen, backward_tracking und makro_analog. Fuer die uebrigen 15 - darunter `refresh_prices`, `refresh_history`, `marktscan`, `hebel_screening` - ist NICHT nachvollziehbar, wann sie zuletzt liefen. Nach einem Ausfall ist damit nicht feststellbar, was gefehlt hat

- Quelle: NB-Sicherung 2026-09-11 · job_laeufe

**2.344** — ✔ WAS AM NOTEBOOK LAEUFT: `signals` bis 11.09. 04:48 (6.842 Zeilen) · `price_history` und `price_history_ohlc` bis 10.09. · `macro_snapshot` und `externe_reihe` bis 11.09. Der Betrieb laeuft, die Kursdaten sind frisch. Die Luecken sitzen in den ABGELEITETEN Groessen, nicht in der Beschaffung

- Quelle: NB-Sicherung 2026-09-11

**2.345** — ⚠️⚠️ ALLE NB-BEFUNDE STEHEN UNTER EINEM VORBEHALT, den der Nutzer am 11.09. genannt hat: *,der Codestand am NB ist sehr alt und wir machen jetzt einen massiven Umbau.'* Was ich aus der Sicherung lese, ist die AUSGABE VON ALTEM CODE. ➔ Das entwertet die Befunde nicht, aber es aendert ihre Folge: **der Rollout ist der Moment, sie zu beheben** - der Code wird ohnehin ersetzt, und S-1/S-2 gehoeren in dasselbe Paket

- Quelle: Nutzerhinweis 11.09.

**2.346** — ⚠️ EIGENER FEHLGRIFF, sofort bemerkt: ich wollte die sechs Symbole ohne Kurs benennen und habe Symbol gegen `coingecko_id` gejoint - die Watchlist steht aber NICHT in der Datenbank (sie kommt aus `config.yaml` und `Assets.xlsx`). Das Ergebnis meldete BTC und ETH als ,kein Kurs', was offensichtlich falsch ist. Belastbar ist allein die Zahl aus der Tabelle selbst: 6 von 32

- Quelle: Selbstbefund 11.09.2026

**2.331** — ⚠️⚠️ V11: `schnitt50` BESTEHT N-73 NICHT - 2 von 3 Beitragsmengen. Er traegt auf 10 %% (+0,0846) und 20 %% (+0,0698), bei 50 %% lautet das Urteil TRAEGT NICHT bis 0,0213 R - eine ECHTE Aussage, kein nicht-trennbar. Kriterium 1 dagegen ist erfuellt: 536 Symbole = 100 %%, 251,6 Anker/Tag. ⚠️ Damit steht er SCHWAECHER da als `schnitt` (3 von 3) und gleichauf mit `funding` (2 von 3) - als robuster Ersatz taugt er nicht

- Quelle: n111_v11_schnitt50.py

**2.331-2187** — ✔ UND DER WIDERSPRUCH IM BESTAND IST AUFGELOEST: 2.187-was-haelt (,`schnitt50` bleibt abgelehnt, auf ALLEN Mengen') und 2.219 (,widerspricht sich ueber die Mengen') hatten DIESELBE Basis und sagten das Gegenteil. **2.219 hatte recht** - er traegt auf 10 %% und 20 %%, nicht auf 50 %%. 2.187s Formulierung war zu weit

- Quelle: n111_v11_schnitt50.py / 2.219

**2.332** — ⚠️⚠️ DIE EHRLICHE GEGENFRAGE AUS V11 TEIL C: ein Kandidat OHNE Wirkung ist trivial stabil - also stehen Wirkung und Haelftenunterschied nebeneinander. Auf der 20-%%-Menge bewegen sich ALLE DREI um 80 bis 106 %% ihrer eigenen Wirkung: `schnitt` 1,06 · `funding` 0,89 · `schnitt50` 0,80. ⚠️ Der einzige Unterschied ist der BETRAG - `schnitt`s groesserer Wert schliesst die Null aus, die kleineren fallen unter dieselbe ABSOLUTE Leiter. Kriterium 2 trennt damit nicht stabil von instabil, sondern GROSS von KLEIN

- Quelle: n111_v11_schnitt50.py Teil C / n112 G4

**2.333** — ⚠️⚠️⚠️ UND DAMIT FAELLT DIE ZUSCHREIBUNG AUS 2.325: `schnitt`s Instabilitaet ist eine Eigenschaft der AUSWAHL, nicht seine. Mit gleich grosser, aber ZUFAELLIGER Auswahl (`entzerrte_reihe(auswahl_saat=...)`, drei Saaten) faellt der Haelftenunterschied auf der 20-%%-Menge von +0,1973 auf +0,0380 / +0,0264 / +0,0310 - ein Faktor 6, und STABIL in allen drei. Das ist genau der Test, den der Docstring des Parameters vorgibt: ,Traegt die Instabilitaet dann nicht mehr, ist sie eine Eigenschaft der AUSWAHL und nicht von `schnitt`'

- Quelle: n112_v11_gegenpruefung.py G3 / N-88 / 2.222

**2.333-schaerfer** — ✔✔ DIE NAHELIEGENDE GEGENERKLAERUNG IST AUSGESCHLOSSEN - und zwar umgekehrt: unter Zufallsauswahl ist der Test nicht SCHWAECHER, sondern VIERMAL SCHAERFER. Trennschaerfe 0,05 statt 0,20, Band [-0,0055 .. +0,0897] statt [+0,0717 .. +0,3892]. **Ein Nullbefund bei hoeherer Aufloesung** - das sauberste Ergebnis, das der Aufbau liefern kann

- Quelle: n112 Zusatzpruefung

**2.334** — ⚠️⚠️ UND UNTER DEMSELBEN SCHAERFEREN TEST KIPPT AUSGERECHNET `funding` - der LIVE laeuft: bei Saat 20260911 auf der 20-%%-Menge +0,0417 [+0,0036 .. +0,0785], Band schliesst die Null AUS, also NICHT STABIL. In 1 von 3 Saaten. `schnitt`, `schnitt50` und `zufall` sind dort in 3 von 3 stabil. ⚠️ Kein Grund zum Abschalten - aber dieselbe Lage wie bei V2/2.312: die Huerde ist fuer den BESTAND neu zu begruenden, nicht fuer den Kandidaten zu senken

- Quelle: n112_v11_gegenpruefung.py G3

**2.335** — ⚠️⚠️⚠️ DER EIGENTLICHE EINWAND GEGEN `schnitt` IST EIN ANDERER UND STAERKERER - und er steht seit dem 09.09. da: er bildet die AUSWAHL nach. Spearman +0,704 mit dem 250-Tage-Momentum (2.158-redundanz), Wirkung zu vier Fuenfteln Auswahlartefakt (+0,1858 auf der Momentummenge gegen +0,0366 auf Zufallsmengen, 2.222). **Ein Beitrag, der die bereits getroffene Auswahl wiederholt, bringt der Kette wenig Neues** - und dieser Grund ist von Kriterium 2 voellig unabhaengig

- Quelle: 2.222 / 2.222-passt / 2.158-redundanz

**2.336** — ⚠️⚠️ BILANZ NACH V11: ES GIBT KEINEN DRITTEN BEITRAG. `schnitt` bildet zu 4/5 die Auswahl nach (2.335) · `schnitt50` besteht N-73 nicht (2.331) · `vola` faellt an Kriterium 2 UND hat N-73 mit 1 von 3 (2.327, 2.293). Das deckt sich mit dem frueheren Befund, dass die Kursreihe als Quelle erschoepft ist - ein weiterer Beitrag braucht eine NEUE Quelle

- Quelle: V11 / 2.168-erschoepft

**2.337** — ⚠️⚠️ EIGENER FEHLER, ZWEITER DIESER ART IN ZWEI TAGEN: ich habe `entzerrte_reihe` korrigiert und erweitert, ohne zu sehen, dass sie seit dem 09.09. einen Parameter `auswahl_saat` GENAU FUER DIESE FRAGE hat - samt Testvorschrift im Docstring. Am 10.09. war es dasselbe Muster bei V9 (,das richtige Werkzeug lag vor, wegen eines Aufrufparameters verworfen'). **Vor dem Aendern eines Werkzeugs seine SIGNATUR und seinen Docstring ganz lesen**, nicht nur die Stelle, die man aendern will

- Quelle: Selbstbefund 11.09.2026

**2.338** — ⚠️ UND EINE FALSCHE ZITIERUNG, DIE ICH WEITER-GEREICHT HABE: ,`schnitt50` ist nach 2.222 die einzige monotone Form' steht in 2.305, 2.326, im Gesamtplan und im Kopf von `n102` - aber **2.222 sagt das nicht**, es handelt von `schnitt`s Auswahlartefakt. Die Behauptung stammt aus `Anforderungen_Umbau_28_08.md` (O4/N2), gilt dort nur LAENGS, ist vorstandardlich, und ihr eigener Nachtest N2 ist OFFEN. Im Hebelzusammenhang (H2/H3) fuehrt die Fakten-Entscheidungsmappe `schnitt50` sogar ausdruecklich als NICHT MONOTON

- Quelle: Basisinfos/Anforderungen_Umbau_28_08.md O4/N2 / Fakten_Entscheidungsmappe.md

**2.339** — ✔ WAS V11 SAUBER REPRODUZIERT HAT (R-R11): alle ZWOELF Haelftenunterschiede aus n110 auf vier Nachkommastellen · `schnitt`s Wirkungen aus n108 (+0,1830 / +0,1858 / +0,0434) · `funding`s (+0,0688 / +0,0582 / +0,0313) · `schnitt50`s +0,0698 aus 2.308-vorfrage. ⚠️ UND DER MASSSTAB IST GEPRUEFT: mean(entzerrte Reihe) trifft Wirkung minus Nullpunkt bei allen vier Kandidaten - ohne das waere das Verhaeltnis in 2.332 sinnlos gewesen

- Quelle: n112_v11_gegenpruefung.py G1/G2

**2.321** — ✔ S-7 IST GEKLAERT - und REPRODUZIERT, auf drei Wegen: die Wirkungszahlen (Faktor 1,14 bis 1,45 gegen S-7s Tafel), der JAHRESVERLAUF (2019 +0,52 gegen +0,45 · 2022 +0,022 gegen +0,019 · 2023 −0,047 gegen −0,050) und der HAELFTENUNTERSCHIED (+0,1973 gegen +0,2238, samt der Vorzeichendrehung bei 10 %%: −0,0805 gegen −0,0647). R-R11 ist erfuellt, das Urteil darf gedeutet werden

- Quelle: n108_s7_geklaert.py / n109_s7_gegenpruefung.py

**2.321-wortlaut** — ⚠️⚠️ ABER S-7 IST NUR IN SEINEM EIGENEN WORTLAUT BESTAETIGT - *,es ist unentschieden'* - und NICHT in der Lesart, `schnitt` trage ab 2022 nicht. Auf allen drei Mengen ab 2022 lautet das Urteil NICHT TRENNBAR, nicht TRAEGT NICHT. Der Unterschied ist der Kern der Norm: `zufall` bekommt in JEDER Zeile ein TRAEGT NICHT bis X - eine Aussage ueber die Welt. `schnitt` bekommt dreimal keine Aussage

- Quelle: n108_s7_geklaert.py / messnorm.urteil

**2.321-ab2024** — ⚠️⚠️ UND S-7s SPALTE ,AB 2024' WAR NIE GUELTIG: 962 Tage = 16 Bloecke, gefordert sind 20. Unter dem heutigen Standard ist das KEIN BEFUND, nicht traegt nicht. ⚠️ Mein eigener Hauptlauf sagte es NICHT - bei leerer Mengenliste laeuft die innere Schleife nie und es wird gar nichts gedruckt. Fail-silent im eigenen Werkzeug; die Abnahmetafel hat es aufgefangen, die Zeile nicht

- Quelle: n109_s7_gegenpruefung.py G4

**2.322** — ⚠️⚠️ DER MECHANISMUS IST DIE BANDBREITE, NICHT ein fehlender Effekt. Bei GLEICHER Blockzahl ist `schnitt`s Band rund sechsmal breiter als `funding`s (ab 2022, 10 %%: 0,383 gegen 0,063). Signal je Bandbreite im Mittel 0,36 gegen 0,61. Er hat die GROESSERE Wirkung und den SCHLECHTEREN Schaetzer - und das bestaetigt die Notiz vom 07.09. (`schnitt`s Baender sind fuenfmal breiter) aus eigener Rechnung

- Quelle: n109_s7_gegenpruefung.py G2

**2.323** — ✖ MEINE ERKLAERUNG ,KLUMPIGKEIT' IST WIDERLEGT - und zwar von der eigenen Kontrolle. Das Kriterium Streuung-ueber-Mittel gab ALLEN dreien klumpig, auch `zufall` (Str/Mit 1,25). Damit misst es eine Eigenschaft des Jahresfensters, nicht des Kandidaten. ⚠️ Die Tafel zeigt statt Streuen einen NIVEAUABFALL: 2019 bis 2021 bei +0,36 bis +0,57, ab 2022 zwischen −0,05 und +0,17 - und `zufall` liegt dort bei 0,03 bis 0,07, also zehnmal kleiner. Die Frueh-Erhoehung ist NICHT vom Zeitfenster erklaert

- Quelle: n109_s7_gegenpruefung.py G3

**2.324** — ⚠️⚠️⚠️ UND DABEI IST EIN FEHLER IM VIERFACHTEST SELBST AUFGEFALLEN: `n102_vierfachtest.py:135` entschied Kriterium 2 allein ueber d[unten] <= 0.0 <= d[oben] - STABIL hiess dort nur DAS BAND SCHLIESST DIE NULL EIN. Ein NICHT-Verwerfen, als Haken ausgegeben, mit einer Richtung, die den falschen Kandidaten belohnt: JE BREITER DAS BAND, DESTO SICHERER DAS ✔. `schnitt`, dessen Baender sechsmal breiter sind, bestand also nicht, WEIL er stabil ist, sondern WEIL er unruhig ist

- Quelle: n102_vierfachtest.py:135 / Selbstbefund 10.09.

**2.324-n73** — ⚠️⚠️ ZWEITER FEHLER, GLEICHE STELLE: N-73 war bei Kriterium 2 nie angewandt. Im selben `main()`, zehn Zeilen auseinander, lief Kriterium 1 ueber ALLE zulaessigen Mengen und Kriterium 2 ueber EINE. Und genau das kippt: `schnitt`s Haelftenunterschied dreht mit der Menge (−0,0805 bei 10 %%, +0,1973 bei 20 %%). WER EINE MENGE WAEHLT, WAEHLT DAS URTEIL. Der Bestand hatte es am 07.09. schon notiert, es war nur nie in den Test gewandert

- Quelle: n102_vierfachtest.py / 2.7-07.09.

**2.325** — ⚠️⚠️⚠️ RICHTIG GEMESSEN FAELLT `schnitt` AN KRITERIUM 2 - und es ist KEIN nicht-trennbar, sondern ein NACHGEWIESENER Unterschied: auf der 20-%%-Menge +0,1973 [+0,0717 .. +0,3892], Band schliesst die Null AUS, 20/20 Bloecke. Auf 10 %% und 50 %% ist er stabil - nach N-73 zaehlt das nicht als Entlastung, sondern als fehlende Robustheit. ⚠️ `zufall` bekommt nirgends NICHT STABIL (stabil bis 0,02 bis 0,05) - die Kontrolle haelt

- Quelle: n110_kriterium2_mit_trennschaerfe.py

**2.325-2319** — ⚠️⚠️⚠️ DAMIT IST 2.319 ZU WIDERRUFEN: `schnitt` hat NICHT alle vier Kriterien. Er hat DREI - Abdeckung, Unabhaengigkeit, Regel 3 - und faellt an der STABILITAET. ⚠️ Der Widerruf ist zulaessig, weil er reproduziert wurde (2.321): dreimal, auf drei verschiedenen Wegen. R-R11 ist erfuellt

- Quelle: n110_kriterium2_mit_trennschaerfe.py / R-R11

**2.328** — ✔✔ KEIN LAUFENDER BEITRAG IST BETROFFEN: `funding` (bis 0,10 · 0,10 · 0,05), `oi_aenderung` (bis 0,05 · 0,02) und `turnover` (bis 0,10) sind auf ALLEN ihren zulaessigen Mengen stabil - mit Aussage, nicht mit nicht-trennbar. Dieser Lauf aendert nichts am Betrieb; er verhindert eine Registrierung, die sonst auf einem fehlerhaften Kriterium beruht haette

- Quelle: n110_kriterium2_mit_trennschaerfe.py

**2.329** — ⚠️ VOM VORABTEST GEFANGEN - DIE ZWEI LEITERN SIND NICHT DIESELBE SKALA: der Stabilitaetstest pflanzt den Versatz 1:1 auf die entzerrte Reihe, `messnorm` pflanzt gegen den Nullpunkt mit der Daempfung aus GRENZE = 0,80 (gepflanzte 0,10 R erscheinen als rund 0,02). Ein bis-0,20 im Stabilitaetstest ist NICHT mit einem 0,05 R der Norm zu vergleichen. Steht jetzt im Kopf beider Werkzeuge und in der Ausgabe

- Quelle: n110 / n68.stabilitaetsurteil

**2.330** — ✔ DAS KORRIGIERTE URTEIL STEHT AN DER QUELLE - `n68_zeitstabilitaet.stabilitaetsurteil()`, gerufen von `n102` UND `n110`. Vorgabe: ein Test muss die ECHTE Funktion rufen, nie eine Kopie. ⚠️ Die alte Konstruktion sitzt sonst nirgends: `n88:152` und `n89:106` nutzen dieselbe Zeile in der RICHTIGEN Richtung (als trennt), geprueft per Suche ueber alle Skripte

- Quelle: n68_zeitstabilitaet.py / n102 / n110

**2.316** — ✔✔✔ V9: KRITERIUM 3 IST BEANTWORTET - `funding` erklaert bei KEINEM Kandidaten etwas. Geschichtet gemessen als EIN Befund mit EINEM Band: `schnitt` echt +0,0388 gegen gemischt +0,0361 · `schnitt50` +0,0300 gegen +0,0311 · `turnover` +0,0442 gegen +0,0514 · `oi_aenderung` +0,0135 gegen +0,0128. ⚠️⚠️ Der ABFALL durch die Schichtung (`schnitt` von +0,1858 auf +0,0388) tritt mit BEDEUTUNGSLOSEM Partner genauso ein - er ist ein Artefakt der Schichtung, keine Redundanz

- Quelle: n107_v9_kriterium3_ein_befund.py

**2.316-lesart** — ✔ DIE LESART GIBT DAS WERKZEUG SELBST VOR - `pruefe_n1_schichtung_gegen_partner`: ,Bleibt es auch dort beim selben Wert, ist es die SCHICHTUNG - der Partner erklaert NICHTS.' Und ,der Partner erklaert nichts' IST Unabhaengigkeit, also genau das, was Kriterium 3 fragt. ⚠️ Meine erste Ausgabe sagte nur ,kein Unterschied, Baender ueberlappen' - technisch richtig, aber sie liess den Leser mit der Zahl allein, statt den Schluss zu ziehen

- Quelle: n107_v9_kriterium3_ein_befund.py

**2.317** — ✔✔ UND DIE TRENNSCHAERFE IST BEZIFFERT: 0,05 R in jeder Zeile. Bei den Zaehlmetriken von V7 und V8 gab es KEINE - ein ,traegt nicht' war dort nie von Untermacht zu unterscheiden. Jetzt ist der Nullbefund bei `zufall` eine echte Aussage. ⚠️ Das ist der Grund, warum V9 gelingt, wo V7 und V8 gescheitert sind: eine STETIGE Kennzahl mit Band und Leiter statt einer Zaehlung mit drei bis sechs moeglichen Werten

- Quelle: n107_v9_kriterium3_ein_befund.py

**2.318** — ⚠️⚠️ DREI ANLAEUFE, DREI EIGENE FEHLER - und jeder von einer anderen Instanz gefangen: V7 - Zaehlmetrik zu grob, und die Kontrolle bekam ,unabhaengig' (vom VORABTEST gefangen). V8 - mein Loesungsweg ,weniger Faecher' machte die Zaehlmetrik GROEBER statt besser (vom ERGEBNIS gefangen). V9 - das richtige Werkzeug lag vor, ich hatte es wegen eines Aufrufparameters verworfen, und beim Umbau die Vorfrage aus V7 nicht mitgenommen (vom ERGEBNIS gefangen, weil `zufall` wieder ein positives Urteil bekam)

- Quelle: Selbstbefund 10.09.2026

**2.320** — ⚠️ WAS BEI `vola` UEBRIG BLEIBT: geschichtet traegt er nicht mehr - echt wie gemischt, bei einer Trennschaerfe von 0,05 R. Das ist ein ECHTER Nullbefund, keine Untermacht: `funding` erklaert auch bei ihm nichts, aber die Schichtung nimmt ihm die Trennbarkeit. Zusammen mit N-73 (1 von 3 Mengen) bleibt er der wackligste der Kandidaten

- Quelle: n107_v9_kriterium3_ein_befund.py / 2.293

**2.188** — ⚠️⚠️⚠️ DIE URSACHE DES HIN UND HER GEFUNDEN: `messnorm_auswahl.ZIEHUNGEN` ist 5, und `Befund.traegt` prueft `unten > max(0, null_oben)` - wobei `null_oben` das MAXIMUM ueber diese fuenf Mischungen ist. Ein Maximum ueber wenige Ziehungen ist systematisch ZU NIEDRIG, also faellt das Urteil zu WOHLWOLLEND aus

- Quelle: Methodik 2.188 / Nutzervorgabe 08.09.

**2.188-beleg** — ⚠️⚠️ DER BELEG, an `funding` bei 50 % (Abstand `unten - null_oben`): bei 5 Ziehungen +0,0002 R -> TRAEGT · bei 20 Ziehungen -0,0045 -> NICHT TRENNBAR · bei 40 Ziehungen -0,0056 -> TRAEGT NICHT bis 0,05. ZWEI Zehntausendstel R entschieden ueber das Urteil. `null_oben` steigt dabei von +0,0192 auf +0,0250

- Quelle: Methodik 2.188

**2.188-schnitt** — ✔ NICHT ALLE URTEILE HAENGEN DARAN: `schnitt` bei 20 % haelt bei 5, 10, 20 UND 40 Ziehungen durchgehend TRAEGT - der Abstand betraegt dort +0,0595 bis +0,0521. Ein Befund mit grossem Abstand ist robust; gefaehrlich sind die knappen

- Quelle: Methodik 2.188

**2.188-vorgabe** — ⚠️ UND ES WIDERSPRICHT ZWEI EIGENEN STEHENDEN VORGABEN: 'Die ZIEHUNGSZAHL gehoert in JEDE Kontrolle' und 'EINE ZIEHUNG IST KEIN NULLPUNKT'. Beide wurden fuer die WIRKUNG befolgt und fuer den NULLPUNKT uebersehen

- Quelle: Methodik 2.188

**2.188-inkonsistenz** — ⚠️ Und eine zweite Unstimmigkeit in derselben Anlage: die TRENNSCHAERFE prueft `pb['unten'] > 0` - gegen NULL. Das URTEIL prueft gegen `null_oben`. Wenn `null_oben` > 0 ist, ist das Urteil STRENGER als die Trennschaerfe angibt. Ein Kandidat kann eine Trennschaerfe von 0,02 haben und bei einem Effekt von 0,05 kein TRAEGT erreichen

- Quelle: Methodik 2.188

**2.188-nichtsaat** — ⚠️ Eine eigene Vermutung wurde dabei WIDERLEGT: ich hielt `null_oben` fuer saatabhaengig. Es ist deterministisch - die Nullziehungen laufen auf der festen Saat `SAAT + z`, nicht auf der uebergebenen `rng`. Fuenf Saaten liefern +0,0375 bis +0,0383. Was wandert, ist die Reaktion auf geaenderte DATEN, nicht auf Zufall

- Quelle: Methodik 2.188

**2.187** — ⚠️⚠️ R-R11 AUF DER NEUEN MESSBASIS: die Durchsicht aller Kandidaten (N-73) ist auf der Basis vom 08.09. (536 Symbole) wiederholt. DIE WIRKUNGEN REPRODUZIEREN FAST EXAKT - turnover 50 % +0,0913 gegen +0,0909, schnitt 20 % +0,1858 gegen +0,1759, funding frei +0,0249 gegen +0,0246. ABER DREI URTEILE WANDERN, weil sich Nullpunkte und Trennschaerfen verschieben

- Quelle: Methodik 2.187 / n73 auf neuer Basis

**2.187-was-wandert** — ⚠️ WAS WANDERT, jeweils bei nahezu gleicher Wirkung: `turnover` 50 % von TRAEGT auf 'nicht trennbar' · `funding` frei von 'traegt nicht bis 0,10' auf TRAEGT · `vola` 20 % von 'nicht trennbar' auf TRAEGT. Die Zahl der Mengen-Widersprueche steigt von ZWEI auf VIER

- Quelle: Methodik 2.187

**2.187-lehre** — ⚠️⚠️ DIE LEHRE: die Urteile der Norm haengen an NULLPUNKT und TRENNSCHAERFE, und beide werden je Lauf aus Ziehungen geschaetzt. Eine um 2 % veraenderte Messbasis verschiebt die WIRKUNG um weniger als 0,0005 R, kann aber ein Urteil kippen. Wer nur die Wirkung vergleicht, sieht das nicht - wer nur das Urteil vergleicht, haelt eine Verschiebung des Nullpunkts fuer einen neuen Befund

- Quelle: Methodik 2.187

**2.187-feld** — ✔ STRUKTURELLER FIX: `Befundlage` hat jetzt ein Feld `basis`. Am 08.09. war nach zwei Basiswechseln nicht mehr feststellbar, welche der 92 geltenden Befunde auf welcher Grundlage entstanden waren - 25 tragen Messzahlen. ⚠️ R-R11 verlangt Reproduktion vor Widerruf, aber wer nicht weiss, WORAUF ein Befund steht, kann ihn nicht reproduzieren. Vorgabe leer (die Altbefunde bleiben unveraendert), ab jetzt gefuellt

- Quelle: Methodik 2.187

**2.186** — ⚠️ MEINE AUSSAGE 'CANTON HAT GAR KEINE KURSREIHE' WAR ZU ENG. Es hat 252 CoinGecko-Tagespreise in `price_history`. Was fehlt, ist OHLC - nur `close`, also kein ATR, keine Stopgeometrie, kein `vola`. Fuer einen gleitenden Schnitt genuegt es; `marktrang.py` nutzt genau das

- Quelle: Methodik 2.186 / Nutzerhinweis 08.09.

**2.186-symbol** — ✔ DAS SYMBOLPROBLEM IST REAL, DOKUMENTIERT UND GELOEST: CoinGecko fuehrt `canton-network` unter dem Symbol **CC**, unsere Watchlist unter `CANTON`. Der Abgleich lief ueber das SYMBOL - 'CANTON konnte deshalb NIE gefunden werden, und zwar lautlos' (marktrang.py). Seit 31.08. laeuft er ueber die `coingecko_id`

- Quelle: Methodik 2.186

**2.186-frische** — ⚠️⚠️ WARUM CANTON TROTZDEM IN `schnitte()` FEHLT - und der Grund ist NICHT CANTON: `SCHNITT_FRISCHE_TAGE` ist 10, CANTONs letzter Tagespreis ist vom 2026-07-19 und damit 51 Tage alt. ⚠️ ABER `bitcoin` und `kaspa` sind in `price_history` GENAUSO 51 Tage alt - DIE GANZE TABELLE STEHT SEIT DEM 19.07. STILL. Das ist ein Datenstand-Befund ueber die DESKTOP-KOPIE

- Quelle: Methodik 2.186

**2.186-notebook** — ⚠️ WAS VON HIER AUS NICHT FESTSTELLBAR IST: ob `refresh_prices_job` auf dem NOTEBOOK weiterlaeuft. Steht `price_history` auch dort seit dem 19.07., fehlen seit 51 Tagen die Tagespreise fuer ALLE Werte ohne Boersenlisting (CANTON, VSN, AIOZ, SUPRA). Das waere kein niedrig priorisierter Punkt mehr - es ist eine RUECKFRAGE, keine Messung

- Quelle: Methodik 2.186

**2.186-abstand** — ⚠️ UND DIE UEBERNAHME HAT EINE NEUE LUECKE ERZEUGT: `schnitte()` liefert jetzt 536 Symbole, `schnitt_werte()` nur 516. ACHT der zehn Uebernommenen (AIOZ, AKT, BRETT, CAT, GRIFFAIN, HYPE, KAS, SUPRA) haben einen 200-Tage-Schnitt, aber KEINEN Abstand - `schnitt_werte` braucht einen AKTUELLEN Kurs vom Binance-Ticker, und dort sind sie nicht gelistet. MORPHO und PLUME funktionieren (sie haben Binance-Zeilen). ✔ Heute FOLGENLOS, weil `schnitt` nicht registriert ist (zustand='null') und die Messungen direkt aus der Messbasis lesen - aber bei einer Aktivierung waeren diese acht ohne Rang

- Quelle: Methodik 2.186

**2.185** — ✔✔ D-1 ERLEDIGT: ZEHN REIHEN AUS DER PRODUKTION UEBERNOMMEN (AIOZ, AKT, BRETT, CAT, GRIFFAIN, HYPE, KAS, MORPHO, PLUME, SUPRA) - 6.768 Zeilen, alle mit Median-Tagesabstand 1, null Luecken, null Zeilen ohne Tagesspanne. Messbasis 526 -> 536 Krypto-Symbole. Die gehaltenen Luecken sinken von ACHT auf DREI

- Quelle: Methodik 2.185 / uebernehme_messreihen.py

**2.185-quelle** — ⚠️⚠️ DIE QUELLENREINHEIT BLEIBT SICHTBAR: jede uebernommene Zeile traegt eine eigene Quelle - `uebernommen_gemessen` 3.878, `uebernommen_bybit` 2.822, `uebernommen_binance` 68 gegen `binance_mess` 5.121.873. Ein `SELECT DISTINCT quelle` zeigt es sofort. Bei mehreren Quellen je Tag gewinnt die beste: binance vor bybit vor gemessen

- Quelle: Methodik 2.185

**2.185-veralten** — ⚠️ UND DER PREIS IST BENANNT: diese Symbole sind NICHT auf Binance - `lade_messreihen.py` kann sie NIE auffrischen. Sie enden am 19.08. bzw. 13.07. und bleiben dort stehen. Deshalb tragen sie in `messreihen_status` den eigenen Status `uebernommen` statt `handelnd` - sichtbar statt still

- Quelle: Methodik 2.185

**2.185-rest** — WAS OFFEN BLEIBT, mit prazisierter Begruendung: ASTER (318 USD-Tage) und MON (269) liegen unter der 400er-Grenze - eine DATENLAGE-Grenze, keine Nachlaessigkeit; die Coins existieren erst seit 10/2025 bzw. 11/2025. CANTON hat in der Produktion GAR KEINE Kursreihe und ist zugleich Kernwert. VSN ist auf Nutzerentscheidung 08.09. ausgenommen ('vsn ist nicht relevant')

- Quelle: Methodik 2.185

**2.185-meldung** — ⚠️ Die Meldung selbst war nach der Uebernahme UNGENAU geworden: sie sagte bei ASTER und MON weiter 'die Daten sind da, nur nicht uebernommen', dabei sind sie zu kurz. Ursache: sie zaehlte die GESAMTzeilen (USD+EUR) statt der USD-Tage. Korrigiert - jetzt nennt sie die USD-Tageszahl und trennt 'zu kurz' von 'nicht uebernommen'

- Quelle: Methodik 2.185

**2.184** — ✔✔ DIE AUFFRISCHUNG IST DURCH: 347 Reihen, 539.568 Kerzen, 259 s. Die Krypto-Messbasis steht jetzt auf 2026-09-08 statt 2026-08-21 - nur noch drei Reihen auf dem alten Stand. Ablauf protokolliert: Sicherung (SHA-256 bitgleich) -> Anker VORHER -> Trockenlauf -> Schreiben -> Anker NACHHER

- Quelle: Methodik 2.184 / Gesamtplan 08.09.

**2.184-urteile** — ⚠️⚠️ ZWEI URTEILE HABEN SICH GEAENDERT, und beide sind VERBESSERUNGEN durch mehr Daten, keine Instabilitaet: `funding` H20 frei geht von 'traegt nicht bis 0,10 R' auf TRAEGT (+0,02458 -> +0,02581, also nur +0,00123 Verschiebung), und `zufall` H20 5 % von 'KEIN BEFUND' auf 'traegt nicht bis 0,05 R'. In beiden Faellen ist das BAND enger geworden - 526 statt 524 Symbole und 18 Tage mehr Daten

- Quelle: Methodik 2.184

**2.184-logik** — ⚠️ DABEI EINE EIGENE FEHLANNAHME KORRIGIERT: ich hielt 'TRAEGT' fuer 'Effekt ueber der Trennschaerfe'. `messnorm.Befund.urteil` sagt es anders - TRAEGT heisst 'das Band schliesst den NULLPUNKT aus'. Die Trennschaerfe blieb bei 0,1; sie erklaert den Wechsel nicht. Und er ist SAATSTABIL: fuenf Saaten, ein Urteil

- Quelle: Methodik 2.184

**2.184-rr11** — ⚠️ R-R11 GILT TROTZDEM: die Anker in `messbasis_anker.json` stehen jetzt auf der NEUEN Basis. Der registrierte `funding`-Befund (+0,0246) und alle heutigen Messungen (N-73 bis N-80) liefen auf der ALTEN. Die groesste Verschiebung betraegt +0,01358 R (`schnitt` H20 20 %: +0,17593 -> +0,18951) - kein Urteil dort aendert sich, aber die ZAHLEN sind nachzuziehen

- Quelle: Methodik 2.184

**2.182** — ✔ DIE FRISCHEPRUEFUNG WAR ZU STRENG und ist korrigiert: EINGESTELLTE Reihen sind VOLLSTAENDIG, nicht veraltet - sie handeln nicht mehr, es gibt keine neuen Kurse. Die erste Fassung zaehlte alle 174 eingestellten Krypto-Reihen als Mangel und haette das Paket dauerhaft rot gehalten fuer etwas, das kein Fehler ist. Jetzt: 350 handelnde, davon 344 veraltet (98 %); die 174 eingestellten getrennt ausgewiesen

- Quelle: Methodik 2.182

**2.182-trocken** — DER TROCKENLAUF DER AUFFRISCHUNG: 347 von 487 Binance-Paaren brauchbar, 539.568 Kerzen, 4,6 Minuten. 140 abgelehnt - ALLE wegen 'zu kurz' (< 400 Kerzen), keine Plausibilitaets- oder Lueckenfehler. Schreibsemantik ist ein sauberer Upsert (INSERT OR REPLACE, PK ueber symbol/assetklasse/currency/date) - eine Auffrischung ERGAENZT, sie ueberschreibt keine Historie. Die harte Sperre gegen die Produktions-DB greift

- Quelle: Methodik 2.182 / lade_messreihen.py

**2.183** — ⚠️⚠️ DIE F-198-KOLLISIONEN SIND NUR HALB BEREINIGT: sieben Symbole (BOND, C, DASH, DIA, MDT, STX, T) tragen in `price_history_ohlc` eine ANDERE Klasse als in `messreihen`. Alle sieben haben Kurse in ZWEI Klassen - DASH etwa aktien 1.440 UND krypto 2.721 -, aber `messreihen.symbol` ist PRIMARY KEY und kann nur EINER Klasse zuordnen

- Quelle: Methodik 2.183

**2.183-folge** — ✔ DIE MESSUNGEN SIND NICHT BETROFFEN: `_reihen_roh` ueberspringt den `messreihen`-Filter, wenn `price_history_ohlc` die Spalte `assetklasse` traegt - der Fix vom 07.09. ⚠️ ABER `klassen_aus_db()` liest weiterhin aus `messreihen` und liefert fuer diese sieben die FALSCHE Klasse. Ueber ZEHN Messwerkzeuge importieren sie. Wer sie zur Klassenentscheidung nutzt, bekommt dort das Falsche

- Quelle: Methodik 2.183

**2.183-nichtjetzt** — ⚠️ NICHT JETZT REPARIERT, und mit Grund: der saubere Fix verlangt, dass ein Symbol MEHREREN Klassen zugeordnet werden kann - das ist eine Strukturaenderung an `messreihen` und beruehrt zehn Werkzeuge. Nutzervorgabe 08.09.: 'langsam und vorsichtig planen und umsetzen'. Als Suitepruefung gemeldet, damit es nicht wieder untergeht

- Quelle: Methodik 2.183

**2.181** — ⚠️ KORREKTUR AN MEINER EIGENEN KLASSIFIZIERUNG: `HYPE` IST AUFNEHMBAR. Ich hatte es als 'zu kurz' gefuehrt (bybit 238, gemessen 167) - KOMBINIERT ergeben die beiden USD-Quellen 405 einzigartige Tage von 405 moeglichen, also LUECKENLOS und ueber der 400er-Grenze. Sie ergaenzen sich exakt: bybit 2025-07-11 bis 2026-08-19, gemessen 2026-01-28 bis 2026-07-13. Damit sind es ZEHN aufnehmbare, nicht neun

- Quelle: Methodik 2.181 / Nutzerhinweis 08.09.

**2.181-grenzen** — ASTER (318 Tage) und MON (269) bleiben auch kombiniert unter 400 - aber der Grund ist die DATENLAGE, nicht die Sammlung: die Coins existieren erst seit 10/2025 bzw. 11/2025. Beide Reihen sind zu 100 % lueckenlos. Das ist eine Grenze, keine Nachlaessigkeit

- Quelle: Methodik 2.181

**2.181-canton** — ⚠️⚠️ CANTON ist der schwierigste Fall - und er hat DOCH Daten, nur in der falschen Tabelle: `price_history` (CoinGecko-Tagespreise) fuehrt `canton-network` mit 252 Zeilen (2025-11-10 bis 2026-07-19). ⚠️ Diese Tabelle hat aber NUR `price_usd`/`price_eur` - KEIN Hoch/Tief. Ohne Tagesspanne gibt es kein ATR, keine Stopgeometrie und kein `vola`. CANTON ist damit zu kurz UND ohne Spanne - als KERNWERT im Bestand ist das eine echte Einschraenkung, die der Nutzer kennen muss

- Quelle: Methodik 2.181

**2.181-gemessen** — ✔ Entwarnung zur Quelle `gemessen`: laut `database/db.py` ist sie ein 'echter Kursabruf' (ueber `api/boersen_klines.py` bzw. `api/yfinance_krypto_fallback.py`), also echte Kerzen mit Hoch und Tief. Der Anteil ohne Tagesspanne betraegt bei den fraglichen Symbolen 0,0 %

- Quelle: Methodik 2.181

**2.180** — ⚠️⚠️ DIE FEHLENDEN MESSREIHEN SIND KEIN UEBERNAHMEVERSAEUMNIS, sondern eine QUELLENFRAGE. Die Messbasis laedt Binance-USDT-Spotpaare (`quelle='binance_mess'`, 5.114.965 Zeilen einheitlich). Binance FUEHRT die fehlenden Symbole ueberwiegend nicht: von 14 haben nur ASTER (51 Zeilen), MORPHO (31) und PLUME (37) ueberhaupt Binance-Daten, alle erst seit Juli 2026

- Quelle: Methodik 2.180 / Audit 08.09.

**2.180-ersatz** — Die Produktion ergaenzt aus ANDEREN Quellen: `bybit` (AIOZ, BRETT, CAT, HYPE, KAS, MON, SUPRA) und `gemessen` (AKT, GRIFFAIN und andere). ⚠️ Eine Uebernahme wuerde die Quellenreinheit der Messbasis brechen - deshalb ist Kopieren NICHT der saubere Weg, sondern Uebernahme MIT Quellenkennzeichnung

- Quelle: Methodik 2.180

**2.180-qualitaet** — GEPRUEFT, ob die Ersatzquellen die Aufnahmebedingungen halten (Median-Tagesabstand genau 1, >= 400 Kerzen, < 5 % Luecken): NEUN sind aufnehmbar - AIOZ (bybit 592), AKT (gemessen 727), BRETT (bybit 854), CAT (418), GRIFFAIN (537), KAS (608 bzw. bybit 470), MORPHO (606), PLUME (447), SUPRA (bybit 631). DREI sind zu kurz: ASTER (267), HYPE (238), MON (232). ZWEI haben nirgends Daten: CANTON, VSN

- Quelle: Methodik 2.180

**2.180-gehalten** — Auf die ACHT gehaltenen Positionen heruntergebrochen: VIER aufnehmbar (BRETT, KAS, MORPHO, SUPRA), ZWEI zu kurz (ASTER, MON - das ist eine Datenlage-Grenze, keine Nachlaessigkeit), ZWEI ohne jede Quelle (CANTON, VSN)

- Quelle: Methodik 2.180

**2.180-spanne** — ⚠️ Ein Qualitaetsverdacht wurde geprueft und AUSGERAEUMT: `gemessen` hat insgesamt in 6,6 % der Zeilen `high = low = close` - also keine Tagesspanne, womit ATR und `vola` dort wertlos waeren. Bei den 14 fraglichen Symbolen betraegt der Anteil aber 0,0 %. Die 6,6 % betreffen andere Werte

- Quelle: Methodik 2.180

**2.180-vorrang** — ⚠️⚠️ ENTSCHEIDUNG ZUR REIHENFOLGE: die GROESSERE Luecke ist die Frische. 518 von 524 Krypto-Reihen sind 18 Tage alt; neun Reihen zu ergaenzen, waehrend 518 veralten, waere die falsche Reihenfolge. Und die Auffrischung hat KEIN Qualitaetsproblem - dieselbe Quelle, dasselbe Werkzeug

- Quelle: Methodik 2.180

**2.179** — ✔ DIE MELDELUECKE IST GESCHLOSSEN: `pruefe_neuaufnahme.py` prueft die drei Lebenszyklus-Faelle, die der Nutzer benannt hat - NEU (Watchlist/Bestand ohne Messreihe), FAELLT WEG (nur berichtet, KEIN Mangel wegen P6) und AENDERT SICH (Frische je Klasse). Dazu die Beitragslage der gehaltenen Werte. Als Suitepaket `Neuaufnahme` verdrahtet

- Quelle: Methodik 2.179 / pruefe_neuaufnahme.py

**2.179-rot** — ⚠️⚠️ DAS PAKET IST ROT, UND DAS IST RICHTIG: 3 von 5 Pruefungen schlagen an. Ein Paket, das eine offene Luecke gruen faerbt, waere schlimmer als keines. Gruen wird es, wenn die acht Messreihen uebernommen und die Krypto-Basis nachgeladen ist

- Quelle: Methodik 2.179

**2.179-frische** — ⚠️⚠️⚠️ DABEI GEFUNDEN: DIE KRYPTO-MESSBASIS IST ZU 99 % VERALTET. Die Median-Reihe endet am 21.08.2026 - 18 Tage alt; 518 von 524 Reihen sind aelter als sieben Tage. Nur SECHS Reihen (die am 07.09. nachgeladenen) reichen bis heute. Die Nicht-Krypto-Klassen sind mit 5 Tagen aktuell

- Quelle: Methodik 2.179

**2.179-median** — ⚠️ Und die Pruefung hat einen Fehler in SICH SELBST aufgedeckt: die erste Fassung nahm das MAXIMUM je Klasse und meldete 'krypto 1 Tag alt' - weil sechs frische Reihen die ganze Klasse frisch aussehen liessen. Der MEDIAN und der Anteil der Veralteten sind das richtige Mass. Dieselbe Fehlerklasse wie beim Stichprobenmedian in N-65

- Quelle: Methodik 2.179

**2.179-core** — ⚠️ DREI KERNWERTE betroffen, nicht einer: CANTON (gehalten, `rolle=core`, NIRGENDS Daten), MORPHO (gehalten, `core`, 1.243 Zeilen in der Produktion) und HYPE (Watchlist, `core`, 572 Zeilen). Ich hatte zuerst nur CANTON gesehen

- Quelle: Methodik 2.179

**2.176** — ⚠️⚠️⚠️ ACHT GEHALTENE KRYPTO-POSITIONEN HABEN KEINE MESSREIHE - und NICHTS meldet es. Betroffen: ASTER, BRETT, CANTON, KAS, MON, MORPHO, SUPRA, VSN. ⚠️ CANTON hat `rolle=core` - ein KERNWERT ohne jede Kursreihe. Gefunden auf Nutzerhinweis 08.09.: 'neues Asset in der Watchlist oder neuer Coin-Bestand - die Daten zur Bewertung muessen vorhanden sein'

- Quelle: Methodik 2.176 / Audit 08.09.

**2.176-vorhanden** — ⚠️ SECHS DAVON HABEN HISTORIE IN DER PRODUKTIONS-DB, sie wurde nur nie in die Messbasis uebernommen: KAS 1.686 Zeilen · MORPHO 1.243 · BRETT 854 · SUPRA 631 · ASTER 585 · MON 501. Zwei haben gar nichts: CANTON und VSN. Es ist also ueberwiegend ein UEBERNAHME-, kein Beschaffungsproblem

- Quelle: Methodik 2.176

**2.176-still** — ⚠️⚠️ UND ES IST STILL: die acht sind in `messreihen` UND `messreihen_status` gar nicht gefuehrt, und es gibt KEINE Pruefung, die fehlende Messreihen fuer gehaltene Positionen meldet (im ganzen Baum kein Treffer). Werkzeuge zum Nachladen existieren (`lade_messreihen.py`), aber kein Automatismus bei Neuaufnahme

- Quelle: Methodik 2.176

**2.176-eurcv** — ✔ EURCV gehoert NICHT in diese Liste (Nutzerhinweis 08.09.): es hat `ist_cash_aequivalent = True` und ist das Cash-Aequivalent, kein zu bewertender Coin. `asset_schalter.py` behandelt es gesondert und notiert den Datenmangel bereits. Es braucht einen PREIS fuer die Cash-Quote, aber keine Bewertung

- Quelle: Methodik 2.176

**2.177** — ⚠️ AUFLAGE 2 GEPRUEFT - die Trennung Bewertung gegen Wirtschaftlichkeit ist im CODE sauber: `potential.py` rechnet ausdruecklich gebuehrenfrei ('BEWERTUNG = ist das ein guter Trade, OHNE Gebuehren', `gebuehr_je_seite=0.0` ist kein Versehen), und `stop_relativ` geht nicht in die Quote ein - Stop 5 % und 25 % liefern beide 0,373033

- Quelle: Methodik 2.177

**2.177-etikett** — ⚠️⚠️ ABER DIE STUFENBESCHRIFTUNG IST ALTBESTAND: `rollen_gate.STUFEN` nennt die zwoelfte Stufe 'Trefferquote schlaegt den Breakeven'. Seit U-1 (30.08.) entscheidet dort `potential.traegt()` - gebuehrenfrei. Der Kommentar darueber sagt es selbst ('die alte Begruendung galt einem Modul, das an dieser Stelle nicht mehr steht'), aber das ETIKETT wurde nicht nachgezogen. Wer es liest, glaubt an einen Wirtschaftlichkeitsfilter, den es nicht gibt

- Quelle: Methodik 2.177 / Auflage 1

**2.178** — ⚠️⚠️ AUFLAGE 3 BESTAETIGT (Nutzerhinweis): SPOT HAT IN DER BEWERTUNG KEINEN STOP. `messnorm.STOP_BEENDET` kennt nur hebel x einstieg und hebel x swing. ⚠️ ABER die Zielgroesse `bewegung_r` aller Messungen TEILT DURCH DIE STOPWEITE - sie normiert bei Spot durch eine Groesse, die die Bewertung dort nicht kennt. Dieselbe Fehlerklasse wie 2.172 (geliehene Geometrie); bei Krypto ist die Weite rund 0,75 ATR und damit ein brauchbarer Massstab, aber es gehoert benannt

- Quelle: Methodik 2.178

**2.178-instrument** — Und ein Nebenfund: `instrument = 'hebel'` hat es in der NEUEN Kette nie gegeben - 3.513 spot, 11 absicherung, 0 hebel. Der Hebel entsteht als ETIKETT innerhalb von spot x einstieg, sobald `verlustanteil / stop_rel > 1`

- Quelle: Methodik 2.178

**2.175** — ✔ N-11 DURCHGEFUEHRT: die Klassen in STREUUNGSEINHEITEN gemessen (in_r geteilt durch den IQA der eigenen Kandidatenwelt, Fenster ab 2018). Ergebnis: krypto `schnitt` +0,059 (1 von 4 Mengen) · themen_etf `vola` +0,062 (2 von 5) · rohstoffe `schnitt` +0,025 (0 von 2) · aktien `schnitt` und `vola` je +0,015 (0 von allen). `zufall` in jeder Klasse sauber

- Quelle: Methodik 2.175 / n80_streuungseinheiten.py

**2.175-aktien** — ⚠️ DIE AKTIEN-EFFEKTE SIND RUND EIN VIERTEL VON KRYPTO (+0,015 gegen +0,059), nicht gleichauf. Meine Handrechnung hatte das Gegenteil nahegelegt - sie stand auf dem falschen Nenner. Der N-8-Nullbefund fuer Aktien bleibt damit ZURUECKGEZOGEN (die Messung war zu grob), aber die Effekte sind dort auch normiert klein

- Quelle: Methodik 2.175

**2.175-etf** — ⚠️⚠️ DER STAERKSTE WERT DES GANZEN LAUFS ist `vola` bei THEMEN_ETF: +0,062 Streuungseinheiten und als einziger auf ZWEI von fuenf zulaessigen Mengen tragend - mehr als Krypto `schnitt` (1 von 4). ⚠️ Der Vorbehalt aus 2.170-etf bleibt: die Klasse hat effektiv nur 1,9 unabhaengige Reihen

- Quelle: Methodik 2.175

**2.175-robust** — ⚠️ UND DER NUECHTERNE GESAMTBEFUND: KEIN Kandidat traegt in KEINER Klasse auf ALLEN zulaessigen Mengen. Krypto `schnitt` 1 von 4, ETF `vola` 2 von 5, alles andere 0. Nach der N-73-Regel ist damit keiner robust - auch nach der Normierung nicht

- Quelle: Methodik 2.175

**2.174** — ⚠️⚠️⚠️ DAS HEBELKONZEPT IST NICHT GESCHEITERT - es wurde auf einer inzwischen GEFALLENEN Kalibrierung fuer gescheitert erklaert. Nutzervorgabe (F-220, woertlich): 'die Wahrscheinlichkeit auf positives Chance-Risiko-Verhaeltnis soll den Hebel dynamisch erzeugen', Zielzone 2-5x

- Quelle: Methodik 2.174 / Recherche 08.09.

**2.174-ist** — ⚠️⚠️ WAS HEUTE GEBAUT IST: die Produktion rechnet `hebel_noetig = verlustanteil / stop_rel`. Die QUOTE geht NICHT ein - `agent/assetklassen.py` sagt es ausdruecklich ('es gibt keinen Zirkelbezug, hebel_noetig haengt an Verlustanteil'). Der Hebel entsteht aus der GEOMETRIE, nicht aus der Wahrscheinlichkeit. Die Nutzervorgabe ist damit NICHT umgesetzt

- Quelle: Methodik 2.174

**2.174-f220** — F-220 rechnete mit einem Kalibrierungsfaktor 0,195 und kam zu 'nur EINE Lage erreicht 2-5x'. ⚠️ Zwei Dinge dazu: (a) der Faktor ist am 05.09. GEFALLEN - F-215s Kalibrierung besteht die Invarianzpruefung nicht (Verfuegbarkeits-Artefakt), und (b) er wird NIRGENDS IM CODE angewandt. Die Produktion rechnet unkalibriert. F-220 selbst ist am 06.09. zurueckgezogen

- Quelle: Methodik 2.174

**2.174-neu** — ✔✔ UNKALIBRIERT MIT DER HEUTIGEN BEITRAGSLAGE GERECHNET (Kapital 10.000, Einsatz 500, Stop 5 %, halbes Kelly, CRV 2,0) FUNKTIONIERT DIE DYNAMISCHE ERZEUGUNG: kein Beitrag 0,00x · mittlere Lage 1,02x · nur funding bestes 3,90x · bestes funding + mittleres turnover 4,56x · nur turnover bestes 9,45x · beide bestes 13,35x. ZWEI Lagen liegen in der Zielzone 2-5x, und die Abstufung ist echt

- Quelle: Methodik 2.174

**2.174-grenzen** — ⚠️ ZWEI EINSCHRAENKUNGEN, benannt: (1) die Spitze 13,35x braucht den vorhandenen Deckel `GRENZEN['hebel_max']` = 10,0. (2) Die Abstufung SPRINGT von 1,02x auf 3,90x - zwischen 'kein Hebel' und 'fast 4x' liegt nichts. Ursache ist die grobe Fuenftel-Aufloesung der Beitraege. Fuer eine feine Zielzone 2-5x reicht sie nicht

- Quelle: Methodik 2.174

**2.173** — ⚠️⚠️ ZWEI EIGENE FEHLDARSTELLUNGEN ZUM STRATEGIESTAND, vom Nutzer korrigiert (08.09.). Ich hatte gesagt, `swing` und `hebel` haetten 'keine Beitraege' und das als Luecke dargestellt. Beides war falsch eingeordnet

- Quelle: Methodik 2.173 / Nutzerkorrektur 08.09.

**2.173-swing** — `swing` IST KEINE LUECKE, SONDERN GESTRICHEN. `Anforderungen_Umbau_28_08.md`: 'hebel x swing entfaellt (Nutzerentscheidung 31.08.: nur Einstieg reicht)' und 'spot x swing ist ausdruecklich gestrichen'. Begruendung dort: bei 1-20 Tagen Horizont ist der praktische Unterschied zu `einstieg` klein, und Swing verlangt ein eigenes Ausstiegswerk

- Quelle: Methodik 2.173

**2.173-hebel** — ⚠️⚠️ DER HEBEL BEKOMMT SEHR WOHL EINE BEWERTUNG - sie ist nur nicht vom Spot UNTERSCHEIDBAR. Im Code geprueft: `wahrscheinlichkeit.Beitrag` hat die Felder klassen/strategien/richtungen, aber KEIN `instrumente`. Und `rechne()` liefert bei Stop 6,4 % gegen 2,5 % und mit Finanzierung 0,02 R dreimal EXAKT dieselbe Quote 0,373033. Das ist der Befund vom 01.09. ('die Bewertung hat keine Instrument-Achse'), nicht 'keine Bewertung'

- Quelle: Methodik 2.173

**2.173-regel2** — Nebenbei belegt: `rechne()` rechnet `kosten_r` aus Gebuehr und Finanzierung, laesst sie aber NICHT in die Quote einfliessen. Regel 2 (Gebuehren gehoeren nicht in die Bewertung) ist im Code korrekt umgesetzt

- Quelle: Methodik 2.173

**2.173-amihud** — ⚠️ UND EINE LUECKE IN MEINER EIGENEN N-76-ARBEIT: ich habe `amihud` nur als NIVEAU gemessen (feste Baender, Regel-3-konform). F-228 hatte die VERAENDERUNG als Hebel-Kandidaten benannt. ⚠️ F-228 ist zwar am 06.09. selbst zurueckgezogen (gemessen auf 'Ziel vor Stop' und/oder der freien Menge) - aber die Frage nach der VERAENDERUNG ist damit weder bestaetigt noch widerlegt. `messe_fremdgroesse.py` trennt beides ausdruecklich: NIVEAU = Eigenschaft, VERAENDERUNG = LAGE

- Quelle: Methodik 2.173

**2.172** — ⚠️⚠️ DIE ZIELGROESSE `bewegung_r` IST UEBER DIE ASSETKLASSEN NICHT VERGLEICHBAR - und das entwertet den N-8-Nullbefund. Sie teilt durch max(5 % Kurs, 0,75 ATR). Gemessen ab 2018: der Boden bindet bei Krypto in 29,1 % der Anker, bei AKTIEN in 97,1 %, bei THEMEN_ETF in 99,2 %, bei Rohstoffen in 97,4 %. Der Stop liegt dort 2,29 / 4,43 / 2,50 ATR entfernt statt 0,75

- Quelle: Methodik 2.172 / Nutzerhinweis 08.09.

**2.172-untermacht** — ⚠️⚠️ DAMIT IST DER AKTIEN-BEFUND UNTERMACHT, KEIN NULLBEFUND. Ein Effekt der Krypto-Groesse haette in Aktien +0,0915 R ergeben - die Trennschaerfe lag bei 0,05 bis 0,10 R, also genau an der Grenze. Gemessen wurden +0,0725. Die Messung KONNTE dort nichts zeigen

- Quelle: Methodik 2.172

**2.172-etf** — ⚠️ Und der ETF-Befund wird dadurch nicht kleiner, sondern GROESSER: `vola` liegt dort bei 0,254 Streuungseinheiten (5 %: 0,322) - das FUENFFACHE des staerksten Krypto-Effekts. Der Vorbehalt aus 2.170-etf bleibt (1 von 5 Mengen, effektiv 1,9 unabhaengige Reihen), aber die Groesse verdient eine eigene Messung

- Quelle: Methodik 2.172

**2.172-lehre** — ⚠️ DIE LEHRE: eine Zielgroesse, die durch eine GEOMETRIE normiert, ist nur dort vergleichbar, wo die Geometrie gleich wirkt. Der 5-%-Boden ist fuer Krypto gebaut (ATR/Kurs 8,6 %) und bindet dort selten; bei Aktien (2,2 %) und ETF (1,1 %) bindet er fast immer. Wer Klassen vergleicht, muss die Effekte in EIGENEN Streuungseinheiten ausdruecken - oder die Geometrie je Klasse kalibrieren

- Quelle: Methodik 2.172

**2.170-rohstoffe** — ROHSTOFFE sind NICHT MESSBAR: 35 Symbole, 28,8 Werte je Tag, nur `50%` und `frei` zulaessig - und dort lautet JEDES Urteil 'KEIN BEFUND'. Die Norm sagt es selbst. Das ist eine Datenlage-Aussage, keine Bewertung

- Quelle: Methodik 2.170

**2.170-etf** — ⚠️ THEMEN_ETF: `vola` traegt bei 10 % (+0,2303 [+0,0993 .. +0,3712]) und zeigt einen MONOTON fallenden Verlauf ueber alle fuenf Mengen (+0,2911 / +0,2303 / +0,0919 / +0,0382 / +0,0287) - ein Effekt, der auf die selektiertesten Werte konzentriert ist. Kein Mengenartefakt: `zufall` zeigt in KEINER Klasse einen fallenden Verlauf

- Quelle: Methodik 2.170

**2.170-etf-vorbehalt** — ⚠️⚠️ ABER DER ETF-BEFUND STEHT AUF DUENNEM EIS: nur 1 von 5 Mengen erreicht 'TRAEGT' (N-73-Regel: nicht robust), UND die Klasse hat die hoechste Querschnittskorrelation aller vier - im Mittel 0,527 gegen 0,209 bei Aktien. Das entspricht effektiv 1,9 unabhaengigen Reihen. 293 Themen-ETF halten grossteils DIESELBEN Aktien; der Blockbootstrap behandelt Zeit-, nicht Querschnittsabhaengigkeit

- Quelle: Methodik 2.170

**2.170-g6** — WAS FUER G-6 FOLGT: die Sperre der vier Klassen nach DATENLAGE bleibt begruendet. Fuer Aktien und Rohstoffe gibt es keinen tragenden Beitrag, bei Themen-ETF nur einen nicht robusten Hinweis. ⚠️ Die Sperre ist damit nicht mehr nur 'nach Datenlage' - fuer Aktien ist sie jetzt GEMESSEN begruendet

- Quelle: Methodik 2.170

**2.170-fenster** — Das gemeinsame Fenster ab 2018-01-01 stand VOR der Messung fest und ist vom Nutzer bestaetigt: 'zu den daten ab 1972 - auch hier aehnlich wie bei krypto, waere ich der Meinung sollte man vorsichtig sein'. Ohne es haette man Krypto ab 2017 gegen Aktien ab 1972 gestellt - und Aktien haetten mit 211 gegen 42 Bloecken allein durch Aussagekraft besser ausgesehen

- Quelle: Methodik 2.170

**2.169** — ⛔ N-9 ERLEDIGT: KEINER DER VIER TERMINMARKT-KANAELE TRAEGT AUF `bewegung_r`. `oi_je_umsatz` 0 von 3 zulaessigen Mengen, `long_bias` 0 von 3, `top_bias` 0 von 2, `taker_bias` 0 von 3. Die Referenz `oi_aenderung` dagegen 3 von 3 - ihr Band schliesst in JEDER Menge die Null aus (+0,0469 / +0,0243 / +0,0145). `zufall` traegt auf keiner

- Quelle: Methodik 2.169 / n78_terminmarkt_kanaele.py

**2.169-zielgroesse** — ⚠️⚠️ DAMIT UEBERTRAGEN SICH DIE N-17b-BEFUNDE NICHT. Dort trugen `oi_je_umsatz`, `long_bias` und `top_bias` - aber gegen FRONTLOADING, eine andere Zielgroesse. Genau diese Verwechslung hat F-207 schon einmal erzeugt. Ein Kandidat, der die Frontloading-Quote verschiebt, verbessert deshalb nicht das ERGEBNIS

- Quelle: Methodik 2.169

**2.169-redundanz** — Zwei Redundanzen sauber gemessen, beide INNERHALB der Auswahl: `oi_je_umsatz` gegen `turnover` -0,490 - beide sind umsatznormiert, das ist eine echte Ueberschneidung. Und `long_bias` gegen `top_bias` +0,950, was N-17b (+0,955) exakt REPRODUZIERT. Die drei uebrigen Paare liegen unter 0,16

- Quelle: Methodik 2.169

**2.169-gesamt** — ⚠️ DER GESAMTBEFUND: mit den vorhandenen Daten gibt es keinen vierten Beitrag AUS DEN GEPRUEFTEN QUELLEN. Kursreihe erschoepft (2.168), Terminmarkt erschoepft (nur `oi_aenderung` traegt), onchain liefert `turnover`, Binance liefert `funding`

- Quelle: Methodik 2.169

**2.169-korrektur** — ⚠️⚠️ EINSCHRAENKUNG, am selben Abend gefunden: 'alle Quellen erschoepft' war ZU WEIT gefasst. Die Durchsicht des Datenbestands (auf Nutzerhinweis) zeigt zwei weitere Quellen, die es gibt und die gemessen WURDEN - aber unter der ALTEN Norm vom 30.08., vor den heutigen Mengenregeln: `tvl_historie` (188 Symbole, 261.406 Zeilen, ab 2018-02) und `adractcnt` - aktive Adressen (66 Symbole, 203.378 Zeilen, ab 2013-01), beide in `messe_fremdgroesse.py`. Sie gehoeren unter der heutigen Norm nachgemessen - das ist ein OFFENER Punkt, kein erledigter

- Quelle: Methodik 2.169

**2.168** — ⛔ N-6 IST FALSCH GESTELLT UND WIRD GESTRICHEN. Die Abdeckungsluecke ist kein BETRIEBSproblem: ueber die Watchlist mit k=2 haben nur 4,2 % der gewaehlten Anker keinen Beitrag, und das sind FLOKI und XNO. ⚠️ Nutzervorgabe 07.09. woertlich: bei Meme- und Smallcap-Werten ist eine fehlende Bewertung 'als UNKRITISCH zu bewerten'

- Quelle: Methodik 2.168 / n77_ist_die_abdeckung_repraesentativ.py

**2.168-mess** — Als MESSfrage ist die Luecke groesser: auf der Messbasis haben 32,4 % der gewaehlten Anker keinen Beitrag. Geprueft, ob die abgedeckte Teilmenge deshalb verzerrt: `schnitt` und `vola` (beide 100 % Abdeckung) zeigen zwischen den Gruppen -0,0774 bzw. -0,0885, beide Baender schliessen null ein. ⚠️ ABER die Trennschaerfe liegt bei 0,10 R - groesser als die Effekte, um die es geht (0,02 bis 0,09 R). Also NICHT ENTSCHIEDEN auf der Aufloesung, die zaehlen wuerde

- Quelle: Methodik 2.168

**2.168-kontrolle** — ⚠️⚠️ Und die Kontrolle hat einen eigenen Fehler gefangen: der erste Anlauf differenzierte die ROHEN Tagesreihen der beiden Gruppen. Bei 35 gegen 20 Ankern je Tag ist die N-65-Verzerrung UNGLEICH - `zufall` zeigte prompt einen 'Unterschied' von -0,0212 [-0,0417 .. -0,0038]. Mit je Gruppe entzerrten Reihen: -0,0056, Band schliesst null ein

- Quelle: Methodik 2.168

**2.168-erschoepft** — ⚠️⚠️ WARUM EIN NEUER KURSREIHEN-BEITRAG NICHT DIE ANTWORT IST: die Kombinationsmatrix vom 27.08. hat es bereits festgehalten - von 17 Merkmalen sind M2 bis M12 und M15 bis M17 ALLE aus Kurs, Volumen oder Modellantwort abgeleitet. 'Die Information steckt nicht in den Kursdaten. Wer nur Kursreihen kombiniert, kombiniert Ableitungen derselben Quelle.' Die heutige Durchsicht bestaetigt das: schnitt, vola, rsi, amihud, momentum, schnitt50 sind alle gemessen, keiner traegt robust

- Quelle: Methodik 2.168

**2.168-quellen** — DIE BEIDEN ECHTEN FREMDQUELLEN, geprueft: M13 Terminmarkt ist REALISIERT (122 Symbole, 1.734 Tage bis 02.09.2026) - deckt aber nur 122 von 524 ab und schliesst die Luecke NICHT. M14 Entwickleraktivitaet: das Messwerkzeug existiert, aber in KEINER Datenbank liegt eine Tabelle dazu. ⚠️ Es gibt derzeit keine verfuegbare Quelle, die die Luecke schliessen wuerde

- Quelle: Methodik 2.168

**2.168-offen** — ⚠️ WAS STATTDESSEN OFFEN IST, ohne neue Datenquelle: der Terminmarkt liefert VIER weitere Kanaele, die nicht registriert sind - `oi_wert`, `long_bias`, `top_bias`, `taker_bias`, je 122 Symbole und rund 1.400 bis 1.736 Tage. Zwei davon (long_bias, top_bias) sind in N-17b als nicht unabhaengig vom RSI gemessen; `oi_wert` und `taker_bias` nie unter der Norm

- Quelle: Methodik 2.168

**2.167** — ⛔ `amihud` TRAEGT AUCH AN DER POSITIONSGROESSE NICHT - aber jetzt mit einem GRUND, nicht als Nullbefund. Zwei Hypothesen, beide gemessen, beide verneint: der Stop rutscht nicht, und die Mehrstreuung liegt auf der falschen Seite

- Quelle: Methodik 2.167 / n76_amihud_an_der_groesse.py

**2.167-luecke** — ⚠️⚠️ DER STOP-DURCHSCHLAG EXISTIERT IN KRYPTO PRAKTISCH NICHT: 71 Faelle von 728.920 Ankern (0,0097 %). Der Grund generalisiert - KRYPTO HANDELT DURCHGEHEND. Ein Kurstag, der GANZ unter dem Stop liegt, verlangt eine Uebernachtluecke, und die gibt es an einem 24/7-Markt nicht. Die Kontrolle (gemischt) liefert 15/10/20/14 gegen echte 0/14/18/28/11 - nicht unterscheidbar

- Quelle: Methodik 2.167

**2.167-rm1** — ✔✔ DARAUS FOLGT ETWAS NUETZLICHES, unabhaengig von amihud: RM-1 rechnet `max_position = risk_budget / (stop_abstand / kurs)` und SETZT VORAUS, DASS DER STOP HAELT. Fuer Krypto ist diese Annahme belegt - in 99,99 % der Anker war der Stop zum Stoppreis handelbar

- Quelle: Methodik 2.167

**2.167-open** — ⚠️⚠️ KORREKTUR 07.09. abends: N-76 nannte als Vorbehalt 'ohne Eroeffnungskurs ist nur nachweisbar, was den GANZEN Tag unter dem Stop lag'. DIE SPALTE `open` GIBT ES - in `price_history_ohlc`, zu 100 % gefuellt, in ALLEN vier Assetklassen. Nur `messe_eigenschaft_beitrag.lade()` liest sie nicht. Der Stop-Durchschlag waere damit EXAKT messbar statt konservativ genaehert - gefunden erst, als der Nutzer eine Durchsicht des Datenbestands verlangte

- Quelle: Methodik 2.167 / Datenbestandsdurchsicht 07.09.

**2.167-seite** — ⚠️⚠️ DIE ZWEITE HYPOTHESE (illiquide Werte streuen breiter, also kleiner dimensionieren) IST WIDERLEGT - und zwar an der SEITE. Der Interquartilsabstand steigt zwar (3,251 -> 3,780 gegen eine Kontrollspanne von nur 0,027), aber er steigt VOLLSTAENDIG NACH OBEN: P75-Median 1,342 -> 2,054, waehrend Median-P25 von 1,909 auf 1,727 FAELLT. Auf der VERLUSTSEITE sind illiquide Werte enger. Kleiner zu dimensionieren waere unbegruendet

- Quelle: Methodik 2.167

**2.167-geometrie** — Der naheliegende Einwand wurde geprueft und AUSGERAEUMT: der 5-%-Boden koennte bei ruhigen Werten oefter binden und die kleinere R-Streuung erzeugen. Gemessen bindet er bei Band 0 in 38,2 % und bei Band 4 in 38,5 % der Anker, ATR/Kurs 0,0790 gegen 0,0752 - praktisch gleich. Der Unterschied ist echt, nur zeigt er nach oben

- Quelle: Methodik 2.167

**2.167-ausgabe** — ⚠️ ZWEI EIGENE AUSGABEFEHLER, beide zwischen Ergebnis und Deutung gefangen (Methodik 2.80): 'Durchschlag 0,0 %' war GERUNDET statt null - die Mittelwerte standen auf 11 Faellen, ohne dass die Zahl dastand. Und die STANDARDABWEICHUNG als Streuungsmass lag bei 250, getragen von 0,06 % der Anker (ein Coin, der sich in 20 Tagen verzwanzigfacht, ergibt bei 5 % Stopweite 400 R). Beides ersetzt durch absolute Zahlen und den Interquartilsabstand

- Quelle: Methodik 2.167

**2.166** — DIE DURCHSICHT DER GEFALLENEN BEITRAEGE: bei VIER von fuenf ist ein Messfehler ausgeschlossen. `rsi` und `amihud` tragen auf KEINER Achse (quer wie laengs) und ueber alle zulaessigen Mengen (N-73) - sie sind sauber abgelehnt. `schnitt` ist vierfach geprueft. Offen bleibt allein `H`

- Quelle: Methodik 2.166 / n75_quer_gegen_laengs.py

**2.166-these** — ⚠️ MEINE THESE WAR: die Beitragsmaschinerie rangt INNERHALB DES TAGES, ist also rein querschnittlich - Kandidaten mit Zeitreihen-Natur (`H`, `rsi`, `schnitt`) waeren mit dem falschen Instrument gemessen. GEMESSEN UND WIDERLEGT: kein Kandidat traegt NUR laengs. Kontrollen halten - `zufall` traegt auf keiner Achse, `funding` (ein CS-Signal) ist quer staerker als laengs (+0,0229 gegen +0,0011), wie es muss

- Quelle: Methodik 2.166

**2.166-momentum** — ⚠️⚠️ AUSNAHME `momentum`: sein Urteil 'traegt nicht' ist NICHT INTERPRETIERBAR. Spearman +0,930 zur Auswahlgroesse `momentum250` der Stufe 5 - er wird auf der Menge gemessen, die er selbst definiert. Das ist kein Befund ueber Momentum, sondern eine Tautologie. Er sitzt bereits an Stufe 5

- Quelle: Methodik 2.166

**2.166-h** — ⚠️ `H` IST DER EINZIGE, BEI DEM EIN MESSFEHLER OFFEN BLEIBT. Er braucht Marken, Stop und Ziel - nicht nur Kursreihen - und laesst sich deshalb durch `messe_kandidaten_als_regel` gar nicht messen. Sein Fall beruht auf gepoolt (+4,5) gegen je Tag (-1,02). ⚠️ Und er ist ein ABSOLUTES Kriterium je Asset, waehrend die Maschinerie querschnittlich rangt - `messe_h_als_filter` nennt genau das im eigenen Kopf

- Quelle: Methodik 2.166

**2.166-woanders** — WO EIN GEFALLENER SINNVOLL WAERE: `amihud` misst Illiquiditaet - das ist eine Frage der AUSFUEHRBARKEIT und POSITIONSGROESSE (wieviel laesst sich handeln, ohne den Kurs zu bewegen), nicht der Richtung. Dort nie geprueft. `schnitt` traegt auf der VERBILLIGUNG bei H90 (+0,0292, im flachsten Fuenftel +0,0481) - das ist die AKKUMULATION, nicht `einstieg`. ⚠️ Kein Widerspruch zu 2.164: andere Zielgroesse, anderer Horizont

- Quelle: Methodik 2.166

**2.166-register** — ⚠️ Beim Durchsehen gefunden: das `live`-Feld von `turnover` nannte noch die am 07.09. ZURUECKGENOMMENEN Stufen (+0,33 x3 / -0,48 x2) - waehrend die `warnung` desselben Eintrags die Ruecknahme beschrieb. Das Blatt widersprach sich selbst und dem Code. Die Selbstpruefung fing es nicht: sie prueft nur, OB ein Merkmal vorkommt. Jetzt vergleicht sie die ZAHLEN (scharf getestet)

- Quelle: Methodik 2.166

**2.165** — ✔✔ N-7 ERLEDIGT: `turnover`s STUFEN SIND RICHTIG. Entzerrt nachgerechnet ergibt der Querschnitt +3,13 / +0,76 / +0,22 / -1,73 / -2,38 gegen registriert +3,15 / +0,83 / +0,22 / -1,79 / -2,40 - Abweichung hoechstens 0,07 Punkte. Monoton, Spanne +5,51 gegen +5,55. Kontrolle `zufall` bei maximal 0,38 Punkten. R-R11 vorab erfuellt: `rechne_turnover_beitrag.py` reproduziert die Tabelle exakt

- Quelle: Methodik 2.165 / n74_turnover_stufen_nachgerechnet.py

**2.165-warum** — ⚠️ WARUM DIE ENTZERRUNG HIER NICHTS AENDERT, bei `schnitt` aber alles: im Querschnitt sind die Fuenftel GLEICH GROSS (9,0 bis 9,8 Anker je Tag). Die Verzerrung aus N-65 trifft alle fuenf gleich und hebt sich im Bezug auf den Mittelwert der fuenf auf. Bei `schnitt` auf der selektierten Menge hatte Fuenftel 0 dagegen 1,49 Anker und Fuenftel 4 dann 29,35

- Quelle: Methodik 2.165

**2.165-auswahl** — ⚠️ Auf der AUSWAHL (50 %) waere die Tabelle um 25 % steiler: +4,04 / +0,96 / -0,04 / -2,06 / -2,90, Spanne +6,94. Das passt zur Richtung aus N-73 (Wirkung dort 48 % staerker). ⚠️ ABER: die Fuenftel haben dort nur 3,9 bis 5,2 Anker, und die Auswahl nach momentum250 ist nur ein STELLVERTRETER fuer die Werte, die in der Kette wirklich bis zur Bewertung kommen. Die registrierte Tabelle UNTERSCHAETZT also - und unterschaetzen ist die sichere Richtung

- Quelle: Methodik 2.165

**2.165-entscheidung** — EMPFEHLUNG: Tabelle NICHT aendern. Sie reproduziert, ist monoton, haelt der Entzerrung stand und ihre Ableitungsbasis (voller Querschnitt) ist GENAU die, auf der `marktrang` auch in der Produktion rangt. Die steilere Variante stuende auf duennerer Besetzung und einem Stellvertreter - und loeste R-R9 aus (Neukalibrierung der Schwelle 0,080) ohne belegten Gewinn

- Quelle: Methodik 2.165

**2.164** — ✔✔ DIE DURCHSICHT ALLER KANDIDATEN (N-5) ist durch und faellt BERUHIGEND aus: von zehn Kandidaten aendern nur ZWEI ihr Urteil mit der Menge. `amihud`, `rsi`, `schnitt50`, `vola`, `momentum` und `funding` urteilen ueber alle Mengen gleich - ihre Befunde stehen. `zufall` traegt auf keiner Menge

- Quelle: Methodik 2.164 / n73_durchsicht_kandidaten.py

**2.164-schnitt** — ⚠️⚠️ `schnitt` IST NICHT ROBUST: zulaessig sind {10 %, 20 %, 50 %, frei}, aber er traegt NUR bei 20 % (+0,1759 [+0,0715 .. +0,2907]). Bei 10 % steht fast derselbe Punktschaetzer (+0,1780) mit breiterem Band [+0,0274 .. +0,3361] - 'nicht trennbar'. Der N-59-Befund haengt an der Wahl 20 %

- Quelle: Methodik 2.164

**2.164-regel** — ⚠️ UND EIN DENKFEHLER IN DER EIGENEN REGEL, von der Durchsicht aufgedeckt: die SCHMALSTE zulaessige Menge ist zugleich die RAUSCHENDSTE. Sie zum alleinigen Massstab zu machen bestraft Kandidaten mit guter Abdeckung. Richtig: die Zulaessigkeit sortiert aus, was zu duenn ist - das URTEIL muss ueber ALLE zulaessigen Mengen halten. Gebaut als `zulaessige_mengen()`

- Quelle: Methodik 2.164

**2.163** — ⚠️⚠️ DIE ZEITSTABILITAET, korrekt gemessen: jeder Beitrag auf SEINER Menge, Trennschaerfe ZENTRIERT. `oi_aenderung` stabil bis 0,05 R (-0,0051), `turnover` und `funding` stabil bis 0,10 R (+0,0256 / +0,0415), `zufall` stabil bis 0,05 R. ⚠️ `schnitt` auf 10 %: -0,0647 [-0,3098 .. +0,2161] bei einer Trennschaerfe von >0,20 R - UNENTSCHIEDEN, weder stabil noch instabil nachgewiesen

- Quelle: Methodik 2.163

**2.163-schnitt** — Fuer `schnitt` bleibt das PRAKTISCHE Ergebnis unveraendert, aber der Grund ist schwaecher: nicht 'instabil belegt', sondern 'nichts davon entscheidbar'. Die Stufen sind nicht monoton (2.158), die heutige Wirkung nicht trennbar (+0,1152 [-0,0377 .. +0,2687] ab 2022 auf 10 %), die Stabilitaet unentschieden. ⚠️ Drei offene Fragen sind keine Bauentscheidung

- Quelle: Methodik 2.163

**2.163-massstab** — ⚠️⚠️ UND EIN BEFUND UEBER `schnitt` SELBST: sein Haelftenunterschied DREHT mit der Menge (+0,2238 bei 20 %, -0,0647 bei 10 %). Bei `funding` (+0,0473 / +0,0415) und `zufall` (-0,0083 / -0,0229) tut er das NICHT. Eine Groesse, deren Vorzeichen am Messfenster haengt, ist keine verlaessliche Grundlage - das ist die stehende Vorgabe 'der Massstab entscheidet das Vorzeichen', hier zum wiederholten Mal

- Quelle: Methodik 2.163

**2.163-anker** — R-R11 nach dem Umbau: alle SIEBEN Anker aus `messbasis_anker.json` reproduzieren auf fuenf Stellen. Das Hinzufuegen von `50%` und `menge_nach_datenlage` hat keine bestehende Messung verschoben

- Quelle: Methodik 2.163

**2.160-heute** — ⛔⛔ UND ER TRAEGT HEUTE NICHT MEHR NACHWEISBAR - weder allein noch in der Kette. Allein: ab 2022 +0,0414 [-0,0307 .. +0,1002], ab 2023 +0,0478, ab 2024 +0,0855 - kein Band schliesst null aus. In der Kette: ab 2022 +0,0165, ab 2023 +0,0216, ab 2024 +0,0264 - ebenfalls keines

- Quelle: Methodik 2.160 / n69_traegt_er_heute_noch.py

**2.160-kontrolle** — ⚠️⚠️ UND ES LIEGT NICHT AN DER MESSDAUER: `funding` traegt in DENSELBEN Fenstern - ab 2022 +0,0157 [+0,0043 .. +0,0318], ab 2023 +0,0170, ab 2024 +0,0182 - mit einem KLEINEREN Effekt als `schnitt`. `schnitt`s Baender sind rund fuenfmal breiter: der Effekt ist gross, aber zu unruhig

- Quelle: Methodik 2.160

**2.160-epoche** — Der Jahresverlauf zeigt die Quelle: 2019 +0,4532 / 2020 +0,5100 / 2021 +0,3440 / 2022 +0,0187 / 2023 -0,0498 / 2024 +0,1603 / 2025 +0,1280 / 2026 -0,1158. ⚠️ `funding` zeigt DASSELBE Muster schwaecher (2020 +0,2876, danach +0,01 bis +0,03) - ein Teil gehoert der EPOCHE, nicht dem Kandidaten: der fruehe Kryptomarkt war ineffizienter

- Quelle: Methodik 2.160

**2.160-genauigkeit** — ⚠️ WAS NICHT GESAGT IST: 'traegt heute nicht NACHWEISBAR' ist nicht 'traegt nicht'. Die Trennschaerfe liegt allein bei 0,10 R und in der Kette bei 0,05 R; die gemessenen Werte liegen darunter. Es ist UNENTSCHIEDEN, nicht widerlegt - aber eine Bauentscheidung braucht einen Nachweis, keine offene Frage. Das Fenster ab 2024 hat zudem nur 15 Bloecke und verfehlt die eigene 20er-Regel

- Quelle: Methodik 2.160

**2.160-methode** — Und WARUM N-60 nicht weiterkam: es fragte 'traegt er in A?' UND 'traegt er in B?' - zwei halbierte Tests. Die richtige Frage ist EINE: 'ist (A-B) von null zu trennen?' auf der ganzen Reihe. Der Test wurde auf Kunstdaten geeicht (40 Laeufe je Fall): 18 % Fehlalarm bei Wahrheit null statt nominell 10 %, 100 % Treffer ab +0,03. Er erklaert also zu OFT einen Unterschied - was den gefundenen Unterschied vorsichtig, einen Nullbefund aber stark macht

- Quelle: Methodik 2.160

**2.159** — ✔✔ `schnitt` TRAEGT ZUSAETZLICH - ueber die Kette simuliert. Nach Auswahl (Stufe 5) UND nach funding + turnover gemessen: +0,0397 R entzerrt, Rohband [+0,0132 .. +0,0751] - es schliesst den eigenen Nullwert +0,0052 AUS. Die Kontrolle `zufall` an derselben Stelle: +0,0058 entzerrt, Rohband [-0,0003 .. +0,0230] - schliesst ihn EIN. 2.461 Kalendertage

- Quelle: Methodik 2.159 / n67_schnitt_ueber_die_kette.py

**2.159-quote** — Die Durchlassquote der simulierten Kette: 50,6 Anker je Tag nach der Auswahl, 43,0 nach funding + turnover (die beiden sperren nur 15 %, weil ihre Abdeckung bei 56 % bzw. 13 % liegt), davon sperrt `schnitt` weitere 21,6 %

- Quelle: Methodik 2.159

**2.159-grenze** — ⚠️ WAS OFFEN BLEIBT: die Rohbaender von `schnitt` und `zufall` UEBERLAPPEN in [+0,0132 .. +0,0230]. Der Nachweis stuetzt sich darauf, dass nur `schnitt`s Band den eigenen Nullwert ausschliesst - nicht auf getrennte Baender. Und eine TRENNSCHAERFE wurde in diesem Aufbau nicht bestimmt

- Quelle: Methodik 2.159

**2.158** — ⚠️⚠️ DIE FUENF STUFEN FUER `schnitt` LASSEN SICH NICHT HERLEITEN. Entzerrt ergeben sie +4,07 / +5,55 / +9,49 / +1,71 / -4,65 Punkte - ein BUCKEL mit Hochpunkt bei Fuenftel 2, nicht bei 0. Die Vorabfestlegung in `messe_schnittabstand_beitrag.py` verlangt Monotonie fuer nutzbar. Zum ZWEITEN Mal bei derselben Groesse (31.08.: +1,27 +1,59 +0,24 -1,28 -1,82, ebenfalls Buckel) und in derselben Form wie der 27.08.-Buckel

- Quelle: Methodik 2.158 / n64+n65

**2.158-verzerrung** — ⚠️⚠️ Und die eigene Kontrolle fing einen Konstruktionsfehler: `median(Gruppe) - median(alle)` lieferte bei GEMISCHTEN Raengen +0,10 bis +0,16 R statt null - der Stichprobenmedian kleiner Gruppen ist bei schiefer Verteilung nach oben verzerrt. Fuenftel 0 hat 1,49 Anker je Tag. Die Verzerrung war so gross wie die gesuchten Effekte; alle Zahlen sind seither entzerrt (Nullwert je Gruppe abgezogen, 20 Ziehungen)

- Quelle: Methodik 2.158 / n65

**2.158-form** — Die FORMFRAGE bleibt OFFEN. Gleichstandsfrei gemessen (Schalter fragt `kennzahl<0` direkt statt ueber den Rang): SCHALTER +0,0370 R [-0,0511 .. +0,2498], REGLER -0,1399 R [-0,0627 .. +0,0440] fuer die Gruppe UEBER dem Schnitt. Die Rohbaender UEBERLAPPEN - die Formen sind nicht unterscheidbar

- Quelle: Methodik 2.158 / n66

**2.158-redundanz** — ⚠️ `schnitt` und die AUSWAHL der Kette messen teilweise dasselbe: Spearman +0,704 im vollen Tagesquerschnitt, aber +0,418 INNERHALB der Auswahl - und nur die zweite Zahl zaehlt, weil Stufe 12 auf der bereits ausgewaehlten Menge arbeitet. Ursache: hohes 250-Tage-Momentum heisst fast zwangslaeufig ueber dem eigenen 200-Schnitt. 60,6 % der Gewaehlten liegen darueber, im vollen Querschnitt nur 34,8 %

- Quelle: Methodik 2.158 / n66

**2.157** — ⚠️⚠️ `schnitt` UND DAS AKKUMULATIONSMASS SIND DIESELBE GROESSE: `c/mean(200)-1` als Regler gegen `kurs<sma200` als Schalter. Sie standen nie nebeneinander, weil der 28.08.-Befund nie ins Register kam und `schnitt` am 31.08. auf kontaminierter Basis verworfen wurde (2.153). Damit sind 'schnitt wieder einbauen' und 'Akkumulationsmass als Beitrag' EINE Aufgabe

- Quelle: Methodik 2.157 / n63_form_der_achse.py

**2.157-regler** — Was aus N-63 BLEIBT: der Regler-Arm reproduziert den registrierten Anker auf die vierte Stelle (+0,17593 gegen +0,1759). Dort gibt es keine Gleichstaende. Die FORMFRAGE ist damit wieder OFFEN

- Quelle: Methodik 2.157 / R-R11

**2.157-anker** — ⚠️ Und die Messung REPRODUZIERT den registrierten Anker auf die vierte Stelle: +0,17593 (messbasis_anker.json, N-59) gegen +0,1759 heute. Der Schalter kommt aus DERSELBEN Kandidatenwelt, nur die Kennzahl ist 0/1 - der Unterschied kann nicht aus der Datenlage stammen

- Quelle: Methodik 2.157 / R-R11

**2.157-grenze** — ⚠️ WAS DAMIT NICHT GESAGT IST: der Schalter verliert auf `bewegung_r`. Das 28.08.-Mass wurde auf der VERBILLIGUNG gemessen (Perzentilrang der eigenen Reihe) - ein anderes Erfolgsmass fuer eine andere Frage. 2.154 bleibt dort gueltig

- Quelle: Methodik 2.157

**2.156** — ⚠️⚠️ BTC/ETH/SOL BRAUCHEN KEINE EIGENE LOESUNG. Die -0,0251/-0,0308/-0,0291 aus 2.154 sind mit p 0,833 NICHT von null zu trennen - drei Reihen, 8 bis 12 Bloecke. Auf allen 507 Reihen nach Tiefanteil geschichtet traegt `UNTER_SMA` in 4 von 5 Fuenfteln, und im FLACHSTEN - dort liegen BTC (2,0 %) und ETH (9,7 %) - am staerksten von allen: +0,0481 (p 0,000, 101 Reihen). SOL liegt im zweiten (+0,0246, p 0,035)

- Quelle: Methodik 2.156 / n62_wirkung_nach_tiefe.py

**2.156-tiefe** — Der ZAEHLBEFUND dahinter (3.003 Tage, keine Untermacht): BTC liegt an 2,0 % der Tage unter -40 % vom eigenen 200-Schnitt, das uebrige Universum an 20,6 % - zehnfacher Unterschied. Umgekehrt liegt BTC an 21,1 % der Tage ueber +30 % (Universum 13,2 %). Die Kernwerte sind seltener tief, nicht anders gebaut

- Quelle: Methodik 2.156 / n61_kernwerte_akkumulation.py

**2.156-eigenschaft** — ⚠️ Und der Schichter ERKLAERT die Wirkung nicht: der Verlauf ueber die fuenf Fuenftel ist nicht monoton (+0,048 / +0,025 / +0,016 / +0,025 / +0,032). Das REPRODUZIERT den Vorbefund `eigenschaften_erklaeren_den_vorsprung_nicht` - es ist kein neuer Nullbefund. Vorab benannt, nicht nachtraeglich

- Quelle: Methodik 2.156

**2.155** — ⚠️⚠️ Die DURCHLASSQUOTE ist entschieden: Schwelle 0,080 R = 16,4 % Durchlass = rund 6 Empfehlungen/Woche. R-R9 verlangt sie als NUTZERENTSCHEIDUNG, und sie stand seit dem 30.08. aus - damit war jede Kalibrierung willkuerlich. Haerter filtern ist gemessen SCHAEDLICH (0,010: -0,0558 je verworfenem Signal)

- Quelle: Nutzerentscheidung 07.09. / agent/potential.py

**2.155-sicht** — ⚠️⚠️ Und der Befund dahinter: die Zahl, die entscheidet OB eine Empfehlung entsteht, war UNSICHTBAR - nur Konstante im Code, kein `bewertung`-Block in config.yaml, kein Wort in Mail oder GUI. Nutzerhinweis: 'so einen Parameter vergesse ich in Kuerze und du auch - die Doku reicht bei so einer zentralen Einstellung nicht'. Jetzt: config.yaml steuert ohne Neustart, jede Mail nennt Wert/Quelle/Alter, fuenf Suitepruefungen halten es offen

- Quelle: Methodik 2.155 / paket Kalibrierung

**2.155-leiche** — ⚠️ Beim Aufraeumen gefunden: der Docstring in potential.py behauptete noch 'steht seit 07.09. auf 0,005' - der Wert der am selben Tag zurueckgenommenen Aenderung. Genau der Fall, vor dem die Datei selbst warnt ('eine falsche Zahl im Docstring einer Schwelle ist teurer als anderswo')

- Quelle: Methodik 2.155

**2.154** — Das AKKUMULATIONSMASS haelt auf der neuen Basis: UNTER_SMA +0,0288 (28.08.: +0,0283), TIEFPUNKT +0,4242 BITGLEICH, WOCHENTAG -0,0008. Kennlinie weiter monoton ueber neun Baender. BTC -0,0251 / ETH -0,0308 / SOL -0,0291 bis auf die dritte Stelle reproduziert

- Quelle: Methodik 2.154 / messe_akkumulationsmass.py

**2.154-achse** — ⚠️ Das Werkzeug war heute unsicher: es fragte OHNE Filter ab. Die Symbole fielen durch die Lueckenlosigkeitspruefung heraus (Aktien haben Wochenendluecken), aber die KALENDERACHSE blieb bei 14.728 statt 3.309 Tagen - und ueber die laeuft der zirkulaere Verschub. Eine zu enge Nullverteilung erzeugt falsch positive Befunde. Gefixt

- Quelle: Methodik 2.154

**2.153** — Der 31.08.-Befund zu `schnitt` ist ABGELOEST: reproduziert mit demselben Werkzeug drehen alle Vorzeichen (H5 -0,0069 -> +0,0092). Ursache: die Messung lief auf 1.314 Symbolen inkl. 798 Nicht-Krypto; der N-19-Fix kam erst am 03.09.

- Quelle: Methodik 2.153

**2.152** — Der Zustand der Kette je Strategie: bei `einstieg` ENTSCHEIDET Stufe 12 (funding+turnover), bei `akkumulation` WINKT SIE DURCH (vermessen=False, Notiz statt Sperre - eine Sperre ohne Beitraege waere eine Sperre nach Datenlage, Regel 4)

- Quelle: Methodik 2.152

**2.152-akkum** — ⚠️⚠️ Das Akkumulationsmass IST `schnitt` (Abstand zum 200-Schnitt, H90 statt H20). Gemessen am 28.08., monoton ueber NEUN Baender in beiden Kalenderhaelften - aber es kam NIE ins Kandidatenregister. N-59 fand am 07.09. denselben Wert fuer `einstieg`, ohne dass die Verbindung gezogen war

- Quelle: Methodik 2.152

**2.152-nummer** — ⚠️ Namensschatten: der `entscheider` ist die ZWOELFTE Stufe, heisst aber ueberall ,Stufe 11'. `terminmarkt` wurde nachtraeglich eingefuegt (N-14). Folgenlos, weil der Code ueber NAMEN adressiert - jetzt in `rollen_gate.STUFEN` vermerkt

- Quelle: Methodik 2.152

**2.151** — Die sieben F-198-Kryptoreihen sind GELADEN (8 von 183, 13.168 Kerzen; 175 zu kurz). Messbasis 516 -> 524. Die Trennung haelt: DASH aktien 1.440 Kerzen ab 2020, krypto 2.721 ab 2019. Kursprobe eindeutig: T 0,0044 $ (Threshold, nicht AT&T)

- Quelle: Methodik 2.151 / lade_messreihen.py

**2.151-filter** — ⚠️ Ohne den Fix waeren SECHS Aktien-/ETF-Reihen mit Kryptokerzen verwoben worden (C, DASH, MDT, STX, BOND, DIA) - und die sieben Kryptoreihen haette die 1:1-Zuordnung trotzdem verworfen. Beide Haelften des Fixes waren noetig

- Quelle: Methodik 2.151

**2.151-anker** — Beim Basiswechsel kippen ZWEI Urteile - beide auf der FREIEN Menge (funding traegt->traegt nicht, turnover nicht trennbar->traegt). Die Wirkungen bewegten sich nur um 0,002-0,003 R. JEDER Anker auf der SELEKTIERTEN Menge ist unveraendert - `schnitt` bleibt Kandidat (+0,17593 statt +0,17072)

- Quelle: Methodik 2.151

**2.151-suite** — ⚠️ Eine Suite-Pruefung hatte selbst den Fehler, den sie verhindern soll: sie pruefte gegen `messreihen` (1:1) und meldete die sieben Kryptowerte als ,Nicht-Krypto'. Umgestellt auf `price_history_ohlc.assetklasse`

- Quelle: Methodik 2.151

**2.150** — ⚠️⚠️ `marktrang.schnitte()` rangte gegen ALLE 1.314 Symbole der Messbasis - 798 davon Nicht-Krypto. Der Krypto-Schnittrang lief gegen AAPL. Gefixt: assetklasse='krypto' an beiden Stellen, 1.314 -> 516

- Quelle: Methodik 2.150 / agent/marktrang.py

**2.150-zufall** — ✔ Es schlug nicht durch, weil `schnitt_werte()` einen Binance-USDT-Preis braucht - den haben Aktien nicht (0 von 29 Watchlist-Werten wechselten das Fuenftel). ⚠️ Aber es war Schutz durch ZUFALL der Datenlage, nicht durch Design

- Quelle: Methodik 2.150

**2.150-acht** — ⚠️ Acht Werte waren doch falsch: BOND, C, DASH, DIA, MDT, MUB, STX, T - die F-198-Kollisionen. Fuer DASH wurde der Kryptopreis durch den DoorDash-Aktienschnitt geteilt

- Quelle: Methodik 2.150

**2.149** — STRUKTURFIX: F-198s Reparatur war im LADEPFAD nie angekommen - `lade_reihen_aus_db` las die `assetklasse`-Spalte nicht und gruppierte nach (symbol, currency). Jetzt filtert die Abfrage, und `_reihen_roh` ueberspringt die schaedliche 1:1-Zuordnung aus `messreihen`

- Quelle: Methodik 2.149 / pruefe_assetklassen_trennung.py

**2.149-beweis** — Der Fix aendert HEUTE NICHTS: ueber alle vier Klassen und 5,1 Mio Kurswerte BITGLEICH (516/470/293/35 Symbole). Kein bestehender Befund ist betroffen. 25 abhaengige Module importieren, Suite 1.988 bestanden

- Quelle: Methodik 2.149

**2.148** — F-198s offener Punkt ist BEANTWORTET: sieben Kryptoreihen fehlen wirklich (DASH 2.721 Kerzen, STX 2.510, DIA 2.195, MDT 2.149, T 1.656, BOND 1.114, C 417). Von 183 ,fehlenden' Paaren sind 175 zu kurz und 7 Kollisionen

- Quelle: Methodik 2.148 / pruefe_messbasis_wechsel.py

**2.148-engpass** — ⚠️ Die Messung scheitert NICHT an der Datenmenge: `schnitt` hat 233 Anker je Tag und 186 Bloecke (Grenze 20). Der Engpass ist die Wirkungsgroesse gegen die Streuung. Meine Empfehlung ,Kursreihen nachladen hilft' war falsch

- Quelle: Methodik 2.148

**2.147** — `schnitt`s STABILITAET ist mit diesen Daten NICHT ENTSCHEIDBAR. Bei H20 fehlen die Bloecke (BAER 19 von 20), bei H5 die Trennschaerfe (0,05 R ueber den Effekten). Die Gegenprobe `funding` faellt BEIDE Male in jeder Phase durch - ein Befund ueber die SCHICHTUNG, nicht ueber `schnitt`

- Quelle: Methodik 2.147 / n60_schnitt_stabilitaet.py

**2.146** — Abdeckung: Kern (BTC, ETH, SOL) 3/3 und grosse Werte 8/8 zu 100 % bewertbar - KEINE Luecke bei den stabilen Werten. Uebrige 16/33. ⚠️ 13 Nicht-Krypto-Eintraege gehoeren nicht in die Rechnung (richtig ist 29 von 44, nicht von 57)

- Quelle: Methodik 2.146 / zeige_abdeckung_krypto.py

**2.144** — Die MENGE ist jetzt an die FRAGE gebunden: `messnorm.FRAGEARTEN` lehnt ein Beitragsurteil auf der freien Menge ab und verweist auf `messnorm_auswahl`. Sechs Suite-Pruefungen sichern die Bindung

- Quelle: Methodik 2.144 / messnorm.FRAGEARTEN

**2.144-mengen** — Die tatsaechlichen Groessen: Messuniversum 516 · Watchlist 57 (davon nur 29 im Messuniversum!) · selektiert ~2-3 je Tag · Abdeckung funding 288 (56 %), oi 115 (22 %), turnover 65 (13 %)

- Quelle: Methodik 2.144

**2.144-ast** — ⚠️ `ast.parse` faengt doppelte Schluesselwortargumente NICHT - nur `compile()`. Die Syntaxpruefung meldete 0 Fehler, waehrend Python beim Import SyntaxError warf

- Quelle: Methodik 2.144

**2.143** — AUDIT: sechs von sieben Messungen des 06./07.09. liefen auf der FREIEN statt der selektierten Menge. F-212 belegt seit 04.09., dass die Beitraege dort auf 1,5 % der Anker wirken. Dieselbe Fehlerklasse wie 2.134 - die Grundmenge ist Teil der FRAGE

- Quelle: Methodik 2.143 / pruefe_audit_06_07_09.py

**2.143-norm** — ⚠️ Vier Nullbefunde ohne Trennschaerfe. Ich habe `messnorm` umgangen, weil meine Zielgroesse dort nicht vorgesehen war - und der Grund dafuer WAR der Befund. Wer die Norm umgeht, umgeht die Pruefung, die den eigenen Aufbau ablehnen wuerde

- Quelle: Methodik 2.143

**2.142-alt** — Kalibrierung durchgefuehrt: turnover-Stufen auf (+0,33 x3, -0,48 x2), SCHWELLE_VORGABE 0,080 -> 0,005. erreichbar_max faellt 0,1335 -> 0,0489 R, Durchlass steigt 16,4 % -> 54,0 %. Verfahren vorher an der alten Lage REPRODUZIERT (gab 0,080 zurueck)

- Quelle: Methodik 2.142 / Befundkarte 3.9d

**2.142-fiktion** — ⚠️⚠️ Haerter filtern macht das Ergebnis SCHLECHTER (bei 0,010: -0,0558 je verworfenem). Die alte Schwelle 0,080 war die beste WEGEN turnovers riesiger Stufen - die Trennschaerfe der Schwelle kam aus einer Fiktion

- Quelle: Methodik 2.142

**2.141** — `turnover`s Stufen lassen sich NICHT herleiten - weder als Fuenfteilung noch als Zweiteilung noch als SCHALTER. Trennschaerfe 2,0 Punkte; die registrierte Tabelle hat 5,55 Punkte Spanne - waere sie echt, wuerde man sie sehen

- Quelle: Methodik 2.141 / n58_turnover_stufen_neu.py

**2.140** — Bei H5 laufen 31,4 % der Anker FLACH aus (H20: 5,3 %). Die Kalibrierungsbasis zaehlt sie als Nicht-Treffer und liegt damit um +0,2898 R daneben - mit falschem Vorzeichen (-0,3654 gegen +0,0430)

- Quelle: Methodik 2.140 / n57_flach_in_der_produktion.py

**2.140-formel** — ✔ Die POTENTIALFORMEL stimmt fuer die Produktion: unter den Aufgeloesten liegt die Trefferquote bei 34,8 %, die Formel setzt basisrate(2,0) = 33,3 %. Kaputt ist die Messung, nicht die Bewertung

- Quelle: Methodik 2.140

**2.139** — Die LIVE geschaltete OI-Sperre traegt RICHTUNG: GS +0,00220 [+0,00058 .. +0,00373] bei H20 und +0,00381 [+0,00205 .. +0,00550] bei H5, beide 0/5. Reproduktion in der Live-Form gelungen (+0,00978, registriert +0,0145 im Band)

- Quelle: Methodik 2.139 / n56_oi_richtungsrein.py

**2.139-quote** — ⚠️ Dieselbe Sperre SENKT bei H5 die Barrieren-Trefferquote (-0,00262, Band ganz im Minus), weil der Aufloesungskanal dagegenlaeuft (-0,00989). Richtung besser, Quote schlechter - und `q` in der Potentialformel IST die Quote

- Quelle: Methodik 2.139

**2.139-turnover** — ⚠️⚠️ `turnover` reproduziert NICHT: gemessen -0,06293 [-0,13183 .. -0,00785] gegen registriert +0,0616 - gleiche Groessenordnung, umgekehrtes Vorzeichen. Die Fuenftel haben keine Ordnung (bestes ist 4, die Tabelle bestraft es mit -2,40). Bestaetigt 2.133

- Quelle: Methodik 2.139

**2.139-funding** — `funding` reproduziert bis in die FORM: Fuenftel +0,071 +0,083 +0,009 -0,053 -0,105, monoton, und auch die registrierte Tabelle hat bei Fuenftel 1 ihr Maximum

- Quelle: Methodik 2.139

**2.138** — `vola` ordnet den realisierten Ertrag: die Spreizung ruhig-lebhaft liegt in ALLEN 12 Geometrien ueber der artefaktbedingten (+0,035 bis +0,126 R, Tagesklammer). Es waehlt aber KEINE Bauform - dieselbe Geometrie gewinnt in allen Dritteln (Stop 2,0 x ATR / H20)

- Quelle: Methodik 2.138 / n55_vola_in_der_geometrie.py

**2.138-null** — Der Nullpunkt fuer ,EW in R' ist NICHT null: Tageskerzen ueberschiessen die Barriere, die nahe staerker als die ferne (P(Ziel|aufgeloest) 0,344 statt 0,333). Er wird aus drei GEEICHTEN Kunstwelten gewonnen; ungeeicht unterschaetzt man ihn um das Doppelte

- Quelle: Methodik 2.138

**2.136** — `turnover` traegt RICHTUNG +0,00512 [+0,00212 .. +0,00831], 0/5 - richtungsrein der STAERKSTE der drei. Auf der registrierten Barrieren-Quote traegt es nicht (+0,00168 ns), weil sein Aufloesungskanal (-0,00218) gegen die Richtung laeuft

- Quelle: Methodik 2.136 / n53_richtungsprobe_alle_drei.py

**2.136-f** — `funding` traegt RICHTUNG +0,00197 [+0,00024 .. +0,00376], 0/5, und reitet den Aufloesungskanal NICHT (AUF ns) - sein G0-Befund war sauber, nur unguenstig gemessen

- Quelle: Methodik 2.136

**2.136-EWR** — Auch der Erwartungswert in R ist kontaminiert: er feuert in der richtungsfreien Kunstwelt (+0,01363). Vier von sechs Massstaeben sind es - sauber ist allein GS

- Quelle: Methodik 2.136

**2.137** — Die zwei Ebenen spielen NICHT zusammen - funding und turnover wirken nicht staerker im guten vola-Drittel (Baender ueberlappen). `vola` ist ein UNABHAENGIGER Geometriehebel

- Quelle: Methodik 2.137

**2.135** — `vola` traegt KEINE Richtung - richtungsrein (symmetrische Barrieren, nur aufgeloeste Anker) -0,00041 [-0,00287 .. +0,00194], 2/5, keine Ordnung der Drittel. Der Befund geht restlos in zwei GROESSENkanaele auf

- Quelle: Methodik 2.135 / n52_vola_geometrieprobe.py

**2.135-AUF** — Die AUFLOESUNGSQUOTE traegt +0,03088 [+0,02753 .. +0,03436], monoton ueber die Drittel - ruhige Assets loesen ihre Barrieren nachweisbar oefter auf. Groesster sauberer Effekt des Tages, aber ueber die GEOMETRIE, nicht ueber den Markt

- Quelle: Methodik 2.135

**2.112** — Der MITTELWERT ist der falsche Massstab - der Ertrag liegt im oberen Rand (p50 -0,19 R, aber 6,65 % der Asset-Tage ueber +2 R)

- Quelle: Methodik 2.112

**2.115** — Ein im Rang GEFALLENES Asset hat auf kurzer Zeitachse mehr Randpotential (+0,0068, Band [+0,0034 .. +0,0108], Zufallskontrolle sauber)

- Quelle: Methodik 2.115

**2.116** — Die KATEGORIE traegt nicht (1,2 Prozentpunkte ueber das ganze Universum), der ZUSTAND innerhalb schon

- Quelle: Methodik 2.116

**2.117** — Der Datenqualitaetsfilter entfernt kein Rauschen, sondern den BELEG - er zerstoert den Befund aus 2.115

- Quelle: Methodik 2.117

**2.118** — Der Randmassstab hat Trennschaerfe (6 von 6 Kandidaten) und ist 2,5- bis 10-fach stumpfer als das Mittel - er wird ZWEITE Zielgroesse

- Quelle: Methodik 2.118

**2.119** — Reproduktionspflicht: alle drei Registrierungen reproduzieren; nichts ist gefallen

- Quelle: Methodik 2.119 · R-R11

**2.120** — `vola` ist kein Mitlaeufer, aber nicht reif: funding erklaert 3 % (p=0,325), turnover 18 % (p=0,025); der Rest ist im Schichtentest nicht trennbar

- Quelle: Methodik 2.120

**2.121** — `vola ODER turnover` traegt am Randmassstab mehr als jede Einzelgroesse - mengenkontrolliert, in beiden Historienhaelften, ueber drei Saaten

- Quelle: Methodik 2.121

**2.121-UND** — Werte mit BEIDEN Extremen sind WENIGER schlecht als Werte mit EINEM Extrem (UND-Reinheit +0,01267 gegen +0,01590 / +0,01678 einzeln)

- Quelle: Methodik 2.121
- Warum: unerklaert. Kein Messfehler - die Symmetrieprobe ist bitgenau. Es erklaert, warum UND versagt und ODER gewinnt

**2.122** — Die Schwelle ist ein Anteil von 59,9 % der bei DIESER Datenlage erreichbaren Spanne. Ein Wert mit nur Funding kommt zu 40 % durch, einer mit beiden Raengen nur zu 12 %

- Quelle: Methodik 2.122

**2.123** — `vola` allein traegt bei jeder Sperrmenge; der Abdeckungskompromiss kostet 17 % Wirkung

- Quelle: Methodik 2.123

**2.124** — `turnover` verschiebt die Frontloading-Quote um +4,0 bis +4,5 Punkte - bei JEDER Breite, Band ohne Null. Die Horizontwahl aus der Kursreihe ist belegbar und klein

- Quelle: Methodik 2.124

**2.126** — Die SPERRFORM ist fuer `vola` der falsche Weg - er gehoert als BEITRAG. Ein Beitrag unterliegt nicht der Bestandsausnahme und passt zur Quoten-Architektur

- Quelle: Methodik 2.126

**2.126-Auswahl** — Die 250-Tage-Momentum-Auswahl selektiert systematisch HOCHVOLATILE Werte: bei 5 % Auswahl trifft eine 20-%-vola-Sperre 74,8 % statt der erwarteten 20 %

- Quelle: Methodik 2.126
- Warum: auf der FREIEN Menge sind beide unabhaengig (20,3 % gegen 20,0 %) - die Ueberschneidung entsteht ausschliesslich durch die Auswahl

## ○ WAS OFFEN IST

**2.145-zeit** — ⚠️ ABER `schnitt` haelt ueber die ZEIT nicht durch: erste Haelfte +0,3483 (nur 17 Bloecke), zweite +0,0375 (Trennschaerfe 0,10 - untermaechtig, nicht widerlegt). KANDIDAT, kein registrierungsreifer Befund

- Quelle: Methodik 2.145

**2.307** — ➔ DER LOESUNGSWEG FUER KRITERIUM 3 (Nutzervorgabe ,kein Beitrag faellt ohne Loesung'): ZWEI Schichten statt fuenf. Bei fuenf Faechern bleiben 30 Symbole je Tag; bei zwei waeren es 75, und auf der 20-%%-Beitragsmenge immer noch rund 25 - ueber dem Mindestquerschnitt von 12. ⚠️ Das halbiert den Machtverlust UND erlaubt, die Kandidaten auf ihrer BEITRAGSmenge zu messen statt auf `frei`. Damit waeren beide Gruende aus 2.303 zugleich adressiert

- Quelle: V8, aus 2.303 und 2.306

**2.310** — ➔ V9 IST DER RICHTIGE WEG FUER KRITERIUM 3: `pruefe_geschichtet(..., marke=None)` statt einer Zaehlung ueber Faecher. Eine STETIGE Kennzahl mit einem Band schlaegt eine Zaehlung mit drei bis sechs moeglichen Werten - genau der Unterschied, an dem V7 und V8 gescheitert sind. Die Gegenkontrolle (GEMISCHTES Funding) bleibt, sie ist von der Kennzahl unabhaengig

- Quelle: V9, aus 2.308 und 2.309

**2.315** — ➔ WAS AUS 2.312 FOLGT - und es ist KEIN Abschalten: `funding` traegt auf 10 %% und 50 %%, nur bei 20 %% nicht. Nach der Nutzervorgabe faellt kein Beitrag ohne Grund, und ein Nichttragen auf EINER von drei Mengen ist ein Grund zum Nachsehen, keiner zum Entfernen. ⚠️ Zu klaeren: ob die 20-%%-Menge bei `funding` eine Besonderheit hat (Abdeckung 300 von 536 - die Momentum-Auswahl und die Funding-Verfuegbarkeit koennten sich ueberschneiden) oder ob es Rauschen ist

- Quelle: V10, aus 2.312

**2.391-hilfe** — ⚠️⚠️ VORGABE GEGEN IST: *,die LLM-Stufen sollen eine Entscheidungshilfe sein und nichts blockieren oder aendern'* (Nutzer 12.09.). Gemessen gilt das fuer ZWEI der drei Stellen: Rolle A verliert an `lagebild` NULL Zellen, Z.ai hat kein Veto (ihr Einwand steht als Text in der Mail). ⚠️ ROLLE BC TUT BEIDES: (1) SIE BLOCKIERT - 56 Zellen in 7 Tagen fielen an der Aktionsstufe mit ,NICHTS_TUN' (von 247 Verlusten dort sind die uebrigen deterministisch: 166 ,Ausstieg steht auf SCHLIESSEN', 25 ,vollstaendig gestakt'); das sind 2,7 %% der 2.046 beurteilten Zellen - wenig, aber nicht null. (2) SIE AENDERT ZAHLEN - ihr WIDERLEGUNGSPREIS geht in die Stopweite ein (`rechne(umgeworfen_preis_eur=...)`), und am Stop haengen Betrag, Hebel und Ziel. In der SOL-Mail vom 12.09. stammt der Stop 80,26 EUR aus dieser Angabe: daraus folgen 8,9 %% Stopabstand, Hebel 3,9x und 174 EUR Risiko. ➔ ZWEI ENTSCHEIDUNGEN STEHEN AN: darf das Modell eine Empfehlung verhindern, und darf seine Preisangabe die Geometrie bestimmen?

- Quelle: gate_durchlaessigkeit 7 Tage · rollen_lauf · Nutzer 12.09.

**2.390-gui** — ⚠️⚠️ GUI UND MAIL LAUFEN AUSEINANDER (Nutzerbefund 12.09.: *,die GUI bzw. Anzeige und eMail sollten nicht wesentlich auseinanderlaufen'*). Die Mail hat seit S-4 die neue Gliederung (AUF EINEN BLICK · WAS DAGEGEN SPRICHT · sechs Abschnitte · Anhang A/B/C). Der Hebel-Reiter der Oberflaeche zeigt weiter die ALTE Dreiteilung: ,1. MATHEMATISCH BERECHNET / 2. LLM-BEWERTUNG (Konfidenz -) / 3. KONKLUSION (RISIKOFAKTOREN)' mit ,Keine strukturierten Risikofaktoren verfuegbar'. ⚠️ DREI KONKRETE ABWEICHUNGEN: (1) die Spalten ,Konfidenz' und ,Trigger' sind leer, weil die neue Kette sie bewusst nicht liefert (Konfidenz war 77,5 %% vorhergesagt gegen 33,3 %% eingetreten); (2) die Liste fuehrt Zeilen mit 1,0x bis 1,2x als ,Hebel' - seit dem Rollout ist alles unter 2x SPOT, die Zeilen stammen aus Laeufen vor 07:08; (3) die GUI zeigt Zonen in USD UND EUR, die Mail nur in EUR. Es sind ZWEI Leser desselben Signals, und sie erzaehlen Verschiedenes

- Quelle: GUI Hebel-Reiter 12.09. · Mail SOL 12.09.

**2.390-warnungen** — ⚠️⚠️ DIE MAIL WARNT MEHR ALS SIE SAGT (Nutzerbefund 12.09.: *,ich sehe vor lauter Warnungen was nicht passen koennte nicht auf einen Blick was relevant ist'*). Gezaehlt an der SOL-Mail: rund 19 Warn- und Dagegen-Zeilen (Kopf 3, ,Was dagegen spricht' 3, Bewertung 3, Rechnung 2, Marktvergleich 3, Termine und Projekt 4, Anhang 1). Dem steht KEINE einzige Dafuer-Zeile gegenueber: ,von 4 pruefbaren Merkmalen 2 dagegen, 2 noch nicht bewertbar'. ⚠️ Das ist kein Darstellungsfehler, sondern die ehrliche Folge einer duennen Bewertung (EIN tragender Beitrag) - die Mail sagt es sogar selbst. Die Frage ist, ob der Leser bei dieser Dichte noch erkennt, was ENTSCHEIDET. ⚠️ Dazu echte Doppelungen in derselben Mail: ,steht auf EINEM Beitrag' zweimal, die Kursmarke 91,15 EUR dreimal (Marken, Widerstand, Kursmarken), der Umschlag 7,6 %% zweimal (Lage und Belege), der Stopabstand 8,9 %% dreimal

- Quelle: Mail SOL 12.09. · Nutzerbefund

**2.390-zahlen** — ⚠️⚠️⚠️ ZAHLENVERDACHT IN ANHANG B: DIE GEBUEHREN IGNORIEREN DEN HEBEL. Der Kopf rechnet gehebelt (,am Stop -174 EUR' bei 3,9x), Anhang B rechnet auf den EINSATZ: ,Standard 0,30 %%: 3,0 %% des Einsatzes (rund 15 EUR) - davon Handel 0,6 %%, Finanzierung 2,4 %% fuer 16 Tage -> frisst 33 %% Ihres Risikos'. Die 33 %% ergeben sich gegen 44,50 EUR, also gegen das UNGEHEBELTE Risiko (8,9 %% von 500 EUR) - nicht gegen die 174 EUR aus dem Kopf. Und die Finanzierung von 2,4 %% ist auf 500 EUR gerechnet; bei 3,9x liegt der KREDIT bei rund 1.462 EUR, 16 Tage x 0,18 %% waeren rund 42 EUR statt 12. ⚠️ WENN DAS ZUTRIFFT, ist die Kostenaussage bei jedem Hebelgeschaeft zu niedrig - und sie steht in derselben Mail wie die gehebelte Ergebniszeile. ZU PRUEFEN, nicht angenommen: an `trefferbilanz`/`kosten` gegen die echten Funktionen, mit einem Fall ohne und einem mit Hebel

- Quelle: Mail SOL 12.09. Anhang B · Schritt 41

**2.389-richtung** — ⚠️ ABSICHERUNG: ZWEI SIGNALE FIELEN AN DER RICHTUNGSPFLICHT. Im ersten Umlauf nach dem Neustart meldete hedge/absicherung 2 Fehler: *,DBPK: NACHKAUFEN ohne Richtung - erlaubt (LONG, SHORT), bekommen None'*, dasselbe fuer 3QSS. S6c verlangt die Richtung instrumentunabhaengig; das Modell liefert sie fuer die beiden Absicherungstitel nicht. Im ZWEITEN Umlauf trat es nicht auf - es haengt am Modell, nicht an der Struktur. ⚠️ Folge: an solchen Laeufen entsteht fuer die Absicherung kein Signal, ohne dass es jemandem auffaellt (2 von 2 Werten)

- Quelle: NB-Export 12.09. 07:09 · empfehlung_vertrag.BRAUCHT_RICHTUNG

**2.387-job** — ⚠️ OFFEN NACH DEM ROLLOUT: DER PORTFOLIOWERT-JOB HAT ZEHN TAGE NICHT GESCHRIEBEN (01.09. bis 11.09., am Notebook beim Rollout gesehen). Er ist eingeplant (`id=portfolio_wert`, mit Nachholfenster), und seine Abdeckungsschranke kann es nicht gewesen sein: 26 von 32 Werten mit Kurs sind 81 %% gegen die geforderten 80 %%. Das Nachrechnen hat die LUECKE geschlossen, nicht die URSACHE. ➔ Nach dem Neustart an der juengsten Zeile pruefen: schreibt er wieder taeglich, war es der abgeraeumte Prozess vom 02.09.; schreibt er nicht, ist es der Job selbst. ⚠️ Dazu ein zweiter Punkt: die aelteren Luecken der Zeitreihe (03.08.->20.08., 20.08.->26.08., 26.08.->01.09.) werden NICHT nachgerechnet - der Verlauf hat dort weiter Sprungstellen, der Index bleibt stetig

- Quelle: Notebook-Rollout 12.09. · scheduler/background.portfolio_wert_job

**2.387-fortschreibung** — ⚠️ OFFEN NACH DEM ROLLOUT: SECHS BOERSENTITEL WERDEN DAUERND FORTGESCHRIEBEN. In jeder nachgerechneten Zeile stehen dieselben Symbole (ISOC, OD7C, OD7H, OD7L, OD7N, CEBS, DBPK, EXH3, VVMX) mit 3 bis 4 Tagen Fortschreibung - genau die, die yfinance am 02.09. 31-mal als ,possibly delisted' meldete und die damals als FREMDE Quelle abgehakt wurden. ✔ Die Fortschreibung ist gedeckelt (`MAX_FORTSCHREIBEN_TAGE = 4`), danach zaehlt der Wert als ohne Kurs und drueckt die Abdeckung - sie kann also nicht unbemerkt weiterlaufen. ⚠️ Aber: eine Meldung aus fremder Quelle hat Folgen in der eigenen Rechnung, denn aus dem Kapital kommt der Hebel-Deckel. Zu pruefen sind die TICKER (VVMX.DE, DBPK.DE, X136.MU, EXH3.DE, CEBS.DE, ISOC.SG), nicht die Fortschreibung

- Quelle: Notebook-Lauf 12.09. · portfolio_historie.MAX_FORTSCHREIBEN_TAGE

**2.385-pscan** — ➔ VORSCHLAG P-SCAN: DIE ENTDECKUNG AUF DAS POTENTIAL STELLEN (Nutzerauftrag 12.09.: *,ueberlege dir als Experte eine neue Loesung, um Assets mit Potential zu empfehlen'*). Die Idee: dieselbe gemessene Bewertung wie in der Kette (`potential.rechne` aus den registrierten Beitraegen) NICHT nur auf die Watchlist anwenden, sondern auf alle Werte, fuer die die Messbasis reicht - der Rang ist ein Querschnittsvergleich und dafuer ausdruecklich zugelassen (Regel 3). ⚠️ DIE REICHWEITE IST HEUTE BEGRENZT, gemessen am Desktop 12.09.: Funding 302 Symbole, Terminmarkt 100, Onchain/Turnover nur 66 - BEIDE tragenden Beitraege liegen fuer 42 Werte vor, davon 35 NICHT in der Watchlist (ADA, DOT, DOGE, AAVE, BCH ...). Der Engpass ist die Onchain-Basis, nicht die Idee. Vorgehen in drei Stufen: (1) SCHATTEN - den Rang je Tag mitschreiben, ohne Mail; (2) MESSEN - traegt ein hoher Rang ausserhalb der Watchlist mehr Potential (`bewegung_r`, NICHT Zielerreichung) als die heutige Watchlist? Ohne diesen Nachweis keine Empfehlung (P-1); (3) erst dann eine woechentliche AUFNAHME-Liste mit Begruendung, gefiltert auf bei Bitpanda handelbare Werte (`config.kandidat_ist_handelbar`). ⚠️ Regel 1: die Liste schlaegt BEOBACHTUNG vor, kein Handeln - das Signal entsteht weiter in der Kette. Solange das nicht gemessen ist, bleibt der alte Marktscan an

- Quelle: Schritt 39 · 2.385 · Messbasis-Zaehlung 12.09.

**2.382-akku-anlass** — ⚠️⚠️ ZU 2.380-akku-cooldown: DIE AKKUMULATIONSZELLE ERREICHT IHRE SPERRE IM LAUF NIE - und nicht nur wegen des Cooldowns. `anlass.beobachte` ist je Symbol und Instrument verschluesselt, nicht je Strategie; die Einstiegszelle laeuft zuerst (`_REIHENFOLGE`), die zweite sieht ,nur 0 zaehlende Blockaenderung(en)' - die Anlass-Sperre ist im Betrieb aktiv. Ohne Anlass-Sperre (nur in der Kopie) fielen beide Zellen am Cooldown je Symbol. `zellen()` laesst (spot, einstieg) IMMER zu - ein Kernwert hat stets zwei Zellen. Folge fuer Paket B: kein Akkumulationssignal (gewollt), aber der Grund im Trichter lautet ,anlass' statt der Sperre; die Verdrahtung der Sperre belegt die Suite (Paket 17). Folge fuer Schritt 26: Anlass UND Cooldown je Zelle, mit Kostenschutz - sonst bleibt die Akkumulation auch nach der Registrierung stumm

- Quelle: simuliere_kette --nachweis-paket-b 11.09. · rollen_lauf._REIHENFOLGE · anlass.beobachte

**2.382-rundung** — ○ FEINSCHLIFF (nach dem Rollout): der Hebel wird auf 0,1 GERUNDET (`round(hebel, 1)`), und der Verlust am Stop rechnet mit dem gerundeten Wert - aufgerundet ueberschreitet er das r(q)-Budget um bis zu 2,5 %% (ONDO: 2,09 -> 2,1x, 125,15 statt 124 EUR); die Liquidation nimmt den ungerundeten. Und Anhang C sagt auch bei einem Hebelgeschaeft ,falls ein Hebel noetig wird'

- Quelle: simuliere_kette --nachweis-paket-b 11.09. · entscheidungsrechnung.rechne

**2.380-annahmen** — ⚠️⚠️ ZUR ABSTIMMUNG - drei gesetzte Annahmen. (1) DAS FENSTER (`hebelfuehrung.KOPPEL_TAGE` = 3 Tage): wie weit ein Signal vor der Eroeffnung als Plan gilt UND wie lange ein nicht eroeffnetes Hebelsignal Risiko belegt. Echte Latenz Signal -> Eroeffnung am NB: 0,5 / 0,6 / 3,4 STUNDEN (nur drei Faelle seit 14.07.); Haltedauer der 188 echten Positionen Median 0,3 Tage, 90 %% unter 3,3. Bei 3 Tagen macht der Deckel 72,7 %% der Hebelkandidaten zu Spot, bei 1 Tag 32,4 %% (2.380-sim). (2) POSITION OHNE BEKANNTEN STOP zaehlt mit dem ganzen Eigenkapital: echte Positionen Median 222 EUR, 90 %% 720, hoechstens 1.831 EUR - schon eine groessere Handposition fuellt den Deckel von 546 EUR allein; gleichzeitig offen waren hoechstens 5 Positionen mit 3.944 EUR Eigenkapital. (3) Gezaehlt wird bis zum URSPRUENGLICHEN Stop - ein nachgezogener Stop senkt das Risiko nicht, weil das System nicht weiss, welcher Stop bei der Boerse liegt

- Quelle: NB-Sicherung 11.09. hebel_positions/hebel_signals · 2.380-sim

**2.380-akku-cooldown** — ⚠️⚠️⚠️ DIE AKKUMULATION LIEF IM BETRIEB NIE - trotz Schalter. NB-Sicherung 11.09.: 0 von 3.859 Rollen-Signalen mit Strategie akkumulation (1.994 einstieg, 1.865 aus der Zeit vor der Strategiespalte). BTC, ETH und SOL tragen nur einstieg (88 / 79 / 77). URSACHE im Code: `wiederholung.gesperrt_bis()` bekommt die Strategie, fragt aber das juengste Signal des SYMBOLS ab, gleich welcher Strategie. Die Zellen laufen einstieg vor akkumulation (`rollen_lauf._REIHENFOLGE`). REPRODUZIERT mit der echten Funktion an der NB-Sicherung: nach dem Einstiegssignal BTC 11.09. 04:47 ist die Einstiegszelle nach 12 h frei, die Akkumulationszelle bis 13.09. 04:47 gesperrt (48 h) - und weil die Einstiegszelle rund alle 12 h eine neue Zeile schreibt, laeuft die 48-h-Sperre nie ab. Dieselbe Ursache hinter der alten Simulationsluecke ,KEIN Asset lief mit zwei Zellen durch'. ⚠️ Fuer Paket B ohne Wirkung (die Akkumulation ist gesperrt). ⚠️ Der Fix gehoert in Paket 2 (Schritt 26) und braucht einen Kostenschutz: eine gesperrte Akkumulationszelle schreibt keine Zeile - ohne Cooldown holte sie sich sonst je Lauf ein eigenes Modellurteil

- Quelle: wiederholung.gesperrt_bis · rollen_lauf._REIHENFOLGE · NB-Sicherung 11.09.

**2.379-tage** — ⚠️⚠️ WIE LANGE EIN HEBEL SICHER BLEIBT. RM-11 prueft bei der Eroeffnung Tag 0 (Nutzerentscheidung 14.07.: keine Haltedauer raten); die Finanzierung schiebt die Liquidation um rund 0,2 %% des Einstiegs je Tag. `simuliere_hebelverteilung.py` mit korrigiertem RM-11: bei 18.213 EUR erreicht die Liquidation den Stop im Median nach 79 Tagen (10 %% nach 26), KEIN Fall unter 3,3 Tagen; Watchlist 2026 Median 73 (10 %% 25). Bei 30.000 EUR: Median 31 (10 %% 2,6), am ersten Tag 8,5 %%, unter 3,3 Tagen 11,2 %%. Die 188 echten Positionen am NB hielten im Median 0,3 Tage (90 %% unter 3,3; Hebel Median 5,6x). ➔ beim heutigen Kapital keine Handlung noetig; ueber eine Tagesreserve beim Einstieg ist zu entscheiden, wenn das Kapital waechst

- Quelle: simuliere_hebelverteilung.py 11.09. (drei Laeufe) · NB hebel_positions

**2.359-abruf** — ⚠️ UND EINE OFFENE UNGENAUIGKEIT, benannt statt verschwiegen: keine der drei Messquellen fuehrt eine `fetched_at`-Spalte. Der ABRUFSTAND - nach dem Kopf des Moduls *,der eigentliche Gesundheitswert'* - kommt deshalb aus der AENDERUNGSZEIT der Datei. Die beweist, dass ueberhaupt geschrieben wurde, NICHT dass der Abruf vollstaendig war. Fuer ,laeuft der Job noch?' genuegt das; fuer ,war er vollstaendig?' nicht. Eine echte `fetched_at`-Spalte kommt, wenn die drei Jobs bekommen

- Quelle: agent/datenfrische._stand_datei

**2.343** — ⚠️ `hebel_signals` STEHT SEIT DEM 10.08. - ein Monat ohne neue Zeile, bei 1.998 vorhandenen. Ob das ein Ausfall oder die richtige Folge der Lage ist, ist NICHT geklaert. ⚠️ Es passt zur Hebelspur: die Lage `hebel` ist blockiert (A1/A9/P-1), aber ein stilles Versiegen sieht genauso aus wie ein begruendetes Schweigen

- Quelle: NB-Sicherung 2026-09-11 · hebel_signals

**2.327** — ⚠️ `vola` FAELLT AN DERSELBEN STELLE - und fast mit derselben Zahl: +0,2039 [+0,0760 .. +0,3912] auf 20 %%, gegen `schnitt`s +0,1973, beide mit 20/20 Bloecken. Das ist zu aehnlich fuer Zufall und stuetzt 2.293 (`vola` ist Geometrie, nicht Richtung): die beiden koennten denselben geometrischen Anteil enthalten. ⚠️ HYPOTHESE, nicht Befund - sie ist nicht gemessen

- Quelle: n110_kriterium2_mit_trennschaerfe.py

**2.152-kern** — ⚠️⚠️ Das Akkumulationsmass traegt NICHT fuer BTC (-0,0251, p=0,723), ETH (-0,0308) und SOL (-0,0291) - und `asset_dca_settings` enthaelt genau BTC und ETH. Die Akkumulation laeuft auf den Werten, fuer die das Mass keine Begruendung liefert

- Quelle: Methodik 2.152

**2.149-prod** — ⚠️ Die PRODUKTIONSDATENBANK hat die `assetklasse`-Spalte NICHT. F-198 fuehrte sie nur in der Messbasis ein. Heute folgenlos (Watchlist-Symbole sind eindeutig), aber die Trennung ist dort strukturell nicht moeglich

- Quelle: Methodik 2.149

**2.148-sperre** — ⚠️ LADEN IST NOCH NICHT SICHER: F-198 hat `price_history_ohlc` gefixt (PK mit assetklasse), aber `messreihen` nicht - dort gilt ,eine Klasse je Symbol'. Rund zehn Messwerkzeuge lesen `klassen_aus_db` und wuerden die neuen Kryptokerzen falsch einordnen. ERST Strukturfix, DANN laden

- Quelle: Methodik 2.148

**2.147-weg** — ⚠️ Die Frage braucht MEHR ANKER, nicht eine andere Schichtung. Eine dritte Einteilung zu suchen, bis eine ,traegt', waere der Fehler aus Prueflliste 2.80. Was hilft: die neun fehlenden Kursreihen nachladen

- Quelle: Methodik 2.147

**2.146-luecke** — ⚠️ Neun Watchlist-Werte haben funding/oi, aber KEINE Kursreihe: AKT, ASTER, BRETT, GRIFFAIN, HYPE, KAS, MON, MORPHO, PLUME. Keine Symbolfehler - die coingecko-IDs stimmen, die Kurse wurden nie geladen. Behebbar

- Quelle: Methodik 2.146

**2.141-lage** — ⚠️ ENTSCHEIDUNG OFFEN: Tabelle lassen (aktiv falsch), auf die gemessene Zweiteilung +0,33/-0,48 (nicht belegt, aber 17x kleiner und gleichgerichtet) oder auf null (entfernt einen belegten Richtungstraeger). Jeder Weg verlangt R-R9

- Quelle: Methodik 2.141

**2.138-offen** — ⚠️ Die ZUSCHREIBUNG der Spreizung ist offen. Die Kunstwelt hat einen Strukturfehler: Hoch und Tief sind dort unabhaengiges Rauschen um den Schluss, in echten Daten liegt an einem Aufwaertstag das Tief nahe der Eroeffnung. Sie ueberschaetzt die Stop-Treffer. Naechster Schritt: Brownsche Bruecke je Tag

- Quelle: Methodik 2.138

**D3** — Ist H20 der richtige Horizont fuer die OI-Sperre, wenn der Betriebshorizont 3-5 Tage betraegt?

- Quelle: Methodik 2.119
- Warum: ENTWURFSfrage, keine Messfrage - Nutzerentscheidung

**N11** — Die Durchlassquote haengt an der SCHIEFE der Beitragsstufen, nicht am Asset: funding laesst 2 von 5 Fuenfteln durch, turnover nur 1 von 5

- Quelle: Methodik 2.122
- Warum: turnovers Maximum (+3,15) steht allein, der Zweite (+0,83) liegt bei 26 % davon. Bei funding liegt der Zweite (+0,82) bei 63 % des Maximums (+1,30)

**N14** — Traegt das HEBEL-SCREENING als zweite, von der Kursreihe UNABHAENGIGE Quelle fuer die Horizontwahl?

- Quelle: Methodik 2.124 · F-185
- Warum: 227.395 OI-Zeilen, 13.254 Kandidaten. Der einzige verbliebene Hebel fuer mehr Trennschaerfe - alle Kursreihengroessen sind ausgemessen

**N15** — `UND @ 10 %` zeigt 58,3 % frontlastig (+7,1 Punkte, Band [+2,8 .. +13,0]) bei nur 6,1 % der Anker

- Quelle: Methodik 2.124
- Warum: Band ohne Null, aber die anteilgewichtete Wirkung traegt nicht - zu wenige Anker. Mit mehr Terminmarkt-Historie pruefbar. Zurueckgestellt, nicht verworfen

**N16** — `vola` als BEITRAG verdrahten - Quotenpunkte je Fuenftel aus der Randwirkung

- Quelle: Methodik 2.126
- Warum: R-R9 beachten: Beitragswechsel = Neukalibrierung der Schwelle plus Nachzug von KALIBRIERT_FUER

**N17** — Traegt der Momentum-Rang etwas ueber `vola` hinaus? 74,8 % Ueberschneidung bei 5 % Auswahl

- Quelle: Methodik 2.126

**N18** — Der Engpass ist der COOLDOWN (93,8 %), nicht die Auswahl und nicht eine fehlende Sperre

- Quelle: F-180/F-182 · Methodik 2.126
- Warum: jede weitere Sperre verschaerft ein System, dessen Problem nicht Durchlaessigkeit ist

**N10** — Die Potentialformel meint eine BARRIEREN-Quote, das Randmass eine HORIZONT-Quote

- Quelle: Methodik 2.121

**N6** — `turnover` traegt auch am RAND (+0,01389 bei H20), registriert ist er nur am Mittel

- Quelle: Methodik 2.119

**N7** — Der Schichtentest braucht rueckwirkend eine Trennschaerfe - alle frueheren Nullbefunde daraus sind unbeziffert

- Quelle: Methodik 2.120
- Warum: messe_kandidaten_als_regel.geschichtet() hatte nie eine Positivkontrolle

**N2** — Warum traegt `schnitt50` bei H5, aber nicht bei H2 und H20?

- Quelle: Schritt 4a

## ↩ WAS ABGELOEST IST

**2.161-turnover** — „`turnover` dreht ab 2022 das Vorzeichen (-0,0112 / -0,0307)"

- Quelle: Methodik 2.161
- **Abgeloest durch: 2.162**
- Warum: auf der 20-%-Menge gemessen, die seine Datenlage NICHT traegt: 10,1 Anker je Tag (frueh 5,3). `pruefe_auswahl` reproduziert den Wechsel NICHT und sagt woertlich 'KEIN BEFUND - untermaechtig'. Auf der Menge, die seine Abdeckung traegt (50 %), ist er ab 2022 POSITIV: +0,0598 [+0,0066 .. +0,1139]

**2.160** — „`schnitt` ist nicht zeitstabil: Haelften +0,2238 R [+0,0792 .. +0,3988], Trennschaerfe 0,02 R"

- Quelle: Methodik 2.160
- **Abgeloest durch: 2.163**
- Warum: ZWEI Fehler, beide eigene. (1) Gemessen auf der 20-%-Menge - `schnitt`s Datenlage verlangt 10 % (schmalste mit >= 12 Ankern UND >= 20 Bloecken). Dort ist der Unterschied -0,0647 [-0,3098 .. +0,2161], also mit umgekehrtem Vorzeichen und nicht trennbar. (2) Die Trennschaerfe war auf die ECHTE Reihe gepflanzt, also auf einen bereits trennbaren Unterschied - dann bleibt er es bei jedem Versatz. 'Ab 0,02 R' hiess nur 'der Effekt ist gross'. Zentriert gemessen liegt sie bei >0,20 R

**2.170** — „In Aktien traegt kein Kandidat - ein belastbarer Nullbefund"

- Quelle: Methodik 2.170
- **Abgeloest durch: 2.172**
- Warum: die Zielgroesse `bewegung_r` ist ueber die Klassen NICHT vergleichbar. Sie teilt durch max(5 % Kurs, 0,75 ATR) - und bei Nicht-Krypto bindet fast immer der 5-%-Boden (Aktien 97,1 %, ETF 99,2 %). Der Stop liegt dort 2,29 bzw. 4,43 ATR entfernt statt 0,75. In eigenen Streuungseinheiten sind die Aktien-Effekte GENAUSO GROSS wie die von Krypto (0,038 gegen 0,047) - sie waren nur nicht von null zu trennen

**2.170-grundbefund** — „Der Grundbefund vom 10.08. ist nicht krypto-spezifisch - er gilt in Aktien genauso"

- Quelle: Methodik 2.170
- **Abgeloest durch: 2.172**
- Warum: stand auf 2.170 und faellt mit ihm. Die Messung konnte in Aktien gar nichts zeigen

**2.259** — ✔✔✔ N-95: DER KNICK IST NICHT BELEGT - und zwar mit TRENNSCHAERFE, nicht aus Untermacht. Bei den beiden Beitraegen, wo die Maschinerie nachweislich arbeitet (`funding` d34 +0,0656 [+0,019..+0,118] TRENNBAR, `oi_aenderung` d34 +0,0520 [+0,007..+0,094] TRENNBAR), ist d01 NICHT trennbar (+0,0402 [-0,037..+0,116] und +0,0260 [-0,027..+0,083])

- Quelle: n95_ist_der_knick_stabil.py
- **Abgeloest durch: 2.263**
- Warum: Gemessen wurde auf `frei` - der RANGmenge. Auf der AUSWAHLmenge (20 %), fuer die die Beitraege gebaut sind, ist d01 bei `funding` TRENNBAR (+0,2069 [+0,0137 .. +0,4304]) bei stummer Kontrolle. Der Nullbefund gilt fuer die Rangmenge, nicht fuer die Bewertungsmenge - N-96 hat ihn auf `frei` exakt reproduziert (R-R11 erfuellt), bevor er eingeschraenkt wurde.

**2.259-b11** — ✔✔ DAMIT IST B11 BEANTWORTET: 'das Extrem ist nicht der beste Fall' ist NICHT belegt. Der Unterschied zwischen Fuenftel 0 und 1 ist Rauschen. ⚠️ Und das passt zu `funding_extrem`, der im Gesamtlauf Widerspruch zeigt und die Live-Sperre nicht verbessert (F-207) - zwei unabhaengige Zugaenge, dasselbe Ergebnis

- Quelle: n95_ist_der_knick_stabil.py
- **Abgeloest durch: 2.263 / 2.264**
- Warum: Auf der Auswahlmenge ist der Unterschied trennbar, auf der Live-Menge (k=2 je Tag) mangels Besetzung gar nicht beurteilbar. B11 ist damit wieder OFFEN - als Frage der Datenlage, nicht als beantwortete Frage.

**2.260** — ✔✔✔ UND DAMIT IST AUCH B10 GELOEST - OHNE DIE MONOTONIE-VORGABE AUFZUGEBEN. Werden die zwei Stufen zusammengelegt, die GEMESSEN nicht unterscheidbar sind, werden BEIDE Tabellen monoton fallend: `funding` +1,06 / +1,06 / +0,12 / -0,54 / -1,70 und `schnitt` +1,44 / +1,44 / +0,28 / -1,19 / -1,96

- Quelle: n95_ist_der_knick_stabil.py
- **Abgeloest durch: 2.263 / 2.264 / 2.265**
- Warum: Die Zusammenlegung ist NICHT AUSGEFUEHRT. Es gibt keine Menge, auf der d01 und der Pruefstein d34 zusammenpassen. Und `pruefe_funding_monoton.py:59` prueft mit 0,02 R Toleranz, waehrend die Inversion 0,002 R betrug - der Knick war bekannt und bewusst durchgelassen, das Zusammenlegen waere Kosmetik statt Korrektur.

**2.260-nicht-angepasst** — ⚠️ UND ES IST KEINE ANPASSUNG AN DAS GEWUENSCHTE ERGEBNIS: die Zusammenlegung ist durch die MESSUNG begruendet (d01 nicht trennbar, waehrend d34 es ist) und war VORAB als Konsequenz benannt - im Skriptkopf, vor dem Lauf: 'Dann waeren Stufe 0 und 1 ZUSAMMENZULEGEN, nicht die Beitraege zu verwerfen'

- Quelle: n95_ist_der_knick_stabil.py
- **Abgeloest durch: 2.263**
- Warum: Die Aussage ueber das VERFAHREN bleibt richtig - die Konsequenz stand vorab im Skriptkopf. Sie praesupponiert aber die Zusammenlegung, und die ist nicht ausgefuehrt: auf der Auswahlmenge ist d01 trennbar.

**2.260-rr9** — ⚠️⚠️ ES IST ABER EIN EINGRIFF IN EINEN LIVE LAUFENDEN BEITRAG: `funding`s registrierte Stufen wuerden von +0,82/+1,30/... auf +1,06/+1,06/... wechseln. Das aendert die Beitragslage und loest R-R9 aus - die Schwelle waere neu zu kalibrieren. NUTZERENTSCHEIDUNG, nicht stille Automatik

- Quelle: agent/wahrscheinlichkeit.BEITRAEGE / R-R9
- **Abgeloest durch: 2.263**
- Warum: Die Bedingung ist richtig geblieben, der Fall aber nicht eingetreten: die Stufen wurden NICHT geaendert, R-R9 wurde nicht ausgeloest. Der Vorgang steht als Kommentar neben der Tabelle in `agent/wahrscheinlichkeit.py`.

**2.261** — ⚠️ ZWEI VORSCHLAEGE VON MIR SIND HEUTE DURCHGEFALLEN, bevor der dritte trug: die MONOTONIE als Huerde (sie reisst den Bestand mit - sechs von acht Kandidaten brechen sie, darunter zwei live) und die SPANNE als Ersatz (sie laesst alle acht durch). Erst die Frage 'ist der Knick STABIL' hat entschieden - und sie brauchte kein neues Kriterium, nur die vorhandene Maschinerie

- Quelle: Selbstbefund 09.09.2026
- **Abgeloest durch: 2.263 / 2.266**
- Warum: Auch der DRITTE Vorschlag hat nicht getragen. Die Frage 'ist der Knick stabil' war richtig gestellt, aber auf der falschen Menge beantwortet - und mein erster Korrekturlauf hatte selbst die Rangreihenfolge vertauscht. Der Tag endete mit drei durchgefallenen Vorschlaegen, nicht mit zweien.

**2.277** — ⚠️ NEBENBEFUND: KEIN Kandidat traegt auf der LAENGS-Achse - weder unter dem Verschub noch unter der Tagesmischung. `amihud` -0,0445 · `vola` +0,0056 · `schnitt` -0,0163 · `rsi` -0,0104. ⚠️⚠️ `amihud` ist dabei UMGEKEHRT gerichtet und sein Band schliesst die Null knapp aus ([-0,0994 .. -0,0005]) - das ist keine Bestaetigung, aber auch kein Nullbefund, und es passt zu 2.166 (er misst Ausfuehrbarkeit, nicht Potential). ⚠️ Das Urteil steht unter dem Vorbehalt aus 2.274: solange der Nullpunkt nicht entschieden ist, ist auch ,traegt nicht' nur vorlaeufig

- Quelle: n98_n46_laengs_nullpunkt.py
- **Abgeloest durch: 2.283**
- Warum: Es ist UNTERMACHT, kein Nullbefund. Bei der Beharrlichkeit von `schnitt` (0,985) findet die Anlage einen Effekt von 0,03 R in 20 % und von 0,05 R in 50 % der Faelle - die echten Kandidaten liegen genau in diesem Bereich. Ein ,traegt nicht' sagt dort nichts ueber die Welt.

**2.326** — ✔✔ DIE LOESUNG STEHT IN DERSELBEN TAFEL - `schnitt50` ist auf ALLEN DREI Mengen stabil (bis 0,20 · 0,20 · 0,05). ⚠️ Nutzervorgabe: Kein Beitrag darf einfach fallen, konkrete Begruendung erforderlich und ggf. Loesung suchen. Die Begruendung steht in 2.325; die Loesung ist die 50er-Form, die der Nutzer am 09.09. selbst zurueckgeholt hat (Warum hast du schnitt50 einfach herausgenommen?) und die nach 2.222 die einzige MONOTONE Form ist. Zu pruefen bleiben bei ihm Kriterium 1 und N-73

- Quelle: n110_kriterium2_mit_trennschaerfe.py / 2.222
- **Abgeloest durch: 2.331**
- Warum: V11 hat beide Stuetzen weggenommen: N-73 besteht er
                     NICHT (2 von 3, 2.331), und die Monotonie war FALSCH
                     ZITIERT (2.338). Kriterium 1 erfuellt er - das allein
                     macht ihn nicht zum Ersatz

**2.319** — ✔✔✔ `schnitt` HAT DAMIT ALLE VIER KRITERIEN: 1 ABDECKUNG 100 %% (536 von 536) · 2 STABILITAET stabil (N-68-Form) · 3 UNABHAENGIG von `funding` (V9) · 4 REGEL 3 mit 25,4 %% Asset-Anteil roh bestanden. Dazu N-73 mit 3 von 3 Mengen - BESSER als jeder registrierte Beitrag (`funding` 2 von 3) - und er traegt zusaetzlich in der AKKUMULATIONSlage (+0,0470, p 0,000). ⚠️ Die Entscheidung ueber die Registrierung ist eine NUTZERENTSCHEIDUNG und loest R-R9 aus: die Schwelle 0,080 waere neu zu kalibrieren

- Quelle: V1/V2/V9 · Vierfachtest · 2.286-schnitt
- **Abgeloest durch: 2.325**
- Warum: Kriterium 2 war fehlerhaft konstruiert (2.324): ,stabil' hiess dort nur ,das Band schliesst die Null ein', ohne Trennschaerfe und auf EINER Menge statt allen. Richtig gemessen ist `schnitt`s Haelftenunterschied auf der 20-%%-Menge NACHGEWIESEN (+0,1973 [+0,0717 .. +0,3892], 20/20 Bloecke) - er hat DREI Kriterien, nicht vier. ⚠️ Reproduziert vor dem Widerruf, dreifach (2.321), R-R11 erfuellt

**2.187-was-haelt** — ✔ WAS REPRODUZIERT: `schnitt` ist weiterhin NICHT ROBUST (traegt nur bei 20 %, nicht bei 10 % oder frei) · `amihud`, `rsi`, `momentum` und `schnitt50` bleiben abgelehnt, auf ALLEN Mengen · `zufall` traegt nirgends. Die tragenden Ablehnungen des 07.09. stehen

- Quelle: Methodik 2.187
- **Abgeloest durch: 2.331-2187**
- Warum: Die Teilaussage zu `schnitt50` (,bleibt abgelehnt, auf ALLEN Mengen') ist FALSCH - er traegt auf 10 %% (+0,0846) und 20 %% (+0,0698), nur auf 50 %% nicht. 2.219 hatte recht. Der Rest des Befundes steht

**2.172-streuung** — „In Streuungseinheiten liegen die Effekte fast gleichauf - Aktien 0,038, Rohstoffe 0,070"

- Quelle: Methodik 2.172
- **Abgeloest durch: 2.175**
- Warum: HANDRECHNUNG mit dem falschen Nenner: ich habe durch die Streuung der GANZEN Klasse geteilt, gemessen wird aber die Kandidatenwelt (bei Rohstoffen IQA 4,775 statt 1,715). Sauber gemessen (N-80): Aktien +0,015, Rohstoffe +0,025 gegen Krypto +0,059

**2.164-turnover** — „`turnover` traegt auf 50 % (+0,0909, Urteil TRAEGT) und ist damit voll rehabilitiert"

- Quelle: Methodik 2.164
- **Abgeloest durch: 2.187**
- Warum: R-R11 auf der NEUEN Messbasis (08.09., 536 Symbole): die WIRKUNG reproduziert auf drei Stellen (+0,0913 gegen +0,0909), aber das URTEIL auf 50 % ist jetzt 'NICHT TRENNBAR' - der Nullpunkt hat sich in das Band geschoben. ⚠️ `turnover` traegt weiterhin, aber auf `frei` (+0,0639, TRAEGT), nicht auf 50 %

**2.157-form** — „Die Form ist entschieden: REGLER +0,1759 R schlaegt SCHALTER +0,0040 R"

- Quelle: Methodik 2.157
- **Abgeloest durch: 2.158**
- Warum: der Schalter-Arm hat NIE einen Schalter gemessen. `pruefe_auswahl` sperrt Rang >= 0,8; bei einer 0/1-Kennzahl mit 65,2 % Einsen liegt das oberste Rangfuenftel GANZ in der Einser-Gruppe, und `rang` bricht Gleichstaende nach ARRAY-REIHENFOLGE. Belegt: nach Umsortieren der Zeilen EINES Tages sind nur 15 von 62 Symbolen dieselben. Der Arm mass eine BELIEBIGE Teilmenge - +0,0040 R ist genau das erwartete Nichts. Die Formfrage ist wieder OFFEN

**2.141** — „`turnover`s Stufen lassen sich nicht herleiten"

- Quelle: Methodik 2.141
- **Abgeloest durch: 2.143**
- Warum: auf der FREIEN Menge gemessen, wo selbst funding bei -0,0003 R liegt. Auf der selektierten reproduziert turnover: +0,0635 gegen registriert +0,0616 (F-212)

**2.142** — „Kalibrierung durchgefuehrt: turnover auf +0,33/-0,48, Schwelle 0,005"

- Quelle: Methodik 2.142
- **Abgeloest durch: 2.143**
- Warum: ZURUECKGENOMMEN - stand auf 2.139 und 2.141, beide gefallen. Es bleibt der R-R9-Verstoss (nach Wirkung statt Durchlassquote kalibriert) und die Reproduktion des Verfahrens

**2.139-quote-deutung** — „`q` in der Potentialformel zaehlt einen wertlosen Kanal mit"

- Quelle: Methodik 2.139
- **Abgeloest durch: 2.140**
- Warum: falsch adressiert. Die Kette hat KEINEN Zeitausstieg - in der Produktion laeuft eine Position bis Stop oder Ziel. Der Fehler sitzt in der Messkonvention mit festem Horizont, nicht in der Formel

**Audit-H20R** — „Die Registrierungsbasis H20/R ist kontaminiert"

- Quelle: Audit 06.09.
- **Abgeloest durch: 2.139**
- Warum: zu stark formuliert. Belegt war die Kontamination fuer H5 mit `vola`; bei H20 mit externen Kennzahlen feuert `bewegung_r` in keiner der beiden Kunstwelten

**2.133-turnover** — „`turnover` ist in keiner Form belegt und gehoert stillgelegt"

- Quelle: Methodik 2.133
- **Abgeloest durch: 2.136**
- Warum: auf der Barrieren-Quote gemessen, die Aufloesung und Richtung mischt. Richtungsrein ist turnover der staerkste der drei

**2.133-vola** — „`vola` ist die einzige Groesse mit belegter Stufenordnung und gehoert registriert"

- Quelle: Methodik 2.133
- **Abgeloest durch: 2.135**
- Warum: an der Barrieren-Quote gemessen, die Aufloesung und Richtung mischt. Richtungsrein bleibt nichts uebrig

**2.113-M4** — „tief im Rang = mehr Chance ist widerlegt - in R wird nach unten alles schlechter"

- Quelle: Methodik 2.113
- **Abgeloest durch: 2.115**
- Warum: am MITTELWERT gemessen und unzulaessig zu einer Asset-Aussage verallgemeinert - Regel 3

**2.113-S3** — Rangzugehoerigkeit traegt (+0,1020 R zwischen „in Top 100 geblieben" und „neu")

- Quelle: Methodik 2.113
- **Abgeloest durch: 2.114**
- Warum: GEPOOLT gerechnet. Mit Tagesklammer +0,0379, Band [-0,0317 .. +0,1030] - traegt nicht

**2.116-9.7** — Die 9,7 % Ueberdeckung zwischen System und Messuniversum sind ein Problem

- Quelle: Methodik 2.116
- **Abgeloest durch: 2.116-Korrektur**
- Warum: Nutzerkorrektur: die Bewertung muss allgemein und neutral funktionieren. Auf die gehandelten Symbole zu messen waere ein Zirkelschluss

**2.111-ab2024** — Der Abschnitt ab 2024 ist die primaere Messbasis

- Quelle: Methodik 2.111
- **Abgeloest durch: 2.119**
- Warum: Die Wirkung der Kandidaten ist NICHT epochenabhaengig. Auf 959 Tagen sind sie in JEDEM Fenster unentscheidbar - Datenmenge, nicht Epoche. Primaer ist jetzt die volle Historie

**S3-Meldung** — Beide registrierten Beitraege fallen bei H5 ab 2024

- Quelle: Schritt 3, 06.09.
- **Abgeloest durch: 2.119**
- Warum: Zwei Groessen gleichzeitig geaendert (Horizont UND Epoche). Alle drei Registrierungen reproduzieren auf ihrer eigenen Basis - R-R11

**N1** — Traegt `vola` unabhaengig, oder ist es redundant zu funding/turnover?

- Quelle: Schritt 4a
- **Abgeloest durch: 2.120**
- Warum: beantwortet: KEIN Mitlaeufer (82 % bleiben), aber auch nicht reif - 18 % Ueberlappung mit turnover belegt (Rang 1 von 40, p=0,025), Rest nicht trennbar

**F-206-Anfuehrung** — F-206 (turnover+vola praktisch identisch) belegt Redundanz bei N1

- Quelle: eigene Anfuehrung 06.09.
- **Abgeloest durch: 2.120**
- Warum: F-206 wurde auf H2/Frontloading gemessen; F-207 haelt fest, dass sich das nicht auf H20/R uebertraegt. Die Anfuehrung war eine Horizontverwechslung

**N5** — Traegt die KOMBINATION `vola` UND `turnover` am Randmassstab mehr als jede Groesse einzeln?

- Quelle: Methodik 2.120
- **Abgeloest durch: 2.121**
- Warum: beantwortet: ODER traegt (+0,00777), mengenkontrolliert +26 % bis +34 % ueber der besten Einzelgroesse, beide Haelften, drei Saaten. UND traegt NICHT

**N8** — `turnover` ist bereits als Regler am Mittel registriert - eine Sperre mit `turnover` wendet ihn ZWEIMAL an

- Quelle: Methodik 2.121
- **Abgeloest durch: 2.122**
- Warum: KEINE Doppelzaehlung: wo turnover vorliegt (7 von 57), verlangt das Tor ohnehin Fuenftel 0 - die Sperre wuerde Fuenftel 4 sperren, das nie durchkommt. Wo er fehlt (50 von 57), kann die Sperre ihn nicht auswerten. Wirkungslos, nicht doppelt

**88-Prozent-Meldung** — 88 % der beobachteten Werte koennen die Potentialschwelle nie erreichen

- Quelle: eigene Rechnung 06.09.
- **Abgeloest durch: 2.122**
- Warum: gegen die FESTE Vorgabe 0,080 gerechnet statt gegen `Potential.schwelle` je Datenlage. Das Projekt hatte genau diesen Fehler am 31.08. selbst gemacht und behoben - ich habe ihn nachgebaut

**N12** — Traegt `vola` ALLEIN als Sperre genug?

- Quelle: Methodik 2.122
- **Abgeloest durch: 2.123**
- Warum: JA - bei allen vier Sperrmengen (10/20/30/40 %). Bei 40 % erreicht sie 83 % der Kombinationswirkung bei 516 statt 65 Symbolen. Der Kompromiss kostet 17 % Wirkung fuer die achtfache Abdeckung

**Breite-Hebel** — Eine engere Auswahl verbessert die Frontloading-Verschiebung um 40 %

- Quelle: eigene Lesart 06.09.
- **Abgeloest durch: 2.124**
- Warum: Punktschaetzer-Vergleich ohne Deckung. Die Baender ueberlappen vollstaendig: +4,0 [+2,8 .. +5,2] gegen +4,5 [+2,8 .. +6,2]

**Kursreihe-Nullaussage** — Die Kursreihe liefert die Instrumentwahl nicht

- Quelle: eigene Formulierung 2.123
- **Abgeloest durch: 2.124**
- Warum: Kapitulationsformel statt Analyse. Der richtige Vergleich ist nicht ein perfekter Waehler, sondern der TAKT - und der hat null gemessenen Vorteil (Regel 1)

**N9** — 36 % Sperrmenge bei zwoelf bestehenden Trichterstufen - welche Durchlassmenge bleibt?

- Quelle: Methodik 2.121
- **Abgeloest durch: 2.126**
- Warum: Die Frage war falsch gestellt. Die Werte passieren die Auswahl ueber den BESTANDSVORRANG, nicht ueber den Momentum-Rang (F-180/F-182) - eine Durchlassrechnung auf der Momentum-Auswahl bildet den Betrieb nicht ab. Und eine vola-Sperre stuende vor derselben Gabel wie N-14: mit Bestandsausnahme wirkungslos, ohne sie trifft sie genau die Werte, die als einzige durchkommen

