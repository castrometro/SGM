import streamlit as st
from data.loader_contabilidad import cargar_datos_redis
from modules import esf, eri, ecp, resumen, movimientos, analisis, excel_tools
import os

def obtener_cliente_desde_parametros():
    """Obtener cliente_id desde parámetros de URL o session state"""
    # Verificar parámetros de query string
    query_params = st.query_params
    
    # Si hay cliente_id en URL, usarlo
    if 'cliente_id' in query_params:
        try:
            cliente_id = int(query_params['cliente_id'])
            st.session_state.cliente_id = cliente_id
            return cliente_id, True  # True indica que viene de URL
        except (ValueError, TypeError):
            # Si hay error en la conversión, retornar None
            pass
    elif 'cliente_id' in st.session_state:
        return st.session_state.cliente_id, False
    
    # Sin cliente específico
    return None, False

def mostrar_pagina_inicio():
    """Mostrar página de inicio cuando no hay cliente específico"""
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h2 style="color: #0A58CA;">¡Bienvenido al Dashboard Contable SGM!</h2>
        <p style="font-size: 18px; color: #6c757d; margin-bottom: 30px;">
            Para acceder al dashboard de un cliente específico, necesitas un enlace directo desde el sistema SGM.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Información sobre cómo acceder
    st.info("""
    📋 **¿Cómo acceder al dashboard de un cliente?**
    
    1. Ve al sistema SGM principal
    2. Navega a la sección de cierres contables
    3. Busca un cierre **finalizado**
    4. Haz clic en el botón **"Ver Dashboard Contable"**
    5. Se abrirá automáticamente este dashboard con los datos del cliente
    """)
    
    st.warning("""
    ⚠️ **Acceso directo no disponible**
    
    Este dashboard está diseñado para ser accedido desde el sistema SGM principal. 
    No es posible seleccionar un cliente manualmente desde esta interfaz.
    """)
    
    # Información técnica para desarrolladores
    with st.expander("🔧 Información técnica"):
        st.code("""
        URL de acceso: http://host:puerto/?cliente_id=123
        
        Parámetros requeridos:
        - cliente_id: ID numérico del cliente en la base de datos
        
        Ejemplo: http://172.17.11.18:8502/?cliente_id=5
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 14px;">
        <p>SGM Dashboard Contable v1.0 | Para soporte técnico contacta al administrador del sistema</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Dashboard Contable", layout="wide")

    # Limpiar cualquier contenido previo del sidebar
    st.sidebar.empty()  # Comentado por si acaso cause conflictos

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

    # Obtener cliente_id desde parámetros o session state
    cliente_id_actual, viene_de_url = obtener_cliente_desde_parametros()
    
    # Si no hay cliente específico, mostrar página de inicio
    if cliente_id_actual is None:
        mostrar_pagina_inicio()
        return
    
    # Mostrar información del cliente seleccionado si viene de parámetros
    if viene_de_url:
        st.success(f"🎯 **Cliente cargado automáticamente:** ID {cliente_id_actual}")

    # Obtener información de Redis y cierres disponibles
    try:
        from data.loader_contabilidad import obtener_info_redis_completa
        info_redis = obtener_info_redis_completa(cliente_id=cliente_id_actual)
    except:
        info_redis = {
            'ruta_redis': 'redis:6379/DB1',
            'cliente_id': cliente_id_actual,
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
    try:
        logo_path = "assets/SGM_logo.png"
        if os.path.exists(logo_path):
            # Cargar imagen como bytes para evitar problemas de path
            with open(logo_path, "rb") as f:
                logo_bytes = f.read()
            st.sidebar.image(logo_bytes, width=100)
    except Exception:
        # Si hay cualquier error con el logo, simplemente no mostrar nada
        pass

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
        ["Resumen General", "ESF", "ERI", "ECP", "Movimientos", "Análisis", "Herramientas Excel"]
    )

    # Cargar datos de Redis usando el período seleccionado y cliente actual
    data = cargar_datos_redis(cliente_id=cliente_id_actual, periodo=periodo_seleccionado)

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
        esf.show(data.get("esf"), metadata=metadata, data_eri=data.get("eri"))
    elif menu == "ERI":
        eri.show(data.get("eri"), metadata=metadata)
    elif menu == "Movimientos":
        movimientos.show(
            data_esf=data.get("esf"),
            data_eri=data.get("eri"),
            metadata=metadata,
            data_ecp=data.get("ecp")
        )
    elif menu == "ECP":  # Agregar este caso nuevo
        ecp.show(
            data_ecp=data.get("ecp"),
            metadata=metadata,
            data_eri=data.get("eri"),
            data_esf=data.get("esf")
        )
    elif menu == "Análisis":
        analisis.show(
            data_esf=data.get("esf"),
            data_eri=data.get("eri"),
            metadata=metadata
        )
    elif menu == "Herramientas Excel":
        excel_tools.show_excel_tools_section()

if __name__ == "__main__":
    main()
