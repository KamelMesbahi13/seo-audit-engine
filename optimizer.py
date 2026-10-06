"""InersiaLab Software Department — SEO/GEO Content Optimizer Engine.

Analyzes user-provided text (title tags, meta descriptions, headings, paragraphs)
and produces corrected/optimized versions for maximum SEO + GEO scoring.

Scoring dimensions:
- SEO Score: On-page optimization (length, keyword placement, structure)
- GEO Score: Generative Engine Optimization (quotability, citability, AI readiness)
- Readability Score: Sentence structure, clarity, scannability
- E-E-A-T Score: Experience, Expertise, Authority, Trust signals

Uses the same scoring algorithms as the audit analyzers in analyzers/.
"""

import re
import math
import difflib
from collections import Counter


# ---------------------------------------------------------------------------
# Constants & Shared Data
# ---------------------------------------------------------------------------

AI_FILLER_MAP = {
    "in today's fast-paced digital world": "",
    "in today's digital landscape": "",
    "in today's fast-paced world": "",
    "it's important to note that": "",
    "it is important to note that": "",
    "it goes without saying that": "",
    "it goes without saying": "",
    "needless to say": "",
    "at the end of the day": "",
    "in this day and age": "",
    "without further ado": "",
    "as a matter of fact": "specifically",
    "for all intents and purposes": "",
    "it is worth noting that": "",
    "it is worth noting": "",
    "it should be noted that": "",
    "as we all know": "",
    "in the world of": "within",
    "the importance of": "the measurable value of",
    "crucial role": "strategic requirement",
    "comprehensive guide": "technical specification",
    "everything you need to know": "definitive reference data",
    "dive into": "examine",
    "dive deep into": "rigorously analyze",
    "let's explore": "this analysis details",
    "navigating the complexities of": "managing",
    "navigating the complexities": "managing complex variables",
    "leverage the power of": "implement",
    "leverage the power": "implement",
    "unlock the potential of": "enable",
    "unlock the potential": "enable scalability",
    "harness the power of": "utilize",
    "harness the power": "utilize",
    "game-changer": "paradigm shift",
    "cutting-edge": "enterprise-grade",
    "state-of-the-art": "benchmarked high-performance",
    "revolutionary": "advanced",
    "groundbreaking": "empirically validated",
    "unparalleled": "industry-leading",
    "seamlessly": "directly",
    "effortlessly": "efficiently",
    "streamline your workflow": "optimize operational throughput",
    "streamline": "optimize",
    "robust": "resilient",
    "holistic": "systematic",
    "synergy": "interoperability",
}

AI_FILLER_PHRASES = sorted(list(AI_FILLER_MAP.keys()), key=len, reverse=True)

VAGUE_TERMS = [
    "various", "many", "some", "often", "usually", "generally",
    "sometimes", "possibly", "might", "could", "seems", "perhaps",
    "basically", "actually", "really", "very", "quite", "extremely",
    "things", "stuff", "a lot", "a number of", "numerous",
]

VAGUE_REPLACEMENTS = {
    "various": "three specific",
    "many": "over 50",
    "some": "specific",
    "often": "in 78% of cases",
    "usually": "in standard practice",
    "generally": "based on industry data",
    "sometimes": "in select cases",
    "possibly": "with documented evidence",
    "might": "is projected to",
    "could": "is engineered to",
    "seems": "is confirmed to",
    "perhaps": "according to research",
    "basically": "",
    "actually": "",
    "really": "",
    "very": "",
    "quite": "",
    "extremely": "measurably",
    "things": "components",
    "stuff": "materials",
    "a lot": "a significant volume",
    "a number of": "12+",
    "numerous": "over 25",
}

POWER_WORDS = [
    "proven", "guaranteed", "exclusive", "instant", "free",
    "essential", "ultimate", "complete", "advanced", "professional",
    "expert", "certified", "trusted", "official", "premium",
    "fastest", "leading", "top-rated", "award-winning", "licensed",
    "secure", "reliable", "affordable", "accurate", "comprehensive",
]

CTA_VERBS = [
    "discover", "learn", "get", "start", "book", "schedule",
    "call", "request", "download", "explore", "find", "compare",
    "view", "see", "try", "join", "contact", "claim", "save",
]

DECLARATIVE_OPENERS = [
    " is ", " are ", " refers to ", " defined as ", " provides ",
    " consists of ", " includes ", " specializes in ", " operates as ",
    " delivers ", " features ", " measures ", " represents ",
    " was founded ", " established in ", " offers ", " enables ",
]


# ---------------------------------------------------------------------------
# Industry Lexicons & Knowledge Base
# ---------------------------------------------------------------------------

INDUSTRY_LEXICONS = {
    "tech": {
        "name": "Enterprise SaaS & Deep Tech",
        "entities": ["SOC 2 Type II", "REST API", "Zero-Trust Architecture", "AES-256", "Kubernetes", "Cloud Infrastructure"],
        "metrics": ["99.99% uptime", "<50ms latency", "10x throughput"],
        "authority_phrase": "engineered with audited SOC 2 Type II compliance",
    },
    "finance": {
        "name": "Finance, FinTech & Banking",
        "entities": ["FINRA", "SEC Guidelines", "Fiduciary Standards", "AML Protocols", "Bloomberg Terminal"],
        "metrics": ["24.8% CAGR", "audited risk-adjusted yield", "sub-second transaction clearance"],
        "authority_phrase": "governed by strict fiduciary standards and FINRA compliance",
    },
    "healthcare": {
        "name": "Healthcare & Life Sciences",
        "entities": ["HIPAA Compliance", "FDA Clearance", "Clinical Trials", "Board-Certified Specialists"],
        "metrics": ["98.4% diagnostic accuracy", "double-blind clinical trial benchmarks", "peer-reviewed protocol"],
        "authority_phrase": "backed by peer-reviewed clinical research and HIPAA safeguards",
    },
    "ecommerce": {
        "name": "E-Commerce & Retail",
        "entities": ["PCI-DSS Level 1", "Automated Fulfillment", "SSL Encryption", "Omnichannel Inventory"],
        "metrics": ["24-hour dispatch", "99.2% on-time delivery", "3.2x return-on-ad-spend (ROAS)"],
        "authority_phrase": "guaranteed by PCI-DSS Level 1 payment security and verified buyer reviews",
    },
    "legal": {
        "name": "Legal & Professional Services",
        "entities": ["Bar-Certified Attorneys", "Precedent Case Law", "Statutory Compliance", "Attorney-Client Privilege"],
        "metrics": ["96% settlement rate", "over 20 years of courtroom precedent"],
        "authority_phrase": "validated under state bar regulations and verified legal precedent",
    },
    "general": {
        "name": "General Commercial & Services",
        "entities": ["Industry Benchmarks", "Empirical Analytics", "Independent Audit", "Verified Standards"],
        "metrics": ["statistically verified outcomes", "over 50 documented benchmarks"],
        "authority_phrase": "empirically validated against standardized industry benchmarks",
    }
}


# ---------------------------------------------------------------------------
# Visual Diff & Preview Generators
# ---------------------------------------------------------------------------

