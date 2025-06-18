import streamlit as st
import pandas as pd
from datetime import datetime

def mostrar(data=None):
    """Mostrar movimientos contables en forma interactiva"""
    st.header("🧾 Movimientos Contables")

    if not data or 'movimientos' not in data:
        st.warning("No hay movimientos disponibles")
        return

    df = pd.DataFrame(data['movimientos'])
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Opciones de filtrado
    with st.expander("Filtros", expanded=True):
        centros = sorted(df['centro_costo'].dropna().unique())
        tipos_doc = sorted(df['tipo_documento'].dropna().unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_centros = st.multiselect(
                "Centro de Costo",
                centros,
                default=centros
            )
        with col2:
            selected_tipos = st.multiselect(
                "Tipo Documento",
                tipos_doc,
                default= tipos_doc
            )

        fecha_min = df['fecha'].min().date()
        fecha_max = df['fecha'].max().date()
        start_date, end_date = st.date_input(
            "Rango de fechas",
            (fecha_min, fecha_max),
            min_value=fecha_min,
            max_value=fecha_max
        )

    mask = pd.Series(True, index=df.index)
    if selected_centros:
        mask &= df['centro_costo'].isin(selected_centros)
    if selected_tipos:
        mask &= df['tipo_documento'].isin(selected_tipos)
    if isinstance(start_date, datetime) and isinstance(end_date, datetime):
        mask &= (df['fecha'] >= pd.to_datetime(start_date)) & (df['fecha'] <= pd.to_datetime(end_date))

    df_filtered = df[mask].sort_values('fecha')

    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Movimientos", f"{len(df_filtered):,}")
    with col2:
        st.metric("Total Debe", f"${df_filtered['debe'].sum():,.0f}")
    with col3:
        st.metric("Total Haber", f"${df_filtered['haber'].sum():,.0f}")

