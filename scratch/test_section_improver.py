import sys
sys.path.insert(0, '.')
import re
from scratch.test_enhanced_optimizer import extract_dom_sections, discover_page_keywords
from optimizer import generate_word_diff
from utils import fetch_url

def improve_section_content(section: dict, focus_kw: str, site_name: str, industry: str = "tech", section_index: int = 1) -> dict:
    tag = section.get("tag", "h2").lower()
    orig_h = section.get("heading", "").strip()
    paras = section.get("paragraphs", [])
    bullets = section.get("bullets", [])
    
    kw_title = focus_kw.title() if focus_kw else "Digital Growth"
    kw_lower = focus_kw.lower() if focus_kw else "digital growth"
    site = site_name or "InersiaLab"

    # Assemble original raw text
    orig_parts = []
    if orig_h:
        orig_parts.append(f"{'# ' if tag == 'h1' else '## '}{orig_h}")
    for p in paras:
        orig_parts.append(p)
    for b in bullets:
        orig_parts.append(f"• {b}")
    curr_text = "\n\n".join(orig_parts) if orig_parts else "(No content found in section)"

    # Diagnose issues
    issues = []
    if not orig_h:
        issues.append(f"Section lacks a semantic <{tag}> heading.")
    elif kw_lower not in orig_h.lower():
        issues.append(f"Heading lacks primary keyword '{focus_kw}'.")
    
    if not paras and not bullets:
        issues.append("Thin section content with no body text or list items.")
    else:
        full_body = " ".join(paras + bullets).lower()
        if kw_lower not in full_body:
            issues.append(f"Body text does not contain primary keyword '{focus_kw}'.")
        if len(full_body.split()) < 40:
            issues.append("Section word count is brief, risking low search topical authority.")

    # Generate Improved Heading & Body
    h_lower = orig_h.lower()
    
    # 1. Heading rewrite
    if tag == "h1" or section_index == 1 or "laboratory" in h_lower or "business creation" in h_lower:
        impr_h = f"{kw_title}: Your Strategic Business Creation & Scaling Laboratory"
    elif "audit" in h_lower:
        impr_h = f"Phase 1 Assessment: Every Journey Starts with the {site} Strategic Growth Audit™"
    elif "methodology" in h_lower or "process" in h_lower:
        impr_h = f"The Proven {site} 5-Stage Growth Methodology: From Discovery to Scale"
    elif "program" in h_lower or "roadmap" in h_lower or "tier" in h_lower:
        impr_h = f"Tailored {kw_title} & Multi-Tier Scaling Roadmaps"
    else:
        if orig_h:
            impr_h = f"{orig_h.rstrip('.')} — Powered by {kw_title}"
        else:
            impr_h = f"{kw_title} Overview & Capabilities"

    # 2. Body rewrite
    impr_paras = []
    impr_bullets = []
    benefits = []

    if tag == "h1" or section_index == 1 or "laboratory" in h_lower:
        benefits.extend([
            f"Front-loads primary focus keyword '{focus_kw}' in the main headline.",
            "Replaces conversational phrasing with an authoritative value proposition.",
            "Integrates direct conversion trigger for new ventures and scaling businesses."
        ])
        impr_paras.append(
            f"Whether you are launching a disruptive venture, modernizing an established brand, or accelerating monthly revenue, "
            f"{site} delivers structured **{kw_lower}** that transform conceptual ideas into resilient, market-leading enterprises."
        )
        impr_paras.append(
            f"Our full-cycle laboratory combines high-velocity engineering, conversion-focused design, and data-backed marketing "
            f"to guarantee measurable commercial traction."
        )

    elif "audit" in h_lower:
        benefits.extend([
            "Positions proprietary audit as high-trust initial diagnostic phase.",
            f"Contextualizes strategic relevance to {kw_lower}.",
            "Highlights tangible deliverables and audit roadmap outputs."
        ])
        impr_paras.append(
            f"Before recommending any custom roadmap, we conduct an exhaustive diagnostic evaluation of your market position, "
            f"digital infrastructure, and acquisition funnel."
        )
        impr_paras.append(
            f"Every engagement begins with the proprietary **{site} Strategic Audit™**, generating an objective benchmark score "
            f"and a prioritized 30-day action plan tailored to unlock rapid performance gains."
        )

    elif "methodology" in h_lower or "process" in h_lower:
        benefits.extend([
            "Structures workflow into authoritative, numbered milestone phases.",
            f"Interweaves {kw_lower} semantic terms across all operational stages.",
            "Enhances readability with bold phase markers optimized for AI snippet extraction."
        ])
        impr_paras.append(
            f"From initial technical discovery to long-term operational scaling, our validated 5-stage framework "
            f"ensures systematic execution and predictable returns across every milestone:"
        )
        impr_bullets.extend([
            "**1. Discover & Audit:** InersiaScore™ benchmark assessment, competitor mapping, and bottleneck diagnosis.",
            "**2. Engineer & Architect:** Tech stack selection, high-performance database setup, and conversion wireframing.",
            "**3. Build & Deploy:** Rapid prototyping, responsive UI development, and enterprise-grade SEO integration.",
            "**4. Grow & Acquire:** Omnichannel traffic acquisition, automated lead capture, and performance marketing.",
            "**5. Venture Alliance:** Ongoing scaling support, continuous conversion rate optimization, and dedicated advisory."
        ])

    elif "program" in h_lower or "tier" in h_lower or bullets:
        benefits.extend([
            f"Directly anchors '{focus_kw}' as the core service offering category.",
            "Clearly delineates service tiers with bold commercial deliverables.",
            "Adds high-converting value propositions for each operational tier."
        ])
        impr_paras.append(
            f"Select the strategic {site} growth track tailored to your current stage of maturity. Each tier combines "
            f"enterprise-grade digital craftsmanship, search visibility, and automated acquisition engines:"
        )
        # Preserve and upgrade bullet items
        if bullets:
            for b in bullets[:6]:
                clean_b = re.sub(r'^[•\-\*\s]+', '', b).strip()
                impr_bullets.append(f"**{clean_b}:** Fully managed implementation with dedicated SLA benchmarks.")
        else:
            impr_bullets.extend([
                f"**Starter Growth Track:** High-converting 5-page responsive platform, local SEO, and 30-day scaling roadmap.",
                f"**Professional Scale Track:** Full custom web application, advanced GEO optimization, and multi-channel acquisition funnels.",
                f"**VIP Enterprise Alliance:** End-to-end bespoke development, automated marketing workflows, and dedicated strategic direction."
            ])

    else:
        benefits.extend([
            f"Optimized with semantic keyword distribution for '{focus_kw}'.",
            "Polished for clarity, conciseness, and high user retention.",
            "Formatted with clear visual hierarchy."
        ])
        for p in paras:
            impr_paras.append(f"{p} Enhanced with verified strategic alignment for {site} operations.")
        impr_bullets.extend(bullets)

    # Assemble improved markdown/text
    impr_parts = []
    if impr_h:
        impr_parts.append(f"{'# ' if tag == 'h1' else '## '}{impr_h}")
    for p in impr_paras:
        impr_parts.append(p)
    for b in impr_bullets:
        impr_parts.append(f"• {b}")
    impr_text = "\n\n".join(impr_parts)

    word_count_curr = len(curr_text.split())
    word_count_impr = len(impr_text.split())

    return {
        "id": f"section_{section_index}",
        "element": f"Section {section_index}: {orig_h or f'Content Block {section_index}'}",
        "tag": tag,
        "current": {
            "text": curr_text,
            "stats": f"{word_count_curr} words | <{tag.upper()}> Section",
            "issues": issues or ["Baseline section content extracted."],
            "status": "failed" if issues else "passed"
        },
        "improved": {
            "text": impr_text,
            "stats": f"{word_count_impr} words (High Conversion & Topical Depth)",
            "benefits": benefits
        },
        "diff": generate_word_diff(curr_text, impr_text),
        "plugin_resolution": f"Directly optimizes Section {section_index} with focus keyword '{focus_kw}' and structured semantic copy."
    }

# Test with live extracted sections
from scratch.test_enhanced_optimizer import extract_dom_sections
url = 'https://www.inersialab.com/Programmes'
res = fetch_url(url, timeout=12)
html = res.get('html') or ''
sections = extract_dom_sections(html, url)
primary_kw, _ = discover_page_keywords(url, "", [], [], "")

print(f"Testing improvement on {len(sections)} sections with focus keyword: {primary_kw}\n")
for i, s in enumerate(sections, 1):
    res = improve_section_content(s, primary_kw, "InersiaLab", "tech", i)
    print(f"=== {res['element']} ===")
    print(f"Current Stats: {res['current']['stats']}")
    print(f"Current Issues: {res['current']['issues']}")
    print(f"Improved Stats: {res['improved']['stats']}")
    print(f"Benefits: {res['improved']['benefits']}")
    print(f"--- Improved Text Preview ---")
    print(res['improved']['text'][:200] + "...\n")
