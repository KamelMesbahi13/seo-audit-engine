"""InersiaLab Software Department — SEO Audit Engine & New Website Architect Web UI.

Minimalist, high-performance local web interface:
- Tab 1: Existing Website Audit (Full technical audit, real-time streaming, PDF generation)
- Tab 2: New Website Architect (Pre-launch architecture manual & turnkey starter kit generator)
- InersiaLab 3-color design system: Black (#111827), Green (#15803d), Red (#b91c1c).
- Strictly NO shadows, strictly NO emojis, clean professional typography.
"""

import os
import sys
import json
import time
import queue
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Import blueprint module
try:
    from blueprint import (
        QUESTIONNAIRE_SCHEMA,
        BlueprintSynthesizer,
        build_blueprint_html,
        generate_blueprint_pdf,
        generate_blueprint_starter_kit,
    )
except ImportError:
    QUESTIONNAIRE_SCHEMA = []
    BlueprintSynthesizer = None
    build_blueprint_html = None
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

# Global state for audit execution
audit_state = {
    "is_running": False,
    "status": "Ready",
    "logs": [],
    "last_result": None,
    "last_pdf": None,
}

# Global state for blueprint generator
blueprint_state = {
    "is_generating": False,
    "status": "Ready",
    "last_pdf": None,
    "last_starter_dir": None,
    "last_html": None,
    "last_brand": None,
}

# Global state for page content generator
content_state = {
    "is_generating": False,
    "status": "Ready",
    "last_dir": None,
    "last_results": None,
}

log_subscribers = []


def add_log(message: str):
    audit_state["logs"].append(message)
    if len(audit_state["logs"]) > 2000:
        audit_state["logs"].pop(0)
    if "(ETA:" in message:
        for line in message.split("\n"):
            if "(ETA:" in line:
                audit_state["status"] = line.strip()


class ThreadSafeLogWriter:
    def write(self, text):
        if text:
            add_log(text)

    def flush(self):
        pass


