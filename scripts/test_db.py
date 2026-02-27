#!/usr/bin/env python3
import pytest
from dotenv import load_dotenv

load_dotenv()

from scripts.database import verificar_conexion, engine
from sqlalchemy import text


def test_conexion_postgresql():
    """Verifica que la conexión a PostgreSQL esté activa."""
    resultado = verificar_conexion()
    assert resultado is True, "❌ No se pudo conectar a PostgreSQL. Revisa las variables de entorno en .env"


def test_conexion_ejecuta_query():
    """Verifica que se puede ejecutar una query básica."""
    with engine.connect() as conn:
        resultado = conn.execute(text("SELECT 1")).scalar()
    assert resultado == 1, "❌ La query de prueba no retornó el valor esperado."


def test_base_de_datos_correcta():
    """Verifica que estamos conectados a la base de datos cats_db."""
    with engine.connect() as conn:
        db_actual = conn.execute(text("SELECT current_database()")).scalar()
    assert db_actual == "gatos_db", f"❌ Base de datos incorrecta: '{db_actual}'. Se esperaba 'gatos_db'."
