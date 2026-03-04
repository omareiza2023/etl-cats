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
    .carrusel-img { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .raza-info { background: #f0f2f6; padding: 12px 18px; border-radius: 10px; margin-bottom: 10px; }
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

vida_min_g  = int(df_raw['vida_anos'].dropna().min())
vida_max_g  = int(df_raw['vida_anos'].dropna().max())
peso_min_g  = int(df_raw['peso_kg'].dropna().min())
peso_max_g  = int(df_raw['peso_kg'].dropna().max())
razas_opts  = sorted(df_raw['nombre_raza'].dropna().unique())
origen_opts = sorted(df_raw['origen'].dropna().unique())

# ── KPIs ──────────────────────────────────────────────────────
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
# SECCIÓN 1: Comparativa — filtros: energía, inteligencia, social, peso
# ════════════════════════════════════════════════════════════
st.markdown("### 🔀 Comparativa de Características por Raza")
with st.expander("🔧 Filtros", expanded=True):
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        s1_energia = st.slider("⚡ Energía:", 1, 5, (1, 5), key="s1_energia")
    with fc2:
        s1_inteligencia = st.slider("🧠 Inteligencia:", 1, 5, (1, 5), key="s1_inteligencia")
    with fc3:
        s1_social = st.slider("🤝 Social:", 1, 5, (1, 5), key="s1_social")
    with fc4:
        s1_peso = st.slider("⚖️ Peso (kg):", peso_min_g, peso_max_g, (peso_min_g, peso_max_g), key="s1_peso")

df_s1 = df_raw[
    df_raw['nivel_energia'].between(s1_energia[0], s1_energia[1]) &
    df_raw['inteligencia'].between(s1_inteligencia[0], s1_inteligencia[1]) &
    df_raw['social_humanos'].between(s1_social[0], s1_social[1]) &
    df_raw['peso_kg'].between(s1_peso[0], s1_peso[1])
]
df_s1_razas = agrupar_por_raza(df_s1)

if df_s1_razas.empty:
    st.warning("⚠️ Sin resultados para estos filtros.")
else:
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_s1_razas.sort_values('nivel_energia', ascending=True),
                     x='nivel_energia', y='nombre_raza', orientation='h',
                     title="⚡ Nivel de Energía por Raza",
                     color='nivel_energia', color_continuous_scale='YlOrRd',
                     labels={'nivel_energia': 'Energía (1-5)', 'nombre_raza': 'Raza'})
        fig.update_layout(showlegend=False, yaxis_title=None, height=500)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(df_s1_razas.sort_values('vida_anos', ascending=True),
                     x='vida_anos', y='nombre_raza', orientation='h',
                     title="📅 Longevidad por Raza",
                     color='vida_anos', color_continuous_scale='RdYlGn',
                     labels={'vida_anos': 'Años de vida', 'nombre_raza': 'Raza'})
        fig.update_layout(showlegend=False, yaxis_title=None, height=500)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 2: Dispersión
# ════════════════════════════════════════════════════════════
st.markdown("### 🔵 Energía vs Longevidad vs Peso")
with st.expander("🔧 Filtros", expanded=True):
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
    fig = px.scatter(df_s2_razas, x='nivel_energia', y='vida_anos',
                     size='peso_kg', color='nombre_raza',
                     hover_name='nombre_raza',
                     hover_data={'origen': True, 'inteligencia': True, 'social_humanos': True, 'total_imagenes': True},
                     title='Relación Energía — Longevidad — Peso por Raza',
                     labels={'nivel_energia': 'Nivel de Energía (1-5)', 'vida_anos': 'Vida Promedio (años)', 'peso_kg': 'Peso (kg)'},
                     size_max=40)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"📊 Mostrando **{df_s2_razas.shape[0]} razas**")

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 3: Comparador directo
# ════════════════════════════════════════════════════════════
st.markdown("### ⚖️ Comparador Directo de Razas")
with st.expander("🔧 Filtros", expanded=True):
    fd1, fd2 = st.columns(2)
    with fd1:
        s3_raza_a = st.selectbox("🐱 Raza A:", options=razas_opts, index=0, key="s3_raza_a")
    with fd2:
        s3_raza_b = st.selectbox("🐱 Raza B:", options=razas_opts, index=min(1, len(razas_opts)-1), key="s3_raza_b")

