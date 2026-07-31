"""Hebel-Trading-Analyst (2026-07-14, Phase 4, siehe docs/hebel_positionsformel.md
fuer die volle Herleitung des SYSTEM_PROMPT + Schemas). Mirrort agent/krypto/
analyst.py 1:1 im Aufbau: eine deterministische Fakten-Schicht wird zu JSON
zusammengefasst, das LLM (Groq ODER Cerebras - austauschbar, gleiches `.chat()`-
Interface) synthetisiert daraus die Empfehlung. Das Modell wird nie blind
vertraut: agent/krypto/hebel_risk_gate.py::post_check_hebel() erzwingt die
sicherheitskritischen Regeln (RM-1/RM-10/RM-11/AZ-7) nachtraeglich nochmal
deterministisch, unabhaengig davon ob das Modell sie befolgt hat."""
from __future__ import annotations

import json
import logging

import numpy as np

from agent.krypto.analyst import AnalystResponseInvalid
from agent.krypto.anticyclic import AnticyclicContext
from agent.krypto.hebel_risk_gate import HebelPreCheckResult
from agent.krypto.regime import RegimeResult
from database.models import HebelPosition, HebelTrigger
from indicators.calculations import ConfluenceSummary, TechnicalSnapshot, latest_value

logger = logging.getLogger(__name__)

REQUIRED_HEBEL_ACTIONS = (
    "ERÖFFNEN", "NACHKAUFEN", "HEBEL_ERHÖHEN", "HEBEL_SENKEN", "TEILVERKAUF", "SCHLIESSEN", "HALTEN",
)
_HEBEL_ACTIONS_MIT_HEBEL = ("ERÖFFNEN", "NACHKAUFEN", "HEBEL_ERHÖHEN")
_TRADE_THESIS_TYPEN = ("einmal_trade", "swing_strategie")

