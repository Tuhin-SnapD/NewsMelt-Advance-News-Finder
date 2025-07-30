# 🚀 Quick Start Guide

Get NewsMelt up and running in 5 minutes!

## ⚡ Quick Setup

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/News-Extractor-Summarizer.git
cd News-Extractor-Summarizer
python setup.py
```

### 2. Add API Keys
Edit the `.env` file and add your API keys:
```env
NEWS_API=your_news_api_key_here
GOOGLE_API=your_google_api_key_here
SEARCH_ENGINE_ID=your_search_engine_id_here
```

### 3. Run the Application
```bash
python main.py
```

### 4. Open the Dashboard
Open `app/index.html` in your web browser or serve it:
```bash
python -m http.server 8000
# Then visit http://localhost:8000/app/
```

## 🔑 Getting API Keys

### NewsAPI (Free)
1. Visit [NewsAPI.org](https://newsapi.org/)
2. Sign up for free account
3. Copy your API key

### Google Custom Search (Free tier available)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Custom Search API
4. Create credentials (API key)
5. Visit [Programmable Search Engine](https://programmablesearchengine.google.com/)
6. Create a search engine and get the Search Engine ID

## 🎯 First Run

1. **Select a category** from the dashboard
2. **Wait for processing** (first run downloads models)
3. **View results** in the interactive dashboard
4. **Export reports** using the download button

## 🐛 Troubleshooting

### Models not downloading?
```bash
# Clear cache and retry
rm -rf cache_dir/transformers/*
python main.py
```

### Memory issues?
- Ensure you have 4GB+ RAM
- Close other applications
- Reduce batch sizes in `src/utils/config.py`

### API errors?
- Check your API keys in `.env`
- Verify API quotas and limits
- Ensure internet connection

## 📚 Need Help?

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/yourusername/News-Extractor-Summarizer/issues)
- 💬 [Ask Questions](https://github.com/yourusername/News-Extractor-Summarizer/discussions)

---

**Ready to analyze news like never before?** 🎉 