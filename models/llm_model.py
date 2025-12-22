from huggingface_hub import hf_hub_download
from core.config import settings

class LocalLLM:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                from llama_cpp import Llama
                print("Loading Local LLM (Download ~5GB if first time)...")
                model_path = hf_hub_download(repo_id=settings.LLM_REPO_ID, filename=settings.LLM_FILENAME)
                cls._instance = Llama(
                    model_path=model_path,
                    n_ctx=4096,
                    n_gpu_layers=-1,
                    verbose=False
                )
                print("Local LLM loaded.")
            except ImportError:
                print("llama-cpp-python not installed.")
                return None
            except Exception as e:
                print(f"❌ Error loading LLM: {e}")
                return None
        return cls._instance