import os
import json
from newsapi import NewsApiClient
from dotenv import load_dotenv


def fetch_news_data(config):
    load_dotenv()
    api_key = os.getenv(config['news_api']['api_key_env_var'])

    newsapi = NewsApiClient(api_key=api_key)

    top_headlines = newsapi.get_everything(
        q=config['news_api']['query'],
        sources=config['news_api']['sources'],
        domains=config['news_api']['domains']
    )

    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(top_headlines, f, ensure_ascii=False, indent=4)

    print("Data saved to news_data.json")