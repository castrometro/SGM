import streamlit as st
from layout.sidebar import mostrar_sidebar
from layout.header import mostrar_header
from data.loader import cargar_datos
from views import dashboard_general

st.set_page_config(layout="wide", page_title="SGM - Dashboard Nómina", page_icon="💼")

if st.session_state.get('scroll_to_top', False):
    st.session_state.scroll_to_top = False
    top_placeholder = st.empty()
    top_placeholder.markdown("")

selected_tab = mostrar_sidebar()

if 'data' in st.session_state:
    data = st.session_state.data
else:
    data = cargar_datos()

if not data:
    st.error("🚨 No se pudieron cargar los datos")
    st.stop()

mostrar_header(data)

if selected_tab == "📊 Dashboard General":
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