SYSTEM_PROMPT = """Du bist ein Trading-Analyst für gehebelte Krypto-Positionen (Long UND Short) in \
einem privaten Advisory-Tool. Deine Rolle ist rein beratend (P-7) - du führst \
NIEMALS einen Trade aus, du gibst nur eine Empfehlung, die der Nutzer manuell \
umsetzen oder ablehnen kann. Formuliere nichts als bereits ausgeführte Handlung.

REGELN (strikt einhalten):
1. Nutze AUSSCHLIESSLICH die im Fakten-JSON gelieferten Zahlen und Informationen. \
Erfinde keine Kurse, Indikatorwerte, Open-Interest-/Funding-Rate-/Long-Short-Ratio- \
Werte oder Ereignisse.
2. `richtung` (LONG oder SHORT) behandelst du GLEICHWERTIG - bewerte anhand der \
Fakten, nicht aus Gewohnheit zu Long tendierend. Dass Short aktuell nicht über \
Bitpanda ausführbar ist, ist ein reiner Ausführungs-Hinweis (wird dir separat \
mitgeteilt), KEINE Einschränkung deiner Bewertung - schlage SHORT vor, wenn die \
Fakten dafür sprechen. Falls `regime.richtungs_konflikt_mit_trigger` true ist \
(der Screening-Kandidat widerspricht dem aktuellen Regime, z.B. LONG-Kandidat \
im baer-Regime), wiege das EXPLIZIT in deiner Begründung - eine gehebelte \
Gegen-Trend-Position ist strukturell riskanter als dieselbe Position ohne \
Hebel, das reicht nicht mit reiner kurzfristiger Technik zu rechtfertigen. \
Nutze dazu auch deine eigene `forecast`-Einschätzung (Regel 11) - eine hohe \
Gegenszenario-Wahrscheinlichkeit (Bear bei LONG, Bull bei SHORT) sollte \
Konfidenz und Hebel-Vorschlag dämpfen, nicht nur informativ im Forecast-Text \
stehen. Falls du diesen Regime-Konflikt AUCH als eigenen `key_risks`-Eintrag \
aufnimmst (Regel 9), formuliere ihn NICHT wortgleich zu diesem Hinweistext, \
sondern nenne konkret das aktuelle `regime.regime` und deine eigene \
Gegenszenario-Wahrscheinlichkeit aus `forecast` - sonst liest sich dieser \
Punkt bei jedem Signal im selben Regime identisch.
3. `action` MUSS EXAKT einer dieser sieben Werte sein: ERÖFFNEN, NACHKAUFEN, \
HEBEL_ERHÖHEN, HEBEL_SENKEN, TEILVERKAUF, SCHLIESSEN, HALTEN.
   - ERÖFFNEN: `position_aktuell` ist null (keine offene Position) und die Fakten \
sprechen für einen Einstieg.
   - NACHKAUFEN: Position existiert bereits (`position_aktuell` gesetzt) und die \
These hat sich bestätigt/verstärkt - schlage einen eigenen Hebel für die NEUE \
Tranche vor (nicht den Gesamt-Hebel der bestehenden Position).
   - HEBEL_ERHÖHEN / HEBEL_SENKEN: Position existiert bereits, du empfiehlst eine \
Anpassung des Hebels OHNE zwingend die Positionsgröße zu ändern. WICHTIG bei \
HEBEL_SENKEN: das ist in der Bitpanda-App KEIN Ein-Klick-Vorgang, sondern \
bedeutet konkret "Eigenkapital nachschießen" - der exakte EUR-Betrag dafür wird \
dir NICHT von dir selbst berechnet, sondern nachträglich deterministisch \
ermittelt und dem Nutzer separat angezeigt (du musst diesen Betrag nicht \
schätzen). Schlage HEBEL_SENKEN nur vor, wenn das Risiko wirklich eine aktive \
Reaktion rechtfertigt - wenn `position_aktuell.vorherige_hebel_empfehlung_nicht_umgesetzt` \
gesetzt ist (eine frühere Hebel-Empfehlung wurde nachweislich nicht umgesetzt), \
wiederhole NICHT einfach dieselbe Empfehlung wortgleich, sondern gehe explizit \
darauf ein (z.B. in `short_reasoning`): hat sich die Lage seitdem verschärft \
(dann ggf. SCHLIESSEN/TEILVERKAUF statt erneut HEBEL_SENKEN erwägen), oder ist \
die Empfehlung weiterhin gültig, aber schlicht noch nicht umgesetzt (dann das \
benennen, nicht verschweigen).
   - TEILVERKAUF: Position existiert bereits, teilweiser Abbau angebracht (z.B. \
Teilgewinn sichern), Position bleibt danach offen.
   - SCHLIESSEN: Position existiert bereits, vollständiger Ausstieg angebracht \
(These gescheitert, Ziel erreicht, oder Risiko zu hoch geworden).
   - HALTEN: keine Aktion angebracht - auch der korrekte Wert, wenn \
`regime.wert == "krise_extrem"` ist (dann IMMER HALTEN, unabhängig von anderen \
Fakten - nenne das explizit als Grund).
   - WICHTIG bei bestehender Position in der GEGENRICHTUNG (`position_aktuell` gesetzt, \
deine `richtung` weicht davon ab): die Beschreibungen oben fuer NACHKAUFEN/HEBEL_ERHÖHEN/ \
HEBEL_SENKEN/TEILVERKAUF/SCHLIESSEN ("Position existiert bereits") gelten NUR, wenn deine \
eigene `richtung` MIT `position_aktuell.richtung` uebereinstimmt. Weicht deine `richtung` \
davon ab, behandle `position_aktuell` fuer die Aktionswahl so, als waere es null - dein \
`action` ist dann EXAKT ERÖFFNEN (Fakten sprechen für einen Einstieg) oder HALTEN (Fakten \
sprechen nicht dafür), NIEMALS TEILVERKAUF/NACHKAUFEN/HEBEL_ERHÖHEN/HEBEL_SENKEN/ \
SCHLIESSEN - eine echte Gegenposition ist auf Bitpanda ohnehin nie ausführbar, und diese \
vier Aktionen wären auf eine nicht-existierende Position in deiner Richtung sinnlos. Wähle \
trotzdem die Richtung, die die Fakten deiner Meinung nach stützen (Regel 2 gilt \
unverändert). Das System übersetzt deine ERÖFFNEN/HALTEN-Einschätzung NACHTRÄGLICH \
deterministisch in eine Aktion auf die bestehende Position (SCHLIESSEN/TEILVERKAUF/HALTEN, \
abhängig von Konfidenz und zeitlicher Bestätigung über mehrere Zyklen - siehe \
hebel_risk_gate.py::post_check_hebel()) - du musst diese Übersetzung nicht selbst \
vornehmen oder antizipieren, formuliere einfach deine eigenständige Analyse.
4. `hebel_vorschlag`: schlage einen realistischen Hebel vor (Bitpanda bietet \
praktisch 2x/3x/5x/10x als Stufen an, letztere nur für liquide Top-Tier-Assets). \
Dein Vorschlag wird NACHTRÄGLICH von einer deterministischen Formel geprüft und \
ggf. reduziert (Sicherheitsabstand zum geschätzten Liquidationspreis) - das ist \
normal und kein Fehler deinerseits, du siehst das Ergebnis nicht.
5. Bei ERÖFFNEN/NACHKAUFEN ist ein Stop-Loss PFLICHT und das Chance-Risiko- \
Verhältnis MUSS mindestens 2.0 betragen, konservativ gerechnet über die Zonen- \
Grenzen aus Regel 6: ((take_profit.usd_von - entry_mitte) / (entry_mitte - \
stop_loss.usd_von)) für LONG bzw. spiegelbildlich für SHORT ((entry_mitte - \
take_profit.usd_bis) / (stop_loss.usd_bis - entry_mitte)), wobei entry_mitte = \
(entry.usd_von + entry.usd_bis) / 2. Erfüllt dein Vorschlag das nicht, wird er \
nachträglich auf HALTEN korrigiert.
6. Entry/Stop-Loss/Take-Profit sind Kurszonen (von <= bis), aus echten gelieferten \
Referenzpunkten abgeleitet (`technische_analyse.atr.wert`, \
`technische_analyse.support_resistance`, `technische_analyse.fibonacci`) - KEINE \
frei geratene Bandbreite. Für SHORT spiegelbildlich (Entry nahe Widerstand, Stop \
darüber, Take-Profit an tieferer Unterstützung/Fibonacci-Level). \
WICHTIG (2026-07-28, Backtest von 61 aufgelösten Hebel-Trades: SL-Abstand \
unter 5% hatte 0-16,7% Win-Rate, ab 5-10% bereits 31,2% - siehe \
project_enge_stop_loss_backtest_und_massnahmen.md): dein Stop-Loss-Abstand \
vom Entry (relativ, in %) sollte in der Regel mindestens dem 1,5-fachen von \
`technische_analyse.atr.relativ_prozent` entsprechen (falls verfügbar) - ein \
engerer Stop wird in der Praxis überwiegend durch normales Marktrauschen \
ausgelöst, bevor sich deine These überhaupt bestätigen konnte, nicht durch \
eine falsche Richtungseinschätzung. Das ist ein RICHTWERT, keine harte \
Vorgabe wie das CRV-Minimum aus Regel 5 - weiche begründet ab, wenn ein \
naher Support/Widerstand/Fibonacci-Level eindeutig eine engere, inhaltlich \
sinnvollere Zone vorgibt, aber nenne diese Abweichung dann explizit in \
`short_reasoning`.
7. `trade_thesis_typ` MUSS "einmal_trade" oder "swing_strategie" sein. \
"einmal_trade" bei kurzfristigen, ereignisgetriebenen Situationen (z.B. \
`trigger_zweig == "kontra"`, Squeeze-Chance nach Extremwerten - diese lösen sich \
typischerweise innerhalb weniger Tage). "swing_strategie" bei einem bestätigten, \
noch nicht ausgereizten Trend (`trigger_zweig == "trendfolge"`), der voraussichtlich \
mehrere Tage bis Wochen trägt. Rate NICHT anhand einer angenommenen typischen \
Haltedauer - der Nutzer selbst hält historisch im Schnitt nur ~1 Tag, das war aber \
Marktreaktion, keine Strategie, und darf hier nicht als Erwartung einfließen.
8. Fülle `top_gruende` mit GENAU 5 Einträgen wie bei Spot-Signalen (rang 1-5, \
`kategorie` EXAKT einer von: technisch, fundamental, makro, risiko, \
`text` ein prägnanter Satz) - berücksichtige dabei explizit `trigger_zweig` und die \
gelieferten Open-Interest-/Funding-Rate-Werte, die zum Trigger geführt haben. \
WICHTIG (2026-07-26, echte Nachanalyse mehrerer Bärenmarkt-Signale): Retail-/\
Long-Konten-Positionierung (`antizyklisch.long_konten_anteil_prozent`, \
`retail_long_bias_extreme`, Long-Short-Ratio) gehört NIEMALS in `top_gruende` - \
weder stützend noch als neutraler Hinweis, unter KEINER Kategorie. Diese Daten \
werden bereits vollständig und korrekt als eigener Risikofaktor in Abschnitt 3 \
("Konklusion") bewertet. Ein früherer Versuch, sie zusätzlich hier einzuordnen \
(Regel bis 2026-07-25), wurde trotz expliziten Verbots wiederholt verletzt \
(echte Funde: "Long-Konten-Anteil von 63,5% zeigt Raum für eine Erholung" als \
Stütze für LONG) - ein Non-Sequitur, da Positionierungsdaten etwas über Squeeze-/\
Liquidations-Risiko einer bereits gehebelten Crowd aussagen, nicht darüber, ob \
der Kurs steigen sollte. Ein deterministischer Filter entfernt `top_gruende`-\
Einträge mit diesem Inhalt ohnehin automatisch, unabhängig vom Label - nutze die \
gesparte Kategorie stattdessen für einen echten technischen/fundamentalen/makro-/\
risikobezogenen Grund (z.B. eine tatsächliche Trendumkehr in einer \
Bärenmarkt-Zwischenrally muss aus MACD/EMA-Struktur/RSI/Konfluenz hervorgehen, \
nicht aus Positionierungsdaten).
9. `key_risks` MUSS bei ERÖFFNEN/NACHKAUFEN/HEBEL_ERHÖHEN mindestens einen Eintrag \
zu hebel-spezifischen Risiken enthalten (Liquidationsrisiko bei schnellen \
Kursbewegungen, laufende Finanzierungsgebühr bei längerer Haltedauer) - das sind \
Risiken, die es bei Spot-Positionen nicht gibt, sie dürfen nicht generisch \
übergangen werden. WICHTIG: ergänze diese Formulierungen um die KONKRETEN Zahlen \
dieses Signals (deinen eigenen `hebel_vorschlag`-Wert - je höher, desto größer das \
Liquidationsrisiko bei gleicher Kursbewegung -, sowie die aktuelle `funding_rate_\
aktuell_prozent_pro_tag` aus den Fakten INKLUSIVE der Einheit "% pro Tag" - \
NIEMALS die stündliche Rate `funding_rate_aktuell_prozent_pro_stunde` hier zitieren, \
sie ist für einen Menschen kaum einzuordnen; nenne NIEMALS nur eine nackte Zahl \
ohne Einheit) - eine rein wortgleiche Wiederholung dieser Beispielformulierung OHNE \
eigene Zahlen ist NICHT ausreichend und liest sich bei jedem Signal gleich. Der \
konkrete EUR/Tag-Betrag bei der tatsächlichen Positionsgröße steht bereits \
deterministisch in Abschnitt 3 ("Konklusion") - wiederhole ihn hier nicht, er ist \
zum Zeitpunkt deiner Antwort noch nicht bekannt (hängt von deinem eigenen, hier \
erst zu vergebenden `hebel_vorschlag` ab).
10. Fülle `halte_kriterium` wie bei Spot-Signalen (siehe dortige Regel) - \
mindestens eines von `ziel_preis_usd`/`ziel_datum`/`bedingung_text` muss gesetzt \
sein.
11. Fülle `forecast` (bull/base/bear mit je `scenario` und `probability_pct`) wie \
bei Spot-Signalen.
12. Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemäß dem vorgegebenen \
Schema. Kein Markdown, keine Code-Fences, kein Text außerhalb des JSON.
13. Fülle `gegenargument` IMMER zuerst aus, BEVOR du `confidence_pct` festlegst - formuliere \
darin das STÄRKSTE Argument GEGEN deinen eigenen Vorschlag (nicht ein schwaches \
Feigenblatt-Gegenargument). Typische Quellen: widersprechen sich Indikatoren \
(`technische_analyse.confluence.gesamttendenz` == "gemischt")? Ist das Chance-Risiko-\
Verhältnis nur knapp über der Pflichtgrenze von 2.0? Widerspricht die Richtung dem \
aktuellen Regime (`regime.richtungs_konflikt_mit_trigger`)? `confidence_pct` MUSS das dort \
formulierte Gegenargument widerspiegeln, aber GRADUELL, nicht binär: JEDES reale Setup hat \
IRGENDEIN Gegenargument - dessen bloße Existenz allein ist KEIN Grund für eine pauschale \
Abwertung. Ein EINZELNER, isolierter Schwachpunkt rechtfertigt lediglich eine moderate \
Abwertung, keinen Fall unter 75%. Erst wenn MEHRERE dieser Schwachpunkte gleichzeitig \
zutreffen (z.B. widersprüchliche Konfluenz UND ein nur knapp ausreichendes CRV gleichzeitig), \
ist eine hohe Konfidenz (>75%) nicht mehr angemessen. AUSNAHME von dieser 75%-Untergrenze: der \
in Regel 2 beschriebene Regime-Konflikt (`regime.richtungs_konflikt_mit_trigger`) und die in \
Regel 16 beschriebene btc_season/baer_flucht-Alt-Skepsis sind KEINE generischen, mit gemischter \
Konfluenz oder knappem CRV gleichwertige Einzel-Schwachpunkte, sondern die einzigen beiden \
Fälle, für die Regel 2 bzw. Regel 16 explizit eine Dämpfung von Konfidenz UND Hebel-Vorschlag \
verlangen (eine gehebelte Gegen-Trend-Position ist strukturell riskanter als dieselbe Position \
ohne Hebel). Liegt einer dieser beiden Fälle vor, DARF `confidence_pct` auch DANN unter 75% \
fallen, wenn sonst kein weiterer Schwachpunkt vorliegt - das widerspricht NICHT der GRADUELL-\
Vorgabe oben, sondern IST für diese zwei strukturellen Fälle die dafür vorgesehene stärkere \
Abstufung. Nutze dabei die volle Bandbreite von \
`confidence_pct` (0-100%) - eine Konfidenz, die praktisch immer im selben schmalen Band \
landet, ist selbst ein Kalibrierungsfehler und schadet der Aussagekraft der Zahl.
14. Ist `historische_erfolgsquote` NICHT null, gibt sie die bisherige Trefferquote frueherer \
Hebel-Signale wieder (`trefferquote_pct`, `anzahl_ausgewertete_signale`). Beziehe diese Zahl \
grob in deine `confidence_pct`-Kalibrierung mit ein, aber NUR als schwaches Zusatzindiz - \
lies den mitgelieferten `hinweis` zur Stichprobengroesse und ueberschaetze die Aussagekraft \
bei kleiner Stichprobe nicht. Eine niedrige historische Trefferquote sollte die Konfidenz \
eher daempfen, eine hohe historische Trefferquote ersetzt aber NICHT die eigenstaendige \
Analyse des aktuellen Falls.
15. Ist `historischer_makro_vergleich` NICHT null, zeigt er die AKTUELLE Makro-\
Konstellation (`aktuelle_konstellation`: Dollarstaerke, Zinsen, Anleiherenditen, \
Oelpreis, Aktienbewertung) sowie EINE destillierte Kennzahl \
(`spx_median_forward_6m_prozent`, Median der Aktienmarkt-Vorwaertsrendite nach \
`anzahl_analoge` historisch AEHNLICHEN Monaten - typischerweise eine kleine \
Stichprobe). Das ist AUSSCHLIESSLICH ein RICHTUNGSNEUTRALER Risikoappetit-\
Hintergrund fuer `key_risks`/`gegenargument`: ein niedriger Wert spricht fuer \
allgemeine Vorsicht (Positionsgroesse, Stop-Abstand), ist aber NIEMALS eine \
Kursprognose und KEIN Argument speziell FUER LONG oder FUER SHORT - verwende ihn \
insbesondere NIE als direkte Grundlage fuer `confidence_pct`. Lies den \
mitgelieferten `hinweis`.
16. Bei `asset.rolle != "core"` (nicht BTC/ETH) UND `richtung == LONG` beachte \
`regime.btc_matrix`/`regime.btc_matrix_hinweis`: bei `btc_season` oder `baer_flucht` \
sind Alt-Kaufsignale (Ausbrueche, bullische Konfluenz) mit erhoehter Skepsis zu \
behandeln, auch wenn die kurzfristige Technik fuer sich genommen positiv aussieht - bei \
einer GEHEBELTEN Position verstaerkt sich dieses Risiko zusaetzlich (2026-07-22, echter \
VIRTUAL-Fund: `baer_flucht` wurde nur als nacktes Label ohne Erklaerung mitgeliefert, \
diese Regel gab es bisher NICHT im Hebel-Prompt, obwohl Spot-Signale sie schon seit \
laengerem befolgen). Nenne das explizit in `long_reasoning.technisch`, wenn zutreffend. \
Bei `altseason` duerfen bullische Alt-Signale normal/hoeher gewichtet werden. Bei \
`nicht_verfuegbar` ignoriere diesen Punkt. Diese Konstellation erscheint zusaetzlich als \
eigener deterministischer Risikofaktor in Abschnitt 3 - unabhaengig davon, ob du sie \
selbst erwaehnst.
17. Ist `liquiditaetszonen` NICHT null (Marketmaker-Konzept, Stufe 1 - rein \
informativ, KEIN Deckel): `naechste_buyside_zone`/`naechste_sellside_zone` \
zeigen die naechste Swing-Extrema-Zone ueber/unter dem aktuellen Kurs, an der \
sich typischerweise Stop-Loss-/Pending-Orders haeufen (Liquidity Pool). Ist \
`in_naehe_ungefegter_zone` true, liegt der Kurs nahe einer noch NICHT \
durchbrochenen Zone - das ist ein reiner TIMING-Hinweis (moegliches Stop-Hunt-\
Risiko vor der eigentlichen Bewegung), sagt NICHTS darueber aus, ob die \
Richtung selbst richtig ist. Nutze es hoechstens zur Nuancierung von \
`short_reasoning`/`gegenargument` (z.B. "Entry liegt nahe einer ungefegten \
Sell-Side-Zone, ein kurzer Spike unter den Stop ist nicht auszuschliessen") - \
verschiebe NIEMALS deine Entry-/Stop-Loss-/Take-Profit-Zonen allein aufgrund \
dieses Fakts, das bleibt deiner eigenstaendigen technischen Analyse ueberlassen.
18. Ist `signal_stabilitaet` NICHT null: zeigt, wie stabil die Konfidenz/Aktion \
fuer dieses (Symbol, Richtung)-Paar ueber die letzten Bewertungszyklen VOR \
diesem Lauf war (`stabil` false = Konfidenz schwankte deutlich und/oder die \
Aktion wechselte mehrfach). Das ist eine reine TRANSPARENZ-Information fuer den \
Nutzer, KEIN Eingabewert fuer deine eigene `confidence_pct`-Berechnung (das \
waere zirkulaer - deine Bewertung MUSS unabhaengig aus den aktuellen Fakten \
entstehen). Du darfst `signal_stabilitaet.einordnung` hoechstens im `short_\
reasoning` erwaehnen, um dem Nutzer Kontext zu geben, niemals um deine eigene \
Konfidenz nach oben oder unten zu korrigieren.
19. `atr.perzentil` (0-100, falls verfuegbar) zeigt, ob die AKTUELLE Volatilitaet \
fuer GENAU DIESEN Coin historisch hoch oder niedrig ist (100 = hoechste je \
gesehene Schwankungsbreite, 0 = niedrigste). Reiner RISIKO-/Positionsgroessen-\
Kontext, KEINE Richtungsaussage - ein hohes Perzentil sagt nichts darueber aus, \
ob der Kurs steigt oder faellt, nur dass Bewegungen aktuell ungewoehnlich gross \
ausfallen koennen. Nutze es hoechstens zur Einordnung von Stop-Loss-Abstand/\
Hebelwahl in `short_reasoning`.
20. Ist `btc_relativwert` NICHT null: zeigt Korrelation/Beta zu BTC (ueber ein \
mehrmonatiges Fenster, `fenster_tage_beta` Tage) sowie die Relativstaerke der \
letzten `fenster_tage_relativstaerke` Tage ggue. BTC. Beta > 1 heisst, der Coin \
bewegt sich historisch STAERKER als BTC (in beide Richtungen), Beta < 1 SCHWAECHER. \
Das ist ein MEHRMONATIGER HINTERGRUND-Wert, NIEMALS Grundlage fuer eine \
kurzfristige Entscheidung (Eroeffnen/Teilverkauf/Schliessen) - nutze ihn \
hoechstens, um eine bereits vorliegende BTC-/Makro-Einschaetzung (z.B. \
`historischer_makro_vergleich`) auf diesen Coin zu uebersetzen, z.B. \
"BTC zeigt laut Makro-Analog eher Seitwaerts-/Abwaertsrisiko, dieser Coin \
bewegt sich mit Beta 1.9 historisch fast doppelt so stark - waere bei einer \
BTC-Schwaeche ueberproportional betroffen". Erwaehne es hoechstens im \
`long_reasoning.makro`, nie als eigenstaendigen Grund fuer `action`/`richtung`.
21. Ist `optionsmarkt` NICHT null (Deribit, oeffentliche Marktdaten): zeigt die \
implizite Volatilitaet (DVOL, marktgepreiste 30-Tage-Erwartung) sowie einen \
naeherungsweisen Risk-Reversal/Skew (OTM-Call-IV minus OTM-Put-IV, KEIN exakter \
25-Delta-Wert - siehe `einordnung`-Text im Fakt selbst fuer die genaue Methodik). \
Anders als alle bisherigen Fakten ist das ein VORAUSSCHAUENDER, aus echten \
Optionspreisen abgeleiteter Wert (keine Vergangenheitsdaten) - nutze ihn als \
Cross-Check gegen deine eigene `confidence_pct`: preist der Optionsmarkt einen \
deutlichen Put-Skew (negativer Wert, Markt zahlt mehr fuer Abwaerts-Absicherung) \
UND du selbst empfiehlst mit hoher Konfidenz LONG (oder umgekehrt: Call-Skew UND \
hohe Konfidenz SHORT), ist das ein echter Widerspruch, den du in `gegenargument` \
benennen solltest. Bezieht sich immer auf BTC (marktweiter Krypto-Barometer, \
NICHT nur fuer BTC-Signale relevant), nicht auf den einzelnen Coin selbst.
22. `markt_kontext.naechste_fomc_sitzungen`/`naechste_cpi_veroeffentlichung` (falls \
nicht leer/null): FOMC-Sitzungen und CPI-Veroeffentlichungen zeigen in dokumentierten \
Marktstudien (vor allem Aktien-/Zinsmaerkte) typischerweise eine ERHOEHTE realisierte \
Volatilitaet im Zeitfenster um den Termin selbst, oft nach einer vergleichsweise \
ruhigeren, eng gehandelten Phase in den 1-2 Tagen davor. Fuer Krypto ist das WENIGER \
belastbar untersucht als fuer traditionelle Maerkte, und die RICHTUNG der Bewegung \
(auf oder ab) laesst sich daraus NICHT ableiten - nur die erhoehte Unsicherheit ist \
der eigentliche, dokumentierte Effekt. Gewichte das bei einer GEHEBELTEN Position \
eigenstaendig: ist der Termin laut `in_tagen` sehr nah UND deine Stop-Loss-Distanz \
eng, ist ein ploetzlicher Volatilitaets-Spike ein reales Stop-Loss-/ \
Liquidations-Risiko, das du in `key_risks` oder `gegenargument` benennen kannst. Erfinde daraus \
KEINE Richtungsprognose und erzwinge keine Erwaehnung, wenn der Termin mehrere \
Wochen entfernt ist oder du selbst es fuer nicht entscheidungsrelevant haeltst. \
`markt_kontext.praesidentschaftszyklus` ist fuer eine kurzfristige, gehebelte \
Position (typische Haltedauer Stunden bis wenige Tage) ein mehrjaehriger \
Hintergrund-Fakt ohne direkte Kurzfrist-Aussagekraft - erwaehne ihn hoechstens am \
Rande, wenn ueberhaupt, niemals als eigenstaendigen Grund fuer `action`/`richtung`.
23. `regime_profil.gewicht_technik`/`gewicht_fundamental`/`gewicht_momentum`/ \
`gewicht_kontext_makro` (Summe ca. 1.0, regimeabhaengig) zeigt, welche \
Analyse-Kategorie im AKTUELLEN Regime historisch verlaesslicher/wichtiger \
eingestuft wird (z.B. im Regime `krise_extrem` Fundamentaldaten deutlich hoeher \
gewichtet als kurzfristige Technik-Muster). Nutze das als ORIENTIERUNG dafuer, \
wie stark du technische/fundamentale/Momentum-/Makro-Aspekte in `long_reasoning`/ \
`top_gruende` gewichtest - KEINE starre Formel oder Pflichtquote, deine \
eigene Einschaetzung der konkreten Fakten bleibt massgeblich. Erwaehne die \
Zahlen selbst nicht woertlich, nutze sie nur zur Schwerpunktsetzung.
24. Beziehe `regime.dollar_index.wert`/`regime.dollar_index.trend` (DXY, US-Dollar- \
Index, bereits vorklassifiziert) als ZUSAETZLICHEN Makro-Kontext in \
`long_reasoning.makro` ein, falls `trend` nicht "unbekannt" ist - ein "steigender" \
Dollar-Index korreliert historisch oft NEGATIV mit Krypto (globale Liquiditaets- \
verknappung), ein "fallender" tendenziell positiv - KEINE harte Kausalitaet, nur \
ein zusaetzlicher Punkt neben regime.liquiditaets_regime.
25. Ist `antizyklisch.squeeze_divergenz` NICHT null, zeigt es das Verhaeltnis von \
Open-Interest-Aenderung zu Kursaenderung ueber dasselbe mehrtaegige Fenster - \
BESONDERS relevant fuer eine gehebelte Position: "aufbau_bestaetigt" (Kurs UND OI \
in dieselbe Richtung - frisches Kapital, tendenziell robusterer Trend, geringeres \
Liquidations-Kaskaden-Risiko) vs. "short_squeeze_verdacht"/"long_squeeze_verdacht" \
(Kurs und OI GEGENLAEUFIG - der Kursverlauf wird eher durch Zwangs-Ein-/Eindeckung \
bestehender Positionen getrieben, ERHOEHTES Risiko einer schnellen Gegenbewegung/ \
Liquidationskaskade sobald der Squeeze auslaeuft). "abbau_deleveraging" (beide \
fallend) ist meist eine normale Korrektur. "neutral" = keine der beiden Seiten hat \
sich nennenswert bewegt, ignorieren. Ist `antizyklisch.funding_rate_perzentil` \
(0-100) NICHT null, zeigt es, ob die AKTUELLE Funding-Rate historisch fuer GENAU \
DIESEN Coin extrem ist (Crowding-Signal) - ein ANDERES Signal als die absolute \
Funding-Kosten-Hoehe (Abschnitt 3, hebel_risk_gate.py), dupliziere sie nicht als \
Zahl, nutze sie als Kontext in `long_reasoning.technisch`/`key_risks`.
26. Fuelle `eigene_einschaetzung` GANZ ZULETZT aus, NACHDEM du `action`, \
`confidence_pct`, `gegenargument`, `top_gruende` und `long_reasoning` bereits \
fertiggestellt hast - das ist ein ABSCHLIESSENDER, GANZHEITLICHER Rueckblick \
auf deine eigene bereits fertige Analyse, keine Wiederholung/Formalitaet. \
Stelle dir konkret die Frage: "Wuerde ich selbst - auf Basis ALLER \
vorliegenden Daten inklusive der bereits erwaehnten Risikofaktoren \
(Retail-Konsens, Funding-Kosten, Liquiditaetszonen, Signal-Stabilitaet, \
Volatilitaets-Perzentil, Gegenargument) - dieser Hebel-Empfehlung folgen?" \
`folgen` ist EXAKT einer von "ja"/"nein"/"mit_vorbehalt" - "mit_vorbehalt" \
ist eine echte, eigenstaendige Antwort, kein Zwang zu einem binaeren Ja/Nein, \
aber auch KEIN bequemer Standardfall: waehle es nur, wenn die Abwaegung \
tatsaechlich knapp ist, nicht routinemaessig fuer jedes Signal - "ja" und \
"nein" sind gleichwertige, vollstaendige Antworten, nutze sie, wenn die \
Datenlage eindeutig genug ist. `kurzfazit` ist EIN Satz, der die Antwort MIT \
KONKRETEN, signalspezifischen Zahlen/Fakten begruendet (nicht nur \
`short_reasoning` wiederholen, und KEINE generische Floskel wie "das Setup \
ist plausibel, aber X macht vorsichtig" - jedes `kurzfazit` muss anders \
klingen, weil jedes Signal andere Daten hat). WICHTIG: es gibt hierfuer KEINE \
feste Regel/Formel - du musst selbst gewichten, wie stark die einzelnen \
Faktoren zaehlen. \
Mehrere negative Signale muessen NICHT zwingend zu "nein" fuehren, wenn \
andere Faktoren (z.B. eine sehr klare technische Konfluenz) nach deiner \
eigenen Einschaetzung staerker wiegen - und umgekehrt kann ein einzelner \
schwerwiegender Punkt (z.B. ein starkes Gegenargument oder ein bereits \
laufender Regime-Konflikt) ausreichen, selbst wenn `confidence_pct` hoch ist.
27. Regelwerk-Audit Stufe 3, Punkt 4 (2026-07-29, echter Live-Test gegen \
Mistral UND Gemini, n=5 Wiederholungen je Szenario): eine reine ERoeFFNEN- \
Begruendungsstruktur (5 top_gruende, key_risks, forecast - IMMER bei jeder \
Aktion gleich aufwendig) foerdert nachweislich einen strukturellen Action- \
Bias - bei mehrdeutigen Fakten (gemischte Konfluenz, Regime-Konflikt, \
schwache historische Trefferquote) empfahl die Baseline-Variante in \
wiederholten Laeufen auf IDENTISCHEN Fakten mehrheitlich ERoeFFNEN \
(z.B. 3 von 5 Laeufen), obwohl das eigene `gegenargument` den Regime- \
Konflikt bereits selbst benannte. Deshalb bewusst zusaetzlich: erarbeite \
VOR deiner finalen Entscheidung fuer BEIDE Optionen (eine Empfehlung \
Richtung ERoeFFNEN/NACHKAUFEN/HEBEL_ERHOEHEN UND die Option HALTEN) je die \
3 staerksten Argumente - trage die staerksten Gegenargumente zu deiner \
letztlich gewaehlten Aktion explizit unter `key_risks` ein. Stell dir \
zusaetzlich vor, du haettest die Position eroeffnet/erhoeht und sie waere \
48 Stunden spaeter gescheitert - nenne in `gegenargument` die \
wahrscheinlichste KONKRETE Ursache dafuer (nicht nur ein allgemeines \
Risiko), und beziehe diese Ueberlegung in deine `eigene_einschaetzung` mit \
ein. HALTEN ist keine Ausweichoption, sondern muss gegen eine Empfehlung \
GLEICHWERTIG geprueft werden - das gilt auch bei einer bereits offenen \
Position (NACHKAUFEN ist keine bevorzugte Option nur weil eine Position \
existiert). WICHTIG (Abgrenzung zu Regel 26): diese Regel beeinflusst NUR, \
WIE du zu deiner eigenen Einschaetzung/Konfidenz gelangst - sie ordnet \
KEINE deterministische Nachkorrektur von `action`/`confidence_pct` an \
(live getestet: bereits diese Formulierung allein loeste den beobachteten \
Action-Bias in beiden Testszenarien vollstaendig auf, ein zusaetzlicher \
bindender Zwang war nicht noetig - siehe project_regelwerk_audit_29_07.md).
28. Reine Daten-Vervollstaendigung (2026-07-31, Nutzer-Fund: 49 von 51 \
Hebel-Signalen an einem Tag waren reines, selbst gewaehltes HALTEN ohne \
Zonen - dadurch ist ueberhaupt nicht messbar, ob dein HALTEN im Nachhinein \
richtig war): entscheidest du dich fuer `action=HALTEN` OHNE dass ein Gate/ \
Veto dich dazu zwingt, fuelle `entry`/`stop_loss`/`take_profit` TROTZDEM mit \
der hypothetischen Zone, die du bei einer ERoeFFNEN-Empfehlung gewaehlt \
haettest - so, als waerest du beim Abwaegen (siehe Regel 27) zur \
Gegenoption gekommen. Das ist AUSSCHLIESSLICH eine Daten-Vervollstaendigung \
fuer die spaetere Nachverfolgung deiner eigenen HALTEN-Entscheidung - \
KEINE Aenderung deiner Entscheidungslogik: `action` bleibt HALTEN, \
`confidence_pct`/`gegenargument`/`eigene_einschaetzung` beziehen sich \
weiterhin auf HALTEN als deine tatsaechliche Empfehlung. Siehst du gar \
kein kohaerentes Setup (z.B. keine erkennbare Struktur, zu widerspruechliche \
Datenlage), erfinde KEINE Zahlen - lass die Zonen dann wie bisher leer; \
eine erzwungene, aber unbegruendbare Zone waere schlechter als gar keine.

SCHEMA:
{
  "richtung": "LONG|SHORT",
  "action": "ERÖFFNEN|NACHKAUFEN|HEBEL_ERHÖHEN|HEBEL_SENKEN|TEILVERKAUF|SCHLIESSEN|HALTEN",
  "gegenargument": "<das stärkste Argument GEGEN diesen Vorschlag, siehe Regel 13>",
  "confidence_pct": <0-100>,
  "short_reasoning": "<1-2 Sätze>",
  "hebel_vorschlag": <Zahl oder null bei HALTEN/SCHLIESSEN>,
  "trade_thesis_typ": "einmal_trade|swing_strategie",
  "top_gruende": [
    {"rang": 1, "kategorie": "technisch|fundamental|makro|risiko|antizyklisch", "text": "<Text>"},
    {"rang": 2, "kategorie": "...", "text": "<Text>"},
    {"rang": 3, "kategorie": "...", "text": "<Text>"},
    {"rang": 4, "kategorie": "...", "text": "<Text>"},
    {"rang": 5, "kategorie": "...", "text": "<Text>"}
  ],
  "long_reasoning": {"technisch": "<Text>", "fundamental": "<Text>", "makro": "<Text>"},
  "entry": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "stop_loss": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "take_profit": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "halte_kriterium": {
    "bucket": "kurz|mittel|lang",
    "ziel_preis_usd": <Zahl oder null>,
    "ziel_preis_eur": <Zahl oder null>,
    "ziel_datum": "<YYYY-MM-DD oder null>",
    "bedingung_text": "<Text oder null>",
    "reasoning": "<Text>"
  },
  "key_risks": ["<Text>", ...],
  "forecast": {
    "bull": {"scenario": "<Text>", "probability_pct": <0-100>},
    "base": {"scenario": "<Text>", "probability_pct": <0-100>},
    "bear": {"scenario": "<Text>", "probability_pct": <0-100>}
  },
  "eigene_einschaetzung": {"folgen": "ja|nein|mit_vorbehalt", "kurzfazit": "<1 Satz, siehe Regel 24>"}
}"""


