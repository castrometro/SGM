import streamlit as st
import json
from layout.sidebar import mostrar_sidebar
from layout.header import mostrar_header
from data.loader_contabilidad import cargar_datos, cargar_datos_redis, listar_esf_disponibles
from views import dashboard_general, movimientos, estado_situacion_financiera, estado_resultados, estado_resultados_integral, estado_cambio_patrimonio

st.set_page_config(layout="wide", page_title="SGM - Dashboard Contable", page_icon="📊")

# Sidebar para selección de fuente de datos y vista de JSON raw
mostrar_header()
sidebar_result = mostrar_sidebar()
selected_tab = sidebar_result["selected_tab"]

# Cargar datos según la configuración del sidebar
if sidebar_result["usar_redis"]:
    data = cargar_datos_redis(
        cliente_id=sidebar_result["cliente_id"],
        periodo=sidebar_result["periodo"],
        test_type=sidebar_result["test_type"]
    )
    st.sidebar.success(f"✅ Usando datos de Redis")
    if data.get("fuente") == "archivo_ejemplo":
        st.sidebar.warning("⚠️ Redis no disponible, usando datos de ejemplo")
else:
    data = cargar_datos()
    data["fuente"] = "archivo_ejemplo"
    st.sidebar.info("📁 Usando datos de archivo de ejemplo")

# Mostrar JSON raw si está habilitado
if sidebar_result["mostrar_json"]:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 JSON Raw")
    
    if "raw_json" in data:
        json_str = json.dumps(data["raw_json"], indent=2, ensure_ascii=False)
        st.sidebar.text_area(
            "Datos JSON completos:",
            value=json_str,
            height=400,
            help="JSON raw cargado desde Redis o archivo de ejemplo"
        )
    else:
        st.sidebar.warning("No hay datos JSON raw disponibles")

# Mostrar las vistas según la pestaña seleccionada
if selected_tab == "📊 Dashboard General":
    dashboard_general.mostrar(data)
elif selected_tab == "🧾 Movimientos":
    movimientos.mostrar(data)
elif selected_tab == "🏛️ Estado de Situación Financiera (ESF)":
    estado_situacion_financiera.mostrar(data)
elif selected_tab == "📈 Estado de Resultados (ESR)":
    estado_resultados.mostrar(data)
elif selected_tab == "📊 Estado de Resultados Integral (ERI)":
    estado_resultados_integral.mostrar(data)
elif selected_tab == "💰 Estado de Cambio de Patrimonio (ECP)":
    estado_cambio_patrimonio.mostrar(data)
