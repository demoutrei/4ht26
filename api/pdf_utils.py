# pdf_utils.py
from fpdf import FPDF
import os
from datetime import datetime

def generate_memo_pdf(title: str, body: str, requester: str, recipients: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    
    # Safety watermark (light gray, centered)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 80, "DRAFT - PENDING APPROVAL", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "MEMORANDUM", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align="R")
    pdf.cell(0, 8, f"From: {requester}", ln=True)
    pdf.cell(0, 8, f"To: {recipients}", ln=True)
    pdf.cell(0, 8, f"Subject: {title}", ln=True)
    pdf.ln(10)
    
    pdf.multi_cell(0, 8, body)
    
    os.makedirs("generated_docs", exist_ok=True)
    filename = f"generated_docs/memo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename