from typing import cast

import httpx

from app.core.config import settings

def get_embedding(text: str) -> list[float]:
    response = httpx.post(
        f'{settings.ollama_url}/api/embeddings',
        json={'model': settings.embedding_model, 'prompt': text},
        timeout=60.0,
    )
    response.raise_for_status()
    return cast(list[float], response.json()['embedding'])