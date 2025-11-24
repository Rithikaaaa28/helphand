# 🚀 HelpHand - Quick Start Guide

## Prerequisites
- Python 3.8 or higher
- Tesseract OCR installed on your system

---

## Installation Steps

### 1️⃣ Install Tesseract OCR

#### Windows:
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR\`
3. If installed elsewhere, update `TESSERACT_CMD` in `config.py`

#### macOS:
```bash
brew install tesseract
```

#### Linux:
```bash
sudo apt-get install tesseract-ocr
```

---

### 2️⃣ Install Python Dependencies

```bash
# Activate virtual environment (if not already active)
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Install packages
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

If SSL issues occur, use:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org Flask Flask-SQLAlchemy Flask-Login Flask-Migrate bcrypt pytesseract scikit-learn nltk textblob pillow geopy pandas numpy
```

---

### 3️⃣ Download NLTK Data (for Sentiment Analysis)

```bash
python -c "import nltk; nltk.download('vader_lexicon')"
```

---

### 4️⃣ Initialize Database

```bash
python init_db.py
```

This will:
- Create all database tables (users, volunteers, tasks, feedback)
- Seed demo data with sample users and tasks
- Display demo login credentials

---

### 5️⃣ Run the Application

```bash
python run.py
```

The application will start on: **http://localhost:5000**

---

## 🔑 Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@helphand.com | admin123 |
| **User** | user@helphand.com | user123 |
| **Volunteer** | volunteer@helphand.com | volunteer123 |

---

## 🎯 Testing the Features

### As Admin:
1. Login with admin credentials
2. Go to "Verify Volunteers" section
3. View pending applications with OCR-extracted ID info
4. Approve or reject volunteers

### As User (Task Requester):
1. Login with user credentials
2. Click "Post New Task"
3. Fill in task details (title, description, category)
4. Enable browser location for GPS-based matching
5. View AI-matched volunteers ranked by relevance
6. Assign task to a volunteer
7. Mark complete and submit feedback

### As Volunteer:
1. Login with volunteer credentials
2. View available tasks nearby
3. Accept tasks
4. Complete tasks
5. Receive ratings and build reputation

---

## 📊 Testing Sentiment Analysis

To test sentiment analysis:
1. Complete a task as a volunteer
2. Login as the user who posted the task
3. Submit feedback with different sentiments:
   - **Positive**: "Excellent work! Very professional and on time."
   - **Negative**: "Poor quality work, arrived late, unprofessional."
   - **Neutral**: "Work was done as expected."
4. Check volunteer's rating update based on sentiment

---

## 🧪 Testing Location-Based Matching

1. Post a task with your current location (allow browser geolocation)
2. View matched volunteers - they should be ranked by:
   - Skill similarity (60% weight)
   - Distance proximity (40% weight)
3. If no volunteers within 10km, system auto-expands to 50km

---

## 🪪 Testing OCR Verification

1. Register as a new volunteer
2. Upload a government ID (PAN/Aadhaar/Driving License)
   - Use a clear, high-quality image for best results
3. Login as admin
4. View "Verify Volunteers" page
5. See OCR-extracted text (name, ID number, etc.)
6. Approve or reject the volunteer

---

## 💰 Testing Commercial Features

1. Post a task with "Commercial Task" checkbox enabled
2. Enter payment amount (e.g., ₹2000)
3. System automatically calculates 8% platform fee (₹160)
4. Assign to a Pro subscriber volunteer (gets priority)

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors
**Solution**: Ensure all packages are installed:
```bash
pip install -r requirements.txt
```

### Issue: OCR not working
**Solution**: 
1. Verify Tesseract is installed: `tesseract --version`
2. Check `TESSERACT_CMD` path in `config.py`
3. Windows: Ensure path is `r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

### Issue: Database errors
**Solution**: Re-initialize database:
```bash
# Delete old database
rm instance/helphand.db  # Linux/Mac
Remove-Item instance\helphand.db  # Windows PowerShell

# Create fresh database
python init_db.py
```

### Issue: Sentiment analysis not working
**Solution**: Download NLTK data:
```bash
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"
```

### Issue: Port 5000 already in use
**Solution**: Use a different port:
- Edit `run.py`, change: `app.run(debug=True, port=5001)`

---

## 📈 Performance Tips

### For Large Datasets:
1. Consider switching from SQLite to MySQL/PostgreSQL:
   ```python
   # config.py
   SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@localhost/helphand'
   ```

2. Add database indexes for frequently queried fields:
   ```python
   # In models.py
   __table_args__ = (db.Index('idx_pincode', 'pincode'),)
   ```

3. Enable caching for AI model predictions

---

## 🔒 Security Recommendations (Before Production)

1. **Change Secret Key**:
   ```python
   # config.py
   SECRET_KEY = 'your-strong-random-secret-key-here'
   ```

2. **Use Environment Variables**:
   ```bash
   # .env file
   SECRET_KEY=your-secret-key
   DATABASE_URL=your-database-url
   ```

3. **Disable Debug Mode**:
   ```python
   # run.py
   app.run(debug=False)
   ```

4. **Add CSRF Protection** (already included via Flask-WTF)

5. **Enable HTTPS** in production

---

## 📞 Need Help?

- Check `IMPLEMENTATION_SUMMARY.md` for complete feature documentation
- Check `README.md` for detailed project information
- Review code comments in source files
- Check Flask documentation: https://flask.palletsprojects.com/

---

## ✅ Verification Checklist

Before presentation, verify:
- [ ] Database initialized successfully
- [ ] Can login with demo credentials
- [ ] Can post a task
- [ ] Can view AI-matched volunteers
- [ ] Can assign and complete tasks
- [ ] Can submit feedback
- [ ] Sentiment analysis updates ratings
- [ ] OCR extracts text from uploaded IDs
- [ ] Admin can approve/reject volunteers
- [ ] Location-based filtering works

---

**Everything ready? Let's demo! 🚀**
