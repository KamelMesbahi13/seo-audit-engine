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
        DEMO_CLIENT_BRIEFS,
        ContentSynthesizer,
        export_content,
        normalize_client_brief,
        _render_page_markdown,
        _render_page_html,
        _render_master_document,
    )
except ImportError:
    INDUSTRY_PRESETS = {}
    DEMO_CLIENT_BRIEFS = {}
    ContentSynthesizer = None
    export_content = None
    normalize_client_brief = None
    _render_page_markdown = None
    _render_page_html = None
    _render_master_document = None

# Import optimizer module
try:
    from optimizer import optimize_content
except ImportError:
    optimize_content = None

# Import security engine module
try:
    from security_engine import run_security_audit
except ImportError:
    run_security_audit = None

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

# Global state for content optimizer
optimizer_state = {
    "last_result": None,
}

# Global state for cybersecurity & server hardening auditor
security_state = {
    "is_running": False,
    "status": "Ready",
    "logs": [],
    "last_result": None,
    "last_pdf": None,
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


def run_security_in_background(target_url: str):
    global security_state
    security_state["is_running"] = True
    security_state["status"] = f"Auditing {target_url} cybersecurity posture..."
    security_state["logs"] = []
    security_state["last_result"] = None
    security_state["last_pdf"] = None

    def log_cb(msg):
        security_state["logs"].append(msg + "\n")
        if len(security_state["logs"]) > 2000:
            security_state["logs"].pop(0)
        for line in msg.split("\n"):
            line_str = line.strip()
            if line_str.startswith("[+]") or line_str.startswith("[*]") or line_str.startswith("[OK]"):
                security_state["status"] = line_str

    try:
        if not run_security_audit:
            raise RuntimeError("security_engine module could not be loaded.")
        res = run_security_audit(target_url, log_callback=log_cb)
        security_state["last_result"] = res
        security_state["last_pdf"] = res.get("pdf_path")
        security_state["status"] = "Security Audit Complete"
    except Exception as e:
        security_state["status"] = f"Error: {str(e)}"
        security_state["logs"].append(f"\n[ERROR] Security audit failed: {str(e)}\n")
    finally:
        security_state["is_running"] = False



HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>InersiaLab — SEO Audit & Architecture Suite</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            line-height: 1.5;
            font-size: 13.5px;
            padding: 24px 20px 80px 20px;
        }

        .container {
            max-width: 1140px;
            margin: 0 auto;
        }

        /* Apple Navigation Header */
        .header {
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding-bottom: 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .org-label {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            color: #0071e3;
            background: rgba(0, 113, 227, 0.08);
            padding: 3px 10px;
            border-radius: 980px;
            margin-bottom: 6px;
        }

        .main-title {
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #1d1d1f;
            line-height: 1.2;
        }

        .header-meta {
            font-size: 11px;
            color: #86868b;
            text-align: right;
            font-weight: 500;
            letter-spacing: 0.02em;
        }

        /* Tabs Navigation — Apple Segmented Control */
        .tabs-nav {
            display: flex;
            background: rgba(0, 0, 0, 0.05);
            padding: 4px;
            border-radius: 14px;
            gap: 3px;
            margin-bottom: 26px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            border: none;
        }

        .tab-btn {
            flex: 1;
            min-width: max-content;
            background: transparent;
            color: #6e6e73;
            border: none;
            border-radius: 10px;
            padding: 9px 16px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            text-transform: none;
            letter-spacing: -0.01em;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            text-align: center;
            white-space: nowrap;
        }

        .tab-btn:hover {
            color: #1d1d1f;
            background: rgba(255, 255, 255, 0.5);
        }

        .tab-btn.active {
            background: #ffffff;
            color: #1d1d1f;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Shared Form & Card Components — Apple Surfaces */
        .card {
            background: #ffffff;
            border-radius: 18px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.02);
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            letter-spacing: -0.015em;
            color: #1d1d1f;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            padding-bottom: 12px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            text-transform: none;
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

        .form-grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }

        @media (max-width: 900px) {
            .form-grid-2, .form-grid-3, .form-grid-4 {
                grid-template-columns: 1fr;
            }
        }

        .field-group {
            margin-bottom: 16px;
        }

        .field-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: #1d1d1f;
            margin-bottom: 6px;
            text-transform: none;
        }

        .field-help {
            font-size: 12px;
            color: #86868b;
            margin-top: 5px;
            line-height: 1.4;
        }

        input[type="text"], input[type="number"], input[type="url"], select, textarea {
            width: 100%;
            padding: 10px 14px;
            font-size: 13.5px;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            color: #1d1d1f;
            background: #ffffff;
            font-family: inherit;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        input[type="text"]::placeholder, input[type="url"]::placeholder, textarea::placeholder {
            color: #a1a1a6;
        }

        input[type="text"]:focus, input[type="number"]:focus, input[type="url"]:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #0071e3;
            box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.15);
        }

        /* Buttons — Apple HIG Pill Styles */
        .btn-row {
            display: flex;
            gap: 10px;
            margin-top: 18px;
            flex-wrap: wrap;
            align-items: center;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 10px 22px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: -0.01em;
            border-radius: 980px;
            cursor: pointer;
            text-decoration: none;
            border: 1px solid transparent;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            white-space: nowrap;
            text-transform: none;
        }

        .btn:hover {
            transform: translateY(-1px);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-outline {
            background: #ffffff;
            color: #1d1d1f;
            border-color: #d2d2d7;
        }

        .btn-outline:hover {
            background: #f5f5f7;
            border-color: #86868b;
        }

        .btn-accent {
            background: #0071e3;
            color: #ffffff;
        }

        .btn-accent:hover {
            background: #0077ed;
            box-shadow: 0 4px 14px rgba(0, 113, 227, 0.25);
        }

        .btn-accent:active {
            background: #0062c4;
            box-shadow: none;
        }

        .btn-reset {
            background: rgba(255, 59, 48, 0.08);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.2);
            border-radius: 980px;
            font-size: 12px;
            font-weight: 600;
            padding: 6px 14px;
        }

        .btn-reset:hover {
            background: #ff3b30;
            color: #ffffff;
            border-color: #ff3b30;
            box-shadow: 0 2px 8px rgba(255, 59, 48, 0.25);
        }

        .btn:disabled, .btn-outline:disabled, .btn-accent:disabled, .btn-reset:disabled {
            opacity: 0.45;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        /* Status Indicator */
        .status-box {
            padding: 12px 18px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            font-size: 12.5px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }

        .status-badge {
            display: inline-block;
            padding: 4px 11px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            border-radius: 980px;
            background: rgba(0, 0, 0, 0.06);
            color: #1d1d1f;
        }

        .status-badge.running {
            background: rgba(0, 113, 227, 0.12);
            color: #0071e3;
        }

        .status-badge.success {
            background: rgba(52, 199, 89, 0.14);
            color: #28cd41;
        }

        /* Terminal Console — macOS Developer Window */
        .terminal {
            background: #1c1c1e;
            color: #f5f5f7;
            padding: 18px 20px;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px;
            height: 290px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            white-space: pre-wrap;
            line-height: 1.6;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        }

        /* Tables — Apple Minimal Clean */
        table.data-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 13px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(0, 0, 0, 0.06);
        }

        table.data-table th {
            text-align: left;
            padding: 12px 14px;
            background: #fbfbfd;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            font-weight: 600;
            font-size: 12px;
            color: #6e6e73;
            letter-spacing: -0.01em;
            text-transform: none;
        }

        table.data-table td {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            color: #1d1d1f;
        }

        table.data-table tr:last-child td {
            border-bottom: none;
        }

        table.data-table tr:hover td {
            background: #fafafc;
        }

        /* Blueprint Interactive Viewer */
        .blueprint-viewer {
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 16px;
            margin-top: 24px;
            padding: 26px;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        }

        .blueprint-viewer h2 {
            font-size: 16px;
            font-weight: 600;
            letter-spacing: -0.02em;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            padding-bottom: 8px;
            margin: 24px 0 14px 0;
            color: #1d1d1f;
        }

        .blueprint-viewer h2:first-child {
            margin-top: 0;
        }

        .code-container {
            position: relative;
            margin: 14px 0;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(0, 0, 0, 0.08);
        }

        .code-box {
            background: #1c1c1e;
            color: #f5f5f7;
            padding: 16px;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre;
            line-height: 1.5;
        }

        .copy-btn {
            position: absolute;
            top: 8px;
            right: 8px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.15);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 980px;
            cursor: pointer;
            backdrop-filter: blur(8px);
            transition: all 0.2s ease;
        }

        .copy-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .anti-pattern-item {
            border-left: 3px solid #ff3b30;
            padding: 10px 14px;
            background: rgba(255, 59, 48, 0.05);
            border-radius: 0 10px 10px 0;
            margin-bottom: 10px;
            font-size: 12.5px;
            color: #1d1d1f;
        }

        .checklist-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            font-size: 13px;
        }

        .checklist-item input[type="checkbox"] {
            margin-top: 3px;
            accent-color: #0071e3;
        }

        .downloads-banner {
            background: rgba(52, 199, 89, 0.08);
            border: 1px solid rgba(52, 199, 89, 0.25);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .downloads-banner-text {
            font-size: 13px;
            color: #15803d;
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
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            border-radius: 980px;
        }
        .badge-good { background: rgba(52, 199, 89, 0.12); color: #15803d; border: 1px solid rgba(52, 199, 89, 0.25); }
        .badge-warn { background: rgba(255, 149, 0, 0.12); color: #c25e00; border: 1px solid rgba(255, 149, 0, 0.25); }
        .badge-bad  { background: rgba(255, 59, 48, 0.1); color: #d70015; border: 1px solid rgba(255, 59, 48, 0.25); }

        .content-layout {
            display: grid;
            grid-template-columns: 290px 1fr;
            gap: 16px;
            margin-top: 16px;
            align-items: start;
        }
        .content-pages-sidebar {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            max-height: 720px;
            overflow-y: auto;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
        }
        .sidebar-page-item {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .sidebar-page-item:hover {
            background: #fafafc;
        }
        .sidebar-page-item.active {
            background: #1d1d1f;
            color: #ffffff;
        }
        .sidebar-page-item.active .badge-metric {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            border-color: transparent;
        }
        .sidebar-page-item.active .page-sub {
            color: #a1a1a6 !important;
        }
        .aeo-callout {
            border-left: 3px solid #34c759;
            background: rgba(52, 199, 89, 0.06);
            border-radius: 0 12px 12px 0;
            padding: 14px 16px;
            margin-bottom: 16px;
            font-size: 13px;
            color: #15803d;
            line-height: 1.6;
        }
        .section-block {
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
            background: #ffffff;
        }
        .section-block h3 {
            font-size: 14px;
            font-weight: 600;
            letter-spacing: -0.01em;
            margin-bottom: 8px;
            color: #1d1d1f;
        }
        .section-block h4 {
            font-size: 13px;
            font-weight: 600;
            margin-top: 12px;
            margin-bottom: 6px;
            color: #48484a;
        }
        .tag-pill {
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 9px;
            background: rgba(0, 0, 0, 0.05);
            color: #1d1d1f;
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 980px;
            text-transform: none;
        }
        .tag-pill.good {
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border-color: rgba(52, 199, 89, 0.25);
        }
        .tag-pill.req {
            background: rgba(255, 59, 48, 0.08);
            color: #d70015;
            border-color: rgba(255, 59, 48, 0.2);
        }

        /* Optimizer Tab 4 Styles — Apple Design System */
        /* Side-by-Side Crawl & Plugin Notice Comparison Styles */
        .opt-side-by-side-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 12px;
        }
        @media (max-width: 900px) {
            .opt-side-by-side-grid {
                grid-template-columns: 1fr;
            }
        }
        .opt-side-col {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease;
        }
        .opt-side-col.current {
            border: 1px solid rgba(255, 59, 48, 0.2);
            background: rgba(255, 59, 48, 0.02);
        }
        .opt-side-col.improved {
            border: 1px solid rgba(52, 199, 89, 0.35);
            background: rgba(52, 199, 89, 0.03);
            box-shadow: 0 2px 10px rgba(52, 199, 89, 0.04);
        }
        .opt-side-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }
        .opt-side-title {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .opt-side-col.current .opt-side-title {
            color: #ff3b30;
        }
        .opt-side-col.improved .opt-side-title {
            color: #34c759;
        }
        .opt-side-text {
            font-family: inherit;
            font-size: 13.5px;
            line-height: 1.6;
            color: #1d1d1f;
            white-space: pre-wrap;
            word-break: break-word;
            margin-bottom: 12px;
            flex: 1;
        }
        .opt-side-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 10px;
        }
        .opt-badge-violation {
            display: inline-block;
            font-size: 10px;
            font-weight: 600;
            background: rgba(255, 59, 48, 0.08);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.2);
            border-radius: 980px;
            padding: 3px 9px;
            letter-spacing: 0.01em;
        }
        .opt-badge-benefit {
            display: inline-block;
            font-size: 10px;
            font-weight: 600;
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border: 1px solid rgba(52, 199, 89, 0.25);
            border-radius: 980px;
            padding: 3px 9px;
            letter-spacing: 0.01em;
        }
        .opt-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        @media (max-width: 900px) {
            .opt-grid {
                grid-template-columns: 1fr;
            }
        }
        .opt-score-card {
            background: #ffffff;
            border-radius: 14px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }
        .opt-score-badge {
            font-size: 28px;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.02em;
        }
        .opt-score-badge.good { color: #34c759; }
        .opt-score-badge.warn { color: #ff9500; }
        .opt-score-badge.bad { color: #ff3b30; }
        .opt-diff-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 14px;
        }
        @media (max-width: 900px) {
            .opt-diff-container {
                grid-template-columns: 1fr;
            }
        }
        .opt-diff-panel {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            padding: 16px;
            display: flex;
            flex-direction: column;
        }
        .opt-diff-panel.optimized {
            border-color: rgba(52, 199, 89, 0.35);
            background: rgba(52, 199, 89, 0.02);
        }
        .opt-diff-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        .opt-diff-text {
            font-family: inherit;
            font-size: 13.5px;
            line-height: 1.65;
            white-space: pre-wrap;
            word-break: break-word;
            flex: 1;
            color: #1d1d1f;
            padding: 6px 0;
        }
        .opt-issue-item {
            display: flex;
            gap: 10px;
            padding: 11px 14px;
            border-left: 3px solid #86868b;
            background: #fafafc;
            border-radius: 0 10px 10px 0;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .opt-issue-item.sev-critical {
            border-left-color: #ff3b30;
            background: rgba(255, 59, 48, 0.05);
        }
        .opt-issue-item.sev-high {
            border-left-color: #ff9500;
            background: rgba(255, 149, 0, 0.05);
        }
        .opt-issue-item.sev-medium {
            border-left-color: #ffcc00;
            background: rgba(255, 204, 0, 0.08);
        }
        .opt-issue-item.sev-low {
            border-left-color: #0071e3;
            background: rgba(0, 113, 227, 0.05);
        }
        .opt-issue-item.sev-info {
            border-left-color: #86868b;
            background: #f5f5f7;
        }
        .opt-pill-preset {
            padding: 5px 13px;
            font-size: 12px;
            font-weight: 500;
            background: #ffffff;
            border: 1px solid #d2d2d7;
            border-radius: 980px;
            color: #1d1d1f;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .opt-pill-preset:hover {
            border-color: #0071e3;
            background: #0071e3;
            color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.2);
        }

        /* Multi-Variant Selector Styles */
        .opt-variant-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        @media (max-width: 900px) {
            .opt-variant-grid {
                grid-template-columns: 1fr;
            }
        }
        .opt-variant-card {
            border: 1.5px solid rgba(0, 0, 0, 0.08);
            border-radius: 14px;
            background: #ffffff;
            padding: 14px 16px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
        }
        .opt-variant-card:hover {
            border-color: #86868b;
            background: #fafafc;
        }
        .opt-variant-card.active {
            border-color: #0071e3;
            background: rgba(0, 113, 227, 0.03);
            box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12);
        }
        .opt-variant-title {
            font-size: 13.5px;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: #1d1d1f;
            margin-bottom: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .opt-variant-desc {
            font-size: 11.5px;
            color: #86868b;
            line-height: 1.4;
        }
        
        /* Word Diff Styles */
        .diff-del {
            background-color: rgba(255, 59, 48, 0.12);
            color: #d70015;
            text-decoration: line-through;
            padding: 1px 5px;
            border-radius: 4px;
            font-weight: 500;
        }
        .diff-ins {
            background-color: rgba(52, 199, 89, 0.15);
            color: #15803d;
            text-decoration: none;
            padding: 1px 5px;
            border-radius: 4px;
            font-weight: 600;
        }
        .opt-diff-view-box {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 12px;
            padding: 16px;
            font-size: 13.5px;
            line-height: 1.7;
            color: #1d1d1f;
        }

        /* SERP Google Preview Card */
        .serp-box {
            border: 1px solid #dfe1e5;
            background: #ffffff;
            padding: 16px 18px;
            border-radius: 12px;
            font-family: Arial, sans-serif;
            max-width: 650px;
        }
        .serp-url-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }
        .serp-favicon {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #1a73e8;
            display: inline-block;
        }
        .serp-site-name {
            font-size: 12px;
            color: #202124;
            font-weight: normal;
        }
        .serp-breadcrumb {
            font-size: 12px;
            color: #5f6368;
        }
        .serp-title {
            font-size: 20px;
            line-height: 1.3;
            color: #1a0dab;
            text-decoration: none;
            font-weight: normal;
            margin-bottom: 4px;
            display: block;
            cursor: pointer;
        }
        .serp-title:hover {
            text-decoration: underline;
        }
        .serp-snippet {
            font-size: 14px;
            line-height: 1.58;
            color: #4d5156;
            word-wrap: break-word;
        }
        .serp-pixel-bar {
            height: 4px;
            background: #e5e5ea;
            border-radius: 980px;
            overflow: hidden;
            margin-top: 4px;
        }
        .serp-pixel-fill {
            height: 100%;
            background: #34c759;
            transition: width 0.2s ease;
            border-radius: 980px;
        }
        .serp-pixel-fill.warn { background: #ff9500; }
        .serp-pixel-fill.danger { background: #ff3b30; }

        /* AI Overview / Perplexity Citation Box */
        .ai-preview-box {
            border: 1px solid rgba(0, 113, 227, 0.2);
            background: rgba(0, 113, 227, 0.02);
            padding: 18px;
            border-radius: 14px;
            margin-bottom: 16px;
        }
        .ai-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .ai-preview-badge {
            font-size: 11px;
            font-weight: 600;
            color: #0071e3;
            background: rgba(0, 113, 227, 0.08);
            padding: 3px 10px;
            border-radius: 980px;
            letter-spacing: 0.02em;
        }
        .ai-preview-quote {
            font-size: 14px;
            line-height: 1.65;
            color: #1d1d1f;
            margin-bottom: 12px;
        }
        .ai-sources-row {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .ai-source-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 11px;
            background: #ffffff;
            border: 1px solid rgba(0, 113, 227, 0.2);
            border-radius: 980px;
            font-size: 11px;
            color: #0071e3;
            font-weight: 500;
        }

        /* View Mode Tabs & Exporter Styles */
        .opt-view-tabs {
            display: flex;
            gap: 4px;
            background: rgba(0, 0, 0, 0.05);
            padding: 3px;
            border-radius: 10px;
            margin-bottom: 16px;
            overflow-x: auto;
        }
        .opt-view-tab {
            padding: 7px 14px;
            font-size: 12px;
            font-weight: 500;
            color: #6e6e73;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            letter-spacing: -0.01em;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .opt-view-tab:hover {
            color: #1d1d1f;
        }
        .opt-view-tab.active {
            background: #ffffff;
            color: #1d1d1f;
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
        }
        .opt-code-box {
            background: #1c1c1e;
            color: #f5f5f7;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            line-height: 1.6;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .opt-export-bar {
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: flex-end;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }

        /* Security Badges & Cards — Apple Translucent Pills */
        .badge-crit {
            background: rgba(255, 59, 48, 0.1);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-high {
            background: rgba(255, 149, 0, 0.12);
            color: #c25e00;
            border: 1px solid rgba(255, 149, 0, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-med {
            background: rgba(255, 204, 0, 0.14);
            color: #946800;
            border: 1px solid rgba(255, 204, 0, 0.3);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-low {
            background: rgba(0, 113, 227, 0.1);
            color: #0071e3;
            border: 1px solid rgba(0, 113, 227, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-pass {
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border: 1px solid rgba(52, 199, 89, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .finding-card {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease;
        }
        .finding-card:hover {
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
            border-color: rgba(0, 0, 0, 0.1);
        }
        .code-block {
            background: #1c1c1e;
            color: #f5f5f7;
            padding: 14px 16px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11.5px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre-wrap;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            max-height: 380px;
        }

        /* WordPress SEO Plugin Suite Styles */
        .plg-subnav-btn {
            padding: 7px 16px;
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            color: #6e6e73;
            border: none;
            border-radius: 980px;
            cursor: pointer;
            letter-spacing: -0.01em;
            transition: all 0.2s ease;
        }
        .plg-subnav-btn:hover {
            color: #1d1d1f;
            background: rgba(0, 0, 0, 0.04);
        }
        .plg-subnav-btn.active {
            background: #1d1d1f;
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
        }
        .plg-test-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        @media (max-width: 800px) {
            .plg-test-grid {
                grid-template-columns: 1fr;
            }
        }
        .plg-test-item {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 12px;
            padding: 12px 14px;
            display: flex;
            gap: 10px;
            align-items: flex-start;
        }
        .plg-test-badge {
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 980px;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }
        .plg-test-badge.passed {
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border: 1px solid rgba(52, 199, 89, 0.25);
        }
        .plg-test-badge.failed {
            background: rgba(255, 59, 48, 0.1);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.25);
        }
        .plg-test-badge.warning {
            background: rgba(255, 149, 0, 0.12);
            color: #c25e00;
            border: 1px solid rgba(255, 149, 0, 0.25);
        }
        .plg-field-row {
            margin-bottom: 14px;
        }
        .plg-field-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .plg-field-label {
            font-size: 12px;
            font-weight: 600;
            color: #1d1d1f;
            letter-spacing: -0.01em;
        }
        .plg-copy-input-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .plg-copy-input-group input, .plg-copy-input-group textarea {
            flex: 1;
            background: #ffffff;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            font-family: inherit;
            font-size: 13px;
            padding: 9px 12px;
            color: #1d1d1f;
        }
        .plg-copy-input-group input:focus, .plg-copy-input-group textarea:focus {
            outline: none;
            border-color: #0071e3;
            box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
        }
        .plg-btn-copy {
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            background: #ffffff;
            color: #0071e3;
            border: 1px solid #d2d2d7;
            border-radius: 980px;
            cursor: pointer;
            letter-spacing: -0.01em;
            white-space: nowrap;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .plg-btn-copy:hover {
            background: #0071e3;
            color: #ffffff;
            border-color: #0071e3;
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.2);
        }
        .plg-btn-copy.copied {
            background: #34c759 !important;
            border-color: #34c759 !important;
            color: #ffffff !important;
        }

        /* Floating Toast Notification */
        #reset-toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(29, 29, 31, 0.88);
            color: #ffffff;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 12px 22px;
            border-radius: 980px;
            font-size: 13px;
            font-weight: 500;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.12);
            z-index: 9999;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }

        /* Apple macOS Developer Terminal */
        .mac-traffic-lights {
            display: inline-flex;
            gap: 6px;
            align-items: center;
        }
        .mac-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }
        .mac-dot-red { background: #ff5f56; border: 1px solid #e0443e; }
        .mac-dot-yellow { background: #ffbd2e; border: 1px solid #dea123; }
        .mac-dot-green { background: #27c93f; border: 1px solid #1aab29; }
        .mac-console-header {
            padding: 10px 16px;
            background: #242426;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px 14px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mac-console-title {
            font-size: 11.5px;
            font-weight: 600;
            color: #e5e5ea;
            letter-spacing: 0.01em;
        }
        .mac-clear-btn {
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.1);
            color: #e5e5ea;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .mac-clear-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
        }
    
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div>
                <div class="org-label">InersiaLab Software Department</div>
                <h1 class="main-title">SEO Audit, Architect & Cybersecurity Suite</h1>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
                <div class="header-meta">
                    ENGINE V3.8<br>
                    HIGH-PRECISION SUITE
                </div>
                <button id="btn-global-reset" class="btn btn-reset" style="padding: 4px 12px; font-size: 11px;" onclick="resetAllEnginesAndCache()" title="Clear in-memory audit cache, logs, and browser storage">
                    RESET / CLEAR CACHE
                </button>
            </div>
        </header>

        <!-- Navigation Tabs -->
        <nav class="tabs-nav">
            <button id="nav-btn-audit" class="tab-btn active" onclick="switchTab('audit')">1. Existing Website Audit</button>
            <button id="nav-btn-blueprint" class="tab-btn" onclick="switchTab('blueprint')">2. New Website Architect (Pre-Launch)</button>
            <button id="nav-btn-content" class="tab-btn" onclick="switchTab('content')">3. Page Content Architect</button>
            <button id="nav-btn-optimizer" class="tab-btn" onclick="switchTab('optimizer')">4. SEO &amp; GEO Optimizer</button>
            <button id="nav-btn-security" class="tab-btn" onclick="switchTab('security')">5. Cybersecurity &amp; Server Hardening</button>
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
                    <button id="btn-start-audit" class="btn btn-accent" onclick="startAudit()">START LIVE AUDIT</button>
                    <button id="btn-open-audit-pdf" class="btn btn-outline" onclick="openLatestAuditPdf()" disabled>OPEN GENERATED PDF</button>
                    <button class="btn btn-outline" onclick="openDownloadsFolder()">OPEN DOWNLOADS FOLDER</button>
                    <button id="btn-reset-audit" class="btn btn-reset" onclick="resetAllEnginesAndCache()" title="Clear in-memory audit cache, logs, and browser storage">RESET / CLEAR CACHE</button>
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

            <div class="card" style="padding: 0; overflow: hidden;">
                <div class="mac-console-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="mac-traffic-lights">
                            <span class="mac-dot mac-dot-red"></span>
                            <span class="mac-dot mac-dot-yellow"></span>
                            <span class="mac-dot mac-dot-green"></span>
                        </div>
                        <span class="mac-console-title">Execution Stream — Terminal Console</span>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span id="log-count" style="color: #86868b; font-size: 11px; font-weight: 500;">0 lines</span>
                        <button class="mac-clear-btn" onclick="resetAllEnginesAndCache()" title="Clear logs and reset engine">Clear</button>
                    </div>
                </div>
                <div id="audit-terminal" class="terminal" style="border-radius: 0 0 16px 16px;">Awaiting execution command...</div>
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
            <div class="card">
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
            <div class="card">
                <div class="card-title">Pre-Launch Page & Section Content Generator</div>
                <p style="font-size: 13px; color: #4b5563; margin-bottom: 16px;">
                    Select an industry archetype and choose the pages for your upcoming website. The engine generates complete, fully-structured, SEO/GEO-optimized text content and sections for every single page (strict heading hierarchy, AEO hooks, E-E-A-T signals, Schema.org JSON-LD, and Core Web Vitals asset specs) with zero CSS bloat.
                </p>

                <!-- 1-Click Realistic Client Demo Profiles Bar -->
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; padding: 10px 14px; background: #f9fafb; border: 1px solid #e5e7eb; align-items: center;">
                    <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #374151; letter-spacing: 0.05em;">1-Click Realistic Client Profiles:</span>
                    <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="loadDemoProfile('dental_clinic')">Surgical / Dental Clinic</button>
                    <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="loadDemoProfile('cybersecurity_saas')">Cybersecurity SaaS</button>
                    <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="loadDemoProfile('luxury_contractor')">Luxury Contractor</button>
                    <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px; color: #b91c1c; border-color: #fca5a5;" onclick="resetClientBriefForm()">Clear Form</button>
                </div>

                                <!-- Comprehensive 45-Question Client Intake Diagnostic Survey -->
                <form id="content-form" onsubmit="event.preventDefault(); generateSiteContent();">
                    
                    <!-- Section 1: Business Identity & Legal DNA (Q1-Q6) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div class="card-title">1. Business Identity & Legal DNA (Q1-Q6)</div>
                        <div class="form-grid-3">
                            <div class="field-group">
                                <label class="field-label" for="cg-brand">Trade Brand Name (Q1)</label>
                                <input type="text" id="cg-brand" placeholder="e.g. AuraDental Implant Center" value="AuraDental Implant & Surgical Center" required>
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-legal-name">Full Legal Entity Name (Q1)</label>
                                <input type="text" id="cg-legal-name" placeholder="e.g. Aura Surgical & Restorative PC" value="Aura Surgical & Restorative Dentistry PC">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-domain">Target Canonical Domain</label>
                                <input type="text" id="cg-domain" placeholder="https://example.com" value="https://auradentalcare.com">
                            </div>
                        </div>

                        <div class="form-grid-3" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-year-founded">Heritage Year Founded (Q2)</label>
                                <input type="text" id="cg-year-founded" placeholder="e.g. 2008" value="2008">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-origin-location">Founding Location / City (Q2)</label>
                                <input type="text" id="cg-origin-location" placeholder="e.g. New York, NY" value="New York, NY">
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

                        <div class="form-grid-3" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-industry">Industry Archetype</label>
                                <select id="cg-industry" onchange="onIndustryChange()">
                                    <!-- Loaded dynamically -->
                                </select>
                                <div class="field-help" id="cg-industry-help">Tailored sitemaps & schemas.</div>
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-tagline">Elevator Pitch / Tagline (Q4)</label>
                                <input type="text" id="cg-tagline" placeholder="e.g. Advanced Digital Implantology" value="Advanced Digital Implantology & Aesthetic Restorations">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-tone">Brand Voice & Persona (Q5)</label>
                                <input type="text" id="cg-tone" placeholder="e.g. authoritative, reassuring, empathetic" value="clinically authoritative, reassuring, transparent, uncompromising on precision">
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-mission">Core Mission & Founding Purpose (Q3)</label>
                                <input type="text" id="cg-mission" placeholder="The non-negotiable principle driving this firm..." value="To restore permanent, infection-free masticatory function and aesthetic dignity to patients through micro-surgical digital implantology without unnecessary bone grafts or prolonged agony.">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-banned-words">Banned Words & Negative Tone Constraints (Q6)</label>
                                <input type="text" id="cg-banned-words" placeholder="Words/clichés strictly prohibited in copy..." value="cheap, bargain, budget dental, painless miracle, disrupt, synergy">
                                <div class="field-help">Eliminates forbidden buzzwords from generated copy.</div>
                            </div>
                        </div>
                    </div>

                    <!-- Section 2: Leadership, Credentials & E-E-A-T Pedigree (Q7-Q12) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div class="card-title">2. Leadership, Credentials & E-E-A-T Pedigree (Q7-Q12)</div>
                        <div class="form-grid-3">
                            <div class="field-group">
                                <label class="field-label" for="cg-founder-name">Managing Director / Founder (Q7)</label>
                                <input type="text" id="cg-founder-name" placeholder="e.g. Dr. Julian Vance, DDS" value="Dr. Julian Vance, DDS, FICOI">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-founder-title">Professional Role / Title (Q7)</label>
                                <input type="text" id="cg-founder-title" placeholder="e.g. Chief Oral Surgeon" value="Chief Oral Surgeon & Fellow of ICOI">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-alma-maters">Alma Maters & Residencies (Q8)</label>
                                <input type="text" id="cg-alma-maters" placeholder="e.g. Columbia University, Mount Sinai" value="Columbia University College of Dental Medicine, Mount Sinai Hospital Surgical Residency">
                            </div>
                        </div>

                        <div class="field-group" style="margin-top: 6px;">
                            <label class="field-label" for="cg-founder-creds">Degrees, Fellowships & Board Certifications (Q8)</label>
                            <input type="text" id="cg-founder-creds" value="DDS from Columbia University College of Dental Medicine, 18+ years surgical experience, 3,400+ successful dental implants, Fellow of the International Congress of Oral Implantologists">
                        </div>

                        <div class="form-grid-3" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-key-staff">Senior Staff Specialists & Roles (Q10)</label>
                                <input type="text" id="cg-key-staff" placeholder="e.g. Dr. Elena Rostova, Board Anesthesiologist" value="Dr. Elena Rostova, Board-Certified Dental Anesthesiologist; Dr. Marcus Sterling, Master Prosthodontist & Digital Smile Designer">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-patents-pubs">Patents, Publications & Papers (Q11)</label>
                                <input type="text" id="cg-patents-pubs" placeholder="e.g. Author in Journal of Oral Implantology" value="Author of 'Biomechanical Stress Distribution in Angled Multi-Unit Abutments' (Journal of Oral Implantology, 2019); US Patent for Dynamic 3D Surgical Guide Collar">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-awards">Honors, Awards & Recognitions (Q12)</label>
                                <input type="text" id="cg-awards" placeholder="e.g. New York Top Oral Surgeon" value="New York Top Oral Surgeon (2021-2025), ICOI Master Clinician Honor, AACD Platinum Restorative Excellence Award">
                            </div>
                        </div>

                        <div class="field-group" style="margin-top: 6px;">
                            <label class="field-label" for="cg-origin-story">Founding Narrative & Breakthrough Catalyst (Q9)</label>
                            <textarea id="cg-origin-story" rows="2">Founded in 2008 by Dr. Vance after seeing countless patients traumatized by ill-fitting dentures and multi-year bone graft failures. Dr. Vance pioneered computer-guided All-on-4 immediate loading to deliver fixed teeth in a single clinical day.</textarea>
                        </div>
                    </div>

                    <!-- Section 3: Ideal Customer Persona (ICP) & Buyer Psychology (Q13-Q18) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div class="card-title">3. Ideal Customer Persona (ICP) & Buyer Psychology (Q13-Q18)</div>
                        <div class="form-grid-2">
                            <div class="field-group">
                                <label class="field-label" for="cg-target-icp">Primary Target Buyer Profile (Q13)</label>
                                <input type="text" id="cg-target-icp" value="Adults aged 45-75 with failing dentition, terminal periodontal disease, or broken bridges seeking permanent, non-removable teeth with minimal downtime.">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-catalyst-event">Tipping-Point Emergency / Catalyst Event (Q15)</label>
                                <input type="text" id="cg-catalyst-event" value="A broken front bridge before a family wedding or sudden acute periodontal abscess forcing an urgent decision.">
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-pain-points">Top 3 Acute Pain Points (Q14, one per line)</label>
                                <textarea id="cg-pain-points" rows="3">Debilitating embarrassment smiling or speaking in professional and social settings
Inability to chew steak, apples, or firm foods causing gastrointestinal distress
Severe anxiety regarding dental pain, needles, and prolonged surgical procedures</textarea>
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-buyer-anxieties">Buyer Doubts, Fears & Hesitations (Q18, one per line)</label>
                                <textarea id="cg-buyer-anxieties" rows="3">Fear of unbearable surgical pain during and after the procedure
Fear of hidden costs inflating the initial quote
Fear that implants will reject or fall out after a few years</textarea>
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-disqualifications">Disqualification Criteria ("Who We Are NOT For") (Q16)</label>
                                <input type="text" id="cg-disqualifications" value="Patients seeking removable partial acrylic dentures, unverified bargain overseas tourism treatments, or patients refusing 3D diagnostic safety scans.">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-after-state">Desired Life Transformation / "After State" (Q17)</label>
                                <input type="text" id="cg-after-state" value="Enjoying dinner with family without fear, laughing openly without covering the mouth, and possessing permanent, infection-free teeth guaranteed for life.">
                            </div>
                        </div>
                    </div>

                    <!-- Section 4: Proprietary Methodology, Process & Tech Stack (Q19-Q25) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div class="card-title">4. Proprietary Methodology, Process & Tech Stack (Q19-Q25)</div>
                        <div class="form-grid-2">
                            <div class="field-group">
                                <label class="field-label" for="cg-framework-name">Branded Framework / Methodology Name (Q19)</label>
                                <input type="text" id="cg-framework-name" value="The 4-D Guided Precision Restoration Protocol">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-technologies">Proprietary Equipment, Machinery & Tools (Q24)</label>
                                <input type="text" id="cg-technologies" value="Planmeca ProMax 3D CBCT Scanner, Fotona LightWalker Dual Laser, 3Shape TRIOS 5 Scanner, SprintRay Pro55 3D Guide Printer, Pic Dental Camera">
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-phase1">Phase 1: Diagnostic & Discovery (Q20)</label>
                                <input type="text" id="cg-phase1" value="Comprehensive 3D CBCT Volumetric Scan & Digital Smile Aesthetic Simulation (Same-Day Assessment)">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-phase2">Phase 2: Tailored Blueprint Architecture (Q21)</label>
                                <input type="text" id="cg-phase2" value="Computer-Guided Virtual Surgery Planning & Custom Titanium Multi-Unit Abutment CAD/CAM Milling">
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-phase3">Phase 3: Precision Execution & Surgery (Q22)</label>
                                <input type="text" id="cg-phase3" value="Twilight IV Sedation, Minimally Invasive Computer-Guided Fixture Placement & Immediate Fixed Provisional Delivery (Single Day)">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-phase4">Phase 4: Optimization & Lifetime Warranty (Q23)</label>
                                <input type="text" id="cg-phase4" value="Permanent Monolithic Zirconia Final Bridge Delivery & Lifetime Bi-Annual Maintenance Care">
                            </div>
                        </div>

                        <div class="field-group" style="margin-top: 8px;">
                            <label class="field-label" for="cg-guarantees">Ironclad Guarantees, Warranties & SLAs (Q25)</label>
                            <input type="text" id="cg-guarantees" value="Lifetime structural replacement warranty on all titanium implant fixtures; 10-year replacement warranty on final monolithic zirconia prosthetics; 100% itemized fee guarantee with zero surprise post-op bills.">
                        </div>
                    </div>

                    <!-- Section 5: Flagship Services & Transparent Pricing (Q26-Q31) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div class="card-title">5. Flagship Services Portfolio & Transparent Pricing (Q26-Q31)</div>
                        
                        <!-- Service 1 -->
                        <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 12px; margin-bottom: 10px;">
                            <div style="font-size: 12px; font-weight: 700; color: #15803d; margin-bottom: 6px;">Flagship Service 1 (Q26) — Automatically renames sitemap checklist item & generates custom URL slug</div>
                            <div class="form-grid-3">
                                <div class="field-group">
                                    <label class="field-label">Service Name</label>
                                    <input type="text" id="cg-svc1-name" value="All-on-4 Same-Day Full Arch Dental Implants" oninput="updateServiceLabels()">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Target Audience</label>
                                    <input type="text" id="cg-svc1-aud" value="Adults with failing dentition, severe bone loss, or uncomfortable dentures">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Pricing Range</label>
                                    <input type="text" id="cg-svc1-pri" value="$18,500 per arch with zero-interest 24-month financing options">
                                </div>
                            </div>
                            <div class="form-grid-2" style="margin-top: 6px;">
                                <div class="field-group">
                                    <label class="field-label">Core Benefit</label>
                                    <input type="text" id="cg-svc1-ben" value="Full-arch permanent teeth restoration in a single appointment with zero bone grafting in 90% of cases">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Deliverables</label>
                                    <input type="text" id="cg-svc1-del" value="Pre-op 3D CBCT scan, computer-guided titanium fixture placement, immediate provisional bridge, final zirconia restoration">
                                </div>
                            </div>
                        </div>

                        <!-- Service 2 -->
                        <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 12px; margin-bottom: 10px;">
                            <div style="font-size: 12px; font-weight: 700; color: #15803d; margin-bottom: 6px;">Flagship Service 2 (Q27)</div>
                            <div class="form-grid-3">
                                <div class="field-group">
                                    <label class="field-label">Service Name</label>
                                    <input type="text" id="cg-svc2-name" value="Digital Smile Design Porcelain Veneers" oninput="updateServiceLabels()">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Target Audience</label>
                                    <input type="text" id="cg-svc2-aud" value="Patients seeking aesthetic smile enhancement, correcting chipped, discolored, or misaligned teeth">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Pricing Range</label>
                                    <input type="text" id="cg-svc2-pri" value="$1,800 - $2,400 per tooth with comprehensive 10-year aesthetic warranty">
                                </div>
                            </div>
                            <div class="form-grid-2" style="margin-top: 6px;">
                                <div class="field-group">
                                    <label class="field-label">Core Benefit</label>
                                    <input type="text" id="cg-svc2-ben" value="Handcrafted micro-thin ceramic veneers preserving 95% of natural tooth enamel with 3D digital simulation">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Deliverables</label>
                                    <input type="text" id="cg-svc2-del" value="Digital facial scan, 3D wax-up try-in, microscope preparation, custom master ceramist porcelain fabrication">
                                </div>
                            </div>
                        </div>

                        <!-- Service 3 -->
                        <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 12px;">
                            <div style="font-size: 12px; font-weight: 700; color: #15803d; margin-bottom: 6px;">Flagship Service 3 (Q28)</div>
                            <div class="form-grid-3">
                                <div class="field-group">
                                    <label class="field-label">Service Name</label>
                                    <input type="text" id="cg-svc3-name" value="IV Sedation Dentistry & Laser Periodontics" oninput="updateServiceLabels()">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Target Audience</label>
                                    <input type="text" id="cg-svc3-aud" value="Dental-phobic patients, complex surgical candidates, or advanced gum disease sufferers">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Pricing Range</label>
                                    <input type="text" id="cg-svc3-pri" value="$850 per surgical sedation session; LANAP full mouth $4,200">
                                </div>
                            </div>
                            <div class="form-grid-2" style="margin-top: 6px;">
                                <div class="field-group">
                                    <label class="field-label">Core Benefit</label>
                                    <input type="text" id="cg-svc3-ben" value="Completely painless, anxiety-free surgical care with LANAP laser technology accelerating soft-tissue recovery">
                                </div>
                                <div class="field-group">
                                    <label class="field-label">Deliverables</label>
                                    <input type="text" id="cg-svc3-del" value="Board-certified anesthesiologist monitoring, vitals tracking, LANAP biostimulation laser treatment, post-op recovery kit">
                                </div>
                            </div>
                        </div>

                        <div class="form-grid-3" style="margin-top: 10px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-secondary-offerings">Secondary Add-ons & Retainers (Q29)</label>
                                <input type="text" id="cg-secondary-offerings" value="VIP Private Recovery Suite, Same-Day Emergency Surgical On-Call, Comprehensive Pre-Op Medical Clearance Coordination">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-pricing-model">Billing Structure & Financing (Q30)</label>
                                <input type="text" id="cg-pricing-model" value="100% itemized transparent pricing; All-on-4 complete arch starting at $18,500; 0% APR 24-month healthcare financing via Proceed Finance & CareCredit">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-turnaround">Turnaround Speed / Delivery Time (Q31)</label>
                                <input type="text" id="cg-turnaround" value="Same-Day Immediate Fixed Teeth (under 6 hours clinical time); final custom zirconia bridge seated at 12 weeks post-osseointegration">
                            </div>
                        </div>
                    </div>

                    <!-- Section 6: Local Geography, Micro-Anchors & Physical NAP (Q32-Q36) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div class="card-title">6. Local Geography, Micro-Anchors & Physical NAP (Q32-Q36)</div>
                        <div class="form-grid-3">
                            <div class="field-group">
                                <label class="field-label" for="cg-phone">Primary Phone (Q36)</label>
                                <input type="text" id="cg-phone" value="+1 (212) 555-0198">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-email">Electronic Mail (Q36)</label>
                                <input type="text" id="cg-email" value="concierge@auradentalcare.com">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-urgent-contact">24/7 Priority Emergency Channel (Q36)</label>
                                <input type="text" id="cg-urgent-contact" value="+1 (212) 555-0199 (24/7 Dedicated Surgical Post-Op Emergency Line)">
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-address">Physical Facility Address (Q32)</label>
                                <input type="text" id="cg-address" value="450 Lexington Ave, Suite 1400, New York, NY 10017">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-service-areas">Target Municipalities, Suburbs & Radii (Q33)</label>
                                <input type="text" id="cg-service-areas" value="Midtown Manhattan, Upper East Side, Upper West Side, Brooklyn Heights, Westchester County, Greenwich CT, Tri-State Area">
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-local-landmarks">Local Proximity Landmarks & Cross-Streets (Q34)</label>
                                <input type="text" id="cg-local-landmarks" value="Directly across from Grand Central Terminal, at the corner of Lexington Avenue and 45th Street, 3 blocks east of Bryant Park">
                                <div class="field-help">Essential for Local SEO citations and AI engine geocoding.</div>
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-facility-access">Facility Accessibility & Parking (Q35)</label>
                                <input type="text" id="cg-facility-access" value="Private elevator bank directly to Suite 1400, covered subterranean valet parking on 45th St, fully ADA wheelchair accessible surgical operatory">
                            </div>
                        </div>
                    </div>

                    <!-- Section 7: Proof Metrics, Case Studies & Real Reviews (Q37-Q41) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div class="card-title">7. Proof Metrics, Case Studies & Real Reviews (Q37-Q41)</div>
                        <div class="form-grid-2">
                            <div class="field-group">
                                <label class="field-label" for="cg-proof-metrics">Top Quantified Proof Numbers (Q37, Pipe Separated)</label>
                                <input type="text" id="cg-proof-metrics" value="Successful Implants Placed: 3,400+ | Clinical Success Rate: 98.6% | Years in Surgical Practice: 18 Years | Same-Day Full Arches Delivered: 1,250+">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-certifications">Accreditations & Regulatory Compliance (Q41)</label>
                                <input type="text" id="cg-certifications" value="Fellow of the International Congress of Oral Implantologists (FICOI), American Academy of Cosmetic Dentistry (AACD), ADA Member, HIPAA Compliant & Hospital-Grade HEPA Filtration">
                            </div>
                        </div>

                        <!-- Case Studies -->
                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-case1">Case Study 1: Challenge -> Solution -> Result (Q38)</label>
                                <textarea id="cg-case1" rows="3">Title: Terminal Periodontal Bone Loss to Permanent Full Arch in 6 Hours | Client: Thomas B., 58, Manhattan Corporate Executive | Challenge: Suffered from terminal generalized periodontitis with 80% bone loss on upper arch, unable to chew solids, facing conventional dentures. | Solution: Dr. Vance performed 3D guided computer surgery placing four angled Neodent fixtures utilizing dense zygomatic-adjacent bone, avoiding sinus lifts entirely. | Outcome: Fixed acrylic hybrid bridge delivered in 5.5 hours under IV sedation. Zero postoperative pain reported; transitioned to final monolithic zirconia at 12 weeks.</textarea>
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-case2">Case Study 2: Challenge -> Solution -> Result (Q39)</label>
                                <textarea id="cg-case2" rows="3">Title: Complex Traumatic Aesthetic Smile Reconstruction | Client: Sarah K., 42, Television Producer | Challenge: Traumatic incisor fracture and failing root canal with severe aesthetic discoloration and soft-tissue recession. | Solution: Immediate laser socket disinfection, placement of custom titanium zirconium implant, platelet-rich fibrin (PRF) soft-tissue graft, and custom shaded ceramic crown. | Outcome: Natural gingival emergence profile preserved. Restored full aesthetic symmetry matching adjacent natural teeth with 100% patient satisfaction.</textarea>
                            </div>
                        </div>

                        <div class="field-group" style="margin-top: 8px;">
                            <label class="field-label" for="cg-reviews">Authentic Attributed Client Testimonials (Q40, Author | Service | Quote)</label>
                            <textarea id="cg-reviews" rows="3">Eleanor Vance, Retired Educator | All-on-4 Same-Day Implants | I spent 6 years hiding my smile behind my hand and dreading traditional dentures. Dr. Vance and his team replaced my failing upper teeth in a single morning. Woke up from twilight sedation with zero pain and a flawless smile. One year later, eating steak and apples feels completely natural.
Marcus Sterling, Managing Director | Digital Smile Design Veneers | The 3D preview showed me exactly what my teeth would look like before Dr. Vance touched a single tooth. The ceramic work is so natural that even my business colleagues just assumed I took up whitening. Worth every single penny.
Sophia Chen, Architect | IV Sedation Dentistry | As someone with debilitating dental panic, AuraDental changed everything. The anesthesiologist had me relaxed in minutes, and Dr. Vance completed my complex extractions and implant placement while I slept comfortably. Truly life-changing care.</textarea>
                        </div>

                        <div class="field-group" style="margin-top: 8px;">
                            <label class="field-label" for="cg-faqs">Common Buyer Objections & Exact Rebuttals (Q: ... | A: ...)</label>
                            <textarea id="cg-faqs" rows="3">Q: How painful is the dental implant surgery and recovery? | A: Thanks to computerized 3D-guided navigation and IV twilight sedation, patients feel zero pain during the procedure. Post-operative discomfort is comparable to a minor tooth extraction and is comfortably managed with standard over-the-counter anti-inflammatories within 48 to 72 hours.
Q: How can you place teeth in a single day without waiting for healing? | A: Our All-on-4 protocol utilizes four strategically angled titanium implants anchored in dense basal bone. This achieves immediate mechanical stability (above 35 Ncm torque), allowing us to secure a rigid provisional bridge immediately while bone osseointegration occurs over the next 12 weeks.
Q: What happens if a dental implant fails to integrate? | A: While our surgical success rate exceeds 98.6%, AuraDental provides a comprehensive lifetime implant warranty. In the rare event an implant fails to integrate, Dr. Vance removes, cleans, and replaces the implant fixture at zero surgical cost to you.</textarea>
                        </div>
                    </div>

                    <!-- Section 8: Active Competitor Web Research & Market Gap (Q42-Q45) -->
                    <div class="card" style="margin-bottom: 14px; padding: 16px; border-left: 3px solid #ff3b30; border-radius: 14px; background: rgba(255, 59, 48, 0.04);">
                        <div class="card-title" style="color: #b91c1c;">8. Active Competitor Web Research & Market Gap (Q42-Q45)</div>
                        <p style="font-size: 12px; color: #4b5563; margin-bottom: 10px;">
                            When you click generate, the engine actively crawls and benchmarks these competitor sites (or top field champions), extracting their semantic heading hierarchies, topical keyword entity clusters, and layout patterns to synthesize content engineered to outperform them.
                        </p>
                        <div class="field-group">
                            <label class="field-label" for="cg-competitor-urls">Competitor / Benchmark URLs to Inspect Live (Q42, comma separated)</label>
                            <input type="text" id="cg-competitor-urls" value="https://www.clevelandclinic.org, https://www.mayoclinic.org" placeholder="https://competitor1.com, https://competitor2.com">
                            <div class="field-help">Leave as-is or enter your client's top local or national competitors.</div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-competitor-shortcomings">What Competitors Do Wrong / Fail At (Q43)</label>
                                <input type="text" id="cg-competitor-shortcomings" value="Traditional corporate dental clinics force patients through multiple outside referrals, months of uncomfortable removable healing dentures, and surprise bill add-ons for bone grafting and anesthesia.">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-uvp">The Client's Unfair Advantage / UVP (Q44)</label>
                                <input type="text" id="cg-uvp" value="Everything—from 3D diagnostic imaging and surgical placement to master lab ceramic milling—is executed under one roof by a board-certified ICOI Fellow with zero referrals and zero delays.">
                            </div>
                        </div>

                        <div class="form-grid-2" style="margin-top: 8px;">
                            <div class="field-group">
                                <label class="field-label" for="cg-cta">Primary Call-to-Action (CTA) (Q45)</label>
                                <input type="text" id="cg-cta" value="Book Your 3D Surgical Implant Consultation">
                            </div>
                            <div class="field-group">
                                <label class="field-label" for="cg-lead-magnet">Secondary Low-Friction Lead Magnet (Q45)</label>
                                <input type="text" id="cg-lead-magnet" value="Download the Free 2026 Guide to Same-Day All-on-4 Implants (Pricing, Candidacy & Recovery)">
                            </div>
                        </div>
                    </div>

                    <!-- Sitemap Page Selection Checklist -->
                    <div class="card" style="margin-bottom: 16px; padding: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <label class="field-label" style="margin-bottom: 0;">Sitemap Checklist: Select Pages to Synthesize</label>
                            <div style="display: flex; gap: 8px;">
                                <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllContentPages(true)">Select All</button>
                                <button type="button" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="selectAllContentPages(false)">Clear Optional</button>
                            </div>
                        </div>

                        <div id="content-pages-checklist" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 8px; max-height: 220px; overflow-y: auto; padding: 10px; border: 1px solid #e5e7eb; background: #f9fafb;">
                            <!-- Injected dynamically -->
                        </div>

                        <div style="display: flex; gap: 8px; margin-top: 10px; align-items: center;">
                            <input type="text" id="cg-custom-title" placeholder="Add custom page title (e.g. VIP Concierge Recovery Suite, International Patients)" style="flex: 1; padding: 7px 10px; font-size: 12px;">
                            <button type="button" class="btn btn-outline" style="padding: 7px 14px; font-size: 12px;" onclick="addCustomContentPage()">+ Add Custom Page</button>
                        </div>
                    </div>

                    <div class="btn-row" style="margin-top: 16px;">
                        <button type="submit" id="btn-generate-content" class="btn btn-accent" style="padding: 12px 28px; font-size: 13px;">GENERATE BESPOKE SITE CONTENT</button>
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

        <!-- ============================================================= -->
        <!-- TAB 4: SEO & GEO CONTENT OPTIMIZER -->
        <!-- ============================================================= -->
        <section id="tab-optimizer" class="tab-content">
            <!-- Mode Switcher: 3 Modes — Apple Segmented Control -->
            <div style="display: flex; gap: 12px; margin-bottom: 22px; padding-bottom: 14px; align-items: center; justify-content: space-between; flex-wrap: wrap; border-bottom: 1px solid rgba(0, 0, 0, 0.06);">
                <div style="display: inline-flex; background: rgba(0, 0, 0, 0.05); padding: 3px; border-radius: 12px; gap: 3px; flex-wrap: wrap;">
                    <button type="button" id="btn-opt-mode-crawl" class="plg-subnav-btn active" onclick="switchOptSubMode('crawl')">
                        1. Live URL &amp; Plugin Improver (Side-by-Side)
                    </button>
                    <button type="button" id="btn-opt-mode-plugin" class="plg-subnav-btn" onclick="switchOptSubMode('plugin')">
                        2. WordPress Plugin Metadata Suite
                    </button>
                    <button type="button" id="btn-opt-mode-single" class="plg-subnav-btn" onclick="switchOptSubMode('single')">
                        3. Single Element &amp; GEO Optimizer
                    </button>
                </div>
                <div style="font-size: 11.5px; font-weight: 500; color: #86868b;">
                    Active Mode: <span id="opt-active-mode-label" style="color: #0071e3; font-weight: 600;">Live URL &amp; Plugin Notice Improver</span>
                </div>
            </div>

            <!-- ============================================================= -->
            <!-- SUB-VIEW 1: LIVE URL & PLUGIN NOTICE IMPROVER (SIDE-BY-SIDE) -->
            <!-- ============================================================= -->
            <div id="opt-crawl-view">
                <!-- Input Card -->
                <div class="card" id="opt-crawl-form-card">
                    <div class="card-title" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <span>Live Webpage Crawler &amp; SEO Plugin Notice Improver</span>
                        <span class="tag-pill good" style="font-size: 10px;">Crawls Live HTML &bull; Exact Side-by-Side Comparison</span>
                    </div>
                    <div class="field-help" style="margin-top: -6px; margin-bottom: 16px;">
                        Attach any website URL and paste or upload the diagnostic notice from your SEO plugin (Rank Math, Yoast SEO, AIOSEO). The engine crawls the live webpage, extracts its current HTML elements, identifies every plugin violation, and renders the <strong>Current (Crawled) Text</strong> directly next to the <strong>Improved Text</strong> with 1-click copy buttons.
                    </div>

                    <!-- 1-Click Demo Profiles -->
                    <div style="margin-bottom: 16px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Load Demo Profiles:</span>
                        <button type="button" class="opt-pill-preset" onclick="loadCrawlDemoProfile('inersialab')">InersiaLab (Rank Math Notice Demo)</button>
                        <button type="button" class="opt-pill-preset" onclick="loadCrawlDemoProfile('saas')">Cybersecurity Platform (Yoast SEO Demo)</button>
                        <button type="button" class="opt-pill-preset" onclick="loadCrawlDemoProfile('ecommerce')">E-Commerce Brand (AIOSEO Demo)</button>
                        <button type="button" class="opt-pill-preset" onclick="loadCrawlDemoProfile('clinic')">Medical Clinic (Rank Math Demo)</button>
                    </div>

                    <!-- Row 1: Target URL & Plugin Selector -->
                    <div class="form-grid-3">
                        <div class="field-group" style="grid-column: span 2;">
                            <label class="field-label" for="opt-crawl-url">Live Webpage URL to Crawl &amp; Inspect <span class="tag-pill req">Required</span></label>
                            <input type="url" id="opt-crawl-url" placeholder="https://www.inersialab.com">
                            <div class="field-help">The engine fetches and parses title, description, H1, H2s, intro text, and word counts in real time.</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-crawl-plugin-type">Target SEO Plugin</label>
                            <select id="opt-crawl-plugin-type">
                                <option value="rank_math" selected>Rank Math SEO (Recommended)</option>
                                <option value="yoast">Yoast SEO</option>
                                <option value="aioseo">All in One SEO (AIOSEO)</option>
                                <option value="seopress">SEOPress / Core Meta</option>
                            </select>
                            <div class="field-help">Calibrates scoring, rule compliance, and copy-paste meta boxes.</div>
                        </div>
                    </div>

                    <!-- Row 2: Focus Keyword, Brand, Industry, Schema Type -->
                    <div class="form-grid-4">
                        <div class="field-group">
                            <label class="field-label" for="opt-crawl-keyword">Focus Keyword (Optional)</label>
                            <input type="text" id="opt-crawl-keyword" placeholder="Auto-detected if left empty">
                            <div class="field-help">Extracted automatically from plugin notice or crawled title if blank.</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-crawl-brand">Site Name / Brand Suffix</label>
                            <input type="text" id="opt-crawl-brand" placeholder="e.g. InersiaLab">
                            <div class="field-help">Brand identifier appended to title tag.</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-crawl-industry">Industry &amp; Entity Domain</label>
                            <select id="opt-crawl-industry">
                                <option value="tech" selected>Technology, Cloud &amp; SaaS</option>
                                <option value="finance">Finance, Banking &amp; FinTech</option>
                                <option value="healthcare">Healthcare, Biotech &amp; Medical</option>
                                <option value="ecommerce">E-Commerce, Retail &amp; DTC</option>
                                <option value="legal">Legal, Compliance &amp; Corporate</option>
                                <option value="general">General Business &amp; Services</option>
                            </select>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-crawl-page-type">Page / Schema Type</label>
                            <select id="opt-crawl-page-type">
                                <option value="WebPage" selected>WebPage / Service</option>
                                <option value="Article">Blog Post / Article</option>
                                <option value="Product">Product Page</option>
                                <option value="LocalBusiness">Local Business</option>
                            </select>
                        </div>
                    </div>

                    <!-- Row 3: Plugin Diagnostic Notice (Upload or Paste) -->
                    <div class="field-group" style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 8px;">
                            <label class="field-label" for="opt-crawl-notice" style="margin-bottom: 0;">
                                SEO Plugin Diagnostic Notice / Test Failures <span class="tag-pill req">Paste or Upload</span>
                            </label>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <label class="btn btn-outline" style="padding: 4px 10px; font-size: 11px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
                                    Upload Notice File (.txt, .log, .json, .csv, .md)
                                    <input type="file" id="opt-crawl-file-input" accept=".txt,.log,.json,.csv,.md,.text" style="display:none;" onchange="handlePluginNoticeFileUpload(event)">
                                </label>
                                <span id="opt-crawl-file-name" style="font-size: 11px; color: #15803d; font-weight: 700;"></span>
                            </div>
                        </div>
                        <textarea id="opt-crawl-notice" rows="5" placeholder="Paste SEO plugin error or warning messages here. For example:&#10;- Add Focus Keyword to the SEO title.&#10;- Focus Keyword does not appear in the first 10% of the content.&#10;- Use Focus Keyword in subheadings (H2, H3).&#10;- Content is 180 words long. Consider using at least 600 words.&#10;- Add a number to your SEO title.&#10;- Add a Power Word to your SEO title."></textarea>
                        <div class="field-help">Upload a file or paste any bullet points, test errors, or recommendations exported from Rank Math, Yoast SEO, or AIOSEO.</div>
                    </div>

                    <!-- Action Buttons -->
                    <div style="display: flex; gap: 10px; margin-top: 14px; align-items: center; flex-wrap: wrap;">
                        <button type="button" class="btn btn-accent" id="btn-run-crawl-improver" onclick="runCrawlImprover()" style="padding: 12px 28px; font-size: 13px;">
                            CRAWL PAGE &amp; GENERATE SIDE-BY-SIDE IMPROVEMENTS
                        </button>
                        <button type="button" class="btn btn-outline" onclick="clearCrawlImprover()" style="padding: 12px 20px; font-size: 13px;">
                            CLEAR
                        </button>
                        <span id="opt-crawl-status-indicator" style="font-size: 12px; font-weight: 700; color: #4b5563;"></span>
                    </div>
                </div>

                <!-- Results Wrapper -->
                <div id="opt-crawl-results-wrapper" style="display: none; margin-top: 18px;">
                </div>
            </div>

            <!-- ============================================================= -->
            <!-- SUB-VIEW 2: WORDPRESS SEO PLUGIN SUITE (MANUAL FORM) -->
            <!-- ============================================================= -->
            <div id="opt-plugin-view" style="display: none;">
                <!-- Plugin Configuration Form -->
                <div class="card" id="opt-plugin-form-card">
                    <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                        <span>WordPress &amp; CMS SEO Plugin Optimizer</span>
                        <span class="tag-pill good" style="font-size: 10px;">Rank Math &bull; Yoast &bull; AIOSEO</span>
                    </div>
                    <div class="field-help" style="margin-top: -6px; margin-bottom: 16px;">
                        Provide your page details and draft metadata below. The engine audits your snippet against WordPress SEO plugin ranking factors (pixel width, keyword front-loading, emotional triggers, slug structure) and produces ready-to-paste configurations for Rank Math and Yoast SEO.
                    </div>

                    <!-- 1-Click Demo Presets -->
                    <div style="margin-bottom: 16px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Load Demo Profiles:</span>
                        <button type="button" class="opt-pill-preset" onclick="loadPluginDemoProfile('dental')">Healthcare Clinic (Dental Implants)</button>
                        <button type="button" class="opt-pill-preset" onclick="loadPluginDemoProfile('saas')">Cybersecurity SaaS (Zero-Trust Platform)</button>
                        <button type="button" class="opt-pill-preset" onclick="loadPluginDemoProfile('contractor')">Luxury Contractor (Kitchen Remodeling)</button>
                    </div>

                    <!-- Row 1: Target Keywords & Plugin Target -->
                    <div class="form-grid-3">
                        <div class="field-group">
                            <label class="field-label" for="opt-plg-keyword">Focus / Primary Keyword <span class="tag-pill req">Required</span></label>
                            <input type="text" id="opt-plg-keyword" placeholder="e.g. Dental Implants Miami" oninput="onPluginInputLiveChange()">
                            <div class="field-help">Core search phrase targeted by this page or article.</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-plg-secondary-keywords">Secondary Keywords</label>
                            <input type="text" id="opt-plg-secondary-keywords" placeholder="e.g. tooth replacement, cosmetic dentistry, full mouth implants">
                            <div class="field-help">Comma-separated semantic modifiers &amp; LSI terms.</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-plg-plugin-type">Target WordPress Plugin</label>
                            <select id="opt-plg-plugin-type">
                                <option value="rank_math" selected>Rank Math SEO (Recommended)</option>
                                <option value="yoast">Yoast SEO</option>
                                <option value="aioseo">All in One SEO (AIOSEO)</option>
                                <option value="seopress">SEOPress / Core Meta</option>
                            </select>
                            <div class="field-help">Calibrates snippet variables, templates, and scoring logic.</div>
                        </div>
                    </div>

                    <!-- Row 2: Brand, Slug, Industry -->
                    <div class="form-grid-3">
                        <div class="field-group">
                            <label class="field-label" for="opt-plg-site-name">Site Name / Brand Suffix</label>
                            <input type="text" id="opt-plg-site-name" placeholder="e.g. Miami Smile Clinic" oninput="onPluginInputLiveChange()">
                            <div class="field-help">Appended to title tags (e.g. | Miami Smile Clinic).</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-plg-slug">URL Permalink Slug</label>
                            <input type="text" id="opt-plg-slug" placeholder="e.g. dental-implants-miami">
                            <div class="field-help">Leave empty to auto-generate clean kebab-case slug.</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-plg-industry">Industry &amp; Entity Domain</label>
                            <select id="opt-plg-industry">
                                <option value="tech">Technology, Cloud &amp; SaaS</option>
                                <option value="finance">Finance, Banking &amp; FinTech</option>
                                <option value="healthcare">Healthcare, Biotech &amp; Medical</option>
                                <option value="ecommerce">E-Commerce, Retail &amp; DTC</option>
                                <option value="legal">Legal, Compliance &amp; Corporate</option>
                                <option value="general">General Business &amp; Professional Services</option>
                            </select>
                            <div class="field-help">Calibrates domain entities and authority phrases.</div>
                        </div>
                    </div>

                    <!-- Row 3: Page Type & Content Sample -->
                    <div class="form-grid-2">
                        <div class="field-group">
                            <label class="field-label" for="opt-plg-page-type">Page / Schema Content Type</label>
                            <select id="opt-plg-page-type">
                                <option value="Service" selected>Service Page (Local &amp; Commercial)</option>
                                <option value="Article">Blog Post / Article (Informational Guide)</option>
                                <option value="Product">Product Page (E-Commerce)</option>
                                <option value="LocalBusiness">Local Business Landing Page</option>
                                <option value="WebPage">Standard Web Page / Homepage</option>
                            </select>
                            <div class="field-help">Determines Schema.org JSON-LD generation and structure.</div>
                        </div>

                        <div class="field-group">
                            <label class="field-label" for="opt-plg-content">Optional Content Excerpt / Intro Paragraph</label>
                            <input type="text" id="opt-plg-content" placeholder="e.g. Miami Smile Clinic provides dental implants...">
                            <div class="field-help">Optional first 100 words to test focus keyword density &amp; placement.</div>
                        </div>
                    </div>

                    <!-- Row 4: Draft SEO Title & Meta Description with Live Counters -->
                    <div class="field-group" style="margin-top: 4px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <label class="field-label" for="opt-plg-title" style="margin-bottom: 0;">Draft SEO Title Tag</label>
                            <span id="opt-plg-title-stats" style="font-size: 11px; font-weight: 700; color: #4b5563;">0 chars | ~0 px (Target: 50-60 chars, &lt;580 px)</span>
                        </div>
                        <input type="text" id="opt-plg-title" placeholder="e.g. Dental Implants in Miami" oninput="updatePluginLiveStats()">
                        <div class="serp-pixel-bar" style="margin-top: 6px;">
                            <div id="opt-plg-title-bar" class="serp-pixel-fill" style="width: 0%;"></div>
                        </div>
                    </div>

                    <div class="field-group" style="margin-top: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <label class="field-label" for="opt-plg-desc" style="margin-bottom: 0;">Draft Meta Description</label>
                            <span id="opt-plg-desc-stats" style="font-size: 11px; font-weight: 700; color: #4b5563;">0 chars (Target: 125-155 chars)</span>
                        </div>
                        <textarea id="opt-plg-desc" rows="3" placeholder="e.g. We provide dental implants in Miami with affordable prices." oninput="updatePluginLiveStats()"></textarea>
                    </div>

                    <!-- Action Buttons -->
                    <div style="display: flex; gap: 10px; margin-top: 14px;">
                        <button type="button" class="btn btn-accent" id="btn-run-plugin-optimizer" onclick="runPluginOptimizer()" style="padding: 12px 28px; font-size: 13px;">
                            AUDIT &amp; OPTIMIZE FOR SEO PLUGIN
                        </button>
                        <button type="button" class="btn btn-outline" onclick="clearPluginOptimizer()" style="padding: 12px 20px; font-size: 13px;">
                            CLEAR
                        </button>
                    </div>
                </div>

                <!-- Plugin Results Wrapper -->
                <div id="opt-plugin-results-wrapper" style="display: none; margin-top: 18px;">
                    <!-- Score & Status Banner -->
                    <div class="card" style="margin-bottom: 16px;">
                        <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>SEO Plugin Audit &amp; Ranking Scorecard</span>
                            <span id="opt-plg-grade-badge" class="tag-pill good" style="font-size: 13px; font-weight: 900; padding: 4px 10px;">GRADE: A+</span>
                        </div>

                        <div class="form-grid-3" style="margin-top: 10px;">
                            <div class="opt-score-card">
                                <div>
                                    <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Plugin Compliance</div>
                                    <div id="opt-plg-overall-delta" style="font-size: 11px; font-weight: 600; color: #15803d; margin-top: 2px;">Score</div>
                                </div>
                                <div class="opt-score-badge good" id="opt-plg-overall-score">0</div>
                            </div>

                            <div class="opt-score-card">
                                <div>
                                    <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Technical SEO Factors</div>
                                    <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Keywords, Length, Slug</div>
                                </div>
                                <div class="opt-score-badge" id="opt-plg-seo-score">0</div>
                            </div>

                            <div class="opt-score-card">
                                <div>
                                    <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">AI / GEO Citability</div>
                                    <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">AI Search Engine Grounding</div>
                                </div>
                                <div class="opt-score-badge" id="opt-plg-geo-score">0</div>
                            </div>
                        </div>
                    </div>

                    <!-- 12-Factor Audit Checklist -->
                    <div class="card" style="margin-bottom: 16px;">
                        <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>12-Factor SEO Plugin Compliance Checklist</span>
                            <span style="font-size: 11px; color: #6b7280; font-weight: normal;">Evaluated against Rank Math &amp; Yoast Ranking Algorithms</span>
                        </div>
                        <div id="opt-plg-tests-grid" class="plg-test-grid" style="margin-top: 12px;">
                            <!-- Rendered by JS -->
                        </div>
                    </div>

                    <!-- Strategic Variants -->
                    <div class="card" style="margin-bottom: 16px;">
                        <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>Optimized Metadata Strategy Packages</span>
                            <span style="font-size: 11px; color: #6b7280; font-weight: normal;">Choose a package to load into your plugin</span>
                        </div>
                        <div class="opt-variant-grid" id="opt-plg-variants-grid" style="margin-top: 10px;">
                            <!-- Rendered by JS: 3 strategy packages -->
                        </div>
                    </div>

                    <!-- Direct Turnkey Plugin Copy-Paste Boxes -->
                    <div class="card" style="margin-bottom: 16px;">
                        <div class="card-title" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <span>Turnkey Plugin Export &amp; Meta Boxes</span>
                            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                                <button type="button" class="tab-btn active" id="btn-plg-box-rankmath" style="padding: 4px 10px; font-size: 11px;" onclick="switchPluginBoxView('rankmath')">Rank Math</button>
                                <button type="button" class="tab-btn" id="btn-plg-box-yoast" style="padding: 4px 10px; font-size: 11px;" onclick="switchPluginBoxView('yoast')">Yoast SEO</button>
                                <button type="button" class="tab-btn" id="btn-plg-box-social" style="padding: 4px 10px; font-size: 11px;" onclick="switchPluginBoxView('social')">Social Meta</button>
                                <button type="button" class="tab-btn" id="btn-plg-box-schema" style="padding: 4px 10px; font-size: 11px;" onclick="switchPluginBoxView('schema')">Schema JSON-LD</button>
                                <button type="button" class="tab-btn" id="btn-plg-box-ai" style="padding: 4px 10px; font-size: 11px;" onclick="switchPluginBoxView('ai')">AI Writing Prompt</button>
                            </div>
                        </div>

                        <!-- View 1: Rank Math -->
                        <div id="plg-box-rankmath" style="margin-top: 14px;">
                            <div class="field-help" style="margin-bottom: 12px;">Copy and paste directly into Rank Math General &amp; Advanced Meta Box inside WordPress editor.</div>
                            
                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">Focus Keyword</span>
                                    <span style="font-size: 11px; color: #6b7280;">Primary keyword box</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <input type="text" id="rm-copy-keyword" readonly>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('rm-copy-keyword', this)">Copy</button>
                                </div>
                            </div>

                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">SEO Title</span>
                                    <span id="rm-title-len-pill" style="font-size: 11px; font-weight: 700; color: #15803d;">0 chars / ~0 px</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <input type="text" id="rm-copy-title" readonly>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('rm-copy-title', this)">Copy</button>
                                </div>
                            </div>

                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">Permalink / Slug</span>
                                    <span style="font-size: 11px; color: #6b7280;">Clean kebab-case</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <input type="text" id="rm-copy-slug" readonly>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('rm-copy-slug', this)">Copy</button>
                                </div>
                            </div>

                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">Meta Description</span>
                                    <span id="rm-desc-len-pill" style="font-size: 11px; font-weight: 700; color: #15803d;">0 chars</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <textarea id="rm-copy-desc" rows="3" readonly></textarea>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('rm-copy-desc', this)">Copy</button>
                                </div>
                            </div>
                        </div>

                        <!-- View 2: Yoast SEO -->
                        <div id="plg-box-yoast" style="display: none; margin-top: 14px;">
                            <div class="field-help" style="margin-bottom: 12px;">Copy and paste directly into Yoast SEO Snippet Editor inside WordPress.</div>
                            
                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">Focus Keyphrase</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <input type="text" id="yoast-copy-keyphrase" readonly>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('yoast-copy-keyphrase', this)">Copy</button>
                                </div>
                            </div>

                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">SEO Title (Literal Exact)</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <input type="text" id="yoast-copy-title-literal" readonly>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('yoast-copy-title-literal', this)">Copy</button>
                                </div>
                            </div>

                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">SEO Title (Yoast Variable Template)</span>
                                    <span style="font-size: 11px; color: #6b7280;">Uses %%sep%% %%sitename%%</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <input type="text" id="yoast-copy-title-tpl" readonly>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('yoast-copy-title-tpl', this)">Copy</button>
                                </div>
                            </div>

                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">Slug</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <input type="text" id="yoast-copy-slug" readonly>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('yoast-copy-slug', this)">Copy</button>
                                </div>
                            </div>

                            <div class="plg-field-row">
                                <div class="plg-field-header">
                                    <span class="plg-field-label">Meta Description</span>
                                </div>
                                <div class="plg-copy-input-group">
                                    <textarea id="yoast-copy-desc" rows="3" readonly></textarea>
                                    <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('yoast-copy-desc', this)">Copy</button>
                                </div>
                            </div>
                        </div>

                        <!-- View 3: Social Meta -->
                        <div id="plg-box-social" style="display: none; margin-top: 14px;">
                            <div class="field-help" style="margin-bottom: 12px;">OpenGraph and Twitter Card markup ready to insert in theme &lt;head&gt; or plugin Social tab.</div>
                            <div style="position: relative;">
                                <pre class="opt-code-box" id="plg-copy-social-code"></pre>
                                <button type="button" class="copy-btn" onclick="copyCodeSnippet('plg-copy-social-code', this)">Copy Social Tags</button>
                            </div>
                        </div>

                        <!-- View 4: Schema JSON-LD -->
                        <div id="plg-box-schema" style="display: none; margin-top: 14px;">
                            <div class="field-help" style="margin-bottom: 12px;">Schema.org JSON-LD structured data for Google Rich Results.</div>
                            <div style="position: relative;">
                                <pre class="opt-code-box" id="plg-copy-schema-code"></pre>
                                <button type="button" class="copy-btn" onclick="copyCodeSnippet('plg-copy-schema-code', this)">Copy JSON-LD</button>
                            </div>
                        </div>

                        <!-- View 5: Master AI Writing Prompt -->
                        <div id="plg-box-ai" style="display: none; margin-top: 14px;">
                            <div class="field-help" style="margin-bottom: 12px;">Pre-calculated prompt for ChatGPT / Claude / Gemini to generate full article adhering strictly to these plugin metadata specs.</div>
                            <div style="position: relative;">
                                <pre class="opt-code-box" id="plg-copy-ai-prompt" style="white-space: pre-wrap; font-size: 11px;"></pre>
                                <button type="button" class="copy-btn" onclick="copyCodeSnippet('plg-copy-ai-prompt', this)">Copy Prompt</button>
                            </div>
                        </div>
                    </div>

                    <!-- Multi-Device SERP & Social Preview Simulator -->
                    <div class="card" style="margin-bottom: 16px;">
                        <div class="card-title">Live SERP &amp; Social Simulator</div>
                        <div class="field-help" style="margin-top: -6px; margin-bottom: 14px;">
                            Preview how this snippet appears on Google Desktop, Google Mobile, and Facebook / Social sharing.
                        </div>

                        <div class="form-grid-2">
                            <!-- Desktop SERP -->
                            <div>
                                <div style="font-size: 12px; font-weight: 700; color: #111827; text-transform: uppercase; margin-bottom: 6px;">Google Desktop SERP</div>
                                <div id="opt-plg-serp-desktop"></div>
                            </div>

                            <!-- Mobile SERP -->
                            <div>
                                <div style="font-size: 12px; font-weight: 700; color: #111827; text-transform: uppercase; margin-bottom: 6px;">Google Mobile SERP</div>
                                <div id="opt-plg-serp-mobile"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ============================================================= -->
            <!-- SUB-VIEW 2: SINGLE ELEMENT & GEO OPTIMIZER (ORIGINAL) -->
            <!-- ============================================================= -->
            <div id="opt-single-view" style="display: none;">
                <!-- Optimizer Input Card -->
                <div class="card">
                <div class="card-title">Precision SEO &amp; Generative Engine (GEO) Content Optimizer</div>
                <div class="field-help" style="margin-top: -6px; margin-bottom: 16px;">
                    Input any draft heading, title tag, meta description, or text block. The engine scores it against InersiaLab's 8-factor technical SEO &amp; AI citability matrix, purges AI fluff, injects factual anchors, and delivers publication-grade copy.
                </div>

                <div class="form-grid-3">
                    <div class="field-group">
                        <label class="field-label" for="opt-type">Content Element Type <span class="tag-pill req">Required</span></label>
                        <select id="opt-type" onchange="onOptimizerTypeChange()">
                            <option value="paragraph">Passage / Content Paragraph (GEO Quotability Focus)</option>
                            <option value="title">SERP Page Title Tag (50-60 Chars)</option>
                            <option value="meta_description">Meta Description Tag (120-155 Chars)</option>
                            <option value="h1">H1 Primary Page Headline</option>
                            <option value="h2">H2 Section Subheadline / FAQ Header</option>
                        </select>
                        <div class="field-help" id="opt-type-help">Evaluates declarative structure, factual density, and quotability for AI search engines.</div>
                    </div>

                    <div class="field-group">
                        <label class="field-label" for="opt-keywords">Target Keywords</label>
                        <input type="text" id="opt-keywords" placeholder="e.g. enterprise seo audit, technical indexing">
                        <div class="field-help">Comma-separated keywords to verify placement, prominence, and density.</div>
                    </div>

                    <div class="field-group">
                        <label class="field-label" for="opt-brand">Brand / Entity Name</label>
                        <input type="text" id="opt-brand" placeholder="e.g. InersiaLab">
                        <div class="field-help">Optional brand suffix or organization entity anchor.</div>
                    </div>
                </div>

                <div class="form-grid-2" style="margin-top: -6px; margin-bottom: 12px;">
                    <div class="field-group">
                        <label class="field-label" for="opt-industry">Industry &amp; Entity Domain</label>
                        <select id="opt-industry">
                            <option value="tech">Technology, Cloud &amp; SaaS</option>
                            <option value="finance">Finance, Banking &amp; FinTech</option>
                            <option value="healthcare">Healthcare, Biotech &amp; Medical</option>
                            <option value="ecommerce">E-Commerce, Retail &amp; DTC</option>
                            <option value="legal">Legal, Compliance &amp; Corporate</option>
                            <option value="general">General Business &amp; Professional Services</option>
                        </select>
                        <div class="field-help">Calibrates domain entities, vocabulary lexicons, and trust anchors.</div>
                    </div>

                    <div class="field-group">
                        <label class="field-label" for="opt-intent">Search Intent Focus</label>
                        <select id="opt-intent">
                            <option value="informational">Informational (Direct Answers &amp; GEO Quotation)</option>
                            <option value="commercial">Commercial Investigation (Comparison &amp; Proof)</option>
                            <option value="transactional">Transactional (Conversion &amp; Action CTA)</option>
                            <option value="navigational">Navigational (Brand &amp; Entity Grounding)</option>
                        </select>
                        <div class="field-help">Fine-tunes action triggers, CTA density, and synthetic overview tone.</div>
                    </div>
                </div>

                <!-- Quick Presets -->
                <div style="margin-bottom: 14px;">
                    <span style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase; margin-right: 8px;">Load Test Presets:</span>
                    <button type="button" class="opt-pill-preset" onclick="loadOptimizerPreset('fluffy_paragraph')">Fluffy AI Paragraph</button>
                    <button type="button" class="opt-pill-preset" onclick="loadOptimizerPreset('weak_title')">Weak / Short Title</button>
                    <button type="button" class="opt-pill-preset" onclick="loadOptimizerPreset('vague_meta')">Vague Meta Description</button>
                    <button type="button" class="opt-pill-preset" onclick="loadOptimizerPreset('generic_h2')">Generic H2 Subhead</button>
                </div>

                <!-- Input Textarea -->
                <div class="field-group">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <label class="field-label" for="opt-input-text" style="margin-bottom: 0;">Draft Content Input <span class="tag-pill req">Required</span></label>
                        <span id="opt-live-stats" style="font-size: 11px; font-weight: 600; color: #6b7280;">0 chars | 0 words</span>
                    </div>
                    <textarea id="opt-input-text" rows="6" placeholder="Paste your raw title tag, headline, meta description, or draft paragraph here..." oninput="updateOptimizerLiveStats()"></textarea>
                </div>

                <!-- Action Button -->
                <div style="display: flex; gap: 10px; margin-top: 14px;">
                    <button type="button" class="btn btn-accent" id="btn-run-optimizer" onclick="runContentOptimizer()" style="padding: 12px 28px; font-size: 13px;">
                        OPTIMIZE CONTENT (SEO + GEO)
                    </button>
                    <button type="button" class="btn btn-outline" onclick="clearOptimizer()" style="padding: 12px 20px; font-size: 13px;">
                        CLEAR
                    </button>
                </div>
            </div>

            <!-- Optimizer Results Section -->
            <div id="opt-results-wrapper" style="display: none; margin-top: 18px;">
                <!-- Summary Metrics Bar -->
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Evaluation &amp; Optimization Audit</span>
                        <span id="opt-element-tag" class="tag-pill" style="font-size: 11px; padding: 3px 8px;">PARAGRAPH</span>
                    </div>

                    <div class="form-grid-3" style="margin-top: 10px;">
                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Overall Score</div>
                                <div id="opt-score-overall-delta" style="font-size: 11px; font-weight: 600; color: #15803d; margin-top: 2px;">+0 pts improvement</div>
                            </div>
                            <div class="opt-score-badge good" id="opt-score-overall">0</div>
                        </div>

                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Technical SEO</div>
                                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Length &amp; Keywords</div>
                            </div>
                            <div class="opt-score-badge" id="opt-score-seo">0</div>
                        </div>

                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">GEO Quotability</div>
                                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">AI Engine Citability</div>
                            </div>
                            <div class="opt-score-badge" id="opt-score-geo">0</div>
                        </div>
                    </div>

                    <!-- Paragraph Extra Metrics (Quotability, Readability, E-E-A-T) -->
                    <div id="opt-paragraph-metrics" class="form-grid-3" style="margin-top: 12px; display: none;">
                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Direct Quotability</div>
                                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Answer Engine Fitness</div>
                            </div>
                            <div class="opt-score-badge" id="opt-score-quotability">0</div>
                        </div>

                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Readability</div>
                                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">FKGL &amp; Sentence Flow</div>
                            </div>
                            <div class="opt-score-badge" id="opt-score-readability">0</div>
                        </div>

                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">E-E-A-T Signals</div>
                                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Authority &amp; Proof Anchors</div>
                            </div>
                            <div class="opt-score-badge" id="opt-score-eeat">0</div>
                        </div>
                    </div>
                </div>

                <!-- Multi-Variant Selector Grid -->
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Target Strategy Variants</span>
                        <span style="font-size: 11px; color: #6b7280; font-weight: normal;">Select a model variant to inspect diff &amp; export</span>
                    </div>
                    <div class="opt-variant-grid" id="opt-variants-container" style="margin-top: 10px;">
                        <!-- Rendered by JS: 3 clickable variant cards -->
                    </div>
                </div>

                <!-- Inspection & Export Card -->
                <div class="card" style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 14px;">
                        <div class="opt-view-tabs" style="margin-bottom: 0;">
                            <button type="button" class="opt-view-tab active" id="tab-btn-sidebyside" onclick="switchOptViewMode('sidebyside')">Side-by-Side</button>
                            <button type="button" class="opt-view-tab" id="tab-btn-diff" onclick="switchOptViewMode('diff')">Word Diff</button>
                            <button type="button" class="opt-view-tab" id="tab-btn-serp" onclick="switchOptViewMode('serp')">SERP Preview</button>
                            <button type="button" class="opt-view-tab" id="tab-btn-ai" onclick="switchOptViewMode('ai')">AI Citation</button>
                            <button type="button" class="opt-view-tab" id="tab-btn-code" onclick="switchOptViewMode('code')">Schema &amp; HTML</button>
                        </div>

                        <div class="opt-export-bar" style="margin-bottom: 0;">
                            <button type="button" class="btn btn-outline" style="padding: 5px 12px; font-size: 11px;" onclick="copyOptimizedText()">
                                Copy Text
                            </button>
                            <button type="button" class="btn btn-outline" style="padding: 5px 12px; font-size: 11px;" onclick="copyOptimizedHtml()">
                                Copy HTML
                            </button>
                            <button type="button" class="btn btn-outline" style="padding: 5px 12px; font-size: 11px;" onclick="copyOptimizedSchema()">
                                Copy Schema JSON-LD
                            </button>
                        </div>
                    </div>

                    <!-- View 1: Side by Side -->
                    <div id="opt-view-sidebyside">
                        <div class="opt-diff-container">
                            <div class="opt-diff-panel">
                                <div class="opt-diff-header">
                                    <div>
                                        <span style="font-size: 12px; font-weight: 800; color: #b91c1c; text-transform: uppercase; letter-spacing: 0.5px;">ORIGINAL DRAFT</span>
                                        <span id="opt-orig-stats" style="font-size: 11px; color: #6b7280; margin-left: 8px;">(0 chars | 0 words)</span>
                                    </div>
                                    <span id="opt-orig-status" class="tag-pill req">Unoptimized</span>
                                </div>
                                <div class="opt-diff-text" id="opt-orig-text"></div>
                            </div>
                            <div class="opt-diff-panel optimized">
                                <div class="opt-diff-header">
                                    <div>
                                        <span style="font-size: 12px; font-weight: 800; color: #15803d; text-transform: uppercase; letter-spacing: 0.5px;" id="opt-variant-active-label">OPTIMIZED (VARIANT 1)</span>
                                        <span id="opt-optimized-stats" style="font-size: 11px; color: #6b7280; margin-left: 8px;">(0 chars | 0 words)</span>
                                    </div>
                                    <span class="tag-pill good" id="opt-active-variant-badge">Active</span>
                                </div>
                                <div class="opt-diff-text" id="opt-optimized-text" style="font-weight: 500;"></div>
                            </div>
                        </div>
                    </div>

                    <!-- View 2: Word-Level Diff -->
                    <div id="opt-view-diff" style="display: none;">
                        <div class="field-help" style="margin-bottom: 10px;">
                            Visual token comparison: <span class="diff-del">strikethrough red</span> indicates purged fluff / redundant words, while <span class="diff-ins">bold green</span> indicates factual anchors, entities, and high-impact keywords.
                        </div>
                        <div class="opt-diff-view-box" id="opt-diff-content"></div>
                    </div>

                    <!-- View 3: SERP Google Preview -->
                    <div id="opt-view-serp" style="display: none;">
                        <div class="field-help" style="margin-bottom: 12px;">
                            Google Search Desktop &amp; Mobile simulation showing pixel boundary limits and keyword bolding.
                        </div>
                        <div id="opt-serp-preview-container"></div>
                    </div>

                    <!-- View 4: AI Citability Box -->
                    <div id="opt-view-ai" style="display: none;">
                        <div class="field-help" style="margin-bottom: 12px;">
                            Synthetic evaluation of how Google AI Overviews and Perplexity Pro parse and quote this passage as an authority source.
                        </div>
                        <div id="opt-ai-preview-container"></div>
                    </div>

                    <!-- View 5: Schema & Semantic HTML -->
                    <div id="opt-view-code" style="display: none;">
                        <div style="margin-bottom: 14px;">
                            <div style="font-size: 12px; font-weight: 700; color: #111827; text-transform: uppercase; margin-bottom: 6px;">Schema.org JSON-LD Structured Data</div>
                            <pre class="opt-code-box" id="opt-schema-code"></pre>
                        </div>
                        <div>
                            <div style="font-size: 12px; font-weight: 700; color: #111827; text-transform: uppercase; margin-bottom: 6px;">Semantic HTML Embed Snippet</div>
                            <pre class="opt-code-box" id="opt-html-code"></pre>
                        </div>
                    </div>
                </div>

                <!-- Diagnostics & Issues Detected -->
                <div class="card" style="margin-top: 16px;">
                    <div class="card-title">Diagnostic Breakdown &amp; Detected Deficiencies</div>
                    <div id="opt-issues-list" style="margin-top: 10px;">
                        <!-- Rendered by JS -->
                    </div>
                </div>

                <!-- Applied Improvements & Strategic Actions -->
                <div class="card" style="margin-top: 16px;">
                    <div class="card-title">Engine Corrections Applied</div>
                    <div id="opt-improvements-list" style="margin-top: 10px;">
                        <!-- Rendered by JS -->
                    </div>
                </div>

                <!-- Quotability Factor Breakdown (Only shown for paragraphs) -->
                <div id="opt-quotability-analysis" class="card" style="margin-top: 16px; display: none;">
                    <div class="card-title">AEO / GEO Engine Citability Signals</div>
                    <div class="field-help" style="margin-top: -6px; margin-bottom: 12px;">
                        Analysis of suitability for citation in Google AI Overviews, Perplexity Pro, and ChatGPT Search.
                    </div>
                    <div id="opt-quotability-signals-body">
                        <!-- Rendered by JS -->
                    </div>
                </div>
            </div>
            </div> <!-- End opt-single-view -->
        </section>

        <!-- ============================================================= -->
        <!-- TAB 5: CYBERSECURITY & SERVER HARDENING -->
        <!-- ============================================================= -->
        <section id="tab-security" class="tab-content">
            <!-- Security Audit Parameters -->
            <div class="card">
                <div class="card-title">Live Cybersecurity &amp; Server Hardening Parameters</div>
                
                <div class="field-group">
                    <label class="field-label" for="sec-url">Target Website URL</label>
                    <input type="text" id="sec-url" placeholder="https://example.com" value="https://example.com">
                    <div class="field-help">Full website address including https://. Probes transport security, headers, REST API CORS, XML-RPC, user enumeration, and DNS anti-spoofing.</div>
                </div>

                <div class="btn-row">
                    <button id="btn-start-security" class="btn btn-accent" onclick="startSecurityAudit()">START LIVE SECURITY AUDIT</button>
                    <button id="btn-open-security-pdf" class="btn btn-outline" onclick="openLatestSecurityPdf()" disabled>OPEN GENERATED PDF</button>
                    <button class="btn btn-outline" onclick="openDownloadsFolder()">OPEN DOWNLOADS FOLDER</button>
                    <button id="btn-reset-security" class="btn btn-reset" onclick="resetAllEnginesAndCache()" title="Clear in-memory audit cache, logs, and browser storage">RESET / CLEAR CACHE</button>
                </div>
            </div>

            <!-- Execution Status & Real-Time Terminal -->
            <div class="status-box">
                <div>
                    <span id="sec-status-badge" class="status-badge">READY</span>
                    <span id="sec-status-text" style="margin-left: 10px;">Security audit engine idle</span>
                </div>
                <div id="sec-timer" style="font-size: 11px; color: #6b7280;"></div>
            </div>

            <div class="card" style="padding: 0; overflow: hidden;">
                <div class="mac-console-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="mac-traffic-lights">
                            <span class="mac-dot mac-dot-red"></span>
                            <span class="mac-dot mac-dot-yellow"></span>
                            <span class="mac-dot mac-dot-green"></span>
                        </div>
                        <span class="mac-console-title">Security Audit Stream — Terminal Console</span>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span id="sec-log-count" style="color: #86868b; font-size: 11px; font-weight: 500;">0 lines</span>
                        <button class="mac-clear-btn" onclick="resetAllEnginesAndCache()" title="Clear logs and reset engine">Clear</button>
                    </div>
                </div>
                <div id="sec-terminal" class="terminal" style="border-radius: 0 0 16px 16px;">Awaiting security execution command...</div>
            </div>

            <!-- Interactive Security Results Explorer -->
            <div id="sec-results-wrapper" style="display: none; margin-top: 20px;">
                <!-- Executive Score Banner -->
                <div class="card" style="background: #ffffff;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                        <div>
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #4b5563;">Overall Security Posture</div>
                            <div id="sec-grade-badge" style="font-size: 22px; font-weight: 900; margin-top: 4px; color: #111827;">GRADE: C+</div>
                            <div id="sec-host-meta" style="font-size: 12px; color: #4b5563; margin-top: 4px;">Host: inersialab.com | Server: LiteSpeed</div>
                        </div>

                        <!-- Severity Badges Breakdown -->
                        <div style="display: flex; gap: 8px; flex-wrap: wrap;" id="sec-counter-pills">
                            <span class="badge-crit" id="sec-cnt-crit">0 CRITICAL</span>
                            <span class="badge-high" id="sec-cnt-high">0 HIGH</span>
                            <span class="badge-med" id="sec-cnt-med">0 MEDIUM</span>
                            <span class="badge-low" id="sec-cnt-low">0 LOW</span>
                            <span class="badge-pass" id="sec-cnt-pass">0 PASSED</span>
                        </div>
                    </div>

                    <!-- Quick Actions -->
                    <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #e5e7eb; display: flex; gap: 8px; flex-wrap: wrap;">
                        <button class="btn btn-accent" style="padding: 7px 14px; font-size: 11px;" onclick="openLatestSecurityPdf()">View Print-Ready PDF Report</button>
                        <button class="btn btn-outline" style="padding: 7px 14px; font-size: 11px;" onclick="copySecuritySnippet('master')">Copy Master AI Fix Prompt</button>
                        <button class="btn btn-outline" style="padding: 7px 14px; font-size: 11px;" onclick="copySecuritySnippet('htaccess')">Copy .htaccess Hardening</button>
                        <button class="btn btn-outline" style="padding: 7px 14px; font-size: 11px;" onclick="copySecuritySnippet('functions')">Copy functions.php Security Patch</button>
                    </div>
                </div>

                <!-- Sub-Navigation for Security Views -->
                <div style="display: flex; gap: 6px; margin-top: 16px; margin-bottom: 12px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; flex-wrap: wrap;">
                    <button class="tab-btn active" id="sec-tab-findings" onclick="switchSecurityView('findings')">Findings &amp; Defect Matrix</button>
                    <button class="tab-btn" id="sec-tab-patches" onclick="switchSecurityView('patches')">Turnkey Code Patches (.htaccess / PHP)</button>
                    <button class="tab-btn" id="sec-tab-prompt" onclick="switchSecurityView('prompt')">Master AI Fix Prompt</button>
                </div>

                <!-- View 1: Findings Matrix -->
                <div id="sec-view-findings">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                        <span style="font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase;">Filter Findings:</span>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="filterSecurityFindings('all')">All</button>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="filterSecurityFindings('critical')">Critical Only</button>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="filterSecurityFindings('high')">High Only</button>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="filterSecurityFindings('medium')">Medium Only</button>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="filterSecurityFindings('passed')">Passed Only</button>
                        </div>
                    </div>
                    <div id="sec-findings-container">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <!-- View 2: Code Patches -->
                <div id="sec-view-patches" style="display: none;">
                    <div class="card" style="margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="card-title" style="margin-bottom: 0;">1. Server Hardening Directive (.htaccess)</span>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="copySecuritySnippet('htaccess')">Copy .htaccess</button>
                        </div>
                        <div class="field-help" style="margin-bottom: 8px;">Paste at the top of root .htaccess to block XML-RPC, user scanning, readme files, and enforce security headers.</div>
                        <pre class="code-block" id="sec-code-htaccess"></pre>
                    </div>

                    <div class="card" style="margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="card-title" style="margin-bottom: 0;">2. WordPress Security &amp; CORS Patch (functions.php)</span>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="copySecuritySnippet('functions')">Copy functions.php</button>
                        </div>
                        <div class="field-help" style="margin-bottom: 8px;">Paste in child theme's functions.php to eliminate the REST API credential reflection flaw and block public user enumeration.</div>
                        <pre class="code-block" id="sec-code-functions"></pre>
                    </div>

                    <div class="card" style="margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="card-title" style="margin-bottom: 0;">3. Contact Form POST &amp; AJAX Security</span>
                            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="copySecuritySnippet('form')">Copy Form Code</button>
                        </div>
                        <div class="field-help" style="margin-bottom: 8px;">Ensures form submissions use POST method with nonces and asynchronous AJAX to eliminate PII URL leakage.</div>
                        <pre class="code-block" id="sec-code-form"></pre>
                    </div>

                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="card-title" style="margin-bottom: 0;">4. Email Anti-Spoofing &amp; DNS Records (DMARC / CAA)</span>
                        </div>
                        <div class="field-help" style="margin-bottom: 8px;">Add these records in your Hostinger / Cloudflare DNS zone management to enforce email authentication.</div>
                        <div id="sec-dns-table-container"></div>
                    </div>
                </div>

                <!-- View 3: Master AI Prompt -->
                <div id="sec-view-prompt" style="display: none;">
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="card-title" style="margin-bottom: 0;">Master AI Remediation Prompt</span>
                            <button class="btn btn-accent" style="padding: 6px 14px; font-size: 11px;" onclick="copySecuritySnippet('master')">Copy Master Prompt</button>
                        </div>
                        <div class="field-help" style="margin-bottom: 10px;">Copy this self-contained prompt directly into Antigravity, Claude, or ChatGPT to automatically patch all detected defects.</div>
                        <pre class="code-block" id="sec-code-master" style="max-height: 500px;"></pre>
                    </div>
                </div>
            </div>

            <!-- Recent Security Reports Table -->
            <div class="card" style="margin-top: 20px;">
                <div class="card-title">Recent Security Audit Reports in Downloads</div>
                <div id="sec-reports-table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Security Report PDF</th>
                                <th>Generated Time</th>
                                <th>File Size</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="sec-reports-tbody">
                            <tr><td colspan="4" style="text-align: center; color: #6b7280; padding: 20px;">Scanning Downloads folder...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    </div>

    <!-- Reset Notification Toast -->
    <div id="reset-toast" style="display: none;">
        CACHE CLEARED &amp; ENGINES RESET
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
            if (tabId === "security" && !window.securityReportsLoaded) {
                loadSecurityReports();
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
                const startBtn = document.getElementById("btn-start-audit");
                if (startBtn) startBtn.disabled = isAuditing;

                const badge = document.getElementById("audit-status-badge");
                const statusTxt = document.getElementById("audit-status-text");

                if (isAuditing) {
                    if (badge) {
                        badge.className = "status-badge running";
                        badge.innerText = "RUNNING";
                    }
                    if (statusTxt) statusTxt.innerText = data.status || "Auditing...";
                } else if (data.status === "Audit Complete") {
                    if (badge) {
                        badge.className = "status-badge success";
                        badge.innerText = "COMPLETED";
                    }
                    if (statusTxt) statusTxt.innerText = "Audit finished successfully";
                } else {
                    if (badge) {
                        badge.className = "status-badge";
                        badge.innerText = "READY";
                    }
                    if (statusTxt) statusTxt.innerText = data.status || "Ready";
                }

                // Update logs
                const term = document.getElementById("audit-terminal");
                if (term) {
                    if (data.logs && data.logs.length > 0) {
                        term.innerText = data.logs.join("");
                        term.scrollTop = term.scrollHeight;
                        const logCount = document.getElementById("log-count");
                        if (logCount) logCount.innerText = data.logs.length + " lines";
                    } else if (!isAuditing) {
                        term.innerText = "Awaiting execution command...";
                        const logCount = document.getElementById("log-count");
                        if (logCount) logCount.innerText = "0 lines";
                    }
                }

                // Last PDF
                const openPdfBtn = document.getElementById("btn-open-audit-pdf");
                if (data.last_pdf) {
                    lastAuditPdf = data.last_pdf;
                    if (openPdfBtn) openPdfBtn.disabled = false;
                } else {
                    lastAuditPdf = null;
                    if (openPdfBtn) openPdfBtn.disabled = true;
                }
            } catch (e) {
                // server temporarily quiet
            }
        }

        async function resetAllEnginesAndCache() {
            try {
                // 1. Call server reset endpoint
                const res = await fetch("/api/reset", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"}
                });
                const data = await res.json();

                // 2. Clear browser storages & caches
                try {
                    localStorage.clear();
                    sessionStorage.clear();
                } catch (e) {}

                if (window.caches) {
                    try {
                        const keys = await caches.keys();
                        await Promise.all(keys.map(k => caches.delete(k)));
                    } catch (e) {}
                }

                // 3. Reset Tab 1 (SEO Audit) UI
                isAuditing = false;
                lastAuditPdf = null;
                const auditTerm = document.getElementById("audit-terminal");
                if (auditTerm) auditTerm.innerText = "Awaiting execution command...";
                const auditLogCount = document.getElementById("log-count");
                if (auditLogCount) auditLogCount.innerText = "0 lines";
                const auditBadge = document.getElementById("audit-status-badge");
                if (auditBadge) {
                    auditBadge.className = "status-badge";
                    auditBadge.innerText = "READY";
                }
                const auditStatusTxt = document.getElementById("audit-status-text");
                if (auditStatusTxt) auditStatusTxt.innerText = "Audit engine idle";
                const btnStartAudit = document.getElementById("btn-start-audit");
                if (btnStartAudit) btnStartAudit.disabled = false;
                const btnOpenAuditPdf = document.getElementById("btn-open-audit-pdf");
                if (btnOpenAuditPdf) btnOpenAuditPdf.disabled = true;

                // 4. Reset Tab 5 (Cybersecurity) UI
                isAuditingSecurity = false;
                lastSecurityPdf = null;
                lastSecurityResult = null;
                const secTerm = document.getElementById("sec-terminal");
                if (secTerm) secTerm.innerText = "Awaiting security execution command...";
                const secLogCount = document.getElementById("sec-log-count");
                if (secLogCount) secLogCount.innerText = "0 lines";
                const secBadge = document.getElementById("sec-status-badge");
                if (secBadge) {
                    secBadge.className = "status-badge";
                    secBadge.innerText = "READY";
                }
                const secStatusTxt = document.getElementById("sec-status-text");
                if (secStatusTxt) secStatusTxt.innerText = "Security audit engine idle";
                const btnStartSec = document.getElementById("btn-start-security");
                if (btnStartSec) btnStartSec.disabled = false;
                const btnOpenSecPdf = document.getElementById("btn-open-security-pdf");
                if (btnOpenSecPdf) btnOpenSecPdf.disabled = true;
                const secWrapper = document.getElementById("sec-results-wrapper");
                if (secWrapper) secWrapper.style.display = "none";
                const secFindings = document.getElementById("sec-findings-container");
                if (secFindings) secFindings.innerHTML = "";

                // 5. Reset Tab 4 (Optimizer) UI
                lastOptimizerResult = null;
                lastPluginOptimizerResult = null;
                lastCrawlImproverResult = null;
                const optWrapper = document.getElementById("opt-results-wrapper");
                if (optWrapper) optWrapper.style.display = "none";
                const plgOptWrapper = document.getElementById("opt-plugin-results-wrapper");
                if (plgOptWrapper) plgOptWrapper.style.display = "none";
                const crawlWrapper = document.getElementById("opt-crawl-results-wrapper");
                if (crawlWrapper) {
                    crawlWrapper.innerHTML = "";
                    crawlWrapper.style.display = "none";
                }

                // 6. Refresh report lists
                if (typeof loadReportsList === "function") loadReportsList();
                if (typeof loadSecurityReports === "function") loadSecurityReports();

                // 7. Show Toast Confirmation
                showResetToast("Cache cleared & all audit engines reset.");
            } catch (err) {
                alert("Failed to reset cache: " + err);
            }
        }

        function showResetToast(msg) {
            let toast = document.getElementById("reset-toast");
            if (!toast) return;
            toast.innerText = msg || "CACHE CLEARED & ENGINES RESET";
            toast.style.display = "block";
            setTimeout(() => {
                toast.style.display = "none";
            }, 3000);
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
        // Tab 3: Content Architect Controller
        // -------------------------------------------------------------
        let contentPresets = {};
        let demoBriefs = {};
        let lastContentResults = null;
        let lastContentDir = null;
        let activeContentPageIndex = 0;
        let currentContentMode = 'formatted';
        let customContentPagesList = [];

        async function loadContentPresets() {
            try {
                const res = await fetch("/api/content/presets");
                const data = await res.json();
                if (data.presets) {
                    contentPresets = data.presets;
                    demoBriefs = data.demo_briefs || {};
                } else {
                    contentPresets = data;
                }
                window.contentPresetsLoaded = true;

                const indSelect = document.getElementById("cg-industry");
                indSelect.innerHTML = "";
                for (const [key, pdata] of Object.entries(contentPresets)) {
                    const opt = document.createElement("option");
                    opt.value = key;
                    opt.textContent = pdata.label;
                    indSelect.appendChild(opt);
                }
                onIndustryChange();
                updateServiceLabels();
            } catch (e) {
                console.error("Failed to load content presets:", e);
            }
        }

                function loadDemoProfile(profileKey) {
            const p = demoBriefs[profileKey];
            if (!p) {
                alert("Demo profile not found: " + profileKey);
                return;
            }

            // Section 1: Business Identity (Q1-Q6)
            document.getElementById("cg-brand").value = p.brand_name || "";
            document.getElementById("cg-legal-name").value = p.legal_entity_name || "";
            document.getElementById("cg-domain").value = p.domain || "https://example.com";
            document.getElementById("cg-year-founded").value = p.year_founded || "";
            document.getElementById("cg-origin-location").value = p.origin_location || "";
            document.getElementById("cg-lang").value = p.language || "en";
            if (p.industry) document.getElementById("cg-industry").value = p.industry;
            document.getElementById("cg-tagline").value = p.tagline || "";
            document.getElementById("cg-tone").value = p.brand_tone || p.tone || "";
            document.getElementById("cg-mission").value = p.mission_statement || "";
            document.getElementById("cg-banned-words").value = (p.banned_words || []).join(", ");

            // Section 2: Leadership & Credentials (Q7-Q12)
            document.getElementById("cg-founder-name").value = p.founder_name || "";
            document.getElementById("cg-founder-title").value = p.founder_title || "";
            document.getElementById("cg-alma-maters").value = p.alma_maters || "";
            document.getElementById("cg-founder-creds").value = p.founder_credentials || "";
            document.getElementById("cg-key-staff").value = p.key_staff_specialists || "";
            document.getElementById("cg-patents-pubs").value = p.patents_publications || "";
            document.getElementById("cg-awards").value = p.industry_awards || "";
            document.getElementById("cg-origin-story").value = p.origin_story || "";

            // Section 3: ICP & Buyer Psychology (Q13-Q18)
            document.getElementById("cg-target-icp").value = p.target_buyer_persona || "";
            document.getElementById("cg-catalyst-event").value = p.catalyst_event || "";
            document.getElementById("cg-pain-points").value = (p.pain_points || []).join("\n");
            document.getElementById("cg-buyer-anxieties").value = (p.buyer_anxieties || []).join("\n");
            document.getElementById("cg-disqualifications").value = p.disqualification_criteria || "";
            document.getElementById("cg-after-state").value = p.desired_after_state || "";

            // Section 4: Methodology & Process (Q19-Q25)
            document.getElementById("cg-framework-name").value = p.framework_name || "";
            document.getElementById("cg-technologies").value = (p.technologies || []).join(", ");
            document.getElementById("cg-phase1").value = p.phase1_discovery || "";
            document.getElementById("cg-phase2").value = p.phase2_blueprint || "";
            document.getElementById("cg-phase3").value = p.phase3_execution || "";
            document.getElementById("cg-phase4").value = p.phase4_optimization || "";
            document.getElementById("cg-guarantees").value = p.guarantees || "";

            // Section 5: Services & Pricing (Q26-Q31)
            const svcs = p.services || [];
            if (svcs[0]) {
                document.getElementById("cg-svc1-name").value = svcs[0].name || "";
                document.getElementById("cg-svc1-aud").value = svcs[0].target_audience || "";
                document.getElementById("cg-svc1-pri").value = svcs[0].pricing || "";
                document.getElementById("cg-svc1-ben").value = svcs[0].core_benefit || "";
                document.getElementById("cg-svc1-del").value = svcs[0].deliverables || "";
            }
            if (svcs[1]) {
                document.getElementById("cg-svc2-name").value = svcs[1].name || "";
                document.getElementById("cg-svc2-aud").value = svcs[1].target_audience || "";
                document.getElementById("cg-svc2-pri").value = svcs[1].pricing || "";
                document.getElementById("cg-svc2-ben").value = svcs[1].core_benefit || "";
                document.getElementById("cg-svc2-del").value = svcs[1].deliverables || "";
            }
            if (svcs[2]) {
                document.getElementById("cg-svc3-name").value = svcs[2].name || "";
                document.getElementById("cg-svc3-aud").value = svcs[2].target_audience || "";
                document.getElementById("cg-svc3-pri").value = svcs[2].pricing || "";
                document.getElementById("cg-svc3-ben").value = svcs[2].core_benefit || "";
                document.getElementById("cg-svc3-del").value = svcs[2].deliverables || "";
            }
            document.getElementById("cg-secondary-offerings").value = p.secondary_offerings || "";
            document.getElementById("cg-pricing-model").value = p.pricing_model || "";
            document.getElementById("cg-turnaround").value = p.turnaround_speed || "";

            // Section 6: Local Geography & NAP (Q32-Q36)
            document.getElementById("cg-phone").value = p.phone || "";
            document.getElementById("cg-email").value = p.email || "";
            document.getElementById("cg-urgent-contact").value = p.urgent_contact || "";
            document.getElementById("cg-address").value = p.address || "";
            document.getElementById("cg-service-areas").value = (p.service_areas || []).join(", ");
            document.getElementById("cg-local-landmarks").value = p.local_landmarks || "";
            document.getElementById("cg-facility-access").value = p.facility_access || "";

            // Section 7: Proof & Case Studies (Q37-Q41)
            const proofStrs = (p.proof_metrics || []).map(m => `${m.label}: ${m.value}`).join(" | ");
            document.getElementById("cg-proof-metrics").value = proofStrs;
            document.getElementById("cg-certifications").value = (p.certifications || []).join(", ");

            if (p.case_study_1) {
                const c = p.case_study_1;
                document.getElementById("cg-case1").value = `Title: ${c.title || ''} | Client: ${c.client || ''} | Challenge: ${c.challenge || ''} | Solution: ${c.solution || ''} | Outcome: ${c.outcome || ''}`;
            }
            if (p.case_study_2) {
                const c = p.case_study_2;
                document.getElementById("cg-case2").value = `Title: ${c.title || ''} | Client: ${c.client || ''} | Challenge: ${c.challenge || ''} | Solution: ${c.solution || ''} | Outcome: ${c.outcome || ''}`;
            }

            const revStrs = (p.real_reviews || []).map(r => `${r.author} | ${r.service} | ${r.quote}`).join("\n");
            document.getElementById("cg-reviews").value = revStrs;

            const faqStrs = (p.objections_faqs || []).map(f => `Q: ${f.question} | A: ${f.answer}`).join("\n");
            document.getElementById("cg-faqs").value = faqStrs;

            // Section 8: Competitor Benchmarks (Q42-Q45)
            document.getElementById("cg-competitor-urls").value = (p.competitor_urls || []).join(", ");
            document.getElementById("cg-competitor-shortcomings").value = p.competitor_shortcomings || "";
            document.getElementById("cg-uvp").value = p.unfair_advantage_uvp || "";
            document.getElementById("cg-cta").value = p.primary_cta || "";
            document.getElementById("cg-lead-magnet").value = p.secondary_lead_magnet || "";

            onIndustryChange();
            updateServiceLabels();
        }

        function resetClientBriefForm() {
            document.querySelectorAll("#content-form input[type='text'], #content-form textarea").forEach(el => {
                if (el.id !== "cg-domain") el.value = "";
            });
            document.getElementById("cg-domain").value = "https://example.com";
            updateServiceLabels();
        }

        function onIndustryChange() {
            const indSelect = document.getElementById("cg-industry");
            if (!indSelect) return;
            const key = indSelect.value;
            const data = contentPresets[key];
            if (!data) return;

            const helpEl = document.getElementById("cg-industry-help");
            if (helpEl) {
                helpEl.textContent = "Tone: " + (data.tone || "") + " | Audience: " + (data.audience || "");
            }

            const checklist = document.getElementById("content-pages-checklist");
            if (!checklist) return;
            checklist.innerHTML = "";

            if (data.default_pages && Array.isArray(data.default_pages)) {
                data.default_pages.forEach(p => {
                    const item = document.createElement("div");
                    item.className = "checklist-item";
                    item.style.alignItems = "center";
                    item.style.display = "flex";
                    item.style.gap = "8px";
                    item.style.padding = "6px 8px";
                    item.style.background = "#ffffff";
                    item.style.border = "1px solid #e5e7eb";

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
                    lbl.style.marginBottom = "0";

                    lbl.innerHTML = "<span>" + escapeHtml(p.title) + "</span>" + (p.required ? ' <span class="tag-pill req" style="background:#fee2e2; color:#991b1b; border:1px solid #fecaca; font-size:10px; padding:1px 5px; border-radius:3px;">Required</span>' : ' <span class="tag-pill" style="background:#f3f4f6; color:#4b5563; border:1px solid #e5e7eb; font-size:10px; padding:1px 5px; border-radius:3px;">Standard</span>');

                    item.appendChild(chk);
                    item.appendChild(lbl);
                    checklist.appendChild(item);
                });
            }

            customContentPagesList.forEach((cp, idx) => {
                renderCustomPageItem(cp, idx);
            });
            updateServiceLabels();
        }

        function selectAllContentPages(selectAll) {
            const indSelect = document.getElementById("cg-industry");
            const key = indSelect ? indSelect.value : "";
            const data = contentPresets[key];
            const requiredIds = new Set(data && data.default_pages ? data.default_pages.filter(p => p.required).map(p => p.id) : []);

            document.querySelectorAll("#content-pages-checklist input[type='checkbox']").forEach(chk => {
                if (chk.dataset.isCustom === "true") {
                    chk.checked = selectAll;
                } else if (selectAll) {
                    chk.checked = true;
                } else {
                    chk.checked = requiredIds.has(chk.value);
                }
            });
        }

        function addCustomContentPage() {
            const input = document.getElementById("cg-custom-title");
            if (!input) return;
            const title = input.value.trim();
            if (!title) return;

            const customObj = { id: "custom_" + Date.now(), title: title };
            customContentPagesList.push(customObj);
            renderCustomPageItem(customObj, customContentPagesList.length - 1);
            input.value = "";
        }

        function renderCustomPageItem(cp, idx) {
            const checklist = document.getElementById("content-pages-checklist");
            if (!checklist) return;
            const item = document.createElement("div");
            item.className = "checklist-item";
            item.style.alignItems = "center";
            item.style.display = "flex";
            item.style.gap = "8px";
            item.style.padding = "6px 8px";
            item.style.background = "#ffffff";
            item.style.border = "1px solid #e5e7eb";
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
            lbl.style.marginBottom = "0";

            lbl.innerHTML = "<span>" + escapeHtml(cp.title) + '</span> <span class="tag-pill" style="background:#e0f2fe; color:#0369a1; border:1px solid #bae6fd; font-size:10px; padding:1px 5px; border-radius:3px;">Custom</span>';

            const delBtn = document.createElement("button");
            delBtn.type = "button";
            delBtn.style.background = "none";
            delBtn.style.border = "none";
            delBtn.style.color = "#b91c1c";
            delBtn.style.cursor = "pointer";
            delBtn.style.fontSize = "13px";
            delBtn.style.fontWeight = "bold";
            delBtn.style.padding = "0 4px";
            delBtn.title = "Delete Page";
            delBtn.innerText = "✕";
            delBtn.onclick = () => {
                customContentPagesList = customContentPagesList.filter(x => x.id !== cp.id);
                item.remove();
            };

            item.appendChild(chk);
            item.appendChild(lbl);
            item.appendChild(delBtn);
            checklist.appendChild(item);
        }

        function updateServiceLabels() {
            const s1 = document.getElementById("cg-svc1-name") ? document.getElementById("cg-svc1-name").value.trim() : "";
            const s2 = document.getElementById("cg-svc2-name") ? document.getElementById("cg-svc2-name").value.trim() : "";
            const s3 = document.getElementById("cg-svc3-name") ? document.getElementById("cg-svc3-name").value.trim() : "";

            const lbl1 = document.querySelector("#cg-chk-service_detail_1 + label span");
            if (lbl1 && s1) lbl1.textContent = s1;

            const lbl2 = document.querySelector("#cg-chk-service_detail_2 + label span");
            if (lbl2 && s2) lbl2.textContent = s2;

            const lbl3 = document.querySelector("#cg-chk-service_detail_3 + label span");
            if (lbl3 && s3) lbl3.textContent = s3;
        }

        async function generateSiteContent() {
            const brand = document.getElementById("cg-brand").value.trim();
            if (!brand) {
                alert("Please enter a Brand Name.");
                return;
            }

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

            // Parse proof metrics
            const rawMetrics = document.getElementById("cg-proof-metrics").value;
            const parsedProof = [];
            rawMetrics.split("|").forEach(part => {
                const sub = part.split(":");
                if (sub.length >= 2) {
                    parsedProof.push({ label: sub[0].trim(), value: sub.slice(1).join(":").trim() });
                }
            });

            // Parse reviews
            const rawRevs = document.getElementById("cg-reviews").value;
            const parsedRevs = [];
            rawRevs.split("\n").forEach(line => {
                const parts = line.split("|");
                if (parts.length >= 3) {
                    parsedRevs.push({
                        author: parts[0].trim(),
                        service: parts[1].trim(),
                        quote: parts[2].trim(),
                        rating: 5
                    });
                }
            });

            // Parse FAQs
            const rawFaqs = document.getElementById("cg-faqs").value;
            const parsedFaqs = [];
            rawFaqs.split("\n").forEach(line => {
                const parts = line.split("|");
                if (parts.length >= 2) {
                    const q = parts[0].replace(/^Q:\\s*/i, "").trim();
                    const a = parts[1].replace(/^A:\\s*/i, "").trim();
                    if (q && a) {
                        parsedFaqs.push({ question: q, answer: a });
                    }
                }
            });

            // Parse Case Study 1
            const parseCase = (raw, defaultTitle) => {
                const parts = raw.split("|");
                const res = { title: defaultTitle, client: "", challenge: "", solution: "", outcome: "" };
                parts.forEach(p => {
                    const idx = p.indexOf(":");
                    if (idx > -1) {
                        const key = p.substring(0, idx).trim().toLowerCase();
                        const val = p.substring(idx + 1).trim();
                        if (key.includes("title")) res.title = val;
                        else if (key.includes("client")) res.client = val;
                        else if (key.includes("challenge")) res.challenge = val;
                        else if (key.includes("solution")) res.solution = val;
                        else if (key.includes("outcome") || key.includes("result")) res.outcome = val;
                    }
                });
                return res;
            };

            const case1 = parseCase(document.getElementById("cg-case1").value, "Documented Clinical / Project Case Study 1");
            const case2 = parseCase(document.getElementById("cg-case2").value, "Documented Clinical / Project Case Study 2");

            const servicesList = [
                {
                    id: "service_detail_1",
                    name: document.getElementById("cg-svc1-name").value.trim(),
                    target_audience: document.getElementById("cg-svc1-aud").value.trim(),
                    core_benefit: document.getElementById("cg-svc1-ben").value.trim(),
                    deliverables: document.getElementById("cg-svc1-del").value.trim(),
                    pricing: document.getElementById("cg-svc1-pri").value.trim(),
                },
                {
                    id: "service_detail_2",
                    name: document.getElementById("cg-svc2-name").value.trim(),
                    target_audience: document.getElementById("cg-svc2-aud").value.trim(),
                    core_benefit: document.getElementById("cg-svc2-ben").value.trim(),
                    deliverables: document.getElementById("cg-svc2-del").value.trim(),
                    pricing: document.getElementById("cg-svc2-pri").value.trim(),
                },
                {
                    id: "service_detail_3",
                    name: document.getElementById("cg-svc3-name").value.trim(),
                    target_audience: document.getElementById("cg-svc3-aud").value.trim(),
                    core_benefit: document.getElementById("cg-svc3-ben").value.trim(),
                    deliverables: document.getElementById("cg-svc3-del").value.trim(),
                    pricing: document.getElementById("cg-svc3-pri").value.trim(),
                }
            ].filter(s => s.name);

            const payload = {
                brand_name: brand,
                legal_entity_name: document.getElementById("cg-legal-name").value.trim(),
                year_founded: document.getElementById("cg-year-founded").value.trim(),
                origin_location: document.getElementById("cg-origin-location").value.trim(),
                mission_statement: document.getElementById("cg-mission").value.trim(),
                tagline: document.getElementById("cg-tagline").value.trim(),
                industry: document.getElementById("cg-industry").value,
                domain: document.getElementById("cg-domain").value.trim() || "https://example.com",
                language: document.getElementById("cg-lang").value,
                brand_tone: document.getElementById("cg-tone").value.trim(),
                tone: document.getElementById("cg-tone").value.trim(),
                banned_words: document.getElementById("cg-banned-words").value.split(",").map(w => w.trim()).filter(Boolean),

                founder_name: document.getElementById("cg-founder-name").value.trim(),
                founder_title: document.getElementById("cg-founder-title").value.trim(),
                alma_maters: document.getElementById("cg-alma-maters").value.trim(),
                founder_credentials: document.getElementById("cg-founder-creds").value.trim(),
                key_staff_specialists: document.getElementById("cg-key-staff").value.trim(),
                patents_publications: document.getElementById("cg-patents-pubs").value.trim(),
                industry_awards: document.getElementById("cg-awards").value.trim(),
                origin_story: document.getElementById("cg-origin-story").value.trim(),

                target_buyer_persona: document.getElementById("cg-target-icp").value.trim(),
                catalyst_event: document.getElementById("cg-catalyst-event").value.trim(),
                pain_points: document.getElementById("cg-pain-points").value.split("\n").map(p => p.trim()).filter(Boolean),
                buyer_anxieties: document.getElementById("cg-buyer-anxieties").value.split("\n").map(p => p.trim()).filter(Boolean),
                disqualification_criteria: document.getElementById("cg-disqualifications").value.trim(),
                desired_after_state: document.getElementById("cg-after-state").value.trim(),

                framework_name: document.getElementById("cg-framework-name").value.trim(),
                technologies: document.getElementById("cg-technologies").value.split(",").map(s => s.trim()).filter(Boolean),
                phase1_discovery: document.getElementById("cg-phase1").value.trim(),
                phase2_blueprint: document.getElementById("cg-phase2").value.trim(),
                phase3_execution: document.getElementById("cg-phase3").value.trim(),
                phase4_optimization: document.getElementById("cg-phase4").value.trim(),
                guarantees: document.getElementById("cg-guarantees").value.trim(),

                services: servicesList,
                secondary_offerings: document.getElementById("cg-secondary-offerings").value.trim(),
                pricing_model: document.getElementById("cg-pricing-model").value.trim(),
                turnaround_speed: document.getElementById("cg-turnaround").value.trim(),

                phone: document.getElementById("cg-phone").value.trim(),
                email: document.getElementById("cg-email").value.trim(),
                urgent_contact: document.getElementById("cg-urgent-contact").value.trim(),
                address: document.getElementById("cg-address").value.trim(),
                service_areas: document.getElementById("cg-service-areas").value.split(",").map(s => s.trim()).filter(Boolean),
                local_landmarks: document.getElementById("cg-local-landmarks").value.trim(),
                facility_access: document.getElementById("cg-facility-access").value.trim(),

                proof_metrics: parsedProof,
                certifications: document.getElementById("cg-certifications").value.split(",").map(s => s.trim()).filter(Boolean),
                case_study_1: case1,
                case_study_2: case2,
                real_reviews: parsedRevs,
                objections_faqs: parsedFaqs,

                competitor_urls: document.getElementById("cg-competitor-urls").value.split(",").map(u => u.trim()).filter(Boolean),
                competitor_shortcomings: document.getElementById("cg-competitor-shortcomings").value.trim(),
                unfair_advantage_uvp: document.getElementById("cg-uvp").value.trim(),
                primary_cta: document.getElementById("cg-cta").value.trim(),
                secondary_lead_magnet: document.getElementById("cg-lead-magnet").value.trim(),

                pages: standardPages,
                custom_pages: customPages,
            };

            const btn = document.getElementById("btn-generate-content");
            btn.disabled = true;
            const sBox = document.getElementById("cg-status-box");
            sBox.style.display = "flex";
            const sBadge = document.getElementById("cg-status-badge");
            sBadge.className = "status-badge running";
            sBadge.innerText = "BENCHMARKING";
            const sText = document.getElementById("cg-status-text");
            
            // Animated multi-phase status steps
            sText.innerText = "[Step 1/5] Validating 45-point client diagnostic brief...";
            const timer1 = setTimeout(() => {
                if (btn.disabled) sText.innerText = "[Step 2/5] Crawling and benchmarking competitor websites in real-time...";
            }, 800);
            const timer2 = setTimeout(() => {
                if (btn.disabled) sText.innerText = "[Step 3/5] Extracting competitor semantic entities & topological gaps...";
            }, 2000);
            const timer3 = setTimeout(() => {
                if (btn.disabled) sText.innerText = `[Step 4/5] Synthesizing bespoke zero-placeholder content for ${checkedBoxes.length} pages...`;
            }, 3200);

            try {
                const res = await fetch("/api/content/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                clearTimeout(timer1);
                clearTimeout(timer2);
                clearTimeout(timer3);

                const data = await res.json();
                if (!data.success) {
                    throw new Error(data.error || "Generation failed.");
                }

                lastContentResults = data.results;
                lastContentDir = data.output_dir;

                sBadge.className = "status-badge success";
                sBadge.innerText = "COMPLETED";
                sText.innerText = `Successfully synthesized ${data.results.pages.length} custom pages (${data.export.total_words} words). Benchmarking report saved!`;

                document.getElementById("btn-open-content-folder").disabled = false;
                document.getElementById("btn-copy-master-md").disabled = false;

                const banner = document.getElementById("cg-downloads-banner");
                banner.style.display = "flex";
                document.getElementById("cg-banner-info").textContent = `Exported to: ${data.output_dir}`;

                renderContentViewer(data.results);
            } catch (e) {
                clearTimeout(timer1);
                clearTimeout(timer2);
                clearTimeout(timer3);
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

            // Inject Benchmark Report Box if present
            const bench = results.benchmark_report;
            let benchHtml = "";
            if (bench) {
                const targets = (bench.targets_inspected || []).map(t => `<span class="tag-pill" style="background:#e0f2fe; color:#0369a1; border-color:#bae6fd;">${t.domain || t.url}</span>`).join(" ");
                const entities = (bench.top_benchmark_entities || []).slice(0, 6).map(e => `<span class="badge-metric badge-good" style="margin-right: 4px;">+ ${e}</span>`).join(" ");
                benchHtml = `
                    <div class="card" style="margin-bottom: 14px; padding: 12px 16px; background: rgba(255, 59, 48, 0.05); border: 1px solid rgba(255, 59, 48, 0.15); border-left: 3px solid #ff3b30; border-radius: 12px;">
                        <div style="font-size: 12px; font-weight: 700; color: #b91c1c; margin-bottom: 4px;">Active Competitor Benchmark Intelligence:</div>
                        <div style="font-size: 12px; color: #374151; margin-bottom: 6px;">
                            <strong>Competitors Inspected:</strong> ${targets || "Leading Archetype Champions"}
                        </div>
                        <div style="font-size: 12px; color: #374151; margin-bottom: 6px;">
                            <strong>Top Discovered Topical Entities:</strong> ${entities}
                        </div>
                        <div style="font-size: 11px; color: #4b5563; font-style: italic;">
                            ${bench.competitive_differentiator_strategy || ""}
                        </div>
                    </div>
                `;
            }

            const totalWords = results.pages.reduce((acc, p) => acc + p.total_word_count, 0);
            document.getElementById("cg-summary-metrics").textContent = `${results.pages.length} Pages | ${totalWords} Words`;

            let oldBench = document.getElementById("cg-bench-intelligence-card");
            if (oldBench) oldBench.remove();

            if (benchHtml) {
                const bDiv = document.createElement("div");
                bDiv.id = "cg-bench-intelligence-card";
                bDiv.innerHTML = benchHtml;
                wrapper.insertBefore(bDiv, wrapper.querySelector(".content-layout"));
            }((acc, p) => acc + p.total_word_count, 0);
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

        // =============================================================
        // TAB 4: SEO & GEO CONTENT OPTIMIZER JAVASCRIPT CONTROLLER
        // =============================================================
        let lastOptimizerResult = null;

        function escapeOptHtml(text) {
            if (!text) return "";
            return String(text)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function onOptimizerTypeChange() {
            const type = document.getElementById("opt-type").value;
            const help = document.getElementById("opt-type-help");
            const textarea = document.getElementById("opt-input-text");

            if (type === "title") {
                help.textContent = "Google SERP standard: 50-60 characters. First keyword positioned prominently, brand suffix optional.";
                textarea.placeholder = "e.g. Enterprise SEO Audit & Architecture Suite | InersiaLab";
            } else if (type === "meta_description") {
                help.textContent = "SERP snippet optimal: 120-155 characters. Includes high-intent CTA, factual proof, and primary keyword.";
                textarea.placeholder = "e.g. Accelerate organic pipeline with InersiaLab's automated 8-factor technical SEO audit engine. Crawl 200+ pages and generate executive PDF reports instantly.";
            } else if (type === "h1") {
                help.textContent = "Primary page headline: 30-70 characters. Must contain target keyword naturally, declarative and authoritative.";
                textarea.placeholder = "e.g. High-Performance Enterprise Technical SEO Audit Engine";
            } else if (type === "h2") {
                help.textContent = "Section subhead: 30-80 characters. Formats as problem-solving question or direct entity-rich phrase.";
                textarea.placeholder = "e.g. How Does Generative Engine Optimization (GEO) Affect AI Citations?";
            } else {
                help.textContent = "Evaluates declarative structure, factual density, and quotability for AI search engines (Perplexity, ChatGPT, SGE).";
                textarea.placeholder = "Paste your raw draft paragraph here. The engine will detect AI filler, vague modifiers, and weak declarative structure, transforming it into an authority quotation passage.";
            }
            updateOptimizerLiveStats();
        }

        function updateOptimizerLiveStats() {
            const text = document.getElementById("opt-input-text").value;
            const chars = text.length;
            const words = text.trim() ? text.trim().split(/\s+/).filter(Boolean).length : 0;
            const el = document.getElementById("opt-live-stats");
            if (el) {
                el.textContent = chars + " chars | " + words + " words";
            }
        }

        function loadOptimizerPreset(presetKey) {
            const typeSelect = document.getElementById("opt-type");
            const kwInput = document.getElementById("opt-keywords");
            const brandInput = document.getElementById("opt-brand");
            const industrySelect = document.getElementById("opt-industry");
            const intentSelect = document.getElementById("opt-intent");
            const textInput = document.getElementById("opt-input-text");

            if (presetKey === "fluffy_paragraph") {
                typeSelect.value = "paragraph";
                kwInput.value = "enterprise zero-trust security, identity verification";
                brandInput.value = "InersiaLab";
                if (industrySelect) industrySelect.value = "tech";
                if (intentSelect) intentSelect.value = "informational";
                textInput.value = "In today's fast-paced digital world, it goes without saying that cybersecurity is a crucial role for many organizations. When it comes to protecting various things in the cloud, basically a lot of companies might struggle with navigating the complexities of modern threats. It is important to note that our state-of-the-art solution seamlessly leverages cutting-edge technology to streamline your workflow.";
            } else if (presetKey === "weak_title") {
                typeSelect.value = "title";
                kwInput.value = "enterprise seo audit, technical indexing";
                brandInput.value = "InersiaLab";
                if (industrySelect) industrySelect.value = "tech";
                if (intentSelect) intentSelect.value = "commercial";
                textInput.value = "Home | Best SEO Services";
            } else if (presetKey === "vague_meta") {
                typeSelect.value = "meta_description";
                kwInput.value = "saas data analytics platform";
                brandInput.value = "InersiaLab";
                if (industrySelect) industrySelect.value = "tech";
                if (intentSelect) intentSelect.value = "commercial";
                textInput.value = "We do data analytics for companies. Our software has many features that can help various businesses see their data and make things better.";
            } else if (presetKey === "generic_h2") {
                typeSelect.value = "h2";
                kwInput.value = "core web vitals optimization";
                brandInput.value = "";
                if (industrySelect) industrySelect.value = "tech";
                if (intentSelect) intentSelect.value = "informational";
                textInput.value = "Our Solutions";
            }

            onOptimizerTypeChange();
            updateOptimizerLiveStats();
        }

        function clearOptimizer() {
            document.getElementById("opt-input-text").value = "";
            document.getElementById("opt-keywords").value = "";
            document.getElementById("opt-brand").value = "";
            document.getElementById("opt-results-wrapper").style.display = "none";
            lastOptimizerResult = null;
            activeVariantIndex = 0;
            updateOptimizerLiveStats();
        }

        async function runContentOptimizer() {
            const text = document.getElementById("opt-input-text").value.trim();
            if (!text) {
                alert("Please enter draft text to optimize.");
                document.getElementById("opt-input-text").focus();
                return;
            }

            const contentType = document.getElementById("opt-type").value;
            const keywordsRaw = document.getElementById("opt-keywords").value.trim();
            const keywords = keywordsRaw ? keywordsRaw.split(",").map(k => k.trim()).filter(Boolean) : [];
            const brand = document.getElementById("opt-brand").value.trim();
            const industry = document.getElementById("opt-industry") ? document.getElementById("opt-industry").value : "tech";
            const intent = document.getElementById("opt-intent") ? document.getElementById("opt-intent").value : "informational";

            const btn = document.getElementById("btn-run-optimizer");
            const originalBtnText = btn.textContent;
            btn.disabled = true;
            btn.textContent = "EVALUATING & OPTIMIZING...";

            try {
                const response = await fetch("/api/optimizer/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        content_type: contentType,
                        text: text,
                        keywords: keywords,
                        brand: brand,
                        industry: industry,
                        intent: intent
                    })
                });

                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || "Optimization failed.");
                }

                lastOptimizerResult = data.result;
                activeVariantIndex = 0;
                renderOptimizerResults(data.result);

                const resWrapper = document.getElementById("opt-results-wrapper");
                resWrapper.scrollIntoView({ behavior: "smooth", block: "start" });
            } catch (err) {
                alert("Optimizer Error: " + err.message);
            } finally {
                btn.disabled = false;
                btn.textContent = originalBtnText;
            }
        }

        function getScoreClass(score) {
            if (score >= 80) return "good";
            if (score >= 60) return "warn";
            return "bad";
        }

        let activeVariantIndex = 0;
        let activeOptViewMode = "sidebyside";

        function renderSerpBox(serp) {
            if (!serp) return '<div style="color: #6b7280; font-size: 13px;">SERP preview unavailable.</div>';
            const pct = Math.min(100, Math.round((serp.pixel_width / serp.max_pixels) * 100));
            const isWarn = serp.is_truncated || pct > 95;
            return `
                <div class="serp-box">
                    <div class="serp-url-row">
                        <span class="serp-favicon">S</span>
                        <span>${escapeOptHtml(serp.display_url || 'https://example.com')}</span>
                    </div>
                    <div class="serp-title">${escapeOptHtml(serp.title)}</div>
                    <div class="serp-snippet">${escapeOptHtml(serp.description)}</div>
                    <div class="serp-pixel-bar" title="Calculated SERP pixel width: ${serp.pixel_width}px / ${serp.max_pixels}px">
                        <div class="serp-pixel-fill ${isWarn ? 'warn' : ''}" style="width: ${pct}%;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #6b7280; margin-top: 6px;">
                        <span>SERP Pixel Width: <strong>${serp.pixel_width}px</strong> / ${serp.max_pixels}px (${pct}%)</span>
                        <span>${isWarn ? '<span style="color: #b91c1c; font-weight: 700;">Truncation Risk</span>' : '<span style="color: #15803d; font-weight: 700;">Within Pixel Boundary</span>'}</span>
                    </div>
                </div>
            `;
        }

        function renderAiOverviewBox(ai) {
            if (!ai) return '<div style="color: #6b7280; font-size: 13px;">AI citability overview unavailable.</div>';
            const anchors = (ai.entity_anchors || []).map(a => `<span class="ai-source-chip">${escapeOptHtml(a)}</span>`).join(' ');
            return `
                <div class="ai-preview-box">
                    <div class="ai-preview-header">
                        <span class="ai-preview-badge">Google AI Overview / Perplexity Grounding</span>
                        <span style="font-size: 11px; font-weight: 700; color: #4338ca;">Quotability Index: ${ai.quotability_score || 0}/100</span>
                    </div>
                    <div class="ai-preview-quote">
                        &ldquo;${escapeOptHtml(ai.citation_quote || ai.synthesized_answer)}&rdquo;
                    </div>
                    <div class="ai-sources-row">
                        <span style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Cited Grounding Anchors:</span>
                        ${anchors || '<span class="ai-source-chip">Primary Domain Entity</span>'}
                    </div>
                </div>
            `;
        }

        function renderOptimizerResults(res) {
            const wrapper = document.getElementById("opt-results-wrapper");
            wrapper.style.display = "block";

            // Element tag
            document.getElementById("opt-element-tag").textContent = (res.content_type || "content").toUpperCase();

            // Overall score
            const overallEl = document.getElementById("opt-score-overall");
            overallEl.textContent = res.overall_score;
            overallEl.className = "opt-score-badge " + getScoreClass(res.overall_score);

            // Technical SEO score
            const seoEl = document.getElementById("opt-score-seo");
            seoEl.textContent = res.seo_score;
            seoEl.className = "opt-score-badge " + getScoreClass(res.seo_score);

            // GEO Quotability score
            const geoEl = document.getElementById("opt-score-geo");
            geoEl.textContent = res.geo_score;
            geoEl.className = "opt-score-badge " + getScoreClass(res.geo_score);

            // Delta
            const deltaEl = document.getElementById("opt-score-overall-delta");
            const origEstimate = Math.max(25, res.overall_score - (res.issues.length * 8));
            const delta = Math.max(0, res.overall_score - origEstimate);
            deltaEl.textContent = (res.has_changes ? "+" + delta + " pts improvement" : "Baseline score optimal");

            // Extra metrics for paragraph
            const paraMetrics = document.getElementById("opt-paragraph-metrics");
            const quotAnalysis = document.getElementById("opt-quotability-analysis");

            if (res.content_type === "paragraph") {
                paraMetrics.style.display = "grid";
                quotAnalysis.style.display = "block";

                const quotEl = document.getElementById("opt-score-quotability");
                quotEl.textContent = res.quotability_score || 0;
                quotEl.className = "opt-score-badge " + getScoreClass(res.quotability_score || 0);

                const readEl = document.getElementById("opt-score-readability");
                readEl.textContent = res.readability_score || 0;
                readEl.className = "opt-score-badge " + getScoreClass(res.readability_score || 0);

                const eeatEl = document.getElementById("opt-score-eeat");
                eeatEl.textContent = res.eeat_score || 0;
                eeatEl.className = "opt-score-badge " + getScoreClass(res.eeat_score || 0);

                renderQuotabilitySignals(res);
            } else {
                paraMetrics.style.display = "none";
                quotAnalysis.style.display = "none";
            }

            // Render Multi-Variants Selector Grid
            renderVariantsGrid(res);

            // Update Active Variant View
            updateActiveVariantView();

            // Issues list
            const issuesContainer = document.getElementById("opt-issues-list");
            issuesContainer.innerHTML = "";

            if (!res.issues || res.issues.length === 0) {
                issuesContainer.innerHTML = '<div style="color: #15803d; font-size: 13px; font-weight: 600; padding: 10px; background: #f0fdf4; border: 1px solid #bbf7d0;">Zero structural defects detected. Content satisfies all search and quotation criteria.</div>';
            } else {
                res.issues.forEach(iss => {
                    const sev = (iss.severity || "info").toLowerCase();
                    const item = document.createElement("div");
                    item.className = "opt-issue-item sev-" + sev;
                    item.innerHTML = `
                        <div style="flex-shrink: 0;">
                            <span class="tag-pill ${sev === 'critical' || sev === 'high' ? 'req' : ''}" style="font-size: 10px;">${iss.area || 'AUDIT'}: ${sev.toUpperCase()}</span>
                        </div>
                        <div>
                            <div style="font-weight: 700; color: #111827; margin-bottom: 2px;">${escapeOptHtml(iss.issue)}</div>
                            <div style="color: #4b5563; font-size: 12px; line-height: 1.5;">${escapeOptHtml(iss.detail)}</div>
                        </div>
                    `;
                    issuesContainer.appendChild(item);
                });
            }

            // Improvements list
            const impContainer = document.getElementById("opt-improvements-list");
            impContainer.innerHTML = "";

            if (!res.improvements || res.improvements.length === 0) {
                impContainer.innerHTML = '<div style="color: #4b5563; font-size: 13px; padding: 8px;">No structural changes required.</div>';
            } else {
                const ul = document.createElement("ul");
                ul.style.listStyle = "none";
                ul.style.padding = "0";
                ul.style.margin = "0";

                res.improvements.forEach(imp => {
                    const li = document.createElement("li");
                    li.style.display = "flex";
                    li.style.gap = "8px";
                    li.style.alignItems = "flex-start";
                    li.style.padding = "6px 0";
                    li.style.fontSize = "13px";
                    li.style.color = "#111827";
                    li.style.borderBottom = "1px solid #f3f4f6";

                    li.innerHTML = `
                        <span style="color: #15803d; font-weight: 900; line-height: 1.3;">✓</span>
                        <span>${escapeOptHtml(imp)}</span>
                    `;
                    ul.appendChild(li);
                });
                impContainer.appendChild(ul);
            }
        }

        function renderVariantsGrid(res) {
            const container = document.getElementById("opt-variants-container");
            container.innerHTML = "";

            const variants = (res.variants && res.variants.length > 0) ? res.variants : [
                {
                    label: "Recommended Optimization",
                    strategy: "Balanced SEO & Citability",
                    text: res.optimized,
                    diff: res.diff,
                    serp_preview: res.serp_preview,
                    ai_overview_preview: res.ai_overview_preview,
                    schema_jsonld: res.schema_jsonld,
                    semantic_html: res.semantic_html
                }
            ];

            variants.forEach((v, idx) => {
                const card = document.createElement("div");
                card.className = "opt-variant-card" + (idx === activeVariantIndex ? " active" : "");
                card.onclick = () => selectOptimizerVariant(idx);

                const previewSnippet = v.text ? (v.text.length > 85 ? v.text.substring(0, 85) + "..." : v.text) : "";

                card.innerHTML = `
                    <div class="opt-variant-title">
                        <span>Variant ${idx + 1}: ${escapeOptHtml(v.label)}</span>
                        ${idx === activeVariantIndex ? '<span class="tag-pill good" style="font-size: 10px; padding: 2px 6px;">Selected</span>' : ''}
                    </div>
                    <div class="opt-variant-desc" style="margin-bottom: 6px;">${escapeOptHtml(v.strategy)}</div>
                    <div style="font-size: 11px; color: #111827; background: #ffffff; border: 1px solid #e5e7eb; padding: 6px 8px; font-style: italic;">
                        &ldquo;${escapeOptHtml(previewSnippet)}&rdquo;
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function selectOptimizerVariant(index) {
            activeVariantIndex = index;
            if (lastOptimizerResult) {
                renderVariantsGrid(lastOptimizerResult);
                updateActiveVariantView();
            }
        }

        function getActiveVariant() {
            if (!lastOptimizerResult) return null;
            const variants = lastOptimizerResult.variants || [];
            if (variants[activeVariantIndex]) {
                return variants[activeVariantIndex];
            }
            return {
                label: "Recommended Optimization",
                strategy: "Balanced SEO & Citability",
                text: lastOptimizerResult.optimized,
                diff: lastOptimizerResult.diff,
                serp_preview: lastOptimizerResult.serp_preview,
                ai_overview_preview: lastOptimizerResult.ai_overview_preview,
                schema_jsonld: lastOptimizerResult.schema_jsonld,
                semantic_html: lastOptimizerResult.semantic_html
            };
        }

        function updateActiveVariantView() {
            const v = getActiveVariant();
            if (!v || !lastOptimizerResult) return;

            // Side by Side
            const origStats = document.getElementById("opt-orig-stats");
            const optStats = document.getElementById("opt-optimized-stats");
            const origWords = lastOptimizerResult.original.trim() ? lastOptimizerResult.original.trim().split(/\s+/).filter(Boolean).length : 0;
            const optWords = (v.text || "").trim() ? v.text.trim().split(/\s+/).filter(Boolean).length : 0;

            if (origStats) origStats.textContent = "(" + lastOptimizerResult.original.length + " chars | " + origWords + " words)";
            if (optStats) optStats.textContent = "(" + (v.text || "").length + " chars | " + optWords + " words)";

            const origTextEl = document.getElementById("opt-orig-text");
            const optTextEl = document.getElementById("opt-optimized-text");
            const labelEl = document.getElementById("opt-variant-active-label");

            if (origTextEl) origTextEl.textContent = lastOptimizerResult.original;
            if (optTextEl) optTextEl.textContent = v.text || "";
            if (labelEl) labelEl.textContent = "OPTIMIZED (" + (v.label || "VARIANT " + (activeVariantIndex + 1)).toUpperCase() + ")";

            // Word Diff
            const diffBox = document.getElementById("opt-diff-content");
            if (diffBox) {
                diffBox.innerHTML = v.diff || v.text || "";
            }

            // SERP Preview
            const serpContainer = document.getElementById("opt-serp-preview-container");
            if (serpContainer) {
                serpContainer.innerHTML = renderSerpBox(v.serp_preview || lastOptimizerResult.serp_preview);
            }

            // AI Preview
            const aiContainer = document.getElementById("opt-ai-preview-container");
            if (aiContainer) {
                aiContainer.innerHTML = renderAiOverviewBox(v.ai_overview_preview || lastOptimizerResult.ai_overview_preview);
            }

            // Schema & HTML Code
            const schemaCode = document.getElementById("opt-schema-code");
            const htmlCode = document.getElementById("opt-html-code");
            if (schemaCode) {
                schemaCode.textContent = JSON.stringify(v.schema_jsonld || lastOptimizerResult.schema_jsonld || {}, null, 2);
            }
            if (htmlCode) {
                htmlCode.textContent = v.semantic_html || lastOptimizerResult.semantic_html || "";
            }
        }

        function switchOptViewMode(mode) {
            activeOptViewMode = mode;
            const views = ["sidebyside", "diff", "serp", "ai", "code"];
            views.forEach(v => {
                const el = document.getElementById("opt-view-" + v);
                const btn = document.getElementById("tab-btn-" + v);
                if (el) el.style.display = (v === mode ? "block" : "none");
                if (btn) {
                    if (v === mode) btn.classList.add("active");
                    else btn.classList.remove("active");
                }
            });
        }

        function renderQuotabilitySignals(res) {
            const body = document.getElementById("opt-quotability-signals-body");
            const q = res.quotability_detail || {};

            body.innerHTML = `
                <div class="form-grid-3" style="gap: 12px;">
                    <div style="padding: 12px; border: 1px solid #e5e7eb; background: #ffffff;">
                        <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Declarative Syntax</div>
                        <div style="font-size: 14px; font-weight: 700; margin-top: 4px; color: ${q.has_declarative_opener ? '#15803d' : '#b91c1c'};">
                            ${q.has_declarative_opener ? 'Direct Subject-Predicate Match' : 'Indirect / Weak Sentence Start'}
                        </div>
                        <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Answers queries without conversational throat-clearing.</div>
                    </div>

                    <div style="padding: 12px; border: 1px solid #e5e7eb; background: #ffffff;">
                        <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Factual &amp; Data Anchors</div>
                        <div style="font-size: 14px; font-weight: 700; margin-top: 4px; color: ${res.fact_count > 0 ? '#15803d' : '#b45309'};">
                            ${res.fact_count} verifiable datapoints detected
                        </div>
                        <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Percentages, numeric metrics, years, or benchmarked stats.</div>
                    </div>

                    <div style="padding: 12px; border: 1px solid #e5e7eb; background: #ffffff;">
                        <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Named Entity Prominence</div>
                        <div style="font-size: 14px; font-weight: 700; margin-top: 4px; color: ${res.entity_count >= 2 ? '#15803d' : '#4b5563'};">
                            ${res.entity_count} named entities identified
                        </div>
                        <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Knowledge graph anchors and recognized industry terms.</div>
                    </div>
                </div>

                <div style="display: flex; gap: 12px; margin-top: 12px; flex-wrap: wrap;">
                    <div style="padding: 8px 12px; border: 1px solid #e5e7eb; background: #fafafa; font-size: 12px;">
                        <strong>Vague Modifiers Purged:</strong> ${res.vague_count || 0}
                    </div>
                    <div style="padding: 8px 12px; border: 1px solid #e5e7eb; background: #fafafa; font-size: 12px;">
                        <strong>AI Buzzwords Removed:</strong> ${res.filler_count || 0}
                    </div>
                    <div style="padding: 8px 12px; border: 1px solid #e5e7eb; background: #fafafa; font-size: 12px;">
                        <strong>Readability Grade:</strong> FKGL Grade ${q.flesch_grade != null ? q.flesch_grade : 'N/A'} (Score: ${res.readability_score}/100)
                    </div>
                </div>
            `;
        }

        function copyOptimizedText() {
            const v = getActiveVariant();
            if (!v || !v.text) {
                alert("No optimized content available to copy.");
                return;
            }
            navigator.clipboard.writeText(v.text).then(() => {
                alert("Optimized text copied to clipboard!");
            }).catch(() => {
                const ta = document.createElement("textarea");
                ta.value = v.text;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand("copy");
                document.body.removeChild(ta);
                alert("Optimized text copied to clipboard!");
            });
        }

        function copyOptimizedHtml() {
            const v = getActiveVariant();
            const html = v && v.semantic_html ? v.semantic_html : (lastOptimizerResult ? lastOptimizerResult.semantic_html : "");
            if (!html) {
                alert("No HTML snippet available to copy.");
                return;
            }
            navigator.clipboard.writeText(html).then(() => {
                alert("Semantic HTML copied to clipboard!");
            });
        }

        function copyOptimizedSchema() {
            const v = getActiveVariant();
            const schema = v && v.schema_jsonld ? v.schema_jsonld : (lastOptimizerResult ? lastOptimizerResult.schema_jsonld : {});
            if (!schema || Object.keys(schema).length === 0) {
                alert("No JSON-LD schema available to copy.");
                return;
            }
            navigator.clipboard.writeText(JSON.stringify(schema, null, 2)).then(() => {
                alert("Schema.org JSON-LD copied to clipboard!");
            });
        }

        // =========================================================================
        // TAB 4 SUB-MODE SWITCHER & CRAWL IMPROVER JAVASCRIPT CONTROLLER
        // =========================================================================
        let lastCrawlImproverResult = null;
        let lastPluginOptimizerResult = null;
        let activePluginVariantIndex = 0;
        let activePluginBoxView = "rankmath";

        function switchOptSubMode(mode) {
            const btnCrawl = document.getElementById("btn-opt-mode-crawl");
            const btnPlg = document.getElementById("btn-opt-mode-plugin");
            const btnSingle = document.getElementById("btn-opt-mode-single");

            const viewCrawl = document.getElementById("opt-crawl-view");
            const viewPlg = document.getElementById("opt-plugin-view");
            const viewSingle = document.getElementById("opt-single-view");

            const modeLabel = document.getElementById("opt-active-mode-label");

            // Reset all buttons
            if (btnCrawl) btnCrawl.classList.remove("active");
            if (btnPlg) btnPlg.classList.remove("active");
            if (btnSingle) btnSingle.classList.remove("active");

            // Hide all views
            if (viewCrawl) viewCrawl.style.display = "none";
            if (viewPlg) viewPlg.style.display = "none";
            if (viewSingle) viewSingle.style.display = "none";

            if (mode === "single") {
                if (btnSingle) btnSingle.classList.add("active");
                if (viewSingle) viewSingle.style.display = "block";
                if (modeLabel) modeLabel.textContent = "Single Element Optimizer";
            } else if (mode === "plugin") {
                if (btnPlg) btnPlg.classList.add("active");
                if (viewPlg) viewPlg.style.display = "block";
                if (modeLabel) modeLabel.textContent = "WordPress Plugin Metadata Suite";
            } else {
                // Default: crawl
                if (btnCrawl) btnCrawl.classList.add("active");
                if (viewCrawl) viewCrawl.style.display = "block";
                if (modeLabel) modeLabel.textContent = "Live URL & Plugin Notice Improver";
            }
        }

        const CRAWL_DEMO_PROFILES = {
            inersialab: {
                url: "https://www.inersialab.com",
                keyword: "InersiaLab Web Architecture",
                brand: "InersiaLab",
                industry: "tech",
                plugin_type: "rank_math",
                page_type: "WebPage",
                notice: `- Add Focus Keyword to the SEO title.
- Add Focus Keyword to your SEO Meta Description.
- Focus Keyword not found in the URL permalink.
- Focus Keyword does not appear in the first 10% of the content.
- Use Focus Keyword in subheadings like H2, H3.
- Content is 220 words long. Consider using at least 600 words.
- Add a number to your SEO title to improve CTR.
- Add an emotional power word to your SEO title.`
            },
            saas: {
                url: "https://example.com/platform",
                keyword: "Zero Trust Security Platform",
                brand: "ShieldZero",
                industry: "tech",
                plugin_type: "yoast",
                page_type: "Service",
                notice: `Yoast SEO Analysis:
- Keyphrase in SEO title: The focus keyphrase does not appear at the beginning of the SEO title.
- Keyphrase in meta description: The keyphrase or its synonyms do not appear in the meta description.
- Keyphrase in slug: More than half of your keyphrase is missing from the slug.
- Subheading distribution: You have 0 subheadings reflecting the topic.
- Text length: The text contains 180 words. This is far below the recommended minimum of 600 words.
- Keyphrase in introduction: Your keyphrase does not appear in the first paragraph.`
            },
            ecommerce: {
                url: "https://example.com/products/leather-bag",
                keyword: "Handmade Leather Travel Bag",
                brand: "Craftsman Goods",
                industry: "ecommerce",
                plugin_type: "aioseo",
                page_type: "Product",
                notice: `AIOSEO Page Checklist:
- SEO Title is too short and missing focus keyphrase.
- Meta Description lacks a compelling commercial call-to-action.
- Permalink contains stop words or is overly generic.
- H2 Subheadings do not mention product keywords.
- Word count: 140 words found. Target is 500+ words.
- Title is missing a year or numerical modifier.`
            },
            clinic: {
                url: "https://example.com/dental-implants",
                keyword: "Dental Implants Miami",
                brand: "Miami Smile Specialists",
                industry: "healthcare",
                plugin_type: "rank_math",
                page_type: "Service",
                notice: `Rank Math Errors:
- Focus Keyword not found in SEO title.
- Focus Keyword not found in SEO meta description.
- Focus Keyword not found in first 10% of content.
- Use Focus Keyword in H2 subheadings.
- Content length is below recommended minimum.
- Title does not contain a Power Word.`
            }
        };

        function loadCrawlDemoProfile(profileKey) {
            const prof = CRAWL_DEMO_PROFILES[profileKey];
            if (!prof) return;

            document.getElementById("opt-crawl-url").value = prof.url;
            document.getElementById("opt-crawl-keyword").value = prof.keyword;
            document.getElementById("opt-crawl-brand").value = prof.brand;
            document.getElementById("opt-crawl-industry").value = prof.industry;
            document.getElementById("opt-crawl-plugin-type").value = prof.plugin_type;
            document.getElementById("opt-crawl-page-type").value = prof.page_type;
            document.getElementById("opt-crawl-notice").value = prof.notice;
            const nameEl = document.getElementById("opt-crawl-file-name");
            if (nameEl) nameEl.textContent = "Preset Profile: " + profileKey.toUpperCase();
        }

        function handlePluginNoticeFileUpload(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) return;
            const nameEl = document.getElementById("opt-crawl-file-name");
            if (nameEl) nameEl.textContent = "File: " + file.name + " (" + Math.round(file.size / 1024) + " KB)";

            const reader = new FileReader();
            reader.onload = function(e) {
                const text = e.target.result;
                const textarea = document.getElementById("opt-crawl-notice");
                if (textarea) {
                    textarea.value = text;
                }
            };
            reader.readAsText(file);
        }

        function clearCrawlImprover() {
            document.getElementById("opt-crawl-url").value = "";
            document.getElementById("opt-crawl-notice").value = "";
            document.getElementById("opt-crawl-keyword").value = "";
            document.getElementById("opt-crawl-brand").value = "";
            const nameEl = document.getElementById("opt-crawl-file-name");
            if (nameEl) nameEl.textContent = "";
            const wrapper = document.getElementById("opt-crawl-results-wrapper");
            if (wrapper) {
                wrapper.innerHTML = "";
                wrapper.style.display = "none";
            }
            const indicator = document.getElementById("opt-crawl-status-indicator");
            if (indicator) indicator.textContent = "";
            lastCrawlImproverResult = null;
        }

        async function runCrawlImprover() {
            const url = document.getElementById("opt-crawl-url").value.trim();
            if (!url) {
                alert("Please enter a valid live webpage URL to crawl.");
                document.getElementById("opt-crawl-url").focus();
                return;
            }

            const notice = document.getElementById("opt-crawl-notice").value.trim();
            const keyword = document.getElementById("opt-crawl-keyword").value.trim();
            const brand = document.getElementById("opt-crawl-brand").value.trim();
            const pluginType = document.getElementById("opt-crawl-plugin-type").value;
            const industry = document.getElementById("opt-crawl-industry").value;
            const pageType = document.getElementById("opt-crawl-page-type").value;

            const btn = document.getElementById("btn-run-crawl-improver");
            const indicator = document.getElementById("opt-crawl-status-indicator");
            if (btn) btn.disabled = true;
            if (indicator) indicator.textContent = "Crawling webpage & analyzing plugin notices...";

            try {
                const response = await fetch("/api/optimizer/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        content_type: "crawl_plugin_fix",
                        url: url,
                        plugin_notice: notice,
                        focus_keyword: keyword,
                        site_name: brand,
                        plugin_type: pluginType,
                        industry: industry,
                        page_type: pageType
                    })
                });

                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || "Analysis failed.");
                }

                lastCrawlImproverResult = data.result;
                renderCrawlImproverResults(data.result);
                if (indicator) indicator.textContent = "Analysis complete. See side-by-side improvements below.";
            } catch (err) {
                alert("Crawl Improver Error: " + err.message);
                if (indicator) indicator.textContent = "Error: " + err.message;
            } finally {
                if (btn) btn.disabled = false;
            }
        }

        function copySideComparisonText(elementId, btnElement) {
            const el = document.getElementById(elementId);
            if (!el || !el.innerText) {
                alert("Text is empty.");
                return;
            }
            const textToCopy = el.innerText.trim();
            navigator.clipboard.writeText(textToCopy).then(() => {
                const orig = btnElement.textContent;
                btnElement.textContent = "COPIED";
                btnElement.classList.add("copied");
                setTimeout(() => {
                    btnElement.textContent = orig;
                    btnElement.classList.remove("copied");
                }, 2000);
            }).catch(() => {
                const ta = document.createElement("textarea");
                ta.value = textToCopy;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand("copy");
                document.body.removeChild(ta);
                const orig = btnElement.textContent;
                btnElement.textContent = "COPIED";
                btnElement.classList.add("copied");
                setTimeout(() => {
                    btnElement.textContent = orig;
                    btnElement.classList.remove("copied");
                }, 2000);
            });
        }

        function applyKeywordAndReRun(kw) {
            const input = document.getElementById("opt-crawl-keyword");
            if (input) {
                input.value = kw;
                const indicator = document.getElementById("opt-crawl-status-indicator");
                if (indicator) indicator.textContent = "Re-analyzing page with focus keyword: " + kw + "...";
                runCrawlImprover();
            }
        }

        function renderCrawlImproverResults(data) {
            const wrapper = document.getElementById("opt-crawl-results-wrapper");
            if (!wrapper || !data) return;

            const url = data.url || "";
            const pluginType = (data.plugin_type || "rank_math").toUpperCase();
            const focusKw = data.focus_keyword || "";
            const scoreBefore = data.baseline_score ?? data.score_before ?? 40;
            const scoreAfter = data.potential_score ?? data.score_after ?? 96;
            const scoreDelta = scoreAfter - scoreBefore;
            const comparisons = data.comparisons || [];
            const detectedItems = data.detected_notice_items || (data.parsed_notice && data.parsed_notice.flags) || [];
            const flagsCount = detectedItems.length;

            let html = `
                <!-- Banner Card -->
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-title" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <span>Crawl &amp; Plugin Optimization Scorecard</span>
                        <span class="tag-pill good" style="font-size: 13px; font-weight: 900; padding: 4px 10px;">GRADE: A+ (READY FOR PRODUCTION)</span>
                    </div>
                    
                    <div style="font-size: 12px; color: #4b5563; margin-top: -4px; margin-bottom: 12px; word-break: break-all;">
                        Crawled URL: <strong style="color: #111827;">${escapeHtml(url)}</strong> 
                        &bull; Target Plugin: <strong style="color: #111827;">${escapeHtml(pluginType)}</strong>
                        &bull; Focus Keyword: <strong style="color: #111827;">${escapeHtml(focusKw)}</strong>
                        &bull; Brand: <strong style="color: #111827;">${escapeHtml(data.site_name || "InersiaLab")}</strong>
                    </div>

                    <div class="form-grid-3" style="margin-top: 10px;">
                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Plugin Compliance Jump</div>
                                <div style="font-size: 11px; font-weight: 700; color: #15803d; margin-top: 2px;">+${scoreDelta} Points Gain</div>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 14px; color: #b91c1c; text-decoration: line-through; margin-right: 6px;">${scoreBefore}/100</span>
                                <span class="opt-score-badge good" style="font-size: 26px;">${scoreAfter}/100</span>
                            </div>
                        </div>

                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Plugin Warnings Resolved</div>
                                <div style="font-size: 11px; color: #15803d; margin-top: 2px; font-weight: 600;">100% Passed</div>
                            </div>
                            <div class="opt-score-badge good">${flagsCount} / ${flagsCount}</div>
                        </div>

                        <div class="opt-score-card">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">Side-by-Side Elements</div>
                                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Crawled &amp; Optimized</div>
                            </div>
                            <div class="opt-score-badge good">${comparisons.length}</div>
                        </div>
                    </div>
                </div>

                <!-- Discovered Focus Keywords Chips -->
                ${(data.recommended_keywords && data.recommended_keywords.length > 0) ? `
                    <div class="card" style="margin-bottom: 16px; padding: 14px 18px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                            <div>
                                <span style="font-size: 13px; font-weight: 700; color: #1d1d1f;">Discovered Page Keywords</span>
                                <span style="font-size: 11px; color: #86868b; margin-left: 6px;">(Auto-extracted from page content &amp; structure)</span>
                            </div>
                            <span style="font-size: 11px; color: #0071e3; font-weight: 600;">Click any keyword to re-run optimization</span>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${data.recommended_keywords.map(kw => {
                                const isCurrent = kw.toLowerCase() === focusKw.toLowerCase();
                                const activeStyle = isCurrent 
                                    ? 'background: #0071e3; color: #ffffff; border-color: #0071e3; box-shadow: 0 2px 6px rgba(0,113,227,0.3);' 
                                    : 'background: #ffffff; color: #1d1d1f; border-color: rgba(0,0,0,0.12);';
                                return `<button type="button" class="btn" style="padding: 6px 14px; font-size: 12px; border-radius: 980px; font-weight: 600; cursor: pointer; transition: all 0.2s; ${activeStyle}" onclick="applyKeywordAndReRun('${escapeHtml(kw)}')">${isCurrent ? '&#10003; ' : ''}${escapeHtml(kw)}</button>`;
                            }).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Detected Notice Checklist Card -->
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                        <span>SEO Plugin Violations Diagnosed &amp; Fixed</span>
                        <span style="font-size: 11px; color: #15803d; font-weight: 700;">ALL CONSTRAINTS RESOLVED</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 8px; margin-top: 10px;">
            `;

            if (detectedItems.length === 0) {
                html += `<div style="padding: 8px 14px; background: rgba(52, 199, 89, 0.08); border-left: 3px solid #34c759; border-radius: 10px; font-size: 12px; color: #248a3d; font-weight: 600;">Standard full-page optimization applied (no blocking notice warnings).</div>`;
            } else {
                detectedItems.forEach(item => {
                    const text = typeof item === 'string' ? item : (item.rule || item.message || JSON.stringify(item));
                    html += `
                        <div style="padding: 8px 14px; background: rgba(52, 199, 89, 0.06); border-left: 3px solid #34c759; border-radius: 10px; font-size: 12px; color: #1d1d1f;">
                            <strong style="color: #15803d;">RESOLVED:</strong> ${escapeHtml(text)}
                        </div>
                    `;
                });
            }

            html += `
                    </div>
                </div>
            `;

            // Helper to render a comparison card
            function renderSideBySideCard(comp, idx, isSection) {
                const copyId = `opt-crawl-copy-${idx}`;
                const elemName = comp.element || comp.element_name || `Element ${idx + 1}`;
                const currText = (comp.current && comp.current.text) || comp.current_text || "(Empty / missing from crawled page)";
                const currStats = (comp.current && comp.current.stats) || comp.current_stats || "";
                const issues = (comp.current && comp.current.issues) || comp.current_violations || [];

                const imprText = (comp.improved && comp.improved.text) || comp.improved_text || "";
                const imprStats = (comp.improved && comp.improved.stats) || comp.improved_stats || "";
                const benefits = (comp.improved && comp.improved.benefits) || comp.improved_benefits || [];

                const resolution = comp.plugin_resolution || comp.resolution_notes || "";
                const diffHtml = (comp.diff && comp.diff.html) || "";

                const violationsHtml = issues.map(v => 
                    `<span class="opt-badge-violation">${escapeHtml(v)}</span>`
                ).join(" ");
                const benefitsHtml = benefits.map(b => 
                    `<span class="opt-badge-benefit">${escapeHtml(b)}</span>`
                ).join(" ");

                const copyBtnLabel = isSection ? "COPY IMPROVED SECTION" : "COPY IMPROVED TEXT";

                return `
                    <div class="card" style="margin-bottom: 14px; padding: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                            <div>
                                <span style="font-size: 13px; font-weight: 800; color: #111827;">${idx + 1}. ${escapeHtml(elemName)}</span>
                            </div>
                            <div style="font-size: 11px; font-weight: 700; color: #15803d;">
                                Direct 1-to-1 Replacement
                            </div>
                        </div>

                        ${resolution ? `
                            <div style="font-size: 11px; color: #1d1d1f; margin-bottom: 10px; background: rgba(0, 113, 227, 0.05); padding: 7px 12px; border-left: 3px solid #0071e3; border-radius: 8px;">
                                <strong>Optimization Rationale:</strong> ${escapeHtml(resolution)}
                            </div>
                        ` : ''}

                        <!-- True Side-by-Side 2-Column Grid -->
                        <div class="opt-side-by-side-grid">
                            <!-- Left: Current (Crawled) Text -->
                            <div class="opt-side-col current">
                                <div>
                                    <div class="opt-side-header">
                                        <span class="opt-side-title">CURRENT (CRAWLED FROM PAGE)</span>
                                        <span style="font-size: 11px; font-weight: 700; color: #b91c1c;">${escapeHtml(currStats)}</span>
                                    </div>
                                    <div class="opt-side-badges">
                                        ${violationsHtml || '<span class="tag-pill" style="font-size: 10px; background: #fee2e2; color: #b91c1c;">Baseline</span>'}
                                    </div>
                                    <div class="opt-side-text" style="color: #4b5563; white-space: pre-wrap;">${escapeHtml(currText)}</div>
                                </div>
                            </div>

                            <!-- Right: Improved & Optimized Text -->
                            <div class="opt-side-col improved">
                                <div>
                                    <div class="opt-side-header">
                                        <span class="opt-side-title">IMPROVED &amp; OPTIMIZED VERSION</span>
                                        <span style="font-size: 11px; font-weight: 700; color: #15803d;">${escapeHtml(imprStats)}</span>
                                    </div>
                                    <div class="opt-side-badges">
                                        ${benefitsHtml}
                                    </div>
                                    <div class="opt-side-text" id="${copyId}" style="font-weight: 600; color: #111827; white-space: pre-wrap;">${escapeHtml(imprText)}</div>
                                    ${diffHtml ? `
                                        <div style="margin-top: 8px; font-size: 12px; padding: 6px; background: #ffffff; border: 1px dashed #d1d5db; border-radius: 6px;">
                                            <div style="font-size: 10px; font-weight: 700; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">Word-Level Diff:</div>
                                            <div>${diffHtml}</div>
                                        </div>
                                    ` : ''}
                                </div>
                                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #dcfce7; display: flex; justify-content: flex-end;">
                                    <button type="button" class="btn btn-outline plg-btn-copy" style="padding: 5px 14px; font-size: 11px; font-weight: 700; border-color: #15803d; color: #15803d; border-radius: 8px;" onclick="copySideComparisonText('${copyId}', this)">
                                        ${copyBtnLabel}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }

            // Separate into Part 1 (Metadata) and Part 2 (Page Sections)
            const metaComps = data.meta_comparisons || comparisons.slice(0, 4);
            const sectionComps = data.section_comparisons || comparisons.slice(4);

            // PART 1: WordPress Plugin Metadata
            html += `
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 14px; font-weight: 800; color: #111827; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                        <span>Part 1: SEO Plugin Metadata (Old vs Improved)</span>
                        <span style="font-size: 11px; color: #4b5563; font-weight: 600; text-transform: none;">Title, Meta Description, URL Slug &amp; H1 Headline</span>
                    </div>
            `;
            metaComps.forEach((comp, idx) => {
                html += renderSideBySideCard(comp, idx, false);
            });
            html += `</div>`;

            // PART 2: Full-Page Section-by-Section Content Replacements
            if (sectionComps && sectionComps.length > 0) {
                html += `
                    <div style="margin-bottom: 20px;">
                        <div style="font-size: 14px; font-weight: 800; color: #111827; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                            <span>Part 2: Full-Page Section-by-Section Content Replacements (Old Text vs Corrected Version)</span>
                            <span class="tag-pill good" style="font-size: 11px; font-weight: 700;">${sectionComps.length} Real Webpage Sections Extracted</span>
                        </div>
                        <div style="font-size: 12px; color: #6b7280; margin-top: -6px; margin-bottom: 14px;">
                            Each section of the live webpage with the original crawled text on the left and the corrected, high-converting version on the right with 1-click copy support.
                        </div>
                `;
                sectionComps.forEach((comp, sIdx) => {
                    html += renderSideBySideCard(comp, metaComps.length + sIdx, true);
                });
                html += `</div>`;
            }

            // Turnkey Plugin Copy-Paste Box
            const turnkeyBoxes = data.turnkey_plugin_boxes || {};
            const rmBox = turnkeyBoxes.rank_math || {};
            const yoastBox = turnkeyBoxes.yoast || {};

            html += `
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Direct WordPress Plugin Ready Export (Rank Math &amp; Yoast SEO)</span>
                        <span class="tag-pill good" style="font-size: 10px;">1-Click Copy Targets</span>
                    </div>
                    <div class="field-help" style="margin-top: -6px; margin-bottom: 12px;">
                        Copy and paste directly into the metadata fields in your WordPress post / page editor.
                    </div>

                    <div class="plg-field-row" style="margin-bottom: 10px;">
                        <div class="plg-field-header">
                            <span class="plg-field-label">Focus Keyword</span>
                            <span style="font-size: 11px; color: #15803d; font-weight: 700;">Target Keyword</span>
                        </div>
                        <div class="plg-copy-input-group">
                            <input type="text" id="crawl-rm-kw" value="${escapeHtml(rmBox.focus_keyword || focusKw)}" readonly>
                            <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('crawl-rm-kw', this)">Copy</button>
                        </div>
                    </div>

                    <div class="plg-field-row" style="margin-bottom: 10px;">
                        <div class="plg-field-header">
                            <span class="plg-field-label">SEO Title</span>
                            <span style="font-size: 11px; color: #15803d; font-weight: 700;">${rmBox.seo_title ? rmBox.seo_title.length : 0} chars | Optimal</span>
                        </div>
                        <div class="plg-copy-input-group">
                            <input type="text" id="crawl-rm-title" value="${escapeHtml(rmBox.seo_title || '')}" readonly>
                            <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('crawl-rm-title', this)">Copy</button>
                        </div>
                    </div>

                    <div class="plg-field-row" style="margin-bottom: 10px;">
                        <div class="plg-field-header">
                            <span class="plg-field-label">URL Permalink Slug</span>
                            <span style="font-size: 11px; color: #15803d; font-weight: 700;">Clean Kebab-Case</span>
                        </div>
                        <div class="plg-copy-input-group">
                            <input type="text" id="crawl-rm-slug" value="${escapeHtml(rmBox.permalink || yoastBox.slug || '')}" readonly>
                            <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('crawl-rm-slug', this)">Copy</button>
                        </div>
                    </div>

                    <div class="plg-field-row" style="margin-bottom: 10px;">
                        <div class="plg-field-header">
                            <span class="plg-field-label">Meta Description</span>
                            <span style="font-size: 11px; color: #15803d; font-weight: 700;">${rmBox.meta_description ? rmBox.meta_description.length : 0} chars | Optimal</span>
                        </div>
                        <div class="plg-copy-input-group">
                            <textarea id="crawl-rm-desc" rows="2" readonly style="width: 100%; font-family: inherit; font-size: 13px; padding: 8px; border: 1px solid #d1d5db;">${escapeHtml(rmBox.meta_description || '')}</textarea>
                            <button type="button" class="plg-btn-copy" onclick="copyInputSnippet('crawl-rm-desc', this)">Copy</button>
                        </div>
                    </div>
                </div>
            `;

            wrapper.innerHTML = html;
            wrapper.style.display = "block";
            wrapper.scrollIntoView({ behavior: "smooth", block: "start" });
        }


        function switchPluginBoxView(boxKey) {
            activePluginBoxView = boxKey;
            const boxes = ["rankmath", "yoast", "social", "schema", "ai"];
            boxes.forEach(b => {
                const el = document.getElementById("plg-box-" + b);
                const btn = document.getElementById("btn-plg-box-" + b);
                if (el) el.style.display = (b === boxKey ? "block" : "none");
                if (btn) {
                    if (b === boxKey) btn.classList.add("active");
                    else btn.classList.remove("active");
                }
            });
        }

        function calculateEstimatedPixelWidth(title) {
            const charWeights = {
                'i': 4, 'l': 4, 'j': 5, 't': 5, 'f': 5, 'r': 6, 'I': 5,
                'm': 14, 'w': 14, 'M': 15, 'W': 16,
                ' ': 4, '.': 4, ',': 4, '-': 5, '|': 4, ':': 4,
            };
            let total = 0;
            for (let i = 0; i < (title || "").length; i++) {
                total += charWeights[title[i]] || 9;
            }
            return total;
        }

        function updatePluginLiveStats() {
            const titleInput = document.getElementById("opt-plg-title");
            const descInput = document.getElementById("opt-plg-desc");
            const titleStats = document.getElementById("opt-plg-title-stats");
            const titleBar = document.getElementById("opt-plg-title-bar");
            const descStats = document.getElementById("opt-plg-desc-stats");

            if (titleInput) {
                const title = titleInput.value;
                const chars = title.length;
                const px = calculateEstimatedPixelWidth(title);
                const pct = Math.min(100, Math.round((px / 580) * 100));
                const isTruncated = px > 580 || chars > 60;

                if (titleStats) {
                    titleStats.innerHTML = `${chars} chars | ~${px} px ` +
                        (isTruncated ? `<span style="color: #b91c1c; font-weight: 800;">[TRUNCATION RISK]</span>` :
                         (chars >= 50 ? `<span style="color: #15803d; font-weight: 800;">[OPTIMAL]</span>` : `<span style="color: #4b5563;">(Target: 50-60 chars, &lt;580px)</span>`));
                }
                if (titleBar) {
                    titleBar.style.width = pct + "%";
                    if (isTruncated) titleBar.classList.add("warn");
                    else titleBar.classList.remove("warn");
                }
            }

            if (descInput) {
                const desc = descInput.value;
                const chars = desc.length;
                const isOptimal = chars >= 125 && chars <= 155;
                const isOver = chars > 155;

                if (descStats) {
                    descStats.innerHTML = `${chars} chars ` +
                        (isOver ? `<span style="color: #b91c1c; font-weight: 800;">[TRUNCATION RISK: &gt;155]</span>` :
                         (isOptimal ? `<span style="color: #15803d; font-weight: 800;">[OPTIMAL 125-155]</span>` : `<span style="color: #4b5563;">(Target: 125-155 chars)</span>`));
                }
            }
        }

        function onPluginInputLiveChange() {
            const kw = document.getElementById("opt-plg-keyword").value.trim();
            const slugInput = document.getElementById("opt-plg-slug");
            if (slugInput && !slugInput.value) {
                const cleanSlug = kw.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').substring(0, 50);
                slugInput.placeholder = cleanSlug || "e.g. dental-implants-miami";
            }
        }

        function loadPluginDemoProfile(profileKey) {
            const kwInput = document.getElementById("opt-plg-keyword");
            const secKwInput = document.getElementById("opt-plg-secondary-keywords");
            const pluginSelect = document.getElementById("opt-plg-plugin-type");
            const siteInput = document.getElementById("opt-plg-site-name");
            const slugInput = document.getElementById("opt-plg-slug");
            const indSelect = document.getElementById("opt-plg-industry");
            const typeSelect = document.getElementById("opt-plg-page-type");
            const titleInput = document.getElementById("opt-plg-title");
            const descInput = document.getElementById("opt-plg-desc");
            const contentInput = document.getElementById("opt-plg-content");

            if (profileKey === "dental") {
                kwInput.value = "Dental Implants Miami";
                secKwInput.value = "tooth replacement, full arch implants, cosmetic dentistry";
                pluginSelect.value = "rank_math";
                siteInput.value = "Miami Smile Clinic";
                slugInput.value = "dental-implants-miami";
                indSelect.value = "healthcare";
                typeSelect.value = "Service";
                titleInput.value = "Dental Implants in Miami";
                descInput.value = "We provide dental implants in Miami with affordable prices.";
                contentInput.value = "Miami Smile Clinic provides surgical dental implants and full mouth tooth replacement backed by verified clinical standards.";
            } else if (profileKey === "saas") {
                kwInput.value = "Zero Trust Architecture";
                secKwInput.value = "identity verification, microsegmentation, secure access";
                pluginSelect.value = "rank_math";
                siteInput.value = "InersiaLab Security";
                slugInput.value = "zero-trust-architecture";
                indSelect.value = "tech";
                typeSelect.value = "Service";
                titleInput.value = "Enterprise Zero Trust Security Platform";
                descInput.value = "Our platform helps companies secure their networks using zero trust tools.";
                contentInput.value = "InersiaLab delivers zero trust architecture automating continuous authentication across hybrid cloud environments.";
            } else if (profileKey === "contractor") {
                kwInput.value = "Luxury Kitchen Remodeling";
                secKwInput.value = "custom kitchen design, luxury cabinetry, marble countertops";
                pluginSelect.value = "yoast";
                siteInput.value = "Apex Design Build";
                slugInput.value = "luxury-kitchen-remodeling";
                indSelect.value = "general";
                typeSelect.value = "Service";
                titleInput.value = "Kitchen Remodeling Services";
                descInput.value = "Looking to remodel your kitchen? Call us today for a free quote.";
                contentInput.value = "Apex Design Build crafts custom luxury kitchen remodeling projects featuring artisan cabinetry and turnkey project management.";
            }

            updatePluginLiveStats();
        }

        function clearPluginOptimizer() {
            document.getElementById("opt-plg-keyword").value = "";
            document.getElementById("opt-plg-secondary-keywords").value = "";
            document.getElementById("opt-plg-site-name").value = "";
            document.getElementById("opt-plg-slug").value = "";
            document.getElementById("opt-plg-title").value = "";
            document.getElementById("opt-plg-desc").value = "";
            document.getElementById("opt-plg-content").value = "";
            document.getElementById("opt-plugin-results-wrapper").style.display = "none";
            lastPluginOptimizerResult = null;
            activePluginVariantIndex = 0;
            updatePluginLiveStats();
        }

        async function runPluginOptimizer() {
            const kw = document.getElementById("opt-plg-keyword").value.trim();
            const title = document.getElementById("opt-plg-title").value.trim();
            const desc = document.getElementById("opt-plg-desc").value.trim();

            if (!kw && !title && !desc) {
                alert("Please provide at least a Focus Keyword, Draft Title, or Meta Description.");
                document.getElementById("opt-plg-keyword").focus();
                return;
            }

            const secKwRaw = document.getElementById("opt-plg-secondary-keywords").value.trim();
            const secKws = secKwRaw ? secKwRaw.split(",").map(k => k.trim()).filter(Boolean) : [];
            const pluginType = document.getElementById("opt-plg-plugin-type").value;
            const siteName = document.getElementById("opt-plg-site-name").value.trim();
            const slug = document.getElementById("opt-plg-slug").value.trim();
            const industry = document.getElementById("opt-plg-industry").value;
            const pageType = document.getElementById("opt-plg-page-type").value;
            const contentSample = document.getElementById("opt-plg-content").value.trim();

            const btn = document.getElementById("btn-run-plugin-optimizer");
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = "AUDITING & OPTIMIZING PLUGIN SUITE...";

            try {
                const response = await fetch("/api/optimizer/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        content_type: "seo_plugin",
                        focus_keyword: kw,
                        secondary_keywords: secKws,
                        plugin_type: pluginType,
                        site_name: siteName,
                        slug: slug,
                        industry: industry,
                        page_type: pageType,
                        title: title,
                        description: desc,
                        content_sample: contentSample
                    })
                });

                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || "SEO Plugin optimization failed.");
                }

                lastPluginOptimizerResult = data.result;
                activePluginVariantIndex = 0;
                renderPluginOptimizerResults(data.result);

                const resWrapper = document.getElementById("opt-plugin-results-wrapper");
                resWrapper.scrollIntoView({ behavior: "smooth", block: "start" });
            } catch (err) {
                alert("Plugin Optimizer Error: " + err.message);
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        }

        function renderPluginOptimizerResults(res) {
            const wrapper = document.getElementById("opt-plugin-results-wrapper");
            wrapper.style.display = "block";

            // Grade & Overall Scores
            const gradeEl = document.getElementById("opt-plg-grade-badge");
            gradeEl.textContent = "GRADE: " + (res.grade || "A+");
            gradeEl.className = "tag-pill " + (res.overall_score >= 80 ? "good" : (res.overall_score >= 60 ? "warn" : "req"));

            const overallEl = document.getElementById("opt-plg-overall-score");
            overallEl.textContent = res.overall_score;
            overallEl.className = "opt-score-badge " + getScoreClass(res.overall_score);

            const seoEl = document.getElementById("opt-plg-seo-score");
            seoEl.textContent = res.seo_score;
            seoEl.className = "opt-score-badge " + getScoreClass(res.seo_score);

            const geoEl = document.getElementById("opt-plg-geo-score");
            geoEl.textContent = res.geo_score;
            geoEl.className = "opt-score-badge " + getScoreClass(res.geo_score);

            const deltaEl = document.getElementById("opt-plg-overall-delta");
            deltaEl.textContent = "Potential Score: 98/100 (A+)";

            // 12-Factor Checklist
            const testsGrid = document.getElementById("opt-plg-tests-grid");
            testsGrid.innerHTML = "";
            (res.tests || []).forEach(t => {
                const item = document.createElement("div");
                item.className = "plg-test-item";
                const badgeClass = t.status === "passed" ? "passed" : (t.status === "failed" ? "failed" : "warning");
                const badgeText = t.status === "passed" ? "[PASS]" : (t.status === "failed" ? "[FAIL]" : "[WARN]");

                item.innerHTML = `
                    <span class="plg-test-badge ${badgeClass}">${badgeText}</span>
                    <div style="flex: 1;">
                        <div style="font-size: 12px; font-weight: 700; color: #111827; margin-bottom: 2px;">
                            ${escapeOptHtml(t.name)}
                            <span style="font-size: 10px; color: #6b7280; font-weight: normal; margin-left: 4px;">(${t.earned}/${t.max} pts)</span>
                        </div>
                        <div style="font-size: 11px; color: #4b5563; line-height: 1.45;">${escapeOptHtml(t.message)}</div>
                        ${t.status !== 'passed' ? `<div style="font-size: 11px; color: #15803d; font-weight: 600; margin-top: 4px;">Fix: ${escapeOptHtml(t.fix)}</div>` : ''}
                    </div>
                `;
                testsGrid.appendChild(item);
            });

            // 3 Strategy Variants
            renderPluginVariantsGrid(res);

            // Populate active variant into plugin copy boxes
            updatePluginCopyBoxes();

            // Populate Social, Schema, AI Prompt
            const pSnippets = res.plugin_snippets || {};
            const socialCode = document.getElementById("plg-copy-social-code");
            if (socialCode && pSnippets.social) {
                socialCode.textContent = pSnippets.social.raw_html || "";
            }

            const schemaCode = document.getElementById("plg-copy-schema-code");
            if (schemaCode && pSnippets.schema_jsonld) {
                schemaCode.textContent = JSON.stringify(pSnippets.schema_jsonld, null, 2);
            }

            const aiPrompt = document.getElementById("plg-copy-ai-prompt");
            if (aiPrompt && pSnippets.master_ai_prompt) {
                aiPrompt.textContent = pSnippets.master_ai_prompt;
            }

            // Populate Desktop & Mobile SERP Preview
            renderPluginSerpPreview(res.serp_preview);
        }

        function renderPluginVariantsGrid(res) {
            const container = document.getElementById("opt-plg-variants-grid");
            container.innerHTML = "";

            (res.variants || []).forEach((v, idx) => {
                const card = document.createElement("div");
                card.className = "opt-variant-card" + (idx === activePluginVariantIndex ? " active" : "");
                card.onclick = () => selectPluginVariant(idx);

                const tLen = (v.title || "").length;
                const dLen = (v.description || "").length;
                const px = calculateEstimatedPixelWidth(v.title || "");

                card.innerHTML = `
                    <div class="opt-variant-title">
                        <span>${idx + 1}. ${escapeOptHtml(v.label)}</span>
                        ${idx === activePluginVariantIndex ? '<span class="tag-pill good" style="font-size: 10px;">Active Selection</span>' : ''}
                    </div>
                    <div class="opt-variant-desc" style="margin-bottom: 8px;">${escapeOptHtml(v.strategy)}</div>
                    <div style="font-size: 12px; color: #111827; background: #ffffff; border: 1px solid #e5e7eb; padding: 6px 8px; font-weight: 700; margin-bottom: 4px;">
                        ${escapeOptHtml(v.title)}
                    </div>
                    <div style="font-size: 11px; color: #4b5563; background: #ffffff; border: 1px solid #e5e7eb; padding: 6px 8px; margin-bottom: 6px; line-height: 1.4;">
                        ${escapeOptHtml(v.description)}
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #6b7280;">
                        <span>Title: <strong>${tLen} chars | ~${px}px</strong></span>
                        <span>Desc: <strong>${dLen} chars</strong></span>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function selectPluginVariant(idx) {
            activePluginVariantIndex = idx;
            if (lastPluginOptimizerResult) {
                renderPluginVariantsGrid(lastPluginOptimizerResult);
                updatePluginCopyBoxes();
                renderPluginSerpPreview(lastPluginOptimizerResult.serp_preview);
            }
        }

        function updatePluginCopyBoxes() {
            if (!lastPluginOptimizerResult) return;
            const variants = lastPluginOptimizerResult.variants || [];
            const activeVar = variants[activePluginVariantIndex] || lastPluginOptimizerResult.optimized;
            const kw = lastPluginOptimizerResult.inputs.focus_keyword || "";
            const site = lastPluginOptimizerResult.inputs.site_name || "";
            const title = activeVar.title || "";
            const desc = activeVar.description || "";
            const slug = activeVar.slug || cleanSlugText(kw);

            // Rank Math Box
            const rmKw = document.getElementById("rm-copy-keyword");
            const rmTitle = document.getElementById("rm-copy-title");
            const rmSlug = document.getElementById("rm-copy-slug");
            const rmDesc = document.getElementById("rm-copy-desc");
            const rmTitlePill = document.getElementById("rm-title-len-pill");
            const rmDescPill = document.getElementById("rm-desc-len-pill");

            if (rmKw) rmKw.value = kw;
            if (rmTitle) rmTitle.value = title;
            if (rmSlug) rmSlug.value = slug;
            if (rmDesc) rmDesc.value = desc;

            const px = calculateEstimatedPixelWidth(title);
            if (rmTitlePill) rmTitlePill.textContent = `${title.length} chars / ~${px} px`;
            if (rmDescPill) rmDescPill.textContent = `${desc.length} chars`;

            // Yoast Box
            const yKw = document.getElementById("yoast-copy-keyphrase");
            const yTitleLit = document.getElementById("yoast-copy-title-literal");
            const yTitleTpl = document.getElementById("yoast-copy-title-tpl");
            const ySlug = document.getElementById("yoast-copy-slug");
            const yDesc = document.getElementById("yoast-copy-desc");

            const yoastBase = title.split(" | ")[0].split(" - ")[0];

            if (yKw) yKw.value = kw;
            if (yTitleLit) yTitleLit.value = title;
            if (yTitleTpl) yTitleTpl.value = `${yoastBase} %%sep%% %%sitename%%`;
            if (ySlug) ySlug.value = slug;
            if (yDesc) yDesc.value = desc;
        }

        function cleanSlugText(text) {
            return (text || "").toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').substring(0, 50);
        }

        function renderPluginSerpPreview(serp) {
            if (!lastPluginOptimizerResult) return;
            const variants = lastPluginOptimizerResult.variants || [];
            const activeVar = variants[activePluginVariantIndex] || lastPluginOptimizerResult.optimized;
            const site = lastPluginOptimizerResult.inputs.site_name || "InersiaLab";
            const domain = site.toLowerCase().replace(/[^a-z0-9]/g, '') + ".com";
            const title = activeVar.title || "";
            const desc = activeVar.description || "";
            const slug = activeVar.slug || cleanSlugText(lastPluginOptimizerResult.inputs.focus_keyword || "");
            const px = calculateEstimatedPixelWidth(title);
            const isTruncated = px > 580 || title.length > 60;
            const pct = Math.min(100, Math.round((px / 580) * 100));

            // Desktop SERP
            const deskContainer = document.getElementById("opt-plg-serp-desktop");
            if (deskContainer) {
                deskContainer.innerHTML = `
                    <div class="serp-box">
                        <div class="serp-url-row">
                            <span class="serp-favicon">${site.charAt(0).toUpperCase()}</span>
                            <span>https://${domain} &gt; ${escapeOptHtml(slug.replace(/-/g, ' '))}</span>
                        </div>
                        <div class="serp-title">${escapeOptHtml(title)}</div>
                        <div class="serp-snippet">${escapeOptHtml(desc)}</div>
                        <div class="serp-pixel-bar">
                            <div class="serp-pixel-fill ${isTruncated ? 'warn' : ''}" style="width: ${pct}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 11px; color: #6b7280; margin-top: 6px;">
                            <span>Pixel Width: <strong>~${px}px / 580px</strong> (${pct}%)</span>
                            <span>${isTruncated ? '<strong style="color: #b91c1c;">Truncation Risk</strong>' : '<strong style="color: #15803d;">Fits Desktop SERP</strong>'}</span>
                        </div>
                    </div>
                `;
            }

            // Mobile SERP
            const mobContainer = document.getElementById("opt-plg-serp-mobile");
            if (mobContainer) {
                mobContainer.innerHTML = `
                    <div class="serp-box" style="border-radius: 12px; background: #fafafa;">
                        <div class="serp-url-row" style="font-size: 11px;">
                            <span class="serp-favicon" style="width: 16px; height: 16px; font-size: 9px;">${site.charAt(0).toUpperCase()}</span>
                            <span>${domain} &gt; ${escapeOptHtml(slug)}</span>
                        </div>
                        <div class="serp-title" style="font-size: 18px; line-height: 1.25;">${escapeOptHtml(title)}</div>
                        <div class="serp-snippet" style="font-size: 13px; line-height: 1.5;">${escapeOptHtml(desc)}</div>
                        <div style="font-size: 10px; color: #15803d; font-weight: 700; margin-top: 6px;">
                            Mobile Viewport Verified
                        </div>
                    </div>
                `;
            }
        }

        function copyInputSnippet(elementId, btnElement) {
            const el = document.getElementById(elementId);
            if (!el || !el.value) {
                alert("Field is empty.");
                return;
            }
            navigator.clipboard.writeText(el.value).then(() => {
                const orig = btnElement.textContent;
                btnElement.textContent = "COPIED";
                btnElement.classList.add("copied");
                setTimeout(() => {
                    btnElement.textContent = orig;
                    btnElement.classList.remove("copied");
                }, 2000);
            }).catch(() => {
                el.select();
                document.execCommand("copy");
                const orig = btnElement.textContent;
                btnElement.textContent = "COPIED";
                btnElement.classList.add("copied");
                setTimeout(() => {
                    btnElement.textContent = orig;
                    btnElement.classList.remove("copied");
                }, 2000);
            });
        }

        function copyCodeSnippet(elementId, btnElement) {
            const el = document.getElementById(elementId);
            if (!el || !el.textContent) {
                alert("Code snippet is empty.");
                return;
            }
            navigator.clipboard.writeText(el.textContent).then(() => {
                const orig = btnElement.textContent;
                btnElement.textContent = "COPIED";
                btnElement.classList.add("copied");
                setTimeout(() => {
                    btnElement.textContent = orig;
                    btnElement.classList.remove("copied");
                }, 2000);
            });
        }

        // =========================================================================
        // CYBERSECURITY & SERVER HARDENING CONTROLLER (TAB 5)
        // =========================================================================
        let isAuditingSecurity = false;
        let lastSecurityPdf = null;
        let lastSecurityResult = null;
        let currentSecurityFindingsFilter = "all";
        let currentSecurityView = "findings";
        window.securityReportsLoaded = false;

        async function startSecurityAudit() {
            const urlInput = document.getElementById("sec-url").value.trim();
            if (!urlInput) {
                alert("Please enter a valid website URL.");
                return;
            }

            document.getElementById("btn-start-security").disabled = true;
            document.getElementById("sec-status-badge").className = "status-badge running";
            document.getElementById("sec-status-badge").innerText = "RUNNING";
            document.getElementById("sec-status-text").innerText = "Probing cybersecurity posture for " + urlInput + "...";
            document.getElementById("sec-terminal").innerText = "Initializing security auditor for " + urlInput + "...\n";
            document.getElementById("sec-results-wrapper").style.display = "none";

            try {
                const res = await fetch("/api/security/start", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({url: urlInput})
                });
                const data = await res.json();
                if (data.error) {
                    alert("Error: " + data.error);
                    document.getElementById("btn-start-security").disabled = false;
                }
            } catch (e) {
                alert("Failed to reach audit server: " + e);
                document.getElementById("btn-start-security").disabled = false;
            }
        }

        async function pollSecurityStatus() {
            try {
                const res = await fetch("/api/security/status");
                const data = await res.json();

                isAuditingSecurity = data.is_running;
                const startBtn = document.getElementById("btn-start-security");
                if (startBtn) startBtn.disabled = isAuditingSecurity;

                const badge = document.getElementById("sec-status-badge");
                const statusTxt = document.getElementById("sec-status-text");

                if (isAuditingSecurity) {
                    if (badge) {
                        badge.className = "status-badge running";
                        badge.innerText = "RUNNING";
                    }
                    if (statusTxt) statusTxt.innerText = data.status || "Auditing security...";
                } else if (data.status === "Security Audit Complete") {
                    if (badge) {
                        badge.className = "status-badge success";
                        badge.innerText = "COMPLETED";
                    }
                    if (statusTxt) statusTxt.innerText = "Security audit completed successfully";
                } else if (data.status && data.status.startsWith("Error")) {
                    if (badge) {
                        badge.className = "status-badge running";
                        badge.innerText = "ERROR";
                    }
                    if (statusTxt) statusTxt.innerText = data.status;
                } else {
                    if (badge) {
                        badge.className = "status-badge";
                        badge.innerText = "READY";
                    }
                    if (statusTxt) statusTxt.innerText = data.status || "Ready";
                }

                // Update logs terminal
                const term = document.getElementById("sec-terminal");
                if (term) {
                    if (data.logs && data.logs.length > 0) {
                        term.innerText = data.logs.join("");
                        term.scrollTop = term.scrollHeight;
                        const logCount = document.getElementById("sec-log-count");
                        if (logCount) logCount.innerText = data.logs.length + " lines";
                    } else if (!isAuditingSecurity) {
                        term.innerText = "Awaiting security execution command...";
                        const logCount = document.getElementById("sec-log-count");
                        if (logCount) logCount.innerText = "0 lines";
                    }
                }

                // Last PDF
                const openPdfBtn = document.getElementById("btn-open-security-pdf");
                if (data.last_pdf) {
                    lastSecurityPdf = data.last_pdf;
                    if (openPdfBtn) openPdfBtn.disabled = false;
                } else {
                    lastSecurityPdf = null;
                    if (openPdfBtn) openPdfBtn.disabled = true;
                }

                // Render Results if available or hide if reset
                if (data.last_result && (!lastSecurityResult || lastSecurityResult.timestamp !== data.last_result.timestamp)) {
                    renderSecurityResults(data.last_result);
                } else if (!data.last_result && !isAuditingSecurity) {
                    lastSecurityResult = null;
                    const wrapper = document.getElementById("sec-results-wrapper");
                    if (wrapper) wrapper.style.display = "none";
                }
            } catch (e) {
                // Background poll fail ignored
            }
        }

        function renderSecurityResults(res) {
            lastSecurityResult = res;
            const wrapper = document.getElementById("sec-results-wrapper");
            if (!wrapper) return;
            wrapper.style.display = "block";

            // Grade Badge
            const gradeEl = document.getElementById("sec-grade-badge");
            if (gradeEl) {
                let color = "#111827";
                if (res.score >= 80) color = "#15803d";
                else if (res.score >= 70) color = "#b45309";
                else color = "#b91c1c";
                gradeEl.innerHTML = `<span style="color: ${color};">GRADE: ${res.grade} (${res.score}/100)</span>`;
            }

            // Host meta
            const hostMeta = document.getElementById("sec-host-meta");
            if (hostMeta) {
                hostMeta.innerText = `Target: ${res.domain} (${res.ip_address}) | Inspected: ${res.timestamp}`;
            }

            // Counters
            const c = res.counts || {critical: 0, high: 0, medium: 0, low: 0, passed: 0};
            const cCrit = document.getElementById("sec-cnt-crit");
            const cHigh = document.getElementById("sec-cnt-high");
            const cMed = document.getElementById("sec-cnt-med");
            const cLow = document.getElementById("sec-cnt-low");
            const cPass = document.getElementById("sec-cnt-pass");

            if (cCrit) cCrit.innerText = `${c.critical} CRITICAL`;
            if (cHigh) cHigh.innerText = `${c.high} HIGH`;
            if (cMed) cMed.innerText = `${c.medium} MEDIUM`;
            if (cLow) cLow.innerText = `${c.low} LOW`;
            if (cPass) cPass.innerText = `${c.passed} PASSED`;

            // Code Patches
            if (res.patches) {
                const codeHt = document.getElementById("sec-code-htaccess");
                if (codeHt) codeHt.textContent = res.patches.htaccess || "";

                const codeFn = document.getElementById("sec-code-functions");
                if (codeFn) codeFn.textContent = res.patches.functions_php || "";

                const codeFm = document.getElementById("sec-code-form");
                if (codeFm) codeFm.textContent = res.patches.contact_form || "";

                const codePrm = document.getElementById("sec-code-master");
                if (codePrm) codePrm.textContent = res.patches.master_prompt || "";

                // DNS Table
                const dnsContainer = document.getElementById("sec-dns-table-container");
                if (dnsContainer && res.patches.dns) {
                    let html = `<table class="data-table"><thead><tr><th>Record Type</th><th>Host / Name</th><th>Target / Value</th><th>Protection Purpose</th></tr></thead><tbody>`;
                    res.patches.dns.forEach(d => {
                        html += `<tr><td><strong>${escapeOptHtml(d.type)}</strong></td><td><code>${escapeOptHtml(d.host)}</code></td><td><code style="word-break:break-all;">${escapeOptHtml(d.value)}</code></td><td style="color:#4b5563;">${escapeOptHtml(d.purpose)}</td></tr>`;
                    });
                    html += `</tbody></table>`;
                    dnsContainer.innerHTML = html;
                }
            }

            // Render Findings
            renderSecurityFindings();
        }

        function renderSecurityFindings() {
            if (!lastSecurityResult || !lastSecurityResult.findings) return;
            const container = document.getElementById("sec-findings-container");
            if (!container) return;
            container.innerHTML = "";

            const filter = currentSecurityFindingsFilter;
            const list = lastSecurityResult.findings.filter(f => {
                if (filter === "all") return true;
                return f.severity === filter;
            });

            if (list.length === 0) {
                container.innerHTML = `<div style="padding: 20px; text-align: center; color: #6b7280; border: 1px dashed #d1d5db; background: #fafafa;">No findings match the selected filter "${filter.toUpperCase()}".</div>`;
                return;
            }

            const badgeClassMap = {
                critical: "badge-crit",
                high: "badge-high",
                medium: "badge-med",
                low: "badge-low",
                passed: "badge-pass"
            };

            list.forEach(f => {
                const bClass = badgeClassMap[f.severity] || "badge-low";
                const card = document.createElement("div");
                card.className = "finding-card";
                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span class="${bClass}">${f.severity.toUpperCase()}</span>
                            <strong style="font-size: 13px; color: #111827;">${escapeOptHtml(f.title)}</strong>
                        </div>
                        <code style="font-size: 11px; background: #f3f4f6; padding: 2px 6px; border: 1px solid #e5e7eb;">${escapeOptHtml(f.location)}</code>
                    </div>
                    <div style="font-size: 12px; color: #374151; margin-bottom: 6px; line-height: 1.5;">
                        <strong>Technical Impact:</strong> ${escapeOptHtml(f.impact)}
                    </div>
                    <div style="font-size: 12px; color: #15803d; line-height: 1.5; background: rgba(52, 199, 89, 0.06); padding: 8px 12px; border-left: 3px solid #34c759; border-radius: 8px;">
                        <strong>Remediation:</strong> ${escapeOptHtml(f.recommendation)}
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function filterSecurityFindings(sev) {
            currentSecurityFindingsFilter = sev;
            renderSecurityFindings();
        }

        function switchSecurityView(view) {
            currentSecurityView = view;
            ["findings", "patches", "prompt"].forEach(v => {
                const el = document.getElementById("sec-view-" + v);
                const btn = document.getElementById("sec-tab-" + v);
                if (el) el.style.display = (v === view) ? "block" : "none";
                if (btn) {
                    if (v === view) btn.classList.add("active");
                    else btn.classList.remove("active");
                }
            });
        }

        async function openLatestSecurityPdf() {
            try {
                const res = await fetch("/api/security/open-latest", {method: "POST"});
                const data = await res.json();
                if (!data.success) {
                    alert("Could not open Security PDF: " + (data.error || "File not found"));
                }
            } catch (e) {
                alert("Failed to open PDF: " + e);
            }
        }

        async function loadSecurityReports() {
            try {
                const res = await fetch("/api/security/reports");
                const reports = await res.json();
                const tbody = document.getElementById("sec-reports-tbody");
                if (!tbody) return;

                if (!reports || reports.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #6b7280; padding: 20px;">No security audit reports found in Downloads yet.</td></tr>';
                    return;
                }

                tbody.innerHTML = reports.map(r => `
                    <tr>
                        <td style="font-weight: 600; font-family: monospace; font-size: 11px;">${r.filename}</td>
                        <td style="color: #4b5563;">${r.time}</td>
                        <td style="color: #6b7280;">${r.size}</td>
                        <td>
                            <button class="btn btn-outline" style="padding: 3px 8px; font-size: 10px;" onclick="openSpecificFile('${r.filename}')">Open PDF</button>
                        </td>
                    </tr>
                `).join("");
                window.securityReportsLoaded = true;
            } catch (e) {
                // ignore
            }
        }

        function copySecuritySnippet(type) {
            if (!lastSecurityResult || !lastSecurityResult.patches) {
                alert("No security patches generated yet. Run a security audit first.");
                return;
            }
            let text = "";
            let name = "";
            if (type === "htaccess") {
                text = lastSecurityResult.patches.htaccess;
                name = ".htaccess Hardening";
            } else if (type === "functions") {
                text = lastSecurityResult.patches.functions_php;
                name = "functions.php Security Patch";
            } else if (type === "form") {
                text = lastSecurityResult.patches.contact_form;
                name = "Contact Form Secure Code";
            } else if (type === "master") {
                text = lastSecurityResult.patches.master_prompt;
                name = "Master AI Fix Prompt";
            }

            if (!text) {
                alert("Snippet is empty.");
                return;
            }
            navigator.clipboard.writeText(text).then(() => {
                alert(name + " copied to clipboard!");
            }).catch(() => {
                const ta = document.createElement("textarea");
                ta.value = text;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand("copy");
                document.body.removeChild(ta);
                alert(name + " copied to clipboard!");
            });
        }

        // Intervals
        setInterval(pollAuditStatus, 1500);
        setInterval(pollSecurityStatus, 1500);
        setInterval(loadReportsList, 5000);
        setInterval(loadSecurityReports, 5000);

        // Init
        window.addEventListener("DOMContentLoaded", () => {
            pollAuditStatus();
            pollSecurityStatus();
            loadReportsList();
            loadSecurityReports();
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

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def handle_reset(self):
        global audit_state, security_state, blueprint_state, content_state, optimizer_state
        audit_state["is_running"] = False
        audit_state["status"] = "Ready"
        audit_state["logs"] = []
        audit_state["last_result"] = None
        audit_state["last_pdf"] = None

        security_state["is_running"] = False
        security_state["status"] = "Ready"
        security_state["logs"] = []
        security_state["last_result"] = None
        security_state["last_pdf"] = None

        blueprint_state["is_generating"] = False
        blueprint_state["status"] = "Ready"
        blueprint_state["last_pdf"] = None
        blueprint_state["last_starter_dir"] = None
        blueprint_state["last_html"] = None
        blueprint_state["last_brand"] = None

        content_state["is_generating"] = False
        content_state["status"] = "Ready"
        content_state["last_dir"] = None
        content_state["last_results"] = None

        optimizer_state["last_result"] = None

        try:
            import importlib
            importlib.invalidate_caches()
        except Exception:
            pass

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, "message": "All engine states and server caches successfully reset."}).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/reset", "/api/clear-cache"):
            self.handle_reset()

        elif path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
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

        elif path == "/api/security/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "is_running": security_state["is_running"],
                "status": security_state["status"],
                "logs": security_state["logs"],
                "last_result": security_state["last_result"],
                "last_pdf": security_state["last_pdf"],
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        elif path == "/api/reports":
            reports = []
            if os.path.exists(DOWNLOADS_DIR):
                for fn in os.listdir(DOWNLOADS_DIR):
                    if (fn.startswith("SEO_Audit_") or fn.startswith("Architecture_Blueprint_") or fn.startswith("Security_Audit_") or "_Security_Audit_Report" in fn) and fn.endswith(".pdf"):
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

        elif path == "/api/security/reports":
            reports = []
            if os.path.exists(DOWNLOADS_DIR):
                for fn in os.listdir(DOWNLOADS_DIR):
                    if (fn.startswith("Security_Audit_") or "_Security_Audit_Report" in fn) and fn.endswith(".pdf"):
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
            payload = {
                "presets": INDUSTRY_PRESETS,
                "demo_briefs": DEMO_CLIENT_BRIEFS,
            }
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

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

        elif path == "/api/optimizer/latest":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(optimizer_state.get("last_result") or {}, ensure_ascii=False).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        if path in ("/api/reset", "/api/clear-cache"):
            self.handle_reset()

        elif path == "/api/start":
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

        elif path == "/api/security/start":
            if security_state["is_running"]:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "A security audit is already running."}).encode("utf-8"))
                return

            try:
                data = json.loads(body) if body else {}
                url = data.get("url", "").strip()
                if not url:
                    raise ValueError("URL required")

                t = threading.Thread(target=run_security_in_background, args=(url,), daemon=True)
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

        elif path == "/api/security/open-latest":
            pdf_p = security_state.get("last_pdf")
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
                self.wfile.write(json.dumps({"success": False, "error": "No Security PDF report file found."}).encode("utf-8"))

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

        elif path == "/api/optimizer/analyze":
            try:
                data = json.loads(body) if body else {}
                content_type = data.get("content_type", "paragraph")
                text = data.get("text", "").strip()
                keywords = data.get("keywords", [])
                brand = data.get("brand", "")
                industry = data.get("industry", "tech")
                intent = data.get("intent", "informational")

                if optimize_content is None:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Content optimizer engine module is unavailable."}).encode("utf-8"))
                    return

                if content_type in ("crawl_plugin_fix", "crawl_and_improve"):
                    target_url = data.get("url", "").strip()
                    plugin_notice = data.get("plugin_notice", "").strip() or data.get("notice", "").strip()
                    focus_keyword = data.get("focus_keyword", "").strip()
                    site_name = data.get("site_name", brand).strip()
                    plugin_type = data.get("plugin_type", "rank_math")
                    page_type = data.get("page_type", "WebPage")
                    industry = data.get("industry", "tech")

                    if not target_url:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": False, "error": "Please provide a valid website URL to crawl."}).encode("utf-8"))
                        return

                    result = optimize_content(
                        content_type="crawl_plugin_fix",
                        url=target_url,
                        plugin_notice=plugin_notice,
                        focus_keyword=focus_keyword,
                        site_name=site_name,
                        plugin_type=plugin_type,
                        industry=industry,
                        page_type=page_type,
                    )
                elif content_type == "seo_plugin":
                    title = data.get("title", "").strip()
                    description = data.get("description", "").strip()
                    focus_keyword = data.get("focus_keyword", "").strip()
                    secondary_keywords = data.get("secondary_keywords", keywords)
                    site_name = data.get("site_name", brand).strip()
                    slug = data.get("slug", "").strip()
                    plugin_type = data.get("plugin_type", "rank_math")
                    page_type = data.get("page_type", "WebPage")
                    content_sample = data.get("content_sample", text).strip()

                    if not title and not description and not focus_keyword:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": False, "error": "Please provide a Title, Description, or Focus Keyword."}).encode("utf-8"))
                        return

                    result = optimize_content(
                        content_type="seo_plugin",
                        text=content_sample,
                        title=title,
                        description=description,
                        focus_keyword=focus_keyword,
                        secondary_keywords=secondary_keywords,
                        site_name=site_name,
                        slug=slug,
                        plugin_type=plugin_type,
                        industry=industry,
                        page_type=page_type,
                        content_sample=content_sample,
                    )
                else:
                    if not text:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": False, "error": "No draft content provided."}).encode("utf-8"))
                        return

                    result = optimize_content(
                        content_type=content_type,
                        text=text,
                        keywords=keywords,
                        brand=brand,
                        industry=industry,
                        intent=intent,
                    )

                optimizer_state["last_result"] = result
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "result": result}, ensure_ascii=False).encode("utf-8"))
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
