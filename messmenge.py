# -*- coding: utf-8 -*-
"""DIE MESSMENGE KRYPTO — eingefroren und versioniert (09.09.2026)

## ⚠️⚠️ Warum es diese Datei gibt

Bis heute war die Messmenge das, was `messe_eigenschaft_beitrag.lade()`
gerade aus der Datenbank holte. **Damit verschiebt sich die Basis unter
den Befunden**, und R-R11 ("ein Befund darf nur von einer Messung
umgestossen werden, die ihn zuerst reproduziert") ist nicht
durchsetzbar - man kann nicht reproduzieren, was sich bewegt.

Am 09.09.2026 dreimal erlebt. Das deutlichste Beispiel:

    `oi_aenderung` registriert 02.09.   +0,0145 R   117 Symbole
    dasselbe gemessen      09.09.       +0,0126 R   122 Symbole

Der Unterschied war NICHT der Kandidat, sondern die gewachsene Basis.

## Der Zuschnitt (Nutzerentscheidung 09.09.2026)

    Inhalt      alle Symbole, die den Historienfilter bestehen
                (mehr als RUECKBLICK + 60 Tage), EINSCHLIESSLICH der
                eingestellten Reihen
    Auswahl     KEINE nach Groesse, Liquiditaet oder Leistung
    Aenderung   nur mit NEUER Versionsnummer, nie stillschweigend

⚠️⚠️ **Die eingestellten Reihen sind kein Ballast, sie sind der Schutz.**
Wer nur die nimmt, die heute noch laufen, misst Survivorship. In dieser
Version sind 174 von 536 Reihen eingestellt.

⚠️ **Nicht nach Marktkapitalisierung filtern.** Das waere Survivorship
durch die Hintertuer: gross ist, was gross GEWORDEN ist.

## Die Abdeckung je Zusatzquelle — dokumentiert statt implizit

    Kursreihen      536 von 536
    Funding         300
    Terminmarkt     122
    Turnover        66   ⚠️ der Engpass, und er haengt an der QUELLE
                         (Coin Metrics liefert nur diese) - kein
                         Zuschnitt aendert daran etwas

## Wie sie benutzt wird

    import messmenge
    reihen = {s: v for s, v in B.lade().items() if s in messmenge.V1}

⚠️ Wer eine ANDERE Menge misst, schreibt das in den Befund. Eine Messung
ohne genannte Version ist nicht reproduzierbar.
"""
from __future__ import annotations

VERSION = "v1"
GESETZT_AM = "2026-09-09"
KRITERIUM = ("alle Krypto-Symbole der Messbasis mit mehr als "
             "RUECKBLICK + 60 Tagen Historie, einschliesslich der "
             "eingestellten Reihen - keine Auswahl nach Groesse, "
             "Liquiditaet oder Leistung")

# ⚠️ Abdeckung je Zusatzquelle, festgehalten am Tag des Einfrierens.
ABDECKUNG = {"kursreihen": 536, "funding": 300, "terminmarkt": 122,
             "turnover": 66, "eingestellt": 174}


def zeile() -> str:
    """Die Messmenge IN KLARTEXT - fuer jeden Messkopf und Befund."""
    return ("Messmenge Krypto %s (gesetzt %s): %d Symbole, davon %d "
            "eingestellt · Funding %d · Terminmarkt %d · Turnover %d"
            % (VERSION, GESETZT_AM, len(V1), ABDECKUNG["eingestellt"],
                ABDECKUNG["funding"], ABDECKUNG["terminmarkt"],
                ABDECKUNG["turnover"]))


