#!/usr/bin/env python3
"""
Setup script for NewsMelt - Advanced News Analysis & Data Visualization Platform
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path('.env')
    if not env_file.exists():
        print("\n📝 Creating .env file...")
        env_content = """# NewsMelt Environment Configuration
# Add your API keys here

# Required API Keys
# Get your NewsAPI key from: https://newsapi.org/
NEWS_API=your_news_api_key_here

# Get your Google API key from: https://console.cloud.google.com/
GOOGLE_API=your_google_api_key_here

# Get your Search Engine ID from: https://programmablesearchengine.google.com/
SEARCH_ENGINE_ID=your_search_engine_id_here
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your actual API keys")
    else:
        print("✅ .env file already exists")

def create_directories():
    """Create necessary directories"""
    directories = [
        'cache_dir',
        'dataset',
        'output',
        'dataset/raw',
        'dataset/topics',
        'dataset/multi-summaries',
        'dataset/graphs',
        'dataset/final'
    ]
    
    print("\n📁 Creating directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")

def check_python_version():
    """Check if Python version is compatible"""
    print(f"\n🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    return True

def download_models():
    """Download required NLP models"""
    print("\n🤖 Setting up NLP models...")
    
    # Download SpaCy model
    if not run_command("python -m spacy download en_core_web_sm", "Downloading SpaCy model"):
        print("⚠️  SpaCy model download failed, will be downloaded on first run")
    
    print("✅ Model setup instructions:")
    print("   - Pegasus-XSum and T5 models will be downloaded automatically on first run")
    print("   - This may take several minutes depending on your internet connection")
    print("   - Models will be cached in cache_dir/transformers/")
    
    return True

def main():
    """Main setup function"""
    print("🚀 NewsMelt Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Setup models
    download_models()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Run: python main.py")
    print("3. Open app/index.html in your browser")
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main() 