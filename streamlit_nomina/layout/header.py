import streamlit as st
import getpass


def mostrar_header():
    st.title("💼 Dashboard de Nómina")
    st.caption(f"👤 Usuario: {getpass.getuser()} | 🏢 Cliente: Compañía XYZ | 📅 Período: 2024")
    st.markdown("---")
