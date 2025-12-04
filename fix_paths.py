"""Clear extracted_text and fix paths"""
import sys
sys.path.insert(0, 'c:\\Users\\pattarit\\MJ')

from app import create_app, db
from app.models import Volunteer

app = create_app()
with app.app_context():
    # Get pending volunteers
    volunteers = Volunteer.query.filter_by(verification_status='pending').all()
    
    print(f"Found {len(volunteers)} pending volunteers")
    
    for v in volunteers:
        print(f"\nVolunteer ID {v.id}: {v.user_profile.name}")
        print(f"  Original path: {v.document_path}")
        print(f"  Extracted text: {v.extracted_text}")
        
        # Clear extracted_text to force reprocessing
        v.extracted_text = None
        v.verification_notes = None
        
        # Fix path separators - replace backslashes with forward slashes
        if v.document_path:
            v.document_path = v.document_path.replace('\\', '/')
            print(f"  Fixed path: {v.document_path}")
    
    db.session.commit()
    print("\n✅ All paths fixed and extracted_text cleared!")
