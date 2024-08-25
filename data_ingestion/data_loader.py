import json

def load_articles():
    with open('news_data.json', 'r') as f:
        data = json.load(f)
    return data['articles']