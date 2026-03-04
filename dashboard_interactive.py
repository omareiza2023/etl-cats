#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.insert(0, '.')

try:
    from scripts.database import SessionLocal
    from scripts.models import Raza, Imagen
except Exception as e:
    st.error(f"❌ Error de importación: {e}")
    st.stop()

st.set_page_config(
    page_title="Dashboard Interactivo Gatos",
    page_icon="🎛️",
    layout="wide"
)

st.markdown("""
<style>
    .stDownloadButton button { background-color: #636EFA; color: white; border-radius: 8px; }
    .filter-box { background-color: #f8f9fa; padding: 10px; border-radius: 8px; }
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
    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        return pd.DataFrame()
    finally:
        session.close()

df_raw = cargar_datos()

if df_raw.empty:
    st.warning("⚠️ No hay datos. Ejecuta el extractor y el loader primero.")
    st.stop()

# ── Helper: agrupar por raza ──────────────────────────────────
def agrupar_por_raza(df):
    return df.groupby('nombre_raza').agg(
        origen=('origen', 'first'),
        nivel_energia=('nivel_energia', 'mean'),
        inteligencia=('inteligencia', 'mean'),
        social_humanos=('social_humanos', 'mean'),
        adaptabilidad=('adaptabilidad', 'mean'),
        vida_anos=('vida_anos', 'mean'),
        peso_kg=('peso_kg', 'mean'),
        total_imagenes=('imagen_id', 'count')
    ).reset_index()

# Valores globales para rangos de sliders
vida_min_g = int(df_raw['vida_anos'].dropna().min())
vida_max_g = int(df_raw['vida_anos'].dropna().max())
peso_min_g = int(df_raw['peso_kg'].dropna().min())
peso_max_g = int(df_raw['peso_kg'].dropna().max())
razas_opts  = sorted(df_raw['nombre_raza'].dropna().unique())
origen_opts = sorted(df_raw['origen'].dropna().unique())

# ── KPIs generales ────────────────────────────────────────────
st.markdown("### 📊 Resumen General")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("🐱 Razas", df_raw['nombre_raza'].nunique())
with col2:
    st.metric("🖼️ Imágenes", len(df_raw))
with col3:
    st.metric("📅 Vida Prom.", f"{df_raw['vida_anos'].mean():.1f} años")
with col4:
    st.metric("⚡ Energía Prom.", f"{df_raw['nivel_energia'].mean():.1f} / 5")
with col5:
    st.metric("⚖️ Peso Prom.", f"{df_raw['peso_kg'].mean():.1f} kg")

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 1: Comparativa de características por raza
# ════════════════════════════════════════════════════════════
st.markdown("### 🔀 Comparativa de Características por Raza")

with st.expander("🔧 Filtros — Comparativa", expanded=True):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        s1_razas = st.multiselect("🐱 Razas:", options=razas_opts, default=[], key="s1_razas", placeholder="Todas...")
    with fc2:
        s1_origen = st.multiselect("🌍 Origen:", options=origen_opts, default=[], key="s1_origen", placeholder="Todos...")
    with fc3:
        s1_energia = st.slider("⚡ Energía:", 1, 5, (1, 5), key="s1_energia")

df_s1 = df_raw.copy()
if s1_razas:
    df_s1 = df_s1[df_s1['nombre_raza'].isin(s1_razas)]
if s1_origen:
    df_s1 = df_s1[df_s1['origen'].isin(s1_origen)]
df_s1 = df_s1[df_s1['nivel_energia'].between(s1_energia[0], s1_energia[1])]
df_s1_razas = agrupar_por_raza(df_s1)

if df_s1_razas.empty:
    st.warning("⚠️ Sin resultados para estos filtros.")
else:
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            df_s1_razas.sort_values('nivel_energia', ascending=True),
            x='nivel_energia', y='nombre_raza', orientation='h',
            title="⚡ Nivel de Energía por Raza",
            color='nivel_energia', color_continuous_scale='YlOrRd',
            labels={'nivel_energia': 'Energía (1-5)', 'nombre_raza': 'Raza'}
        )
        fig.update_layout(showlegend=False, yaxis_title=None, height=500)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(
            df_s1_razas.sort_values('vida_anos', ascending=True),
            x='vida_anos', y='nombre_raza', orientation='h',
            title="📅 Longevidad por Raza",
            color='vida_anos', color_continuous_scale='RdYlGn',
            labels={'vida_anos': 'Años de vida', 'nombre_raza': 'Raza'}
        )
        fig.update_layout(showlegend=False, yaxis_title=None, height=500)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 2: Energía vs Longevidad vs Peso
# ════════════════════════════════════════════════════════════
st.markdown("### 🔵 Energía vs Longevidad vs Peso")

with st.expander("🔧 Filtros — Dispersión", expanded=True):
    fs1, fs2, fs3, fs4 = st.columns(4)
    with fs1:
        s2_energia = st.slider("⚡ Energía:", 1, 5, (1, 5), key="s2_energia")
    with fs2:
        s2_vida = st.slider("📅 Longevidad:", vida_min_g, vida_max_g, (vida_min_g, vida_max_g), key="s2_vida")
    with fs3:
        s2_peso = st.slider("⚖️ Peso (kg):", peso_min_g, peso_max_g, (peso_min_g, peso_max_g), key="s2_peso")
    with fs4:
        s2_inteligencia = st.slider("🧠 Inteligencia:", 1, 5, (1, 5), key="s2_inteligencia")

df_s2 = df_raw[
    df_raw['nivel_energia'].between(s2_energia[0], s2_energia[1]) &
    df_raw['vida_anos'].between(s2_vida[0], s2_vida[1]) &
    df_raw['peso_kg'].between(s2_peso[0], s2_peso[1]) &
    df_raw['inteligencia'].between(s2_inteligencia[0], s2_inteligencia[1])
]
df_s2_razas = agrupar_por_raza(df_s2)

if df_s2_razas.empty:
    st.warning("⚠️ Sin resultados para estos filtros.")
else:
    fig = px.scatter(
        df_s2_razas,
        x='nivel_energia', y='vida_anos',
        size='peso_kg', color='nombre_raza',
        hover_name='nombre_raza',
        hover_data={'origen': True, 'inteligencia': True, 'social_humanos': True, 'total_imagenes': True},
        title='Relación Energía — Longevidad — Peso por Raza',
        labels={'nivel_energia': 'Nivel de Energía (1-5)', 'vida_anos': 'Vida Promedio (años)', 'peso_kg': 'Peso (kg)'},
        size_max=40
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"📊 Mostrando **{df_s2_razas.shape[0]} razas** con los filtros aplicados")

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 3: Comparador directo de razas
# ════════════════════════════════════════════════════════════
st.markdown("### ⚖️ Comparador Directo de Razas")

with st.expander("🔧 Filtros — Comparador", expanded=True):
    fd1, fd2 = st.columns(2)
    with fd1:
        s3_raza_a = st.selectbox("🐱 Raza A:", options=razas_opts, index=0, key="s3_raza_a")
    with fd2:
        s3_raza_b = st.selectbox("🐱 Raza B:", options=razas_opts, index=min(1, len(razas_opts)-1), key="s3_raza_b")

df_s3_razas = agrupar_por_raza(df_raw)

if s3_raza_a and s3_raza_b:
    da     = df_s3_razas[df_s3_razas['nombre_raza'] == s3_raza_a]
    db_row = df_s3_razas[df_s3_razas['nombre_raza'] == s3_raza_b]

    if not da.empty and not db_row.empty:
        da     = da.iloc[0]
        db_row = db_row.iloc[0]

        atributos = ['Energía', 'Inteligencia', 'Adaptabilidad', 'Social']
        vals_a    = [da['nivel_energia'], da['inteligencia'], da['adaptabilidad'], da['social_humanos']]
        vals_b    = [db_row['nivel_energia'], db_row['inteligencia'], db_row['adaptabilidad'], db_row['social_humanos']]

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(name=s3_raza_a, x=atributos, y=vals_a, marker_color='#636EFA'))
            fig.add_trace(go.Bar(name=s3_raza_b, x=atributos, y=vals_b, marker_color='#EF553B'))
            fig.update_layout(barmode='group', title=f"{s3_raza_a} vs {s3_raza_b}", yaxis=dict(range=[0, 5]))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals_a + [vals_a[0]], theta=atributos + [atributos[0]],
                fill='toself', name=s3_raza_a, line_color='#636EFA'
            ))
            fig.add_trace(go.Scatterpolar(
                r=vals_b + [vals_b[0]], theta=atributos + [atributos[0]],
                fill='toself', name=s3_raza_b, line_color='#EF553B'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                title=f"Radar: {s3_raza_a} vs {s3_raza_b}"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Tabla comparativa
        st.markdown("##### 📋 Resumen Comparativo")
        comp = pd.DataFrame({
            'Atributo':   ['Energía', 'Inteligencia', 'Adaptabilidad', 'Social', 'Longevidad (años)', 'Peso (kg)'],
            s3_raza_a:    [da['nivel_energia'], da['inteligencia'], da['adaptabilidad'], da['social_humanos'], da['vida_anos'], da['peso_kg']],
            s3_raza_b:    [db_row['nivel_energia'], db_row['inteligencia'], db_row['adaptabilidad'], db_row['social_humanos'], db_row['vida_anos'], db_row['peso_kg']],
        })
        st.dataframe(comp, use_container_width=True, hide_index=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 4: Distribución por origen
# ════════════════════════════════════════════════════════════
st.markdown("### 🌍 Distribución por País de Origen")

with st.expander("🔧 Filtros — Origen", expanded=True):
    fo1, fo2 = st.columns(2)
    with fo1:
        s4_energia = st.slider("⚡ Energía:", 1, 5, (1, 5), key="s4_energia")
    with fo2:
        s4_social = st.slider("🤝 Social:", 1, 5, (1, 5), key="s4_social")

df_s4 = df_raw[
    df_raw['nivel_energia'].between(s4_energia[0], s4_energia[1]) &
    df_raw['social_humanos'].between(s4_social[0], s4_social[1])
]
df_s4_razas = agrupar_por_raza(df_s4)

if df_s4_razas.empty:
    st.warning("⚠️ Sin resultados para estos filtros.")
else:
    col1, col2 = st.columns(2)

    with col1:
        conteo_razas = df_s4_razas['origen'].value_counts().reset_index()
        conteo_razas.columns = ['origen', 'cantidad']
        top8  = conteo_razas.head(8).copy()
        otros = conteo_razas.iloc[8:]['cantidad'].sum()
        if otros > 0:
            top8 = pd.concat([top8, pd.DataFrame([{'origen': 'Otros', 'cantidad': otros}])], ignore_index=True)
        fig = px.pie(top8, names='origen', values='cantidad',
                     title="Razas por País de Origen",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        conteo_imgs = df_s4.groupby('origen')['imagen_id'].count().reset_index()
        conteo_imgs.columns = ['origen', 'cantidad']
        conteo_imgs = conteo_imgs.sort_values('cantidad', ascending=False)
        top8_imgs  = conteo_imgs.head(8).copy()
        otros_imgs = conteo_imgs.iloc[8:]['cantidad'].sum()
        if otros_imgs > 0:
            top8_imgs = pd.concat([top8_imgs, pd.DataFrame([{'origen': 'Otros', 'cantidad': otros_imgs}])], ignore_index=True)
        fig = px.pie(top8_imgs, names='origen', values='cantidad',
                     title="Imágenes por País de Origen",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 5: Tabla completa
# ════════════════════════════════════════════════════════════
st.markdown("### 📋 Tabla Completa de Datos")

with st.expander("🔧 Filtros — Tabla", expanded=True):
    ft1, ft2, ft3, ft4 = st.columns(4)
    with ft1:
        s5_razas = st.multiselect("🐱 Razas:", options=razas_opts, default=[], key="s5_razas", placeholder="Todas...")
    with ft2:
        s5_energia = st.slider("⚡ Energía:", 1, 5, (1, 5), key="s5_energia")
    with ft3:
        s5_inteligencia = st.slider("🧠 Inteligencia:", 1, 5, (1, 5), key="s5_inteligencia")
    with ft4:
        s5_social = st.slider("🤝 Social:", 1, 5, (1, 5), key="s5_social")

df_s5 = df_raw.copy()
if s5_razas:
    df_s5 = df_s5[df_s5['nombre_raza'].isin(s5_razas)]
df_s5 = df_s5[
    df_s5['nivel_energia'].between(s5_energia[0], s5_energia[1]) &
    df_s5['inteligencia'].between(s5_inteligencia[0], s5_inteligencia[1]) &
    df_s5['social_humanos'].between(s5_social[0], s5_social[1])
]

columnas_disponibles = ['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
                        'nivel_energia', 'inteligencia', 'adaptabilidad',
                        'social_humanos', 'temperamento', 'vida_promedio', 'peso_metrico']

col1, col2 = st.columns(2)
with col1:
    mostrar_todos = st.checkbox("Mostrar todos los registros", value=False)
with col2:
    columnas_sel = st.multiselect(
        "Columnas:",
        options=columnas_disponibles,
        default=['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
                 'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos']
    )

if columnas_sel:
    df_tabla = df_s5[columnas_sel].drop_duplicates(subset=['nombre_raza']) if 'nombre_raza' in columnas_sel else df_s5[columnas_sel]
    if 'vida_anos' in columnas_sel:
        df_tabla = df_tabla.sort_values('vida_anos', ascending=False)
    st.info(f"📊 **{len(df_tabla)} razas** encontradas")
    if mostrar_todos:
        st.dataframe(df_tabla, use_container_width=True, height=600)
    else:
        st.dataframe(df_tabla.head(20), use_container_width=True)

    st.markdown("---")
    csv = df_s5[columnas_disponibles].to_csv(index=False)
    st.download_button(
        label="⬇️ Descargar datos filtrados como CSV",
        data=csv,
        file_name=f"gatos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )