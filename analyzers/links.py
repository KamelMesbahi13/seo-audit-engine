"""agy-seo: Link Equity Intelligence — Internal PageRank, click-depth, anchor dilution.

Advanced link graph analysis including:
- Internal PageRank approximation via iterative power method
- Click-depth (crawl-depth) calculation from homepage
- Anchor text dilution detection (over-optimized or repetitive anchors)
- Link equity flow visualization data
"""

import re
from collections import defaultdict
from urllib.parse import urlparse
from utils import clamp_score, check_url_status, normalize_url, is_same_domain


def _compute_internal_pagerank(all_pages: dict, damping: float = 0.85, iterations: int = 20) -> dict:
    """Compute simplified internal PageRank scores using the power iteration method.
    
    Args:
        all_pages: Dict of {norm_url: page_info} from crawler
        damping: Damping factor (default 0.85 per original PageRank)
        iterations: Number of iterations for convergence
    
    Returns:
        Dict of {url: pagerank_score} normalized to 0-100
    """
    # Build adjacency list
    pages = {}
    outlinks = defaultdict(set)
    inlinks = defaultdict(set)
    
    for norm_url, page_info in all_pages.items():
        if not page_info.get("parsed"):
            continue
        pages[norm_url] = True
        internal_links = page_info["parsed"].get("links", {}).get("internal", [])
        for link in internal_links:
            target = normalize_url(link["href"])
            if target in all_pages:
                outlinks[norm_url].add(target)
                inlinks[target].add(norm_url)
    
    if not pages:
        return {}
    
    n = len(pages)
    page_list = list(pages.keys())
    
    # Initialize uniform PageRank
    pr = {url: 1.0 / n for url in page_list}
    
    # Power iteration
    for _ in range(iterations):
        new_pr = {}
        for url in page_list:
            rank_sum = 0.0
            for src in inlinks.get(url, set()):
                out_count = len(outlinks.get(src, set()))
                if out_count > 0:
                    rank_sum += pr.get(src, 0) / out_count
            new_pr[url] = (1 - damping) / n + damping * rank_sum
        pr = new_pr
    
    # Normalize to 0-100 scale
    if pr:
        max_pr = max(pr.values())
        min_pr = min(pr.values())
        range_pr = max_pr - min_pr if max_pr != min_pr else 1
        pr_normalized = {url: round(((val - min_pr) / range_pr) * 100, 1) for url, val in pr.items()}
    else:
        pr_normalized = {}
    
    return pr_normalized


def _compute_click_depth(all_pages: dict, base_url: str) -> dict:
    """Compute click-depth (minimum clicks from homepage) for each page using BFS.
    
    Returns:
        Dict of {url: depth} where depth is minimum clicks from homepage
    """
    from collections import deque
    
    homepage = normalize_url(base_url)
    
    # Build adjacency
    adjacency = defaultdict(set)
    for norm_url, page_info in all_pages.items():
        if not page_info.get("parsed"):
            continue
        internal_links = page_info["parsed"].get("links", {}).get("internal", [])
        for link in internal_links:
            target = normalize_url(link["href"])
            if target in all_pages:
                adjacency[norm_url].add(target)
    
    # BFS from homepage
    depths = {homepage: 0}
    queue = deque([homepage])
    
    while queue:
        current = queue.popleft()
        current_depth = depths[current]
        
        for neighbor in adjacency.get(current, set()):
            if neighbor not in depths:
                depths[neighbor] = current_depth + 1
                queue.append(neighbor)
    
    # Mark unreachable pages
    for norm_url in all_pages:
        if norm_url not in depths:
            depths[norm_url] = -1  # Unreachable from homepage
    
    return depths


