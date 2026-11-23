from __future__ import annotations

from dataclasses import replace

import pytest
from qdrant_client import QdrantClient

from src.config import settings
from src.vectorstore import qdrant_client


@pytest.fixture
def cliente_qdrant(monkeypatch):
    client = QdrantClient(":memory:")
    monkeypatch.setattr(qdrant_client, "get_client", lambda: client)
    yield client
    client.close()


def test_buscar_en_coleccion_inexistente(cliente_qdrant):
    assert qdrant_client.buscar([1.0, 0.0]) == []


def test_buscar_vector_nombrado_con_umbral_y_payload(cliente_qdrant, monkeypatch):
    monkeypatch.setattr(qdrant_client, "settings", replace(settings, embedding_dim=2))
    qdrant_client.upsert_fragmentos(
        ids=["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
        vectores=[[1.0, 0.0], [0.0, 1.0]],
        contenidos=["Coincidente", "No coincidente"],
        metadatas=[{"documento_id": "doc-1"}, {"documento_id": "doc-2"}],
    )

    resultados = qdrant_client.buscar([1.0, 0.0], top_k=2, score_threshold=0.5)

    assert len(resultados) == 1
    assert resultados[0].id == "00000000-0000-0000-0000-000000000001"
    assert resultados[0].contenido == "Coincidente"
    assert resultados[0].score == pytest.approx(1.0)
    assert resultados[0].metadata == {"documento_id": "doc-1"}

    assert len(qdrant_client.buscar([1.0, 0.0], top_k=1, score_threshold=0.0)) == 1
