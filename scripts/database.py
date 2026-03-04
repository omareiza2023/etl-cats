#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from scripts.models import Base, Raza, Imagen, MetricasETL

logger = logging.getLogger(__name__)


# ── Construcción de URL ──────────────────────────────────────────────────────

def _build_database_url() -> str:
    """Lee DATABASE_URL desde Streamlit Secrets o desde .env local."""

    # 1. Intentar desde Streamlit Cloud secrets
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            logger.info("🔐 DATABASE_URL leída desde Streamlit Secrets.")
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    # 2. Fallback a variable de entorno local (.env)
    url = os.getenv('DATABASE_URL')
    if url:
        return url

    # 3. Construir desde variables individuales
    host     = os.getenv('DB_HOST',     'localhost')
    port     = os.getenv('DB_PORT',     '5432')
    name     = os.getenv('DB_NAME',     'gatos_db')
    user     = os.getenv('DB_USER',     'postgres')
    password = os.getenv('DB_PASS',     '')
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── Funciones de utilidad ────────────────────────────────────────────────────

def crear_tablas():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas / verificadas correctamente.")
    except Exception as e:
        logger.error(f"❌ Error al crear tablas: {e}")
        raise


def verificar_conexion() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a PostgreSQL exitosa.")
        return True
    except Exception as e:
        logger.error(f"❌ No se pudo conectar a PostgreSQL: {e}")
        return False


# ── Funciones UPSERT ─────────────────────────────────────────────────────────

def upsert_raza(session, datos_raza: dict):
    try:
        stmt = pg_insert(Raza).values(**datos_raza)
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                'nombre_raza':          stmt.excluded.nombre_raza,
                'origen':               stmt.excluded.origen,
                'temperamento':         stmt.excluded.temperamento,
                'vida_promedio':        stmt.excluded.vida_promedio,
                'peso_metrico':         stmt.excluded.peso_metrico,
                'wikipedia_url':        stmt.excluded.wikipedia_url,
                'adaptabilidad':        stmt.excluded.adaptabilidad,
                'nivel_energia':        stmt.excluded.nivel_energia,
                'inteligencia':         stmt.excluded.inteligencia,
                'social_humanos':       stmt.excluded.social_humanos,
                'vida_anos':            stmt.excluded.vida_anos,
                'peso_kg':              stmt.excluded.peso_kg,
                'fecha_actualizacion':  stmt.excluded.fecha_extraccion,
            }
        )
        session.execute(stmt)
        logger.debug(f"  🐱 Raza procesada: {datos_raza.get('nombre_raza')}")
    except Exception as e:
        logger.error(f"❌ Error en upsert_raza ({datos_raza.get('id')}): {e}")
        raise


def upsert_imagen(session, datos_imagen: dict):
    try:
        stmt = pg_insert(Imagen).values(**datos_imagen)
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                'url':   stmt.excluded.url,
                'ancho': stmt.excluded.ancho,
                'alto':  stmt.excluded.alto,
            }
        )
        session.execute(stmt)
        logger.debug(f"  🖼️  Imagen procesada: {datos_imagen.get('id')}")
    except Exception as e:
        logger.error(f"❌ Error en upsert_imagen ({datos_imagen.get('id')}): {e}")
        raise


def guardar_datos(lista_datos: list):
    if not lista_datos:
        logger.warning("⚠️ No hay datos para guardar.")
        return

    session = SessionLocal()
    try:
        razas_procesadas    = 0
        imagenes_procesadas = 0

        for dato in lista_datos:
            datos_raza = {
                'id':               dato.get('raza_id'),
                'nombre_raza':      dato.get('nombre_raza'),
                'origen':           dato.get('origen_raza'),
                'temperamento':     dato.get('temperamento'),
                'vida_promedio':    dato.get('vida_promedio'),
                'peso_metrico':     dato.get('peso_metrico'),
                'wikipedia_url':    dato.get('wikipedia_url'),
                'adaptabilidad':    dato.get('adaptabilidad'),
                'nivel_energia':    dato.get('nivel_energia'),
                'inteligencia':     dato.get('inteligencia'),
                'social_humanos':   dato.get('social_humanos'),
                'vida_anos':        dato.get('vida_anos'),
                'peso_kg':          dato.get('peso_kg'),
                'fecha_extraccion': dato.get('fecha_extraccion'),
            }

            datos_imagen = {
                'id':               dato.get('imagen_id'),
                'raza_id':          dato.get('raza_id'),
                'url':              dato.get('url'),
                'ancho':            dato.get('ancho'),
                'alto':             dato.get('alto'),
                'fecha_extraccion': dato.get('fecha_extraccion'),
            }

            upsert_raza(session, datos_raza)
            razas_procesadas += 1

            upsert_imagen(session, datos_imagen)
            imagenes_procesadas += 1

        session.commit()
        logger.info(f"✅ UPSERT completado: {razas_procesadas} razas, {imagenes_procesadas} imágenes.")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error en guardar_datos, se hizo rollback: {e}")
        raise
    finally:
        session.close()


# ── Ejecución directa ────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if verificar_conexion():
        crear_tablas()
        print("✅ Base de datos lista.")
    else:
        print("❌ Revisa las variables de entorno de conexión.")