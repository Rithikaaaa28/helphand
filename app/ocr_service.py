import os
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename
import re
import cv2
import numpy as np

class OCRService:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Set Tesseract path for Windows (common installation path)
        # Users can override this by setting TESSERACT_PATH environment variable
        if os.name == 'nt':  # Windows
            default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            env_path = os.environ.get('TESSERACT_PATH', default_path)
            if os.path.exists(env_path):
                pytesseract.pytesseract.tesseract_cmd = env_path
    
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR accuracy"""
        try:
            # Read image with OpenCV
            img = cv2.imread(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to make text clearer
            threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(threshold, None, 10, 7, 21)
            
            # Save preprocessed image temporarily
            temp_path = image_path.replace('.', '_preprocessed.')
            cv2.imwrite(temp_path, denoised)
            
            return temp_path
        except Exception as e:
            print(f"Preprocessing error: {e}")
            return image_path  # Return original if preprocessing fails
    
    def extract_text_from_image(self, image_path):
        """Extract text from uploaded ID document"""
        try:
            # Preprocess image for better OCR
            preprocessed_path = self.preprocess_image(image_path)
            
            # Open and process image
            image = Image.open(preprocessed_path)
            
            # Extract text using OCR with custom config for better accuracy
            custom_config = r'--oem 3 --psm 6'
            extracted_text = pytesseract.image_to_string(image, lang='eng', config=custom_config)
            
            # Clean up temporary preprocessed image
            if preprocessed_path != image_path and os.path.exists(preprocessed_path):
                os.remove(preprocessed_path)
            
            # Clean and process text
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            # Extract specific information
            extracted_info = self._parse_id_info(cleaned_text)
            
            return {
                'success': True,
                'raw_text': extracted_text,
                'cleaned_text': cleaned_text,
                'parsed_info': extracted_info,
                'confidence': self._calculate_confidence(extracted_info)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_text': '',
                'cleaned_text': '',
                'parsed_info': {},
                'confidence': 0.0
            }
    
    def _calculate_confidence(self, extracted_info):
        """Calculate confidence score based on extracted information"""
        confidence = 0.0
        
        # Check if key fields are present
        if 'name' in extracted_info:
            confidence += 0.3
        if 'id_number' in extracted_info:
            confidence += 0.4
        if 'id_type' in extracted_info:
            confidence += 0.2
        if 'date_of_birth' in extracted_info:
            confidence += 0.1
        
        return confidence
    
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
    
    def verify_volunteer_document(self, image_path, volunteer_name):
        """
        Comprehensive document verification for volunteer
        Returns verification result with match score
        """
        # Extract text from document
        ocr_result = self.extract_text_from_image(image_path)
        
        if not ocr_result['success']:
            return {
                'verified': False,
                'reason': f"OCR failed: {ocr_result.get('error', 'Unknown error')}",
                'match_score': 0.0
            }
        
        extracted_info = ocr_result['parsed_info']
        
        # Check if document type is valid
        if not self.validate_document_type(extracted_info):
            return {
                'verified': False,
                'reason': 'Invalid or unrecognized document type',
                'match_score': 0.2,
                'extracted_info': extracted_info
            }
        
        # Check name matching
        name_match_score = self._match_name(extracted_info.get('name', ''), volunteer_name)
        
        # Verification criteria
        verified = name_match_score > 0.6 and 'id_number' in extracted_info
        
        return {
            'verified': verified,
            'reason': 'Document verified successfully' if verified else 'Name mismatch or missing ID number',
            'match_score': name_match_score,
            'extracted_info': extracted_info,
            'confidence': ocr_result.get('confidence', 0.0)
        }
    
    def _match_name(self, extracted_name, volunteer_name):
        """
        Calculate name match score using fuzzy matching
        Returns score between 0.0 and 1.0
        """
        if not extracted_name or not volunteer_name:
            return 0.0
        
        # Normalize names
        extracted_name = extracted_name.lower().strip()
        volunteer_name = volunteer_name.lower().strip()
        
        # Exact match
        if extracted_name == volunteer_name:
            return 1.0
        
        # Check if volunteer name is contained in extracted name
        if volunteer_name in extracted_name or extracted_name in volunteer_name:
            return 0.8
        
        # Split names and check for partial matches
        extracted_parts = set(extracted_name.split())
        volunteer_parts = set(volunteer_name.split())
        
        if len(extracted_parts) == 0 or len(volunteer_parts) == 0:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = extracted_parts.intersection(volunteer_parts)
        union = extracted_parts.union(volunteer_parts)
        
        similarity = len(intersection) / len(union) if len(union) > 0 else 0.0
        
        return similarity