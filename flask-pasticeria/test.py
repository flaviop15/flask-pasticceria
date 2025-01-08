import os
import re
import pdfplumber
import pytesseract
from PIL import Image

def extract_values(text):
    patterns = {
        "Doc_Acquisto": r"Doc\.?\s*Acquisto\s*[:\-]?\s*([\w-]+)",
        "CIG": r"CIG\s*:\s*([\w-]+)",
        "CUP": r"CUP\s*:\s*([\w-]+)",
        "IBAN": r"IBAN\s*:\s*([A-Z0-9]+)",
        "Fornitore": r"Fornitore\s*:\s*([\w-]+)\s*([^0-9\s]+.*)",
        "Org_Acq": r"OA\s*(.*?)\s*Protocollo",
        "Gruppo_Acquisti": r"([A-Z]{2})\s*Divisa",
        "Totali_Importo_EM": r"Totali\s*:\s*([\d\.,]+)\s",
        "Totali_Recupero_Anticipazione": r"Totali\s*:\s*[\d\.,]+\s([\d\.,]+)\s[\d\.,]+\s",
        "Totali_Trattenute": r"Totali\s*:\s*[\d\.,]+\s[\d\.,]+\s[\d\.,]+\s([\d\.,]+)\s"
    }

    results = {}

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if key == "Fornitore" and matches:
            entry = (matches[0][0], matches[0][1].strip())
            results[key] = f"{entry[0]} - {entry[1]}"
        elif matches:
            results[key] = matches[0]
        else:
            results[key] = ""

    # Special handling for CIG and CUP
    if "CIG" in results and results["CIG"].endswith("CUP"):
        results["CIG"] = results["CIG"][:-3]
    
    if "CUP" in results and results["CUP"] == "FORNITORE":
        results["CUP"] = ""

    return results

def extract_table_data(lines):
    table_data = []
    table_row_pattern = r"(\d+)\s+(\d+)\s+(\d{2}\.\d{2}\.\d{4})\s+((?:[\d\.]+,\d{2}|-))\s+((?:[\d,]+,\d{2}|-))\s+((?:[\d\.]+,\d{2}|-))\s+((?:[\d,]+,\d{2}|-))\s+((?:[\d,]+,\d{2}|-))\s+([\d-]+)\s+(\d{2}\.\d{2}\.\d{4})"
    for line in lines:
        match = re.match(table_row_pattern, line)
        if match:
            table_data.append(match.groups())
    return table_data

def ocr_page(page):
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img)
    return text

def process_pdf(file_path):
    text = ""
    lines = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
                lines.extend(page_text.split('\n'))
            '''
            else:
                # Perform OCR if no text is found
                with fitz.open(file_path) as doc:
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        ocr_text = ocr_page(page)
                        text += ocr_text
                        lines.extend(ocr_text.split('\n'))
            '''
    values = extract_values(text)
    table_data = extract_table_data(lines)
    return values, table_data

def process_folder(folder_path):
    results = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf") or file_name.endswith(".PDF"):
            file_path = os.path.join(folder_path, file_name)
            values, table_data = process_pdf(file_path)
            structured_data = []
            for row in table_data:
                structured_row = {
                    "Doc_Acquisto": values.get("Doc_Acquisto", ""),
                    "Entrata_Merce": row[1],
                    "Data_Reg_EM": row[2],
                    "Bolla": row[8][-3:],
                    "Data_Bolla": row[9],
                    "CIG": values.get("CIG", ""),
                    "CUP": values.get("CUP", ""),
                    "IBAN": values.get("IBAN", ""),
                    "Fornitore": values.get("Fornitore", ""),
                    "Org_Acq": values.get("Org_Acq", ""),
                    "Gruppo_Acquisti": values.get("Gruppo_Acquisti", ""),
                    "Totali_Importo_EM": values.get("Totali_Importo_EM", ""),
                    "Totali_Recupero_Anticipazione": values.get("Totali_Recupero_Anticipazione", ""),
                    "Totali_Trattenute": values.get("Totali_Trattenute", "")
                }
                structured_data.append(structured_row)
            results[file_name] = structured_data
    return results

# Specify the folder path
folder_path = "/Users/flavioporocani/Desktop/medialogicai-files"

# Process all files in the folder
results = process_folder(folder_path)

# Print the structured data
for file_name, data in results.items():
    print(f"File: {file_name}")
    for row in data:
        print(f"  Doc_Acquisto: {row['Doc_Acquisto']}")
        print(f"  Entrata_Merce: {row['Entrata_Merce']}")
        print(f"  Data_Reg_EM: {row['Data_Reg_EM']}")
        print(f"  Bolla: {row['Bolla']}")
        print(f"  Data_Bolla: {row['Data_Bolla']}")
        print(f"  CIG: {row['CIG']}")
        print(f"  CUP: {row['CUP']}")
        print(f"  IBAN: {row['IBAN']}")
        print(f"  Fornitore: {row['Fornitore']}")
        print(f"  Org_Acq: {row['Org_Acq']}")
        print(f"  Gruppo_Acquisti: {row['Gruppo_Acquisti']}")
        print(f"  Totali_Importo_EM: {row['Totali_Importo_EM']}")
        print(f"  Totali_Recupero_Anticipazione: {row['Totali_Recupero_Anticipazione']}")
        print(f"  Totali_Trattenute: {row['Totali_Trattenute']}")
