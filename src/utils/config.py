"""
Configuration management for the News Extractor Summarizer
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration management"""
    
    # API Configuration
    NEWS_API_KEY = os.getenv('NEWS_API')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API')
    SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
    
    # Directory Structure
    BASE_DIR = Path(__file__).parent.parent.parent
    DATASET_DIR = BASE_DIR / 'dataset'
    CACHE_DIR = BASE_DIR / 'cache_dir'
    OUTPUT_DIR = BASE_DIR / 'output'
    
    # Dataset subdirectories
    RAW_DIR = DATASET_DIR / 'raw'
    TOPICS_DIR = DATASET_DIR / 'topics'
    MULTI_SUMMARIES_DIR = DATASET_DIR / 'multi-summaries'
    GRAPHS_DIR = DATASET_DIR / 'graphs'
    FINAL_DIR = DATASET_DIR / 'final'
    
    # File paths
    NEWS_RAW_FILE = RAW_DIR / 'news_1.csv'
    NEWS_WITH_CONTENT_FILE = RAW_DIR / 'news_with_full_content_2.csv'
    NEWS_WITH_TOPICS_FILE = RAW_DIR / 'news_with_full_content_with_topic_3.csv'
    
    # News API Configuration
    NEWS_API_CONFIG = {
        'query': 'business economy finance market stock investment company corporate trade economic financial commerce earnings revenue profit merger acquisition IPO startup technology innovation',
        'from_date': '2024-01-01',  # Will be dynamically set
        'to_date': '2024-12-31',    # Will be dynamically set
        'language': 'en',
        'sort_by': 'popularity',
        'page_size': 100,
        'max_retries': 3,
        'retry_delay': 2
    }
    
    # Content Extraction Configuration
    CONTENT_EXTRACTION_CONFIG = {
        'max_workers': 5,
        'timeout': 15,
        'max_retries': 3,
        'retry_delay': 1,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Topic Modeling Configuration
    TOPIC_MODELING_CONFIG = {
        'model_path': 'cache_dir/transformers/mrm8488/t5-base-finetuned-news-title-classification',
        'max_retries': 3,
        'retry_delay': 1,
        'batch_size': 10
    }
    
    # Summarization Configuration
    SUMMARIZATION_CONFIG = {
        'model_name': 'google/pegasus-xsum',
        'max_length': 150,
        'num_beams': 4,
        'temperature': 1.0,
        'do_sample': True,
        'min_text_length': 10,
        'max_input_length': 512,
        'batch_size': 5
    }
    
    # Graph Summarization Configuration
    GRAPH_SUMMARIZATION_CONFIG = {
        'alpha': 0.9,
        'similarity_threshold': 0.07,
        'stopping_criterion': 0.00005,
        'max_loops': 3000,
        'default_sum_size': 5
    }
    
    # Web Search Configuration
    WEB_SEARCH_CONFIG = {
        'base_url': 'https://www.googleapis.com/customsearch/v1',
        'max_results': 10,
        'timeout': 30
    }
    
    @classmethod
    def create_directories(cls) -> None:
        """Create all necessary directories"""
        directories = [
            cls.DATASET_DIR,
            cls.RAW_DIR,
            cls.TOPICS_DIR,
            cls.MULTI_SUMMARIES_DIR,
            cls.GRAPHS_DIR,
            cls.FINAL_DIR,
            cls.CACHE_DIR,
            cls.OUTPUT_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logging.info(f"Directory ensured: {directory}")
    
    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """Validate API keys and return status"""
        validation = {
            'news_api': bool(cls.NEWS_API_KEY),
            'google_api': bool(cls.GOOGLE_API_KEY),
            'search_engine': bool(cls.SEARCH_ENGINE_ID)
        }
        return validation
    
    @classmethod
    def get_required_api_keys(cls) -> list:
        """Get list of required API keys"""
        required = []
        if not cls.NEWS_API_KEY:
            required.append('NEWS_API')
        if not cls.GOOGLE_API_KEY:
            required.append('GOOGLE_API')
        if not cls.SEARCH_ENGINE_ID:
            required.append('SEARCH_ENGINE_ID')
        return required
    
    @classmethod
    def update_dates(cls, days_back: int = 20) -> None:
        """Update date range in NEWS_API_CONFIG"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        cls.NEWS_API_CONFIG['from_date'] = start_date.strftime('%Y-%m-%d')
        cls.NEWS_API_CONFIG['to_date'] = end_date.strftime('%Y-%m-%d') 