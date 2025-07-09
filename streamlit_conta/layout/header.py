import streamlit as st
import getpass
import os

def mostrar_header():
    st.title("📊 Dashboard de Reportería y Análisis Contable")
    st.caption(f"� Usuario: {getpass.getuser()} | 🏢 Cliente: Empresa ABC S.A. | 📅 Período: 2024")
    st.markdown("---")