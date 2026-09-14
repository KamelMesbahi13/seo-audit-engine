"""agy-seo: Shared utilities for fetching, parsing, and normalizing web pages."""

import hashlib
import re
import sys
import time
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, Comment

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
GOOGLEBOT_UA = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)
REQUEST_TIMEOUT = 15
MAX_RETRIES = 2

SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
    "x-xss-protection",
    "cross-origin-opener-policy",
    "cross-origin-resource-policy",
]

AI_CRAWLERS = {
    "GPTBot": {"purpose": "OpenAI training", "search": False},
    "OAI-SearchBot": {"purpose": "ChatGPT Search", "search": True},
    "ChatGPT-User": {"purpose": "ChatGPT browsing", "search": True},
    "ClaudeBot": {"purpose": "Anthropic training", "search": False},
    "Claude-SearchBot": {"purpose": "Claude search", "search": True},
    "PerplexityBot": {"purpose": "Perplexity search", "search": True},
    "Google-Extended": {"purpose": "Gemini training", "search": False},
    "Applebot-Extended": {"purpose": "Apple Intelligence training", "search": False},
    "CCBot": {"purpose": "Common Crawl", "search": False},
    "cohere-ai": {"purpose": "Cohere training", "search": False},
    "Bytespider": {"purpose": "ByteDance/TikTok", "search": False},
}


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower().rstrip(".")
    # Remove default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    path = parsed.path or "/"
    # Remove trailing slash except for root
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    # Remove fragment
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))


def get_domain(url: str) -> str:
    """Extract the domain (netloc) from a URL."""
    return urlparse(url).netloc.lower()


def is_same_domain(url: str, base_url: str) -> bool:
    """Check if a URL belongs to the same domain as base_url."""
    return get_domain(url) == get_domain(base_url)


def resolve_url(href: str, base_url: str) -> str | None:
    """Resolve a potentially relative href against a base URL."""
    if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return None
    try:
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            return None
        return absolute
    except Exception:
        return None


def url_hash(url: str) -> str:
    """Short hash for a URL, useful as a filename-safe identifier."""
    return hashlib.md5(normalize_url(url).encode()).hexdigest()[:10]


# ---------------------------------------------------------------------------
# HTTP fetching
# ---------------------------------------------------------------------------

def fetch_url(url: str, timeout: int = REQUEST_TIMEOUT, ua: str = USER_AGENT) -> dict:
    """Fetch a URL and return status, headers, and body.
    
    Returns dict with keys: url, final_url, status, headers, html, error, 
    redirect_chain, response_time_ms
    """
    result = {
        "url": url,
        "final_url": url,
        "status": 0,
        "headers": {},
        "html": "",
        "error": None,
        "redirect_chain": [],
        "response_time_ms": 0,
    }
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            start = time.monotonic()
            resp = requests.get(
                url,
                headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                timeout=timeout,
                allow_redirects=True,
            )
            elapsed = (time.monotonic() - start) * 1000
            
            result["status"] = resp.status_code
            result["headers"] = dict(resp.headers)
            result["final_url"] = resp.url
            result["response_time_ms"] = round(elapsed)
            result["redirect_chain"] = [
                {"url": r.url, "status": r.status_code}
                for r in resp.history
            ]
            
            # Handle encoding
            resp.encoding = resp.apparent_encoding or "utf-8"
            result["html"] = resp.text
            return result
            
        except requests.exceptions.Timeout:
            result["error"] = f"Timeout after {timeout}s"
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"Connection error: {str(e)[:200]}"
        except requests.exceptions.RequestException as e:
            result["error"] = f"Request error: {str(e)[:200]}"
        
        if attempt < MAX_RETRIES:
            time.sleep(1 * (attempt + 1))
    
    return result


def fetch_robots_txt(base_url: str) -> str:
    """Fetch robots.txt for a domain."""
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    result = fetch_url(robots_url, timeout=10)
    if result["status"] == 200:
        return result["html"]
    return ""


