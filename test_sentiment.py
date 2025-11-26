"""Test sentiment analysis functionality"""
import sys
sys.path.insert(0, 'c:\\Users\\pattarit\\MJ')

from app.services.ai_matching import AIMatchingService

# Initialize the service
ai_service = AIMatchingService()

# Test cases
test_cases = [
    "This volunteer was amazing! Very helpful and professional.",
    "Terrible experience. The volunteer never showed up.",
    "It was okay, nothing special.",
    "Absolutely wonderful! Best volunteer ever! Highly recommend!",
    "Very disappointing and unprofessional behavior."
]

print("=" * 60)
print("SENTIMENT ANALYSIS TEST")
print("=" * 60)

for i, text in enumerate(test_cases, 1):
    result = ai_service.analyze_sentiment(text)
    print(f"\nTest {i}: {text}")
    print(f"  Label: {result['label']}")
    print(f"  Compound Score: {result['compound']:.3f}")
    print(f"  Positive: {result['pos']:.3f}, Negative: {result['neg']:.3f}, Neutral: {result['neu']:.3f}")

print("\n" + "=" * 60)
print("Test completed!")
