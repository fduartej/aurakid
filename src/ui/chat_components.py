"""Componentes de render para el chat (REQ-001, REQ-004, REQ-008)."""
from __future__ import annotations

import streamlit as st

from src.db.mensajes import Mensaje


def render_mensaje(mensaje: Mensaje) -> None:
    with st.chat_message(mensaje.rol):
        if mensaje.estado == "error":
            st.error(mensaje.contenido)
        else:
            st.markdown(mensaje.contenido)
            if mensaje.estado == "incompleto":
                st.caption("⚠️ Respuesta incompleta (se interrumpió la generación).")
        fuentes = mensaje.metadata.get("fuentes") if mensaje.metadata else None
        if fuentes:
            render_fuentes(fuentes)


def render_fuentes(fuentes: list[dict]) -> None:
    with st.expander(f"Fuentes ({len(fuentes)})"):
        for i, f in enumerate(fuentes, start=1):
            st.markdown(f"**{i}. {f.get('nombre_archivo', 'desconocido')}** · score `{f.get('score')}`")
            st.caption(f.get("fragmento", ""))