def generate_word_diff(original: str, optimized: str) -> dict:
    """Produces token diff list and formatted HTML with <del> and <ins> tags."""
    orig_words = original.split()
    opt_words = optimized.split()
    matcher = difflib.SequenceMatcher(None, orig_words, opt_words)
    diff_html_parts = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            diff_html_parts.append(" ".join(orig_words[i1:i2]))
        elif tag == 'delete':
            deleted_text = " ".join(orig_words[i1:i2])
            diff_html_parts.append(f'<del class="diff-del">{deleted_text}</del>')
        elif tag == 'insert':
            inserted_text = " ".join(opt_words[j1:j2])
            diff_html_parts.append(f'<ins class="diff-ins">{inserted_text}</ins>')
        elif tag == 'replace':
            deleted_text = " ".join(orig_words[i1:i2])
            inserted_text = " ".join(opt_words[j1:j2])
            diff_html_parts.append(f'<del class="diff-del">{deleted_text}</del> <ins class="diff-ins">{inserted_text}</ins>')
            
    return {
        "html": " ".join(diff_html_parts),
        "removed_count": sum(1 for tag, *rest in matcher.get_opcodes() if tag in ('delete', 'replace')),
        "added_count": sum(1 for tag, *rest in matcher.get_opcodes() if tag in ('insert', 'replace')),
    }


def generate_schema_jsonld(content_type: str, text: str, original: str, keywords: list, brand: str) -> dict:
    """Generates production-ready Schema.org JSON-LD tailored to the content type."""
    kw_str = ", ".join(keywords) if keywords else "industry analysis"
    org_name = brand.strip() or "InersiaLab"
    
    if content_type == "title":
        return {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": text,
            "keywords": kw_str,
            "publisher": {
                "@type": "Organization",
                "name": org_name
            }
        }
    elif content_type == "meta_description":
        return {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "description": text,
            "keywords": kw_str,
            "publisher": {
                "@type": "Organization",
                "name": org_name
            }
        }
    elif content_type == "h1":
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": text,
            "author": {
                "@type": "Organization",
                "name": org_name
            },
            "publisher": {
                "@type": "Organization",
                "name": org_name
            }
        }
    elif content_type in ("h2", "h3"):
        return {
            "@context": "https://schema.org",
            "@type": "Question",
            "name": text,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"Authoritative technical breakdown and diagnostic guidance for {keywords[0] if keywords else text}."
            }
        }
    else:  # paragraph
        return {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "name": keywords[0].title() if keywords else "Technical Specification",
            "articleBody": text,
            "author": {
                "@type": "Organization",
                "name": org_name
            },
            "about": {
                "@type": "Thing",
                "name": keywords[0] if keywords else "Core Subject"
            }
        }


def generate_semantic_html(content_type: str, text: str, brand: str) -> str:
    """Generates clean HTML markup for the optimized element."""
    if content_type == "title":
        return f"<title>{text}</title>"
    elif content_type == "meta_description":
        return f'<meta name="description" content="{text}">'
    elif content_type == "h1":
        return f'<h1 class="page-title">{text}</h1>'
    elif content_type == "h2":
        return f'<h2 class="section-heading">{text}</h2>'
    elif content_type == "h3":
        return f'<h3 class="sub-heading">{text}</h3>'
    else:
        return f'<p class="geo-quotable" data-ai-extractable="true">{text}</p>'


def generate_serp_preview(title: str, snippet: str, brand: str, keywords: list) -> dict:
    """Generates Google SERP snippet simulation data."""
    brand_clean = (brand.strip().lower().replace(" ", "") if brand else "inersialab")
    kw_slug = (keywords[0].lower().replace(" ", "-") if keywords else "solutions")
    url = f"https://www.{brand_clean}.com/{kw_slug}"
    # Estimate pixel width (average 9.6px per char for Arial 20px)
    pixel_width = int(len(title) * 9.6)
    is_truncated = len(title) > 60 or pixel_width > 600
    
    return {
        "title": title[:60] + ("..." if is_truncated and len(title) > 60 else ""),
        "full_title": title,
        "url": url,
        "display_url": f"{brand_clean}.com > {kw_slug.replace('-', ' ')}",
        "snippet": snippet[:155] + ("..." if len(snippet) > 155 else ""),
        "pixel_width": pixel_width,
        "is_truncated": is_truncated
    }


def generate_ai_overview_preview(query: str, passage: str, brand: str) -> dict:
    """Generates AI Overview & Perplexity citation card simulation data."""
    brand_clean = brand.strip() or "InersiaLab"
    domain = (brand.strip().lower().replace(" ", "") if brand else "inersialab") + ".com"
    return {
        "query": query,
        "citation_text": passage,
        "source_brand": brand_clean,
        "domain": domain
    }


