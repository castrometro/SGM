import streamlit as st
import pandas as pd
import plotly.express as px


def mostrar(data=None):
    st.header("📊 Resumen General de Nómina")
    st.markdown("**Visión general del cierre de remuneraciones**")

    if not data:
        st.error("No hay datos disponibles")
        return

    mostrar_info_cierre(data)
    mostrar_kpis(data)
    mostrar_resumen_conceptos(data)
    mostrar_empleados(data)


def mostrar_info_cierre(data):
    cierre = data.get("cierre", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cliente", cierre.get("cliente", "-"))
    with col2:
        st.metric("Período", cierre.get("periodo", "-"))
    with col3:
        st.metric("Estado", cierre.get("estado", "-").title())


def mostrar_kpis(data):
    cierre = data.get("cierre", {})
    haberes = cierre.get("total_haberes", 0)
    descuentos = cierre.get("total_descuentos", 0)
    liquido = haberes - descuentos

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Empleados", cierre.get("num_empleados", 0))
    with col2:
        st.metric("Total Haberes", f"${haberes:,.0f}")
    with col3:
        st.metric("Total Descuentos", f"${descuentos:,.0f}")
    with col4:
        st.metric("Total Líquido", f"${liquido:,.0f}")


def mostrar_resumen_conceptos(data):
    col1, col2 = st.columns(2)
    resumen_haberes = pd.DataFrame(data.get("resumen_haberes", []))
    resumen_desc = pd.DataFrame(data.get("resumen_descuentos", []))

    with col1:
        st.subheader("Haberes")
        if not resumen_haberes.empty:
            fig = px.bar(resumen_haberes, x="concepto", y="total", title="Distribución de Haberes")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de haberes")

    with col2:
        st.subheader("Descuentos")
        if not resumen_desc.empty:
            fig = px.bar(resumen_desc, x="concepto", y="total", title="Distribución de Descuentos", color_discrete_sequence=["#ef553b"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de descuentos")


def mostrar_empleados(data):
    st.markdown("---")
    st.subheader("Empleados")
    df_emp = pd.DataFrame(data.get("empleados", []))
    if df_emp.empty:
        st.info("Sin información de empleados")
    else:
        st.dataframe(df_emp)
