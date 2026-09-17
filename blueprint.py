"""InersiaLab Software Department — Pre-Launch Website Architecture & Blueprint Engine.

Generates complete, enterprise-grade engineering specifications for BRAND NEW websites
to prevent all technical SEO, GEO (Generative Engine Optimization), and Core Web Vitals
defects before development starts.
"""

import json
import os
import re
import sys
import shutil
import tempfile
from datetime import datetime
from urllib.parse import urlparse

# Strict 3-color palette
COLOR_BLACK = "#111827"
COLOR_RED = "#b91c1c"
COLOR_GREEN = "#15803d"
COLOR_MUTED = "#4b5563"
COLOR_BORDER = "#e5e7eb"


# ---------------------------------------------------------------------------
# Comprehensive Questionnaire Definition
# ---------------------------------------------------------------------------

QUESTIONNAIRE_SCHEMA = [
    {
        "id": "brand_info",
        "category": "1. Brand & Strategic Identity",
        "fields": [
            {
                "id": "brand_name",
                "label": "Brand / Company Name",
                "type": "text",
                "placeholder": "e.g. InersiaLab",
                "default": "InersiaLab",
                "required": True,
                "help": "Official trade name used in title tags, brand citations, and Organization schema."
            },
            {
                "id": "domain",
                "label": "Primary Canonical Domain",
                "type": "text",
                "placeholder": "e.g. https://inersialab.com",
                "default": "https://example.com",
                "required": True,
                "help": "Canonical domain root including https:// (used for canonical tags and sitemaps)."
            },
            {
                "id": "industry",
                "label": "Industry / Business Category",
                "type": "select",
                "options": [
                    {"value": "technology_software", "label": "Technology, SaaS & Software Engineering"},
                    {"value": "digital_agency", "label": "Digital Agency, Marketing & Creative Services"},
                    {"value": "ecommerce_retail", "label": "E-Commerce & Online Retail Store"},
                    {"value": "healthcare_medical", "label": "Healthcare, Medical Clinic & Dental Services"},
                    {"value": "finance_legal", "label": "Financial, Legal, Accounting & Consulting"},
                    {"value": "real_estate", "label": "Real Estate, Property Management & Architecture"},
                    {"value": "education_courses", "label": "Education, Academy, Online Courses & Coaching"},
                    {"value": "hospitality_tourism", "label": "Hospitality, Travel, Tourism & Restaurants"},
                    {"value": "media_publishing", "label": "News Media, Editorial Blog & Content Publishing"},
                    {"value": "industrial_b2b", "label": "Manufacturing, Logistics & Industrial B2B"}
                ],
                "default": "technology_software"
            },
            {
                "id": "description",
                "label": "Core Value Proposition / Tagline",
                "type": "text",
                "placeholder": "e.g. Enterprise software engineering and digital transformation agency",
                "default": "Professional modern solutions and strategic engineering services.",
                "required": True,
                "help": "Used for default meta descriptions, llms.txt summary, and schema descriptions."
            },
            {
                "id": "target_market",
                "label": "Primary Geographic Target Market",
                "type": "select",
                "options": [
                    {"value": "global", "label": "Global / International Audience"},
                    {"value": "north_america", "label": "North America (US & Canada)"},
                    {"value": "europe_uk", "label": "Europe & United Kingdom (GDPR compliant)"},
                    {"value": "mena_gulf", "label": "MENA & Gulf Region (Middle East & North Africa)"},
                    {"value": "local_metro", "label": "Local Metro / City Specific Service Area"}
                ],
                "default": "global"
            }
        ]
    },
    {
        "id": "archetype_stack",
        "category": "2. Architecture, Framework & Infrastructure",
        "fields": [
            {
                "id": "site_type",
                "label": "Website Archetype & Model",
                "type": "select",
                "options": [
                    {"value": "corporate_services", "label": "Corporate Website & B2B Services Showcase"},
                    {"value": "saas_webapp", "label": "SaaS Platform / Web Application Landing & Portal"},
                    {"value": "ecommerce", "label": "E-Commerce Store (Product catalog & Checkout)"},
                    {"value": "local_business", "label": "Local Physical Business (Storefront / Clinic / Office)"},
                    {"value": "content_blog", "label": "Content Publisher, Editorial Blog & Media Publication"},
                    {"value": "directory_marketplace", "label": "Directory, Listing Portal or Two-Sided Marketplace"},
                    {"value": "portfolio_creative", "label": "Creative Agency / Designer / Studio Portfolio"}
                ],
                "default": "corporate_services"
            },
            {
                "id": "tech_stack",
                "label": "Frontend Framework / Engine",
                "type": "select",
                "options": [
                    {"value": "nextjs", "label": "Next.js (App Router, React Server Components)"},
                    {"value": "astro", "label": "Astro (Content-first, Zero-JS Island Architecture)"},
                    {"value": "react_vite", "label": "React + Vite SPA (Client-rendered with SSR/Prerender)"},
                    {"value": "wordpress", "label": "WordPress (Custom Theme / Headless CMS)"},
                    {"value": "shopify", "label": "Shopify (Liquid or Hydrogen Storefront)"},
                    {"value": "nuxt", "label": "Nuxt.js (Vue 3 SSR/SSG Framework)"},
                    {"value": "laravel", "label": "Laravel + Blade / Livewire Full-Stack PHP"},
                    {"value": "vanilla_html", "label": "Modern Semantic HTML5 + Vanilla CSS + JavaScript"}
                ],
                "default": "nextjs"
            },
            {
                "id": "rendering_strategy",
                "label": "Rendering Architecture",
                "type": "select",
                "options": [
                    {"value": "ssg", "label": "SSG — Static Site Generation (Pre-rendered HTML at build time — Fastest)"},
                    {"value": "ssr", "label": "SSR — Server-Side Rendering (Dynamic per request — Real-time state)"},
                    {"value": "isr", "label": "ISR — Incremental Static Regeneration (Cached static with background revalidation)"},
                    {"value": "spa_prerender", "label": "SPA + Automated Prerendering (Client React/Vue with headless crawler HTML)"}
                ],
                "default": "ssg"
            },
            {
                "id": "cms_type",
                "label": "Content Management / Authoring Source",
                "type": "select",
                "options": [
                    {"value": "headless_cms", "label": "Headless CMS (Sanity, Strapi, Contentful, Ghost)"},
                    {"value": "git_markdown", "label": "Git-based Markdown / MDX / Content Collections (Developer-first)"},
                    {"value": "native_wordpress", "label": "Native WordPress Admin / WooCommerce"},
                    {"value": "database_backend", "label": "Custom Database (PostgreSQL, Supabase, Firebase)"},
                    {"value": "static_code", "label": "Hardcoded Components (No CMS required)"}
                ],
                "default": "git_markdown"
            },
            {
                "id": "hosting",
                "label": "Hosting & Deployment Environment",
                "type": "select",
                "options": [
                    {"value": "cloudflare", "label": "Cloudflare Pages / Workers (Global Edge CDN)"},
                    {"value": "vercel", "label": "Vercel Edge Network (Optimized for Next.js)"},
                    {"value": "nginx_vps", "label": "Linux VPS / Dedicated Server (Ubuntu + Nginx + Certbot)"},
                    {"value": "netlify", "label": "Netlify Edge Platform"},
                    {"value": "aws_gcp", "label": "AWS CloudFront / Google Cloud Run Enterprise"},
                    {"value": "apache_cpanel", "label": "Traditional Apache / cPanel / LiteSpeed Server"}
                ],
                "default": "cloudflare"
            }
        ]
    },
    {
        "id": "languages_i18n",
        "category": "3. Internationalization, Multilingual & RTL",
        "fields": [
            {
                "id": "language_setup",
                "label": "Language Configuration",
                "type": "select",
                "options": [
                    {"value": "single_en", "label": "Single Language — English Only"},
                    {"value": "single_fr", "label": "Single Language — French Only"},
                    {"value": "single_ar", "label": "Single Language — Arabic Only (RTL Support)"},
                    {"value": "bilingual_en_fr", "label": "Bilingual — English & French (/fr/ subdirectory)"},
                    {"value": "multilingual_en_fr_ar", "label": "Multilingual + RTL — English, French & Arabic (/fr/, /ar/)"},
                    {"value": "global_multi", "label": "Global Multi-Regional (US, UK, FR, DE, ES, MENA)"}
                ],
                "default": "bilingual_en_fr"
            },
            {
                "id": "url_structure",
                "label": "Multilingual URL Architecture",
                "type": "select",
                "options": [
                    {"value": "subdirectory", "label": "Subdirectories — example.com/fr/ (Google Recommended)"},
                    {"value": "subdomain", "label": "Subdomains — fr.example.com"},
                    {"value": "cctld", "label": "Separate ccTLDs — example.fr, example.ae"},
                    {"value": "none", "label": "Not Applicable (Single Language)"}
                ],
                "default": "subdirectory"
            },
            {
                "id": "rtl_support",
                "label": "Right-to-Left (RTL) Layout & Arabic Typography",
                "type": "select",
                "options": [
                    {"value": "rtl_required", "label": "Full RTL Support (CSS Logical Properties + Cairo/Tajawal web fonts)"},
                    {"value": "ltr_only", "label": "LTR Only (Standard Left-to-Right layout)"}
                ],
                "default": "ltr_only"
            }
        ]
    },
    {
        "id": "geo_ai_search",
        "category": "4. Generative Engine Optimization (GEO) & AI Crawlers",
        "fields": [
            {
                "id": "geo_priority",
                "label": "Generative Engine Optimization (GEO) Ambition",
                "type": "select",
                "options": [
                    {"value": "high_geo", "label": "Maximum AI Citability — Optimize for SearchGPT, Perplexity, Claude & Gemini"},
                    {"value": "balanced_seo_geo", "label": "Balanced Hybrid — Equal focus on Google Search & AI Overviews"},
                    {"value": "standard_seo", "label": "Traditional SEO Focus — Prioritize Google & Bing SERP Rank"}
                ],
                "default": "high_geo"
            },
            {
                "id": "ai_bot_policy",
                "label": "AI Search Crawler Access Policy",
                "type": "select",
                "options": [
                    {"value": "allow_all_search", "label": "Allow All AI Search Bots (GPTBot, PerplexityBot, ClaudeBot, Google-Extended)"},
                    {"value": "search_only_block_training", "label": "Allow Search Citation Bots, Block Uncredited Model Training Bots"},
                    {"value": "block_all_ai", "label": "Block All AI Crawlers in robots.txt (Traditional search only)"}
                ],
                "default": "allow_all_search"
            },
            {
                "id": "llms_txt",
                "label": "Deploy /llms.txt Machine-Readable Files",
                "type": "select",
                "options": [
                    {"value": "yes", "label": "Yes — Deploy /llms.txt and /llms-full.txt at domain root (Recommended)"},
                    {"value": "no", "label": "No — Standard search crawler files only"}
                ],
                "default": "yes"
            },
            {
                "id": "schema_strategy",
                "label": "Schema.org Structured Data Strategy",
                "type": "select",
                "options": [
                    {"value": "comprehensive_graph", "label": "Comprehensive Entity Graph (Organization + WebSite + BreadcrumbList + Archetype Entity + FAQPage)"},
                    {"value": "baseline_only", "label": "Baseline Organization & WebSite Schemas Only"}
                ],
                "default": "comprehensive_graph"
            }
        ]
    },
    {
        "id": "performance_cwv",
        "category": "5. Performance, Core Web Vitals & Assets",
        "fields": [
            {
                "id": "cwv_target",
                "label": "Core Web Vitals Performance Target",
                "type": "select",
                "options": [
                    {"value": "ultra_fast", "label": "Ultra-Fast: <1.0s LCP, 0.00 CLS, <100ms INP (100 Mobile Score Target)"},
                    {"value": "enterprise", "label": "Enterprise Standard: <1.8s LCP, <0.05 CLS, <150ms INP (90+ Score Target)"},
                    {"value": "standard", "label": "Standard Web: <2.5s LCP, <0.10 CLS, <200ms INP"}
                ],
                "default": "ultra_fast"
            },
            {
                "id": "font_strategy",
                "label": "Web Fonts & Typography Engineering",
                "type": "select",
                "options": [
                    {"value": "self_hosted_woff2", "label": "Self-Hosted WOFF2 with Preload & font-display: swap (Zero CLS, Zero 3rd-party latency)"},
                    {"value": "system_fonts", "label": "System Font Stack (-apple-system, BlinkMacSystemFont, Segoe UI — 0.00ms latency)"},
                    {"value": "google_fonts_cdn", "label": "Google Fonts CDN with preconnect hints"}
                ],
                "default": "self_hosted_woff2"
            },
            {
                "id": "media_strategy",
                "label": "Visual Media & Asset Policy",
                "type": "select",
                "options": [
                    {"value": "balanced_webp", "label": "Automated WebP/AVIF with explicit CLS dimensions & fetchpriority=\"high\" for hero"},
                    {"value": "heavy_photography", "label": "High-Resolution Creative Portfolio (Responsive srcset with WebP fallbacks)"},
                    {"value": "video_centric", "label": "Video-Centric (Embedded player optimizations & poster frame preloading)"}
                ],
                "default": "balanced_webp"
            },
            {
                "id": "analytics_strategy",
                "label": "Analytics & Tracking Script Overhead",
                "type": "select",
                "options": [
                    {"value": "privacy_first", "label": "Privacy-First Lightweight (Plausible / Umami — <2KB, zero cookies, no banner needed)"},
                    {"value": "ga4_deferred", "label": "Google Analytics 4 / GTM (Deferred with Google Consent Mode v2)"},
                    {"value": "full_marketing_suite", "label": "Full Marketing Suite (GA4, Meta Pixel, LinkedIn Insight, Hotjar — Tag-managed)"},
                    {"value": "none", "label": "None (Zero third-party tracking scripts)"}
                ],
                "default": "privacy_first"
            }
        ]
    },
    {
        "id": "features_compliance",
        "category": "6. Interactive Modules, Security & Compliance",
        "fields": [
            {
                "id": "interactive_features",
                "label": "Core Interactive Feature Focus",
                "type": "select",
                "options": [
                    {"value": "lead_form", "label": "High-Conversion Lead Capture Form (Anti-spam, CSRF protected)"},
                    {"value": "ecommerce_checkout", "label": "Full Shopping Cart, Dynamic Inventory & Stripe/PayPal Checkout"},
                    {"value": "user_accounts", "label": "User Authentication & Protected Client Portal (Auth0 / Supabase / NextAuth)"},
                    {"value": "booking_calendar", "label": "Consultation & Appointment Booking Scheduler"}
                ],
                "default": "lead_form"
            },
            {
                "id": "security_level",
                "label": "HTTP Security Headers & SSL Posture",
                "type": "select",
                "options": [
                    {"value": "strict_a_plus", "label": "Maximum A+ Grade (Strict CSP, HSTS 2-Year Preload, X-Frame-Options, Permissions-Policy)"},
                    {"value": "standard_secure", "label": "Standard Secure (HSTS, X-Content-Type-Options, Referrer-Policy)"}
                ],
                "default": "strict_a_plus"
            },
            {
                "id": "cookie_compliance",
                "label": "Regulatory & Privacy Compliance",
                "type": "select",
                "options": [
                    {"value": "strict_gdpr", "label": "Strict GDPR / ePrivacy Compliance (Granular opt-in cookie banner before script load)"},
                    {"value": "zero_cookie", "label": "Zero-Cookie Architecture (No cookies used — Legal banner not required)"},
                    {"value": "standard_notice", "label": "Standard Informational Privacy Notice"}
                ],
                "default": "strict_gdpr"
            }
        ]
    }
]


