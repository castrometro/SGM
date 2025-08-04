import streamlit as st
from data.loader_nomina import cargar_datos_redis, obtener_info_redis_completa
from modules import dashboard_ejecutivo, analisis_financiero, analisis_personal, datos_detallados
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
        <h2 style="color: #0A58CA;">¡Bienvenido al Dashboard de Nómina SGM!</h2>
        <p style="font-size: 18px; color: #6c757d; margin-bottom: 30px;">
            Para acceder al dashboard de un cliente específico, necesitas un enlace directo desde el sistema SGM.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Información sobre cómo acceder
    st.info("""
    📋 **¿Cómo acceder al dashboard de un cliente?**
    
    1. Ve al sistema SGM principal
    2. Navega a la sección de cierres de nómina
    3. Busca un cierre **finalizado**
    4. Haz clic en el botón **"Ver Dashboard de Nómina"**
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
        
        Ejemplo: http://172.17.11.18:8503/?cliente_id=5
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 14px;">
                <p>SGM Dashboard Nómina v1.0 | Para soporte técnico contacta al administrador del sistema</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Dashboard Nómina", layout="wide")

    # Limpiar cualquier contenido previo del sidebar
    st.sidebar.empty()

    # Header
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("assets/SGM_logo.png", width=50)
    with col2:
        st.markdown(
            "<h1 style='color:#0A58CA; margin-bottom: 0;'>SGM - Dashboard Nómina</h1>"
            "<p style='color: #6c757d; margin-top: 0;'>Gestión de nómina y reportería</p>",
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
        info_redis = obtener_info_redis_completa(cliente_id=cliente_id_actual)
    except:
        info_redis = {
            'ruta_redis': 'redis:6379/DB2',
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
        error_info = info_redis.get('error', None)
        
        if cierres:
            # Manejar si cierres son strings o diccionarios
            if cierres and isinstance(cierres[0], dict):
                # Si son diccionarios, extraer solo los períodos para mostrar
                periodos_mostrar = [c.get('periodo', str(c)) for c in cierres[:3]]
            else:
                # Si ya son strings, usarlos directamente
                periodos_mostrar = cierres[:3]
            
            cierres_str = "\n".join([f"• {p}" for p in periodos_mostrar])
            if len(cierres) > 3:
                cierres_str += f"\n... y {len(cierres)-3} más"
            st.success(f"📊 **Cierres disponibles:**\n{cierres_str}")
        else:
            # Mostrar mensaje específico según el error
            if error_info:
                st.error(f"📊 **{error_info}**")
            else:
                st.warning(f"📊 **No se encontraron cierres para el cliente {cliente_id_actual}**")
    
    with col4_selector:
        if cierres:
            # Preparar opciones para el selectbox
            if cierres and isinstance(cierres[0], dict):
                # Si son diccionarios, crear opciones legibles pero mantener referencias
                opciones_selectbox = []
                mapeo_opciones = {}
                
                for cierre in cierres:
                    periodo = cierre.get('periodo', 'N/A')
                    cliente_nombre = cierre.get('cliente_nombre', 'N/A')
                    fecha_gen = cierre.get('fecha_generacion', '')
                    
                    # Crear etiqueta legible
                    if fecha_gen:
                        try:
                            from datetime import datetime
                            fecha_obj = datetime.fromisoformat(fecha_gen.replace('Z', '+00:00'))
                            fecha_corta = fecha_obj.strftime('%d/%m/%Y')
                            etiqueta = f"{periodo} ({fecha_corta})"
                        except:
                            etiqueta = periodo
                    else:
                        etiqueta = periodo
                    
                    opciones_selectbox.append(etiqueta)
                    mapeo_opciones[etiqueta] = periodo  # Solo guardar el período como string
                
                opcion_seleccionada = st.selectbox(
                    "🎯 **Seleccionar cierre:**",
                    options=opciones_selectbox,
                    index=0
                )
                
                # Obtener el período real
                periodo_seleccionado = mapeo_opciones.get(opcion_seleccionada, "2025-03")
            else:
                # Si ya son strings, usarlos directamente
                periodo_seleccionado = st.selectbox(
                    "🎯 **Seleccionar cierre:**",
                    options=cierres,
                    index=0
                )
        else:
            periodo_seleccionado = "2025-03"  # fallback
            error_info = info_redis.get('error', None)
            if error_info:
                st.error(f"🎯 **{error_info}**")
            else:
                st.warning(f"🎯 **No se encontraron cierres para el cliente {cliente_id_actual}**")

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

    st.sidebar.title("SGM Dashboard Nómina")

    # Sidebar - Navegación
    menu = st.sidebar.radio(
        "Navegación",
        ["Dashboard Ejecutivo", "Análisis Financiero", "Análisis Personal", "Datos Detallados"]
    )

    # Cargar datos de Redis usando el período seleccionado y cliente actual
    data = cargar_datos_redis(cliente_id=cliente_id_actual, periodo=periodo_seleccionado)

    # Verificar si se pudieron cargar los datos
    if data is None:
        st.error(f"❌ **No se pudieron cargar los datos para el cliente {cliente_id_actual} en el período {periodo_seleccionado}**")
        st.info("""
        **Posibles causas:**
        - El cliente no tiene informes de nómina disponibles
        - Error de conexión con Redis
        - Los datos no están completos
        
        **Solución:** Verifica que el cierre esté finalizado y que los datos estén disponibles en Redis DB2.
        """)
    else:
        # Solo proceder si los datos se cargaron correctamente
        metadata = {
            "cliente_nombre": data.get("metadatos", {}).get("cliente"),
            "periodo": data.get("metadatos", {}).get("periodo"),
            "fecha_generacion": data.get("metadatos", {}).get("fecha_calculo")
        }

        # Mostrar página elegida
        if menu == "Dashboard Ejecutivo":
            dashboard_ejecutivo.show(data, metadata)
        elif menu == "Análisis Financiero":
            analisis_financiero.show(data, metadata)
        elif menu == "Análisis Personal":
            analisis_personal.show(data, metadata)
        elif menu == "Datos Detallados":
            datos_detallados.show(data, metadata)

if __name__ == "__main__":
    main()
