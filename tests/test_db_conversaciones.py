from __future__ import annotations

from src.db import conversaciones as conv_repo
from src.db import mensajes as msg_repo


def test_crear_y_listar_conversacion():
    conv = conv_repo.crear_conversacion("owner-1", "Mi charla")
    listadas = conv_repo.listar_conversaciones("owner-1")
    assert len(listadas) == 1
    assert listadas[0].id == conv.id
    assert listadas[0].titulo == "Mi charla"


def test_conversaciones_no_mezclan_propietarios():
    conv_repo.crear_conversacion("owner-1", "A")
    conv_repo.crear_conversacion("owner-2", "B")
    assert len(conv_repo.listar_conversaciones("owner-1")) == 1
    assert len(conv_repo.listar_conversaciones("owner-2")) == 1


def test_renombrar_y_eliminar_conversacion():
    conv = conv_repo.crear_conversacion("owner-1", "Original")
    assert conv_repo.renombrar_conversacion(conv.id, "owner-1", "Nuevo título")
    actualizada = conv_repo.obtener_conversacion(conv.id, "owner-1")
    assert actualizada.titulo == "Nuevo título"

    assert conv_repo.eliminar_conversacion(conv.id, "owner-1")
    assert conv_repo.obtener_conversacion(conv.id, "owner-1") is None


def test_eliminar_conversacion_de_otro_propietario_falla():
    conv = conv_repo.crear_conversacion("owner-1", "Privada")
    assert conv_repo.eliminar_conversacion(conv.id, "owner-2") is False
    assert conv_repo.obtener_conversacion(conv.id, "owner-1") is not None


def test_mensajes_persisten_y_mantienen_orden():
    conv = conv_repo.crear_conversacion("owner-1")
    msg_repo.agregar_mensaje(conv.id, "user", "Hola")
    msg_repo.agregar_mensaje(conv.id, "assistant", "¿En qué te ayudo?", metadata={"fuentes": []})

    mensajes = msg_repo.listar_mensajes(conv.id)
    assert [m.rol for m in mensajes] == ["user", "assistant"]
    assert [m.orden for m in mensajes] == [0, 1]
    assert mensajes[1].metadata == {"fuentes": []}


def test_ventana_reciente_limita_cantidad():
    conv = conv_repo.crear_conversacion("owner-1")
    for i in range(10):
        msg_repo.agregar_mensaje(conv.id, "user", f"mensaje {i}")

    ventana = msg_repo.ventana_reciente(conv.id, 4)
    assert len(ventana) == 4
    assert ventana[-1].contenido == "mensaje 9"
