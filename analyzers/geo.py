"""agy-seo: Advanced Generative Engine Optimization (GEO) & AI Search Analyzer.

Enhanced with:
- LLM Quotability Scoring (passage-level analysis)
- 5-Intent AEO Matrix (informational, navigational, commercial, transactional, local)
- Auto-generation of llms.txt and llms-full.txt content
- Deeper AI search crawler analysis
"""

import re
import math
from urllib.parse import urlparse
from utils import clamp_score, AI_CRAWLERS, is_bot_blocked


# ---------------------------------------------------------------------------
# LLM Quotability Scorer
# ---------------------------------------------------------------------------

def _score_passage_quotability(text: str) -> dict:
    """Score a text passage for LLM quotability (how likely an AI will cite it).
    
    Ideal citable passages are 134-167 words, contain factual claims,
    use declarative structure, and include named entities.
    """
    words = text.split()
    word_count = len(words)
    
    # Length score: ideal is 134-167 words
    if 100 <= word_count <= 200:
        length_score = 1.0
    elif 60 <= word_count < 100 or 200 < word_count <= 300:
        length_score = 0.7
    elif 30 <= word_count < 60:
        length_score = 0.4
    else:
        length_score = 0.2
    
    text_lower = text.lower()
    
    # Factual density: numbers, percentages, dates, currencies
    fact_patterns = [
        r'\b\d+(?:\.\d+)?%',                       # 95%, 4.5%
        r'[\$€£]\s*\d+(?:,\d{3})*(?:\.\d+)?',      # $500, €1,200
        r'\b\d+\s*(?:MAD|USD|EUR|GBP|TRY)\b',       # Currency codes
        r'\b(?:19|20)\d{2}\b',                      # Years
        r'\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b',
        r'\b\d+\s*(?:users|clients|customers|projects|employees|records)\b',
    ]
    fact_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in fact_patterns)
    fact_score = min(fact_count / 3.0, 1.0)
    
    # Declarative structure: starts with a definition or assertion
    declarative_openers = [
        " is ", " are ", " refers to ", " defined as ", " provides ",
        " consists of ", " includes ", " specializes in ", " operates as ",
        " delivers ", " features ", " measures ", " represents ",
        " was founded ", " established in ", " offers ", " enables "
    ]
    first_sentence = text.split(".")[0].lower() if "." in text else text_lower
    declarative_score = 1.0 if any(d in first_sentence for d in declarative_openers) else 0.3
    
    # Named entity density: capitalized multi-word phrases
    entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
    entities = re.findall(entity_pattern, text)
    entity_score = min(len(entities) / 2.0, 1.0)
    
    # Specificity: avoids vague language
    vague_terms = ["various", "many", "some", "often", "usually", "generally",
                   "sometimes", "possibly", "might", "could", "seems", "perhaps"]
    vague_count = sum(1 for v in vague_terms if v in text_lower)
    specificity_score = max(1.0 - (vague_count * 0.2), 0.0)
    
    # Composite score
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
    }


def _analyze_quotability(body_text: str) -> dict:
    """Analyze entire page for LLM quotability across all passages."""
    # Split into paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\r\n\s*\r\n', body_text) if len(p.strip()) > 50]
    if not paragraphs:
        # Fall back to sentence-level splitting
        sentences = re.split(r'[.!?]\s+', body_text)
        # Group sentences into ~150-word chunks
        chunk, chunks = [], []
        for s in sentences:
            chunk.append(s)
            if len(" ".join(chunk).split()) >= 120:
                chunks.append(" ".join(chunk))
                chunk = []
        if chunk:
            chunks.append(" ".join(chunk))
        paragraphs = [c for c in chunks if len(c.split()) >= 30]
    
    if not paragraphs:
        return {"overall_score": 0, "passages": [], "citable_count": 0, "total_count": 0, "citable_ratio": 0.0, "avg_passage_words": 0}
    
    passage_scores = []
    for p in paragraphs[:20]:  # Limit to first 20 passages
        result = _score_passage_quotability(p)
        result["text_preview"] = p[:200] + "..." if len(p) > 200 else p
        passage_scores.append(result)
    
    citable = [p for p in passage_scores if p["score"] >= 60]
    avg_score = sum(p["score"] for p in passage_scores) / len(passage_scores) if passage_scores else 0
    citable_ratio = len(citable) / len(passage_scores) if passage_scores else 0.0
    avg_words = round(sum(p.get("word_count", 0) for p in passage_scores) / len(passage_scores)) if passage_scores else 0
    
    return {
        "overall_score": round(avg_score),
        "passages": passage_scores,
        "citable_count": len(citable),
        "total_count": len(passage_scores),
        "citable_ratio": citable_ratio,
        "avg_passage_words": avg_words,
    }


