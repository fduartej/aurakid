from __future__ import annotations

from io import BytesIO

import pytest
from pypdf import PdfWriter

from src.config import settings
from src.ingestion.loaders import ValidacionDocumentoError, cargar_documento


def _pdf_sin_texto() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_txt_valido_se_carga_correctamente():
    contenido = "Este documento tiene suficiente contenido textual para pasar la validación." * 2
    doc = cargar_documento("notas.txt", contenido.encode("utf-8"))
    assert doc.tipo == "txt"
    assert doc.texto.strip() == contenido.strip()


def test_md_valido_se_carga_correctamente():
    contenido = "# Título\n\nEste es un documento markdown con contenido suficiente para indexar."
    doc = cargar_documento("guia.md", contenido.encode("utf-8"))
    assert doc.tipo == "md"


def test_extension_no_soportada_lanza_error():
    with pytest.raises(ValidacionDocumentoError, match="no soportado"):
        cargar_documento("datos.csv", b"a,b,c\n1,2,3")


def test_archivo_vacio_lanza_error():
    with pytest.raises(ValidacionDocumentoError, match="vacío"):
        cargar_documento("vacio.txt", b"")


def test_archivo_demasiado_grande_lanza_error():
    original = settings.max_upload_mb
    try:
        object.__setattr__(settings, "max_upload_mb", 0)
        with pytest.raises(ValidacionDocumentoError, match="supera el límite"):
            cargar_documento("grande.txt", b"contenido suficiente para pasar el resto de validaciones" * 5)
    finally:
        object.__setattr__(settings, "max_upload_mb", original)


def test_pdf_sin_texto_extraible_lanza_error():
    with pytest.raises(ValidacionDocumentoError, match="contenido textual"):
        cargar_documento("escaneado.pdf", _pdf_sin_texto())
