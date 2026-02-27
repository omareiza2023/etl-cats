#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from scripts.database import verificar_conexion, crear_tablas, guardar_datos

# ── Logging ──────────────────────────────────────────────────────────────────
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

# ── Ruta del archivo fuente ───────────────────────────────────────────────────
JSON_PATH = os.getenv('CATS_JSON_PATH', 'data/cats_raw.json')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _promedio_rango(valor: str):
    """
    Convierte un rango tipo '14 - 15' o '3 - 5' a su promedio numérico (float).
    Retorna None si no puede parsearlo.
    """
    try:
        partes = str(valor).split('-')
        return sum(float(p.strip()) for p in partes) / len(partes)
    except Exception:
        return None


def _parsear_fecha(valor):
    """Convierte string ISO a datetime si es necesario."""
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.fromisoformat(str(valor))
    except Exception:
        return datetime.now()


# ── Carga y validación del JSON ───────────────────────────────────────────────

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


# ── Transformación para compatibilidad con database.py ───────────────────────

def preparar_registro(dato: dict) -> dict | None:
    """
    Asegura que cada registro tenga los campos que esperan
    upsert_raza() y upsert_imagen() en database.py.

    Campos requeridos en el dict de salida:
        raza_id, imagen_id, nombre_raza, origen_raza, temperamento,
        vida_promedio, peso_metrico, wikipedia_url,
        adaptabilidad, nivel_energia, inteligencia, social_humanos,
        vida_anos, peso_kg,
        url, ancho, alto, fecha_extraccion
    """
    try:
        raza_id   = dato.get('raza_id') or dato.get('id')
        imagen_id = dato.get('imagen_id') or dato.get('id')

        if not raza_id or not imagen_id:
            logger.warning(f"⚠️ Registro sin id válido, se omite: {dato}")
            return None

        return {
            # ── Identificadores ──────────────────────────────
            'raza_id':          raza_id,
            'imagen_id':        imagen_id,

            # ── Datos de raza ─────────────────────────────────
            'nombre_raza':      dato.get('nombre_raza', 'Desconocida'),
            'origen_raza':      dato.get('origen_raza') or dato.get('origen', 'N/A'),
            'temperamento':     dato.get('temperamento', 'N/A'),
            'vida_promedio':    dato.get('vida_promedio', 'N/A'),
            'peso_metrico':     dato.get('peso_metrico', 'N/A'),
            'wikipedia_url':    dato.get('wikipedia_url', 'N/A'),

            # ── Atributos numéricos (escala 1-5) ──────────────
            'adaptabilidad':    dato.get('adaptabilidad'),
            'nivel_energia':    dato.get('nivel_energia'),
            'inteligencia':     dato.get('inteligencia'),
            'social_humanos':   dato.get('social_humanos'),

            # ── Campos calculados ─────────────────────────────
            'vida_anos':        _promedio_rango(dato.get('vida_promedio')),
            'peso_kg':          _promedio_rango(dato.get('peso_metrico')),

            # ── Datos de imagen ───────────────────────────────
            'url':              dato.get('url'),
            'ancho':            dato.get('ancho'),
            'alto':             dato.get('alto'),

            # ── Auditoría ─────────────────────────────────────
            'fecha_extraccion': _parsear_fecha(dato.get('fecha_extraccion')),
        }
    except Exception as e:
        logger.error(f"❌ Error preparando registro: {e}")
        return None


# ── Pipeline principal ────────────────────────────────────────────────────────

def ejecutar_carga(path: str = JSON_PATH):
    """
    Pipeline completo del loader:
      1. Verifica conexión a PostgreSQL
      2. Crea tablas si no existen
      3. Lee el JSON
      4. Prepara y valida cada registro
      5. Ejecuta el UPSERT en la BD
    """
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO LOADER — CAT ETL")
    logger.info("=" * 60)

    # 1. Verificar conexión
    if not verificar_conexion():
        logger.error("❌ No se puede continuar sin conexión a la BD.")
        return False

    # 2. Crear tablas si no existen
    crear_tablas()

    # 3. Leer JSON
    datos_crudos = cargar_json(path)
    if not datos_crudos:
        logger.error("❌ No hay datos para cargar.")
        return False

    # 4. Preparar registros
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

    # 5. UPSERT en la BD
    guardar_datos(datos_preparados)

    logger.info("=" * 60)
    logger.info(f"✅ CARGA COMPLETADA — {len(datos_preparados)} registros procesados.")
    logger.info("=" * 60)
    return True


# ── Ejecución directa ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    exito = ejecutar_carga()
    exit(0 if exito else 1)