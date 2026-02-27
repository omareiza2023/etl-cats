#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Raza, Imagen

# ── Configuración de página ───────────────────────────────────
st.set_page_config(
    page_title="Dashboard Gatos ETL",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🐱 Dashboard de Razas de Gatos — ETL The Cat API")
st.markdown("---")

# ── Conexión a la BD ──────────────────────────────────────────
db = SessionLocal()

try:
    # ── Cargar datos ──────────────────────────────────────────
    razas   = db.query(Raza).all()
    imagenes = db.query(Imagen).all()

    if not razas:
        st.warning("⚠️ No hay datos en la base de datos. Ejecuta el extractor y el loader primero.")
        st.stop()

    # ── Construir DataFrames ───────────────────────────────────
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
        'fecha_extraccion': r.fecha_extraccion,
    } for r in razas])

    df_imagenes = pd.DataFrame([{
        'raza_id': img.raza_id,
        'url':     img.url,
    } for img in imagenes])

    # ── SIDEBAR — Filtros ─────────────────────────────────────
    st.sidebar.title("🔧 Filtros")

    origenes_disponibles = sorted(df['origen'].unique())
    origenes_seleccionados = st.sidebar.multiselect(
        "🌍 Filtrar por origen:",
        options=origenes_disponibles,
        default=origenes_disponibles
    )

    energia_min, energia_max = st.sidebar.slider(
        "⚡ Nivel de energía:",
        min_value=1, max_value=5,
        value=(1, 5)
    )

    df_f = df[
        df['origen'].isin(origenes_seleccionados) &
        df['nivel_energia'].between(energia_min, energia_max)
    ].dropna(subset=['vida_anos'])

    st.sidebar.markdown("---")
    st.sidebar.info(f"📊 Mostrando **{len(df_f)}** de **{len(df)}** razas")

    # ── SECCIÓN 1 — Métricas resumen ──────────────────────────
    st.subheader("📈 Métricas Resumen")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🐱 Total Razas",
            value=len(df_f)
        )
    with col2:
        energia_prom = df_f['nivel_energia'].mean()
        st.metric(
            label="⚡ Energía Promedio",
            value=f"{energia_prom:.1f} / 5"
        )
    with col3:
        vida_prom = df_f['vida_anos'].mean()
        st.metric(
            label="📅 Longevidad Promedio",
            value=f"{vida_prom:.1f} años"
        )
    with col4:
        peso_prom = df_f['peso_kg'].mean()
        st.metric(
            label="⚖️ Peso Promedio",
            value=f"{peso_prom:.1f} kg"
        )

    st.markdown("---")

    # ── SECCIÓN 2 — Gráficas ──────────────────────────────────
    st.subheader("📉 Visualizaciones")

    col1, col2 = st.columns(2)

    # Barras: Top razas más longevas
    with col1:
        top15 = df_f.nlargest(15, 'vida_anos').sort_values('vida_anos')
        fig_barras = px.bar(
            top15,
            x='vida_anos',
            y='nombre_raza',
            orientation='h',
            title="🏆 Top 15 Razas Más Longevas",
            color='vida_anos',
            color_continuous_scale='RdYlGn',
            labels={'vida_anos': 'Años de vida', 'nombre_raza': 'Raza'}
        )
        fig_barras.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_barras, use_container_width=True)

    # Pastel: Distribución por origen
    with col2:
        conteo_origen = df_f['origen'].value_counts().reset_index()
        conteo_origen.columns = ['origen', 'cantidad']
        top8 = conteo_origen.head(8)
        otros = conteo_origen.iloc[8:]['cantidad'].sum()
        if otros > 0:
            top8 = pd.concat([top8, pd.DataFrame([{'origen': 'Otros', 'cantidad': otros}])], ignore_index=True)

        fig_pie = px.pie(
            top8,
            names='origen',
            values='cantidad',
            title="🌍 Distribución de Razas por País de Origen",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    col1, col2 = st.columns(2)

    # Dispersión: Energía vs Longevidad
    with col1:
        fig_scatter = px.scatter(
            df_f.dropna(subset=['nivel_energia', 'vida_anos']),
            x='nivel_energia',
            y='vida_anos',
            color='origen',
            size='peso_kg',
            hover_name='nombre_raza',
            hover_data=['temperamento'],
            title="⚡ Energía vs Longevidad por Raza",
            labels={
                'nivel_energia': 'Nivel de Energía (1-5)',
                'vida_anos': 'Vida Promedio (años)'
            }
        )
        fig_scatter.update_layout(showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Heatmap: Correlación entre características
    with col2:
        columnas_heatmap = ['vida_anos', 'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos', 'peso_kg']
        etiquetas = ['Longevidad', 'Energía', 'Inteligencia', 'Adaptabilidad', 'Social', 'Peso']
        df_corr = df_f[columnas_heatmap].dropna().corr()
        df_corr.index   = etiquetas
        df_corr.columns = etiquetas

        fig_heat = go.Figure(data=go.Heatmap(
            z=df_corr.values,
            x=etiquetas,
            y=etiquetas,
            colorscale='RdBu',
            zmid=0,
            text=df_corr.round(2).values,
            texttemplate='%{text}',
            textfont={'size': 11},
        ))
        fig_heat.update_layout(title="🔥 Correlación entre Características")
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # ── SECCIÓN 3 — Galería de imágenes ───────────────────────
    st.subheader("🖼️ Galería de Imágenes")

    razas_con_imagen = df_f[df_f['id'].isin(df_imagenes['raza_id'])]['nombre_raza'].unique()
    raza_seleccionada = st.selectbox(
        "Selecciona una raza para ver sus imágenes:",
        options=sorted(razas_con_imagen)
    )

    if raza_seleccionada:
        raza_id = df_f[df_f['nombre_raza'] == raza_seleccionada]['id'].values[0]
        urls = df_imagenes[df_imagenes['raza_id'] == raza_id]['url'].tolist()

        if urls:
            cols = st.columns(min(len(urls), 4))
            for i, url in enumerate(urls[:4]):
                with cols[i % 4]:
                    st.image(url, caption=raza_seleccionada, use_column_width=True)
        else:
            st.info("No hay imágenes disponibles para esta raza.")

    st.markdown("---")

    # ── SECCIÓN 4 — Tabla detallada ───────────────────────────
    st.subheader("📋 Tabla Detallada de Razas")

    columnas_tabla = ['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
                      'nivel_energia', 'inteligencia', 'adaptabilidad',
                      'social_humanos', 'temperamento']

    st.dataframe(
        df_f[columnas_tabla].sort_values('vida_anos', ascending=False).rename(columns={
            'nombre_raza':    'Raza',
            'origen':         'Origen',
            'vida_anos':      'Vida (años)',
            'peso_kg':        'Peso (kg)',
            'nivel_energia':  'Energía',
            'inteligencia':   'Inteligencia',
            'adaptabilidad':  'Adaptabilidad',
            'social_humanos': 'Social',
            'temperamento':   'Temperamento',
        }),
        use_container_width=True,
        height=420
    )

finally:
    db.close()