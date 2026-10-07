import sys
sys.path.insert(0, '.')
from utils import fetch_url
from bs4 import BeautifulSoup
import re

url = "https://www.inersialab.com/Programmes"
res = fetch_url(url, timeout=12)
html = res.get("html") or ""

soup = BeautifulSoup(html, "lxml")

# Remove header nav, footer, scripts, styles
for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
    tag.decompose()

# Find main content container if available
main_el = soup.find("main") or soup.find("article") or soup.find("body") or soup

# Extract sections grouped by H1 / H2
sections = []
current_section = {
    "title": "Hero / Page Header",
    "level": "h1",
    "heading": "",
    "paragraphs": [],
    "bullets": [],
}

# Walk top-level or heading-level elements
for el in main_el.find_all(["h1", "h2", "h3", "p", "ul", "ol"]):
    tag = el.name
    text = el.get_text(" ", strip=True)
    if not text or len(text) < 3:
        continue
    
    # Check if element is inside footer or nav
    if el.find_parent(["footer", "nav"]):
        continue

    if tag in ("h1", "h2"):
        if current_section["heading"] or current_section["paragraphs"] or current_section["bullets"]:
            sections.append(current_section)
        current_section = {
            "title": text,
            "level": tag,
            "heading": text,
            "paragraphs": [],
            "bullets": [],
        }
    elif tag == "h3":
        current_section["paragraphs"].append(f"### {text}")
    elif tag == "p":
        # Filter out tiny boilerplate
        if len(text.split()) >= 3:
            current_section["paragraphs"].append(text)
    elif tag in ("ul", "ol"):
        items = [li.get_text(" ", strip=True) for li in el.find_all("li") if li.get_text(" ", strip=True)]
        if items:
            current_section["bullets"].extend(items[:8])

if current_section["heading"] or current_section["paragraphs"] or current_section["bullets"]:
    sections.append(current_section)

print(f"Total Sections Extracted: {len(sections)}")
for i, s in enumerate(sections):
    print(f"\n--- SECTION {i+1}: [{s['level'].upper()}] {s['heading'] or s['title']} ---")
    print(f"Paragraphs count: {len(s['paragraphs'])}, Bullets count: {len(s['bullets'])}")
    if s["paragraphs"]:
        print("Sample P:", s["paragraphs"][0][:120])
    if s["bullets"]:
        print("Sample Bullets:", s["bullets"][:3])
