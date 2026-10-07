import re
import sys
import os

with open('web_ui.py', 'r', encoding='utf-8') as f:
    web_content = f.read()

sys.path.insert(0, 'scratch')
from apply_apple_ui import apple_css

# Extract all class names in web_ui.py
classes_in_html = set()
for m in re.finditer(r'class="([^"]+)"', web_content):
    for cls in m.group(1).split():
        classes_in_html.add(cls)

# Extract all classes defined in old css
old_style = web_content[web_content.find('<style>'):web_content.find('</style>')]
old_css_classes = set(re.findall(r'\.([a-zA-Z0-9_\-]+)', old_style))

# Extract all classes in new apple css
new_css_classes = set(re.findall(r'\.([a-zA-Z0-9_\-]+)', apple_css))

print(f"Total HTML classes: {len(classes_in_html)}")
print(f"Classes in old CSS: {len(old_css_classes)}")
print(f"Classes in new Apple CSS: {len(new_css_classes)}")

missing_from_new = old_css_classes - new_css_classes
print(f"Classes present in old CSS but missing in new Apple CSS: {len(missing_from_new)}")
if missing_from_new:
    print(f"Examples: {sorted(list(missing_from_new))[:30]}")