def _analyze_anchor_text_dilution(all_pages: dict) -> dict:
    """Analyze anchor text distribution across the site for dilution/over-optimization.
    
    Returns analysis of:
    - Over-optimized anchors (same text used excessively)
    - Under-descriptive anchors (generic text)
    - Anchor text diversity per target page
    """
    # Collect all anchor texts pointing to each internal URL
    target_anchors = defaultdict(list)
    
    for norm_url, page_info in all_pages.items():
        if not page_info.get("parsed"):
            continue
        internal_links = page_info["parsed"].get("links", {}).get("internal", [])
        for link in internal_links:
            target = normalize_url(link["href"])
            text = link.get("text", "").strip()
            if text and target in all_pages:
                target_anchors[target].append({
                    "text": text,
                    "source": norm_url,
                })
    
    issues = []
    
    for target_url, anchors in target_anchors.items():
        if len(anchors) < 3:
            continue
        
        # Count anchor text frequency
        text_counts = defaultdict(int)
        for a in anchors:
            text_counts[a["text"].lower()] += 1
        
        total = len(anchors)
        
        # Over-optimization: single anchor text used >60% of the time
        for text, count in text_counts.items():
            ratio = count / total
            if ratio > 0.60 and count >= 3:
                issues.append({
                    "type": "over_optimized",
                    "target": target_url,
                    "anchor_text": text,
                    "count": count,
                    "total": total,
                    "ratio": round(ratio * 100),
                })
        
        # Low diversity: fewer than 3 unique anchor texts for a page with 5+ inbound links
        unique_count = len(text_counts)
        if total >= 5 and unique_count < 3:
            issues.append({
                "type": "low_diversity",
                "target": target_url,
                "unique_anchors": unique_count,
                "total_links": total,
            })
    
    return {
        "issues": issues,
        "pages_analyzed": len(target_anchors),
    }


