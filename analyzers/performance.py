"""agy-seo: Performance analyzer — Core Web Vitals, resource hints, page weight."""

import re
from utils import clamp_score


def analyze_performance(page_data: dict, fetch_data: dict) -> dict:
    """Analyze page performance and Core Web Vitals risk factors."""
    findings = []
    fixes = []
    score = 100

    url = page_data["url"]
    scripts = page_data.get("scripts", [])
    stylesheets = page_data.get("stylesheets", [])
    images = page_data.get("images", [])
    preloads = page_data.get("preload_hints", [])
    html = fetch_data.get("html", "")
    html_size = len(html.encode("utf-8", errors="replace"))
    response_time = fetch_data.get("response_time_ms", 0)

    # -------------------------------------------------------------------
    # 1. TTFB (Time to First Byte)
    # -------------------------------------------------------------------
    if response_time > 3000:
        score -= 25
        findings.append({"category": "TTFB", "severity": "critical",
            "issue": f"Very slow TTFB: {response_time}ms",
            "detail": "Google recommends TTFB < 200ms for good LCP. Your server takes over 3 seconds to respond."})
        fixes.append({"issue": "Slow TTFB",
            "fix": "Reduce Time to First Byte:\n"
                   "1. Enable server-side caching (Redis, Memcached, or object caching)\n"
                   "2. Use a CDN (Cloudflare, Fastly, or your hosting CDN)\n"
                   "3. Optimize database queries and server-side logic\n"
                   "4. Consider upgrading to a faster hosting provider\n"
                   "5. Enable HTTP/2 or HTTP/3 on your server"})
    elif response_time > 1500:
        score -= 15
        findings.append({"category": "TTFB", "severity": "high",
            "issue": f"High server response latency (TTFB: {response_time}ms)",
            "detail": "TTFB exceeds 1.5s, severely delaying browser First Contentful Paint."})
    elif response_time > 800:
        score -= 10
        findings.append({"category": "TTFB", "severity": "medium",
            "issue": f"Suboptimal TTFB: {response_time}ms",
            "detail": "TTFB should be under 200ms for optimal Core Web Vitals."})

    # -------------------------------------------------------------------
    # 2. Render-blocking resources
    # -------------------------------------------------------------------
    blocking_scripts = [s for s in scripts if s.get("src") and not s.get("async") and not s.get("defer") and s.get("type", "") != "module"]
    if blocking_scripts:
        score -= min(len(blocking_scripts) * 4, 20)
        findings.append({"category": "Render Blocking", "severity": "high",
            "issue": f"{len(blocking_scripts)} render-blocking script(s) found",
            "detail": "Scripts without async/defer attributes block HTML parsing and delay rendering.\n"
                      + "\n".join(f"  - {s['src']}" for s in blocking_scripts[:10])})
        fixes.append({"issue": "Render-blocking scripts",
            "fix": "Add async or defer attribute to non-critical scripts:\n\n" +
                   "\n".join(f'Change:\n  <script src="{s["src"]}"></script>\nTo:\n  <script src="{s["src"]}" defer></script>\n'
                             for s in blocking_scripts[:5])})

    # CSS blocking
    blocking_css = [s for s in stylesheets if not s.get("media") or s.get("media") == "all"]
    if len(blocking_css) > 3:
        score -= min((len(blocking_css) - 3) * 3, 15)
        findings.append({"category": "Render Blocking", "severity": "medium",
            "issue": f"{len(blocking_css)} render-blocking CSS files",
            "detail": "Multiple CSS files block initial render. Consider inlining critical CSS.\n"
                      + "\n".join(f"  - {s['href']}" for s in blocking_css[:5] if s.get("href"))})
        fixes.append({"issue": "Multiple blocking CSS files",
            "fix": "Optimize CSS delivery:\n"
                   "1. Inline critical (above-the-fold) CSS directly in <head>\n"
                   "2. Load non-critical CSS asynchronously:\n"
                   '   <link rel="preload" href="style.css" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">\n'
                   "3. Combine multiple CSS files into fewer files\n"
                   "4. Remove unused CSS (use PurgeCSS or similar)"})

    # -------------------------------------------------------------------
    # 3. Image optimization (CLS and LCP risks)
    # -------------------------------------------------------------------
    def _clean_src(s: str) -> str:
        if not s:
            return ""
        if s.startswith("data:"):
            return "[inline base64 image data]"
        return s

    images_no_dimensions = [img for img in images if img.get("src") and (not img.get("width") or not img.get("height"))]
    if images_no_dimensions:
        score -= min(len(images_no_dimensions) * 2, 10)
        findings.append({"category": "CLS", "severity": "high",
            "issue": f"{len(images_no_dimensions)} image(s) missing width/height attributes",
            "detail": "Images without explicit dimensions cause layout shifts (CLS).\n"
                      + "\n".join(f"  - {_clean_src(img['src'])}" for img in images_no_dimensions[:5])})
        sample_fix_urls = [img['src'] for img in images_no_dimensions if not img.get('src', '').startswith('data:')]
        if not sample_fix_urls:
            sample_fix_urls = ["image.webp"]
        fixes.append({"issue": "Images without dimensions",
            "fix": "Add width and height attributes to all <img> tags:\n\n" +
                   "\n".join(f'<img src="{u}" width="YOUR_WIDTH" height="YOUR_HEIGHT" alt="..." />'
                             for u in sample_fix_urls[:3])})

    # Check for modern formats
    if images:
        non_modern = [img for img in images if img.get("src") and
                      any(img["src"].lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp"))
                      and not img.get("srcset")]
        if non_modern:
            findings.append({"category": "Image Optimization", "severity": "medium",
                "issue": f"{len(non_modern)} image(s) not using modern formats (WebP/AVIF)",
                "detail": "WebP is ~25-35% smaller than JPEG. AVIF is ~50% smaller.\n"
                          + "\n".join(f"  - {_clean_src(img['src'])}" for img in non_modern[:5])})
            fixes.append({"issue": "Legacy image formats",
                "fix": "Convert images to modern formats:\n"
                       "1. Use WebP for broad compatibility\n"
                       "2. Use AVIF for maximum compression (with WebP fallback)\n"
                       "3. Implement with <picture> tag:\n\n"
                       "<picture>\n"
                       '  <source srcset="image.avif" type="image/avif">\n'
                       '  <source srcset="image.webp" type="image/webp">\n'
                       '  <img src="image.jpg" alt="description" width="800" height="600">\n'
                       "</picture>"})

    # Lazy loading on above-the-fold images
    first_images = images[:2]
    for img in first_images:
        if img.get("loading") == "lazy":
            score -= 3
            findings.append({"category": "LCP", "severity": "medium",
                "issue": f"Above-the-fold image has loading=\"lazy\" — harms LCP",
                "detail": f"Image: {img.get('src', '')}\nLazy-loaded images above the fold delay LCP."})
            fixes.append({"issue": "Lazy-loaded hero image",
                "fix": f'Remove loading="lazy" from above-the-fold images and add fetchpriority:\n'
                       f'<img src="{img.get("src", "")}" fetchpriority="high" alt="{img.get("alt", "")}" />'})

    # -------------------------------------------------------------------
    # 4. Resource hints
    # -------------------------------------------------------------------
    preload_types = set(p.get("rel", "") for p in preloads)
    if "preconnect" not in " ".join(preload_types):
        findings.append({"category": "Resource Hints", "severity": "low",
            "issue": "No preconnect hints found",
            "detail": "Preconnect reduces DNS + TLS time for third-party origins."})
        # Check for common third-party domains in scripts
        third_party_domains = set()
        for s in scripts:
            src = s.get("src", "")
            if src and "://" in src:
                domain = src.split("://")[1].split("/")[0]
                if domain not in page_data["url"]:
                    third_party_domains.add(domain)
        if third_party_domains:
            fixes.append({"issue": "Missing preconnect",
                "fix": "Add preconnect for third-party domains in <head>:\n\n" +
                       "\n".join(f'<link rel="preconnect" href="https://{d}" crossorigin>'
                                 for d in list(third_party_domains)[:5])})

    # -------------------------------------------------------------------
    # 5. Page weight
    # -------------------------------------------------------------------
    if html_size > 500_000:  # 500KB
        score -= 5
        findings.append({"category": "Page Weight", "severity": "medium",
            "issue": f"Large HTML document ({html_size / 1024:.0f}KB)",
            "detail": "HTML documents over 500KB are slower to parse and may indicate inline resources or excessive DOM."})

    # Inline script/style size
    inline_scripts = [s for s in scripts if s.get("inline")]
    total_js_files = len([s for s in scripts if s.get("src")])
    total_css_files = len(stylesheets)

    if total_js_files > 15:
        score -= 5
        findings.append({"category": "Page Weight", "severity": "medium",
            "issue": f"Too many JavaScript files ({total_js_files})",
            "detail": "Each file requires a separate HTTP request. Consider bundling or lazy-loading."})

    if total_css_files > 8:
        score -= 3
        findings.append({"category": "Page Weight", "severity": "low",
            "issue": f"Many CSS files ({total_css_files})",
            "detail": "Consider combining CSS files to reduce HTTP requests."})

    # -------------------------------------------------------------------
    # 6. Fetchpriority hint on LCP candidate
    # -------------------------------------------------------------------
    lcp_candidates = [img for img in images[:3] if img.get("src")]
    has_fetchpriority = any(img.get("fetchpriority") == "high" for img in lcp_candidates)
    if lcp_candidates and not has_fetchpriority:
        findings.append({"category": "LCP", "severity": "medium",
            "issue": "No fetchpriority=\"high\" on likely LCP image",
            "detail": "Adding fetchpriority=\"high\" to your hero/banner image can improve LCP by 5-10%."})
        if lcp_candidates:
            fixes.append({"issue": "Missing fetchpriority on LCP image",
                "fix": f'Add fetchpriority="high" to your hero image:\n'
                       f'<img src="{lcp_candidates[0]["src"]}" fetchpriority="high" />'})

    # -------------------------------------------------------------------
    # 7. Speculation Rules API
    # -------------------------------------------------------------------
    has_speculation = 'type="speculationrules"' in html
    if not has_speculation:
        findings.append({"category": "Navigation", "severity": "low",
            "issue": "No Speculation Rules API found",
            "detail": "Speculation Rules enable instant page navigations by prefetching/prerendering likely next pages."})
        fixes.append({"issue": "Missing Speculation Rules",
            "fix": 'Add Speculation Rules for instant navigations:\n\n'
                   '<script type="speculationrules">\n'
                   '{\n'
                   '  "prerender": [{\n'
                   '    "where": { "href_matches": "/*" },\n'
                   '    "eagerness": "moderate"\n'
                   '  }]\n'
                   '}\n'
                   '</script>'})

    return {
        "analyzer": "performance",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
        "metrics": {
            "ttfb_ms": response_time,
            "html_size_kb": round(html_size / 1024),
            "js_files": total_js_files,
            "css_files": total_css_files,
            "total_images": len(images),
            "images_no_dimensions": len(images_no_dimensions),
        }
    }
