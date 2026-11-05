"""Conexión SQLite y creación de esquema.

SQLite es la fuente persistente de verdad para conversaciones y mensajes.
`st.session_state` solo debe usarse para estado efímero de interfaz.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from src.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversaciones (
    id              TEXT PRIMARY KEY,
    titulo          TEXT NOT NULL,
    propietario_id  TEXT NOT NULL,
    creada_en       TEXT NOT NULL,
    actualizada_en  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mensajes (
    id              TEXT PRIMARY KEY,
    conversacion_id TEXT NOT NULL REFERENCES conversaciones(id) ON DELETE CASCADE,
    orden           INTEGER NOT NULL,
    rol             TEXT NOT NULL CHECK (rol IN ('user', 'assistant')),
    contenido       TEXT NOT NULL,
    estado          TEXT NOT NULL DEFAULT 'completo' CHECK (estado IN ('completo', 'error', 'incompleto')),
    creado_en       TEXT NOT NULL,
    metadata_json   TEXT
);

CREATE TABLE IF NOT EXISTS documentos (
    id              TEXT PRIMARY KEY,
    nombre_archivo  TEXT NOT NULL,
    tipo            TEXT NOT NULL,
    tamano_bytes    INTEGER NOT NULL,
    propietario_id  TEXT,
    estado          TEXT NOT NULL DEFAULT 'procesando' CHECK (estado IN ('procesando', 'listo', 'error')),
    num_fragmentos  INTEGER NOT NULL DEFAULT 0,
    error_detalle   TEXT,
    creado_en       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mensajes_conversacion ON mensajes(conversacion_id, orden);
CREATE INDEX IF NOT EXISTS idx_conversaciones_propietario ON conversaciones(propietario_id);
"""

_local = threading.local()


def _connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Devuelve una conexión SQLite reutilizable por hilo (modelo de ejecución de Streamlit)."""
    path = db_path or settings.sqlite_path
    cached = getattr(_local, "conn", None)
    if cached is None or getattr(_local, "path", None) != path:
        cached = _connect(path)
        cached.executescript(_SCHEMA)
        cached.commit()
        _local.conn = cached
        _local.path = path
    return cached


@contextmanager
def transaction(db_path: str | None = None):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db(db_path: str | None = None) -> None:
    """Fuerza la creación del esquema (útil en tests y arranque de la app)."""
    get_connection(db_path)
