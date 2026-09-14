"""agy-seo: Content quality & E-E-A-T analyzer."""

import re
from collections import Counter
from utils import clamp_score

# Filler phrases commonly found in low-quality AI content
AI_FILLER_PHRASES = [
    "in today's digital landscape", "it's important to note that",
    "in conclusion", "when it comes to", "it goes without saying",
    "needless to say", "at the end of the day", "in this day and age",
    "without further ado", "as a matter of fact", "for all intents and purposes",
    "it is worth noting", "it should be noted that", "as we all know",
    "in the world of", "the importance of", "crucial role",
    "comprehensive guide", "everything you need to know",
    "dive into", "dive deep into", "let's explore",
    "navigating the complexities", "leverage the power",
    "unlock the potential", "harness the power",
    "game-changer", "cutting-edge", "state-of-the-art",
    "revolutionary", "groundbreaking", "unparalleled",
    "seamlessly", "effortlessly", "streamline",
    "robust", "holistic", "synergy",
]

TRUST_SIGNALS = [
    "about us", "about", "contact", "team", "our team",
    "phone", "email", "address", "privacy policy",
    "terms", "legal", "disclaimer", "copyright",
    "certified", "accredited", "licensed", "registered",
]

EXPERIENCE_SIGNALS = [
    "case study", "our experience", "we built", "we created",
    "we helped", "our client", "years of experience",
    "hands-on", "first-hand", "in-house", "our team",
    "portfolio", "project", "testimonial", "review",
]


