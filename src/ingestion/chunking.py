"""Fragmentación (chunking) de texto para indexar en Qdrant."""
from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings


def fragmentar_texto(texto: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    fragmentos = splitter.split_text(texto)
    return [f.strip() for f in fragmentos if f.strip()]
