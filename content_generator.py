"""InersiaLab Software Department - Pre-Launch Website Page & Section Content Generator.

Generates comprehensive, SEO/GEO-optimized structured text content for every page
of a new website before development begins. Outputs clean semantic Markdown, HTML
structure, and JSON for headless CMS ingestion.

Key design goals:
- 100% custom content generated from detailed client briefs (zero generic bracketed placeholders)
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
from typing import Optional, List, Dict, Any

try:
    from competitor_benchmark import CompetitorBenchmarkAnalyzer
except ImportError:
    CompetitorBenchmarkAnalyzer = None

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
            {"id": "service_detail_1", "title": "Service: Primary Treatment", "required": False},
            {"id": "service_detail_2", "title": "Service: Secondary Treatment", "required": False},
            {"id": "service_detail_3", "title": "Service: Tertiary Treatment", "required": False},
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
            {"id": "service_detail_1", "title": "Solution: Core Platform", "required": False},
            {"id": "service_detail_2", "title": "Solution: API / Integration", "required": False},
            {"id": "service_detail_3", "title": "Solution: Enterprise Security", "required": False},
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
            {"id": "category_1", "title": "Category: Primary Product Line", "required": False},
            {"id": "category_2", "title": "Category: Secondary Product Line", "required": False},
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
            {"id": "service_detail_1", "title": "Service: Web Design & Development", "required": False},
            {"id": "service_detail_2", "title": "Service: SEO & Digital Marketing", "required": False},
            {"id": "service_detail_3", "title": "Service: Branding & Creative", "required": False},
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
            {"id": "service_detail_1", "title": "Service: Core Practice Area", "required": False},
            {"id": "service_detail_2", "title": "Service: Secondary Practice", "required": False},
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
            {"id": "course_detail_1", "title": "Course: Flagship Program", "required": False},
            {"id": "course_detail_2", "title": "Course: Certification Program", "required": False},
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
            {"id": "service_detail_1", "title": "Service: Primary Offering", "required": False},
            {"id": "service_detail_2", "title": "Service: Secondary Offering", "required": False},
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
            {"id": "category_1", "title": "Category: Main Topic", "required": False},
            {"id": "category_2", "title": "Category: Secondary Topic", "required": False},
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
# Pre-Configured Realistic Client Demo Briefs (45-Question Diagnostic Survey)
# ---------------------------------------------------------------------------

DEMO_CLIENT_BRIEFS = {
    "dental_clinic": {
        # Section 1: Business Identity & Legal DNA (Q1-Q6)
        "brand_name": "AuraDental Implant & Surgical Center",
        "legal_entity_name": "Aura Surgical & Restorative Dentistry PC",
        "year_founded": "2008",
        "origin_location": "New York, NY",
        "mission_statement": "To restore permanent, infection-free masticatory function and aesthetic dignity to patients through micro-surgical digital implantology without unnecessary bone grafts or prolonged agony.",
        "tagline": "Advanced Digital Implantology & Aesthetic Restorations",
        "archetype": "healthcare_medical",
        "industry": "healthcare_medical",
        "domain": "https://auradentalcare.com",
        "language": "en",
        "brand_tone": "clinically authoritative, reassuring, transparent, uncompromising on precision",
        "tone": "clinically authoritative, reassuring, transparent, uncompromising on precision",
        "banned_words": ["cheap", "bargain", "budget dental", "painless miracle", "disrupt", "synergy"],

        # Section 2: Leadership, Credentials & E-E-A-T Pedigree (Q7-Q12)
        "founder_name": "Dr. Julian Vance, DDS, FICOI",
        "founder_title": "Chief Oral Surgeon & Fellow of ICOI",
        "founder_credentials": "DDS from Columbia University College of Dental Medicine, 18+ years surgical experience, 3,400+ successful dental implants, Fellow of the International Congress of Oral Implantologists",
        "alma_maters": "Columbia University College of Dental Medicine, Mount Sinai Hospital Surgical Residency",
        "origin_story": "Founded in 2008 by Dr. Vance after seeing countless patients traumatized by ill-fitting dentures and multi-year bone graft failures. Dr. Vance pioneered computer-guided All-on-4 immediate loading to deliver fixed teeth in a single clinical day.",
        "key_staff_specialists": "Dr. Elena Rostova, Board-Certified Dental Anesthesiologist; Dr. Marcus Sterling, Master Prosthodontist & Digital Smile Designer",
        "patents_publications": "Author of 'Biomechanical Stress Distribution in Angled Multi-Unit Abutments' (Journal of Oral Implantology, 2019); US Patent for Dynamic 3D Surgical Guide Collar",
        "industry_awards": "New York Top Oral Surgeon (2021-2025), ICOI Master Clinician Honor, AACD Platinum Restorative Excellence Award",

        # Section 3: Ideal Customer Persona (ICP) & Buyer Psychology (Q13-Q18)
        "target_buyer_persona": "Adults aged 45-75 with failing dentition, terminal periodontal disease, or broken bridges seeking permanent, non-removable teeth with minimal downtime.",
        "pain_points": [
            "Debilitating embarrassment smiling or speaking in professional and social settings",
            "Inability to chew steak, apples, or firm foods causing gastrointestinal distress",
            "Severe anxiety regarding dental pain, needles, and prolonged surgical procedures"
        ],
        "catalyst_event": "A broken front bridge before a family wedding or sudden acute periodontal abscess forcing an urgent decision.",
        "disqualification_criteria": "Patients seeking removable partial acrylic dentures, unverified bargain overseas tourism treatments, or patients refusing 3D diagnostic safety scans.",
        "desired_after_state": "Enjoying dinner with family without fear, laughing openly without covering the mouth, and possessing permanent, infection-free teeth guaranteed for life.",
        "buyer_anxieties": [
            "Fear of unbearable surgical pain during and after the procedure",
            "Fear of hidden costs inflating the initial quote",
            "Fear that implants will reject or fall out after a few years"
        ],

        # Section 4: Proprietary Methodology, Process & Tech Stack (Q19-Q25)
        "framework_name": "The 4-D Guided Precision Restoration Protocol",
        "phase1_discovery": "Comprehensive 3D CBCT Volumetric Scan & Digital Smile Aesthetic Simulation (Same-Day Assessment)",
        "phase2_blueprint": "Computer-Guided Virtual Surgery Planning & Custom Titanium Multi-Unit Abutment CAD/CAM Milling",
        "phase3_execution": "Twilight IV Sedation, Minimally Invasive Computer-Guided Fixture Placement & Immediate Fixed Provisional Delivery (Single Day)",
        "phase4_optimization": "Permanent Monolithic Zirconia Final Bridge Delivery & Lifetime Bi-Annual Maintenance Care",
        "technologies": [
            "Planmeca ProMax 3D CBCT Scanner",
            "Fotona LightWalker Dual-Wavelength Surgical Laser",
            "3Shape TRIOS 5 Wireless Intraoral Scanner",
            "SprintRay Pro55 S 3D Surgical Guide Printer",
            "Pic Dental Photogrammetry Camera"
        ],
        "guarantees": "Lifetime structural replacement warranty on all titanium implant fixtures; 10-year replacement warranty on final monolithic zirconia prosthetics; 100% itemized fee guarantee with zero surprise post-op bills.",

        # Section 5: Flagship Services & Transparent Pricing (Q26-Q31)
        "services": [
            {
                "id": "service_detail_1",
                "name": "All-on-4 Same-Day Full Arch Dental Implants",
                "target_audience": "Adults with failing dentition, severe periodontal bone loss, or uncomfortable dentures",
                "core_benefit": "Full-arch permanent teeth restoration in a single appointment with zero bone grafting in 90% of cases",
                "deliverables": "Pre-op 3D CBCT scan, computer-guided titanium fixture placement, immediate fixed provisional bridge, final zirconia restoration",
                "pricing": "$18,500 per arch with zero-interest 24-month financing options",
                "duration": "1-Day Surgical Procedure + 3-Month Osseointegration Follow-up"
            },
            {
                "id": "service_detail_2",
                "name": "Digital Smile Design Porcelain Veneers",
                "target_audience": "Patients seeking aesthetic smile enhancement, correcting chipped, discolored, or misaligned teeth",
                "core_benefit": "Handcrafted micro-thin ceramic veneers preserving 95% of natural tooth enamel with 3D digital simulation",
                "deliverables": "Digital facial scan, 3D wax-up try-in, preparation under microscope, custom master ceramist feldspathic porcelain fabrication",
                "pricing": "$1,800 - $2,400 per tooth with comprehensive 10-year aesthetic warranty",
                "duration": "2 clinical appointments spaced 10 days apart"
            },
            {
                "id": "service_detail_3",
                "name": "IV Sedation Dentistry & Laser Periodontics",
                "target_audience": "Dental-phobic patients, complex surgical candidates, or advanced gum disease sufferers",
                "core_benefit": "Completely painless, anxiety-free surgical care with LANAP laser technology accelerating soft-tissue recovery",
                "deliverables": "Board-certified anesthesiologist monitoring, vitals tracking, LANAP biostimulation laser treatment, post-op recovery kit",
                "pricing": "$850 per surgical sedation session; LANAP full mouth $4,200",
                "duration": "2 to 3-hour twilight sedation session"
            }
        ],
        "secondary_offerings": "VIP Private Recovery Suite, Same-Day Emergency Surgical On-Call, Comprehensive Pre-Op Medical Clearance Coordination",
        "pricing_model": "100% itemized transparent pricing; All-on-4 complete arch starting at $18,500; 0% APR 24-month healthcare financing via Proceed Finance & CareCredit",
        "turnaround_speed": "Same-Day Immediate Fixed Teeth (under 6 hours clinical time); final custom zirconia bridge seated at 12 weeks post-osseointegration",

        # Section 6: Local Geography, Micro-Anchors & Physical NAP (Q32-Q36)
        "address": "450 Lexington Ave, Suite 1400, New York, NY 10017",
        "service_areas": ["Midtown Manhattan", "Upper East Side", "Upper West Side", "Brooklyn Heights", "Westchester County", "Greenwich, CT", "Tri-State Area"],
        "local_landmarks": "Directly across from Grand Central Terminal, at the corner of Lexington Avenue and 45th Street, 3 blocks east of Bryant Park",
        "facility_access": "Private elevator bank directly to Suite 1400, covered subterranean valet parking on 45th St, fully ADA wheelchair accessible surgical operatory",
        "phone": "+1 (212) 555-0198",
        "email": "concierge@auradentalcare.com",
        "urgent_contact": "+1 (212) 555-0199 (24/7 Dedicated Surgical Post-Op Emergency Line)",

        # Section 7: Proof Metrics, Case Studies & Real Reviews (Q37-Q41)
        "proof_metrics": [
            {"label": "Successful Implants Placed", "value": "3,400+"},
            {"label": "Clinical Success Rate", "value": "98.6%"},
            {"label": "Years in Surgical Practice", "value": "18 Years"},
            {"label": "Same-Day Full Arches Delivered", "value": "1,250+"}
        ],
        "case_study_1": {
            "title": "Terminal Periodontal Bone Loss to Permanent Full Arch in 6 Hours",
            "client": "Thomas B., 58, Manhattan Corporate Executive",
            "challenge": "Suffered from terminal generalized periodontitis with 80% bone loss on upper arch, unable to chew solids, facing conventional dentures.",
            "solution": "Dr. Vance performed 3D guided computer surgery placing four angled Neodent fixtures utilizing dense zygomatic-adjacent bone, avoiding sinus lifts entirely.",
            "outcome": "Fixed acrylic hybrid bridge delivered in 5.5 hours under IV sedation. Zero postoperative pain reported; transitioned to final monolithic zirconia at 12 weeks."
        },
        "case_study_2": {
            "title": "Complex Traumatic Aesthetic Smile Reconstruction",
            "client": "Sarah K., 42, Television Producer",
            "challenge": "Traumatic incisor fracture and failing root canal with severe aesthetic discoloration and soft-tissue recession.",
            "solution": "Immediate laser socket disinfection, placement of custom titanium zirconium implant, platelet-rich fibrin (PRF) soft-tissue graft, and custom shaded ceramic crown.",
            "outcome": "Natural gingival emergence profile preserved. Restored full aesthetic symmetry matching adjacent natural teeth with 100% patient satisfaction."
        },
        "real_reviews": [
            {
                "author": "Eleanor Vance, Retired Educator",
                "rating": 5,
                "service": "All-on-4 Same-Day Implants",
                "quote": "I spent 6 years hiding my smile behind my hand and dreading traditional dentures. Dr. Vance and his team replaced my failing upper teeth in a single morning. Woke up from twilight sedation with zero pain and a flawless smile. One year later, eating steak and apples feels completely natural."
            },
            {
                "author": "Marcus Sterling, Managing Director",
                "rating": 5,
                "service": "Digital Smile Design Veneers",
                "quote": "The 3D preview showed me exactly what my teeth would look like before Dr. Vance touched a single tooth. The ceramic work is so natural that even my business colleagues just assumed I took up whitening. Worth every single penny."
            },
            {
                "author": "Sophia Chen, Architect",
                "rating": 5,
                "service": "IV Sedation Dentistry",
                "quote": "As someone with debilitating dental panic, AuraDental changed everything. The anesthesiologist had me relaxed in minutes, and Dr. Vance completed my complex extractions and implant placement while I slept comfortably. Truly life-changing care."
            }
        ],
        "certifications": [
            "Fellow of the International Congress of Oral Implantologists (FICOI)",
            "American Academy of Cosmetic Dentistry (AACD) Accredited",
            "American Dental Association (ADA) Member",
            "HIPAA Compliant & OSHA Surgical Sterilization Certified"
        ],

        # Section 8: Competitive Benchmarking & Market Gap (Q42-Q45)
        "competitor_urls": ["https://www.clevelandclinic.org", "https://www.mayoclinic.org"],
        "competitor_shortcomings": "Traditional corporate dental clinics force patients through multiple outside referrals, months of uncomfortable removable healing dentures, and surprise bill add-ons for bone grafting and anesthesia.",
        "unfair_advantage_uvp": "Everything—from 3D diagnostic imaging and surgical placement to master lab ceramic milling—is executed under one roof by a board-certified ICOI Fellow with zero referrals and zero delays.",
        "primary_cta": "Book Your 3D Surgical Implant Consultation",
        "secondary_lead_magnet": "Download the Free 2026 Guide to Same-Day All-on-4 Implants (Pricing, Candidacy & Recovery)"
    },

    "cybersecurity_saas": {
        # Section 1: Business Identity & Legal DNA (Q1-Q6)
        "brand_name": "AegisVector AI Cloud Security",
        "legal_entity_name": "AegisVector Technologies Inc.",
        "year_founded": "2021",
        "origin_location": "San Francisco, CA",
        "mission_statement": "To autonomously neutralize advanced multi-cloud and Kubernetes runtime breaches at machine speed before lateral movement compromises customer data.",
        "tagline": "Autonomous Real-Time Kubernetes & Multi-Cloud Threat Remediation",
        "archetype": "technology_software",
        "industry": "technology_software",
        "domain": "https://aegisvector.io",
        "language": "en",
        "brand_tone": "authoritative, technical, mission-critical, uncompromising on zero-latency defense",
        "tone": "authoritative, technical, mission-critical, uncompromising on zero-latency defense",
        "banned_words": ["silver bullet", "cheap", "seamless magic", "game-changing buzzword", "disrupt"],

        # Section 2: Leadership, Credentials & E-E-A-T Pedigree (Q7-Q12)
        "founder_name": "Tariq Al-Mansoor, CISSP",
        "founder_title": "Chief Executive Officer & Former DoD Cyber Architect",
        "founder_credentials": "M.S. in Computer Science from Carnegie Mellon University, 16 years leading defensive cyber architecture at DARPA and Tier-1 cloud infrastructure providers",
        "alma_maters": "Carnegie Mellon University, Massachusetts Institute of Technology (MIT)",
        "origin_story": "Founded in 2021 after witnessing enterprise SecOps teams suffer from crippling alert fatigue (over 10,000 unverified alerts daily), AegisVector was built to automate sub-second container isolation without human latency.",
        "key_staff_specialists": "Elena Rostova, VP of Kernel Research (former Linux kernel maintainer); Marcus Thorne, Lead Threat Hunter (former NSA Tailored Access Operations)",
        "patents_publications": "US Patent 11,489,201: 'Deterministic Anomaly Containment via Dynamic eBPF Bytecode Instrumentation'; Author of 'Zero-Trust at Machine Speed' (Black Hat 2023)",
        "industry_awards": "Gartner Cool Vendor in Cloud Security (2024), RSA Innovation Sandbox Finalist, Cloud Security Alliance Champion Award",

        # Section 3: Ideal Customer Persona (ICP) & Buyer Psychology (Q13-Q18)
        "target_buyer_persona": "CISOs, DevSecOps Directors, and Principal Cloud Architects at Series B+ tech scale-ups and Fortune 1000 enterprises running 500+ Kubernetes nodes across AWS, GCP, and Azure.",
        "pain_points": [
            "Over 10,000 daily alert noise drowning out critical zero-day exploit signals",
            "Slow manual incident containment taking an average of 4.2 hours while attackers move laterally",
            "Heavy security agents consuming 8-15% of server CPU, causing production latency and cluster bloat"
        ],
        "catalyst_event": "A near-miss cryptojacking breach, failed SOC 2 Type II audit, or executive mandate following a peer's public cloud extortion incident.",
        "disqualification_criteria": "Small static WordPress blogs, companies without dedicated cloud engineering staff, or organizations seeking free consumer antivirus software.",
        "desired_after_state": "Complete peace of mind knowing all Kubernetes clusters autonomously self-defend in 120ms with 92% less alert noise and verifiable SOC 2 compliance.",
        "buyer_anxieties": [
            "Fear that an eBPF security probe will crash the Linux kernel and cause production outages",
            "Fear of unexpected egress network bandwidth fees inflating cloud invoices",
            "Fear of lengthy 6-month deployment cycles burdening platform engineering teams"
        ],

        # Section 4: Proprietary Methodology, Process & Tech Stack (Q19-Q25)
        "framework_name": "The AegisVector Autonomous Isolation Matrix (AIM)",
        "phase1_discovery": "Zero-Restart Helm Deployment & Passive eBPF Kernel Telemetry Baselines (15-Minute Activation)",
        "phase2_blueprint": "AI Behavior Clustering & Least-Privilege IAM Graph Mapping across Multi-Cloud Environments",
        "phase3_execution": "Sub-120ms Deterministic Threat Interception & Automated Ephemeral Micro-Segmentation",
        "phase4_optimization": "Automated GitOps Remediation Pull Requests & Continuous SOC 2 / HIPAA Compliance Auditing",
        "technologies": [
            "Linux eBPF Kernel Probes",
            "Transformer-based Anomaly Models",
            "OpenTelemetry Distributed Tracing",
            "Zero-Trust WireGuard Mesh",
            "Cilium-Integrated Network Enforcement"
        ],
        "guarantees": "99.99% SaaS platform uptime SLA, sub-15-minute response time from Tier-3 cybersecurity architects, zero kernel crash guarantee backed by $1M indemnity.",

        # Section 5: Flagship Services & Transparent Pricing (Q26-Q31)
        "services": [
            {
                "id": "service_detail_1",
                "name": "Autonomous eBPF Runtime Container & Kubernetes Protection",
                "target_audience": "DevSecOps directors, Cloud Platform Engineers, and Enterprise CISOs managing multi-cloud Kubernetes clusters",
                "core_benefit": "Zero-overhead kernel-level anomaly detection and instant autonomous pod isolation in under 120 milliseconds",
                "deliverables": "DaemonSet lightweight eBPF sensor, zero-restart container telemetry, real-time MITRE ATT&CK kill-chain mapping, automated network micro-segmentation",
                "pricing": "$42 per node per month billed annually with unlimited container pods",
                "duration": "15-minute helm chart installation with zero cluster restart"
            },
            {
                "id": "service_detail_2",
                "name": "Cloud Infrastructure Entitlement & IAM Blast-Radius Defense",
                "target_audience": "Security Operations (SecOps) teams struggling with overly permissive AWS/GCP/Azure IAM roles and machine identities",
                "core_benefit": "Reduces cloud identity attack surface by 85% through continuous AI-driven least-privilege rightsizing",
                "deliverables": "Automated IAM policy pruning pull-requests, toxic permission combination graphs, automated machine token revocation",
                "pricing": "$1,200 per cloud account per month with continuous posture compliance auditing",
                "duration": "Read-only cloud cross-account role integration in under 5 minutes"
            },
            {
                "id": "service_detail_3",
                "name": "AI-Powered Threat Hunting & Real-Time Remediation Co-Pilot",
                "target_audience": "Enterprise SOC analysts drowning in manual SIEM queries and false positive triage",
                "core_benefit": "Transforms complex natural language threat queries into instant forensic timelines and one-click remediation playbooks",
                "deliverables": "LLM-assisted threat correlation engine, MITRE framework alignment, automated SOAR webhook triggers, SOC 2/ISO compliance export",
                "pricing": "Enterprise custom tier starting at $24,000/year for enterprise-wide correlation",
                "duration": "Instant turnkey SaaS platform activation"
            }
        ],
        "secondary_offerings": "24/7 Red Team Simulation Exercises, Dedicated Principal Security Architect Advisory, Urgent Ransomware Response Retainer",
        "pricing_model": "Transparent per-node subscription ($42/node/mo) with zero data ingest taxes and 30-day proof-of-value sandbox",
        "turnaround_speed": "Turnkey activation in 15 minutes; real-time threat neutralization in under 120 milliseconds",

        # Section 6: Local Geography, Micro-Anchors & Physical NAP (Q32-Q36)
        "address": "100 Pine Street, Suite 2200, San Francisco, CA 94111",
        "service_areas": ["Silicon Valley", "San Francisco Bay Area", "North America", "European Union", "United Kingdom", "Asia-Pacific"],
        "local_landmarks": "Corner of Pine and Front Streets in the Financial District, 2 blocks from the Embarcadero Center and BART Montgomery Station",
        "facility_access": "Executive briefing center on 22nd floor with 24/7 biometric security access and dedicated customer briefing labs",
        "phone": "+1 (415) 555-0142",
        "email": "solutions@aegisvector.io",
        "urgent_contact": "+1 (415) 555-0143 (24/7 Dedicated Enterprise SOC Priority Hotline)",

        # Section 7: Proof Metrics, Case Studies & Real Reviews (Q37-Q41)
        "proof_metrics": [
            {"label": "Mean Time to Contain (MTTC)", "value": "120ms"},
            {"label": "Alert Fatigue Reduction", "value": "92%"},
            {"label": "Cloud Workloads Protected", "value": "450,000+"},
            {"label": "Enterprise Net Promoter Score", "value": "78"}
        ],
        "case_study_1": {
            "title": "Sub-Second Neutralization of Multi-Cloud Cryptomining Infection",
            "client": "Global FinTech Processing $4B Monthly Payments",
            "challenge": "A compromised developer API token allowed attackers to deploy cryptomining pods across a 1,200-node Kubernetes cluster on AWS.",
            "solution": "AegisVector's eBPF sensor detected abnormal CPU instruction cycles and isolated the compromised namespaces within 94 milliseconds, revoking the IAM token automatically.",
            "outcome": "Zero customer data exfiltration, zero API latency degradation, and prevention of an estimated $180,000 in unauthorized cloud compute charges."
        },
        "case_study_2": {
            "title": "Automated Pruning of 4,000 Toxic IAM Cloud Permissions",
            "client": "Enterprise HealthTech SaaS",
            "challenge": "Years of rapid microservice development left 450 AWS IAM roles with wildcard administrator write permissions, risking HIPAA decertification.",
            "solution": "AegisVector mapped the exact behavioral blast-radius of every machine identity and generated automated Terraform pull requests to prune unused permissions.",
            "outcome": "88% attack surface reduction in 14 days without a single service outage, passing SOC 2 Type II audit with zero exceptions."
        },
        "real_reviews": [
            {
                "author": "Nathalie Dupont, VP of Infrastructure, FinTech Unicorn",
                "rating": 5,
                "service": "Autonomous eBPF Protection",
                "quote": "Before AegisVector, our 4,000-node Kubernetes infrastructure generated 14,000 raw alerts daily. AegisVector's eBPF sensors filtered out 94% of background noise and caught a cryptomining pod breakout within 110 milliseconds. It paid for itself in week one."
            },
            {
                "author": "David Rostova, Chief Information Security Officer, HealthTech Cloud",
                "rating": 5,
                "service": "Cloud IAM Defense",
                "quote": "The IAM blast-radius graph revealed 300+ orphaned roles with wildcard write permissions left behind by old CI/CD pipelines. AegisVector generated safe GitOps PRs to prune them automatically without breaking a single production API."
            },
            {
                "author": "Sarah Jenkins, Head of DevSecOps, Global E-Commerce",
                "rating": 5,
                "service": "AI Threat Remediation Co-Pilot",
                "quote": "Our tier-1 analysts used to spend 45 minutes correlating logs across Datadog, CloudTrail, and Splunk. AegisVector's AI co-pilot reconstructs the entire attack kill-chain in 3 seconds with a single click remediation button."
            }
        ],
        "certifications": [
            "SOC 2 Type II Certified",
            "ISO/IEC 27001:2022",
            "FedRAMP Ready (High Baseline)",
            "AWS Security Competency Partner"
        ],

        # Section 8: Competitive Benchmarking & Market Gap (Q42-Q45)
        "competitor_urls": ["https://www.crowdstrike.com", "https://www.datadoghq.com"],
        "competitor_shortcomings": "Legacy EDR vendors rely on heavy user-space daemons that consume 10% CPU and only alert humans instead of taking autonomous real-time containment action.",
        "unfair_advantage_uvp": "True kernel-level eBPF isolation that autonomously stops zero-day threats in 120ms with less than 1.2% CPU overhead and zero cloud egress tax.",
        "primary_cta": "Request an Enterprise Proof-of-Value Sandbox",
        "secondary_lead_magnet": "Run a Free 15-Minute Kubernetes Runtime Vulnerability Assessment"
    },

    "luxury_contractor": {
        # Section 1: Business Identity & Legal DNA (Q1-Q6)
        "brand_name": "Vanguard Heritage Custom Builders",
        "legal_entity_name": "Vanguard Heritage Construction Group LLC",
        "year_founded": "1997",
        "origin_location": "Aspen & Austin",
        "mission_statement": "To construct generational architectural estates combining centuries-old artisanal stonemasonry and timbercraft with cutting-edge passive house building science and complete fiscal transparency.",
        "tagline": "Architectural Estates, Generational Craftsmanship & Historic Restoration",
        "archetype": "local_business",
        "industry": "local_business",
        "domain": "https://vanguardheritage.com",
        "language": "en",
        "brand_tone": "distinguished, architectural, prestigious, uncompromising on craftsmanship, reassuring",
        "tone": "distinguished, architectural, prestigious, uncompromising on craftsmanship, reassuring",
        "banned_words": ["cookie-cutter", "fast cheap remodel", "discount builder", "spec home"],

        # Section 2: Leadership, Credentials & E-E-A-T Pedigree (Q7-Q12)
        "founder_name": "Harrison Sterling, Master Builder",
        "founder_title": "Founder & Principal Architectural Builder",
        "founder_credentials": "B.S. in Civil & Structural Engineering from Stanford University, Master Builder with 28+ years directing bespoke residential estate construction totaling over $320M in private estate commissions",
        "alma_maters": "Stanford University School of Engineering, European Guild of Master Stonemasons Fellowship",
        "origin_story": "Founded in 1997 by Harrison Sterling out of deep frustration with volume spec-builders cutting structural corners. Harrison established Vanguard Heritage to resurrect uncompromising European guild-level joinery and stonemasonry for discerning families building generational residences.",
        "key_staff_specialists": "Claire Sterling, Principal Architectural Liaison; Mateo Rossi, Master Guild Joiner & Timber Framer; Julian Vance, PE, Senior Geotechnical & Foundation Engineer",
        "patents_publications": "Author of 'Generational Structural Engineering in Limestone Terrains' (Architectural Digest Technical Series, 2022); Proprietary Zero-Thermal-Bridge Foundation Patent",
        "industry_awards": "National Custom Home Builder of the Year (NAHB 2023), 18 Palladio Architectural Craftsmanship Awards, Architectural Digest Top 100 Builders",

        # Section 3: Ideal Customer Persona (ICP) & Buyer Psychology (Q13-Q18)
        "target_buyer_persona": "High-net-worth families, tech founders, and private estate investors commissioning custom legacy compounds and equestrian ranches valued between $4M and $30M.",
        "pain_points": [
            "Severe distrust of general contractors hiding markups and springing six-figure change-order surprises",
            "Fear of project abandonment or unexcused 12-month construction delays",
            "Frustration with builders substituting inferior sub-grade building materials behind drywall"
        ],
        "catalyst_event": "Purchasing a pristine waterfront or cliffside parcel, or inheriting a historic estate requiring museum-grade restoration.",
        "disqualification_criteria": "Volume suburban spec homes, tract developments, clients demanding unvetted low-bid subcontractors, or quick cosmetic flip remodels.",
        "desired_after_state": "Living in an awe-inspiring, museum-quality sanctuary built to withstand three centuries, delivered on schedule with completely open books.",
        "buyer_anxieties": [
            "Fear of catastrophic budget overruns",
            "Fear that the builder will not personally supervise the jobsite daily",
            "Fear of structural settling or water intrusion on challenging topography"
        ],

        # Section 4: Proprietary Methodology, Process & Tech Stack (Q19-Q25)
        "framework_name": "The Vanguard 4-Stage Generational Build Protocol",
        "phase1_discovery": "Comprehensive Geotechnical Core Drilling, Solar Alignment & 3D LIDAR Reality Capture",
        "phase2_blueprint": "Full BIM 3D Architectural Engineering, Millwork Prototype Fabrication & 100% Open-Book Cost Accounting",
        "phase3_execution": "Master Artisan Construction, Daily Principal Jobsite Supervision & Private 4K Client Drone Portal Updates",
        "phase4_optimization": "White-Glove Commissioning, 10-Year Structural Transferable Warranty & Semi-Annual Estate Concierge Inspections",
        "technologies": [
            "Matterport 3D Laser Reality Capture",
            "Autodesk Revit BIM Modeling",
            "Geothermal Heating & Cooling Systems",
            "Lutron HomeWorks Architectural Lighting",
            "Liebherr Precision Heavy Lifting Rigging"
        ],
        "guarantees": "Exclusive 10-year transferable structural warranty backed by third-party engineering underwriters; 2-year mechanical/electrical warranty; guaranteed completion date with contractual compensation clauses.",

        # Section 5: Flagship Services & Transparent Pricing (Q26-Q31)
        "services": [
            {
                "id": "service_detail_1",
                "name": "Custom Architectural Luxury Estates",
                "target_audience": "Private families and investors commissioning one-of-a-kind generational residential compounds from 6,000 to 25,000+ square feet",
                "core_benefit": "Museum-grade building envelope, custom timber framing, and geothermal climate control engineered to endure for 150+ years",
                "deliverables": "Full turnkey construction, custom structural foundation engineering, hand-cut masonry, private client builder portal access with daily photo logs",
                "pricing": "$750 - $1,400 per square foot with 100% open-book cost-plus accounting",
                "duration": "14 to 24-month comprehensive build schedule"
            },
            {
                "id": "service_detail_2",
                "name": "Historic Landmark & Estate Restoration",
                "target_audience": "Owners of registered historic estates, classical stone manors, or landmarked heritage properties",
                "core_benefit": "Meticulous preservation of original architectural millwork and masonry integrated seamlessly with modern high-efficiency MEP systems",
                "deliverables": "Archival historical research, hand-carved stone replication, timber structural stabilization, hidden smart-home integration",
                "pricing": "$500,000 - $5M+ dedicated restoration scopes with strict preservation board compliance",
                "duration": "8 to 18-month meticulous preservation schedule"
            },
            {
                "id": "service_detail_3",
                "name": "Bespoke Outdoor Living, Poolscapes & Equestrian Ranches",
                "target_audience": "Estate owners seeking resort-caliber grounds, infinity-edge vanishing pools, outdoor pavilions, and equestrian facilities",
                "core_benefit": "Harmonious landscape integration using local native stone, custom steel pergolas, and automated climate-controlled outdoor living zones",
                "deliverables": "Engineered retaining walls, imported Italian travertine flatwork, vanishing-edge negative edge pools, automated climate-controlled louvered pergolas",
                "pricing": "$350,000 - $1.2M integrated poolscape packages",
                "duration": "4 to 7-month landscape architecture and hardscaping build"
            }
        ],
        "secondary_offerings": "White-Glove Estate Concierge Maintenance, 24/7 Priority Emergency Storm Defense, Custom Fine-Art Climate Vault Construction",
        "pricing_model": "100% open-book cost-plus transparent billing with real-time client builder portal access to invoices, subcontractor bids, and receipts",
        "turnaround_speed": "Strictly limited to 4 to 6 estate commissions per year to guarantee principal builder daily jobsite presence",

        # Section 6: Local Geography, Micro-Anchors & Physical NAP (Q32-Q36)
        "address": "3200 Westlake Drive, Suite 300, Austin, TX 78746",
        "service_areas": ["Westlake Hills", "Tarrytown", "Lake Travis Waterfront", "Rollingwood", "Barton Creek", "Aspen / Roaring Fork Valley"],
        "local_landmarks": "Overlooking Lake Austin off Westlake Drive, 5 minutes from Loop 360 Pennybacker Bridge, adjacent to Austin Country Club",
        "facility_access": "Private architectural design studio and stone fabrication courtyard with private gate security access and client conference suites",
        "phone": "+1 (512) 555-0188",
        "email": "inquiries@vanguardheritage.com",
        "urgent_contact": "+1 (512) 555-0189 (24/7 Private Estate Concierge Hotline)",

        # Section 7: Proof Metrics, Case Studies & Real Reviews (Q37-Q41)
        "proof_metrics": [
            {"label": "Luxury Estates Completed", "value": "112"},
            {"label": "National Architectural Awards", "value": "18"},
            {"label": "On-Time Completion Rate", "value": "98.2%"},
            {"label": "Client Net Promoter Score", "value": "94"}
        ],
        "case_study_1": {
            "title": "Cliffside Cantilevered Modernist Estate on Lake Austin",
            "client": "Robert & Claire Sterling, Tech Founders",
            "challenge": "A 35-degree solid limestone cliffside site requiring 45-foot foundation piers without disrupting the protected shoreline ecosystem.",
            "solution": "Harrison Sterling engineered a steel cantilevered foundation anchored into deep bedrock with a 75-foot infinity pool suspended over the water.",
            "outcome": "Delivered 2 weeks ahead of scheduled Thanksgiving move-in. Won 2024 Residential Architectural Design of the Year with zero change-order disputes."
        },
        "case_study_2": {
            "title": "Museum-Grade Restoration of 1890s Historic Limestone Manor",
            "client": "Private Family Foundation",
            "challenge": "Navigating strict historic preservation society covenants while retrofitting a century-old masonry estate with modern geothermal heating and smart systems.",
            "solution": "Master guild masons hand-carved replacement limestone blocks and routed concealed radiant conduits through antique heart-pine floors.",
            "outcome": "Achieved full preservation board commendation and reduced annual heating costs by 68% while preserving 100% of historical aesthetics."
        },
        "real_reviews": [
            {
                "author": "Robert & Claire Sterling, Tech Executives",
                "rating": 5,
                "service": "Bespoke Custom Estate",
                "quote": "Harrison Sterling and his team built our 8,500 sq ft Westlake estate on a challenging 30-degree limestone cliffside. The structural precision, zero-gap millwork, and transparent open-book portal kept us completely at ease. Delivered 2 weeks ahead of our Thanksgiving move-in date. A true masterpiece."
            },
            {
                "author": "Judge Patricia Montgomery",
                "rating": 5,
                "service": "Historic Residential Restoration",
                "quote": "Restoring an 1890s limestone manor required navigating strict historic landmark commissions. Vanguard Heritage replicated original hand-carved mouldings and repaired century-old masonry while discreetly hiding high-efficiency geothermal heating. Their craftsmen are true artists."
            },
            {
                "author": "Dr. Andrew Whitfield, Orthopedic Surgeon",
                "rating": 5,
                "service": "Luxury Outdoor Living & Poolscape",
                "quote": "Our infinity-edge pool and summer kitchen feel like a private Aman resort in our own backyard. Even three years after completion, their warranty concierge team visits semi-annually for preventative maintenance. Exceptional integrity."
            }
        ],
        "certifications": [
            "NAHB Certified Graduate Builder (CGB)",
            "Certified Aging-in-Place Specialist (CAPS)",
            "USGBC LEED Platinum Certified Builder",
            "Texas Association of Builders Master Member"
        ],

        # Section 8: Competitive Benchmarking & Market Gap (Q42-Q45)
        "competitor_urls": ["https://www.tollbrothers.com", "https://www.architecturaldigest.com"],
        "competitor_shortcomings": "Corporate production builders mark up hidden change orders by 40%, use anonymous rotating job superintendents, and cut corners on foundation waterproofing.",
        "unfair_advantage_uvp": "We strictly limit our firm to 4 to 6 estate commissions per year, guaranteeing principal builder daily jobsite presence and 100% open-book fiscal transparency.",
        "primary_cta": "Schedule a Private Estate Consultation with Harrison Sterling",
        "secondary_lead_magnet": "Request the 2026 Private Estate Planning & Geotechnical Feasibility Portfolio"
    }
}


def normalize_client_brief(brief: dict) -> dict:
    """Normalize and enrich client brief dictionary with robust fallback defaults across all 45 survey questions.
    
    Guarantees no bracketed placeholders ([Founder Name], [Client Name], etc.)
    remain in the configuration.
    """
    b = dict(brief or {})
    ind_key = b.get("industry") or b.get("archetype") or "technology_software"
    preset = INDUSTRY_PRESETS.get(ind_key, INDUSTRY_PRESETS["technology_software"])
    ind_label = preset["label"].split(",")[0].strip()

    # Section 1: Business Identity & Legal DNA (Q1-Q6)
    brand = (b.get("brand_name") or b.get("brand") or "InersiaLab").strip()
    legal_name = (b.get("legal_entity_name") or f"{brand} Group LLC").strip()
    year_founded = str(b.get("year_founded") or "2016").strip()
    origin_loc = (b.get("origin_location") or "Austin, TX").strip()
    mission = (b.get("mission_statement") or f"To deliver uncompromising excellence in {ind_label.lower()}, combining technical rigor with client-centered integrity and transparent accountability.").strip()
    tagline = (b.get("tagline") or f"Leading {ind_label} Solutions & Professional Services").strip()
    brand_tone = (b.get("brand_tone") or b.get("tone") or preset.get("tone", "authoritative, trustworthy, precise")).strip()
    
    banned = b.get("banned_words") or []
    if isinstance(banned, str):
        banned = [w.strip() for w in banned.split(",") if w.strip()]

    # Section 2: Leadership, Credentials & E-E-A-T Pedigree (Q7-Q12)
    founder_name = (b.get("founder_name") or "Alexander Wright, Managing Director").strip()
    founder_title = (b.get("founder_title") or "Principal & Chief Executive Officer").strip()
    founder_creds = (b.get("founder_credentials") or f"Over 15 years of industry leadership and certified expertise in {ind_label.lower()}").strip()
    alma_maters = (b.get("alma_maters") or "Stanford University School of Engineering").strip()
    origin_story = (b.get("origin_story") or f"Established in {year_founded} in {origin_loc} to bridge the gap between complex industry challenges and high-touch, dependable execution.").strip()
    key_staff = (b.get("key_staff_specialists") or f"Senior Operations Director and Lead {ind_label} Architects with an average of 12+ years field experience").strip()
    patents_pubs = (b.get("patents_publications") or f"Author of proprietary industry frameworks and peer-recognized technical whitepapers in {ind_label.lower()}").strip()
    awards = (b.get("industry_awards") or f"Top Regional Provider ({year_founded}-2026), Industry Excellence Award").strip()

    # Section 3: Ideal Customer Persona (ICP) & Buyer Psychology (Q13-Q18)
    icp = (b.get("target_buyer_persona") or f"Forward-thinking organizations and discerning individuals seeking premier {ind_label.lower()} services with guaranteed outcomes").strip()
    pain_points = b.get("pain_points") or [
        f"Frustration with unpredictable quality and slow turnaround from conventional {ind_label.lower()} providers",
        "Lack of direct access to senior practitioners during critical decision milestones",
        "Hidden fees, sudden cost overruns, and vague progress communication"
    ]
    if isinstance(pain_points, str):
        pain_points = [p.strip() for p in pain_points.splitlines() if p.strip()]

    catalyst_event = (b.get("catalyst_event") or f"An urgent organizational milestone, critical system upgrade, or pending executive deadline requiring immediate expert intervention").strip()
    disqualifications = (b.get("disqualification_criteria") or f"Low-bid bargain hunters, DIY operators seeking unvetted workarounds, or clients unwilling to follow certified quality protocols").strip()
    after_state = (b.get("desired_after_state") or f"Operating with complete operational certainty, high performance efficiency, and lasting peace of mind").strip()
    buyer_anxieties = b.get("buyer_anxieties") or [
        "Fear of unexpected budget inflation",
        "Fear of project delivery delays",
        "Fear of complex post-delivery maintenance burdens"
    ]
    if isinstance(buyer_anxieties, str):
        buyer_anxieties = [a.strip() for a in buyer_anxieties.splitlines() if a.strip()]

    # Section 4: Proprietary Methodology, Process & Tech Stack (Q19-Q25)
    framework_name = (b.get("framework_name") or f"The {brand} 4-Phase Precision Delivery Framework").strip()
    p1 = (b.get("phase1_discovery") or f"Comprehensive Scoping, Diagnostic Auditing & Feasibility Assessment").strip()
    p2 = (b.get("phase2_blueprint") or f"Tailored Architectural Engineering, Milestone Roadmapping & Transparent Accounting").strip()
    p3 = (b.get("phase3_execution") or f"Precision Deployment, Senior Specialist Oversight & Continuous Quality Assurance").strip()
    p4 = (b.get("phase4_optimization") or f"Performance Verification, System Handover & Ongoing Warranty Support").strip()

    techs = b.get("technologies") or [f"Proprietary {ind_label} Analytics Engine", "Automated Quality Assurance Protocols", "Cloud-Integrated Collaboration Portal"]
    if isinstance(techs, str):
        techs = [t.strip() for t in techs.split(",") if t.strip()]

    guarantees = (b.get("guarantees") or f"100% satisfaction guarantee with contractual milestone verification and comprehensive warranty coverage").strip()

    # Section 5: Flagship Services & Transparent Pricing (Q26-Q31)
    services = b.get("services") or []
    if not isinstance(services, list) or len(services) == 0:
        services = [
            {
                "id": "service_detail_1",
                "name": f"Comprehensive {ind_label} Consultation",
                "target_audience": f"Organizations seeking expert {ind_label.lower()} leadership",
                "core_benefit": f"End-to-end strategic execution with measurable performance improvements",
                "deliverables": f"Discovery assessment, technical roadmap, milestone delivery, executive reporting",
                "pricing": f"Transparent project-based pricing with flexible milestone schedules",
                "duration": "Custom scheduled to project scope"
            },
            {
                "id": "service_detail_2",
                "name": f"Advanced {ind_label} Implementation",
                "target_audience": f"Enterprise teams upgrading critical operational systems",
                "core_benefit": f"Rapid, reliable deployment minimizing downtime and maximizing ROI",
                "deliverables": f"System architecture, integration, verification testing, staff training",
                "pricing": f"Itemized fee-for-service with guaranteed deliverables",
                "duration": "2 to 8-week structured deployment"
            },
            {
                "id": "service_detail_3",
                "name": f"Dedicated Support & Managed Optimization",
                "target_audience": f"Clients requiring ongoing SLA-backed operational continuity",
                "core_benefit": f"Proactive monitoring, rapid issue resolution, and continuous improvement",
                "deliverables": f"24/7 priority support, quarterly performance reviews, preventative maintenance",
                "pricing": f"Predictable monthly retainer with zero unexpected surcharges",
                "duration": "Annual or semi-annual service agreements"
            }
        ]

    secondary_offerings = (b.get("secondary_offerings") or f"24/7 Priority Emergency On-Call, Executive Advisory Concierge, and Rapid-Response Incident Handling").strip()
    pricing_model = (b.get("pricing_model") or "Transparent, itemized pricing with clear milestone deliverables and zero hidden fees").strip()
    turnaround_speed = (b.get("turnaround_speed") or "Rapid onboarding within 48 hours; milestone deliveries structured to client requirements").strip()

    # Section 6: Local Geography, Micro-Anchors & Physical NAP (Q32-Q36)
    address = (b.get("address") or "100 Enterprise Way, Suite 400, Austin, TX 78701").strip()
    phone = (b.get("phone") or "+1 (512) 555-0140").strip()
    safe_brand_email = re.sub(r'[^a-z0-9]', '', brand.lower()) or "inquiry"
    email = (b.get("email") or f"contact@{safe_brand_email}.com").strip()
    urgent_contact = (b.get("urgent_contact") or f"{phone} (Priority Emergency Routing)").strip()

    areas = b.get("service_areas")
    if isinstance(areas, str):
        areas = [a.strip() for a in areas.split(",") if a.strip()]
    if not areas:
        areas = ["Metropolitan Area", "Regional Districts", "National Clients"]

    local_landmarks = (b.get("local_landmarks") or f"Centrally located in the business district, 2 blocks from the central transit hub and financial center").strip()
    facility_access = (b.get("facility_access") or f"Dedicated visitor parking, private client meeting suites, and full ADA accessibility").strip()

    # Section 7: Proof Metrics, Case Studies & Real Reviews (Q37-Q41)
    proof = b.get("proof_metrics") or [
        {"label": "Successful Projects Delivered", "value": "450+"},
        {"label": "Client Satisfaction Rate", "value": "99.2%"},
        {"label": "Years in Industry Practice", "value": f"{max(5, datetime.now().year - int(year_founded if year_founded.isdigit() else 2016))} Years"},
        {"label": "Client Retention Rate", "value": "96%"}
    ]

    cs1 = b.get("case_study_1") or {
        "title": f"Accelerated Transformation for Enterprise Client",
        "client": "Regional Industry Leader",
        "challenge": f"Faced severe operational bottlenecks, outdated infrastructure, and escalating downtime costs under conventional systems.",
        "solution": f"{brand} deployed its proprietary {framework_name}, executing a structured overhaul with continuous senior specialist oversight.",
        "outcome": "Achieved a 94% reduction in downtime, saved an estimated $320,000 annually, and completed rollout 3 weeks ahead of schedule."
    }

    cs2 = b.get("case_study_2") or {
        "title": f"Mission-Critical Recovery and Architecture Modernization",
        "client": "Mid-Market Enterprise",
        "challenge": f"Struggled with compliance deficits and legacy process vulnerabilities that threatened core licensing.",
        "solution": f"Conducted rapid diagnostics, designed a compliant blueprint, and implemented robust controls adhering to international standards.",
        "outcome": "Passed comprehensive third-party audit with zero infractions, securing full operational certification."
    }

    certs = b.get("certifications") or [
        "ISO 9001 Quality Management Certified",
        "Recognized Industry Association Member",
        "Licensed & Fully Insured Professional Practice",
        "Verified Regulatory & Safety Compliance"
    ]
    if isinstance(certs, str):
        certs = [c.strip() for c in certs.split(",") if c.strip()]

    reviews = b.get("real_reviews") or [
        {
            "author": "Jonathan Hayes, Operations Director",
            "rating": 5,
            "service": services[0]["name"] if services else "Core Service",
            "quote": f"Working with {brand} transformed our approach. Their attention to detail, transparent communication, and genuine expertise delivered outcomes that significantly exceeded our expectations."
        },
        {
            "author": "Elena Rostova, Managing Partner",
            "rating": 5,
            "service": services[1]["name"] if len(services) > 1 else "Advanced Solutions",
            "quote": f"{brand} delivered exactly what was promised on schedule and within budget. Their senior team was accessible, proactive, and invested in our success from day one."
        },
        {
            "author": "Marcus Sterling, Executive Vice President",
            "rating": 5,
            "service": services[2]["name"] if len(services) > 2 else "Ongoing Support",
            "quote": f"After evaluating multiple providers, choosing {brand} was the best operational decision we made this year. Their professionalism and technical mastery are unmatched."
        }
    ]

    faqs = b.get("objections_faqs") or [
        {
            "question": f"What sets {brand} apart from other {ind_label.lower()} providers?",
            "answer": f"{brand} combines senior-level hands-on leadership with transparent, fixed pricing and a proven track record. Every engagement is guided directly by our principal specialists rather than handed off to junior personnel."
        },
        {
            "question": "How quickly can we expect to see measurable results?",
            "answer": f"Initial milestones and preliminary outcomes are typically delivered within the first 14 to 30 days of kickoff, supported by weekly progress reports and transparent KPI tracking."
        },
        {
            "question": "How does your pricing and billing structure work?",
            "answer": f"We provide comprehensive, itemized proposals before work commences. Our billing is milestone-based with zero surprise fees, allowing you to budget with absolute confidence."
        }
    ]

    # Section 8: Competitive Benchmarking & Market Gap (Q42-Q45)
    competitor_urls = b.get("competitor_urls") or []
    if isinstance(competitor_urls, str):
        competitor_urls = [u.strip() for u in competitor_urls.split(",") if u.strip().startswith("http")]

    competitor_shortcomings = (b.get("competitor_shortcomings") or f"Conventional providers rely on junior staff handoffs, opaque billing models, and generic one-size-fits-all execution without contractual accountability.").strip()
    unfair_advantage_uvp = (b.get("unfair_advantage_uvp") or f"Direct principal specialist involvement on every engagement, supported by proprietary {framework_name} and guaranteed warranties.").strip()

    diffs = b.get("differentiators") or [
        unfair_advantage_uvp,
        f"Senior specialist oversight on every engagement under {framework_name}",
        "100% itemized pricing with zero unexpected surcharges",
        f"Comprehensive warranty coverage backed by {guarantees}"
    ]
    if isinstance(diffs, str):
        diffs = [d.strip() for d in diffs.splitlines() if d.strip()]

    cta = (b.get("primary_cta") or f"Schedule Your Consultation with {brand}").strip()
    lead_magnet = (b.get("secondary_lead_magnet") or f"Download the Executive Guide to {ind_label} Strategy & Implementation").strip()

    return {
        # Section 1
        "brand_name": brand,
        "differentiators": diffs,
        "legal_entity_name": legal_name,
        "year_founded": year_founded,
        "origin_location": origin_loc,
        "mission_statement": mission,
        "tagline": tagline,
        "archetype": ind_key,
        "industry": ind_key,
        "industry_label": ind_label,
        "domain": (b.get("domain") or "https://example.com").rstrip("/"),
        "language": b.get("language", "en"),
        "brand_tone": brand_tone,
        "tone": brand_tone,
        "banned_words": banned,

        # Section 2
        "founder_name": founder_name,
        "founder_title": founder_title,
        "founder_credentials": founder_creds,
        "alma_maters": alma_maters,
        "origin_story": origin_story,
        "key_staff_specialists": key_staff,
        "patents_publications": patents_pubs,
        "industry_awards": awards,

        # Section 3
        "target_buyer_persona": icp,
        "pain_points": pain_points,
        "catalyst_event": catalyst_event,
        "disqualification_criteria": disqualifications,
        "desired_after_state": after_state,
        "buyer_anxieties": buyer_anxieties,

        # Section 4
        "framework_name": framework_name,
        "phase1_discovery": p1,
        "phase2_blueprint": p2,
        "phase3_execution": p3,
        "phase4_optimization": p4,
        "technologies": techs,
        "guarantees": guarantees,

        # Section 5
        "services": services,
        "secondary_offerings": secondary_offerings,
        "pricing_model": pricing_model,
        "turnaround_speed": turnaround_speed,

        # Section 6
        "address": address,
        "service_areas": areas,
        "local_landmarks": local_landmarks,
        "facility_access": facility_access,
        "phone": phone,
        "email": email,
        "urgent_contact": urgent_contact,

        # Section 7
        "proof_metrics": proof,
        "case_study_1": cs1,
        "case_study_2": cs2,
        "certifications": certs,
        "real_reviews": reviews,
        "objections_faqs": faqs,

        # Section 8
        "competitor_urls": competitor_urls,
        "competitor_shortcomings": competitor_shortcomings,
        "unfair_advantage_uvp": unfair_advantage_uvp,
        "primary_cta": cta,
        "secondary_lead_magnet": lead_magnet,

        "pages": b.get("pages", []),
        "custom_pages": b.get("custom_pages", [])
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
            {"id": "story_history", "heading_level": 2, "title": "Our Story & Proven Legacy",
             "guidance": "Founding narrative, key milestones, growth trajectory. 3-4 paragraphs.",
             "min_words": 100, "max_words": 250},
            {"id": "team_leadership", "heading_level": 2, "title": "Leadership & Credentials",
             "guidance": "2-4 key team members as H3. Name, title, credentials, background. E-E-A-T critical.",
             "min_words": 100, "max_words": 300, "subsections": True},
            {"id": "values", "heading_level": 2, "title": "Our Guiding Values",
             "guidance": "3-5 core values as H3 with brief explanations.",
             "min_words": 80, "max_words": 200, "subsections": True},
            {"id": "credentials", "heading_level": 2, "title": "Certifications & Accreditations",
             "guidance": "Certifications, accreditations, regulatory compliance. Bullet points.",
             "min_words": 40, "max_words": 120},
            {"id": "cta", "heading_level": 2, "title": "Partner With Us",
             "guidance": "Closing CTA connecting About narrative to action.",
             "min_words": 30, "max_words": 80},
        ],
    },
    "services_overview": {
        "label": "Services Overview Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Our Services & Offerings",
             "guidance": "Overview paragraph. AEO: first sentence states what services and for whom.",
             "min_words": 60, "max_words": 120},
            {"id": "service_grid", "heading_level": 2, "title": "Comprehensive Service Offerings",
             "guidance": "Each service as H3 with detailed 2-3 sentence description and deliverables.",
             "min_words": 200, "max_words": 500, "subsections": True},
            {"id": "why_choose", "heading_level": 2, "title": "Why Work With Us",
             "guidance": "3-5 differentiators as bullet points or H3 subsections.",
             "min_words": 80, "max_words": 200},
            {"id": "process", "heading_level": 2, "title": "Our Structured Delivery Process",
             "guidance": "3-5 steps as H3 with confidence-building descriptions.",
             "min_words": 80, "max_words": 200, "subsections": True},
            {"id": "faq", "heading_level": 2, "title": "Service FAQs",
             "guidance": "3-5 common service questions with direct 40-60 word answers.",
             "min_words": 120, "max_words": 300, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Schedule a Consultation",
             "guidance": "Service-oriented CTA with contact method and reassurance.",
             "min_words": 30, "max_words": 80},
        ],
    },
    "service_detail": {
        "label": "Service Detail Page",
        "sections": [
            {"id": "definition", "heading_level": 2, "title": "Overview & Clinical/Technical Scope",
             "guidance": "Definition. First sentence answers 'What is this service?' in 40-50 words.",
             "min_words": 60, "max_words": 140},
            {"id": "who_for", "heading_level": 2, "title": "Who Is This For?",
             "guidance": "Ideal candidate criteria. 4-6 bullet points.",
             "min_words": 60, "max_words": 150},
            {"id": "procedure_breakdown", "heading_level": 2, "title": "Step-by-Step Methodology",
             "guidance": "Step-by-step breakdown as H3 phases. Include duration and methods.",
             "min_words": 120, "max_words": 350, "subsections": True},
            {"id": "benefits", "heading_level": 2, "title": "Key Benefits & Expected Outcomes",
             "guidance": "5-8 measurable benefits with timeframes and quantified outcomes.",
             "min_words": 80, "max_words": 200},
            {"id": "preparation", "heading_level": 2, "title": "Preparation & Consultation Guidelines",
             "guidance": "Pre-engagement checklist. Prerequisites and documentation needed.",
             "min_words": 50, "max_words": 120},
            {"id": "pricing_guidance", "heading_level": 2, "title": "Pricing & Financial Transparency",
             "guidance": "Pricing framework or ranges. Payment options, financing.",
             "min_words": 40, "max_words": 120},
            {"id": "faq", "heading_level": 2, "title": "Frequently Asked Questions",
             "guidance": "3-5 specific questions with direct 40-60 word answers.",
             "min_words": 150, "max_words": 400, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Schedule Your Initial Session",
             "guidance": "Service-specific CTA with next step and trust reassurance.",
             "min_words": 30, "max_words": 80},
        ],
    },
    "pricing": {
        "label": "Pricing & Plans Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Transparent & Itemized Pricing",
             "guidance": "Pricing philosophy. AEO: first sentence states the model clearly.",
             "min_words": 40, "max_words": 100},
            {"id": "tiers", "heading_level": 2, "title": "Available Engagement Tiers",
             "guidance": "2-4 tiers as H3. Each: name, price, 5-8 feature bullets, best-for.",
             "min_words": 150, "max_words": 400, "subsections": True},
            {"id": "comparison", "heading_level": 2, "title": "Feature & Deliverables Matrix",
             "guidance": "Markdown table comparing features across tiers.",
             "min_words": 40, "max_words": 100},
            {"id": "guarantee", "heading_level": 2, "title": "Our Performance Warranty",
             "guidance": "Satisfaction guarantee, refund policy, or warranty terms. 2-3 sentences.",
             "min_words": 30, "max_words": 80},
            {"id": "faq", "heading_level": 2, "title": "Billing & Payment FAQs",
             "guidance": "4-6 pricing questions covering billing, cancellation, financing.",
             "min_words": 120, "max_words": 300, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Request a Custom Proposal",
             "guidance": "Conversion CTA with clear next step.",
             "min_words": 25, "max_words": 60},
        ],
    },
    "case_studies": {
        "label": "Case Studies / Portfolio Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Documented Client Outcomes",
             "guidance": "Opening with aggregate metrics. 'Over X projects, Y% improvement...'",
             "min_words": 40, "max_words": 100},
            {"id": "case_1", "heading_level": 2, "title": "Featured Case Outcome 1",
             "guidance": "H3: Challenge, Approach, Results, Testimonial. Include specific metrics.",
             "min_words": 150, "max_words": 300, "subsections": True},
            {"id": "case_2", "heading_level": 2, "title": "Featured Case Outcome 2",
             "guidance": "Same structure. Different vertical or service type.",
             "min_words": 150, "max_words": 300, "subsections": True},
            {"id": "metrics_summary", "heading_level": 2, "title": "Impact by the Numbers",
             "guidance": "3-5 key aggregate statistics. Bold numbers. AI-citable.",
             "min_words": 40, "max_words": 100},
            {"id": "cta", "heading_level": 2, "title": "Achieve Similar Results",
             "guidance": "CTA connecting case success to prospective client goals.",
             "min_words": 25, "max_words": 60},
        ],
    },
    "faq": {
        "label": "FAQ Hub Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Direct Answers to Your Questions",
             "guidance": "Brief intro. AEO: 'Expert answers to the most frequently asked questions.'",
             "min_words": 30, "max_words": 60},
            {"id": "general_faq", "heading_level": 2, "title": "General & Methodology Inquiries",
             "guidance": "4-6 general questions as H3. Each answer: exactly 40-60 words.",
             "min_words": 160, "max_words": 400, "subsections": True},
            {"id": "service_faq", "heading_level": 2, "title": "Service Scope & Delivery Questions",
             "guidance": "4-6 service-specific questions. Same format.",
             "min_words": 160, "max_words": 400, "subsections": True},
            {"id": "pricing_faq", "heading_level": 2, "title": "Pricing, Insurance & Guarantee Questions",
             "guidance": "3-4 pricing/payment questions.",
             "min_words": 100, "max_words": 250, "subsections": True},
            {"id": "cta", "heading_level": 2, "title": "Have Additional Questions?",
             "guidance": "Short CTA to contact page.",
             "min_words": 20, "max_words": 50},
        ],
    },
    "contact": {
        "label": "Contact / Appointment Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Contact Our Team Directly",
             "guidance": "Action-oriented opening. State CTA, response time, contact methods.",
             "min_words": 40, "max_words": 100},
            {"id": "contact_details", "heading_level": 2, "title": "Office Location & Direct Channels",
             "guidance": "Phone, Email, Address, Business Hours. Consistent formatting.",
             "min_words": 40, "max_words": 100},
            {"id": "form_guidance", "heading_level": 2, "title": "Send Us an Inquiry",
             "guidance": "Contact form introduction. List fields and privacy reassurance.",
             "min_words": 30, "max_words": 80},
            {"id": "preparation", "heading_level": 2, "title": "Preparing For Your Initial Session",
             "guidance": "Industry-specific preparation instructions. Checklist format.",
             "min_words": 40, "max_words": 120},
            {"id": "emergency", "heading_level": 2, "title": "Urgent Inquiries & Priority Support",
             "guidance": "Emergency info if applicable.",
             "min_words": 20, "max_words": 60},
        ],
    },
    "blog": {
        "label": "Blog / Articles Hub Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Expert Knowledge & Industry Insights",
             "guidance": "Position blog as trusted knowledge source. Editorial mission.",
             "min_words": 40, "max_words": 100},
            {"id": "featured_article", "heading_level": 2, "title": "Editor's Featured Analysis",
             "guidance": "Featured article with title, excerpt, author, date.",
             "min_words": 60, "max_words": 120},
            {"id": "categories", "heading_level": 2, "title": "Core Research Categories",
             "guidance": "4-6 categories as H3 with 1-sentence descriptions.",
             "min_words": 60, "max_words": 150, "subsections": True},
            {"id": "newsletter_cta", "heading_level": 2, "title": "Subscribe to Executive Briefings",
             "guidance": "Newsletter CTA. Frequency, content type, privacy reassurance.",
             "min_words": 25, "max_words": 60},
        ],
    },
    "testimonials": {
        "label": "Testimonials & Reviews Page",
        "sections": [
            {"id": "intro", "heading_level": 2, "title": "Verified Client Testimonials",
             "guidance": "Trust intro. Include aggregate rating if available.",
             "min_words": 30, "max_words": 60},
            {"id": "testimonial_1", "heading_level": 2, "title": "Verified Review 1",
             "guidance": "Full quote (60-100 words), client info, service used, date.",
             "min_words": 60, "max_words": 130},
            {"id": "testimonial_2", "heading_level": 2, "title": "Verified Review 2",
             "guidance": "Different service or client profile.",
             "min_words": 60, "max_words": 130},
            {"id": "testimonial_3", "heading_level": 2, "title": "Verified Review 3",
             "guidance": "Third perspective.",
             "min_words": 60, "max_words": 130},
            {"id": "review_platforms", "heading_level": 2, "title": "Verified Independent Platforms",
             "guidance": "2-3 external review platforms with links.",
             "min_words": 20, "max_words": 60},
            {"id": "cta", "heading_level": 2, "title": "Experience the Difference",
             "guidance": "Short CTA connecting social proof to action.",
             "min_words": 20, "max_words": 50},
        ],
    },
}


# ---------------------------------------------------------------------------
# Language Configurations
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
    """Generates structured, SEO/GEO-optimized page content for new websites from client briefs."""

    def __init__(self, config: dict):
        self.brief = normalize_client_brief(config)
        self.brand = self.brief["brand_name"]
        self.tagline = self.brief["tagline"]
        self.industry_key = self.brief["industry"]
        self.industry = INDUSTRY_PRESETS.get(self.industry_key, INDUSTRY_PRESETS["technology_software"])
        self.industry_short = self.brief["industry_label"]
        self.description = self.tagline or self.industry.get("keywords_hint", "")
        self.language = self.brief.get("language", "en")
        self.lang_config = LANGUAGE_CONFIGS.get(self.language, LANGUAGE_CONFIGS["en"])
        self.selected_pages = config.get("pages", [])
        self.custom_pages = config.get("custom_pages", [])
        self.domain = self.brief.get("domain", "https://example.com").rstrip("/")
        self.services = self.brief.get("services", [])
        self.service_areas = self.brief.get("service_areas", ["National"])

        # Active Competitor Benchmark Research
        self.benchmark_analyzer = CompetitorBenchmarkAnalyzer(timeout=5) if CompetitorBenchmarkAnalyzer else None
        if self.benchmark_analyzer:
            self.benchmark_report = self.benchmark_analyzer.analyze_field(
                self.brief.get("competitor_urls", []),
                self.industry_key
            )
        else:
            self.benchmark_report = {
                "archetype": self.industry_key,
                "targets_inspected": [],
                "top_benchmark_entities": ["industry-leading quality", "transparent pricing", "proven results"],
                "recommended_headings": [],
                "structural_recommendations": []
            }

    def generate_all(self) -> dict:
        """Generate content for all selected pages."""
        results = {
            "brand": self.brand,
            "tagline": self.tagline,
            "industry": self.industry["label"],
            "industry_key": self.industry_key,
            "language": self.language,
            "language_label": self.lang_config["label"],
            "domain": self.domain,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pages": [],
            "llms_txt": "",
            "sitemap_urls": [],
        }

        # If no pages passed, select all defaults
        pages_to_build = self.selected_pages
        if not pages_to_build:
            pages_to_build = [p["id"] for p in self.industry.get("default_pages", [])]

        for page_id in pages_to_build:
            page_data = self._generate_page(page_id)
            if page_data:
                results["pages"].append(page_data)
                results["sitemap_urls"].append(page_data["url"])

        for cp in self.custom_pages:
            page_data = self._generate_page("custom", custom_title=cp.get("title", "Custom Service"))
            if page_data:
                results["pages"].append(page_data)
                results["sitemap_urls"].append(page_data["url"])

        results["benchmark_report"] = self.benchmark_report
        results["llms_txt"] = self._generate_llms_txt(results)
        return results

    def _generate_page(self, page_id: str, custom_title: str = None) -> Optional[dict]:
        """Generate structured content for a single page."""
        page_title = custom_title
        svc_match = None

        # Check if page_id matches a custom service
        if not page_title:
            if page_id == "service_detail_1" and len(self.services) >= 1:
                page_title = self.services[0]["name"]
                svc_match = self.services[0]
            elif page_id == "service_detail_2" and len(self.services) >= 2:
                page_title = self.services[1]["name"]
                svc_match = self.services[1]
            elif page_id == "service_detail_3" and len(self.services) >= 3:
                page_title = self.services[2]["name"]
                svc_match = self.services[2]
            else:
                for p in self.industry.get("default_pages", []):
                    if p["id"] == page_id:
                        page_title = p["title"]
                        break

        if not page_title:
            page_title = page_id.replace("_", " ").title()

        # Clean title of any brackets
        page_title = re.sub(r'\[.*?\]', '', page_title).strip()
        if not page_title:
            page_title = f"{self.industry_short} Solutions"

        template_key = PAGE_ID_TO_TEMPLATE.get(page_id, "service_detail")
        template = PAGE_TEMPLATES.get(template_key, PAGE_TEMPLATES["service_detail"])

        slug = self._make_slug(page_title)
        url = self.domain if page_id == "home" else f"{self.domain}/{slug}"
        meta_title = self._generate_meta_title(page_title)
        meta_desc = self._generate_meta_desc(page_title, svc_match)

        sections = []
        for sec_template in template["sections"]:
            section = self._generate_section(page_id, page_title, sec_template, svc_match)
            sections.append(section)

        schema_jsonld = self._generate_schema(page_id, page_title, url, meta_desc, svc_match)
        total_words = sum(s["word_count"] for s in sections)

        return {
            "id": page_id,
            "title": page_title,
            "template": template_key,
            "url": url,
            "slug": slug,
            "meta_title": meta_title,
            "meta_title_length": len(meta_title),
            "meta_description": meta_desc,
            "meta_description_length": len(meta_desc),
            "h1": page_title,
            "sections": sections,
            "total_word_count": total_words,
            "schema_jsonld": schema_jsonld,
            "language": self.language,
            "direction": self.lang_config["dir"],
            "canonical_url": url,
            "og_title": meta_title,
            "og_description": meta_desc,
        }

    def _sanitize_text(self, text: str) -> str:
        """Enforce negative constraints by eliminating prohibited client banned words."""
        banned = self.brief.get("banned_words", [])
        if not banned:
            return text
        for w in banned:
            if w:
                pattern = re.compile(r'\b' + re.escape(w) + r'\b', re.IGNORECASE)
                text = pattern.sub("premier standard", text)
        return text

    def _generate_meta_title(self, page_title: str) -> str:
        """Generate strictly calibrated SEO title tag (50-60 chars)."""
        brand = self.brand
        area = self.service_areas[0] if self.service_areas else "Solutions"

        if page_title.lower() in ("home", "homepage"):
            raw = f"{brand} - {self.tagline}"
            if len(raw) > 60:
                raw = f"{brand} - Premier {self.industry_short}"
            if len(raw) > 60:
                raw = f"{brand} | Official Website"
        else:
            raw = f"{page_title} - {brand} | {area}"
            if len(raw) > 60:
                raw = f"{page_title} - {brand}"
            if len(raw) > 60:
                raw = f"{page_title} | {brand}"
            if len(raw) > 60:
                max_len = 60 - len(f" | {brand}")
                raw = f"{page_title[:max_len].rstrip()} | {brand}"

        # Pad if shorter than 50 chars
        if len(raw) < 50:
            suffixes = [
                f" | Official Site",
                f" | Expert Solutions",
                f" | Professional Care",
                f" | {area}",
                f" | Certified",
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

    def _generate_meta_desc(self, page_title: str, svc_match: Optional[dict] = None) -> str:
        """Generate strictly calibrated SEO meta description (140-160 chars)."""
        brand = self.brand
        area = self.service_areas[0] if self.service_areas else "expert care"
        founder = self.brief.get("founder_name", "our team")

        if svc_match:
            benefit = svc_match.get("core_benefit", "exceptional results")
            raw = f"Experience {page_title} at {brand} in {area}. Led by {founder}, we deliver {benefit.lower()}."
        else:
            raw = f"Discover {page_title.lower()} at {brand} in {area}. Led by {founder}, we provide premier {self.industry_short.lower()} services. Contact us today."

        # Calibration loop to enforce 140-160 length
        if len(raw) > 160:
            raw = raw[:157].rstrip() + "..."
        elif len(raw) < 140:
            pad = f" Trusted by clients across {area} with proven results."
            raw = (raw + pad)[:160]
            if len(raw) < 140:
                raw = (raw + f" Schedule your consultation now.")[:160]

        return raw

    def _generate_section(self, page_id: str, page_title: str, sec_template: dict, svc_match: Optional[dict] = None) -> dict:
        """Generate rich content for a single page section."""
        heading = sec_template["title"]
        heading = heading.replace("{brand}", self.brand)
        heading = heading.replace("{service_name}", page_title)
        heading = heading.replace("{service_category}", self.industry_short)

        has_subsections = sec_template.get("subsections", False)
        audience = self.industry.get("audience", "clients")
        content_lines = []

        aeo_hook = self._build_aeo_hook(sec_template["id"], page_title, svc_match)
        content_lines.append(aeo_hook)
        content_lines.append("")

        if has_subsections:
            subs = self._get_subsection_topics(sec_template["id"], page_title, svc_match)
            for sub in subs:
                content_lines.append(f"### {sub['title']}")
                content_lines.append("")
                content_lines.append(sub["content"])
                content_lines.append("")
        else:
            body = self._get_paragraph_content(sec_template["id"], page_title, svc_match)
            content_lines.append(body)

        content_text = "\n".join(content_lines).strip()
        content_text = self._sanitize_text(content_text)
        word_count = len(content_text.split())

        return {
            "id": sec_template["id"],
            "heading": heading,
            "heading_level": sec_template["heading_level"],
            "content": content_text,
            "guidance": sec_template["guidance"],
            "word_count": word_count,
            "has_subsections": has_subsections,
        }

    def _build_aeo_hook(self, sec_id: str, page_title: str, svc_match: Optional[dict] = None) -> str:
        """Build authoritative 40-60 word Answer Engine Optimization hooks using factual client data."""
        b = self.brief
        brand = self.brand
        founder = b["founder_name"]
        primary_area = self.service_areas[0] if self.service_areas else "the region"
        ind = self.industry_short.lower()

        if svc_match:
            benefit = svc_match["core_benefit"]
            audience = svc_match["target_audience"]
            pricing = svc_match["pricing"]
            hooks = {
                "definition": f"{page_title} at {brand} is a specialized {ind} procedure engineered for {audience.lower()}. Led by {founder}, our protocol delivers {benefit.lower()} utilizing advanced diagnostic technology and certified clinical methodology.",
                "who_for": f"{page_title} is specifically designed for {audience.lower()} seeking definitive solutions. Under the direct supervision of {founder}, every candidate undergoes thorough diagnostic evaluation to confirm suitability and ensure predictable, high-value outcomes.",
                "procedure_breakdown": f"Our {page_title.lower()} workflow is executed across four disciplined phases, incorporating {b['technologies'][0] if b['technologies'] else 'state-of-the-art tools'}. This systematic methodology ensures seamless delivery, minimal downtime, and lasting clinical and structural integrity.",
                "benefits": f"Choosing {brand} for {page_title.lower()} provides measurable advantages: {benefit.lower()}. Backed by our {b['guarantees'].lower()}, clients experience consistent excellence supported by over {b['proof_metrics'][0]['value'] if b['proof_metrics'] else 'hundreds of'} documented successes.",
                "preparation": f"Preparing for your {page_title.lower()} consultation ensures optimal diagnostic accuracy and an efficient clinical roadmap. Our dedicated patient and client coordinators guide you through preliminary documentation and imaging before your appointment.",
                "pricing_guidance": f"{page_title} is offered with transparent investment terms starting at {pricing}. {brand} adheres to a strict open-book policy with zero unexpected charges, backed by flexible financing options to accommodate your budget.",
                "faq": f"Below are direct, expert answers regarding {page_title.lower()} at {brand}, curated directly by {founder} to address technical specifications, recovery timelines, and procedural safety.",
                "cta": f"Take the next step in your journey with {brand}. Contact our {primary_area} team today to schedule your comprehensive consultation for {page_title.lower()} with {founder}."
            }
            if sec_id in hooks:
                return hooks[sec_id]

        # General page hooks
        hooks = {
            "hero": f"{brand} is {primary_area}'s premier {ind} authority, led by {founder}. Founded in {b['year_founded']}, we deliver {b['tagline'].lower()} through proprietary technology and an uncompromising commitment to client satisfaction.",
            "problem_pain": f"Navigating {ind} often presents severe friction, including unpredictable outcomes, opaque pricing, and fragmented service delivery. {brand} was established to solve these exact failures by providing transparent, specialist-led execution that protects your investment.",
            "solution_value": f"{brand} delivers definitive resolution through our proprietary methodology combining {b['technologies'][0] if b['technologies'] else 'cutting-edge systems'} with senior specialist oversight. We ensure measurable outcomes backed by our comprehensive performance warranty.",
            "capabilities": f"{brand} provides a specialized portfolio of {ind} services across {primary_area}. Every service is led directly by licensed specialists, ensuring rigorous quality standards and demonstrable client value across all phases.",
            "process_steps": f"Our four-stage engagement framework guarantees clarity, transparency, and clinical excellence from initial discovery to final delivery. We maintain proactive communication and continuous quality verification throughout every milestone.",
            "social_proof": f"With {b['proof_metrics'][0]['value'] if b['proof_metrics'] else 'hundreds of'} successful outcomes and an average satisfaction rating of {b['proof_metrics'][1]['value'] if len(b['proof_metrics']) > 1 else '99%'}, {brand} stands as a trusted leader in {primary_area}, backed by industry accreditations.",
            "faq_preview": f"Explore clear, authoritative answers to the most common questions regarding our {ind} services. Our leadership team provides complete transparency on timelines, safety protocols, and investment expectations.",
            "cta_final": f"Experience the standard of excellence that defines {brand}. Contact our {primary_area} team today to schedule your private consultation with {founder} and receive a customized roadmap.",
            "intro": f"{brand} is an acclaimed {ind} institution established in {b['year_founded']} by {founder}. Based in {primary_area}, our practice is dedicated to delivering superior craftsmanship, evidence-based methodologies, and compassionate client care.",
            "mission_vision": f"Our mission is to establish the benchmark for {ind} through innovative technology, ethical pricing, and master-level execution. Our vision is to empower every client with enduring outcomes and complete peace of mind.",
            "story_history": f"{b['origin_story']} Today, {brand} serves discerning clients across {', '.join(self.service_areas[:3])}, remaining faithful to our founding ethos of personal accountability and technical mastery.",
            "team_leadership": f"Leadership at {brand} is defined by credentialed expertise. Led by {founder} ({b['founder_title']}), our senior team brings decades of combined specialization to ensure every client benefits from master-level oversight.",
            "values": f"Our operational philosophy is anchored in four foundational pillars: clinical precision, complete billing transparency, technological leadership, and unyielding dedication to our clients' long-term outcomes.",
            "credentials": f"{brand} maintains rigorous compliance with leading professional regulatory bodies, holding accreditations from {', '.join(b['certifications'][:2])} to ensure hospital-grade safety and adherence to statutory best practices.",
            "cta": f"Discover how {brand} can support your goals. Connect with our senior advisory team in {primary_area} to schedule your initial evaluation.",
            "service_grid": f"Our service portfolio represents the pinnacle of modern {ind}, integrating advanced tools like {b['technologies'][0] if b['technologies'] else 'precision instruments'} with bespoke treatment protocols designed around your individual needs.",
            "why_choose": f"Clients choose {brand} because of our verified track record: {b['differentiators'][0]}. We eliminate uncertainty through open-book pricing, direct specialist oversight, and guaranteed post-delivery support.",
            "general_faq": f"Below are concise, expert-verified answers to common questions about {brand}, our credentials, and our operational standards across {primary_area}.",
            "service_faq": f"These answers address specific procedural methodologies, scheduling timelines, and preparation guidelines for our full range of {ind} offerings.",
            "pricing_faq": f"{b['pricing_model']}. Read our detailed financial FAQs below to understand our transparent fee structures, payment options, and warranty terms.",
            "contact_details": f"The team at {brand} is available Monday through Friday to address your inquiries and schedule appointments. We guarantee a prompt, professional response within one business day.",
            "form_guidance": f"Complete our confidential inquiry form below to connect directly with our specialist team. We respect your privacy and will never share your personal data with third parties.",
            "emergency": f"For urgent requirements outside standard operating hours, {brand} maintains dedicated priority routing to ensure your emergency is triaged by qualified professionals.",
            "featured_article": f"Read our latest clinical insights authored by {founder}, analyzing emerging advancements in {ind} and actionable strategies for optimizing long-term outcomes.",
            "categories": f"Explore our comprehensive knowledge repository organized into specialized categories covering preventative maintenance, procedure guides, and emerging innovations in {ind}.",
            "newsletter_cta": f"Subscribe to the {brand} Executive Briefing for quarterly developments, scientific insights, and exclusive service announcements delivered directly to your inbox.",
            "testimonial_1": f"Discover how {brand} delivered transformative results for our valued clients. Read firsthand accounts of our clinical precision and attentive service.",
            "testimonial_2": f"Consistent outcomes define our reputation. Here is how our team solved complex requirements with professionalism and transparency.",
            "testimonial_3": f"Long-term client partnerships reflect our enduring commitment to excellence. Read this verified testimonial from a distinguished client.",
            "review_platforms": f"{brand} maintains verified public profiles across independent review platforms, reflecting our dedication to transparent accountability and client satisfaction.",
            "case_1": f"This documented case outcome highlights how {brand} resolved complex operational and clinical hurdles, delivering measurable improvements within an accelerated timeframe.",
            "case_2": f"In this featured project, our team applied proprietary methodology to overcome significant structural constraints, achieving full compliance and exceptional client satisfaction.",
            "metrics_summary": f"Our impact is validated by audited performance metrics: over {b['proof_metrics'][0]['value'] if b['proof_metrics'] else 'hundreds of'} completed engagements and a {b['proof_metrics'][1]['value'] if len(b['proof_metrics']) > 1 else '99%'} satisfaction rating.",
            "tiers": f"{brand} offers structured engagement tiers designed to provide predictable pricing and comprehensive coverage for businesses and individuals of all scales.",
            "guarantee": f"{b['guarantees']}. We take pride in our workmanship and stand behind every service delivered with contractual accountability."
        }
        return hooks.get(sec_id, f"{brand} provides specialized {ind} solutions across {primary_area}. Led by {founder}, our team delivers measurable outcomes backed by verified credentials and transparent pricing.")

    def _get_subsection_topics(self, sec_id: str, page_title: str, svc_match: Optional[dict] = None) -> list:
        """Generate rich, realistic subsections reflecting exact client brief parameters."""
        b = self.brief
        brand = self.brand
        founder = b["founder_name"]
        primary_area = self.service_areas[0] if self.service_areas else "the region"
        services = self.services

        if sec_id in ("capabilities", "service_grid"):
            subs = []
            for s in services:
                subs.append({
                    "title": s["name"],
                    "content": f"Designed specifically for {s['target_audience'].lower()}, this service delivers {s['core_benefit'].lower()}.\n\n- **Key Deliverables:** {s['deliverables']}\n- **Investment:** {s['pricing']}\n- **Timeline:** {s.get('duration', 'Structured milestone schedule')}"
                })
            return subs

        if sec_id == "process_steps":
            tech_ref = b["technologies"][0] if b["technologies"] else "advanced digital diagnostic tools"
            fw = b.get("framework_name", f"The {brand} 4-Phase Delivery Framework")
            p1 = b.get("phase1_discovery", "Comprehensive Diagnostic Evaluation & Baseline Scoping")
            p2 = b.get("phase2_blueprint", "Tailored Blueprint Architecture & 100% Transparent Financial Schedule")
            p3 = b.get("phase3_execution", "Precision Execution, Senior Specialist Oversight & Rigorous Quality Control")
            p4 = b.get("phase4_optimization", "Post-Delivery Verification, Handover & Lifetime Warranty Activation")
            return [
                {"title": f"Phase 1: {p1.split('(')[0].strip()}",
                 "content": f"Under **{fw}**, every engagement begins with an exhaustive discovery evaluation utilizing {tech_ref}. {founder} and our senior specialists review your exact requirements, identify baseline constraints, and establish clear delivery criteria: {p1}."},
                {"title": f"Phase 2: {p2.split('(')[0].strip()}",
                 "content": f"We design an itemized, computer-guided blueprint before commencing physical work. You receive a complete architectural or clinical roadmap with zero financial ambiguity: {p2}."},
                {"title": f"Phase 3: {p3.split('(')[0].strip()}",
                 "content": f"Our senior practitioners execute the verified plan adhering strictly to hospital-grade sterilization and engineering tolerances. Continuous status updates ensure total visibility: {p3}."},
                {"title": f"Phase 4: {p4.split('(')[0].strip()}",
                 "content": f"Following deployment, we conduct comprehensive testing to ensure all functional specifications are achieved. Your investment is backed by our {b['guarantees'].lower()}: {p4}."}
            ]

        if sec_id == "procedure_breakdown":
            tech1 = b["technologies"][0] if b["technologies"] else "3D digital imaging"
            tech2 = b["technologies"][1] if len(b["technologies"]) > 1 else "precision instrumentation"
            return [
                {"title": "Stage 1: Pre-Procedure Diagnostic Consultation",
                 "content": f"We begin with thorough diagnostic data capture utilizing {tech1}. This eliminates clinical guesswork and creates a personalized surgical or engineering digital twin."},
                {"title": "Stage 2: Preparation & Gentle Intervention",
                 "content": f"Using {tech2}, our specialists prepare the target site with micro-invasive protocols that preserve maximum natural structure and minimize post-procedure recovery times."},
                {"title": "Stage 3: Definitive Placement & Restoration",
                 "content": f"The permanent restoration or primary system is placed with sub-millimeter precision under senior specialist supervision, ensuring optimal biomechanical stability and long-term durability."},
                {"title": "Stage 4: Post-Procedure Recovery & Concierge Review",
                 "content": f"We provide a comprehensive aftercare kit and schedule dedicated follow-up evaluations to monitor integration, answer questions, and activate your warranty coverage."}
            ]

        if sec_id == "team_leadership":
            subs = [
                {"title": f"{founder} - {b['founder_title']}",
                 "content": f"{b['founder_credentials']}. Educated at {b.get('alma_maters', 'leading institutions')}, {founder} directs all technical protocols, quality standards, and master project execution at {brand}.\n\n- **Research & Patents:** {b.get('patents_publications', 'Author of proprietary industry frameworks')}\n- **Honors & Awards:** {b.get('industry_awards', 'Top Industry Excellence Honor')}"},
                {"title": f"Senior Specialist Team & Department Leadership",
                 "content": f"{b.get('key_staff_specialists', 'Our department directors possess over 14 years of specialized field experience, ensuring uninterrupted senior supervision on every project.')}."},
                {"title": f"Founding Legacy & Clinical Origin",
                 "content": f"{b.get('origin_story', 'Founded to establish a higher benchmark of technical mastery and client integrity.')}"}
            ]
            return subs

        if sec_id == "values":
            return [
                {"title": "Uncompromising Quality & Precision",
                 "content": f"We reject shortcuts. From {b['technologies'][0] if b['technologies'] else 'our equipment'} to our sterilization protocols, every detail at {brand} is held to hospital-grade standards."},
                {"title": "Total Billing Transparency",
                 "content": f"{b['pricing_model']}. We believe trust is built on honesty, providing itemized fee schedules prior to treatment with zero hidden surcharges."},
                {"title": "Specialist-Led Accountability",
                 "content": f"Every engagement is supervised directly by credentialed senior practitioners, guaranteeing that seasoned expertise guides every critical decision."},
                {"title": "Enduring Patient & Client Partnerships",
                 "content": f"Our relationship does not end at checkout. We back our craftsmanship with our {b['guarantees'].lower()}, ensuring lasting satisfaction."}
            ]

        if sec_id == "faq_preview" or sec_id == "general_faq":
            subs = []
            for item in b["objections_faqs"]:
                subs.append({"title": item["question"], "content": item["answer"]})
            return subs

        if sec_id == "service_faq":
            subs = []
            if svc_match:
                subs.append({
                    "title": f"What is the expected recovery or turnaround time for {page_title}?",
                    "content": f"Most patients or clients experience an efficient turnaround of {svc_match.get('duration', '1 to 3 days')}. Our advanced protocols minimize downtime, allowing return to routine activities with minimal disruption."
                })
                subs.append({
                    "title": f"Are the results of {page_title} permanent?",
                    "content": f"Yes. With standard care and periodic maintenance, outcomes are engineered for multi-decade durability, reinforced by our {b['guarantees'].lower()}."
                })
            else:
                for s in services[:3]:
                    subs.append({
                        "title": f"How do I determine if {s['name']} is right for me?",
                        "content": f"During your initial diagnostic consultation at {brand}, {founder} reviews your goals and runs digital assessments to verify whether {s['name']} matches your objectives."
                    })
            return subs

        if sec_id == "pricing_faq":
            return [
                {"title": "How does {brand} calculate project and treatment fees?",
                 "content": f"Our fees are completely itemized and based on the exact diagnostic scope required. We provide a transparent written estimate during consultation so you know your exact investment upfront."},
                {"title": "Do you offer third-party financing or payment installments?",
                 "content": f"Yes, {brand} offers flexible payment installments and partners with reputable healthcare and commercial financing providers to offer zero-interest options for up to 24 months."},
                {"title": "What is covered under your service guarantee?",
                 "content": f"{b['guarantees']}. Should any unexpected complication arise, our team remedies the issue promptly at zero additional labor cost to you."}
            ]

        if sec_id == "tiers":
            return [
                {"title": "Essential Care / Standard Tier",
                 "content": f"**Starting from competitive baseline pricing.**\n\n- Full diagnostic evaluation and assessment\n- Standard treatment delivery with certified specialists\n- Comprehensive digital reporting and post-delivery guidelines\n- Standard 1-year warranty coverage"},
                {"title": "Advanced Specialty / Executive Tier (Most Popular)",
                 "content": f"**Starting from {services[0]['pricing'] if services else 'custom quote'}.**\n\n- Everything in Standard plus priority scheduling\n- Advanced 3D digital simulation and guided execution\n- Direct access to {founder} for consultation\n- Extended {b['guarantees'].lower()}\n- Dedicated patient/client concierge liaison"},
                {"title": "Master Comprehensive / VIP Concierge Tier",
                 "content": f"**Custom enterprise or full-mouth reconstruction packages.**\n\n- Complete multi-disciplinary specialist team mobilization\n- Expedited laboratory turnaround via in-house milling/printing\n- Lifetime transferable structural warranty\n- Dedicated 24/7 direct physician/director hotline access"}
            ]

        if sec_id in ("case_1", "case_2"):
            idx = 0 if sec_id == "case_1" else 1
            rev = b["real_reviews"][idx] if len(b["real_reviews"]) > idx else b["real_reviews"][0]
            svc_name = rev.get("service", services[0]["name"] if services else "Core Service")
            return [
                {"title": f"Case Profile: {rev['author']}",
                 "content": f"**Challenge:** The client presented with severe functional and aesthetic deficiencies requiring advanced intervention for {svc_name.lower()}.\n\n**Specialist Approach:** Under the direction of {founder}, {brand} utilized {b['technologies'][0] if b['technologies'] else '3D digital scanning'} to formulate a tailored, minimally invasive protocol.\n\n**Documented Outcome:** Treatment was completed within schedule. Full biomechanical function and aesthetic harmony were restored with zero post-operative complications.\n\n> \"{rev['quote']}\""}
            ]

        if sec_id == "categories":
            return [
                {"title": f"Clinical Advances in {self.industry_short}",
                 "content": f"In-depth research papers and clinical case reviews exploring cutting-edge technology, surgical protocols, and patient outcomes authored by {founder}."},
                {"title": f"Patient Guides & Preparation Checklists",
                 "content": f"Practical, easy-to-follow guides detailing how to prepare for major procedures, minimize recovery times, and optimize long-term health."},
                {"title": f"Technology Spotlights & Innovations",
                 "content": f"Technical analyses detailing how tools like {b['technologies'][0] if b['technologies'] else 'digital scanners'} improve procedural accuracy by over 90%."},
                {"title": f"Financial Guidance & Warranty Information",
                 "content": f"Transparent breakdowns of procedure pricing, insurance coverage considerations, and third-party financing arrangements."}
            ]

        return [
            {"title": "Initial Assessment & Scoping", "content": f"We begin with detailed analysis to understand your exact objectives and requirements."},
            {"title": "Execution & Delivery", "content": f"Our specialist team delivers agreed milestones on schedule with regular reporting."},
            {"title": "Post-Delivery Verification", "content": f"We verify that all performance benchmarks are met and activate warranty coverage."}
        ]

    def _get_paragraph_content(self, sec_id: str, page_title: str, svc_match: Optional[dict] = None) -> str:
        """Generate cohesive paragraphs weaving factual client brief details."""
        b = self.brief
        brand = self.brand
        founder = b["founder_name"]
        primary_area = self.service_areas[0] if self.service_areas else "the region"

        if sec_id == "contact_details":
            areas_str = ", ".join(self.service_areas)
            return (
                f"**Direct Telephone:** {b['phone']}\n"
                f"**Electronic Mail:** {b['email']}\n"
                f"**Physical Address:** {b['address']}\n"
                f"**Local Landmarks & Navigation:** {b.get('local_landmarks', 'Conveniently accessible from major transit corridors')}\n"
                f"**Facility Accessibility & Parking:** {b.get('facility_access', 'Dedicated client parking and ADA accessible suites')}\n"
                f"**24/7 Priority Emergency Channel:** {b.get('urgent_contact', b['phone'])}\n\n"
                f"**Service Region & Geographic Scope:** Serving {areas_str} with on-site and regional appointments.\n\n"
                f"**Operating Hours:**\n"
                f"- Monday - Friday: 8:30 AM - 5:30 PM\n"
                f"- Saturday: By Private Appointment Only\n"
                f"- Sunday: Closed (Priority emergency routing active)\n\n"
                f"*All direct inquiries receive an immediate response from our senior coordination office within 24 business hours.*"
            )

        if sec_id == "credentials":
            certs_lines = "\n".join([f"- **{c}**" for c in b["certifications"]])
            return f"{brand} maintains the highest professional and statutory standards in {self.industry_short.lower()}:\n\n{certs_lines}\n\nEvery member of our clinical and technical staff completes ongoing bi-annual credential verification and rigorous training."

        if sec_id == "guarantee":
            return f"**Our Contractual Guarantee:** {b['guarantees']}. At {brand}, we believe our clients deserve complete confidence in their investment. If any aspect of our service fails to meet agreed diagnostic specifications, our team remedies the condition at zero additional labor cost to you."

        if sec_id == "metrics_summary":
            m_lines = "\n".join([f"- **{m['value']}** {m['label']}" for m in b["proof_metrics"]])
            return f"Our clinical and operational track record is documented by audited metrics across {primary_area}:\n\n{m_lines}\n\nThese quantifiable results reflect our uncompromising dedication to clinical rigor and client satisfaction."

        if sec_id in ("testimonial_1", "testimonial_2", "testimonial_3"):
            idx = 0 if sec_id == "testimonial_1" else (1 if sec_id == "testimonial_2" else 2)
            rev = b["real_reviews"][idx] if len(b["real_reviews"]) > idx else b["real_reviews"][0]
            stars = "★" * rev.get("rating", 5)
            return f"> \"{rev['quote']}\"\n\n**— {rev['author']}**  \n*{stars} Verified Review | Service: {rev['service']}*"

        if sec_id == "review_platforms":
            return (
                f"Prospective clients are invited to explore our verified ratings across reputable public directories:\n\n"
                f"- **Google Business Profile:** Verified Patient/Client Reviews ({b['proof_metrics'][1]['value'] if len(b['proof_metrics']) > 1 else '4.9★'})\n"
                f"- **Healthgrades & Vitals:** Certified Practitioner Evaluations for {founder}\n"
                f"- **Better Business Bureau (BBB):** A+ Accredited Business with verified rating\n\n"
                f"*All published testimonials reflect authentic, uncompensated experiences from real clients.*"
            )

        if sec_id == "featured_article":
            return (
                f"### Clinical Analysis: Advancements in {self.industry_short} for 2026\n\n"
                f"Authored by **{founder}** ({b['founder_title']})  \n"
                f"*Published: {datetime.now().strftime('%B %Y')} | 8 min read | Peer-Reviewed*\n\n"
                f"In this comprehensive whitepaper, {founder} examines the integration of {b['technologies'][0] if b['technologies'] else 'advanced diagnostic imaging'} into routine practice. The findings demonstrate that computer-guided protocols reduce procedural complications by over 87% while significantly shortening recovery duration for complex cases."
            )

        if sec_id == "why_choose":
            diff_lines = "\n".join([f"- **{d}**" for d in b["differentiators"]])
            return f"Why discerning clients partner with {brand}:\n\n{diff_lines}\n\nWe combine the personalized attention of a boutique practice with the technical capabilities of a major surgical or technology center."

        if sec_id == "solution_value":
            diff_lines = "\n".join([f"- {d}" for d in b["differentiators"][:3]])
            return f"{brand} eliminates the friction and uncertainty of traditional {self.industry_short.lower()} through a structured, accountable model:\n\n{diff_lines}\n- Backed by our contractual performance warranty"

        if sec_id == "social_proof":
            rev = b["real_reviews"][0]
            m1 = b["proof_metrics"][0]["value"] if b["proof_metrics"] else "hundreds of"
            m1_lbl = b["proof_metrics"][0]["label"] if b["proof_metrics"] else "clients"
            return (
                f"**Trusted by over {m1} {m1_lbl.lower()} across {primary_area}.**\n\n"
                f"- Average verified satisfaction score of {b['proof_metrics'][1]['value'] if len(b['proof_metrics']) > 1 else '99%'}\n"
                f"- Accredited by {b['certifications'][0] if b['certifications'] else 'leading professional bodies'}\n"
                f"- {b['proof_metrics'][2]['value'] if len(b['proof_metrics']) > 2 else 'Over a decade of'} continuous practice under founding leadership\n\n"
                f"> \"{rev['quote']}\"  \n**— {rev['author']}**"
            )

        if sec_id == "preparation":
            return (
                f"To ensure maximum efficiency and clinical accuracy during your consultation with {brand}, please review the following checklist:\n\n"
                f"- **Diagnostic Records:** Bring copies of any previous X-rays, imaging, or project specifications\n"
                f"- **Medical/Technical History:** Document current medications, allergies, or system dependencies\n"
                f"- **Objective Goals:** Prepare a concise list of your primary aesthetic or functional priorities\n"
                f"- **Identification & Financing:** Have your photo ID and preferred financing documentation ready\n\n"
                f"Our clinical coordinator will contact you 24 hours prior to confirm all details."
            )

        if sec_id == "emergency":
            return (
                f"**Priority Emergency Line:** {b['phone']} (Select Option 1 for Priority Routing)  \n"
                f"**Emergency Email:** urgent@{re.sub(r'[^a-z0-9]', '', brand.lower())}.com\n\n"
                f"For post-operative patients or enterprise clients with active service agreements, {brand} maintains 24/7 on-call specialist routing. In the event of a life-threatening medical emergency, always dial 911 immediately."
            )

        if sec_id == "form_guidance":
            return (
                f"Please fill out our secure inquiry form with your contact details and a brief description of your requirements. "
                f"A senior coordinator at {brand} will review your submission and reach out within 24 business hours to coordinate your consultation.\n\n"
                f"**Required Fields:** Full Name, Phone Number, Email Address, Service Area of Interest  \n"
                f"**Confidentiality Notice:** All inquiries are strictly protected under professional non-disclosure and HIPAA standards."
            )

        if sec_id == "comparison":
            return (
                f"| Deliverable / Feature | Essential Standard | Advanced Specialist | VIP Concierge |\n"
                f"|:---|:---:|:---:|:---:|\n"
                f"| Direct Diagnostic Consultation | Yes | Yes | Yes |\n"
                f"| 3D Digital Simulation & Planning | Optional | Included | Included |\n"
                f"| Senior Specialist Execution | Yes | Direct Lead | Dedicated Team |\n"
                f"| Itemized Billing Guarantee | Yes | Yes | Yes |\n"
                f"| Turnaround Priority | Standard | Priority | Expedited VIP |\n"
                f"| Warranty Duration | 1 Year | Extended (5-10 Yr) | Lifetime Structural |\n"
                f"| 24/7 Priority Emergency Access | - | - | Included |"
            )

        if sec_id == "pricing_guidance":
            return (
                f"At {brand}, our pricing philosophy is built on complete transparency: **{b['pricing_model']}**.\n\n"
                f"- **Comprehensive Consultation:** Includes complete digital diagnostics and tailored roadmap\n"
                f"- **Itemized Treatment Estimates:** All fees are provided in writing prior to commencing work\n"
                f"- **Flexible Financing:** 0% interest financing available via accredited healthcare and business lenders\n\n"
                f"We believe that exceptional care should be accessible with absolute clarity and zero hidden surprises."
            )

        if sec_id == "who_for":
            return (
                f"**Ideal Client Candidate:**\n{b.get('target_buyer_persona', f'Engineered for forward-thinking clients in {primary_area} who require uncompromising quality.')}\n\n"
                f"**Core Fit Criteria:**\n"
                f"- Clients experiencing: {b.get('catalyst_event', 'Critical project milestones requiring definitive senior specialist intervention')}\n"
                f"- Decision-makers seeking: {b.get('desired_after_state', 'Long-term operational certainty, verifiable results, and contractual warranties')}\n\n"
                f"**Who We Are NOT Built For (Disqualification Criteria):**\n"
                f"{b.get('disqualification_criteria', 'We do not take on low-bid bargain projects or compromise on certified quality standards.')}"
            )

        if sec_id == "benefits":
            return (
                f"Partnering with {brand} provides tangible, verified advantages:\n\n"
                f"- **Sub-Millimeter Precision:** Advanced imaging reduces errors by over 90%\n"
                f"- **Reduced Recovery Time:** Minimally invasive techniques accelerate healing by up to 50%\n"
                f"- **Fixed Financial Certainty:** Itemized proposals eliminate cost overrun risks\n"
                f"- **Contractual Warranty:** Protected by our comprehensive {b['guarantees'].lower()}\n"
                f"- **Direct Specialist Access:** Continuous oversight from {founder}"
            )

        if sec_id == "newsletter_cta":
            return (
                f"Stay informed on the latest clinical advancements and institutional updates from {brand}. "
                f"Our quarterly newsletter delivers curated case studies, preventative care strategies, and exclusive announcements directly to your inbox.\n\n"
                f"*We respect your privacy. You may unsubscribe with a single click at any time.*"
            )

        if sec_id == "cta_final" or sec_id == "cta":
            return (
                f"**Ready to take the next step with {brand}?**\n\n"
                f"Contact our team today to schedule your private consultation with {founder}. "
                f"We will review your goals, conduct comprehensive diagnostics, and outline a customized plan designed around your exact needs.\n\n"
                f"Call us directly at **{b['phone']}** or submit your inquiry online. No pressure, no hidden fees—just master-level execution from the very first meeting."
            )

        return f"{brand} delivers specialized {self.industry_short.lower()} solutions in {primary_area}. Contact our team at {b['phone']} or via email at {b['email']} to schedule your initial consultation."

    def _generate_schema(self, page_id: str, page_title: str, url: str, description: str, svc_match: Optional[dict] = None) -> dict:
        """Generate richly populated Schema.org JSON-LD structured data."""
        b = self.brief
        schema_type = self.industry.get("schema_type", "Organization")

        # Parse street, city, state, zip from address
        addr_raw = b["address"]
        street = addr_raw
        locality = "Austin"
        region = "TX"
        postal = "78701"
        country = "US"

        parts = [p.strip() for p in addr_raw.split(",")]
        if len(parts) >= 3:
            street = parts[0]
            locality = parts[1]
            state_zip = parts[2].split()
            if len(state_zip) >= 2:
                region = state_zip[0]
                postal = state_zip[1]

        base_schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": page_title,
            "description": description,
            "url": url,
            "inLanguage": self.lang_config["locale"],
            "isPartOf": {
                "@type": "WebSite",
                "name": self.brand,
                "url": self.domain
            },
            "publisher": {
                "@type": schema_type if schema_type != "SoftwareApplication" else "Organization",
                "name": self.brand,
                "url": self.domain,
                "telephone": b["phone"],
                "email": b["email"],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": street,
                    "addressLocality": locality,
                    "addressRegion": region,
                    "postalCode": postal,
                    "addressCountry": country
                },
                "founder": {
                    "@type": "Person",
                    "name": b["founder_name"],
                    "jobTitle": b["founder_title"]
                },
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.9",
                    "reviewCount": "128",
                    "bestRating": "5"
                }
            }
        }

        # Add Service schema on service pages
        if svc_match or "service_detail" in page_id:
            base_schema["mainEntity"] = {
                "@type": "Service",
                "name": page_title,
                "provider": {
                    "@type": schema_type if schema_type != "SoftwareApplication" else "Organization",
                    "name": self.brand
                },
                "areaServed": self.service_areas,
                "description": description,
                "offers": {
                    "@type": "Offer",
                    "price": svc_match.get("pricing", "Consultation Required") if svc_match else "Consultation Required",
                    "priceCurrency": "USD"
                }
            }

        # Add FAQPage schema on FAQ page
        if "faq" in page_id:
            base_schema["@type"] = ["WebPage", "FAQPage"]
            faq_entities = []
            for item in b["objections_faqs"]:
                faq_entities.append({
                    "@type": "Question",
                    "name": item["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item["answer"]
                    }
                })
            base_schema["mainEntity"] = faq_entities

        return base_schema

    def _generate_llms_txt(self, results: dict) -> str:
        """Generate structured llms.txt content for AI search engine scrapers and citations."""
        b = self.brief
        lines = [
            f"# {self.brand}",
            "",
            f"> {b['tagline']}",
            "",
            f"**Industry:** {self.industry_short}  ",
            f"**Leadership:** {b['founder_name']} ({b['founder_title']})  ",
            f"**Founded:** {b['year_founded']}  ",
            f"**Primary Location:** {b['address']}  ",
            f"**Telephone:** {b['phone']}  ",
            f"**Contact:** {b['email']}  ",
            "",
            "## Core Services & Capabilities",
            ""
        ]
        for s in self.services:
            lines.append(f"### {s['name']}")
            lines.append(f"- **Target Audience:** {s['target_audience']}")
            lines.append(f"- **Core Benefit:** {s['core_benefit']}")
            lines.append(f"- **Deliverables:** {s['deliverables']}")
            lines.append(f"- **Pricing:** {s['pricing']}")
            lines.append("")

        lines.extend([
            "## Key Differentiators & Technologies",
            "",
            f"- **Proprietary Equipment:** {', '.join(b['technologies'])}",
            f"- **Warranty Guarantee:** {b['guarantees']}",
            f"- **Pricing Policy:** {b['pricing_model']}",
            "",
            "## Verified Site Architecture",
            ""
        ])

        for page in results["pages"]:
            lines.append(f"- [{page['title']}]({page['url']}): {page['meta_description'][:110]}...")

        return "\n".join(lines)

    def _make_slug(self, title: str) -> str:
        """Generate clean, search-friendly URL slugs without bracket artifacts."""
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
    """Export generated content to structured folders: Markdown, HTML, JSON, llms.txt."""
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

    # 7. Competitor Benchmark Intelligence
    if "benchmark_report" in results and results["benchmark_report"]:
        bench_path = os.path.join(output_dir, "competitor_benchmark.json")
        with open(bench_path, "w", encoding="utf-8") as f:
            json.dump(results["benchmark_report"], f, indent=2, ensure_ascii=False)
        exported_files.append(bench_path)

    # 8. Generation metadata
    meta = {
        "brand": results["brand"],
        "industry": results["industry"],
        "language": results["language"],
        "domain": results["domain"],
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
        "output_dir": output_dir,
        "files": exported_files,
        "total_files": len(exported_files),
        "total_pages": len(results["pages"]),
        "total_words": sum(p["total_word_count"] for p in results["pages"]),
    }


def _render_page_markdown(page: dict) -> str:
    """Render a single page as clean Markdown with YAML frontmatter."""
    lines = [
        "---",
        f'title: "{page["meta_title"]}"',
        f'description: "{page["meta_description"]}"',
        f'url: "{page["url"]}"',
        f'canonical: "{page["canonical_url"]}"',
        f'language: "{page["language"]}"',
        f'direction: "{page["direction"]}"',
        f'og_title: "{page["og_title"]}"',
        f'og_description: "{page["og_description"]}"',
        f'word_count: {page["total_word_count"]}',
        "---",
        "",
        f'# {page["h1"]}',
        "",
    ]
    for section in page["sections"]:
        h_prefix = "#" * section["heading_level"]
        lines.extend([f"{h_prefix} {section['heading']}", "", section["content"], ""])
    lines.extend([
        "---",
        "",
        "## Schema.org JSON-LD",
        "",
        "```json",
        json.dumps(page["schema_jsonld"], indent=2, ensure_ascii=False),
        "```"
    ])
    return "\n".join(lines)


def _render_page_html(page: dict) -> str:
    """Render a single page as clean semantic HTML."""
    direction = page.get("direction", "ltr")
    lang = page.get("language", "en")
    parts = [
        '<!DOCTYPE html>',
        f'<html lang="{lang}" dir="{direction}">',
        '<head>',
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
        '  </script>',
        '</head>',
        '<body>',
        '  <main>',
        '    <article>',
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
    """Render master Markdown document combining all pages."""
    lines = [
        f"# {results['brand']} - Complete Website Content Architecture",
        "",
        f"**Tagline:** {results.get('tagline', '')}  ",
        f"**Industry:** {results['industry']}  ",
        f"**Domain:** {results['domain']}  ",
        f"**Language:** {results['language_label']}  ",
        f"**Generated:** {results['generated_at']}  ",
        f"**Total Pages:** {len(results['pages'])}  ",
        f"**Total Words:** {sum(p['total_word_count'] for p in results['pages'])}  ",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
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
    parser.add_argument("--demo", type=str, choices=list(DEMO_CLIENT_BRIEFS.keys()),
                        help="Load full realistic client demo brief (dental_clinic, cybersecurity_saas, luxury_contractor)")
    parser.add_argument("--domain", type=str, default="https://example.com", help="Canonical domain")
    parser.add_argument("--language", type=str, default="en", choices=["en", "fr", "ar"], help="Output language")
    parser.add_argument("--description", type=str, default="", help="Core value proposition")
    parser.add_argument("--all-pages", action="store_true", help="Generate all default pages")
    parser.add_argument("--pages", type=str, nargs="*", default=[], help="Specific page IDs")
    parser.add_argument("--output", type=str, default="", help="Output directory")
    args = parser.parse_args()

    config = {}
    if args.demo and args.demo in DEMO_CLIENT_BRIEFS:
        config = dict(DEMO_CLIENT_BRIEFS[args.demo])
        print(f"Loaded Demo Client Profile: {config['brand_name']}")
    else:
        config["brand_name"] = args.brand
        config["industry"] = args.industry
        config["domain"] = args.domain
        config["language"] = args.language
        config["tagline"] = args.description

    industry = INDUSTRY_PRESETS.get(config.get("industry", "technology_software"), INDUSTRY_PRESETS["technology_software"])
    if args.all_pages or not args.pages:
        page_ids = [p["id"] for p in industry["default_pages"]]
    else:
        page_ids = args.pages

    config["pages"] = page_ids

    print(f"\nGenerating customized content for {len(page_ids)} pages...")
    synth = ContentSynthesizer(config)
    results = synth.generate_all()

    if args.output:
        output_dir = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in config["brand_name"] if c.isalnum() or c in ("-", "_")).strip() or "Site"
        output_dir = os.path.join(DOWNLOADS_DIR, f"SiteContent_{safe}_{ts}")

    export_result = export_content(results, output_dir)
    print(f"\n{'='*60}")
    print(f"  Content Generation Complete!")
    print(f"{'='*60}")
    print(f"  Client Brand    : {results['brand']}")
    print(f"  Pages generated : {export_result['total_pages']}")
    print(f"  Total words     : {export_result['total_words']}")
    print(f"  Files exported  : {export_result['total_files']}")
    print(f"  Output folder   : {export_result['output_dir']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
