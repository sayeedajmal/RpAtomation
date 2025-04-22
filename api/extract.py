import os
import csv
import pytesseract
from PIL import Image
from datetime import datetime
import re

# === CONFIG ===
INPUT_DIR = "invoices"  # Folder where downloaded invoices are saved
OUTPUT_CSV = "extracted_invoices.csv"  # Output CSV file name

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
    invoice_files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f)) 
                    and f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    for image_filename in invoice_files:
        # Get the invoice ID from the filename (remove extension)
        invoice_id = os.path.splitext(image_filename)[0]
        image_path = os.path.join(INPUT_DIR, image_filename)
        
        print(f"🔢 Extracting data from {image_filename}...")
        extracted_data = extract_invoice_data(image_path)

        if extracted_data:
            invoice_number, invoice_date, company_name, total_due = extracted_data

            try:
                # Convert invoice date to DD-MM-YYYY format
                invoice_date_obj = datetime.strptime(invoice_date, "%b %d, %Y")
                formatted_invoice_date = invoice_date_obj.strftime("%d-%m-%Y")
                
                # Calculate due date (assuming it's in the past so we can't extract it)
                # This is just a placeholder - in a real scenario you would extract this data
                due_date = "25-02-2019"  # Placeholder
                
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
                    print(f"❌ Skipping {image_filename} - Due date is in the future.")

            except Exception as e:
                print(f"❌ Failed to process date for {image_filename}: {e}")
        else:
            print(f"❌ Failed to extract data from {image_filename}")

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "DueDate", "InvoiceNo", "InvoiceDate", "CompanyName", "TotalDue"])
        writer.writerows(invoices_data)

    print(f"\n🏁 Done. Extracted data saved in {OUTPUT_CSV}")

if __name__ == "__main__":
    process_invoices()