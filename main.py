#!/usr/bin/env python3
"""
News Extractor Summarizer - Main Entry Point
A comprehensive news processing pipeline with progress bars and improved structure
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.pipeline import PipelineOrchestrator

def main():
    """Main entry point for the News Extractor Summarizer"""
    try:
        # Initialize and run the pipeline
        orchestrator = PipelineOrchestrator()
        success = orchestrator.run_pipeline()
        
        if success:
            print("\n🎉 Pipeline completed successfully!")
            print("Check the 'dataset' directory for results.")
        else:
            print("\n❌ Pipeline completed with errors.")
            print("Check the output above for details.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
