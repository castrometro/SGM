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

    # Obtener información de Redis y cierres disponibles
    try:
        from data.loader_contabilidad import obtener_info_redis_completa
        info_redis = obtener_info_redis_completa()
    except:
        info_redis = {
            'ruta_redis': 'redis:6379/DB1',
            'cliente_id': 2,
            'cierres_disponibles': [],
            'error': 'Error conectando'
        }

    # Información del sistema y selector
    col1_info, col2_info, col3_info, col4_selector = st.columns([2, 2, 3, 3])
    
    with col1_info:
        st.info(f"🔗 **Ruta Redis:**\n{info_redis.get('ruta_redis', 'N/A')}")
    
    with col2_info:
        st.info(f"👤 **Cliente ID:**\n{info_redis.get('cliente_id', 'N/A')}")
    
    with col3_info:
        cierres = info_redis.get('cierres_disponibles', [])
        if cierres:
            cierres_str = "\n".join([f"• {c}" for c in cierres[:3]])
            if len(cierres) > 3:
                cierres_str += f"\n... y {len(cierres)-3} más"
            st.success(f"📊 **Cierres disponibles:**\n{cierres_str}")
        else:
            st.warning("📊 **Sin cierres disponibles**")
    
    with col4_selector:
        if cierres:
            periodo_seleccionado = st.selectbox(
                "🎯 **Seleccionar cierre:**",
                options=cierres,
                index=0
            )
        else:
            periodo_seleccionado = "2025-03"  # fallback
            st.warning("🎯 **Sin cierres para seleccionar**")

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

    # Cargar datos de Redis usando el período seleccionado
    data = cargar_datos_redis(cliente_id=info_redis.get('cliente_id', 2), periodo=periodo_seleccionado)

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
