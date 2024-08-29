import streamlit as st
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from newsapi import NewsApiClient
from utils.config_loader import load_config
from data_ingestion.data_loader import load_articles
from embedding.models import init_embedding_models
from indexing.qdrant_indexer import init_qdrant_client, create_collection, index_articles
from search.search_engine import search_articles

def fetch_news_data(config):
    load_dotenv()
    api_key = os.getenv(config['news_api']['api_key_env_var'])

    newsapi = NewsApiClient(api_key=api_key)

    top_headlines = newsapi.get_everything(
        q=config['news_api']['query'],
        sources=config['news_api']['sources'],
        domains=config['news_api']['domains']
    )

    # Clean the JSON data
    cleaned_articles = []
    for article in top_headlines['articles']:
        cleaned_article = {
            'title': article['title'],
            'description': article['description'],
            'url': article['url'],
            'publishedAt': article['publishedAt'],
            'source': article['source']['name']
        }
        cleaned_articles.append(cleaned_article)

    cleaned_data = {'articles': cleaned_articles}

    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

    print("Data saved to news_data.json")

def main():
    config = load_config()

    # Fetch and load data
    fetch_news_data(config)
    articles = load_articles()

    # Initialize embedding models
    embedding_models = init_embedding_models(config)

    # Initialize Qdrant client and create collection
    qdrant_client = init_qdrant_client(config)
    create_collection(qdrant_client, config)

    # Index articles
    index_articles(qdrant_client, articles, embedding_models, config)

    return qdrant_client, embedding_models, config


import streamlit as st
from datetime import datetime


def streamlit_app():
    st.title("Real-Time News Search Using Qdrant Query API")

    # Initialize the main components
    if 'qdrant_client' not in st.session_state:
        st.session_state.qdrant_client, st.session_state.embedding_models, st.session_state.config = main()

    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 60  # Default to 60 minutes

    # User input
    query = st.text_input("Enter your search query:")

    # Refresh interval
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        new_refresh_interval = st.number_input("Refresh interval (minutes):", min_value=1,
                                               value=st.session_state.refresh_interval, step=1)
    with col2:
        if st.button("Set Interval"):
            st.session_state.refresh_interval = new_refresh_interval
            st.success(f"Interval set to {new_refresh_interval} min.")
    with col3:
        if st.button("Refresh Now"):
            st.session_state.last_refresh = datetime.now()
            st.session_state.qdrant_client, st.session_state.embedding_models, st.session_state.config = main()
            st.success("Data refreshed successfully!")

    if query:
        # Perform search
        search_results = search_articles(st.session_state.qdrant_client, st.session_state.embedding_models, query,
                                         st.session_state.config)

        # Display results in cards
        for result in search_results:
            # Check if 'payload' key exists, if not, use the result directly
            data = result.get('payload', result)

            with st.expander(data.get('title', 'No title available')):
                st.write(f"Source: {data.get('source', 'N/A')}")
                st.write(f"Published: {data.get('publishedAt', 'N/A')}")
                st.write(f"Description: {data.get('description', 'No description available')}")
                st.write(f"Score: {result.get('score', 0):.4f}")
                if 'url' in data:
                    st.markdown(f"[Read more]({data['url']})")

    # Auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()

    time_since_last_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds() / 60
    if time_since_last_refresh >= st.session_state.refresh_interval:
        st.session_state.qdrant_client, st.session_state.embedding_models, st.session_state.config = main()
        st.session_state.last_refresh = datetime.now()
        st.success("Data auto-refreshed successfully!")

    st.write(f"Last refresh: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"Current refresh interval: {st.session_state.refresh_interval} minutes")

if __name__ == "__main__":
    streamlit_app()