def check_url_status(url: str, timeout: int = 8) -> int:
    """Quick HEAD request to check URL status code."""
    try:
        resp = requests.head(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        return resp.status_code
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

def parse_page(html: str, url: str) -> dict:
    """Parse an HTML page and extract all SEO-relevant data."""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    
    data = {
        "url": url,
        "title": _extract_title(soup),
        "meta_description": _extract_meta(soup, "description"),
        "meta_robots": _extract_meta(soup, "robots"),
        "canonical": _extract_canonical(soup),
        "charset": _extract_charset(soup),
        "viewport": _extract_meta(soup, "viewport"),
        "lang": _extract_lang(soup),
        "h1": _extract_headings(soup, "h1"),
        "h2": _extract_headings(soup, "h2"),
        "h3": _extract_headings(soup, "h3"),
        "h4": _extract_headings(soup, "h4"),
        "h5": _extract_headings(soup, "h5"),
        "h6": _extract_headings(soup, "h6"),
        "images": _extract_images(soup, url),
        "links": _extract_links(soup, url),
        "schema": _extract_schema(soup),
        "open_graph": _extract_og(soup),
        "twitter_card": _extract_twitter(soup),
        "hreflang": _extract_hreflang(soup),
        "word_count": _count_words(soup),
        "body_text": _extract_body_text(soup),
        "preload_hints": _extract_preloads(soup),
        "scripts": _extract_scripts(soup),
        "stylesheets": _extract_stylesheets(soup),
        "forms": _extract_forms(soup),
    }
    return data


def _extract_title(soup: BeautifulSoup) -> str:
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else ""


def _extract_meta(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"name": re.compile(f"^{name}$", re.I)})
    if tag:
        return tag.get("content", "")
    # Also check property for OG-style tags
    tag = soup.find("meta", attrs={"property": re.compile(f"^{name}$", re.I)})
    return tag.get("content", "") if tag else ""


def _extract_canonical(soup: BeautifulSoup) -> str:
    tag = soup.find("link", attrs={"rel": "canonical"})
    return tag.get("href", "") if tag else ""


def _extract_charset(soup: BeautifulSoup) -> str:
    tag = soup.find("meta", attrs={"charset": True})
    if tag:
        return tag.get("charset", "")
    tag = soup.find("meta", attrs={"http-equiv": re.compile("content-type", re.I)})
    if tag:
        content = tag.get("content", "")
        m = re.search(r"charset=([^\s;]+)", content, re.I)
        return m.group(1) if m else ""
    return ""


def _extract_lang(soup: BeautifulSoup) -> str:
    html_tag = soup.find("html")
    return html_tag.get("lang", "") if html_tag else ""


def _extract_headings(soup: BeautifulSoup, tag_name: str) -> list[str]:
    return [h.get_text(" ", strip=True) for h in soup.find_all(tag_name)]


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[dict]:
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if src:
            src = urljoin(base_url, src)
        images.append({
            "src": src,
            "alt": img.get("alt", ""),
            "width": img.get("width", ""),
            "height": img.get("height", ""),
            "loading": img.get("loading", ""),
            "fetchpriority": img.get("fetchpriority", ""),
            "srcset": img.get("srcset", ""),
        })
    return images


def _extract_links(soup: BeautifulSoup, base_url: str) -> dict:
    internal, external = [], []
    base_domain = get_domain(base_url)
    
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        resolved = resolve_url(href, base_url)
        if not resolved:
            continue
        
        link_data = {
            "href": resolved,
            "text": a.get_text(" ", strip=True),
            "rel": a.get("rel", []),
            "title": a.get("title", ""),
        }
        
        if is_same_domain(resolved, base_url):
            internal.append(link_data)
        else:
            external.append(link_data)
    
    return {"internal": internal, "external": external}


def _extract_schema(soup: BeautifulSoup) -> list:
    import json
    schemas = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                schemas.extend(data)
            elif isinstance(data, dict):
                if "@graph" in data:
                    schemas.extend(data["@graph"])
                else:
                    schemas.append(data)
        except (json.JSONDecodeError, TypeError):
            pass
    return schemas


def _extract_og(soup: BeautifulSoup) -> dict:
    og = {}
    for tag in soup.find_all("meta", attrs={"property": re.compile("^og:", re.I)}):
        og[tag.get("property", "")] = tag.get("content", "")
    return og


def _extract_twitter(soup: BeautifulSoup) -> dict:
    tc = {}
    for tag in soup.find_all("meta", attrs={"name": re.compile("^twitter:", re.I)}):
        tc[tag.get("name", "")] = tag.get("content", "")
    return tc


def _extract_hreflang(soup: BeautifulSoup) -> list[dict]:
    tags = []
    for link in soup.find_all("link", attrs={"rel": "alternate", "hreflang": True}):
        tags.append({
            "lang": link.get("hreflang", ""),
            "href": link.get("href", ""),
        })
    return tags


def _count_words(soup: BeautifulSoup) -> int:
    text = _extract_body_text(soup)
    return len(text.split())


