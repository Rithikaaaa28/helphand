import math
import re
from typing import List, Dict, Any

class SimpleAIMatchingService:
    """Simplified AI matching service without external ML dependencies"""
    
    def __init__(self):
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
    
    def rank_volunteers_for_task(self, task, volunteers, max_results=10):
        """Rank volunteers for a specific task"""
        if not volunteers:
            return []
        
        ranked_volunteers = []
        
        for volunteer in volunteers:
            # Calculate similarity score
            similarity_score = self._calculate_similarity(
                task.description, 
                volunteer.skills or ""
            )
            
            # Calculate proximity score
            task_location = (task.latitude, task.longitude) if task.latitude and task.longitude else None
            volunteer_location = (
                volunteer.user_profile.latitude, 
                volunteer.user_profile.longitude
            ) if volunteer.user_profile.latitude and volunteer.user_profile.longitude else None
            
            proximity_score = self._calculate_proximity_score(task_location, volunteer_location)
            
            # Calculate hybrid score
            hybrid_score = self._calculate_hybrid_score(
                similarity_score=similarity_score,
                proximity_score=proximity_score,
                volunteer_rating=volunteer.rating or 0,
                completed_tasks=volunteer.completed_tasks or 0
            )
            
            # Calculate distance
            distance_km = self._calculate_distance(task_location, volunteer_location)
            
            # Add to results if above threshold
            if hybrid_score > 0.1:  # Minimum threshold
                ranked_volunteers.append({
                    'volunteer': volunteer,
                    'similarity_score': similarity_score,
                    'proximity_score': proximity_score,
                    'hybrid_score': hybrid_score,
                    'distance_km': distance_km
                })
        
        # Sort by hybrid score (descending)
        ranked_volunteers.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return ranked_volunteers[:max_results]
    
    def _calculate_similarity(self, task_description, volunteer_skills):
        """Calculate similarity using simple keyword matching"""
        if not task_description or not volunteer_skills:
            return 0.0
        
        # Normalize and tokenize
        task_words = set(self._tokenize(task_description.lower()))
        skill_words = set(self._tokenize(volunteer_skills.lower()))
        
        # Remove stop words
        task_words = task_words - self.stop_words
        skill_words = skill_words - self.stop_words
        
        if not task_words or not skill_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = task_words.intersection(skill_words)
        union = task_words.union(skill_words)
        
        similarity = len(intersection) / len(union) if union else 0.0
        
        # Boost for exact skill matches
        exact_matches = 0
        for skill_word in skill_words:
            if len(skill_word) > 3 and skill_word in task_description.lower():
                exact_matches += 1
        
        # Add bonus for exact matches
        exact_bonus = min(exact_matches * 0.2, 0.5)  # Max 50% bonus
        
        return min(similarity + exact_bonus, 1.0)
    
    def _tokenize(self, text):
        """Simple tokenization"""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text)
        return [word.strip() for word in text.split() if len(word.strip()) > 1]
    
    def _calculate_proximity_score(self, task_location, volunteer_location):
        """Calculate proximity score based on distance"""
        if not task_location or not volunteer_location:
            return 0.5  # Default score if no location data
        
        try:
            distance_km = self._calculate_distance(task_location, volunteer_location)
            
            # Convert distance to score (closer = higher score)
            if distance_km <= 1:
                return 1.0
            elif distance_km <= 2:
                return 0.9
            elif distance_km <= 5:
                return 0.8
            elif distance_km <= 10:
                return 0.6
            elif distance_km <= 25:
                return 0.4
            elif distance_km <= 50:
                return 0.2
            else:
                return 0.1
        
        except Exception:
            return 0.5
    
    def _calculate_distance(self, location1, location2):
        """Calculate distance using Haversine formula"""
        if not location1 or not location2:
            return float('inf')
        
        try:
            lat1, lon1 = location1
            lat2, lon2 = location2
            
            # Haversine formula
            R = 6371  # Earth's radius in km
            
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            return R * c
        
        except Exception:
            return float('inf')
    
    def _calculate_hybrid_score(self, similarity_score, proximity_score, 
                              volunteer_rating=0, completed_tasks=0,
                              similarity_weight=0.6, proximity_weight=0.4):
        """Calculate weighted hybrid matching score"""
        
        # Base score from similarity and proximity
        base_score = (similarity_weight * similarity_score) + (proximity_weight * proximity_score)
        
        # Rating boost (0-1 scale)
        rating_boost = (volunteer_rating / 5.0) * 0.1 if volunteer_rating > 0 else 0
        
        # Experience boost based on completed tasks
        experience_boost = min(completed_tasks / 100.0, 0.1) * 0.05 if completed_tasks > 0 else 0
        
        # Final score
        final_score = base_score + rating_boost + experience_boost
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def analyze_sentiment(self, text):
        """Simple sentiment analysis using keyword matching"""
        if not text:
            return {'compound': 0.0, 'label': 'neutral'}
        
        text_lower = text.lower()
        
        # Simple positive/negative word lists
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'helpful', 'kind', 'professional', 'quick', 'efficient', 'satisfied', 'happy', 'pleased', 'recommend', 'perfect', 'awesome'}
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'poor', 'slow', 'rude', 'unprofessional', 'disappointing', 'unsatisfied', 'unhappy', 'worst', 'hate', 'angry', 'frustrated'}
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate compound score
        total_words = len(text_lower.split())
        if total_words == 0:
            compound = 0.0
        else:
            compound = (positive_count - negative_count) / max(total_words, 1)
            compound = max(-1.0, min(1.0, compound * 3))  # Scale and clamp
        
        # Determine label
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'compound': compound,
            'positive': positive_count / max(total_words, 1),
            'negative': negative_count / max(total_words, 1),
            'neutral': 1 - (positive_count + negative_count) / max(total_words, 1),
            'label': label
        }
    
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