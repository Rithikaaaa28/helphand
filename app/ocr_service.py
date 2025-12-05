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
        """Preprocess image for better OCR accuracy with multiple techniques"""
        try:
            # Read image with OpenCV
            img = cv2.imread(image_path)
            if img is None:
                return image_path
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Resize if too small or too large (improves OCR accuracy)
            height, width = gray.shape
            target_height = 2000  # Larger size for better OCR
            if height < target_height:
                scale = target_height / height
                gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            elif height > 3000:
                scale = 3000 / height
                gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Apply binary thresholding
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Dilation to make text bolder
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
            dilated = cv2.dilate(binary, kernel, iterations=1)
            
            # Save the preprocessed version
            temp_path = image_path.replace('.', '_preprocessed.')
            cv2.imwrite(temp_path, dilated)
            
            return temp_path
        except Exception as e:
            print(f"Preprocessing error: {e}")
            return image_path  # Return original if preprocessing fails
    
    def extract_text_from_image(self, image_path):
        """Extract text from uploaded ID document with improved OCR"""
        try:
            # Preprocess image for better OCR
            preprocessed_path = self.preprocess_image(image_path)
            
            # Open and process image
            image = Image.open(preprocessed_path)
            
            # Use multiple Tesseract configurations and combine results
            # PSM modes: 3=auto, 6=uniform block, 11=sparse text, 4=single column
            configs = [
                '--oem 3 --psm 6',  # Uniform text block (best for ID cards)
                '--oem 3 --psm 3',  # Fully automatic page segmentation
            ]
            
            all_text = []
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, lang='eng', config=config)
                    if text.strip():
                        all_text.append(text)
                except Exception:
                    continue
            
            # Use the longest result (usually most complete)
            extracted_text = max(all_text, key=len, default="") if all_text else ""
            
            # Clean up temporary preprocessed image
            if preprocessed_path != image_path and os.path.exists(preprocessed_path):
                os.remove(preprocessed_path)
            
            # Clean and process text
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            # Extract specific information (use raw text to preserve line structure)
            extracted_info = self._parse_id_info(extracted_text)
            
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
        """Parse specific information from ID documents with improved name extraction"""
        info = {}
        text_upper = text.upper()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        # Try to extract ID numbers first (helps identify document type)
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
        
        # Improved name extraction strategies
        name_found = False
        
        # Strategy 1: Look for explicit "NAME:" patterns
        name_patterns = [
            r'NAME[:\s]+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
            r'HOLDER[:\s]+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_upper)
            if match:
                potential_name = match.group(1).strip()
                # Clean up the name
                potential_name = re.sub(r'\s+', ' ', potential_name)
                if len(potential_name.split()) >= 1 and len(potential_name) > 3:
                    info['name'] = potential_name
                    name_found = True
                    break
        
        # Strategy 2: If no explicit name found, look for capitalized words on their own line
        # (names are usually prominent in ID cards)
        if not name_found:
            for i, line in enumerate(lines[:15]):  # Check first 15 lines
                # Clean up the line - remove common symbols
                line_clean = re.sub(r'[—_\-.,;:\'\"]+', ' ', line).strip()
                words = line_clean.split()
                
                # Look for lines with 1-4 words that look like names (allow single names too)
                if 1 <= len(words) <= 4:
                    # Check if words look like a name (start with uppercase, mostly alphabetic, at least 3 chars)
                    valid_words = []
                    for word in words:
                        # Word should be mostly alphabetic, at least 3 chars, start with uppercase
                        if (len(word) >= 3 and 
                            word[0].isupper() and 
                            sum(c.isalpha() for c in word) >= len(word) * 0.8):
                            valid_words.append(word)
                    
                    # If we have 1-4 valid name-like words (accept single names)
                    if 1 <= len(valid_words) <= 4:
                        potential_name = ' '.join(valid_words).upper()
                        # Exclude common headers/words and short garbled text
                        excluded = ['GOVERNMENT', 'INDIA', 'REPUBLIC', 'UNIQUE', 'IDENTIFICATION',
                                  'AUTHORITY', 'AADHAAR', 'CARD', 'GRILL', 'OVERNMENT', 'RIE', 'FOC']
                        
                        if not any(exc in potential_name for exc in excluded):
                            info['name'] = potential_name
                            name_found = True
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