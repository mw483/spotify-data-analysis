from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta

def generate_date_list(start_date, end_date):
    """Generate list of dates between start_date and end_date (inclusive)"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates

def setup_driver():
    """Initialize Chrome driver"""
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome driver initialized successfully")
        return driver
    except Exception as e:
        print(f"❌ Error initializing driver: {e}")
        return None

def download_csv_for_date(driver, date, is_first_run=False):
    """Download CSV for a specific date"""
    url = f"https://charts.spotify.com/charts/view/regional-global-daily/{date}"
    
    print(f"\n📅 Processing date: {date}")
    print(f"🌐 Navigating to: {url}")
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Only handle login on first run
        if is_first_run:
            current_url = driver.current_url
            if "accounts.spotify.com" in current_url or "login" in current_url:
                print("🔐 Login required. Please log in manually.")
                input("After logging in, press Enter to continue...")
                
                # Navigate to the URL again after login
                driver.get(url)
                time.sleep(5)
        
        # Look for CSV download button
        print("🔍 Looking for CSV download button...")
        
        wait = WebDriverWait(driver, 15)
        selectors_to_try = [
            "button[aria-labelledby='csv_download']",
            "button.Button-sc-1dqy6lx-0.jlmwLy",
            "button[data-encore-id='buttonTertiary']"
        ]
        
        button_found = False
        for i, selector in enumerate(selectors_to_try):
            try:
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                # Scroll to button and click
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(2)
                button.click()
                
                print(f"✅ CSV downloaded for {date}")
                button_found = True
                break
                
            except Exception as e:
                if i < len(selectors_to_try) - 1:
                    continue
                else:
                    print(f"❌ Could not find download button for {date}: {e}")
        
        if button_found:
            time.sleep(3)  # Wait for download to start
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error processing {date}: {e}")
        return False

def main():
    """Main function to download CSV files for multiple dates"""
    
    # Define date range
    START_DATE = "2025-08-25"  # Change this to your desired start date
    END_DATE = "2025-09-12"    # Change this to your desired end date
    
    # Generate list of dates
    dates = generate_date_list(START_DATE, END_DATE)
    print(f"📊 Will download CSV files for {len(dates)} dates")
    print(f"📅 Date range: {START_DATE} to {END_DATE}")
    
    # Confirm before starting
    proceed = input(f"\nDo you want to download CSV files for all {len(dates)} dates? (y/n): ").lower().strip()
    if proceed != 'y':
        print("❌ Operation cancelled")
        return
    
    # Initialize driver
    driver = setup_driver()
    if driver is None:
        return
    
    successful_downloads = 0
    failed_downloads = 0
    
    try:
        print(f"\n🚀 Starting batch download...")
        print("=" * 50)
        
        for i, date in enumerate(dates):
            is_first_run = (i == 0)
            
            success = download_csv_for_date(driver, date, is_first_run)
            
            if success:
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            # Progress update
            print(f"📊 Progress: {i+1}/{len(dates)} completed")
            print(f"✅ Successful: {successful_downloads} | ❌ Failed: {failed_downloads}")
            
            # Small delay between requests to be respectful
            if i < len(dates) - 1:  # Don't wait after the last one
                print("⏳ Waiting 2 seconds before next download...")
                time.sleep(2)
        
        # Final summary
        print("\n" + "=" * 50)
        print("🎉 Batch download completed!")
        print(f"✅ Successful downloads: {successful_downloads}")
        print(f"❌ Failed downloads: {failed_downloads}")
        print(f"📁 Check your Downloads folder for the CSV files")
        
        if failed_downloads > 0:
            print(f"\n⚠️ {failed_downloads} downloads failed. You may need to:")
            print("   - Check your internet connection")
            print("   - Verify the dates exist in Spotify Charts")
            print("   - Run the script again for failed dates")
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Download interrupted by user")
        print(f"✅ Completed: {successful_downloads}")
        print(f"❌ Failed: {failed_downloads}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()