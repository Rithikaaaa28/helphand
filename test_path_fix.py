"""Test path resolution fix"""
import sys
import os
sys.path.insert(0, 'c:\\Users\\pattarit\\MJ')

# Simulate what the app does
static_folder = r"c:\Users\pattarit\MJ\app\static"
relative_path = r"uploads\documents\1764852927_AA1CFntJ.jpg"

absolute_path = os.path.join(static_folder, relative_path)

print("=" * 70)
print("PATH RESOLUTION TEST")
print("=" * 70)
print(f"Static folder: {static_folder}")
print(f"Relative path: {relative_path}")
print(f"Absolute path: {absolute_path}")
print(f"File exists: {os.path.exists(absolute_path)}")

if os.path.exists(absolute_path):
    print("\n✅ Path resolution is correct!")
    
    # Test OCR with the absolute path
    from app.ocr_service import OCRService
    ocr = OCRService()
    
    result = ocr.extract_text_from_image(absolute_path)
    print(f"\nOCR Success: {result['success']}")
    if result['success']:
        print(f"Extracted name: {result['parsed_info'].get('name', 'N/A')}")
        print("\n✅ OCR works with absolute path!")
else:
    print("\n❌ File not found at absolute path")
    
print("=" * 70)
