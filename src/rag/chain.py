"""Cadena RAG: reformulación con historial, recuperación en Qdrant y generación
en streaming con Groq vía LangChain (REQ-001, REQ-004, REQ-008).
"""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.config import settings
from src.db.mensajes import Mensaje
from src.rag.history import formatear_historial
from src.vectorstore.embeddings import embed_consulta
from src.vectorstore.qdrant_client import Fragmento, buscar

MENSAJE_SIN_EVIDENCIA = (
    "No encontré evidencia suficiente en los documentos indexados para responder esta pregunta. "
    "Prueba reformularla o carga un documento que contenga esta información."
)

_PROMPT_REFORMULACION = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Reescribe la última pregunta del usuario como una pregunta autocontenida, "
            "usando el historial solo si la pregunta depende de él (p. ej. '¿y cuánto cuesta?'). "
            "Responde únicamente con la pregunta reescrita, sin explicaciones.",
        ),
        ("human", "Historial:\n{historial}\n\nPregunta actual: {pregunta}"),
    ]
)

_PROMPT_RESPUESTA = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente que responde preguntas basándote EXCLUSIVAMENTE en el contexto "
            "proporcionado, extraído de documentos indexados. Si el contexto no contiene la "
            "respuesta, dilo explícitamente en vez de inventar información. Cita de forma breve "
            "de qué fragmento proviene cada afirmación cuando sea relevante.",
        ),
        (
            "human",
            "Contexto recuperado:\n{contexto}\n\nHistorial reciente:\n{historial}\n\nPregunta: {pregunta}",
        ),
    ]
)


@lru_cache(maxsize=1)
def get_llm(streaming: bool = True) -> ChatGroq:
    return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, streaming=streaming, temperature=0.1)


def reformular_pregunta(pregunta: str, historial: list[Mensaje]) -> str:
    """Si no hay historial, devuelve la pregunta tal cual (evita una llamada LLM innecesaria)."""
    if not historial:
        return pregunta
    llm = get_llm(streaming=False)
    mensaje = _PROMPT_REFORMULACION.format_messages(historial=formatear_historial(historial), pregunta=pregunta)
    respuesta = llm.invoke(mensaje)
    texto = (respuesta.content or "").strip()
    return texto or pregunta


def recuperar_contexto(pregunta: str) -> list[Fragmento]:
    vector = embed_consulta(pregunta)
    return buscar(vector)


def _formatear_contexto(fragmentos: list[Fragmento]) -> str:
    bloques = []
    for i, frag in enumerate(fragmentos, start=1):
        nombre = frag.metadata.get("nombre_archivo", "desconocido")
        bloques.append(f"[Fuente {i} - {nombre}]\n{frag.contenido}")
    return "\n\n".join(bloques)


def generar_respuesta_stream(pregunta: str, historial: list[Mensaje], fragmentos: list[Fragmento]) -> Iterator[str]:
    """Genera la respuesta en streaming. Si no hay fragmentos (sin evidencia), no llama al LLM."""
    if not fragmentos:
        yield MENSAJE_SIN_EVIDENCIA
        return

    llm = get_llm(streaming=True)
    mensajes = _PROMPT_RESPUESTA.format_messages(
        contexto=_formatear_contexto(fragmentos),
        historial=formatear_historial(historial),
        pregunta=pregunta,
    )
    for trozo in llm.stream(mensajes):
        if trozo.content:
            yield trozo.content


def fuentes_para_metadata(fragmentos: list[Fragmento]) -> list[dict]:
    return [
        {
            "fragmento_id": f.id,
            "nombre_archivo": f.metadata.get("nombre_archivo"),
            "documento_id": f.metadata.get("documento_id"),
            "score": round(f.score, 4),
            "fragmento": f.contenido[:300],
        }
        for f in fragmentos
    ]
