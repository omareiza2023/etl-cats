#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import func
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Raza, Imagen, MetricasETL

st.set_page_config(
    page_title="Dashboard Avanzado Gatos ETL",
    page_icon="🐱",
    layout="wide"
)

st.title("🐱 Dashboard Avanzado — Análisis de Razas de Gatos")
st.markdown("---")

db = SessionLocal()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Vista General",
    "🔍 Análisis por Raza",
    "📈 Comparativas",
    "⚙️ Métricas ETL"
])

# ── Carga de datos compartida ─────────────────────────────────
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
            'fecha_extraccion': r.fecha_extraccion,
        } for r in razas])

        df_img = pd.DataFrame([{
            'raza_id': img.raza_id,
            'url':     img.url,
        } for img in imagenes])

        return df, df_img
    finally:
        session.close()

df, df_img = cargar_datos()

if df.empty:
    st.warning("⚠️ No hay datos en la base de datos. Ejecuta el extractor y el loader primero.")
    st.stop()

# ════════════════════════════════════════════════════════════
# PESTAÑA 1 — Vista General
# ════════════════════════════════════════════════════════════
with tab1:
    st.subheader("📊 Vista General")

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_razas = db.query(func.count(Raza.id)).scalar()
        st.metric("🐱 Total Razas", total_razas)

    with col2:
        total_imagenes = db.query(func.count(Imagen.id)).scalar()
        st.metric("🖼️ Total Imágenes", total_imagenes)

    with col3:
        vida_prom = df['vida_anos'].mean()
        st.metric("📅 Longevidad Promedio", f"{vida_prom:.1f} años")

    with col4:
        ultima = db.query(func.max(Raza.fecha_extraccion)).scalar()
        st.metric("⏰ Última Extracción", ultima.strftime("%Y-%m-%d %H:%M") if ultima else "N/A")

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Barras: Top 15 razas más longevas
    with col1:
        top15 = df.dropna(subset=['vida_anos']).nlargest(15, 'vida_anos').sort_values('vida_anos')
        fig = px.bar(
            top15,
            x='vida_anos', y='nombre_raza',
            orientation='h',
            title="🏆 Top 15 Razas Más Longevas",
            color='vida_anos',
            color_continuous_scale='RdYlGn',
            labels={'vida_anos': 'Años de vida', 'nombre_raza': 'Raza'}
        )
        fig.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    # Pastel: Distribución por origen
    with col2:
        conteo = df['origen'].value_counts().reset_index()
        conteo.columns = ['origen', 'cantidad']
        top8 = conteo.head(8).copy()
        otros = conteo.iloc[8:]['cantidad'].sum()
        if otros > 0:
            top8 = pd.concat([top8, pd.DataFrame([{'origen': 'Otros', 'cantidad': otros}])], ignore_index=True)

        fig = px.pie(
            top8, names='origen', values='cantidad',
            title="🌍 Distribución por País de Origen",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabla resumen
    st.subheader("📋 Tabla de Razas")
    st.dataframe(
        df[['nombre_raza', 'origen', 'vida_anos', 'peso_kg',
            'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos']]
        .sort_values('vida_anos', ascending=False)
        .rename(columns={
            'nombre_raza':    'Raza',
            'origen':         'Origen',
            'vida_anos':      'Vida (años)',
            'peso_kg':        'Peso (kg)',
            'nivel_energia':  'Energía',
            'inteligencia':   'Inteligencia',
            'adaptabilidad':  'Adaptabilidad',
            'social_humanos': 'Social',
        }),
        use_container_width=True,
        height=400
    )

# ════════════════════════════════════════════════════════════
# PESTAÑA 2 — Análisis por Raza
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🔍 Análisis Detallado por Raza")

    raza_sel = st.selectbox(
        "Selecciona una raza:",
        options=sorted(df['nombre_raza'].unique())
    )

    if raza_sel:
        raza_data = df[df['nombre_raza'] == raza_sel].iloc[0]

        col1, col2 = st.columns([1, 2])

        # Ficha de la raza
        with col1:
            st.markdown(f"### 🐱 {raza_data['nombre_raza']}")
            st.markdown(f"**🌍 Origen:** {raza_data['origen']}")
            st.markdown(f"**📅 Vida promedio:** {raza_data['vida_promedio']}")
            st.markdown(f"**⚖️ Peso:** {raza_data['peso_metrico']} kg")
            st.markdown(f"**😸 Temperamento:** {raza_data['temperamento']}")
            if raza_data['wikipedia_url']:
                st.markdown(f"[📖 Ver en Wikipedia]({raza_data['wikipedia_url']})")

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("⚡ Energía",       f"{raza_data['nivel_energia']} / 5")
                st.metric("🧠 Inteligencia",  f"{raza_data['inteligencia']} / 5")
            with col_b:
                st.metric("🔄 Adaptabilidad", f"{raza_data['adaptabilidad']} / 5")
                st.metric("🤝 Social",         f"{raza_data['social_humanos']} / 5")

        # Radar chart de atributos
        with col2:
            categorias   = ['Energía', 'Inteligencia', 'Adaptabilidad', 'Social']
            valores_raza = [
                raza_data['nivel_energia']  or 0,
                raza_data['inteligencia']   or 0,
                raza_data['adaptabilidad']  or 0,
                raza_data['social_humanos'] or 0,
            ]
            # Cerrar el polígono
            categorias_cierre = categorias + [categorias[0]]
            valores_cierre    = valores_raza + [valores_raza[0]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=valores_cierre,
                theta=categorias_cierre,
                fill='toself',
                name=raza_data['nombre_raza'],
                line_color='#636EFA'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                title=f"Perfil de {raza_data['nombre_raza']}",
                showlegend=False
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Galería de imágenes
        st.markdown("---")
        st.markdown("### 🖼️ Imágenes")
        urls = df_img[df_img['raza_id'] == raza_data['id']]['url'].tolist()
        if urls:
            cols = st.columns(min(len(urls), 4))
            for i, url in enumerate(urls[:4]):
                with cols[i % 4]:
                    st.image(url, use_column_width=True)
        else:
            st.info("No hay imágenes disponibles para esta raza.")

# ════════════════════════════════════════════════════════════
# PESTAÑA 3 — Comparativas
# ════════════════════════════════════════════════════════════
with tab3:
    st.subheader("📈 Comparativas entre Razas")

    # Filtro por origen
    origenes = sorted(df['origen'].unique())
    origenes_sel = st.multiselect(
        "🌍 Filtrar por origen:",
        options=origenes,
        default=origenes[:5] if len(origenes) >= 5 else origenes
    )

    df_comp = df[df['origen'].isin(origenes_sel)].dropna(subset=['vida_anos'])

    col1, col2 = st.columns(2)

    # Dispersión: Energía vs Longevidad
    with col1:
        fig = px.scatter(
            df_comp.dropna(subset=['nivel_energia']),
            x='nivel_energia', y='vida_anos',
            color='origen', size='peso_kg',
            hover_name='nombre_raza',
            hover_data=['temperamento'],
            title="⚡ Energía vs Longevidad",
            labels={'nivel_energia': 'Nivel de Energía (1-5)', 'vida_anos': 'Vida (años)'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Heatmap de correlaciones
    with col2:
        cols_corr   = ['vida_anos', 'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos', 'peso_kg']
        etiquetas   = ['Longevidad', 'Energía', 'Inteligencia', 'Adaptabilidad', 'Social', 'Peso']
        df_corr     = df_comp[cols_corr].dropna().corr()
        df_corr.index   = etiquetas
        df_corr.columns = etiquetas

        fig = go.Figure(data=go.Heatmap(
            z=df_corr.values,
            x=etiquetas, y=etiquetas,
            colorscale='RdBu', zmid=0,
            text=df_corr.round(2).values,
            texttemplate='%{text}',
            textfont={'size': 11}
        ))
        fig.update_layout(title="🔥 Correlación entre Características")
        st.plotly_chart(fig, use_container_width=True)

    # Comparación directa entre dos razas
    st.markdown("---")
    st.subheader("⚖️ Comparar dos Razas")

    col1, col2 = st.columns(2)
    with col1:
        raza_a = st.selectbox("Raza A:", options=sorted(df['nombre_raza'].unique()), key='raza_a')
    with col2:
        raza_b = st.selectbox("Raza B:", options=sorted(df['nombre_raza'].unique()), index=1, key='raza_b')

    if raza_a and raza_b:
        da = df[df['nombre_raza'] == raza_a].iloc[0]
        db_row = df[df['nombre_raza'] == raza_b].iloc[0]

        atributos = ['Energía', 'Inteligencia', 'Adaptabilidad', 'Social']
        vals_a    = [da['nivel_energia'] or 0, da['inteligencia'] or 0,
                     da['adaptabilidad'] or 0, da['social_humanos'] or 0]
        vals_b    = [db_row['nivel_energia'] or 0, db_row['inteligencia'] or 0,
                     db_row['adaptabilidad'] or 0, db_row['social_humanos'] or 0]

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(name=raza_a, x=atributos, y=vals_a, marker_color='#636EFA'))
        fig_comp.add_trace(go.Bar(name=raza_b, x=atributos, y=vals_b, marker_color='#EF553B'))
        fig_comp.update_layout(
            barmode='group',
            title=f"Comparación: {raza_a} vs {raza_b}",
            yaxis=dict(range=[0, 5]),
            legend_title="Raza"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

# ════════════════════════════════════════════════════════════
# PESTAÑA 4 — Métricas ETL
# ════════════════════════════════════════════════════════════
with tab4:
    st.subheader("⚙️ Métricas de Ejecución ETL")

    metricas = db.query(MetricasETL).order_by(
        MetricasETL.fecha_ejecucion.desc()
    ).limit(20).all()

    if metricas:
        data_m = [{
            'Fecha':       m.fecha_ejecucion,
            'Estado':      m.estado,
            'Extraídos':   m.registros_extraidos,
            'Guardados':   m.registros_guardados,
            'Fallidos':    m.registros_fallidos,
            'Tiempo (s)':  round(m.tiempo_ejecucion_segundos, 2)
        } for m in metricas]

        df_m = pd.DataFrame(data_m)

        # Métricas resumen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Ejecuciones Exitosas", len(df_m[df_m['Estado'] == 'exitoso']))
        with col2:
            st.metric("❌ Ejecuciones Fallidas", len(df_m[df_m['Estado'] == 'fallido']))
        with col3:
            st.metric("⏱️ Tiempo Promedio", f"{df_m['Tiempo (s)'].mean():.2f} s")

        st.markdown("---")
        st.dataframe(df_m, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df_m, x='Fecha', y='Guardados',
                title='Registros Guardados por Ejecución',
                color='Estado',
                color_discrete_map={'exitoso': '#00CC96', 'fallido': '#EF553B'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                df_m, x='Fecha', y='Tiempo (s)',
                size='Guardados', color='Estado',
                title='Duración de Ejecuciones',
                color_discrete_map={'exitoso': '#00CC96', 'fallido': '#EF553B'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay métricas registradas aún. Las métricas se registran automáticamente al ejecutar el loader.")

db.close()