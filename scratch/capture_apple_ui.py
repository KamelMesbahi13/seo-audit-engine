import os
import sys
import time
from playwright.sync_api import sync_playwright

def find_browser_executable():
    # 1. Check local Playwright paths in Claude / Gemini skills
    playwright_paths = [
        os.path.expanduser('~/.gemini/config/skills/claude-seo/ms-playwright'),
        os.path.expanduser('~/.claude/skills/seo/ms-playwright'),
    ]
    for pw_path in playwright_paths:
        if os.path.exists(pw_path):
            for dirpath, dirnames, filenames in os.walk(pw_path):
                for fn in filenames:
                    if fn in ('chrome.exe', 'chromium.exe', 'headless_shell.exe'):
                        return os.path.join(dirpath, fn)
    # 2. Check standard Edge / Chrome paths
    win_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p
    return None

def capture_ui():
    exe_path = find_browser_executable()
    print(f"Using browser executable: {exe_path}")

    with sync_playwright() as p:
        launch_kwargs = {"headless": True}
        if exe_path:
            launch_kwargs["executable_path"] = exe_path
        else:
            launch_kwargs["channel"] = "msedge"

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(viewport={"width": 1400, "height": 900}, device_scale_factor=1.5)
        page = context.new_page()

        print("Navigating to http://127.0.0.1:8765/ ...")
        page.goto("http://127.0.0.1:8765/", wait_until="networkidle")
        time.sleep(1)

        # 1. Capture Header & Tab 1 (Existing Website Audit)
        page.screenshot(path="scratch/apple_ui_tab1_audit.png", full_page=False)
        print("Captured Tab 1 Audit.")

        # 2. Switch to Tab 2 (Blueprint)
        page.click("#nav-btn-blueprint")
        time.sleep(0.5)
        page.screenshot(path="scratch/apple_ui_tab2_blueprint.png", full_page=False)
        print("Captured Tab 2 Blueprint.")

        # 3. Switch to Tab 4 (Optimizer)
        page.click("#nav-btn-optimizer")
        time.sleep(0.5)
        page.screenshot(path="scratch/apple_ui_tab4_optimizer.png", full_page=False)
        print("Captured Tab 4 Optimizer.")

        # Crawl & Improve Notice subtab in Tab 4
        page.click("#subnav-btn-crawl-improve")
        time.sleep(0.5)
        page.screenshot(path="scratch/apple_ui_tab4_crawl_mode.png", full_page=False)
        print("Captured Tab 4 Crawl & Improve Subtab.")

        # 4. Switch to Tab 5 (Cybersecurity)
        page.click("#nav-btn-security")
        time.sleep(0.5)
        page.screenshot(path="scratch/apple_ui_tab5_security.png", full_page=False)
        print("Captured Tab 5 Cybersecurity.")

        browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    capture_ui()
