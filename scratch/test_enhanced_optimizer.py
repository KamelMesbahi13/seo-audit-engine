import sys
sys.path.insert(0, '.')
import re
from utils import fetch_url
from bs4 import BeautifulSoup
from optimizer import clean_seo_slug, estimate_pixel_width, generate_word_diff

def extract_keyword_from_notice(notice_text: str) -> str:
    """Extracts a genuine focus keyword from plugin notice ONLY if explicitly declared."""
    if not notice_text:
        return ""
    text = notice_text.strip()
    # 1. Quoted declaration: Focus Keyword: 'xyz'
    m = re.search(r'(?:focus\s+key(?:word|phrase)|keyphrase|target\s+keyword)[:\s]+[\'\"“]([^\'\"”]{2,45})[\'\"”]', text, re.I)
    if m:
        candidate = m.group(1).strip()
        negative_words = ['not found', 'missing', 'error', 'warning', 'too short', 'too long', 'appear', 'add', 'use', 'consider', 'in the', 'to the']
        if not any(nw in candidate.lower() for nw in negative_words):
            return candidate

    # 2. Key: val syntax
    m = re.search(r'^(?:focus\s+key(?:word|phrase)|keyword)\s*:\s*([a-zA-Z0-9\s\-_]{3,40})$', text, re.I | re.M)
    if m:
        candidate = m.group(1).strip()
        negative_words = ['not found', 'missing', 'error', 'warning', 'too short', 'too long', 'appear', 'add', 'use', 'consider']
        if not any(nw in candidate.lower() for nw in negative_words):
            return candidate

    return ""

def discover_page_keywords(target_url: str, title: str, h1_list: list, h2_list: list, body_text: str) -> tuple:
    """Discovers high-intent topical focus keywords directly from page content."""
    slug_raw = target_url.strip("/").split("/")[-1].replace("-", " ").replace("_", " ")
    candidates = []

    # 1. Topic from slug
    if "program" in slug_raw.lower():
        candidates.extend(["Digital Growth Programs", "Custom Scaling Roadmaps", "Business Growth Programs"])
    elif "service" in slug_raw.lower():
        candidates.extend(["Digital Experience & Engineering", "Software & Branding Services"])
    elif "audit" in slug_raw.lower():
        candidates.extend(["Strategic Growth Audit", "SEO & Technical Audit"])
    else:
        if slug_raw and slug_raw.lower() not in ("home", "index"):
            candidates.append(f"{slug_raw.title()} Solutions")

    # 2. Headings analysis
    all_headings = (h1_list or []) + (h2_list or [])
    for h in all_headings:
        cleaned = re.sub(r'[^\w\s]', '', h).strip()
        words = [w for w in cleaned.split() if w.lower() not in (
            'your', 'the', 'starts', 'every', 'with', 'today', 'got', 'a', 'mind', 'lets', 'get', 'started',
            'what', 'is', 'why', 'how', 'about', 'from', 'more', 'and', 'or', 'for', 'in'
        )]
        if 2 <= len(words) <= 4:
            candidate = " ".join(words).title()
            if len(candidate) > 7:
                candidates.append(candidate)

    # 3. Frequent significant phrases in body text
    m_phrases = re.findall(r'\b((?:Digital|Growth|Business|Strategic|Marketing|Engineering|Custom|Brand|Scaling)\s+(?:Programs|Roadmaps|Solutions|Laboratory|Strategy|Audit|Services|Platform))\b', body_text, re.I)
    for p in m_phrases:
        candidates.append(p.title())

    # Deduplicate and rank
    seen = set()
    ranked = []
    for c in candidates:
        norm = c.lower().strip()
        if norm not in seen and len(norm) > 5 and not any(bad in norm for bad in ('thank you', 'useful links', 'details', 'contact us', 'idea in')):
            seen.add(norm)
            ranked.append(c.strip())

    primary = ranked[0] if ranked else (f"{slug_raw.title()} Solutions" if slug_raw else "Digital Growth Services")
    return primary, ranked[:5]

def extract_dom_sections(html: str, target_url: str) -> list:
    """Extracts actual content sections from crawled HTML."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()

    main_el = soup.find("main") or soup.find("article") or soup.body or soup
    raw_sections = []
    curr_sec = {
        "tag": "h1",
        "heading": "",
        "paragraphs": [],
        "bullets": []
    }

    for el in main_el.find_all(["h1", "h2", "h3", "p", "ul", "ol"]):
        if el.find_parent(["footer", "nav"]):
            continue
        tag = el.name
        txt = el.get_text(" ", strip=True)
        if not txt or len(txt) < 3:
            continue

        if tag in ("h1", "h2"):
            if curr_sec["heading"] or curr_sec["paragraphs"] or curr_sec["bullets"]:
                raw_sections.append(curr_sec)
            curr_sec = {
                "tag": tag,
                "heading": txt,
                "paragraphs": [],
                "bullets": []
            }
        elif tag == "h3":
            curr_sec["paragraphs"].append(f"**{txt}**")
        elif tag == "p":
            if len(txt.split()) >= 3 and not any(skip in txt.lower() for skip in ('your request has been sent', 'cookies', 'all rights reserved')):
                curr_sec["paragraphs"].append(txt)
        elif tag in ("ul", "ol"):
            items = [li.get_text(" ", strip=True) for li in el.find_all("li") if len(li.get_text(strip=True)) > 2]
            if items and not any(nav_w in [i.lower() for i in items[:3]] for nav_w in ('home', 'services', 'programmes', 'about')):
                curr_sec["bullets"].extend(items)

    if curr_sec["heading"] or curr_sec["paragraphs"] or curr_sec["bullets"]:
        raw_sections.append(curr_sec)

    # Consolidate and clean sections
    clean_sections = []
    seen_headings = set()
    for s in raw_sections:
        h_text = s["heading"].strip()
        h_norm = h_text.lower()
        if not h_text and not s["paragraphs"] and not s["bullets"]:
            continue
        if any(skip in h_norm for skip in ('useful links', 'our services', 'thank you', 'navigation')):
            continue
        if h_norm in seen_headings:
            # Merge with existing section
            for prev in clean_sections:
                if prev["heading"].lower() == h_norm:
                    prev["paragraphs"].extend(s["paragraphs"])
                    prev["bullets"].extend(s["bullets"])
                    break
        else:
            seen_headings.add(h_norm)
            clean_sections.append(s)

    return clean_sections

url = "https://www.inersialab.com/Programmes"
res = fetch_url(url, timeout=12)
html = res.get("html") or ""
soup = BeautifulSoup(html, "lxml")
raw_title = soup.title.get_text(strip=True) if soup.title else ""
h1_list = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
h2_list = [h.get_text(" ", strip=True) for h in soup.find_all("h2")]
body_text = soup.get_text(" ", strip=True)

primary_kw, rec_kws = discover_page_keywords(url, raw_title, h1_list, h2_list, body_text)
print("Primary Focus Keyword:", primary_kw)
print("Recommended Keywords:", rec_kws)

sections = extract_dom_sections(html, url)
print(f"\nExtracted {len(sections)} distinct content sections:")
for i, s in enumerate(sections):
    print(f"\n--- Section {i+1} [{s['tag'].upper()}]: {s['heading']} ---")
    print(f"P count: {len(s['paragraphs'])}, Bullets: {len(s['bullets'])}")
    if s["paragraphs"]:
        print("P0:", s["paragraphs"][0][:120])
    if s["bullets"]:
        print("B0:", s["bullets"][0][:80])
