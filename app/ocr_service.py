import os
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename
import re

class OCRService:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_text_from_image(self, image_path):
        """Extract text from uploaded ID document"""
        try:
            # Open and process image
            image = Image.open(image_path)
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(image, lang='eng')
            
            # Clean and process text
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            # Extract specific information
            extracted_info = self._parse_id_info(cleaned_text)
            
            return {
                'success': True,
                'raw_text': extracted_text,
                'cleaned_text': cleaned_text,
                'parsed_info': extracted_info
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_text': '',
                'cleaned_text': '',
                'parsed_info': {}
            }
    
    def _clean_extracted_text(self, text):
        """Clean and normalize extracted text"""
        # Remove extra whitespaces and newlines
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep alphanumeric and basic punctuation
        cleaned = re.sub(r'[^\w\s\-\.]', ' ', cleaned)
        
        return cleaned
    
    def _parse_id_info(self, text):
        """Parse specific information from ID documents"""
        info = {}
        text_upper = text.upper()
        
        # Try to extract name patterns
        name_patterns = [
            r'NAME[:\s]+([A-Z\s]+)',
            r'HOLDER[:\s]+([A-Z\s]+)',
            r'([A-Z]{2,}\s+[A-Z]{2,}(?:\s+[A-Z]{2,})?)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_upper)
            if match:
                info['name'] = match.group(1).strip()
                break
        
        # Try to extract ID numbers (Aadhaar, PAN, etc.)
        id_patterns = {
            'aadhaar': r'\b\d{4}\s?\d{4}\s?\d{4}\b',
            'pan': r'\b[A-Z]{5}\d{4}[A-Z]\b',
            'driving_license': r'\b[A-Z]{2}\d{13}\b'
        }
        
        for id_type, pattern in id_patterns.items():
            match = re.search(pattern, text_upper)
            if match:
                info['id_number'] = match.group(0)
                info['id_type'] = id_type
                break
        
        # Try to extract date of birth
        dob_patterns = [
            r'DOB[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})',
            r'BIRTH[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})',
            r'(\d{2}[/\-]\d{2}[/\-]\d{4})'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text_upper)
            if match:
                info['date_of_birth'] = match.group(1)
                break
        
        return info
    
    def validate_document_type(self, extracted_info):
        """Validate if the document is an acceptable ID proof"""
        acceptable_types = ['aadhaar', 'pan', 'driving_license']
        
        if 'id_type' in extracted_info and extracted_info['id_type'] in acceptable_types:
            return True
        
        return False