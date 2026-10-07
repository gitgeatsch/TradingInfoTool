"""Echtes Beispiel der E-Mail 'Altcoins - Fortbestand und Gelegenheit' als HTML im Stil der REGEL0-Mail (agent/regel0_mail._als_html).

    python Basisinfos/Spot_Voranalyse_04_10/mail_beispiel_html.py   -> mail_beispiel_altcoins.html (wird NICHT versendet)

Quelle des Inhalts: mail_entwurf_beide_ebenen.md (mail_entwurf.py, gegengeprueft mail_gegenprobe.py 19/19). Hier nur die Darstellung:
Betreff, Abschnitte mit farbigen Ueberschriften, Listen und Tabellen, max. 680 px breit - bricht am Handy um.
"""
import os
import re
from html import escape as e

HIER = os.path.dirname(os.path.abspath(__file__))
QUELLE = os.path.join(HIER, "mail_entwurf_beide_ebenen.md")
ZIEL = os.path.join(HIER, "mail_beispiel_altcoins.html")
SANS = "font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
FARBE = {"Phase": "#7f8c8d", "Dein Bestand": "#1e8449", "Rangliste": "#1f4e79", "Protokoll": "#7f8c8d", "Anhang": "#7f8c8d"}


def inline(t):
    t = e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i style='color:#555'>\1</i>", t)
    return t


def h(text):
    farbe = next((v for k, v in FARBE.items() if text.startswith(k)), "#1f4e79")
    return "<div style='%sfont-weight:bold;font-size:15px;color:%s;margin:18px 0 6px;border-bottom:2px solid %s'>%s</div>" % (SANS, farbe, farbe, e(text))


def main():
    zeilen = open(QUELLE, encoding="utf-8").read().splitlines()
    titel = zeilen[0].lstrip("# ").replace("ENTWURF · ", "")
    betreff = "Altcoins September · Fortbestand und Gelegenheit · Watchlist 26 Coins, Bestand 11"
    teile = ["<div style='max-width:680px;%s color:#1a1a1a'>" % SANS,
             "<div style='background:#fff3cd;border:1px solid #e0c36b;padding:6px 10px;font-size:12px;margin-bottom:10px'>"
             "<b>BEISPIEL aus echten Daten · nicht versendet.</b> Stichtag 01.09.2026, Kurse bis 20.09.2026, Bestand aus der Desktop-Kopie vom 19.07.2026.</div>",
             "<div style='font-size:12px;color:#555'>Betreff: <b>%s</b></div>" % e(betreff),
             "<div style='font-weight:bold;font-size:17px;margin:6px 0 4px'>%s</div>" % e(titel)]
    in_liste = in_tab = False
    for z in zeilen[1:]:
        if z.startswith("|"):
            zellen = [c.strip() for c in z.strip("|").split("|")]
            if set("".join(zellen)) <= set("-: "):
                continue
            if not in_tab:
                teile.append("<table style='border-collapse:collapse;width:100%%;font-size:12px;%s'>" % SANS); in_tab = True
                teile.append("<tr>%s</tr>" % "".join("<th style='text-align:left;padding:3px 6px;border-bottom:1px solid #ccc'>%s</th>" % inline(c) for c in zellen))
            else:
                teile.append("<tr>%s</tr>" % "".join("<td style='padding:3px 6px;vertical-align:top;border-bottom:1px solid #eee'>%s</td>" % inline(c) for c in zellen))
            continue
        if in_tab:
            teile.append("</table>"); in_tab = False
        if z.startswith("- "):
            if not in_liste:
                teile.append("<ul style='padding-left:18px;margin:4px 0'>"); in_liste = True
            teile.append("<li style='margin:0 0 8px;line-height:1.4'>%s</li>" % inline(z[2:]))
            continue
        if in_liste:
            teile.append("</ul>"); in_liste = False
        if z.startswith("## "):
            teile.append(h(z[3:]))
        elif z.startswith("### "):
            teile.append("<div style='font-weight:bold;font-size:14px;margin:12px 0 4px'>%s</div>" % inline(z[4:]))
        elif z.strip():
            teile.append("<p style='margin:6px 0;line-height:1.4'>%s</p>" % inline(z))
    if in_liste:
        teile.append("</ul>")
    if in_tab:
        teile.append("</table>")
    teile.append("<div style='margin-top:14px;color:#555;font-size:12px'>TradingInfoTool · Spot-Strang · Auskunft, kein Kaufsignal. "
                 "Herleitung: Voranalyse_Spot_Neubau_04_10.md §19–§26.</div></div>")
    html = "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>" \
           "<title>%s</title></head><body style='background:#fff;margin:12px'>%s</body></html>" % (e(betreff), "".join(teile))
    open(ZIEL, "w", encoding="utf-8").write(html)
    print("geschrieben: %s (%d Zeichen) · Betreff: %s" % (ZIEL, len(html), betreff))


if __name__ == "__main__":
    main()
