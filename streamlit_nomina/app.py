import streamlit as st
from layout.sidebar import mostrar_sidebar
from layout.header import mostrar_header
from data.loader import cargar_datos
from data.loader_nomina import cargar_datos_redis, obtener_info_redis_completa, cargar_informe_local
from views import dashboard_general
from views import dashboard_informe_compacto

st.set_page_config(layout="wide", page_title="SGM - Dashboard Nómina", page_icon="💼")

if st.session_state.get('scroll_to_top', False):
    st.session_state.scroll_to_top = False
    top_placeholder = st.empty()
    top_placeholder.markdown("")

# Sidebar con selección de fuente de datos
selected_tab, selected_config = mostrar_sidebar()

# Determinar qué datos cargar según la configuración
if selected_config and selected_config.get('fuente') == 'redis':
    # Cargar desde Redis
    cliente_id = selected_config.get('cliente_id', 6)
    periodo = selected_config.get('periodo', '2025-03')
    
    # Mostrar información de Redis
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"📡 **Fuente:** Redis DB2 | **Cliente:** {cliente_id} | **Período:** {periodo}")
    with col2:
        if st.button("🔄 Recargar desde Redis"):
            st.session_state.pop('data', None)
            st.rerun()
    
    # Cargar datos desde Redis
    if 'data' not in st.session_state or st.session_state.get('last_config') != selected_config:
        with st.spinner(f"🔍 Cargando datos desde Redis..."):
            data = cargar_datos_redis(cliente_id=cliente_id, periodo=periodo)
            if data:
                st.session_state.data = data
                st.session_state.last_config = selected_config
                st.success(f"✅ Datos cargados desde Redis: {data.get('cliente_nombre')} - {periodo}")
            else:
                st.error(f"❌ No se encontraron datos en Redis para cliente {cliente_id}, período {periodo}")
                st.info("💡 **Posibles soluciones:**\n- Verifica que el cierre esté finalizado\n- Confirma que los datos estén en Redis DB2")
                st.stop()
    else:
        data = st.session_state.data
else:
    # Cargar desde archivos locales. Intentar informe compacto primero.
    if 'data' in st.session_state and st.session_state.get('last_config') == selected_config:
        data = st.session_state.data
    else:
        archivo_actual = None
        if selected_config and selected_config.get('fuente') == 'archivos':
            archivo_actual = selected_config.get('archivo_actual')
        datos_informe = cargar_informe_local(nombre=archivo_actual)
        if datos_informe:
            data = datos_informe
        else:
            # fallback legacy a loader original
            data = cargar_datos(archivo_actual)
        st.session_state.data = data
        st.session_state.last_config = selected_config

if not data:
    st.error("🚨 No se pudieron cargar los datos")
    st.stop()

mostrar_header(data)

if selected_tab == "📊 Dashboard General":
    # Si la estructura es la compacta (nueva), usar el nuevo dashboard
    if isinstance(data, dict) and ('totales_libro' in data or 'totales_movimientos' in data):
        dashboard_informe_compacto.mostrar(data)
    else:
        dashboard_general.mostrar(data)
elif selected_tab == "📈 Análisis Financiero":
    st.header("📈 Análisis Financiero")
    st.info("🚧 Esta sección está en desarrollo. Mostrará análisis financiero detallado del período seleccionado.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Análisis de Costos")
        st.write("Aquí se mostrará el análisis detallado de costos por categoría")
    
    with col2:
        st.subheader("Tendencias Financieras")
        st.write("Aquí se mostrarán las tendencias financieras del período")
        
elif selected_tab == "📋 Comparación Histórica":
    st.header("📋 Comparación Histórica")
    st.info("🚧 Esta sección está en desarrollo. Mostrará comparaciones entre períodos históricos.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Comparación de Períodos")
        st.write("Aquí se mostrará la comparación entre períodos")
    
    with col2:
        st.subheader("Evolución de Indicadores")
        st.write("Aquí se mostrará la evolución de indicadores clave")
else:
    st.info(f"Pestaña seleccionada: {selected_tab}")
    
with st.expander("🔧 Info de Debug"):
    st.write(f"**Pestaña seleccionada:** {selected_tab}")
    st.write(f"**Datos disponibles:** {len(data) if data else 0} elementos")
    st.write(f"**Cliente:** {data.get('cliente_nombre', 'N/A') if data else 'N/A'}")
    st.write(f"**Archivo:** {st.session_state.get('archivo_seleccionado', 'N/A')}")
