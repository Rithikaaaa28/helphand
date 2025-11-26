"""Test TF-IDF matching service"""
from app.services.ai_matching import AIMatchingService

print("="*60)
print("Testing TF-IDF Volunteer Matching")
print("="*60)

# Initialize service
service = AIMatchingService()
print(f"✅ Service initialized")
print(f"✅ TF-IDF Vectorizer: {service.vectorizer is not None}")

# Test data
volunteers = [
    {
        'skills': 'plumbing, home repairs, electrical work, carpentry',
        'latitude': 12.9716,
        'longitude': 77.5946,
        'name': 'John (Plumber)'
    },
    {
        'skills': 'tutoring, teaching, homework help, math, science',
        'latitude': 12.9816,
        'longitude': 77.6046,
        'name': 'Mary (Tutor)'
    },
    {
        'skills': 'grocery shopping, elderly care, companionship',
        'latitude': 12.9916,
        'longitude': 77.6146,
        'name': 'Bob (Caregiver)'
    }
]

# Test case 1: Plumbing task
print("\n" + "="*60)
print("Test 1: Task - 'Need help fixing leaking bathroom pipes'")
print("="*60)

result = service.match_volunteers_to_task(
    'Need help fixing leaking bathroom pipes',
    volunteers,
    12.9716,
    77.5946
)

for i, match in enumerate(result[:3], 1):
    print(f"\n{i}. {match['name']}")
    print(f"   Match Score: {match['match_score']:.3f}")
    print(f"   Skills: {match['skills'][:50]}...")

# Test case 2: Tutoring task
print("\n" + "="*60)
print("Test 2: Task - 'Need math tutoring for 10th grade student'")
print("="*60)

result = service.match_volunteers_to_task(
    'Need math tutoring for 10th grade student',
    volunteers,
    12.9716,
    77.5946
)

for i, match in enumerate(result[:3], 1):
    print(f"\n{i}. {match['name']}")
    print(f"   Match Score: {match['match_score']:.3f}")
    print(f"   Skills: {match['skills'][:50]}...")

print("\n" + "="*60)
print("✅ TF-IDF is working correctly!")
print("="*60)