def run_audit_in_background(target_url: str, max_pages: int, report_mode: str = "detailed"):
    global audit_state
    audit_state["is_running"] = True
    effective_pages = max_pages if (max_pages and max_pages > 0) else None
    scope_desc = f"{effective_pages} pages" if effective_pages else "All Pages (Unlimited)"
    audit_state["status"] = f"Auditing {target_url} ({scope_desc}) [{report_mode.upper()} mode]..."
    audit_state["last_result"] = None
    audit_state["last_pdf"] = None

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    writer = ThreadSafeLogWriter()

    try:
        sys.stdout = writer
        sys.stderr = writer

        import agy_seo
        result = agy_seo.run_audit(target_url, max_pages=effective_pages, report_mode=report_mode)
        audit_state["last_result"] = {
            "domain": result.get("domain", ""),
            "overall_score": result.get("overall_score", 0),
            "pages_crawled": result.get("pages_crawled", 0),
            "site_scores": result.get("site_scores", {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Locate newest generated PDF in Downloads
        domain_safe = result.get("domain", "").replace(".", "_").replace(":", "_")
        candidates = [
            os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR)
            if f.startswith(f"SEO_Audit_{domain_safe}") and f.endswith(".pdf")
        ]
        if candidates:
            candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            audit_state["last_pdf"] = candidates[0]
            add_log(f"\n[OK] Report generated: {os.path.basename(audit_state['last_pdf'])}")

        audit_state["status"] = "Audit Complete"
    except Exception as e:
        audit_state["status"] = f"Error: {str(e)}"
        add_log(f"\n[ERROR] Audit execution failed: {str(e)}")
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        audit_state["is_running"] = False


def run_blueprint_in_background(answers: dict):
    global blueprint_state
    blueprint_state["is_generating"] = True
    brand = answers.get("brand_name", "InersiaLab").strip() or "InersiaLab"
    blueprint_state["status"] = f"Synthesizing architecture specification for {brand}..."
    blueprint_state["last_brand"] = brand

    try:
        synth = BlueprintSynthesizer(answers)
        data = synth.synthesize()

        blueprint_state["status"] = "Rendering executive architecture HTML..."
        html = build_blueprint_html(data)
        blueprint_state["last_html"] = html

        # Generate PDF into Downloads
        blueprint_state["status"] = "Compiling print-ready Playwright PDF manual..."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_brand = "".join(c for c in brand if c.isalnum() or c in ("-", "_")).strip() or "Architecture"
        pdf_name = f"Architecture_Blueprint_{safe_brand}_{timestamp}.pdf"
        pdf_path = os.path.join(DOWNLOADS_DIR, pdf_name)
        generate_blueprint_pdf(data, pdf_path)
        blueprint_state["last_pdf"] = pdf_path

        # Generate Turnkey Starter Kit
        blueprint_state["status"] = "Exporting turnkey repository starter kit..."
        starter_name = f"StarterKit_{safe_brand}_{timestamp}"
        starter_dir = os.path.join(DOWNLOADS_DIR, starter_name)
        generate_blueprint_starter_kit(data, starter_dir)
        blueprint_state["last_starter_dir"] = starter_dir

        blueprint_state["status"] = "Pre-Launch Architecture Blueprint Generated Successfully"
    except Exception as e:
        blueprint_state["status"] = f"Error: {str(e)}"
    finally:
        blueprint_state["is_generating"] = False


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InersiaLab — SEO Audit & Architecture Suite</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            box-shadow: none !important;
            text-shadow: none !important;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #ffffff;
            color: #111827;
            line-height: 1.5;
            font-size: 14px;
            padding: 30px 20px;
        }

        .container {
            max-width: 1040px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            border-bottom: 2px solid #111827;
            padding-bottom: 14px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }

        .org-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #4b5563;
            margin-bottom: 4px;
        }

        .main-title {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #111827;
        }

        .header-meta {
            font-size: 11px;
            color: #4b5563;
            text-align: right;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }

        /* Tabs Navigation */
        .tabs-nav {
            display: flex;
            border-bottom: 2px solid #111827;
            margin-bottom: 24px;
            gap: 4px;
        }

        .tab-btn {
            background: #f9fafb;
            color: #4b5563;
            border: 1px solid #e5e7eb;
            border-bottom: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.15s ease;
        }

        .tab-btn:hover {
            background: #f3f4f6;
            color: #111827;
        }

        .tab-btn.active {
            background: #111827;
            color: #ffffff;
            border-color: #111827;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Shared Form & Card Components */
        .card {
            border: 1px solid #e5e7eb;
            padding: 20px;
            margin-bottom: 20px;
            background: #ffffff;
        }

        .card-title {
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #111827;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 8px;
            margin-bottom: 16px;
        }

        .form-grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .form-grid-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
        }

        @media (max-width: 768px) {
            .form-grid-2, .form-grid-3 {
                grid-template-columns: 1fr;
            }
        }

        .field-group {
            margin-bottom: 14px;
        }

        .field-label {
            display: block;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #374151;
            margin-bottom: 4px;
        }

        .field-help {
            font-size: 11px;
            color: #6b7280;
            margin-top: 3px;
            line-height: 1.3;
        }

        input[type="text"], input[type="number"], select, textarea {
            width: 100%;
            padding: 8px 10px;
            font-size: 13px;
            border: 1px solid #d1d5db;
            color: #111827;
            background: #ffffff;
            font-family: inherit;
        }

        input[type="text"]:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #111827;
        }

        /* Buttons */
        .btn-row {
            display: flex;
            gap: 10px;
            margin-top: 16px;
            flex-wrap: wrap;
        }

        .btn {
            display: inline-block;
            padding: 9px 18px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid #111827;
            background: #111827;
            color: #ffffff;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
        }

        .btn:hover {
            background: #000000;
        }

        .btn-outline {
            background: #ffffff;
            color: #111827;
            border: 1px solid #111827;
        }

        .btn-outline:hover {
            background: #f3f4f6;
        }

        .btn-accent {
            background: #15803d;
            border-color: #15803d;
            color: #ffffff;
        }

        .btn-accent:hover {
            background: #166534;
        }

        .btn:disabled, .btn-outline:disabled, .btn-accent:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Status Indicator */
        .status-box {
            padding: 10px 14px;
            border: 1px solid #e5e7eb;
            background: #f9fafb;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            background: #111827;
            color: #ffffff;
        }

        .status-badge.running {
            background: #b91c1c;
        }

        .status-badge.success {
            background: #15803d;
        }

        /* Terminal Console */
        .terminal {
            background: #111827;
            color: #f3f4f6;
            padding: 14px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            height: 280px;
            overflow-y: auto;
            border: 1px solid #111827;
            white-space: pre-wrap;
            line-height: 1.45;
        }

        /* Tables */
        table.data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }

        table.data-table th {
            text-align: left;
            padding: 8px 10px;
            background: #f9fafb;
            border-bottom: 2px solid #111827;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        table.data-table td {
            padding: 8px 10px;
            border-bottom: 1px solid #e5e7eb;
        }

        /* Blueprint Interactive Viewer */
        .blueprint-viewer {
            border: 1px solid #111827;
            margin-top: 24px;
            padding: 24px;
            background: #ffffff;
        }

        .blueprint-viewer h2 {
            font-size: 16px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #111827;
            padding-bottom: 6px;
            margin: 24px 0 12px 0;
        }

        .blueprint-viewer h2:first-child {
            margin-top: 0;
        }

        .code-container {
            position: relative;
            margin: 12px 0;
        }

        .code-box {
            background: #111827;
            color: #f9fafb;
            padding: 14px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            overflow-x: auto;
            white-space: pre;
            line-height: 1.4;
        }

        .copy-btn {
            position: absolute;
            top: 6px;
            right: 6px;
            padding: 3px 8px;
            font-size: 10px;
            font-weight: 700;
            background: #374151;
            color: #ffffff;
            border: 1px solid #4b5563;
            cursor: pointer;
            text-transform: uppercase;
        }

        .copy-btn:hover {
            background: #1f2937;
        }

        .anti-pattern-item {
            border-left: 3px solid #b91c1c;
            padding: 8px 12px;
            background: #fef2f2;
            margin-bottom: 8px;
            font-size: 12px;
        }

        .checklist-item {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 6px 0;
            border-bottom: 1px solid #f3f4f6;
            font-size: 12px;
        }

        .checklist-item input[type="checkbox"] {
            margin-top: 2px;
        }

        .downloads-banner {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 16px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .downloads-banner-text {
            font-size: 13px;
            color: #166534;
        }
        .downloads-banner-text strong {
            display: block;
            font-size: 14px;
            color: #14532d;
            margin-bottom: 2px;
        }

        /* Tab 3: Content Architect Styles */
        .badge-metric {
            display: inline-block;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 700;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            border-radius: 2px;
        }
        .badge-good { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
        .badge-warn { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
        .badge-bad  { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

        .content-layout {
            display: grid;
            grid-template-columns: 290px 1fr;
            gap: 16px;
            margin-top: 16px;
            align-items: start;
        }
        .content-pages-sidebar {
            border: 1px solid #e5e7eb;
            background: #ffffff;
            max-height: 720px;
            overflow-y: auto;
        }
        .sidebar-page-item {
            padding: 10px 12px;
            border-bottom: 1px solid #f3f4f6;
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .sidebar-page-item:hover {
            background: #f9fafb;
        }
        .sidebar-page-item.active {
            background: #111827;
            color: #ffffff;
            border-color: #111827;
        }
        .sidebar-page-item.active .badge-metric {
            background: #374151;
            color: #ffffff;
            border-color: #4b5563;
        }
        .sidebar-page-item.active .page-sub {
            color: #9ca3af !important;
        }
        .aeo-callout {
            border-left: 3px solid #15803d;
            background: #f0fdf4;
            padding: 12px 14px;
            margin-bottom: 14px;
            font-size: 13px;
            color: #166534;
            line-height: 1.6;
        }
        .section-block {
            border: 1px solid #e5e7eb;
            padding: 16px;
            margin-bottom: 16px;
            background: #ffffff;
        }
        .section-block h3 {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #111827;
        }
        .section-block h4 {
            font-size: 13px;
            font-weight: 700;
            margin-top: 12px;
            margin-bottom: 6px;
            color: #374151;
        }
        .tag-pill {
            font-size: 10px;
            font-weight: 700;
            padding: 1px 6px;
            background: #f3f4f6;
            color: #4b5563;
            border: 1px solid #e5e7eb;
            border-radius: 2px;
            text-transform: uppercase;
        }
        .tag-pill.req {
            background: #fef2f2;
            color: #b91c1c;
            border-color: #fecaca;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div>
                <div class="org-label">InersiaLab Software Department</div>
                <h1 class="main-title">SEO Audit & Pre-Launch Architect</h1>
            </div>
            <div class="header-meta">
                ENGINE V3.8<br>
                HIGH-PRECISION SUITE
            </div>
        </header>

        <!-- Navigation Tabs -->
        <nav class="tabs-nav">
            <button id="nav-btn-audit" class="tab-btn active" onclick="switchTab('audit')">1. Existing Website Audit</button>
            <button id="nav-btn-blueprint" class="tab-btn" onclick="switchTab('blueprint')">2. New Website Architect (Pre-Launch)</button>
            <button id="nav-btn-content" class="tab-btn" onclick="switchTab('content')">3. Page Content Architect</button>
        </nav>

        <!-- ============================================================= -->
        <!-- TAB 1: EXISTING WEBSITE AUDIT -->
        <!-- ============================================================= -->
        <section id="tab-audit" class="tab-content active">
            <!-- Audit Configuration Form -->
            <div class="card">
                <div class="card-title">Live Website Audit Parameters</div>
                
                <div class="field-group">
                    <label class="field-label" for="audit-url">Target Website URL</label>
                    <input type="text" id="audit-url" placeholder="https://example.com" value="https://example.com">
                    <div class="field-help">Full website address including https://. Crawler automatically handles canonical redirection.</div>
                </div>

                <div class="form-grid-2">
                    <div class="field-group">
                        <label class="field-label" for="audit-scope">Crawl Scope (Max Pages)</label>
                        <select id="audit-scope" onchange="toggleCustomScope()">
                            <option value="0" selected>Full Website (All Pages — Unlimited Depth)</option>
                            <option value="15">Sample Audit (15 Pages)</option>
                            <option value="50">Medium Audit (50 Pages)</option>
                            <option value="150">Large Audit (150 Pages)</option>
                            <option value="custom">Custom Page Count...</option>
                        </select>
                        <input type="number" id="audit-custom-scope" placeholder="Enter number of pages" style="display:none; margin-top:6px;" min="1">
                        <div class="field-help">Full audit recommended for comprehensive site diagnosis and exact broken links.</div>
                    </div>

                    <div class="field-group">
                        <label class="field-label" for="audit-mode">Executive Report Mode</label>
                        <select id="audit-mode">
                            <option value="detailed" selected>Detailed Report (Full page-by-page diagnosis & fixes)</option>
                            <option value="short">Short Report (Executive summary of issues & global fixes)</option>
                            <option value="both">Both Reports (Detailed manual + Executive brief)</option>
                        </select>
                        <div class="field-help">Saved directly into your local Downloads directory as print-ready PDF.</div>
                    </div>
                </div>

                <div class="btn-row">
                    <button id="btn-start-audit" class="btn" onclick="startAudit()">START LIVE AUDIT</button>
                    <button id="btn-open-audit-pdf" class="btn btn-outline" onclick="openLatestAuditPdf()" disabled>OPEN GENERATED PDF</button>
                    <button class="btn btn-outline" onclick="openDownloadsFolder()">OPEN DOWNLOADS FOLDER</button>
                </div>
            </div>

            <!-- Execution Status & Real-Time Terminal -->
            <div class="status-box">
                <div>
                    <span id="audit-status-badge" class="status-badge">READY</span>
                    <span id="audit-status-text" style="margin-left: 10px;">Audit engine idle</span>
                </div>
                <div id="audit-timer" style="font-size: 11px; color: #6b7280;"></div>
            </div>

            <div class="card" style="padding: 0;">
                <div style="padding: 10px 14px; border-bottom: 1px solid #111827; background: #111827; color: #ffffff; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; display: flex; justify-content: space-between;">
                    <span>Execution Stream</span>
                    <span id="log-count" style="color: #9ca3af;">0 lines</span>
                </div>
                <div id="audit-terminal" class="terminal">Awaiting execution command...</div>
            </div>

            <!-- Recent Reports Table -->
            <div class="card">
                <div class="card-title">Recent Audit Reports in Downloads</div>
                <div id="reports-table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Report PDF</th>
                                <th>Generated Time</th>
                                <th>File Size</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="reports-tbody">
                            <tr><td colspan="4" style="text-align: center; color: #6b7280; padding: 20px;">Scanning Downloads folder...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 2: NEW WEBSITE ARCHITECT (PRE-LAUNCH BLUEPRINT) -->
        <!-- ============================================================= -->
        <section id="tab-blueprint" class="tab-content">
            <div class="card" style="border-left: 3px solid #111827;">
                <div class="card-title">Pre-Launch Architecture Guide & Turnkey Starter Kit Generator</div>
                <p style="font-size: 13px; color: #4b5563; margin-bottom: 16px;">
                    When building a new website from scratch, configure your technical specifications below. 
                    The architect synthesizes an exhaustive technical prevention manual and exports a turnkey repository starter kit 
                    (production <code>robots.txt</code>, <code>llms.txt</code>, semantic <code>&lt;head&gt;</code> template, server headers, and Schema.org graphs) 
                    guaranteeing 100/100 Technical SEO, Core Web Vitals, and Generative AI (GEO) citability before coding begins.
                </p>

                <!-- Form Generated Dynamically from Schema -->
                <form id="blueprint-form" onsubmit="event.preventDefault(); generateBlueprint();">
                    <div id="blueprint-fields-container">
                        <!-- Loaded dynamically via /api/blueprint/schema -->
                        <div style="padding: 20px; text-align: center; color: #6b7280;">Loading architecture questionnaire...</div>
                    </div>

                    <div class="btn-row" style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                        <button type="submit" id="btn-generate-blueprint" class="btn btn-accent">GENERATE PRE-LAUNCH BLUEPRINT & STARTER KIT</button>
                        <button type="button" id="btn-open-blueprint-pdf" class="btn btn-outline" onclick="openBlueprintPdf()" disabled>OPEN BLUEPRINT PDF</button>
                        <button type="button" id="btn-open-starter-dir" class="btn btn-outline" onclick="openStarterDir()" disabled>OPEN STARTER KIT FOLDER</button>
                    </div>
                </form>
            </div>

            <!-- Blueprint Generation Status -->
            <div id="blueprint-status-box" class="status-box" style="display: none;">
                <div>
                    <span id="bp-status-badge" class="status-badge">READY</span>
                    <span id="bp-status-text" style="margin-left: 10px;">Idle</span>
                </div>
            </div>

            <!-- Downloads Success Banner -->
            <div id="bp-downloads-banner" class="downloads-banner" style="display: none;">
                <div class="downloads-banner-text">
                    <strong>Pre-Launch Architecture Artifacts Successfully Generated</strong>
                    <span id="bp-downloads-info">Files exported to your Downloads folder.</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-outline" onclick="openBlueprintPdf()">View PDF Manual</button>
                    <button class="btn btn-accent" onclick="openStarterDir()">Open Starter Kit</button>
                </div>
            </div>

            <!-- Interactive On-Screen Guide Viewer -->
            <div id="blueprint-viewer-container" style="display: none;">
                <div class="card-title" style="margin-top: 28px; margin-bottom: 12px; font-size: 14px;">Interactive Architecture Guide</div>
                <div id="blueprint-content-area" class="blueprint-viewer">
                    <!-- Synthesized HTML injected here -->
                </div>
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 3: PAGE CONTENT ARCHITECT (PRE-LAUNCH CONTENT GENERATOR) -->
        <!-- ============================================================= -->
        <section id="tab-content" class="tab-content">
            <div class="card" style="border-left: 3px solid #15803d;">
                <div class="card-title">Pre-Launch Page & Section Content Generator</div>
                <p style="font-size: 13px; color: #4b5563; margin-bottom: 16px;">
                    Select an industry archetype and choose the pages for your upcoming website. The engine generates complete, fully-structured, SEO/GEO-optimized text content and sections for every single page (strict heading hierarchy, AEO hooks, E-E-A-T signals, Schema.org JSON-LD, and Core Web Vitals asset specs) with zero CSS bloat.
                </p>

                <!-- Generation Parameters Form -->
                <form id="content-form" onsubmit="event.preventDefault(); generateSiteContent();">
                    <div class="form-grid-3">
                        <div class="field-group">
                            <label class="field-label" for="cg-brand">Brand / Business Name</label>
                            <input type="text" id="cg-brand" placeholder="e.g. Apex Health Clinic" value="InersiaMedical" required>
                        </div>
                        <div class="field-group">
                            <label class="field-label" for="cg-domain">Target Domain</label>
                            <input type="text" id="cg-domain" placeholder="https://example.com" value="https://example.com">
                        </div>
                        <div class="field-group">
                            <label class="field-label" for="cg-lang">Content Language</label>
                            <select id="cg-lang">
                                <option value="en" selected>English (Default)</option>
                                <option value="fr">French (Français)</option>
                                <option value="ar">Arabic (العربية - RTL)</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-grid-2" style="margin-top: 10px;">
                        <div class="field-group">
                            <label class="field-label" for="cg-industry">Website Archetype / Industry</label>
                            <select id="cg-industry" onchange="onIndustryChange()">
                                <!-- Dynamically loaded from presets -->
                            </select>
                            <div class="field-help" id="cg-industry-help">Pre-configured pages tailored to this archetype.</div>
                        </div>
                        <div class="field-group">
                            <label class="field-label" for="cg-keywords">Core Value Proposition / Focus Keywords</label>
                            <input type="text" id="cg-keywords" placeholder="e.g. expert dental implants, cosmetic dentistry, gentle care">
                            <div class="field-help">Injected into section copy, answer engine hooks, and metadata.</div>
                        </div>
                    </div>

                    <!-- Sitemap Page Selection Checklist -->
                    <div style="margin-top: 18px; border-top: 1px solid #e5e7eb; padding-top: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <label class="field-label" style="margin-bottom: 0;">Select Pages to Generate Content For</label>
                            <div style="display: flex; gap: 8px;">
                                <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllContentPages(true)">Select All</button>
                                <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllContentPages(false)">Clear Optional</button>
                            </div>
                        </div>

                        <div id="content-pages-checklist" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 8px; max-height: 220px; overflow-y: auto; padding: 10px; border: 1px solid #e5e7eb; background: #f9fafb;">
                            <!-- Checkboxes injected dynamically -->
                        </div>

                        <!-- Add Custom Page Row -->
                        <div style="display: flex; gap: 8px; margin-top: 10px; align-items: center;">
                            <input type="text" id="cg-custom-title" placeholder="Add custom page title (e.g. Pediatric Care, London Office, VIP Concierge)" style="flex: 1; padding: 7px 10px; font-size: 12px;">
                            <button type="button" class="btn btn-outline" style="padding: 7px 14px; font-size: 12px;" onclick="addCustomContentPage()">+ Add Custom Page</button>
                        </div>
                    </div>

                    <div class="btn-row" style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                        <button type="submit" id="btn-generate-content" class="btn btn-accent">GENERATE SITE CONTENT</button>
                        <button type="button" id="btn-open-content-folder" class="btn btn-outline" onclick="openContentFolder()" disabled>OPEN GENERATED FOLDER</button>
                        <button type="button" id="btn-copy-master-md" class="btn btn-outline" onclick="copyMasterMarkdown()" disabled>COPY MASTER MARKDOWN</button>
                    </div>
                </form>
            </div>

            <!-- Content Generation Status Box -->
            <div id="cg-status-box" class="status-box" style="display: none;">
                <div>
                    <span id="cg-status-badge" class="status-badge">READY</span>
                    <span id="cg-status-text" style="margin-left: 10px;">Idle</span>
                </div>
            </div>

            <!-- Content Export Success Banner -->
            <div id="cg-downloads-banner" class="downloads-banner" style="display: none;">
                <div class="downloads-banner-text">
                    <strong id="cg-banner-title">Content Architecture Successfully Exported</strong>
                    <span id="cg-banner-info">Exported to Downloads with Markdown, HTML, JSON, and llms.txt.</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-accent" onclick="openContentFolder()">Open Export Folder</button>
                </div>
            </div>

            <!-- Multi-Page Content Viewer -->
            <div id="cg-viewer-wrapper" style="display: none; margin-top: 20px;">
                <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>Generated Pages Content Explorer</span>
                    <span id="cg-summary-metrics" style="font-size: 11px; color: #6b7280; font-family: monospace;"></span>
                </div>

                <div class="content-layout">
                    <!-- Left Sidebar: Pages List -->
                    <div class="content-pages-sidebar" id="cg-pages-list">
                        <!-- Rendered dynamically -->
                    </div>

                    <!-- Right Main Content Area -->
                    <div class="card" style="margin-bottom: 0;">
                        <!-- Active Page Meta Header -->
                        <div id="cg-page-header" style="border-bottom: 1px solid #e5e7eb; padding-bottom: 14px; margin-bottom: 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <h2 id="cg-view-title" style="font-size: 18px; font-weight: 800; color: #111827;">Page Title</h2>
                                    <div id="cg-view-slug" style="font-size: 12px; color: #6b7280; font-family: monospace; margin-top: 2px;"></div>
                                </div>
                                <div style="display: flex; gap: 6px;">
                                    <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="copyActivePageMarkdown()">Copy MD</button>
                                    <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="copyActivePageHtml()">Copy HTML</button>
                                    <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="copyActivePageSchema()">Copy Schema</button>
                                </div>
                            </div>

                            <!-- Meta tags inspection grid -->
                            <div style="margin-top: 12px; background: #f9fafb; border: 1px solid #e5e7eb; padding: 10px 12px; font-size: 12px;">
                                <div style="margin-bottom: 6px; display: flex; align-items: baseline; gap: 8px;">
                                    <strong style="color: #374151; width: 110px;">Meta Title:</strong>
                                    <span id="cg-view-meta-title" style="flex: 1; color: #111827; font-weight: 600;"></span>
                                    <span id="cg-view-title-pill" class="badge-metric badge-good">54 chars</span>
                                </div>
                                <div style="display: flex; align-items: baseline; gap: 8px;">
                                    <strong style="color: #374151; width: 110px;">Meta Description:</strong>
                                    <span id="cg-view-meta-desc" style="flex: 1; color: #4b5563;"></span>
                                    <span id="cg-view-desc-pill" class="badge-metric badge-good">152 chars</span>
                                </div>
                            </div>

                            <!-- View Mode Tabs -->
                            <div style="display: flex; gap: 4px; margin-top: 14px; border-bottom: 1px solid #e5e7eb;">
                                <button type="button" class="tab-btn active" id="btn-mode-formatted" style="padding: 6px 14px; font-size: 11px;" onclick="switchPageViewMode('formatted')">Structured Sections</button>
                                <button type="button" class="tab-btn" id="btn-mode-markdown" style="padding: 6px 14px; font-size: 11px;" onclick="switchPageViewMode('markdown')">Markdown Source</button>
                                <button type="button" class="tab-btn" id="btn-mode-html" style="padding: 6px 14px; font-size: 11px;" onclick="switchPageViewMode('html')">Semantic HTML</button>
                                <button type="button" class="tab-btn" id="btn-mode-schema" style="padding: 6px 14px; font-size: 11px;" onclick="switchPageViewMode('schema')">Schema JSON-LD</button>
                            </div>
                        </div>

                        <!-- Active Page Body Container -->
                        <div id="cg-page-body">
                            <!-- Dynamic Content Rendered Here -->
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- JavaScript Controller -->
    <script>
        let currentTab = "audit";
        let isAuditing = false;
        let isGeneratingBlueprint = false;
        let lastAuditPdf = null;
        let lastBlueprintPdf = null;
        let lastStarterDir = null;

        // Tab Switching
        function switchTab(tabId) {
            currentTab = tabId;
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            document.getElementById("nav-btn-" + tabId).classList.add("active");
            document.getElementById("tab-" + tabId).classList.add("active");

            if (tabId === "blueprint" && !window.blueprintSchemaLoaded) {
                loadBlueprintSchema();
            }
            if (tabId === "content" && !window.contentPresetsLoaded) {
                loadContentPresets();
            }
        }

        // Scope toggle
        function toggleCustomScope() {
            const sel = document.getElementById("audit-scope").value;
            const customInput = document.getElementById("audit-custom-scope");
            if (sel === "custom") {
                customInput.style.display = "block";
                customInput.focus();
            } else {
                customInput.style.display = "none";
            }
        }

        // Audit Controller
        async function startAudit() {
            const urlInput = document.getElementById("audit-url").value.trim();
            if (!urlInput) {
                alert("Please enter a valid website URL.");
                return;
            }

            const scopeSel = document.getElementById("audit-scope").value;
            let maxPages = 0;
            if (scopeSel === "custom") {
                maxPages = parseInt(document.getElementById("audit-custom-scope").value, 10) || 0;
            } else {
                maxPages = parseInt(scopeSel, 10) || 0;
            }

            const mode = document.getElementById("audit-mode").value;

            document.getElementById("btn-start-audit").disabled = true;
            document.getElementById("audit-status-badge").className = "status-badge running";
            document.getElementById("audit-status-badge").innerText = "RUNNING";
            document.getElementById("audit-status-text").innerText = "Initializing crawler for " + urlInput + "...";

            try {
                const res = await fetch("/api/start", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({url: urlInput, max_pages: maxPages, mode: mode})
                });
                const data = await res.json();
                if (data.error) {
                    alert("Error: " + data.error);
                    document.getElementById("btn-start-audit").disabled = false;
                }
            } catch (e) {
                alert("Failed to reach audit server: " + e);
                document.getElementById("btn-start-audit").disabled = false;
            }
        }

        // Poll audit status & logs
        async function pollAuditStatus() {
            try {
                const res = await fetch("/api/status");
                const data = await res.json();

                isAuditing = data.is_running;
                document.getElementById("btn-start-audit").disabled = isAuditing;

                if (isAuditing) {
                    document.getElementById("audit-status-badge").className = "status-badge running";
                    document.getElementById("audit-status-badge").innerText = "RUNNING";
                    document.getElementById("audit-status-text").innerText = data.status || "Auditing...";
                } else if (data.status === "Audit Complete") {
                    document.getElementById("audit-status-badge").className = "status-badge success";
                    document.getElementById("audit-status-badge").innerText = "COMPLETED";
                    document.getElementById("audit-status-text").innerText = "Audit finished successfully";
                } else {
                    document.getElementById("audit-status-badge").className = "status-badge";
                    document.getElementById("audit-status-badge").innerText = "READY";
                    document.getElementById("audit-status-text").innerText = data.status || "Ready";
                }

                // Update logs
                const term = document.getElementById("audit-terminal");
                if (data.logs && data.logs.length > 0) {
                    term.innerText = data.logs.join("");
                    term.scrollTop = term.scrollHeight;
                    document.getElementById("log-count").innerText = data.logs.length + " lines";
                }

                // Last PDF
                if (data.last_pdf) {
                    lastAuditPdf = data.last_pdf;
                    document.getElementById("btn-open-audit-pdf").disabled = false;
                }
            } catch (e) {
                // server temporarily quiet
            }
        }

        async function openLatestAuditPdf() {
            await fetch("/api/open-latest", {method: "POST"});
        }

        async function openDownloadsFolder() {
            await fetch("/api/open-folder", {method: "POST"});
        }

        async function loadReportsList() {
            try {
                const res = await fetch("/api/reports");
                const list = await res.json();
                const tbody = document.getElementById("reports-tbody");
                if (!list || list.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #6b7280; padding: 16px;">No generated audit reports found in Downloads yet.</td></tr>';
                    return;
                }

                let html = "";
                for (const r of list) {
                    html += `<tr>
                        <td><strong>${escapeHtml(r.filename)}</strong></td>
                        <td style="color:#6b7280;">${escapeHtml(r.time)}</td>
                        <td style="color:#6b7280;">${escapeHtml(r.size)}</td>
                        <td>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="openReportFile('${escapeHtml(r.filename)}')">Open</button>
                        </td>
                    </tr>`;
                }
                tbody.innerHTML = html;
            } catch (e) {}
        }

        async function openReportFile(fn) {
            await fetch("/api/open-file", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({filename: fn})
            });
        }

        // =============================================================
        // BLUEPRINT CONTROLLER
        // =============================================================
        async function loadBlueprintSchema() {
            try {
                const res = await fetch("/api/blueprint/schema");
                const schema = await res.json();
                window.blueprintSchemaLoaded = true;

                const container = document.getElementById("blueprint-fields-container");
                let html = "";

                for (const cat of schema) {
                    html += `<div class="card" style="margin-bottom: 16px;">
                        <div class="card-title">${escapeHtml(cat.category)}</div>
                        <div class="form-grid-2">`;

                    for (const f of cat.fields) {
                        html += `<div class="field-group">
                            <label class="field-label" for="bp-${f.id}">${escapeHtml(f.label)}</label>`;

                        if (f.type === "text") {
                            html += `<input type="text" id="bp-${f.id}" name="${f.id}" value="${escapeHtml(f.default || '')}" placeholder="${escapeHtml(f.placeholder || '')}">`;
                        } else if (f.type === "select") {
                            html += `<select id="bp-${f.id}" name="${f.id}">`;
                            for (const opt of f.options) {
                                const sel = opt.value === f.default ? "selected" : "";
                                html += `<option value="${escapeHtml(opt.value)}" ${sel}>${escapeHtml(opt.label)}</option>`;
                            }
                            html += `</select>`;
                        }

                        if (f.help) {
                            html += `<div class="field-help">${escapeHtml(f.help)}</div>`;
                        }
                        html += `</div>`;
                    }

                    html += `</div></div>`;
                }

                container.innerHTML = html;
            } catch (e) {
                document.getElementById("blueprint-fields-container").innerHTML = `<div style="color:#b91c1c; padding: 20px;">Failed to load questionnaire schema: ${e}</div>`;
            }
        }

        async function generateBlueprint() {
            const form = document.getElementById("blueprint-form");
            const formData = new FormData(form);
            const answers = {};
            for (const [k, v] of formData.entries()) {
                answers[k] = v;
            }

            // UI feedback
            const statusBox = document.getElementById("blueprint-status-box");
            const badge = document.getElementById("bp-status-badge");
            const text = document.getElementById("bp-status-text");
            const genBtn = document.getElementById("btn-generate-blueprint");

            statusBox.style.display = "flex";
            badge.className = "status-badge running";
            badge.innerText = "SYNTHESIZING";
            text.innerText = "Compiling pre-launch architecture specification and starter kit...";
            genBtn.disabled = true;

            try {
                const res = await fetch("/api/blueprint/generate", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(answers)
                });
                const result = await res.json();

                if (result.success) {
                    badge.className = "status-badge success";
                    badge.innerText = "SUCCESS";
                    text.innerText = "Architecture manual & starter kit created.";

                    lastBlueprintPdf = result.pdf_path;
                    lastStarterDir = result.starter_dir;

                    document.getElementById("btn-open-blueprint-pdf").disabled = false;
                    document.getElementById("btn-open-starter-dir").disabled = false;

                    // Show downloads banner
                    document.getElementById("bp-downloads-banner").style.display = "flex";
                    document.getElementById("bp-downloads-info").innerText = 
                        "Manual PDF: " + (result.pdf_filename || "Architecture_Blueprint.pdf") + " | Starter Kit: " + (result.starter_dirname || "StarterKit/");

                    // Display interactive viewer
                    if (result.html) {
                        document.getElementById("blueprint-viewer-container").style.display = "block";
                        document.getElementById("blueprint-content-area").innerHTML = result.html;
                        attachCopyHandlers();
                    }
                } else {
                    badge.className = "status-badge running";
                    badge.innerText = "ERROR";
                    text.innerText = result.error || "Generation failed";
                    alert("Error: " + (result.error || "Generation failed"));
                }
            } catch (e) {
                badge.className = "status-badge running";
                badge.innerText = "ERROR";
                text.innerText = e.toString();
                alert("Failed to generate blueprint: " + e);
            } finally {
                genBtn.disabled = false;
            }
        }

        async function openBlueprintPdf() {
            if (!lastBlueprintPdf) return;
            await fetch("/api/blueprint/open-pdf", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({pdf_path: lastBlueprintPdf})
            });
        }

        async function openStarterDir() {
            if (!lastStarterDir) return;
            await fetch("/api/blueprint/open-starter", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({starter_dir: lastStarterDir})
            });
        }

        function attachCopyHandlers() {
            document.querySelectorAll(".blueprint-viewer pre").forEach(pre => {
                if (pre.parentElement.classList.contains("code-container")) return;

                const container = document.createElement("div");
                container.className = "code-container";
                pre.parentNode.insertBefore(container, pre);
                container.appendChild(pre);
                pre.className = "code-box";

                const btn = document.createElement("button");
                btn.className = "copy-btn";
                btn.type = "button";
                btn.innerText = "COPY";
                btn.onclick = () => {
                    navigator.clipboard.writeText(pre.innerText).then(() => {
                        btn.innerText = "COPIED!";
                        setTimeout(() => btn.innerText = "COPY", 2000);
                    });
                };
                container.appendChild(btn);
            });
        }

        function escapeHtml(str) {
            if (!str) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        // -------------------------------------------------------------
        // Tab 3: Content Architect Controller
        // -------------------------------------------------------------
        let contentPresets = {};
        let lastContentResults = null;
        let lastContentDir = null;
        let activeContentPageIndex = 0;
        let currentContentMode = 'formatted';
        let customContentPagesList = [];

        async function loadContentPresets() {
            try {
                const res = await fetch("/api/content/presets");
                contentPresets = await res.json();
                window.contentPresetsLoaded = true;

                const indSelect = document.getElementById("cg-industry");
                indSelect.innerHTML = "";
                for (const [key, data] of Object.entries(contentPresets)) {
                    const opt = document.createElement("option");
                    opt.value = key;
                    opt.textContent = data.label;
                    indSelect.appendChild(opt);
                }
                onIndustryChange();
            } catch (e) {
                console.error("Failed to load content presets:", e);
            }
        }

        function onIndustryChange() {
            const key = document.getElementById("cg-industry").value;
            const data = contentPresets[key];
            if (!data) return;

            document.getElementById("cg-industry-help").textContent = "Tone: " + data.tone + " | Audience: " + data.audience;
            if (!document.getElementById("cg-keywords").value) {
                document.getElementById("cg-keywords").value = data.keywords_hint || "";
            }

            const checklist = document.getElementById("content-pages-checklist");
            checklist.innerHTML = "";

            data.default_pages.forEach(p => {
                const item = document.createElement("div");
                item.className = "checklist-item";
                item.style.alignItems = "center";
                const chk = document.createElement("input");
                chk.type = "checkbox";
                chk.id = "cg-chk-" + p.id;
                chk.value = p.id;
                chk.checked = true;
                chk.dataset.title = p.title;

                const lbl = document.createElement("label");
                lbl.htmlFor = chk.id;
                lbl.style.cursor = "pointer";
                lbl.style.display = "flex";
                lbl.style.alignItems = "center";
                lbl.style.gap = "6px";
                lbl.style.flex = "1";

                lbl.innerHTML = "<span>" + escapeHtml(p.title) + "</span>" + (p.required ? '<span class="tag-pill req">Required</span>' : '<span class="tag-pill">Standard</span>');

                item.appendChild(chk);
                item.appendChild(lbl);
                checklist.appendChild(item);
            });

            customContentPagesList.forEach((cp, idx) => {
                renderCustomPageItem(cp, idx);
            });
        }

        function selectAllContentPages(selectAll) {
            const key = document.getElementById("cg-industry").value;
            const data = contentPresets[key];
            const requiredIds = new Set(data ? data.default_pages.filter(p => p.required).map(p => p.id) : []);

            document.querySelectorAll("#content-pages-checklist input[type='checkbox']").forEach(chk => {
                if (selectAll) {
                    chk.checked = true;
                } else {
                    chk.checked = requiredIds.has(chk.value);
                }
            });
        }

        function addCustomContentPage() {
            const input = document.getElementById("cg-custom-title");
            const title = input.value.trim();
            if (!title) return;

            const customObj = { id: "custom_" + Date.now(), title: title };
            customContentPagesList.push(customObj);
            renderCustomPageItem(customObj, customContentPagesList.length - 1);
            input.value = "";
        }

        function renderCustomPageItem(cp, idx) {
            const checklist = document.getElementById("content-pages-checklist");
            const item = document.createElement("div");
            item.className = "checklist-item";
            item.style.alignItems = "center";
            item.id = "cg-item-" + cp.id;

            const chk = document.createElement("input");
            chk.type = "checkbox";
            chk.id = "cg-chk-" + cp.id;
            chk.value = cp.id;
            chk.checked = true;
            chk.dataset.isCustom = "true";
            chk.dataset.title = cp.title;

            const lbl = document.createElement("label");
            lbl.htmlFor = chk.id;
            lbl.style.cursor = "pointer";
            lbl.style.display = "flex";
            lbl.style.alignItems = "center";
            lbl.style.gap = "6px";
            lbl.style.flex = "1";
            lbl.innerHTML = "<span>" + escapeHtml(cp.title) + '</span> <span class="tag-pill" style="background:#e0f2fe; color:#0369a1; border-color:#bae6fd;">Custom</span>';

            const delBtn = document.createElement("button");
            delBtn.type = "button";
            delBtn.style.background = "none";
            delBtn.style.border = "none";
            delBtn.style.color = "#b91c1c";
            delBtn.style.cursor = "pointer";
            delBtn.style.fontSize = "12px";
            delBtn.style.fontWeight = "bold";
            delBtn.innerText = "×";
            delBtn.onclick = () => {
                customContentPagesList = customContentPagesList.filter(x => x.id !== cp.id);
                item.remove();
            };

            item.appendChild(chk);
            item.appendChild(lbl);
            item.appendChild(delBtn);
            checklist.appendChild(item);
        }

        async function generateSiteContent() {
            const brand = document.getElementById("cg-brand").value.trim();
            if (!brand) {
                alert("Please enter a Brand Name.");
                return;
            }
            const domain = document.getElementById("cg-domain").value.trim() || "https://example.com";
            const lang = document.getElementById("cg-lang").value;
            const industry = document.getElementById("cg-industry").value;
            const keywords = document.getElementById("cg-keywords").value.trim();

            const checkedBoxes = Array.from(document.querySelectorAll("#content-pages-checklist input[type='checkbox']:checked"));
            if (checkedBoxes.length === 0) {
                alert("Please select at least one page to generate.");
                return;
            }

            const standardPages = [];
            const customPages = [];
            checkedBoxes.forEach(chk => {
                if (chk.dataset.isCustom === "true") {
                    customPages.push({ id: chk.value, title: chk.dataset.title });
                } else {
                    standardPages.push(chk.value);
                }
            });

            const btn = document.getElementById("btn-generate-content");
            btn.disabled = true;
            const sBox = document.getElementById("cg-status-box");
            sBox.style.display = "flex";
            const sBadge = document.getElementById("cg-status-badge");
            sBadge.className = "status-badge running";
            sBadge.innerText = "GENERATING";
            const sText = document.getElementById("cg-status-text");
            sText.innerText = `Synthesizing structured SEO/GEO content for ${checkedBoxes.length} pages...`;

            try {
                const res = await fetch("/api/content/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        brand_name: brand,
                        domain: domain,
                        language: lang,
                        industry: industry,
                        description: keywords,
                        pages: standardPages,
                        custom_pages: customPages,
                    })
                });
                const data = await res.json();
                if (!data.success) {
                    throw new Error(data.error || "Generation failed.");
                }

                lastContentResults = data.results;
                lastContentDir = data.output_dir;

                sBadge.className = "status-badge success";
                sBadge.innerText = "COMPLETED";
                sText.innerText = `Successfully synthesized ${data.results.pages.length} pages (${data.export.total_words} words). Saved to Downloads!`;

                document.getElementById("btn-open-content-folder").disabled = false;
                document.getElementById("btn-copy-master-md").disabled = false;

                const banner = document.getElementById("cg-downloads-banner");
                banner.style.display = "flex";
                document.getElementById("cg-banner-info").textContent = `Exported to: ${data.output_dir}`;

                renderContentViewer(data.results);
            } catch (e) {
                sBadge.className = "status-badge";
                sBadge.innerText = "ERROR";
                sText.innerText = "Content synthesis error: " + e.message;
                alert("Error generating content: " + e.message);
            } finally {
                btn.disabled = false;
            }
        }

        function renderContentViewer(results) {
            const wrapper = document.getElementById("cg-viewer-wrapper");
            wrapper.style.display = "block";

            const totalWords = results.pages.reduce((acc, p) => acc + p.total_word_count, 0);
            document.getElementById("cg-summary-metrics").textContent = `${results.pages.length} Pages | ${totalWords} Words`;

            const sidebar = document.getElementById("cg-pages-list");
            sidebar.innerHTML = "";

            results.pages.forEach((page, idx) => {
                const item = document.createElement("div");
                item.className = "sidebar-page-item" + (idx === 0 ? " active" : "");
                item.id = "cg-side-item-" + idx;
                item.onclick = () => selectContentPage(idx);

                item.innerHTML = `
                    <div>
                        <div style="font-size: 13px; font-weight: 700;">${escapeHtml(page.title)}</div>
                        <div class="page-sub" style="font-size: 11px; color: #6b7280; font-family: monospace;">/${escapeHtml(page.slug)}</div>
                    </div>
                    <span class="badge-metric badge-good">${page.total_word_count}w</span>
                `;
                sidebar.appendChild(item);
            });

            selectContentPage(0);
        }

        function selectContentPage(idx) {
            if (!lastContentResults || !lastContentResults.pages[idx]) return;
            activeContentPageIndex = idx;

            document.querySelectorAll(".sidebar-page-item").forEach((el, i) => {
                if (i === idx) el.classList.add("active");
                else el.classList.remove("active");
            });

            const page = lastContentResults.pages[idx];
            document.getElementById("cg-view-title").textContent = page.title;
            document.getElementById("cg-view-slug").textContent = `URL: ${page.url} (Slug: ${page.slug})`;

            document.getElementById("cg-view-meta-title").textContent = page.meta_title;
            const tLen = page.meta_title_length;
            const tPill = document.getElementById("cg-view-title-pill");
            tPill.textContent = `${tLen} chars`;
            tPill.className = "badge-metric " + (tLen >= 50 && tLen <= 60 ? "badge-good" : (tLen >= 40 && tLen <= 65 ? "badge-warn" : "badge-bad"));

            document.getElementById("cg-view-meta-desc").textContent = page.meta_description;
            const dLen = page.meta_description_length;
            const dPill = document.getElementById("cg-view-desc-pill");
            dPill.textContent = `${dLen} chars`;
            dPill.className = "badge-metric " + (dLen >= 140 && dLen <= 160 ? "badge-good" : (dLen >= 120 && dLen <= 170 ? "badge-warn" : "badge-bad"));

            renderCurrentPageBody();
        }

        function switchPageViewMode(mode) {
            currentContentMode = mode;
            ["formatted", "markdown", "html", "schema"].forEach(m => {
                const btn = document.getElementById("btn-mode-" + m);
                if (btn) {
                    if (m === mode) btn.classList.add("active");
                    else btn.classList.remove("active");
                }
            });
            renderCurrentPageBody();
        }

        function renderCurrentPageBody() {
            if (!lastContentResults) return;
            const page = lastContentResults.pages[activeContentPageIndex];
            if (!page) return;
            const container = document.getElementById("cg-page-body");
            container.innerHTML = "";

            if (currentContentMode === "formatted") {
                const article = document.createElement("div");
                article.style.lineHeight = "1.6";

                page.sections.forEach(sec => {
                    const block = document.createElement("div");
                    block.className = "section-block";

                    const hTag = "h" + sec.heading_level;
                    const hEl = document.createElement(hTag);
                    hEl.textContent = sec.heading;
                    hEl.style.color = "#111827";
                    hEl.style.marginBottom = "8px";
                    block.appendChild(hEl);

                    if (sec.guidance) {
                        const guide = document.createElement("div");
                        guide.style.fontSize = "11px";
                        guide.style.color = "#6b7280";
                        guide.style.marginBottom = "10px";
                        guide.style.fontStyle = "italic";
                        guide.textContent = "Objective: " + sec.guidance;
                        block.appendChild(guide);
                    }

                    const lines = sec.content.split("\n");
                    let inAeo = true;
                    let aeoText = "";
                    let remainingLines = [];

                    for (let i = 0; i < lines.length; i++) {
                        const l = lines[i];
                        if (inAeo && l.trim()) {
                            aeoText = l.trim();
                            inAeo = false;
                        } else if (!inAeo) {
                            remainingLines.push(l);
                        }
                    }

                    if (aeoText) {
                        const aeoDiv = document.createElement("div");
                        aeoDiv.className = "aeo-callout";
                        aeoDiv.innerHTML = "<strong>AEO Answer Hook (AI Citability):</strong><br>" + escapeHtml(aeoText);
                        block.appendChild(aeoDiv);
                    }

                    if (remainingLines.length > 0) {
                        const restDiv = document.createElement("div");
                        restDiv.style.fontSize = "13px";
                        restDiv.style.color = "#374151";

                        let currentUl = null;
                        remainingLines.forEach(rl => {
                            const trimmed = rl.trim();
                            if (!trimmed) return;

                            if (trimmed.startsWith("### ")) {
                                currentUl = null;
                                const h3 = document.createElement("h4");
                                h3.textContent = trimmed.substring(4);
                                restDiv.appendChild(h3);
                            } else if (trimmed.startsWith("- ")) {
                                if (!currentUl) {
                                    currentUl = document.createElement("ul");
                                    currentUl.style.paddingLeft = "20px";
                                    currentUl.style.margin = "8px 0";
                                    restDiv.appendChild(currentUl);
                                }
                                const li = document.createElement("li");
                                li.innerHTML = escapeHtml(trimmed.substring(2));
                                currentUl.appendChild(li);
                            } else if (trimmed.startsWith("> ")) {
                                currentUl = null;
                                const bq = document.createElement("blockquote");
                                bq.style.borderLeft = "2px solid #9ca3af";
                                bq.style.paddingLeft = "10px";
                                bq.style.margin = "8px 0";
                                bq.style.color = "#4b5563";
                                bq.style.fontStyle = "italic";
                                bq.textContent = trimmed.substring(2);
                                restDiv.appendChild(bq);
                            } else {
                                currentUl = null;
                                const p = document.createElement("p");
                                p.style.marginBottom = "8px";
                                p.textContent = trimmed;
                                restDiv.appendChild(p);
                            }
                        });
                        block.appendChild(restDiv);
                    }

                    article.appendChild(block);
                });
                container.appendChild(article);

            } else if (currentContentMode === "markdown") {
                const pre = document.createElement("pre");
                pre.className = "code-box";
                pre.style.maxHeight = "550px";
                pre.style.overflow = "auto";
                pre.style.padding = "14px";
                pre.style.fontSize = "12px";

                let md = "---\ntitle: \"" + page.meta_title + "\"\ndescription: \"" + page.meta_description + "\"\nurl: \"" + page.url + "\"\ncanonical: \"" + page.canonical_url + "\"\nword_count: " + page.total_word_count + "\n---\n\n# " + page.h1 + "\n\n";
                page.sections.forEach(s => {
                    md += "#".repeat(s.heading_level) + " " + s.heading + "\n\n" + s.content + "\n\n";
                });
                pre.textContent = md;
                container.appendChild(pre);

            } else if (currentContentMode === "html") {
                const pre = document.createElement("pre");
                pre.className = "code-box";
                pre.style.maxHeight = "550px";
                pre.style.overflow = "auto";
                pre.style.padding = "14px";
                pre.style.fontSize = "12px";

                let html = '<!DOCTYPE html>\n<html lang="' + page.language + '" dir="' + page.direction + '">\n<head>\n  <meta charset="UTF-8">\n  <title>' + escapeHtml(page.meta_title) + '</title>\n  <meta name="description" content="' + escapeHtml(page.meta_description) + '">\n  <link rel="canonical" href="' + page.canonical_url + '">\n</head>\n<body>\n  <main>\n    <article>\n      <h1>' + escapeHtml(page.h1) + '</h1>\n';
                page.sections.forEach(s => {
                    html += "      <section>\n        <h" + s.heading_level + ">" + escapeHtml(s.heading) + "</h" + s.heading_level + ">\n        <p>" + escapeHtml(s.content) + "</p>\n      </section>\n";
                });
                html += "    </article>\n  </main>\n</body>\n</html>";
                pre.textContent = html;
                container.appendChild(pre);

            } else if (currentContentMode === "schema") {
                const pre = document.createElement("pre");
                pre.className = "code-box";
                pre.style.maxHeight = "550px";
                pre.style.overflow = "auto";
                pre.style.padding = "14px";
                pre.style.fontSize = "12px";
                pre.textContent = JSON.stringify(page.schema_jsonld, null, 2);
                container.appendChild(pre);
            }
        }

        function copyActivePageMarkdown() {
            if (!lastContentResults) return;
            const page = lastContentResults.pages[activeContentPageIndex];
            if (!page) return;
            let md = "---\ntitle: \"" + page.meta_title + "\"\ndescription: \"" + page.meta_description + "\"\nurl: \"" + page.url + "\"\ncanonical: \"" + page.canonical_url + "\"\nword_count: " + page.total_word_count + "\n---\n\n# " + page.h1 + "\n\n";
            page.sections.forEach(s => {
                md += "#".repeat(s.heading_level) + " " + s.heading + "\n\n" + s.content + "\n\n";
            });
            navigator.clipboard.writeText(md).then(() => alert("Page Markdown copied to clipboard!"));
        }

        function copyActivePageHtml() {
            if (!lastContentResults) return;
            const page = lastContentResults.pages[activeContentPageIndex];
            if (!page) return;
            let html = '<!DOCTYPE html>\n<html lang="' + page.language + '" dir="' + page.direction + '">\n<head>\n  <meta charset="UTF-8">\n  <title>' + page.meta_title + '</title>\n  <meta name="description" content="' + page.meta_description + '">\n  <link rel="canonical" href="' + page.canonical_url + '">\n</head>\n<body>\n  <main>\n    <article>\n      <h1>' + page.h1 + '</h1>\n';
            page.sections.forEach(s => {
                html += "      <section>\n        <h" + s.heading_level + ">" + s.heading + "</h" + s.heading_level + ">\n        <p>" + s.content + "</p>\n      </section>\n";
            });
            html += "    </article>\n  </main>\n</body>\n</html>";
            navigator.clipboard.writeText(html).then(() => alert("Page Semantic HTML copied to clipboard!"));
        }

        function copyActivePageSchema() {
            if (!lastContentResults) return;
            const page = lastContentResults.pages[activeContentPageIndex];
            if (!page) return;
            navigator.clipboard.writeText(JSON.stringify(page.schema_jsonld, null, 2)).then(() => alert("Schema JSON-LD copied to clipboard!"));
        }

        function copyMasterMarkdown() {
            if (!lastContentResults) return;
            let master = "# " + lastContentResults.brand + " - Complete Website Content Architecture\n\n";
            master += "Industry: " + lastContentResults.industry + "\nDomain: " + lastContentResults.domain + "\n\n---\n\n";
            lastContentResults.pages.forEach(p => {
                master += "## " + p.title + "\n\nURL: " + p.url + "\nMeta Title: " + p.meta_title + "\nMeta Description: " + p.meta_description + "\n\n";
                p.sections.forEach(s => {
                    master += "#".repeat(s.heading_level) + " " + s.heading + "\n\n" + s.content + "\n\n";
                });
                master += "\n---\n\n";
            });
            navigator.clipboard.writeText(master).then(() => alert("Master website content markdown copied to clipboard!"));
        }

        async function openContentFolder() {
            if (!lastContentDir) return;
            await fetch("/api/content/open-folder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ dir: lastContentDir })
            });
        }

        // Intervals
        setInterval(pollAuditStatus, 1500);
        setInterval(loadReportsList, 5000);

        // Init
        window.addEventListener("DOMContentLoaded", () => {
            pollAuditStatus();
            loadReportsList();
            loadContentPresets();
        });
    </script>
