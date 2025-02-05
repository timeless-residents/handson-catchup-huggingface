# HuggingFace Model Tracker

This Python application automatically tracks and records trending and popular models from HuggingFace. It scrapes model information daily and stores it in a Notion database for easy reference and analysis.

## Features

- 🤖 Tracks trending models from HuggingFace
- 📊 Collects popular model statistics
- 📝 Stores model data in Notion
- ⏰ Runs automatically on a daily schedule
- 🔍 Enriches model data with detailed information

## Project Structure

```
├── config.py           # Configuration settings
├── main.py            # Main application entry point
├── models/            # Model definitions
│   └── huggingface.py # HuggingFace model class
└── services/          # Service implementations
    ├── huggingface.py # HuggingFace API service
    ├── notion.py      # Notion API service
    └── scraper.py     # Web scraping service
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/timeless-residents/handson-catchup-huggingface.git
cd handson-catchup-huggingface
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_notion_database_id
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
```

## Usage

Run the application:

```bash
python main.py
```

The application will:
1. Perform an initial update to fetch current trending and popular models
2. Set up a scheduler to run daily updates at the configured time
3. Continue running in the background, updating the Notion database with new model information each day

To stop the application, press `Ctrl+C`.

## Configuration

The application can be configured through `config.py`. Key settings include:
- Update time for daily runs (default: 09:00)
- Model limit for tracking (default: 10)
- API endpoints:
  - HuggingFace Base URL: https://huggingface.co
  - HuggingFace API URL: https://huggingface.co/api/models

## Requirements

- Python 3.7+
- HuggingFace API access
- Notion API access and a configured database

### Python Packages
- schedule: For scheduling daily updates
- requests: For API interactions
- python-dotenv: For environment variable management
- beautifulsoup4: For web scraping
- anthropic: For Anthropic API integration
- notion-client: For Notion API integration

See `requirements.txt` for specific version requirements.
