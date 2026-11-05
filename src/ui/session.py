"""Identidad de propietario y protección de administración (REQ-009).

`st.session_state` se reinicia con cada recarga de script, pero persiste
mientras la pestaña del navegador siga abierta. Para sobrevivir a un cierre
de navegador usamos un identificador estable guardado en los parámetros de
la URL (`st.query_params`), que el usuario puede marcar como favorito o que
persiste si no borra la URL. Esto es una solución ligera: para una app con
cuentas reales de usuario, sustituir por autenticación propiamente dicha.
"""
from __future__ import annotations

import uuid

import streamlit as st

from src.config import settings

_PARAM_OWNER = "u"


def obtener_propietario_id() -> str:
    params = st.query_params
    owner_id = params.get(_PARAM_OWNER)
    if not owner_id:
        owner_id = uuid.uuid4().hex[:12]
        st.query_params[_PARAM_OWNER] = owner_id
    return owner_id


def es_admin() -> bool:
    return bool(st.session_state.get("es_admin", False))


def render_admin_gate() -> bool:
    """Muestra un formulario de contraseña si ADMIN_PASSWORD está configurado.

    Devuelve True si el acceso administrativo está desbloqueado (o si no hay
    contraseña configurada, en cuyo caso no se restringe).
    """
    if not settings.admin_password:
        return True
    if es_admin():
        return True

    st.info("Esta sección requiere contraseña de administración.")
    clave = st.text_input("Contraseña de administración", type="password")
    if st.button("Acceder"):
        if clave == settings.admin_password:
            st.session_state["es_admin"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    return False
