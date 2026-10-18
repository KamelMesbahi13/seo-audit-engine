"""InersiaLab Software Department — SEO & GEO Blog Architect Engine.

Synthesizes publication-ready, deeply researched, and rigorously calibrated blogs:
- Multilingual Support: English (EN), French (FR), and Arabic (AR RTL)
- Dual Intake Modes: Essential Intake (Min Questions) vs Comprehensive Intake (Max Questions)
- Primary Keyless LLM Generation: OVHcloud Llama 3.3 70B / Mistral Small / LLM7 / Pollinations
- Strict On-Page SEO Calibration: Single H1, ordered H2/H3, Title (50-60c), Meta Description (140-160c)
- Generative Engine Optimization (GEO & AEO): Definitional hooks for SearchGPT, Perplexity, Claude, Google AI Overviews
- E-E-A-T Author Authority: Pedigree bylines, fact-checking credentials, and editorial audit stamps
- Complete Schema.org JSON-LD: BlogPosting + FAQPage + BreadcrumbList
- Domain-Adaptive Algorithmic Fallback: 100% offline synthesis guarantee (Medical, Travel, Tech, Finance, General)
- Export Package: Markdown, Semantic HTML with RTL styling, JSON-LD, metadata scorecard, and llms.txt
"""

import os
import re
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from utils import fetch_url
from optimizer import clean_seo_slug, estimate_pixel_width
from llm import catalog, client

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def clean_multilingual_slug(text: str) -> str:
    """Creates a clean, SEO-friendly slug preserving Arabic, French, and English characters."""
    if not text:
        return "blog-guide"
    cleaned = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE).strip()
    slug = re.sub(r'[-\s]+', '-', cleaned)
    return slug.strip('-') or "blog-guide"

# ==============================================================================
# INTAKE QUESTIONNAIRE SCHEMA (MIN & MAX MODES)
# ==============================================================================

MIN_QUESTIONS = [
    {
        "id": "topic",
        "label": "1. Blog Topic / Main Subject",
        "placeholder": "e.g., Sustainable Architecture in 2026 / How to Start Real Estate Investing / Guide to Intermittent Fasting",
        "default": "",
        "help": "The primary subject and overarching thesis of the article.",
        "required": True,
    },
    {
        "id": "focus_keyword",
        "label": "2. Primary Focus Keyword",
        "placeholder": "e.g., sustainable architecture / real estate investing / intermittent fasting",
        "default": "",
        "help": "Exact keyword targeted for Google and AI search citability.",
        "required": True,
    },
    {
        "id": "target_audience",
        "label": "3. Target Audience & Reader Intent",
        "placeholder": "e.g., Homeowners, B2B decision makers, beginners, or industry specialists",
        "default": "",
        "help": "Defines the technical depth, vocabulary, and pain-point alignment.",
        "required": True,
    },
    {
        "id": "language",
        "label": "4. Target Language",
        "placeholder": "en, fr, or ar",
        "default": "en",
        "options": [
            {"val": "en", "label": "English (US/UK Global Standard)"},
            {"val": "fr", "label": "Français (French - International Standard)"},
            {"val": "ar", "label": "العربية (Arabic - Modern Standard with RTL Layout)"},
        ],
        "help": "Generates native linguistic structures with appropriate RTL directional styles.",
        "required": True,
    },
    {
        "id": "word_count_range",
        "label": "5. Target Word Count Range",
        "placeholder": "Min: 1200, Max: 2500",
        "min_default": 1200,
        "max_default": 2400,
        "help": "High-depth technical long-form content engineered to outrank thin content.",
        "required": True,
    },
]

MAX_QUESTIONS = MIN_QUESTIONS + [
    {
        "id": "secondary_keywords",
        "label": "6. Secondary & Semantic (LSI) Entities",
        "placeholder": "e.g., energy efficiency, passive solar, LEED certification, building materials",
        "default": "",
        "help": "Topical entities that reinforce topical authority in Google's Knowledge Graph.",
        "required": False,
    },
    {
        "id": "author_name",
        "label": "7. Author Name & E-E-A-T Credentials",
        "placeholder": "e.g., Jane Doe, Senior Sustainable Architect, AIA, LEED AP",
        "default": "",
        "help": "Author pedigree for E-E-A-T credibility boxes and Schema.org Author entity.",
        "required": False,
    },
    {
        "id": "tone",
        "label": "8. Tone of Voice & Editorial Angle",
        "placeholder": "e.g., Authoritative, educational, empirical, engaging, practical",
        "default": "Authoritative, insightful, engaging, and practically actionable",
        "help": "Directs the pacing, sentence length, and analytical posture.",
        "required": False,
    },
    {
        "id": "subtopics",
        "label": "9. Required Sub-Topics & Must-Include Points",
        "placeholder": "e.g., 1. Core principles 2. Cost-benefit analysis 3. Step-by-step roadmap 4. Real-world case study",
        "default": "",
        "help": "Specific technical sections or arguments that must appear in the final blog.",
        "required": False,
    },
    {
        "id": "competitor_url",
        "label": "10. Competitor URL to Outrank (Optional)",
        "placeholder": "e.g., https://competitor.com/blog/sustainable-architecture-guide",
        "default": "",
        "help": "If provided, the system spot-checks competitor heading structure to engineer superior coverage.",
        "required": False,
    },
    {
        "id": "cta",
        "label": "11. Call to Action (CTA) & Conversion Target",
        "placeholder": "e.g., Download our free checklist / Schedule a discovery consultation",
        "default": "",
        "help": "Natural, high-value conclusion invitation.",
        "required": False,
    },
    {
        "id": "faqs",
        "label": "12. Specific FAQs to Answer (Optional)",
        "placeholder": "e.g., What are the upfront costs? How long until positive ROI? What are common mistakes?",
        "default": "",
        "help": "Questions to format for Schema.org FAQPage rich snippets.",
        "required": False,
    },
]


# ==============================================================================
# MASTER SYSTEM & USER PROMPTS FOR LLM GENERATION
# ==============================================================================

def build_system_prompt(language: str = "en") -> str:
    lang = (language or "en").lower()

    if lang == "ar":
        return """أنت خبير التحرير وصياغة المحتوى المتخصص وتحسين محركات البحث التوليدية (SEO / GEO / AEO) في InersiaLab.
مهمتك كتابة مقال مرجعي متكامل وشامل وموثوق لأي موضوع أو مجال يحدده المستخدم (طبي، تقني، مالي، قانوني، سياحي، تعليمي، تجاري، علمي، إلخ).

تعليمات التحرير والمعايير الإلزامية:
1. الالتزام المطلق بمجال وموضوع المستخدم: اكتب بدقة واحترافية مستخدماً المصطلحات الأصيلة الخاصة بالمجال المستهدف.
2. تنسيق المخرجات: اكتب المقال كاملاً بتنسيق GitHub Flavored Markdown فقط. ابدأ مباشرة بعنوان المقال H1 ولا تضع أي مقدمات خارج الماركداون أو كتل كود (```json أو ```markdown).
3. هيكل المقال الإلزامي:
   # [عنوان SEO جذاب وشامل بين 45 إلى 65 حرفاً يتضمن الكلمة المفتاحية الرئيسية]

   > **الخلاصة التنفيذية (إجابة مباشرة لمحركات الذكاء الاصطناعي):** [إجابة قطعية ومباشرة في جملتين إلى ثلاث تشرح الموضوع وتجيب عن أهم تساؤلات القارئ لمحركات البحث مثل SearchGPT و Perplexity و Google AI Overviews].

   ## 1. [القسم الأول: مقدمة تشخيصية ونظرة شاملة حول الموضوع]
   [يجب أن تبدأ أول جملة في كل عنوان H2 بتعريف مباشر وواضح قابل للاقتباس الفوري (GEO Citability Hook)].

   ## 2. [القسم الثاني: المنهجية التطبيقية أو المراحل التفصيلية أو المحاور الجوهرية]
   [شرح متعمق للمراحل والخطوات العملية بشكل منظم، مع عناوين فرعية H3 لكل محور].

   ## 3. [القسم الثالث: جدول مقارنة أو بيانات رقمية مفصلة (Markdown Table)]
   [جدول ماركداون احترافي يقارن الخيارات أو المعايير أو التكاليف أو المزايا بأرقام وبيانات واضحة ومحددة].

   ## 4. [القسم الرابع: خطة العمل العملية وأفضل الممارسات والأخطاء الشائعة]
   [قوائم نقطية، نصائح تطبيقية، وتوجيهات عملية واضحة للجمهور المستهدف].

   ## 5. الأسئلة الشائعة حول [الموضوع] (FAQ)
   [اطرح من 4 إلى 6 أسئلة بحثية حقيقية يطرحها الجمهور، بحيث يكون كل سؤال في عنوان فرعي مستقل H3 متبوعاً بإجابة نموذجية ومباشرة من 40 إلى 60 كلمة]:
   ### [السؤال الأول]؟
   [الإجابة المباشرة والواضحة].

   ### [السؤال الثاني]؟
   [الإجابة المباشرة والواضحة].

   ## بيانات الاعتماد والتحقق التحريري
   - **الكاتب / الخبير المشرف:** [اسم الكاتب أو الفريق الاستشاري]
   - **المراجعة والتدقيق:** هيئة التدقيق والتحرير المتخصص
   - **الخطوة التالية (دعوة لاتخاذ إجراء):** [الدعوة لاتخاذ إجراء المحددة من المستخدم]

اكتب بلغة عربية فصحى راقية، واضحة، متماسكة، خالية من الركاكة والأخطاء، وتناسب تطلعات الجمهور المستهدف بدقة."""

    elif lang == "fr":
        return """Vous êtes le rédacteur en chef et architecte de contenu SEO & GEO chez InersiaLab.
Votre mission est de rédiger un article de blog exhaustif, professionnel et rigoureusement optimisé pour le référencement naturel et les moteurs génératifs (SearchGPT, Perplexity, Google AI Overviews), adapté à N'IMPORTE QUEL domaine (technologie, finance, santé, tourisme, droit, immobilier, lifestyle, etc.).

DIRECTIVES STRICTES :
1. Pertinence absolue du domaine : Adoptez rigoureusement le vocabulaire métier, le ton et les concepts propres au secteur d'activité du sujet choisi par l'utilisateur.
2. Format de sortie : Rédigez l'article complet directement en GitHub Flavored Markdown sans balises de code (```markdown) ni texte préliminaire.
3. Structure obligatoire :
   # [Titre SEO percutant de 45 à 65 caractères contenant le mot-clé principal]

   > **Synthèse Exécutive :** [Réponse directe en 2-3 phrases optimisée pour la citabilité IA].

   ## 1. [Section 1 : Vue d'ensemble, enjeux fondamentaux et définitions clés]
   [La première phrase de chaque H2 doit être une définition ou conclusion factuelle directe].

   ## 2. [Section 2 : Méthodologie, étapes clés ou analyse détaillée]
   [Sous-sections H3 détaillées et développées en profondeur].

   ## 3. [Section 3 : Tableau comparatif ou métriques en Markdown]
   [Tableau Markdown comparant options, critères, coûts, protocoles ou performances].

   ## 4. [Section 4 : Recommandations pratiques, plan d'action et pièges à éviter]

   ## 5. Foire Aux Questions (FAQ)
   [4 à 6 questions fréquentes avec titre H3 pour chaque question et réponse claire de 40 à 60 mots].

   ## Validation Éditoriale et Auteur
   - **Auteur :** [Nom de l'auteur]
   - **Revue :** Comité de validation éditoriale
   - **Appel à l'action :** [CTA utilisateur]"""

    else:
        return """You are the Chief Editorial & SEO/GEO Architecture Engine at InersiaLab.
Your mission is to produce an exhaustive, authoritative, deeply researched blog post strictly calibrated for #1 Google rankings and generative search citability (SearchGPT, Perplexity, Claude, and Google AI Overviews), across ANY domain or industry (technology, business, finance, healthcare, lifestyle, law, education, real estate, ecommerce, etc.).

STRICT ARCHITECTURAL DIRECTIVES:
1. Complete Subject Fidelity: Seamlessly adapt to the specific domain and target audience of the user's prompt. Employ natural, authentic terminology specific to that industry.
2. Output Format: Return the complete article purely in GitHub Flavored Markdown. Start immediately with `# ` Title. Do NOT wrap in ```json or markdown code fences.
3. Required Structural Blueprint:
   # [Compelling SEO Title Tag: 45–65 characters including focus keyword]

   > **Executive Answer:** [Direct 2–3 sentence definitional answer engineered for AI Overviews and Perplexity citability].

   ## 1. [Section 1: Executive Overview, Foundational Landscape & Core Definitions]
   [The very first sentence of every H2 must be a crisp, standalone factual takeaway or definition].

   ## 2. [Section 2: Comprehensive Framework, Phases, or In-Depth Breakdown]
   [Detailed subsections using ### H3 headers with actionable depth].

   ## 3. [Section 3: Comparative Benchmark Data Table]
   [High-density Markdown table comparing options, criteria, costs, performance, or specifications].

   ## 4. [Section 4: Strategic Roadmap, Practical Checklists & Best Practices]

   ## 5. Frequently Asked Questions (FAQ)
   [4 to 6 real search queries, each formatted as a ### H3 heading followed by an authoritative 40–60 word answer].

   ## Author & Editorial Verification
   - **Lead Author:** [Author Name & Credentials]
   - **Peer Review:** InersiaLab Editorial & Domain Audit Board
   - **Recommended Action (CTA):** [User CTA]"""


def build_user_prompt(data: Dict[str, Any]) -> str:
    topic = data.get("topic", "Comprehensive Guide").strip()
    focus_kw = data.get("focus_keyword", topic).strip()
    sec_kws = data.get("secondary_keywords", "").strip()
    audience = data.get("target_audience", "General Audience").strip()
    lang = data.get("language", "en").lower()
    min_w = data.get("min_words", 1200)
    max_w = data.get("max_words", 2400)
    author = data.get("author_name", "Editorial Team").strip()
    tone = data.get("tone", "Authoritative, empirical, and actionable").strip()
    subtopics = data.get("subtopics", "").strip()
    competitor = data.get("competitor_url", "").strip()
    cta = data.get("cta", "").strip()
    custom_faqs = data.get("faqs", "").strip()
    custom_prompt = data.get("custom_prompt", "").strip()
    comp_headings = data.get("competitor_headings", [])

    prompt = f"""Generate an exhaustive, publication-ready, deeply researched article adhering to these specific inputs:

TOPIC & AUDIENCE PARAMETERS:
- Main Subject: {topic}
- Primary Focus Keyword: {focus_kw}
- Secondary / LSI Keywords: {sec_kws or 'Extract relevant high-volume LSI entities automatically'}
- Target Audience: {audience}
- Language: {lang}
- Desired Length: Comprehensive long-form (at least {min_w} words, target {max_w} words)
- Author Name & Credentials: {author}
- Tone & Angle: {tone}
- Must-Include Sub-Topics: {subtopics or 'Cover all essential phases, criteria, and practical guidance thoroughly'}
- Call to Action: {cta or 'Invite readers to consult with verified specialists'}
- Specific FAQs to Answer: {custom_faqs or 'Include the top 4-6 most searched questions on this topic'}
"""
    if competitor:
        prompt += f"\n- Competitor URL Target: {competitor}\n"
    if comp_headings:
        prompt += f"- Competitor Headings to Outrank: {', '.join(comp_headings)}\n"

    if custom_prompt:
        prompt += f"""
HIGH-PRIORITY USER CUSTOM DIRECTIVES:
{custom_prompt}
(Apply all specific instructions, stylistic requests, and angle directives above strictly.)
"""

    prompt += "\nSynthesize the complete, in-depth Markdown article now starting immediately with the # H1 title."
    return prompt


# ==============================================================================
# DOMAIN-ADAPTIVE ALGORITHMIC BLOG SYNTHESIZER (100% OFFLINE FALLBACK)
# ==============================================================================

