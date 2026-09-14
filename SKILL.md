---
name: agy-seo
description: "Antigravity-native full-site SEO audit toolkit. Crawls entire websites (up to 200+ pages), runs 8 comprehensive analyzers (Technical SEO & Security, On-Page & Metadata, Content Quality & E-E-A-T, Schema & Structured Data, Performance & Core Web Vitals, AI Search / GEO / Citability, Images & Assets, Link Architecture & Anchor Text), and generates exhaustive, actionable PDF audit reports saved directly to the user's Downloads directory with detailed problem diagnoses, prioritized action plans, and copy-paste code fixes."
---

# AGY-SEO: Native SEO Audit Engine for Antigravity

A high-performance, full-site SEO auditing toolkit designed specifically for Antigravity agents and developers. It crawls entire domains, evaluates multi-page architectures across 8 core SEO disciplines, and renders publication-ready PDF reports complete with precise code fixes.

## Quick Execution

Run a full-site audit with the dedicated Python virtual environment:

```powershell
& "C:\Users\EL ASSLI HI TECH\.gemini\config\skills\agy-seo\.venv\Scripts\python.exe" "C:\Users\EL ASSLI HI TECH\.gemini\config\skills\agy-seo\agy_seo.py" audit "<URL>"
```

### Options:
- `--max-pages <N>`: Maximum pages to crawl (default: `200`).
- `--output "<PATH>"`: Custom output PDF file path. If omitted, the audit report is **automatically saved directly into the user's Downloads folder**: `C:\Users\<User>\Downloads\SEO_Audit_<Domain>_<Timestamp>.pdf`.

---

## Architecture & Capabilities

### 1. Multi-Page Crawler (`crawler.py`)
- Discovers URLs recursively via XML sitemaps (`sitemap.xml`, sitemap indexes, WordPress Yoast/RankMath sitemaps) and in-page anchor links.
- Respects domain boundaries and robots.txt directives.
- Captures HTTP status, response headers, redirect chains, TTFB, and DOM structure.

### 2. The 8 Audit Engines (`analyzers/`)
1. **Technical SEO & Security (`technical.py`)**:
   - HTTP/HTTPS enforcement and HSTS headers.
   - Self-referencing and canonical tag validity.
   - Mixed content, framing protection (X-Frame-Options), Content-Security-Policy.
   - Sitemaps validity, indexability, and robots.txt rules.
2. **On-Page SEO & Metadata (`onpage.py`)**:
   - Title tag length (50-60 chars optimal), presence, and duplicate checks.
   - Meta description quality and length (120-160 chars).
   - Heading hierarchy: strict single `<h1>`, logical `<h2>`/`<h3>` nesting without skipped levels.
   - Social meta tags: OpenGraph (`og:title`, `og:image`, `og:type`) and Twitter Cards.
3. **Content Quality & E-E-A-T (`content.py`)**:
   - Word count and thin content detection (< 300 words).
   - Flesch Reading Ease score and sentence complexity.
   - Experience, Expertise, Authoritativeness, and Trustworthiness signals: Author bylines, editorial dates, citations, external references, and about/contact cues.
4. **Schema & Structured Data (`schema_analyzer.py`)**:
   - JSON-LD and Microdata extraction and validation.
   - Required and recommended fields for standard schema types: `Organization`, `WebSite`, `Article`, `Product`, `LocalBusiness`, `MedicalBusiness`, `FAQPage`, `BreadcrumbList`.
   - Rich snippet qualification testing.
5. **Performance & Core Web Vitals (`performance.py`)**:
   - TTFB latency analysis (< 200ms good, > 600ms poor).
   - Page payload weight, external stylesheet/script count.
   - Render-blocking CSS/JS detection.
   - Font optimization: `font-display: swap`, local hosting vs Google Fonts preconnect.
6. **AI Search & GEO (`geo.py`)**:
   - Generative Engine Optimization readiness for SearchGPT, Perplexity, Google Gemini / AI Overviews.
   - AI bot permissions in `robots.txt` (`GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`, `Amazonbot`).
   - Information density, Q&A / FAQ formatting, extractable definitional sentences.
7. **Image SEO & Assets (`images.py`)**:
   - Missing or empty `alt` text.
   - Descriptive quality of alt text (flagging filenames like `IMG_123.jpg`).
   - Cumulative Layout Shift (CLS) prevention: Explicit `width` and `height` attributes.
   - Modern image formats (`.webp`, `.avif`).
   - Responsive images (`srcset`, `sizes`).
8. **Link Architecture & Anchors (`links.py`)**:
   - Internal vs external link ratios.
   - Generic or empty anchor texts ("click here", "read more", blank links).
   - `rel="nofollow"` misuse on internal links.
   - Broken external link spot-checking.
   - Orphan page detection and crawl depth distribution.

### 3. Reporting Engine (`reporter.py`)
- Compiles an exhaustive HTML document with executive summaries, visual scorecards, category radar breakdowns, per-page analysis tables, and prioritized step-by-step remediation plans.
- Produces before-and-after code snippets for developers (HTML meta tags, JSON-LD, robots.txt, Apache/Nginx headers).
- Automatically converts to high-fidelity A4 PDF using headless Chromium (Playwright).
