import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pathlib
from datetime import datetime

def mostrar(data=None):
    """Mostrar vista del Estado de Resultados"""
    st.header("📈 Estado de Resultados (ESR)")
    st.markdown("**Análisis de ingresos, gastos y resultados del período**")
    
    if not data:
        st.warning("No hay datos disponibles para mostrar el Estado de Resultados")
        return
    
    # Información del período
    mostrar_info_periodo(data)
    
    # KPIs de resultados
    mostrar_kpis_resultados(data)
    
    # Análisis de ingresos y gastos
    mostrar_analisis_ingresos_gastos(data)
    
    # Gráficos de resultados
    mostrar_graficos_resultados(data)

def mostrar_info_periodo(data):
    """Mostrar información del período analizado"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Período", "2024-12")
    
    with col2:
        empresa = data.get("cierre", {}).get("cliente", "N/A")
        st.metric("Empresa", empresa)
    
    with col3:
        st.metric("Estado", "Procesado")

def mostrar_kpis_resultados(data):
    """Mostrar KPIs principales del estado de resultados"""
    st.subheader("📊 Indicadores Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Ingresos Totales",
            value="$ 0",
            delta="0%"
        )
    
    with col2:
        st.metric(
            label="Gastos Totales", 
            value="$ 0",
            delta="0%"
        )
    
    with col3:
        st.metric(
            label="Resultado Operacional",
            value="$ 0",
            delta="0%"
        )
    
    with col4:
        st.metric(
            label="Resultado Neto",
            value="$ 0",
            delta="0%"
        )

def mostrar_analisis_ingresos_gastos(data):
    """Mostrar análisis detallado de ingresos y gastos"""
    st.subheader("💰 Análisis de Ingresos y Gastos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ingresos")
        if 'movimientos' in data:
            # Aquí se analizarían los movimientos de ingresos
            st.info("Análisis de ingresos por implementar")
        else:
            st.warning("No hay datos de movimientos disponibles")
    
    with col2:
        st.subheader("Gastos")
        if 'movimientos' in data:
            # Aquí se analizarían los movimientos de gastos
            st.info("Análisis de gastos por implementar")
        else:
            st.warning("No hay datos de movimientos disponibles")

def mostrar_graficos_resultados(data):
    """Mostrar gráficos del estado de resultados"""
    st.subheader("📈 Visualizaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Evolución de Resultados")
        # Crear gráfico de ejemplo
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
            y=[100, 120, 110, 130, 125, 140],
            mode='lines+markers',
            name='Resultado Mensual'
        ))
        fig.update_layout(
            title="Evolución del Resultado",
            xaxis_title="Mes",
            yaxis_title="Resultado ($)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Composición de Ingresos")
        # Crear gráfico de pie de ejemplo
        fig = px.pie(
            values=[40, 30, 20, 10],
            names=['Ventas', 'Servicios', 'Otros ingresos', 'Financieros'],
            title="Distribución de Ingresos"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def cargar_datos_esr():
    """Cargar datos específicos del Estado de Resultados"""
    try:
        current_dir = pathlib.Path(__file__).parent.parent.resolve()
        # Intentar cargar archivo específico del ESR si existe
        excel_path = current_dir / "data" / "ESR-Example.xlsx"
        
        if excel_path.exists():
            excel_data = pd.read_excel(excel_path, sheet_name=None, header=None)
            return excel_data
        else:
            return None
    except Exception as e:
        st.error(f"Error al cargar datos del ESR: {str(e)}")
        return None
