"""Carga y validación de documentos (REQ-005): PDF, TXT y Markdown.

Valida tamaño máximo y que el archivo tenga contenido extraíble (por ejemplo,
rechaza un PDF escaneado sin texto, que produciría una colección "vacía" de
forma silenciosa).
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

from src.config import settings

TIPOS_SOPORTADOS = {"pdf", "txt", "md"}
MIN_CARACTERES_EXTRAIBLES = 20


class ValidacionDocumentoError(Exception):
    """Error de validación de un documento cargado por el usuario (REQ-008)."""


@dataclass
class DocumentoCargado:
    nombre_archivo: str
    tipo: str
    tamano_bytes: int
    texto: str


def _tipo_desde_nombre(nombre_archivo: str) -> str:
    extension = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else ""
    if extension not in TIPOS_SOPORTADOS:
        raise ValidacionDocumentoError(
            f"Tipo de archivo no soportado: '.{extension}'. Tipos permitidos: {', '.join(sorted(TIPOS_SOPORTADOS))}."
        )
    return extension


def _extraer_pdf(datos: bytes) -> str:
    try:
        lector = PdfReader(BytesIO(datos))
    except Exception as exc:  # archivo corrupto o no es un PDF válido
        raise ValidacionDocumentoError(f"No se pudo leer el PDF: {exc}") from exc
    paginas = [pagina.extract_text() or "" for pagina in lector.pages]
    return "\n\n".join(paginas).strip()


def _extraer_texto_plano(datos: bytes) -> str:
    try:
        return datos.decode("utf-8")
    except UnicodeDecodeError:
        return datos.decode("latin-1", errors="replace")


def cargar_documento(nombre_archivo: str, datos: bytes) -> DocumentoCargado:
    tipo = _tipo_desde_nombre(nombre_archivo)

    tamano_bytes = len(datos)
    limite_bytes = settings.max_upload_mb * 1024 * 1024
    if tamano_bytes > limite_bytes:
        raise ValidacionDocumentoError(
            f"El archivo pesa {tamano_bytes / (1024 * 1024):.1f} MB, supera el límite de {settings.max_upload_mb} MB."
        )
    if tamano_bytes == 0:
        raise ValidacionDocumentoError("El archivo está vacío.")

    texto = _extraer_pdf(datos) if tipo == "pdf" else _extraer_texto_plano(datos)

    if len(texto.strip()) < MIN_CARACTERES_EXTRAIBLES:
        raise ValidacionDocumentoError(
            "No se pudo extraer contenido textual suficiente del archivo "
            "(¿es un PDF escaneado sin texto, o está vacío?)."
        )

    return DocumentoCargado(nombre_archivo=nombre_archivo, tipo=tipo, tamano_bytes=tamano_bytes, texto=texto)
