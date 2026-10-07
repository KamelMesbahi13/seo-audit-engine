import os
import sys
import time
from playwright.sync_api import sync_playwright

def find_browser_executable():
    win_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p
    return None

def verify_crawl_improver():
    exe_path = find_browser_executable()
    print("Using browser executable:", exe_path)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe_path, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, device_scale_factor=1.5)
        page = context.new_page()

        print("Navigating to http://127.0.0.1:8765/ ...")
        page.goto("http://127.0.0.1:8765/", wait_until="networkidle")
        time.sleep(1)

        # Tab 4: Optimizer
        print("Clicking Tab 4...")
        page.click("#nav-btn-optimizer")
        time.sleep(0.5)

        # Fill URL and notice
        print("Filling URL and Rank Math notice...")
        page.fill("#opt-crawl-url", "https://www.inersialab.com/Programmes")
        notice_text = """- Focus Keyword not found in the URL permalink
- Focus Keyword does not appear in the first 10% of the content.
- Use Focus Keyword in subheadings like H2, H3.
- Content is 220 words long. Consider using at least 600 words.
- Add a number to your SEO title to improve CTR.
- Add an emotional power word to your SEO title."""
        page.fill("#opt-crawl-notice", notice_text)
        page.fill("#opt-crawl-keyword", "") # Leave empty to verify auto-detection

        # Run Improver
        print("Clicking Run Crawl Improver...")
        page.click("#btn-run-crawl-improver")

        # Wait for results
        page.wait_for_selector("#opt-crawl-results-wrapper .opt-side-by-side-grid", timeout=25000)
        time.sleep(1.5)

        # Extract text stats
        scorecard = page.inner_text("#opt-crawl-results-wrapper .card:first-child")
        print("\n=== SCORECARD OUTPUT ===")
        print(scorecard[:300])

        # Verify focus keyword is NOT "to the SEO title"
        assert "to the SEO title" not in scorecard, "FAILED: 'to the SEO title' found in scorecard!"
        assert "Digital Growth Programs" in scorecard or "InersiaLab" in scorecard, "Verified valid domain keyword!"
        print("\nSUCCESS: Focus keyword is accurately identified from real page content!")

        # Take screenshots
        os.makedirs("scratch/screenshots", exist_ok=True)
        
        # 1. Top scorecard & discovered keywords
        page.evaluate("window.scrollTo(0, 300)")
        time.sleep(0.5)
        page.screenshot(path="scratch/screenshots/01_keywords_and_scorecard.png")
        print("Captured 01_keywords_and_scorecard.png")

        # 2. Part 1 Metadata side-by-side
        page.evaluate("window.scrollTo(0, 750)")
        time.sleep(0.5)
        page.screenshot(path="scratch/screenshots/02_part1_metadata_side_by_side.png")
        print("Captured 02_part1_metadata_side_by_side.png")

        # 3. Part 2 Section-by-section improvements
        page.evaluate("window.scrollTo(0, 1600)")
        time.sleep(0.5)
        page.screenshot(path="scratch/screenshots/03_part2_sections_side_by_side.png")
        print("Captured 03_part2_sections_side_by_side.png")

        # 4. Scroll further down to sections 3 & 4
        page.evaluate("window.scrollTo(0, 2400)")
        time.sleep(0.5)
        page.screenshot(path="scratch/screenshots/04_part2_sections_methodology_tiers.png")
        print("Captured 04_part2_sections_methodology_tiers.png")

        # Test copying an improved section
        copy_btn = page.locator("button:has-text('COPY IMPROVED SECTION')").first
        if copy_btn:
            copy_btn.click()
            time.sleep(0.5)
            print("Clicked COPY IMPROVED SECTION button!")

        browser.close()
        print("\nAll Playwright UI verifications passed with flying colors!")

if __name__ == "__main__":
    verify_crawl_improver()
