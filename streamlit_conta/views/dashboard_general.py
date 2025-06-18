import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def mostrar(data=None):
    st.header("📊 Dashboard General de Contabilidad")
    st.markdown("**Resumen ejecutivo del cierre contable**")
    
    if not data:
        st.error("No hay datos disponibles")
        return
    
    # Información del cierre
    mostrar_info_cierre(data)
    
    # KPIs principales
    mostrar_kpis_principales(data)
    
    # Análisis de actividad
    mostrar_analisis_actividad(data)
    
    # Estado del procesamiento
    mostrar_estado_procesamiento(data)

def mostrar_info_cierre(data):
    """Mostrar información del cierre contable"""
    if 'cierre' not in data:
        return
    
    cierre = data['cierre']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Cliente",
            value=cierre['cliente']
        )
    
    with col2:
        st.metric(
            label="Período",
            value=cierre['periodo']
        )
    
    with col3:
        estado_color = {
            'completo': '🟢',
            'procesando': '🟡', 
            'pendiente': '🔴',
            'aprobado': '✅'
        }
        st.metric(
            label="Estado",
            value=f"{estado_color.get(cierre['estado'], '⚪')} {cierre['estado'].title()}"
        )
    
    with col4:
        st.metric(
            label="Cuentas Nuevas",
            value=cierre.get('cuentas_nuevas', 0),
            delta=f"+{cierre.get('cuentas_nuevas', 0)}"
        )

def mostrar_kpis_principales(data):
    """Mostrar KPIs financieros principales"""
    st.markdown("---")
    st.subheader("💼 KPIs Financieros Principales")
    
    if 'resumen_financiero' not in data:
        st.warning("No hay resumen financiero disponible")
        return
    
    resumen = data['resumen_financiero']
    totales = resumen['totales']
    
    # Primera fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Activos",
            value=f"${totales['total_activos']:,.0f}",
            help="Suma de activos corrientes y no corrientes"
        )
    
    with col2:
        st.metric(
            label="Total Pasivos", 
            value=f"${totales['total_pasivos']:,.0f}",
            help="Suma de pasivos corrientes y no corrientes"
        )
    
    with col3:
        st.metric(
            label="Patrimonio",
            value=f"${totales['total_patrimonio']:,.0f}",
            help="Total patrimonio"
        )
    
    with col4:
        # Calcular ratio de endeudamiento
        if totales['total_activos'] > 0:
            endeudamiento = (totales['total_pasivos'] / totales['total_activos']) * 100
        else:
            endeudamiento = 0
        st.metric(
            label="Endeudamiento",
            value=f"{endeudamiento:.1f}%",
            delta="-2.3%" if endeudamiento < 50 else "+1.2%",
            help="Pasivos / Activos"
        )
    
    # Segunda fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Ingresos Totales",
            value=f"${totales['total_ingresos']:,.0f}",
            help="Total de ingresos del período"
        )
    
    with col2:
        st.metric(
            label="Costos y Gastos",
            value=f"${totales['total_costos_gastos']:,.0f}",
            help="Total de costos y gastos"
        )
    
    with col3:
        st.metric(
            label="Resultado del Ejercicio",
            value=f"${totales['resultado_ejercicio']:,.0f}",
            delta=f"{(totales['resultado_ejercicio']/totales['total_ingresos']*100):.1f}%" if totales['total_ingresos'] > 0 else "0%",
            help="Resultado neto del período"
        )
    
    with col4:
        # Calcular margen neto
        if totales['total_ingresos'] > 0:
            margen_neto = (totales['resultado_ejercicio'] / totales['total_ingresos']) * 100
        else:
            margen_neto = 0
        st.metric(
            label="Margen Neto",
            value=f"{margen_neto:.1f}%",
            delta="+1.8%" if margen_neto > 10 else "-0.5%",
            help="Resultado / Ingresos"
        )

def mostrar_analisis_actividad(data):
    """Mostrar análisis de actividad contable"""
    st.markdown("---")
    st.subheader("📈 Análisis de Actividad Contable")
    
    if 'movimientos' not in data:
        st.warning("No hay datos de movimientos disponibles")
        return
    
    movimientos = data['movimientos']
    df_mov = pd.DataFrame(movimientos)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Movimientos por fecha
        df_mov['fecha'] = pd.to_datetime(df_mov['fecha'])
        movimientos_por_fecha = df_mov.groupby('fecha').size().reset_index()
        movimientos_por_fecha.columns = ['Fecha', 'Cantidad']
        
        fig_actividad = px.line(
            movimientos_por_fecha,
            x='Fecha',
            y='Cantidad',
            title="Movimientos Diarios",
            markers=True
        )
        fig_actividad.update_layout(xaxis_title="Fecha", yaxis_title="Cantidad de Movimientos")
        st.plotly_chart(fig_actividad, use_container_width=True)
    
    with col2:
        # Movimientos por tipo de documento
        movimientos_por_tipo = df_mov['tipo_documento'].value_counts().reset_index()
        movimientos_por_tipo.columns = ['Tipo Documento', 'Cantidad']
        
        fig_tipos = px.pie(
            movimientos_por_tipo,
            values='Cantidad',
            names='Tipo Documento',
            title="Distribución por Tipo de Documento"
        )
        st.plotly_chart(fig_tipos, use_container_width=True)
    
    # Resumen de actividad
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Movimientos",
            value=f"{len(df_mov):,}",
            help="Cantidad total de movimientos en el período"
        )
    
    with col2:
        promedio_diario = len(df_mov) / df_mov['fecha'].dt.day.nunique()
        st.metric(
            label="Promedio Diario",
            value=f"{promedio_diario:.1f}",
            help="Promedio de movimientos por día"
        )
    
    with col3:
        total_debe = df_mov['debe'].sum()
        st.metric(
            label="Total Debe",
            value=f"${total_debe:,.0f}",
            help="Suma total de débitos"
        )
    
    with col4:
        total_haber = df_mov['haber'].sum()
        st.metric(
            label="Total Haber",
            value=f"${total_haber:,.0f}",
            help="Suma total de créditos"
        )
    
    # Verificación de balance
    diferencia = abs(total_debe - total_haber)
    if diferencia < 1:
        st.success("✅ **Balance verificado:** Los débitos y créditos están balanceados")
    else:
        st.error(f"❌ **Error de balance:** Diferencia de ${diferencia:,.0f}")

