"""Página principal: chat documental con streaming, historial persistente y fuentes.

REQ-001, REQ-002, REQ-003, REQ-004, REQ-008, REQ-009.
"""
from __future__ import annotations

import streamlit as st

from src.config import settings
from src.db import conversaciones as conv_repo
from src.db import mensajes as msg_repo
from src.db.database import init_db
from src.rag.chain import fuentes_para_metadata, generar_respuesta_stream, recuperar_contexto, reformular_pregunta
from src.ui.chat_components import render_fuentes, render_mensaje
from src.ui.session import obtener_propietario_id

st.set_page_config(page_title="Asistente documental", page_icon="💬", layout="wide")
init_db()

propietario_id = obtener_propietario_id()

# --- Sidebar: gestión de conversaciones (REQ-002) ---------------------------------
with st.sidebar:
    st.header("Conversaciones")

    if st.button("➕ Nueva conversación", use_container_width=True):
        nueva = conv_repo.crear_conversacion(propietario_id)
        st.session_state["conversacion_id"] = nueva.id
        st.rerun()

    conversaciones = conv_repo.listar_conversaciones(propietario_id)

    if "conversacion_id" not in st.session_state and conversaciones:
        st.session_state["conversacion_id"] = conversaciones[0].id

    for conv in conversaciones:
        seleccionada = st.session_state.get("conversacion_id") == conv.id
        col_sel, col_ren, col_del = st.columns([6, 1, 1])
        with col_sel:
            if st.button(("🟢 " if seleccionada else "") + conv.titulo, key=f"sel_{conv.id}", use_container_width=True):
                st.session_state["conversacion_id"] = conv.id
                st.rerun()
        with col_ren:
            if st.button("✏️", key=f"ren_{conv.id}", help="Renombrar"):
                st.session_state["renombrando_id"] = conv.id
        with col_del:
            if st.button("🗑️", key=f"del_{conv.id}", help="Eliminar"):
                conv_repo.eliminar_conversacion(conv.id, propietario_id)
                if st.session_state.get("conversacion_id") == conv.id:
                    st.session_state.pop("conversacion_id", None)
                st.rerun()

        if st.session_state.get("renombrando_id") == conv.id:
            nuevo_titulo = st.text_input("Nuevo título", value=conv.titulo, key=f"titulo_{conv.id}")
            colr1, colr2 = st.columns(2)
            if colr1.button("Guardar", key=f"guardar_{conv.id}"):
                conv_repo.renombrar_conversacion(conv.id, propietario_id, nuevo_titulo.strip() or conv.titulo)
                st.session_state.pop("renombrando_id", None)
                st.rerun()
            if colr2.button("Cancelar", key=f"cancelar_{conv.id}"):
                st.session_state.pop("renombrando_id", None)
                st.rerun()

    if not conversaciones:
        st.caption("Aún no tienes conversaciones. Crea una para empezar.")

# --- Área principal: chat ---------------------------------------------------------
st.title("💬 Asistente documental")

conversacion_id = st.session_state.get("conversacion_id")

if conversacion_id:
    for mensaje in msg_repo.listar_mensajes(conversacion_id):
        render_mensaje(mensaje)

pregunta = st.chat_input("Escribe tu pregunta sobre los documentos indexados…")

if pregunta:
    if not conversacion_id:
        titulo = pregunta.strip()[:60] or "Nueva conversación"
        conv = conv_repo.crear_conversacion(propietario_id, titulo=titulo)
        conversacion_id = conv.id
        st.session_state["conversacion_id"] = conversacion_id

    historial_previo = msg_repo.ventana_reciente(conversacion_id, settings.history_window_messages)

    msg_repo.agregar_mensaje(conversacion_id, "user", pregunta)
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        try:
            pregunta_reformulada = reformular_pregunta(pregunta, historial_previo)
            fragmentos = recuperar_contexto(pregunta_reformulada)
            contenido_final = st.write_stream(
                generar_respuesta_stream(pregunta_reformulada, historial_previo, fragmentos)
            )
            fuentes = fuentes_para_metadata(fragmentos)
            if fuentes:
                render_fuentes(fuentes)
            msg_repo.agregar_mensaje(
                conversacion_id,
                "assistant",
                contenido_final,
                estado="completo",
                metadata={
                    "fuentes": fuentes,
                    "modelo": settings.groq_model,
                    "pregunta_reformulada": pregunta_reformulada,
                },
            )
        except Exception as exc:  # REQ-008: informar explícitamente el fallo, no simular éxito
            detalle = f"No se pudo generar la respuesta: {exc}"
            st.error(detalle)
            msg_repo.agregar_mensaje(conversacion_id, "assistant", detalle, estado="error")

    conv_repo.tocar_conversacion(conversacion_id)
    st.rerun()

if not conversacion_id:
    st.info("Crea o selecciona una conversación en la barra lateral, o simplemente escribe tu primera pregunta.")
