import sys
sys.path.insert(0, '.')
from utils import fetch_url
from bs4 import BeautifulSoup
import re
from optimizer import generate_word_diff

def extract_and_improve_page_sections(url: str, custom_kw: str = "", custom_brand: str = "", industry: str = "tech"):
    res = fetch_url(url, timeout=12)
    html = res.get("html") or ""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()

    raw_title = soup.title.get_text(strip=True) if soup.title else ""
    meta_desc = ""
    m_tag = soup.find("meta", attrs={"name": "description"})
    if m_tag and m_tag.get("content"):
        meta_desc = m_tag["content"].strip()

    # Discover brand
    brand = custom_brand.strip()
    if not brand:
        if " - " in raw_title:
            brand = raw_title.split(" - ")[-1].strip()
        elif " | " in raw_title:
            brand = raw_title.split(" | ")[-1].strip()
        else:
            brand = "InersiaLab"

    # Extract all headings and text blocks
    h1_list = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    h2_list = [h.get_text(" ", strip=True) for h in soup.find_all("h2")]

    # 1. Determine focus keyword and recommendations
    candidates = []
    slug_raw = url.strip("/").split("/")[-1].replace("-", " ").replace("_", " ")
    if "program" in slug_raw.lower():
        candidates.extend(["Digital Growth Programs", "Custom Scaling Roadmaps", "Business Growth Programs"])
    elif "service" in slug_raw.lower():
        candidates.extend(["Digital Experience & Engineering", "Software & Branding Services"])
    else:
        if slug_raw and slug_raw.lower() not in ("home", "index"):
            candidates.append(f"{slug_raw.title()} Solutions")

    for h in (h1_list + h2_list):
        cleaned = re.sub(r'[^\w\s]', '', h).strip()
        words = [w for w in cleaned.split() if w.lower() not in ('your', 'the', 'starts', 'every', 'with', 'today', 'got', 'a', 'mind', 'lets', 'get', 'started')]
        if 2 <= len(words) <= 4:
            candidates.append(" ".join(words).title())

    # Filter candidates
    rec_keywords = []
    seen = set()
    for c in candidates:
        norm = c.lower()
        if norm not in seen and len(norm) > 6 and not any(bad in norm for bad in ('thank you', 'details', 'useful links', 'contact us')):
            seen.add(norm)
            rec_keywords.append(c)

    focus_kw = custom_kw.strip() or (rec_keywords[0] if rec_keywords else "Digital Growth Programs")
    kw_title = focus_kw.title()

    # 2. Extract real DOM sections
    # Find all top-level content sections or group by H1/H2
    main_el = soup.find("main") or soup.find("article") or soup.body or soup

    raw_sections = []
    curr_sec = {
        "heading_tag": "h1" if h1_list else "h2",
        "heading": h1_list[0] if h1_list else (raw_title or "Page Header"),
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
            # Check if this heading has meaningful content
            if curr_sec["paragraphs"] or curr_sec["bullets"] or curr_sec["heading"]:
                raw_sections.append(curr_sec)
            curr_sec = {
                "heading_tag": tag,
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
            # Avoid menu lists
            if items and not any(nav_w in [i.lower() for i in items[:3]] for nav_w in ('home', 'services', 'programmes', 'about')):
                curr_sec["bullets"].extend(items)

    if curr_sec["paragraphs"] or curr_sec["bullets"] or curr_sec["heading"]:
        raw_sections.append(curr_sec)

    # Filter meaningful sections (drop empty ones or mere navigation repeats)
    meaningful_sections = []
    for s in raw_sections:
        h_lower = s["heading"].lower()
        if any(skip in h_lower for skip in ('useful links', 'our services', 'thank you', 'navigation')):
            continue
        if s["paragraphs"] or s["bullets"] or len(s["heading"]) > 10:
            meaningful_sections.append(s)

    print(f"Total Meaningful Sections Extracted: {len(meaningful_sections)}")
    for idx, s in enumerate(meaningful_sections):
        print(f"\n--- SECTION {idx+1}: [{s['heading_tag'].upper()}] {s['heading']} ---")
        p_preview = " | ".join(s["paragraphs"][:2])
        print(f"Text preview: {p_preview[:140]}...")
        if s["bullets"]:
            print(f"Bullets ({len(s['bullets'])}): {s['bullets'][:2]}")

extract_and_improve_page_sections("https://www.inersialab.com/Programmes")
