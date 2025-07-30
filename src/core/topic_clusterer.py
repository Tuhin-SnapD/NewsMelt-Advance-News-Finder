"""
Topic clustering module with progress bars and improved error handling
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info
from ..utils.config import Config as AppConfig

class TopicClusterer:
    """Enhanced topic-based clustering with progress tracking"""
    
    def __init__(self, input_file: Path, output_dir: Path):
        """
        Initialize the TopicClusterer
        
        Args:
            input_file: Path to input CSV file
            output_dir: Directory to save topic files
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_input_file(self) -> bool:
        """
        Validate that input file exists and contains required columns
        
        Returns:
            True if valid, False otherwise
        """
        if not self.input_file.exists():
            display_error(f"Input file {self.input_file} does not exist.")
            return False
        
        try:
            df = pd.read_csv(self.input_file, nrows=1)
            required_columns = ['Title', 'Description', 'Content']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                display_error(f"Missing required columns: {missing_columns}")
                return False
            
            return True
        except Exception as e:
            display_error(f"Error reading input file: {str(e)}")
            return False
    
    def load_data(self) -> Optional[pd.DataFrame]:
        """
        Load and validate the input data
        
        Returns:
            DataFrame with news data or None if error
        """
        try:
            df = pd.read_csv(self.input_file)
            display_info(f"Loaded {len(df)} articles from {self.input_file}")
            return df
        except Exception as e:
            display_error(f"Error loading data: {str(e)}")
            return None
    
    def get_topics(self, df: pd.DataFrame) -> List[str]:
        """
        Get unique topics from the dataframe
        
        Args:
            df: DataFrame with news data
            
        Returns:
            List of unique topics
        """
        if 'topic' in df.columns:
            topics = df['topic'].dropna().unique().tolist()
            display_info(f"Found {len(topics)} topics: {', '.join(topics)}")
            return topics
        else:
            display_info("No topic column found. Creating single file with all articles.")
            return ['all_articles']
    
    def create_topic_file(self, topic: str, df: pd.DataFrame) -> bool:
        """
        Create a CSV file for a specific topic
        
        Args:
            topic: Topic name
            df: DataFrame with news data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if topic == 'all_articles':
                topic_rows = df.dropna()
            else:
                topic_rows = df[df['topic'] == topic].dropna()
            
            if topic_rows.empty:
                display_info(f"No articles found for topic '{topic}'")
                return False
            
            # Create filename
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_topic}.csv"
            file_path = self.output_dir / filename
            
            # Save to CSV
            topic_rows.to_csv(file_path, index=False)
            display_success(f"Created {filename} with {len(topic_rows)} articles")
            return True
            
        except Exception as e:
            display_error(f"Error creating file for topic '{topic}': {str(e)}")
            return False
    
    def process_topics(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Process all topics and create individual files with progress tracking
        
        Args:
            df: DataFrame with news data
            
        Returns:
            Dictionary with topic names and article counts
        """
        topics = self.get_topics(df)
        results = {}
        
        with ProgressManager("Creating topic clusters", len(topics)) as progress:
            for i, topic in enumerate(topics):
                success = self.create_topic_file(topic, df)
                if success:
                    topic_rows = df[df['topic'] == topic].dropna() if topic != 'all_articles' else df.dropna()
                    results[topic] = len(topic_rows)
                
                progress.update(1, f"Processing topic {i+1}/{len(topics)}: {topic}")
        
        return results

def main() -> None:
    """Main execution function with enhanced progress tracking"""
    display_section_header("Topic Clusterer", "Organizing articles by topic")
    
    # Setup paths
    input_file = AppConfig.NEWS_WITH_TOPICS_FILE
    output_dir = AppConfig.TOPICS_DIR
    
    # Initialize processor
    processor = TopicClusterer(input_file, output_dir)
    
    # Validate input file
    if not processor.validate_input_file():
        display_error("Please run topic_classifier.py first to create the input file.")
        exit(1)
    
    # Load data
    df = processor.load_data()
    if df is None:
        exit(1)
    
    # Process topics
    display_info("Creating topic clusters...")
    results = processor.process_topics(df)
    
    # Print summary
    display_success("Topic cluster formation completed!")
    display_info("Summary:")
    total_articles = sum(results.values())
    display_info(f"  Total articles processed: {total_articles}")
    display_info(f"  Topic files created: {len(results)}")
    
    for topic, count in results.items():
        display_info(f"  {topic}: {count} articles")
    
    display_success(f"Check {output_dir} for topic files")

if __name__ == "__main__":
    main() 