"""
Comprehensive Database Viewer for HelpHand
Shows all tables with formatted output
"""

import sqlite3
from datetime import datetime

def show_database():
    """Display all database contents in a formatted way"""
    
    db_path = 'instance/helphand.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 HELPHAND DATABASE CONTENTS")
    print("="*80 + "\n")
    
    # 1. USERS TABLE
    print("👥 USERS TABLE")
    print("-" * 80)
    cursor.execute("SELECT id, name, email, role, pincode, verified, created_at FROM users")
    users = cursor.fetchall()
    
    print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Role':<10} {'Pincode':<8} {'Verified':<10} {'Created':<12}")
    print("-" * 80)
    for user in users:
        verified = '✅' if user['verified'] else '❌'
        created = user['created_at'][:10] if user['created_at'] else 'N/A'
        print(f"{user['id']:<5} {user['name'][:19]:<20} {user['email'][:29]:<30} {user['role']:<10} {user['pincode'] or 'N/A':<8} {verified:<10} {created:<12}")
    
    print(f"\n📈 Total Users: {len(users)}\n")
    
    # 2. VOLUNTEERS TABLE
    print("\n🤝 VOLUNTEERS TABLE")
    print("-" * 80)
    cursor.execute("""
        SELECT v.id, u.name, v.skills, v.verification_status, v.rating, 
               v.completed_tasks, v.subscription_type, v.premium_verified
        FROM volunteers v
        JOIN users u ON v.user_id = u.id
    """)
    volunteers = cursor.fetchall()
    
    print(f"{'ID':<5} {'Name':<20} {'Skills':<35} {'Status':<12} {'Rating':<8} {'Tasks':<6} {'Plan':<8}")
    print("-" * 80)
    for vol in volunteers:
        skills_short = vol['skills'][:33] + '..' if vol['skills'] and len(vol['skills']) > 35 else (vol['skills'] or 'N/A')
        rating = f"{vol['rating']:.1f}⭐" if vol['rating'] else 'N/A'
        premium = '💎' if vol['premium_verified'] else ''
        plan = (vol['subscription_type'] or 'basic') + premium
        
        print(f"{vol['id']:<5} {vol['name'][:19]:<20} {skills_short:<35} {vol['verification_status']:<12} {rating:<8} {vol['completed_tasks']:<6} {plan:<8}")
    
    print(f"\n📈 Total Volunteers: {len(volunteers)}\n")
    
    # 3. TASKS TABLE
    print("\n📋 TASKS TABLE")
    print("-" * 80)
    cursor.execute("""
        SELECT t.id, u.name as requester, t.title, t.category, t.status, 
               t.urgency, t.assigned_volunteer_id, t.is_commercial, t.payment_amount, t.created_at
        FROM tasks t
        JOIN users u ON t.user_id = u.id
    """)
    tasks = cursor.fetchall()
    
    print(f"{'ID':<5} {'Requester':<15} {'Title':<30} {'Category':<15} {'Status':<10} {'Type':<12} {'Assigned':<10}")
    print("-" * 80)
    for task in tasks:
        title_short = task['title'][:28] + '..' if len(task['title']) > 30 else task['title']
        assigned = f"Vol #{task['assigned_volunteer_id']}" if task['assigned_volunteer_id'] else 'None'
        task_type = f"₹{task['payment_amount']}" if task['is_commercial'] else 'Volunteer'
        
        print(f"{task['id']:<5} {task['requester'][:14]:<15} {title_short:<30} {(task['category'] or 'General')[:14]:<15} {task['status']:<10} {task_type:<12} {assigned:<10}")
    
    print(f"\n📈 Total Tasks: {len(tasks)}\n")
    
    # 4. FEEDBACK TABLE
    print("\n💬 FEEDBACK TABLE")
    print("-" * 80)
    cursor.execute("""
        SELECT f.id, t.title, u.name as user_name, v_user.name as volunteer_name,
               f.rating, f.sentiment_label, f.sentiment_score, f.created_at
        FROM feedback f
        JOIN tasks t ON f.task_id = t.id
        JOIN users u ON f.user_id = u.id
        JOIN volunteers v ON f.volunteer_id = v.id
        JOIN users v_user ON v.user_id = v_user.id
    """)
    feedback = cursor.fetchall()
    
    if feedback:
        print(f"{'ID':<5} {'Task':<25} {'User':<15} {'Volunteer':<15} {'Rating':<8} {'Sentiment':<20}")
        print("-" * 80)
        for fb in feedback:
            title_short = fb['title'][:23] + '..' if len(fb['title']) > 25 else fb['title']
            sentiment = f"{fb['sentiment_label']} ({fb['sentiment_score']:.2f})" if fb['sentiment_label'] else 'N/A'
            
            print(f"{fb['id']:<5} {title_short:<25} {fb['user_name'][:14]:<15} {fb['volunteer_name'][:14]:<15} {fb['rating']}⭐{'':<5} {sentiment:<20}")
        print(f"\n📈 Total Feedback: {len(feedback)}")
    else:
        print("❌ No feedback submitted yet")
    
    print()
    
    # 5. DATABASE STATISTICS
    print("\n📊 DATABASE STATISTICS")
    print("-" * 80)
    
    # User statistics
    cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
    role_counts = cursor.fetchall()
    print("\n👥 Users by Role:")
    for role in role_counts:
        print(f"   {role['role'].capitalize()}: {role['count']}")
    
    # Task statistics
    cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
    task_counts = cursor.fetchall()
    print("\n📋 Tasks by Status:")
    for status in task_counts:
        print(f"   {status['status'].capitalize()}: {status['count']}")
    
    # Volunteer statistics
    cursor.execute("SELECT verification_status, COUNT(*) as count FROM volunteers GROUP BY verification_status")
    vol_counts = cursor.fetchall()
    print("\n🤝 Volunteers by Status:")
    for vstatus in vol_counts:
        print(f"   {vstatus['verification_status'].capitalize()}: {vstatus['count']}")
    
    # 6. COMMERCIAL FEATURES
    print("\n\n💰 COMMERCIAL FEATURES")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN is_commercial = 1 THEN 1 ELSE 0 END) as commercial,
               SUM(CASE WHEN is_commercial = 1 THEN payment_amount ELSE 0 END) as total_revenue,
               SUM(CASE WHEN is_commercial = 1 THEN platform_fee ELSE 0 END) as platform_earnings
        FROM tasks
    """)
    commercial = cursor.fetchone()
    
    print(f"   Total Tasks: {commercial['total']}")
    print(f"   Commercial Tasks: {commercial['commercial']}")
    print(f"   Free Tasks: {commercial['total'] - commercial['commercial']}")
    print(f"   Total Revenue: ₹{commercial['total_revenue']:.2f}" if commercial['total_revenue'] else "   Total Revenue: ₹0.00")
    print(f"   Platform Earnings (8%): ₹{commercial['platform_earnings']:.2f}" if commercial['platform_earnings'] else "   Platform Earnings (8%): ₹0.00")
    
    # Subscription breakdown
    cursor.execute("SELECT subscription_type, COUNT(*) as count FROM volunteers GROUP BY subscription_type")
    subs = cursor.fetchall()
    
    if subs:
        print("\n📊 Subscription Plans:")
        for s in subs:
            plan = s['subscription_type'] or 'basic'
            print(f"   {plan.capitalize()}: {s['count']} volunteers")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ Database location: instance/helphand.db")
    print("✅ All data loaded successfully!")
    print("="*80 + "\n")

if __name__ == '__main__':
    try:
        show_database()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTrying basic view...")
        
        # Fallback to basic view
        conn = sqlite3.connect('instance/helphand.db')
        cursor = conn.cursor()
        
        print("\n📋 Basic Database Info:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        conn.close()