def analyze_content(page_data: dict) -> dict:
    """Analyze content quality and E-E-A-T signals."""
    findings = []
    fixes = []
    score = 100

    body_text = page_data.get("body_text", "")
    word_count = page_data.get("word_count", 0)
    title = page_data.get("title", "")
    h1s = page_data.get("h1", [])
    h2s = page_data.get("h2", [])
    url = page_data["url"]

    text_lower = body_text.lower()

    # -------------------------------------------------------------------
    # 0. Word Count & Thin Content
    # -------------------------------------------------------------------
    if word_count < 100:
        score -= 30
        findings.append({
            "category": "Content Quality", "severity": "critical",
            "issue": f"Extremely thin content ({word_count} words)",
            "detail": "Pages with under 100 words fail search engine quality thresholds and risk being classified as soft 404s.",
        })
        fixes.append({
            "issue": "Expand Thin Content",
            "fix": "Add at least 350-500 words of descriptive, original content explaining your service, product, or topic.",
        })
    elif word_count < 250:
        score -= 15
        findings.append({
            "category": "Content Quality", "severity": "high",
            "issue": f"Low content volume ({word_count} words)",
            "detail": "Pages under 250 words struggle to rank against comprehensive competitor resources.",
        })

    # -------------------------------------------------------------------
    # 1. E-E-A-T Analysis
    # -------------------------------------------------------------------
    eeat = {"experience": 0, "expertise": 0, "authority": 0, "trust": 0}

    # Experience (20% weight)
    experience_hits = sum(1 for s in EXPERIENCE_SIGNALS if s in text_lower)
    eeat["experience"] = min(experience_hits * 15, 100)

    # Expertise (25% weight) — technical depth indicators
    has_specific_numbers = len(re.findall(r'\b\d{2,}\b', body_text)) > 3
    has_technical_terms = word_count > 500
    has_structured_content = len(h2s) >= 3
    expertise_score = 0
    if has_specific_numbers: expertise_score += 30
    if has_technical_terms: expertise_score += 30
    if has_structured_content: expertise_score += 40
    eeat["expertise"] = min(expertise_score, 100)

    # Authority (25% weight) — external recognition signals
    external_links = page_data.get("links", {}).get("external", [])
    has_citations = len(external_links) > 2
    schema = page_data.get("schema", [])
    has_org_schema = any(
        s.get("@type") in ("Organization", "LocalBusiness", "ProfessionalService",
                           "MedicalOrganization", "Corporation")
        for s in schema
    )
    authority_score = 0
    if has_citations: authority_score += 40
    if has_org_schema: authority_score += 30
    if len(external_links) > 5: authority_score += 30
    eeat["authority"] = min(authority_score, 100)

    # Trust (30% weight) — trustworthiness signals
    trust_hits = sum(1 for s in TRUST_SIGNALS if s in text_lower)
    has_https = url.startswith("https://")
    has_contact = any(s in text_lower for s in ["contact", "phone", "email", "tel:"])
    has_privacy = any(s in text_lower for s in ["privacy policy", "terms"])

    trust_score = 0
    if has_https: trust_score += 25
    if has_contact: trust_score += 25
    if has_privacy: trust_score += 20
    trust_score += min(trust_hits * 5, 30)
    eeat["trust"] = min(trust_score, 100)

    # Weighted E-E-A-T score
    eeat_total = (
        eeat["experience"] * 0.20 +
        eeat["expertise"] * 0.25 +
        eeat["authority"] * 0.25 +
        eeat["trust"] * 0.30
    )

    if eeat_total < 40:
        score -= 20
        findings.append({"category": "E-E-A-T", "severity": "high",
            "issue": f"Low overall E-E-A-T score ({eeat_total:.0f}/100)",
            "detail": f"Experience: {eeat['experience']}/100, Expertise: {eeat['expertise']}/100, "
                      f"Authority: {eeat['authority']}/100, Trust: {eeat['trust']}/100"})
    elif eeat_total < 60:
        score -= 10
        findings.append({"category": "E-E-A-T", "severity": "medium",
            "issue": f"Moderate E-E-A-T score ({eeat_total:.0f}/100)",
            "detail": f"Experience: {eeat['experience']}/100, Expertise: {eeat['expertise']}/100, "
                      f"Authority: {eeat['authority']}/100, Trust: {eeat['trust']}/100"})

    # Specific E-E-A-T improvement recommendations
    if eeat["experience"] < 40:
        fixes.append({"issue": "Low Experience signals",
            "fix": "Add first-hand experience content:\n"
                   "- Include case studies with real results and metrics\n"
                   "- Add 'Our Experience' or 'Our Work' sections\n"
                   "- Include original photography from your projects\n"
                   "- Add client testimonials with specific outcomes"})
    if eeat["trust"] < 40:
        fixes.append({"issue": "Low Trust signals",
            "fix": "Improve trustworthiness:\n"
                   "- Add a visible Contact page with phone, email, and physical address\n"
                   "- Add Privacy Policy and Terms of Service pages\n"
                   "- Display certifications, licenses, or accreditations\n"
                   "- Add clear author/team attribution for content"})

    # -------------------------------------------------------------------
    # 2. AI Content Detection (Heuristic)
    # -------------------------------------------------------------------
    filler_count = 0
    filler_found = []
    for phrase in AI_FILLER_PHRASES:
        occurrences = text_lower.count(phrase)
        if occurrences > 0:
            filler_count += occurrences
            filler_found.append(f'"{phrase}" (x{occurrences})')

    if filler_count > 5:
        score -= 10
        findings.append({"category": "Content Quality", "severity": "high",
            "issue": f"High AI filler phrase density ({filler_count} instances)",
            "detail": "Detected phrases: " + ", ".join(filler_found[:10])})
        fixes.append({"issue": "AI filler phrases",
            "fix": "Replace generic AI-generated phrases with specific, factual language:\n"
                   "- Instead of 'in today's digital landscape' → state the specific context\n"
                   "- Instead of 'cutting-edge' → describe the specific technology\n"
                   "- Instead of 'comprehensive guide' → describe what the reader will learn\n"
                   "- Add unique data, original research, or specific case examples"})
    elif filler_count > 2:
        score -= 5
        findings.append({"category": "Content Quality", "severity": "medium",
            "issue": f"Some AI filler phrases detected ({filler_count} instances)",
            "detail": "Detected: " + ", ".join(filler_found)})

    # -------------------------------------------------------------------
    # 3. Readability
    # -------------------------------------------------------------------
    sentences = re.split(r'[.!?]+', body_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if sentences:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_length > 25:
            score -= 5
            findings.append({"category": "Readability", "severity": "medium",
                "issue": f"Average sentence length is high ({avg_sentence_length:.0f} words)",
                "detail": "Recommended: 15-20 words per sentence for web content. Long sentences reduce readability."})
            fixes.append({"issue": "Long sentences",
                "fix": "Break long sentences into shorter, scannable chunks:\n"
                       "- Aim for 15-20 words per sentence\n"
                       "- Use bullet points for lists\n"
                       "- Start paragraphs with the key point"})

    # -------------------------------------------------------------------
    # 4. Content depth and keyword optimization
    # -------------------------------------------------------------------
    if word_count > 50:
        words = re.findall(r'\b\w{4,}\b', text_lower)
        word_freq = Counter(words)
        top_words = word_freq.most_common(20)

        # Check if H1/title keywords appear in body
        if h1s:
            h1_words = set(re.findall(r'\b\w{4,}\b', h1s[0].lower()))
            body_words = set(words)
            h1_in_body = h1_words & body_words
            if len(h1_in_body) < len(h1_words) * 0.3 and len(h1_words) > 2:
                score -= 3
                findings.append({"category": "Content", "severity": "medium",
                    "issue": "H1 keywords are underrepresented in body content",
                    "detail": f"H1: \"{h1s[0]}\"\nOnly {len(h1_in_body)}/{len(h1_words)} significant H1 words appear in the body text."})

    # -------------------------------------------------------------------
    # 5. Content freshness
    # -------------------------------------------------------------------
    schema = page_data.get("schema", [])
    has_date = False
    for s in schema:
        if s.get("dateModified") or s.get("datePublished"):
            has_date = True
            break
    if not has_date:
        findings.append({"category": "Freshness", "severity": "low",
            "issue": "No publication or modification date found in schema",
            "detail": "Adding datePublished and dateModified to your schema helps search engines assess content freshness."})

    return {
        "analyzer": "content",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
        "eeat_scores": eeat,
        "eeat_total": round(eeat_total),
        "word_count": word_count,
        "filler_count": filler_count,
    }
