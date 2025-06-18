import streamlit as st
from components.charts import plot_control_gestion, plot_resumen_ingresos_anual, plot_facturacion_sector_industrial
from components.chatbot import mostrar_chatbot
import pandas as pd

def mostrar(data):
    st.header("📊 Resumen General")

    if "control_ingresos" in data:
        df_real = pd.DataFrame(data["control_ingresos"].get("distribucion_real", []))
        st.subheader("Distribución Real FC&T")
        st.plotly_chart(plot_control_gestion(df_real, "Real FC&T"), use_container_width=True)

    if "resumen_ingresos_anual" in data:
        df_resumen = pd.DataFrame(data["resumen_ingresos_anual"])
        st.subheader("Ingresos Anuales vs Presupuesto")
        st.plotly_chart(plot_resumen_ingresos_anual(df_resumen), use_container_width=True)

    if "facturacion_sector_industrial" in data:
        df_facturacion = pd.DataFrame(data["facturacion_sector_industrial"])
        st.subheader("Facturación por Sector Industrial")
        st.plotly_chart(plot_facturacion_sector_industrial(df_facturacion), use_container_width=True)

    st.markdown("---")
    mostrar_chatbot()
