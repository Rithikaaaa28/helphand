from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from app import db
from app.models import User, Volunteer, Task, Feedback
from app.ocr_service import OCRService

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
# Import AI service with TF-IDF and ML capabilities
ai_service = None
try:
    from app.services.ai_matching import AIMatchingService
    ai_service = AIMatchingService()
    print("✅ Using AI matching service with TF-IDF and Cosine Similarity")
except ImportError as e:
    print(f"⚠️  ML service unavailable, falling back to simple matching: {e}")
    try:
        from app.services.simple_ai import SimpleAIMatchingService
        ai_service = SimpleAIMatchingService()
        print("Using simple keyword-based matching service")
    except ImportError:
        print(f"Warning: No AI service available")
        ai_service = None

# Create blueprints
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)
volunteer_bp = Blueprint('volunteer', __name__)

# Initialize OCR service
ocr_service = OCRService()

# Authentication routes
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        pincode = request.form.get('pincode')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        # Create user
        user = User(name=name, email=email, role=role, pincode=pincode)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            session.permanent = True
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'volunteer':
                return redirect(url_for('volunteer.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))

# Main routes
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'volunteer':
        return redirect(url_for('volunteer.dashboard'))
    
    # User dashboard
    user_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    return render_template('user_dashboard.html', tasks=user_tasks)

@main_bp.route('/post_task', methods=['GET', 'POST'])
@login_required
def post_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form.get('category')
        pincode = request.form.get('pincode')
        is_commercial = request.form.get('is_commercial') == 'on'
        payment_amount = float(request.form.get('payment_amount', 0))
        urgency = request.form.get('urgency', 'medium')
        
        # Calculate platform fee for commercial tasks
        platform_fee = 0
        if is_commercial and payment_amount > 0:
            platform_fee = payment_amount * (current_app.config['PLATFORM_FEE_PERCENTAGE'] / 100)
        
        task = Task(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            pincode=pincode or current_user.pincode,
            latitude=current_user.latitude,
            longitude=current_user.longitude,
            is_commercial=is_commercial,
            payment_amount=payment_amount,
            platform_fee=platform_fee,
            urgency=urgency
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task posted successfully', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('post_task.html')

@main_bp.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Get matched volunteers if task is pending
    matched_volunteers = []
    if task.status == 'pending' and ai_service:
        # Get approved volunteers
        volunteers = Volunteer.query.filter_by(verification_status='approved').all()
        
        # Filter by location first
        if task.latitude and task.longitude:
            volunteers = ai_service.filter_volunteers_by_location(
                volunteers,
                task.latitude,
                task.longitude,
                radius_km=current_app.config.get('DEFAULT_RADIUS_KM', 10),
                fallback_radius_km=current_app.config.get('FALLBACK_RADIUS_KM', 50)
            )
        
        # Rank volunteers using AI matching
        matched_volunteers = ai_service.rank_volunteers_for_task(task, volunteers, max_results=5)
    
    return render_template('view_task.html', task=task, matched_volunteers=matched_volunteers)

@main_bp.route('/assign_task/<int:task_id>/<int:volunteer_id>')
@login_required
def assign_task(task_id, volunteer_id):
    task = Task.query.get_or_404(task_id)
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    
    if task.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('main.dashboard'))
    
    task.status = 'assigned'
    task.assigned_volunteer_id = volunteer_id
    
    db.session.commit()
    
    flash(f'Task assigned to {volunteer.user_profile.name}', 'success')
    return redirect(url_for('main.view_task', task_id=task_id))

@main_bp.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if task.user_id != current_user.id or task.status != 'assigned':
        flash('Unauthorized', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Mark task as completed
    task.status = 'completed'
    task.completed_at = db.func.now()
    
    # Update volunteer stats
    volunteer = task.assigned_volunteer
    volunteer.completed_tasks += 1
    
    db.session.commit()
    
    flash('Task marked as completed', 'success')
    return redirect(url_for('main.submit_feedback', task_id=task_id))

@main_bp.route('/feedback/<int:task_id>', methods=['GET', 'POST'])
@login_required
def submit_feedback(task_id):
    task = Task.query.get_or_404(task_id)
    
    if task.user_id != current_user.id or task.status != 'completed':
        flash('Unauthorized', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        text = request.form.get('text', '')
        
        # Analyze sentiment using AI service
        sentiment_result = {'compound': 0.0, 'label': 'neutral', 'pos': 0.0, 'neg': 0.0, 'neu': 1.0}
        if ai_service:
            sentiment_result = ai_service.analyze_sentiment(text)
        
        # Create feedback
        feedback = Feedback(
            task_id=task_id,
            user_id=current_user.id,
            volunteer_id=task.assigned_volunteer_id,
            rating=rating,
            text=text,
            sentiment_score=sentiment_result['compound'],
            sentiment_label=sentiment_result['label']
        )
        
        db.session.add(feedback)
        
        # Update volunteer rating
        volunteer = task.assigned_volunteer
        if ai_service:
            new_rating = ai_service.update_volunteer_rating(volunteer, sentiment_result, rating)
            volunteer.rating = new_rating
        else:
            # Simple fallback: just use user rating
            total_tasks = volunteer.completed_tasks
            if total_tasks == 0:
                volunteer.rating = rating
            else:
                volunteer.rating = ((volunteer.rating * (total_tasks - 1)) + rating) / total_tasks
        
        db.session.commit()
        
        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('feedback.html', task=task)

# Volunteer routes
@volunteer_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'volunteer':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    volunteer = current_user.volunteer_profile
    if not volunteer:
        return redirect(url_for('volunteer.setup_profile'))
    
    # Get available tasks
    available_tasks = Task.query.filter_by(status='pending').order_by(Task.created_at.desc()).limit(10).all()
    
    # Get assigned tasks
    assigned_tasks = Task.query.filter_by(
        assigned_volunteer_id=volunteer.id,
        status='assigned'
    ).order_by(Task.created_at.desc()).all()
    
    return render_template('volunteer_dashboard.html', 
                         volunteer=volunteer, 
                         available_tasks=available_tasks,
                         assigned_tasks=assigned_tasks)

@volunteer_bp.route('/process_premium_payment', methods=['POST'])
@login_required
def process_premium_payment():
    """Simulate premium verification payment processing"""
    if current_user.role != 'volunteer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # In production, integrate with payment gateway (Razorpay, Stripe, etc.)
    # For demo purposes, we'll return success
    amount = current_app.config.get('PREMIUM_VERIFICATION_FEE', 99)
    
    return jsonify({
        'success': True,
        'message': f'Payment of ₹{amount} will be processed',
        'amount': amount
    })

@volunteer_bp.route('/upgrade_to_pro', methods=['GET', 'POST'])
@login_required
def upgrade_to_pro():
    """Upgrade volunteer to Pro subscription"""
    if current_user.role != 'volunteer':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Redirect GET requests to dashboard
    if request.method == 'GET':
        return redirect(url_for('volunteer.dashboard'))
    
    volunteer = current_user.volunteer_profile
    
    if not volunteer:
        flash('Please complete your volunteer profile first', 'error')
        return redirect(url_for('volunteer.setup_profile'))
    
    if volunteer.subscription_type == 'pro':
        flash('You already have a Pro subscription!', 'info')
        return redirect(url_for('volunteer.dashboard'))
    
    # In production, integrate with payment gateway (Razorpay, Stripe, etc.)
    # For demo purposes, we'll simulate successful payment
    pro_fee = current_app.config.get('PRO_SUBSCRIPTION_FEE', 199)
    
    # Update volunteer to Pro
    volunteer.subscription_type = 'pro'
    volunteer.subscription_expires = datetime.utcnow() + timedelta(days=30)
    
    db.session.commit()
    
    flash(f'Success! Payment of ₹{pro_fee} processed. You are now a Pro Volunteer!', 'success')
    return redirect(url_for('volunteer.dashboard'))

@volunteer_bp.route('/setup_profile', methods=['GET', 'POST'])
@login_required
def setup_profile():
    if current_user.role != 'volunteer':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        skills = request.form['skills']
        premium_verification = request.form.get('premium_verification') == 'on'
        
        # Handle file upload
        document = request.files.get('document')
        document_path = None
        
        if document and document.filename:
            # Check if file type is allowed
            if not allowed_file(document.filename):
                flash('Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF).', 'error')
                return redirect(url_for('volunteer.setup_profile'))
            
            filename = secure_filename(document.filename)
            # Add timestamp to filename to avoid conflicts
            import time
            filename = f"{int(time.time())}_{filename}"
            
            # Ensure upload directory exists
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
            os.makedirs(upload_dir, exist_ok=True)
            
            document_path = os.path.join(upload_dir, filename)
            document.save(document_path)
            
            # Store relative path in database
            document_path = os.path.join('uploads', 'documents', filename)
        else:
            flash('Please upload a verification document.', 'error')
            return redirect(url_for('volunteer.setup_profile'))
        
        # Handle premium verification
        if premium_verification:
            # In a real app, this would process payment via payment gateway
            # For demo, we'll simulate payment success
            flash(f'Payment of ₹{current_app.config.get("PREMIUM_VERIFICATION_FEE", 99)} processed successfully!', 'success')
            verification_status = 'pending'
            is_premium = True
            message = 'Premium verification requested! Your profile will be verified within 2 hours.'
        else:
            verification_status = 'pending'
            is_premium = False
            message = 'Profile created. Please wait for admin verification (typically 24-48 hours).'
        
        # Create volunteer profile
        volunteer = Volunteer(
            user_id=current_user.id,
            skills=skills,
            document_path=document_path,
            verification_status=verification_status,
            premium_verified=is_premium
        )
        
        db.session.add(volunteer)
        db.session.commit()
        
        flash(message, 'success')
        return redirect(url_for('volunteer.dashboard'))
    
    return render_template('volunteer_setup.html')

@volunteer_bp.route('/task/<int:task_id>')
@login_required
def view_task_detail(task_id):
    if current_user.role != 'volunteer':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    task = Task.query.get_or_404(task_id)
    volunteer = current_user.volunteer_profile
    
    if not volunteer or volunteer.verification_status != 'approved':
        flash('You must be a verified volunteer to view tasks', 'error')
        return redirect(url_for('volunteer.dashboard'))
    
    return render_template('volunteer_task_detail.html', task=task, volunteer=volunteer)

@volunteer_bp.route('/apply_task/<int:task_id>', methods=['POST'])
@login_required
def apply_task(task_id):
    if current_user.role != 'volunteer':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    volunteer = current_user.volunteer_profile
    
    if not volunteer or volunteer.verification_status != 'approved':
        flash('You must be a verified volunteer to apply for tasks', 'error')
        return redirect(url_for('volunteer.dashboard'))
    
    task = Task.query.get_or_404(task_id)
    
    if task.status != 'pending':
        flash('This task is no longer available', 'error')
        return redirect(url_for('volunteer.dashboard'))
    
    # Auto-assign the task to the volunteer (simplified flow)
    # In a real app, you might want to notify the user for approval
    task.status = 'assigned'
    task.assigned_volunteer_id = volunteer.id
    
    db.session.commit()
    
    flash(f'You have successfully applied for the task: {task.title}', 'success')
    return redirect(url_for('volunteer.dashboard'))

# Admin routes
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get statistics
    total_users = User.query.count()
    total_volunteers = Volunteer.query.count()
    pending_verifications = Volunteer.query.filter_by(verification_status='pending').count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    
    stats = {
        'total_users': total_users,
        'total_volunteers': total_volunteers,
        'pending_verifications': pending_verifications,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks
    }
    
    return render_template('admin_dashboard.html', stats=stats)

@admin_bp.route('/verify_volunteers')
@login_required
def verify_volunteers():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get pending volunteers, sort premium first
    pending_volunteers = Volunteer.query.filter_by(verification_status='pending')\
        .order_by(Volunteer.premium_verified.desc(), Volunteer.created_at.asc()).all()
    
    # Process OCR for documents that haven't been processed yet
    for volunteer in pending_volunteers:
        if volunteer.document_path and not volunteer.extracted_text:
            try:
                # Convert relative path to absolute path for OCR
                # Handle both old format (app/static/uploads/...) and new format (uploads/...)
                doc_path = volunteer.document_path
                if doc_path.startswith('app/static/'):
                    # Old format - already has app/static prefix
                    absolute_path = os.path.join(os.getcwd(), doc_path)
                else:
                    # New format - needs static folder prefix
                    absolute_path = os.path.join(current_app.static_folder, doc_path)
                
                print(f"DEBUG: Processing volunteer {volunteer.id}")
                print(f"DEBUG: Original path: {doc_path}")
                print(f"DEBUG: Absolute path: {absolute_path}")
                print(f"DEBUG: File exists: {os.path.exists(absolute_path)}")
                
                # Use comprehensive document verification
                verification_result = ocr_service.verify_volunteer_document(
                    absolute_path, 
                    volunteer.user_profile.name
                )
                
                if verification_result.get('verified'):
                    volunteer.extracted_text = verification_result.get('extracted_info', {}).get('name', '')
                    # Add verification metadata
                    volunteer.verification_notes = f"Auto-verified (Score: {verification_result.get('match_score', 0):.2f})"
                else:
                    volunteer.extracted_text = verification_result.get('reason', 'Verification failed')
                    volunteer.verification_notes = f"Needs manual review: {verification_result.get('reason', 'Unknown')}"
                
                db.session.commit()
            except Exception as e:
                print(f"OCR Error for volunteer {volunteer.id}: {e}")
                volunteer.verification_notes = f"OCR Error: {str(e)}"
                db.session.commit()
    
    return render_template('verify_volunteers.html', volunteers=pending_volunteers)

@admin_bp.route('/approve_volunteer/<int:volunteer_id>')
@login_required
def approve_volunteer(volunteer_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    volunteer.verification_status = 'approved'
    volunteer.user_profile.verified = True
    
    db.session.commit()
    
    flash(f'Volunteer {volunteer.user_profile.name} approved', 'success')
    return redirect(url_for('admin.verify_volunteers'))

@admin_bp.route('/reject_volunteer/<int:volunteer_id>')
@login_required
def reject_volunteer(volunteer_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    volunteer.verification_status = 'rejected'
    
    db.session.commit()
    
    flash(f'Volunteer {volunteer.user_profile.name} rejected', 'success')
    return redirect(url_for('admin.verify_volunteers'))

@admin_bp.route('/api/verify_document/<int:volunteer_id>', methods=['POST'])
@login_required
def api_verify_document(volunteer_id):
    """API endpoint for real-time OCR verification"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    
    if not volunteer.document_path:
        return jsonify({'error': 'No document uploaded'}), 400
    
    try:
        # Convert relative path to absolute path for OCR
        # Handle both old format (app/static/uploads/...) and new format (uploads/...)
        doc_path = volunteer.document_path
        if doc_path.startswith('app/static/'):
            # Old format - already has app/static prefix
            absolute_path = os.path.join(os.getcwd(), doc_path)
        else:
            # New format - needs static folder prefix
            absolute_path = os.path.join(current_app.static_folder, doc_path)
        
        # Perform OCR verification
        verification_result = ocr_service.verify_volunteer_document(
            absolute_path,
            volunteer.user_profile.name
        )
        
        return jsonify({
            'success': True,
            'verified': verification_result.get('verified', False),
            'reason': verification_result.get('reason', ''),
            'match_score': verification_result.get('match_score', 0.0),
            'confidence': verification_result.get('confidence', 0.0),
            'extracted_info': verification_result.get('extracted_info', {})
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    flash(f'Volunteer {volunteer.user_profile.name} rejected', 'error')
    return redirect(url_for('admin.verify_volunteers'))

@admin_bp.route('/reports')
@login_required
def view_reports():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    
    # Basic stats
    total_users = User.query.count()
    total_volunteers = Volunteer.query.count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    pending_tasks = Task.query.filter_by(status='pending').count()
    assigned_tasks = Task.query.filter_by(status='assigned').count()
    
    # Volunteer stats
    verified_volunteers = Volunteer.query.filter_by(verification_status='verified').count()
    pending_volunteers = Volunteer.query.filter_by(verification_status='pending').count()
    
    # Task completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Average rating
    avg_rating = db.session.query(func.avg(Volunteer.rating)).scalar() or 0.0
    
    # Feedback stats
    total_feedback = Feedback.query.count()
    avg_feedback_rating = db.session.query(func.avg(Feedback.rating)).scalar() or 0.0
    
    # Top volunteers by completed tasks
    top_volunteers = db.session.query(
        Volunteer, 
        func.count(Task.id).label('completed_count')
    ).join(Task, Task.assigned_volunteer_id == Volunteer.id)\
     .filter(Task.status == 'completed')\
     .group_by(Volunteer.id)\
     .order_by(func.count(Task.id).desc())\
     .limit(5)\
     .all()
    
    # Recent tasks
    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(10).all()
    
    # Tasks by category (if you have categories)
    category_stats = db.session.query(
        Task.title,
        func.count(Task.id).label('count')
    ).group_by(Task.title).all()
    
    # Monthly task trends (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_tasks = db.session.query(
        extract('month', Task.created_at).label('month'),
        func.count(Task.id).label('count')
    ).filter(Task.created_at >= six_months_ago)\
     .group_by(extract('month', Task.created_at))\
     .all()
    
    # User registration trends
    monthly_users = db.session.query(
        extract('month', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= six_months_ago)\
     .group_by(extract('month', User.created_at))\
     .all()
    
    # Commercial stats - Calculate from actual database
    pro_subscriptions = Volunteer.query.filter_by(subscription_type='pro').count()
    premium_verifications = Volunteer.query.filter_by(premium_verified=True).count()
    paid_tasks = Task.query.filter_by(is_commercial=True).count()
    completed_paid_tasks = Task.query.filter_by(is_commercial=True, status='completed').count()
    
    # Calculate revenue (simulated - in production, this would come from payment records)
    pro_revenue = pro_subscriptions * current_app.config.get('PRO_SUBSCRIPTION_FEE', 199)
    premium_revenue = premium_verifications * current_app.config.get('PREMIUM_VERIFICATION_FEE', 99)
    platform_fees = db.session.query(func.sum(Task.platform_fee)).filter(
        Task.status == 'completed', 
        Task.is_commercial == True
    ).scalar() or 0.0
    
    commercial_stats = {
        'monthly_revenue': int(pro_revenue + premium_revenue + platform_fees),
        'pro_subscriptions': pro_subscriptions,
        'platform_fees': int(platform_fees),
        'premium_verifications': premium_verifications,
        'revenue_growth': 15,  # Mock data - would require historical data
        'total_paid_tasks': paid_tasks
    }
    
    return render_template('admin_reports.html',
                         total_users=total_users,
                         total_volunteers=total_volunteers,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks,
                         assigned_tasks=assigned_tasks,
                         verified_volunteers=verified_volunteers,
                         pending_volunteers=pending_volunteers,
                         completion_rate=completion_rate,
                         avg_rating=avg_rating,
                         total_feedback=total_feedback,
                         avg_feedback_rating=avg_feedback_rating,
                         top_volunteers=top_volunteers,
                         recent_tasks=recent_tasks,
                         category_stats=category_stats,
                         monthly_tasks=monthly_tasks,
                         monthly_users=monthly_users,
                         commercial_stats=commercial_stats)

# API routes for location
@main_bp.route('/api/update_location', methods=['POST'])
@login_required
def update_location():
    data = request.get_json()
    
    if 'latitude' in data and 'longitude' in data:
        current_user.latitude = float(data['latitude'])
        current_user.longitude = float(data['longitude'])
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 400

# User analytics route
@main_bp.route('/analytics')
@login_required
def user_analytics():
    if current_user.role != 'user':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Get user's tasks
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Calculate stats
    total_tasks = len(user_tasks)
    completed_tasks = len([t for t in user_tasks if t.status == 'completed'])
    pending_tasks = len([t for t in user_tasks if t.status == 'pending'])
    assigned_tasks = len([t for t in user_tasks if t.status == 'assigned'])
    
    # Calculate completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get feedback stats
    task_ids = [t.id for t in user_tasks]
    feedback_count = Feedback.query.filter(Feedback.task_id.in_(task_ids)).count() if task_ids else 0
    avg_feedback = db.session.query(func.avg(Feedback.rating))\
        .filter(Feedback.task_id.in_(task_ids)).scalar() if task_ids else 0.0
    
    # Monthly trends (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    recent_tasks = [t for t in user_tasks if t.created_at >= six_months_ago]
    
    # Group by month
    monthly_data = {}
    for task in recent_tasks:
        month_key = task.created_at.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'total': 0, 'completed': 0}
        monthly_data[month_key]['total'] += 1
        if task.status == 'completed':
            monthly_data[month_key]['completed'] += 1
    
    return render_template('user_analytics.html',
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks,
                         assigned_tasks=assigned_tasks,
                         completion_rate=completion_rate,
                         feedback_count=feedback_count,
                         avg_feedback=avg_feedback or 0.0,
                         monthly_data=monthly_data,
                         recent_tasks=user_tasks[-10:])

# Admin settings route
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Handle settings update
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin.settings'))
    
    # Get current settings (mock data - implement with a Settings model if needed)
    settings_data = {
        'platform_name': 'HelpHand',
        'platform_fee_percentage': 5.0,
        'auto_verify_volunteers': False,
        'require_volunteer_documents': True,
        'max_task_distance_km': 50,
        'enable_commercial_tasks': True,
        'enable_notifications': True,
        'maintenance_mode': False
    }
    
    return render_template('admin_settings.html', settings=settings_data)

# Export routes
@admin_bp.route('/export/csv')
@login_required
def export_csv():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    import csv
    from io import StringIO
    from flask import make_response
    
    # Create CSV data
    si = StringIO()
    writer = csv.writer(si)
    
    # Write headers
    writer.writerow(['ID', 'Name', 'Email', 'Role', 'Created At'])
    
    # Write user data
    users = User.query.all()
    for user in users:
        writer.writerow([user.id, user.name, user.email, user.role, user.created_at.strftime('%Y-%m-%d')])
    
    # Create response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=users_export.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

@admin_bp.route('/export/pdf')
@login_required
def export_pdf():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    flash('PDF export functionality will be available soon. Please use CSV export for now.', 'info')
    return redirect(url_for('admin.view_reports'))

@admin_bp.route('/export/excel')
@login_required
def export_excel():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    flash('Excel export functionality will be available soon. Please use CSV export for now.', 'info')
    return redirect(url_for('admin.view_reports'))