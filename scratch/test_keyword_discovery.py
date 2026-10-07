import sys
sys.path.insert(0, '.')
from utils import fetch_url
from bs4 import BeautifulSoup
import re

url = "https://www.inersialab.com/Programmes"
res = fetch_url(url, timeout=12)
html = res.get("html") or ""
soup = BeautifulSoup(html, "lxml")

for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
    tag.decompose()

title = soup.title.get_text(strip=True) if soup.title else ""
h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
h2s = [h.get_text(" ", strip=True) for h in soup.find_all("h2")]
ps = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True).split()) > 5]

slug = url.strip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()

print("Slug:", slug)
print("Title:", title)
print("H1:", h1)
print("H2s:", h2s[:4])

# Test notice
notice = """- Focus Keyword not found in the URL permalink
- Focus Keyword does not appear in the first 10% of the content.
- Use Focus Keyword in subheadings like H2, H3.
- Content is 220 words long. Consider using at least 600 words.
- Add a number to your SEO title to improve CTR.
- Add an emotional power word to your SEO title."""

def extract_keyword_from_notice(notice_text: str) -> str:
    if not notice_text:
        return ""
    m = re.search(r'(?:focus\s+key(?:word|phrase)|keyphrase|keyword)[:\s]+[\'\"“]([^\'\"”]{2,40})[\'\"”]', notice_text, re.I)
    if m:
        kw = m.group(1).strip()
        if not re.search(r'\b(not found|missing|error|warning|too short|too long|appear|add|use)\b', kw, re.I):
            return kw
    m = re.search(r'(?:focus\s+key(?:word|phrase)|target\s+keyword)[:\s]+([a-zA-Z0-9\s\-_]{3,35})(?:\n|\.|\,|$)', notice_text, re.I)
    if m:
        candidate = m.group(1).strip()
        negative_words = [
            'not found', 'missing', 'does not', "doesn't", 'appear', 'add a', 'add an',
            'use focus', 'consider', 'too short', 'too long', 'in the', 'to the', 'like',
            'permalink', 'url', 'density', 'below', 'is set', 'has been'
        ]
        if not any(nw in candidate.lower() for nw in negative_words):
            words = candidate.split()
            if len(words) <= 5 and not any(w in ('not', 'no', 'is', 'in', 'to', 'for', 'the') for w in words[:1]):
                return candidate
    return ""

print("Notice extracted keyword:", extract_keyword_from_notice(notice))

def discover_page_keywords(url, title, h1_list, h2_list, body_snippets):
    slug_raw = url.strip("/").split("/")[-1].replace("-", " ").replace("_", " ")
    slug_title = slug_raw.title()
    
    candidates = []
    
    # 1. Look for high-intent combinations in H2s and H1
    all_headings = (h1_list or []) + (h2_list or [])
    for h in all_headings:
        # Clean heading
        h_clean = re.sub(r'[^\w\s]', '', h).strip()
        words = h_clean.split()
        if 2 <= len(words) <= 5:
            candidates.append(h_clean)
        # Check for phrases containing "Program", "Service", "Solution", "Development", "Growth", "Agency", etc.
        m = re.search(r'\b((?:[A-Z][a-z]+\s+){1,3}(?:Programs|Programmes|Solutions|Roadmaps|Services|Laboratory|Strategy|Audit))\b', h, re.I)
        if m:
            candidates.append(m.group(1).strip().title())
            
    # 2. Add composite combinations from slug + main topic
    if slug_title and slug_title.lower() not in ("home", "index"):
        if "program" in slug_title.lower():
            candidates.append("Digital Growth Programs")
            candidates.append("Custom Scaling Programs")
        elif "service" in slug_title.lower():
            candidates.append("Software & Branding Services")
        else:
            candidates.append(f"{slug_title} Solutions")
            
    # Add H1 topic
    if h1_list:
        h1_text = h1_list[0]
        m = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', h1_text)
        if m and len(m.group(1).split()) >= 2:
            candidates.append(m.group(1).strip().title())
            
    # Deduplicate while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        norm = c.lower().strip()
        if norm not in seen and len(norm) > 5 and not any(w in norm for w in ('your', 'every', 'today', 'starts with', 'what is', 'got a')):
            seen.add(norm)
            unique_candidates.append(c.strip().title())
            
    return unique_candidates[:6]

recommended = discover_page_keywords(url, title, h1, h2s, ps)
print("Recommended Keywords:", recommended)
