"""
Main pipeline orchestrator for the News Extractor Summarizer
Coordinates all processing modules with enhanced progress tracking and error handling
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any
import logging
import time

from .utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info, display_warning
from .utils.config import Config
from .core.news_crawler import NewsCrawler
from .core.content_extractor import ContentExtractor
from .core.topic_classifier import TopicClassifier
from .core.topic_clusterer import TopicClusterer
from .core.summarizer import MultiSummarizer, TopicProcessor
from .core.graph_summarizer import GraphSummarizer, FileProcessor
from .core.result_display import ResultDisplay

class PipelineOrchestrator:
    """Main pipeline orchestrator with comprehensive progress tracking"""
    
    def __init__(self):
        """Initialize the pipeline orchestrator"""
        self.steps = [
            ('news_crawler', 'News Crawling', self._run_news_crawler),
            ('content_extractor', 'Content Extraction', self._run_content_extractor),
            ('topic_classifier', 'Topic Classification', self._run_topic_classifier),
            ('topic_clusterer', 'Topic Clustering', self._run_topic_clusterer),
            ('summarizer', 'Multi-Document Summarization', self._run_summarizer),
            ('graph_summarizer', 'Graph-Based Summarization', self._run_graph_summarizer),
            ('result_display', 'Result Display', self._run_result_display)
        ]
        
        self.results = {}
        self.failed_steps = []
    
    def setup_environment(self, steps_to_run: List[str] = None) -> bool:
        """Setup the environment and validate prerequisites"""
        try:
            display_section_header("Pipeline Setup", "Initializing environment and validating prerequisites")
            
            # Create directories
            Config.create_directories()
            
            # Only validate API keys for steps that need them
            if steps_to_run is None or any(step in ['news_crawler', 'content_extractor', 'topic_classifier'] for step in steps_to_run):
                api_validation = Config.validate_api_keys()
                required_keys = Config.get_required_api_keys()
                
                if required_keys:
                    display_warning("Missing API keys:")
                    for key in required_keys:
                        display_warning(f"  - {key}")
                    display_info("Please set these in your .env file")
                    return False
            
            display_success("Environment setup completed successfully")
            return True
            
        except Exception as e:
            display_error(f"Environment setup failed: {str(e)}")
            return False
    
    def _run_news_crawler(self) -> bool:
        """Run news crawling step"""
        try:
            display_info("Starting news crawling...")
            crawler = NewsCrawler()
            
            # Use the configuration that was already set up
            config = Config.NEWS_API_CONFIG.copy()
            
            # Fetch articles
            articles = crawler.fetch_articles(config)
            if not articles:
                return False
            
            # Save to CSV
            crawler.save_to_csv(articles, "news_1.csv")
            return True
            
        except Exception as e:
            display_error(f"News crawling failed: {str(e)}")
            return False
    
    def _run_content_extractor(self) -> bool:
        """Run content extraction step"""
        try:
            display_info("Starting content extraction...")
            
            # Validate input file
            if not Config.NEWS_RAW_FILE.exists():
                display_error("News raw file not found. Please run news crawling first.")
                return False
            
            # Run content extraction
            from .core.content_extractor import main as content_extractor_main
            content_extractor_main()
            return True
            
        except Exception as e:
            display_error(f"Content extraction failed: {str(e)}")
            return False
    
    def _run_topic_classifier(self) -> bool:
        """Run topic classification step"""
        try:
            display_info("Starting topic classification...")
            
            # Validate input file
            if not Config.NEWS_WITH_CONTENT_FILE.exists():
                display_error("News with content file not found. Please run content extraction first.")
                return False
            
            # Run topic classification
            from .core.topic_classifier import main as topic_classifier_main
            topic_classifier_main()
            return True
            
        except Exception as e:
            display_error(f"Topic classification failed: {str(e)}")
            return False
    
    def _run_topic_clusterer(self) -> bool:
        """Run topic clustering step"""
        try:
            display_info("Starting topic clustering...")
            
            # Validate input file
            if not Config.NEWS_WITH_TOPICS_FILE.exists():
                display_error("News with topics file not found. Please run topic classification first.")
                return False
            
            # Run topic clustering
            from .core.topic_clusterer import main as topic_clusterer_main
            topic_clusterer_main()
            return True
            
        except Exception as e:
            display_error(f"Topic clustering failed: {str(e)}")
            return False
    
    def _run_summarizer(self) -> bool:
        """Run multi-document summarization step"""
        try:
            display_info("Starting multi-document summarization...")
            
            # Validate input directory
            if not Config.TOPICS_DIR.exists():
                display_error("Topics directory not found. Please run topic clustering first.")
                return False
            
            # Run summarization
            from .core.summarizer import main as summarizer_main
            summarizer_main()
            return True
            
        except Exception as e:
            display_error(f"Multi-document summarization failed: {str(e)}")
            return False
    
    def _run_graph_summarizer(self) -> bool:
        """Run graph-based summarization step"""
        try:
            display_info("Starting graph-based summarization...")
            
            # Validate input directory
            if not Config.MULTI_SUMMARIES_DIR.exists():
                display_error("Multi-summaries directory not found. Please run summarization first.")
                return False
            
            # Run graph summarization
            from .core.graph_summarizer import main as graph_summarizer_main
            graph_summarizer_main()
            return True
            
        except Exception as e:
            display_error(f"Graph-based summarization failed: {str(e)}")
            return False
    
    def _run_result_display(self) -> bool:
        """Run result display step"""
        try:
            display_info("Starting result display...")
            
            # Validate directories
            if not Config.GRAPHS_DIR.exists() or not Config.FINAL_DIR.exists():
                display_error("Results directories not found. Please run the pipeline first.")
                return False
            
            # Run result display
            from .core.result_display import main as result_display_main
            result_display_main()
            return True
            
        except Exception as e:
            display_error(f"Result display failed: {str(e)}")
            return False
    
    def run_step(self, step_id: str, step_name: str, step_func) -> bool:
        """Run a single pipeline step with progress tracking"""
        try:
            display_section_header(f"Step: {step_name}", f"Executing {step_id}")
            
            start_time = time.time()
            success = step_func()
            end_time = time.time()
            
            if success:
                duration = end_time - start_time
                display_success(f"{step_name} completed successfully in {duration:.2f} seconds")
                self.results[step_id] = {'status': 'success', 'duration': duration}
                return True
            else:
                display_error(f"{step_name} failed")
                self.results[step_id] = {'status': 'failed', 'duration': 0}
                self.failed_steps.append(step_id)
                return False
                
        except Exception as e:
            display_error(f"Unexpected error in {step_name}: {str(e)}")
            self.results[step_id] = {'status': 'error', 'duration': 0}
            self.failed_steps.append(step_id)
            return False
    
    def run_pipeline(self, steps_to_run: List[str] = None) -> bool:
        """Run the complete pipeline or specified steps"""
        display_section_header("News Extractor Summarizer Pipeline", "Starting comprehensive news processing pipeline")
        
        # Setup environment
        if not self.setup_environment(steps_to_run):
            return False
        
        # Determine which steps to run
        if steps_to_run is None:
            steps_to_run = [step[0] for step in self.steps]
        
        # Filter steps
        filtered_steps = [step for step in self.steps if step[0] in steps_to_run]
        
        if not filtered_steps:
            display_error("No valid steps specified")
            return False
        
        # Run pipeline with overall progress tracking
        successful_steps = 0
        
        with ProgressManager("Pipeline Execution", len(filtered_steps)) as progress:
            for i, (step_id, step_name, step_func) in enumerate(filtered_steps):
                success = self.run_step(step_id, step_name, step_func)
                if success:
                    successful_steps += 1
                
                progress.update(1, f"Completed {i+1}/{len(filtered_steps)} steps")
        
        # Display final summary
        self._display_summary(successful_steps, len(filtered_steps))
        
        return successful_steps == len(filtered_steps)
    
    def _display_summary(self, successful_steps: int, total_steps: int) -> None:
        """Display pipeline execution summary"""
        display_section_header("Pipeline Summary", "Execution results and statistics")
        
        display_info(f"Total steps: {total_steps}")
        display_info(f"Successful: {successful_steps}")
        display_info(f"Failed: {total_steps - successful_steps}")
        
        if successful_steps == total_steps:
            display_success("🎉 Pipeline completed successfully!")
        else:
            display_warning(f"⚠️  Pipeline completed with {total_steps - successful_steps} failures")
        
        # Display detailed results
        display_info("\nDetailed Results:")
        for step_id, result in self.results.items():
            status_icon = "✓" if result['status'] == 'success' else "✗"
            status_color = "green" if result['status'] == 'success' else "red"
            display_info(f"  {status_icon} {step_id}: {result['status']} ({result['duration']:.2f}s)")
        
        if self.failed_steps:
            display_warning(f"\nFailed steps: {', '.join(self.failed_steps)}")

def main():
    """Main entry point for the pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="News Extractor Summarizer Pipeline")
    parser.add_argument("--steps", nargs="+", help="Specific steps to run")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    
    args = parser.parse_args()
    
    # Determine steps to run
    if args.all or not args.steps:
        steps_to_run = None  # Run all steps
    else:
        steps_to_run = args.steps
    
    # Run pipeline
    orchestrator = PipelineOrchestrator()
    success = orchestrator.run_pipeline(steps_to_run)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 