# ---------------------------------------------------------------------------
# Blueprint Synthesis Engine
# ---------------------------------------------------------------------------

class BlueprintSynthesizer:
    """Takes questionnaire inputs and compiles an exhaustive architectural specification."""

    def __init__(self, answers: dict):
        self.answers = answers
        self.brand_name = answers.get("brand_name", "InersiaLab").strip() or "InersiaLab"
        raw_domain = answers.get("domain", "https://example.com").strip()
        if not raw_domain.startswith("http"):
            raw_domain = "https://" + raw_domain
        self.domain = raw_domain.rstrip("/")
        self.parsed_domain = urlparse(self.domain).netloc or "example.com"
        self.industry = answers.get("industry", "technology_software")
        self.description = answers.get("description", "Enterprise software engineering and digital transformation agency").strip()
        self.target_market = answers.get("target_market", "global")
        
        self.site_type = answers.get("site_type", "corporate_services")
        self.tech_stack = answers.get("tech_stack", "nextjs")
        self.rendering_strategy = answers.get("rendering_strategy", "ssg")
        self.cms_type = answers.get("cms_type", "git_markdown")
        self.hosting = answers.get("hosting", "cloudflare")
        
        self.language_setup = answers.get("language_setup", "bilingual_en_fr")
        self.url_structure = answers.get("url_structure", "subdirectory")
        self.rtl_support = answers.get("rtl_support", "ltr_only")
        if "ar" in self.language_setup:
            self.rtl_support = "rtl_required"
            
        self.geo_priority = answers.get("geo_priority", "high_geo")
        self.ai_bot_policy = answers.get("ai_bot_policy", "allow_all_search")
        self.llms_txt = answers.get("llms_txt", "yes")
        self.schema_strategy = answers.get("schema_strategy", "comprehensive_graph")
        
        self.content_scope = answers.get("content_scope", "lean_brochure")
        self.cwv_target = answers.get("cwv_target", "ultra_fast")
        self.font_strategy = answers.get("font_strategy", "self_hosted_woff2")
        self.media_strategy = answers.get("media_strategy", "balanced_webp")
        self.analytics_strategy = answers.get("analytics_strategy", "privacy_first")
        
        self.interactive_features = answers.get("interactive_features", "lead_form")
        self.security_level = answers.get("security_level", "strict_a_plus")
        self.cookie_compliance = answers.get("cookie_compliance", "strict_gdpr")
        
        self.timestamp = datetime.now().strftime("%B %d, %Y")

    def synthesize(self) -> dict:
        """Run full architectural synthesis and return complete specification data."""
        sections = []

        # 1. Executive Summary & Target Metrics
        sections.append(self._build_section_executive())

        # 2. Technical Server & Infrastructure Configuration
        sections.append(self._build_section_infrastructure())

        # 3. Robots.txt Directives & AI Search Permissions
        sections.append(self._build_section_robots())

        # 4. XML Sitemap Architecture
        sections.append(self._build_section_sitemaps())

        # 5. HTML Document Architecture & Semantic Standards
        sections.append(self._build_section_html_semantics())

        # 6. International & Multilingual SEO (Hreflang & RTL)
        if "bilingual" in self.language_setup or "multilingual" in self.language_setup or "ar" in self.language_setup or "global" in self.language_setup:
            sections.append(self._build_section_international())

        # 7. Generative Engine Optimization (GEO & AI Citability)
        sections.append(self._build_section_geo())

        # 8. Schema.org Structured Data Knowledge Graph
        sections.append(self._build_section_schema())

        # 9. Performance & Core Web Vitals Engineering
        sections.append(self._build_section_core_web_vitals())

        # 10. Image & Media Asset Engineering Policy
        sections.append(self._build_section_media_policy())

        # 11. The Anti-Pattern Handbook (What NOT to Do)
        sections.append(self._build_section_anti_patterns())

        # 12. 25-Point Pre-Launch Verification Checklist
        sections.append(self._build_section_checklist())

        return {
            "brand_name": self.brand_name,
            "domain": self.domain,
            "host_domain": self.parsed_domain,
            "timestamp": self.timestamp,
            "answers": self.answers,
            "sections": sections,
        }

    # -----------------------------------------------------------------------
    # Section Generators
    # -----------------------------------------------------------------------

    def _build_section_executive(self) -> dict:
        stack_labels = {
            "nextjs": "Next.js (App Router, Server Components)",
            "astro": "Astro (Island Architecture, Content-First)",
            "react_vite": "React + Vite SPA",
            "wordpress": "WordPress (CMS)",
            "shopify": "Shopify Liquid / Hydrogen",
            "nuxt": "Nuxt.js (Vue 3 SSR)",
            "laravel": "Laravel Full-Stack PHP",
            "vanilla_html": "Semantic HTML5 + Vanilla CSS/JS"
        }
        hosting_labels = {
            "cloudflare": "Cloudflare Pages & Workers Edge",
            "vercel": "Vercel Global Edge Network",
            "nginx_vps": "Linux VPS (Ubuntu + Nginx + Certbot)",
            "netlify": "Netlify Edge Platform",
            "aws_gcp": "AWS CloudFront / GCP Enterprise",
            "apache_cpanel": "Apache / cPanel / LiteSpeed"
        }

        return {
            "id": "section-executive",
            "title": "1. Executive Architectural Strategy & Target KPIs",
            "description": "Architectural roadmap defining target technical performance, crawlability, and generative citability benchmarks before engineering begins.",
            "kpis": [
                {"label": "Target Tech SEO Score", "value": "100/100", "grade": "Grade A"},
                {"label": "Target Core Web Vitals", "value": "100/100", "grade": "Sub-800ms LCP"},
                {"label": "Target GEO Citability", "value": "100%", "grade": "Full AI Search Bot Coverage"},
                {"label": "Defect Tolerance", "value": "Zero", "grade": "Strict Pre-Launch Compliance"}
            ],
            "content": f"""
            <div class="blueprint-card">
                <h4>Project Scope Overview</h4>
                <table class="data-table">
                    <tr><td style="width: 200px; font-weight: 700;">Client / Brand</td><td>{self.brand_name}</td></tr>
                    <tr><td style="font-weight: 700;">Target Canonical Domain</td><td><code>{self.domain}</code></td></tr>
                    <tr><td style="font-weight: 700;">Selected Stack</td><td>{stack_labels.get(self.tech_stack, self.tech_stack)}</td></tr>
                    <tr><td style="font-weight: 700;">Deployment Target</td><td>{hosting_labels.get(self.hosting, self.hosting)}</td></tr>
                    <tr><td style="font-weight: 700;">Primary Target</td><td>{self.description}</td></tr>
                </table>
                <div style="margin-top: 14px; font-size: 9pt; line-height: 1.5; color: #374151;">
                    <strong>Core Architectural Mandate:</strong> The development team must follow this specification strictly. 
                    Unlike traditional retrospective audits that uncover hundreds of defects post-launch, adhering to this blueprint 
                    guarantees clean semantic markup, automated sitemaps, robust server headers, valid structured data, and 
                    instant citability across Google Search, SearchGPT, Perplexity, and Claude on Day 1.
                </div>
            </div>
            """
        }

    def _build_section_infrastructure(self) -> dict:
        config_code = ""
        config_filename = ""

        if self.hosting in ("cloudflare", "vercel") and self.tech_stack == "nextjs":
            config_filename = "next.config.mjs (Security Headers & Canonical Enforcer)"
            config_code = f"""/** @type {{import('next').NextConfig}} */
const nextConfig = {{
  reactStrictMode: true,
  poweredByHeader: false, // Suppress X-Powered-By
  trailingSlash: false,    // Canonicalize URLs without trailing slashes
  async headers() {{
    return [
      {{
        source: '/(.*)',
        headers: [
          {{ key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' }},
          {{ key: 'X-Content-Type-Options', value: 'nosniff' }},
          {{ key: 'X-Frame-Options', value: 'SAMEORIGIN' }},
          {{ key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' }},
          {{ key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' }},
          {{ key: 'Cross-Origin-Opener-Policy', value: 'same-origin' }}
        ],
      }},
    ];
  }},
}};

export default nextConfig;"""
        elif self.hosting == "cloudflare":
            config_filename = "_headers (Cloudflare Pages Production Config)"
            config_code = f"""/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Cross-Origin-Opener-Policy: same-origin
  Cache-Control: public, max-age=3600, stale-while-revalidate=86400

/assets/*
  Cache-Control: public, max-age=31536000, immutable"""
        elif self.hosting == "vercel":
            config_filename = "vercel.json (Enterprise Edge Headers)"
            config_code = f"""{{
  "headers": [
    {{
      "source": "/(.*)",
      "headers": [
        {{ "key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains; preload" }},
        {{ "key": "X-Content-Type-Options", "value": "nosniff" }},
        {{ "key": "X-Frame-Options", "value": "SAMEORIGIN" }},
        {{ "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }},
        {{ "key": "Cross-Origin-Opener-Policy", "value": "same-origin" }}
      ]
    }}
  ]
}}"""
        elif self.hosting == "nginx_vps":
            config_filename = f"/etc/nginx/sites-available/{self.parsed_domain}"
            config_code = f"""# Redirect HTTP to HTTPS (301 Permanent)
server {{
    listen 80;
    listen [::]:80;
    server_name {self.parsed_domain} www.{self.parsed_domain};
    return 301 https://{self.parsed_domain}$request_uri;
}}

# Redirect www to non-www
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.{self.parsed_domain};
    ssl_certificate /etc/letsencrypt/live/{self.parsed_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.parsed_domain}/privkey.pem;
    return 301 https://{self.parsed_domain}$request_uri;
}}

# Primary Server Block
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {self.parsed_domain};

    root /var/www/{self.parsed_domain}/public;
    index index.html;

    # SSL TLS v1.2 / v1.3
    ssl_certificate /etc/letsencrypt/live/{self.parsed_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.parsed_domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Mandatory Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;

    # Gzip & Brotli Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;
    gzip_min_length 256;

    # Static Asset Caching
    location ~* \\.(jpg|jpeg|png|gif|ico|webp|avif|css|js|woff2)$ {{
        expires 365d;
        add_header Cache-Control "public, no-transform, immutable";
    }}

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}"""
        else:
            config_filename = ".htaccess (Apache Web Server Standards)"
            config_code = f"""# Enable Rewrite Engine
RewriteEngine On

# 1. Force HTTPS
RewriteCond %{{HTTPS}} off
RewriteRule ^(.*)$ https://%{{HTTP_HOST}}%{{REQUEST_URI}} [L,R=301]

# 2. Force non-www (or canonical host)
RewriteCond %{{HTTP_HOST}} ^www\\.(.+)$ [NC]
RewriteRule ^(.*)$ https://%1/$1 [R=301,L]

# 3. Security Headers
<IfModule mod_headers.c>
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Cross-Origin-Opener-Policy "same-origin"
</IfModule>

# 4. Gzip Compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/javascript application/json image/svg+xml
</IfModule>"""

        return {
            "id": "section-infrastructure",
            "title": "2. Server Infrastructure, Security Headers & Protocol Standards",
            "description": "Server-level directives to guarantee A+ security header scores, eliminate redirect loops, and enable modern compression.",
            "code_block": {
                "filename": config_filename,
                "code": config_code,
                "language": "nginx" if "nginx" in config_filename else ("javascript" if "next" in config_filename else "apache")
            },
            "directives": [
                f"<strong>Strict-Transport-Security (HSTS)</strong>: Set to <code>max-age=31536000; includeSubDomains; preload</code> to enforce HTTPS everywhere.",
                "<strong>X-Content-Type-Options</strong>: Set to <code>nosniff</code> to prevent MIME type sniffing attacks.",
                f"<strong>Canonical Domain Enforcement</strong>: Choose non-www (<code>https://{self.parsed_domain}</code>) or www once. Issue a 301 permanent redirect from the alternative.",
                "<strong>Trailing Slash Strategy</strong>: Pick strict trailing slash or no trailing slash across all routes. Inconsistent slashes dilute PageRank equity.",
                "<strong>Compression</strong>: Verify Brotli (br) or Gzip is active on all text, CSS, JavaScript, and SVG assets."
            ]
        }

    def _build_section_robots(self) -> dict:
        robots_code = f"""# ==============================================================================
# Production robots.txt for {self.parsed_domain}
# Engineered by InersiaLab Software Department
# ==============================================================================

User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Disallow: /checkout/
Disallow: /search
Disallow: /*?*sort=
Disallow: /*?*filter=

# ------------------------------------------------------------------------------
# Verified Search Engine Crawlers (Full Crawl Access)
# ------------------------------------------------------------------------------
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# ------------------------------------------------------------------------------
# Generative AI & Conversational Search Bots (SearchGPT, Perplexity, Claude)
# ------------------------------------------------------------------------------
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Google-Extended
Allow: /

# ------------------------------------------------------------------------------
# Sitemap & AI Knowledge Files Declarations
# ------------------------------------------------------------------------------
Sitemap: {self.domain}/sitemap.xml
Sitemap: {self.domain}/sitemap_index.xml
"""

        return {
            "id": "section-robots",
            "title": "3. Production robots.txt & AI Crawler Directives",
            "description": "Standardized crawler control file ensuring optimal search indexing while welcoming next-generation AI search engines.",
            "code_block": {
                "filename": "public/robots.txt",
                "code": robots_code.strip(),
                "language": "text"
            },
            "rules": [
                f"Deploy strictly at the domain root: <code>{self.domain}/robots.txt</code>.",
                "Do NOT block CSS, JS, or image folders; search crawlers require them to render pages.",
                "Explicitly declare AI search engines (<code>OAI-SearchBot</code>, <code>PerplexityBot</code>) to guarantee citations in generative AI answers.",
                "Always point to the canonical XML sitemap location at the bottom of the file."
            ]
        }

    def _build_section_sitemaps(self) -> dict:
        sitemap_code = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  
  <!-- Homepage -->
  <url>
    <loc>{self.domain}/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>

  <!-- Core Service / Product Pillar -->
  <url>
    <loc>{self.domain}/services/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>

  <!-- About / Company -->
  <url>
    <loc>{self.domain}/about/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>

  <!-- Contact & Consultation -->
  <url>
    <loc>{self.domain}/contact/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>

