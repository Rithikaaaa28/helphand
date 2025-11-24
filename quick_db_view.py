import sqlite3

conn = sqlite3.connect('instance/helphand.db')
cursor = conn.cursor()

print("\n" + "="*60)
print("📊 HELPHAND DATABASE - Quick View")
print("="*60)

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("\n📁 Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Count records
print("\n📈 Record Counts:")
cursor.execute("SELECT COUNT(*) FROM users")
print(f"  Users: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM volunteers")
print(f"  Volunteers: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM tasks")
print(f"  Tasks: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM feedback")
print(f"  Feedback: {cursor.fetchone()[0]}")

# Show some sample data
print("\n👤 Sample Users:")
cursor.execute("SELECT id, name, email, role FROM users LIMIT 5")
for row in cursor.fetchall():
    print(f"  {row[0]}. {row[1]} ({row[2]}) - {row[3]}")

print("\n📋 Sample Tasks:")
cursor.execute("SELECT id, title, status FROM tasks LIMIT 5")
for row in cursor.fetchall():
    print(f"  {row[0]}. {row[1]} - Status: {row[2]}")

print("\n" + "="*60)
print("✅ Database location: instance/helphand.db")
print("="*60 + "\n")

conn.close()
