import streamlit as st

def mostrar_sidebar():
    """ st.sidebar.image("assets/SGM_LOGO.png", width=50) """
    st.sidebar.markdown("## **Panel de Navegación SGM**")
    selected_tab = st.sidebar.radio("Selecciona una vista:", [
        "Resumen General",
        "Rentabilidad",
        "Volumen de Ingresos"
    ], index=0)
    st.sidebar.markdown("---")
    st.sidebar.markdown("📊 *Dashboard generado automáticamente a partir de los datos.*")
    return selected_tab
