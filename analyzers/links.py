"""agy-seo: Link analysis — internal/external links, broken links, anchor text."""

from utils import clamp_score, check_url_status, normalize_url


def analyze_links(page_data: dict, all_pages: dict = None) -> dict:
    """Analyze internal and external links for a single page."""
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

    return {
        "analyzer": "links",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
        "internal_count": len(internal),
        "external_count": len(external),
        "broken_count": len(broken_external),
        "empty_anchor_count": total_empty,
    }