</body>
</html>
"""


class SEOHttpHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence standard HTTP access logging to console
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "is_running": audit_state["is_running"],
                "status": audit_state["status"],
                "logs": audit_state["logs"],
                "last_result": audit_state["last_result"],
                "last_pdf": audit_state["last_pdf"],
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        elif path == "/api/reports":
            reports = []
            if os.path.exists(DOWNLOADS_DIR):
                for fn in os.listdir(DOWNLOADS_DIR):
                    if (fn.startswith("SEO_Audit_") or fn.startswith("Architecture_Blueprint_")) and fn.endswith(".pdf"):
                        full_p = os.path.join(DOWNLOADS_DIR, fn)
                        stat = os.stat(full_p)
                        reports.append({
                            "filename": fn,
                            "time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                            "size": f"{stat.st_size / 1024:.1f} KB",
                            "mtime": stat.st_mtime
                        })
            reports.sort(key=lambda x: x["mtime"], reverse=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(reports[:25]).encode("utf-8"))

        elif path == "/api/blueprint/schema":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(QUESTIONNAIRE_SCHEMA).encode("utf-8"))

        elif path == "/api/blueprint/latest":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "is_generating": blueprint_state["is_generating"],
                "status": blueprint_state["status"],
                "last_pdf": blueprint_state["last_pdf"],
                "last_starter_dir": blueprint_state["last_starter_dir"],
                "last_brand": blueprint_state["last_brand"],
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        elif path == "/api/content/presets":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(INDUSTRY_PRESETS, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/content/latest":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            resp = {
                "is_generating": content_state["is_generating"],
                "status": content_state["status"],
                "last_dir": content_state["last_dir"],
                "results": content_state["last_results"],
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        if path == "/api/start":
            if audit_state["is_running"]:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "An audit is already running."}).encode("utf-8"))
                return

            try:
                data = json.loads(body) if body else {}
                url = data.get("url", "").strip()
                max_pages = int(data.get("max_pages", 0))
                mode = data.get("mode", "detailed").strip().lower()
                if not url:
                    raise ValueError("URL required")

                t = threading.Thread(target=run_audit_in_background, args=(url, max_pages, mode), daemon=True)
                t.start()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/open-latest":
            pdf_p = audit_state.get("last_pdf")
            if pdf_p and os.path.exists(pdf_p):
                try:
                    os.startfile(pdf_p)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "No PDF report file found."}).encode("utf-8"))

        elif path == "/api/open-file":
            try:
                data = json.loads(body) if body else {}
                filename = data.get("filename", "")
                full_p = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.exists(full_p) and full_p.endswith(".pdf"):
                    os.startfile(full_p)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "File not found."}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif path == "/api/open-folder":
            try:
                os.startfile(DOWNLOADS_DIR)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif path == "/api/blueprint/generate":
            try:
                data = json.loads(body) if body else {}
                brand = data.get("brand_name", "InersiaLab").strip() or "InersiaLab"

                # Synthesize synchronously
                synth = BlueprintSynthesizer(data)
                blueprint_data = synth.synthesize()

                html = build_blueprint_html(blueprint_data)

                # PDF Path
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_brand = "".join(c for c in brand if c.isalnum() or c in ("-", "_")).strip() or "Architecture"
                pdf_name = f"Architecture_Blueprint_{safe_brand}_{timestamp}.pdf"
                pdf_path = os.path.join(DOWNLOADS_DIR, pdf_name)
                generate_blueprint_pdf(blueprint_data, pdf_path)

                # Starter Kit Path
                starter_name = f"StarterKit_{safe_brand}_{timestamp}"
                starter_dir = os.path.join(DOWNLOADS_DIR, starter_name)
                generate_blueprint_starter_kit(blueprint_data, starter_dir)

                blueprint_state["last_pdf"] = pdf_path
                blueprint_state["last_starter_dir"] = starter_dir
                blueprint_state["last_html"] = html
                blueprint_state["last_brand"] = brand

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "pdf_path": pdf_path,
                    "pdf_filename": pdf_name,
                    "starter_dir": starter_dir,
                    "starter_dirname": starter_name,
                    "html": html,
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif path == "/api/blueprint/open-pdf":
            try:
                data = json.loads(body) if body else {}
                pdf_path = data.get("pdf_path") or blueprint_state.get("last_pdf")
                if pdf_path and os.path.exists(pdf_path):
                    os.startfile(pdf_path)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Blueprint PDF not found."}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif path == "/api/blueprint/open-starter":
            try:
                data = json.loads(body) if body else {}
                starter_dir = data.get("starter_dir") or blueprint_state.get("last_starter_dir")
                if starter_dir and os.path.exists(starter_dir):
                    os.startfile(starter_dir)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Starter kit directory not found."}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif path == "/api/content/generate":
            try:
                data = json.loads(body) if body else {}
                content_state["is_generating"] = True
                brand = data.get("brand_name", "Site").strip() or "Site"
                content_state["status"] = f"Synthesizing page content for {brand}..."

                synth = ContentSynthesizer(data)
                results = synth.generate_all()

                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_brand = "".join(c for c in brand if c.isalnum() or c in ("-", "_")).strip() or "Site"
                output_dir = os.path.join(DOWNLOADS_DIR, f"SiteContent_{safe_brand}_{ts}")

                export_res = export_content(results, output_dir)

                content_state["last_dir"] = output_dir
                content_state["last_results"] = results
                content_state["status"] = f"Complete: {len(results['pages'])} pages generated"

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "results": results,
                    "export": export_res,
                    "output_dir": output_dir,
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                content_state["status"] = f"Error: {str(e)}"
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            finally:
                content_state["is_generating"] = False

        elif path == "/api/content/open-folder":
            try:
                data = json.loads(body) if body else {}
                target_dir = data.get("dir") or content_state.get("last_dir") or DOWNLOADS_DIR
                if target_dir and os.path.exists(target_dir):
                    os.startfile(target_dir)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Folder not found."}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


def start_server(port=8765):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, SEOHttpHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"============================================================")
    print(f"  InersiaLab Software Department — SEO & Architecture Suite")
    print(f"  Web Interface running at: {url}")
    print(f"============================================================")

    # Open in default browser after 1 second
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    start_server()
