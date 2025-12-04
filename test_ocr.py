"""Test OCR functionality"""
import sys
import os
sys.path.insert(0, 'c:\\Users\\pattarit\\MJ')

from app.ocr_service import OCRService

print("=" * 60)
print("OCR COMPONENT TEST")
print("=" * 60)

# Initialize OCR service
try:
    ocr = OCRService()
    print("✓ OCR Service initialized")
    
    # Check if Tesseract is accessible
    import pytesseract
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract found: Version {version}")
        print(f"✓ Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
        print("\n✅ OCR component is WORKING!")
    except Exception as e:
        print(f"✗ Tesseract not accessible: {e}")
        print("\n❌ OCR component is NOT WORKING")
        print("\nTo fix this:")
        print("1. Download: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Install to: C:\\Program Files\\Tesseract-OCR")
        print("3. Restart terminal and try again")
        
except Exception as e:
    print(f"✗ Error initializing OCR: {e}")
    print("\n❌ OCR component FAILED")

print("=" * 60)