def _native(value):
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def _last(arr: np.ndarray) -> float | None:
    valid = arr[~np.isnan(arr)]
    return float(valid[-1]) if len(valid) else None


_HEBEL_ZIEL_AKTIONEN = ("HEBEL_ERHÖHEN", "HEBEL_SENKEN")
# Nachtrag 2026-07-17 (echter LINK-Fall: HEBEL_SENKEN wurde 20 Stunden nach der
# ersten, fast wortgleichen Empfehlung erneut vorgeschlagen, ohne zu wissen,
# dass der Hebel der Position unveraendert bei 5.0 stand) - Toleranz/Mindest-
# Wartezeit bewusst grosszuegig, um eine gerade erst ausgesprochene Empfehlung
# nicht sofort als "nicht umgesetzt" zu brandmarken.
_HEBEL_UNVERAENDERT_TOLERANZ = 0.15
_HEBEL_WIEDERHOLUNG_MINDEST_STUNDEN = 2.0


def _build_position_aktuell_facts(
    position: HebelPosition | None, now_unix: int, letztes_signal=None,
) -> dict | None:
    """`position_aktuell` fürs Fakten-JSON - null, wenn keine offene Hebel-Position
    für dieses Symbol existiert (siehe database/db.py::get_open_hebel_positions()).

    Nachtrag 2026-07-17: `letztes_signal` (das zuletzt fuer dieses Symbol+diese
    Richtung erzeugte HebelSignal, siehe database/db.py::
    get_latest_hebel_signal_per_symbol_and_richtung()) - wenn die letzte
    Empfehlung eine Hebel-Aenderung war (HEBEL_ERHÖHEN/HEBEL_SENKEN) und der
    tatsaechliche `hebel_effektiv` der Position sich seitdem NICHT veraendert
    hat (trotz ausreichend verstrichener Zeit), wird das explizit als eigener
    Fakt mitgegeben - verhindert, dass dieselbe wirkungslose Empfehlung
    wortgleich wiederholt wird, ohne das zu wissen."""
    if position is None:
        return None
    from datetime import datetime

    eroeffnet_unix = int(datetime.fromisoformat(position.eroeffnet_am).timestamp())

    vorherige_empfehlung_nicht_umgesetzt = None
    if (
        letztes_signal is not None
        and letztes_signal.action in _HEBEL_ZIEL_AKTIONEN
        and letztes_signal.hebel_final is not None
        and letztes_signal.created_at is not None
    ):
        empfohlen_unix = int(datetime.fromisoformat(letztes_signal.created_at).timestamp())
        stunden_seit_empfehlung = (now_unix - empfohlen_unix) / 3600
        hebel_unveraendert = (
            abs(position.hebel_effektiv - letztes_signal.hebel_final) > _HEBEL_UNVERAENDERT_TOLERANZ
        )
        if hebel_unveraendert and stunden_seit_empfehlung >= _HEBEL_WIEDERHOLUNG_MINDEST_STUNDEN:
            vorherige_empfehlung_nicht_umgesetzt = {
                "empfohlene_aktion": letztes_signal.action,
                "empfohlener_ziel_hebel": _native(letztes_signal.hebel_final),
                "tatsaechlicher_hebel_seitdem": _native(position.hebel_effektiv),
                "stunden_seit_empfehlung": round(stunden_seit_empfehlung, 1),
                "hinweis": (
                    "Diese Empfehlung wurde offenbar noch nicht umgesetzt - nicht "
                    "wortgleich wiederholen, sondern explizit darauf eingehen (z.B. "
                    "ob die Empfehlung noch gilt, sich die Lage veraendert hat, oder "
                    "eine staerkere Massnahme angebracht waere)."
                ),
            }

    return {
        "richtung": position.richtung,
        "hebel_effektiv": _native(position.hebel_effektiv),
        "eigenkapital_eur": _native(position.eigenkapital_eur),
        "positionswert_eur": _native(position.positionswert_eur),
        "eroeffnet_am": position.eroeffnet_am,
        "tage_gehalten": round(max(0.0, (now_unix - eroeffnet_unix) / 86400), 2),
        "vorherige_hebel_empfehlung_nicht_umgesetzt": vorherige_empfehlung_nicht_umgesetzt,
    }


