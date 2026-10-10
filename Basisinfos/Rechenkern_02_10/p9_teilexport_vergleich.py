"""P9 (10.10.2026): Ausgabe des Teilexports auf einem PRUEFVERZEICHNIS festhalten - vorher/nachher zeilengleich nachweisen.

    python Basisinfos/Rechenkern_02_10/p9_teilexport_vergleich.py <Pruefverzeichnis> <Ausgabedatei>

Ruft ``nb_teilexport_betriebsdaten._inhalt()`` mit ``DATEN = <Pruefverzeichnis>`` (Kopien, nie die Produktion), ohne Ablage im
Austauschordner und ohne REGEL0-Kopie. Zeitstempel der Kopfzeile und freier Speicher werden neutralisiert (sie aendern sich je Lauf).
"""
import contextlib
import io
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import nb_teilexport_betriebsdaten as T  # noqa: E402

T.DATEN = sys.argv[1]
puffer = io.StringIO()
with contextlib.redirect_stdout(puffer):
    rc = T._inhalt()
text = puffer.getvalue()
text = re.sub(r"\(Schritt 4, nur lesen\) - \d{4}-\d{2}-\d{2} \d{2}:\d{2}", "(Schritt 4, nur lesen) - <ZEIT>", text)
text = re.sub(r"freier Speicher am Projektlaufwerk: [\d.]+ GB", "freier Speicher am Projektlaufwerk: <GB>", text)
text = re.sub(r"geaendert \d{4}-\d{2}-\d{2} \d{2}:\d{2}", "geaendert <ZEIT>", text)
text = text.replace(sys.argv[1].replace("/", "\\"), "<DATEN>").replace(sys.argv[1], "<DATEN>")
io.open(sys.argv[2], "w", encoding="utf-8").write(text)
print("rc %s · %d Zeilen -> %s" % (rc, text.count("\n"), sys.argv[2]))
