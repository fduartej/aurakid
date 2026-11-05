"""Prueba de búsqueda semántica: muestra fragmentos y puntuaciones (REQ-007)."""
from __future__ import annotations

import streamlit as st

from src.config import settings
from src.db.database import init_db
from src.vectorstore.embeddings import embed_consulta
from src.vectorstore.qdrant_client import buscar

st.set_page_config(page_title="Búsqueda semántica", page_icon="🔍", layout="wide")
init_db()

st.title("🔍 Probar búsqueda semántica")
st.caption("Consulta directa a Qdrant, sin paso por el LLM. Útil para depurar la recuperación de contexto.")

consulta = st.text_input("Consulta")
col1, col2 = st.columns(2)
top_k = col1.number_input("Top K", min_value=1, max_value=50, value=settings.retrieval_top_k)
umbral = col2.slider("Umbral mínimo de score", min_value=0.0, max_value=1.0, value=settings.retrieval_score_threshold)

if st.button("Buscar") and consulta.strip():
    with st.spinner("Buscando…"):
        try:
            vector = embed_consulta(consulta)
            resultados = buscar(vector, top_k=int(top_k), score_threshold=float(umbral))
        except Exception as exc:
            st.error(f"Fallo al consultar Qdrant: {exc}")
            resultados = []

    if not resultados:
        st.warning("Sin resultados por encima del umbral: no hay evidencia suficiente para esta consulta.")
    else:
        for i, frag in enumerate(resultados, start=1):
            with st.container(border=True):
                st.markdown(f"**{i}. {frag.metadata.get('nombre_archivo', 'desconocido')}** · score `{frag.score:.4f}`")
                st.write(frag.contenido)
                st.caption(f"documento_id: {frag.metadata.get('documento_id')} · id fragmento: {frag.id}")
