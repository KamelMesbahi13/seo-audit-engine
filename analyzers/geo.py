"""agy-seo: Advanced Generative Engine Optimization (GEO) & AI Search Analyzer."""

import re
from utils import clamp_score, AI_CRAWLERS, is_bot_blocked


def analyze_geo(page_data: dict, fetch_data: dict, robots_data: dict) -> dict:
    """Analyze Generative Engine Optimization (GEO) / AI Search readiness.
    
    Evaluates how effectively the page can be parsed, understood, and cited by
    generative AI search systems (SearchGPT, Google AI Overviews, Perplexity, Claude).
    """
    findings = []
    fixes = []
    score = 100

    url = page_data["url"]
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
        findings.append({
            "category": "AI Standards",
            "severity": "medium",
            "issue": "No llms.txt standard detected",
            "detail": "llms.txt is the emerging standard (similar to robots.txt) for providing markdown-structured "
                      "site summaries directly to LLM crawlers and AI search engines.",
        })
        fixes.append({
            "issue": "Create /llms.txt for AI Search Engines",
            "fix": "Place an llms.txt file at your domain root (e.g. https://yourdomain.com/llms.txt):\n\n"
                   "# Brand Name\n\n"
                   "> Concise 1-2 sentence description of company and core offerings.\n\n"
                   "## Core Capabilities\n"
                   "- [Service or Product A](https://yourdomain.com/service-a): Full capabilities and specifications\n"
                   "- [Service or Product B](https://yourdomain.com/service-b): Technical specifications and use cases\n\n"
                   "## Documentation & Contact\n"
                   "- [About](https://yourdomain.com/about): Background, founders, and credentials\n"
                   "- [Contact](https://yourdomain.com/contact): Direct contact channels",
        })

    # -------------------------------------------------------------------
    # 3. Information Density & Statistical Citability (Facts & Data Points)
    # -------------------------------------------------------------------
    stat_patterns = [
        r'\b\d+(?:\.\d+)?%',                      # Percentages: 95%, 4.5%
        r'[\$€£]\s*\d+(?:,\d{3})*(?:\.\d+)?',     # Currencies: $500, €1,200
        r'\b\d+\s*(?:MAD|USD|EUR|GBP)\b',          # Currency codes
        r'\b(?:19|20)\d{2}\b',                     # Years: 2024, 2026
        r'\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b', # Time units
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
    # 4. Direct Answer Extraction (Definitional Openings)
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
    # 5. Conversational & Question-Based Headings
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
    # 6. Entity Grounding & Knowledge Graph Authority (sameAs Links)
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
    # 7. Structured Tables and Comparison Matrices
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
    # 8. Content Freshness & Temporal Metadata
    # -------------------------------------------------------------------
    date_published = page_data.get("date_published") or ""
    date_modified = page_data.get("date_modified") or ""
    has_date_signal = bool(date_published or date_modified)

    if not has_date_signal:
        # Check in HTML for standard meta tags
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
    # 9. Server-Side Rendering (SSR) Verification for AI Crawlers
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
    }
