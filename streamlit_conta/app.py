import streamlit as st
from data.loader_contabilidad import cargar_datos_redis
from pages import esf, eri, resumen, movimientos, analisis
import os

def main():
    st.set_page_config(page_title="Dashboard Contable", layout="wide")

    # Header
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("assets/SGM_logo.png", width=50)
    with col2:
        st.markdown(
            "<h1 style='color:#0A58CA; margin-bottom: 0;'>SGM - Dashboard Contable</h1>"
            "<p style='color: #6c757d; margin-top: 0;'>Gestión contable y reportería</p>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Sidebar - Logo
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "SGM_logo.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=100)
    else:
        st.sidebar.warning("Logo no encontrado en 'assets/SGM_logo.png'")

    st.sidebar.title("SGM Dashboard")

    # Sidebar - Idioma
    idioma = st.sidebar.radio(
        "Selecciona idioma del informe:",
        options=["Español", "English"],
        index=0
    )

    # Guardar idioma en session_state
    if idioma == "Español":
        st.session_state.lang_field = "nombre_es"
    else:
        st.session_state.lang_field = "nombre_en"

    # Sidebar - Navegación
    menu = st.sidebar.radio(
        "Navegación",
        ["Resumen General", "ESF", "ERI", "Movimientos", "Análisis"]
    )

    # Cargar datos de Redis o archivo de ejemplo
    data = cargar_datos_redis(cliente_id=2, periodo="2025-03")

    metadata = {
        "cliente_nombre": data.get("cliente", {}).get("nombre"),
        "periodo": data.get("cierre", {}).get("periodo"),
        "moneda": data.get("esf", {}).get("metadata", {}).get("moneda", "CLP"),
        "idioma": idioma
    }

    # Mostrar página elegida
    if menu == "Resumen General":
        resumen.show(data_esf=data.get("esf"), data_eri=data.get("eri"), metadata=metadata)
    elif menu == "ESF":
        esf.show(data.get("esf"), metadata=metadata)
    elif menu == "ERI":
        eri.show(data.get("eri"), metadata=metadata)
    elif menu == "Movimientos":
        movimientos.show(
            data_esf=data.get("esf"),
            data_eri=data.get("eri"),
            metadata=metadata
        )
    elif menu == "Análisis":
        analisis.show(
            data_esf=data.get("esf"),
            data_eri=data.get("eri"),
            metadata=metadata
        )

if __name__ == "__main__":
    main()
