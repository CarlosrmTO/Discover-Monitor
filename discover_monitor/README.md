# Google Discover Monitor

A Python-based tool to monitor and track articles from multiple news websites that appear in Google Discover.

## Features

- Monitors multiple Spanish news websites for new articles
- Tracks article metadata including title, section, and publication date
- Identifies which articles appear in Google Discover (for your own site)
- Saves data to CSV for analysis
- Handles sitemap indexes and nested sitemaps
- Respects robots.txt and includes proper user-agent headers

## Prerequisites

- Python 3.7+
- pip (Python package manager)
- Google Search Console account (for tracking your own site in Discover)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd discover-monitor
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Google Search Console API (for your own site):
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Search Console API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials JSON file and save it as `credentials.json` in the project root

## Configuration

Edit the `config.py` file to:
- Add or remove websites from the `WEBSITES` list
- Update the `GSC_PROPERTY` to match your Search Console property (e.g., 'sc-domain:theobjective.com')
- Adjust data storage locations if needed

## Usage

### Basic Usage

```bash
python main.py
```

This will:
1. Scan all configured websites for new articles
2. Extract article metadata
3. Save the results to `data/articles.csv`

### Command Line Options

```bash
python main.py --limit 20 --output data/my_report.csv
```

- `--limit`: Maximum number of articles to process per website (default: 50)
- `--output`: Output CSV file path (default: data/discover_report.csv)

## Output

The tool generates two main output files:

1. `data/articles.csv`: Contains all discovered articles with their metadata
   - url: Article URL
   - title: Article title
   - section: Website section/category
   - description: Article description (if available)
   - timestamp: When the article was processed
   - source: Website name
   - is_own_site: Whether it's from your own website

2. `data/discover_data.csv`: Contains Google Discover performance data (if configured)

## Scheduling Regular Runs

To run the monitor daily, you can set up a cron job (Linux/macOS) or Task Scheduler (Windows):

```bash
# Example cron job to run daily at 8 AM
0 8 * * * cd /path/to/discover-monitor && /path/to/venv/bin/python main.py
```

## Troubleshooting

- **Sitemap Issues**: Some websites may have non-standard sitemap formats. You may need to update the `fetch_sitemap` method in `scraper.py` to handle these cases.
- **Rate Limiting**: The tool includes delays between requests, but some sites may still block aggressive scraping. If you encounter issues, try increasing the delay.
- **Google API Limits**: The Google Search Console API has usage limits. If you hit these limits, the tool will back off and retry.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
