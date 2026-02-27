#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import func, and_
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Raza, Imagen

st.set_page_config(
    page_title="Dashboard Interactivo Gatos",
    page_icon="🎛️",
    layout="wide"
)

# ── CSS personalizado ─────────────────────────────────────────
st.markdown("""
<style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stDownloadButton button {
        background-color: #636EFA;
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎛️ Dashboard Interactivo — Control Total de Razas de Gatos")

db = SessionLocal()

# ── Carga de datos ────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    session = SessionLocal()
    try:
        razas    = session.query(Raza).all()
        imagenes = session.query(Imagen).all()

        df = pd.DataFrame([{
            'id':             r.id,
            'nombre_raza':    r.nombre_raza,
            'origen':         r.origen or 'Desconocido',
            'temperamento':   r.temperamento or 'N/A',
            'vida_promedio':  r.vida_promedio or 'N/A',
            'peso_metrico':   r.peso_metrico or 'N/A',
            'adaptabilidad':  r.adaptabilidad,
            'nivel_energia':  r.nivel_energia,
            'inteligencia':   r.inteligencia,
            'social_humanos': r.social_humanos,
            'vida_anos':      r.vida_anos,
            'peso_kg':        r.peso_kg,
            'wikipedia_url':  r.wikipedia_url or '',
            'fecha_extraccion': pd.to_datetime(r.fecha_extraccion),
        } for r in razas])

        df_img = pd.DataFrame([{
            'raza_id': img.raza_id,
            'url':     img.url,
        } for img in imagenes])

        return df, df_img
    finally:
        session.close()

df_raw, df_img = cargar_datos()

if df_raw.empty:
    st.warning("⚠️ No hay datos en la base de datos. Ejecuta el extractor y el loader primero.")
    st.stop()

# ── SIDEBAR — Controles ───────────────────────────────────────
st.sidebar.markdown("### 🔧 Controles")

# Selector de orígenes
origenes_disponibles = sorted(df_raw['origen'].dropna().unique())
origenes_sel = st.sidebar.multiselect(
    "🌍 Países de Origen:",
    options=origenes_disponibles,
    default=origenes_disponibles[:5] if len(origenes_disponibles) >= 5 else origenes_disponibles
)

# Filtro de energía
energia_min, energia_max = st.sidebar.slider(
    "⚡ Rango de Energía (1-5):",
    min_value=1, max_value=5, value=(1, 5)
)

# Filtro de longevidad
vida_min, vida_max = st.sidebar.slider(
    "📅 Rango de Longevidad (años):",
    min_value=1, max_value=25,
    value=(1, 25)
)

# Filtro de peso
peso_min, peso_max = st.sidebar.slider(
    "⚖️ Rango de Peso (kg):",
    min_value=1, max_value=15,
    value=(1, 15)
)

# Aplicar filtros
df = df_raw[
    df_raw['origen'].isin(origenes_sel) &
    df_raw['nivel_energia'].between(energia_min, energia_max) &
    df_raw['vida_anos'].between(vida_min, vida_max) &
    df_raw['peso_kg'].between(peso_min, peso_max)
].dropna(subset=['vida_anos', 'nivel_energia'])

st.sidebar.markdown("---")
st.sidebar.info(f"📊 Mostrando **{len(df)}** de **{len(df_raw)}** razas")

if df.empty:
    st.warning("⚠️ No hay razas que coincidan con los filtros seleccionados.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────
st.markdown("### 📊 Indicadores Clave")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📅 Vida Máx",   f"{df['vida_anos'].max():.1f} años")
with col2:
    st.metric("📅 Vida Mín",   f"{df['vida_anos'].min():.1f} años")
with col3:
    st.metric("📅 Vida Prom",  f"{df['vida_anos'].mean():.1f} años")
with col4:
    st.metric("⚡ Energía Prom", f"{df['nivel_energia'].mean():.1f} / 5")
with col5:
    st.metric("⚖️ Peso Prom",  f"{df['peso_kg'].mean():.1f} kg")

st.markdown("---")

# ── Gráficas interactivas ─────────────────────────────────────
col1, col2 = st.columns(2)

# Box plot: Distribución de longevidad por origen
with col1:
    st.markdown("#### 📦 Distribución de Longevidad por Origen")
    fig = px.box(
        df, x='origen', y='vida_anos',
        color='origen',
        title='Longevidad por País de Origen',
        labels={'vida_anos': 'Años de vida', 'origen': 'Origen'}
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

# Barras: Promedio de energía por origen
with col2:
    st.markdown("#### ⚡ Energía Promedio por Origen")
    energia_origen = df.groupby('origen')['nivel_energia'].mean().reset_index()
    energia_origen.columns = ['origen', 'energia_prom']
    energia_origen = energia_origen.sort_values('energia_prom', ascending=False)

    fig = px.bar(
        energia_origen, x='origen', y='energia_prom',
        color='energia_prom',
        color_continuous_scale='YlOrRd',
        title='Nivel de Energía Promedio por Origen',
        labels={'energia_prom': 'Energía Promedio', 'origen': 'Origen'}
    )
    fig.update_layout(xaxis_tickangle=-35, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Dispersión: Energía vs Longevidad (con peso como tamaño)
st.markdown("#### 🔵 Energía vs Longevidad vs Peso")
fig = px.scatter(
    df,
    x='nivel_energia', y='vida_anos',
    size='peso_kg', color='origen',
    hover_name='nombre_raza',
    hover_data=['temperamento', 'adaptabilidad', 'inteligencia'],
    title='Relación Energía — Longevidad — Peso por Raza',
    labels={
        'nivel_energia': 'Nivel de Energía (1-5)',
        'vida_anos':     'Vida Promedio (años)',
        'peso_kg':       'Peso (kg)'
    },
    size_max=30
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Evolución temporal de extracciones
st.markdown("#### 📈 Razas Extraídas en el Tiempo")
df_tiempo = df.copy()
df_tiempo['fecha_dia'] = df_tiempo['fecha_extraccion'].dt.date
conteo_tiempo = df_tiempo.groupby('fecha_dia').size().reset_index(name='cantidad')

fig = px.line(
    conteo_tiempo, x='fecha_dia', y='cantidad',
    title='Cantidad de Razas Extraídas por Día',
    markers=True,
    labels={'fecha_dia': 'Fecha', 'cantidad': 'Razas extraídas'}
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Tabla interactiva ─────────────────────────────────────────
st.markdown("#### 📋 Datos Detallados")

col1, col2 = st.columns(2)

with col1:
    mostrar_todos = st.checkbox("Mostrar todos los registros", value=False)

with col2:
    columnas_disponibles = ['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
                            'nivel_energia', 'inteligencia', 'adaptabilidad',
                            'social_humanos', 'temperamento', 'fecha_extraccion']
    columnas_sel = st.multiselect(
        "Columnas a mostrar:",
        options=columnas_disponibles,
        default=['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
                 'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos']
    )

df_tabla = df[columnas_sel].sort_values('vida_anos', ascending=False) if 'vida_anos' in columnas_sel else df[columnas_sel]

if mostrar_todos:
    st.dataframe(df_tabla, use_container_width=True, height=600)
else:
    st.dataframe(df_tabla.head(20), use_container_width=True)

# ── Descarga de datos ─────────────────────────────────────────
st.markdown("---")
csv = df[columnas_disponibles].to_csv(index=False)
st.download_button(
    label="⬇️ Descargar datos filtrados como CSV",
    data=csv,
    file_name=f"gatos_datos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

db.close()