def mostrar_estado_procesamiento(data):
    """Mostrar estado del procesamiento del cierre"""
    st.markdown("---")
    st.subheader("⚙️ Estado del Procesamiento")
    
    if 'cierre' not in data:
        return
    
    cierre = data['cierre']
    
    # Timeline del proceso
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Simular etapas del proceso
        etapas = [
            {"etapa": "Carga de Libros", "estado": "completado", "fecha": "2024-12-31"},
            {"etapa": "Parsing de Datos", "estado": "completado", "fecha": "2024-12-31"},
            {"etapa": "Clasificación de Cuentas", "estado": "completado", "fecha": "2025-01-02"},
            {"etapa": "Revisión de Incidencias", "estado": "completado", "fecha": "2025-01-03"},
            {"etapa": "Aprobación Final", "estado": "completado" if cierre['estado'] == 'completo' else "pendiente", "fecha": "2025-01-04"}
        ]
        
        st.markdown("#### 📋 Timeline del Proceso")
        
        for etapa in etapas:
            if etapa['estado'] == 'completado':
                st.success(f"✅ **{etapa['etapa']}** - Completado ({etapa['fecha']})")
            elif etapa['estado'] == 'pendiente':
                st.warning(f"⏳ **{etapa['etapa']}** - Pendiente")
            else:
                st.info(f"⚪ **{etapa['etapa']}** - No iniciado")
    
    with col2:
        st.markdown("#### 📊 Estadísticas del Proceso")
        
        # Simular estadísticas
        if cierre.get('parsing_completado', False):
            st.metric("Parsing", "✅ Completo")
        else:
            st.metric("Parsing", "⏳ Pendiente")
        
        st.metric("Archivos Procesados", "1", help="Libros mayores procesados")
        
        if 'plan_cuentas' in data:
            st.metric("Cuentas en Plan", f"{len(data['plan_cuentas'])}")
        
        if 'clasificaciones' in data:
            st.metric("Sets de Clasificación", f"{len(data['clasificaciones'])}")
    
    # Información adicional
    if cierre.get('fecha_inicio_libro') and cierre.get('fecha_fin_libro'):
        st.info(f"📅 **Rango de fechas del libro:** {cierre['fecha_inicio_libro']} al {cierre['fecha_fin_libro']}")
    
    # Alertas y recomendaciones
    st.markdown("#### 🔔 Alertas y Recomendaciones")
    
    alertas = []
    
    # Verificar balance
    if 'resumen_financiero' in data:
        resumen = data['resumen_financiero']
        if 'movimientos' in data:
            df_mov = pd.DataFrame(data['movimientos'])
            diferencia_balance = abs(df_mov['debe'].sum() - df_mov['haber'].sum())
            if diferencia_balance > 0:
                alertas.append(f"⚠️ Diferencia en balance: ${diferencia_balance:,.0f}")
    
    # Verificar cuentas nuevas
    if cierre.get('cuentas_nuevas', 0) > 0:
        alertas.append(f"🆕 {cierre['cuentas_nuevas']} cuentas nuevas detectadas - revisar clasificaciones")
    
    # Verificar actividad inusual
    if 'movimientos' in data and len(data['movimientos']) > 1000:
        alertas.append("📊 Alto volumen de movimientos - verificar procesamiento")
    
    if alertas:
        for alerta in alertas:
            st.warning(alerta)
    else:
        st.success("✅ No hay alertas pendientes")
    
    # Plan de cuentas y clasificaciones
    if 'plan_cuentas' in data and 'clasificaciones' in data:
        st.markdown("---")
        st.subheader("📚 Información de Configuración")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📋 Plan de Cuentas")
            df_cuentas = pd.DataFrame(data['plan_cuentas'])
            tipos_cuenta = df_cuentas['tipo'].value_counts()
            
            fig_tipos_cuenta = px.bar(
                x=tipos_cuenta.index,
                y=tipos_cuenta.values,
                title="Distribución de Tipos de Cuenta"
            )
            fig_tipos_cuenta.update_xaxes(tickangle=45)
            st.plotly_chart(fig_tipos_cuenta, use_container_width=True)
        
        with col2:
            st.markdown("##### 🏷️ Sets de Clasificación")
            clasificaciones = data['clasificaciones']
            
            for clasificacion in clasificaciones[:3]:  # Mostrar solo los primeros 3
                st.info(f"**{clasificacion['nombre']}** ({clasificacion['idioma'].upper()})")
                st.caption(f"{len(clasificacion['opciones'])} opciones disponibles")
