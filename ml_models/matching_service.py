import numpy as np
import pickle
import os
import re

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: scikit-learn not available. Some AI features will be limited.")

try:
    from geopy.distance import geodesic
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False
    print("Warning: geopy not available. Distance calculations will be limited.")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False
    print("Warning: NLTK not available. Using TextBlob for sentiment analysis.")

try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    print("Warning: TextBlob not available. Sentiment analysis will be limited.")

class AIMatchingService:
    def __init__(self):
        if HAS_SKLEARN:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
        else:
            self.vectorizer = None
        self.sentiment_analyzer = None
        self._initialize_sentiment_analyzer()
    
    def _initialize_sentiment_analyzer(self):
        """Initialize sentiment analyzer"""
        if HAS_NLTK:
            try:
                nltk.download('vader_lexicon', quiet=True)
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
            except:
                self.sentiment_analyzer = None
        else:
            self.sentiment_analyzer = None
    
    def calculate_task_volunteer_similarity(self, task_description, volunteer_skills):
        """Calculate similarity between task description and volunteer skills"""
        if not HAS_SKLEARN or not self.vectorizer:
            # Fallback to simple text matching
            return self._simple_text_similarity(task_description, volunteer_skills)
        
        try:
            # Combine texts for vectorization
            texts = [task_description, volunteer_skills]
            
            # Handle empty or None values
            texts = [text if text else "" for text in texts]
            
            if not any(texts):
                return 0.0
            
            # Vectorize texts
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Return similarity between task and volunteer
            return similarity_matrix[0, 1]
        
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return self._simple_text_similarity(task_description, volunteer_skills)
    
    def _simple_text_similarity(self, text1, text2):
        """Simple text similarity calculation without sklearn"""
        if not text1 or not text2:
            return 0.0
        
        # Convert to lowercase and split into words
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_distance_score(self, task_location, volunteer_location, max_distance_km=50):
        """Calculate proximity score based on distance"""
        if not HAS_GEOPY:
            return self._simple_distance_score(task_location, volunteer_location, max_distance_km)
        
        try:
            if not all([task_location, volunteer_location]):
                return 0.0
            
            # Calculate distance using Haversine formula
            distance = geodesic(task_location, volunteer_location).kilometers
            
            # Convert distance to score (closer = higher score)
            if distance > max_distance_km:
                return 0.0
            
            # Normalize score (1.0 for 0km, decreases as distance increases)
            score = max(0, 1 - (distance / max_distance_km))
            return score
        
        except Exception as e:
            print(f"Error calculating distance: {e}")
            return self._simple_distance_score(task_location, volunteer_location, max_distance_km)
    
    def _simple_distance_score(self, task_location, volunteer_location, max_distance_km=50):
        """Simple distance calculation without geopy"""
        if not all([task_location, volunteer_location]):
            return 0.0
        
        try:
            # Simple Euclidean distance (approximation for small distances)
            lat_diff = task_location[0] - volunteer_location[0]
            lon_diff = task_location[1] - volunteer_location[1]
            
            # Rough conversion: 1 degree ≈ 111 km
            distance_km = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
            
            if distance_km > max_distance_km:
                return 0.0
            
            return max(0, 1 - (distance_km / max_distance_km))
        
        except Exception as e:
            print(f"Error in simple distance calculation: {e}")
            return 0.5  # Return neutral score if calculation fails
    
    def calculate_hybrid_score(self, similarity_score, proximity_score, 
                             volunteer_rating=0, completed_tasks=0,
                             similarity_weight=0.6, proximity_weight=0.4):
        """Calculate weighted hybrid matching score"""
        
        # Base score from similarity and proximity
        base_score = (similarity_weight * similarity_score) + (proximity_weight * proximity_score)
        
        # Rating boost (0-1 scale)
        rating_boost = (volunteer_rating / 5.0) * 0.1  # Max 10% boost
        
        # Experience boost based on completed tasks
        experience_boost = min(completed_tasks / 100.0, 0.1) * 0.05  # Max 5% boost
        
        # Final score
        final_score = base_score + rating_boost + experience_boost
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def rank_volunteers_for_task(self, task, volunteers, max_results=10):
        """Rank volunteers for a specific task"""
        if not volunteers:
            return []
        
        ranked_volunteers = []
        
        for volunteer in volunteers:
            # Calculate similarity score
            similarity_score = self.calculate_task_volunteer_similarity(
                task.description, 
                volunteer.skills or ""
            )
            
            # Calculate proximity score
            task_location = (task.latitude, task.longitude) if task.latitude and task.longitude else None
            volunteer_location = (
                volunteer.user_profile.latitude, 
                volunteer.user_profile.longitude
            ) if volunteer.user_profile.latitude and volunteer.user_profile.longitude else None
            
            proximity_score = self.calculate_distance_score(task_location, volunteer_location)
            
            # Calculate hybrid score
            hybrid_score = self.calculate_hybrid_score(
                similarity_score=similarity_score,
                proximity_score=proximity_score,
                volunteer_rating=volunteer.rating,
                completed_tasks=volunteer.completed_tasks
            )
            
            # Calculate actual distance for display
            actual_distance = float('inf')
            if task_location and volunteer_location:
                if HAS_GEOPY:
                    try:
                        actual_distance = geodesic(task_location, volunteer_location).kilometers
                    except:
                        # Fallback to simple calculation
                        lat_diff = task_location[0] - volunteer_location[0]
                        lon_diff = task_location[1] - volunteer_location[1]
                        actual_distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
                else:
                    # Simple distance calculation
                    lat_diff = task_location[0] - volunteer_location[0]
                    lon_diff = task_location[1] - volunteer_location[1]
                    actual_distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
            
            # Add to results if above threshold
            if hybrid_score > 0.1:  # Minimum threshold
                ranked_volunteers.append({
                    'volunteer': volunteer,
                    'similarity_score': similarity_score,
                    'proximity_score': proximity_score,
                    'hybrid_score': hybrid_score,
                    'distance_km': actual_distance
                })
        
        # Sort by hybrid score (descending)
        ranked_volunteers.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return ranked_volunteers[:max_results]
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of feedback text"""
        if not text:
            return {'compound': 0.0, 'label': 'neutral'}
        
        try:
            if self.sentiment_analyzer and HAS_NLTK:
                # Use NLTK VADER
                scores = self.sentiment_analyzer.polarity_scores(text)
                
                # Determine label
                compound = scores['compound']
                if compound >= 0.05:
                    label = 'positive'
                elif compound <= -0.05:
                    label = 'negative'
                else:
                    label = 'neutral'
                
                return {
                    'compound': compound,
                    'positive': scores['pos'],
                    'negative': scores['neg'],
                    'neutral': scores['neu'],
                    'label': label
                }
            elif HAS_TEXTBLOB:
                # Use TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.1:
                    label = 'positive'
                elif polarity < -0.1:
                    label = 'negative'
                else:
                    label = 'neutral'
                
                return {
                    'compound': polarity,
                    'label': label
                }
            else:
                # Simple rule-based sentiment analysis
                return self._simple_sentiment_analysis(text)
        
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {'compound': 0.0, 'label': 'neutral'}
    
    def _simple_sentiment_analysis(self, text):
        """Simple rule-based sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'helpful', 'kind', 'friendly']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing', 'unhelpful', 'rude', 'poor']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return {'compound': 0.5, 'label': 'positive'}
        elif negative_count > positive_count:
            return {'compound': -0.5, 'label': 'negative'}
        else:
            return {'compound': 0.0, 'label': 'neutral'}
    
    def update_volunteer_rating(self, volunteer, new_feedback_sentiment, new_rating):
        """Update volunteer rating based on new feedback"""
        try:
            # Get current metrics
            current_rating = volunteer.rating or 0
            completed_tasks = volunteer.completed_tasks or 0
            
            # Weight for new feedback (newer feedback has more impact)
            total_weight = completed_tasks + 1
            
            # Calculate new rating (combines star rating and sentiment)
            sentiment_adjustment = new_feedback_sentiment.get('compound', 0) * 0.5  # Max ±0.5 adjustment
            adjusted_new_rating = new_rating + sentiment_adjustment
            adjusted_new_rating = max(1, min(5, adjusted_new_rating))  # Keep in 1-5 range
            
            # Calculate weighted average
            new_average_rating = ((current_rating * completed_tasks) + adjusted_new_rating) / total_weight
            
            return round(new_average_rating, 2)
        
        except Exception as e:
            print(f"Error updating rating: {e}")
            return volunteer.rating or 0
    
    def save_model(self, filepath):
        """Save the trained vectorizer"""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath):
        """Load a pre-trained vectorizer"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        return False