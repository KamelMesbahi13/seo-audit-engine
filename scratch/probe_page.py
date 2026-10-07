import sys
sys.path.insert(0, '.')
from utils import fetch_url
from bs4 import BeautifulSoup

url = sys.argv[1] if len(sys.argv) > 1 else "https://www.inersialab.com/Programmes"
r = fetch_url(url, timeout=15)
print("status", r.get("status"), "final", r.get("final_url"), "len", len(r.get("html") or ""))
soup = BeautifulSoup(r.get("html") or "", "lxml")
print("TITLE:", soup.title.get_text(strip=True) if soup.title else None)
md = soup.find("meta", attrs={"name": "description"})
print("DESC:", md.get("content") if md else None)
for t in soup(["script", "style", "noscript", "svg"]):
    t.decompose()
body = soup.body or soup
for el in body.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
    txt = el.get_text(" ", strip=True)
    if txt:
        print(f"[{el.name}] {txt[:160]}")
