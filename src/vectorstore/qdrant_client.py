"""Cliente Qdrant de bajo nivel.

Se usa `qdrant-client` directamente (en vez del wrapper `VectorStore` de
LangChain) para controlar con exactitud el esquema del payload y no romper
la compatibilidad con la colección ya existente:

- Vector nombrado "text".
- Texto del fragmento almacenado en el campo "contenido".
- Resto de metadatos como claves planas (sin anidar bajo "metadata").
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.config import settings


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_collection() -> None:
    """Crea la colección si no existe, con el esquema esperado. No la recrea si ya existe."""
    client = get_client()
    if client.collection_exists(settings.qdrant_collection):
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config={
            settings.qdrant_vector_name: qmodels.VectorParams(
                size=settings.embedding_dim,
                distance=qmodels.Distance.COSINE,
            )
        },
    )


@dataclass
class Fragmento:
    id: str
    contenido: str
    score: float
    metadata: dict[str, Any]


def upsert_fragmentos(
    ids: list[str],
    vectores: list[list[float]],
    contenidos: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    """Escribe en lotes de `settings.upsert_batch_size` puntos con payload plano."""
    client = get_client()
    ensure_collection()
    lote = settings.upsert_batch_size
    total = len(ids)
    for inicio in range(0, total, lote):
        fin = min(inicio + lote, total)
        puntos = [
            qmodels.PointStruct(
                id=ids[i],
                vector={settings.qdrant_vector_name: vectores[i]},
                payload={settings.qdrant_content_field: contenidos[i], **metadatas[i]},
            )
            for i in range(inicio, fin)
        ]
        client.upsert(collection_name=settings.qdrant_collection, points=puntos, wait=True)


def buscar(
    vector_consulta: list[float],
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> list[Fragmento]:
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return []
    resultados = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=(settings.qdrant_vector_name, vector_consulta),
        limit=top_k or settings.retrieval_top_k,
        score_threshold=score_threshold if score_threshold is not None else settings.retrieval_score_threshold,
        with_payload=True,
    )
    fragmentos = []
    for punto in resultados:
        payload = dict(punto.payload or {})
        contenido = payload.pop(settings.qdrant_content_field, "")
        fragmentos.append(Fragmento(id=str(punto.id), contenido=contenido, score=punto.score, metadata=payload))
    return fragmentos


def eliminar_por_documento(documento_id: str) -> None:
    """Elimina todos los fragmentos (puntos) de un documento, por su `documento_id` en el payload."""
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="documento_id", match=qmodels.MatchValue(value=documento_id))]
            )
        ),
    )