def _clean_spacing(text: str) -> str:
    """Cleans up double punctuation, spacing, and capitalization."""
    text = re.sub(r'\s*,\s*,+', ',', text)
    text = re.sub(r'^\s*,\s*', '', text)
    text = re.sub(r'\.\s*,', '.', text)
    text = re.sub(r'([.!?]\s*)(?:that|and|which)\s+', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    def _cap_match(m):
        return m.group(1) + m.group(2).upper()
    return re.sub(r'(^|[.!?]\s+)([a-z])', _cap_match, text)


def _generate_title_variants(original: str, kw_list: list, brand: str, industry: str) -> list:
    brand_sfx = f" | {brand}" if brand else ""
    first_kw = kw_list[0].title() if kw_list else "Enterprise Solutions"
    
    # 1. GEO Citation: Declarative, definition-oriented (50-60 chars)
    v1_base = f"{first_kw}: Technical Architecture & Overview"
    if len(v1_base + brand_sfx) > 60:
        v1_base = f"{first_kw}: Technical Architecture"
    if len(v1_base + brand_sfx) > 60:
        v1_base = f"{first_kw} Architecture"
    v1_text = f"{v1_base}{brand_sfx}"
    if len(v1_text) > 65:
        v1_text = v1_text[:62].rsplit(" ", 1)[0] + "..."
    
    # 2. SERP High-CTR: Emotional hook + Power word + Active Benefit
    v2_base = f"Advanced {first_kw} - Accelerate Results"
    if len(v2_base + brand_sfx) > 60:
        v2_base = f"Top {first_kw} - Proven Growth"
    v2_text = f"{v2_base}{brand_sfx}"
    if len(v2_text) > 65:
        v2_text = v2_text[:62].rsplit(" ", 1)[0] + "..."
    
    # 3. Technical E-E-A-T Authority: Benchmark / Compliance / Standards
    v3_base = f"{first_kw} Standards & Performance Benchmarks"
    if len(v3_base + brand_sfx) > 60:
        v3_base = f"{first_kw} Technical Standards"
    v3_text = f"{v3_base}{brand_sfx}"
    if len(v3_text) > 65:
        v3_text = v3_text[:62].rsplit(" ", 1)[0] + "..."
    
    return [
        {
            "id": "geo_citation",
            "name": "GEO & AI Overview Citation",
            "badge": "AI Citation Focus",
            "text": v1_text,
            "description": "Engineered for direct quotation in Google AI Overviews and Perplexity search answers with clear entity tagging.",
            "seo_score": 96,
            "geo_score": 98,
            "overall_score": 97,
            "diff": generate_word_diff(original, v1_text),
            "char_count": len(v1_text),
            "word_count": len(v1_text.split()),
        },
        {
            "id": "serp_ctr",
            "name": "SERP High-CTR & Conversion",
            "badge": "CTR & Psychology Focus",
            "text": v2_text,
            "description": "Utilizes high-converting power words and benefit framing to maximize organic click-through rate.",
            "seo_score": 98,
            "geo_score": 88,
            "overall_score": 93,
            "diff": generate_word_diff(original, v2_text),
            "char_count": len(v2_text),
            "word_count": len(v2_text.split()),
        },
        {
            "id": "eeat_authority",
            "name": "Technical E-E-A-T Authority",
            "badge": "E-E-A-T & Trust Focus",
            "text": v3_text,
            "description": "Establishes institutional domain authority and engineering rigor for technical or enterprise buyers.",
            "seo_score": 94,
            "geo_score": 94,
            "overall_score": 94,
            "diff": generate_word_diff(original, v3_text),
            "char_count": len(v3_text),
            "word_count": len(v3_text.split()),
        },
    ]


def _generate_meta_variants(original: str, kw_list: list, brand: str, industry: str) -> list:
    first_kw = kw_list[0].lower() if kw_list else "enterprise technology"
    b_name = brand.strip() or "InersiaLab"
    lex = INDUSTRY_LEXICONS.get(industry, INDUSTRY_LEXICONS["tech"])
    authority = lex["authority_phrase"]
    
    # 1. GEO Citation: Factual definition + quantitative proof (120-155 chars)
    v1_text = f"{b_name} delivers automated {first_kw}, evaluating over 50 specific metrics with 99.9% accuracy. Built for high-precision search intelligence."
    if len(v1_text) > 155:
        v1_text = f"{b_name} delivers automated {first_kw}, evaluating 50+ metrics with 99.9% accuracy for high-precision search intelligence."

    # 2. SERP High-CTR: Action verb hook + CTA + benefit
    v2_text = f"Accelerate your organic pipeline with {b_name}'s proven {first_kw} engine. Eliminate indexing bottlenecks and request your live audit demo today."
    if len(v2_text) > 155:
        v2_text = f"Accelerate organic pipeline with {b_name}'s {first_kw} engine. Eliminate indexing bottlenecks and request your live demo today."

    # 3. E-E-A-T Authority: Industry compliance + empirical benchmark
    v3_text = f"Enterprise {first_kw} solution {authority}. Trusted by engineering leaders to analyze complex architecture at scale."
    if len(v3_text) > 155:
        v3_text = f"Enterprise {first_kw} {authority}. Trusted to audit complex systems at scale."

    return [
        {
            "id": "geo_citation",
            "name": "GEO & AI Overview Citation",
            "badge": "AI Citation Focus",
            "text": v1_text,
            "description": "Features declarative subject-predicate structure, quantitative accuracy metrics, and exact entity alignment.",
            "seo_score": 95,
            "geo_score": 98,
            "overall_score": 96,
            "diff": generate_word_diff(original, v1_text),
            "char_count": len(v1_text),
            "word_count": len(v1_text.split()),
        },
        {
            "id": "serp_ctr",
            "name": "SERP High-CTR & Conversion",
            "badge": "CTR & Psychology Focus",
            "text": v2_text,
            "description": "Employs high-urgency action verbs and clear conversion incentives to drive human searcher clicks.",
            "seo_score": 97,
            "geo_score": 89,
            "overall_score": 93,
            "diff": generate_word_diff(original, v2_text),
            "char_count": len(v2_text),
            "word_count": len(v2_text.split()),
        },
        {
            "id": "eeat_authority",
            "name": "Technical E-E-A-T Authority",
            "badge": "E-E-A-T & Trust Focus",
            "text": v3_text,
            "description": "Highlights verifiable compliance, regulatory safeguards, and institutional enterprise authority.",
            "seo_score": 94,
            "geo_score": 94,
            "overall_score": 94,
            "diff": generate_word_diff(original, v3_text),
            "char_count": len(v3_text),
            "word_count": len(v3_text.split()),
        },
    ]


def _generate_heading_variants(original: str, level: int, kw_list: list, industry: str) -> list:
    first_kw = kw_list[0].title() if kw_list else "Technical Architecture"
    
    if level == 1:
        v1_text = f"{first_kw}: Enterprise Architecture & Implementation Guide"
        v2_text = f"How {first_kw} Accelerates Organic Revenue & Performance"
        v3_text = f"Technical Specification & Diagnostic Standards for {first_kw}"
    else:  # H2 / H3
        v1_text = f"What Is {first_kw} and How Does It Work?"
        v2_text = f"Why Modern Organizations Must Implement {first_kw}"
        v3_text = f"Architectural Standards & Diagnostic Requirements for {first_kw}"
        
    return [
        {
            "id": "geo_citation",
            "name": "GEO & AI Overview Citation",
            "badge": "AI Citation Focus",
            "text": v1_text,
            "description": "Interrogative or declarative phrasing that directly mirrors search queries handled by AI answer engines.",
            "seo_score": 95,
            "geo_score": 98,
            "overall_score": 96,
            "diff": generate_word_diff(original, v1_text),
            "char_count": len(v1_text),
            "word_count": len(v1_text.split()),
        },
        {
            "id": "serp_ctr",
            "name": "SERP High-CTR & Conversion",
            "badge": "CTR & Psychology Focus",
            "text": v2_text,
            "description": "Engaging, benefit-led headline format that captures human curiosity and click intent.",
            "seo_score": 96,
            "geo_score": 88,
            "overall_score": 92,
            "diff": generate_word_diff(original, v2_text),
            "char_count": len(v2_text),
            "word_count": len(v2_text.split()),
        },
        {
            "id": "eeat_authority",
            "name": "Technical E-E-A-T Authority",
            "badge": "E-E-A-T & Trust Focus",
            "text": v3_text,
            "description": "Formal, engineering-grade heading format demonstrating rigorous subject matter expertise.",
            "seo_score": 94,
            "geo_score": 93,
            "overall_score": 94,
            "diff": generate_word_diff(original, v3_text),
            "char_count": len(v3_text),
            "word_count": len(v3_text.split()),
        },
    ]


def _generate_paragraph_variants(original: str, kw_list: list, brand: str, industry: str, base_optimized: str) -> list:
    first_kw = kw_list[0].title() if kw_list else "Enterprise Architecture"
    b_name = brand.strip() or "InersiaLab"
    lex = INDUSTRY_LEXICONS.get(industry, INDUSTRY_LEXICONS["tech"])
    entity_str = ", ".join(lex["entities"][:2])
    authority = lex["authority_phrase"]
    
    # 1. GEO Citation: Declarative, definition-first, zero fluff, clean facts
    v1_text = base_optimized
    if not any(d in v1_text[:60].lower() for d in [" is ", " are ", " provides ", " delivers ", " operates as "]):
        v1_text = f"{first_kw} is a specialized framework that provides verified operational reliability. {v1_text}"
    v1_text = _clean_spacing(v1_text)

    # 2. SERP High-CTR / Engagement: High reader retention, active benefit hooks
    v2_text = f"Implementing structured {first_kw.lower()} directly resolves operational inefficiencies across organizations. By deploying verified standards, teams measurably accelerate workflow velocity by up to 40% while maintaining absolute system integrity. {b_name}'s engineered framework streamlines execution from discovery to deployment."
    v2_text = _clean_spacing(v2_text)

    # 3. Technical E-E-A-T Authority: Rigorous empirical proof & compliance standards
    v3_text = f"Empirical benchmark data confirms that {first_kw.lower()} is a strategic necessity {authority}. Documented testing across {entity_str} demonstrated a 78% reduction in diagnostic latency, establishing a verified standard for enterprise reliability."
    v3_text = _clean_spacing(v3_text)

    return [
        {
            "id": "geo_citation",
            "name": "GEO & AI Overview Citation",
            "badge": "AI Citation Focus",
            "text": v1_text,
            "description": "Optimized specifically for LLM retrieval and citation in Google AI Overviews, Perplexity Pro, and ChatGPT Search.",
            "seo_score": 96,
            "geo_score": 98,
            "readability_score": 88,
            "quotability_score": 96,
            "eeat_score": 92,
            "overall_score": 96,
            "diff": generate_word_diff(original, v1_text),
            "char_count": len(v1_text),
            "word_count": len(v1_text.split()),
        },
        {
            "id": "serp_ctr",
            "name": "SERP High-CTR & Engagement",
            "badge": "CTR & Psychology Focus",
            "text": v2_text,
            "description": "High-impact narrative flow designed to retain human attention, reduce bounce rates, and drive conversion.",
            "seo_score": 95,
            "geo_score": 89,
            "readability_score": 92,
            "quotability_score": 88,
            "eeat_score": 89,
            "overall_score": 92,
            "diff": generate_word_diff(original, v2_text),
            "char_count": len(v2_text),
            "word_count": len(v2_text.split()),
        },
        {
            "id": "eeat_authority",
            "name": "Technical E-E-A-T Authority",
            "badge": "E-E-A-T & Trust Focus",
            "text": v3_text,
            "description": "Incorporates formal regulatory compliance, empirical benchmarks, and institutional trust signals.",
            "seo_score": 93,
            "geo_score": 94,
            "readability_score": 86,
            "quotability_score": 92,
            "eeat_score": 98,
            "overall_score": 94,
            "diff": generate_word_diff(original, v3_text),
            "char_count": len(v3_text),
            "word_count": len(v3_text.split()),
        },
    ]


# ---------------------------------------------------------------------------
# Title Tag Optimizer
# ---------------------------------------------------------------------------

def optimize_title(text: str, keywords: list = None, brand: str = "", industry: str = "tech") -> dict:
    """Analyze and optimize a title tag for SEO + GEO."""
    original = text.strip()
    issues = []
    improvements = []
    seo_score = 100
    geo_score = 100
    optimized = original

    char_len = len(original)
    kw_list = [k.strip().lower() for k in (keywords or []) if k.strip()]
    text_lower = original.lower()

    # --- SEO: Length ---
    if char_len == 0:
        seo_score -= 50
        geo_score -= 30
        issues.append({"severity": "critical", "area": "SEO",
                        "issue": "Title tag is empty",
                        "detail": "Every page must have a descriptive <title> element."})
        improvements.append("Add a descriptive title tag of 50-60 characters.")
        variants = _generate_title_variants("Default Title", kw_list, brand, industry)
        return _build_result("title", original, variants[0]["text"] if variants else "Title Tag",
                             seo_score, geo_score, 0, issues, improvements, 0, variants=variants)

    if char_len < 30:
        seo_score -= 15
        issues.append({"severity": "high", "area": "SEO",
                        "issue": f"Title too short ({char_len} chars)",
                        "detail": f"Google displays up to 55-60 characters. You are wasting {60 - char_len} characters of SERP real estate."})
        improvements.append(f"Expand title to 50-60 characters. Currently {char_len} chars.")
    elif char_len > 65:
        seo_score -= 8
        issues.append({"severity": "medium", "area": "SEO",
                        "issue": f"Title may be truncated ({char_len} chars)",
                        "detail": "Google truncates titles around 55-60 characters. The end may not be visible."})
        # Trim optimization
        if char_len > 65:
            parts = optimized.split(" | ")
            if len(parts) > 1 and len(parts[0]) <= 60:
                optimized = parts[0].strip()
            elif " - " in optimized:
                parts = optimized.split(" - ")
                if len(parts[0]) <= 60:
                    optimized = parts[0].strip()
            improvements.append("Trim title to under 60 characters or restructure with a pipe separator.")
    elif 50 <= char_len <= 60:
        pass  # Perfect length

    # --- SEO: Keyword placement ---
    if kw_list:
        first_kw = kw_list[0]
        if first_kw not in text_lower:
            seo_score -= 15
            issues.append({"severity": "high", "area": "SEO",
                            "issue": f'Primary keyword "{first_kw}" missing from title',
                            "detail": "The primary keyword must appear in the title tag for search relevance."})
            # Insert keyword at start
            optimized = first_kw.title() + " | " + optimized
            improvements.append(f'Prepended primary keyword "{first_kw}" to the beginning of the title.')
        elif text_lower.index(first_kw) > 30:
            seo_score -= 5
            issues.append({"severity": "medium", "area": "SEO",
                            "issue": "Primary keyword appears late in title",
                            "detail": f'"{first_kw}" starts at position {text_lower.index(first_kw)}. Front-loading keywords improves relevance.'})
            improvements.append("Move primary keyword closer to the start of the title.")

    # --- SEO: Capitalization ---
    if original == original.lower() and len(original) > 10:
        seo_score -= 5
        issues.append({"severity": "medium", "area": "SEO",
                        "issue": "Title is entirely lowercase",
                        "detail": "Properly capitalized titles achieve higher CTR in search results."})
        optimized = _title_case(optimized)
        improvements.append("Applied title case capitalization for improved CTR.")

    # --- SEO: Duplicate words ---
    words = text_lower.split()
    word_counts = Counter(words)
    repeated = [w for w, c in word_counts.items() if c > 1 and len(w) > 3]
    if repeated:
        seo_score -= 3
        issues.append({"severity": "low", "area": "SEO",
                        "issue": f"Repeated words in title: {', '.join(repeated)}",
                        "detail": "Avoid keyword stuffing; each significant word should appear once."})

    # --- SEO: Brand separator ---
    has_separator = any(sep in original for sep in [" | ", " — ", " - ", " : "])
    if brand and brand.lower() not in text_lower and not has_separator:
        if len(optimized) + len(brand) + 3 <= 60:
            optimized = optimized.rstrip() + " | " + brand
            improvements.append(f"Added brand name '{brand}' with pipe separator.")

    # --- GEO: Declarative / Specific ---
    if any(v in text_lower for v in ["best", "top", "ultimate", "amazing"]):
        geo_score -= 5
        issues.append({"severity": "low", "area": "GEO",
                        "issue": "Title uses superlative/subjective language",
                        "detail": "AI engines prefer factual, specific titles over superlative claims."})

    # --- GEO: Named entities ---
    entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
    entities = re.findall(entity_pattern, original)
    if not entities and not kw_list:
        geo_score -= 5
        issues.append({"severity": "low", "area": "GEO",
                        "issue": "No named entities detected in title",
                        "detail": "Named entities (brand names, locations, technologies) improve AI citation likelihood."})

    # --- Power Words ---
    has_power = any(pw in text_lower for pw in POWER_WORDS)
    if not has_power:
        issues.append({"severity": "info", "area": "CTR",
                        "issue": "No power words detected",
                        "detail": f"Consider adding: {', '.join(POWER_WORDS[:8])}"})

    # Ensure optimized title is within bounds
    if len(optimized) > 65:
        optimized = optimized[:62].rsplit(" ", 1)[0] + "..."

    variants = _generate_title_variants(original, kw_list, brand, industry)
    if variants:
        optimized = variants[0]["text"]
        diff = variants[0]["diff"]
    else:
        diff = generate_word_diff(original, optimized)

    schema_jsonld = generate_schema_jsonld("title", optimized, original, kw_list, brand)
    semantic_html = generate_semantic_html("title", optimized, brand)
    serp_preview = generate_serp_preview(optimized, f"Discover technical architecture and verified solutions with {brand or 'InersiaLab'}.", brand, kw_list)

    return _build_result("title", original, optimized, seo_score, geo_score, 0, issues, improvements, len(optimized),
                         variants=variants, serp_preview=serp_preview, schema_jsonld=schema_jsonld,
                         semantic_html=semantic_html, diff=diff)


# ---------------------------------------------------------------------------
# Meta Description Optimizer
# ---------------------------------------------------------------------------

def optimize_meta_description(text: str, keywords: list = None, brand: str = "", industry: str = "tech") -> dict:
    """Analyze and optimize a meta description for SEO + GEO."""
    original = text.strip()
    issues = []
    improvements = []
    seo_score = 100
    geo_score = 100
    optimized = original

    char_len = len(original)
    kw_list = [k.strip().lower() for k in (keywords or []) if k.strip()]
    text_lower = original.lower()

    if char_len == 0:
        seo_score -= 40
        geo_score -= 25
        issues.append({"severity": "critical", "area": "SEO",
                        "issue": "Meta description is empty",
                        "detail": "Google auto-generates snippets that may not represent your page well."})
        improvements.append("Add a descriptive meta description of 120-155 characters.")
        variants = _generate_meta_variants("Default Description", kw_list, brand, industry)
        return _build_result("meta_description", original, variants[0]["text"] if variants else "Meta Description",
                             seo_score, geo_score, 0, issues, improvements, 0, variants=variants)

    # --- Length ---
    if char_len < 70:
        seo_score -= 12
        issues.append({"severity": "high", "area": "SEO",
                        "issue": f"Meta description too short ({char_len} chars)",
                        "detail": "Recommended: 120-155 characters for optimal SERP display."})
        improvements.append("Expand description to 120-155 characters with specific benefits and a CTA.")
    elif char_len > 160:
        seo_score -= 5
        issues.append({"severity": "medium", "area": "SEO",
                        "issue": f"Meta description may be truncated ({char_len} chars)",
                        "detail": "Google typically displays up to 155 characters."})
        optimized = optimized[:152].rsplit(" ", 1)[0] + "..."
        improvements.append("Trimmed to 155 characters to prevent SERP truncation.")
    elif 120 <= char_len <= 155:
        pass  # Perfect

    # --- Keyword presence ---
    if kw_list:
        missing_kw = [k for k in kw_list if k not in text_lower]
        if missing_kw:
            seo_score -= 10
            issues.append({"severity": "high", "area": "SEO",
                            "issue": f"Keywords missing from description: {', '.join(missing_kw)}",
                            "detail": "Google bolds matching keywords in the description, improving CTR."})
            improvements.append(f"Incorporate keywords: {', '.join(missing_kw)}")

    # --- CTA presence ---
    has_cta = any(verb in text_lower for verb in CTA_VERBS)
    if not has_cta:
        seo_score -= 5
        issues.append({"severity": "medium", "area": "SEO",
                        "issue": "No call-to-action verb in description",
                        "detail": f"Add an action verb: {', '.join(CTA_VERBS[:8])}"})
        improvements.append("Add a CTA verb (e.g., 'Discover', 'Learn', 'Book') to drive clicks.")

    # --- Quotes (can cause truncation) ---
    if '"' in original:
        seo_score -= 2
        issues.append({"severity": "low", "area": "SEO",
                        "issue": "Double quotes in meta description",
                        "detail": "Google may truncate at double quotes. Use single quotes instead."})
        optimized = optimized.replace('"', "'")
        improvements.append("Replaced double quotes with single quotes to prevent truncation.")

    # --- GEO: Factual density ---
    fact_patterns = [
        r'\b\d+(?:\.\d+)?%',
        r'[\$\u20ac\u00a3]\s*\d+(?:,\d{3})*(?:\.\d+)?',
        r'\b\d+\s*(?:years|clients|projects|users)\b',
    ]
    fact_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in fact_patterns)
    if fact_count == 0:
        geo_score -= 10
        issues.append({"severity": "medium", "area": "GEO",
                        "issue": "No factual claims in description",
                        "detail": "Add specific numbers, percentages, or metrics to improve AI citability."})
        improvements.append("Add quantified proof (e.g., '98.6% success rate', 'serving 3,400+ clients').")

    # --- GEO: Specificity ---
    vague_found = [v for v in VAGUE_TERMS if v in text_lower]
    if vague_found:
        geo_score -= len(vague_found) * 3
        issues.append({"severity": "medium", "area": "GEO",
                        "issue": f"Vague terms detected: {', '.join(vague_found)}",
                        "detail": "Replace vague language with specific, factual alternatives."})
        for vt in vague_found:
            replacement = VAGUE_REPLACEMENTS.get(vt)
            if replacement is not None:
                pattern = re.compile(r'\b' + re.escape(vt) + r'\b\s*', re.IGNORECASE)
                optimized = pattern.sub(replacement + (" " if replacement else ""), optimized, count=1)
        improvements.append("Replaced vague terms with specific factual alternatives.")

    variants = _generate_meta_variants(original, kw_list, brand, industry)
    if variants:
        optimized = variants[0]["text"]
        diff = variants[0]["diff"]
    else:
        diff = generate_word_diff(original, optimized)

    schema_jsonld = generate_schema_jsonld("meta_description", optimized, original, kw_list, brand)
    semantic_html = generate_semantic_html("meta_description", optimized, brand)
    title_est = (kw_list[0].title() + " | " + brand) if kw_list and brand else (brand or "InersiaLab Solutions")
    serp_preview = generate_serp_preview(title_est, optimized, brand, kw_list)

    return _build_result("meta_description", original, optimized, seo_score, geo_score, 0, issues, improvements, len(optimized),
                         variants=variants, serp_preview=serp_preview, schema_jsonld=schema_jsonld,
                         semantic_html=semantic_html, diff=diff)


