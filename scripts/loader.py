#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal, test_connection, create_all_tables, engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from scripts.models import Raza, Imagen

# ── Logging ───────────────────────────────────────────────────
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

JSON_PATH = os.getenv('CATS_JSON_PATH', 'data/cats_raw.json')


# ── Helpers ───────────────────────────────────────────────────

def _promedio_rango(valor: str):
    """Convierte '14 - 15' → 14.5"""
    try:
        partes = str(valor).split('-')
        return sum(float(p.strip()) for p in partes) / len(partes)
    except Exception:
        return None


def _parsear_fecha(valor):
    """Convierte string ISO a datetime."""
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.fromisoformat(str(valor))
    except Exception:
        return datetime.now()


# ── Carga del JSON ────────────────────────────────────────────

def cargar_json(path: str) -> list:
    """Lee el archivo JSON y retorna la lista de registros."""
    if not os.path.exists(path):
        logger.error(f"❌ Archivo no encontrado: {path}")
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        logger.info(f"📂 {len(datos)} registros leídos desde {path}")
        return datos
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al parsear JSON: {e}")
        return []


# ── Transformación ────────────────────────────────────────────

def preparar_registro(dato: dict) -> dict | None:
    """Transforma un registro del JSON al formato de la BD."""
    try:
        raza_id   = dato.get('raza_id') or dato.get('id')
        imagen_id = dato.get('imagen_id') or dato.get('id')

        if not raza_id or not imagen_id:
            logger.warning(f"⚠️ Registro sin id válido, se omite.")
            return None

        return {
            'raza_id':          raza_id,
            'imagen_id':        imagen_id,
            'nombre_raza':      dato.get('nombre_raza', 'Desconocida'),
            'origen_raza':      dato.get('origen_raza') or dato.get('origen', 'N/A'),
            'temperamento':     dato.get('temperamento', 'N/A'),
            'vida_promedio':    dato.get('vida_promedio', 'N/A'),
            'peso_metrico':     dato.get('peso_metrico', 'N/A'),
            'wikipedia_url':    dato.get('wikipedia_url', 'N/A'),
            'adaptabilidad':    dato.get('adaptabilidad'),
            'nivel_energia':    dato.get('nivel_energia'),
            'inteligencia':     dato.get('inteligencia'),
            'social_humanos':   dato.get('social_humanos'),
            'vida_anos':        _promedio_rango(dato.get('vida_promedio')),
            'peso_kg':          _promedio_rango(dato.get('peso_metrico')),
            'url':              dato.get('url'),
            'ancho':            dato.get('ancho'),
            'alto':             dato.get('alto'),
            'fecha_extraccion': _parsear_fecha(dato.get('fecha_extraccion')),
        }
    except Exception as e:
        logger.error(f"❌ Error preparando registro: {e}")
        return None


# ── UPSERT ────────────────────────────────────────────────────

def guardar_datos(lista_datos: list):
    """Ejecuta UPSERT de razas e imágenes en la BD."""
    if not lista_datos:
        logger.warning("⚠️ No hay datos para guardar.")
        return

    session = SessionLocal()
    try:
        razas_ok = 0
        imgs_ok  = 0

        for dato in lista_datos:
            # Raza
            stmt = pg_insert(Raza).values(
                id                  = dato.get('raza_id'),
                nombre_raza         = dato.get('nombre_raza'),
                origen              = dato.get('origen_raza'),
                temperamento        = dato.get('temperamento'),
                vida_promedio       = dato.get('vida_promedio'),
                peso_metrico        = dato.get('peso_metrico'),
                wikipedia_url       = dato.get('wikipedia_url'),
                adaptabilidad       = dato.get('adaptabilidad'),
                nivel_energia       = dato.get('nivel_energia'),
                inteligencia        = dato.get('inteligencia'),
                social_humanos      = dato.get('social_humanos'),
                vida_anos           = dato.get('vida_anos'),
                peso_kg             = dato.get('peso_kg'),
                fecha_extraccion    = dato.get('fecha_extraccion'),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'nombre_raza':      stmt.excluded.nombre_raza,
                    'origen':           stmt.excluded.origen,
                    'temperamento':     stmt.excluded.temperamento,
                    'vida_promedio':    stmt.excluded.vida_promedio,
                    'peso_metrico':     stmt.excluded.peso_metrico,
                    'wikipedia_url':    stmt.excluded.wikipedia_url,
                    'adaptabilidad':    stmt.excluded.adaptabilidad,
                    'nivel_energia':    stmt.excluded.nivel_energia,
                    'inteligencia':     stmt.excluded.inteligencia,
                    'social_humanos':   stmt.excluded.social_humanos,
                    'vida_anos':        stmt.excluded.vida_anos,
                    'peso_kg':          stmt.excluded.peso_kg,
                    'fecha_actualizacion': dato.get('fecha_extraccion'),
                }
            )
            session.execute(stmt)
            razas_ok += 1

            # Imagen
            stmt = pg_insert(Imagen).values(
                id               = dato.get('imagen_id'),
                raza_id          = dato.get('raza_id'),
                url              = dato.get('url'),
                ancho            = dato.get('ancho'),
                alto             = dato.get('alto'),
                fecha_extraccion = dato.get('fecha_extraccion'),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'url':   stmt.excluded.url,
                    'ancho': stmt.excluded.ancho,
                    'alto':  stmt.excluded.alto,
                }
            )
            session.execute(stmt)
            imgs_ok += 1

        session.commit()
        logger.info(f"✅ UPSERT completado: {razas_ok} razas, {imgs_ok} imágenes.")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error en guardar_datos, rollback ejecutado: {e}")
        raise
    finally:
        session.close()


# ── Pipeline principal ────────────────────────────────────────

def ejecutar_carga(path: str = JSON_PATH):
    """Pipeline completo: verificar → crear tablas → leer JSON → UPSERT."""
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO LOADER — CAT ETL")
    logger.info("=" * 60)

    if not test_connection():
        logger.error("❌ No se puede continuar sin conexión a la BD.")
        return False

    create_all_tables()

    datos_crudos = cargar_json(path)
    if not datos_crudos:
        logger.error("❌ No hay datos para cargar.")
        return False

    datos_preparados = []
    omitidos = 0
    for dato in datos_crudos:
        registro = preparar_registro(dato)
        if registro:
            datos_preparados.append(registro)
        else:
            omitidos += 1

    logger.info(f"📋 Registros válidos: {len(datos_preparados)} | Omitidos: {omitidos}")

    if not datos_preparados:
        logger.error("❌ Ningún registro válido para cargar.")
        return False

    guardar_datos(datos_preparados)

    logger.info("=" * 60)
    logger.info(f"✅ CARGA COMPLETADA — {len(datos_preparados)} registros procesados.")
    logger.info("=" * 60)
    return True


# ── Ejecución directa ─────────────────────────────────────────

if __name__ == "__main__":
    exito = ejecutar_carga()
    exit(0 if exito else 1)