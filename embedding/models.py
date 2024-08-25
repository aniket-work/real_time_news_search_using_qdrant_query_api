from fastembed.embedding import TextEmbedding
from fastembed.sparse.bm25 import Bm25
from fastembed.late_interaction import LateInteractionTextEmbedding

def init_embedding_models(config):
    return {
        "dense": TextEmbedding(config['embedding_models']['dense']),
        "bm25": Bm25(config['embedding_models']['bm25']),
        "late_interaction": LateInteractionTextEmbedding(config['embedding_models']['late_interaction'])
    }