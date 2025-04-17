# import os
# import csv
# import time
# import requests
# from urllib.parse import urljoin
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options

# # === CONFIG ===
# BASE_URL = "https://rpachallengeocr.azurewebsites.net/"
# OUTPUT_DIR = "invoices"
# CSV_FILENAME = "invoices.csv"

# print("🚀 Starting invoice downloader...")

# # === SETUP ===
# os.makedirs(OUTPUT_DIR, exist_ok=True)
# chrome_options = Options()
# chrome_options.add_argument("--headless")
# driver = webdriver.Chrome(service=Service(), options=chrome_options)

# print(f"🌐 Navigating to {BASE_URL}")
# driver.get(BASE_URL)
# time.sleep(2)

# # === PARSE THE TABLE ===
# print("📄 Looking for invoice table rows...")
# rows = driver.find_elements(By.CSS_SELECTOR, "#tableSandbox tbody tr")

# print(f"🔍 Found {len(rows)} rows in the table.")
# invoices_data = []

# for i, row in enumerate(rows, start=1):
#     print(f"\n🔢 Processing row {i}...")
#     cols = row.find_elements(By.TAG_NAME, "td")
#     if len(cols) < 4:
#         print("⚠️ Skipping row (not enough columns).")
#         continue

#     # Extract information from the table
#     index = cols[0].text.strip()
#     invoice_id = cols[1].text.strip()
#     due_date = cols[2].text.strip()
#     link_element = cols[3].find_element(By.TAG_NAME, "a")
#     download_href = link_element.get_attribute("href")
#     invoice_url = urljoin(BASE_URL, download_href)

#     print(f"🧾 Invoice ID: {invoice_id}")
#     print(f"📅 Due Date : {due_date}")
#     print(f"🔗 URL      : {invoice_url}")

#     # === DOWNLOAD THE INVOICE ===
#     try:
#         response = requests.get(invoice_url)
#         response.raise_for_status()

#         filename = f"{invoice_id}.jpg"
#         filepath = os.path.join(OUTPUT_DIR, filename)
#         with open(filepath, "wb") as f:
#             f.write(response.content)

#         print(f"✅ Downloaded and saved as {filename}")
#         invoices_data.append([invoice_id, due_date, filename])
#     except Exception as e:
#         print(f"❌ Failed to download {invoice_url}: {e}")

# # === LOOP OVER INVOICES 1 TO 12 ===
# print("\n📥 Starting download of invoices from 1 to 12...")

# for invoice_num in range(1, 13):
#     print(f"\n🔢 Processing Invoice {invoice_num}...")

#     # Construct the invoice URL for the numbered invoices (1.jpg, 2.jpg, ..., 12.jpg)
#     invoice_url = f"https://rpachallengeocr.azurewebsites.net/invoices/{invoice_num}.jpg"
#     try:
#         response = requests.get(invoice_url)
#         response.raise_for_status()

#         filename = f"{invoice_num}.jpg"
#         filepath = os.path.join(OUTPUT_DIR, filename)
#         with open(filepath, "wb") as f:
#             f.write(response.content)

#         print(f"✅ Downloaded and saved as {filename}")
#         invoices_data.append([invoice_num, "N/A", filename])  # Due date is "N/A" for these
#     except Exception as e:
#         print(f"❌ Failed to download {invoice_url}: {e}")

# # === SAVE TO CSV ===
# print(f"\n🧾 Creating CSV: {CSV_FILENAME}")
# with open(CSV_FILENAME, "w", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerow(["Invoice ID", "Due Date", "Filename"])
#     writer.writerows(invoices_data)

# print(f"\n🏁 Done. Downloaded {len(invoices_data)} invoices.")
# print(f"📂 Saved invoices in: {OUTPUT_DIR}")
# print(f"📄 CSV file created: {CSV_FILENAME}")

# driver.quit()


import os
import requests
import csv

# === CONFIG ===
BASE_URL = "https://rpachallengeocr.azurewebsites.net/invoices/"
OUTPUT_DIR = "invoices"
CSV_FILENAME = "invoices.csv"

# === SETUP ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === DOWNLOAD INVOICES FROM 1 TO 12 ===
invoices_data = []

for i in range(1, 13):
    invoice_url = f"{BASE_URL}{i}.jpg"
    try:
        response = requests.get(invoice_url)
        response.raise_for_status()

        filename = f"{i}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"✅ Downloaded and saved as {filename}")
        invoices_data.append([i, "N/A", filename])  # Since no due date available
    except Exception as e:
        print(f"❌ Failed to download {invoice_url}: {e}")

# === SAVE TO CSV ===
with open(CSV_FILENAME, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Invoice ID", "Due Date", "Filename"])
    writer.writerows(invoices_data)

print(f"\n🏁 Done. Downloaded {len(invoices_data)} invoices.")
print(f"📂 Saved invoices in: {OUTPUT_DIR}")
print(f"📄 CSV file created: {CSV_FILENAME}")
