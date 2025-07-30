"""
Multi-document summarization module with progress bars and improved error handling
"""

from transformers import PegasusForConditionalGeneration, AutoTokenizer
import csv
import numpy as np
import os
from pathlib import Path
import re
import pandas as pd
import sys
from typing import List, Dict, Optional, Tuple
import logging
import time

from ..utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info, display_warning
from ..utils.config import Config as AppConfig

class MultiSummarizer:
    """Enhanced multi-document summarizer with progress tracking"""
    
    def __init__(self):
        """Initialize the MultiSummarizer with model loading"""
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the Pegasus model and tokenizer"""
        try:
            display_info("Loading Pegasus model...")
            self.tokenizer = AutoTokenizer.from_pretrained(AppConfig.SUMMARIZATION_CONFIG['model_name'])
            self.model = PegasusForConditionalGeneration.from_pretrained(AppConfig.SUMMARIZATION_CONFIG['model_name'])
            display_success("Pegasus model loaded successfully")
        except Exception as e:
            display_error(f"Failed to load Pegasus model: {str(e)}")
            sys.exit(1)
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for summarization
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        if not text or pd.isna(text):
            return ""
        
        # Clean text
        text = str(text).strip()
        text = text.replace("\n", " ")
        text = re.sub(r'[^\w\s\.]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def validate_text(self, text: str) -> bool:
        """
        Validate if text is suitable for summarization
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not text or len(text.split()) < AppConfig.SUMMARIZATION_CONFIG['min_text_length']:
            return False
        
        # Check for common low-quality content patterns
        low_quality_patterns = [
            'all images are copyrighted',
            'all photographs',
            'javascript seems to be disabled',
            'please enable javascript',
            'consent',
            'error',
            'blocked',
            'access denied'
        ]
        
        text_lower = text.lower()
        for pattern in low_quality_patterns:
            if pattern in text_lower:
                return False
        
        return True
    
    def summarize_text(self, text: str) -> str:
        """
        Summarize a single text using Pegasus model
        
        Args:
            text: Text to summarize
            
        Returns:
            Generated summary
        """
        try:
            # Preprocess text
            text = self.preprocess_text(text)
            
            if not self.validate_text(text):
                return "Article too short to summarize."
            
            # Tokenize
            tokens = self.tokenizer.encode(
                text, 
                return_tensors='pt', 
                max_length=AppConfig.SUMMARIZATION_CONFIG['max_input_length'], 
                truncation=True
            )
            
            # Check token length
            if tokens.shape[1] > self.model.config.max_position_embeddings:
                tokens = self.tokenizer.encode(
                    text, 
                    return_tensors='pt', 
                    max_length=self.model.config.max_position_embeddings, 
                    truncation=True
                )
            
            # Generate summary
            summary_ids = self.model.generate(
                tokens,
                max_length=AppConfig.SUMMARIZATION_CONFIG['max_length'],
                num_beams=AppConfig.SUMMARIZATION_CONFIG['num_beams'],
                temperature=AppConfig.SUMMARIZATION_CONFIG['temperature'],
                do_sample=AppConfig.SUMMARIZATION_CONFIG['do_sample']
            )
            
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            # Ensure summary ends with period
            if summary and not summary.endswith('.'):
                summary += '.'
            
            return summary
            
        except Exception as e:
            logging.warning(f"Error in summarization: {str(e)}")
            return "Error generating summary."
    
    def process_batch(self, texts: List[str]) -> List[str]:
        """
        Process a batch of texts for summarization
        
        Args:
            texts: List of texts to summarize
            
        Returns:
            List of summaries
        """
        summaries = []
        for text in texts:
            summary = self.summarize_text(text)
            summaries.append(summary)
        return summaries