V1 = frozenset((
    "1000CAT", "1000CHEEMS", "1000SATS", "1INCH", "1MBABYDOGE", "A",
    "AAVE", "ACA", "ACE", "ACH", "ACM", "ACT",
    "ACX", "ADA", "ADX", "AERGO", "AEUR", "AEVO",
    "AGIX", "AGLD", "AI", "AION", "AIOZ", "AIXBT",
    "AKRO", "AKT", "ALCX", "ALGO", "ALICE", "ALPACA",
    "ALPHA", "ALPINE", "ALT", "AMB", "AMP", "ANIME",
    "ANKR", "ANT", "APE", "API3", "APT", "AR",
    "ARB", "ARDR", "ARK", "ARKM", "ARPA", "ASR",
    "AST", "ASTR", "ATA", "ATM", "ATOM", "AUCTION",
    "AUD", "AUDIO", "AUTO", "AVA", "AVAX", "AWE",
    "AXL", "AXS", "BABY", "BADGER", "BAKE", "BAL",
    "BANANA", "BANANAS31", "BAND", "BAR", "BAT", "BB",
    "BCH", "BEAM", "BEAMX", "BEL", "BERA", "BETA",
    "BICO", "BIFI", "BIGTIME", "BIO", "BLUR", "BLZ",
    "BMT", "BNB", "BNSOL", "BNT", "BNX", "BOME",
    "BOND", "BONK", "BRETT", "BROCCOLI714", "BSW", "BTC",
    "BTCST", "BTG", "BTS", "BTT", "BTTC", "BURGER",
    "BUSD", "BZRX", "C", "C98", "CAKE", "CAT",
    "CATI", "CELO", "CELR", "CETUS", "CFX", "CGPT",
    "CHESS", "CHR", "CHZ", "CITY", "CKB", "CLV",
    "COCOS", "COMBO", "COMP", "COOKIE", "COS", "COTI",
    "COW", "CREAM", "CRV", "CTK", "CTSI", "CTXC",
    "CVC", "CVP", "CVX", "CYBER", "D", "DAR",
    "DASH", "DATA", "DCR", "DEGO", "DENT", "DEXE",
    "DF", "DGB", "DIA", "DNT", "DOCK", "DODO",
    "DOGE", "DOGS", "DOT", "DREP", "DUSK", "DYDX",
    "DYM", "EDU", "EGLD", "EIGEN", "ELF", "ENA",
    "ENJ", "ENS", "EOS", "EPIC", "EPS", "EPX",
    "ERA", "ERD", "ERN", "ETC", "ETH", "ETHFI",
    "EUR", "EURI", "FARM", "FDUSD", "FET", "FIDA",
    "FIL", "FIO", "FIRO", "FIS", "FLM", "FLOKI",
    "FLOW", "FLUX", "FOR", "FORM", "FORTH", "FRONT",
    "FTM", "FTT", "FUN", "FXS", "G", "GAL",
    "GALA", "GAS", "GBP", "GFT", "GHST", "GLM",
    "GLMR", "GMT", "GMX", "GNO", "GNS", "GPS",
    "GRIFFAIN", "GRT", "GTC", "GTO", "GUN", "GXS",
    "HAEDAL", "HARD", "HBAR", "HC", "HEI", "HFT",
    "HIFI", "HIGH", "HIVE", "HMSTR", "HNT", "HOME",
    "HOOK", "HOT", "HUMA", "HYPE", "HYPER", "ICP",
    "ICX", "ID", "IDEX", "ILV", "IMX", "INIT",
    "INJ", "IO", "IOST", "IOTA", "IOTX", "IQ",
    "IRIS", "JASMY", "JOE", "JST", "JTO", "JUP",
    "JUV", "KAIA", "KAITO", "KAS", "KAVA", "KDA",
    "KERNEL", "KEY", "KLAY", "KMD", "KMNO", "KNC",
    "KP3R", "KSM", "LA", "LAYER", "LAZIO", "LDO",
    "LEVER", "LINA", "LINK", "LISTA", "LIT", "LOKA",
    "LOOM", "LPT", "LQTY", "LRC", "LSK", "LTC",
    "LTO", "LUMIA", "LUNA", "LUNC", "MAGIC", "MANA",
    "MANTA", "MASK", "MATIC", "MAV", "MBL", "MBOX",
    "MC", "MDT", "MDX", "ME", "MEME", "METIS",
    "MFT", "MINA", "MIR", "MITH", "MKR", "MLN",
    "MOB", "MORPHO", "MOVE", "MOVR", "MTL", "MUBARAK",
    "MULTI", "NANO", "NBS", "NEAR", "NEIRO", "NEO",
    "NEWT", "NEXO", "NFP", "NIL", "NKN", "NMR",
    "NOT", "NPXS", "NTRN", "NULS", "NXPC", "OAX",
    "OCEAN", "OG", "OGN", "OM", "OMG", "OMNI",
    "ONDO", "ONE", "ONG", "ONT", "OOKI", "OP",
    "ORCA", "ORDI", "ORN", "OSMO", "OXT", "PARTI",
    "PAX", "PAXG", "PDA", "PENDLE", "PENGU", "PEOPLE",
    "PEPE", "PERL", "PERP", "PHA", "PHB", "PIVX",
    "PIXEL", "PLA", "PLUME", "PNT", "PNUT", "POL",
    "POLS", "POLYX", "POND", "PORTAL", "PORTO", "POWR",
    "PROM", "PROS", "PROVE", "PSG", "PUNDIX", "PYR",
    "PYTH", "QI", "QKC", "QNT", "QTUM", "QUICK",
    "RAD", "RAMP", "RARE", "RAY", "RDNT", "RED",
    "REEF", "REI", "REN", "RENDER", "REP", "REQ",
    "RESOLV", "REZ", "RIF", "RLC", "RNDR", "RONIN",
    "ROSE", "RPL", "RSR", "RUNE", "RVN", "S",
    "SAGA", "SAHARA", "SAND", "SANTOS", "SC", "SCR",
    "SCRT", "SEI", "SFP", "SHELL", "SHIB", "SIGN",
    "SKL", "SLP", "SNT", "SNX", "SOL", "SOLV",
    "SOPH", "SPELL", "SPK", "SRM", "SSV", "STEEM",
    "STG", "STMX", "STO", "STORJ", "STPT", "STRAX",
    "STRK", "STX", "SUI", "SUN", "SUPER", "SUPRA",
    "SUSD", "SUSHI", "SXP", "SXT", "SYN", "SYRUP",
    "SYS", "T", "TAO", "TCT", "TFUEL", "THE",
    "THETA", "TIA", "TKO", "TLM", "TNSR", "TOMO",
    "TON", "TORN", "TOWNS", "TRB", "TREE", "TRIBE",
    "TROY", "TRU", "TRUMP", "TRX", "TST", "TURBO",
    "TUSD", "TUT", "TVK", "TWT", "UFT", "UMA",
    "UNFI", "UNI", "USD1", "USDC", "USDP", "USDSOLD",
    "USTC", "USUAL", "UTK", "VANA", "VANRY", "VELODROME",
    "VET", "VGX", "VIB", "VIC", "VIDT", "VIRTUAL",
    "VITE", "VOXEL", "VTHO", "W", "WAN", "WAVES",
    "WAXP", "WBETH", "WBTC", "WCT", "WIF", "WIN",
    "WING", "WLD", "WNXM", "WOO", "WRX", "WTC",
    "XAI", "XEC", "XEM", "XLM", "XMR", "XNO",
    "XRP", "XTZ", "XUSD", "XVG", "XVS", "YFI",
    "YFII", "YGG", "ZEC", "ZEN", "ZIL", "ZK",
    "ZRO", "ZRX",
))
