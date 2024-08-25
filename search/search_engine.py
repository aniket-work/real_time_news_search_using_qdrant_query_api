def search_articles(client, embedding_models, query, config, limit=None):
    if limit is None:
        limit = config['search']['default_limit']

    dense_query_vector = next(embedding_models['dense'].embed([query])).tolist()

    search_result = client.search(
        collection_name=config['qdrant']['collection_name'],
        query_vector=("all-MiniLM-L6-v2", dense_query_vector),
        limit=limit * 2,
        with_payload=True,
        score_threshold=config['search']['score_threshold'],
    )

    print(f"Number of results: {len(search_result)}")

    if not search_result:
        print("No results found. Checking collection info...")
        collection_info = client.get_collection(config['qdrant']['collection_name'])
        print(f"Collection info: {collection_info}")
        return []

    results = [
        {
            "dense_score": scored_point.score,
            "title": scored_point.payload["title"],
            "description": scored_point.payload["description"],
            "url": scored_point.payload["url"],
            "source": scored_point.payload["source"],
            "publishedAt": scored_point.payload["publishedAt"],
        }
        for scored_point in search_result
    ]

    results.sort(key=lambda x: x["dense_score"], reverse=True)

    return results[:limit]