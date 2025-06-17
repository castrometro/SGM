import streamlit as st
import getpass
import os

def mostrar_header():
    st.title("📊 Dashboard de Reportes")
    st.caption(f"📣 Usuario: {getpass.getuser()} | 📁 Carpeta actual: {os.getcwd()}")
