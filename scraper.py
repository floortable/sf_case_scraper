import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

SF_LOGIN_URL = os.getenv("SF_LOGIN_URL", "https://login.fugagfuga.com")
SF_USERNAME = os.getenv("SF_USERNAME")
SF_PASSWORD = os.getenv("SF_PASSWORD")
SF_PROXY = os.getenv("SF_PROXY") # Example: http://user:pass@host:port
TARGET_CASE_ID = os.getenv("TARGET_CASE_ID", "500xxxxxxxxxxxx") # Default or from env
BASE_URL = os.getenv("SF_BASE_URL", "https://fugafuga.com") 
USER_DATA_DIR = os.getenv("SF_USER_DATA_DIR", "./chrome_user_data")

def login_and_scrape():
    # Note: Password might not be needed if session is persisted
    if not SF_USERNAME:
        print("Warning: SF_USERNAME not set. Relying on persistent session or manual login.")

    playwright_args = {
        "user_data_dir": USER_DATA_DIR,
        "headless": False,
        "channel": "chrome", # Try to use Google Chrome
        "args": ["--disable-blink-features=AutomationControlled"] # Attempt to reduce bot detection
    }
    
    if SF_PROXY:
        print(f"Using proxy: {SF_PROXY}")
        playwright_args["proxy"] = {"server": SF_PROXY}

    with sync_playwright() as p:
        print(f"Launching Chrome with user data dir: {USER_DATA_DIR}")
        # Use launch_persistent_context instead of launch + new_context
        try:
            context = p.chromium.launch_persistent_context(**playwright_args)
        except Exception as e:
            print(f"Failed to launch 'chrome'. Falling back to bundled chromium. Error: {e}")
            del playwright_args["channel"]
            context = p.chromium.launch_persistent_context(**playwright_args)

        page = context.pages[0] if context.pages else context.new_page()

        print(f"Navigating to {SF_LOGIN_URL}...")
        page.goto(SF_LOGIN_URL)

        # Check if already logged in (simple check: are we redirected?)
        page.wait_for_load_state("networkidle")
        if "login" in page.url:
            print("Not logged in. Attempting login...")
            if SF_USERNAME and SF_PASSWORD:
                print("Filling credentials...")
                page.fill("#username", SF_USERNAME)
                page.fill("#password", SF_PASSWORD)
                page.click("#Login")
                print("Waiting for login to complete...")
                page.wait_for_load_state("networkidle")
            else:
                print("Credentials not found. Please log in manually in the browser window.")
                # Wait for user to login manually
                page.wait_for_url(lambda u: "login" not in u, timeout=300000) # 5 min timeout
        else:
            print("Already logged in (or redirected).")

        # Navigate to specific Case URL
        target_url = f"{BASE_URL}/fuga?caseId={TARGET_CASE_ID}"
        print(f"Navigating to target Case URL: {target_url}")
        page.goto(target_url)
        
        page.wait_for_load_state("domcontentloaded")
        time.sleep(5) 
        
        # Dump page content for inspection
        output_file = "case_detail.html"
        print(f"Saving page content to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(page.content())
        
        print("Title:", page.title())
        
        # Keep browser open for a bit to verify
        time.sleep(5)
        context.close()

if __name__ == "__main__":
    login_and_scrape()
