"""agy-seo: Technical SEO analyzer — crawlability, indexing, security, mobile, rendering."""

import re
from utils import (
    SECURITY_HEADERS, AI_CRAWLERS, clamp_score,
    is_bot_blocked, parse_robots_txt, fetch_robots_txt,
)


def analyze_technical(page_data: dict, fetch_data: dict, robots_data: dict,
                      sitemap_urls: list, robots_raw: str) -> dict:
    """Run full technical SEO analysis on a single page."""
    findings = []
    fixes = []
    score = 100

    url = page_data["url"]
    headers = fetch_data.get("headers", {})
    status = fetch_data.get("status", 0)

    # -------------------------------------------------------------------
    # 1. HTTPS & Security
    # -------------------------------------------------------------------
    if not url.startswith("https://"):
        findings.append({
            "category": "Security", "severity": "critical",
            "issue": "Page served over HTTP (not HTTPS)",
            "detail": f"URL: {url}",
        })
        fixes.append({
            "issue": "HTTP not HTTPS",
            "fix": "Configure SSL/TLS certificate and redirect all HTTP to HTTPS via .htaccess or server config:\n"
                   "RewriteEngine On\nRewriteCond %{HTTPS} off\nRewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]",
        })
        score -= 20

    # Security headers check
    missing_security = []
    header_lower = {k.lower(): v for k, v in headers.items()}
    for sh in SECURITY_HEADERS:
        if sh not in header_lower:
            missing_security.append(sh)

    if missing_security:
        severity = "high" if "strict-transport-security" in missing_security else "medium"
        score_penalty = min(len(missing_security) * 2, 15)
        score -= score_penalty
        findings.append({
            "category": "Security", "severity": severity,
            "issue": f"{len(missing_security)} security header(s) missing",
            "detail": ", ".join(missing_security),
        })
        header_fixes = []
        if "strict-transport-security" in missing_security:
            header_fixes.append("Strict-Transport-Security: max-age=31536000; includeSubDomains; preload")
        if "x-content-type-options" in missing_security:
            header_fixes.append("X-Content-Type-Options: nosniff")
        if "x-frame-options" in missing_security:
            header_fixes.append("X-Frame-Options: SAMEORIGIN")
        if "referrer-policy" in missing_security:
            header_fixes.append("Referrer-Policy: strict-origin-when-cross-origin")
        if "permissions-policy" in missing_security:
            header_fixes.append("Permissions-Policy: geolocation=(), camera=(), microphone=()")
        if "content-security-policy" in missing_security:
            header_fixes.append("Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
        if "cross-origin-opener-policy" in missing_security:
            header_fixes.append("Cross-Origin-Opener-Policy: same-origin")

        if header_fixes:
            fixes.append({
                "issue": "Missing security headers",
                "fix": "Add the following headers to your server configuration (Apache .htaccess, Nginx, or WordPress plugin like 'HTTP Headers'):\n\n"
                       + "\n".join(header_fixes),
            })

    # -------------------------------------------------------------------
    # 2. Redirect chains
    # -------------------------------------------------------------------
    chain = fetch_data.get("redirect_chain", [])
    if len(chain) > 1:
        score -= min(len(chain) * 3, 10)
        findings.append({
            "category": "Redirects", "severity": "medium",
            "issue": f"Redirect chain with {len(chain)} hops",
            "detail": " → ".join([r["url"] for r in chain] + [fetch_data.get("final_url", url)]),
        })
        fixes.append({
            "issue": "Redirect chain",
            "fix": f"Update the original URL to point directly to the final destination:\n"
                   f"Original: {chain[0]['url']}\nFinal: {fetch_data.get('final_url', url)}\n"
                   f"Remove intermediate redirects to reduce latency and crawl budget waste.",
        })
    elif len(chain) == 1:
        findings.append({
            "category": "Redirects", "severity": "low",
            "issue": "Single redirect detected",
            "detail": f"{chain[0]['url']} → {fetch_data.get('final_url', url)}",
        })

    # -------------------------------------------------------------------
    # 3. Meta robots / indexability
    # -------------------------------------------------------------------
    meta_robots = page_data.get("meta_robots", "").lower()
    if "noindex" in meta_robots:
        findings.append({
            "category": "Indexability", "severity": "high",
            "issue": "Page has noindex directive — will NOT appear in search results",
            "detail": f"meta robots: {page_data.get('meta_robots', '')}",
        })
        score -= 15

    x_robots = header_lower.get("x-robots-tag", "").lower()
    if "noindex" in x_robots:
        findings.append({
            "category": "Indexability", "severity": "high",
            "issue": "X-Robots-Tag header contains noindex",
            "detail": f"X-Robots-Tag: {headers.get('X-Robots-Tag', '')}",
        })
        score -= 15

    # -------------------------------------------------------------------
    # 4. Canonical
    # -------------------------------------------------------------------
    canonical = page_data.get("canonical", "")
    if not canonical:
        score -= 5
        findings.append({
            "category": "Indexability", "severity": "medium",
            "issue": "No canonical tag found",
            "detail": "Self-referencing canonical tags help prevent duplicate content issues.",
        })
        fixes.append({
            "issue": "Missing canonical tag",
            "fix": f'Add to <head>:\n<link rel="canonical" href="{url}" />',
        })
    elif canonical != url and canonical != fetch_data.get("final_url", url):
        findings.append({
            "category": "Indexability", "severity": "medium",
            "issue": "Canonical URL differs from current URL",
            "detail": f"Page URL: {url}\nCanonical: {canonical}\nSearch engines will consolidate signals to the canonical URL.",
        })

    # -------------------------------------------------------------------
    # 5. Mobile readiness
    # -------------------------------------------------------------------
    viewport = page_data.get("viewport", "")
    if not viewport:
        score -= 10
        findings.append({
            "category": "Mobile", "severity": "high",
            "issue": "No viewport meta tag — page will not render correctly on mobile",
            "detail": "Missing <meta name=\"viewport\"> tag in <head>.",
        })
        fixes.append({
            "issue": "Missing viewport meta tag",
            "fix": 'Add to <head>:\n<meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        })
    elif "width=device-width" not in viewport:
        score -= 5
        findings.append({
            "category": "Mobile", "severity": "medium",
            "issue": "Viewport tag does not include width=device-width",
            "detail": f"Current viewport: {viewport}",
        })

    # -------------------------------------------------------------------
    # 6. Response time
    # -------------------------------------------------------------------
    response_time = fetch_data.get("response_time_ms", 0)
    if response_time > 3000:
        score -= 10
        findings.append({
            "category": "Performance", "severity": "high",
            "issue": f"Slow server response: {response_time}ms (TTFB > 3s)",
            "detail": "Google recommends TTFB under 200ms for good LCP. Consider a CDN, server caching, or upgrading hosting.",
        })
    elif response_time > 1000:
        score -= 5
        findings.append({
            "category": "Performance", "severity": "medium",
            "issue": f"Server response time: {response_time}ms (TTFB > 1s)",
            "detail": "Optimize server-side rendering, enable caching, or use a CDN.",
        })

    # -------------------------------------------------------------------
    # 7. Charset
    # -------------------------------------------------------------------
    charset = page_data.get("charset", "").lower()
    if charset and charset != "utf-8":
        findings.append({
            "category": "Technical", "severity": "low",
            "issue": f"Character encoding is '{charset}' instead of UTF-8",
            "detail": "UTF-8 is the recommended encoding for modern web pages.",
        })
    elif not charset:
        findings.append({
            "category": "Technical", "severity": "low",
            "issue": "No explicit charset declaration found",
            "detail": "Add <meta charset=\"UTF-8\"> as the first element in <head>.",
        })

    # -------------------------------------------------------------------
    # 8. Language attribute
    # -------------------------------------------------------------------
    lang = page_data.get("lang", "")
    if not lang:
        score -= 3
        findings.append({
            "category": "Accessibility", "severity": "medium",
            "issue": "No lang attribute on <html> tag",
            "detail": "Screen readers and search engines use this to determine content language.",
        })
        fixes.append({
            "issue": "Missing lang attribute",
            "fix": 'Add to your <html> tag:\n<html lang="en">  (or the appropriate language code)',
        })

    return {
        "analyzer": "technical",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
    }


def analyze_robots_and_sitemaps(robots_raw: str, robots_data: dict,
                                 sitemap_urls: list, base_url: str) -> dict:
    """Site-level analysis of robots.txt and sitemaps."""
    findings = []
    fixes = []
    score = 100

    # Robots.txt existence
    if not robots_raw:
        score -= 10
        findings.append({
            "category": "Crawlability", "severity": "high",
            "issue": "No robots.txt file found",
            "detail": f"Checked {base_url}/robots.txt — returned empty or non-200.",
        })
        fixes.append({
            "issue": "Missing robots.txt",
            "fix": f"Create a robots.txt file at the root of your domain:\n\n"
                   f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml",
        })

    # Sitemap validation
    declared_sitemaps = robots_data.get("sitemaps", [])
    if not declared_sitemaps and not sitemap_urls:
        score -= 35
        findings.append({
            "category": "Crawlability", "severity": "critical",
            "issue": "No XML sitemap found",
            "detail": "No sitemap declared in robots.txt and no sitemap found at common paths (/sitemap.xml, /sitemap_index.xml, /wp-sitemap.xml).",
        })
        fixes.append({
            "issue": "Missing XML sitemap",
            "fix": "Generate and submit an XML sitemap:\n"
                   "1. Use your CMS sitemap feature (Yoast SEO, Rank Math, etc.) or an online generator\n"
                   "2. Place it at /sitemap.xml\n"
                   "3. Declare it in robots.txt: Sitemap: {base_url}/sitemap.xml\n"
                   "4. Submit it in Google Search Console under Sitemaps",
        })
    elif declared_sitemaps and not sitemap_urls:
        score -= 45
        findings.append({
            "category": "Crawlability", "severity": "critical",
            "issue": "Declared sitemap(s) are broken (HTTP 404 or invalid XML)",
            "detail": "robots.txt declares: " + ", ".join(declared_sitemaps) + " — but none returned valid content.",
        })
        fixes.append({
            "issue": "Broken sitemap declaration",
            "fix": "The sitemap URL(s) in robots.txt return 404. Either:\n"
                   "1. Regenerate the sitemap and ensure it's accessible at the declared URL\n"
                   "2. Update robots.txt to point to the correct sitemap URL",
        })

    # AI crawler access
    for bot_name, bot_info in AI_CRAWLERS.items():
        blocked = is_bot_blocked(robots_data, bot_name)
        if blocked and bot_info["search"]:
            score -= 10
            findings.append({
                "category": "AI Search", "severity": "high",
                "issue": f"AI search bot '{bot_name}' is BLOCKED in robots.txt",
                "detail": f"{bot_name} is used for {bot_info['purpose']}. Blocking it prevents your content from appearing in AI-powered search results.",
            })
            fixes.append({
                "issue": f"{bot_name} blocked",
                "fix": f"Allow {bot_name} in robots.txt:\n\nUser-agent: {bot_name}\nAllow: /",
            })
        elif blocked and not bot_info["search"]:
            findings.append({
                "category": "AI Training", "severity": "info",
                "issue": f"Training bot '{bot_name}' is blocked (OK for most sites)",
                "detail": f"{bot_name}: {bot_info['purpose']}. Blocking training-only bots is common and does not affect search visibility.",
            })

    return {
        "analyzer": "robots_sitemaps",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
    }
