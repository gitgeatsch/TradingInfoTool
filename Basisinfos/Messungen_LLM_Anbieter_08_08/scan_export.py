"""Nur LESEN: Top-Level-Schluessel des Notebook-Exports + kommt facts_json vor?"""
P = r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/notebook_diagnose.json"

keys = []
depth = 0
instr = False
esc = False
cur = None
treffer = 0
BACKSLASH = chr(92)

with open(P, encoding="utf-8") as f:
    while True:
        chunk = f.read(1 << 22)
        if not chunk:
            break
        treffer += chunk.count('"facts_json"')
        for ch in chunk:
            if instr:
                if esc:
                    esc = False
                elif ch == BACKSLASH:
                    esc = True
                elif ch == '"':
                    instr = False
                    if depth == 1 and isinstance(cur, list):
                        cur = "".join(cur)
                elif depth == 1 and isinstance(cur, list):
                    cur.append(ch)
                continue
            if ch == '"':
                instr = True
                if depth == 1:
                    cur = []
                continue
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
            elif ch == ":" and depth == 1 and isinstance(cur, str):
                keys.append(cur)
                cur = None

print(f'"facts_json" kommt {treffer}x vor')
print(f"{len(keys)} Top-Level-Schluessel:")
for k in keys:
    print("  ", k)
