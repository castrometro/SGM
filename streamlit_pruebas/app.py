import streamlit as st
from layout.sidebar import mostrar_sidebar
from layout.header import mostrar_header
from data.loader import cargar_datos
from views import resumen_general, rentabilidad, ingresos

st.set_page_config(layout="wide", page_title="SGM Dashboard")

data = cargar_datos()
selected_tab = mostrar_sidebar()
mostrar_header()

if selected_tab == "Resumen General":
    resumen_general.mostrar(data)
elif selected_tab == "Rentabilidad":
    rentabilidad.mostrar(data)
elif selected_tab == "Volumen de Ingresos":
    ingresos.mostrar(data)
