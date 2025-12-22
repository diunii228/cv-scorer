from sentence_transformers import SentenceTransformer
from core.config import settings

class EmbeddingModel:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            print(f"⏳ Loading Embedding Model: {settings.EMBEDDING_MODEL_NAME}...")
            cls._instance = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return cls._instance