"""
Database initialization script for HelpHand project
Creates all tables and optionally seeds with demo data
"""

from app import create_app, db
from app.models import User, Volunteer, Task, Feedback
from datetime import datetime

def init_database(seed_demo_data=True):
    """Initialize database with schema and optional demo data"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        if seed_demo_data:
            print("\n🌱 Seeding demo data...")
            seed_data()
            print("✅ Demo data seeded successfully!")
        
        print("\n📊 Database schema:")
        print("  - users: User accounts with roles (admin/user/volunteer)")
        print("  - volunteers: Volunteer profiles with skills and verification")
        print("  - tasks: Tasks posted by users")
        print("  - feedback: Ratings and sentiment analysis")
        print("\n✨ Database ready!")

def seed_data():
    """Seed database with demo data"""
    
    # Check if data already exists
    if User.query.first():
        print("⚠️  Data already exists, skipping seed...")
        return
    
    # Create Admin
    admin = User(
        name='Admin User',
        email='admin@helphand.com',
        role='admin',
        pincode='560001',
        latitude=12.9716,
        longitude=77.5946,
        verified=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create Demo User
    user1 = User(
        name='John Doe',
        email='user@helphand.com',
        role='user',
        pincode='560001',
        latitude=12.9716,
        longitude=77.5946
    )
    user1.set_password('user123')
    db.session.add(user1)
    
    # Create Another User
    user2 = User(
        name='Jane Smith',
        email='jane@helphand.com',
        role='user',
        pincode='560002',
        latitude=12.9816,
        longitude=77.6046
    )
    user2.set_password('user123')
    db.session.add(user2)
    
    # Create Volunteers
    volunteer1_user = User(
        name='Ramesh Kumar',
        email='volunteer@helphand.com',
        role='volunteer',
        pincode='560001',
        latitude=12.9766,
        longitude=77.5996,
        verified=True
    )
    volunteer1_user.set_password('volunteer123')
    db.session.add(volunteer1_user)
    db.session.flush()
    
    volunteer1 = Volunteer(
        user_id=volunteer1_user.id,
        skills='Home repairs, plumbing, electrical work, carpentry, painting',
        verification_status='approved',
        rating=4.8,
        completed_tasks=25,
        subscription_type='pro',
        premium_verified=True
    )
    db.session.add(volunteer1)
    
    volunteer2_user = User(
        name='Priya Sharma',
        email='priya@helphand.com',
        role='volunteer',
        pincode='560002',
        latitude=12.9866,
        longitude=77.6096,
        verified=True
    )
    volunteer2_user.set_password('volunteer123')
    db.session.add(volunteer2_user)
    db.session.flush()
    
    volunteer2 = Volunteer(
        user_id=volunteer2_user.id,
        skills='Tutoring, teaching, homework help, music lessons, language classes',
        verification_status='approved',
        rating=4.9,
        completed_tasks=30,
        subscription_type='basic'
    )
    db.session.add(volunteer2)
    
    volunteer3_user = User(
        name='Amit Patel',
        email='amit@helphand.com',
        role='volunteer',
        pincode='560001',
        latitude=12.9916,
        longitude=77.6146,
        verified=True
    )
    volunteer3_user.set_password('volunteer123')
    db.session.add(volunteer3_user)
    db.session.flush()
    
    volunteer3 = Volunteer(
        user_id=volunteer3_user.id,
        skills='Grocery shopping, elderly care, companionship, medication reminders, cooking',
        verification_status='approved',
        rating=4.7,
        completed_tasks=18
    )
    db.session.add(volunteer3)
    
    # Create pending volunteer for verification demo
    pending_vol_user = User(
        name='Neha Gupta',
        email='neha@helphand.com',
        role='volunteer',
        pincode='560003',
        latitude=12.9966,
        longitude=77.6196,
        verified=False
    )
    pending_vol_user.set_password('volunteer123')
    db.session.add(pending_vol_user)
    db.session.flush()
    
    pending_vol = Volunteer(
        user_id=pending_vol_user.id,
        skills='Pet care, dog walking, pet sitting, grooming assistance',
        verification_status='pending',
        rating=0.0,
        completed_tasks=0
    )
    db.session.add(pending_vol)
    
    db.session.commit()
    
    # Create sample tasks
    task1 = Task(
        user_id=user1.id,
        title='Need help with bathroom plumbing',
        description='Leaking faucet in bathroom needs urgent repair. Water dripping constantly.',
        category='Home Repairs',
        pincode='560001',
        latitude=12.9716,
        longitude=77.5946,
        status='pending',
        urgency='high'
    )
    db.session.add(task1)
    
    task2 = Task(
        user_id=user1.id,
        title='Math tutoring for 10th grade',
        description='Need math tutor for 10th grade student. Topics: algebra, geometry, trigonometry.',
        category='Education',
        pincode='560001',
        latitude=12.9716,
        longitude=77.5946,
        status='pending',
        urgency='medium'
    )
    db.session.add(task2)
    
    task3 = Task(
        user_id=user2.id,
        title='Grocery shopping assistance',
        description='Need someone to help with weekly grocery shopping for elderly parent. Heavy lifting required.',
        category='Shopping',
        pincode='560002',
        latitude=12.9816,
        longitude=77.6046,
        status='assigned',
        assigned_volunteer_id=volunteer3.id,
        urgency='low'
    )
    db.session.add(task3)
    
    # Create commercial task
    task4 = Task(
        user_id=user2.id,
        title='Website bug fixing',
        description='Need experienced developer to fix bugs in my small business website. PHP and MySQL knowledge required.',
        category='Professional Services',
        pincode='560002',
        latitude=12.9816,
        longitude=77.6046,
        status='pending',
        is_commercial=True,
        payment_amount=2000.0,
        platform_fee=160.0,  # 8%
        urgency='high'
    )
    db.session.add(task4)
    
    db.session.commit()
    
    print("  ✓ Created 1 admin, 2 users, 4 volunteers")
    print("  ✓ Created 4 sample tasks (3 community, 1 commercial)")
    print("\n📝 Demo credentials:")
    print("  Admin:     admin@helphand.com / admin123")
    print("  User:      user@helphand.com / user123")
    print("  Volunteer: volunteer@helphand.com / volunteer123")

if __name__ == '__main__':
    init_database(seed_demo_data=True)
