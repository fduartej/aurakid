"""CRUD de conversaciones (REQ-002, REQ-003, REQ-009)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from src.db.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Conversacion:
    id: str
    titulo: str
    propietario_id: str
    creada_en: str
    actualizada_en: str


def crear_conversacion(propietario_id: str, titulo: str = "Nueva conversación") -> Conversacion:
    conv_id = str(uuid.uuid4())
    ahora = _now()
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversaciones (id, titulo, propietario_id, creada_en, actualizada_en) "
        "VALUES (?, ?, ?, ?, ?)",
        (conv_id, titulo, propietario_id, ahora, ahora),
    )
    conn.commit()
    return Conversacion(conv_id, titulo, propietario_id, ahora, ahora)


def listar_conversaciones(propietario_id: str) -> list[Conversacion]:
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM conversaciones WHERE propietario_id = ? ORDER BY actualizada_en DESC",
        (propietario_id,),
    ).fetchall()
    return [Conversacion(**dict(f)) for f in filas]


def obtener_conversacion(conversacion_id: str, propietario_id: str) -> Conversacion | None:
    conn = get_connection()
    fila = conn.execute(
        "SELECT * FROM conversaciones WHERE id = ? AND propietario_id = ?",
        (conversacion_id, propietario_id),
    ).fetchone()
    return Conversacion(**dict(fila)) if fila else None


def renombrar_conversacion(conversacion_id: str, propietario_id: str, nuevo_titulo: str) -> bool:
    conn = get_connection()
    cur = conn.execute(
        "UPDATE conversaciones SET titulo = ?, actualizada_en = ? WHERE id = ? AND propietario_id = ?",
        (nuevo_titulo, _now(), conversacion_id, propietario_id),
    )
    conn.commit()
    return cur.rowcount > 0


def eliminar_conversacion(conversacion_id: str, propietario_id: str) -> bool:
    conn = get_connection()
    cur = conn.execute(
        "DELETE FROM conversaciones WHERE id = ? AND propietario_id = ?",
        (conversacion_id, propietario_id),
    )
    conn.commit()
    return cur.rowcount > 0


def tocar_conversacion(conversacion_id: str) -> None:
    """Actualiza `actualizada_en` para que la conversación suba al tope de la lista."""
    conn = get_connection()
    conn.execute(
        "UPDATE conversaciones SET actualizada_en = ? WHERE id = ?",
        (_now(), conversacion_id),
    )
    conn.commit()
