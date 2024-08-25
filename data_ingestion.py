from fastembed.embedding import TextEmbedding

dense_embedding_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
dense_embeddings = list(dense_embedding_model.passage_embed(dataset["text"][0:1]))
len(dense_embeddings)