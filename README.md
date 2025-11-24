# HelpHand: AI-Driven Community Assistance Platform

A comprehensive volunteer matching platform built with Flask that uses AI and machine learning to connect people who need help with verified volunteers in their community.

## 🌟 Features

### Core Functionality
- **User Authentication**: Role-based access (Admin, User, Volunteer) with secure password hashing
- **ID Verification**: OCR-powered document verification using PyTesseract
- **AI Matching**: TF-IDF vectorization and cosine similarity for intelligent volunteer-task matching
- **Location Services**: GPS-based distance calculation and pincode filtering
- **Sentiment Analysis**: VADER sentiment analysis for feedback processing
- **Real-time Notifications**: Task assignment and completion notifications

### Advanced Features
- **Hybrid Scoring**: Combines similarity, proximity, ratings, and experience for optimal matching
- **Rating System**: Dynamic volunteer ratings updated based on feedback sentiment
- **Commercial Services**: Paid tasks with platform fee calculation
- **Subscription Plans**: Basic and Pro volunteer memberships
- **Premium Verification**: Fast-track verification for enhanced trust

## 🛠 Technology Stack

### Backend
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-Login** - Session management
- **Flask-Migrate** - Database migrations

### AI/ML Components
- **PyTesseract** - OCR for ID verification
- **scikit-learn** - TF-IDF vectorization and cosine similarity
- **NLTK VADER** - Sentiment analysis
- **geopy** - GPS distance calculations

### Frontend
- **Tailwind CSS** - Modern UI styling
- **Alpine.js** - Lightweight JavaScript framework
- **Font Awesome** - Icons

### Database
- **SQLite** (Development) / **MySQL** (Production)
- **Flask-SQLAlchemy** - ORM

## 📊 Database Schema

### Users
- user_id, name, email, password_hash, role, pincode, latitude, longitude, verified

### Volunteers  
- volunteer_id, user_id, skills, document_path, verification_status, rating, completed_tasks, subscription_type

### Tasks
- task_id, user_id, title, description, category, status, assigned_volunteer_id, is_commercial, payment_amount

### Feedback
- feedback_id, task_id, user_id, volunteer_id, rating, text, sentiment_score, sentiment_label

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Tesseract OCR (for document verification)
```

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd helphand
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR**
- **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

4. **Configure Tesseract path** (if needed)
```python
# In config.py
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
```

5. **Run the application**
```bash
python run.py
```

6. **Access the application**
- Open http://localhost:5000
- The database will be automatically created with demo data

### Demo Credentials
```
Admin: admin@helphand.com / admin123
User: user@helphand.com / user123  
Volunteer: volunteer@helphand.com / volunteer123
```

## 🎯 How It Works

### For Users (Help Seekers)
1. **Register** as a user
2. **Post tasks** with detailed descriptions
3. **Review matched volunteers** ranked by AI
4. **Assign tasks** to preferred volunteers
5. **Provide feedback** with automatic sentiment analysis

### For Volunteers
1. **Register** as a volunteer
2. **Upload ID documents** for OCR verification
3. **Wait for admin approval** (24-48 hours)
4. **Browse available tasks** in your area
5. **Apply for tasks** matching your skills

### For Admins
1. **Review volunteer applications** with OCR-extracted data
2. **Approve/reject verifications** based on document authenticity
3. **Monitor platform statistics** and user activities
4. **Manage commercial features** and revenue tracking

## 🧠 AI & Machine Learning

### Task-Volunteer Matching
```python
# Hybrid scoring formula
final_score = (0.6 * similarity_score) + (0.4 * proximity_score) + rating_boost + experience_boost
```

- **Similarity Score**: TF-IDF cosine similarity between task description and volunteer skills
- **Proximity Score**: Normalized distance score (closer = higher)
- **Rating Boost**: Performance bonus based on volunteer rating
- **Experience Boost**: Bonus for completed tasks

### Sentiment Analysis
- **VADER** sentiment analyzer for feedback processing
- **Dynamic rating updates** based on sentiment scores
- **Sentiment-adjusted ratings** for improved volunteer ranking

### OCR Processing
- **Text extraction** from government ID documents
- **Information parsing** for name, ID numbers, dates
- **Validation** of document types (Aadhaar, PAN, Driving License)

## 💼 Commercial Features

### Revenue Model
- **Platform Fees**: 8% commission on paid tasks
- **Pro Subscriptions**: ₹199/month for enhanced volunteer visibility
- **Premium Verification**: ₹99 for fast-track ID verification

### Subscription Benefits
| Feature | Basic (Free) | Pro (₹199/month) |
|---------|--------------|------------------|
| Task Applications | ✅ | ✅ |
| Priority Matching | ❌ | ✅ |
| Premium Badge | ❌ | ✅ |
| Advanced Analytics | ❌ | ✅ |
| Customer Support | Basic | Priority |

## 🏗 Project Structure

```
helphand/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models
│   ├── routes.py                # Application routes
│   ├── ocr_service.py           # OCR processing
│   ├── static/                  # CSS, JS, uploads
│   └── templates/               # Jinja2 templates
├── ml_models/
│   └── matching_service.py      # AI matching algorithms
├── migrations/                  # Database migrations
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
└── run.py                       # Application entry point
```

## 🔧 Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///helphand.db
TESSERACT_CMD=/usr/local/bin/tesseract
```