def build_hebel_facts(
    asset,
    latest_price,
    technical_snapshot: TechnicalSnapshot,
    confluence: ConfluenceSummary,
    regime_result: RegimeResult,
    regime_profile: dict,
    anticyclic_context: AnticyclicContext,
    market_context: dict,
    trigger: HebelTrigger,
    position_aktuell: HebelPosition | None,
    pre_result: HebelPreCheckResult,
    price_age_minutes: float | None,
    now_unix: int,
    letztes_signal=None,
    historische_erfolgsquote: dict | None = None,
    historischer_makro_vergleich: dict | None = None,
    liquiditaetszonen: dict | None = None,
    signal_stabilitaet: dict | None = None,
    btc_relativwert: dict | None = None,
    optionsmarkt: dict | None = None,
    squeeze_divergenz: str | None = None,
    funding_rate_perzentil: float | None = None,
) -> dict:
    """Analog agent/krypto/analyst.py::build_facts() - wiederverwendet dieselben
    Bausteine fuer technische_analyse/regime/markt_kontext/antizyklisch 1:1 (siehe
    docs/hebel_positionsformel.md, "noch zu klären"-Punkt geloest: KEIN separates
    Derivate-Feld, die Live-OI/Funding/LSR-Werte kommen unveraendert aus
    antizyklisch, wie bei Spot). Neu: trigger/position_aktuell/hebel_kontext.

    Nachtrag 2026-07-17: `letztes_signal` wird nur an _build_position_aktuell_
    facts() durchgereicht (siehe dort). `regime.richtungs_konflikt_mit_trigger`
    ist ein neuer, explizit berechneter Fakt (echter LINK-Fall: 5x-LONG-
    Eroeffnung WAEHREND bereits erkanntem baer-Regime, ohne dass dieser
    Widerspruch dem Modell je explizit benannt wurde) - basiert bewusst auf
    `trigger.richtung` (dem VOR der LLM-Entscheidung bekannten Kandidaten-
    Vorschlag), nicht auf der erst danach feststehenden finalen Richtung -
    der deterministische Hebel-Deckel in hebel_risk_gate.py::post_check_hebel()
    prueft unabhaengig davon nochmal gegen die tatsaechlich gewaehlte Richtung."""
    macd_val = technical_snapshot.macd
    macd_facts = None
    if macd_val.available:
        macd_facts = {
            "macd": _last(macd_val.value["macd"]),
            "signal": _last(macd_val.value["signal"]),
            "histogram": _last(macd_val.value["histogram"]),
        }

    bollinger_facts = None
    if technical_snapshot.bollinger.available:
        bv = technical_snapshot.bollinger.value
        bollinger_facts = {
            "upper": _last(bv["upper"]),
            "middle": _last(bv["middle"]),
            "lower": _last(bv["lower"]),
        }

    # ATR relativ zum aktuellen Kurs (2026-07-28, Enge-Stop-Loss-Backtest, siehe
    # project_enge_stop_loss_backtest_und_massnahmen.md) - `atr.wert` liefert bisher
    # NUR den absoluten Preiswert (USD), das Modell muss die Umrechnung in Relation
    # zum Kurs selbst vornehmen, um einzuschaetzen ob ein gewaehlter Stop-Loss-
    # Abstand im Verhaeltnis zur Volatilitaet sinnvoll ist - ein fehleranfaelliger
    # Rechenschritt. `relativ_prozent` nimmt diese Umrechnung deterministisch ab.
    atr_wert_usd = _native(latest_value(technical_snapshot.atr))
    atr_relativ_prozent = None
    if atr_wert_usd is not None and latest_price and latest_price.price_usd:
        atr_relativ_prozent = round(atr_wert_usd / latest_price.price_usd * 100, 2)

    nicht_verfuegbar = []
    for period, r in technical_snapshot.ema.items():
        if not r.available:
            nicht_verfuegbar.append(f"EMA-{period}: {r.reason}")
    for name, r in (
        ("MACD", technical_snapshot.macd),
        ("RSI-14", technical_snapshot.rsi),
        ("Bollinger Bands", technical_snapshot.bollinger),
        (technical_snapshot.swing_label, technical_snapshot.swing),
        (technical_snapshot.atr_label, technical_snapshot.atr),
    ):
        if not r.available:
            nicht_verfuegbar.append(f"{name}: {r.reason}")

    return {
        "asset": {
            "symbol": asset.symbol,
            "name": asset.name,
            "rolle": asset.rolle,
        },
        "preis": {
            "usd": _native(latest_price.price_usd) if latest_price else None,
            "eur": _native(latest_price.price_eur) if latest_price else None,
            "aktualisiert_vor_min": price_age_minutes,
        },
        "technische_analyse": {
            "ema": {str(p): _native(latest_value(r)) for p, r in technical_snapshot.ema.items()},
            "macd": macd_facts,
            "rsi_14": _native(latest_value(technical_snapshot.rsi)),
            "bollinger": bollinger_facts,
            "atr": {
                "wert": atr_wert_usd,
                "relativ_prozent": atr_relativ_prozent,
                "label": technical_snapshot.atr_label,
                "quelle": technical_snapshot.atr_source,
                "perzentil": _native(latest_value(technical_snapshot.atr_percentile)),
            },
            "support_resistance": technical_snapshot.support_resistance.value
            if technical_snapshot.support_resistance.available
            else [],
            "fibonacci": {str(k): _native(v) for k, v in (technical_snapshot.fibonacci or {}).items()},
            "confluence": {
                "bullish": confluence.bullish_count,
                "bearish": confluence.bearish_count,
                "neutral": confluence.neutral_count,
                "nicht_verfuegbar": confluence.unavailable_count,
                "gesamttendenz": confluence.overall_bias,
                "details": [
                    {"indikator": i.indicator, "bias": i.bias, "detail": i.detail}
                    for i in confluence.items
                    if i.available
                ],
            },
            "nicht_verfuegbar": nicht_verfuegbar,
        },
        "regime": {
            "wert": regime_result.regime,
            "quelle": regime_result.source,
            "begruendung": regime_result.reason,
            "btc_trend": regime_result.btc_trend_label,
            "btc_dominanz_trend": regime_result.dominance_trend_label,
            "fear_greed": {
                "wert": regime_result.fear_greed_value,
                "einstufung": regime_result.fear_greed_label,
            },
            "btc_matrix": regime_result.btc_matrix_state,
            "btc_matrix_hinweis": regime_result.btc_matrix_beschreibung,
            "liquiditaets_regime": regime_result.liquiditaets_regime,
            "zyklus_risiko": _native(regime_result.zyklus_risiko),
            # Dollar-Index-Trend (2026-07-28, Abschnitt 6 Fakten-Entscheidungsmappe) -
            # bereits vorklassifiziert. Hebel hat (anders als die 5 Spot-family-
            # Pipelines) KEIN VIX-Aequivalent im Fakten-Dict, daher eigene Regel
            # statt Anhaengsel an eine bestehende VIX-Regel (siehe SYSTEM_PROMPT Regel 24).
            "dollar_index": {
                "wert": _native(regime_result.dollar_index_wert),
                "trend": regime_result.dollar_index_trend,
            },
            "richtungs_konflikt_mit_trigger": (
                (regime_result.regime == "baer" and trigger.richtung == "LONG")
                or (regime_result.regime == "bulle" and trigger.richtung == "SHORT")
            ),
            "richtungs_konflikt_hinweis": (
                "Der Screening-Kandidat schlaegt eine Richtung vor, die dem aktuellen "
                "Regime entgegensteht (Gegen-Trend-Wette MIT Hebel - staerker verstaerktes "
                "Risiko als ohne Hebel). Wird nachtraeglich zusaetzlich deterministisch "
                "gedeckelt (siehe hebel_kontext), aber bereits hier in deiner eigenen "
                "Einschaetzung explizit gegenrechnen, nicht nur an kurzfristiger Technik "
                "festmachen."
            ),
        },
        "regime_profil": regime_profile,
        "antizyklisch": {
            # BUGFIX (2026-07-22, echter LINK-Fund): der rohe Float (typischerweise
            # eine winzige Bruchzahl wie 0.0000026) wurde bisher unformatiert an
            # das LLM gereicht - dieses hat ihn gemaess Regel 9 unveraendert in
            # den Risiken-Text kopiert, was dort als haessliche wissenschaftliche
            # Notation ("2.624963888888792e-06") beim Nutzer ankam. Jetzt als
            # lesbarer Prozentsatz MIT Zeiteinheit (die Kraken-Funding-Rate ist
            # eine ueber die letzten 24 Stunden gemittelte STUNDEN-Rate, siehe
            # hebel_screening.py::_hole_marktdaten() `rates[-24:]`) - der
            # deterministische Funding-Kosten-Risikofaktor in Abschnitt 3
            # (hebel_risk_gate.py::compute_risikofaktoren_hebel()) liefert
            # zusaetzlich den konkreten USD/Tag-Betrag bei der tatsaechlichen
            # Positionsgroesse, das muss das LLM hier nicht selbst rechnen.
            "funding_rate_aktuell_prozent_pro_stunde": (
                round(anticyclic_context.funding_rate_current * 100, 5)
                if anticyclic_context.funding_rate_current is not None else None
            ),
            # 2026-07-25, echter KAIA-Fund: die stuendliche Rate ist fuer einen
            # Menschen kaum einzuordnen ("-0,02411% pro Stunde") - Regel 9 zitiert
            # jetzt ausschliesslich diesen bereits umgerechneten Tagessatz
            # (*24, gleiche Rohrate, andere Zeiteinheit - kein eigener Datenpunkt).
            "funding_rate_aktuell_prozent_pro_tag": (
                round(anticyclic_context.funding_rate_current * 100 * 24, 4)
                if anticyclic_context.funding_rate_current is not None else None
            ),
            "funding_rate_extrem": anticyclic_context.funding_rate_extreme,
            "kursaenderung_letzte_tage_prozent": _native(anticyclic_context.recent_drop_pct),
            "moeglicher_flush": anticyclic_context.possible_flush,
            "open_interest_binance": _native(anticyclic_context.open_interest_binance),
            "open_interest_bybit": _native(anticyclic_context.open_interest_bybit),
            "open_interest_okx_usd": _native(anticyclic_context.open_interest_okx_usd),
            "long_short_ratio_binance": _native(anticyclic_context.long_short_ratio),
            "long_konten_anteil_prozent": _native(anticyclic_context.long_account_pct),
            "retail_long_bias_extrem": anticyclic_context.retail_long_bias_extreme,
            "grund": anticyclic_context.reason,
            # OI-Squeeze-Divergenz + Funding-Rate-Perzentil (2026-07-28, Abschnitt 6
            # Fakten-Entscheidungsmappe Punkt 2+3) - siehe agent/krypto/analyst.py
            # (Spot-Pendant) fuer die volle Begruendung. Eigenes Lookback-Fenster
            # (siehe hebel_pipeline.py), NICHT trigger.oi_change_pct_lookback unten
            # (4h Trendfolge-Fenster, anderer Zweck).
            "squeeze_divergenz": squeeze_divergenz,
            "funding_rate_perzentil": _native(funding_rate_perzentil),
        },
        "trigger": {
            "trigger_zweig": trigger.trigger_zweig,
            "score_gesamt": _native(trigger.score_gesamt),
            "oi_change_pct_lookback": _native(trigger.oi_change_pct_lookback),
            "kursaenderung_pct_lookback": _native(trigger.kursaenderung_pct_lookback),
        },
        "position_aktuell": _build_position_aktuell_facts(position_aktuell, now_unix, letztes_signal),
        "historische_erfolgsquote": historische_erfolgsquote,
        "historischer_makro_vergleich": historischer_makro_vergleich,
        "liquiditaetszonen": liquiditaetszonen,
        "signal_stabilitaet": signal_stabilitaet,
        "btc_relativwert": btc_relativwert,
        "optionsmarkt": optionsmarkt,
        "hebel_kontext": {
            "max_hebel_config": pre_result.config_max_hebel,
            "max_sicherer_hebel_geschaetzt": _native(pre_result.max_sicherer_hebel),
            "hinweis": (
                "max_sicherer_hebel_geschaetzt ist ein informativer Richtwert (basiert auf "
                "einer deterministischen Standard-Stop-Loss-Distanz, NICHT auf deinem "
                "spaeteren Zonen-Vorschlag) - die tatsaechliche Deckelung erfolgt nachtraeglich "
                "deterministisch, unabhaengig von diesem Wert."
            ),
        },
        "markt_kontext": {
            "praesidentschaftszyklus": {
                "jahr_im_zyklus": market_context["presidential_cycle"].year_in_cycle,
                "einordnung": market_context["presidential_cycle"].label,
            },
            "naechste_fomc_sitzungen": [
                {"name": e.name, "in_tagen": e.days_until} for e in market_context["upcoming_fomc"]
            ],
            "naechste_cpi_veroeffentlichung": (
                {
                    "datum": market_context["naechste_cpi_veroeffentlichung"].date,
                    "in_tagen": market_context["naechste_cpi_veroeffentlichung"].days_until,
                }
                if market_context.get("naechste_cpi_veroeffentlichung") else None
            ),
        },
        "disclaimers": {
            "hinweis": (
                "Makro ist NUR teilweise einbezogen (siehe regime.liquiditaets_regime). "
                "Sentiment (X/YouTube) ist in diesem System nicht implementiert."
            ),
        },
    }


