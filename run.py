from app import create_app, db
import os

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from app.models import User, Volunteer
        
        # Create database tables
        db.create_all()
        
        # Add extracted_text column if it doesn't exist (migration)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('volunteers')]
            if 'extracted_text' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE volunteers ADD COLUMN extracted_text TEXT'))
                    conn.commit()
                print("✅ Added extracted_text column to volunteers table")
        except Exception as e:
            print(f"Note: Column migration - {e}")
        
        # Create demo users if they don't exist
        admin = User.query.filter_by(email='admin@helphand.com').first()
        if not admin:
            admin = User(
                name='Admin User',
                email='admin@helphand.com',
                role='admin',
                pincode='110001',
                verified=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        user = User.query.filter_by(email='user@helphand.com').first()
        if not user:
            user = User(
                name='Demo User',
                email='user@helphand.com',
                role='user',
                pincode='110001',
                latitude=28.6139,
                longitude=77.2090
            )
            user.set_password('user123')
            db.session.add(user)
        
        volunteer_user = User.query.filter_by(email='volunteer@helphand.com').first()
        if not volunteer_user:
            volunteer_user = User(
                name='Demo Volunteer',
                email='volunteer@helphand.com',
                role='volunteer',
                pincode='110001',
                latitude=28.6239,
                longitude=77.2190,
                verified=True
            )
            volunteer_user.set_password('volunteer123')
            db.session.add(volunteer_user)
            db.session.commit()
            
            volunteer = Volunteer(
                user_id=volunteer_user.id,
                skills='Home repairs, gardening, grocery shopping, elderly care, tutoring, pet care',
                verification_status='approved',
                rating=4.8,
                completed_tasks=15
            )
            db.session.add(volunteer)
        
        db.session.commit()
        print("Database initialized with demo data!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
