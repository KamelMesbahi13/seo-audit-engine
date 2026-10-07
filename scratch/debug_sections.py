import sys
sys.path.insert(0, '.')
from utils import fetch_url
from bs4 import BeautifulSoup
from scratch.test_enhanced_optimizer import extract_dom_sections, discover_page_keywords

url = 'https://www.inersialab.com/Programmes'
res = fetch_url(url, timeout=12)
html = res.get('html') or ''
sections = extract_dom_sections(html, url)
print(f"Total sections: {len(sections)}")
for i, s in enumerate(sections):
    print(f"\n=== Section {i+1}: <{s['tag']}> {s['heading']} ===")
    print(f"Paragraphs ({len(s['paragraphs'])}):")
    for p in s['paragraphs'][:3]:
        print(f"  - {p[:120]}")
    print(f"Bullets ({len(s['bullets'])}):")
    for b in s['bullets'][:4]:
        print(f"  * {b[:120]}")
