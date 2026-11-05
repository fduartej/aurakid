"""Orquestación de ingesta de un documento: validar, fragmentar, embeber e indexar.

Si cualquier paso falla a mitad de camino, se eliminan los fragmentos ya
escritos en Qdrant para el documento y se marca el documento como 'error' en
SQLite, de forma que nunca quede en un estado "a medias" mostrado como listo
(REQ-008).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.db import documentos as documentos_repo
from src.ingestion.chunking import fragmentar_texto
from src.ingestion.loaders import ValidacionDocumentoError, cargar_documento
from src.vectorstore import qdrant_client
from src.vectorstore.embeddings import embed_documentos


@dataclass
class ResultadoIngesta:
    documento_id: str
    num_fragmentos: int


class IngestaError(Exception):
    """Error durante la ingesta (validación o fallo del servicio de vectores)."""


def ingerir_documento(nombre_archivo: str, datos: bytes, propietario_id: str | None) -> ResultadoIngesta:
    # 1. Validar (puede lanzar ValidacionDocumentoError antes de tocar la base de datos).
    try:
        cargado = cargar_documento(nombre_archivo, datos)
    except ValidacionDocumentoError as exc:
        raise IngestaError(str(exc)) from exc

    documento = documentos_repo.crear_documento(
        nombre_archivo=cargado.nombre_archivo,
        tipo=cargado.tipo,
        tamano_bytes=cargado.tamano_bytes,
        propietario_id=propietario_id,
    )

    try:
        fragmentos = fragmentar_texto(cargado.texto)
        if not fragmentos:
            raise IngestaError("La fragmentación no produjo ningún fragmento indexable.")

        vectores = embed_documentos(fragmentos)
        ids = [str(uuid.uuid4()) for _ in fragmentos]
        metadatas = [
            {
                "documento_id": documento.id,
                "nombre_archivo": documento.nombre_archivo,
                "tipo": documento.tipo,
                "fragmento_indice": i,
                "propietario_id": propietario_id,
            }
            for i in range(len(fragmentos))
        ]

        qdrant_client.upsert_fragmentos(ids=ids, vectores=vectores, contenidos=fragmentos, metadatas=metadatas)
    except Exception as exc:
        # Limpieza defensiva: no dejar fragmentos huérfanos de un documento fallido.
        try:
            qdrant_client.eliminar_por_documento(documento.id)
        finally:
            documentos_repo.marcar_error(documento.id, str(exc))
        raise IngestaError(f"Fallo al indexar '{nombre_archivo}': {exc}") from exc

    documentos_repo.marcar_listo(documento.id, num_fragmentos=len(fragmentos))
    return ResultadoIngesta(documento_id=documento.id, num_fragmentos=len(fragmentos))


def eliminar_documento(documento_id: str) -> None:
    """Elimina el documento y todos sus fragmentos en Qdrant (REQ-006)."""
    qdrant_client.eliminar_por_documento(documento_id)
    documentos_repo.eliminar_documento(documento_id)
