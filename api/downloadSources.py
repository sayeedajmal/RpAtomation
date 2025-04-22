import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from extract import process_invoices

# Setup
download_dir = "invoices"
os.makedirs(download_dir, exist_ok=True)

print("🚀 Starting invoice workflow...")

# Initialize driver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://rpachallengeocr.azurewebsites.net/")
print("🌐 Navigating to https://rpachallengeocr.azurewebsites.net/")

# Wait for page to load
wait = WebDriverWait(driver, 10)

try:
    # Count total pages
    page_buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#tableSandbox_paginate a.paginate_button")))
    page_texts = [btn.text for btn in page_buttons if btn.text.isdigit()]
    total_pages = len(page_texts)
    print(f"📑 Found {total_pages} pages.")
    
    # Process all pages
    for current_page in range(1, total_pages + 1):
        print(f"\n📄 Visiting page {current_page}")
        
        # Get table rows
        rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#tableSandbox tbody tr")))
        print(f"🔍 Found {len(rows)} rows on page {current_page}")
        
        # Process each row
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            invoice_id = cols[1].text.strip()
            due_date_str = cols[2].text.strip()
            
            try:
                download_link = cols[3].find_element(By.TAG_NAME, "a").get_attribute("href")
                
                # Convert due date
                due_date = datetime.strptime(due_date_str, "%d-%m-%Y")
                if due_date > datetime.today():
                    print(f"⏩ Skipping {invoice_id} - due {due_date_str} (future)")
                    continue
                
                # Download the image directly using requests
                response = requests.get(download_link, stream=True) # type: ignore
                
                if response.status_code == 200:
                    # Determine file extension from content type
                    content_type = response.headers.get('content-type', '')
                    ext = 'jpg'  # Default extension
                    if 'image/jpeg' in content_type:
                        ext = 'jpg'
                    elif 'image/png' in content_type:
                        ext = 'png'
                    
                    # Save the image
                    file_path = os.path.join(download_dir, f"{invoice_id}.{ext}")
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"✅ Downloaded {invoice_id}.{ext}")
                else:
                    print(f"❌ Failed to download image for {invoice_id}: HTTP status {response.status_code}")
                
            except Exception as e:
                print(f"❌ Error processing {invoice_id}: {str(e)}")
        
        # Go to next page if not on last page
        if current_page < total_pages:
            # Find and click the next page button using a simpler selector
            try:
                # First approach: find by text
                next_page_num = current_page + 1
                next_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//div[@id='tableSandbox_paginate']//a[contains(@class, 'paginate_button') and text()='{next_page_num}']")
                ))
                next_button.click()
            except:
                # Alternative approach: use the "Next" button
                next_button = wait.until(EC.element_to_be_clickable(
                    (By.ID, "tableSandbox_next")
                ))
                next_button.click()
            
            # Wait for the page to load
            time.sleep(2)
            
except Exception as e:
    print(f"❌ Error: {str(e)}")
finally:
    driver.quit()
    print("\n🎉 Download done!")

# Parsing And Extraction
print("Extracting: .....")
process_invoices()