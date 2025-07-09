"""
Componentes visuales modernos para el dashboard de contabilidad
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def crear_card_metrica(titulo, valor, subtitulo=None, color="primary", icono=None):
    """Crear una card moderna para mostrar métricas"""
    
    color_map = {
        "primary": "#1f77b4",
        "success": "#2ca02c", 
        "warning": "#ff7f0e",
        "danger": "#d62728",
        "info": "#17a2b8"
    }
    
    color_hex = color_map.get(color, "#1f77b4")
    
    card_html = f"""
    <div style="
        background: linear-gradient(135deg, {color_hex}15 0%, {color_hex}05 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid {color_hex}30;
        border-left: 4px solid {color_hex};
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            {f'<span style="font-size: 1.2rem; margin-right: 0.5rem;">{icono}</span>' if icono else ''}
            <h3 style="margin: 0; color: {color_hex}; font-size: 0.9rem; font-weight: 600; text-transform: uppercase;">
                {titulo}
            </h3>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: #2c3e50; margin: 0.5rem 0;">
            {valor}
        </div>
        {f'<div style="font-size: 0.8rem; color: #6c757d;">{subtitulo}</div>' if subtitulo else ''}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def crear_grafico_barras_horizontal(data, titulo, color_scheme="viridis"):
    """Crear gráfico de barras horizontal moderno"""
    
    if not data or len(data) == 0:
        st.warning("No hay datos para mostrar")
        return None
        
    fig = go.Figure()
    
    # Preparar datos
    labels = list(data.keys())
    values = list(data.values())
    
    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation='h',
        marker=dict(
            color=values,
            colorscale=color_scheme,
            line=dict(color='rgba(50, 171, 96, 0.6)', width=1)
        ),
        text=[f"${v:,.0f}" for v in values],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Valor: $%{x:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,
            font=dict(size=16, color='#2c3e50')
        ),
        xaxis=dict(
            title="Valor ($)",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        yaxis=dict(
            title="",
            categoryorder='total ascending'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def crear_grafico_pastel(data, titulo, color_scheme=None):
    """Crear gráfico de pastel moderno"""
    
    if not data or len(data) == 0:
        st.warning("No hay datos para mostrar")
        return None
    
    labels = list(data.keys())
    values = list(data.values())
    
    # Colores personalizados para contabilidad
    colors = color_scheme or [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(
            colors=colors[:len(labels)],
            line=dict(color='#FFFFFF', width=2)
        ),
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>Valor: $%{value:,.0f}<br>Porcentaje: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,
            font=dict(size=16, color='#2c3e50')
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )
    
    return fig

def crear_tabla_moderna(df, titulo=None, max_height=400):
    """Crear tabla moderna con estilos"""
    
    if titulo:
        st.subheader(titulo)
    
    # Aplicar estilos a la tabla
    styled_df = df.style.format({
        col: "${:,.0f}" for col in df.columns if df[col].dtype in ['int64', 'float64']
    }).set_table_styles([
        {
            'selector': 'thead th',
            'props': [
                ('background-color', '#f8f9fa'),
                ('color', '#2c3e50'),
                ('font-weight', 'bold'),
                ('text-align', 'center'),
                ('border-bottom', '2px solid #dee2e6')
            ]
        },
        {
            'selector': 'tbody td',
            'props': [
                ('text-align', 'right'),
                ('padding', '8px 12px'),
                ('border-bottom', '1px solid #dee2e6')
            ]
        },
        {
            'selector': 'tbody tr:nth-child(even)',
            'props': [('background-color', '#f8f9fa')]
        },
        {
            'selector': 'tbody tr:hover',
            'props': [('background-color', '#e3f2fd')]
        }
    ])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=max_height
    )

def crear_indicadores_financieros(activos, pasivos, patrimonio):
    """Crear panel de indicadores financieros clave"""
    
    st.subheader("📈 Indicadores Financieros Clave")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Ratio de liquidez (asumiendo estructura básica)
    with col1:
        if pasivos > 0:
            ratio_endeudamiento = pasivos / activos * 100
            crear_card_metrica(
                "Ratio Endeudamiento",
                f"{ratio_endeudamiento:.1f}%",
                "Pasivos / Activos",
                color="warning" if ratio_endeudamiento > 60 else "success",
                icono="📊"
            )
        else:
            crear_card_metrica("Ratio Endeudamiento", "0%", "Sin deudas", color="success", icono="📊")
    
    # Participación del patrimonio
    with col2:
        if activos > 0:
            participacion_patrimonio = patrimonio / activos * 100
            crear_card_metrica(
                "Participación Patrimonio",
                f"{participacion_patrimonio:.1f}%",
                "Patrimonio / Activos",
                color="success" if participacion_patrimonio > 40 else "warning",
                icono="🏛️"
            )
    
    # Solidez financiera
    with col3:
        if pasivos > 0:
            solidez = patrimonio / pasivos
            crear_card_metrica(
                "Solidez Financiera",
                f"{solidez:.2f}",
                "Patrimonio / Pasivos",
                color="success" if solidez > 1 else "danger",
                icono="🛡️"
            )
        else:
            crear_card_metrica("Solidez Financiera", "∞", "Sin pasivos", color="success", icono="🛡️")
    
    # Balance verificación
    with col4:
        balance_ok = abs(activos - (pasivos + patrimonio)) < 1
        crear_card_metrica(
            "Balance",
            "✅ OK" if balance_ok else "❌ Error",
            "A = P + Pat",
            color="success" if balance_ok else "danger",
            icono="⚖️"
        )

def crear_resumen_ejecutivo(data):
    """Crear panel de resumen ejecutivo"""
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <h2 style="margin: 0 0 1rem 0; font-weight: 300;">📊 Resumen Ejecutivo</h2>
        <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">
            Vista general de la situación financiera actual
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not data or 'esf' not in data:
        st.warning("No hay datos de Estado de Situación Financiera disponibles")
        return
    
    esf = data['esf']
    
    # Extraer totales principales
    activos = esf.get('total_activos', 0)
    pasivos = esf.get('total_pasivos', 0) 
    patrimonio = esf.get('total_patrimonio', 0)
    
    # Panel de métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        crear_card_metrica(
            "Total Activos",
            f"${activos:,.0f}",
            "Recursos totales",
            color="primary",
            icono="💰"
        )
    
    with col2:
        crear_card_metrica(
            "Total Pasivos", 
            f"${pasivos:,.0f}",
            "Obligaciones totales",
            color="warning",
            icono="📋"
        )
    
    with col3:
        crear_card_metrica(
            "Patrimonio",
            f"${patrimonio:,.0f}",
            "Capital propio",
            color="success",
            icono="🏛️"
        )
    
    # Indicadores financieros
    crear_indicadores_financieros(activos, pasivos, patrimonio)
