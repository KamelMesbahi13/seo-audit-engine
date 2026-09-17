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

        // Intervals
        setInterval(pollAuditStatus, 1500);
        setInterval(loadReportsList, 5000);

        // Init
        window.addEventListener("DOMContentLoaded", () => {
            pollAuditStatus();
            loadReportsList();
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
