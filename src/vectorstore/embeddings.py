"""Wrapper de embeddings para intfloat/multilingual-e5-small.

Precaución crítica: los modelos de la familia E5 requieren anteponer
"query: " a las consultas y "passage: " a los textos indexados. Si se omite
este prefijo, o si se cambia de modelo/estrategia sin reindexar, los vectores
dejan de ser comparables aunque compartan la misma dimensión (384). Por eso
esta clase es el único punto donde se genera texto para embeber, tanto en
ingesta como en búsqueda.
"""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.config import settings


@lru_cache(maxsize=1)
def _modelo() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed_documentos(textos: list[str]) -> list[list[float]]:
    """Embebe fragmentos para indexar (prefijo 'passage: ')."""
    preparados = [f"passage: {t}" for t in textos]
    vectores = _modelo().encode(preparados, normalize_embeddings=True, convert_to_numpy=True)
    return vectores.tolist()


def embed_consulta(texto: str) -> list[float]:
    """Embebe una consulta de búsqueda (prefijo 'query: ')."""
    vector = _modelo().encode(f"query: {texto}", normalize_embeddings=True, convert_to_numpy=True)
    return vector.tolist()
