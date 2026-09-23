# InersiaLab Software Department — SEO Audit & Architecture Suite (agy-seo)

An executive-grade technical SEO audit engine, pre-launch technical architecture synthesizer, and turnkey page & section content generator.

## Core Capabilities & Modules

### 1. Existing Website Audit Engine
- **Deep Multi-Page Crawling**: Traverses XML sitemaps and discovers internal links with native Arabic and Unicode URL support. Unlimited crawl depth (Scope 0).
- **8 Comprehensive Analyzers**:
  1. Technical SEO & Security (Sitemap 404 penalties, HTTPS, security headers, canonicals)
  2. On-Page & Metadata (Titles 50–60c, meta descriptions 140–160c, semantic headings H1/H2/H3, OpenGraph)
  3. Content Quality & E-E-A-T (Word counts, reading ease, thin content detection, author authority)
  4. Schema & Structured Data (JSON-LD validation, Organization, MedicalBusiness, sameAs)
  5. Performance & Core Web Vitals (TTFB latency, render-blocking scripts, LCP, image CLS)
  6. Generative Engine Optimization (GEO / AI Search for SearchGPT, Perplexity, Claude, llms.txt)
  7. Images & Assets (Alt text, explicit dimensions, modern WebP/AVIF formats, lazy loading)
  8. Link Architecture (Broken links, anchor text signals, nofollow audit, orphan page detection)

### 2. New Website Architect (Pre-Launch Technical Blueprint)
- **Technical Prevention Manual**: Ingests project parameters (brand, domain, frontend framework, edge hosting, language/RTL, and business archetype) and synthesizes an exhaustive engineering manual preventing defects before development starts.
- **Turnkey Repository Starter Kit**: Automatically generates production-ready `robots.txt`, `llms.txt`, semantic HTML5 boilerplate with pre-configured `<head>`, security headers, and Schema.org knowledge graph JSON-LD.

### 3. Pre-Launch Page & Section Content Architect
- **Content Synthesis Engine**: Automatically generates complete, fully-structured text content for every page of a new website based on selected business archetype and custom page lists.
- **10 Industry Presets**: Healthcare/Clinic, SaaS/Software, E-Commerce, Digital Agency, Finance/Legal, Real Estate, Education/Courses, Hospitality/Tourism, Local Business/Contractor, and Media Publishing.
- **SEO/GEO Optimization Standards**:
  - Strict heading hierarchy (exactly 1 `<h1>`, ordered `<h2>` -> `<h3>`, zero skipped levels)
  - Title tags engineered to 50–60 characters; Meta descriptions to 140–160 characters
  - First-sentence Answer Engine Optimization (AEO) hooks in every section for AI search engine extraction (SearchGPT, Perplexity, Claude)
  - Comprehensive body paragraphs, process steps, comparison tables, and FAQ accordion pairs
  - Schema.org JSON-LD graph tailored per page type
  - Multilingual support: English (EN), French (FR), and Arabic (AR RTL)
- **Export Artifacts**:
  - Structured Markdown per page (`pages/<slug>.md`)
  - Semantic HTML per page (`html/<slug>.html`)
  - Headless CMS JSON per page (`json/<slug>.json`)
  - Master Website Content document (`MASTER_CONTENT.md`)
  - AI Crawler Index (`llms.txt`)
  - Sitemap URLs (`sitemap_urls.txt`)

## Strict Executive Design Standards
- Exactly 3 brand colors: Black (#111827), Red (#b91c1c), Green (#15803d).
- Pure white background (#ffffff), no colored background box fills, no box shadows, zero icons/emojis.
- All reports, blueprints, starter kits, and content exports saved directly to the user's Downloads folder.

## User Interfaces

- **Native Desktop GUI**: Run `run_gui.bat` (or `python gui.py`) for a clean, minimalist 3-tab desktop application (Tab 1: Audit, Tab 2: Architect Blueprint, Tab 3: Page Content Architect).
- **Web Browser UI**: Run `run_web.bat` (or `python web_ui.py`) to launch the local web interface at `http://127.0.0.1:8765` featuring real-time execution streaming and interactive multi-page content viewer.
- **CLI Commands**:
  - Audit: `python agy_seo.py audit <URL>`
  - Content Generator: `python content_generator.py --brand "MyBrand" --industry healthcare_medical --all-pages`

## Reports & Exports Location
All generated PDF reports, starter kits, and site content packages are saved directly to:
`C:\Users\EL ASSLI HI TECH\Downloads\`

## License
Proprietary • InersiaLab Software Department • All Rights Reserved