</urlset>"""

        return {
            "id": "section-sitemaps",
            "title": "4. XML Sitemap Architecture & Submission Workflow",
            "description": "Clean, dynamic sitemap specifications ensuring 100% of canonical URLs are discovered immediately.",
            "code_block": {
                "filename": "public/sitemap.xml",
                "code": sitemap_code,
                "language": "xml"
            },
            "guidelines": [
                "<strong>Zero 404s in Sitemap</strong>: Every URL listed must return HTTP 200 OK. Never include redirects or broken URLs.",
                "<strong>Canonical Exclusivity</strong>: Only include canonical, indexable URLs (no <code>noindex</code> pages, no session query params).",
                "<strong>Automated Generation</strong>: Ensure your framework dynamically rebuilds the sitemap during CI/CD build or on new content publication.",
                f"<strong>Webmaster Registration</strong>: Immediately submit <code>{self.domain}/sitemap.xml</code> to Google Search Console and Bing Webmaster Tools upon domain DNS activation."
            ]
        }

    def _build_section_html_semantics(self) -> dict:
        head_code = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  
  <!-- Primary Meta Tags -->
  <title>{self.brand_name} — {self.description[:45]} | Official Site</title>
  <meta name="description" content="{self.description} Discover high-performance solutions tailored to your business needs." />
  <link rel="canonical" href="{self.domain}/" />
  
  <!-- Preconnect to Critical Asset CDNs -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{self.domain}/" />
  <meta property="og:title" content="{self.brand_name} — {self.description[:45]}" />
  <meta property="og:description" content="{self.description}" />
  <meta property="og:image" content="{self.domain}/assets/og-image.jpg" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />

  <!-- Twitter Cards -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{self.brand_name} — {self.description[:45]}" />
  <meta name="twitter:description" content="{self.description}" />
  <meta name="twitter:image" content="{self.domain}/assets/og-image.jpg" />

  <!-- Favicons -->
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="icon" href="/icon.svg" type="image/svg+xml" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
</head>
<body>
  <!-- Semantic Body Structure -->
  <header>
    <nav aria-label="Main Navigation">
      <!-- Accessible Links -->
    </nav>
  </header>

  <main>
    <!-- CRITICAL RULE: Exactly ONE <h1> per page -->
    <h1>Transforming Business Potential Through Modern Technology</h1>
    
    <section>
      <h2>Comprehensive Strategic Engineering Services</h2>
      <p>Substantive topic paragraph...</p>
    </section>
  </main>

  <footer>
    <!-- Footer links, NAP details, copyright -->
  </footer>
</body>
</html>"""

        return {
            "id": "section-html",
            "title": "5. Document Architecture, Semantic HTML & Heading Hierarchy",
            "description": "Baseline HTML5 standard template preventing common structural errors, missing tags, and heading hierarchy penalties.",
            "code_block": {
                "filename": "head-boilerplate.html",
                "code": head_code,
                "language": "html"
            },
            "rules": [
                "<strong>The Single H1 Rule</strong>: Exactly one semantic <code>&lt;h1&gt;</code> must exist per page. Never duplicate <code>&lt;h1&gt;</code>.",
                "<strong>NEVER Code UI Elements as Headings</strong>: A pervasive defect is coding form status messages (e.g. <em>'Thank you!'</em>), category badges, or modal dialogs as <code>&lt;h3&gt;</code> or <code>&lt;h4&gt;</code>. Use standard <code>&lt;span class='badge'&gt;</code> or <code>&lt;p&gt;</code>.",
                "<strong>Title Tag Character Target</strong>: Keep between 50 and 60 characters. Always include primary keyword + Brand Name.",
                "<strong>Meta Description Target</strong>: Keep between 120 and 155 characters with an action-oriented call to action."
            ]
        }

    def _build_section_international(self) -> dict:
        hreflang_code = f"""<!-- In document <head> of ALL language versions (English, French, Arabic): -->

<!-- Self-referencing link for English Homepage -->
<link rel="alternate" hreflang="en" href="{self.domain}/" />

<!-- Alternate link for French Version -->
<link rel="alternate" hreflang="fr" href="{self.domain}/fr/" />

<!-- Alternate link for Arabic Version (if active) -->
<link rel="alternate" hreflang="ar" href="{self.domain}/ar/" />

<!-- Mandatory x-default Fallback for unmatched regions -->
<link rel="alternate" hreflang="x-default" href="{self.domain}/" />"""

        return {
            "id": "section-international",
            "title": "6. Internationalization, Multilingual Architecture & Hreflang Reciprocity",
            "description": "Definitive multi-region setup preventing the duplicate content penalty and ensuring bidirectional hreflang validation.",
            "code_block": {
                "filename": "hreflang-boilerplate.html",
                "code": hreflang_code,
                "language": "html"
            },
            "directives": [
                f"<strong>Subdirectories over Subdomains</strong>: Use <code>{self.domain}/fr/</code> instead of <code>fr.{self.parsed_domain}</code>. Subdirectories consolidate domain authority and PageRank equity.",
                "<strong>Bidirectional Reciprocity</strong>: If Page A links to Page B as French alternate, Page B MUST link back to Page A as English alternate. If not reciprocal, Google ignores the hreflang entirely.",
                "<strong>Always Include x-default</strong>: Designate your primary international version as <code>hreflang='x-default'</code>.",
                "<strong>Arabic / Hebrew RTL Rules</strong>: Set <code>&lt;html lang='ar' dir='rtl'&gt;</code>. Use modern CSS logical properties (<code>margin-inline-start</code> instead of <code>margin-left</code>) to eliminate layout shift."
            ]
        }

    def _build_section_geo(self) -> dict:
        llms_code = f"""# {self.brand_name}
> {self.description}

## Core Services & Solutions
- Enterprise Architecture & Web Development: High-performance modern web platforms.
- Strategic Brand Engineering: Technical identity, digital positioning, and market presence.
- AI Automation Solutions: Custom intelligent workflows and generative AI integrations.

## Canonical Reference
- Official Website: {self.domain}
- Primary Documentation & Services: {self.domain}/services/
- Contact & Technical Inquiries: {self.domain}/contact/
"""

        answer_capsule_example = f"""<section class="service-block">
  <h2>What is Strategic Digital Transformation?</h2>
  
  <!-- 40-60 Word Self-Contained Answer Capsule for SearchGPT & Perplexity -->
  <p class="answer-capsule">
    Strategic digital transformation is the comprehensive integration of modern cloud architecture, 
    automated software pipelines, and data intelligence into an organization's core operations. 
    It modernizes legacy workflows, eliminates operational technical debt, and accelerates market delivery.
  </p>

  <p>Expanded detailed analysis, methodology, and implementation steps follow here...</p>
</section>"""

        return {
            "id": "section-geo",
            "title": "7. Generative Engine Optimization (GEO & AI Citability Strategy)",
            "description": "Architectural guidelines ensuring content is quoted, referenced, and cited by AI engines like SearchGPT, Perplexity, Claude, and Gemini.",
            "code_block": {
                "filename": "public/llms.txt",
                "code": llms_code.strip(),
                "language": "markdown"
            },
            "answer_capsule_sample": {
                "filename": "answer-capsule-pattern.html",
                "code": answer_capsule_example,
                "language": "html"
            },
            "best_practices": [
                "<strong>The 40–60 Word 'Answer Capsule'</strong>: Directly beneath every H2 or H3 question header, provide a concise, factual definition in 40–60 words. LLM extraction pipelines extract these capsules directly into AI summaries.",
                "<strong>Information Gain & Fact Density</strong>: Avoid vague marketing prose (<em>'we are the best'</em>). Use specific metrics, percentages, timeline steps, and concrete technical terms.",
                f"<strong>Deploy /llms.txt at Root</strong>: Publish clean markdown summaries at <code>{self.domain}/llms.txt</code> and <code>/llms-full.txt</code>.",
                "<strong>Structured Comparison Tables</strong>: Generative engines prioritize structured tables when answering comparison queries (e.g. <em>'Next.js vs Astro for e-commerce'</em>)."
            ]
        }

    def _build_section_schema(self) -> dict:
        org_schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{self.domain}/#organization",
            "name": self.brand_name,
            "url": self.domain,
            "logo": {
                "@type": "ImageObject",
                "url": f"{self.domain}/assets/logo.png",
                "width": 512,
                "height": 512
            },
            "description": self.description,
            "sameAs": [
                f"https://www.linkedin.com/company/{self.brand_name.lower().replace(' ', '')}",
                f"https://twitter.com/{self.brand_name.lower().replace(' ', '')}"
            ],
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Customer Service",
                "url": f"{self.domain}/contact/"
            }
        }

        website_schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{self.domain}/#website",
            "url": self.domain,
            "name": self.brand_name,
            "publisher": {
                "@id": f"{self.domain}/#organization"
            },
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{self.domain}/search?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        }

        return {
            "id": "section-schema",
            "title": "8. Schema.org JSON-LD Entity Graph Specification",
            "description": "Production-ready structured data templates to guarantee Google Rich Results eligibility and disambiguate your brand entity.",
            "code_block": {
                "filename": "schemas/organization_and_website.json",
                "code": f"""<!-- Include in document <head> of Homepage: -->\n<script type="application/ld+json">\n{json.dumps([org_schema, website_schema], indent=2)}\n</script>""",
                "language": "html"
            },
            "requirements": [
                "<strong>Single Consolidated Script</strong>: Place JSON-LD script inside the HTML <code>&lt;head&gt;</code>.",
                "<strong>Always Include Entity IDs (<code>@id</code>)</strong>: Linking entities via <code>@id</code> allows search engines to build an interconnected knowledge graph.",
                "<strong>Include Official <code>sameAs</code> Social Links</strong>: Linking to active LinkedIn, Twitter/X, and Crunchbase profiles disambiguates your entity in AI knowledge bases.",
                "<strong>BreadcrumbList on Subpages</strong>: Every subpage (e.g. <code>/services/web-development/</code>) must implement <code>BreadcrumbList</code> schema for Google search breadcrumbs."
            ]
        }

    def _build_section_core_web_vitals(self) -> dict:
        return {
            "id": "section-cwv",
            "title": "9. Performance & Core Web Vitals Pre-Emptive Engineering",
            "description": "Performance guidelines designed to achieve 95–100 Google Lighthouse scores and pass Core Web Vitals out of the box.",
            "cwv_targets": [
                {"metric": "LCP (Largest Contentful Paint)", "threshold": "< 1.2s", "target": "Preload hero image with fetchpriority='high'"},
                {"metric": "CLS (Cumulative Layout Shift)", "threshold": "0.00", "target": "Explicit width/height on 100% of images/videos"},
                {"metric": "INP (Interaction to Next Paint)", "threshold": "< 100ms", "target": "Defer non-critical scripts; zero main-thread blockage"}
            ],
            "rules": [
                "<strong>Hero Image Preloading</strong>: For the above-the-fold hero image, add: <code>&lt;link rel='preload' as='image' href='/hero.webp' fetchpriority='high'&gt;</code>.",
                "<strong>Zero Layout Shift (CLS = 0)</strong>: Never render an image, video, iframe, or ad without explicit HTML <code>width</code> and <code>height</code> attributes or CSS <code>aspect-ratio</code>.",
                "<strong>Font Display Strategy</strong>: Use <code>font-display: swap;</code> and self-host fonts (e.g. WOFF2). Avoid external Google Fonts requests when possible to reduce connection overhead.",
                "<strong>Script Deferral</strong>: Add <code>defer</code> or <code>async</code> to all non-critical JavaScript. Keep initial bundle size under 150KB gzip."
            ]
        }

    def _build_section_media_policy(self) -> dict:
        return {
            "id": "section-media",
            "title": "10. Image & Media Asset Engineering Standards",
            "description": "Standard operating procedures for imagery and media to prevent accessibility failures and layout shifts.",
            "standards": [
                "<strong>Format Hierarchy</strong>: Use <strong>AVIF</strong> first, with <strong>WebP</strong> fallback. Avoid uncompressed PNGs/JPEGs except where lossless transparency is essential.",
                "<strong>Descriptive Kebab-Case Filenames</strong>: Never upload <code>IMG_8943.jpg</code>. Always name files descriptively: <code>software-architecture-consultation.webp</code>.",
                "<strong>Descriptive Alt Attributes</strong>: Every informative image must have a concise, descriptive <code>alt</code> attribute explaining what the image depicts. Purely decorative elements must explicitly use <code>alt=''</code>.",
                "<strong>Responsive Sizing</strong>: Use modern <code>srcset</code> and <code>sizes</code> attributes so mobile devices do not download desktop 2000px assets."
            ]
        }

    def _build_section_anti_patterns(self) -> dict:
        anti_patterns = [
            {"num": "01", "error": "Multiple H1 tags or missing H1 tag", "fix": "Ensure strictly ONE <h1> per page representing the core topic."},
            {"num": "02", "error": "Using H3 or H4 for form status or UI badges", "fix": "Never use heading tags for 'Thank you!' or tags. Use span or p elements."},
            {"num": "03", "error": "Missing width and height on images (CLS bloat)", "fix": "Declare explicit width='800' height='600' on every single image tag."},
            {"num": "04", "error": "Empty or missing image alt attributes", "fix": "Write descriptive alt tags explaining the image's context."},
            {"num": "05", "error": "Inconsistent canonical domain (both www and non-www 200)", "fix": "Enforce a 301 permanent redirect from www to non-www."},
            {"num": "06", "error": "Inconsistent trailing slash structure (/page vs /page/)", "fix": "Configure the web server to enforce one pattern via 301 redirect."},
            {"num": "07", "error": "Missing HSTS security header", "fix": "Configure Strict-Transport-Security: max-age=31536000; includeSubDomains; preload."},
            {"num": "08", "error": "Blocking AI search bots in robots.txt", "fix": "Explicitly allow GPTBot, OAI-SearchBot, PerplexityBot, and ClaudeBot."},
            {"num": "09", "error": "Broken URLs or 404s inside XML sitemap", "fix": "Automate sitemap generation from live routes; never hardcode URLs."},
            {"num": "10", "error": "Missing x-default in multilingual hreflang", "fix": "Always define a fallback hreflang='x-default' pointing to the primary language."},
            {"num": "11", "error": "Render-blocking external CSS/JS in head", "fix": "Defer non-critical scripts and preload critical viewport assets."},
            {"num": "12", "error": "Non-descriptive anchor text ('click here', 'read more')", "fix": "Use keyword-rich anchor text: 'Explore our software engineering services'."},
            {"num": "13", "error": "Orphan pages with zero internal links", "fix": "Ensure every public page is accessible within 3 clicks of the homepage."},
            {"num": "14", "error": "Missing OpenGraph and Twitter Card images", "fix": "Provide a 1200x630px og:image for attractive social sharing previews."},
            {"num": "15", "error": "Generic 'Lorem Ipsum' or thin copy under 250 words", "fix": "Author at least 400+ words of comprehensive, authoritative original copy."},
            {"num": "16", "error": "Invalid JSON-LD syntax or missing @id", "fix": "Validate schemas against Google Rich Results Test before shipping."},
            {"num": "17", "error": "Generic title tags ('Home', 'Services')", "fix": "Author unique titles: 'Custom Software Development — InersiaLab'."},
            {"num": "18", "error": "Meta descriptions over 160 characters (truncated)", "fix": "Keep meta descriptions between 120 and 155 characters."},
            {"num": "19", "error": "Deploying with 'Disallow: /' left over from staging", "fix": "Verify robots.txt on the production domain before public launch."},
            {"num": "20", "error": "Missing /llms.txt generative AI standard file", "fix": "Publish /llms.txt at domain root containing a clean markdown summary."}
        ]

        return {
            "id": "section-anti-patterns",
            "title": "11. The Anti-Pattern Handbook — 20 Critical Pitfalls to Avoid",
            "description": "The exact technical defects discovered by the InersiaLab Audit Engine on existing websites and how to avoid them during coding.",
            "anti_patterns": anti_patterns
        }

    def _build_section_checklist(self) -> dict:
        checks = [
            {"cat": "Technical & Server", "item": "HTTPS enforced with valid TLS certificate and 301 redirects from HTTP"},
            {"cat": "Technical & Server", "item": "HSTS header configured with max-age=31536000 and includeSubDomains"},
            {"cat": "Technical & Server", "item": "X-Content-Type-Options: nosniff and X-Frame-Options: SAMEORIGIN active"},
            {"cat": "Technical & Server", "item": "Brotli or Gzip compression enabled across all text, CSS, and JS assets"},
            {"cat": "Crawling & Discovery", "item": "robots.txt active at /robots.txt declaring sitemap and allowing AI bots"},
            {"cat": "Crawling & Discovery", "item": "sitemap.xml returns HTTP 200 and contains only canonical, live URLs"},
            {"cat": "Crawling & Discovery", "item": "Google Search Console and Bing Webmaster Tools property verified"},
            {"cat": "HTML & Semantics", "item": "Every page has exactly one <h1> containing the primary keyword"},
            {"cat": "HTML & Semantics", "item": "Zero UI status badges or decorative components coded as <h3> or <h4>"},
            {"cat": "HTML & Semantics", "item": "Unique <title> tag between 50–60 characters on every URL"},
            {"cat": "HTML & Semantics", "item": "Unique <meta name='description'> between 120–155 characters on every URL"},
            {"cat": "HTML & Semantics", "item": "Canonical <link rel='canonical'> matches exact production URL"},
            {"cat": "Social & Sharing", "item": "OpenGraph og:title, og:description, and 1200x630 og:image configured"},
            {"cat": "Social & Sharing", "item": "Twitter Card meta tags active with summary_large_image"},
            {"cat": "Structured Data", "item": "Organization and WebSite JSON-LD schemas validated in Google Rich Results"},
            {"cat": "Structured Data", "item": "BreadcrumbList schema active on all category and sub-pages"},
            {"cat": "Core Web Vitals", "item": "Hero above-the-fold image preloaded with fetchpriority='high'"},
            {"cat": "Core Web Vitals", "item": "100% of images and videos declare explicit width and height dimensions"},
            {"cat": "Core Web Vitals", "item": "Non-critical JavaScript deferred; initial JS bundle under 150KB gzip"},
            {"cat": "Core Web Vitals", "item": "Web fonts use font-display: swap with WOFF2 format"},
            {"cat": "AI Search (GEO)", "item": "/llms.txt published at domain root with clean service summaries"},
            {"cat": "AI Search (GEO)", "item": "40–60 word Answer Capsules placed beneath primary H2 question headers"},
            {"cat": "International", "item": "Bidirectional hreflang reciprocal links validated if multilingual"},
            {"cat": "Accessibility", "item": "Every informative image contains descriptive alt attribute text"},
            {"cat": "Final Verification", "item": "Run full InersiaLab Audit on staging environment prior to DNS switch"}
        ]

        return {
            "id": "section-checklist",
            "title": "12. 25-Point Pre-Launch QA Verification Checklist",
            "description": "Rigorous pre-launch signoff checklist required before pointing domain DNS records to production.",
            "checks": checks
        }


