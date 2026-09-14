"""agy-seo: On-page SEO analyzer — title, meta description, headings, OG, Twitter, hreflang."""

import re
from utils import clamp_score


def analyze_onpage(page_data: dict) -> dict:
    """Analyze on-page SEO elements for a single page."""
    findings = []
    fixes = []
    score = 100
    url = page_data["url"]

    # -------------------------------------------------------------------
    # 1. Title tag
    # -------------------------------------------------------------------
    title = page_data.get("title", "")
    title_len = len(title)

    if not title:
        score -= 25
        findings.append({"category": "Title", "severity": "critical",
            "issue": "Missing title tag", "detail": "The page has no <title> element."})
        fixes.append({"issue": "Missing title tag",
            "fix": f'Add a descriptive title tag to <head>:\n<title>Your Primary Keyword | Brand Name</title>'})
    else:
        if title_len < 30:
            score -= 12
            findings.append({"category": "Title", "severity": "high",
                "issue": f"Title tag too short ({title_len} chars)",
                "detail": f'Current: "{title}"\nGoogle displays up to 55-60 characters. You are wasting {60 - title_len} characters of SERP real estate.'})
            fixes.append({"issue": "Short title tag",
                "fix": f'Expand your title to 50-60 characters to maximize SERP visibility.\nCurrent ({title_len} chars): "{title}"\nRecommended format: "Primary Keyword — Secondary Keyword | Brand Name"'})
        elif title_len > 65:
            score -= 5
            findings.append({"category": "Title", "severity": "medium",
                "issue": f"Title tag may be truncated ({title_len} chars)",
                "detail": f'Current: "{title}"\nGoogle truncates titles around 55-60 characters. The end of your title may not be visible.'})

        if title == title.lower() and len(title) > 10:
            score -= 4
            findings.append({"category": "Title", "severity": "medium",
                "issue": "Title tag is entirely lowercase",
                "detail": f'"{title}" — Properly capitalized titles have higher CTR in search results.'})
            fixes.append({"issue": "Lowercase title",
                "fix": f'Capitalize your title properly:\nCurrent: "{title}"\nRecommended: "{title.title()}"'})

    # -------------------------------------------------------------------
    # 2. Meta description
    # -------------------------------------------------------------------
    meta_desc = page_data.get("meta_description", "")
    desc_len = len(meta_desc)

    if not meta_desc:
        score -= 20
        findings.append({"category": "Meta Description", "severity": "high",
            "issue": "Missing meta description", "detail": "Google may auto-generate a snippet from page content, which may not represent your page well."})
        fixes.append({"issue": "Missing meta description",
            "fix": f'Add a compelling meta description (120-155 chars) to <head>:\n<meta name="description" content="Your compelling description with target keywords and a call-to-action." />'})
    else:
        if desc_len < 70:
            score -= 8
            findings.append({"category": "Meta Description", "severity": "medium",
                "issue": f"Meta description too short ({desc_len} chars)",
                "detail": f'"{meta_desc}"\nRecommended: 120-155 characters for optimal SERP display.'})
        elif desc_len > 160:
            score -= 3
            findings.append({"category": "Meta Description", "severity": "low",
                "issue": f"Meta description may be truncated ({desc_len} chars)",
                "detail": f'Google typically displays up to 155 characters.'})

    # -------------------------------------------------------------------
    # 3. Heading hierarchy
    # -------------------------------------------------------------------
    h1s = page_data.get("h1", [])
    h2s = page_data.get("h2", [])
    h3s = page_data.get("h3", [])

    if not h1s:
        score -= 25
        findings.append({"category": "Headings", "severity": "critical",
            "issue": "No H1 tag found", "detail": "Every page should have exactly one H1 that describes the main topic."})
        fixes.append({"issue": "Missing H1",
            "fix": f'Add a single <h1> tag containing your primary keyword:\n<h1>Your Main Topic Keyword</h1>'})
    elif len(h1s) > 1:
        score -= 5
        findings.append({"category": "Headings", "severity": "medium",
            "issue": f"Multiple H1 tags found ({len(h1s)})",
            "detail": "H1 tags:\n" + "\n".join(f'  - "{h}"' for h in h1s) + "\n\nBest practice: Use exactly one H1 per page."})
        fixes.append({"issue": "Multiple H1 tags",
            "fix": f'Keep only the most descriptive H1 and convert others to H2:\n'
                   f'Keep: <h1>{h1s[0]}</h1>\n'
                   f'Change to H2: ' + ', '.join(f'"{h}"' for h in h1s[1:])})
    else:
        # Check for concatenated words in H1 (common animation bug)
        h1_text = h1s[0]
        concat_pattern = re.findall(r'[a-z][A-Z]', h1_text)
        if concat_pattern:
            score -= 3
            findings.append({"category": "Headings", "severity": "medium",
                "issue": "H1 contains concatenated words (likely CSS animation bug)",
                "detail": f'H1: "{h1_text}"\nWords appear glued together without spaces, likely from nested <span> tags in an animation.'})
            fixes.append({"issue": "H1 word concatenation",
                "fix": f'Add spaces between nested animation spans in your H1:\nCurrent text: "{h1_text}"\nEnsure proper spacing between <span> elements.'})

    if not h2s:
        score -= 5
        findings.append({"category": "Headings", "severity": "medium",
            "issue": "No H2 tags found", "detail": "H2 tags help search engines understand page structure and subtopics."})

    # Check for non-content headings (form status, error messages)
    for heading_list, tag_name in [(h2s, "H2"), (h3s, "H3")]:
        for h in heading_list:
            h_lower = h.lower().strip()
            if any(pattern in h_lower for pattern in [
                "error", "thank you", "success", "loading", "please wait",
                "حدث خطأ", "تم استلام", "شكرا", "merci"
            ]):
                score -= 2
                findings.append({"category": "Headings", "severity": "medium",
                    "issue": f"Form/UI status message coded as <{tag_name.lower()}>",
                    "detail": f'<{tag_name.lower()}>{h}</{tag_name.lower()}> — Form status messages should not be semantic headings.'})
                fixes.append({"issue": f"UI message as {tag_name}",
                    "fix": f'Replace:\n  <{tag_name.lower()}>{h}</{tag_name.lower()}>\nWith:\n  <div class="form-status" role="status" aria-live="polite">{h}</div>'})

    # -------------------------------------------------------------------
    # 4. Open Graph
    # -------------------------------------------------------------------
    og = page_data.get("open_graph", {})
    if not og:
        score -= 5
        findings.append({"category": "Social", "severity": "medium",
            "issue": "No Open Graph tags found", "detail": "OG tags control how your page appears when shared on Facebook, LinkedIn, WhatsApp, etc."})
        fixes.append({"issue": "Missing Open Graph tags",
            "fix": f'Add to <head>:\n<meta property="og:title" content="{title}" />\n<meta property="og:description" content="{meta_desc}" />\n<meta property="og:type" content="website" />\n<meta property="og:url" content="{url}" />\n<meta property="og:image" content="https://yourdomain.com/og-image.jpg" />'})
    else:
        og_type = og.get("og:type", "")
        if og_type == "article" and ("/" == page_data.get("url", "").rstrip("/").split("/")[-1] or page_data.get("url", "").rstrip("/") == page_data.get("url", "").split("//")[1].split("/")[0] if "//" in page_data.get("url", "") else False):
            findings.append({"category": "Social", "severity": "medium",
                "issue": 'Homepage uses og:type="article" instead of "website"',
                "detail": f'og:type is set to "article" on what appears to be a homepage. This should be "website".'})
            fixes.append({"issue": "Wrong og:type on homepage",
                "fix": 'Change:\n<meta property="og:type" content="article" />\nTo:\n<meta property="og:type" content="website" />'})

        og_site_name = og.get("og:site_name", "")
        if og_site_name and " - " in og_site_name:
            parts = og_site_name.split(" - ")
            if len(set(p.strip() for p in parts)) < len(parts):
                findings.append({"category": "Social", "severity": "low",
                    "issue": f'Duplicated text in og:site_name: "{og_site_name}"',
                    "detail": "The site name appears to contain repeated text."})

        if not og.get("og:image"):
            score -= 3
            findings.append({"category": "Social", "severity": "medium",
                "issue": "No og:image tag found", "detail": "Shared links will show without a preview image. Recommended size: 1200x630px."})

    # -------------------------------------------------------------------
    # 5. Twitter Card
    # -------------------------------------------------------------------
    tc = page_data.get("twitter_card", {})
    if not tc:
        score -= 2
        findings.append({"category": "Social", "severity": "low",
            "issue": "No Twitter Card tags found", "detail": "Twitter Cards control how links appear on X (Twitter). Falls back to OG tags but explicit tags are preferred."})

    # -------------------------------------------------------------------
    # 6. Word count
    # -------------------------------------------------------------------
    word_count = page_data.get("word_count", 0)
    if word_count < 100:
        score -= 10
        findings.append({"category": "Content", "severity": "high",
            "issue": f"Very thin content ({word_count} words)",
            "detail": "Pages with fewer than 100 words provide little value to users or search engines."})
    elif word_count < 300:
        score -= 5
        findings.append({"category": "Content", "severity": "medium",
            "issue": f"Thin content ({word_count} words)",
            "detail": "Most content pages should have 500+ words for adequate topical coverage."})

    # -------------------------------------------------------------------
    # 7. Hreflang validation
    # -------------------------------------------------------------------
    hreflang = page_data.get("hreflang", [])
    if hreflang:
        langs = [h["lang"] for h in hreflang]
        if "x-default" not in langs:
            findings.append({"category": "International", "severity": "low",
                "issue": "Hreflang tags present but missing x-default",
                "detail": "x-default tells search engines which version to show when no other language matches."})
        # Check for self-referencing
        current_lang = next((h for h in hreflang if h["href"].rstrip("/") == url.rstrip("/")), None)
        if not current_lang:
            findings.append({"category": "International", "severity": "medium",
                "issue": "Hreflang tags do not include a self-referencing entry",
                "detail": "Each page with hreflang must include a tag pointing to itself."})

    return {
        "analyzer": "onpage",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
    }
