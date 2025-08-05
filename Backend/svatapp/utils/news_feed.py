import requests
from typing import Dict, List, Any
import feedparser
from datetime import datetime

def fetch_all_news() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch security news from multiple RSS feeds.
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary mapping source names to lists of news items
    """
    feeds = {
        "nvd": "https://nvd.nist.gov/feeds/xml/cve/rss/nvdrss.xml",
        "threatpost": "https://threatpost.com/feed/",
        "securityweek": "https://www.securityweek.com/feed/"
    }
    news_data = {}
    
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            entries = []
            for entry in feed.entries[:10]:  # Limit to 10 entries per source
                published = entry.get('published', 'N/A')
                try:
                    published = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
                entries.append({
                    "title": entry.get('title', 'No title'),
                    "link": entry.get('link', '#'),
                    "published": published
                })
            news_data[source] = entries
        except Exception as e:
            news_data[source] = []
            print(f"Error fetching news from {source}: {str(e)}")
    
    return news_data