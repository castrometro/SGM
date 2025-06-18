import streamlit as st

def mostrar_sidebar():
    """ st.sidebar.image("assets/SGM_LOGO.png", width=50) """
    st.sidebar.markdown("## **Dashboard de Reportería Contable**")
    selected_tab = st.sidebar.radio("Selecciona un reporte:", [
        "📊 Dashboard General",
        "🧾 Movimientos",
        "🏛️ Estado de Situación Financiera (ESF)",
        "📈 Estado de Resultados (ESR)",
        "📊 Estado de Resultados Integral (ERI)",
        "💰 Estado de Cambio de Patrimonio (ECP)"
    ], index=0)
    st.sidebar.markdown("---")
    st.sidebar.markdown("📈 *Reportes financieros y análisis contable*")
    st.sidebar.markdown("👤 **Cliente:** Empresa ABC S.A.")
    st.sidebar.markdown("📅 **Período:** Año 2024")
    return selected_tab