# ---------------------------------------------------------------------------
# 5-Intent AEO Matrix
# ---------------------------------------------------------------------------

def _classify_page_intent(page_data: dict) -> dict:
    """Classify page into the 5-intent AEO matrix and score readiness for each.
    
    Intents: informational, navigational, commercial, transactional, local
    """
    body_text = page_data.get("body_text", "").lower()
    title = page_data.get("title", "").lower()
    url = page_data.get("url", "").lower()
    h1s = [h.lower() for h in page_data.get("h1", [])]
    h2s = [h.lower() for h in page_data.get("h2", [])]
    schema = page_data.get("schema", [])
    forms = page_data.get("forms", [])
    
    word_count = page_data.get("word_count", 0)
    all_headings = " ".join(h1s + h2s)
    
    scores = {}
    
    # --- Informational Intent ---
    info_score = 0
    info_signals = []
    # Long-form content
    if word_count >= 800:
        info_score += 25
        info_signals.append(f"Long-form content ({word_count} words)")
    elif word_count >= 400:
        info_score += 15
    # Question headings
    question_headings = [h for h in h2s if h.strip().endswith("?") or 
                          any(h.strip().startswith(q) for q in ["what", "how", "why", "when", "where", "who"])]
    if question_headings:
        info_score += 25
        info_signals.append(f"{len(question_headings)} question-based headings")
    # Educational keywords
    edu_kw = ["guide", "tutorial", "how to", "what is", "learn", "understand", "explained", "overview", "introduction"]
    edu_matches = [k for k in edu_kw if k in body_text or k in title or k in all_headings]
    if edu_matches:
        info_score += 20
        info_signals.append(f"Educational keywords: {', '.join(edu_matches[:3])}")
    # Article/BlogPosting schema
    article_schemas = [s for s in schema if isinstance(s, dict) and s.get("@type") in ("Article", "BlogPosting", "HowTo", "FAQPage")]
    if article_schemas:
        info_score += 15
        info_signals.append("Article/Blog schema present")
    # Lists and structure
    if "<ol" in page_data.get("body_text", "") or "<ul" in page_data.get("body_text", ""):
        info_score += 10
    scores["informational"] = {"score": min(info_score, 100), "signals": info_signals}
    
    # --- Navigational Intent ---
    nav_score = 0
    nav_signals = []
    # Brand mentions in title/H1
    brand_in_title = any(h.strip() == title.strip() for h in h1s) if h1s else False
    # Homepage indicators
    path = urlparse(page_data.get("url", "")).path
    if path in ("/", ""):
        nav_score += 30
        nav_signals.append("Homepage (root path)")
    # Contact/about pages
    if any(k in url for k in ["/about", "/contact", "/team", "/our-"]):
        nav_score += 25
        nav_signals.append("Brand navigation page")
    # Organization schema
    org_schemas = [s for s in schema if isinstance(s, dict) and s.get("@type") in ("Organization", "LocalBusiness", "Corporation")]
    if org_schemas:
        nav_score += 20
        nav_signals.append("Organization schema present")
    # Social links
    og = page_data.get("open_graph", {})
    if og:
        nav_score += 10
        nav_signals.append("Open Graph metadata present")
    scores["navigational"] = {"score": min(nav_score, 100), "signals": nav_signals}
    
    # --- Commercial Intent ---
    comm_score = 0
    comm_signals = []
    # Comparison/review keywords
    comm_kw = ["best", "top", "compare", "comparison", "review", "vs", "alternative", "pricing", "plan", "features"]
    comm_matches = [k for k in comm_kw if k in body_text or k in title or k in all_headings]
    if comm_matches:
        comm_score += 30
        comm_signals.append(f"Commercial keywords: {', '.join(comm_matches[:3])}")
    # Product/Service schema
    product_schemas = [s for s in schema if isinstance(s, dict) and s.get("@type") in ("Product", "Service", "Offer", "AggregateOffer")]
    if product_schemas:
        comm_score += 25
        comm_signals.append("Product/Service schema present")
    # Pricing tables
    if any(k in body_text for k in ["pricing", "price", "cost", "fee", "starting at", "$", "€", "£"]):
        comm_score += 20
        comm_signals.append("Pricing-related content detected")
    # Tables (comparison)
    if "<table" in page_data.get("body_text", "").lower():
        comm_score += 15
        comm_signals.append("Comparison tables present")
    scores["commercial"] = {"score": min(comm_score, 100), "signals": comm_signals}
    
    # --- Transactional Intent ---
    trans_score = 0
    trans_signals = []
    # CTAs and conversion elements
    cta_kw = ["buy", "order", "purchase", "add to cart", "book now", "sign up", "register",
              "subscribe", "get started", "free trial", "download", "apply", "request", "appointment"]
    cta_matches = [k for k in cta_kw if k in body_text or k in title]
    if cta_matches:
        trans_score += 30
        trans_signals.append(f"CTA keywords: {', '.join(cta_matches[:3])}")
    # Forms
    if forms:
        trans_score += 25
        trans_signals.append(f"{len(forms)} form(s) detected")
    # E-commerce schema
    ecomm_schemas = [s for s in schema if isinstance(s, dict) and s.get("@type") in ("Product", "Offer", "Order")]
    if ecomm_schemas:
        trans_score += 20
        trans_signals.append("E-commerce schema present")
    # Button/CTA detection in URL
    if any(k in url for k in ["/checkout", "/cart", "/order", "/book", "/register", "/signup"]):
        trans_score += 25
        trans_signals.append("Transactional URL path")
    scores["transactional"] = {"score": min(trans_score, 100), "signals": trans_signals}
    
    # --- Local Intent ---
    local_score = 0
    local_signals = []
    # Address/location keywords
    local_kw = ["address", "location", "directions", "map", "near me", "hours", "opening hours",
                "phone", "call us", "visit us", "our office", "our clinic", "our store"]
    local_matches = [k for k in local_kw if k in body_text]
    if local_matches:
        local_score += 25
        local_signals.append(f"Location signals: {', '.join(local_matches[:3])}")
    # LocalBusiness schema
    local_schemas = [s for s in schema if isinstance(s, dict) and s.get("@type") in 
                     ("LocalBusiness", "MedicalClinic", "Hospital", "Restaurant", "Store", 
                      "Dentist", "RealEstateAgent", "LegalService", "FinancialService")]
    if local_schemas:
        local_score += 30
        local_signals.append("LocalBusiness schema present")
    # Geo coordinates
    geo_schemas = [s for s in schema if isinstance(s, dict) and ("geo" in str(s).lower() or "address" in str(s).lower())]
    if geo_schemas:
        local_score += 20
        local_signals.append("Geographic coordinates in schema")
    # Phone number patterns
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
    if re.search(phone_pattern, body_text):
        local_score += 15
        local_signals.append("Phone number detected")
    # Map embeds
    html = page_data.get("body_text", "")
    if "google.com/maps" in html or "maps.googleapis" in html:
        local_score += 10
        local_signals.append("Google Maps embed detected")
    scores["local"] = {"score": min(local_score, 100), "signals": local_signals}
    
    # Determine primary intent
    primary_intent = max(scores, key=lambda k: scores[k]["score"])
    
    return {
        "intents": scores,
        "primary_intent": primary_intent,
        "primary_score": scores[primary_intent]["score"],
    }


