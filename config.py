import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///helphand.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # OCR Configuration
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust path as needed
    
    # Location settings
    DEFAULT_RADIUS_KM = 10
    FALLBACK_RADIUS_KM = 50
    
    # AI/ML settings
    MIN_SIMILARITY_THRESHOLD = 0.1
    PROXIMITY_WEIGHT = 0.4
    SIMILARITY_WEIGHT = 0.6
    
    # Commercial features
    PLATFORM_FEE_PERCENTAGE = 8
    PREMIUM_VERIFICATION_FEE = 99
    PRO_SUBSCRIPTION_FEE = 199