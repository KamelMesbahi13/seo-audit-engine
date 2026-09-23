"""agy-seo: Full-site crawler. Discovers ALL pages via sitemaps + internal link following."""

from collections import deque
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, parse_qsl

from utils import (
    fetch_url, fetch_robots_txt, normalize_url, get_domain,
    is_same_domain, resolve_url, parse_robots_txt, parse_page,
    is_url_disallowed,
)


class SiteCrawler:
    """Crawl a website and discover all pages without artificial limits."""

    def __init__(self, base_url: str, max_pages: int = None, max_depth: int = None,
                 verbose: bool = True, cancel_check: callable = None):
        self.base_url = base_url.rstrip("/")
        self.domain = get_domain(base_url)
        # 0 or None represents unlimited crawl (all pages)
        self.max_pages = max_pages if (max_pages is not None and max_pages > 0) else None
        self.max_depth = max_depth if (max_depth is not None and max_depth > 0) else None
        self.verbose = verbose
        self.cancel_check = cancel_check

        self.discovered: dict[str, dict] = {}   # normalized_url -> metadata
        self.crawled: dict[str, dict] = {}       # normalized_url -> fetch result + parsed
        self.robots_data: dict = {}
        self.robots_raw: str = ""
        self.sitemap_urls: list[str] = []
        self.errors: list[dict] = []
        self.path_query_counts: dict[str, int] = {}  # base path -> number of query variants queued

    def log(self, msg: str):
        if self.verbose:
            print(f"  [crawler] {msg}")

    def crawl(self) -> dict:
        """Run the full crawl pipeline. Returns a summary dict."""
        scope_str = f"{self.max_pages} pages" if self.max_pages is not None else "Unlimited (All Pages)"
        depth_str = f"{self.max_depth}" if self.max_depth is not None else "Unlimited"
        self.log(f"Starting crawl of {self.base_url}")
        self.log(f"Crawl scope: {scope_str}, Depth limit: {depth_str}")

        # 1. Fetch and parse robots.txt
        self._fetch_robots()

        # 2. Discover URLs from sitemaps
        self._discover_from_sitemaps()

        # 3. Add the base URL
        self._add_url(self.base_url, source="seed", depth=0)

        # 4. Crawl discovered pages and follow internal links (full BFS queue)
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

        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        # Skip non-HTML resources and binary assets
        skip_extensions = (
            ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
            ".css", ".js", ".ico", ".woff", ".woff2", ".ttf", ".eot",
            ".mp4", ".mp3", ".zip", ".gz", ".tar", ".rar", ".avi",
            ".mov", ".wmv", ".doc", ".docx", ".xls", ".xlsx", ".ppt",
            ".pptx", ".xml", ".json", ".txt", ".csv", ".exe", ".dmg",
        )
        if any(path_lower.endswith(ext) for ext in skip_extensions):
            return False

        # Spider trap prevention 1: Robots.txt rules (disallow patterns)
        if self.robots_data and is_url_disallowed(url, self.robots_data):
            return False

        # Spider trap prevention 2: Excessive repeating segments
        path_segments = [s for s in path_lower.split("/") if s]
        if len(path_segments) > 12:
            return False
        if any(path_segments.count(s) >= 3 for s in set(path_segments)):
            return False

        # Spider trap prevention 3: Non-SEO transactional, cart, auth, and search paths
        trap_path_prefixes = (
            "/cart", "/panier", "/checkout", "/commander", "/commande", "/order", "/basket",
            "/my-account", "/mon-compte", "/login", "/connexion", "/register", "/signup",
            "/inscription", "/auth", "/logout", "/deconnexion", "/password",
            "/password-recovery", "/mot-de-passe-oublie", "/forgot-password",
            "/wishlist", "/liste-d-envies", "/compare", "/comparateur",
            "/quick-view", "/quickview", "/search", "/recherche", "/find",
            "/wp-admin", "/admin", "/feed", "/rss"
        )
        if any(path_lower == p or path_lower.startswith(p + "/") for p in trap_path_prefixes):
            return False

        # Spider trap prevention 4: Deep pagination traps (page 4+ of listings)
        if parsed.query:
            for k, v in parse_qsl(parsed.query):
                k_lower = k.lower()
                if k_lower in ("page", "p", "paged", "pg") and v.isdigit() and int(v) > 3:
                    return False
                if k_lower == "start" and v.isdigit() and int(v) > 60:
                    return False

            # Spider trap prevention 5: Cap query variations to at most 2 per base path
            query_count = self.path_query_counts.get(path_lower, 0)
            if query_count >= 2:
                return False
            self.path_query_counts[path_lower] = query_count + 1

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
            if self.cancel_check and self.cancel_check():
                break
            if self.max_pages is not None and len(self.discovered) >= self.max_pages:
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
                if self.max_pages is not None and len(self.discovered) >= self.max_pages:
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
        """Crawl discovered pages using a continuous BFS queue until all reachable pages are crawled."""
        queue = deque()

        # Seed the queue with all initial discovered URLs sorted by depth
        for norm, entry in sorted(self.discovered.items(), key=lambda x: x[1]["depth"]):
            if norm not in self.crawled:
                queue.append(entry["url"])

        crawl_count = 0
        limit_str = str(self.max_pages) if self.max_pages is not None else "unlimited"

        while queue:
            if self.cancel_check and self.cancel_check():
                self.log("Crawl interrupted by user stop request.")
                break

            if self.max_pages is not None and crawl_count >= self.max_pages:
                self.log(f"Reached crawl limit of {self.max_pages} pages. Stopping.")
                break

            url = queue.popleft()
            norm = normalize_url(url)

            if norm in self.crawled:
                continue

            entry = self.discovered.get(norm, {"depth": 0, "url": url})
            depth = entry.get("depth", 0)

            # Check depth limit if specified
            if self.max_depth is not None and depth > self.max_depth:
                continue

            crawl_count += 1
            self.log(f"Crawling [{crawl_count}/{limit_str}] (depth={depth}, queue={len(queue)}): {url}")

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

            # Map final URL if redirected on the same domain
            final_norm = normalize_url(result["final_url"])
            if final_norm != norm and is_same_domain(result["final_url"], self.base_url):
                self.crawled[final_norm] = self.crawled[norm]

            # Discover and enqueue new internal links
            if self.max_depth is None or depth < self.max_depth:
                internal_links = parsed.get("links", {}).get("internal", [])
                for link in internal_links:
                    href = link.get("href", "")
                    if href:
                        if self._add_url(href, source="link", depth=depth + 1):
                            new_norm = normalize_url(href)
                            if new_norm not in self.crawled:
                                queue.append(href)
