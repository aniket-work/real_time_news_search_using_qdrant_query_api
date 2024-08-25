from qdrant_client import QdrantClient, models
import tqdm

def init_qdrant_client(config):
    return QdrantClient(
        url=config['qdrant']['url'],
        timeout=config['qdrant']['timeout']
    )

def create_collection(client, config):
    client.create_collection(
        config['qdrant']['collection_name'],
        vectors_config={
            "all-MiniLM-L6-v2": models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            ),
            "colbertv2.0": models.VectorParams(
                size=128,
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

def index_articles(client, articles, embedding_models, config):
    batch_size = config['indexing']['batch_size']
    for i in tqdm.tqdm(range(0, len(articles), batch_size)):
        batch = articles[i:i + batch_size]
        texts = [article['content'] for article in batch]

        dense_embeddings = list(embedding_models['dense'].passage_embed(texts))
        bm25_embeddings = list(embedding_models['bm25'].passage_embed(texts))
        late_interaction_embeddings = list(embedding_models['late_interaction'].passage_embed(texts))

        client.upload_points(
            config['qdrant']['collection_name'],
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