import streamlit as st
import getpass


def mostrar_header(data=None):
    st.title("💼 Dashboard de Nómina")
    
    if data:
        cliente = data.get("cliente_nombre", "N/A")
        periodo = data.get("periodo", "N/A")
        st.caption(f"👤 Usuario: {getpass.getuser()} | 🏢 Cliente: {cliente} | 📅 Período: {periodo}")
    else:
        st.caption(f"👤 Usuario: {getpass.getuser()} | 🏢 Cliente: N/A | 📅 Período: N/A")
    
    st.markdown("---")
