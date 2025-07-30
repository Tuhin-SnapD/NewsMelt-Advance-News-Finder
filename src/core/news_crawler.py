"""
News crawling module with progress bars and improved error handling
"""

import csv
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import logging

from newsapi import NewsApiClient

from ..utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info
from ..utils.config import Config

class NewsCrawler:
    """Enhanced news article crawler with progress tracking"""
    
    def __init__(self):
        """Initialize the NewsCrawler"""
        self.api_key = Config.NEWS_API_KEY
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        
        self.newsapi = NewsApiClient(api_key=self.api_key)
        self.output_dir = Config.RAW_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_text(self, text: Optional[str]) -> str:
        """
        Clean text by removing newlines, extra spaces, and symbols
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ''
        
        # Replace newlines with spaces
        text = text.replace("\n", " ")
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove non-alphanumeric characters except basic punctuation
        text = re.sub(r'[^0-9a-zA-Z\s.,!?;:()]+', '', text)
        return text
    
    def fetch_articles(self, config: Dict[str, Any]) -> List[List[str]]:
        """
        Fetch articles from NewsAPI with retry logic and progress tracking
        
        Args:
            config: Configuration dictionary with query parameters
            
        Returns:
            List of article data lists
        """
        display_info("Fetching articles from NewsAPI...")
        
        for attempt in range(config['max_retries']):
            try:
                logging.info(f"Fetching articles (attempt {attempt + 1}/{config['max_retries']})")
                
                articles = self.newsapi.get_everything(
                    q=config['query'],
                    from_param=config['from_date'],
                    to=config['to_date'],
                    language=config['language'],
                    sort_by=config['sort_by'],
                    page_size=config['page_size']
                )
                
                # Process articles with progress bar
                article_list = articles.get("articles", [])
                processed_articles = []
                
                with ProgressManager("Processing articles", len(article_list)) as progress:
                    for i, article in enumerate(article_list):
                        processed_articles.append([
                            article.get("url", ""),
                            self.clean_text(article.get("title", "")),
                            self.clean_text(article.get("description", "")),
                            self.clean_text(article.get("content", ""))
                        ])
                        progress.update(1, f"Processing article {i+1}/{len(article_list)}")
                
                display_success(f"Successfully fetched {len(processed_articles)} articles")
                return processed_articles
                
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < config['max_retries'] - 1:
                    display_warning(f"Retrying in {config['retry_delay']} seconds...")
                    time.sleep(config['retry_delay'])
                else:
                    raise
    
    def save_to_csv(self, articles: List[List[str]], filename: str) -> None:
        """
        Save articles to CSV file with progress tracking
        
        Args:
            articles: List of article data
            filename: Output filename
        """
        output_path = self.output_dir / filename
        
        display_info(f"Saving {len(articles)} articles to {output_path}")
        
        with open(output_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["URL", "Title", "Description", "Content"])
            
            with ProgressManager("Writing to CSV", len(articles)) as progress:
                for i, article in enumerate(articles):
                    writer.writerow(article)
                    progress.update(1, f"Writing article {i+1}/{len(articles)}")
        
        display_success(f"Articles saved to {output_path}")

def validate_api_key() -> str:
    """Validate and return the NewsAPI key"""
    api_key = Config.NEWS_API_KEY
    if not api_key:
        display_error("NEWS_API environment variable not found")
        display_info("Please create a .env file with your NewsAPI key:")
        display_info("Example: NEWS_API=your_api_key_here")
        sys.exit(1)
    return api_key

def main() -> None:
    """Main execution function with enhanced progress tracking"""
    display_section_header("News Crawler", "Fetching articles from NewsAPI")
    
    # Validate API key
    api_key = validate_api_key()
    
    # Initialize crawler
    crawler = NewsCrawler()
    
    # Update configuration with current dates
    Config.update_dates(days_back=20)
    config = Config.NEWS_API_CONFIG.copy()
    
    # Display configuration
    display_info("Search Configuration:")
    display_info(f"Query: {config['query']}")
    display_info(f"Date range: {config['from_date']} to {config['to_date']}")
    display_info(f"Language: {config['language']}")
    display_info(f"Sort by: {config['sort_by']}")
    
    try:
        # Fetch articles
        articles = crawler.fetch_articles(config)
        
        if articles:
            # Save to CSV
            crawler.save_to_csv(articles, "news_1.csv")
            display_success(f"{len(articles)} articles retrieved and saved to {Config.NEWS_RAW_FILE}")
        else:
            display_error("No articles retrieved. Possible reasons:")
            display_error("1. No articles match the search criteria")
            display_error("2. API rate limit exceeded")
            display_error("3. Date range issues")
            
    except Exception as e:
        error_msg = str(e)
        display_error(f"Failed to retrieve articles: {error_msg}")
        
        if "rateLimited" in error_msg:
            display_error("API rate limit exceeded. Please try again later.")
        elif "apiKeyDisabled" in error_msg:
            display_error("API key is disabled or invalid.")
        elif "quotaExceeded" in error_msg:
            display_error("API quota exceeded. Please upgrade your plan.")
        else:
            display_error("Please check your internet connection and API key.")
        
        logging.error(f"News crawling failed: {error_msg}")
        sys.exit(1)

if __name__ == "__main__":
    main() 