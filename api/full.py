import os
import time
import csv
import requests
import pytesseract
from PIL import Image
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIG ===
download_dir = "invoices"
os.makedirs(download_dir, exist_ok=True)
OUTPUT_CSV = "extracted_invoices.csv"  # Output CSV file name

# Store invoice details during download for later use
invoice_metadata = {}  # Will store invoice_id -> due_date mapping

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
            if due_date_str is not None:
                try:
                    download_link = cols[3].find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Convert due date
                    due_date = datetime.strptime(due_date_str, "%d-%m-%Y")
                    
                    # Store the due date in our metadata dictionary for later use
                    invoice_metadata[invoice_id] = due_date_str
                    
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

# === FUNCTION TO EXTRACT INVOICE DATA ===
def extract_invoice_data(image_path):
    invoice_number = None
    invoice_date = None
    company_name = None
    total_due = None

    try:
        # Perform OCR on the image
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)

        # Split the extracted text into lines for easier processing
        lines = extracted_text.split("\n")

        # Process each line to extract relevant details
        for line in lines:
            line = line.strip()

            # Extract invoice number
            if invoice_number is None and "Invoice #" in line:
                invoice_number = line.split("Invoice #")[-1].strip()
            elif invoice_number is None and line.startswith("#"):
                invoice_number = line.strip().lstrip("#").strip()

            # Extract date (assumes format "Date: Month Day, Year")
            if "Date:" in line:
                invoice_date = line.split(":", 1)[-1].strip()
            elif invoice_date is None and any(char.isdigit() for char in line) and "-" in line:
                match = re.search(r"\d{4}-\d{2}-\d{2}", line)
                if match:
                    try:
                        parsed = datetime.strptime(match.group(), "%Y-%m-%d")
                        invoice_date = parsed.strftime("%b %d, %Y")
                    except ValueError:
                        pass

            # Extract company name and total if in same line
            if (company_name is None or total_due is None) and ("Corp." in line or "LLC" in line) and "$" in line:
                match = re.search(r"(.*?)(\$[\d,]+\.\d{2})", line)
                if match:
                    company_name = match.group(1).strip()
                    total_due = match.group(2).strip()

            # Fallback: Extract company name if not yet found
            if company_name is None and ("Corp." in line or "LLC" in line):
                company_name = line.strip()
                if company_name and "INVOICE" in company_name:
                    company_name = company_name.replace("INVOICE", "").strip()

            # Fallback: Extract total if line starts with "Total"
            if total_due is None:
                match = re.search(r"Total\s+([\d,]+\.\d{2})", line)
                if match:
                    total_due = f"${match.group(1)}"

        # Clean quotes
        if company_name:
            company_name = company_name.replace("'", "").replace("'", "").replace('"', "").strip()

        if invoice_number and invoice_date and company_name and total_due:
            return invoice_number, invoice_date, company_name, total_due
        else:
            print(f"Warning: Missing data for image: {image_path}")
            return None

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

# === PROCESSING THE IMAGES ===
def process_invoices():
    invoices_data = []
    today_date = datetime.today().date()

    # Get all files in the invoices directory
    invoice_files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f)) 
                    and f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    for image_filename in invoice_files:
        # Get the invoice ID from the filename (remove extension)
        invoice_id = os.path.splitext(image_filename)[0]
        image_path = os.path.join(download_dir, image_filename)
        
        print(f"🔢 Extracting data from {image_filename}...")
        extracted_data = extract_invoice_data(image_path)

        if extracted_data:
            invoice_number, invoice_date, company_name, total_due = extracted_data

            try:
                # Convert invoice date to DD-MM-YYYY format
                invoice_date_obj = datetime.strptime(invoice_date, "%b %d, %Y")
                formatted_invoice_date = invoice_date_obj.strftime("%d-%m-%Y")
                
                # Get the due date from our metadata dictionary (previously scraped from the website)
                due_date = invoice_metadata.get(invoice_id, "Unknown")
                
                # Format total due without '$' and with proper decimal
                total_amount = total_due.replace("$", "").strip()
                
                if invoice_date_obj.date() <= today_date:
                    invoices_data.append([
                        invoice_id,
                        due_date,
                        invoice_number,
                        formatted_invoice_date,
                        company_name,
                        total_amount
                    ])
                else:
                    print(f"❌ Skipping {image_filename} - Invoice date is in the future.")

            except Exception as e:
                print(f"❌ Failed to process date for {image_filename}: {e}")
        else:
            print(f"❌ Failed to extract data from {image_filename}")

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "DueDate", "InvoiceNo", "InvoiceDate", "CompanyName", "TotalDue"])
        writer.writerows(invoices_data)

    print(f"\n🏁 Done. Extracted data saved in {OUTPUT_CSV}")

# Execute processing after downloading
print("\n📝 Extracting data from downloaded invoices...")
process_invoices()