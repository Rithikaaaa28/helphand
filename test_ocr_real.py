"""Test OCR with actual uploaded document"""
import sys
import os
sys.path.insert(0, 'c:\\Users\\pattarit\\MJ')

from app.ocr_service import OCRService

# Initialize OCR service
ocr = OCRService()

# Test with actual uploaded document
doc_path = r"app\static\uploads\documents\1764852927_AA1CFntJ.jpg"

print("=" * 70)
print("TESTING OCR WITH UPLOADED DOCUMENT")
print("=" * 70)
print(f"Document: {doc_path}")
print()

# Test extraction
print("1. Extracting text from image...")
result = ocr.extract_text_from_image(doc_path)

print(f"Success: {result['success']}")
if not result['success']:
    print(f"Error: {result.get('error')}")
else:
    print(f"\nRaw Text Extracted:")
    print("-" * 70)
    print(result['raw_text'][:500])  # First 500 chars
    print()
    
    print(f"\nParsed Information:")
    print("-" * 70)
    for key, value in result['parsed_info'].items():
        print(f"{key}: {value}")
    
    print(f"\nConfidence Score: {result['confidence']:.2f}")

# Test verification with a sample name
print("\n" + "=" * 70)
print("2. Testing Document Verification")
print("=" * 70)

test_name = "Aryabatta"  # Change this to match your test document
verification = ocr.verify_volunteer_document(doc_path, test_name)

print(f"Verified: {verification['verified']}")
print(f"Reason: {verification['reason']}")
print(f"Match Score: {verification.get('match_score', 0):.2f}")

if 'extracted_info' in verification:
    print(f"\nExtracted Name: {verification['extracted_info'].get('name', 'Not found')}")
    print(f"Expected Name: {test_name}")

print("\n" + "=" * 70)