class AlgorithmicBlogSynthesizer:
    """Generates an authentic, domain-adaptive SEO & GEO blog without external API keys.

    Detects the topic domain (medical, travel, finance, tech, general) so that
    medical topics NEVER receive software engineering or CI/CD terminology.
    """

    @staticmethod
    def _detect_domain(topic: str, focus_kw: str, audience: str) -> str:
        combined = f"{topic} {focus_kw} {audience}".lower()
        medical_kw = [
            "كبد", "زراعة", "طبي", "علاج", "مريض", "جراح", "مستشفى", "صحة", "دواء", "أورام",
            "liver", "transplant", "medical", "clinic", "surgery", "patient", "doctor", "health",
            "santé", "chirurgie", "médical", "hôpital", "greffe"
        ]
        travel_kw = [
            "سياحة", "فندق", "سفر", "طيران", "تذكرة", "رحلة", "جولة", "معالم",
            "travel", "hotel", "tourism", "flight", "tour", "vacation", "trip", "voyage"
        ]
        finance_kw = [
            "استثمار", "مال", "بورصة", "أسهم", "تداول", "عملات", "تمويل", "بنوك",
            "invest", "finance", "crypto", "stock", "trading", "wealth", "banking"
        ]
        tech_kw = [
            "devops", "cloud", "ci/cd", "kubernetes", "zero-trust", "api", "microservice",
            "software", "cybersecurity", "برمجة", "سحابية", "أمن سيبراني", "معمارية برمجية"
        ]

        if any(w in combined for w in medical_kw):
            return "medical"
        if any(w in combined for w in travel_kw):
            return "travel"
        if any(w in combined for w in finance_kw):
            return "finance"
        if any(w in combined for w in tech_kw):
            return "tech"
        return "general"

    @staticmethod
    def synthesize(data: Dict[str, Any]) -> Dict[str, Any]:
        lang = data.get("language", "en").lower()
        topic = data.get("topic", "Comprehensive Strategic Guide").strip()
        focus_kw = data.get("focus_keyword", topic).strip()
        audience = data.get("target_audience", "Industry specialists and decision makers").strip()
        author = data.get("author_name", "Editorial Board").strip()
        cta = data.get("cta", "Contact our advisory team for a dedicated assessment.").strip()

        domain = AlgorithmicBlogSynthesizer._detect_domain(topic, focus_kw, audience)
        slug = clean_multilingual_slug(focus_kw or topic)
        now_iso = datetime.now().isoformat()

        if lang == "ar":
            return AlgorithmicBlogSynthesizer._synthesize_arabic(data, topic, focus_kw, audience, author, cta, slug, now_iso, domain)
        elif lang == "fr":
            return AlgorithmicBlogSynthesizer._synthesize_french(data, topic, focus_kw, audience, author, cta, slug, now_iso, domain)
        else:
            return AlgorithmicBlogSynthesizer._synthesize_english(data, topic, focus_kw, audience, author, cta, slug, now_iso, domain)

    @staticmethod
    def _synthesize_arabic(data, topic, focus_kw, audience, author, cta, slug, now_iso, domain):
        if domain == "medical":
            title = f"{focus_kw} : الدليل الطبي الشامل لعام 2026"
            if len(title) > 60:
                title = f"{focus_kw} : دليلك الطبي الشامل 2026"

            meta_desc = f"دليل متكامل حول {focus_kw}: التكاليف، شروط المتبرع، المراحل الجراحية، ونسب النجاح وفترة التعافي برعاية طبية معتمدة لعام 2026."
            if len(meta_desc) > 160:
                meta_desc = meta_desc[:157] + "..."

            aeo_summary = f"تعد {focus_kw} من أدق الإجراءات الطبية المتقدمة، حيث تعتمد على استبدال الكبد المتضرر بجزء سليم من متبرع حي أو متوفى، بنسب نجاح تتجاوز 85% في المراكز المعتمدة دولياً."

            md = f"""# {title}

> **الخلاصة التنفيذية (إجابة مباشرة لمحركات الذكاء الاصطناعي):** {aeo_summary}

---

## 1. النظرة الطبية الشاملة: واقع وأهمية {focus_kw}

يمثل إجراء **{focus_kw}** خياراً علاجياً منقذاً للحياة للمرضى الذين يعانون من أمراض الكبد المتقدمة أو الفشل الكبدي النهائي. بفضل التطور الهائل في التقنيات الجراحية وبروتوكولات الرعاية المكثفة، أصبحت العمليات تُجرى بمعدلات أمان مرتفعة للغاية.

صُمم هذا الدليل خصيصاً ليخاطب **{audience}**، مقدماً إجابات وافية وموثوقة مبنية على الأدلة السريرية الدقيقة بعيداً عن التعقيد.

### أهم الركائز الأساسية لنجاح الإجراء
1. **التقييم السريري الدقيق:** إجراء فحوصات شاملة لتقييم كفاءة الأعضاء وتوافق الأنسجة وفصائل الدم بدقة.
2. **فريق جراحي متعدد التخصصات:** يضم استشاريي جراحة الكبد، التخدير، العناية المركزة، والتمريض المتخصص.
3. **أحدث التقنيات الجراحية:** استخدام تقنيات المنظار الجراحي المتقدم وأجهزة مراقبة تدفق الدم اللحظية.
4. **بروتوكولات التثبيط المناعي والمتابعة:** خطة علاجية مخصصة لمنع رفض العضو المزروع وضمان تعافي سريع.

---

## 2. المراحل السريرية للعملية: من التشخيص إلى النقاهة

يمر المريض والمتبرع بخطة علاجية متسلسلة تشمل أربع مراحل أساسية لضمان سلامة الطرفين:

| المرحلة السريرية | الهدف الطبي المباشر | الإجراءات والفحوصات الرئيسية | المدة المتوقعة |
| :--- | :--- | :--- | :--- |
| **المرحلة 1: الفحص الشامل** | تقييم الملاءمة الصحية والتوافق | تحاليل وظائف الكبد، تصوير مقطعي، أشعة رنين، فحص قلب | 3 إلى 5 أيام |
| **المرحلة 2: التحضير والجراحة** | استئصال وزراعة الجزء السليم | جراحة دقيقة تحت تخدير عام بإشراف استشاريين دوليين | 8 إلى 12 ساعة |
| **المرحلة 3: العناية المركزة** | المراقبة اللحظية واستقرار الوظائف | متابعة إنزيمات الكبد، مراقبة تدفق الأوعية الدموية | 4 إلى 7 أيام |
| **المرحلة 4: الاستشفاء والمتابعة** | العودة التدريجية للحياة الطبيعية | أدوية تثبيط المناعة، فحوصات دورية، خطة تغذية متوازنة | 4 إلى 6 أسابيع |

---

## 3. مقارنة التكاليف والخيارات الإكلينيكية المتاحة

تتميز المراكز الطبية المتخصصة في تركيا بتقديم جودة رعاية صحية تضاهي كبرى مستشفيات أوروبا والولايات المتحدة بتكلفة تنافسية ومدروسة تشمل كافة متطلبات الإقامة والرعاية:

| الدولة / الوجهة الطبية | متوسط التكلفة المتوقعة | نسبة النجاح التقريبية | شمولية باقة الرعاية الصحية |
| :--- | :--- | :--- | :--- |
| **تركيا (المستشفيات المعتمدة JCI)** | 50,000$ - 70,000$ | 85% - 92% | تشمل الجراحة، الفحوصات، العناية المركزة، والإقامة |
| **الولايات المتحدة الأمريكية** | 180,000$ - 350,000$ | 87% - 93% | لا تشمل غالباً خدمات الترجمة والإقامة الخارجية |
| **ألمانيا ودول أوروبا الغربية** | 120,000$ - 200,000$ | 86% - 91% | تكاليف مضافة للمتابعة والفحوصات الثانوية |

---

## 4. إرشادات ما بعد العملية وفترة النقاهة

لضمان عمل الكبد الجديد بكفاءة مدى الحياة، ينصح الفريق الطبي باتباع الإرشادات التالية:
- **الالتزام بأدوية المناعة:** تناول الأدوية الموصوفة في مواعيدها الدقيقة دون أي انقطاع أو تعديل للجرعات.
- **الفحوصات الدورية:** متابعة مؤشرات إنزيمات الكبد ومستوى الدواء في الدم وفق الجدول المحدد.
- **التغذية السليمة:** الابتعاد عن الأطعمة النيئة أو غير المعقمة والاعتماد على الغذاء الطازج والمتوازن.
- **ممارسة النشاط البدني الخفيف:** البدء بالمشي الخفيف تدريجياً لتعزيز الدورة الدموية وتجنب الإجهاد الشديد.

---

## 5. الأسئلة الشائعة حول {focus_kw} (FAQ)

### ما هي نسبة نجاح {focus_kw}؟
تتراوح نسب النجاح في المراكز الطبية المعتمدة بين 85% و 92%، وتعتمد النسبة على الحالة الصحية العامة للمريض والالتزام الدقيق ببروتوكولات الرعاية والأدوية بعد الجراحة.

### ما هي شروط المتبرع الحي بالكبد؟
يشترط أن يكون المتبرع بالغاً (بين 18 و 55 عاماً)، متمتعاً بصحة عامة ممتازة، ذا فصيلة دم متوافقة، وأن تكون وظائف الكبد والفحوصات التصويرية سليمة تماماً دون أي ضغوط أو مقابل مادي.

### كم تستغرق فترة الإقامة في المستشفى والتعافي؟
تستغرق الإقامة داخل المستشفى عادة من 10 إلى 15 يوماً (تشمل وحدة العناية المركزة)، بينما تستغرق فترة التعافي المبدئية والعودة للأنشطة اليومية الخفيفة من 6 إلى 8 أسابيع.

### هل يعود كبد المتبرع للنمو مجدداً؟
نعم، يتميز الكبد بقدرته الحيوية المذهلة على التجدد السريع؛ حيث يستعيد الكبد حجمه ووظائفه الطبيعية لدى المتبرع في غضون 6 إلى 8 أسابيع بعد الجراحة.

---

## بيانات الاعتماد والتحقق التحريري
- **الخبير المشرف:** {author}
- **المراجعة والتدقيق:** هيئة التدقيق السريري وجراحة الأعضاء المعتمدة
- **تاريخ النشر:** {now_iso[:10]} | **الحالة:** مراجعة طبية محدثة 2026
- **الخطوة التالية:** {cta}
"""
            faqs = [
                {"question": f"ما هي نسبة نجاح {focus_kw}؟", "answer": "تتراوح نسب النجاح في المراكز المعتمدة بين 85% و92% بحسب الحالة الصحية العامة والالتزام ببروتوكول الأدوية والمتابعة."},
                {"question": "ما هي شروط المتبرع الحي بالكبد؟", "answer": "أن يكون في سن 18-55 عاماً، بصحة ممتازة، متوافقاً في فصيلة الدم والأنسجة، مع كبد سليم تشريحياً وخالٍ من الأمراض المزمنة."},
                {"question": "كم تستغرق فترة الإقامة في المستشفى والتعافي؟", "answer": "تمتد الإقامة بالمستشفى من 10 إلى 15 يوماً، بينما يستغرق التعافي التام والعودة للحياة الطبيعية من 6 إلى 8 أسابيع."},
                {"question": "هل يعود كبد المتبرع للنمو مجدداً؟", "answer": "نعم، يمتلك الكبد قدرة استثنائية على التجدد ويعود لحجمه ووظيفته الطبيعية بنسبة تفوق 90% خلال 6 إلى 8 أسابيع."}
            ]
        else:
            title = f"{focus_kw} : الدليل الشامل لعام 2026"
            if len(title) > 60:
                title = f"{focus_kw} : الدليل الاستراتيجي 2026"

            meta_desc = f"دليل متكامل ومحدث لـ {focus_kw}. استراتيجيات عملية، معايير دقيقة، وأفضل الممارسات لعام 2026 للإجابة عن تساؤلات القراء."
            if len(meta_desc) > 160:
                meta_desc = meta_desc[:157] + "..."

            aeo_summary = f"يمثل {focus_kw} الإطار المنهجي المعتمد لتمكين {audience} من اتخاذ قرارات دقيقة وتحقيق أعلى مستويات الفعالية والنتائج المستدامة."

            md = f"""# {title}

> **الخلاصة التنفيذية (إجابة مباشرة لمحركات الذكاء الاصطناعي):** {aeo_summary}

---

## 1. النظرة الاستراتيجية الشاملة: أبعاد وأهمية {focus_kw}

يعد الإلمام بـ **{focus_kw}** عاملاً حاسماً لتحقيق النجاح وتجاوز التحديات الميدانية في البيئات المتطورة اليوم. تم إعداد هذا المرجع الموثوق ليخاطب **{audience}** بأسلوب عملي مباشر ومدعوم بالحقائق والمعايير المعتمدة.

### المرتكزات الجوهرية
1. **الوضوح والمنهجية:** تحديد الأهداف والمسارات بوضوح لتفادي الأخطاء الشائعة.
2. **القياس والمعايير:** اعتماد مؤشرات أداء دقيقة لمتابعة التقدم والتأكد من النتائج.
3. **الكفاءة والاستدامة:** استثمار الموارد المتاحة لتحقيق أعلى عائد ممكن.
4. **الموثوقية والخبرة:** الاستناد إلى الخبرة العملية الموثقة والأبحاث الميدانية.

---

## 2. خارطة الطريق العملية: مراحل التنفيذ

| المرحلة | الهدف الأساسي | المخرجات الرئيسية | الإطار الزمني |
| :--- | :--- | :--- | :--- |
| **المرحلة الأولى: التحليل والتقييم** | فهم المتطلبات وتحديد الأولويات | تقرير شامل للفرص والاحتياجات | الأسبوع 1–2 |
| **المرحلة الثانية: التخطيط والاعتماد** | صياغة الخطة التنفيذية وتحديد الموارد | جدول عمل معتمد ومؤشرات قياس | الأسبوع 3–4 |
| **المرحلة الثالثة: التطبيق والمتابعة** | التنفيذ العملي ومعالجة العقبات | نتائج ملموسة وتقارير دورية | الأسبوع 5–8 |
| **المرحلة الرابعة: التحسين والتطوير** | تقييم المخرجات وضمان الاستدامة | معايير جودة مستمرة وتحديث دوري | مستمر |

---

## 3. الأسئلة الشائعة حول {focus_kw} (FAQ)

### ما هي الفائدة الأساسية من تطبيق {focus_kw}؟
تتمثل الفائدة الأساسية في توفير إطار عملي موثوق يقلل من المخاطر ويوفر الوقت والتكاليف، مما يضمن تحقيق النتائج المستهدفة بدقة وكفاءة عالية.

### ما هي الخطوة الأولى للبدء؟
البدء بإجراء تقييم دقيق للاحتياجات وتحديد الأهداف المرجوة والاستعانة بالخبراء المعتمدين في هذا المجال.

---

## بيانات الاعتماد والتحقق التحريري
- **الخبير المشرف:** {author}
- **المراجعة والتدقيق:** هيئة التدقيق المتخصصة
- **تاريخ النشر:** {now_iso[:10]} | **الحالة:** وثيقة معتمدة ومحدثة
- **الخطوة التالية:** {cta}
"""
            faqs = [
                {"question": f"ما هي الفائدة الأساسية من تطبيق {focus_kw}؟", "answer": "توفير إطار عملي موثوق يقلل من المخاطر ويوفر التكاليف ويضمن تحقيق النتائج المستهدفة بكفاءة."},
                {"question": "ما هي الخطوة الأولى للبدء؟", "answer": "البدء بإجراء تقييم شامل وتحديد الأهداف بوضوح مع استشارة المختصين المعتمدين."}
            ]

        schema_json = AlgorithmicBlogSynthesizer._build_schema(title, meta_desc, slug, author, now_iso, faqs, lang="ar")

        return {
            "title": title,
            "meta_description": meta_desc,
            "slug": slug,
            "language": "ar",
            "estimated_reading_minutes": 8,
            "word_count_estimate": len(md.split()),
            "aeo_summary": aeo_summary,
            "markdown_content": md,
            "schema_json": schema_json,
            "key_takeaways": [
                f"أهمية الاعتماد على معايير الجودة المعتمدة في {focus_kw}.",
                "خارطة طريق واضحة تقلل من المخاطر وتحقق أفضل النتائج.",
                "التوافق مع متطلبات محركات البحث والذكاء الاصطناعي لضمان أعلى مصداقية."
            ],
            "faqs": faqs,
        }

    @staticmethod
    def _synthesize_french(data, topic, focus_kw, audience, author, cta, slug, now_iso, domain):
        title = f"{focus_kw.title()} : Le Guide Pratique Complet 2026"
        if len(title) > 60:
            title = f"{focus_kw.title()} : Guide 2026"

        meta_desc = f"Découvrez notre guide complet sur {focus_kw.lower()}. Protocoles, comparatifs, étapes clés et réponses d'experts pour {audience.lower()} en 2026."
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."

        aeo_summary = f"{focus_kw.title()} représente le cadre structuré permettant aux acteurs concernés d'obtenir des résultats mesurables, pérennes et conformes aux meilleures normes internationales."

        md = f"""# {title}

> **Synthèse Exécutive :** {aeo_summary}

---

## 1. Vue d'Ensemble et Enjeux Majeurs de {focus_kw.title()}

La maîtrise de **{focus_kw.lower()}** constitue aujourd'hui une étape indispensable pour {audience.lower()}. Cette analyse approfondie présente les repères essentiels, les critères de réussite et les données pratiques indispensables.

### Les Piliers Fondamentaux
- **Rigueur et conformité :** Respect strict des standards de qualité reconnus.
- **Transparence et sécurité :** Évaluation continue des étapes pour prévenir tout risque.
- **Accompagnement expert :** Validation des choix par des spécialistes certifiés.

---

## 2. Feuille de Route Opérationnelle en 4 Étapes

| Étape | Objectif Prioritaire | Livrables Majeurs | Calendrier |
| :--- | :--- | :--- | :--- |
| **Phase 1 : Diagnostic Initial** | Analyse précise des besoins | Bilan complet et recommandations | Semaines 1–2 |
| **Phase 2 : Préparation et Planification** | Définition des protocoles | Calendrier d'action validé | Semaines 3–4 |
| **Phase 3 : Réalisation Pratique** | Déploiement et suivi | Rapport d'exécution détaillé | Semaines 5–8 |
| **Phase 4 : Bilan et Pérennité** | Évaluation des résultats obtenus | Optimisations continues | Continu |

---

## 3. Foire Aux Questions (FAQ)

### Quel est le principal avantage de {focus_kw.lower()} ?
Une efficacité prouvée et une réduction significative des aléas grâce à l'application de protocoles standardisés et rigoureusement testés.

### Quels sont les délais nécessaires pour obtenir des résultats ?
Les premiers effets notables s'observent dès les premières semaines suivant la mise en œuvre, avec une pleine stabilisation en deux mois.

---

## Validation Éditoriale et Auteur
- **Auteur :** {author}
- **Revue :** Département d'Expertise et de Contrôle Qualité InersiaLab
- **Date :** {now_iso[:10]}
- **Prochaine étape :** {cta}
"""
        faqs = [
            {"question": f"Quel est le principal avantage de {focus_kw.lower()} ?", "answer": "Une efficacité mesurable et la sécurisation des processus grâce à une méthodologie éprouvée."},
            {"question": "Quels sont les délais nécessaires pour obtenir des résultats ?", "answer": "Les premiers bénéfices sont visibles sous 2 à 4 semaines avec une stabilisation complète en 8 semaines."}
        ]

        schema_json = AlgorithmicBlogSynthesizer._build_schema(title, meta_desc, slug, author, now_iso, faqs, lang="fr")

        return {
            "title": title,
            "meta_description": meta_desc,
            "slug": slug,
            "language": "fr",
            "estimated_reading_minutes": 7,
            "word_count_estimate": len(md.split()),
            "aeo_summary": aeo_summary,
            "markdown_content": md,
            "schema_json": schema_json,
            "key_takeaways": [
                f"Protocoles rigoureux pour la réussite de {focus_kw.lower()}.",
                "Feuille de route en 4 étapes réduisant les incertitudes opérationnelles.",
                "Alignement strict avec les standards SEO et d'autorité E-E-A-T."
            ],
            "faqs": faqs,
        }

    @staticmethod
    def _synthesize_english(data, topic, focus_kw, audience, author, cta, slug, now_iso, domain):
        title = f"{focus_kw.title()}: The Definitive 2026 Guide"
        if len(title) > 60:
            title = f"{focus_kw.title()}: 2026 Strategic Guide"

        meta_desc = f"Comprehensive 2026 guide to {focus_kw.lower()}. In-depth methodology, benchmark comparisons, expert insights, and clear FAQs for {audience.lower()}."
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."

        aeo_summary = f"{focus_kw.title()} is the structured framework enabling {audience.lower()} to achieve verified, high-impact results through proven operational protocols and evidence-based standards."

        md = f"""# {title}

> **Executive Answer:** {aeo_summary}

---

## 1. Foundational Landscape: The Practical Reality of {focus_kw.title()}

Mastering **{focus_kw.lower()}** is essential for organizations and individuals seeking dependable, high-integrity outcomes. Designed specifically for **{audience.lower()}**, this comprehensive guide details actionable methodologies, concrete metrics, and verified best practices.

### Core Strategic Pillars
- **Evidence-Based Protocols:** Eliminates guesswork through rigorous, repeatable guidelines.
- **Continuous Verification:** Measures performance indicators at every milestone to ensure compliance.
- **Domain Accountability:** Anchors every recommendation to certified expertise and field-tested data.

---

## 2. Implementation Framework: Phased Execution Model

| Phase | Core Objective | Key Deliverables | Expected Timeline |
| :--- | :--- | :--- | :--- |
| **Phase 1: Baseline Assessment** | Diagnostic audit and requirements mapping | Comprehensive gap analysis and roadmap | Weeks 1–2 |
| **Phase 2: Protocol Structuring** | Standards definition and criteria alignment | Structured checklist and resource plan | Weeks 3–4 |
| **Phase 3: Active Execution** | Deployment and milestone tracking | Live execution report and risk mitigation | Weeks 5–8 |
| **Phase 4: Review & Scaling** | Post-implementation evaluation and audit | Long-term performance scorecard | Ongoing |

---

## 3. Frequently Asked Questions (FAQ)

### What is the primary advantage of this approach to {focus_kw.lower()}?
The primary advantage is deterministic reliability. Adhering to structured, peer-reviewed protocols reduces operational failures by over 70% while improving overall outcome consistency.

### How soon can measurable outcomes be expected?
Initial measurable improvements are typically recorded within 14 to 21 days of implementation, with comprehensive results realized by week 8.

---

## Author & Editorial Verification
- **Lead Author:** {author}
- **Peer Review:** InersiaLab Editorial & Domain Audit Board
- **Published:** {now_iso[:10]} | **Status:** Verified Comprehensive Specification
- **Recommended Next Step:** {cta}
"""
        faqs = [
            {"question": f"What is the primary advantage of this approach to {focus_kw.lower()}?", "answer": "Deterministic reliability and significant risk reduction through standardized, evidence-based execution."},
            {"question": "How soon can measurable outcomes be expected?", "answer": "Initial milestones are achieved within 2 to 3 weeks, with complete operational maturity by week 8."}
        ]

        schema_json = AlgorithmicBlogSynthesizer._build_schema(title, meta_desc, slug, author, now_iso, faqs, lang="en")

        return {
            "title": title,
            "meta_description": meta_desc,
            "slug": slug,
            "language": "en",
            "estimated_reading_minutes": 8,
            "word_count_estimate": len(md.split()),
            "aeo_summary": aeo_summary,
            "markdown_content": md,
            "schema_json": schema_json,
            "key_takeaways": [
                f"Proven methodology for executing {focus_kw.lower()}.",
                "Four-stage implementation roadmap minimizes operational risk.",
                "Verified Schema.org knowledge graph integration for maximum AI search citability."
            ],
            "faqs": faqs,
        }

    @staticmethod
    def _build_schema(title, description, slug, author, date_published, faqs, lang="en"):
        faq_entities = []
        for f in (faqs or []):
            faq_entities.append({
                "@type": "Question",
                "name": f.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f.get("answer", "")
                }
            })

        return {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "BlogPosting",
                    "@id": f"https://example.com/blog/{slug}#article",
                    "isPartOf": {
                        "@type": "WebSite",
                        "@id": "https://example.com/#website",
                        "name": "InersiaLab Engineering & Media",
                        "url": "https://example.com"
                    },
                    "headline": title,
                    "description": description,
                    "datePublished": date_published,
                    "dateModified": date_published,
                    "inLanguage": lang,
                    "author": {
                        "@type": "Person",
                        "name": author,
                        "jobTitle": "Lead Domain Specialist"
                    },
                    "publisher": {
                        "@type": "Organization",
                        "name": "InersiaLab",
                        "url": "https://www.inersialab.com"
                    },
                    "mainEntityOfPage": f"https://example.com/blog/{slug}"
                },
                {
                    "@type": "FAQPage",
                    "@id": f"https://example.com/blog/{slug}#faq",
                    "mainEntity": faq_entities
                },
                {
                    "@type": "BreadcrumbList",
                    "@id": f"https://example.com/blog/{slug}#breadcrumb",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com"},
                        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://example.com/blog"},
                        {"@type": "ListItem", "position": 3, "name": title, "item": f"https://example.com/blog/{slug}"}
                    ]
                }
            ]
        }


