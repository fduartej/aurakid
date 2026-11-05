"""CRUD de metadatos de documentos indexados (REQ-005, REQ-006, REQ-008)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from src.db.database import get_connection

Estado = Literal["procesando", "listo", "error"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Documento:
    id: str
    nombre_archivo: str
    tipo: str
    tamano_bytes: int
    propietario_id: str | None
    estado: Estado
    num_fragmentos: int
    error_detalle: str | None
    creado_en: str


def crear_documento(nombre_archivo: str, tipo: str, tamano_bytes: int, propietario_id: str | None) -> Documento:
    doc_id = str(uuid.uuid4())
    ahora = _now()
    conn = get_connection()
    conn.execute(
        "INSERT INTO documentos (id, nombre_archivo, tipo, tamano_bytes, propietario_id, estado, "
        "num_fragmentos, error_detalle, creado_en) VALUES (?, ?, ?, ?, ?, 'procesando', 0, NULL, ?)",
        (doc_id, nombre_archivo, tipo, tamano_bytes, propietario_id, ahora),
    )
    conn.commit()
    return Documento(doc_id, nombre_archivo, tipo, tamano_bytes, propietario_id, "procesando", 0, None, ahora)


def marcar_listo(documento_id: str, num_fragmentos: int) -> None:
    """Solo se marca 'listo' tras confirmar la escritura en Qdrant (REQ-008: no mostrar como cargado si falla)."""
    conn = get_connection()
    conn.execute(
        "UPDATE documentos SET estado = 'listo', num_fragmentos = ?, error_detalle = NULL WHERE id = ?",
        (num_fragmentos, documento_id),
    )
    conn.commit()


def marcar_error(documento_id: str, detalle: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE documentos SET estado = 'error', error_detalle = ? WHERE id = ?",
        (detalle, documento_id),
    )
    conn.commit()


def listar_documentos() -> list[Documento]:
    conn = get_connection()
    filas = conn.execute("SELECT * FROM documentos ORDER BY creado_en DESC").fetchall()
    return [Documento(**dict(f)) for f in filas]


def obtener_documento(documento_id: str) -> Documento | None:
    conn = get_connection()
    fila = conn.execute("SELECT * FROM documentos WHERE id = ?", (documento_id,)).fetchone()
    return Documento(**dict(fila)) if fila else None


def eliminar_documento(documento_id: str) -> bool:
    conn = get_connection()
    cur = conn.execute("DELETE FROM documentos WHERE id = ?", (documento_id,))
    conn.commit()
    return cur.rowcount > 0
