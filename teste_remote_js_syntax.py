"""Ist das ausgelieferte JavaScript der Remote-Seite syntaktisch heil?

DIE FEHLERKLASSE, ZWEIMAL ZUGESCHLAGEN. `_INDEX_HTML` in remote/server.py ist
ein NICHT-ROHER `\"\"\"`-String. Wer darin ein JS-Stringliteral mit doppelten
Anfuehrungszeichen begrenzt und HTML-Attribute (`class=\"...\"`) hineinschreibt,
muss sie fuer Python escapen - und **genau dieses Escape loest Python beim
Parsen wieder auf**. Im Quelltext sieht alles richtig aus, im ausgelieferten
JavaScript endet die Zeichenkette mitten im Attribut.

    Quelltext:      "... <span class=\\"muted-text\\">nicht messbar ..."
    ausgeliefert:   "... <span class="muted-text">nicht messbar ..."
                                        ^ String endet hier, Rest ist Unsinn

  2026-08-04  erstmals aufgetreten, gefunden und behoben.
  2026-08-08  ERNEUT aufgetreten, Zeile 676 Spalte 38 der ausgelieferten Seite:
              `Uncaught SyntaxError: unexpected token: identifier`. Ein
              Syntaxfehler bricht das GESAMTE Skript ab - die Seite rendert,
              aber KEINE einzige Zahl wird gesetzt. Genau das Symptom, das der
              Nutzer gemeldet hat.

WARUM EIN TEST UND NICHT NUR DER FIX: die Lehre von 2026-08-04 lautete bereits
"bei eingebettetem JS immer den GEPARSTEN String pruefen, nicht den Quelltext" -
und trotzdem ist es wieder passiert. Eine Lehre, die man sich merken muss, ist
schwaecher als eine, die eine Maschine prueft.

Der Scanner laeuft ueber die GEPARSTE Zeichenkette und meldet jedes
Stringliteral, auf dessen schliessendes Anfuehrungszeichen unmittelbar ein
Bezeichner folgt - exakt das, was der Browser als "unexpected token" meldet.

KEIN Netzwerk, kein Server-Start.
"""
import re
import sys

from remote.server import _INDEX_HTML

fehler = []


def pruefe(bedingung, text, info=""):
    if bedingung:
        print(f"  OK   {text}  {info}")
    else:
        print(f"  FEHL {text}  {info}")
        fehler.append(text)


def abgebrochenes_literal(zeile: str) -> int | None:
    """Spalte, an der ein Stringliteral endet und direkt ein Bezeichner folgt.

    Bewusst ein Zustandsscanner statt eines regulaeren Ausdrucks: ein Muster
    kann nicht unterscheiden, ob ein `"` ein String OEFFNET oder innerhalb
    eines mit `'` begrenzten Strings steht - und genau daran ist mein erster
    Suchversuch gescheitert (54 Falschmeldungen)."""
    i, delim = 0, None
    while i < len(zeile):
        c = zeile[i]
        if delim is None:
            if c in "\"'":
                delim = c
        elif c == "\\":
            i += 2
            continue
        elif c == delim:
            delim = None
            folgt = zeile[i + 1:i + 2]
            if folgt.isalpha() or folgt == "_":
                return i + 1
        i += 1
    return None


zeilen = _INDEX_HTML.split("\n")
start = next(i for i, z in enumerate(zeilen) if "<script" in z)
ende = next(i for i, z in enumerate(zeilen) if "</script" in z)

print(f"A) SKRIPTBLOCK  (Zeilen {start + 1} bis {ende + 1})")
pruefe(ende - start > 100, "A1 Skriptblock gefunden und nicht leer",
       f"{ende - start} Zeilen")

print("\nB) KEIN ABGEBROCHENES STRINGLITERAL")
treffer = []
for n in range(start + 1, ende):
    spalte = abgebrochenes_literal(zeilen[n])
    if spalte is not None:
        treffer.append((n + 1, spalte, zeilen[n].strip()))
pruefe(not treffer, "B1 jedes Stringliteral schliesst sauber",
       "sonst bricht das GANZE Skript ab, nicht nur die eine Zeile")
for n, spalte, z in treffer:
    print(f"        Zeile {n}, Spalte {spalte}: {z[:100]}")

print("\nC) KLAMMERN AUSGEGLICHEN")
js = "\n".join(zeilen[start + 1:ende])
for auf, zu, name in (("{", "}", "geschweift"), ("(", ")", "rund"), ("[", "]", "eckig")):
    pruefe(js.count(auf) == js.count(zu), f"C {name}",
           f"{js.count(auf)}/{js.count(zu)}")

print("\nD) DIE STELLE, AN DER ES ZWEIMAL BRACH")
# Ein escapetes Anfuehrungszeichen hat im ausgelieferten JS nichts zu suchen,
# wenn es aus einem `\"` im Python-Quelltext stammt - dort steht dann ein
# nacktes `"`. Gegenprobe am QUELLTEXT, nicht am geparsten String.
import pathlib

quelltext = pathlib.Path("remote/server.py").read_text(encoding="utf-8")
i_start = quelltext.index('_INDEX_HTML = """')
i_ende = quelltext.index('"""', i_start + 20)
roh = quelltext[i_start:i_ende]
escapes = [z.strip() for z in roh.split("\n") if '\\"' in z]
pruefe(not escapes, "D1 kein escapetes Anfuehrungszeichen im HTML-String",
       "Python loest \\\" beim Parsen auf - im JS steht dann ein nacktes \"")
for z in escapes[:5]:
    print(f"        {z[:100]}")

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"{len(fehler)} FEHLER: {fehler}"))
sys.exit(1 if fehler else 0)
