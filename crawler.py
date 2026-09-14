"""agy-seo: Full-site crawler. Discovers ALL pages via sitemaps + internal link following."""

import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

from utils import (
    fetch_url, fetch_robots_txt, normalize_url, get_domain,
    is_same_domain, resolve_url, parse_robots_txt, parse_page,
)


class SiteCrawler:
    """Crawl a website and discover all pages."""

    def __init__(self, base_url: str, max_pages: int = 200, max_depth: int = 3,
                 verbose: bool = True):
        self.base_url = base_url.rstrip("/")
        self.domain = get_domain(base_url)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.verbose = verbose

        self.discovered: dict[str, dict] = {}   # normalized_url -> metadata
        self.crawled: dict[str, dict] = {}       # normalized_url -> fetch result + parsed
        self.robots_data: dict = {}
        self.robots_raw: str = ""
        self.sitemap_urls: list[str] = []
        self.errors: list[dict] = []

    def log(self, msg: str):
        if self.verbose:
            print(f"  [crawler] {msg}")

    def crawl(self) -> dict:
        """Run the full crawl pipeline. Returns a summary dict."""
        self.log(f"Starting crawl of {self.base_url}")
        self.log(f"Max pages: {self.max_pages}, Max depth: {self.max_depth}")

        # 1. Fetch and parse robots.txt
        self._fetch_robots()

        # 2. Discover URLs from sitemaps
        self._discover_from_sitemaps()

        # 3. Add the base URL
        self._add_url(self.base_url, source="seed", depth=0)

        # 4. Crawl discovered pages and follow internal links
        self._crawl_pages()

        self.log(f"Crawl complete. {len(self.crawled)} pages crawled, "
                 f"{len(self.discovered)} total URLs discovered.")

        return {
            "base_url": self.base_url,
            "domain": self.domain,
            "pages_crawled": len(self.crawled),
            "urls_discovered": len(self.discovered),
            "robots_txt": self.robots_raw,
            "robots_data": self.robots_data,
            "sitemap_urls": self.sitemap_urls,
            "pages": self.crawled,
            "errors": self.errors,
        }

    def _add_url(self, url: str, source: str = "link", depth: int = 0) -> bool:
        """Add a URL to the discovery queue. Returns True if new."""
        norm = normalize_url(url)
        if norm in self.discovered:
            return False
        if not is_same_domain(url, self.base_url):
            return False
        # Skip non-HTML resources
        parsed = urlparse(url)
        skip_extensions = (
            ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
            ".css", ".js", ".ico", ".woff", ".woff2", ".ttf", ".eot",
            ".mp4", ".mp3", ".zip", ".gz", ".tar", ".rar",
        )
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        self.discovered[norm] = {
            "url": url,
            "source": source,
            "depth": depth,
            "crawled": False,
        }
        return True

    def _fetch_robots(self):
        """Fetch and parse robots.txt."""
        self.log("Fetching robots.txt...")
        self.robots_raw = fetch_robots_txt(self.base_url)
        if self.robots_raw:
            self.robots_data = parse_robots_txt(self.robots_raw)
            sitemaps = self.robots_data.get("sitemaps", [])
            self.log(f"robots.txt found. {len(sitemaps)} sitemap(s) declared.")
        else:
            self.robots_data = {"sitemaps": [], "rules": {}, "crawl_delay": {}}
            self.log("No robots.txt found.")

    def _discover_from_sitemaps(self):
        """Parse XML sitemaps and discover URLs."""
        sitemap_candidates = list(self.robots_data.get("sitemaps", []))

        # Add common fallback paths
        parsed = urlparse(self.base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in ["/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml"]:
            candidate = base + path
            if candidate not in sitemap_candidates:
                sitemap_candidates.append(candidate)

        visited_sitemaps = set()
        for sitemap_url in sitemap_candidates:
            if len(self.discovered) >= self.max_pages:
                break
            self._parse_sitemap(sitemap_url, visited_sitemaps)

    def _parse_sitemap(self, url: str, visited: set, depth: int = 0):
        """Recursively parse a sitemap (index or urlset)."""
        if url in visited or depth > 5:
            return
        visited.add(url)

        self.log(f"Fetching sitemap: {url}")
        result = fetch_url(url, timeout=10)
        if result["status"] != 200:
            self.log(f"  Sitemap {url} returned HTTP {result['status']}")
            return

        self.sitemap_urls.append(url)
        xml_text = result["html"]

        try:
            # Strip namespace for easier parsing
            xml_text_clean = xml_text.encode("utf-8", errors="replace")
            root = ET.fromstring(xml_text_clean)
        except ET.ParseError:
            self.log(f"  Failed to parse XML for {url}")
            return

        # Remove namespaces
        ns_pattern = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        ns_pattern2 = "{http://www.google.com/schemas/sitemap/0.84}"

        tag = root.tag.replace(ns_pattern, "").replace(ns_pattern2, "")

        if tag == "sitemapindex":
            # Sitemap index → follow children
            for sitemap in root:
                loc = sitemap.find(f"{ns_pattern}loc")
                if loc is None:
                    loc = sitemap.find("loc")
                if loc is not None and loc.text:
                    self._parse_sitemap(loc.text.strip(), visited, depth + 1)
        elif tag == "urlset":
            # URL set → extract URLs
            count = 0
            for url_elem in root:
                if len(self.discovered) >= self.max_pages:
                    break
                loc = url_elem.find(f"{ns_pattern}loc")
                if loc is None:
                    loc = url_elem.find("loc")
                if loc is not None and loc.text:
                    page_url = loc.text.strip()
                    if self._add_url(page_url, source="sitemap", depth=0):
                        count += 1
            self.log(f"  Found {count} new URLs in sitemap")

    def _crawl_pages(self):
        """Crawl discovered pages, following internal links."""
        queue = sorted(
            self.discovered.values(),
            key=lambda x: x["depth"]
        )

        crawl_count = 0
        for entry in queue:
            if crawl_count >= self.max_pages:
                break

            norm = normalize_url(entry["url"])
            if norm in self.crawled:
                continue

            url = entry["url"]
            depth = entry["depth"]

            self.log(f"Crawling [{crawl_count + 1}/{self.max_pages}] "
                     f"(depth={depth}): {url}")

            result = fetch_url(url)
            if result["error"]:
                self.errors.append({"url": url, "error": result["error"]})
                continue

            if result["status"] != 200:
                self.errors.append({"url": url, "error": f"HTTP {result['status']}"})
                # Still store for broken link reporting
                self.crawled[norm] = {
                    "fetch": result,
                    "parsed": None,
                }
                crawl_count += 1
                continue

            # Check content type
            content_type = result["headers"].get("Content-Type", "")
            if "text/html" not in content_type.lower() and "application/xhtml" not in content_type.lower():
                continue

            # Parse HTML
            parsed = parse_page(result["html"], result["final_url"])
            self.crawled[norm] = {
                "fetch": result,
                "parsed": parsed,
            }
            crawl_count += 1

            # Follow internal links (if within depth limit)
            if depth < self.max_depth:
                internal_links = parsed.get("links", {}).get("internal", [])
                for link in internal_links:
                    href = link.get("href", "")
                    if href:
                        self._add_url(href, source="link", depth=depth + 1)

        # Re-sort queue after new discoveries
        remaining = [
            e for e in self.discovered.values()
            if normalize_url(e["url"]) not in self.crawled
        ]
        remaining.sort(key=lambda x: x["depth"])

        for entry in remaining:
            if crawl_count >= self.max_pages:
                break
            norm = normalize_url(entry["url"])
            if norm in self.crawled:
                continue

            url = entry["url"]
            self.log(f"Crawling [{crawl_count + 1}/{self.max_pages}] "
                     f"(depth={entry['depth']}): {url}")

            result = fetch_url(url)
            if result["error"] or result["status"] != 200:
                if result["error"]:
                    self.errors.append({"url": url, "error": result["error"]})
                crawl_count += 1
                continue

            content_type = result["headers"].get("Content-Type", "")
            if "text/html" not in content_type.lower():
                continue

            parsed = parse_page(result["html"], result["final_url"])
            self.crawled[norm] = {"fetch": result, "parsed": parsed}
            crawl_count += 1
