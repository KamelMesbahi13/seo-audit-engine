"""InersiaLab Software Department — SEO Audit & Pre-Launch Architect Desktop GUI.

Minimalist, executive desktop user interface:
- Tab 1: Existing Website Audit (Monochrome real-time log, progress, PDF reports)
- Tab 2: New Website Architect (Pre-Launch architecture guide & turnkey starter kit generator)
- Strictly NO colors (monochrome palette: black, white, neutral gray + subtle accents).
- Strictly NO icons or emojis.
"""

import os
import sys
import threading
import queue
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# Ensure skill directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Import blueprint module
try:
    from blueprint import (
        QUESTIONNAIRE_SCHEMA,
        BlueprintSynthesizer,
        generate_blueprint_pdf,
        generate_blueprint_starter_kit,
    )
except ImportError:
    QUESTIONNAIRE_SCHEMA = []
    BlueprintSynthesizer = None
    generate_blueprint_pdf = None
    generate_blueprint_starter_kit = None

# Import content generator module
try:
    from content_generator import (
        INDUSTRY_PRESETS,
        ContentSynthesizer,
        export_content,
        _render_page_markdown,
        _render_page_html,
        _render_master_document,
    )
except ImportError:
    INDUSTRY_PRESETS = {}
    ContentSynthesizer = None
    export_content = None
    _render_page_markdown = None
    _render_page_html = None
    _render_master_document = None


class StdoutRedirector:
    """Redirects stdout/stderr to a thread-safe queue."""
    def __init__(self, queue_obj):
        self.queue_obj = queue_obj

    def write(self, string):
        if string:
            self.queue_obj.put(string)

    def flush(self):
        pass


class SEOAuditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("InersiaLab — SEO Audit & Architecture Suite")
        self.root.geometry("860x720")
        self.root.minsize(760, 600)
        self.root.configure(bg="#ffffff")

        self.log_queue = queue.Queue()
        self.audit_thread = None
        self.blueprint_thread = None
        self.content_thread = None
        self.is_running = False
        self.is_generating_bp = False
        self.is_generating_content = False
        self.cancel_event = threading.Event()
        self.last_pdf_path = None
        self.last_bp_pdf_path = None
        self.last_starter_dir = None
        self.last_content_results = None
        self.last_content_dir = None
        self.cg_page_vars = {}
        self.cg_custom_pages = []

        self._setup_styles()
        self._build_ui()
        self._poll_log_queue()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Configure monochrome ttk styles
        self.style.configure("TProgressbar",
            troughcolor="#f3f4f6",
            background="#111827",
            bordercolor="#e5e7eb",
            lightcolor="#111827",
            darkcolor="#111827"
        )
        self.style.configure("TNotebook", background="#ffffff", borderwidth=0)
        self.style.configure("TNotebook.Tab",
            background="#f3f4f6",
            foreground="#4b5563",
            font=("Segoe UI", 9, "bold"),
            padding=[16, 8],
            borderwidth=1,
            bordercolor="#e5e7eb"
        )
        self.style.map("TNotebook.Tab",
            background=[("selected", "#111827")],
            foreground=[("selected", "#ffffff")]
        )

    def _build_ui(self):
        # Top Header Frame
        header_frame = tk.Frame(self.root, bg="#ffffff", padx=24, pady=14)
        header_frame.pack(fill=tk.X)

        org_label = tk.Label(
            header_frame,
            text="INERSIALAB SOFTWARE DEPARTMENT",
            font=("Segoe UI", 9, "bold"),
            fg="#4b5563",
            bg="#ffffff"
        )
        org_label.pack(anchor="w")

        title_label = tk.Label(
            header_frame,
            text="SEO Audit & Pre-Launch Architect",
            font=("Segoe UI", 18, "bold"),
            fg="#111827",
            bg="#ffffff"
        )
        title_label.pack(anchor="w", pady=(2, 0))

        subtitle_label = tk.Label(
            header_frame,
            text="Technical SEO, Core Web Vitals, Schema Knowledge Graphs & Generative AI (GEO) Citability",
            font=("Segoe UI", 9),
            fg="#6b7280",
            bg="#ffffff"
        )
        subtitle_label.pack(anchor="w", pady=(2, 6))

        # Thin monochrome separator rule
        rule = tk.Frame(header_frame, height=1, bg="#e5e7eb")
        rule.pack(fill=tk.X, pady=(4, 0))

        # Main Tabs Notebook
        self.notebook = ttk.Notebook(self.root, style="TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Tab 1: Existing Website Audit
        self.tab_audit = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_audit, text="  1. Existing Website Audit  ")
        self._build_audit_tab(self.tab_audit)

        # Tab 2: New Website Architect
        self.tab_blueprint = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_blueprint, text="  2. New Website Architect (Pre-Launch)  ")
        self._build_blueprint_tab(self.tab_blueprint)

        # Tab 3: Page Content Architect
        self.tab_content = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_content, text="  3. Page Content Architect  ")
        self._build_content_tab(self.tab_content)

    # -----------------------------------------------------------------------
    # TAB 1: EXISTING WEBSITE AUDIT
    # -----------------------------------------------------------------------
    def _build_audit_tab(self, parent):
        inputs_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=12)
        inputs_frame.pack(fill=tk.X)

        # URL Input
        url_label = tk.Label(
            inputs_frame,
            text="Target Website URL",
            font=("Segoe UI", 9, "bold"),
            fg="#111827",
            bg="#ffffff"
        )
        url_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.url_var = tk.StringVar(value="https://")
        self.url_entry = tk.Entry(
            inputs_frame,
            textvariable=self.url_var,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", ipady=6, padx=(0, 12))

        # Max Pages Input
        pages_label = tk.Label(
            inputs_frame,
            text="Crawl Scope (0=All)",
            font=("Segoe UI", 9, "bold"),
            fg="#111827",
            bg="#ffffff"
        )
        pages_label.grid(row=0, column=1, sticky="w", pady=(0, 4))

        self.pages_var = tk.StringVar(value="0")
        self.pages_entry = tk.Entry(
            inputs_frame,
            textvariable=self.pages_var,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1,
            width=10,
            highlightthickness=0
        )
        self.pages_entry.grid(row=1, column=1, sticky="w", ipady=6, padx=(0, 12))

        # Report Mode Dropdown
        mode_label = tk.Label(
            inputs_frame,
            text="Report Mode",
            font=("Segoe UI", 9, "bold"),
            fg="#111827",
            bg="#ffffff"
        )
        mode_label.grid(row=0, column=2, sticky="w", pady=(0, 4))

        self.mode_var = tk.StringVar(value="Detailed")
        self.mode_combo = ttk.Combobox(
            inputs_frame,
            textvariable=self.mode_var,
            values=["Detailed", "Short", "Both"],
            state="readonly",
            width=10,
            font=("Segoe UI", 9)
        )
        self.mode_combo.grid(row=1, column=2, sticky="w", ipady=4, padx=(0, 14))

        # Action Buttons Frame
        btn_frame = tk.Frame(inputs_frame, bg="#ffffff")
        btn_frame.grid(row=1, column=3, sticky="e")

        self.btn_start = tk.Button(
            btn_frame,
            text="START AUDIT",
            font=("Segoe UI", 9, "bold"),
            bg="#111827",
            fg="#ffffff",
            activebackground="#374151",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=16,
            pady=7,
            cursor="hand2",
            command=self.start_audit
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = tk.Button(
            btn_frame,
            text="STOP",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#6b7280",
            activebackground="#f3f4f6",
            activeforeground="#111827",
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.stop_audit
        )
        self.btn_stop.pack(side=tk.LEFT)

        inputs_frame.columnconfigure(0, weight=1)

        # Status & Progress Frame
        status_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=6)
        status_frame.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Status: Ready to audit")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg="#374151",
            bg="#ffffff"
        )
        self.status_label.pack(anchor="w", pady=(0, 4))

        self.progress_bar = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            mode="indeterminate",
            style="TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X)

        # Activity Log Frame
        log_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=6)
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_title = tk.Label(
            log_frame,
            text="Audit Execution Log",
            font=("Segoe UI", 9, "bold"),
            fg="#111827",
            bg="#ffffff"
        )
        log_title.pack(anchor="w", pady=(0, 4))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Bottom Bar: Actions & Results
        bottom_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=10)
        bottom_frame.pack(fill=tk.X)

        self.btn_open_pdf = tk.Button(
            bottom_frame,
            text="OPEN REPORT PDF",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#111827",
            relief="solid",
            bd=1,
            padx=14,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.open_last_pdf
        )
        self.btn_open_pdf.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_open_folder = tk.Button(
            bottom_frame,
            text="OPEN DOWNLOADS FOLDER",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#4b5563",
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.open_downloads_folder
        )
        self.btn_open_folder.pack(side=tk.LEFT)

        self.info_label = tk.Label(
            bottom_frame,
            text="Reports saved to Downloads",
            font=("Segoe UI", 8),
            fg="#9ca3af",
            bg="#ffffff"
        )
        self.info_label.pack(side=tk.RIGHT, pady=4)

    # -----------------------------------------------------------------------
    # TAB 2: NEW WEBSITE ARCHITECT (PRE-LAUNCH BLUEPRINT)
    # -----------------------------------------------------------------------
    def _build_blueprint_tab(self, parent):
        # Description banner
        desc_frame = tk.Frame(parent, bg="#f9fafb", padx=16, pady=10, relief="solid", bd=1)
        desc_frame.pack(fill=tk.X, padx=16, pady=(12, 8))

        tk.Label(
            desc_frame,
            text="Pre-Launch Architecture Guide & Turnkey Starter Kit Generator",
            font=("Segoe UI", 10, "bold"),
            fg="#111827",
            bg="#f9fafb"
        ).pack(anchor="w")

        tk.Label(
            desc_frame,
            text="Configure your target technical specifications. Generates a definitive pre-launch engineering guide and exports turnkey production starter files (robots.txt, llms.txt, <head> boilerplate, and schemas).",
            font=("Segoe UI", 8),
            fg="#4b5563",
            bg="#f9fafb",
            wraplength=780,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # Questionnaire Form Frame
        form_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=6)
        form_frame.pack(fill=tk.X)

        # Row 1: Brand & Domain
        r1 = tk.Frame(form_frame, bg="#ffffff")
        r1.pack(fill=tk.X, pady=4)

        tk.Label(r1, text="Brand Name:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_brand_var = tk.StringVar(value="InersiaLab")
        tk.Entry(r1, textvariable=self.bp_brand_var, font=("Segoe UI", 9), relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))

        tk.Label(r1, text="Primary Domain:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_domain_var = tk.StringVar(value="https://example.com")
        tk.Entry(r1, textvariable=self.bp_domain_var, font=("Segoe UI", 9), relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 2: Archetype & Stack
        r2 = tk.Frame(form_frame, bg="#ffffff")
        r2.pack(fill=tk.X, pady=4)

        tk.Label(r2, text="Site Archetype:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_type_var = tk.StringVar(value="Corporate B2B Services")
        self.bp_type_combo = ttk.Combobox(
            r2, textvariable=self.bp_type_var, state="readonly", font=("Segoe UI", 9),
            values=["Corporate B2B Services", "SaaS Web Application", "E-Commerce Store", "Local Physical Business", "Content Publisher / Blog", "Creative Portfolio"]
        )
        self.bp_type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))

        tk.Label(r2, text="Frontend Stack:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_stack_var = tk.StringVar(value="Next.js (App Router)")
        self.bp_stack_combo = ttk.Combobox(
            r2, textvariable=self.bp_stack_var, state="readonly", font=("Segoe UI", 9),
            values=["Next.js (App Router)", "Astro (Island Architecture)", "React + Vite SPA", "WordPress", "Shopify", "Nuxt.js (Vue 3)", "Modern Semantic HTML5"]
        )
        self.bp_stack_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 3: Hosting & Language
        r3 = tk.Frame(form_frame, bg="#ffffff")
        r3.pack(fill=tk.X, pady=4)

        tk.Label(r3, text="Hosting / Edge:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_hosting_var = tk.StringVar(value="Cloudflare Pages / Workers")
        self.bp_hosting_combo = ttk.Combobox(
            r3, textvariable=self.bp_hosting_var, state="readonly", font=("Segoe UI", 9),
            values=["Cloudflare Pages / Workers", "Vercel Edge Network", "Linux VPS (Ubuntu + Nginx)", "Netlify Edge", "AWS CloudFront / GCP", "Apache / cPanel"]
        )
        self.bp_hosting_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))

        tk.Label(r3, text="Languages & RTL:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_lang_var = tk.StringVar(value="Bilingual (EN & FR)")
        self.bp_lang_combo = ttk.Combobox(
            r3, textvariable=self.bp_lang_var, state="readonly", font=("Segoe UI", 9),
            values=["Single Language (EN)", "Single Language (FR)", "Single Language (AR RTL)", "Bilingual (EN & FR)", "Multilingual + RTL (EN, FR, AR)", "Global Multi-Regional"]
        )
        self.bp_lang_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 4: GEO & Core Web Vitals
        r4 = tk.Frame(form_frame, bg="#ffffff")
        r4.pack(fill=tk.X, pady=4)

        tk.Label(r4, text="GEO Ambition:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_geo_var = tk.StringVar(value="Maximum AI Citability (SearchGPT, Perplexity, Claude)")
        self.bp_geo_combo = ttk.Combobox(
            r4, textvariable=self.bp_geo_var, state="readonly", font=("Segoe UI", 9),
            values=["Maximum AI Citability (SearchGPT, Perplexity, Claude)", "Balanced Hybrid (Google Search + AI Overviews)", "Traditional Google SERP Only"]
        )
        self.bp_geo_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))

        tk.Label(r4, text="CWV Target:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=14, anchor="w").pack(side=tk.LEFT)
        self.bp_cwv_var = tk.StringVar(value="Ultra-Fast (<1.0s LCP, 100 Score)")
        self.bp_cwv_combo = ttk.Combobox(
            r4, textvariable=self.bp_cwv_var, state="readonly", font=("Segoe UI", 9),
            values=["Ultra-Fast (<1.0s LCP, 100 Score)", "Enterprise Standard (<1.8s LCP, 90+ Score)", "Standard (<2.5s LCP)"]
        )
        self.bp_cwv_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Action Buttons
        act_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=10)
        act_frame.pack(fill=tk.X)

        self.btn_gen_bp = tk.Button(
            act_frame,
            text="GENERATE PRE-LAUNCH BLUEPRINT & STARTER KIT",
            font=("Segoe UI", 9, "bold"),
            bg="#111827",
            fg="#ffffff",
            activebackground="#374151",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.start_blueprint_generation
        )
        self.btn_gen_bp.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_open_bp_pdf = tk.Button(
            act_frame,
            text="OPEN BLUEPRINT PDF",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#111827",
            relief="solid",
            bd=1,
            padx=14,
            pady=7,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.open_blueprint_pdf
        )
        self.btn_open_bp_pdf.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_open_starter = tk.Button(
            act_frame,
            text="OPEN STARTER KIT FOLDER",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#4b5563",
            relief="solid",
            bd=1,
            padx=14,
            pady=7,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.open_starter_folder
        )
        self.btn_open_starter.pack(side=tk.LEFT)

        # Progress / Status
        bp_status_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=4)
        bp_status_frame.pack(fill=tk.X)

        self.bp_status_var = tk.StringVar(value="Status: Ready to configure")
        self.bp_status_label = tk.Label(
            bp_status_frame,
            textvariable=self.bp_status_var,
            font=("Segoe UI", 9),
            fg="#374151",
            bg="#ffffff"
        )
        self.bp_status_label.pack(anchor="w", pady=(0, 4))

        self.bp_progress_bar = ttk.Progressbar(
            bp_status_frame,
            orient="horizontal",
            mode="indeterminate",
            style="TProgressbar"
        )
        self.bp_progress_bar.pack(fill=tk.X)

        # Blueprint Summary Viewer
        bp_view_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=6)
        bp_view_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            bp_view_frame,
            text="Architecture Specification Overview",
            font=("Segoe UI", 9, "bold"),
            fg="#111827",
            bg="#ffffff"
        ).pack(anchor="w", pady=(0, 4))

        self.bp_text = scrolledtext.ScrolledText(
            bp_view_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#ffffff",
            fg="#111827",
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.bp_text.pack(fill=tk.BOTH, expand=True)
        self.bp_text.insert(tk.END, "Configure technical specifications above and click 'GENERATE PRE-LAUNCH BLUEPRINT' to compile the complete architecture manual and turnkey starter kit.\n")

    # -----------------------------------------------------------------------
    # AUDIT LOGIC
    # -----------------------------------------------------------------------
    def start_audit(self):
        url = self.url_var.get().strip()
        if not url or url == "https://":
            messagebox.showerror("Error", "Please enter a valid target URL.")
            return

        try:
            pages_raw = self.pages_var.get().strip()
            max_pages = int(pages_raw) if pages_raw else 0
        except ValueError:
            messagebox.showerror("Error", "Crawl Scope must be a valid number.")
            return

        report_mode = self.mode_var.get().strip().lower()

        self.is_running = True
        self.cancel_event.clear()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_open_pdf.config(state=tk.DISABLED)
        self.progress_bar.start(10)

        scope_desc = f"{max_pages} pages" if max_pages > 0 else "All Pages (Unlimited)"
        self.status_var.set(f"Status: Auditing {url} ({scope_desc}) [{report_mode.upper()} mode]...")
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"============================================================\n")
        self.log_text.insert(tk.END, f"  INERSIALAB SOFTWARE DEPARTMENT — SEO AUDIT ENGINE\n")
        self.log_text.insert(tk.END, f"  Target: {url}\n")
        self.log_text.insert(tk.END, f"  Scope:  {scope_desc}\n")
        self.log_text.insert(tk.END, f"  Mode:   {report_mode.upper()}\n")
        self.log_text.insert(tk.END, f"============================================================\n\n")

        self.audit_thread = threading.Thread(
            target=self._run_audit_worker,
            args=(url, max_pages if max_pages > 0 else None, report_mode),
            daemon=True
        )
        self.audit_thread.start()

    def _run_audit_worker(self, url, max_pages, report_mode):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = StdoutRedirector(self.log_queue)

        try:
            sys.stdout = redirector
            sys.stderr = redirector

            import agy_seo
            result = agy_seo.run_audit(url, max_pages=max_pages, report_mode=report_mode)

            domain_safe = result.get("domain", "").replace(".", "_").replace(":", "_")
            candidates = [
                os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR)
                if f.startswith(f"SEO_Audit_{domain_safe}") and f.endswith(".pdf")
            ]
            if candidates:
                candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                self.last_pdf_path = candidates[0]
                self.log_queue.put(f"\n[OK] Report saved: {self.last_pdf_path}\n")

            self.status_var.set("Status: Audit Complete — Report Generated")
        except Exception as e:
            self.log_queue.put(f"\n[ERROR] Audit failed: {str(e)}\n")
            self.status_var.set(f"Status: Failed — {str(e)}")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.is_running = False
            self.root.after(0, self._on_audit_finished)

    def _on_audit_finished(self):
        self.progress_bar.stop()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        if self.last_pdf_path and os.path.exists(self.last_pdf_path):
            self.btn_open_pdf.config(state=tk.NORMAL)

    def stop_audit(self):
        if self.is_running:
            self.cancel_event.set()
            self.status_var.set("Status: Stopping audit...")
            self.log_queue.put("\n[USER] Audit cancellation requested...\n")
            self.btn_stop.config(state=tk.DISABLED)

    def open_last_pdf(self):
        if self.last_pdf_path and os.path.exists(self.last_pdf_path):
            os.startfile(self.last_pdf_path)

    def open_downloads_folder(self):
        os.startfile(DOWNLOADS_DIR)

    # -----------------------------------------------------------------------
    # BLUEPRINT LOGIC
    # -----------------------------------------------------------------------
    def start_blueprint_generation(self):
        brand = self.bp_brand_var.get().strip() or "InersiaLab"
        domain = self.bp_domain_var.get().strip() or "https://example.com"

        type_map = {
            "Corporate B2B Services": "corporate_services",
            "SaaS Web Application": "saas_webapp",
            "E-Commerce Store": "ecommerce",
            "Local Physical Business": "local_business",
            "Content Publisher / Blog": "content_blog",
            "Creative Portfolio": "portfolio_creative"
        }
        stack_map = {
            "Next.js (App Router)": "nextjs",
            "Astro (Island Architecture)": "astro",
            "React + Vite SPA": "react_vite",
            "WordPress": "wordpress",
            "Shopify": "shopify",
            "Nuxt.js (Vue 3)": "nuxt",
            "Modern Semantic HTML5": "vanilla_html"
        }
        hosting_map = {
            "Cloudflare Pages / Workers": "cloudflare",
            "Vercel Edge Network": "vercel",
            "Linux VPS (Ubuntu + Nginx)": "nginx_vps",
            "Netlify Edge": "netlify",
            "AWS CloudFront / GCP": "aws_gcp",
            "Apache / cPanel": "apache_cpanel"
        }
        lang_map = {
            "Single Language (EN)": "single_en",
            "Single Language (FR)": "single_fr",
            "Single Language (AR RTL)": "single_ar",
            "Bilingual (EN & FR)": "bilingual_en_fr",
            "Multilingual + RTL (EN, FR, AR)": "multilingual_en_fr_ar",
            "Global Multi-Regional": "global_multi"
        }
        geo_map = {
            "Maximum AI Citability (SearchGPT, Perplexity, Claude)": "high_geo",
            "Balanced Hybrid (Google Search + AI Overviews)": "balanced_seo_geo",
            "Traditional Google SERP Only": "standard_seo"
        }
        cwv_map = {
            "Ultra-Fast (<1.0s LCP, 100 Score)": "ultra_fast",
            "Enterprise Standard (<1.8s LCP, 90+ Score)": "enterprise",
            "Standard (<2.5s LCP)": "standard"
        }

        answers = {
            "brand_name": brand,
            "domain": domain,
            "site_type": type_map.get(self.bp_type_var.get(), "corporate_services"),
            "tech_stack": stack_map.get(self.bp_stack_var.get(), "nextjs"),
            "hosting": hosting_map.get(self.bp_hosting_var.get(), "cloudflare"),
            "language_setup": lang_map.get(self.bp_lang_var.get(), "bilingual_en_fr"),
            "geo_priority": geo_map.get(self.bp_geo_var.get(), "high_geo"),
            "cwv_target": cwv_map.get(self.bp_cwv_var.get(), "ultra_fast"),
            "llms_txt": "yes",
            "schema_strategy": "comprehensive_graph",
            "interactive_features": "lead_form",
            "media_strategy": "balanced_webp",
            "security_level": "strict_a_plus",
            "cookie_compliance": "strict_gdpr"
        }

        self.is_generating_bp = True
        self.btn_gen_bp.config(state=tk.DISABLED)
        self.btn_open_bp_pdf.config(state=tk.DISABLED)
        self.btn_open_starter.config(state=tk.DISABLED)
        self.bp_progress_bar.start(10)
        self.bp_status_var.set(f"Status: Synthesizing architecture manual for {brand}...")

        self.bp_text.delete(1.0, tk.END)
        self.bp_text.insert(tk.END, f"Compiling Pre-Launch Architecture Guide for {brand} ({domain})...\n")

        self.blueprint_thread = threading.Thread(
            target=self._run_blueprint_worker,
            args=(answers,),
            daemon=True
        )
        self.blueprint_thread.start()

    def _run_blueprint_worker(self, answers):
        try:
            synth = BlueprintSynthesizer(answers)
            data = synth.synthesize()

            brand = answers.get("brand_name", "InersiaLab")
            safe_brand = "".join(c for c in brand if c.isalnum() or c in ("-", "_")).strip() or "Architecture"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 1. PDF manual
            pdf_name = f"Architecture_Blueprint_{safe_brand}_{timestamp}.pdf"
            pdf_path = os.path.join(DOWNLOADS_DIR, pdf_name)
            generate_blueprint_pdf(data, pdf_path)
            self.last_bp_pdf_path = pdf_path

            # 2. Starter Kit
            starter_name = f"StarterKit_{safe_brand}_{timestamp}"
            starter_dir = os.path.join(DOWNLOADS_DIR, starter_name)
            generate_blueprint_starter_kit(data, starter_dir)
            self.last_starter_dir = starter_dir

            # Format summary text
            summary = []
            summary.append("=" * 64)
            summary.append(f"  PRE-LAUNCH ARCHITECTURE BLUEPRINT: {brand.upper()}")
            summary.append(f"  Domain: {data['domain']} | Stack: {answers['tech_stack'].upper()}")
            summary.append("=" * 64)
            summary.append(f"\n[OK] Executive PDF Manual: {pdf_path}")
            summary.append(f"[OK] Turnkey Starter Kit:  {starter_dir}\n")
            summary.append("-" * 64)
            summary.append("SYNTHESIZED ARCHITECTURAL SPECIFICATIONS:")
            summary.append("-" * 64)

            for sec in data["sections"]:
                summary.append(f"\n• {sec['title']}")
                if "code_block" in sec:
                    summary.append(f"   [Code: {sec['code_block']['filename']}]")

            summary.append("\n" + "=" * 64)
            summary.append("All starter files exported directly to your Downloads folder.")

            self.root.after(0, lambda: self._on_blueprint_success("\n".join(summary)))
        except Exception as e:
            self.root.after(0, lambda: self._on_blueprint_error(str(e)))

    def _on_blueprint_success(self, text):
        self.bp_progress_bar.stop()
        self.btn_gen_bp.config(state=tk.NORMAL)
        self.btn_open_bp_pdf.config(state=tk.NORMAL)
        self.btn_open_starter.config(state=tk.NORMAL)
        self.bp_status_var.set("Status: Architecture Blueprint & Starter Kit Generated Successfully")
        self.bp_text.delete(1.0, tk.END)
        self.bp_text.insert(tk.END, text)

    def _on_blueprint_error(self, err):
        self.bp_progress_bar.stop()
        self.btn_gen_bp.config(state=tk.NORMAL)
        self.bp_status_var.set(f"Status: Error — {err}")
        self.bp_text.insert(tk.END, f"\n[ERROR] Generation failed: {err}\n")

    def open_blueprint_pdf(self):
        if self.last_bp_pdf_path and os.path.exists(self.last_bp_pdf_path):
            os.startfile(self.last_bp_pdf_path)

    def open_starter_folder(self):
        if self.last_starter_dir and os.path.exists(self.last_starter_dir):
            os.startfile(self.last_starter_dir)

    # -----------------------------------------------------------------------
    # TAB 3: PAGE CONTENT ARCHITECT
    # -----------------------------------------------------------------------
    def _build_content_tab(self, parent):
        # Description banner
        desc_frame = tk.Frame(parent, bg="#f9fafb", padx=16, pady=8, relief="solid", bd=1)
        desc_frame.pack(fill=tk.X, padx=16, pady=(10, 6))

        tk.Label(
            desc_frame,
            text="Pre-Launch Page & Section Content Generator",
            font=("Segoe UI", 10, "bold"),
            fg="#111827",
            bg="#f9fafb"
        ).pack(anchor="w")

        tk.Label(
            desc_frame,
            text="Synthesizes complete, fully-structured SEO/GEO-optimized text content and sections for every single page before development begins (strict heading hierarchy, AEO hooks, E-E-A-T signals, and Schema.org JSON-LD).",
            font=("Segoe UI", 8),
            fg="#4b5563",
            bg="#f9fafb",
            wraplength=780,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # Form Inputs Frame
        form_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=4)
        form_frame.pack(fill=tk.X)

        # Row 1: Brand, Domain, Language
        r1 = tk.Frame(form_frame, bg="#ffffff")
        r1.pack(fill=tk.X, pady=2)

        tk.Label(r1, text="Brand Name:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=12, anchor="w").pack(side=tk.LEFT)
        self.cg_brand_var = tk.StringVar(value="InersiaMedical")
        tk.Entry(r1, textvariable=self.cg_brand_var, font=("Segoe UI", 9), relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        tk.Label(r1, text="Domain:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=8, anchor="w").pack(side=tk.LEFT)
        self.cg_domain_var = tk.StringVar(value="https://example.com")
        tk.Entry(r1, textvariable=self.cg_domain_var, font=("Segoe UI", 9), relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        tk.Label(r1, text="Language:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=9, anchor="w").pack(side=tk.LEFT)
        self.cg_lang_var = tk.StringVar(value="English (en)")
        self.cg_lang_combo = ttk.Combobox(
            r1, textvariable=self.cg_lang_var, state="readonly", font=("Segoe UI", 9),
            values=["English (en)", "French (fr)", "Arabic (ar RTL)"], width=14
        )
        self.cg_lang_combo.pack(side=tk.LEFT)

        # Row 2: Industry Archetype & Core Keywords
        r2 = tk.Frame(form_frame, bg="#ffffff")
        r2.pack(fill=tk.X, pady=4)

        tk.Label(r2, text="Archetype:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=12, anchor="w").pack(side=tk.LEFT)
        self.cg_industry_labels = [data["label"] for data in INDUSTRY_PRESETS.values()]
        self.cg_industry_keys = list(INDUSTRY_PRESETS.keys())
        default_label = INDUSTRY_PRESETS.get("healthcare_medical", {}).get("label", "Healthcare, Medical Clinic & Dental Services")
        self.cg_industry_var = tk.StringVar(value=default_label)
        self.cg_industry_combo = ttk.Combobox(
            r2, textvariable=self.cg_industry_var, state="readonly", font=("Segoe UI", 9),
            values=self.cg_industry_labels, width=38
        )
        self.cg_industry_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.cg_industry_combo.bind("<<ComboboxSelected>>", self._on_cg_industry_change)

        tk.Label(r2, text="Keywords:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff", width=9, anchor="w").pack(side=tk.LEFT)
        self.cg_keywords_var = tk.StringVar(value="medical treatment, healthcare clinic, patient care, certified doctors")
        tk.Entry(r2, textvariable=self.cg_keywords_var, font=("Segoe UI", 9), relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Page Checklist Frame
        check_container = tk.Frame(parent, bg="#ffffff", padx=16, pady=2)
        check_container.pack(fill=tk.X)

        check_hdr = tk.Frame(check_container, bg="#ffffff")
        check_hdr.pack(fill=tk.X, pady=(2, 4))
        tk.Label(check_hdr, text="Select Pages to Generate Content For:", font=("Segoe UI", 9, "bold"), fg="#111827", bg="#ffffff").pack(side=tk.LEFT)

        tk.Button(check_hdr, text="Select All", font=("Segoe UI", 8), relief="solid", bd=1, bg="#f9fafb", command=lambda: self._select_all_cg_pages(True)).pack(side=tk.RIGHT, padx=(4, 0))
        tk.Button(check_hdr, text="Clear Optional", font=("Segoe UI", 8), relief="solid", bd=1, bg="#f9fafb", command=lambda: self._select_all_cg_pages(False)).pack(side=tk.RIGHT)

        # Scrollable checklist canvas
        canvas_frame = tk.Frame(check_container, bg="#f9fafb", relief="solid", bd=1)
        canvas_frame.pack(fill=tk.X)

        self.cg_canvas = tk.Canvas(canvas_frame, bg="#f9fafb", highlightthickness=0, height=95)
        self.cg_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.cg_canvas.yview)
        self.cg_scroll_inner = tk.Frame(self.cg_canvas, bg="#f9fafb")
        self.cg_scroll_inner.bind("<Configure>", lambda e: self.cg_canvas.configure(scrollregion=self.cg_canvas.bbox("all")))
        self.cg_canvas.create_window((0, 0), window=self.cg_scroll_inner, anchor="nw")
        self.cg_canvas.configure(yscrollcommand=self.cg_scrollbar.set)

        self.cg_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add Custom Page row
        cp_row = tk.Frame(check_container, bg="#ffffff")
        cp_row.pack(fill=tk.X, pady=(4, 6))
        self.cg_custom_title_var = tk.StringVar()
        tk.Entry(cp_row, textvariable=self.cg_custom_title_var, font=("Segoe UI", 8), relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Button(cp_row, text="+ Add Custom Page", font=("Segoe UI", 8, "bold"), relief="solid", bd=1, bg="#f3f4f6", command=self._add_custom_cg_page).pack(side=tk.LEFT)

        # Populate checklist for default industry
        self._populate_cg_checklist()

        # Action Buttons Row
        btn_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=4)
        btn_frame.pack(fill=tk.X)

        self.btn_gen_content = tk.Button(
            btn_frame,
            text="GENERATE SITE CONTENT",
            font=("Segoe UI", 9, "bold"),
            bg="#111827",
            fg="#ffffff",
            activebackground="#374151",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.generate_content
        )
        self.btn_gen_content.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_open_content_folder = tk.Button(
            btn_frame,
            text="OPEN GENERATED FOLDER",
            font=("Segoe UI", 9),
            bg="#f3f4f6",
            fg="#111827",
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            command=self.open_content_folder
        )
        self.btn_open_content_folder.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_copy_master_content = tk.Button(
            btn_frame,
            text="COPY MASTER MARKDOWN",
            font=("Segoe UI", 9),
            bg="#f3f4f6",
            fg="#111827",
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            command=self.copy_master_markdown
        )
        self.btn_copy_master_content.pack(side=tk.LEFT)

        # Status & Progress Frame
        status_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=2)
        status_frame.pack(fill=tk.X)

        self.cg_status_var = tk.StringVar(value="Status: Ready")
        tk.Label(status_frame, textvariable=self.cg_status_var, font=("Segoe UI", 8), fg="#4b5563", bg="#ffffff").pack(side=tk.LEFT)

        self.cg_progress_bar = ttk.Progressbar(status_frame, mode="indeterminate", style="TProgressbar", length=140)
        self.cg_progress_bar.pack(side=tk.RIGHT)

        # Explorer Split Pane (Left: pages listbox, Right: page preview)
        split_frame = tk.Frame(parent, bg="#ffffff", padx=16, pady=4)
        split_frame.pack(fill=tk.BOTH, expand=True)

        paned = tk.PanedWindow(split_frame, orient=tk.HORIZONTAL, bg="#e5e7eb", bd=1, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left: Pages Listbox Frame
        left_pane = tk.Frame(paned, bg="#ffffff", width=220)
        paned.add(left_pane, minsize=180)

        tk.Label(left_pane, text="GENERATED PAGES", font=("Segoe UI", 8, "bold"), fg="#4b5563", bg="#ffffff", anchor="w").pack(fill=tk.X, pady=(2, 4))
        lb_frame = tk.Frame(left_pane, bg="#ffffff")
        lb_frame.pack(fill=tk.BOTH, expand=True)

        self.cg_pages_listbox = tk.Listbox(
            lb_frame, font=("Segoe UI", 9), relief="solid", bd=1,
            selectbackground="#111827", selectforeground="#ffffff", activestyle="none"
        )
        lb_scroll = ttk.Scrollbar(lb_frame, orient="vertical", command=self.cg_pages_listbox.yview)
        self.cg_pages_listbox.configure(yscrollcommand=lb_scroll.set)
        self.cg_pages_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.cg_pages_listbox.bind("<<ListboxSelect>>", self._on_cg_page_select)

        # Right: Content Preview Frame
        right_pane = tk.Frame(paned, bg="#ffffff")
        paned.add(right_pane, minsize=380)

        # Meta & Action header
        rh = tk.Frame(right_pane, bg="#ffffff")
        rh.pack(fill=tk.X, pady=(0, 4))

        self.cg_meta_summary_var = tk.StringVar(value="Select a generated page to view structured content...")
        tk.Label(rh, textvariable=self.cg_meta_summary_var, font=("Segoe UI", 8, "bold"), fg="#111827", bg="#ffffff", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(rh, text="Copy MD", font=("Segoe UI", 7), relief="solid", bd=1, bg="#f9fafb", command=self.copy_cg_page_md).pack(side=tk.RIGHT, padx=(2, 0))
        tk.Button(rh, text="Copy HTML", font=("Segoe UI", 7), relief="solid", bd=1, bg="#f9fafb", command=self.copy_cg_page_html).pack(side=tk.RIGHT, padx=(2, 0))
        tk.Button(rh, text="Copy Schema", font=("Segoe UI", 7), relief="solid", bd=1, bg="#f9fafb", command=self.copy_cg_page_schema).pack(side=tk.RIGHT)

        # Scrolled Text Box
        self.cg_content_text = scrolledtext.ScrolledText(
            right_pane, font=("Consolas", 9), relief="solid", bd=1,
            bg="#f9fafb", fg="#111827", wrap=tk.WORD
        )
        self.cg_content_text.pack(fill=tk.BOTH, expand=True)

    def _get_current_industry_key(self):
        label = self.cg_industry_var.get()
        for k, v in INDUSTRY_PRESETS.items():
            if v["label"] == label:
                return k
        return "healthcare_medical"

    def _on_cg_industry_change(self, event=None):
        ind_key = self._get_current_industry_key()
        ind_data = INDUSTRY_PRESETS.get(ind_key, {})
        self.cg_keywords_var.set(ind_data.get("keywords_hint", ""))
        self._populate_cg_checklist()

    def _populate_cg_checklist(self):
        for widget in self.cg_scroll_inner.winfo_children():
            widget.destroy()

        self.cg_page_vars.clear()
        ind_key = self._get_current_industry_key()
        ind_data = INDUSTRY_PRESETS.get(ind_key, {})

        col = 0
        row = 0
        for p in ind_data.get("default_pages", []):
            var = tk.BooleanVar(value=True)
            self.cg_page_vars[p["id"]] = var
            tag = " [Req]" if p.get("required") else ""
            cb = tk.Checkbutton(
                self.cg_scroll_inner,
                text=p["title"] + tag,
                variable=var,
                font=("Segoe UI", 8),
                bg="#f9fafb",
                anchor="w"
            )
            cb.grid(row=row, column=col, sticky="w", padx=6, pady=2)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        for cp in self.cg_custom_pages:
            var = tk.BooleanVar(value=True)
            self.cg_page_vars[cp["id"]] = var
            cb = tk.Checkbutton(
                self.cg_scroll_inner,
                text=cp["title"] + " [Custom]",
                variable=var,
                font=("Segoe UI", 8),
                fg="#0369a1",
                bg="#f9fafb",
                anchor="w"
            )
            cb.grid(row=row, column=col, sticky="w", padx=6, pady=2)
            col += 1
            if col >= 2:
                col = 0
                row += 1

    def _select_all_cg_pages(self, select_all=True):
        ind_key = self._get_current_industry_key()
        ind_data = INDUSTRY_PRESETS.get(ind_key, {})
        req_ids = {p["id"] for p in ind_data.get("default_pages", []) if p.get("required")}

        for pid, var in self.cg_page_vars.items():
            if select_all:
                var.set(True)
            else:
                var.set(pid in req_ids)

    def _add_custom_cg_page(self):
        title = self.cg_custom_title_var.get().strip()
        if not title:
            return
        cid = f"custom_{len(self.cg_custom_pages) + 1}"
        self.cg_custom_pages.append({"id": cid, "title": title})
        self.cg_custom_title_var.set("")
        self._populate_cg_checklist()

    def generate_content(self):
        if self.is_generating_content:
            return

        brand = self.cg_brand_var.get().strip()
        if not brand:
            messagebox.showwarning("Brand Required", "Please enter a brand name.")
            return

        selected_page_ids = [pid for pid, var in self.cg_page_vars.items() if var.get() and not pid.startswith("custom_")]
        custom_selected = [cp for cp in self.cg_custom_pages if self.cg_page_vars.get(cp["id"], tk.BooleanVar(value=False)).get()]

        if not selected_page_ids and not custom_selected:
            messagebox.showwarning("Pages Required", "Please select at least one page to generate.")
            return

        lang_val = self.cg_lang_var.get()
        lang_code = "en"
        if "fr" in lang_val.lower():
            lang_code = "fr"
        elif "ar" in lang_val.lower():
            lang_code = "ar"

        ind_key = self._get_current_industry_key()

        config = {
            "brand_name": brand,
            "domain": self.cg_domain_var.get().strip() or "https://example.com",
            "language": lang_code,
            "industry": ind_key,
            "description": self.cg_keywords_var.get().strip(),
            "pages": selected_page_ids,
            "custom_pages": custom_selected,
        }

        self.is_generating_content = True
        self.btn_gen_content.config(state=tk.DISABLED)
        self.cg_progress_bar.start(10)
        self.cg_status_var.set(f"Status: Synthesizing structured SEO/GEO content for {len(selected_page_ids) + len(custom_selected)} pages...")

        self.content_thread = threading.Thread(target=self._run_content_thread, args=(config,), daemon=True)
        self.content_thread.start()

    def _run_content_thread(self, config):
        try:
            synth = ContentSynthesizer(config)
            results = synth.generate_all()

            brand = config.get("brand_name", "Site")
            safe_brand = "".join(c for c in brand if c.isalnum() or c in ("-", "_")).strip() or "Site"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(DOWNLOADS_DIR, f"SiteContent_{safe_brand}_{ts}")

            export_content(results, output_dir)
            self.root.after(0, lambda: self._on_content_success(results, output_dir))
        except Exception as e:
            self.root.after(0, lambda: self._on_content_error(str(e)))

    def _on_content_success(self, results, output_dir):
        self.is_generating_content = False
        self.cg_progress_bar.stop()
        self.btn_gen_content.config(state=tk.NORMAL)
        self.btn_open_content_folder.config(state=tk.NORMAL)
        self.btn_copy_master_content.config(state=tk.NORMAL)

        self.last_content_results = results
        self.last_content_dir = output_dir

        total_words = sum(p["total_word_count"] for p in results["pages"])
        self.cg_status_var.set(f"Status: Complete! {len(results['pages'])} pages ({total_words} words) exported to Downloads.")

        # Populate listbox
        self.cg_pages_listbox.delete(0, tk.END)
        for p in results["pages"]:
            self.cg_pages_listbox.insert(tk.END, f"{p['title']}  ({p['total_word_count']}w)")

        if results["pages"]:
            self.cg_pages_listbox.selection_set(0)
            self._display_cg_page(0)

    def _on_content_error(self, err):
        self.is_generating_content = False
        self.cg_progress_bar.stop()
        self.btn_gen_content.config(state=tk.NORMAL)
        self.cg_status_var.set(f"Status: Error — {err}")
        messagebox.showerror("Content Generation Failed", str(err))

    def _on_cg_page_select(self, event=None):
        sel = self.cg_pages_listbox.curselection()
        if not sel:
            return
        self._display_cg_page(sel[0])

    def _display_cg_page(self, idx):
        if not self.last_content_results or idx >= len(self.last_content_results["pages"]):
            return
        p = self.last_content_results["pages"][idx]

        self.cg_meta_summary_var.set(
            f"Title: {p['meta_title_length']}c | Desc: {p['meta_description_length']}c | Words: {p['total_word_count']}w | Slug: /{p['slug']}"
        )

        md = _render_page_markdown(p)
        self.cg_content_text.delete(1.0, tk.END)
        self.cg_content_text.insert(tk.END, md)

    def copy_cg_page_md(self):
        sel = self.cg_pages_listbox.curselection()
        if not sel or not self.last_content_results:
            return
        p = self.last_content_results["pages"][sel[0]]
        md = _render_page_markdown(p)
        self.root.clipboard_clear()
        self.root.clipboard_append(md)
        messagebox.showinfo("Copied", f"Markdown for '{p['title']}' copied to clipboard.")

    def copy_cg_page_html(self):
        sel = self.cg_pages_listbox.curselection()
        if not sel or not self.last_content_results:
            return
        p = self.last_content_results["pages"][sel[0]]
        html = _render_page_html(p)
        self.root.clipboard_clear()
        self.root.clipboard_append(html)
        messagebox.showinfo("Copied", f"Semantic HTML for '{p['title']}' copied to clipboard.")

    def copy_cg_page_schema(self):
        sel = self.cg_pages_listbox.curselection()
        if not sel or not self.last_content_results:
            return
        p = self.last_content_results["pages"][sel[0]]
        schema_str = json.dumps(p["schema_jsonld"], indent=2, ensure_ascii=False)
        self.root.clipboard_clear()
        self.root.clipboard_append(schema_str)
        messagebox.showinfo("Copied", f"Schema JSON-LD for '{p['title']}' copied to clipboard.")

    def copy_master_markdown(self):
        if not self.last_content_results:
            return
        master = _render_master_document(self.last_content_results)
        self.root.clipboard_clear()
        self.root.clipboard_append(master)
        messagebox.showinfo("Copied", "Master document with all pages copied to clipboard.")

    def open_content_folder(self):
        if self.last_content_dir and os.path.exists(self.last_content_dir):
            os.startfile(self.last_content_dir)

    # -----------------------------------------------------------------------
    # LOG QUEUE POLLING
    # -----------------------------------------------------------------------
    def _poll_log_queue(self):
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)
                if "(ETA:" in msg:
                    for line in msg.split("\n"):
                        if "(ETA:" in line:
                            self.status_var.set(f"Status: {line.strip()}")
            except queue.Empty:
                break
        self.root.after(100, self._poll_log_queue)


def main():
    root = tk.Tk()
    app = SEOAuditApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
