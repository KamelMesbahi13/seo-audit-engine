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

def capture_all():
    exe_path = find_browser_executable()
    print(f"Using browser executable: {exe_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe_path, headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 920}, device_scale_factor=1.5)
        page = context.new_page()

        print("Navigating to http://127.0.0.1:8765/ ...")
        page.goto("http://127.0.0.1:8765/", wait_until="networkidle")
        time.sleep(1)

        # 1. Tab 1: Existing Website Audit
        page.screenshot(path="scratch/apple_tab1_audit_polished.png", full_page=False)
        print("Captured Tab 1 polished.")

        # 2. Tab 2: Blueprint
        page.click("#nav-btn-blueprint")
        time.sleep(0.6)
        page.screenshot(path="scratch/apple_tab2_blueprint_polished.png", full_page=False)
        print("Captured Tab 2 polished.")

        # 3. Tab 3: Content Architect
        page.click("#nav-btn-content")
        time.sleep(0.6)
        page.screenshot(path="scratch/apple_tab3_content_polished.png", full_page=False)
        print("Captured Tab 3 polished.")

        # 4. Tab 4: SEO & GEO Optimizer
        page.click("#nav-btn-optimizer")
        time.sleep(0.6)
        # Click InersiaLab demo preset
        page.click("button:has-text('InersiaLab (Rank Math Notice Demo)')")
        time.sleep(0.5)
        page.screenshot(path="scratch/apple_tab4_optimizer_form.png", full_page=False)
        print("Captured Tab 4 form.")

        # Click Crawl Page & Generate Improvements
        print("Triggering crawl in Tab 4...")
        page.click("#btn-run-crawl-improver")
        # Wait for results wrapper to become visible
        try:
            page.wait_for_selector("#opt-crawl-results-wrapper > div", timeout=15000)
            time.sleep(1)
            # Scroll slightly to results
            page.evaluate("window.scrollTo(0, 480)")
            time.sleep(0.5)
            page.screenshot(path="scratch/apple_tab4_side_by_side_results.png", full_page=False)
            print("Captured Tab 4 side-by-side results!")
        except Exception as e:
            print("Notice crawl timeout or error:", e)

        # 5. Tab 5: Cybersecurity & Server Hardening
        page.click("#nav-btn-security")
        time.sleep(0.6)
        page.screenshot(path="scratch/apple_tab5_security_polished.png", full_page=False)
        print("Captured Tab 5 polished.")

        browser.close()
        print("Done capturing all screenshots.")

if __name__ == "__main__":
    capture_all()
