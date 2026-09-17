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
        self.is_running = False
        self.is_generating_bp = False
        self.cancel_event = threading.Event()
        self.last_pdf_path = None
        self.last_bp_pdf_path = None
        self.last_starter_dir = None

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
