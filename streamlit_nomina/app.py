import streamlit as st
from layout.sidebar import mostrar_sidebar
from layout.header import mostrar_header
from data.loader import cargar_datos
from views import dashboard_general

st.set_page_config(layout="wide", page_title="SGM - Dashboard Nómina", page_icon="💼")

data = cargar_datos()
selected_tab = mostrar_sidebar()
mostrar_header()

if selected_tab == "📊 Dashboard General":
    dashboard_general.mostrar(data)
