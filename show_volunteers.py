"""Show volunteer locations from the database"""
from app import create_app, db
from app.models import User, Volunteer

app = create_app()

with app.app_context():
    volunteers = Volunteer.query.join(User).all()
    
    print("\n" + "="*120)
    print("📍 VOLUNTEER LOCATIONS IN HELPHAND DATABASE")
    print("="*120)
    print(f"\n{'Name':<20} {'Email':<30} {'Pincode':<10} {'Latitude':<12} {'Longitude':<12} {'Status':<12}")
    print("-"*120)
    
    for v in volunteers:
        print(f"{v.user_profile.name:<20} {v.user_profile.email:<30} {v.user_profile.pincode:<10} "
              f"{str(v.user_profile.latitude):<12} {str(v.user_profile.longitude):<12} "
              f"{v.verification_status:<12}")
    
    print("-"*120)
    print(f"\nTotal Volunteers: {len(volunteers)}")
    print(f"Approved: {len([v for v in volunteers if v.verification_status == 'approved'])}")
    print(f"Pending: {len([v for v in volunteers if v.verification_status == 'pending'])}")
    
    print("\n📌 LOCATION DETAILS:")
    print("="*120)
    for v in volunteers:
        print(f"\n{v.user_profile.name}:")
        print(f"  • Email: {v.user_profile.email}")
        print(f"  • Address: Pincode {v.user_profile.pincode}, Bangalore")
        print(f"  • GPS: {v.user_profile.latitude}, {v.user_profile.longitude}")
        print(f"  • Skills: {v.skills}")
        print(f"  • Rating: {v.rating}⭐ ({v.completed_tasks} tasks completed)")
        print(f"  • Status: {v.verification_status}")
        if v.subscription_type == 'pro':
            print(f"  • Subscription: PRO ✨")
    
    print("\n" + "="*120)
