"""InersiaLab Software Department — SEO Audit Engine Desktop GUI.

Minimalist, executive desktop user interface:
- Strictly NO colors (monochrome palette: black, white, neutral gray).
- Strictly NO icons or emojis.
- Real-time progress and log streaming.
- 1-click open of generated PDF reports and Downloads folder.
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
        self.root.title("InersiaLab — SEO Audit Engine")
        self.root.geometry("820x680")
        self.root.minsize(720, 560)
        self.root.configure(bg="#ffffff")

        self.log_queue = queue.Queue()
        self.audit_thread = None
        self.is_running = False
        self.last_pdf_path = None

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

    def _build_ui(self):
        # Top Header Frame
        header_frame = tk.Frame(self.root, bg="#ffffff", padx=24, pady=16)
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
            text="SEO Audit Engine",
            font=("Segoe UI", 18, "bold"),
            fg="#111827",
            bg="#ffffff"
        )
        title_label.pack(anchor="w", pady=(2, 0))

        subtitle_label = tk.Label(
            header_frame,
            text="Technical, On-Page, Schema, Performance, and Generative AI (GEO) Audit",
            font=("Segoe UI", 9),
            fg="#6b7280",
            bg="#ffffff"
        )
        subtitle_label.pack(anchor="w", pady=(2, 8))

        # Thin monochrome separator rule
        rule = tk.Frame(header_frame, height=1, bg="#e5e7eb")
        rule.pack(fill=tk.X, pady=(4, 0))

        # Configuration & Inputs Frame
        inputs_frame = tk.Frame(self.root, bg="#ffffff", padx=24, pady=12)
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
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", ipady=6, padx=(0, 16))

        # Max Pages Input
        pages_label = tk.Label(
            inputs_frame,
            text="Crawl Scope (Pages)",
            font=("Segoe UI", 9, "bold"),
            fg="#111827",
            bg="#ffffff"
        )
        pages_label.grid(row=0, column=2, sticky="w", pady=(0, 4))

        self.pages_var = tk.StringVar(value="10")
        self.pages_entry = tk.Entry(
            inputs_frame,
            textvariable=self.pages_var,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1,
            width=12,
            highlightthickness=0
        )
        self.pages_entry.grid(row=1, column=2, sticky="w", ipady=6, padx=(0, 16))

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
            padx=18,
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
            padx=14,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.stop_audit
        )
        self.btn_stop.pack(side=tk.LEFT)

        inputs_frame.columnconfigure(0, weight=1)

        # Status & Progress Frame
        status_frame = tk.Frame(self.root, bg="#ffffff", padx=24, pady=8)
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

        # Console / Activity Log Frame
        log_frame = tk.Frame(self.root, bg="#ffffff", padx=24, pady=6)
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
            font=("Consolas", 9),
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1,
            wrap=tk.WORD,
            highlightthickness=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Bottom Actions Frame (Results & Links)
        bottom_frame = tk.Frame(self.root, bg="#ffffff", padx=24, pady=16)
        bottom_frame.pack(fill=tk.X)

        self.btn_open_pdf = tk.Button(
            bottom_frame,
            text="OPEN PDF REPORT",
            font=("Segoe UI", 9, "bold"),
            bg="#111827",
            fg="#ffffff",
            activebackground="#374151",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=16,
            pady=7,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.open_pdf
        )
        self.btn_open_pdf.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_open_folder = tk.Button(
            bottom_frame,
            text="OPEN DOWNLOADS FOLDER",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#111827",
            activebackground="#f3f4f6",
            activeforeground="#111827",
            relief="solid",
            bd=1,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.open_downloads_folder
        )
        self.btn_open_folder.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_clear_log = tk.Button(
            bottom_frame,
            text="CLEAR LOG",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#6b7280",
            activebackground="#f3f4f6",
            activeforeground="#111827",
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.clear_log
        )
        self.btn_clear_log.pack(side=tk.RIGHT)

    def _poll_log_queue(self):
        """Reads messages from stdout queue and appends them to ScrolledText."""
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)

                # Check if message contains output report path
                if "PDF Report:" in msg or "Report:" in msg:
                    for line in msg.split("\n"):
                        if "Report:" in line and ".pdf" in line:
                            path = line.split("Report:")[-1].strip()
                            if os.path.exists(path):
                                self.last_pdf_path = path
                                self.btn_open_pdf.config(state=tk.NORMAL)
            except queue.Empty:
                break
        self.root.after(100, self._poll_log_queue)

    def start_audit(self):
        url = self.url_var.get().strip()
        if not url or url in ("http://", "https://"):
            messagebox.showwarning("Input Required", "Please enter a valid target URL to audit.")
            return

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            self.url_var.set(url)

        try:
            pages = int(self.pages_var.get().strip())
            if pages <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Invalid Input", "Crawl Scope must be a positive number (e.g. 10).")
            return

        self.is_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL, fg="#111827")
        self.btn_open_pdf.config(state=tk.DISABLED)
        self.status_var.set(f"Status: Auditing {url} (Crawling up to {pages} pages)...")
        self.progress_bar.start(10)

        self.log_text.insert(tk.END, f"\n--- Starting Audit: {url} ({pages} pages) ---\n\n")
        self.log_text.see(tk.END)

        self.audit_thread = threading.Thread(target=self._run_audit_thread, args=(url, pages), daemon=True)
        self.audit_thread.start()

    def _run_audit_thread(self, url, pages):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = StdoutRedirector(self.log_queue)

        try:
            sys.stdout = redirector
            sys.stderr = redirector

            import agy_seo
            result = agy_seo.run_audit(url, max_pages=pages)
            score = result.get("overall_score", 0)

            # Look up newest generated PDF in Downloads
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            domain = result.get("domain", "").replace(".", "_").replace(":", "_")
            candidates = [
                os.path.join(downloads, f) for f in os.listdir(downloads)
                if f.startswith(f"SEO_Audit_{domain}") and f.endswith(".pdf")
            ]
            if candidates:
                candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                self.last_pdf_path = candidates[0]

            self.root.after(0, self._on_audit_success, score)
        except Exception as e:
            self.root.after(0, self._on_audit_failure, str(e))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _on_audit_success(self, score):
        self.is_running = False
        self.progress_bar.stop()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED, fg="#6b7280")
        self.status_var.set(f"Status: Audit completed successfully. Overall Score: {score}/100")
        if self.last_pdf_path and os.path.exists(self.last_pdf_path):
            self.btn_open_pdf.config(state=tk.NORMAL)

    def _on_audit_failure(self, error_msg):
        self.is_running = False
        self.progress_bar.stop()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED, fg="#6b7280")
        self.status_var.set(f"Status: Audit encountered an error: {error_msg}")
        self.log_queue.put(f"\n[ERROR] Audit failed: {error_msg}\n")

    def stop_audit(self):
        if self.is_running:
            self.status_var.set("Status: Stop requested (process will terminate after current page)")
            self.is_running = False
            self.btn_stop.config(state=tk.DISABLED, fg="#6b7280")

    def open_pdf(self):
        if self.last_pdf_path and os.path.exists(self.last_pdf_path):
            try:
                os.startfile(self.last_pdf_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF report:\n{e}")
        else:
            messagebox.showinfo("Report Not Found", "No PDF report file found for the latest audit.")

    def open_downloads_folder(self):
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(downloads):
            try:
                os.startfile(downloads)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open Downloads folder:\n{e}")

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)


def main():
    root = tk.Tk()
    app = SEOAuditApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