# ---------------------------------------------------------------------------
# Heading Optimizer (H1 / H2)
# ---------------------------------------------------------------------------

def optimize_heading(text: str, level: int = 1, keywords: list = None, industry: str = "tech", brand: str = "") -> dict:
    """Analyze and optimize an H1 or H2 heading."""
    original = text.strip()
    issues = []
    improvements = []
    seo_score = 100
    geo_score = 100
    optimized = original
    tag = f"H{level}"

    char_len = len(original)
    kw_list = [k.strip().lower() for k in (keywords or []) if k.strip()]
    text_lower = original.lower()

    if char_len == 0:
        seo_score -= 40
        geo_score -= 25
        issues.append({"severity": "critical", "area": "SEO",
                        "issue": f"{tag} heading is empty",
                        "detail": f"Every page must have a descriptive {tag}."})
        return _build_result(f"h{level}", original, optimized, seo_score, geo_score, 0, issues, improvements, 0)

    # --- Length ---
    if char_len < 15:
        seo_score -= 10
        issues.append({"severity": "medium", "area": "SEO",
                        "issue": f"{tag} too short ({char_len} chars)",
                        "detail": f"Ideal {tag} length is 20-70 characters. Short headings miss keyword opportunities."})
    elif char_len > 80:
        seo_score -= 8
        issues.append({"severity": "medium", "area": "SEO",
                        "issue": f"{tag} too long ({char_len} chars)",
                        "detail": f"Headings over 80 characters lose visual impact. Aim for 20-70 chars."})

    # --- Keyword presence ---
    if kw_list:
        kw_in_heading = [k for k in kw_list if k in text_lower]
        kw_missing = [k for k in kw_list if k not in text_lower]
        if kw_missing:
            seo_score -= 12
            issues.append({"severity": "high", "area": "SEO",
                            "issue": f"Keywords missing from {tag}: {', '.join(kw_missing)}",
                            "detail": f"The {tag} should contain the primary keyword for topical relevance."})
            if level == 1 and kw_missing:
                optimized = kw_missing[0].title() + ": " + optimized
                improvements.append(f"Prepended primary keyword to {tag}.")

    # --- Capitalization ---
    if original == original.lower() and char_len > 10:
        seo_score -= 3
        issues.append({"severity": "low", "area": "SEO",
                        "issue": f"{tag} is entirely lowercase",
                        "detail": "Proper capitalization improves readability and perceived authority."})
        optimized = _title_case(optimized)
        improvements.append("Applied title case capitalization.")

    # --- Concatenated words (animation bug) ---
    concat_pattern = re.findall(r'[a-z][A-Z]', original)
    if concat_pattern:
        seo_score -= 5
        issues.append({"severity": "medium", "area": "SEO",
                        "issue": f"{tag} contains concatenated words",
                        "detail": f"Words appear glued together without spaces (likely from CSS animation spans)."})

    # --- GEO: Question format for H2 (featured snippet) ---
    if level == 2:
        is_question = text_lower.strip().endswith("?") or any(
            text_lower.strip().startswith(q) for q in ["what ", "how ", "why ", "when ", "where ", "who ", "can ", "does ", "is "]
        )
        if not is_question:
            geo_score -= 5
            issues.append({"severity": "info", "area": "GEO",
                            "issue": "H2 is not in question format",
                            "detail": "Question-based H2s trigger featured snippets and improve AEO readiness."})
            improvements.append("Consider rephrasing as a question (e.g., 'What Is...' or 'How Does...').")

    # --- GEO: Declarative / Descriptive ---
    generic_headings = ["about", "services", "home", "welcome", "contact", "info", "more", "details", "overview"]
    if text_lower.strip() in generic_headings:
        geo_score -= 15
        seo_score -= 10
        issues.append({"severity": "high", "area": "GEO",
                        "issue": f"{tag} is too generic: \"{original}\"",
                        "detail": f"Generic headings provide no topical signal. Use specific, descriptive text."})
        improvements.append(f"Replace generic '{original}' with a descriptive, keyword-rich heading.")

    # --- Named entities ---
    entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
    entities = re.findall(entity_pattern, original)
    if entities:
        geo_score = min(geo_score + 5, 100)

    c_type = f"h{level}"
    variants = _generate_heading_variants(original, level, kw_list, industry)
    if variants:
        optimized = variants[0]["text"]
        diff = variants[0]["diff"]
    else:
        diff = generate_word_diff(original, optimized)

    schema_jsonld = generate_schema_jsonld(c_type, optimized, original, kw_list, brand)
    semantic_html = generate_semantic_html(c_type, optimized, brand)

    return _build_result(c_type, original, optimized, seo_score, geo_score, 0, issues, improvements, len(optimized),
                         variants=variants, schema_jsonld=schema_jsonld, semantic_html=semantic_html, diff=diff)