def _extract_body_text(soup: BeautifulSoup) -> str:
    body = soup.find("body")
    if not body:
        return ""
    # Remove script, style, nav, footer, header for content analysis
    for tag in body.find_all(["script", "style", "noscript"]):
        tag.decompose()
    for comment in body.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    return body.get_text(" ", strip=True)


def _extract_preloads(soup: BeautifulSoup) -> list[dict]:
    preloads = []
    for link in soup.find_all("link", attrs={"rel": True}):
        rel = " ".join(link.get("rel", []))
        if any(r in rel for r in ("preload", "preconnect", "prefetch", "dns-prefetch", "modulepreload")):
            preloads.append({
                "rel": rel,
                "href": link.get("href", ""),
                "as": link.get("as", ""),
                "type": link.get("type", ""),
                "crossorigin": link.get("crossorigin"),
            })
    return preloads


def _extract_scripts(soup: BeautifulSoup) -> list[dict]:
    scripts = []
    for s in soup.find_all("script"):
        src = s.get("src", "")
        scripts.append({
            "src": src,
            "async": s.has_attr("async"),
            "defer": s.has_attr("defer"),
            "type": s.get("type", ""),
            "inline": not bool(src),
        })
    return scripts


def _extract_stylesheets(soup: BeautifulSoup) -> list[dict]:
    sheets = []
    for link in soup.find_all("link", attrs={"rel": "stylesheet"}):
        sheets.append({
            "href": link.get("href", ""),
            "media": link.get("media", ""),
        })
    return sheets


def _extract_forms(soup: BeautifulSoup) -> list[dict]:
    forms = []
    for form in soup.find_all("form"):
        inputs = []
        for inp in form.find_all(["input", "textarea", "select"]):
            inp_id = inp.get("id", "")
            has_label = bool(soup.find("label", attrs={"for": inp_id})) if inp_id else False
            inputs.append({
                "type": inp.get("type", inp.name),
                "name": inp.get("name", ""),
                "id": inp_id,
                "has_label": has_label,
                "aria_label": inp.get("aria-label", ""),
            })
        forms.append({
            "action": form.get("action", ""),
            "method": form.get("method", "GET"),
            "inputs": inputs,
        })
    return forms


# ---------------------------------------------------------------------------
# Robots.txt parsing
# ---------------------------------------------------------------------------

def parse_robots_txt(robots_text: str) -> dict:
    """Parse robots.txt and return structured data."""
    result = {
        "sitemaps": [],
        "rules": {},       # user-agent -> list of {type, path}
        "crawl_delay": {},  # user-agent -> delay
    }
    
    current_ua = "*"
    for line in robots_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        if ":" not in line:
            continue
        
        directive, _, value = line.partition(":")
        directive = directive.strip().lower()
        value = value.strip()
        
        if directive == "user-agent":
            current_ua = value
            if current_ua not in result["rules"]:
                result["rules"][current_ua] = []
        elif directive == "sitemap":
            if value and value not in result["sitemaps"]:
                result["sitemaps"].append(value)
        elif directive in ("disallow", "allow"):
            if current_ua not in result["rules"]:
                result["rules"][current_ua] = []
            result["rules"][current_ua].append({"type": directive, "path": value})
        elif directive == "crawl-delay":
            try:
                result["crawl_delay"][current_ua] = float(value)
            except ValueError:
                pass
    
    return result


def is_bot_blocked(robots_data: dict, bot_name: str) -> bool:
    """Check if a specific bot is blocked in robots.txt rules."""
    # Check bot-specific rules first
    rules = robots_data.get("rules", {})
    
    bot_rules = rules.get(bot_name, [])
    if bot_rules:
        # If there's a specific disallow for / with no allow, it's blocked
        for rule in bot_rules:
            if rule["type"] == "disallow" and rule["path"] in ("/", ""):
                # Check if there's a more specific allow
                has_allow = any(r["type"] == "allow" for r in bot_rules)
                if not has_allow:
                    return True
                # If disallow is / and allow is more specific, still blocked for most
                if rule["path"] == "/":
                    return True
        return False
    
    # Fall back to wildcard rules
    wildcard_rules = rules.get("*", [])
    for rule in wildcard_rules:
        if rule["type"] == "disallow" and rule["path"] == "/":
            return True
    
    return False


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def clamp_score(score: float) -> int:
    """Clamp a score to 0-100 integer range."""
    return max(0, min(100, int(round(score))))