### Key Settings
```python
# In config.py
DEFAULT_RADIUS_KM = 10          # Default search radius
PLATFORM_FEE_PERCENTAGE = 8     # Platform commission
MIN_SIMILARITY_THRESHOLD = 0.1  # Minimum matching threshold
```

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/
```

### Test Coverage
```bash
python -m pytest --cov=app tests/
```

## 📱 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Tasks
- `GET /dashboard` - User dashboard
- `POST /post_task` - Create new task
- `GET /task/<id>` - View task details
- `POST /assign_task/<task_id>/<volunteer_id>` - Assign task

### Volunteer
- `GET /volunteer/dashboard` - Volunteer dashboard
- `POST /volunteer/setup_profile` - Setup volunteer profile
- `GET /volunteer/tasks` - Available tasks

### Admin
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/verify_volunteers` - Pending verifications
- `POST /admin/approve_volunteer/<id>` - Approve volunteer

## 🔒 Security Features

- **Password Hashing**: bcrypt for secure password storage
- **Session Management**: Flask-Login with secure sessions
- **File Upload Security**: Secure filename handling and type validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CSRF Protection**: Flask-WTF CSRF tokens

## 🚀 Deployment

### Production Setup
1. **Set environment variables**
2. **Configure production database** (MySQL/PostgreSQL)
3. **Set up reverse proxy** (Nginx)
4. **Configure SSL certificates**
5. **Set up monitoring** and logging

### Docker Deployment
```bash
docker build -t helphand .
docker run -p 5000:5000 helphand
```

## 📈 Scalability Features

### Performance Optimizations
- **Database indexing** on frequently queried fields
- **Caching** for repeated AI calculations
- **Background processing** for OCR operations
- **CDN integration** for static file delivery

### Horizontal Scaling
- **Stateless design** for easy load balancing
- **Database connection pooling**
- **Microservices architecture** ready
- **API-first design** for mobile apps

## 🎯 Future Enhancements

### Short Term
- [ ] Mobile applications (iOS/Android)
- [ ] Push notifications
- [ ] Multi-language support
- [ ] Advanced analytics dashboard

### Long Term
- [ ] Video calling integration
- [ ] Blockchain-based reputation system
- [ ] AI chatbot for customer support
- [ ] IoT device integration

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit changes** (`git commit -m 'Add AmazingFeature'`)
4. **Push to branch** (`git push origin feature/AmazingFeature`)
5. **Open Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Project Lead**: [Your Name]
- **AI/ML Developer**: [Name]
- **Backend Developer**: [Name]
- **Frontend Developer**: [Name]

## 📞 Support

- **Email**: support@helphand.com
- **Documentation**: [Wiki](wiki-link)
- **Issues**: [GitHub Issues](issues-link)

## 🙏 Acknowledgments

- **OCR Technology**: Tesseract by Google
- **ML Libraries**: scikit-learn, NLTK
- **UI Framework**: Tailwind CSS
- **Icons**: Font Awesome
- **Inspiration**: Community service and volunteer organizations worldwide

---

**Built with ❤️ for community empowerment and social impact**