def analyze_links(page_data: dict, all_pages: dict = None) -> dict:
    """Analyze internal and external links for a single page.
    
    Enhanced with:
    - Internal PageRank scoring
    - Click-depth analysis
    - Anchor text dilution detection
    """
    findings = []
    fixes = []
    score = 100

    url = page_data["url"]
    links = page_data.get("links", {})
    internal = links.get("internal", [])
    external = links.get("external", [])

    # -------------------------------------------------------------------
    # 1. Internal link count
    # -------------------------------------------------------------------
    if len(internal) == 0:
        score -= 25
        findings.append({"category": "Internal Links", "severity": "critical",
            "issue": "Zero internal links found (orphan/dead-end page)",
            "detail": "Pages without internal links are dead-ends for both users and search engine crawlers."})
        fixes.append({"issue": "No internal links",
            "fix": "Add contextual internal links:\n"
                   "1. Link to related service/product pages from content sections\n"
                   "2. Add a related posts/pages section at the bottom\n"
                   "3. Ensure navigation menu links to key pages\n"
                   "4. Add breadcrumb navigation"})
    elif len(internal) < 3:
        score -= 5
        findings.append({"category": "Internal Links", "severity": "medium",
            "issue": f"Very few internal links ({len(internal)})",
            "detail": "Pages should have at least 3-5 internal links to spread link equity and aid navigation."})

    # -------------------------------------------------------------------
    # 2. External link count
    # -------------------------------------------------------------------
    if len(external) == 0 and page_data.get("word_count", 0) > 500:
        findings.append({"category": "External Links", "severity": "low",
            "issue": "No external links on content-rich page",
            "detail": "Linking to authoritative sources can improve content trustworthiness (E-E-A-T)."})

    # -------------------------------------------------------------------
    # 3. Empty anchor text
    # -------------------------------------------------------------------
    empty_anchors_internal = [l for l in internal if not l.get("text", "").strip()]
    empty_anchors_external = [l for l in external if not l.get("text", "").strip()]
    total_empty = len(empty_anchors_internal) + len(empty_anchors_external)

    if total_empty > 0:
        score -= min(total_empty * 2, 8)
        findings.append({"category": "Anchor Text", "severity": "medium",
            "issue": f"{total_empty} link(s) with empty anchor text",
            "detail": "Links without visible text (empty <a> tags or image-only links without alt text) provide no context.\n" +
                      "\n".join(f"  - {l['href']}" for l in (empty_anchors_internal + empty_anchors_external)[:5])})
        fixes.append({"issue": "Empty anchor text",
            "fix": "Add descriptive anchor text to all links:\n"
                   "[INCORRECT] <a href=\"/services\"></a>\n"
                   "[INCORRECT] <a href=\"/services\"><img src=\"icon.png\" /></a>\n"
                   "[CORRECT] <a href=\"/services\">Our Services</a>\n"
                   "[CORRECT] <a href=\"/services\"><img src=\"icon.png\" alt=\"Our Services\" /></a>"})

    # -------------------------------------------------------------------
    # 4. Generic anchor text
    # -------------------------------------------------------------------
    generic_patterns = ["click here", "read more", "learn more", "here", "this", "link",
                        "more", "continue", "اقرأ المزيد", "المزيد"]
    generic_anchors = []
    for l in internal + external:
        text = l.get("text", "").strip().lower()
        if text in generic_patterns:
            generic_anchors.append({"href": l["href"], "text": text})

    if generic_anchors:
        score -= min(len(generic_anchors) * 1, 5)
        findings.append({"category": "Anchor Text", "severity": "medium",
            "issue": f"{len(generic_anchors)} link(s) with generic anchor text",
            "detail": "Generic text like 'click here' or 'read more' wastes link context signals.\n" +
                      "\n".join(f'  - "{ga["text"]}" → {ga["href"]}' for ga in generic_anchors[:5])})
        fixes.append({"issue": "Generic anchor text",
            "fix": "Use descriptive anchor text that tells users and search engines what the linked page is about:\n"
                   "[INCORRECT] <a href=\"/dental-implants\">Click here</a>\n"
                   "[CORRECT] <a href=\"/dental-implants\">dental implant procedures</a>\n\n"
                   "[INCORRECT] <a href=\"/blog/seo-guide\">Read more</a>\n"
                   "[CORRECT] <a href=\"/blog/seo-guide\">complete SEO guide for beginners</a>"})

    # -------------------------------------------------------------------
    # 5. Nofollow misuse on internal links
    # -------------------------------------------------------------------
    nofollow_internal = [l for l in internal if "nofollow" in " ".join(l.get("rel", []))]
    if nofollow_internal:
        score -= min(len(nofollow_internal) * 2, 6)
        findings.append({"category": "Link Equity", "severity": "medium",
            "issue": f"{len(nofollow_internal)} internal link(s) have rel=\"nofollow\"",
            "detail": "Nofollowing internal links wastes PageRank and is almost never appropriate.\n" +
                      "\n".join(f"  - {l['href']} ({l.get('text', '')})" for l in nofollow_internal[:5])})
        fixes.append({"issue": "Nofollow on internal links",
            "fix": "Remove rel=\"nofollow\" from internal links. Internal links should always pass PageRank:\n" +
                   "\n".join(f'  Change: <a href="{l["href"]}" rel="nofollow">{l.get("text", "")}</a>\n'
                             f'  To: <a href="{l["href"]}">{l.get("text", "")}</a>'
                             for l in nofollow_internal[:3])})

    # -------------------------------------------------------------------
    # 6. Broken external links (spot check up to 10)
    # -------------------------------------------------------------------
    broken_external = []
    checked = 0
    for l in external[:15]:
        href = l.get("href", "")
        if not href or not href.startswith("http"):
            continue
        status = check_url_status(href)
        if status >= 400 or status == 0:
            broken_external.append({"href": href, "text": l.get("text", ""), "status": status})
        checked += 1
        if checked >= 10:
            break

    if broken_external:
        score -= min(len(broken_external) * 3, 10)
        findings.append({"category": "Broken Links", "severity": "high",
            "issue": f"{len(broken_external)} broken external link(s) found",
            "detail": "Broken outbound links harm user experience and trust signals.\n" +
                      "\n".join(f"  - [{l['status']}] {l['href']} (anchor: \"{l['text']}\")"
                                for l in broken_external)})
        fixes.append({"issue": "Broken external links",
            "fix": "Fix or remove broken external links:\n" +
                   "\n".join(f"  - Remove or update: {l['href']} (returns HTTP {l['status']})"
                             for l in broken_external)})

    # -------------------------------------------------------------------
    # 7. Orphan page detection (site-wide, if all_pages provided)
    # -------------------------------------------------------------------
    if all_pages:
        all_internal_targets = set()
        for norm_url, page_info in all_pages.items():
            if page_info.get("parsed"):
                page_links = page_info["parsed"].get("links", {}).get("internal", [])
                for l in page_links:
                    all_internal_targets.add(normalize_url(l["href"]))

        norm_current = normalize_url(url)
        if norm_current not in all_internal_targets and len(all_pages) > 1:
            score -= 5
            findings.append({"category": "Orphan Page", "severity": "high",
                "issue": "This page is an orphan — no other crawled page links to it",
                "detail": "Orphan pages are hard for search engines to discover and receive no internal PageRank."})
            fixes.append({"issue": "Orphan page",
                "fix": "Add internal links to this page from at least 2-3 related pages:\n"
                       "1. Add it to relevant navigation menus\n"
                       "2. Link from related content pages using descriptive anchor text\n"
                       "3. Include in a sitemap and footer links"})

    # -------------------------------------------------------------------
    # 8. NEW: Internal PageRank Analysis (site-wide)
    # -------------------------------------------------------------------
    pagerank_data = {}
    click_depth_data = {}
    anchor_dilution_data = {}
    
    if all_pages and len(all_pages) >= 2:
        # Compute PageRank
        pagerank_data = _compute_internal_pagerank(all_pages)
        
        # Check this page's PageRank
        norm_current = normalize_url(url)
        page_pr = pagerank_data.get(norm_current, 0)
        
        if page_pr < 10 and len(all_pages) > 3:
            score -= 5
            findings.append({
                "category": "Link Equity",
                "severity": "high",
                "issue": f"Low internal PageRank ({page_pr:.1f}/100) — page receives minimal link equity",
                "detail": "This page has very low internal PageRank relative to other site pages. "
                          "It receives few inbound internal links and may be hard for search engines to prioritize.",
            })
            fixes.append({
                "issue": "Low internal PageRank",
                "fix": "Boost this page's internal PageRank:\n"
                       "1. Add links from high-authority pages (homepage, main navigation)\n"
                       "2. Include in site-wide footer or sidebar links\n"
                       "3. Create contextual cross-links from related content\n"
                       "4. Add this page to breadcrumb navigation\n"
                       "5. Feature it in 'Related Pages' sections on high-traffic pages",
            })
        
        # Compute click-depth
        base_url = page_data.get("url", "")
        parsed = urlparse(base_url)
        homepage_url = f"{parsed.scheme}://{parsed.netloc}"
        click_depth_data = _compute_click_depth(all_pages, homepage_url)
        
        page_depth = click_depth_data.get(norm_current, -1)
        if page_depth > 3:
            score -= 5
            findings.append({
                "category": "Click Depth",
                "severity": "medium",
                "issue": f"Deep page — {page_depth} clicks from homepage",
                "detail": f"This page is {page_depth} clicks away from the homepage. "
                          "Pages deeper than 3 clicks receive less crawl priority and link equity.",
            })
            fixes.append({
                "issue": "Deep click-depth",
                "fix": f"Reduce click-depth from {page_depth} to 3 or fewer:\n"
                       "1. Add a direct link from a main category page\n"
                       "2. Include in a flat navigation structure\n"
                       "3. Add to a hub page that's linked from the homepage\n"
                       "4. Use breadcrumbs to create shorter link paths",
            })
        elif page_depth == -1 and len(all_pages) > 1:
            score -= 8
            findings.append({
                "category": "Click Depth",
                "severity": "critical",
                "issue": "Page is unreachable from homepage via internal links",
                "detail": "No internal link path exists from the homepage to this page. "
                          "Search engines may never discover or adequately crawl it.",
            })
            fixes.append({
                "issue": "Unreachable page",
                "fix": "Create an internal link path from the homepage:\n"
                       "1. Add to main navigation or sidebar\n"
                       "2. Link from a category page that IS reachable\n"
                       "3. Include in site-wide footer links\n"
                       "4. Add to XML sitemap as a safety net",
            })
        
        # Anchor text dilution analysis
        anchor_dilution_data = _analyze_anchor_text_dilution(all_pages)
        
        for issue in anchor_dilution_data.get("issues", []):
            target = issue.get("target", "")
            if normalize_url(url) != target:
                continue  # Only report for current page
            
            if issue["type"] == "over_optimized":
                score -= 3
                findings.append({
                    "category": "Anchor Text Dilution",
                    "severity": "medium",
                    "issue": f"Over-optimized anchor text: '{issue['anchor_text']}' used in {issue['ratio']}% of inbound links",
                    "detail": f"The anchor text '{issue['anchor_text']}' is used {issue['count']} out of {issue['total']} times "
                              f"({issue['ratio']}%) when linking to this page. Over-optimization can trigger algorithmic penalties.",
                })
                fixes.append({
                    "issue": f"Anchor dilution: '{issue['anchor_text']}'",
                    "fix": f"Diversify anchor text for this page:\n"
                           f"Current: {issue['ratio']}% of links use '{issue['anchor_text']}'\n"
                           f"Target: No single anchor text should exceed 30-40% of total links.\n\n"
                           "Variations to use:\n"
                           "- Brand name + keyword\n"
                           "- Long-tail keyword variations\n"
                           "- Natural phrases describing the page content\n"
                           "- Partial-match keywords",
                })
            elif issue["type"] == "low_diversity":
                findings.append({
                    "category": "Anchor Text Dilution",
                    "severity": "low",
                    "issue": f"Low anchor text diversity: only {issue['unique_anchors']} unique texts across {issue['total_links']} inbound links",
                    "detail": "Using more diverse anchor text helps search engines better understand what this page is about.",
                })

    return {
        "analyzer": "links",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
        "internal_count": len(internal),
        "external_count": len(external),
        "broken_count": len(broken_external),
        "empty_anchor_count": total_empty,
        # NEW: Link equity intelligence
        "pagerank": pagerank_data,
        "click_depth": click_depth_data,
        "anchor_dilution": anchor_dilution_data,
    }
