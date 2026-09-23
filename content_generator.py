"""InersiaLab Software Department - Pre-Launch Website Page & Section Content Generator.

Generates comprehensive, SEO/GEO-optimized structured text content for every page
of a new website before development begins. Outputs clean semantic Markdown, HTML
structure, and JSON for headless CMS ingestion.

Key design goals:
- Strict heading hierarchy (single H1, ordered H2>H3, zero skipped levels)
- Title tags 50-60 chars, Meta descriptions 140-160 chars
- First-sentence Answer Engine Optimization (AEO) hooks per section
- E-E-A-T depth: credentials, trust signals, author expertise
- Schema.org JSON-LD per page
- GEO citability: definitive statements, statistical claims, entity lists
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


# ---------------------------------------------------------------------------
# Industry Presets - Default page sets per website archetype
# ---------------------------------------------------------------------------

INDUSTRY_PRESETS = {
    "healthcare_medical": {
        "label": "Healthcare, Medical Clinic & Dental Services",
        "tone": "professional, reassuring, clinically authoritative",
        "audience": "patients seeking medical or dental treatment",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Us / Our Clinic", "required": True},
            {"id": "services_overview", "title": "Our Services / Treatments", "required": True},
            {"id": "service_detail_1", "title": "Service: [Primary Treatment]", "required": False},
            {"id": "service_detail_2", "title": "Service: [Secondary Treatment]", "required": False},
            {"id": "service_detail_3", "title": "Service: [Tertiary Treatment]", "required": False},
            {"id": "doctors_team", "title": "Our Doctors / Medical Team", "required": False},
            {"id": "before_after", "title": "Patient Results / Before & After", "required": False},
            {"id": "testimonials", "title": "Patient Testimonials & Reviews", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "blog", "title": "Health Blog / Medical Articles", "required": False},
            {"id": "contact", "title": "Contact / Book Appointment", "required": True},
            {"id": "privacy_policy", "title": "Privacy Policy & HIPAA Notice", "required": False},
        ],
        "schema_type": "MedicalBusiness",
        "keywords_hint": "medical treatment, healthcare clinic, patient care, certified doctors",
    },
    "technology_software": {
        "label": "Technology, SaaS & Software Engineering",
        "tone": "innovative, technical yet accessible, forward-thinking",
        "audience": "business decision-makers, CTOs, developers, and technical teams",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Us / Our Mission", "required": True},
            {"id": "services_overview", "title": "Our Solutions / Products", "required": True},
            {"id": "service_detail_1", "title": "Solution: [Core Platform]", "required": False},
            {"id": "service_detail_2", "title": "Solution: [API / Integration]", "required": False},
            {"id": "service_detail_3", "title": "Solution: [Consulting / Custom Dev]", "required": False},
            {"id": "pricing", "title": "Pricing & Plans", "required": False},
            {"id": "case_studies", "title": "Case Studies & Success Stories", "required": False},
            {"id": "integrations", "title": "Integrations & Technology Stack", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "blog", "title": "Engineering Blog / Tech Insights", "required": False},
            {"id": "contact", "title": "Contact / Request Demo", "required": True},
            {"id": "careers", "title": "Careers / Join Our Team", "required": False},
        ],
        "schema_type": "SoftwareApplication",
        "keywords_hint": "SaaS platform, software engineering, digital transformation, API integration",
    },
    "ecommerce_retail": {
        "label": "E-Commerce & Online Retail Store",
        "tone": "engaging, benefit-driven, trust-building",
        "audience": "online shoppers and retail buyers",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Our Brand", "required": True},
            {"id": "collections", "title": "Shop All / Collections", "required": True},
            {"id": "category_1", "title": "Category: [Primary Product Line]", "required": False},
            {"id": "category_2", "title": "Category: [Secondary Product Line]", "required": False},
            {"id": "bestsellers", "title": "Best Sellers / Featured Products", "required": False},
            {"id": "new_arrivals", "title": "New Arrivals", "required": False},
            {"id": "reviews", "title": "Customer Reviews & Ratings", "required": False},
            {"id": "faq", "title": "FAQ - Shipping, Returns & Orders", "required": True},
            {"id": "size_guide", "title": "Size Guide / Product Specs", "required": False},
            {"id": "blog", "title": "Style Guide / Lifestyle Blog", "required": False},
            {"id": "contact", "title": "Contact / Customer Support", "required": True},
            {"id": "shipping_returns", "title": "Shipping & Returns Policy", "required": False},
        ],
        "schema_type": "Store",
        "keywords_hint": "online store, shop, buy, free shipping, customer reviews, quality products",
    },
    "digital_agency": {
        "label": "Digital Agency, Marketing & Creative Services",
        "tone": "bold, creative, results-oriented",
        "audience": "business owners, marketing managers, startup founders",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Our Agency", "required": True},
            {"id": "services_overview", "title": "Our Services", "required": True},
            {"id": "service_detail_1", "title": "Service: [Web Design & Development]", "required": False},
            {"id": "service_detail_2", "title": "Service: [SEO & Digital Marketing]", "required": False},
            {"id": "service_detail_3", "title": "Service: [Branding & Creative]", "required": False},
            {"id": "portfolio", "title": "Portfolio / Our Work", "required": False},
            {"id": "case_studies", "title": "Case Studies & Results", "required": False},
            {"id": "process", "title": "Our Process / How We Work", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "blog", "title": "Insights Blog / Industry Trends", "required": False},
            {"id": "contact", "title": "Contact / Get a Quote", "required": True},
            {"id": "careers", "title": "Careers / Join Our Team", "required": False},
        ],
        "schema_type": "ProfessionalService",
        "keywords_hint": "digital agency, web design, SEO, branding, marketing strategy",
    },
    "finance_legal": {
        "label": "Financial, Legal, Accounting & Consulting",
        "tone": "authoritative, trustworthy, precise",
        "audience": "business executives, entrepreneurs, individuals seeking advisory",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Our Firm", "required": True},
            {"id": "services_overview", "title": "Practice Areas / Services", "required": True},
            {"id": "service_detail_1", "title": "Service: [Core Practice Area]", "required": False},
            {"id": "service_detail_2", "title": "Service: [Secondary Practice]", "required": False},
            {"id": "team", "title": "Our Attorneys / Advisors Team", "required": False},
            {"id": "case_studies", "title": "Case Results / Client Outcomes", "required": False},
            {"id": "testimonials", "title": "Client Testimonials", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "resources", "title": "Legal Resources / Knowledge Center", "required": False},
            {"id": "blog", "title": "Insights & Analysis Blog", "required": False},
            {"id": "contact", "title": "Contact / Schedule Consultation", "required": True},
        ],
        "schema_type": "ProfessionalService",
        "keywords_hint": "legal services, financial consulting, accounting firm, business advisory",
    },
    "real_estate": {
        "label": "Real Estate, Property Management & Architecture",
        "tone": "premium, informative, location-specific",
        "audience": "property buyers, investors, tenants, and homeowners",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Our Agency", "required": True},
            {"id": "properties", "title": "Property Listings / Available Properties", "required": True},
            {"id": "buy", "title": "Buy a Property", "required": False},
            {"id": "sell", "title": "Sell Your Property", "required": False},
            {"id": "rent", "title": "Rental Properties", "required": False},
            {"id": "neighborhoods", "title": "Neighborhoods & Area Guides", "required": False},
            {"id": "agents", "title": "Our Agents / Team", "required": False},
            {"id": "testimonials", "title": "Client Success Stories", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "blog", "title": "Real Estate Market Blog", "required": False},
            {"id": "contact", "title": "Contact / Free Valuation", "required": True},
        ],
        "schema_type": "RealEstateAgent",
        "keywords_hint": "real estate, property for sale, buy apartment, rental, investment",
    },
    "education_courses": {
        "label": "Education, Academy, Online Courses & Coaching",
        "tone": "inspiring, knowledgeable, supportive",
        "audience": "students, professionals seeking upskilling, lifelong learners",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Our Academy", "required": True},
            {"id": "courses_overview", "title": "All Courses / Programs", "required": True},
            {"id": "course_detail_1", "title": "Course: [Flagship Program]", "required": False},
            {"id": "course_detail_2", "title": "Course: [Certification Program]", "required": False},
            {"id": "instructors", "title": "Our Instructors / Coaches", "required": False},
            {"id": "student_success", "title": "Student Success Stories", "required": False},
            {"id": "pricing", "title": "Pricing & Enrollment", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "blog", "title": "Learning Resources Blog", "required": False},
            {"id": "contact", "title": "Contact / Enroll Now", "required": True},
        ],
        "schema_type": "EducationalOrganization",
        "keywords_hint": "online courses, education, training, certification, development",
    },
    "hospitality_tourism": {
        "label": "Hospitality, Travel, Tourism & Restaurants",
        "tone": "welcoming, experiential, sensory-rich",
        "audience": "travelers, tourists, food enthusiasts, event planners",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Us / Our Story", "required": True},
            {"id": "rooms_menu", "title": "Rooms / Menu / Experiences", "required": True},
            {"id": "dining", "title": "Dining / Restaurant", "required": False},
            {"id": "events", "title": "Events & Private Functions", "required": False},
            {"id": "gallery", "title": "Photo Gallery", "required": False},
            {"id": "reviews", "title": "Guest Reviews & Awards", "required": False},
            {"id": "location", "title": "Location & Getting Here", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "blog", "title": "Travel Guide / Local Tips Blog", "required": False},
            {"id": "contact", "title": "Contact / Book Now", "required": True},
        ],
        "schema_type": "LodgingBusiness",
        "keywords_hint": "hotel, restaurant, travel, tourism, booking, accommodation",
    },
    "local_business": {
        "label": "Local Physical Business (Storefront / Contractor / Service)",
        "tone": "friendly, community-focused, reliable",
        "audience": "local residents and businesses seeking nearby services",
        "default_pages": [
            {"id": "home", "title": "Home", "required": True},
            {"id": "about", "title": "About Us", "required": True},
            {"id": "services_overview", "title": "Our Services", "required": True},
            {"id": "service_detail_1", "title": "Service: [Primary Offering]", "required": False},
            {"id": "service_detail_2", "title": "Service: [Secondary Offering]", "required": False},
            {"id": "service_areas", "title": "Service Areas / Locations Covered", "required": False},
            {"id": "gallery", "title": "Project Gallery / Our Work", "required": False},
            {"id": "reviews", "title": "Customer Reviews & Testimonials", "required": False},
            {"id": "faq", "title": "Frequently Asked Questions", "required": True},
            {"id": "blog", "title": "Tips & News Blog", "required": False},
            {"id": "contact", "title": "Contact / Get a Free Estimate", "required": True},
        ],
        "schema_type": "LocalBusiness",
        "keywords_hint": "local service, near me, free estimate, trusted, licensed",
    },
    "media_publishing": {
        "label": "News Media, Editorial Blog & Content Publishing",
        "tone": "informative, journalistic, engaging",
        "audience": "readers, content consumers, industry professionals",
        "default_pages": [
            {"id": "home", "title": "Home / Latest Articles", "required": True},
            {"id": "about", "title": "About / Editorial Mission", "required": True},
            {"id": "categories", "title": "Topics & Categories", "required": True},
            {"id": "category_1", "title": "Category: [Main Topic]", "required": False},
            {"id": "category_2", "title": "Category: [Secondary Topic]", "required": False},
            {"id": "authors", "title": "Our Writers / Contributors", "required": False},
            {"id": "subscribe", "title": "Subscribe / Newsletter", "required": False},
            {"id": "faq", "title": "FAQ", "required": True},
            {"id": "contact", "title": "Contact / Pitch a Story", "required": True},
            {"id": "advertise", "title": "Advertise With Us", "required": False},
        ],
        "schema_type": "NewsMediaOrganization",
        "keywords_hint": "news, articles, editorial, blog, industry analysis",
    },
}


# Map page IDs to template keys
PAGE_ID_TO_TEMPLATE = {
    "home": "home", "about": "about", "services_overview": "services_overview",
    "service_detail_1": "service_detail", "service_detail_2": "service_detail",
    "service_detail_3": "service_detail", "doctors_team": "about",
    "before_after": "case_studies", "testimonials": "testimonials",
    "faq": "faq", "blog": "blog", "contact": "contact", "pricing": "pricing",
    "case_studies": "case_studies", "integrations": "services_overview",
    "careers": "about", "portfolio": "case_studies", "process": "services_overview",
    "collections": "services_overview", "category_1": "service_detail",
    "category_2": "service_detail", "bestsellers": "services_overview",
    "new_arrivals": "services_overview", "reviews": "testimonials",
    "size_guide": "faq", "shipping_returns": "faq", "team": "about",
    "resources": "blog", "properties": "services_overview",
    "buy": "service_detail", "sell": "service_detail", "rent": "service_detail",
    "neighborhoods": "blog", "agents": "about",
    "courses_overview": "services_overview", "course_detail_1": "service_detail",
    "course_detail_2": "service_detail", "instructors": "about",
    "student_success": "case_studies", "rooms_menu": "services_overview",
    "dining": "service_detail", "events": "service_detail",
    "gallery": "case_studies", "location": "contact",
    "service_areas": "services_overview", "subscribe": "contact",
    "categories": "services_overview", "authors": "about",
    "advertise": "contact", "privacy_policy": "faq", "custom": "service_detail",
}


# ---------------------------------------------------------------------------
# Page Section Templates
# ---------------------------------------------------------------------------

PAGE_TEMPLATES = {
    "home": {
        "label": "Home Page",
        "sections": [
            {"id": "hero", "heading_level": 2, "title": "Hero - Primary Value Proposition",
             "guidance": "Opening hero with brand name, primary keyword, and definitive claim in 40-50 words.",
             "min_words": 40, "max_words": 80},
            {"id": "problem_pain", "heading_level": 2, "title": "The Problem We Solve",
             "guidance": "Primary pain point with empathetic language and a statistical data point.",
             "min_words": 60, "max_words": 120},
            {"id": "solution_value", "heading_level": 2, "title": "Our Solution & Core Value",
             "guidance": "How your product/service solves the problem. 3-5 bullet points of key benefits.",
             "min_words": 80, "max_words": 180},
            {"id": "capabilities", "heading_level": 2, "title": "Core Capabilities & Services",
             "guidance": "List 3-6 core services with H3 subsections and 1-2 sentence descriptions.",
             "min_words": 120, "max_words": 300, "subsections": True},
            {"id": "process_steps", "heading_level": 2, "title": "How It Works / Our Process",
             "guidance": "3-5 numbered steps as H3. Keep each to 2-3 sentences.",
             "min_words": 80, "max_words": 200, "subsections": True},
            {"id": "social_proof", "heading_level": 2, "title": "Trust & Social Proof",
             "guidance": "Client count, certifications, awards, and 1-2 testimonial quotes. E-E-A-T critical.",
             "min_words": 60, "max_words": 150},
            {"id": "faq_preview", "heading_level": 2, "title": "Common Questions",
             "guidance": "3-4 FAQ pairs as H3 with 40-60 word direct answers for PAA and SearchGPT.",
             "min_words": 120, "max_words": 300, "subsections": True},
            {"id": "cta_final", "heading_level": 2, "title": "Get Started / Take the Next Step",
             "guidance": "Conversion CTA with next step, what they receive, and reassurance.",
             "min_words": 40, "max_words": 100},
        ],
    },
    "about": {
        "label": "About Us Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Who We Are",
             "guidance": "Brand identity opening. AEO: first sentence answers 'Who is this company?'",
             "min_words": 60, "max_words": 140},
            {"id": "mission_vision", "heading_level": 2, "title": "Our Mission & Vision",
             "guidance": "Mission (what we do now) and vision (where we're heading). 2-3 sentences each.",
             "min_words": 60, "max_words": 120},
            {"id": "story_history", "heading_level": 2, "title": "Our Story",
             "guidance": "Founding narrative, key milestones, growth trajectory. 3-4 paragraphs.",
             "min_words": 100, "max_words": 250},
            {"id": "team_leadership", "heading_level": 2, "title": "Leadership & Expertise",
             "guidance": "2-4 key team members as H3. Name, title, credentials, background. E-E-A-T critical.",
             "min_words": 100, "max_words": 300, "subsections": True},
            {"id": "values", "heading_level": 2, "title": "Our Core Values",
             "guidance": "3-5 core values as H3 with brief explanations.",
             "min_words": 80, "max_words": 200, "subsections": True},
            {"id": "credentials", "heading_level": 2, "title": "Certifications & Awards",
             "guidance": "Certifications, accreditations, regulatory compliance. Bullet points.",
             "min_words": 40, "max_words": 120},
            {"id": "cta", "heading_level": 2, "title": "Work With Us",
             "guidance": "Closing CTA connecting About narrative to action.",
             "min_words": 30, "max_words": 80},
        ],
    },
    "services_overview": {
        "label": "Services Overview Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Our Services",
             "guidance": "Overview paragraph. AEO: first sentence states what services and for whom.",
             "min_words": 60, "max_words": 120},
            {"id": "service_grid", "heading_level": 2, "title": "Complete Service Portfolio",
             "guidance": "Each service as H3 with 2-3 sentence description. 4-8 services.",
             "min_words": 200, "max_words": 500, "subsections": True},
            {"id": "why_choose", "heading_level": 2, "title": "Why Choose Us",
             "guidance": "3-5 differentiators as bullet points or H3 subsections.",
             "min_words": 80, "max_words": 200},
            {"id": "process", "heading_level": 2, "title": "Our Service Delivery Process",
             "guidance": "3-5 steps as H3 with confidence-building descriptions.",
             "min_words": 80, "max_words": 200, "subsections": True},
            {"id": "faq", "heading_level": 2, "title": "Service FAQs",
             "guidance": "3-5 common service questions with direct 40-60 word answers.",
             "min_words": 120, "max_words": 300, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Ready to Get Started?",
             "guidance": "Service-oriented CTA with contact method and reassurance.",
             "min_words": 30, "max_words": 80},
        ],
    },
    "service_detail": {
        "label": "Service Detail Page",
        "sections": [
            {"id": "definition", "heading_level": 2, "title": "What Is This Service?",
             "guidance": "Clinical/technical definition. First sentence answers 'What is [service]?' in 40-50 words.",
             "min_words": 60, "max_words": 140},
            {"id": "who_for", "heading_level": 2, "title": "Who Is This For?",
             "guidance": "Ideal candidate criteria. 4-6 bullet points.",
             "min_words": 60, "max_words": 150},
            {"id": "procedure_breakdown", "heading_level": 2, "title": "How It Works",
             "guidance": "Step-by-step breakdown as H3 phases. Include duration and methods.",
             "min_words": 120, "max_words": 350, "subsections": True},
            {"id": "benefits", "heading_level": 2, "title": "Key Benefits & Expected Results",
             "guidance": "5-8 measurable benefits with timeframes and quantified outcomes.",
             "min_words": 80, "max_words": 200},
            {"id": "preparation", "heading_level": 2, "title": "Preparation & Requirements",
             "guidance": "Pre-engagement checklist. Prerequisites and documentation needed.",
             "min_words": 50, "max_words": 120},
            {"id": "pricing_guidance", "heading_level": 2, "title": "Investment & Pricing",
             "guidance": "Pricing framework or ranges. Payment options, financing.",
             "min_words": 40, "max_words": 120},
            {"id": "faq", "heading_level": 2, "title": "FAQs About This Service",
             "guidance": "5-8 specific questions with direct 40-60 word answers.",
             "min_words": 200, "max_words": 500, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Book Your Consultation",
             "guidance": "Service-specific CTA with next step and trust reassurance.",
             "min_words": 30, "max_words": 80},
        ],
    },
    "pricing": {
        "label": "Pricing & Plans Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Simple, Transparent Pricing",
             "guidance": "Pricing philosophy. AEO: first sentence states the model clearly.",
             "min_words": 40, "max_words": 100},
            {"id": "tiers", "heading_level": 2, "title": "Choose Your Plan",
             "guidance": "2-4 tiers as H3. Each: name, price, 5-8 feature bullets, best-for.",
             "min_words": 150, "max_words": 400, "subsections": True},
            {"id": "comparison", "heading_level": 2, "title": "Feature Comparison",
             "guidance": "Markdown table comparing 8-12 features across tiers.",
             "min_words": 40, "max_words": 100},
            {"id": "guarantee", "heading_level": 2, "title": "Our Guarantee",
             "guidance": "Satisfaction guarantee, refund policy, or trial period. 2-3 sentences.",
             "min_words": 30, "max_words": 80},
            {"id": "faq", "heading_level": 2, "title": "Pricing FAQs",
             "guidance": "4-6 pricing questions covering billing, cancellation, upgrades.",
             "min_words": 120, "max_words": 300, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Get Started Today",
             "guidance": "Conversion CTA with clear next step.",
             "min_words": 25, "max_words": 60},
        ],
    },
    "case_studies": {
        "label": "Case Studies / Portfolio Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Proven Results & Client Success",
             "guidance": "Opening with aggregate metrics. 'Over X projects, Y% improvement...'",
             "min_words": 40, "max_words": 100},
            {"id": "case_1", "heading_level": 2, "title": "Case Study: [Client/Project]",
             "guidance": "H3: Challenge, Approach, Results, Testimonial. Include specific metrics.",
             "min_words": 150, "max_words": 300, "subsections": True},
            {"id": "case_2", "heading_level": 2, "title": "Case Study: [Client/Project]",
             "guidance": "Same structure. Different vertical or service type.",
             "min_words": 150, "max_words": 300, "subsections": True},
            {"id": "metrics_summary", "heading_level": 2, "title": "Impact by the Numbers",
             "guidance": "3-5 key aggregate statistics. Bold numbers. AI-citable.",
             "min_words": 40, "max_words": 100},
            {"id": "cta", "heading_level": 2, "title": "Ready for Similar Results?",
             "guidance": "CTA connecting case success to prospective client goals.",
             "min_words": 25, "max_words": 60},
        ],
    },
    "faq": {
        "label": "FAQ Hub Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Your Questions, Answered",
             "guidance": "Brief intro. AEO: 'Expert answers to the most frequently asked questions.'",
             "min_words": 30, "max_words": 60},
            {"id": "general_faq", "heading_level": 2, "title": "General Questions",
             "guidance": "4-6 general questions as H3. Each answer: exactly 40-60 words.",
             "min_words": 160, "max_words": 400, "subsections": True},
            {"id": "service_faq", "heading_level": 2, "title": "Service & Process Questions",
             "guidance": "4-6 service-specific questions. Same format.",
             "min_words": 160, "max_words": 400, "subsections": True},
            {"id": "pricing_faq", "heading_level": 2, "title": "Pricing & Payment Questions",
             "guidance": "3-4 pricing/payment questions.",
             "min_words": 100, "max_words": 250, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Still Have Questions?",
             "guidance": "Short CTA to contact page.",
             "min_words": 20, "max_words": 50},
        ],
    },
    "contact": {
        "label": "Contact / Appointment Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Get in Touch",
             "guidance": "Action-oriented opening. State CTA, response time, contact methods.",
             "min_words": 40, "max_words": 100},
            {"id": "contact_details", "heading_level": 2, "title": "Contact Information",
             "guidance": "Phone, Email, Address, Business Hours. Consistent formatting.",
             "min_words": 40, "max_words": 100},
            {"id": "form_guidance", "heading_level": 2, "title": "Send Us a Message",
             "guidance": "Contact form introduction. List fields and privacy reassurance.",
             "min_words": 30, "max_words": 80},
            {"id": "preparation", "heading_level": 2, "title": "Before Your Visit / Appointment",
             "guidance": "Industry-specific preparation instructions. Checklist format.",
             "min_words": 40, "max_words": 120},
            {"id": "emergency", "heading_level": 2, "title": "Urgent / Emergency Contact",
             "guidance": "Emergency info if applicable. Skip if not relevant.",
             "min_words": 20, "max_words": 60},
        ],
    },
    "blog": {
        "label": "Blog / Articles Hub Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Expert Insights & Knowledge Hub",
             "guidance": "Position blog as trusted knowledge source. Editorial mission.",
             "min_words": 40, "max_words": 100},
            {"id": "featured_article", "heading_level": 2, "title": "Featured Article",
             "guidance": "Placeholder for featured article with title, excerpt, author, date.",
             "min_words": 60, "max_words": 120},
            {"id": "categories", "heading_level": 2, "title": "Browse by Topic",
             "guidance": "4-6 categories as H3 with 1-sentence descriptions.",
             "min_words": 60, "max_words": 150, "subsections": True},
            {"id": "newsletter_cta", "heading_level": 2, "title": "Subscribe to Our Newsletter",
             "guidance": "Newsletter CTA. Frequency, content type, privacy reassurance.",
             "min_words": 25, "max_words": 60},
        ],
    },
    "testimonials": {
        "label": "Testimonials & Reviews Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "What Our Clients Say",
             "guidance": "Trust intro. Include aggregate rating if available.",
             "min_words": 30, "max_words": 60},
            {"id": "testimonial_1", "heading_level": 2, "title": "Review: [Client]",
             "guidance": "Full quote (60-100 words), client info, service used, date.",
             "min_words": 60, "max_words": 130},
            {"id": "testimonial_2", "heading_level": 2, "title": "Review: [Client]",
             "guidance": "Different service or client profile.",
             "min_words": 60, "max_words": 130},
            {"id": "testimonial_3", "heading_level": 2, "title": "Review: [Client]",
             "guidance": "Third perspective.",
             "min_words": 60, "max_words": 130},
            {"id": "review_platforms", "heading_level": 2, "title": "Find Us on Review Platforms",
             "guidance": "2-3 external review platforms with links.",
             "min_words": 20, "max_words": 60},
            {"id": "cta", "heading_level": 2, "title": "Experience It Yourself",
             "guidance": "Short CTA connecting social proof to action.",
             "min_words": 20, "max_words": 50},
        ],
    },
}


# ---------------------------------------------------------------------------
# Language Templates
# ---------------------------------------------------------------------------

LANGUAGE_CONFIGS = {
    "en": {"label": "English", "dir": "ltr", "locale": "en-US", "schema_locale": "en",
           "connectors": {"and": "and", "or": "or", "learn_more": "Learn More",
                          "contact_us": "Contact Us", "get_started": "Get Started",
                          "book_now": "Book Now", "free_consultation": "Free Consultation"}},
    "fr": {"label": "Francais", "dir": "ltr", "locale": "fr-FR", "schema_locale": "fr",
           "connectors": {"and": "et", "or": "ou", "learn_more": "En Savoir Plus",
                          "contact_us": "Contactez-Nous", "get_started": "Commencer",
                          "book_now": "Reserver", "free_consultation": "Consultation Gratuite"}},
    "ar": {"label": "Arabic", "dir": "rtl", "locale": "ar-SA", "schema_locale": "ar",
           "connectors": {"and": "\u0648", "or": "\u0623\u0648",
                          "learn_more": "\u0627\u0639\u0631\u0641 \u0627\u0644\u0645\u0632\u064a\u062f",
                          "contact_us": "\u0627\u062a\u0635\u0644 \u0628\u0646\u0627",
                          "get_started": "\u0627\u0628\u062f\u0623 \u0627\u0644\u0622\u0646",
                          "book_now": "\u0627\u062d\u062c\u0632 \u0627\u0644\u0622\u0646",
                          "free_consultation": "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0645\u062c\u0627\u0646\u064a\u0629"}},
}


# ---------------------------------------------------------------------------
# Content Synthesizer Engine
# ---------------------------------------------------------------------------

class ContentSynthesizer:
    """Generates structured, SEO/GEO-optimized page content for new websites."""

    def __init__(self, config: dict):
        self.brand = config.get("brand_name", "Your Brand").strip()
        self.industry_key = config.get("industry", "technology_software")
        self.industry = INDUSTRY_PRESETS.get(self.industry_key, INDUSTRY_PRESETS["technology_software"])
        self.description = config.get("description", self.industry.get("keywords_hint", ""))
        self.language = config.get("language", "en")
        self.lang_config = LANGUAGE_CONFIGS.get(self.language, LANGUAGE_CONFIGS["en"])
        self.selected_pages = config.get("pages", [])
        self.custom_pages = config.get("custom_pages", [])
        self.domain = config.get("domain", "https://example.com").rstrip("/")

    def generate_all(self) -> dict:
        """Generate content for all selected pages."""
        results = {
            "brand": self.brand, "industry": self.industry["label"],
            "industry_key": self.industry_key, "language": self.language,
            "language_label": self.lang_config["label"], "domain": self.domain,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pages": [], "llms_txt": "", "sitemap_urls": [],
        }
        for page_id in self.selected_pages:
            page_data = self._generate_page(page_id)
            if page_data:
                results["pages"].append(page_data)
                results["sitemap_urls"].append(page_data["url"])
        for cp in self.custom_pages:
            page_data = self._generate_page("custom", custom_title=cp.get("title", "Custom Page"))
            if page_data:
                results["pages"].append(page_data)
                results["sitemap_urls"].append(page_data["url"])
        results["llms_txt"] = self._generate_llms_txt(results)
        return results

    def _generate_page(self, page_id: str, custom_title: str = None) -> Optional[dict]:
        """Generate structured content for a single page."""
        page_title = custom_title
        if not page_title:
            for p in self.industry.get("default_pages", []):
                if p["id"] == page_id:
                    page_title = p["title"]
                    break
        if not page_title:
            page_title = page_id.replace("_", " ").title()
        template_key = PAGE_ID_TO_TEMPLATE.get(page_id, "service_detail")
        template = PAGE_TEMPLATES.get(template_key, PAGE_TEMPLATES["service_detail"])
        slug = self._make_slug(page_title)
        url = self.domain if page_id == "home" else f"{self.domain}/{slug}"
        meta_title = self._generate_meta_title(page_title)
        meta_desc = self._generate_meta_desc(page_title)
        sections = []
        for sec_template in template["sections"]:
            section = self._generate_section(page_title, sec_template)
            sections.append(section)
        schema_jsonld = self._generate_schema(page_id, page_title, url, meta_desc)
        total_words = sum(s["word_count"] for s in sections)
        return {
            "id": page_id, "title": page_title, "template": template_key,
            "url": url, "slug": slug,
            "meta_title": meta_title, "meta_title_length": len(meta_title),
            "meta_description": meta_desc, "meta_description_length": len(meta_desc),
            "h1": page_title, "sections": sections, "total_word_count": total_words,
            "schema_jsonld": schema_jsonld, "language": self.language,
            "direction": self.lang_config["dir"], "canonical_url": url,
            "og_title": meta_title, "og_description": meta_desc,
        }

    def _generate_meta_title(self, page_title: str) -> str:
        """Generate SEO-optimized title tag (target: 50-60 chars)."""
        industry_short = self.industry["label"].split(",")[0].strip()
        if page_title.lower() in ("home", "homepage"):
            raw = f"{self.brand} - Premier {industry_short} & Services"
            if len(raw) < 50:
                raw = f"{self.brand} - Official Website | Leading {industry_short}"
        else:
            raw = f"{page_title} - {self.brand} | {industry_short}"

        if len(raw) > 60:
            raw = f"{page_title} | {self.brand} - {industry_short}"
        if len(raw) > 60:
            raw = f"{page_title} - {self.brand}"
        if len(raw) > 60:
            raw = f"{page_title} | {self.brand}"
        if len(raw) > 60:
            max_len = 60 - len(f" | {self.brand}")
            raw = f"{page_title[:max_len].rstrip()} | {self.brand}"

        if len(raw) < 50:
            suffixes = [
                f" | Official Site",
                f" | Expert Solutions",
                f" | Professional Services",
                f" | Trusted Care",
                f" | Solutions",
            ]
            for sfx in suffixes:
                if 50 <= len(raw + sfx) <= 60:
                    raw = raw + sfx
                    break
            else:
                for sfx in suffixes:
                    if len(raw + sfx) <= 60:
                        raw = raw + sfx
                        if len(raw) >= 50:
                            break
        return raw

    def _generate_meta_desc(self, page_title: str) -> str:
        """Generate SEO-optimized meta description (140-160 chars)."""
        industry_short = self.industry["label"].split(",")[0].strip()
        base = f"Discover {page_title.lower()} at {self.brand}. "
        base += f"We provide expert {industry_short.lower()} solutions. "
        base += f"Contact us today for a free consultation."
        if len(base) > 160:
            base = base[:157].rstrip() + "..."
        elif len(base) < 140:
            base += f" Trusted by clients worldwide."
            if len(base) > 160:
                base = base[:157].rstrip() + "..."
        return base

    def _generate_section(self, page_title: str, sec_template: dict) -> dict:
        """Generate content for a single page section."""
        heading = sec_template["title"]
        heading = heading.replace("{brand}", self.brand)
        heading = heading.replace("{service_name}", page_title)
        heading = heading.replace("{service_category}", self.industry["label"].split(",")[0].strip())
        heading = heading.replace("{blog_topic}", self.industry["label"].split(",")[0].strip())
        heading = heading.replace("{cta_action}", self.lang_config["connectors"]["free_consultation"])
        has_subsections = sec_template.get("subsections", False)
        industry_short = self.industry["label"].split(",")[0].strip()
        audience = self.industry.get("audience", "clients")
        content_lines = []
        aeo_hook = self._build_aeo_hook(sec_template["id"], page_title, industry_short, audience)
        content_lines.append(aeo_hook)
        content_lines.append("")
        if has_subsections:
            subs = self._get_subsection_topics(sec_template["id"], page_title, industry_short)
            for sub in subs:
                content_lines.append(f"### {sub['title']}")
                content_lines.append("")
                content_lines.append(sub["content"])
                content_lines.append("")
        else:
            body = self._get_paragraph_content(sec_template["id"], page_title, industry_short, audience)
            content_lines.append(body)
        content_text = "\n".join(content_lines)
        word_count = len(content_text.split())
        return {
            "id": sec_template["id"], "heading": heading,
            "heading_level": sec_template["heading_level"],
            "content": content_text, "guidance": sec_template["guidance"],
            "word_count": word_count, "has_subsections": has_subsections,
        }

    def _build_aeo_hook(self, sec_id: str, page_title: str, industry: str, audience: str) -> str:
        """Build a 40-50 word Answer Engine Optimization hook."""
        brand = self.brand
        hooks = {
            "hero": f"{brand} is a leading {industry.lower()} provider delivering high-performance solutions to {audience}. Our proven methodology combines deep industry expertise with cutting-edge technology to help clients achieve measurable results and sustainable growth across all their operations.",
            "problem_pain": f"Many {audience} face significant challenges when navigating the complexities of {industry.lower()}. Without the right partner and methodology, organizations risk wasting resources, falling behind competitors, and missing critical opportunities for growth and operational efficiency.",
            "solution_value": f"{brand} addresses these challenges with a comprehensive approach to {industry.lower()} that prioritizes measurable outcomes. Our solutions are designed to deliver immediate value while building the foundation for long-term success and competitive advantage.",
            "capabilities": f"{brand} offers a complete portfolio of {industry.lower()} capabilities built on years of proven expertise. Each service is tailored to meet the specific needs of {audience}, ensuring optimal results and maximum return on investment.",
            "process_steps": f"Our streamlined process ensures a smooth, efficient experience from initial consultation through final delivery. Each step is designed to maximize transparency, minimize disruption, and deliver exceptional results on time and within budget.",
            "social_proof": f"Trusted by hundreds of satisfied clients across multiple industries, {brand} has established a proven track record of delivering exceptional results. Our client retention rate and positive reviews reflect our unwavering commitment to quality.",
            "faq_preview": f"We understand that choosing the right {industry.lower()} partner is an important decision. Here are expert answers to the most commonly asked questions from {audience} to help you make an informed choice.",
            "cta_final": f"Take the next step toward achieving your goals. Contact {brand} today for a free initial consultation and discover how our {industry.lower()} expertise can deliver the results you need.",
            "intro": f"{brand} is a dedicated {industry.lower()} organization committed to delivering excellence. Founded with a clear mission to serve {audience}, we have grown into a trusted name recognized for quality and measurable outcomes.",
            "mission_vision": f"Our mission is to empower {audience} through innovative {industry.lower()} solutions that drive meaningful impact. Our vision is to become the most trusted provider in our industry, setting new standards for excellence.",
            "story_history": f"The story of {brand} began with a simple yet powerful idea: to make professional {industry.lower()} solutions accessible, effective, and results-driven for every client we serve.",
            "team_leadership": f"Our leadership team brings together decades of combined expertise in {industry.lower()}, ensuring that every client benefits from the highest level of knowledge, skill, and dedicated professional service at {brand}.",
            "values": f"At {brand}, our core values define everything we do. They guide our decisions, shape our culture, and ensure that every interaction with our clients reflects our commitment to excellence and integrity.",
            "credentials": f"{brand} holds multiple industry certifications and accreditations that demonstrate our commitment to maintaining the highest professional standards and ongoing investment in quality and training.",
            "definition": f"{page_title} is a specialized {industry.lower()} solution offered by {brand} that delivers targeted results for {audience}. This service combines proven methodologies with expert execution to achieve measurable improvements.",
            "who_for": f"This service is designed for {audience} who require professional {industry.lower()} support to achieve their goals. It is particularly valuable for those facing specific challenges that demand specialized expertise.",
            "procedure_breakdown": f"Our {page_title.lower()} process follows a proven methodology that ensures consistent, high-quality results. Each phase is carefully planned and executed by experienced professionals using industry best practices.",
            "benefits": f"Clients who choose {brand} for {page_title.lower()} consistently report significant improvements. Key benefits include measurable results, expert guidance, time savings, and a transparent process from start to finish.",
            "preparation": f"To ensure the best possible experience and results, we recommend preparing the following items before your {page_title.lower()} engagement. Proper preparation helps maximize efficiency and ensures optimal outcomes.",
            "pricing_guidance": f"{brand} offers competitive, transparent pricing for {page_title.lower()} services. We believe in clear communication about costs, with no hidden fees, and flexible payment options to accommodate different budgets.",
            "service_grid": f"{brand} provides a comprehensive range of {industry.lower()} services designed to meet the diverse needs of {audience}. Each service is delivered by specialized professionals backed by our commitment to results.",
            "why_choose": f"Clients choose {brand} because of our proven track record, specialized expertise, and unwavering commitment to client satisfaction. Our approach combines best practices with personalized service delivery.",
            "comparison": f"Compare our service tiers side by side to find the plan that best fits your needs. Each tier delivers maximum value with transparent pricing and clear feature inclusion.",
            "guarantee": f"{brand} stands behind the quality of our work with a comprehensive satisfaction guarantee. We are committed to delivering results that meet or exceed your expectations.",
            "tiers": f"Choose the plan that best fits your needs. {brand} offers flexible pricing tiers designed for businesses of all sizes, from startups to enterprise, with scalable features and dedicated support.",
            "general_faq": f"Below are answers to the questions we hear most frequently from {audience}. Each answer is provided by our team of experts to help you understand our services and what to expect.",
            "service_faq": f"These answers cover common questions about our services and delivery process. Our goal is to ensure complete transparency so you can make confident, informed decisions.",
            "pricing_faq": f"We believe in transparent pricing with no surprises. Below are answers to common questions about our pricing structure, payment options, and available discounts or promotions.",
            "contact_details": f"Reaching {brand} is easy. Our team is available during business hours to answer questions, provide quotes, and schedule consultations. We respond to all inquiries within one business day.",
            "form_guidance": f"Use our secure contact form to send us a message directly. Please provide detail about your needs so our team can prepare a tailored response and schedule your consultation.",
            "emergency": f"For urgent matters outside regular business hours, {brand} provides dedicated emergency contact options. Your safety and satisfaction are our top priorities at all times.",
            "featured_article": f"Explore our latest featured article covering important trends and expert insights in {industry.lower()}. Our editorial team produces thoroughly researched content to keep {audience} informed.",
            "categories": f"Browse our knowledge hub by topic to find the expert insights most relevant to your needs. Our content covers the full spectrum of {industry.lower()} topics from guides to strategies.",
            "newsletter_cta": f"Stay informed with the latest {industry.lower()} insights delivered to your inbox. Subscribe to the {brand} newsletter for expert analysis, practical tips, and exclusive updates.",
            "testimonial_1": f"Our clients consistently express satisfaction with the quality, professionalism, and results delivered by {brand}. Here is what one valued client had to say about their experience.",
            "testimonial_2": f"Another perspective from a client who experienced the {brand} difference firsthand. Their feedback highlights the consistent quality and personalized attention that defines our approach.",
            "testimonial_3": f"This testimonial from a long-term client demonstrates the lasting value and ongoing partnership that {brand} builds with every engagement. Sustained results matter.",
            "review_platforms": f"You can find verified reviews of {brand} on multiple independent platforms. We encourage prospective clients to read these unfiltered reviews to gain confidence.",
            "case_1": f"In this case study, we demonstrate how {brand} helped a client overcome significant {industry.lower()} challenges and achieve measurable results that exceeded their initial expectations.",
            "case_2": f"This second case study showcases a different client scenario where {brand} applied specialized methodology to deliver transformative results in a compressed timeline.",
            "metrics_summary": f"The numbers speak for themselves. Across all engagements, {brand} consistently delivers measurable improvements demonstrating the tangible value of our services.",
            "cta": f"Ready to get started? Contact {brand} today and take the first step toward achieving your goals. We look forward to helping you succeed.",
        }
        return hooks.get(sec_id, f"{brand} provides expert {industry.lower()} solutions for {audience}. Our comprehensive approach ensures consistent quality and measurable results across every engagement.")

    def _get_subsection_topics(self, sec_id: str, page_title: str, industry: str) -> list:
        """Generate subsection topics based on section type."""
        brand = self.brand
        il = industry.lower()
        subs = {
            "capabilities": [
                {"title": "Strategic Consultation & Assessment", "content": f"Every engagement begins with a thorough assessment of your current situation and objectives. Our {il} consultants analyze your needs, identify opportunities, and develop a customized strategy that aligns with your goals and budget constraints."},
                {"title": "Custom Solution Design & Implementation", "content": f"{brand} designs and implements tailored solutions that address your specific requirements. Our team leverages proven frameworks and industry best practices to ensure efficient delivery and optimal results."},
                {"title": "Quality Assurance & Testing", "content": f"Rigorous quality assurance is embedded in every phase of our process. We conduct comprehensive testing, validation, and peer review to ensure that all deliverables meet our exacting standards and your expectations."},
                {"title": "Training & Knowledge Transfer", "content": f"We empower your team with the knowledge and skills needed to maximize the value of our solutions. Training programs are customized to your team's experience level with documentation and workshops."},
                {"title": "Ongoing Support & Optimization", "content": f"Our commitment extends beyond delivery. {brand} provides ongoing support, monitoring, and optimization services to ensure sustained performance and continuous improvement over time."},
            ],
            "process_steps": [
                {"title": "Step 1: Discovery & Consultation", "content": f"We begin with a complimentary discovery session to understand your goals, challenges, and expectations. This foundational step ensures every subsequent action is aligned with your specific needs."},
                {"title": "Step 2: Strategy & Planning", "content": f"Based on our discovery findings, our experts develop a detailed action plan with clear milestones, deliverables, and timelines. You receive full transparency into our proposed approach."},
                {"title": "Step 3: Execution & Delivery", "content": f"Our experienced team executes the agreed plan with precision and attention to detail. Regular progress updates keep you informed, and your feedback is incorporated throughout the process."},
                {"title": "Step 4: Review & Optimization", "content": f"Upon completion, we conduct a thorough review of all deliverables against quality benchmarks and your objectives. We make any necessary refinements to ensure complete satisfaction."},
            ],
            "faq_preview": [
                {"title": f"What makes {brand} different from other providers?", "content": f"{brand} differentiates itself through deep specialized expertise, personalized service delivery, and a proven track record of measurable results. Our client-first approach ensures every engagement is tailored to your unique needs."},
                {"title": "How long does it typically take to see results?", "content": f"Most clients begin seeing meaningful results within the first 30-60 days, depending on scope and complexity. We set clear expectations during our initial consultation and provide regular progress updates."},
                {"title": "Do you offer a free initial consultation?", "content": f"Yes, {brand} offers a complimentary initial consultation at no cost or obligation. We assess your needs, answer your questions, and outline how we can help you achieve your objectives."},
                {"title": "What is your pricing structure?", "content": f"Our pricing is transparent and competitive, tailored to the scope of each project. We offer flexible payment options and provide detailed proposals so you understand exactly what you are investing in."},
            ],
            "service_grid": [
                {"title": f"Core {industry} Service", "content": f"Our flagship offering provides comprehensive coverage of your most critical needs. Delivered by senior specialists with extensive experience, this service forms the foundation of most client engagements."},
                {"title": "Advanced Solutions & Specializations", "content": f"For clients with complex requirements, {brand} offers advanced solutions including custom implementations, integration services, and performance optimization packages."},
                {"title": "Consulting & Strategic Advisory", "content": f"Our strategic consulting helps organizations make informed decisions about their {il} investments. We provide objective analysis, market insights, and actionable recommendations."},
                {"title": "Support & Maintenance Programs", "content": f"Ensure continuous performance with dedicated support and maintenance programs. Available in tiered packages with priority response, proactive monitoring, and regular reviews."},
            ],
            "team_leadership": [
                {"title": "[Founder / CEO Name]", "content": f"With over 15 years of experience in {il}, our founder brings visionary leadership and deep expertise to {brand}. Holding advanced certifications, they have led the organization to its position as a trusted leader."},
                {"title": "[Director of Operations]", "content": f"Our Director ensures seamless service delivery across all engagements. With a background in project management and {il} best practices, they maintain the high standards {brand} is known for."},
                {"title": "[Senior Specialist]", "content": f"Our senior specialist brings hands-on expertise and a client-centered approach to every project. Certified in multiple areas of {il}, they serve as primary contact for complex engagements."},
            ],
            "values": [
                {"title": "Excellence in Every Detail", "content": f"We pursue excellence as a standard applied to every deliverable, interaction, and decision at {brand}. Our commitment to quality is reflected in our results and professional reputation."},
                {"title": "Integrity & Transparency", "content": f"Honest communication and transparent practices form the foundation of every client relationship. We provide clear expectations, honest assessments, and straightforward pricing."},
                {"title": "Client-Centered Innovation", "content": f"Every innovation at {brand} is driven by client needs and market realities. We continuously invest in research, training, and new methodologies for effective approaches."},
                {"title": "Measurable Impact", "content": f"We believe in accountability and measurable results. Every project includes clear success metrics, and we track and report on outcomes to demonstrate tangible value."},
            ],
            "tiers": [
                {"title": "Starter Plan", "content": f"Perfect for small businesses getting started. Includes core features, email support, and essential tools. Ideal for those who need reliable {il} foundations without complexity."},
                {"title": "Professional Plan", "content": f"Our most popular option for growing businesses. Includes everything in Starter plus premium tools, analytics, priority support, and dedicated account management."},
                {"title": "Enterprise Plan", "content": f"For organizations with complex needs. Includes unlimited access, custom integrations, dedicated team, SLA guarantees, and white-glove onboarding. Contact us for pricing."},
            ],
            "general_faq": [
                {"title": f"What services does {brand} offer?", "content": f"{brand} offers a comprehensive suite of {il} services including consultation, implementation, optimization, and ongoing support designed to address the full spectrum of client needs."},
                {"title": f"How do I get started with {brand}?", "content": f"Contact us through our website form, email, or phone to schedule a free initial consultation. We will assess your needs, answer questions, and outline a recommended approach."},
                {"title": "What areas or regions do you serve?", "content": f"{brand} serves clients across multiple regions with both local and remote engagements. Our flexible delivery model allows consistent, high-quality service regardless of location."},
                {"title": "Do you offer guarantees on your work?", "content": f"Yes, {brand} stands behind the quality of all our work with a comprehensive satisfaction guarantee. We are committed to meeting or exceeding your expectations."},
            ],
            "service_faq": [
                {"title": "How long does a typical project take?", "content": f"Timelines vary by scope and complexity. Most standard engagements complete within 4-12 weeks. We provide a detailed timeline with clear milestones during initial consultation."},
                {"title": "Can I customize the service to my needs?", "content": f"Absolutely. Every service at {brand} is fully customizable. Our team works closely with you to design a tailored solution that addresses your specific challenges, goals, and budget."},
                {"title": "What happens after project completion?", "content": f"We provide thorough documentation, training, and a transition plan. We also offer ongoing support and maintenance packages to ensure sustained performance and long-term value."},
                {"title": "Who will work on my project?", "content": f"Your project will be handled by a dedicated team of experienced {il} professionals led by a senior specialist. You will have a single point of contact throughout."},
            ],
            "pricing_faq": [
                {"title": "How is pricing determined?", "content": f"Pricing is based on scope, complexity, and duration. We provide detailed proposals with transparent line-item pricing so you understand exactly what you are investing in. No hidden fees."},
                {"title": "Do you offer payment plans?", "content": f"Yes, {brand} offers flexible payment options including monthly installments, milestone-based payments, and custom arrangements for larger projects to fit your budget."},
                {"title": "Is there a minimum contract?", "content": f"Many services are available on a project basis with no long-term commitment. For ongoing services, we offer monthly, quarterly, and annual options with flexibility to adjust."},
            ],
            "categories": [
                {"title": f"{industry} Fundamentals & Guides", "content": f"Comprehensive introductory articles and guides covering core concepts, terminology, and best practices of {il}. Ideal for newcomers and those strengthening foundational knowledge."},
                {"title": "Industry Trends & Analysis", "content": f"Expert analysis of current market trends, regulatory changes, and emerging opportunities in {il}. Stay ahead with data-driven insights from our editorial team."},
                {"title": "Case Studies & Success Stories", "content": f"In-depth explorations of real client engagements showcasing challenges, solutions, and measurable results. Learn from practical examples of excellence."},
                {"title": "Tips, Tools & Resources", "content": f"Actionable tips, recommended tools, and curated resources to help you make better decisions and achieve better outcomes in {il}."},
            ],
            "case_1": [
                {"title": "The Challenge", "content": f"The client came to {brand} facing significant operational challenges limiting their growth and competitive position. Existing approaches produced inconsistent results."},
                {"title": "Our Approach", "content": f"{brand} conducted a thorough assessment and developed a customized strategy addressing root causes. We implemented a phased approach with clear milestones and regular check-ins."},
                {"title": "The Results", "content": f"Within 90 days, the client achieved a 45% improvement in key metrics. Operational costs reduced by 30%, and satisfaction scores increased from 3.2 to 4.7 out of 5."},
                {"title": "Client Feedback", "content": f"\"Working with {brand} transformed our operations. Their expertise and commitment exceeded our expectations. We now consider them an essential strategic partner.\" - [Client Name]"},
            ],
            "case_2": [
                {"title": "The Challenge", "content": f"A mid-size organization approached {brand} with a complex project requiring rapid turnaround and specialized expertise that previous providers could not deliver."},
                {"title": "Our Approach", "content": f"We assembled a dedicated cross-functional team and implemented an accelerated delivery framework, combining deep {il} expertise with agile project management."},
                {"title": "The Results", "content": f"Project delivered two weeks ahead of schedule and 15% under budget. Key metrics showed a 60% improvement over the client's previous baseline, sustained over time."},
            ],
            "procedure_breakdown": [
                {"title": "Phase 1: Initial Assessment", "content": f"The process begins with comprehensive evaluation of your current situation, goals, and requirements. Our specialists gather detailed information to ensure perfectly aligned solutions."},
                {"title": "Phase 2: Custom Plan Development", "content": f"Based on assessment findings, we develop a detailed personalized plan outlining recommended approach, timeline, milestones, and anticipated outcomes."},
                {"title": "Phase 3: Expert Implementation", "content": f"Our experienced team executes the approved plan with precision and care. We maintain clear communication with regular progress updates and prompt adjustments."},
                {"title": "Phase 4: Quality Review & Follow-Up", "content": f"After implementation, we conduct thorough quality review ensuring all objectives are met. Follow-up sessions monitor progress and optimize for long-term success."},
            ],
        }
        return subs.get(sec_id, subs.get("capabilities", [])[:3])

    def _get_paragraph_content(self, sec_id: str, page_title: str, industry: str, audience: str) -> str:
        """Generate paragraph content for non-subsection sections."""
        brand = self.brand
        il = industry.lower()
        contents = {
            "problem_pain": f"In today's competitive {il} landscape, {audience} face mounting pressure to deliver better results with limited resources. Studies indicate that over 60% of organizations struggle with inefficient processes, fragmented solutions, and a lack of specialized expertise. These challenges lead to wasted budgets, missed opportunities, and declining satisfaction among stakeholders.",
            "solution_value": f"{brand} solves these challenges with a proven, comprehensive approach to {il} that delivers measurable results from day one.\n\nKey advantages:\n\n- **Proven methodology** backed by data and real-world results\n- **Dedicated specialists** with deep {il} expertise\n- **Transparent process** with clear milestones and regular reporting\n- **Measurable outcomes** with defined KPIs and success metrics\n- **Ongoing support** to ensure sustained performance",
            "social_proof": f"**Trusted by 500+ clients** across diverse industries, {brand} has established a reputation for excellence.\n\n- **4.9/5 average satisfaction rating** across all engagements\n- **95% client retention rate** demonstrating lasting relationships\n- **12+ years of continuous operation** in {il}\n- Multiple industry certifications and professional accreditations\n\n> \"The team at {brand} delivered exceptional results that exceeded our expectations.\" - Verified Client",
            "credentials": f"Our commitment to excellence is validated by recognized certifications:\n\n- ISO 9001 Quality Management System certified\n- Industry-specific professional licenses and regulatory compliance\n- Member of relevant professional associations\n- Regular continuing education and professional development\n- Multiple excellence awards from industry organizations",
            "contact_details": f"**Phone:** +1 (555) 000-0000\n**Email:** contact@{brand.lower().replace(' ', '')}.com\n**Address:** [Street Address], [City], [Country] [Postal Code]\n\n**Business Hours:**\n- Monday - Friday: 9:00 AM - 6:00 PM\n- Saturday: 10:00 AM - 2:00 PM\n- Sunday: Closed\n\n*We respond to all inquiries within one business day.*",
            "form_guidance": f"Fill out the form below and our team will contact you within 24 hours. Please include detail about your needs for a tailored response.\n\n**Required:** Full Name, Email, Phone\n**Optional:** Company, Subject, Message\n\n*Your information is confidential and never shared with third parties.*",
            "emergency": f"For urgent situations:\n\n**Emergency Line:** +1 (555) 000-0001 (Available 24/7)\n**Email:** urgent@{brand.lower().replace(' ', '')}.com\n\n*Emergency response time: within 1 hour.*",
            "preparation": f"To ensure the best experience, please prepare:\n\n- Relevant documentation and records\n- A list of questions or topics to discuss\n- Previous reports or assessments from other providers\n- Your goals and expected outcomes\n- Budget range and preferred timeline",
            "pricing_guidance": f"Our pricing reflects the value and expertise we deliver:\n\n- **Consultation:** Complimentary initial assessment\n- **Standard projects:** Starting from $X,XXX (varies by scope)\n- **Ongoing programs:** Flexible monthly, quarterly, or annual options\n- **Custom enterprise:** Tailored pricing for complex engagements\n\nPayment options include bank transfer, credit card, and installment plans.",
            "benefits": f"Clients who partner with {brand} consistently report measurable improvements:\n\n- **35% average reduction** in operational overhead\n- **Measurable gains** within the first 60 days\n- **Expert guidance** from senior specialists throughout\n- **40% time savings** through streamlined processes\n- **Cost optimization** with better resource allocation\n- **Sustainable results** that compound over time\n- **Peace of mind** with professional accountability",
            "who_for": f"This service is ideal for:\n\n- {audience.capitalize()} looking for specialized {il} expertise\n- Organizations facing challenges with their current approach\n- Businesses preparing for growth or new markets\n- Teams needing expert support for specific objectives\n- Decision-makers seeking a trusted long-term partner\n- First-time clients looking for professional guidance",
            "intro": f"{brand} is committed to providing the highest standard of {il} services to {audience}. Our approach combines deep expertise, innovative methodologies, and genuine dedication to client success. Every engagement is tailored to your specific goals.",
            "review_platforms": f"Find verified reviews of {brand} on independent platforms:\n\n- **Google Business Profile** - [View Reviews]\n- **Trustpilot** - [View Reviews]\n- **Industry-Specific Platform** - [View Reviews]\n\n*We encourage honest feedback from all clients.*",
            "newsletter_cta": f"Subscribe to the {brand} newsletter for expert {il} insights delivered monthly:\n\n- Latest industry trends and analysis\n- Practical tips and actionable guides\n- Exclusive offers and early access\n\n*Unsubscribe at any time. We respect your privacy.*",
            "featured_article": f"**[Featured: Key Trends in {industry} for 2025]**\n\nAn in-depth analysis of the most important developments shaping {il} this year. From emerging technologies to changing expectations, this covers what {audience} need to know.\n\n*By [Author Name] | Published [Date] | 8 min read*",
            "comparison": f"| Feature | Starter | Professional | Enterprise |\n|---|---|---|---|\n| Core Features | Yes | Yes | Yes |\n| Priority Support | - | Yes | Yes |\n| Advanced Analytics | - | Yes | Yes |\n| Custom Integrations | - | - | Yes |\n| Dedicated Manager | - | - | Yes |\n| SLA Guarantee | - | - | Yes |\n| Training | Basic | Advanced | White-Glove |\n| Reports | Standard | Detailed | Executive |",
            "guarantee": f"{brand} is confident in our quality. If you are not fully satisfied within the first 30 days, we will work with you at no additional cost until your objectives are met. Our reputation is built on client satisfaction.",
            "metrics_summary": f"Our impact across all engagements:\n\n- **500+** successful projects completed\n- **45%** average improvement in key client metrics\n- **95%** client retention and repeat engagement rate\n- **4.9/5** average satisfaction rating\n- **30%** average cost reduction achieved",
            "cta_final": f"Ready to get started? Contact {brand} today for a complimentary consultation. Let us show you how our {il} expertise can help you achieve measurable results.\n\nCall us at +1 (555) 000-0000 or fill out our contact form. No obligation, no pressure - just expert guidance tailored to your needs.",
            "cta": f"Contact {brand} today and take the first step toward achieving your goals. We look forward to helping you succeed.",
            "testimonial_1": f"> \"Working with {brand} was a transformative experience. Their team demonstrated exceptional expertise and genuine commitment to our success. The results exceeded every expectation we had, and the process was seamless from start to finish.\"\n\n**- [Client Name], [Title], [Company]**\n*Service: [Service Used] | [Date]*",
            "testimonial_2": f"> \"{brand} delivered exactly what they promised - and more. Their transparent communication, deep knowledge, and proactive approach made all the difference. We saw measurable improvements within weeks.\"\n\n**- [Client Name], [Title], [Company]**\n*Service: [Service Used] | [Date]*",
            "testimonial_3": f"> \"After trying several providers, we finally found {brand}. The level of professionalism, attention to detail, and genuine care for our outcomes sets them apart. We are proud long-term partners.\"\n\n**- [Client Name], [Title], [Company]**\n*Service: [Service Used] | [Date]*",
        }
        return contents.get(sec_id, f"{brand} delivers professional {il} services tailored to {audience}. Our comprehensive approach ensures consistent quality and measurable results. Contact us today to learn how we can help.")

    def _generate_schema(self, page_id: str, page_title: str, url: str, description: str) -> dict:
        """Generate Schema.org JSON-LD for the page."""
        schema_type = self.industry.get("schema_type", "Organization")
        base = {
            "@context": "https://schema.org", "@type": "WebPage",
            "name": page_title, "description": description, "url": url,
            "inLanguage": self.lang_config["locale"],
            "isPartOf": {"@type": "WebSite", "name": self.brand, "url": self.domain},
            "publisher": {
                "@type": schema_type if schema_type != "SoftwareApplication" else "Organization",
                "name": self.brand, "url": self.domain,
            }
        }
        if "faq" in page_id:
            base["@type"] = ["WebPage", "FAQPage"]
        return base

    def _generate_llms_txt(self, results: dict) -> str:
        """Generate llms.txt content for AI crawlers."""
        lines = [f"# {self.brand}", "", f"> {self.description}", "", "## Pages", ""]
        for page in results["pages"]:
            lines.append(f"- [{page['title']}]({page['url']}): {page['meta_description'][:100]}")
        lines.extend(["", "## Contact", "", f"- Website: {self.domain}",
                       f"- Email: contact@{self.brand.lower().replace(' ', '')}.com"])
        return "\n".join(lines)

    def _make_slug(self, title: str) -> str:
        """Generate a clean URL slug."""
        slug = title.lower()
        slug = re.sub(r'\[.*?\]', '', slug)
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug or "page"


# ---------------------------------------------------------------------------
# Export Functions
# ---------------------------------------------------------------------------

def export_content(results: dict, output_dir: str) -> dict:
    """Export generated content to a structured folder."""
    os.makedirs(output_dir, exist_ok=True)
    exported_files = []

    # 1. Individual page Markdown files
    pages_dir = os.path.join(output_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)
    for page in results["pages"]:
        md = _render_page_markdown(page)
        fp = os.path.join(pages_dir, f"{page['slug']}.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(md)
        exported_files.append(fp)

    # 2. Individual page HTML files
    html_dir = os.path.join(output_dir, "html")
    os.makedirs(html_dir, exist_ok=True)
    for page in results["pages"]:
        html = _render_page_html(page)
        fp = os.path.join(html_dir, f"{page['slug']}.html")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(html)
        exported_files.append(fp)

    # 3. JSON data
    json_dir = os.path.join(output_dir, "json")
    os.makedirs(json_dir, exist_ok=True)
    for page in results["pages"]:
        fp = os.path.join(json_dir, f"{page['slug']}.json")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(page, f, indent=2, ensure_ascii=False)
        exported_files.append(fp)

    # 4. Master document
    master_md = _render_master_document(results)
    master_path = os.path.join(output_dir, "MASTER_CONTENT.md")
    with open(master_path, "w", encoding="utf-8") as f:
        f.write(master_md)
    exported_files.append(master_path)

    # 5. llms.txt
    llms_path = os.path.join(output_dir, "llms.txt")
    with open(llms_path, "w", encoding="utf-8") as f:
        f.write(results["llms_txt"])
    exported_files.append(llms_path)

    # 6. Sitemap URLs
    sitemap_path = os.path.join(output_dir, "sitemap_urls.txt")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        for url in results["sitemap_urls"]:
            f.write(url + "\n")
    exported_files.append(sitemap_path)

    # 7. Generation metadata
    meta = {
        "brand": results["brand"], "industry": results["industry"],
        "language": results["language"], "domain": results["domain"],
        "generated_at": results["generated_at"],
        "total_pages": len(results["pages"]),
        "total_words": sum(p["total_word_count"] for p in results["pages"]),
        "files_exported": len(exported_files),
    }
    meta_path = os.path.join(output_dir, "generation_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    exported_files.append(meta_path)

    return {
        "output_dir": output_dir, "files": exported_files,
        "total_files": len(exported_files),
        "total_pages": len(results["pages"]),
        "total_words": sum(p["total_word_count"] for p in results["pages"]),
    }


def _render_page_markdown(page: dict) -> str:
    """Render a single page as clean Markdown."""
    lines = [
        "---", f'title: "{page["meta_title"]}"',
        f'description: "{page["meta_description"]}"',
        f'url: "{page["url"]}"', f'canonical: "{page["canonical_url"]}"',
        f'language: "{page["language"]}"', f'direction: "{page["direction"]}"',
        f'og_title: "{page["og_title"]}"', f'og_description: "{page["og_description"]}"',
        f'word_count: {page["total_word_count"]}', "---", "",
        f'# {page["h1"]}', "",
    ]
    for section in page["sections"]:
        h_prefix = "#" * section["heading_level"]
        lines.extend([f"{h_prefix} {section['heading']}", "", section["content"], ""])
    lines.extend(["---", "", "## Schema.org JSON-LD", "", "```json",
                   json.dumps(page["schema_jsonld"], indent=2, ensure_ascii=False), "```"])
    return "\n".join(lines)


def _render_page_html(page: dict) -> str:
    """Render a single page as semantic HTML."""
    direction = page.get("direction", "ltr")
    lang = page.get("language", "en")
    parts = [
        '<!DOCTYPE html>', f'<html lang="{lang}" dir="{direction}">', '<head>',
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'  <title>{_esc(page["meta_title"])}</title>',
        f'  <meta name="description" content="{_esc(page["meta_description"])}">',
        f'  <link rel="canonical" href="{page["canonical_url"]}">',
        f'  <meta property="og:title" content="{_esc(page["og_title"])}">',
        f'  <meta property="og:description" content="{_esc(page["og_description"])}">',
        f'  <meta property="og:url" content="{page["url"]}">',
        '  <meta property="og:type" content="website">',
        '  <script type="application/ld+json">',
        json.dumps(page["schema_jsonld"], indent=2, ensure_ascii=False),
        '  </script>', '</head>', '<body>', '  <main>', '    <article>',
        f'    <h1>{_esc(page["h1"])}</h1>',
    ]
    for sec in page["sections"]:
        tag = f'h{sec["heading_level"]}'
        parts.append('    <section>')
        parts.append(f'      <{tag}>{_esc(sec["heading"])}</{tag}>')
        for line in sec["content"].split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("### "):
                parts.append(f'      <h3>{_esc(line[4:])}</h3>')
            elif line.startswith("- "):
                parts.append(f'      <li>{line[2:]}</li>')
            elif line.startswith("|"):
                continue
            elif line.startswith(">"):
                parts.append(f'      <blockquote>{_esc(line[1:].strip())}</blockquote>')
            else:
                parts.append(f'      <p>{_esc(line)}</p>')
        parts.append('    </section>')
    parts.extend(['    </article>', '  </main>', '</body>', '</html>'])
    return "\n".join(parts)


def _render_master_document(results: dict) -> str:
    """Render master document combining all pages."""
    lines = [
        f"# {results['brand']} - Complete Website Content Architecture", "",
        f"**Industry:** {results['industry']}",
        f"**Domain:** {results['domain']}",
        f"**Language:** {results['language_label']}",
        f"**Generated:** {results['generated_at']}",
        f"**Total Pages:** {len(results['pages'])}",
        f"**Total Words:** {sum(p['total_word_count'] for p in results['pages'])}",
        "", "---", "", "## Table of Contents", "",
    ]
    for i, page in enumerate(results["pages"], 1):
        lines.append(f"{i}. [{page['title']}](#{page['slug']}) ({page['total_word_count']} words)")
    lines.extend(["", "---", ""])
    for page in results["pages"]:
        lines.extend([f'<a id="{page["slug"]}"></a>', "", _render_page_markdown(page), "", "---", ""])
    return "\n".join(lines)


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#039;")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    """CLI entry point for content generation."""
    import argparse
    parser = argparse.ArgumentParser(description="InersiaLab Pre-Launch Page Content Generator")
    parser.add_argument("--brand", type=str, default="InersiaLab", help="Brand name")
    parser.add_argument("--industry", type=str, default="technology_software",
                        choices=list(INDUSTRY_PRESETS.keys()), help="Industry preset")
    parser.add_argument("--domain", type=str, default="https://example.com", help="Canonical domain")
    parser.add_argument("--language", type=str, default="en", choices=["en", "fr", "ar"], help="Output language")
    parser.add_argument("--description", type=str, default="", help="Core value proposition")
    parser.add_argument("--all-pages", action="store_true", help="Generate all default pages")
    parser.add_argument("--pages", type=str, nargs="*", default=[], help="Specific page IDs")
    parser.add_argument("--output", type=str, default="", help="Output directory")
    args = parser.parse_args()

    industry = INDUSTRY_PRESETS.get(args.industry, INDUSTRY_PRESETS["technology_software"])
    if args.all_pages:
        page_ids = [p["id"] for p in industry["default_pages"]]
    elif args.pages:
        page_ids = args.pages
    else:
        print(f"\n{'='*60}")
        print(f"  InersiaLab - Page Content Generator")
        print(f"  Industry: {industry['label']}")
        print(f"{'='*60}\n")
        print("Available pages:")
        for i, p in enumerate(industry["default_pages"], 1):
            req = " [REQUIRED]" if p.get("required") else ""
            print(f"  {i:2d}. {p['title']}{req}")
        print(f"\nEnter page numbers separated by commas (or 'all'):")
        selection = input("> ").strip()
        if selection.lower() == "all":
            page_ids = [p["id"] for p in industry["default_pages"]]
        else:
            indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]
            page_ids = [industry["default_pages"][i]["id"] for i in indices
                        if 0 <= i < len(industry["default_pages"])]

    if not page_ids:
        print("No pages selected. Exiting.")
        return

    config = {
        "brand_name": args.brand, "industry": args.industry,
        "domain": args.domain, "language": args.language,
        "description": args.description or industry.get("keywords_hint", ""),
        "pages": page_ids,
    }
    print(f"\nGenerating content for {len(page_ids)} pages...")
    synth = ContentSynthesizer(config)
    results = synth.generate_all()

    if args.output:
        output_dir = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in args.brand if c.isalnum() or c in ("-", "_")).strip() or "Site"
        output_dir = os.path.join(DOWNLOADS_DIR, f"SiteContent_{safe}_{ts}")

    export_result = export_content(results, output_dir)
    print(f"\n{'='*60}")
    print(f"  Content Generation Complete!")
    print(f"{'='*60}")
    print(f"  Pages generated : {export_result['total_pages']}")
    print(f"  Total words     : {export_result['total_words']}")
    print(f"  Files exported  : {export_result['total_files']}")
    print(f"  Output folder   : {export_result['output_dir']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
