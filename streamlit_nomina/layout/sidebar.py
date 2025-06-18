import streamlit as st


def mostrar_sidebar():
    st.sidebar.markdown("## **Dashboard de Nómina**")
    selected_tab = st.sidebar.radio(
        "Selecciona un reporte:",
        ["📊 Dashboard General"],
        index=0
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("💼 *Análisis de remuneraciones*")
    st.sidebar.markdown("👤 **Cliente:** Compañía XYZ")
    st.sidebar.markdown("📅 **Período:** 2024")
    return selected_tab
