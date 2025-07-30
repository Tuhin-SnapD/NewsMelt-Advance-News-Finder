"""
Progress bar utilities using rich library for better visual feedback
"""

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional, Callable, Any
import time

console = Console()

class ProgressManager:
    """Centralized progress bar manager using rich library"""
    
    def __init__(self, description: str = "Processing", total: Optional[int] = None):
        """
        Initialize progress manager
        
        Args:
            description: Description of the current operation
            total: Total number of items to process
        """
        self.description = description
        self.total = total
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        )
        self.task_id = None
    
    def __enter__(self):
        """Context manager entry"""
        self.progress.start()
        if self.total:
            self.task_id = self.progress.add_task(
                self.description, 
                total=self.total
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.progress.stop()
    
    def update(self, advance: int = 1, description: Optional[str] = None):
        """Update progress"""
        if self.task_id is not None:
            if description:
                self.progress.update(self.task_id, description=description)
            self.progress.advance(self.task_id, advance)
    
    def set_description(self, description: str):
        """Set task description"""
        if self.task_id is not None:
            self.progress.update(self.task_id, description=description)

def create_progress_bar(description: str, total: int) -> ProgressManager:
    """
    Create a progress bar for a specific operation
    
    Args:
        description: Description of the operation
        total: Total number of items
        
    Returns:
        ProgressManager instance
    """
    return ProgressManager(description, total)

def process_with_progress(items: list, description: str, processor: Callable, 
                         show_progress: bool = True) -> list:
    """
    Process items with progress bar
    
    Args:
        items: List of items to process
        description: Description of the operation
        processor: Function to process each item
        show_progress: Whether to show progress bar
        
    Returns:
        List of processed items
    """
    results = []
    
    if show_progress:
        with ProgressManager(description, len(items)) as progress:
            for i, item in enumerate(items):
                try:
                    result = processor(item)
                    results.append(result)
                    progress.update(1, f"{description} ({i+1}/{len(items)})")
                except Exception as e:
                    console.print(f"[red]Error processing item {i}: {str(e)}[/red]")
                    results.append(None)
    else:
        for item in items:
            try:
                result = processor(item)
                results.append(result)
            except Exception as e:
                console.print(f"[red]Error processing item: {str(e)}[/red]")
                results.append(None)
    
    return results

def display_section_header(title: str, subtitle: Optional[str] = None):
    """Display a section header with rich formatting"""
    text = Text(title, style="bold cyan")
    if subtitle:
        text.append(f"\n{subtitle}", style="dim")
    
    panel = Panel(text, border_style="cyan")
    console.print(panel)

def display_success(message: str):
    """Display success message"""
    console.print(f"[green]✓ {message}[/green]")

def display_error(message: str):
    """Display error message"""
    console.print(f"[red]✗ {message}[/red]")

def display_warning(message: str):
    """Display warning message"""
    console.print(f"[yellow]⚠ {message}[/yellow]")

def display_info(message: str):
    """Display info message"""
    console.print(f"[blue]ℹ {message}[/blue]") 