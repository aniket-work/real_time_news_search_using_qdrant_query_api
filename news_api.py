import http.client
import urllib.parse
import os
from dotenv import load_dotenv
from fastembed.embedding import TextEmbedding
from fastembed.sparse.bm25 import Bm25
from fastembed.late_interaction import LateInteractionTextEmbedding
from qdrant_client import QdrantClient, models
import json
import tqdm

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv('NEWS_API')


"""
from newsapi import NewsApiClient

# Init
newsapi = NewsApiClient(api_key=api_key)

# /v2/top-headlines
top_headlines = newsapi.get_everything(q='bitcoin',
                            sources='bbc-news,the-verge',
                                       domains='bbc.co.uk,techcrunch.com')

print(top_headlines)

# Save the data as a JSON file
with open('news_data.json', 'w', encoding='utf-8') as f:
    json.dump(top_headlines, f, ensure_ascii=False, indent=4)

print("Data saved to news_data.json")

"""


# Load JSON data
with open('news_data.json', 'r') as f:
    data = json.load(f)

articles = data['articles']

# Initialize embedding models
dense_embedding_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
bm25_embedding_model = Bm25("Qdrant/bm25")
late_interaction_embedding_model = LateInteractionTextEmbedding("colbert-ir/colbertv2.0")

# Initialize Qdrant client
client = QdrantClient("http://localhost:6333", timeout=600)

# Create collection
client.create_collection(
    "news_articles",
    vectors_config={
        "all-MiniLM-L6-v2": models.VectorParams(
            size=384,  # Size for all-MiniLM-L6-v2
            distance=models.Distance.COSINE,
        ),
        "colbertv2.0": models.VectorParams(
            size=128,  # Size for colbertv2.0
            distance=models.Distance.COSINE,
            multivector_config=models.MultiVectorConfig(
                comparator=models.MultiVectorComparator.MAX_SIM,
            )
        ),
    },
    sparse_vectors_config={
        "bm25": models.SparseVectorParams(
            modifier=models.Modifier.IDF,
        )
    }
)

# Index data
batch_size = 4
for i in tqdm.tqdm(range(0, len(articles), batch_size)):
    batch = articles[i:i + batch_size]

    texts = [article['content'] for article in batch]

    dense_embeddings = list(dense_embedding_model.passage_embed(texts))
    bm25_embeddings = list(bm25_embedding_model.passage_embed(texts))
    late_interaction_embeddings = list(late_interaction_embedding_model.passage_embed(texts))

    client.upload_points(
        "news_articles",
        points=[
            models.PointStruct(
                id=i + j,
                vector={
                    "all-MiniLM-L6-v2": dense_embeddings[j].tolist(),
                    "bm25": bm25_embeddings[j].as_object(),
                    "colbertv2.0": late_interaction_embeddings[j].tolist(),
                },
                payload={
                    "title": article['title'],
                    "description": article['description'],
                    "url": article['url'],
                    "source": article['source']['name'],
                    "author": article['author'],
                    "publishedAt": article['publishedAt'],
                    "content": article['content']
                }
            )
            for j, article in enumerate(batch)
        ],
        batch_size=batch_size,
    )

    from fastembed.embedding import TextEmbedding
    from fastembed.sparse.bm25 import Bm25
    from fastembed.late_interaction import LateInteractionTextEmbedding

    dense_embedding_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    bm25_embedding_model = Bm25("Qdrant/bm25")
    late_interaction_embedding_model = LateInteractionTextEmbedding("colbert-ir/colbertv2.0")



#-----

from qdrant_client import QdrantClient, models
from fastembed.embedding import TextEmbedding
from fastembed.sparse.bm25 import Bm25

# Initialize the Qdrant client
client = QdrantClient("http://localhost:6333")

# Initialize the embedding models
dense_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
bm25_model = Bm25("Qdrant/bm25")

def search_articles(query, limit=5):
    # Step 1: Generate dense embedding for the query
    dense_query_vector = next(dense_model.embed([query])).tolist()

    # Step 2: Generate BM25 sparse vector for the query
    bm25_query_vector = next(bm25_model.embed([query]))

    # Step 3: Perform the search using dense embeddings
    search_result = client.search(
        collection_name="news_articles",
        query_vector=("all-MiniLM-L6-v2", dense_query_vector),
        limit=limit * 2,  # Retrieve more results for re-ranking
        with_payload=True,
        score_threshold=0.0,  # Remove the threshold for now
    )

    print(f"Number of results: {len(search_result)}")

    if not search_result:
        print("No results found. Checking collection info...")
        collection_info = client.get_collection("news_articles")
        print(f"Collection info: {collection_info}")
        return []

    # Step 4: Re-rank results using BM25 scores
    results = []
    for scored_point in search_result:
        # We don't have access to BM25 scores here, so we'll skip that part
        result = {
            "dense_score": scored_point.score,
            "title": scored_point.payload["title"],
            "description": scored_point.payload["description"],
            "url": scored_point.payload["url"],
            "source": scored_point.payload["source"],
            "publishedAt": scored_point.payload["publishedAt"],
        }
        results.append(result)

    # Step 5: Sort results by dense score (since we don't have BM25 scores)
    results.sort(key=lambda x: x["dense_score"], reverse=True)

    return results[:limit]

# Example usage
query = "bitcoin technology"
search_results = search_articles(query)

print(f"search_results: {search_results}")

print(f"Search results for query: '{query}'")
for i, result in enumerate(search_results, 1):
    print(f"\n{i}. {result['title']}")
    print(f"   Source: {result['source']}")
    print(f"   Published: {result['publishedAt']}")
    print(f"   Description: {result['description']}")
    print(f"   URL: {result['url']}")
    print(f"   Dense Score: {result['dense_score']:.4f}")

# Add this at the end to check the collection status
collection_info = client.get_collection("news_articles")
print(f"\nCollection info: {collection_info}")