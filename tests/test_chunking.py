from __future__ import annotations

from src.ingestion.chunking import fragmentar_texto


def test_texto_corto_produce_un_solo_fragmento():
    texto = "Este es un texto corto de prueba."
    fragmentos = fragmentar_texto(texto)
    assert len(fragmentos) == 1
    assert fragmentos[0] == texto


def test_texto_largo_se_divide_en_varios_fragmentos():
    parrafo = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50
    fragmentos = fragmentar_texto(parrafo)
    assert len(fragmentos) > 1
    for f in fragmentos:
        assert len(f) > 0


def test_texto_vacio_no_produce_fragmentos():
    assert fragmentar_texto("   ") == []