class TopicProcessor:
    """Enhanced topic processor with progress tracking"""
    
    def __init__(self, input_dir: Path, output_dir: Path):
        """
        Initialize the TopicProcessor
        
        Args:
            input_dir: Directory containing topic CSV files
            output_dir: Directory to save summaries
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_csv_files(self) -> List[Path]:
        """
        Get list of CSV files in input directory
        
        Returns:
            List of CSV file paths
        """
        csv_files = list(self.input_dir.glob('*.csv'))
        if not csv_files:
            display_warning(f"No CSV files found in {self.input_dir}")
        return csv_files
    
    def find_content_column(self, columns: List[str]) -> Optional[str]:
        """
        Find the appropriate content column in CSV
        
        Args:
            columns: List of column names
            
        Returns:
            Content column name or None
        """
        content_columns = ["final_full_content", "spacy_full_content", "raw_full_content", "Content"]
        for col in content_columns:
            if col in columns:
                return col
        return None
    
    def extract_content(self, csv_file: Path) -> List[str]:
        """
        Extract content from CSV file with improved content selection
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            List of content texts
        """
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                columns = next(reader)
                
                # Find all available content columns
                content_columns = ["final_full_content", "spacy_full_content", "raw_full_content", "Content", "Description", "Title"]
                available_columns = {}
                for col in content_columns:
                    if col in columns:
                        available_columns[col] = columns.index(col)
                
                if not available_columns:
                    display_error(f"No content columns found in {csv_file.name}")
                    return []
                
                content_list = []
                
                for row in reader:
                    if len(row) > max(available_columns.values()):
                        # Try to get the best content from available columns
                        best_content = ""
                        best_length = 0
                        
                        for col_name, col_index in available_columns.items():
                            if col_index < len(row):
                                content = row[col_index]
                                if content and not pd.isna(content) and len(content.strip()) > 20:
                                    # Prefer longer, more substantial content
                                    if len(content) > best_length:
                                        best_content = content
                                        best_length = len(content)
                        
                        if best_content:
                            content_list.append(best_content)
                
                return content_list
                
        except Exception as e:
            display_error(f"Error reading {csv_file.name}: {str(e)}")
            return []
    
    def save_summaries(self, summaries: List[str], output_filename: str) -> None:
        """
        Save summaries to text file
        
        Args:
            summaries: List of summaries
            output_filename: Output filename
        """
        output_path = self.output_dir / output_filename
        
        try:
            with open(output_path, "w", encoding='utf-8') as f:
                for summary in summaries:
                    if summary.strip():
                        f.write(summary + "\n")
            
            display_success(f"Saved {len(summaries)} summaries to {output_filename}")
            
        except Exception as e:
            display_error(f"Error saving {output_filename}: {str(e)}")

def main() -> None:
    """Main execution function with enhanced progress tracking"""
    display_section_header("Multi-Document Summarizer", "Generating summaries for topic clusters")
    
    # Setup paths
    input_dir = AppConfig.TOPICS_DIR
    output_dir = AppConfig.MULTI_SUMMARIES_DIR
    
    # Validate input directory
    if not input_dir.exists():
        display_error(f"Input directory {input_dir} does not exist.")
        display_warning("Please run topic_clusterer.py first.")
        sys.exit(1)
    
    # Initialize processors
    summarizer = MultiSummarizer()
    processor = TopicProcessor(input_dir, output_dir)
    
    # Get CSV files
    csv_files = processor.get_csv_files()
    if not csv_files:
        sys.exit(1)
    
    # Process each CSV file
    total_processed = 0
    
    with ProgressManager("Processing topic files", len(csv_files)) as progress:
        for i, csv_file in enumerate(csv_files):
            display_info(f"Processing {csv_file.name}...")
            
            # Extract content
            content_list = processor.extract_content(csv_file)
            if not content_list:
                display_warning(f"No content found in {csv_file.name}")
                progress.update(1)
                continue
            
            display_info(f"Found {len(content_list)} articles to summarize")
            
            # Process in batches
            summaries = []
            batch_size = AppConfig.SUMMARIZATION_CONFIG['batch_size']
            
            with ProgressManager(f"Summarizing {csv_file.name}", len(content_list)) as batch_progress:
                for j in range(0, len(content_list), batch_size):
                    batch = content_list[j:j + batch_size]
                    batch_summaries = summarizer.process_batch(batch)
                    summaries.extend(batch_summaries)
                    batch_progress.update(len(batch), f"Batch {j//batch_size + 1}")
            
            # Save summaries
            output_filename = csv_file.stem + '.txt'
            processor.save_summaries(summaries, output_filename)
            
            total_processed += len(content_list)
            progress.update(1, f"Processed {i+1}/{len(csv_files)} files")
    
    display_success("Multi-summarization completed!")
    display_info(f"Total articles processed: {total_processed}")
    display_info(f"Summary files created: {len(csv_files)}")
    display_success(f"Check {output_dir} for results")

if __name__ == "__main__":
    main() 