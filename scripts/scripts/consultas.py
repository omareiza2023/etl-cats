#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Raza, Imagen, MetricasETL
from sqlalchemy import func
import pandas as pd

db = SessionLocal()


def razas_por_origen():
    """Cantidad de razas por país de origen."""
    registros = db.query(
        Raza.origen,
        func.count(Raza.id).label('total_razas')
    ).group_by(Raza.origen).order_by(func.count(Raza.id).desc()).all()

    df = pd.DataFrame(registros, columns=['Origen', 'Total Razas'])
    print("\n🌍 RAZAS POR PAÍS DE ORIGEN:")
    print(df.to_string(index=False))


def raza_mas_energetica():
    """Raza con mayor nivel de energía."""
    raza = db.query(Raza).order_by(Raza.nivel_energia.desc()).first()
    if raza:
        print(f"\n⚡ RAZA MÁS ENERGÉTICA: {raza.nombre_raza} con energía {raza.nivel_energia}/5")


def raza_mas_inteligente():
    """Raza con mayor inteligencia."""
    raza = db.query(Raza).order_by(Raza.inteligencia.desc()).first()
    if raza:
        print(f"\n🧠 RAZA MÁS INTELIGENTE: {raza.nombre_raza} con inteligencia {raza.inteligencia}/5")


def raza_mas_longeva():
    """Raza con mayor esperanza de vida."""
    raza = db.query(Raza).order_by(Raza.vida_anos.desc()).first()
    if raza:
        print(f"\n📅 RAZA MÁS LONGEVA: {raza.nombre_raza} con {raza.vida_anos} años promedio")


def promedio_caracteristicas():
    """Promedios generales de todas las razas."""
    resultado = db.query(
        func.avg(Raza.nivel_energia).label('energia_prom'),
        func.avg(Raza.inteligencia).label('inteligencia_prom'),
        func.avg(Raza.social_humanos).label('social_prom'),
        func.avg(Raza.adaptabilidad).label('adaptabilidad_prom'),
        func.avg(Raza.vida_anos).label('vida_prom'),
        func.avg(Raza.peso_kg).label('peso_prom'),
    ).one()

    print("\n📊 PROMEDIOS GENERALES:")
    print(f"  ⚡ Energía:        {resultado.energia_prom:.2f} / 5")
    print(f"  🧠 Inteligencia:   {resultado.inteligencia_prom:.2f} / 5")
    print(f"  🤝 Social:         {resultado.social_prom:.2f} / 5")
    print(f"  🔄 Adaptabilidad:  {resultado.adaptabilidad_prom:.2f} / 5")
    print(f"  📅 Vida:           {resultado.vida_prom:.2f} años")
    print(f"  ⚖️  Peso:           {resultado.peso_prom:.2f} kg")


def imagenes_por_raza():
    """Top 10 razas con más imágenes."""
    registros = db.query(
        Raza.nombre_raza,
        func.count(Imagen.id).label('total_imagenes')
    ).join(Imagen).group_by(Raza.nombre_raza).order_by(
        func.count(Imagen.id).desc()
    ).limit(10).all()

    df = pd.DataFrame(registros, columns=['Raza', 'Total Imágenes'])
    print("\n🖼️  TOP 10 RAZAS CON MÁS IMÁGENES:")
    print(df.to_string(index=False))


def metricas_etl():
    """Muestra métricas de las últimas ejecuciones del ETL."""
    metricas = db.query(MetricasETL).order_by(
        MetricasETL.fecha_ejecucion.desc()
    ).limit(5).all()

    print("\n📈 ÚLTIMAS 5 EJECUCIONES DEL ETL:")
    for m in metricas:
        print(f"  - {m.fecha_ejecucion}: {m.estado} ({m.registros_guardados} registros en {m.tiempo_ejecucion_segundos:.2f}s)")


if __name__ == "__main__":
    try:
        print("\n" + "=" * 50)
        print("ANÁLISIS DE DATOS — THE CAT API")
        print("=" * 50)

        razas_por_origen()
        raza_mas_energetica()
        raza_mas_inteligente()
        raza_mas_longeva()
        promedio_caracteristicas()
        imagenes_por_raza()
        metricas_etl()

        print("\n" + "=" * 50 + "\n")

    finally:
        db.close()