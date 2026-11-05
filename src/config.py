"""Configuración centralizada de la aplicación, leída desde variables de entorno.

Mantener toda la configuración sensible al esquema de Qdrant (nombre de colección,
nombre del vector, modelo de embeddings y dimensión) en un único lugar evita que
una parte de la app reindexe con una preparación de texto distinta a la usada
por otra, lo que rompería la compatibilidad de los embeddings almacenados.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


@dataclass(frozen=True)
class Settings:
    # Qdrant
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    qdrant_api_key: str | None = field(default_factory=lambda: os.getenv("QDRANT_API_KEY") or None)
    qdrant_collection: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "documentos"))
    # El nombre del vector y el campo de contenido deben coincidir exactamente con
    # los usados al crear/poblar la colección existente.
    qdrant_vector_name: str = "text"
    qdrant_content_field: str = "contenido"

    # Embeddings
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small"))
    embedding_dim: int = field(default_factory=lambda: _env_int("EMBEDDING_DIM", 384))

    # LLM (Groq)
    groq_api_key: str | None = field(default_factory=lambda: os.getenv("GROQ_API_KEY") or None)
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))

    # SQLite
    sqlite_path: str = field(default_factory=lambda: os.getenv("SQLITE_PATH", "data/chat_history.db"))

    # Administración
    admin_password: str | None = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD") or None)

    # Ingesta
    max_upload_mb: int = field(default_factory=lambda: _env_int("MAX_UPLOAD_MB", 20))
    chunk_size: int = field(default_factory=lambda: _env_int("CHUNK_SIZE", 800))
    chunk_overlap: int = field(default_factory=lambda: _env_int("CHUNK_OVERLAP", 120))
    upsert_batch_size: int = field(default_factory=lambda: _env_int("UPSERT_BATCH_SIZE", 64))

    # Recuperación / RAG
    retrieval_top_k: int = field(default_factory=lambda: _env_int("RETRIEVAL_TOP_K", 5))
    retrieval_score_threshold: float = field(default_factory=lambda: _env_float("RETRIEVAL_SCORE_THRESHOLD", 0.25))
    history_window_messages: int = field(default_factory=lambda: _env_int("HISTORY_WINDOW_MESSAGES", 6))


settings = Settings()
