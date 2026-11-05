"""Ventana de historial reciente para reformulación y generación de respuestas."""
from __future__ import annotations

from src.db.mensajes import Mensaje


def formatear_historial(mensajes: list[Mensaje]) -> str:
    """Convierte mensajes recientes en texto plano 'rol: contenido' para los prompts."""
    lineas = []
    for m in mensajes:
        etiqueta = "Usuario" if m.rol == "user" else "Asistente"
        lineas.append(f"{etiqueta}: {m.contenido}")
    return "\n".join(lineas)