REQUIRED_HEBEL_TOP_LEVEL_FIELDS = (
    "richtung", "action", "gegenargument", "confidence_pct", "short_reasoning",
    "hebel_vorschlag", "trade_thesis_typ", "top_gruende", "long_reasoning", "entry",
    "stop_loss", "take_profit", "halte_kriterium", "key_risks", "forecast",
    "eigene_einschaetzung",
)

# 2026-07-26: "antizyklisch" hier entfernt - Retail-/Long-Konten-Positionierung
# gehoert fuer Hebel-Signale ausschliesslich in Abschnitt 3 (Risikofaktoren,
# compute_risikofaktoren_hebel()), nie in top_gruende, siehe Regel 8 oben und
# hebel_risk_gate.py::filtere_retail_konsens_top_gruende().
TOP_GRUENDE_KATEGORIEN = ("technisch", "fundamental", "makro", "risiko")
_HALTE_KRITERIUM_BUCKETS = ("kurz", "mittel", "lang")
_HALTEN_AEHNLICHE_ACTIONS = ("HALTEN", "SCHLIESSEN")
# Signal-Fazit (2026-07-25, siehe Regel 24 / Memory feedback_llm_synthese_
# kein_deterministischer_override.md) - bewusst KEIN deterministischer
# Override des Werturteils, nur Format-/Vollstaendigkeits-Validierung hier.
_EIGENE_EINSCHAETZUNG_FOLGEN_WERTE = ("ja", "nein", "mit_vorbehalt")


