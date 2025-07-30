"""
Content extraction module with progress bars and improved error handling
"""

import pandas as pd
import newspaper
from newspaper import Config
import requests
import re
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import spacy
from urllib.parse import urlparse
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

from ..utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info, display_warning
from ..utils.config import Config as AppConfig

class ContentExtractor:
    """Enhanced article content extractor with progress tracking"""
    
    def __init__(self):
        """Initialize the ContentExtractor with spaCy model"""
        self.nlp = self._load_spacy_model()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': AppConfig.CONTENT_EXTRACTION_CONFIG['user_agent']})
    
    def _load_spacy_model(self):
        """Load spaCy English model with fallback"""
        try:
            display_info("Loading spaCy English model...")
            return spacy.load("en_core_web_sm")
        except OSError:
            display_warning("Downloading spaCy English model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], 
                         capture_output=True, check=True)
            return spacy.load("en_core_web_sm")
    
    def find_final_url(self, url: str) -> str:
        """
        Find the final URL after any redirections
        
        Args:
            url: Original URL
            
        Returns:
            Final URL after redirections
        """
        try:
            response = self.session.head(url, timeout=AppConfig.CONTENT_EXTRACTION_CONFIG['timeout'], allow_redirects=True)
            final_url = response.url
            
            # Skip consent pages and error pages
            skip_keywords = ['consent', 'error', 'blocked', 'access-denied', 'captcha', 'robot']
            if any(keyword in final_url.lower() for keyword in skip_keywords):
                return url  # Return original URL if redirected to consent page
                
            return final_url
        except requests.exceptions.RequestException:
            return url
    
    def get_article_content(self, url: str) -> str:
        """
        Extract article content from URL with retry logic
        
        Args:
            url: Article URL
            
        Returns:
            Extracted article text
        """
        config = Config()
        config.browser_user_agent = AppConfig.CONTENT_EXTRACTION_CONFIG['user_agent']
        config.request_timeout = AppConfig.CONTENT_EXTRACTION_CONFIG['timeout']
        config.fetch_images = False
        config.memoize_articles = False
        
        for attempt in range(AppConfig.CONTENT_EXTRACTION_CONFIG['max_retries']):
            try:
                article = newspaper.Article(url, config=config)
                article.download()
                article.parse()
                return article.text or ''
            except Exception as e:
                if attempt < AppConfig.CONTENT_EXTRACTION_CONFIG['max_retries'] - 1:
                    time.sleep(AppConfig.CONTENT_EXTRACTION_CONFIG['retry_delay'])
                    continue
                logging.warning(f"Failed to extract content from {url}: {str(e)}")
                return ''
    
    def filter_content(self, text: str, num_sentences: int = 4) -> str:
        """
        Filter and process content using spaCy
        
        Args:
            text: Input text to filter
            num_sentences: Number of sentences to extract
            
        Returns:
            Filtered content
        """
        if not text or pd.isna(text):
            return ''
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
            
            # Get first n sentences
            main_content = " ".join(sentences[:num_sentences])
            return main_content
        except Exception as e:
            logging.warning(f"Error in content filtering: {str(e)}")
            return text[:500] if text else ''  # Fallback to first 500 characters
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing unwanted characters and normalizing whitespace
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove unwanted characters but keep basic punctuation
        text = re.sub(r'[^0-9a-zA-Z\s.,!?;:()]+', '', text)
        # Remove trailing punctuation
        text = re.sub(r'[.,!?;:()]+$', '', text)
        return text
    
    def process_single_article(self, row_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Process a single article row
        
        Args:
            row_data: Dictionary containing article data
            
        Returns:
            Dictionary with processed content
        """
        url = row_data['URL']
        final_url = self.find_final_url(url)
        
        # Extract content with retries
        raw_content = ''
        for attempt in range(AppConfig.CONTENT_EXTRACTION_CONFIG['max_retries']):
            raw_content = self.get_article_content(final_url)
            if raw_content.strip():
                break
            if attempt < AppConfig.CONTENT_EXTRACTION_CONFIG['max_retries'] - 1:
                time.sleep(AppConfig.CONTENT_EXTRACTION_CONFIG['retry_delay'])
        
        # Process content
        spacy_content = self.filter_content(raw_content)
        
        # Clean content
        raw_content_clean = self.clean_text(raw_content)
        spacy_content_clean = self.clean_text(spacy_content)
        
        # Get available content sources
        description = str(row_data.get('Description', '')) if pd.notna(row_data.get('Description')) else ''
        content = str(row_data.get('Content', '')) if pd.notna(row_data.get('Content')) else ''
        title = str(row_data.get('Title', '')) if pd.notna(row_data.get('Title')) else ''
        
        # Clean all content sources
        description_clean = self.clean_text(description)
        content_clean = self.clean_text(content)
        title_clean = self.clean_text(title)
        
        # Create comprehensive content by combining all sources
        all_content_parts = []
        if title_clean and len(title_clean) > 10:
            all_content_parts.append(title_clean)
        if description_clean and len(description_clean) > 20:
            all_content_parts.append(description_clean)
        if content_clean and len(content_clean) > 20:
            all_content_parts.append(content_clean)
        if spacy_content_clean and len(spacy_content_clean) > 20:
            all_content_parts.append(spacy_content_clean)
        if raw_content_clean and len(raw_content_clean) > 20:
            all_content_parts.append(raw_content_clean)
        
        # Combine all content parts
        if all_content_parts:
            final_content = ' '.join(all_content_parts)
            # Remove duplicate sentences and clean up
            final_content = re.sub(r'\d{4} chars$', '', final_content)
            final_content = re.sub(r'\s+', ' ', final_content).strip()
        else:
            # Fallback to best available content
            texts = [spacy_content_clean, description_clean, content_clean, title_clean]
            final_content = max(texts, key=len)
            final_content = re.sub(r'\d{4} chars$', '', final_content)
        
        return {
            'raw_full_content': raw_content_clean,
            'spacy_full_content': spacy_content_clean,
            'final_full_content': final_content
        }

def validate_input_file(input_path: Path) -> None:
    """Validate that input file exists and is readable"""
    if not input_path.exists():
        display_error(f"Input file {input_path} does not exist. Please run news_crawler.py first.")
        exit(1)
    
    try:
        pd.read_csv(input_path, nrows=1)
    except Exception as e:
        display_error(f"Error reading input file: {str(e)}")
        exit(1)

def main() -> None:
    """Main execution function with enhanced progress tracking"""
    display_section_header("Content Extractor", "Extracting full content from article URLs")
    
    # Setup paths
    input_file = AppConfig.NEWS_RAW_FILE
    output_file = AppConfig.NEWS_WITH_CONTENT_FILE
    
    # Validate input file
    validate_input_file(input_file)
    
    # Read input data
    display_info("Reading input data...")
    df = pd.read_csv(input_file)
    display_info(f"Processing {len(df)} articles...")
    
    # Initialize extractor
    extractor = ContentExtractor()
    
    # Add new columns
    df['raw_full_content'] = ''
    df['spacy_full_content'] = ''
    df['final_full_content'] = ''
    
    # Process articles with progress bar
    processed_count = 0
    with ProgressManager("Extracting article content", len(df)) as progress:
        for idx, row in df.iterrows():
            try:
                # Process article
                result = extractor.process_single_article(row.to_dict())
                
                # Update dataframe
                df.loc[idx, 'raw_full_content'] = result['raw_full_content']
                df.loc[idx, 'spacy_full_content'] = result['spacy_full_content']
                df.loc[idx, 'final_full_content'] = result['final_full_content']
                
                processed_count += 1
                progress.update(1, f"Processing article {idx+1}/{len(df)}")
                
            except Exception as e:
                logging.error(f"Error processing row {idx}: {str(e)}")
                continue
    
    # Save results
    display_info("Saving results...")
    df.to_csv(output_file, index=False)
    
    display_success(f"Processed {processed_count}/{len(df)} articles")
    display_success(f"Results saved to {output_file}")

if __name__ == "__main__":
    main() 