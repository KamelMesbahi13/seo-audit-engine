import os
import sys
import time
from playwright.sync_api import sync_playwright

def find_browser_executable():
    win_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p
    return None

def capture_sections():
    exe_path = find_browser_executable()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe_path, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, device_scale_factor=1.5)
        page = context.new_page()

        page.goto("http://127.0.0.1:8765/", wait_until="networkidle")
        time.sleep(1)

        page.click("#nav-btn-optimizer")
        time.sleep(0.5)

        page.fill("#opt-crawl-url", "https://www.inersialab.com/Programmes")
        notice_text = """- Focus Keyword not found in the URL permalink
- Focus Keyword does not appear in the first 10% of the content.
- Use Focus Keyword in subheadings like H2, H3.
- Content is 220 words long. Consider using at least 600 words."""
        page.fill("#opt-crawl-notice", notice_text)
        page.click("#btn-run-crawl-improver")

        page.wait_for_selector("#opt-crawl-results-wrapper .opt-side-by-side-grid", timeout=25000)
        time.sleep(1.5)

        # Scroll to Section 1 & 2
        page.evaluate("window.scrollTo(0, 3100)")
        time.sleep(0.5)
        page.screenshot(path="scratch/screenshots/05_sections_1_and_2.png")

        # Scroll to Section 3 & 4
        page.evaluate("window.scrollTo(0, 4200)")
        time.sleep(0.5)
        page.screenshot(path="scratch/screenshots/06_sections_3_and_4.png")

        browser.close()
        print("Captured sections 1, 2, 3, and 4 screenshots successfully!")

if __name__ == "__main__":
    capture_sections()
