import streamlit as st
import getpass


def mostrar_header(data=None):
    st.title("💼 Dashboard de Nómina")
    
    if data:
        cliente = data.get("cliente_nombre", "N/A")
        periodo = data.get("periodo", "N/A")
        fuente = data.get("fuente", "archivo")

        # Información básica
        info_header = f"👤 Usuario: {getpass.getuser()} | 🏢 Cliente: {cliente} | 📅 Período: {periodo}"

        # Agregar información de fuente de datos
        if fuente == "redis":
            metadata = data.get("_metadata", {})
            ttl_segundos = metadata.get("ttl", 0)
            size_kb = metadata.get("size_kb", 0)

            if ttl_segundos == -1:
                ttl_text = "Sin vencimiento"
            elif ttl_segundos and ttl_segundos > 0:
                ttl_horas = ttl_segundos // 3600
                ttl_minutos = (ttl_segundos % 3600) // 60
                ttl_text = f"{ttl_horas}h {ttl_minutos}m" if ttl_horas > 0 else f"{ttl_minutos}m"
            else:
                ttl_text = "Expirado"

            info_header += f" | 📡 Redis (TTL: {ttl_text}, {size_kb:.1f}KB)"
        else:
            info_header += " | 📁 Archivo Local"

        st.caption(info_header)
    else:
        st.caption(f"👤 Usuario: {getpass.getuser()} | 🏢 Cliente: N/A | 📅 Período: N/A")
    
    st.markdown("---")