df_s3_razas = agrupar_por_raza(df_raw)
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
        fig.add_trace(go.Scatterpolar(r=vals_a + [vals_a[0]], theta=atributos + [atributos[0]],
                                      fill='toself', name=s3_raza_a, line_color='#636EFA'))
        fig.add_trace(go.Scatterpolar(r=vals_b + [vals_b[0]], theta=atributos + [atributos[0]],
                                      fill='toself', name=s3_raza_b, line_color='#EF553B'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                          title=f"Radar: {s3_raza_a} vs {s3_raza_b}")
        st.plotly_chart(fig, use_container_width=True)

    comp = pd.DataFrame({
        'Atributo': ['Energía', 'Inteligencia', 'Adaptabilidad', 'Social', 'Longevidad (años)', 'Peso (kg)'],
        s3_raza_a:  [da['nivel_energia'], da['inteligencia'], da['adaptabilidad'], da['social_humanos'], da['vida_anos'], da['peso_kg']],
        s3_raza_b:  [db_row['nivel_energia'], db_row['inteligencia'], db_row['adaptabilidad'], db_row['social_humanos'], db_row['vida_anos'], db_row['peso_kg']],
    })
    st.dataframe(comp, use_container_width=True, hide_index=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 4: Distribución por origen
# ════════════════════════════════════════════════════════════
st.markdown("### 🌍 Distribución por País de Origen")
with st.expander("🔧 Filtros", expanded=True):
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
        fig = px.pie(top8, names='origen', values='cantidad', title="Razas por País de Origen",
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
        fig = px.pie(top8_imgs, names='origen', values='cantidad', title="Imágenes por País de Origen",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════
# SECCIÓN 5: Galería carrusel por raza
# ════════════════════════════════════════════════════════════
st.markdown("### 🖼️ Galería de Imágenes por Raza")

s5_raza = st.selectbox("🐱 Selecciona una raza:", options=razas_opts, key="s5_raza")

df_galeria = df_raw[df_raw['nombre_raza'] == s5_raza][['url', 'imagen_id']].dropna()
urls = df_galeria['url'].tolist()

if not urls:
    st.warning("⚠️ No hay imágenes para esta raza.")
else:
    info_raza = df_raw[df_raw['nombre_raza'] == s5_raza].iloc[0]
    st.markdown(f"""
    <div class="raza-info">
    🐱 <b>{s5_raza}</b> &nbsp;|&nbsp; 🌍 {info_raza['origen']} &nbsp;|&nbsp;
    📅 {info_raza['vida_promedio']} años &nbsp;|&nbsp; ⚖️ {info_raza['peso_metrico']} kg &nbsp;|&nbsp;
    ⚡ Energía: {info_raza['nivel_energia']} &nbsp;|&nbsp; 🧠 Inteligencia: {info_raza['inteligencia']}
    </div>
    """, unsafe_allow_html=True)

    # ── Carrusel con session_state ────────────────────────────
    key_idx = f"carrusel_{s5_raza}"
    if key_idx not in st.session_state:
        st.session_state[key_idx] = 0

    idx = st.session_state[key_idx]
    total = len(urls)

    # Imagen actual centrada
    col_prev, col_img, col_next = st.columns([1, 6, 1])

    with col_prev:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button("◀", key="prev", use_container_width=True):
            st.session_state[key_idx] = (idx - 1) % total

    with col_img:
        st.image(urls[idx], use_container_width=True)
        st.markdown(f"<p style='text-align:center; color:gray;'>📷 {idx + 1} / {total}</p>", unsafe_allow_html=True)

    with col_next:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button("▶", key="next", use_container_width=True):
            st.session_state[key_idx] = (idx + 1) % total

    # Miniaturas navegables
    st.markdown("##### Miniaturas")
    thumb_cols = st.columns(min(10, total))
    for i, col in enumerate(thumb_cols):
        if i < total:
            with col:
                if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                    st.session_state[key_idx] = i