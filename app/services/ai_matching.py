import numpy as np
from typing import List, Dict, Any
import math

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Using fallback matching.")

try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.stem import PorterStemmer
    import nltk
    import re
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("Warning: NLTK not available. Trying TextBlob for sentiment analysis.")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("Warning: TextBlob not available.")

class AIMatchingService:
    def __init__(self):
        self.vectorizer = None
        self.stemmer = PorterStemmer() if NLTK_AVAILABLE else None
        if SKLEARN_AVAILABLE:
            # Use custom analyzer with stemming for better word matching
            if self.stemmer:
                def stemming_analyzer(text):
                    # Remove punctuation first, then split and stem
                    text = re.sub(r'[^\w\s]', ' ', text.lower())
                    words = text.split()
                    return [self.stemmer.stem(word) for word in words if len(word) > 2]
                self.vectorizer = TfidfVectorizer(
                    analyzer=stemming_analyzer,
                    max_features=1000
                )
            else:
                self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    
    def match_volunteers_to_task(self, task_description: str, volunteers: List[Dict], 
                               task_lat: float = None, task_lon: float = None) -> List[Dict]:
        """
        Match volunteers to a task using AI-based similarity and location proximity
        """
        if not volunteers:
            return []
        
        # Prepare volunteer data
        volunteer_skills = [vol.get('skills', '') or '' for vol in volunteers]
        
        if SKLEARN_AVAILABLE and self.vectorizer and any(volunteer_skills):
            return self._sklearn_matching(task_description, volunteers, volunteer_skills, task_lat, task_lon)
        else:
            return self._fallback_matching(task_description, volunteers, task_lat, task_lon)
    
    def _sklearn_matching(self, task_description: str, volunteers: List[Dict], 
                         volunteer_skills: List[str], task_lat: float, task_lon: float) -> List[Dict]:
        """AI-based matching using TF-IDF and cosine similarity"""
        try:
            # Create corpus
            documents = [task_description] + volunteer_skills
            
            # Vectorize
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            # Calculate similarities
            task_vector = tfidf_matrix[0]
            volunteer_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(task_vector, volunteer_vectors)[0]
            
            # Calculate final scores
            for i, volunteer in enumerate(volunteers):
                similarity_score = similarities[i]
                proximity_score = self._calculate_proximity_score(
                    volunteer.get('latitude'), volunteer.get('longitude'),
                    task_lat, task_lon
                )
                
                # Weighted final score: 85% similarity + 15% proximity (strongly prioritize skill match)
                final_score = (0.85 * similarity_score) + (0.15 * proximity_score)
                volunteer['match_score'] = final_score
                volunteer['similarity_score'] = similarity_score
                volunteer['proximity_score'] = proximity_score
            
            # Sort by match score
            return sorted(volunteers, key=lambda x: x.get('match_score', 0), reverse=True)
            
        except Exception as e:
            print(f"Error in sklearn matching: {e}")
            return self._fallback_matching(task_description, volunteers, task_lat, task_lon)
    
    def _fallback_matching(self, task_description: str, volunteers: List[Dict], 
                          task_lat: float, task_lon: float) -> List[Dict]:
        """Simple keyword-based fallback matching"""
        task_words = set(task_description.lower().split())
        
        for volunteer in volunteers:
            skills = volunteer.get('skills', '') or ''
            skill_words = set(skills.lower().split())
            
            # Simple keyword matching
            common_words = task_words.intersection(skill_words)
            similarity_score = len(common_words) / max(len(task_words), 1)
            
            # Calculate proximity
            proximity_score = self._calculate_proximity_score(
                volunteer.get('latitude'), volunteer.get('longitude'),
                task_lat, task_lon
            )
            
            # Weighted score
            final_score = (0.6 * similarity_score) + (0.4 * proximity_score)
            volunteer['match_score'] = final_score
            volunteer['similarity_score'] = similarity_score
            volunteer['proximity_score'] = proximity_score
        
        return sorted(volunteers, key=lambda x: x.get('match_score', 0), reverse=True)
    
    def _calculate_proximity_score(self, vol_lat, vol_lon, task_lat, task_lon):
        """Calculate proximity score (1 = very close, 0 = far)"""
        if not all([vol_lat, vol_lon, task_lat, task_lon]):
            return 0.5  # Default score if coordinates missing
        
        distance_km = self._haversine_distance(vol_lat, vol_lon, task_lat, task_lon)
        
        # Convert distance to score (closer = higher score)
        if distance_km <= 1:
            return 1.0
        elif distance_km <= 5:
            return 0.8
        elif distance_km <= 10:
            return 0.6
        elif distance_km <= 25:
            return 0.4
        else:
            return 0.2
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def rank_volunteers_for_task(self, task, volunteers, max_results=10):
        """
        Rank volunteers for a specific task using AI matching
        Returns a list of volunteer dictionaries sorted by match score
        """
        # Prepare volunteer data
        volunteer_data = []
        for vol in volunteers:
            volunteer_data.append({
                'id': vol.id,
                'user_id': vol.user_id,
                'name': vol.user_profile.name,
                'skills': vol.skills or '',
                'rating': vol.rating,
                'completed_tasks': vol.completed_tasks,
                'latitude': vol.user_profile.latitude,
                'longitude': vol.user_profile.longitude,
                'subscription_type': vol.subscription_type,
                'premium_verified': vol.premium_verified
            })
        
        # Combine title and description for better matching
        task_text = f"{task.title} {task.description}"
        if task.category:
            task_text += f" {task.category}"
        
        # Perform matching
        matched = self.match_volunteers_to_task(
            task_text,
            volunteer_data,
            task.latitude,
            task.longitude
        )
        
        # Apply additional filters (prioritize premium, higher ratings)
        for vol in matched:
            # Boost score for premium subscribers
            if vol.get('premium_verified'):
                vol['match_score'] *= 1.1
            
            # Boost score based on rating
            rating_boost = vol.get('rating', 0) / 10  # 0-0.5 boost
            vol['match_score'] += rating_boost
        
        # Re-sort after applying boosts
        matched = sorted(matched, key=lambda x: x.get('match_score', 0), reverse=True)
        
        return matched[:max_results]
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of feedback text
        Returns: {'compound': float, 'label': str, 'pos': float, 'neg': float, 'neu': float}
        """
        if not text or len(text.strip()) == 0:
            return {
                'compound': 0.0,
                'label': 'neutral',
                'pos': 0.0,
                'neg': 0.0,
                'neu': 1.0
            }
        
        # Try VADER first (better for social media/informal text)
        if NLTK_AVAILABLE:
            try:
                sia = SentimentIntensityAnalyzer()
                scores = sia.polarity_scores(text)
                
                # Determine label based on compound score
                if scores['compound'] >= 0.05:
                    label = 'positive'
                elif scores['compound'] <= -0.05:
                    label = 'negative'
                else:
                    label = 'neutral'
                
                return {
                    'compound': scores['compound'],
                    'label': label,
                    'pos': scores['pos'],
                    'neg': scores['neg'],
                    'neu': scores['neu']
                }
            except Exception as e:
                print(f"VADER error: {e}")
        
        # Fallback to TextBlob
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity  # -1 to 1
                
                # Convert to VADER-like format
                if polarity > 0.1:
                    label = 'positive'
                elif polarity < -0.1:
                    label = 'negative'
                else:
                    label = 'neutral'
                
                return {
                    'compound': polarity,
                    'label': label,
                    'pos': max(0, polarity),
                    'neg': max(0, -polarity),
                    'neu': 1 - abs(polarity)
                }
            except Exception as e:
                print(f"TextBlob error: {e}")
        
        # Ultimate fallback - neutral sentiment
        return {
            'compound': 0.0,
            'label': 'neutral',
            'pos': 0.0,
            'neg': 0.0,
            'neu': 1.0
        }
    
    def update_volunteer_rating(self, volunteer, sentiment_result, user_rating):
        """
        Update volunteer rating based on sentiment analysis and user rating
        """
        # Weight: 60% user rating, 40% sentiment
        sentiment_score = sentiment_result.get('compound', 0)
        
        # Convert sentiment (-1 to 1) to rating scale (1 to 5)
        sentiment_rating = (sentiment_score + 1) * 2.5  # Maps -1->1, 0->2.5, 1->4
        
        # Combine ratings
        combined_rating = (0.6 * user_rating) + (0.4 * sentiment_rating)
        
        # Update volunteer's average rating
        total_tasks = volunteer.completed_tasks
        if total_tasks == 0:
            new_rating = combined_rating
        else:
            # Running average
            current_rating = volunteer.rating or 0
            new_rating = ((current_rating * (total_tasks - 1)) + combined_rating) / total_tasks
        
        # Ensure rating is between 0 and 5
        new_rating = max(0, min(5, new_rating))
        
        return new_rating
    
    def filter_volunteers_by_location(self, volunteers, task_lat, task_lon, 
                                     radius_km=10, fallback_radius_km=50):
        """
        Filter volunteers by location with fallback radius expansion
        """
        if not task_lat or not task_lon:
            return volunteers  # Return all if no location specified
        
        nearby_volunteers = []
        
        # First pass: try with primary radius
        for vol in volunteers:
            if vol.user_profile.latitude and vol.user_profile.longitude:
                distance = self._haversine_distance(
                    vol.user_profile.latitude,
                    vol.user_profile.longitude,
                    task_lat,
                    task_lon
                )
                
                if distance <= radius_km:
                    nearby_volunteers.append(vol)
        
        # Fallback: expand radius if no volunteers found
        if len(nearby_volunteers) == 0:
            for vol in volunteers:
                if vol.user_profile.latitude and vol.user_profile.longitude:
                    distance = self._haversine_distance(
                        vol.user_profile.latitude,
                        vol.user_profile.longitude,
                        task_lat,
                        task_lon
                    )
                    
                    if distance <= fallback_radius_km:
                        nearby_volunteers.append(vol)
        
        return nearby_volunteers if nearby_volunteers else volunteers