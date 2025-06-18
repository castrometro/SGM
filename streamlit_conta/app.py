import streamlit as st
from layout.sidebar import mostrar_sidebar
from layout.header import mostrar_header
from data.loader_real import cargar_datos
from views import dashboard_general, estado_situacion_financiera, estado_resultados, estado_resultados_integral, estado_cambio_patrimonio

st.set_page_config(layout="wide", page_title="SGM - Dashboard Contable", page_icon="📊")

data = cargar_datos()
selected_tab = mostrar_sidebar()
mostrar_header()

if selected_tab == "📊 Dashboard General":
    dashboard_general.mostrar(data)
elif selected_tab == "🏛️ Estado de Situación Financiera (ESF)":
    estado_situacion_financiera.mostrar(data)
elif selected_tab == "📈 Estado de Resultados (ESR)":
    estado_resultados.mostrar(data)
elif selected_tab == "📊 Estado de Resultados Integral (ERI)":
    estado_resultados_integral.mostrar(data)
elif selected_tab == "💰 Estado de Cambio de Patrimonio (ECP)":
    estado_cambio_patrimonio.mostrar(data)