# ---------------------------------------------------------------------------
# llms.txt Auto-Generator
# ---------------------------------------------------------------------------

def _generate_llms_txt(page_data: dict, domain: str) -> str:
    """Auto-generate llms.txt content based on page analysis."""
    title = page_data.get("title", domain)
    h1s = page_data.get("h1", [])
    h2s = page_data.get("h2", [])
    body_text = page_data.get("body_text", "")
    schema = page_data.get("schema", [])
    url = page_data.get("url", "")
    links = page_data.get("links", {})
    internal = links.get("internal", [])
    
    # Extract organization name from schema
    org_name = domain
    for s in schema:
        if isinstance(s, dict) and s.get("@type") in ("Organization", "LocalBusiness", "Corporation",
                                                        "MedicalOrganization", "ProfessionalService"):
            org_name = s.get("name", domain)
            break
    
    # Extract description
    meta_desc = page_data.get("meta_description", "")
    description = meta_desc if meta_desc else (body_text[:200].strip() + "..." if body_text else "")
    
    # Build sections from headings and links
    sections = []
    for link in internal[:15]:
        text = link.get("text", "").strip()
        href = link.get("href", "")
        if text and href and len(text) > 2:
            sections.append(f"- [{text}]({href}): {text}")
    
    llms_txt = f"""# {org_name}

> {description}

## Core Pages
{chr(10).join(sections[:10]) if sections else '- [Homepage](' + url + '): Main page'}

## About
- [Contact]({url.rstrip("/")}/contact): Get in touch
- [About]({url.rstrip("/")}/about): Learn more about {org_name}
"""
    return llms_txt


