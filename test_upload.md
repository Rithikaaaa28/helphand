# Image Upload Fix - Testing Guide

## Changes Made

### 1. Configuration Updates (`config.py`)
- Added `ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}` to allow image file uploads
- Kept `MAX_CONTENT_LENGTH = 16 * 1024 * 1024` (16MB limit)

### 2. Route Improvements (`app/routes.py`)
- Added `allowed_file()` helper function to validate file extensions
- Enhanced file upload validation with proper error messages
- Added timestamp to filenames to prevent conflicts
- Added proper error handling for missing files
- Fixed path storage (relative path for database)

### 3. Template Enhancements (`volunteer_setup.html`)
- Added live image preview before upload
- Expanded accepted file types in the file input
- Better visual feedback with preview functionality
- Updated file size limit display to 16MB

### 4. Display Fix (`verify_volunteers.html`)
- Fixed image path rendering for admin verification page
- Added proper error handling for missing images

## How to Test

### Step 1: Start the Application
```powershell
.\.venv\Scripts\activate
python run.py
```

### Step 2: Register as Volunteer
1. Go to http://127.0.0.1:5000/register
2. Fill in the form with:
   - Name: Test Volunteer
   - Email: test@volunteer.com
   - Password: test123
   - Role: Volunteer
   - Pincode: 560001

### Step 3: Setup Volunteer Profile
1. After login, you'll be redirected to setup profile
2. Enter skills (e.g., "Home repairs, plumbing, electrical work")
3. Click "Upload a file" or drag and drop an image
4. **Supported formats**: PNG, JPG, JPEG, GIF, BMP
5. **Max size**: 16MB
6. You should see a preview of your image immediately after selection
7. Check the terms checkbox
8. Click Submit

### Step 4: Verify Upload (as Admin)
1. Logout and login as admin:
   - Email: admin@helphand.com
   - Password: admin123
2. Go to "Verify Volunteers" from the dashboard
3. You should see the uploaded document image displayed
4. Click Approve or Reject

## Common Issues and Solutions

### Issue: "Invalid file type" error
**Solution**: Make sure you're uploading an image file (PNG, JPG, JPEG, GIF, BMP). PDF files are not supported.

### Issue: Image not displaying on verification page
**Solution**: 
- Check that the file was actually uploaded to `app/static/uploads/documents/`
- Verify the database has the correct path stored
- Check browser console for 404 errors

### Issue: File too large
**Solution**: Resize your image to under 16MB. Most ID card photos should be well under 1MB.

### Issue: No preview showing
**Solution**: Make sure you're using a modern browser (Chrome, Firefox, Edge). The preview uses JavaScript FileReader API.

## File Structure
```
app/
├── static/
│   └── uploads/
│       └── documents/        ← Uploaded verification documents
│           └── [timestamp]_[filename]
```

## Security Features
- File type validation (only images allowed)
- Filename sanitization using `secure_filename()`
- Timestamp prefix to prevent conflicts
- File size limit (16MB)
- Relative paths stored in database (prevents directory traversal)

## Next Steps (Optional Enhancements)
- [ ] Add image compression for large files
- [ ] Implement drag-and-drop file upload
- [ ] Add EXIF data cleaning for privacy
- [ ] Multiple document upload support
- [ ] Automatic image rotation correction
