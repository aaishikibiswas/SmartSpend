import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO
import tempfile
import os
from datetime import datetime
from backend.services.categorizer import predict_transaction_category
from backend.utils.language_detection import detect_language, normalize_text

def parse_csv(file_bytes: bytes) -> list:
    df = pd.read_csv(BytesIO(file_bytes))
    return process_dataframe(df)

def parse_image(file_bytes: bytes) -> list:
    """Uses OCR to extract text, then tries to parse basic patterns."""
    image = Image.open(BytesIO(file_bytes))
    text = pytesseract.image_to_string(image)
    return parse_raw_text(text)

def parse_pdf(file_bytes: bytes) -> list:
    """Uses pdfplumber to extract text from a statement PDF."""
    transactions = []
    
    # Needs a temp file for pdfplumber
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
        
    try:
        with pdfplumber.open(tmp_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        transactions = parse_raw_text(text)
    finally:
        os.remove(tmp_path)
        
    return transactions

def parse_raw_text(text: str) -> list:
    """
    Very crude rule-based extraction from raw text.
    Assumes "YYYY-MM-DD Description Amount" roughly.
    """
    lines = text.split('\n')
    data = []
    import re
    # Simple regex for date, words, and final number
    pattern = re.compile(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\d+\.?\d*)')
    
    for line in lines:
        match = pattern.search(line)
        if match:
            date_str = match.group(1)
            desc = match.group(2).strip()
            amt = float(match.group(3))
            
            data.append({
                "date": date_str,
                "description": desc,
                "amount": amt
            })
            
    df = pd.DataFrame(data)
    if not df.empty:
        return process_dataframe(df)
    return []

def process_dataframe(df: pd.DataFrame) -> list:
    """Takes standard raw DF and transforms it into our DB dict list format"""
    # Assuming df has 'date', 'description' or 'merchant', and 'amount'
    
    # rename columns to standard
    col_mapping = {}
    for col in df.columns:
        if 'date' in col.lower(): col_mapping[col] = 'date'
        elif 'desc' in col.lower() or 'merch' in col.lower(): col_mapping[col] = 'merchant'
        elif 'amount' in col.lower(): col_mapping[col] = 'amount'
    df = df.rename(columns=col_mapping)
    
    if 'date' not in df.columns or 'merchant' not in df.columns or 'amount' not in df.columns:
        return []
        
    transactions = []
    for _, row in df.iterrows():
        merchant_raw = str(row['merchant'])
        lang = detect_language(merchant_raw)
        merchant_norm = normalize_text(merchant_raw)
        
        amt = float(row['amount'])
        t_type = "income" if amt > 0 else "expense"
        categorization = predict_transaction_category(merchant_norm, amount=amt, date=str(row['date'])[:10])
        cat = categorization["category"]
        
        transactions.append({
            "date": str(row['date'])[:10],
            "merchant": merchant_raw.title(),
            "category": cat,
            "amount": amt,
            "type": t_type,
            "language": lang
        })
        
    return transactions
