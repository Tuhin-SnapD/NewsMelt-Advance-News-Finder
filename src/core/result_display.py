"""
Result display module with progress bars and improved error handling
"""

from PIL import Image
import os
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from ..utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info, display_warning
from ..utils.config import Config as AppConfig

class ResultDisplay:
    """Enhanced result display with progress tracking"""
    
    def __init__(self, graphs_dir: Path, summaries_dir: Path):
        """
        Initialize the ResultDisplay
        
        Args:
            graphs_dir: Directory containing PNG graph files
            summaries_dir: Directory containing TXT summary files
        """
        self.graphs_dir = graphs_dir
        self.summaries_dir = summaries_dir
    
    def validate_directories(self) -> bool:
        """
        Validate that required directories exist
        
        Returns:
            True if valid, False otherwise
        """
        if not self.graphs_dir.exists():
            display_error(f"Graphs directory {self.graphs_dir} does not exist.")
            return False
        
        if not self.summaries_dir.exists():
            display_error(f"Summaries directory {self.summaries_dir} does not exist.")
            return False
        
        return True
    
    def get_png_files(self) -> List[Path]:
        """
        Get list of PNG files in graphs directory
        
        Returns:
            List of PNG file paths
        """
        png_files = list(self.graphs_dir.glob('*.png'))
        if not png_files:
            display_warning(f"No PNG files found in {self.graphs_dir}")
        return png_files
    
    def find_corresponding_txt(self, png_file: Path) -> Optional[Path]:
        """
        Find corresponding TXT file for a PNG file
        
        Args:
            png_file: Path to PNG file
            
        Returns:
            Path to corresponding TXT file or None
        """
        txt_file = self.summaries_dir / f"{png_file.stem}.txt"
        return txt_file if txt_file.exists() else None
    
    def display_image(self, image_path: Path) -> bool:
        """
        Display PNG image
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            img = Image.open(image_path)
            img.show()
            return True
        except Exception as e:
            display_error(f"Error displaying image {image_path.name}: {str(e)}")
            return False
    
    def read_summary(self, txt_path: Path) -> Optional[str]:
        """
        Read summary from TXT file
        
        Args:
            txt_path: Path to TXT file
            
        Returns:
            Summary text or None if error
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return content
        except Exception as e:
            display_error(f"Error reading summary {txt_path.name}: {str(e)}")
            return None
    
    def display_result_pair(self, png_file: Path, txt_file: Path) -> bool:
        """
        Display a pair of PNG graph and TXT summary
        
        Args:
            png_file: Path to PNG file
            txt_file: Path to TXT file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Display image
            if not self.display_image(png_file):
                return False
            
            # Read and display summary
            summary = self.read_summary(txt_file)
            if summary is None:
                return False
            
            # Display summary
            topic_name = png_file.stem
            display_success(f"Most important news of {topic_name}:")
            display_info(summary)
            display_info("=" * 60)
            
            return True
            
        except Exception as e:
            display_error(f"Error displaying result pair: {str(e)}")
            return False
    
    def process_all_results(self) -> Tuple[int, int]:
        """
        Process all PNG files and display corresponding results with progress tracking
        
        Returns:
            Tuple of (total_files, successful_displays)
        """
        png_files = self.get_png_files()
        if not png_files:
            return 0, 0
        
        display_info(f"Found {len(png_files)} graph files to display")
        display_info("=" * 60)
        
        successful_displays = 0
        
        with ProgressManager("Displaying results", len(png_files)) as progress:
            for i, png_file in enumerate(png_files):
                txt_file = self.find_corresponding_txt(png_file)
                
                if txt_file:
                    if self.display_result_pair(png_file, txt_file):
                        successful_displays += 1
                else:
                    display_warning(f"No corresponding TXT file found for {png_file.name}")
                
                progress.update(1, f"Displayed {i+1}/{len(png_files)} results")
        
        return len(png_files), successful_displays

def main() -> None:
    """Main execution function with enhanced progress tracking"""
    display_section_header("Result Display", "Displaying final results and visualizations")
    
    # Setup paths
    graphs_dir = AppConfig.GRAPHS_DIR
    summaries_dir = AppConfig.FINAL_DIR
    
    # Initialize display handler
    display = ResultDisplay(graphs_dir, summaries_dir)
    
    # Validate directories
    if not display.validate_directories():
        display_error("Please run the pipeline first to generate results.")
        return
    
    # Process and display results
    total_files, successful_displays = display.process_all_results()
    
    # Print summary
    display_success("Display completed!")
    display_info("Summary:")
    display_info(f"  Total graph files: {total_files}")
    display_info(f"  Successfully displayed: {successful_displays}")
    
    if successful_displays == 0:
        display_warning("No results were displayed. Check if the pipeline completed successfully.")

if __name__ == "__main__":
    main() 