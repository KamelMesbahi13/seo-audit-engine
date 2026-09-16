"""InersiaLab Software Department — SEO Audit Engine Web UI.

Lightweight, zero-dependency local web interface:
- Strictly NO colors (monochrome palette: black, white, gray).
- Strictly NO icons or emojis.
- Real-time audit execution log streaming.
- 1-click open and download of generated PDF reports.
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

# Global state for audit execution
audit_state = {
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


cancel_event = threading.Event()


def run_audit_in_background(target_url: str, max_pages: int, report_mode: str = "detailed"):
    global audit_state
    audit_state["is_running"] = True
    cancel_event.clear()
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
        result = agy_seo.run_audit(
            target_url,
            max_pages=effective_pages,
            report_mode=report_mode,
            cancel_check=cancel_event.is_set
        )
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

        audit_state["status"] = f"Audit complete. Overall Score: {result.get('overall_score', 0)}/100"
    except KeyboardInterrupt:
        audit_state["status"] = "Audit stopped by user."
        add_log("\n[USER ACTION] Audit cancelled and stopped successfully.\n")
    except Exception as e:
        if cancel_event.is_set():
            audit_state["status"] = "Audit stopped by user."
            add_log("\n[USER ACTION] Audit cancelled and stopped successfully.\n")
        else:
            audit_state["status"] = f"Audit failed: {e}"
            add_log(f"\n[ERROR] {e}\n")
    finally:
        audit_state["is_running"] = False
        sys.stdout = old_stdout
        sys.stderr = old_stderr


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Audit Engine — InersiaLab Software Department</title>
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
            padding: 40px 20px;
        }

        .container {
            max-width: 960px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            border-bottom: 2px solid #111827;
            padding-bottom: 16px;
            margin-bottom: 28px;
        }

        .org-label {
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: #4b5563;
            margin-bottom: 4px;
        }

        .title {
            font-size: 24px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 4px;
        }

        .subtitle {
            font-size: 13px;
            color: #6b7280;
        }

        /* Form Card */
        .card {
            border: 1px solid #111827;
            padding: 24px;
            margin-bottom: 28px;
            background: #ffffff;
        }

        .form-grid {
            display: grid;
            grid-template-columns: 1fr 140px 140px auto;
            gap: 16px;
            align-items: end;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        label {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #111827;
            margin-bottom: 6px;
        }

        input[type="text"], input[type="number"], select {
            border: 1px solid #111827;
            padding: 10px 14px;
            font-size: 14px;
            font-family: "Consolas", monospace;
            background: #ffffff;
            color: #111827;
            outline: none;
            height: 42px;
            box-sizing: border-box;
        }

        input[type="text"]:focus, input[type="number"]:focus, select:focus {
            outline: 2px solid #111827;
        }

        button {
            background: #111827;
            color: #ffffff;
            border: 1px solid #111827;
            padding: 11px 24px;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            cursor: pointer;
            display: inline-block;
        }

        button:hover {
            background: #374151;
        }

        button:disabled {
            background: #e5e7eb;
            color: #9ca3af;
            border-color: #e5e7eb;
            cursor: not-allowed;
        }

        button.btn-secondary {
            background: #ffffff;
            color: #111827;
            border: 1px solid #111827;
        }

        button.btn-secondary:hover {
            background: #f3f4f6;
        }

        /* Status & Terminal */
        .section-heading {
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #111827;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-badge {
            font-size: 12px;
            font-weight: 700;
            color: #111827;
        }

        .terminal-box {
            border: 1px solid #111827;
            background: #ffffff;
            color: #111827;
            font-family: "Consolas", monospace;
            font-size: 12px;
            line-height: 1.45;
            padding: 16px;
            height: 320px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-word;
            margin-bottom: 24px;
        }

        /* Results Card */
        .results-box {
            border: 2px solid #111827;
            padding: 20px 24px;
            margin-bottom: 28px;
            display: none;
        }

        .score-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 14px;
            margin-bottom: 16px;
        }

        .score-number {
            font-size: 32px;
            font-weight: 800;
            color: #111827;
        }

        .btn-group {
            display: flex;
            gap: 12px;
            margin-top: 12px;
            flex-wrap: wrap;
        }

        /* Recent Reports List */
        .reports-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 10px;
        }

        .reports-table th, .reports-table td {
            border: 1px solid #e5e7eb;
            padding: 8px 12px;
            text-align: left;
        }

        .reports-table th {
            background: #ffffff;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #111827;
        }

        .reports-table a {
            color: #111827;
            font-weight: 700;
            text-decoration: underline;
            cursor: pointer;
        }

        .footer {
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="org-label">INERSIALAB SOFTWARE DEPARTMENT</div>
            <div class="title">SEO Audit Engine</div>
            <div class="subtitle">Antigravity Native Technical & Generative Engine Optimization (GEO) Audit Toolkit</div>
        </div>

        <!-- Configuration Form -->
        <div class="card">
            <form id="auditForm" onsubmit="event.preventDefault(); startAudit(event); return false;">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="urlInput">Target Website URL</label>
                        <input type="text" id="urlInput" placeholder="https://example.com/" required value="https://" onkeydown="if(event.key === 'Enter'){event.preventDefault();startAudit(event);}">
                    </div>
                    <div class="form-group">
                        <label for="pagesInput">Scope (0=All)</label>
                        <input type="number" id="pagesInput" value="0" min="0" max="50000" required onkeydown="if(event.key === 'Enter'){event.preventDefault();startAudit(event);}">
                    </div>
                    <div class="form-group">
                        <label for="modeInput">Report Mode</label>
                        <select id="modeInput">
                            <option value="short" selected>Short (Recommended, ~17 pgs)</option>
                            <option value="detailed">Detailed (Full Breakdown)</option>
                            <option value="both">Both</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: flex-end;">
                        <button type="button" id="btnStart" onclick="startAudit(event)" style="flex: 1;">START AUDIT</button>
                        <button type="button" id="btnStop" class="btn-secondary" onclick="stopAudit()" disabled style="color: #b91c1c; border-color: #b91c1c; font-weight: 700; padding: 10px 14px;">STOP</button>
                    </div>
                </div>
            </form>
        </div>

        <!-- Audit Results Box -->
        <div class="results-box" id="resultsBox">
            <div class="score-row">
                <div>
                    <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #4b5563;">Overall Audit Score</div>
                    <div class="score-number" id="overallScoreText">--/100</div>
                    <div id="targetDomainText" style="font-size: 13px; color: #4b5563; margin-top: 2px;">Domain: --</div>
                </div>
                <div class="btn-group">
                    <button type="button" id="btnOpenPdf" onclick="openLatestPdf()">OPEN PDF REPORT</button>
                    <button type="button" class="btn-secondary" onclick="openDownloadsFolder()">OPEN DOWNLOADS</button>
                </div>
            </div>
            <div id="categoriesGrid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 12px;"></div>
        </div>

        <!-- Execution Terminal -->
        <div class="section-heading">
            <span>Execution Terminal</span>
            <span class="status-badge" id="statusBadge">Status: Ready</span>
        </div>
        <div class="terminal-box" id="terminal">Waiting for audit initiation...</div>

        <div style="display: flex; justify-content: flex-end; margin-bottom: 32px;">
            <button type="button" class="btn-secondary" onclick="clearTerminal()" style="padding: 6px 14px; font-size: 11px;">CLEAR TERMINAL</button>
        </div>

        <!-- Recent Audit Reports in Downloads -->
        <div class="section-heading">
            <span>Recent PDF Reports in Downloads</span>
            <button type="button" class="btn-secondary" onclick="fetchReports()" style="padding: 4px 10px; font-size: 11px;">REFRESH</button>
        </div>
        <table class="reports-table">
            <thead>
                <tr>
                    <th>Report File</th>
                    <th style="width: 140px;">Date Generated</th>
                    <th style="width: 100px;">File Size</th>
                    <th style="width: 120px; text-align: center;">Action</th>
                </tr>
            </thead>
            <tbody id="reportsBody">
                <tr>
                    <td colspan="4" style="text-align: center; color: #6b7280; padding: 14px;">Loading reports...</td>
                </tr>
            </tbody>
        </table>

        <div class="footer">
            <div>Report generated by the Software Department of InersiaLab</div>
            <div>Official Executive Toolkit &bull; All Rights Reserved</div>
        </div>
    </div>

    <script>
        let pollTimer = null;

        function appendLog(text) {
            const terminal = document.getElementById("terminal");
            terminal.textContent += text;
            terminal.scrollTop = terminal.scrollHeight;
        }

        function clearTerminal() {
            document.getElementById("terminal").textContent = "";
        }

        async function startAudit(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }
            let url = document.getElementById("urlInput").value.trim();
            const pages = parseInt(document.getElementById("pagesInput").value, 10) || 0;
            const mode = document.getElementById("modeInput").value || "short";

            if (!url || url === "https://" || url === "http://") {
                alert("Please enter a valid website URL (e.g. https://example.com).");
                return false;
            }

            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "https://" + url;
                document.getElementById("urlInput").value = url;
            }

            document.getElementById("btnStart").disabled = true;
            document.getElementById("btnStop").disabled = false;
            document.getElementById("btnStop").textContent = "STOP";
            document.getElementById("statusBadge").textContent = "Status: Auditing in progress...";
            document.getElementById("resultsBox").style.display = "none";
            clearTerminal();
            const scopeDesc = (pages === 0) ? "All Pages (Unlimited)" : (pages + " pages");
            appendLog("--- Initializing SEO Audit for: " + url + " (" + scopeDesc + ") [" + mode.toUpperCase() + " mode] ---" + String.fromCharCode(10, 10));

            try {
                const res = await fetch("/api/start", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: url, max_pages: pages, mode: mode })
                });
                const data = await res.json();
                if (data.status === "started") {
                    startPolling();
                } else {
                    alert("Failed to start: " + (data.error || "Unknown error"));
                    document.getElementById("btnStart").disabled = false;
                    document.getElementById("btnStop").disabled = true;
                }
            } catch (err) {
                alert("Network error: " + err.message);
                document.getElementById("btnStart").disabled = false;
                document.getElementById("btnStop").disabled = true;
            }
            return false;
        }

        async function stopAudit() {
            try {
                const btnStop = document.getElementById("btnStop");
                btnStop.disabled = true;
                btnStop.textContent = "STOPPING...";
                await fetch("/api/stop", { method: "POST" });
            } catch (err) {
                console.error("Stop error:", err);
            }
        }

        function startPolling() {
            if (pollTimer) clearInterval(pollTimer);
            pollTimer = setInterval(pollStatus, 1500);
        }

        async function pollStatus() {
            try {
                const res = await fetch("/api/status");
                const data = await res.json();

                document.getElementById("statusBadge").textContent = "Status: " + data.status;
                const terminal = document.getElementById("terminal");
                if (data.logs && data.logs.length > 0) {
                    terminal.textContent = data.logs.join("");
                    terminal.scrollTop = terminal.scrollHeight;
                }

                if (data.is_running) {
                    document.getElementById("btnStart").disabled = true;
                    document.getElementById("btnStop").disabled = false;
                } else {
                    clearInterval(pollTimer);
                    pollTimer = null;
                    document.getElementById("btnStart").disabled = false;
                    document.getElementById("btnStop").disabled = true;
                    document.getElementById("btnStop").textContent = "STOP";

                    if (data.last_result) {
                        displayResult(data.last_result);
                    }
                    fetchReports();
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }

        function displayResult(result) {
            const resultsBox = document.getElementById("resultsBox");
            resultsBox.style.display = "block";
            document.getElementById("overallScoreText").textContent = result.overall_score + "/100";
            document.getElementById("targetDomainText").textContent = "Domain: " + result.domain + " • Crawled: " + result.pages_crawled + " pages";

            const categoriesGrid = document.getElementById("categoriesGrid");
            categoriesGrid.innerHTML = "";
            if (result.site_scores) {
                for (const [cat, score] of Object.entries(result.site_scores)) {
                    const box = document.createElement("div");
                    box.style.border = "1px solid #e5e7eb";
                    box.style.padding = "10px";
                    box.style.background = "#ffffff";
                    box.innerHTML = '<div style="font-size: 10px; text-transform: uppercase; font-weight: 700; color: #4b5563;">' + cat + '</div>' +
                                    '<div style="font-size: 18px; font-weight: 800; color: #111827; margin-top: 4px;">' + score + '/100</div>';
                    categoriesGrid.appendChild(box);
                }
            }
        }

        async function openLatestPdf() {
            try {
                const res = await fetch("/api/open-latest", { method: "POST" });
                const data = await res.json();
                if (!data.success) {
                    alert(data.error || "Could not open PDF file.");
                }
            } catch (err) {
                alert("Error: " + err.message);
            }
        }

        async function openFile(filename) {
            try {
                const res = await fetch("/api/open-file", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename: filename })
                });
                const data = await res.json();
                if (!data.success) {
                    alert(data.error || "Could not open file.");
                }
            } catch (err) {
                alert("Error: " + err.message);
            }
        }

        async function openDownloadsFolder() {
            try {
                await fetch("/api/open-folder", { method: "POST" });
            } catch (err) {
                alert("Error: " + err.message);
            }
        }

        async function fetchReports() {
            try {
                const res = await fetch("/api/reports");
                const data = await res.json();
                const tbody = document.getElementById("reportsBody");
                tbody.innerHTML = "";

                if (!data.reports || data.reports.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #6b7280; padding: 14px;">No PDF audit reports found in Downloads.</td></tr>';
                    return;
                }

                data.reports.forEach(r => {
                    const row = document.createElement("tr");

                    const tdName = document.createElement("td");
                    tdName.innerHTML = "<strong>" + r.filename + "</strong>";
                    row.appendChild(tdName);

                    const tdDate = document.createElement("td");
                    tdDate.style.color = "#4b5563";
                    tdDate.textContent = r.date;
                    row.appendChild(tdDate);

                    const tdSize = document.createElement("td");
                    tdSize.style.color = "#4b5563";
                    tdSize.textContent = r.size;
                    row.appendChild(tdSize);

                    const tdAction = document.createElement("td");
                    tdAction.style.textAlign = "center";
                    const btn = document.createElement("button");
                    btn.type = "button";
                    btn.className = "btn-secondary";
                    btn.style.padding = "3px 8px";
                    btn.style.fontSize = "11px";
                    btn.textContent = "OPEN PDF";
                    btn.onclick = function() { openFile(r.filename); };
                    tdAction.appendChild(btn);
                    row.appendChild(tdAction);

                    tbody.appendChild(row);
                });
            } catch (err) {
                console.error("Failed to load reports:", err);
            }
        }

        // Initial reports fetch
        fetchReports();
    </script>
</body>
</html>
"""


class SEOHttpHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default HTTP server console noise
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
                    if fn.startswith("SEO_Audit_") and fn.endswith(".pdf"):
                        full_p = os.path.join(DOWNLOADS_DIR, fn)
                        stat = os.stat(full_p)
                        size_kb = round(stat.st_size / 1024, 1)
                        dt = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        reports.append({
                            "filename": fn,
                            "date": dt,
                            "size": f"{size_kb} KB",
                            "mtime": stat.st_mtime,
                        })
                reports.sort(key=lambda x: x["mtime"], reverse=True)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reports": reports[:25]}).encode("utf-8"))

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
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif path == "/api/stop":
            if audit_state["is_running"]:
                cancel_event.set()
                audit_state["status"] = "Stopping audit..."
                add_log("\n[STOP REQUEST] Immediate cancellation requested by user. Terminating audit...\n")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "stopping"}).encode("utf-8"))
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "not_running"}).encode("utf-8"))

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

        else:
            self.send_response(404)
            self.end_headers()


def start_server(preferred_port=8765):
    import socket
    httpd = None
    port = preferred_port
    for p in range(preferred_port, preferred_port + 20):
        try:
            server_address = ("127.0.0.1", p)
            httpd = HTTPServer(server_address, SEOHttpHandler)
            httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = p
            break
        except OSError:
            continue

    if not httpd:
        print(f"[ERROR] Could not bind to any port in range {preferred_port}-{preferred_port+20}")
        sys.exit(1)

    url = f"http://127.0.0.1:{port}"
    print(f"============================================================")
    print(f"  InersiaLab Software Department — SEO Audit Engine")
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