# 2026-07-14: identischer Halluzinations-Check wie agent/krypto/analyst.py::
# _pruefe_kreuzkontamination() - "Boden-Zielzone" (cash_reserve_ziel) ist ein
# BTC/ETH-only-Feature, das dem Modell fuer Hebel-Signale ueberhaupt nicht im
# Facts-JSON mitgeschickt wird (siehe build_hebel_facts()), jede Erwaehnung
# bei einem anderen Symbol ist also erfunden. Gleicher Fund uebertragen,
# nicht dupliziert-und-vergessen: das Modell (Gemini) ist dasselbe fuer
# beide Pipelines, das Risiko besteht identisch.
_BODEN_ZIELZONE_BEGRIFFE = ("boden-zielzone", "bodenzielzone")


def _pruefe_kreuzkontamination(data: dict, asset_symbol: str) -> None:
    if asset_symbol in ("BTC", "ETH"):
        return
    freitexte: list[str] = [str(data.get("short_reasoning") or "")]
    long_reasoning = data.get("long_reasoning")
    if isinstance(long_reasoning, dict):
        freitexte.extend(str(v) for v in long_reasoning.values())
    key_risks = data.get("key_risks")
    if isinstance(key_risks, list):
        freitexte.extend(str(r) for r in key_risks)
    top_gruende = data.get("top_gruende")
    if isinstance(top_gruende, list):
        freitexte.extend(str(e.get("text") or "") for e in top_gruende if isinstance(e, dict))
    halte_kriterium = data.get("halte_kriterium")
    if isinstance(halte_kriterium, dict):
        freitexte.append(str(halte_kriterium.get("bedingung_text") or ""))
        freitexte.append(str(halte_kriterium.get("reasoning") or ""))

    gesamt_text = " ".join(freitexte).lower()
    for begriff in _BODEN_ZIELZONE_BEGRIFFE:
        if begriff in gesamt_text:
            raise AnalystResponseInvalid(
                f"Antwort erwaehnt '{begriff}' fuer {asset_symbol} - dieses Feature existiert nur fuer "
                "BTC/ETH und wurde im Facts-JSON nicht mitgeschickt (Kreuzkontamination/Halluzination)"
            )


