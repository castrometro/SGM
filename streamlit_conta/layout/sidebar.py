import streamlit as st
from data.loader_contabilidad import listar_esf_disponibles

def mostrar_sidebar():
    """ st.sidebar.image("assets/SGM_LOGO.png", width=50) """
    st.sidebar.markdown("## **Dashboard de Reportería Contable**")
    
    # Configuración de fuente de datos
    st.sidebar.markdown("### ⚙️ Configuración de Datos")
    usar_redis = st.sidebar.checkbox("🔴 Usar datos de Redis", value=True, help="Cargar datos desde Redis o usar archivo de ejemplo")
    
    cliente_id = 1
    periodo = "2025-07"
    test_type = "finalizacion_automatica"
    
    if usar_redis:
        # Opciones para Redis
        st.sidebar.markdown("**Parámetros Redis:**")
        cliente_id = st.sidebar.number_input("Cliente ID", min_value=1, value=1, step=1)
        periodo = st.sidebar.text_input("Período", value="2025-07", help="Formato: YYYY-MM")
        
        # Mostrar ESF disponibles
        try:
            esf_info = listar_esf_disponibles(cliente_id)
            if esf_info.get("esf_disponibles"):
                st.sidebar.markdown(f"**ESF disponibles ({esf_info['total_esf']}):**")
                opciones_test = [esf["test_type"] for esf in esf_info["esf_disponibles"] if esf["periodo"] == periodo]
                if opciones_test:
                    test_type = st.sidebar.selectbox("Tipo de test:", opciones_test, index=0)
                else:
                    st.sidebar.warning(f"No hay ESF para período {periodo}")
                    test_type = st.sidebar.text_input("Tipo de test:", value="finalizacion_automatica")
            else:
                st.sidebar.warning("No se encontraron ESF en Redis")
                test_type = st.sidebar.text_input("Tipo de test:", value="finalizacion_automatica")
        except Exception as e:
            st.sidebar.error(f"Error al listar ESF: {e}")
            test_type = st.sidebar.text_input("Tipo de test:", value="finalizacion_automatica")
    
    # Opción para mostrar JSON raw
    st.sidebar.markdown("---")
    mostrar_json = st.sidebar.checkbox("🔍 Mostrar JSON Raw", value=False, help="Mostrar el JSON completo en el sidebar")
    
    # Selección de reportes
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Reportes Disponibles")
    selected_tab = st.sidebar.radio("Selecciona un reporte:", [
        "📊 Dashboard General",
        "🧾 Movimientos",
        "🏛️ Estado de Situación Financiera (ESF)",
        "📈 Estado de Resultados (ESR)",
        "📊 Estado de Resultados Integral (ERI)",
        "💰 Estado de Cambio de Patrimonio (ECP)"
    ], index=0)
    
    # Información del sistema
    st.sidebar.markdown("---")
    st.sidebar.markdown("📈 *Reportes financieros y análisis contable*")
    st.sidebar.markdown(f"👤 **Cliente:** Cliente {cliente_id}")
    st.sidebar.markdown(f"📅 **Período:** {periodo}")
    
    return {
        "selected_tab": selected_tab,
        "usar_redis": usar_redis,
        "cliente_id": cliente_id,
        "periodo": periodo,
        "test_type": test_type,
        "mostrar_json": mostrar_json
    }
