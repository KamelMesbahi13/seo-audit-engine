"""agy-seo: Schema.org / JSON-LD analyzer — detect, validate, and recommend."""

import json
from utils import clamp_score

# Deprecated or removed schema types (as of 2026)
DEPRECATED_TYPES = {
    "HowTo": "Rich results removed September 2023",
    "SpecialAnnouncement": "Deprecated July 31, 2025",
    "CourseInfo": "Retired June 2025",
    "EstimatedSalary": "Retired June 2025",
    "LearningVideo": "Retired June 2025",
}

# FAQPage special handling
FAQPAGE_NOTE = "Google retired FAQ rich results for ALL sites on May 7, 2026. No SERP benefit."

# Required properties per schema type
REQUIRED_PROPERTIES = {
    "Organization": ["name", "url"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Article": ["headline", "author", "datePublished"],
    "BlogPosting": ["headline", "author", "datePublished"],
    "NewsArticle": ["headline", "author", "datePublished"],
    "Product": ["name"],
    "Service": ["name", "provider"],
    "Person": ["name"],
    "WebSite": ["url", "name"],
    "WebPage": ["url", "name"],
    "BreadcrumbList": ["itemListElement"],
    "VideoObject": ["name", "uploadDate", "thumbnailUrl"],
    "Event": ["name", "startDate", "location"],
    "JobPosting": ["title", "datePosted", "description", "hiringOrganization"],
    "Review": ["reviewRating", "author"],
    "AggregateRating": ["ratingValue", "reviewCount"],
}

# Recommended properties (enhance rich results)
RECOMMENDED_PROPERTIES = {
    "Organization": ["logo", "sameAs", "contactPoint", "description"],
    "LocalBusiness": ["openingHoursSpecification", "geo", "priceRange", "image", "sameAs"],
    "Article": ["image", "dateModified", "publisher", "description"],
    "BlogPosting": ["image", "dateModified", "publisher", "description"],
    "Product": ["image", "description", "offers", "aggregateRating", "brand"],
    "WebSite": ["potentialAction"],  # SearchAction for sitelinks searchbox
    "VideoObject": ["description", "duration", "contentUrl"],
}


def analyze_schema(page_data: dict) -> dict:
    """Analyze Schema.org structured data on a page."""
    findings = []
    fixes = []
    score = 100

    schemas = page_data.get("schema", [])
    url = page_data["url"]
    title = page_data.get("title", "")
    meta_desc = page_data.get("meta_description", "")

    if not schemas:
        score = 15  # Zero structured data implemented
        findings.append({"category": "Schema", "severity": "critical",
            "issue": "No JSON-LD structured data found",
            "detail": "Structured data helps search engines understand your content and enables rich results (stars, breadcrumbs, FAQ, etc.)."})

        # Generate recommended schema based on page type
        recommended = _recommend_schema(page_data)
        for rec in recommended:
            fixes.append({
                "issue": f"Missing {rec['type']} schema",
                "fix": f"Add the following JSON-LD to <head>:\n\n<script type=\"application/ld+json\">\n{json.dumps(rec['code'], indent=2)}\n</script>"
            })

        return {"analyzer": "schema", "score": clamp_score(score),
                "findings": findings, "fixes": fixes, "schemas_found": 0}

    # Analyze each schema block
    valid_count = 0
    for idx, schema in enumerate(schemas):
        schema_type = schema.get("@type", "Unknown")

        # Handle array types (e.g., ["Organization", "MedicalClinic"])
        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else "Unknown"

        # Check for deprecated types
        if schema_type in DEPRECATED_TYPES:
            score -= 10
            findings.append({"category": "Schema", "severity": "high",
                "issue": f"Deprecated schema type: {schema_type}",
                "detail": DEPRECATED_TYPES[schema_type]})
            fixes.append({"issue": f"Remove deprecated {schema_type}",
                "fix": f"Remove the {schema_type} JSON-LD block. {DEPRECATED_TYPES[schema_type]}.\n"
                       f"This schema no longer provides any rich result benefit."})
            continue

        if schema_type == "FAQPage":
            findings.append({"category": "Schema", "severity": "info",
                "issue": f"FAQPage schema present — {FAQPAGE_NOTE}",
                "detail": "Existing FAQPage: not harmful but provides no Google SERP benefit. "
                          "AI/GEO visibility benefit is unconfirmed."})

        # Check @context
        context = schema.get("@context", "")
        if context and "schema.org" in str(context):
            if "http://" in str(context) and "https://" not in str(context):
                findings.append({"category": "Schema", "severity": "low",
                    "issue": f"Schema #{idx+1} ({schema_type}): Uses http:// for @context",
                    "detail": 'Best practice: Use "https://schema.org" not "http://schema.org".'})
                fixes.append({"issue": f"HTTP @context in {schema_type}",
                    "fix": f'Change:\n  "@context": "http://schema.org"\nTo:\n  "@context": "https://schema.org"'})

        # Check required properties
        if schema_type in REQUIRED_PROPERTIES:
            missing_required = []
            for prop in REQUIRED_PROPERTIES[schema_type]:
                if prop not in schema or not schema[prop]:
                    missing_required.append(prop)
            if missing_required:
                score -= min(len(missing_required) * 3, 10)
                findings.append({"category": "Schema", "severity": "high",
                    "issue": f"{schema_type}: Missing required properties",
                    "detail": f"Missing: {', '.join(missing_required)}"})
                fixes.append({"issue": f"Missing properties in {schema_type}",
                    "fix": f"Add the following required properties to your {schema_type} schema:\n" +
                           "\n".join(f'  "{p}": "YOUR_VALUE"' for p in missing_required)})

        # Check recommended properties
        if schema_type in RECOMMENDED_PROPERTIES:
            missing_recommended = []
            for prop in RECOMMENDED_PROPERTIES[schema_type]:
                if prop not in schema:
                    missing_recommended.append(prop)
            if missing_recommended:
                findings.append({"category": "Schema", "severity": "low",
                    "issue": f"{schema_type}: Missing recommended properties for enhanced rich results",
                    "detail": f"Missing: {', '.join(missing_recommended)}"})

        # Check for placeholder text
        for key, value in schema.items():
            if isinstance(value, str) and any(p in value for p in ["[", "YOUR_", "example.com", "placeholder"]):
                score -= 5
                findings.append({"category": "Schema", "severity": "high",
                    "issue": f"{schema_type}: Placeholder text in '{key}'",
                    "detail": f'Value: "{value}" — Replace with actual content.'})

        valid_count += 1

    # Check for missing common schemas
    types_present = set()
    for s in schemas:
        t = s.get("@type", "")
        if isinstance(t, list):
            types_present.update(t)
        else:
            types_present.add(t)

    if "BreadcrumbList" not in types_present:
        findings.append({"category": "Schema", "severity": "medium",
            "issue": "No BreadcrumbList schema — missing breadcrumb rich results",
            "detail": "BreadcrumbList provides navigation breadcrumbs in search results."})
        fixes.append({"issue": "Missing BreadcrumbList",
            "fix": f'Add BreadcrumbList schema:\n\n<script type="application/ld+json">\n{json.dumps(_generate_breadcrumb(url, title), indent=2)}\n</script>'})

    if not types_present.intersection({"Organization", "LocalBusiness", "ProfessionalService",
                                        "MedicalOrganization", "Corporation"}):
        findings.append({"category": "Schema", "severity": "medium",
            "issue": "No Organization/LocalBusiness schema",
            "detail": "Organization schema establishes your brand's Knowledge Panel potential."})

    return {
        "analyzer": "schema",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
        "schemas_found": len(schemas),
        "types_present": list(types_present),
    }


def _recommend_schema(page_data: dict) -> list[dict]:
    """Recommend schema types based on page content."""
    recommendations = []
    url = page_data["url"]
    title = page_data.get("title", "Site Name")

    # Always recommend WebSite + Organization for root pages
    path = url.rstrip("/").split("/")[-1] if "/" in url else ""
    if not path or path == url.split("//")[1].split("/")[0] if "//" in url else True:
        recommendations.append({
            "type": "WebSite",
            "code": {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": title,
                "url": url,
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": f"{url.rstrip('/')}/?s={{search_term_string}}"
                    },
                    "query-input": "required name=search_term_string"
                }
            }
        })
        recommendations.append({
            "type": "Organization",
            "code": {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "YOUR ORGANIZATION NAME",
                "url": url,
                "logo": f"{url.rstrip('/')}/logo.png",
                "sameAs": [
                    "https://www.facebook.com/YOUR_PAGE",
                    "https://www.linkedin.com/company/YOUR_COMPANY",
                    "https://twitter.com/YOUR_HANDLE"
                ],
                "contactPoint": {
                    "@type": "ContactPoint",
                    "telephone": "+YOUR-PHONE",
                    "contactType": "customer service"
                }
            }
        })

    # Always recommend BreadcrumbList
    recommendations.append({
        "type": "BreadcrumbList",
        "code": _generate_breadcrumb(url, title)
    })

    return recommendations


def _generate_breadcrumb(url: str, title: str) -> dict:
    """Generate a BreadcrumbList schema from URL path."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]

    items = [{"@type": "ListItem", "position": 1,
              "name": "Home", "item": f"{parsed.scheme}://{parsed.netloc}/"}]

    for i, part in enumerate(parts):
        name = part.replace("-", " ").replace("_", " ").title()
        item_url = f"{parsed.scheme}://{parsed.netloc}/{'/'.join(parts[:i+1])}/"
        items.append({
            "@type": "ListItem",
            "position": i + 2,
            "name": name,
            "item": item_url,
        })

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
