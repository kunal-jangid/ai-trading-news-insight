import json
from eventregistry import EventRegistry, QueryArticlesIter, QueryItems

class NewsFetcher:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("EVENT_REGISTRY_API_KEY is not set. Please add it to your .env file.")
        self.er = EventRegistry(apiKey=api_key, allowUseOfArchive=True)

    def fetch_historical_news(self, keywords: list, start_date: str, end_date: str, output_file: str = "news_archive.jsonl", max_articles: int = 1000):
        # We now accept a list of strings for keywords
        print(f"Starting news fetch for: {keywords} from {start_date} to {end_date}")
        
        # QueryItems.OR() properly formats the boolean search for the API
        q = QueryArticlesIter(
            keywords=QueryItems.OR(keywords),
            dateStart=start_date,
            dateEnd=end_date,
            lang="eng"
        )
        
        downloaded_count = 0
        
        try:
            with open(output_file, "a", encoding="utf-8") as f:
                for art in q.execQuery(self.er, sortBy="date", maxItems=max_articles):
                    json.dump(art, f)
                    f.write("\n")
                    downloaded_count += 1
                    
                    if downloaded_count % 100 == 0:
                        print(f"Successfully downloaded {downloaded_count} articles...")
                        
        except Exception as e:
            print(f"News fetcher interrupted: {e}")
            
        print(f"Finished. Total articles saved: {downloaded_count} to {output_file}")
        return output_file