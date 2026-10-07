import re

with open("web_ui.py", "r", encoding="utf-8") as f:
    text = f.read()

patterns = [
    r'style="[^"]*#111827[^"]*"',
    r'style="[^"]*#15803d[^"]*"',
    r'style="[^"]*#b91c1c[^"]*"',
    r'style="[^"]*border-left[^"]*"',
    r'style="[^"]*border:\s*2px[^"]*"',
    r'style="[^"]*border:\s*3px[^"]*"',
]

for pat in patterns:
    found = re.findall(pat, text)
    print(f"Pattern {pat}: {len(found)} matches")
    for item in list(set(found))[:5]:
        print("   ", item)
