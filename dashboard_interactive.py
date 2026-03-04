#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Raza, Imagen

st.set_page_config(
    page_title="Dashboard Interactivo Gatos",
    page_icon="🎛️",
    layout="wide"
)

st.markdown("""
<style>
    .stDownloadButton button { background-color: #636EFA; color: white; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🎛️ Dashboard Interactivo — Razas de Gatos")

# ── Carga de datos ────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    session = SessionLocal()
    try:
        resultados = session.query(Imagen, Raza).join(Raza, Imagen.raza_id == Raza.id).all()
        df = pd.DataFrame([{
            'imagen_id':      img.id,
            'url':            img.url,
            'raza_id':        raza.id,
            'nombre_raza':    raza.nombre_raza,
            'origen':         raza.origen or 'Desconocido',
            'temperamento':   raza.temperamento or 'N/A',
            'vida_promedio':  raza.vida_promedio or 'N/A',
            'peso_metrico':   raza.peso_metrico or 'N/A',
            'adaptabilidad':  raza.adaptabilidad,
            'nivel_energia':  raza.nivel_energia,
            'inteligencia':   raza.inteligencia,
            'social_humanos': raza.social_humanos,
            'vida_anos':      raza.vida_anos,
            'peso_kg':        raza.peso_kg,
            'wikipedia_url':  raza.wikipedia_url or '',
        } for img, raza in resultados])
        return df
    finally:
        session.close()

df_raw = cargar_datos()

if df_raw.empty:
    st.warning("⚠️ No hay datos. Ejecuta el extractor y el loader primero.")
    st.stop()

# ── SIDEBAR — Filtros ─────────────────────────────────────────
st.sidebar.markdown("### 🔧 Filtros")

# Filtro por raza
razas_disponibles = sorted(df_raw['nombre_raza'].dropna().unique())
razas_sel = st.sidebar.multiselect(
    "🐱 Raza:",
    options=razas_disponibles,
    default=[],
    placeholder="Todas las razas..."
)

# Filtro por origen
origenes_disponibles = sorted(df_raw['origen'].dropna().unique())
origenes_sel = st.sidebar.multiselect(
    "🌍 Origen:",
    options=origenes_disponibles,
    default=[],
    placeholder="Todos los orígenes..."
)

st.sidebar.markdown("---")

# Sliders numéricos
energia_min, energia_max = st.sidebar.slider("⚡ Energía (1-5):", 1, 5, (1, 5))
inteligencia_min, inteligencia_max = st.sidebar.slider("🧠 Inteligencia (1-5):", 1, 5, (1, 5))
social_min, social_max = st.sidebar.slider("🤝 Social con humanos (1-5):", 1, 5, (1, 5))
adaptabilidad_min, adaptabilidad_max = st.sidebar.slider("🔄 Adaptabilidad (1-5):", 1, 5, (1, 5))

vida_min_val = int(df_raw['vida_anos'].dropna().min()) if not df_raw['vida_anos'].dropna().empty else 1
vida_max_val = int(df_raw['vida_anos'].dropna().max()) if not df_raw['vida_anos'].dropna().empty else 25
vida_min, vida_max = st.sidebar.slider("📅 Longevidad (años):", vida_min_val, vida_max_val, (vida_min_val, vida_max_val))

peso_min_val = int(df_raw['peso_kg'].dropna().min()) if not df_raw['peso_kg'].dropna().empty else 1
peso_max_val = int(df_raw['peso_kg'].dropna().max()) if not df_raw['peso_kg'].dropna().empty else 15
peso_min, peso_max = st.sidebar.slider("⚖️ Peso (kg):", peso_min_val, peso_max_val, (peso_min_val, peso_max_val))

# ── Aplicar filtros ───────────────────────────────────────────
df = df_raw.copy()
if razas_sel:
    df = df[df['nombre_raza'].isin(razas_sel)]
if origenes_sel:
    df = df[df['origen'].isin(origenes_sel)]

df = df[
    df['nivel_energia'].between(energia_min, energia_max) &
    df['inteligencia'].between(inteligencia_min, inteligencia_max) &
    df['social_humanos'].between(social_min, social_max) &
    df['adaptabilidad'].between(adaptabilidad_min, adaptabilidad_max) &
    df['vida_anos'].between(vida_min, vida_max) &
    df['peso_kg'].between(peso_min, peso_max)
]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 **{len(df)}** imágenes | **{df['nombre_raza'].nunique()}** razas")

if df.empty:
    st.warning("⚠️ No hay razas que coincidan con los filtros.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────
st.markdown("### 📊 Indicadores Clave")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("🐱 Razas", df['nombre_raza'].nunique())
with col2:
    st.metric("🖼️ Imágenes", len(df))
with col3:
    st.metric("📅 Vida Prom.", f"{df['vida_anos'].mean():.1f} años")
with col4:
    st.metric("⚡ Energía Prom.", f"{df['nivel_energia'].mean():.1f} / 5")
with col5:
    st.metric("⚖️ Peso Prom.", f"{df['peso_kg'].mean():.1f} kg")

st.markdown("---")

# ── SECCIÓN 1: Comparativa de razas ───────────────────────────
st.markdown("### 🔀 Comparativa de Características por Raza")

# Agrupar por raza para comparativas
df_razas = df.groupby('nombre_raza').agg(
    origen=('origen', 'first'),
    nivel_energia=('nivel_energia', 'mean'),
    inteligencia=('inteligencia', 'mean'),
    social_humanos=('social_humanos', 'mean'),
    adaptabilidad=('adaptabilidad', 'mean'),
    vida_anos=('vida_anos', 'mean'),
    peso_kg=('peso_kg', 'mean'),
    total_imagenes=('imagen_id', 'count')
).reset_index()

col1, col2 = st.columns(2)

# Energía por raza
with col1:
    fig = px.bar(
        df_razas.sort_values('nivel_energia', ascending=True),
        x='nivel_energia', y='nombre_raza',
        orientation='h',
        title="⚡ Nivel de Energía por Raza",
        color='nivel_energia',
        color_continuous_scale='YlOrRd',
        labels={'nivel_energia': 'Energía (1-5)', 'nombre_raza': 'Raza'}
    )
    fig.update_layout(showlegend=False, yaxis_title=None, height=500)
    st.plotly_chart(fig, use_container_width=True)

# Longevidad por raza
with col2:
    fig = px.bar(
        df_razas.sort_values('vida_anos', ascending=True),
        x='vida_anos', y='nombre_raza',
        orientation='h',
        title="📅 Longevidad por Raza",
        color='vida_anos',
        color_continuous_scale='RdYlGn',
        labels={'vida_anos': 'Años de vida', 'nombre_raza': 'Raza'}
    )
    fig.update_layout(showlegend=False, yaxis_title=None, height=500)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── SECCIÓN 2: Dispersión Energía vs Longevidad ────────────────
st.markdown("### 🔵 Energía vs Longevidad vs Peso")
fig = px.scatter(
    df_razas,
    x='nivel_energia', y='vida_anos',
    size='peso_kg', color='nombre_raza',
    hover_name='nombre_raza',
    hover_data={'origen': True, 'inteligencia': True, 'social_humanos': True, 'total_imagenes': True},
    title='Relación Energía — Longevidad — Peso por Raza',
    labels={
        'nivel_energia': 'Nivel de Energía (1-5)',
        'vida_anos':     'Vida Promedio (años)',
        'peso_kg':       'Peso (kg)'
    },
    size_max=40
)
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── SECCIÓN 3: Comparador directo de razas ────────────────────
st.markdown("### ⚖️ Comparador Directo de Razas")

razas_comparar = sorted(df_razas['nombre_raza'].unique())
col1, col2 = st.columns(2)
with col1:
    raza_a = st.selectbox("Raza A:", options=razas_comparar, index=0)
with col2:
    raza_b = st.selectbox("Raza B:", options=razas_comparar, index=min(1, len(razas_comparar)-1))

if raza_a and raza_b:
    da = df_razas[df_razas['nombre_raza'] == raza_a].iloc[0]
    db_row = df_razas[df_razas['nombre_raza'] == raza_b].iloc[0]

    atributos = ['Energía', 'Inteligencia', 'Adaptabilidad', 'Social']
    vals_a    = [da['nivel_energia'], da['inteligencia'], da['adaptabilidad'], da['social_humanos']]
    vals_b    = [db_row['nivel_energia'], db_row['inteligencia'], db_row['adaptabilidad'], db_row['social_humanos']]

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name=raza_a, x=atributos, y=vals_a, marker_color='#636EFA'))
        fig.add_trace(go.Bar(name=raza_b, x=atributos, y=vals_b, marker_color='#EF553B'))
        fig.update_layout(barmode='group', title=f"{raza_a} vs {raza_b}", yaxis=dict(range=[0, 5]))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        categorias = ['Energía', 'Inteligencia', 'Adaptabilidad', 'Social']
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals_a + [vals_a[0]], theta=categorias + [categorias[0]],
            fill='toself', name=raza_a, line_color='#636EFA'
        ))
        fig.add_trace(go.Scatterpolar(
            r=vals_b + [vals_b[0]], theta=categorias + [categorias[0]],
            fill='toself', name=raza_b, line_color='#EF553B'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            title=f"Radar: {raza_a} vs {raza_b}"
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── SECCIÓN 4: Pastel por origen ──────────────────────────────
st.markdown("### 🌍 Distribución por País de Origen")

col1, col2 = st.columns(2)

with col1:
    # Pastel por número de razas
    conteo_razas = df_razas['origen'].value_counts().reset_index()
    conteo_razas.columns = ['origen', 'cantidad']
    top8 = conteo_razas.head(8).copy()
    otros = conteo_razas.iloc[8:]['cantidad'].sum()
    if otros > 0:
        top8 = pd.concat([top8, pd.DataFrame([{'origen': 'Otros', 'cantidad': otros}])], ignore_index=True)
    fig = px.pie(
        top8, names='origen', values='cantidad',
        title="Razas por País de Origen",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Pastel por número de imágenes
    conteo_imgs = df.groupby('origen')['imagen_id'].count().reset_index()
    conteo_imgs.columns = ['origen', 'cantidad']
    conteo_imgs = conteo_imgs.sort_values('cantidad', ascending=False)
    top8_imgs = conteo_imgs.head(8).copy()
    otros_imgs = conteo_imgs.iloc[8:]['cantidad'].sum()
    if otros_imgs > 0:
        top8_imgs = pd.concat([top8_imgs, pd.DataFrame([{'origen': 'Otros', 'cantidad': otros_imgs}])], ignore_index=True)
    fig = px.pie(
        top8_imgs, names='origen', values='cantidad',
        title="Imágenes por País de Origen",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── SECCIÓN 5: Tabla completa ─────────────────────────────────
st.markdown("### 📋 Tabla Completa de Datos")

col1, col2 = st.columns(2)
with col1:
    mostrar_todos = st.checkbox("Mostrar todos los registros", value=False)
with col2:
    columnas_disponibles = ['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
                            'nivel_energia', 'inteligencia', 'adaptabilidad',
                            'social_humanos', 'temperamento', 'vida_promedio', 'peso_metrico']
    columnas_sel = st.multiselect(
        "Columnas a mostrar:",
        options=columnas_disponibles,
        default=['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
                 'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos']
    )

df_tabla = df[columnas_sel].drop_duplicates(subset=['nombre_raza']).sort_values('vida_anos', ascending=False) if 'vida_anos' in columnas_sel else df[columnas_sel].drop_duplicates(subset=['nombre_raza'])

if mostrar_todos:
    st.dataframe(df_tabla, use_container_width=True, height=600)
else:
    st.dataframe(df_tabla.head(20), use_container_width=True)

# ── Descarga ──────────────────────────────────────────────────
st.markdown("---")
csv = df[columnas_disponibles].to_csv(index=False)
st.download_button(
    label="⬇️ Descargar datos filtrados como CSV",
    data=csv,
    file_name=f"gatos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)