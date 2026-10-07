import re

with open("web_ui.py", "r", encoding="utf-8") as f:
    text = f.read()

# Find all occurrences of border-left
for m in re.finditer(r'border-left:\s*[^;"\']+', text):
    start = max(0, m.start() - 60)
    end = min(len(text), m.end() + 60)
    line_no = text[:m.start()].count("\n") + 1
    print(f"Line {line_no}: {text[start:end].strip()}")
