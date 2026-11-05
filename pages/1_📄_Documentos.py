"""Gestión de documentos: cargar, listar y eliminar (REQ-005, REQ-006, REQ-008, REQ-009)."""
from __future__ import annotations

import streamlit as st

from src.config import settings
from src.db import documentos as documentos_repo
from src.db.database import init_db
from src.ingestion.loaders import TIPOS_SOPORTADOS
from src.ingestion.pipeline import IngestaError, eliminar_documento, ingerir_documento
from src.ui.session import obtener_propietario_id, render_admin_gate

st.set_page_config(page_title="Documentos", page_icon="📄", layout="wide")
init_db()

propietario_id = obtener_propietario_id()

st.title("📄 Gestión de documentos")

if not render_admin_gate():
    st.stop()

st.subheader("Cargar documento")
st.caption(
    f"Tipos soportados: {', '.join(sorted(TIPOS_SOPORTADOS))}. Tamaño máximo: {settings.max_upload_mb} MB. "
    "Se valida que el archivo tenga contenido textual extraíble."
)

archivo = st.file_uploader("Selecciona un archivo", type=sorted(TIPOS_SOPORTADOS))
if archivo is not None and st.button("Indexar documento"):
    with st.spinner(f"Procesando '{archivo.name}'…"):
        try:
            resultado = ingerir_documento(archivo.name, archivo.getvalue(), propietario_id)
            st.success(f"'{archivo.name}' indexado correctamente ({resultado.num_fragmentos} fragmentos).")
        except IngestaError as exc:
            st.error(f"No se pudo indexar '{archivo.name}': {exc}")

st.divider()
st.subheader("Documentos indexados")

documentos = documentos_repo.listar_documentos()
if not documentos:
    st.caption("Todavía no hay documentos indexados.")
else:
    for doc in documentos:
        col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
        with col1:
            st.markdown(f"**{doc.nombre_archivo}**")
            if doc.estado == "error":
                st.caption(f"⚠️ Error: {doc.error_detalle}")
        with col2:
            st.caption(f"Tipo: {doc.tipo} · {doc.tamano_bytes / 1024:.1f} KB")
        with col3:
            estado_emoji = {"listo": "✅", "procesando": "⏳", "error": "❌"}.get(doc.estado, "")
            st.caption(f"{estado_emoji} {doc.estado} · {doc.num_fragmentos} fragmentos")
        with col4:
            if st.button("🗑️", key=f"del_doc_{doc.id}", help="Eliminar documento y sus fragmentos"):
                eliminar_documento(doc.id)
                st.rerun()