def _generate_llms_full_txt(page_data: dict, domain: str, all_pages_data: dict = None) -> str:
    """Auto-generate llms-full.txt content with comprehensive site information."""
    title = page_data.get("title", domain)
    body_text = page_data.get("body_text", "")
    schema = page_data.get("schema", [])
    url = page_data.get("url", "")
    
    org_name = domain
    org_desc = ""
    for s in schema:
        if isinstance(s, dict) and s.get("@type") in ("Organization", "LocalBusiness", "Corporation"):
            org_name = s.get("name", domain)
            org_desc = s.get("description", "")
            break
    
    if not org_desc:
        org_desc = page_data.get("meta_description", body_text[:300] if body_text else "")
    
    content = f"""# {org_name} — Complete Information

> {org_desc}

## Overview
{body_text[:500] if body_text else 'No content available.'}

## Site Structure
"""
    
    if all_pages_data:
        for pg_url, pg_info in list(all_pages_data.items())[:30]:
            if pg_info.get("parsed"):
                pg_title = pg_info["parsed"].get("title", pg_url)
                pg_desc = pg_info["parsed"].get("meta_description", "")
                content += f"- [{pg_title}]({pg_url}): {pg_desc[:100]}\n"
    
    return content


# ---------------------------------------------------------------------------
# Main Analyzer
# ---------------------------------------------------------------------------