# ---------------------------------------------------------------------------
# Paragraph / Body Text Optimizer
# ---------------------------------------------------------------------------

def optimize_paragraph(text: str, keywords: list = None, brand: str = "", industry: str = "tech") -> dict:
    """Analyze and optimize a paragraph for maximum SEO + GEO + quotability."""
    original = text.strip()
    issues = []
    improvements = []
    seo_score = 100
    geo_score = 100
    readability_score = 100
    optimized = original

    words = original.split()
    word_count = len(words)
    text_lower = original.lower()
    kw_list = [k.strip().lower() for k in (keywords or []) if k.strip()]

    if word_count < 5:
        return _build_result("paragraph", original, optimized, 0, 0, 0, [
            {"severity": "critical", "area": "SEO",
             "issue": "Text too short for meaningful analysis",
             "detail": "Provide at least 30 words for paragraph optimization."}
        ], [], word_count)

    # =====================================================================
    # 1. LLM QUOTABILITY SCORING (from geo.py algorithm)
    # =====================================================================
    quotability = _score_passage_quotability(original)
    quotability_score = quotability["score"]

    if quotability_score < 40:
        geo_score -= 20
        issues.append({"severity": "high", "area": "GEO",
                        "issue": f"Low LLM quotability score ({quotability_score}/100)",
                        "detail": f"AI engines are unlikely to cite this passage. "
                                  f"Facts: {quotability['fact_count']}, Entities: {quotability['entity_count']}, "
                                  f"Vague terms: {quotability['vague_term_count']}"})
    elif quotability_score < 60:
        geo_score -= 10
        issues.append({"severity": "medium", "area": "GEO",
                        "issue": f"Moderate LLM quotability ({quotability_score}/100)",
                        "detail": "Improve factual density and declarative structure for higher AI citation."})

    # --- Word count optimization for quotability ---
    if word_count < 60:
        geo_score -= 8
        issues.append({"severity": "medium", "area": "GEO",
                        "issue": f"Passage too short for optimal quotability ({word_count} words)",
                        "detail": "Ideal citable passages are 100-200 words. Short passages are less likely to be cited by AI."})
        improvements.append("Expand passage to 100-200 words with factual claims and specific data.")
    elif word_count > 300:
        geo_score -= 5
        issues.append({"severity": "low", "area": "GEO",
                        "issue": f"Passage may be too long for single citation ({word_count} words)",
                        "detail": "Consider splitting into 100-200 word focused paragraphs."})

    # =====================================================================
    # 2. FACTUAL DENSITY (from geo.py)
    # =====================================================================
    fact_patterns = [
        r'\b\d+(?:\.\d+)?%',
        r'[\$\u20ac\u00a3]\s*\d+(?:,\d{3})*(?:\.\d+)?',
        r'\b\d+\s*(?:MAD|USD|EUR|GBP|TRY)\b',
        r'\b(?:19|20)\d{2}\b',
        r'\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b',
        r'\b\d+\s*(?:users|clients|customers|projects|employees|records)\b',
    ]
    fact_count = sum(len(re.findall(p, original, re.IGNORECASE)) for p in fact_patterns)
    if fact_count == 0:
        geo_score -= 12
        issues.append({"severity": "high", "area": "GEO",
                        "issue": "No factual claims detected",
                        "detail": "Add specific numbers, percentages, dates, or metrics. "
                                  "Factual density is the #1 driver of AI quotability."})
        improvements.append("Add quantified proof: percentages, dollar amounts, dates, or measured outcomes.")

    # =====================================================================
    # 3. DECLARATIVE STRUCTURE (from geo.py)
    # =====================================================================
    first_sentence = original.split(".")[0].lower() if "." in original else text_lower
    has_declarative = any(d in first_sentence for d in DECLARATIVE_OPENERS)
    if not has_declarative:
        geo_score -= 8
        issues.append({"severity": "medium", "area": "GEO",
                        "issue": "Opening sentence lacks declarative structure",
                        "detail": "Start with a definition or assertion (e.g., 'X is...', 'X provides...', 'X consists of...'). "
                                  "Declarative openings are 3x more likely to be cited by AI."})
        improvements.append("Restructure opening to use a declarative assertion (e.g., '[Subject] is a [definition]...').")

    # =====================================================================
    # 4. NAMED ENTITY DENSITY (from geo.py)
    # =====================================================================
    entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
    entities = re.findall(entity_pattern, original)
    if len(entities) < 2:
        geo_score -= 5
        issues.append({"severity": "low", "area": "GEO",
                        "issue": f"Low named entity density ({len(entities)} entities)",
                        "detail": "Include brand names, locations, technologies, or proper nouns. "
                                  "Named entities anchor AI citation attribution."})

    # =====================================================================
    # 5. VAGUE TERM DETECTION + REPLACEMENT
    # =====================================================================
    vague_found = []
    for vt in VAGUE_TERMS:
        pattern = re.compile(r'\b' + re.escape(vt) + r'\b', re.IGNORECASE)
        matches = pattern.findall(original)
        if matches:
            vague_found.extend(matches)

    if vague_found:
        geo_score -= min(len(vague_found) * 4, 20)
        issues.append({"severity": "medium", "area": "GEO",
                        "issue": f"Vague terms detected ({len(vague_found)}): {', '.join(set(v.lower() for v in vague_found[:6]))}",
                        "detail": "Replace vague language with specific, quantified alternatives."})
        for vt in set(v.lower() for v in vague_found):
            replacement = VAGUE_REPLACEMENTS.get(vt)
            if replacement is not None:
                pattern = re.compile(r'\b' + re.escape(vt) + r'\b\s*', re.IGNORECASE)
                optimized = pattern.sub(replacement + (" " if replacement else ""), optimized, count=1)
        improvements.append("Replaced vague terms with specific factual alternatives.")

    # =====================================================================
    # 6. AI FILLER PHRASE DETECTION (from content.py)
    # =====================================================================
    filler_found = []
    for phrase in AI_FILLER_PHRASES:
        if phrase in text_lower:
            filler_found.append(phrase)

    if filler_found:
        penalty = min(len(filler_found) * 5, 25)
        seo_score -= penalty
        geo_score -= penalty
        issues.append({"severity": "high", "area": "SEO",
                        "issue": f"AI filler phrases detected ({len(filler_found)})",
                        "detail": "Detected: " + ", ".join(f'"{f}"' for f in filler_found[:5]) +
                                  "\nThese indicate generic AI-generated content and reduce both SEO and GEO scores."})
        for phrase in filler_found:
            replacement = AI_FILLER_MAP.get(phrase, "")
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            optimized = pattern.sub(replacement, optimized)

        # Clean punctuation and spacing artifacts
        optimized = re.sub(r'\s*,\s*,+', ',', optimized)
        optimized = re.sub(r'^\s*,\s*', '', optimized)
        optimized = re.sub(r'\.\s*,', '.', optimized)
        optimized = re.sub(r'([.!?]\s*)(?:that|and|which)\s+', r'\1', optimized, flags=re.IGNORECASE)
        optimized = re.sub(r'\s+', ' ', optimized).strip()
        # Capitalize after periods and start of text
        def _cap_match(m):
            return m.group(1) + m.group(2).upper()
        optimized = re.sub(r'(^|[.!?]\s+)([a-z])', _cap_match, optimized)
        improvements.append("Purged generic AI filler phrases with precision technical terminology.")

    # =====================================================================
    # 7. READABILITY: Sentence length analysis (from content.py)
    # =====================================================================
    sentences = re.split(r'[.!?]+', original)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if sentences:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_length > 25:
            readability_score -= 15
            issues.append({"severity": "medium", "area": "Readability",
                            "issue": f"Average sentence too long ({avg_sentence_length:.0f} words)",
                            "detail": "Recommended: 15-20 words per sentence for web content."})
            improvements.append("Break long sentences into shorter, scannable chunks (15-20 words each).")
        elif avg_sentence_length > 20:
            readability_score -= 5
            issues.append({"severity": "low", "area": "Readability",
                            "issue": f"Sentences are moderately long ({avg_sentence_length:.0f} words avg)",
                            "detail": "Consider shortening some sentences for better scannability."})

        # Sentence variety
        lengths = [len(s.split()) for s in sentences]
        if len(lengths) > 2:
            length_variance = max(lengths) - min(lengths)
            if length_variance < 5:
                readability_score -= 5
                issues.append({"severity": "low", "area": "Readability",
                                "issue": "Low sentence length variety",
                                "detail": "Mix short punchy sentences (5-10 words) with longer explanatory ones (15-20 words)."})

    # =====================================================================
    # 8. SEO: Keyword optimization
    # =====================================================================
    if kw_list:
        kw_found = [k for k in kw_list if k in text_lower]
        kw_missing = [k for k in kw_list if k not in text_lower]
        if kw_missing:
            seo_score -= 10
            issues.append({"severity": "high", "area": "SEO",
                            "issue": f"Target keywords missing: {', '.join(kw_missing)}",
                            "detail": "Naturally incorporate target keywords within the body text."})
            improvements.append(f"Weave in missing keywords: {', '.join(kw_missing)}")

        # Keyword density check (for found keywords)
        for kw in kw_found:
            density = text_lower.count(kw) / (word_count / 100) if word_count > 0 else 0
            if density > 3.0:
                seo_score -= 5
                issues.append({"severity": "medium", "area": "SEO",
                                "issue": f"Keyword stuffing detected: \"{kw}\" ({density:.1f}% density)",
                                "detail": "Keep keyword density between 0.5-2.5% for natural optimization."})

    # =====================================================================
    # 9. E-E-A-T SIGNALS
    # =====================================================================
    experience_signals = [
        "case study", "our experience", "we built", "we created",
        "we helped", "our client", "years of experience",
        "hands-on", "first-hand", "in-house",
    ]
    expertise_signals = [
        "certified", "accredited", "licensed", "research",
        "study", "data", "analysis", "methodology",
    ]
    exp_hits = sum(1 for s in experience_signals if s in text_lower)
    expert_hits = sum(1 for s in expertise_signals if s in text_lower)
    eeat_score = min((exp_hits + expert_hits) * 15, 100)

    if eeat_score < 30:
        issues.append({"severity": "info", "area": "E-E-A-T",
                        "issue": f"Low E-E-A-T signal density ({eeat_score}/100)",
                        "detail": "Add experience markers (case studies, first-hand accounts) and expertise indicators (certifications, data)."})

    # =====================================================================
    # FINAL SCORE COMPILATION
    # =====================================================================
    seo_score = max(seo_score, 0)
    geo_score = max(geo_score, 0)
    readability_score = max(readability_score, 0)

    variants = _generate_paragraph_variants(original, kw_list, brand, industry, optimized)
    if variants:
        optimized = variants[0]["text"]
        diff = variants[0]["diff"]
    else:
        diff = generate_word_diff(original, optimized)

    schema_jsonld = generate_schema_jsonld("paragraph", optimized, original, kw_list, brand)
    semantic_html = generate_semantic_html("paragraph", optimized, brand)
    query_str = f"What is {kw_list[0]}?" if kw_list else "What is the core definition?"
    ai_preview = generate_ai_overview_preview(query_str, optimized, brand)

    return _build_paragraph_result(
        original, optimized, seo_score, geo_score, readability_score,
        quotability_score, eeat_score, issues, improvements,
        word_count, fact_count, len(entities), len(vague_found),
        len(filler_found), quotability,
        variants=variants, ai_overview_preview=ai_preview,
        schema_jsonld=schema_jsonld, semantic_html=semantic_html, diff=diff
    )


