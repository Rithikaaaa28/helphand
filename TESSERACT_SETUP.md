# Tesseract OCR Setup Guide

## Overview
HelpHand uses Tesseract OCR to extract text from volunteer verification documents (ID cards, certificates, etc.). This guide will help you install and configure Tesseract OCR on your system.

## Installation

### Windows

1. **Download Tesseract**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (e.g., `tesseract-ocr-w64-setup-5.3.3.exe`)

2. **Install Tesseract**
   - Run the installer
   - Default installation path: `C:\Program Files\Tesseract-OCR`
   - ✅ **Important**: During installation, check "Add to PATH" option
   - Install all language packs (at minimum: English)

3. **Verify Installation**
   ```powershell
   tesseract --version
   ```
   You should see version information like:
   ```
   tesseract 5.3.3
   leptonica-1.83.1
   ```

4. **Configure Environment Variable (if not in PATH)**
   - Open System Properties → Environment Variables
   - Add to System PATH: `C:\Program Files\Tesseract-OCR`
   - Alternatively, set `TESSERACT_PATH` environment variable:
     ```powershell
     $env:TESSERACT_PATH = "C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev

# Verify installation
tesseract --version
```

### macOS

```bash
# Using Homebrew
brew install tesseract

# Verify installation
tesseract --version
```

## Configuration in HelpHand

The OCR service automatically detects Tesseract installation:

1. **Automatic Detection** (Windows)
   - Checks default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
   - Falls back to `TESSERACT_PATH` environment variable

2. **Manual Configuration**
   - Set environment variable in your `.env` file:
     ```
     TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
     ```

## Testing OCR Functionality

### Quick Test

1. **Test with Python**
   ```python
   from app.ocr_service import OCRService
   
   ocr = OCRService()
   result = ocr.extract_text_from_image('path/to/test/image.jpg')
   print(result)
   ```

2. **Test via Command Line**
   ```powershell
   tesseract test_image.jpg output
   cat output.txt
   ```

### Test Document Upload

1. Start the Flask application:
   ```powershell
   python run.py
   ```

2. Register as a volunteer and upload an ID document
3. Admin can verify the document with OCR auto-extraction

## Supported Document Types

The OCR service currently supports:
- ✅ **Aadhaar Card** (Indian national ID)
- ✅ **PAN Card** (Indian tax ID)
- ✅ **Driving License**
- ✅ **Passport**
- ✅ Other government-issued photo IDs

## Image Quality Requirements

For best OCR accuracy:
- **Resolution**: Minimum 300 DPI
- **Format**: JPEG, PNG, TIFF
- **Size**: Maximum 5MB
- **Quality**: Clear, well-lit images without glare
- **Orientation**: Document should be upright and straight

## Troubleshooting

### Issue: "tesseract: command not found"
**Solution**: Tesseract is not installed or not in PATH
- Reinstall Tesseract and add to PATH
- Or set `TESSERACT_PATH` environment variable

### Issue: Poor OCR accuracy
**Solution**: 
- Use higher resolution images (300+ DPI)
- Ensure good lighting and contrast
- Clean the document before scanning
- The app automatically preprocesses images for better accuracy

### Issue: "TesseractNotFoundError"
**Solution**: 
- Check if Tesseract executable path is correct
- Verify installation: `tesseract --version`
- Set correct path in environment variable

### Issue: OCR extraction is empty
**Solution**:
- Check if image contains readable text
- Verify image format is supported
- Try preprocessing the image manually
- Check console logs for specific errors

## Advanced Configuration

### Custom Tesseract Config

Modify `app/ocr_service.py` to use custom configurations:

```python
# Current config (in extract_text_from_image method)
custom_config = r'--oem 3 --psm 6'

# Options:
# --oem 3: Use default OCR Engine Mode
# --psm 6: Assume uniform block of text
# --psm 3: Fully automatic page segmentation
```

### Additional Languages

Install additional language packs:

**Windows**: Download from [Tesseract GitHub](https://github.com/tesseract-ocr/tessdata)

**Linux**:
```bash
sudo apt install tesseract-ocr-hin  # Hindi
sudo apt install tesseract-ocr-tam  # Tamil
```

Then update OCR call:
```python
extracted_text = pytesseract.image_to_string(image, lang='eng+hin')
```

## Performance Optimization

### Image Preprocessing
The OCR service includes automatic preprocessing:
- Grayscale conversion
- Adaptive thresholding
- Noise reduction using Non-local Means Denoising

### Processing Time
- Average processing time: 2-5 seconds per document
- Factors affecting speed:
  - Image resolution
  - Document complexity
  - System performance

## Security Considerations

- Uploaded documents are stored in `app/static/uploads/documents/`
- Only authenticated admins can access verification pages
- OCR extraction happens server-side
- Sensitive data is stored in database with proper access controls

## API Endpoints

### Real-time OCR Verification
```http
POST /admin/api/verify_document/<volunteer_id>
Authorization: Required (Admin role)

Response:
{
  "success": true,
  "verified": true,
  "reason": "Document verified successfully",
  "match_score": 0.85,
  "confidence": 0.9,
  "extracted_info": {
    "name": "JOHN DOE",
    "id_number": "1234 5678 9012",
    "id_type": "aadhaar"
  }
}
```

## Need Help?

- Check application logs: Console output when running Flask
- Enable debug mode in `config.py`
- Review OCR extraction results in admin dashboard
- Test with sample documents first

## References

- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [pytesseract GitHub](https://github.com/madmaze/pytesseract)
- [OpenCV Documentation](https://docs.opencv.org/)
