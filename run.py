#!/usr/bin/env python3
"""
News Extractor Summarizer - Enhanced Run Script
Command-line interface for the refactored news processing pipeline
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.pipeline import PipelineOrchestrator
from src.utils.progress import display_section_header, display_info, display_success, display_error
from src.utils.config import Config

def get_user_query():
    """Prompt user for search query with default value"""
    print("\n" + "="*60)
    print("🔍 NEWS EXTRACTOR SUMMARIZER")
    print("="*60)
    
    default_query = "business economy finance market stock investment company corporate trade economic financial commerce earnings revenue profit merger acquisition IPO startup technology innovation"
    
    print(f"\nEnter your search query (or press Enter for default):")
    print(f"Default: {default_query}")
    
    user_query = input("\nQuery: ").strip()
    
    if not user_query:
        user_query = default_query
        print(f"Using default query: {user_query}")
    
    return user_query

def update_config_with_user_input(query: str):
    """Update configuration with user input and default date range"""
    # Set the query
    Config.NEWS_API_CONFIG['query'] = query
    
    # Set default date range to last 15 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=15)
    
    Config.NEWS_API_CONFIG['from_date'] = start_date.strftime('%Y-%m-%d')
    Config.NEWS_API_CONFIG['to_date'] = end_date.strftime('%Y-%m-%d')
    Config.NEWS_API_CONFIG['language'] = 'en'
    
    print(f"\n📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (Last 15 days)")
    print(f"🌐 Language: English")
    print(f"🔍 Query: {query}")

def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="News Extractor Summarizer - Enhanced News Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Run complete pipeline with user prompt
  python run.py --step news_crawler # Run only news crawling
  python run.py --step content_extractor topic_classifier  # Run specific steps
  python run.py --validate         # Validate environment only
  python run.py --help             # Show this help message
        """
    )
    
    parser.add_argument(
        '--step', '--steps',
        nargs='+',
        choices=['news_crawler', 'content_extractor', 'topic_classifier', 
                'topic_clusterer', 'summarizer', 'graph_summarizer', 'result_display'],
        help='Specific pipeline steps to run'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate environment and API keys only'
    )
    
    parser.add_argument(
        '--list-steps',
        action='store_true',
        help='List all available pipeline steps'
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Search query (if not provided, will prompt user)'
    )
    
    parser.add_argument(
        '--no-prompt',
        action='store_true',
        help='Skip user prompt and use default query'
    )
    
    args = parser.parse_args()
    
    # List available steps
    if args.list_steps:
        display_section_header("Available Pipeline Steps", "Complete list of processing steps")
        steps = [
            ('news_crawler', 'Fetch news articles from NewsAPI'),
            ('content_extractor', 'Extract full content from article URLs'),
            ('topic_classifier', 'Classify articles into topics'),
            ('topic_clusterer', 'Organize articles by topic into separate files'),
            ('summarizer', 'Generate multi-document summaries'),
            ('graph_summarizer', 'Create graph-based summaries and visualizations'),
            ('result_display', 'Display final results and graphs')
        ]
        
        for i, (step, description) in enumerate(steps, 1):
            display_info(f"{i}. {step}: {description}")
        return
    
    # Validate environment only
    if args.validate:
        display_section_header("Environment Validation", "Checking prerequisites and API keys")
        try:
            orchestrator = PipelineOrchestrator()
            if orchestrator.setup_environment():
                display_success("Environment validation passed!")
                display_info("All prerequisites are satisfied.")
            else:
                display_error("Environment validation failed!")
                sys.exit(1)
        except Exception as e:
            display_error(f"Validation error: {str(e)}")
            sys.exit(1)
        return
    
    # Get user query and update configuration
    if args.query:
        query = args.query
        print(f"\nUsing provided query: {query}")
    elif args.no_prompt:
        query = Config.NEWS_API_CONFIG['query']
        print(f"\nUsing default query: {query}")
    else:
        query = get_user_query()
    
    # Update configuration with user input and default parameters
    update_config_with_user_input(query)
    
    # Run pipeline
    try:
        display_section_header("News Extractor Summarizer", "Enhanced News Processing Pipeline")
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Determine steps to run
        if args.step:
            steps_to_run = args.step
            display_info(f"Running specific steps: {', '.join(steps_to_run)}")
        else:
            steps_to_run = None
            display_info("Running complete pipeline")
        
        # Execute pipeline
        success = orchestrator.run_pipeline(steps_to_run)
        
        if success:
            display_success("🎉 Pipeline completed successfully!")
            display_info("Check the 'dataset' directory for results.")
        else:
            display_error("❌ Pipeline completed with errors.")
            display_info("Check the output above for details.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        display_error("⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        display_error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 