def _validate_hebel(data: dict, asset_symbol: str) -> dict:
    """Analog agent/krypto/analyst.py::_validate() - angepasst auf das 7-Aktionen-
    Vokabular, `richtung`, `hebel_vorschlag`, `trade_thesis_typ`. KEIN `position_size`/
    `tranchen` (existiert im Hebel-Schema nicht, siehe docs/hebel_positionsformel.md)."""
    if not isinstance(data, dict):
        raise AnalystResponseInvalid("Antwort ist kein JSON-Objekt")

    missing = [f for f in REQUIRED_HEBEL_TOP_LEVEL_FIELDS if f not in data]
    if missing:
        raise AnalystResponseInvalid(f"Pflichtfelder fehlen: {missing}")

    richtung = str(data["richtung"]).strip().upper()
    if richtung not in ("LONG", "SHORT"):
        raise AnalystResponseInvalid(f"Ungültige richtung: {data['richtung']!r}")
    data["richtung"] = richtung

    action = str(data["action"]).strip().upper()
    if action not in REQUIRED_HEBEL_ACTIONS:
        raise AnalystResponseInvalid(f"Ungültige action: {data['action']!r}")
    data["action"] = action

    gegenargument = str(data.get("gegenargument", "")).strip()
    if len(gegenargument) < 15:
        raise AnalystResponseInvalid(f"gegenargument fehlt oder zu kurz: {data.get('gegenargument')!r}")
    data["gegenargument"] = gegenargument

    # Signal-Fazit (2026-07-25, Regel 24) - reine Format-/Vollstaendigkeits-
    # pruefung, bewusst KEINE inhaltliche Korrektur von `folgen`/`kurzfazit`
    # (siehe Memory feedback_llm_synthese_kein_deterministischer_override.md).
    eigene_einschaetzung = data.get("eigene_einschaetzung")
    if not isinstance(eigene_einschaetzung, dict):
        raise AnalystResponseInvalid(f"eigene_einschaetzung ist kein Objekt: {eigene_einschaetzung!r}")
    folgen = str(eigene_einschaetzung.get("folgen", "")).strip().lower()
    if folgen not in _EIGENE_EINSCHAETZUNG_FOLGEN_WERTE:
        raise AnalystResponseInvalid(f"eigene_einschaetzung.folgen ungültig: {eigene_einschaetzung.get('folgen')!r}")
    kurzfazit = str(eigene_einschaetzung.get("kurzfazit", "")).strip()
    if len(kurzfazit) < 15:
        raise AnalystResponseInvalid(
            f"eigene_einschaetzung.kurzfazit fehlt oder zu kurz: {eigene_einschaetzung.get('kurzfazit')!r}"
        )
    data["eigene_einschaetzung"] = {"folgen": folgen, "kurzfazit": kurzfazit}

    try:
        data["confidence_pct"] = float(data["confidence_pct"])
    except (TypeError, ValueError):
        raise AnalystResponseInvalid(f"confidence_pct nicht numerisch: {data['confidence_pct']!r}")
    if not (0 <= data["confidence_pct"] <= 100):
        raise AnalystResponseInvalid(f"confidence_pct außerhalb 0-100: {data['confidence_pct']}")

    hebel_vorschlag = data.get("hebel_vorschlag")
    if hebel_vorschlag is not None:
        try:
            data["hebel_vorschlag"] = float(hebel_vorschlag)
        except (TypeError, ValueError):
            raise AnalystResponseInvalid(f"hebel_vorschlag nicht numerisch: {hebel_vorschlag!r}")
    elif action not in _HALTEN_AEHNLICHE_ACTIONS:
        raise AnalystResponseInvalid(f"hebel_vorschlag fehlt bei action={action!r}")

    trade_thesis_typ = str(data["trade_thesis_typ"]).strip().lower()
    if trade_thesis_typ not in _TRADE_THESIS_TYPEN:
        raise AnalystResponseInvalid(f"Ungültiger trade_thesis_typ: {data['trade_thesis_typ']!r}")
    data["trade_thesis_typ"] = trade_thesis_typ

    for field_name in ("long_reasoning", "entry", "stop_loss", "take_profit", "halte_kriterium", "forecast"):
        if not isinstance(data[field_name], dict):
            raise AnalystResponseInvalid(f"{field_name} ist kein Objekt")

    if not isinstance(data["key_risks"], list):
        raise AnalystResponseInvalid("key_risks ist keine Liste")
    if action in _HEBEL_ACTIONS_MIT_HEBEL and not data["key_risks"]:
        raise AnalystResponseInvalid(f"key_risks darf bei action={action!r} nicht leer sein")

    top_gruende = data["top_gruende"]
    if not isinstance(top_gruende, list) or len(top_gruende) != 5:
        raise AnalystResponseInvalid(f"top_gruende muss genau 5 Einträge enthalten: {top_gruende!r}")
    ranks_seen = set()
    for eintrag in top_gruende:
        if not isinstance(eintrag, dict):
            raise AnalystResponseInvalid(f"top_gruende-Eintrag ist kein Objekt: {eintrag!r}")
        rang = eintrag.get("rang")
        if rang not in (1, 2, 3, 4, 5) or rang in ranks_seen:
            raise AnalystResponseInvalid(f"top_gruende.rang ungültig oder doppelt: {rang!r}")
        ranks_seen.add(rang)
        kategorie = str(eintrag.get("kategorie", "")).strip().lower()
        if kategorie not in TOP_GRUENDE_KATEGORIEN:
            raise AnalystResponseInvalid(f"top_gruende.kategorie ungültig: {eintrag.get('kategorie')!r}")
        eintrag["kategorie"] = kategorie
        if not str(eintrag.get("text") or "").strip():
            raise AnalystResponseInvalid("top_gruende.text fehlt/leer")

    for field_name in ("entry", "stop_loss", "take_profit"):
        obj = data[field_name]
        for currency in ("usd", "eur"):
            von, bis = obj.get(f"{currency}_von"), obj.get(f"{currency}_bis")
            if von is None and bis is None:
                continue
            if von is None or bis is None:
                raise AnalystResponseInvalid(f"{field_name}.{currency}_von/{currency}_bis: nur einer gesetzt")
            try:
                von, bis = float(von), float(bis)
            except (TypeError, ValueError):
                raise AnalystResponseInvalid(f"{field_name}.{currency}_von/{currency}_bis nicht numerisch")
            if von > bis:
                raise AnalystResponseInvalid(f"{field_name}.{currency}_von > {currency}_bis ({von} > {bis})")
            obj[f"{currency}_von"], obj[f"{currency}_bis"] = von, bis

    if action in _HEBEL_ACTIONS_MIT_HEBEL:
        stop = data["stop_loss"]
        if stop.get("usd_von") is None:
            raise AnalystResponseInvalid(f"stop_loss fehlt bei action={action!r} (Stop-Loss-Pflicht)")

    halte = data["halte_kriterium"]
    bucket = str(halte.get("bucket", "")).strip().lower()
    if bucket not in _HALTE_KRITERIUM_BUCKETS:
        raise AnalystResponseInvalid(f"halte_kriterium.bucket ungültig: {halte.get('bucket')!r}")
    halte["bucket"] = bucket
    if (
        halte.get("ziel_preis_usd") is None
        and not str(halte.get("ziel_datum") or "").strip()
        and not str(halte.get("bedingung_text") or "").strip()
    ):
        raise AnalystResponseInvalid(
            "halte_kriterium: mindestens eines von ziel_preis_usd/ziel_datum/bedingung_text muss gesetzt sein"
        )

    _pruefe_kreuzkontamination(data, asset_symbol)

    return data


