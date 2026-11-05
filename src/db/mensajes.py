"""CRUD de mensajes (REQ-001, REQ-003, REQ-004, REQ-008)."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from src.db.database import get_connection

Rol = Literal["user", "assistant"]
Estado = Literal["completo", "error", "incompleto"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Mensaje:
    id: str
    conversacion_id: str
    orden: int
    rol: Rol
    contenido: str
    estado: Estado
    creado_en: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _siguiente_orden(conversacion_id: str) -> int:
    conn = get_connection()
    fila = conn.execute(
        "SELECT COALESCE(MAX(orden), -1) + 1 AS siguiente FROM mensajes WHERE conversacion_id = ?",
        (conversacion_id,),
    ).fetchone()
    return int(fila["siguiente"])


def agregar_mensaje(
    conversacion_id: str,
    rol: Rol,
    contenido: str,
    estado: Estado = "completo",
    metadata: dict[str, Any] | None = None,
) -> Mensaje:
    msg_id = str(uuid.uuid4())
    orden = _siguiente_orden(conversacion_id)
    ahora = _now()
    metadata = metadata or {}
    conn = get_connection()
    conn.execute(
        "INSERT INTO mensajes (id, conversacion_id, orden, rol, contenido, estado, creado_en, metadata_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (msg_id, conversacion_id, orden, rol, contenido, estado, ahora, json.dumps(metadata, ensure_ascii=False)),
    )
    conn.commit()
    return Mensaje(msg_id, conversacion_id, orden, rol, contenido, estado, ahora, metadata)


def actualizar_mensaje(
    mensaje_id: str,
    contenido: str | None = None,
    estado: Estado | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Permite cerrar un mensaje de asistente tras terminar el streaming (contenido final, fuentes, estado)."""
    conn = get_connection()
    campos: list[str] = []
    valores: list[Any] = []
    if contenido is not None:
        campos.append("contenido = ?")
        valores.append(contenido)
    if estado is not None:
        campos.append("estado = ?")
        valores.append(estado)
    if metadata is not None:
        campos.append("metadata_json = ?")
        valores.append(json.dumps(metadata, ensure_ascii=False))
    if not campos:
        return
    valores.append(mensaje_id)
    conn.execute(f"UPDATE mensajes SET {', '.join(campos)} WHERE id = ?", valores)
    conn.commit()


def listar_mensajes(conversacion_id: str) -> list[Mensaje]:
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM mensajes WHERE conversacion_id = ? ORDER BY orden ASC",
        (conversacion_id,),
    ).fetchall()
    mensajes = []
    for f in filas:
        datos = dict(f)
        metadata_json = datos.pop("metadata_json") or "{}"
        datos["metadata"] = json.loads(metadata_json)
        mensajes.append(Mensaje(**datos))
    return mensajes


def ventana_reciente(conversacion_id: str, n_mensajes: int) -> list[Mensaje]:
    """Recupera solo la ventana reciente de mensajes para no enviar todo el historial al modelo."""
    todos = listar_mensajes(conversacion_id)
    return todos[-n_mensajes:] if n_mensajes > 0 else todos
