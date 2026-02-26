#!/usr/bin/env python3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Cargar datos
df = pd.read_csv('data/breeds.csv')

# ── Limpieza básica ──────────────────────────────────────────
def peso_promedio(valor):
    try:
        partes = str(valor).split('-')
        return sum(float(p.strip()) for p in partes) / len(partes)
    except:
        return None

def vida_promedio(valor):
    try:
        partes = str(valor).split('-')
        return sum(float(p.strip()) for p in partes) / len(partes)
    except:
        return None

df['peso_kg']   = df['peso_metrico'].apply(peso_promedio)
df['vida_anos'] = df['vida_promedio'].apply(vida_promedio)
df = df.dropna(subset=['vida_anos', 'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos'])

# ════════════════════════════════════════════════════════════
# PNG 1 — DISPERSIÓN: Energía vs Vida promedio
# ════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 7))
scatter = ax.scatter(
    df['nivel_energia'], df['vida_anos'],
    c=df['vida_anos'], cmap='YlOrRd',
    s=120, alpha=0.8, edgecolors='white'
)
for _, row in df.iterrows():
    ax.annotate(row['nombre_raza'],
                (row['nivel_energia'], row['vida_anos']),
                fontsize=7, alpha=0.8,
                textcoords="offset points", xytext=(6, 4))
plt.colorbar(scatter, label='Años de vida')
ax.set_title('Energía vs Longevidad por Raza', fontsize=14, fontweight='bold')
ax.set_xlabel('Nivel de Energía (1-5)')
ax.set_ylabel('Vida Promedio (años)')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('data/breeds_scatter.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ breeds_scatter.png guardado")

# ════════════════════════════════════════════════════════════
# PNG 2 — PASTEL: Distribución de razas por origen
# ════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 8))
conteo_origen = df['origen'].value_counts()
top8 = conteo_origen.head(8)
otros = conteo_origen.iloc[8:].sum()
if otros > 0:
    top8['Otros'] = otros
colores = plt.cm.Set3(np.linspace(0, 1, len(top8)))
ax.pie(top8.values, labels=top8.index, autopct='%1.1f%%',
       colors=colores, startangle=140, pctdistance=0.85)
ax.set_title('Distribución de Razas por País de Origen', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('data/breeds_pie.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ breeds_pie.png guardado")

# ════════════════════════════════════════════════════════════
# PNG 3 — BARRAS: Top 15 razas más longevas
# ════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 7))
top15 = df.sort_values('vida_anos', ascending=True).tail(15)
colores_barras = plt.cm.RdYlGn(np.linspace(0.3, 1, len(top15)))
ax.barh(top15['nombre_raza'], top15['vida_anos'], color=colores_barras)
ax.set_title('Top 15 Razas Más Longevas', fontsize=14, fontweight='bold')
ax.set_xlabel('Vida Promedio (años)')
ax.grid(axis='x', alpha=0.3)
for i, (val, name) in enumerate(zip(top15['vida_anos'], top15['nombre_raza'])):
    ax.text(val + 0.1, i, f'{val:.1f} años', va='center', fontsize=8)
plt.tight_layout()
plt.savefig('data/breeds_barras.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ breeds_barras.png guardado")

# ════════════════════════════════════════════════════════════
# PNG 4 — HISTOGRAMA: Distribución de vida promedio
# ════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(df['vida_anos'], bins=10, color='#4ecdc4', edgecolor='white', linewidth=0.8)
ax.axvline(df['vida_anos'].mean(), color='#ff6b6b', linestyle='--',
           linewidth=2, label=f'Promedio: {df["vida_anos"].mean():.1f} años')
ax.axvline(df['vida_anos'].median(), color='#f9a825', linestyle='--',
           linewidth=2, label=f'Mediana: {df["vida_anos"].median():.1f} años')
ax.set_title('Distribución de Vida Promedio entre Razas', fontsize=14, fontweight='bold')
ax.set_xlabel('Años de vida')
ax.set_ylabel('Cantidad de razas')
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('data/breeds_histograma.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ breeds_histograma.png guardado")

# ════════════════════════════════════════════════════════════
# PNG 5 — HEATMAP: Correlación entre características clave
# ════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 7))
columnas_heatmap = ['vida_anos', 'nivel_energia', 'inteligencia', 'adaptabilidad', 'social_humanos', 'peso_kg']
etiquetas = ['Longevidad', 'Energía', 'Inteligencia', 'Adaptabilidad', 'Social', 'Peso']
correlacion = df[columnas_heatmap].corr()
correlacion.index   = etiquetas
correlacion.columns = etiquetas
sns.heatmap(correlacion, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, square=True, linewidths=0.5,
            annot_kws={'size': 10}, ax=ax)
ax.set_title('Correlación entre Características de las Razas', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('data/breeds_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ breeds_heatmap.png guardado")

print("\n" + "="*50)
print("✅ 5 gráficas generadas en data/")
print("="*50)