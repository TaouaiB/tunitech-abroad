from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto("http://127.0.0.1:8021/jobs/")
        page.wait_for_selector(".mobile-sort-button")
        
        # Click the custom mobile sort button to open the menu
        page.click(".mobile-sort-button")
        page.wait_for_timeout(500)
        
        # Take screenshot of the opened custom sort menu
        page.screenshot(path="docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_mobile_repairs_screenshots/jobs_mobile_custom_sort_fixed.png")
        
        context.close()
        browser.close()

if __name__ == "__main__":
    run()
