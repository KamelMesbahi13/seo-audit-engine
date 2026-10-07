import os
import sys
import time
from playwright.sync_api import sync_playwright

def find_browser_executable():
    playwright_paths = [
        os.path.expanduser('~/.gemini/config/skills/claude-seo/ms-playwright'),
        os.path.expanduser('~/.claude/skills/seo/ms-playwright'),
    ]
    for pw_path in playwright_paths:
        if os.path.exists(pw_path):
            for dirpath, dirnames, filenames in os.walk(pw_path):
                for fn in filenames:
                    if fn in ('chrome.exe', 'chromium.exe'):
                        return os.path.join(dirpath, fn)
    win_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p
    return None

def capture_side_by_side():
    exe_path = find_browser_executable()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe_path, headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 1100}, device_scale_factor=1.5)
        page = context.new_page()

        page.goto("http://127.0.0.1:8765/", wait_until="networkidle")
        time.sleep(1)

        # Tab 4
        page.click("#nav-btn-optimizer")
        time.sleep(0.5)
        page.click("button:has-text('InersiaLab (Rank Math Notice Demo)')")
        time.sleep(0.5)
        page.click("#btn-run-crawl-improver")
        page.wait_for_selector("#opt-crawl-results-wrapper > div", timeout=15000)
        time.sleep(1)

        # Scroll to Side-by-Side comparison cards
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(0.5)
        page.screenshot(path="scratch/apple_side_by_side_cards.png", full_page=False)

        # Scroll to Rank Math turnkey box
        page.evaluate("window.scrollTo(0, 1600)")
        time.sleep(0.5)
        page.screenshot(path="scratch/apple_rankmath_export_box.png", full_page=False)

        # Click the Reset button in the header to capture the Apple blur glass toast!
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        page.click("#btn-global-reset")
        time.sleep(0.3)
        page.screenshot(path="scratch/apple_reset_toast_active.png", full_page=False)

        browser.close()
        print("Captured side-by-side cards, export box, and reset toast!")

if __name__ == "__main__":
    capture_side_by_side()
