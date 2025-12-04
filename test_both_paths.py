"""Test path resolution for both old and new formats"""
import os

static_folder = r"c:\Users\pattarit\MJ\app\static"
cwd = r"c:\Users\pattarit\MJ"

# Test cases from database
test_paths = [
    "app/static/uploads\\documents\\Image.jpg",  # Old format (ID 5)
    "uploads\\documents\\1764852927_AA1CFntJ.jpg"  # New format (ID 6)
]

print("=" * 70)
print("PATH RESOLUTION TEST - Both Formats")
print("=" * 70)

for doc_path in test_paths:
    print(f"\nOriginal path: {doc_path}")
    
    if doc_path.startswith('app/static/'):
        # Old format
        absolute_path = os.path.join(cwd, doc_path)
        format_type = "OLD FORMAT"
    else:
        # New format
        absolute_path = os.path.join(static_folder, doc_path)
        format_type = "NEW FORMAT"
    
    print(f"Format: {format_type}")
    print(f"Absolute path: {absolute_path}")
    print(f"File exists: {os.path.exists(absolute_path)}")
    
print("\n" + "=" * 70)
