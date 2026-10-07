import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    artifacts_dir = r"C:\Users\EL ASSLI HI TECH\.gemini\antigravity-ide\brain\02583bd4-f8bb-476e-8dec-9b029f99a72d"
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1080})
        
        print("Navigating to http://127.0.0.1:8765/ ...")
        page.goto("http://127.0.0.1:8765/", wait_until="networkidle", timeout=30000)
        
        # Switch to Tab 4: Optimizer
        print("Switching to Tab 4...")
        page.click("#nav-btn-optimizer")
        page.wait_for_timeout(1000)
        
        # Take screenshot of Tab 4 default view
        screenshot1 = os.path.join(artifacts_dir, "opt_crawl_mode_initial.png")
        page.screenshot(path=screenshot1, full_page=False)
        print(f"Initial Tab 4 screenshot saved: {screenshot1}")
        
        # Click on InersiaLab demo preset
        print("Clicking InersiaLab demo preset...")
        page.click("button:has-text('InersiaLab (Rank Math Notice Demo)')")
        page.wait_for_timeout(500)
        
        # Check that URL and notice inputs were populated
        url_val = page.input_value("#opt-crawl-url")
        notice_val = page.input_value("#opt-crawl-notice")
        print(f"URL populated: {url_val}")
        print(f"Notice length: {len(notice_val)} characters")
        
        # Click Crawl & Improve button
        print("Clicking 'CRAWL PAGE & GENERATE SIDE-BY-SIDE IMPROVEMENTS' button...")
        page.click("#btn-run-crawl-improver")
        
        # Wait for results wrapper to be visible
        print("Waiting for #opt-crawl-results-wrapper to appear...")
        page.wait_for_selector("#opt-crawl-results-wrapper", state="visible", timeout=30000)
        page.wait_for_timeout(2000)
        
        # Take screenshot of results
        screenshot2 = os.path.join(artifacts_dir, "opt_crawl_results_top.png")
        page.screenshot(path=screenshot2, full_page=False)
        print(f"Results top screenshot saved: {screenshot2}")
        
        # Scroll down to side-by-side comparison cards
        print("Scrolling down to side-by-side comparison grid...")
        page.evaluate("window.scrollBy(0, 700)")
        page.wait_for_timeout(1000)
        
        screenshot3 = os.path.join(artifacts_dir, "opt_crawl_side_by_side_diff.png")
        page.screenshot(path=screenshot3, full_page=False)
        print(f"Side-by-side diff screenshot saved: {screenshot3}")
        
        # Test copy button on first improved element
        copy_buttons = page.query_selector_all("#opt-crawl-results-wrapper button:has-text('COPY IMPROVED TEXT')")
        print(f"Found {len(copy_buttons)} copy buttons on improved elements.")
        if copy_buttons:
            copy_buttons[0].click()
            page.wait_for_timeout(500)
            btn_text = copy_buttons[0].inner_text()
            print(f"Copy button text after click: '{btn_text}'")
            
        # Scroll to turnkey WordPress export box
        page.evaluate("window.scrollBy(0, 1200)")
        page.wait_for_timeout(1000)
        
        screenshot4 = os.path.join(artifacts_dir, "opt_crawl_turnkey_export.png")
        page.screenshot(path=screenshot4, full_page=False)
        print(f"Turnkey export screenshot saved: {screenshot4}")
        
        # Test File Upload feature
        test_file_path = os.path.join(artifacts_dir, "scratch", "sample_plugin_notice.txt")
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("Rank Math Notice Export:\n- Add Focus Keyword to SEO Title.\n- Focus Keyword not in first 10% of content.\n- Content is 120 words.")
            
        print("Testing file upload...")
        file_input = page.locator("#opt-crawl-file-input")
        file_input.set_input_files(test_file_path)
        page.wait_for_timeout(800)
        
        uploaded_notice = page.input_value("#opt-crawl-notice")
        print("Notice textarea after file upload:")
        print(uploaded_notice[:100] + "...")
        
        browser.close()
        print("Browser verification test completed successfully!")

if __name__ == "__main__":
    main()