# ---------------------------------------------------------------------------
# HTML & PDF Generation Engine for the Architecture Blueprint
# ---------------------------------------------------------------------------

def build_blueprint_html(blueprint_data: dict) -> str:
    """Renders the architectural specification into clean, branded InersiaLab HTML."""
    brand = blueprint_data["brand_name"]
    domain = blueprint_data["domain"]
    sections = blueprint_data["sections"]
    timestamp = blueprint_data["timestamp"]

    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pre-Launch Website Architecture Blueprint — {brand}</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      box-shadow: none !important;
      text-shadow: none !important;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 9.5pt;
      line-height: 1.45;
      color: {COLOR_BLACK};
      background: #ffffff;
      padding: 0;
    }}
    .blueprint-page {{
      padding: 32px 30px;
      page-break-after: always;
      break-after: page;
    }}
    .cover-header {{
      border-bottom: 2px solid {COLOR_BLACK};
      padding-bottom: 14px;
      margin-bottom: 30px;
    }}
    .org-label {{
      font-size: 9pt;
      font-weight: 800;
      letter-spacing: 0.8px;
      color: {COLOR_MUTED};
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    h1.report-title {{
      font-size: 24pt;
      font-weight: 800;
      color: {COLOR_BLACK};
      line-height: 1.15;
      margin-bottom: 8px;
    }}
    .report-subtitle {{
      font-size: 11pt;
      color: {COLOR_MUTED};
      margin-bottom: 24px;
    }}
    .meta-box {{
      border: 1px solid {COLOR_BORDER};
      padding: 16px 20px;
      margin-bottom: 30px;
      background: #ffffff;
    }}
    .meta-row {{
      display: flex;
      margin-bottom: 8px;
      font-size: 9.5pt;
    }}
    .meta-lbl {{
      width: 180px;
      font-weight: 700;
      color: {COLOR_MUTED};
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 30px;
    }}
    .kpi-card {{
      border: 1px solid {COLOR_BORDER};
      padding: 14px 10px;
      text-align: center;
    }}
    .kpi-val {{
      font-size: 18pt;
      font-weight: 800;
      color: {COLOR_GREEN};
      margin-bottom: 2px;
    }}
    .kpi-lbl {{
      font-size: 7.5pt;
      font-weight: 700;
      color: {COLOR_MUTED};
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .section-container {{
      padding: 24px 24px 16px 24px;
      page-break-after: always;
      break-after: page;
    }}
    .section-header {{
      border-bottom: 2px solid {COLOR_BLACK};
      padding-bottom: 6px;
      margin-bottom: 12px;
    }}
    .section-header h2 {{
      font-size: 14pt;
      font-weight: 800;
      color: {COLOR_BLACK};
    }}
    .section-desc {{
      font-size: 9pt;
      color: {COLOR_MUTED};
      margin-bottom: 16px;
      line-height: 1.4;
    }}
    .code-container {{
      margin: 14px 0 20px 0;
      border: 1px solid {COLOR_BLACK};
      background: #ffffff;
    }}
    .code-header {{
      background: {COLOR_BLACK};
      color: #ffffff;
      padding: 5px 12px;
      font-size: 8pt;
      font-family: "Consolas", monospace;
      font-weight: 700;
    }}
    pre.code-block {{
      padding: 12px;
      font-family: "Consolas", monospace;
      font-size: 8pt;
      line-height: 1.4;
      color: {COLOR_BLACK};
      background: #ffffff;
      white-space: pre-wrap;
      word-break: break-all;
      overflow-x: auto;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 18px;
      font-size: 8.5pt;
    }}
    .data-table th {{
      background: #f9fafb;
      padding: 8px 10px;
      border-bottom: 2px solid {COLOR_BLACK};
      border-right: 1px solid {COLOR_BORDER};
      text-align: left;
      font-size: 7.5pt;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .data-table td {{
      padding: 8px 10px;
      border-bottom: 1px solid {COLOR_BORDER};
      border-right: 1px solid {COLOR_BORDER};
      vertical-align: top;
      line-height: 1.35;
    }}
    .anti-pattern-num {{
      font-weight: 800;
      color: {COLOR_RED};
      text-align: center;
      width: 40px;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 6px;
      font-size: 7.5pt;
      font-weight: 700;
      text-transform: uppercase;
      border: 1px solid {COLOR_BLACK};
    }}
    .badge-red {{
      color: {COLOR_RED};
      border-color: {COLOR_RED};
    }}
    .badge-green {{
      color: {COLOR_GREEN};
      border-color: {COLOR_GREEN};
    }}
    .footer-note {{
      margin-top: 30px;
      padding-top: 14px;
      border-top: 1px solid {COLOR_BORDER};
      font-size: 8pt;
      color: {COLOR_MUTED};
      display: flex;
      justify-content: space-between;
    }}
    @media print {{
      .section-container {{
        page-break-after: always !important;
        break-after: page !important;
      }}
    }}
  </style>
</head>
<body>
""")

    # ---------------- COVER PAGE ----------------
    html_parts.append(f"""
    <div class="blueprint-page">
      <div class="cover-header">
        <div class="org-label">InersiaLab Software Department</div>
        <h1 class="report-title">Pre-Launch Website Architecture &amp; Engineering Blueprint</h1>
        <div class="report-subtitle">Comprehensive Technical SEO, Generative Engine Optimization (GEO) &amp; Core Web Vitals Specification</div>
      </div>

      <div class="meta-box">
        <div class="meta-row"><span class="meta-lbl">Project / Brand:</span><strong>{brand}</strong></div>
        <div class="meta-row"><span class="meta-lbl">Target Canonical Domain:</span><code>{domain}</code></div>
        <div class="meta-row"><span class="meta-lbl">Architectural Specification:</span>Enterprise Zero-Defect Standard</div>
        <div class="meta-row"><span class="meta-lbl">Date Compiled:</span>{timestamp}</div>
        <div class="meta-row"><span class="meta-lbl">Issuing Authority:</span>Software Department of InersiaLab</div>
      </div>

      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-val">100/100</div>
          <div class="kpi-lbl">Target Tech SEO</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val">&lt; 1.0s</div>
          <div class="kpi-lbl">Target LCP Speed</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val">100%</div>
          <div class="kpi-lbl">GEO Citability</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val">0.00</div>
          <div class="kpi-lbl">Target CLS Shift</div>
        </div>
      </div>

      <div style="border: 1px solid {COLOR_BORDER}; padding: 18px 20px; margin-bottom: 30px; font-size: 9pt; line-height: 1.5;">
        <h4 style="font-size: 10pt; font-weight: 800; margin-bottom: 6px; text-transform: uppercase; color: {COLOR_BLACK};">Architectural Directive</h4>
        <p>This engineering manual establishes the mandatory pre-launch technical standards for <strong>{brand}</strong>.
        Every code snippet, server directive, schema template, and semantic layout rule provided within this manual must be 
        implemented verbatim by the development team prior to production deployment. Compliance guarantees zero technical debt, 
        instant crawl indexing, and maximum quotation density across both traditional search engines and next-generation AI platforms.</p>
      </div>

      <div class="footer-note">
        <span>Report generated by the Software Department of InersiaLab</span>
        <span>Confidential &amp; Proprietary Engineering Specification</span>
      </div>
    </div>
    """)

    # ---------------- TABLE OF CONTENTS ----------------
    html_parts.append(f"""
    <div class="blueprint-page">
      <div class="section-header">
        <h2>Table of Contents &amp; Blueprint Navigation</h2>
      </div>
      <p class="section-desc">Index of all 12 core architecture disciplines and implementation guides contained in this manual.</p>

      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 50px; text-align: center;">Sec</th>
            <th>Discipline &amp; Engineering Focus</th>
            <th style="width: 150px; text-align: center;">Standard</th>
          </tr>
        </thead>
        <tbody>
          <tr><td style="text-align: center; font-weight: 700;">01</td><td><strong>Executive Architectural Strategy &amp; Target KPIs</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Scope summary, target benchmarks, and risk mitigation</span></td><td style="text-align: center;"><span class="badge">Mandatory</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">02</td><td><strong>Server Infrastructure, Security Headers &amp; Protocols</strong><br><span style="color: #6b7280; font-size: 7.5pt;">HSTS, CSP, MIME nosniff, Brotli compression, canonical redirects</span></td><td style="text-align: center;"><span class="badge">Grade A+</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">03</td><td><strong>Production robots.txt &amp; AI Crawler Directives</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Crawl permissions for GPTBot, PerplexityBot, ClaudeBot, Googlebot</span></td><td style="text-align: center;"><span class="badge">Universal</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">04</td><td><strong>XML Sitemap Architecture &amp; Submission</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Dynamic sitemap generation, priority tags, zero-404 guarantee</span></td><td style="text-align: center;"><span class="badge">Automated</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">05</td><td><strong>Document Architecture &amp; Semantic HTML5</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Boilerplate head, OpenGraph, Twitter Cards, single H1 rule</span></td><td style="text-align: center;"><span class="badge">W3C Valid</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">06</td><td><strong>Internationalization &amp; Multilingual SEO</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Bidirectional hreflang reciprocity, x-default, RTL styling</span></td><td style="text-align: center;"><span class="badge">Global</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">07</td><td><strong>Generative Engine Optimization (GEO &amp; AI Citability)</strong><br><span style="color: #6b7280; font-size: 7.5pt;">/llms.txt files, 40-60 word Answer Capsules, fact-density metrics</span></td><td style="text-align: center;"><span class="badge">AI Ready</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">08</td><td><strong>Schema.org JSON-LD Knowledge Graph</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Organization, WebSite, Breadcrumbs, Rich Snippet eligibility</span></td><td style="text-align: center;"><span class="badge">Entity Valid</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">09</td><td><strong>Performance &amp; Core Web Vitals Engineering</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Sub-second LCP, zero CLS shift, script deferral, font-display: swap</span></td><td style="text-align: center;"><span class="badge">100/100 CWV</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">10</td><td><strong>Image &amp; Media Asset Standards</strong><br><span style="color: #6b7280; font-size: 7.5pt;">WebP/AVIF policy, explicit width/height, kebab-case naming</span></td><td style="text-align: center;"><span class="badge">Optimized</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">11</td><td><strong>The Anti-Pattern Handbook (What NOT to Do)</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Top 20 technical defects discovered during audits and their prevention</span></td><td style="text-align: center;"><span class="badge badge-red">Critical</span></td></tr>
          <tr><td style="text-align: center; font-weight: 700;">12</td><td><strong>25-Point Pre-Launch QA Verification Checklist</strong><br><span style="color: #6b7280; font-size: 7.5pt;">Mandatory signoff checklist prior to production DNS activation</span></td><td style="text-align: center;"><span class="badge badge-green">Signoff</span></td></tr>
        </tbody>
      </table>

      <div class="footer-note">
        <span>Report generated by the Software Department of InersiaLab</span>
        <span>Page 2 &bull; Architectural Navigation Directory</span>
      </div>
    </div>
    """)

    # ---------------- BODY SECTIONS ----------------
    for sec in sections:
        html_parts.append(f"""
        <div class="section-container" id="{sec['id']}">
          <div class="section-header">
            <h2>{sec['title']}</h2>
          </div>
          <p class="section-desc">{sec['description']}</p>
        """)

        # Custom HTML content
        if "content" in sec:
            html_parts.append(sec["content"])

        # Code blocks
        if "code_block" in sec:
            cb = sec["code_block"]
            html_parts.append(f"""
            <div class="code-container">
              <div class="code-header">{cb['filename']}</div>
              <pre class="code-block">{_escape_html(cb['code'])}</pre>
            </div>
            """)

        # Extra code sample (like answer capsules)
        if "answer_capsule_sample" in sec:
            cs = sec["answer_capsule_sample"]
            html_parts.append(f"""
            <div class="code-container">
              <div class="code-header">{cs['filename']}</div>
              <pre class="code-block">{_escape_html(cs['code'])}</pre>
            </div>
            """)

        # Directives / Guidelines
        directives = sec.get("directives") or sec.get("guidelines") or sec.get("rules") or sec.get("standards") or sec.get("best_practices") or sec.get("requirements")
        if directives:
            html_parts.append("""
            <table class="data-table">
              <thead><tr><th style="width: 40px; text-align: center;">#</th><th>Implementation Directives &amp; Coding Rules</th></tr></thead>
              <tbody>
            """)
            for idx, d in enumerate(directives, 1):
                html_parts.append(f"<tr><td style='text-align: center; font-weight: 700;'>{idx:02d}</td><td>{d}</td></tr>")
            html_parts.append("</tbody></table>")

        # Core Web Vitals targets
        if "cwv_targets" in sec:
            html_parts.append("""
            <table class="data-table">
              <thead><tr><th>Core Web Vital Metric</th><th style="width: 120px; text-align: center;">Target Threshold</th><th>Technical Strategy</th></tr></thead>
              <tbody>
            """)
            for t in sec["cwv_targets"]:
                html_parts.append(f"<tr><td><strong>{t['metric']}</strong></td><td style='text-align: center; font-weight: 700; color: {COLOR_GREEN};'>{t['threshold']}</td><td>{t['target']}</td></tr>")
            html_parts.append("</tbody></table>")

        # Anti-pattern list
        if "anti_patterns" in sec:
            html_parts.append("""
            <table class="data-table">
              <thead>
                <tr>
                  <th style="width: 40px; text-align: center;">ID</th>
                  <th style="width: 45%; color: #b91c1c;">Identified Pitfall / Anti-Pattern (DO NOT DO)</th>
                  <th style="width: 50%; color: #15803d;">Correct Architectural Standard (MUST DO)</th>
                </tr>
              </thead>
              <tbody>
            """)
            for ap in sec["anti_patterns"]:
                html_parts.append(f"""
                <tr>
                  <td class="anti-pattern-num">{ap['num']}</td>
                  <td><strong style="color: #b91c1c;">{_escape_html(ap['error'])}</strong></td>
                  <td><strong style="color: #15803d;">{_escape_html(ap['fix'])}</strong></td>
                </tr>
                """)
            html_parts.append("</tbody></table>")

        # Checklist
        if "checks" in sec:
            html_parts.append("""
            <table class="data-table">
              <thead>
                <tr>
                  <th style="width: 40px; text-align: center;">Sign</th>
                  <th style="width: 180px;">Discipline</th>
                  <th>Pre-Launch Verification Item</th>
                </tr>
              </thead>
              <tbody>
            """)
            for chk in sec["checks"]:
                html_parts.append(f"""
                <tr>
                  <td style="text-align: center;"><span style="display: inline-block; width: 14px; height: 14px; border: 1.5px solid #111827;"></span></td>
                  <td><strong>{chk['cat']}</strong></td>
                  <td>{chk['item']}</td>
                </tr>
                """)
            html_parts.append("</tbody></table>")

        html_parts.append(f"""
          <div class="footer-note">
            <span>Report generated by the Software Department of InersiaLab</span>
            <span>{sec['title'].split('.')[0]} &bull; Pre-Launch Architectural Manual</span>
          </div>
        </div>
        """)

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


# ---------------------------------------------------------------------------
# PDF Manual Generation via Playwright
# ---------------------------------------------------------------------------

def generate_blueprint_pdf(blueprint_data: dict, output_path: str = None) -> str:
    """Renders the HTML blueprint into a publication-grade PDF using Playwright."""
    if output_path is None:
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        safe_brand = re.sub(r'[^a-zA-Z0-9_]', '_', blueprint_data["brand_name"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(downloads, f"Architecture_Blueprint_{safe_brand}_{timestamp}.pdf")

    html_content = build_blueprint_html(blueprint_data)

    # Save temporary HTML
    html_path = output_path.replace(".pdf", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"  [blueprint] Rendering Architecture Manual PDF via Playwright...")
    from playwright.sync_api import sync_playwright

    playwright_paths = [
        os.path.expanduser("~/.gemini/config/skills/claude-seo/ms-playwright"),
        os.path.expanduser("~/.claude/skills/seo/ms-playwright"),
    ]

    browser_path = None
    for pw_path in playwright_paths:
        if os.path.exists(pw_path):
            for dirpath, dirnames, filenames in os.walk(pw_path):
                for fn in filenames:
                    if fn in ("chrome.exe", "chromium.exe", "chromium"):
                        browser_path = os.path.join(dirpath, fn)
                        break
                if browser_path:
                    break
        if browser_path:
            break

    if os.path.exists(playwright_paths[0]):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = playwright_paths[0]

    with sync_playwright() as p:
        launch_args = {"headless": True}
        if browser_path:
            launch_args["executable_path"] = browser_path
        browser = p.chromium.launch(**launch_args)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "12mm", "bottom": "12mm", "left": "8mm", "right": "8mm"},
        )
        browser.close()

    print(f"  [blueprint] Architecture Blueprint PDF generated: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Turnkey Starter Kit Generator (Code Files to Disk)
# ---------------------------------------------------------------------------

def generate_blueprint_starter_kit(blueprint_data: dict, target_dir: str = None) -> str:
    """Exports ready-to-use configuration files into a project starter folder."""
    brand = blueprint_data["brand_name"]
    safe_brand = re.sub(r'[^a-zA-Z0-9_]', '_', brand)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if target_dir is None:
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        target_dir = os.path.join(downloads, f"StarterKit_{safe_brand}_{timestamp}")

    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(os.path.join(target_dir, "schemas"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "public"), exist_ok=True)

    # Extract code blocks from sections
    for sec in blueprint_data["sections"]:
        if "code_block" in sec:
            cb = sec["code_block"]
            fn = cb["filename"]
            base_fn = os.path.basename(fn)
            if "schema" in fn.lower():
                out_p = os.path.join(target_dir, "schemas", base_fn)
            elif "robots" in fn.lower() or "sitemap" in fn.lower() or "llms" in fn.lower():
                out_p = os.path.join(target_dir, "public", base_fn)
            else:
                out_p = os.path.join(target_dir, base_fn)

            with open(out_p, "w", encoding="utf-8") as f:
                f.write(cb["code"])

    # Write README in starter kit
    readme_path = os.path.join(target_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"""# {brand} — Pre-Launch Architecture Starter Kit
Generated by the Software Department of InersiaLab on {blueprint_data['timestamp']}

This starter kit contains turnkey configuration files engineered to guarantee 
100/100 Technical SEO, Core Web Vitals, and Generative AI (GEO) citability.

## Included Files
- `public/robots.txt`: Optimized crawler rules including modern AI search bots.
- `public/sitemap.xml`: Initial XML sitemap declaring canonical URLs.
- `public/llms.txt`: Machine-readable summary for AI search engines (SearchGPT, Perplexity).
- `head-boilerplate.html`: Clean HTML5 `<head>` template with OpenGraph and preconnects.
- `schemas/`: Turnkey Schema.org JSON-LD scripts.
- Server configuration files tailored to your hosting environment.

Deploy these files into your new repository root before committing your first production build.
""")

    print(f"  [blueprint] Turnkey starter kit generated: {target_dir}")
    return target_dir
