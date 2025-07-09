import streamlit as st
import json
from layout.sidebar import mostrar_sidebar
from layout.header import mostrar_header
from data.loader_contabilidad import cargar_datos, cargar_datos_redis, listar_esf_disponibles
from views import dashboard_general, estado_situacion_financiera, estado_resultados_integral

st.set_page_config(layout="wide", page_title="SGM - Dashboard Contable", page_icon="📊")

# CSS para diseño formal y plano
st.markdown("""
<style>
    /* Tema oscuro y minimalista */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Sidebar con diseño plano */
    .css-1d391kg {
        background-color: #262730;
        border-right: 1px solid #464858;
    }
    
    /* Métricas con diseño plano */
    [data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #464858;
        padding: 1rem;
        border-radius: 4px;
        box-shadow: none;
    }
    
    /* Tablas con diseño minimalista */
    .dataframe {
        background-color: #1E1E1E;
        border: 1px solid #464858;
    }
    
    /* Headers sin efectos */
    h1, h2, h3 {
        color: #FAFAFA;
        border-bottom: 1px solid #464858;
        padding-bottom: 0.5rem;
    }
    
    /* Botones planos */
    .stButton > button {
        background-color: #262730;
        border: 1px solid #464858;
        color: #FAFAFA;
        border-radius: 4px;
    }
    
    /* Tabs con diseño formal */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #1E1E1E;
        border-radius: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #262730;
        border: 1px solid #464858;
        color: #FAFAFA;
    }
</style>
""", unsafe_allow_html=True)

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
elif selected_tab == "🏛️ Estado de Situación Financiera (ESF)":
    estado_situacion_financiera.mostrar(data)
elif selected_tab == "📊 Estado de Resultados Integral (ERI)":
    estado_resultados_integral.mostrar(data)