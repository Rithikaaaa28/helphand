from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import User, Volunteer, Task, Feedback
from app.ocr_service import OCRService
# Import AI service with fallback
try:
    from ml_models.matching_service import AIMatchingService
    ai_service = AIMatchingService()
except ImportError:
    try:
        from app.services.simple_ai import SimpleAIMatchingService
        ai_service = SimpleAIMatchingService()
        print("Using simple AI matching service (no ML dependencies)")
    except ImportError as e:
        print(f"Warning: No AI service available: {e}")
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

@volunteer_bp.route('/setup_profile', methods=['GET', 'POST'])
@login_required
def setup_profile():
    if current_user.role != 'volunteer':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        skills = request.form['skills']
        
        # Handle file upload
        document = request.files.get('document')
        document_path = None
        
        if document and document.filename:
            filename = secure_filename(document.filename)
            document_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
            os.makedirs(os.path.dirname(document_path), exist_ok=True)
            document.save(document_path)
        
        # Create volunteer profile
        volunteer = Volunteer(
            user_id=current_user.id,
            skills=skills,
            document_path=document_path,
            verification_status='pending'
        )
        
        db.session.add(volunteer)
        db.session.commit()
        
        flash('Profile created. Please wait for admin verification.', 'success')
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
    
    pending_volunteers = Volunteer.query.filter_by(verification_status='pending').all()
    
    # Process OCR for documents that haven't been processed yet
    for volunteer in pending_volunteers:
        if volunteer.document_path and not volunteer.extracted_text:
            try:
                ocr_result = ocr_service.extract_text_from_image(volunteer.document_path)
                if ocr_result.get('success'):
                    volunteer.extracted_text = ocr_result.get('cleaned_text', '')
                    db.session.commit()
            except Exception as e:
                print(f"OCR Error for volunteer {volunteer.id}: {e}")
    
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
    
    flash(f'Volunteer {volunteer.user_profile.name} rejected', 'error')
    return redirect(url_for('admin.verify_volunteers'))

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