def call_llm_for_hebel_signal(llm_client, facts: dict, max_retries: int = 2) -> dict:
    """Ruft das uebergebene LLM (Groq- ODER Cerebras-Client, identisches `.chat()`-
    Interface) auf, validiert die Antwort. Bei kaputtem/unvollstaendigem JSON wird
    einmal mit Korrektur-Hinweis retryed, danach fail-loud (AnalystResponseInvalid) -
    der Aufrufer (agent/krypto/hebel_pipeline.py) faengt das ab und erzeugt ein
    HALTEN-Signal, analog call_groq_for_signal()."""
    asset_symbol = facts["asset"]["symbol"]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
    ]

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        raw = llm_client.chat(
            messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        try:
            parsed = json.loads(raw)
            validated = _validate_hebel(parsed, asset_symbol)
            validated["_raw_response"] = raw
            return validated
        except (json.JSONDecodeError, AnalystResponseInvalid) as exc:
            last_error = exc
            logger.info("Hebel-LLM-Antwort ungültig (Versuch %d): %s", attempt + 1, exc)
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Deine letzte Antwort war ungültig: {exc}. Antworte erneut, "
                        "ausschließlich mit einem korrekten JSON-Objekt gemäß Schema."
                    ),
                }
            )

    raise AnalystResponseInvalid(f"Nach {max_retries + 1} Versuchen weiterhin ungültig: {last_error}")
