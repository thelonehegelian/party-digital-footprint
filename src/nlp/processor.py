import spacy
from typing import List, Dict, Any, Set
from collections import Counter
import re
from loguru import logger


class BasicNLPProcessor:
    """NLP processor for extracting keywords and analyzing political messaging."""
    
    def __init__(self):
        self.nlp = None
        self.political_terms = self._load_political_terms()
        self.stopwords = self._load_stopwords()
    
    def load_model(self, model_name: str = "en_core_web_sm"):
        """Load spaCy model."""
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.error(f"spaCy model '{model_name}' not found. Install with: python -m spacy download {model_name}")
            self.nlp = None
    
    def _load_political_terms(self) -> Set[str]:
        """Load predefined political terms relevant to UK politics and Reform UK."""
        return {
            # Core Reform UK issues
            'immigration', 'asylum', 'refugee', 'border', 'illegal', 'boat',
            'brexit', 'eu', 'european', 'sovereignty', 'wto', 'leave',
            'economy', 'tax', 'business', 'jobs', 'inflation', 'cost',
            'nhs', 'health', 'doctor', 'hospital', 'waiting', 'healthcare',
            'net zero', 'climate', 'green', 'carbon', 'energy', 'renewable',
            'woke', 'trans', 'gender', 'diversity', 'cancel culture', 'lgbtq',
            'housing', 'rent', 'mortgage', 'property', 'homeless', 'affordable',
            'crime', 'police', 'law', 'justice', 'prison', 'safety',
            'education', 'school', 'university', 'student', 'teacher',
            'elite', 'westminster', 'establishment', 'corrupt', 'swamp',
            
            # UK political entities
            'conservative', 'labour', 'liberal', 'democrat', 'tory', 'lib dem',
            'snp', 'plaid', 'green party', 'ukip', 'dup', 'sinn fein',
            'parliament', 'mp', 'mps', 'government', 'opposition',
            'downing street', 'whitehall', 'house of commons', 'house of lords',
            
            # Key political figures
            'sunak', 'starmer', 'davey', 'farage', 'johnson', 'truss',
            'hunt', 'reeves', 'braverman', 'patel',
            
            # Geographic/regional terms
            'london', 'scotland', 'wales', 'northern ireland', 'england',
            'yorkshire', 'midlands', 'north', 'south', 'west', 'east',
            
            # Economic terms
            'gdp', 'recession', 'growth', 'deficit', 'debt', 'spending',
            'budget', 'fiscal', 'monetary', 'bank of england', 'interest rates',
            
            # Social issues
            'pensioner', 'elderly', 'young people', 'working class', 'middle class',
            'family', 'children', 'welfare', 'benefits', 'universal credit'
        }
    
    def _load_stopwords(self) -> Set[str]:
        """Load common stopwords to filter out."""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
    
    def extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extract keywords from text using multiple methods."""
        if not text:
            return []
        
        keywords = []
        
        # Method 1: Named Entity Recognition (if spaCy is available)
        if self.nlp:
            keywords.extend(self._extract_entities(text))
        
        # Method 2: Political terms matching
        keywords.extend(self._extract_political_terms(text))
        
        # Method 3: Hashtag extraction
        keywords.extend(self._extract_hashtags(text))
        
        # Method 4: Important phrases (simple noun phrases)
        if self.nlp:
            keywords.extend(self._extract_noun_phrases(text))
        
        # Remove duplicates and sort by confidence
        unique_keywords = self._deduplicate_keywords(keywords)
        
        return unique_keywords
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy."""
        keywords = []
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                # Focus on relevant entity types
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'LAW']:
                    keyword = ent.text.lower().strip()
                    
                    if len(keyword) > 2 and keyword not in self.stopwords:
                        keywords.append({
                            'keyword': keyword,
                            'confidence': 0.8,
                            'extraction_method': 'spacy_ner',
                            'entity_type': ent.label_
                        })
        
        except Exception as e:
            logger.warning(f"Error in entity extraction: {e}")
        
        return keywords
    
    def _extract_political_terms(self, text: str) -> List[Dict[str, Any]]:
        """Extract predefined political terms."""
        keywords = []
        text_lower = text.lower()
        
        for term in self.political_terms:
            # Use word boundaries to match whole words
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                keywords.append({
                    'keyword': term,
                    'confidence': 0.9,
                    'extraction_method': 'political_terms'
                })
        
        return keywords
    
    def _extract_hashtags(self, text: str) -> List[Dict[str, Any]]:
        """Extract hashtags from social media content."""
        keywords = []
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text)
        
        for hashtag in hashtags:
            keywords.append({
                'keyword': hashtag.lower(),
                'confidence': 0.7,
                'extraction_method': 'hashtag'
            })
        
        return keywords
    
    def _extract_noun_phrases(self, text: str) -> List[Dict[str, Any]]:
        """Extract important noun phrases."""
        keywords = []
        
        try:
            doc = self.nlp(text)
            
            for chunk in doc.noun_chunks:
                phrase = chunk.text.lower().strip()
                
                # Filter by length and relevance
                if (len(phrase.split()) >= 2 and 
                    len(phrase) > 5 and 
                    not any(stop in phrase for stop in self.stopwords) and
                    any(char.isalpha() for char in phrase)):
                    
                    keywords.append({
                        'keyword': phrase,
                        'confidence': 0.6,
                        'extraction_method': 'noun_phrases'
                    })
        
        except Exception as e:
            logger.warning(f"Error in noun phrase extraction: {e}")
        
        return keywords
    
    def _deduplicate_keywords(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate keywords and sort by confidence."""
        seen = {}
        
        for kw in keywords:
            keyword = kw['keyword']
            if keyword not in seen or kw['confidence'] > seen[keyword]['confidence']:
                seen[keyword] = kw
        
        # Sort by confidence and limit results
        unique_keywords = sorted(seen.values(), key=lambda x: x['confidence'], reverse=True)
        return unique_keywords[:50]  # Limit to top 50 keywords
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Basic sentiment analysis (placeholder for future enhancement)."""
        # This is a simple placeholder - could be enhanced with proper sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'support', 'success', 'progress', 'better', 'strong']
        negative_words = ['bad', 'terrible', 'failed', 'crisis', 'problem', 'disaster', 'weak', 'broken']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'positive_score': positive_count,
            'negative_score': negative_count,
            'method': 'keyword_counting'
        }
    
    def extract_message_themes(self, text: str) -> List[str]:
        """Extract main themes from a message."""
        themes = []
        text_lower = text.lower()
        
        # Define theme categories based on Reform UK's key issues
        theme_patterns = {
            'immigration': ['immigration', 'asylum', 'refugee', 'border', 'boat'],
            'brexit_eu': ['brexit', 'eu', 'european', 'sovereignty', 'leave'],
            'economy': ['economy', 'tax', 'business', 'jobs', 'inflation', 'cost'],
            'healthcare': ['nhs', 'health', 'doctor', 'hospital', 'healthcare'],
            'climate': ['net zero', 'climate', 'green', 'carbon', 'energy'],
            'culture': ['woke', 'trans', 'gender', 'diversity', 'culture'],
            'housing': ['housing', 'rent', 'mortgage', 'property'],
            'crime': ['crime', 'police', 'law', 'justice', 'safety'],
            'education': ['education', 'school', 'university', 'student'],
            'establishment': ['elite', 'westminster', 'establishment', 'corrupt']
        }
        
        for theme, keywords in theme_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)
        
        return themes