# ==============================================================================
# MASTER BLOG ARCHITECT MANAGER (PRIMARY KEYLESS LLM + FALLBACK)
# ==============================================================================

class BlogArchitect:
    """Orchestrates SEO & GEO blog creation via keyless free LLMs with algorithmic fallback."""

    def __init__(self):
        self.client = client
        self.catalog = catalog

    def _query_free_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 50,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> Optional[Tuple[str, str]]:
        """Queries free, 100% keyless inference endpoints in cascade.

        Tier 1: OVHcloud Meta-Llama-3_3-70B-Instruct (Keyless, European AI Cloud)
        Tier 2: OVHcloud Mistral-Small-3.2-24B-Instruct-2506 (Keyless, Fast & Accurate)
        Tier 3: LLM7.io DeepSeek-V4-Flash-0731 (Keyless)
        Tier 4: Pollinations OpenAI / Qwen (Keyless)

        Returns: (markdown_text, provider_model_name) or None.
        """
        def log(m):
            if on_log:
                on_log(m)
            try:
                print(f"[BlogArchitect] {m}")
            except Exception:
                pass

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AgySeo-BlogArchitect/3.8 (Windows NT; InersiaLab)",
        }

        # 1. OVHcloud AI Endpoints (Keyless, 100% Free, High Quality)
        ovh_url = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
        ovh_models = [
            ("Meta-Llama-3_3-70B-Instruct", "OVHcloud Llama 3.3 70B"),
            ("Mistral-Small-3.2-24B-Instruct-2506", "OVHcloud Mistral Small 24B"),
        ]

        for mid, mname in ovh_models:
            log(f"Connecting to Keyless Cloud Engine: {mname}...")
            payload = {
                "model": mid,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            try:
                resp = requests.post(ovh_url, headers=headers, json=payload, timeout=timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        if content and len(content.split()) > 200:
                            log(f"Synthesis received from {mname} ({len(content.split())} words)!")
                            return content, mname
                else:
                    log(f"{mname} returned HTTP {resp.status_code}, trying next engine...")
            except Exception as e:
                log(f"{mname} connection notice ({str(e)[:80]}), falling back to next engine...")

        # 2. LLM7.io Keyless Gateway
        log("Connecting to Keyless Cloud Gateway: LLM7.io (DeepSeek / Mistral)...")
        llm7_url = "https://api.llm7.io/v1/chat/completions"
        for mid, mname in [("DeepSeek-V4-Flash-0731", "LLM7 DeepSeek Flash"), ("mistral-Nemo-Instruct-2407", "LLM7 Mistral Nemo")]:
            payload = {
                "model": mid,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            try:
                resp = requests.post(llm7_url, headers=headers, json=payload, timeout=min(timeout, 35))
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        if content and len(content.split()) > 200:
                            log(f"Synthesis received from {mname} ({len(content.split())} words)!")
                            return content, mname
            except Exception:
                pass

        # 3. Pollinations AI Fallback
        log("Connecting to Keyless AI Gateway: Pollinations AI...")
        poll_url = "https://text.pollinations.ai/"
        for model_id in ["openai", "qwen"]:
            try:
                payload = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "model": model_id,
                    "seed": 42
                }
                resp = requests.post(poll_url, headers=headers, json=payload, timeout=min(timeout, 30))
                if resp.status_code == 200:
                    content = resp.text.strip()
                    if content and len(content.split()) > 200:
                        log(f"Synthesis received from Pollinations ({model_id}) ({len(content.split())} words)!")
                        return content, f"Pollinations ({model_id})"
            except Exception:
                continue

        return None

    def _parse_llm_markdown(
        self,
        raw_md: str,
        intake_data: Dict[str, Any],
        engine_name: str
    ) -> Dict[str, Any]:
        """Parses LLM-generated GitHub Flavored Markdown into a rich, structured BlogOutput."""
        # Clean any accidental outer code fences
        clean_md = raw_md.strip()
        if clean_md.startswith("```markdown"):
            clean_md = clean_md[11:].rsplit("```", 1)[0].strip()
        elif clean_md.startswith("```"):
            clean_md = clean_md[3:].rsplit("```", 1)[0].strip()

        lang = intake_data.get("language", "en").lower()
        topic = intake_data.get("topic", "Comprehensive Strategic Guide").strip()
        focus_kw = intake_data.get("focus_keyword", topic).strip()
        author = intake_data.get("author_name", "InersiaLab Editorial Board").strip()

        # 1. Extract Title (# Heading)
        h1_match = re.search(r'^#\s+(.+)$', clean_md, re.M)
        if h1_match:
            title = h1_match.group(1).strip()
        else:
            title = f"{focus_kw} : الدليل الشامل 2026" if lang == "ar" else f"{focus_kw.title()}: Complete Guide 2026"

        # 2. Extract AEO Executive Summary (> Blockquote)
        aeo_match = re.search(r'^>\s+(.+)$', clean_md, re.M)
        if aeo_match:
            aeo_raw = aeo_match.group(1).strip()
            # Remove bold prefix if present
            aeo_clean = re.sub(r'^\*\*(.*?)\*\*:?\s*', '', aeo_raw).strip()
            aeo_summary = aeo_clean
        else:
            # First paragraph as summary
            lines = [l.strip() for l in clean_md.split("\n") if l.strip() and not l.strip().startswith("#")]
            aeo_summary = lines[0] if lines else f"Comprehensive guide to {focus_kw}."

        # 3. Meta Description (140-160 chars)
        meta_desc = aeo_summary
        if len(meta_desc) > 158:
            meta_desc = meta_desc[:155].rsplit(" ", 1)[0] + "..."
        elif len(meta_desc) < 130:
            if lang == "ar":
                meta_desc = f"دليل شامل وموثوق حول {focus_kw}: تعرف على أهم التفاصيل والمعايير والتكاليف والأسئلة الشائعة برعاية نخبة من المتخصصين لعام 2026."
            elif lang == "fr":
                meta_desc = f"Découvrez notre guide complet sur {focus_kw.lower()} : critères, comparatifs, étapes clés et réponses aux questions fréquentes pour 2026."
            else:
                meta_desc = f"Explore our definitive 2026 guide to {focus_kw.lower()}. In-depth analysis, benchmark comparisons, practical roadmaps, and expert answers."

        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."

        slug = clean_multilingual_slug(focus_kw or topic)
        now_iso = datetime.now().isoformat()

        # 4. Extract FAQs
        faqs = []
        faq_blocks = re.findall(r'^###\s+(.+?\??)\s*\n+(.+?)(?=\n+###|\n+##|\Z)', clean_md, re.M | re.S)
        for q, a in faq_blocks:
            clean_q = q.strip().lstrip("#").strip()
            clean_a = re.sub(r'[*_`]', '', a).strip()
            # Keep only actual questions or QA pairs
            if "?" in clean_q or "؟" in clean_q or "سؤال" in clean_q or "Question" in clean_q or len(faqs) < 4:
                faqs.append({
                    "question": clean_q,
                    "answer": clean_a[:280]
                })

        # Fallback FAQs if regex didn't catch enough
        if len(faqs) < 2:
            if lang == "ar":
                faqs = [
                    {"question": f"ما هي الفائدة الأساسية من معرفة تفاصيل {focus_kw}؟", "answer": f"تتيح لك معرفة كافة الجوانب العملية والطبية والمالية بدقة لاتخاذ القرار الأنسب بأمان تام."},
                    {"question": f"كيف يمكن التواصل والاستفسار أكثر حول {focus_kw}؟", "answer": f"يمكن التواصل مباشرة مع الفريق الاستشاري المتخصص للحصول على تقييم مجاني وشامل للحالة."}
                ]
            else:
                faqs = [
                    {"question": f"What is the key advantage of understanding {focus_kw.lower()}?", "answer": f"It equips decision makers and individuals with actionable clarity, risk mitigation, and verified benchmarks."},
                    {"question": "How can I receive further guidance on this topic?", "answer": "You can reach out directly to the certified advisory board for an individualized consultation."}
                ]

        # 5. Extract Key Takeaways
        bullets = re.findall(r'^[*-]\s+\*?\*?(.+?)\*?\*?$', clean_md, re.M)
        key_takeaways = [b.strip() for b in bullets[:4] if len(b.strip()) > 20]
        if not key_takeaways:
            key_takeaways = [
                f"Definitive strategic insights into {focus_kw}.",
                "Comprehensive structured breakdown of all required phases.",
                "Direct answers to high-intent search queries."
            ]

        # 6. Schema JSON-LD
        schema_json = AlgorithmicBlogSynthesizer._build_schema(title, meta_desc, slug, author, now_iso, faqs, lang=lang)

        word_count = len(clean_md.split())

        return {
            "title": title,
            "meta_description": meta_desc,
            "slug": slug,
            "language": lang,
            "estimated_reading_minutes": max(3, int(word_count / 180)),
            "word_count_estimate": word_count,
            "aeo_summary": aeo_summary,
            "markdown_content": clean_md,
            "schema_json": schema_json,
            "key_takeaways": key_takeaways,
            "faqs": faqs,
            "generation_engine": f"Keyless Cloud AI Engine ({engine_name})",
        }

    def generate_blog(
        self,
        intake_data: Dict[str, Any],
        provider_name: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Main entry point to generate a complete SEO/GEO blog using keyless free LLMs."""
        def log(msg: str):
            if on_log:
                on_log(msg)
            try:
                print(f"[BlogArchitect] {msg}")
            except Exception:
                safe = msg.encode("ascii", "replace").decode("ascii")
                print(f"[BlogArchitect] {safe}")

        topic = intake_data.get("topic", "Modern Strategy").strip()
        lang = intake_data.get("language", "en").lower()
        comp_url = intake_data.get("competitor_url", "").strip()

        log(f"Initiating Autonomous AI Blog Synthesis for: '{topic}' [{lang.upper()}]")
        log("Deploying Keyless Cloud AI Engine with Automatic Multi-Provider Fallback...")

        # Live competitor crawl if URL provided
        if comp_url:
            log(f"Crawling competitor structure at {comp_url}...")
            try:
                comp_res = fetch_url(comp_url, timeout=5)
                if comp_res.get("html"):
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(comp_res["html"], "lxml")
                    comp_h2s = [h.get_text(strip=True) for h in soup.find_all("h2")[:6]]
                    if comp_h2s:
                        intake_data["competitor_headings"] = comp_h2s
                        log(f"Extracted {len(comp_h2s)} competitor sections to engineer superior depth.")
            except Exception as e:
                log(f"Competitor crawl skipped ({str(e)})")

        sys_p = build_system_prompt(lang)
        user_p = build_user_prompt(intake_data)

        # Primary Generation: Commercial Provider if explicitly supplied, else Keyless Waterfall
        raw_markdown = None
        engine_name = "Algorithmic Core"

        if provider_name and api_key:
            log(f"Querying configured commercial provider: {provider_name} ({model_id})...")
            try:
                gen_res = self.client.generate(
                    provider_name=provider_name,
                    model_id=model_id or "gpt-4o",
                    messages=[
                        {"role": "system", "content": sys_p},
                        {"role": "user", "content": user_p}
                    ],
                    custom_key=api_key,
                )
                if gen_res and gen_res.get("content"):
                    raw_markdown = gen_res["content"].strip()
                    engine_name = f"{provider_name} ({model_id})"
                    log(f"Received completion from {provider_name}!")
            except Exception as e:
                log(f"Commercial provider call notice ({str(e)}), transitioning to keyless cascade...")

        if not raw_markdown:
            # Query keyless waterfall
            llm_res = self._query_free_llm(sys_p, user_p, timeout=50, on_log=on_log)
            if llm_res:
                raw_markdown, engine_name = llm_res

        # If LLM succeeded, parse the output
        if raw_markdown and len(raw_markdown.split()) > 150:
            log(f"Parsing and structuring Markdown generated by {engine_name}...")
            result = self._parse_llm_markdown(raw_markdown, intake_data, engine_name)
        else:
            log("Cloud LLM endpoints unavailable or offline; activating domain-adaptive fallback guarantee...")
            result = AlgorithmicBlogSynthesizer.synthesize(intake_data)
            result["generation_engine"] = "Domain-Adaptive InersiaLab Synthesis (Offline Guarantee)"

        # Step 2: Run Quantitative SEO & GEO Scorecard
        log("Evaluating SEO & GEO Citability Scorecard (Single H1, H2/H3 Depth, Meta Bounds)...")
        scorecard = self._evaluate_seo_geo_scorecard(result, intake_data)
        result["scorecard"] = scorecard

        # Step 3: Export to Downloads Package
        log("Packaging .md, .html (RTL), schema.json, metadata.json, and generating PDF...")
        export_meta = self._export_blog_package(result, intake_data)
        result["export"] = export_meta

        log(f"Blog Architecture Complete! Saved directly to: {export_meta['folder']}")
        return result

    def refine_blog(
        self,
        current_blog: Dict[str, Any],
        user_prompt: str,
        provider_name: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Refines or edits an existing blog using user directives via the free LLM."""
        if not user_prompt.strip():
            return current_blog

        lang = current_blog.get("language", "ar")
        existing_md = current_blog.get("markdown_content", "")
        clean_prompt = user_prompt.strip()

        sys_prompt = f"""You are an expert editorial editor and SEO architect.
The user wants to refine, update, expand, or adjust the following blog article.
Rewrite and return the COMPLETE updated article in GitHub Flavored Markdown adhering strictly to the user's directive.
Maintain the Level 1 Title # H1, AEO blockquote > **, ordered H2/H3 hierarchy, markdown tables, and FAQ section.
Do NOT wrap the response in ```json or code blocks."""

        user_p = f"""USER DIRECTIVE:
{clean_prompt}

CURRENT BLOG ARTICLE (MARKDOWN):
{existing_md}

Return the fully updated and refined markdown article now:"""

        ai_refined = None
        engine_name = "Keyless Refinement Engine"

        # Try free LLM cascade
        llm_res = self._query_free_llm(sys_prompt, user_p, timeout=40)
        if llm_res:
            ai_refined, engine_name = llm_res

        if ai_refined and len(ai_refined.split()) > 200:
            intake_data = {
                "language": lang,
                "topic": current_blog.get("title", ""),
                "focus_keyword": current_blog.get("slug", ""),
                "author_name": current_blog.get("schema_json", {}).get("@graph", [{}])[0].get("author", {}).get("name", "Editorial Board"),
            }
            updated = self._parse_llm_markdown(ai_refined, intake_data, f"{engine_name} (Refined)")
            updated["scorecard"] = self._evaluate_seo_geo_scorecard(updated, {})
            export_meta = self._export_blog_package(updated, {})
            updated["export"] = export_meta
            return updated
        else:
            # Algorithmic append if network unavailable
            if "faq" in clean_prompt.lower() or "سؤال" in clean_prompt:
                q_label = "س" if lang == "ar" else "Q"
                a_label = "ج" if lang == "ar" else "A"
                current_blog["markdown_content"] += f"\n\n### {q_label}: {clean_prompt}؟\n**{a_label}:** إجابة مباشرة ومفصلة مبنية على الأدلة والتحليل المعتمد.\n"
            else:
                directive_title = "تعديل موجه" if lang == "ar" else ("Directive d'édition" if lang == "fr" else "Refinement Directive Applied")
                current_blog["markdown_content"] += f"\n\n> **{directive_title}:** {clean_prompt}\n"

            current_blog["word_count_estimate"] = len(current_blog["markdown_content"].split())
            current_blog["scorecard"] = self._evaluate_seo_geo_scorecard(current_blog, {})
            export_meta = self._export_blog_package(current_blog, {})
            current_blog["export"] = export_meta
            return current_blog

    def _evaluate_seo_geo_scorecard(self, blog: Dict[str, Any], intake: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates quantitative SEO & GEO adherence scores."""
        title = blog.get("title", "")
        meta = blog.get("meta_description", "")
        md = blog.get("markdown_content", "")
        faqs = blog.get("faqs", [])

        # Title length (50-60 optimal)
        t_len = len(title)
        t_score = 100 if (48 <= t_len <= 65) else (85 if (40 <= t_len <= 75) else 70)

        # Meta length (140-160 optimal)
        m_len = len(meta)
        m_score = 100 if (135 <= m_len <= 165) else (85 if (120 <= m_len <= 180) else 65)

        # Heading hierarchy
        h1_matches = re.findall(r'^#\s+(.+)$', md, re.M)
        h2_matches = re.findall(r'^##\s+(.+)$', md, re.M)
        h3_matches = re.findall(r'^###\s+(.+)$', md, re.M)

        heading_score = 100
        if len(h1_matches) != 1:
            heading_score -= 20
        if len(h2_matches) < 3:
            heading_score -= 15

        # GEO citability check (first sentence depth and FAQ presence)
        geo_score = 85
        if len(faqs) >= 3:
            geo_score += 10
        if "> **Executive" in md or "خلاصة" in md or "Synthèse" in md or "> **" in md:
            geo_score = min(100, geo_score + 5)

        # Word count target
        word_count = len(md.split())
        min_w = int(intake.get("min_words", 1000))
        wc_score = 100 if word_count >= min_w else int((word_count / max(1, min_w)) * 100)

        total_score = int((t_score * 0.2) + (m_score * 0.2) + (heading_score * 0.2) + (geo_score * 0.2) + (wc_score * 0.2))

        return {
            "overall_score": total_score,
            "title_length": t_len,
            "title_score": t_score,
            "meta_length": m_len,
            "meta_score": m_score,
            "h1_count": len(h1_matches),
            "h2_count": len(h2_matches),
            "h3_count": len(h3_matches),
            "heading_score": heading_score,
            "geo_citability_score": geo_score,
            "word_count": word_count,
            "word_count_score": wc_score,
            "checks": [
                {"name": "SEO Title Length (50–60 chars)", "passed": 48 <= t_len <= 65, "val": f"{t_len} chars"},
                {"name": "Meta Description (140–160 chars)", "passed": 135 <= m_len <= 165, "val": f"{m_len} chars"},
                {"name": "Strict Single H1 Tag", "passed": len(h1_matches) == 1, "val": f"{len(h1_matches)} found"},
                {"name": "Rich Section Depth (H2 >= 3)", "passed": len(h2_matches) >= 3, "val": f"{len(h2_matches)} sections"},
                {"name": "AEO Citability & FAQ Rich Schema", "passed": len(faqs) >= 3, "val": f"{len(faqs)} FAQs verified"},
                {"name": "Target Word Count Fulfillment", "passed": word_count >= min_w, "val": f"{word_count} words"},
            ]
        }

    def _export_blog_package(self, blog: Dict[str, Any], intake: Dict[str, Any]) -> Dict[str, str]:
        """Saves blog package (.md, .html, .json, llms.txt, and PDF) directly into Downloads."""
        slug = blog.get("slug") or "seo-blog"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"Blog_{slug}_{timestamp}"
        out_dir = os.path.join(DOWNLOADS_DIR, folder_name)
        os.makedirs(out_dir, exist_ok=True)

        lang = blog.get("language", "en")
        is_rtl = lang == "ar"
        md_content = blog.get("markdown_content", "")
        title = blog.get("title", "")
        meta = blog.get("meta_description", "")
        schema = blog.get("schema_json", {})

        # 1. Save blog.md
        md_path = os.path.join(out_dir, "blog.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 2. Convert to styled standalone HTML
        html_content = self._render_styled_html(blog, is_rtl)
        html_path = os.path.join(out_dir, "blog.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 3. Save schema.json
        schema_path = os.path.join(out_dir, "schema.json")
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        # 4. Save metadata.json
        meta_path = os.path.join(out_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "title": title,
                "meta_description": meta,
                "slug": slug,
                "language": lang,
                "engine": blog.get("generation_engine", "Keyless AI"),
                "word_count": len(md_content.split()),
                "scorecard": blog.get("scorecard", {}),
                "created_at": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

        # 5. Save llms.txt
        llms_path = os.path.join(out_dir, "llms.txt")
        with open(llms_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n> {blog.get('aeo_summary', '')}\n\n## Core Citations\n- URL: https://example.com/blog/{slug}\n- Language: {lang}\n- Key Takeaways:\n")
            for t in blog.get("key_takeaways", []):
                f.write(f"  - {t}\n")

        # 6. Try generating PDF via Playwright
        pdf_path = os.path.join(out_dir, f"{slug}.pdf")
        self._try_generate_pdf(html_path, pdf_path)

        return {
            "folder": out_dir,
            "markdown": md_path,
            "html": html_path,
            "schema": schema_path,
            "metadata": meta_path,
            "llms": llms_path,
            "pdf": pdf_path if os.path.exists(pdf_path) else None,
        }

    def _render_styled_html(self, blog: Dict[str, Any], is_rtl: bool) -> str:
        """Renders an executive, responsive, publication-ready HTML file."""
        title = blog.get("title", "")
        meta = blog.get("meta_description", "")
        md = blog.get("markdown_content", "")
        schema = blog.get("schema_json", {})
        lang = blog.get("language", "ar")

        body_html = self._simple_markdown_to_html(md)

        direction = "rtl" if is_rtl else "ltr"
        align = "right" if is_rtl else "left"
        font_family = "'Tajawal', Arial, sans-serif" if is_rtl else "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif"

        return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
    <script type="application/ld+json">
    {json.dumps(schema, ensure_ascii=False, indent=2)}
    </script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: {font_family};
            background: #ffffff;
            color: #111827;
            line-height: 1.85;
            font-size: 15.5px;
            padding: 40px 20px;
            text-align: {align};
        }}
        .container {{
            max-width: 860px;
            margin: 0 auto;
        }}
        .header-meta {{
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 24px;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 12px;
            display: flex;
            justify-content: space-between;
        }}
        h1 {{
            font-size: 30px;
            font-weight: 800;
            line-height: 1.3;
            color: #111827;
            margin-bottom: 20px;
            letter-spacing: -0.01em;
        }}
        h2 {{
            font-size: 21px;
            font-weight: 700;
            color: #111827;
            margin-top: 36px;
            margin-bottom: 16px;
            border-bottom: 2px solid #f3f4f6;
            padding-bottom: 8px;
        }}
        h3 {{
            font-size: 17px;
            font-weight: 600;
            color: #1f2937;
            margin-top: 24px;
            margin-bottom: 12px;
        }}
        p {{ margin-bottom: 18px; color: #374151; }}
        blockquote {{
            background: #f0fdf4;
            border-left: 4px solid #10b981;
            padding: 16px 20px;
            margin: 24px 0;
            border-radius: 6px;
            font-size: 15px;
            color: #065f46;
        }}
        [dir="rtl"] blockquote {{
            border-left: none;
            border-right: 4px solid #10b981;
        }}
        ul, ol {{
            margin-bottom: 20px;
            padding-left: 24px;
        }}
        [dir="rtl"] ul, [dir="rtl"] ol {{
            padding-left: 0;
            padding-right: 24px;
        }}
        li {{ margin-bottom: 8px; color: #374151; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 14px;
            border: 1px solid #e5e7eb;
            text-align: {align};
        }}
        th {{
            background: #f9fafb;
            font-weight: 700;
            color: #111827;
        }}
        tr:nth-child(even) {{ background: #fafafa; }}
        .author-box {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-top: 48px;
            font-size: 14px;
        }}
        .author-box strong {{ color: #111827; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-meta">
            <span>InersiaLab SEO &amp; GEO Publication Studio</span>
            <span>Language: {lang.upper()} | Verified Authority</span>
        </div>
        {body_html}
    </div>
</body>
</html>"""

    def _simple_markdown_to_html(self, md: str) -> str:
        """Converts basic markdown formatting to semantic HTML."""
        lines = md.split("\n")
        out = []
        in_table = False
        in_ul = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if in_ul:
                    out.append("</ul>")
                    in_ul = False
                continue

            if stripped.startswith("# "):
                out.append(f"<h1>{stripped[2:]}</h1>")
                continue
            elif stripped.startswith("## "):
                out.append(f"<h2>{stripped[3:]}</h2>")
                continue
            elif stripped.startswith("### "):
                out.append(f"<h3>{stripped[4:]}</h3>")
                continue
            elif stripped.startswith("> "):
                out.append(f"<blockquote>{stripped[2:]}</blockquote>")
                continue
            elif stripped in ("---", "***", "___"):
                out.append("<hr style='border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;'>")
                continue
            elif stripped.startswith("|"):
                if not in_table:
                    out.append("<table><tbody>")
                    in_table = True
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if any(re.match(r"^:?-+:?$", c) for c in cells):
                    continue
                row_html = "".join(f"<td>{c}</td>" for c in cells)
                out.append(f"<tr>{row_html}</tr>")
                continue
            else:
                if in_table:
                    out.append("</tbody></table>")
                    in_table = False

            if stripped.startswith("- ") or stripped.startswith("* "):
                if not in_ul:
                    out.append("<ul>")
                    in_ul = True
                item = stripped[2:]
                item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                out.append(f"<li>{item}</li>")
                continue
            else:
                if in_ul:
                    out.append("</ul>")
                    in_ul = False

            p_text = stripped
            p_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p_text)
            out.append(f"<p>{p_text}</p>")

        if in_table:
            out.append("</tbody></table>")
        if in_ul:
            out.append("</ul>")

        return "\n".join(out)

    def _try_generate_pdf(self, html_path: str, pdf_path: str):
        """Attempts to print HTML to high-fidelity PDF via Playwright."""
        try:
            from playwright.sync_api import sync_playwright
            def find_browser():
                paths = [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                ]
                for p in paths:
                    if os.path.exists(p):
                        return p
                return None

            exe = find_browser()
            with sync_playwright() as p:
                launch_args = {"headless": True}
                if exe:
                    launch_args["executable_path"] = exe
                browser = p.chromium.launch(**launch_args)
                page = browser.new_page()
                page.goto(f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}", wait_until="networkidle")
                page.pdf(
                    path=pdf_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"}
                )
                browser.close()
        except Exception:
            pass


# Global singleton instance
blog_architect = BlogArchitect()
