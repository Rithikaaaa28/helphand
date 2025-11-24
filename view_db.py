"""
Quick script to view database contents
Run: python view_db.py
"""
from app import create_app, db
from app.models import User, Volunteer, Task, Feedback

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("📊 HELPHAND DATABASE CONTENTS")
    print("="*60)
    
    # Users
    users = User.query.all()
    print(f"\n👥 USERS ({len(users)} total):")
    print("-" * 60)
    for user in users:
        print(f"  • {user.name} ({user.email}) - Role: {user.role}")
        print(f"    ID: {user.id} | Verified: {user.verified} | Pincode: {user.pincode}")
    
    # Volunteers
    volunteers = Volunteer.query.all()
    print(f"\n🤝 VOLUNTEERS ({len(volunteers)} total):")
    print("-" * 60)
    for vol in volunteers:
        print(f"  • {vol.user_profile.name}")
        print(f"    Status: {vol.verification_status} | Rating: {vol.rating:.1f}/5.0")
        print(f"    Completed: {vol.completed_tasks} tasks | Skills: {vol.skills[:50]}...")
    
    # Tasks
    tasks = Task.query.all()
    print(f"\n📋 TASKS ({len(tasks)} total):")
    print("-" * 60)
    for task in tasks:
        print(f"  • {task.title}")
        print(f"    Status: {task.status} | Posted by: {task.task_creator.name}")
        if task.assigned_volunteer_id:
            print(f"    Assigned to: {task.assigned_volunteer.user_profile.name}")
        print(f"    Commercial: {task.is_commercial} | Payment: ₹{task.payment_amount}")
    
    # Feedback
    feedbacks = Feedback.query.all()
    print(f"\n⭐ FEEDBACK ({len(feedbacks)} total):")
    print("-" * 60)
    for fb in feedbacks:
        print(f"  • Task: {fb.related_task.title}")
        print(f"    Rating: {fb.rating}/5 | Sentiment: {fb.sentiment_label} ({fb.sentiment_score:.2f})")
        print(f"    Text: {fb.text[:60]}...")
    
    print("\n" + "="*60)
    print("✅ Database view complete!")
    print("="*60 + "\n")
