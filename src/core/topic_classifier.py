"""
Topic classification module with progress bars and improved error handling
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, T5ForConditionalGeneration
import pandas as pd
import time
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info, display_warning
from ..utils.config import Config as AppConfig

# Topic keywords for fallback classification
TOPIC_KEYWORDS = {
    'technology': [
        'tech', 'technology', 'ai', 'artificial intelligence', 'machine learning', 
        'software', 'app', 'digital', 'computer', 'internet', 'cyber', 'data',
        'blockchain', 'crypto', 'startup', 'innovation', 'algorithm', 'automation'
    ],
    'business': [
        'business', 'economy', 'finance', 'market', 'stock', 'investment', 
        'company', 'corporate', 'trade', 'economic', 'financial', 'commerce',
        'earnings', 'revenue', 'profit', 'merger', 'acquisition', 'ipo'
    ],
    'politics': [
        'politics', 'political', 'government', 'election', 'vote', 'democrat', 
        'republican', 'congress', 'senate', 'president', 'policy', 'legislation',
        'campaign', 'poll', 'candidate', 'party', 'administration'
    ],
    'sports': [
        'sport', 'football', 'basketball', 'baseball', 'soccer', 'tennis', 
        'golf', 'olympics', 'championship', 'league', 'team', 'player',
        'game', 'match', 'tournament', 'coach', 'athlete', 'score'
    ],
    'entertainment': [
        'entertainment', 'movie', 'film', 'music', 'celebrity', 'hollywood', 
        'actor', 'actress', 'singer', 'artist', 'show', 'tv', 'netflix',
        'award', 'premiere', 'album', 'concert', 'performance'
    ],
    'health': [
        'health', 'medical', 'medicine', 'doctor', 'hospital', 'disease', 
        'treatment', 'vaccine', 'covid', 'virus', 'healthcare', 'patient',
        'clinical', 'therapy', 'diagnosis', 'symptom', 'recovery'
    ],
    'science': [
        'science', 'research', 'study', 'scientific', 'discovery', 'experiment', 
        'laboratory', 'scientist', 'physics', 'chemistry', 'biology', 'space',
        'climate', 'environment', 'study', 'publication', 'journal'
    ],
    'world': [
        'world', 'international', 'global', 'foreign', 'diplomacy', 'treaty',
        'alliance', 'conflict', 'peace', 'war', 'military', 'defense'
    ]
}

class TopicClassifier:
    """Enhanced topic classifier with progress tracking"""
    
    def __init__(self):
        """Initialize the TopicClassifier with model loading"""
        self.model = None
        self.tokenizer = None
        self.use_transformer = False
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the transformer model with fallback to keyword-based classification"""
        try:
            display_info("Loading transformer model...")
            model_path = Path(AppConfig.TOPIC_MODELING_CONFIG['model_path'])
            
            if not model_path.exists():
                raise FileNotFoundError(f"Model path {model_path} does not exist")
            
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            self.model = T5ForConditionalGeneration.from_pretrained(str(model_path))
            self.use_transformer = True
            display_success("Transformer model loaded successfully")
            
        except Exception as e:
            display_warning(f"Failed to load transformer model: {str(e)}")
            display_warning("Using keyword-based topic classification...")
            self.use_transformer = False
    
    def classify_with_transformer(self, text: str) -> str:
        """
        Classify text using the transformer model
        
        Args:
            text: Text to classify
            
        Returns:
            Predicted topic
        """
        try:
            input_ids = self.tokenizer.encode(text, return_tensors='pt', max_length=512, truncation=True)
            outputs = self.model.generate(input_ids=input_ids, max_new_tokens=50)
            topic = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return topic.lower().strip()
        except Exception as e:
            logging.warning(f"Transformer classification failed: {str(e)}")
            return self.classify_with_keywords(text)
    
    def classify_with_keywords(self, text: str) -> str:
        """
        Classify text using keyword matching
        
        Args:
            text: Text to classify
            
        Returns:
            Predicted topic
        """
        if not text:
            return 'general'
        
        text_lower = text.lower()
        
        # Count matches for each topic
        topic_scores = {}
        for topic_name, keywords in TOPIC_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            topic_scores[topic_name] = score
        
        # Return topic with highest score, or 'general' if no matches
        max_score = max(topic_scores.values())
        if max_score > 0:
            return max(topic_scores, key=topic_scores.get)
        else:
            return 'general'
    
    def classify_text(self, text: str) -> str:
        """
        Classify text using the best available method
        
        Args:
            text: Text to classify
            
        Returns:
            Predicted topic
        """
        if not text or pd.isna(text) or str(text).strip() == '':
            return 'general'
        
        # Clean text
        text = re.sub(r'[^\w\s]', '', str(text)).strip()
        
        if self.use_transformer:
            return self.classify_with_transformer(text)
        else:
            return self.classify_with_keywords(text)

def validate_input_file(input_path: Path) -> None:
    """Validate that input file exists and is readable"""
    if not input_path.exists():
        display_error(f"Input file {input_path} does not exist. Please run content_extractor.py first.")
        exit(1)
    
    try:
        pd.read_csv(input_path, nrows=1)
    except Exception as e:
        display_error(f"Error reading input file: {str(e)}")
        exit(1)

def process_batch(classifier: TopicClassifier, texts: List[str]) -> List[str]:
    """
    Process a batch of texts for topic classification
    
    Args:
        classifier: TopicClassifier instance
        texts: List of texts to classify
        
    Returns:
        List of predicted topics
    """
    topics = []
    for text in texts:
        try:
            topic = classifier.classify_text(text)
            topics.append(topic)
        except Exception as e:
            logging.warning(f"Error classifying text: {str(e)}")
            topics.append('general')
    return topics

def main() -> None:
    """Main execution function with enhanced progress tracking"""
    display_section_header("Topic Classifier", "Classifying articles into topics")
    
    # Setup paths
    input_file = AppConfig.NEWS_WITH_CONTENT_FILE
    output_file = AppConfig.NEWS_WITH_TOPICS_FILE
    
    # Validate input file
    validate_input_file(input_file)
    
    # Read input data
    display_info("Reading input data...")
    df = pd.read_csv(input_file)
    display_info(f"Processing {len(df)} articles...")
    
    # Initialize classifier
    classifier = TopicClassifier()
    
    # Add topic column
    df['topic'] = ''
    
    # Process articles in batches
    processed_count = 0
    batch_size = AppConfig.TOPIC_MODELING_CONFIG['batch_size']
    
    with ProgressManager("Classifying articles", len(df)) as progress:
        for i in range(0, len(df), batch_size):
            batch_end = min(i + batch_size, len(df))
            batch_texts = df.iloc[i:batch_end]['Title'].tolist()
            
            # Classify batch
            batch_topics = process_batch(classifier, batch_texts)
            
            # Update dataframe
            for j, topic in enumerate(batch_topics):
                df.loc[i + j, 'topic'] = topic
                processed_count += 1
            
            progress.update(batch_size, f"Classifying articles {i+1}-{batch_end}/{len(df)}")
    
    # Save results
    display_info("Saving results...")
    df.to_csv(output_file, index=False)
    
    # Print summary
    topic_counts = df['topic'].value_counts()
    display_success(f"Classified {processed_count} articles")
    display_info("Topic distribution:")
    for topic, count in topic_counts.items():
        display_info(f"  {topic}: {count}")
    
    display_success(f"Results saved to {output_file}")

if __name__ == "__main__":
    main() 