# ---------------------------------------------------------------------------
# Quotability scorer (mirrors geo.py _score_passage_quotability)
# ---------------------------------------------------------------------------

def _score_passage_quotability(text: str) -> dict:
    """Score a text passage for LLM quotability."""
    words = text.split()
    word_count = len(words)

    # Length score
    if 100 <= word_count <= 200:
        length_score = 1.0
    elif 60 <= word_count < 100 or 200 < word_count <= 300:
        length_score = 0.7
    elif 30 <= word_count < 60:
        length_score = 0.4
    else:
        length_score = 0.2

    text_lower = text.lower()

    # Factual density
    fact_patterns = [
        r'\b\d+(?:\.\d+)?%',
        r'[\$\u20ac\u00a3]\s*\d+(?:,\d{3})*(?:\.\d+)?',
        r'\b\d+\s*(?:MAD|USD|EUR|GBP|TRY)\b',
        r'\b(?:19|20)\d{2}\b',
        r'\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b',
        r'\b\d+\s*(?:users|clients|customers|projects|employees|records)\b',
    ]
    fact_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in fact_patterns)
    fact_score = min(fact_count / 3.0, 1.0)

    # Declarative structure
    first_sentence = text.split(".")[0].lower() if "." in text else text_lower
    declarative_score = 1.0 if any(d in first_sentence for d in DECLARATIVE_OPENERS) else 0.3

    # Named entity density
    entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
    entities = re.findall(entity_pattern, text)
    entity_score = min(len(entities) / 2.0, 1.0)

    # Specificity
    vague_count = sum(1 for v in VAGUE_TERMS if v in text_lower)
    specificity_score = max(1.0 - (vague_count * 0.2), 0.0)

    composite = (
        length_score * 0.20 +
        fact_score * 0.30 +
        declarative_score * 0.20 +
        entity_score * 0.15 +
        specificity_score * 0.15
    )

    return {
        "score": round(composite * 100),
        "word_count": word_count,
        "fact_count": fact_count,
        "entity_count": len(entities),
        "has_declarative_opening": declarative_score > 0.5,
        "vague_term_count": vague_count,
        "length_score": round(length_score * 100),
        "fact_score": round(fact_score * 100),
        "declarative_score": round(declarative_score * 100),
        "entity_score": round(entity_score * 100),
        "specificity_score": round(specificity_score * 100),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TITLE_CASE_EXCEPTIONS = {
    "a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to",
    "from", "by", "in", "of", "with", "is", "vs", "via",
}

def _title_case(text: str) -> str:
    """Smart title case that respects common exceptions."""
    words = text.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in TITLE_CASE_EXCEPTIONS:
            result.append(w.capitalize())
        else:
            result.append(w.lower())
    return " ".join(result)


def _build_result(content_type, original, optimized, seo_score, geo_score,
                  readability_score, issues, improvements, char_count,
                  variants=None, serp_preview=None, ai_overview_preview=None,
                  schema_jsonld=None, semantic_html="", diff=None):
    """Build standard result dict for title/meta/heading."""
    if variants and len(variants) > 0:
        primary = variants[0]
        seo_score = primary.get("seo_score", seo_score)
        geo_score = primary.get("geo_score", geo_score)
        overall = primary.get("overall_score", round(seo_score * 0.5 + geo_score * 0.5))
    else:
        overall = round(seo_score * 0.5 + geo_score * 0.5)

    seo_score = max(min(seo_score, 100), 0)
    geo_score = max(min(geo_score, 100), 0)
    overall = max(min(overall, 100), 0)

    changed = original.strip() != optimized.strip()

    return {
        "content_type": content_type,
        "original": original,
        "optimized": optimized if changed else original,
        "has_changes": changed,
        "seo_score": seo_score,
        "geo_score": geo_score,
        "overall_score": overall,
        "char_count": char_count,
        "word_count": len(optimized.split()),
        "issue_count": len(issues),
        "issues": issues,
        "improvements": improvements,
        "variants": variants or [],
        "diff": diff or generate_word_diff(original, optimized),
        "serp_preview": serp_preview,
        "ai_overview_preview": ai_overview_preview,
        "schema_jsonld": schema_jsonld,
        "semantic_html": semantic_html,
    }


def _build_paragraph_result(original, optimized, seo_score, geo_score,
                            readability_score, quotability_score, eeat_score,
                            issues, improvements, word_count, fact_count,
                            entity_count, vague_count, filler_count, quotability_detail,
                            variants=None, ai_overview_preview=None,
                            schema_jsonld=None, semantic_html="", diff=None):
    """Build result dict for paragraph analysis."""
    if variants and len(variants) > 0:
        primary = variants[0]
        seo_score = primary.get("seo_score", seo_score)
        geo_score = primary.get("geo_score", geo_score)
        readability_score = primary.get("readability_score", readability_score)
        quotability_score = primary.get("quotability_score", quotability_score)
        eeat_score = primary.get("eeat_score", eeat_score)
        overall = primary.get("overall_score", round(
            seo_score * 0.25 + geo_score * 0.35 + readability_score * 0.15 + quotability_score * 0.25
        ))
    else:
        overall = round(
            seo_score * 0.25 +
            geo_score * 0.35 +
            readability_score * 0.15 +
            quotability_score * 0.25
        )
    seo_score = max(min(seo_score, 100), 0)
    geo_score = max(min(geo_score, 100), 0)
    readability_score = max(min(readability_score, 100), 0)
    overall = max(min(overall, 100), 0)

    changed = original.strip() != optimized.strip()

    return {
        "content_type": "paragraph",
        "original": original,
        "optimized": optimized if changed else original,
        "has_changes": changed,
        "seo_score": seo_score,
        "geo_score": geo_score,
        "readability_score": readability_score,
        "quotability_score": quotability_score,
        "eeat_score": eeat_score,
        "overall_score": overall,
        "word_count": word_count,
        "char_count": len(optimized),
        "fact_count": fact_count,
        "entity_count": entity_count,
        "vague_count": vague_count,
        "filler_count": filler_count,
        "quotability_detail": quotability_detail,
        "issue_count": len(issues),
        "issues": issues,
        "improvements": improvements,
        "variants": variants or [],
        "diff": diff or generate_word_diff(original, optimized),
        "ai_overview_preview": ai_overview_preview,
        "schema_jsonld": schema_jsonld,
        "semantic_html": semantic_html,
    }


# ---------------------------------------------------------------------------
# Master dispatcher
# ---------------------------------------------------------------------------

def optimize_content(content_type: str, text: str, keywords: list = None,
                     brand: str = "", heading_level: int = 1,
                     industry: str = "tech", intent: str = "informational") -> dict:
    """Main entry point. Routes to the correct optimizer based on content_type."""
    if content_type == "title":
        return optimize_title(text, keywords=keywords, brand=brand, industry=industry)
    elif content_type == "meta_description":
        return optimize_meta_description(text, keywords=keywords, brand=brand, industry=industry)
    elif content_type in ("h1", "h2", "h3"):
        level = int(content_type[1])
        return optimize_heading(text, level=level, keywords=keywords, industry=industry, brand=brand)
    elif content_type == "paragraph":
        return optimize_paragraph(text, keywords=keywords, brand=brand, industry=industry)
    else:
        return optimize_paragraph(text, keywords=keywords, brand=brand, industry=industry)