def analyze_geo(page_data: dict, fetch_data: dict, robots_data: dict,
                all_pages: dict = None) -> dict:
    """Analyze Generative Engine Optimization (GEO) / AI Search readiness.
    
    Enhanced with LLM quotability scoring, 5-intent AEO matrix,
    and llms.txt/llms-full.txt auto-generation.
    """
    findings = []
    fixes = []
    score = 100

    url = page_data["url"]
    domain = urlparse(url).netloc
    body_text = page_data.get("body_text", "")
    word_count = page_data.get("word_count", 0)
    h1s = page_data.get("h1", [])
    h2s = page_data.get("h2", [])
    h3s = page_data.get("h3", [])
    schema = page_data.get("schema", [])
    html = fetch_data.get("html", "")
    headers = fetch_data.get("headers", {})

    # -------------------------------------------------------------------
    # 1. AI Search Crawler Permissions (robots.txt)
    # -------------------------------------------------------------------
    search_bots_blocked = []
    training_bots_blocked = []
    for bot_name, bot_info in AI_CRAWLERS.items():
        blocked = is_bot_blocked(robots_data, bot_name)
        if blocked:
            if bot_info.get("search", False):
                search_bots_blocked.append(bot_name)
            else:
                training_bots_blocked.append(bot_name)

    if search_bots_blocked:
        penalty = min(len(search_bots_blocked) * 15, 35)
        score -= penalty
        findings.append({
            "category": "AI Crawler Access",
            "severity": "critical",
            "issue": f"{len(search_bots_blocked)} AI search crawlers explicitly blocked in robots.txt",
            "detail": f"Blocked crawlers: {', '.join(search_bots_blocked)}. "
                      f"Blocking these bots completely eliminates visibility in SearchGPT, Perplexity, and AI Search results.",
        })
        fixes.append({
            "issue": "Unblock AI Search Bots",
            "fix": "Update robots.txt to explicitly allow AI search engines while optionally controlling training bots:\n\n"
                   + "\n".join(f"User-agent: {bot}\nAllow: /" for bot in search_bots_blocked)
                   + "\n\n# Note: Training-only bots (e.g. CCBot, anthropic-ai) can remain restricted if desired.",
        })

    # -------------------------------------------------------------------
    # 2. Emerging AI Standards: /llms.txt and /llms-full.txt
    # -------------------------------------------------------------------
    has_llms_txt = "llms.txt" in html.lower() or "llms-full.txt" in html.lower()
    if not has_llms_txt:
        score -= 5
        generated_llms = _generate_llms_txt(page_data, domain)
        findings.append({
            "category": "AI Standards",
            "severity": "medium",
            "issue": "No llms.txt standard detected",
            "detail": "llms.txt is the emerging standard (similar to robots.txt) for providing markdown-structured "
                      "site summaries directly to LLM crawlers and AI search engines.",
        })
        fixes.append({
            "issue": "Create /llms.txt for AI Search Engines",
            "fix": f"Place an llms.txt file at your domain root (e.g. https://{domain}/llms.txt):\n\n"
                   f"{generated_llms}\n\n"
                   f"Also create /llms-full.txt with comprehensive site information for deep-context retrieval.",
        })

    # -------------------------------------------------------------------
    # 3. LLM Quotability Analysis (NEW)
    # -------------------------------------------------------------------
    quotability = _analyze_quotability(body_text)
    
    if quotability["overall_score"] < 40 and word_count > 150:
        score -= 15
        findings.append({
            "category": "LLM Quotability",
            "severity": "critical",
            "issue": f"Very low LLM quotability score ({quotability['overall_score']}/100) — AI engines unlikely to cite this content",
            "detail": f"Analyzed {quotability['total_count']} passages. Only {quotability['citable_count']} "
                      f"meet the minimum quotability threshold (60+). Content lacks factual density, "
                      f"declarative structure, and named entities that AI systems need to form citations.",
        })
        fixes.append({
            "issue": "Improve LLM Quotability Score",
            "fix": "Restructure content into AI-citable passages (134-167 words each):\n\n"
                   "1. Start each key paragraph with a declarative definition:\n"
                   "   '[Subject] is a [category] that [primary function]. It was [founded/established] in [year].'\n\n"
                   "2. Include at least 3 quantifiable facts per section:\n"
                   "   'Reduces processing time by 42%, serving 500+ clients across 12 countries since 2018.'\n\n"
                   "3. Use named entities (proper nouns, brand names, location names) rather than pronouns:\n"
                   "   Before: 'We provide good service in the area.'\n"
                   "   After: 'InersiaLab delivers enterprise software solutions across Morocco and MENA region.'\n\n"
                   "4. Avoid vague qualifiers (various, many, some, often) — replace with specifics.\n\n"
                   "5. Structure each passage as: Claim → Evidence → Context (CEC pattern).",
        })
    elif quotability["overall_score"] < 60 and word_count > 150:
        score -= 8
        findings.append({
            "category": "LLM Quotability",
            "severity": "high",
            "issue": f"Below-average LLM quotability ({quotability['overall_score']}/100) — {quotability['citable_count']}/{quotability['total_count']} passages meet citation threshold",
            "detail": "Content has some citable passages but lacks consistent factual density and declarative structure.",
        })
        fixes.append({
            "issue": "Boost LLM Quotability to 60+",
            "fix": "Enhance existing passages with quantifiable facts and declarative openings:\n"
                   "- Add 2-3 statistics per section (percentages, counts, dates)\n"
                   "- Begin key sections with 'X is...' or 'X provides...' structure\n"
                   "- Replace vague language with specific claims",
        })

    # -------------------------------------------------------------------
    # 4. 5-Intent AEO Matrix (NEW)
    # -------------------------------------------------------------------
    intent_analysis = _classify_page_intent(page_data)
    primary = intent_analysis["primary_intent"]
    primary_score = intent_analysis["primary_score"]
    
    # Check if primary intent has adequate optimization
    if primary_score < 40:
        score -= 10
        findings.append({
            "category": "AEO Intent Matrix",
            "severity": "high",
            "issue": f"Weak primary intent signal: '{primary}' scores only {primary_score}/100",
            "detail": "The page does not strongly signal any of the 5 search intents "
                      "(informational, navigational, commercial, transactional, local). "
                      "AI search engines use intent classification to determine which queries to surface content for.",
        })
        
        intent_fixes = {
            "informational": "Add question-based H2 headings, expand content to 800+ words, add FAQ schema, "
                           "include step-by-step guides or definition lists",
            "navigational": "Add Organization schema with sameAs links, ensure brand name in title and H1, "
                          "add Open Graph metadata for social sharing",
            "commercial": "Add comparison tables, pricing sections, Product/Service schema, "
                        "feature lists with specifics, and customer review aggregates",
            "transactional": "Add clear CTA buttons, booking/contact forms, Offer/Product schema with prices, "
                           "and action-oriented headlines",
            "local": "Add LocalBusiness schema with address, phone, hours, embed Google Maps, "
                    "include city/neighborhood names in content",
        }
        
        fixes.append({
            "issue": f"Strengthen '{primary}' intent signals",
            "fix": f"Based on the AEO 5-Intent Matrix, this page's strongest signal is '{primary}' "
                   f"but it scores only {primary_score}/100.\n\n"
                   f"To strengthen for '{primary}' queries:\n{intent_fixes.get(primary, '')}\n\n"
                   "Intent scores breakdown:\n" + 
                   "\n".join(f"  - {k.title()}: {v['score']}/100" 
                            for k, v in intent_analysis["intents"].items()),
        })

    # Check for completely unoptimized secondary intents that could be valuable
    zero_intents = [k for k, v in intent_analysis["intents"].items() 
                    if v["score"] == 0 and k != primary]
    if len(zero_intents) >= 3:
        findings.append({
            "category": "AEO Intent Matrix",
            "severity": "medium",
            "issue": f"{len(zero_intents)} search intents have zero optimization: {', '.join(zero_intents)}",
            "detail": "Pages that signal multiple intents capture broader AI search query coverage.",
        })

    # -------------------------------------------------------------------
    # 5. Information Density & Statistical Citability
    # -------------------------------------------------------------------
    stat_patterns = [
        r'\b\d+(?:\.\d+)?%',
        r'[\$€£]\s*\d+(?:,\d{3})*(?:\.\d+)?',
        r'\b\d+\s*(?:MAD|USD|EUR|GBP)\b',
        r'\b(?:19|20)\d{2}\b',
        r'\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b',
        r'\b\d+\s*(?:users|clients|customers|projects|employees|members|records|downloads|reviews)\b',
    ]
    
    total_stat_matches = 0
    for pat in stat_patterns:
        matches = re.findall(pat, body_text, re.IGNORECASE)
        total_stat_matches += len(matches)

    if total_stat_matches < 3 and word_count > 150:
        score -= 10
        findings.append({
            "category": "Information Density",
            "severity": "high",
            "issue": f"Low empirical data density ({total_stat_matches} factual data points detected)",
            "detail": "Generative AI systems prioritize citing statements backed by quantifiable numbers, "
                      "percentages, performance statistics, and verified dates rather than vague qualitative prose.",
        })
        fixes.append({
            "issue": "Enrich Content with Quantifiable Metrics",
            "fix": "Add precise numerical facts, benchmarks, or case study metrics to your copy:\n"
                   "Before: 'We deliver fast results and improve efficiency.'\n"
                   "After: 'We reduce latency by 42% and deliver implementation within 14 business days.'",
        })

    # -------------------------------------------------------------------
    # 6. Direct Answer Extraction (Definitional Openings)
    # -------------------------------------------------------------------
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\r\n\s*\r\n', body_text) if len(p.strip()) > 30]
    if not paragraphs:
        sentences = re.split(r'[.!?]\s+', body_text)
        paragraphs = [s.strip() for s in sentences if len(s.strip()) > 20]

    direct_answers = 0
    for p in paragraphs[:6]:
        words = p.split()
        first_40 = " ".join(words[:40]).lower()
        if any(kw in first_40 for kw in [
            " is ", " are ", " defined as ", " refers to ", " provides ",
            " consists of ", " includes ", " specializes in ", " operates as ",
            " delivers ", " features "
        ]):
            direct_answers += 1

    if paragraphs and direct_answers < 2:
        score -= 10
        findings.append({
            "category": "Direct Answers",
            "severity": "high",
            "issue": "Absence of direct answer definitions in opening paragraphs",
            "detail": f"Only {direct_answers} of the top sections begin with a direct definition or declarative answer. "
                      "AI search engines extract 30-50 word definitional snippets for direct answers.",
        })
        fixes.append({
            "issue": "Lead Sections with Direct Definitional Statements",
            "fix": "Structure key sections using the Inverted Pyramid method:\n"
                   "1. Open the paragraph with a concise 30-word declarative definition.\n"
                   "2. Follow with supporting technical details and operational context.\n"
                   "Example: '[Subject] is a [category] designed to [primary function]. It works by [mechanism]...'",
        })

    # -------------------------------------------------------------------
    # 7. Conversational & Question-Based Headings
    # -------------------------------------------------------------------
    all_headings = h2s + h3s
    question_headings = [
        h for h in all_headings
        if h.strip().endswith("?") or any(
            h.strip().lower().startswith(q)
            for q in ["what", "how", "why", "when", "where", "who", "which", "can", "should", "does", "is", "are"]
        )
    ]

    if all_headings and not question_headings:
        score -= 10
        findings.append({
            "category": "Query Matching",
            "severity": "medium",
            "issue": "Zero question-based headings found across the page",
            "detail": "Natural language user queries to AI search engines (ChatGPT, Perplexity) typically use full questions. "
                      "Formatting subheadings as questions significantly increases retrieval frequency.",
        })
        fixes.append({
            "issue": "Incorporate Question-Formatted Headings",
            "fix": "Convert at least 25% of H2/H3 subheadings into explicit user questions:\n"
                   + "\n".join(f"Current: <h2>{h}</h2> -> Suggested: <h2>What is {h}?</h2> or <h2>How does {h} work?</h2>" for h in all_headings[:2]),
        })

    # -------------------------------------------------------------------
    # 8. Entity Grounding & Knowledge Graph Authority (sameAs Links)
    # -------------------------------------------------------------------
    org_schemas = [
        s for s in schema
        if isinstance(s, dict) and s.get("@type") in (
            "Organization", "LocalBusiness", "MedicalOrganization", "Corporation",
            "ProfessionalService", "MedicalClinic", "Hospital"
        )
    ]
    
    same_as_links = []
    for org in org_schemas:
        sa = org.get("sameAs", [])
        if isinstance(sa, str):
            same_as_links.append(sa)
        elif isinstance(sa, list):
            same_as_links.extend(sa)

    recognized_authorities = {"wikidata.org", "wikipedia.org", "linkedin.com", "crunchbase.com", "github.com", "youtube.com"}
    has_authoritative_link = any(any(auth in link.lower() for auth in recognized_authorities) for link in same_as_links)

    if not same_as_links:
        score -= 15
        findings.append({
            "category": "Entity Resolution",
            "severity": "high",
            "issue": "Missing sameAs authority links in Organization schema",
            "detail": "AI engines use Wikidata, Wikipedia, LinkedIn, and Crunchbase profiles to resolve entities "
                      "in their Knowledge Graphs. Missing sameAs links weakens AI brand identification.",
        })
        fixes.append({
            "issue": "Add Knowledge Graph sameAs Links",
            "fix": "Include verified social and corporate profile URIs in your Organization JSON-LD:\n\n"
                   '{\n'
                   '  "@context": "https://schema.org",\n'
                   '  "@type": "Organization",\n'
                   '  "name": "Your Brand",\n'
                   '  "url": "https://yourdomain.com",\n'
                   '  "sameAs": [\n'
                   '    "https://www.linkedin.com/company/yourcompany",\n'
                   '    "https://www.wikidata.org/wiki/QXXXXX",\n'
                   '    "https://www.crunchbase.com/organization/yourcompany",\n'
                   '    "https://twitter.com/yourhandle"\n'
                   '  ]\n'
                   '}',
        })
    elif not has_authoritative_link:
        score -= 8
        findings.append({
            "category": "Entity Resolution",
            "severity": "medium",
            "issue": "Organization sameAs contains no authoritative knowledge graph source",
            "detail": "Include primary authority profiles (Wikidata, Wikipedia, LinkedIn, Crunchbase) to anchor entity disambiguation.",
        })

    # -------------------------------------------------------------------
    # 9. Structured Tables and Comparison Matrices
    # -------------------------------------------------------------------
    has_tables = "<table" in html.lower()
    has_definition_lists = "<dl" in html.lower()
    has_lists = "<ul" in html.lower() or "<ol" in html.lower()

    if not has_tables and not has_definition_lists and word_count > 300:
        score -= 5
        findings.append({
            "category": "Structured Formatting",
            "severity": "medium",
            "issue": "No structured comparison tables or definition lists present",
            "detail": "Generative models frequently extract tables and definition lists (<dl>, <dt>, <dd>) "
                      "for comparative queries and direct summary blocks.",
        })
        fixes.append({
            "issue": "Format Technical Comparisons in HTML Tables",
            "fix": "Present features, pricing, or specifications in clean semantic HTML tables (<table>) "
                   "with proper <th> header rows and structured rows.",
        })

    # -------------------------------------------------------------------
    # 10. Content Freshness & Temporal Metadata
    # -------------------------------------------------------------------
    date_published = page_data.get("date_published") or ""
    date_modified = page_data.get("date_modified") or ""
    has_date_signal = bool(date_published or date_modified)

    if not has_date_signal:
        has_article_date = bool(re.search(r'article:(?:published_time|modified_time)', html, re.IGNORECASE))
        has_schema_date = any("dateModified" in str(s) or "datePublished" in str(s) for s in schema)
        if not (has_article_date or has_schema_date):
            score -= 10
            findings.append({
                "category": "Temporal Freshness",
                "severity": "high",
                "issue": "Missing explicit publication and modification timestamps",
                "detail": "AI search engines prioritize up-to-date information and require explicit ISO timestamps "
                          "(datePublished, dateModified) to verify source freshness.",
            })
            fixes.append({
                "issue": "Add ISO Timestamps in Meta and Schema",
                "fix": "Add both meta tags and JSON-LD date properties:\n"
                       '<meta property="article:published_time" content="2026-01-15T08:00:00Z">\n'
                       '<meta property="article:modified_time" content="2026-09-14T12:00:00Z">\n\n'
                       'And in JSON-LD:\n"datePublished": "2026-01-15T08:00:00Z",\n"dateModified": "2026-09-14T12:00:00Z"',
            })

    # -------------------------------------------------------------------
    # 11. Server-Side Rendering (SSR) Verification for AI Crawlers
    # -------------------------------------------------------------------
    spa_signals = 0
    if '<div id="root"></div>' in html or '<div id="app"></div>' in html:
        spa_signals += 1
    if "<noscript>" in html and "javascript" in html.lower():
        spa_signals += 1
    if word_count < 80 and len(page_data.get("scripts", [])) > 5:
        spa_signals += 1

    if spa_signals >= 2:
        score -= 20
        findings.append({
            "category": "AI Accessibility",
            "severity": "critical",
            "issue": "Client-Side Rendered (CSR) Single-Page Application detected",
            "detail": "Many AI crawlers (including PerplexityBot and Claude-SearchBot) do not execute heavy JavaScript. "
                      "Pages relying strictly on client-side rendering return empty shells to AI scrapers.",
        })
        fixes.append({
            "issue": "Implement Server-Side Rendering (SSR) or Prerendering",
            "fix": "Implement Server-Side Rendering (Next.js, Nuxt, Astro) or dynamic prerendering for bot user-agents "
                   "to ensure pure HTML text is delivered on the initial HTTP response.",
        })

    # Compute platform-specific readiness scores
    platform_scores = {
        "SearchGPT / OpenAI": clamp_score(score - (20 if "OAI-SearchBot" in search_bots_blocked or "GPTBot" in search_bots_blocked else 0)),
        "Perplexity AI": clamp_score(score - (20 if "PerplexityBot" in search_bots_blocked else 0)),
        "Google AI Overviews": clamp_score(score - (15 if "Google-Extended" in search_bots_blocked else 0)),
        "Anthropic Claude": clamp_score(score - (20 if "Claude-SearchBot" in search_bots_blocked or "ClaudeBot" in search_bots_blocked else 0)),
    }

    # Generate llms.txt content for remediation
    generated_llms_txt = _generate_llms_txt(page_data, domain)
    generated_llms_full_txt = _generate_llms_full_txt(page_data, domain, all_pages)

    return {
        "analyzer": "geo",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
        "platform_scores": platform_scores,
        "search_bots_blocked": search_bots_blocked,
        "training_bots_blocked": training_bots_blocked,
        "has_llms_txt": has_llms_txt,
        "data_points_found": total_stat_matches,
        # NEW: Enhanced analysis data
        "quotability": quotability,
        "intent_analysis": intent_analysis,
        "generated_llms_txt": generated_llms_txt,
        "generated_llms_full_txt": generated_llms_full_txt,
    }
