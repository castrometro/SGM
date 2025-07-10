import streamlit as st
import pandas as pd
import plotly.express as px

def show(data_esf=None, data_eri=None, metadata=None):
    st.subheader("Análisis Exploratorio de Movimientos")

    lang_field = st.session_state.get("lang_field", "nombre_es")
    idioma_legible = "Español" if lang_field == "nombre_es" else "English"

    if data_esf is None and data_eri is None:
        st.info("No se encontró información de movimientos para análisis.")
        return

    # ----------------------------
    # Extraer movimientos
    # ----------------------------
    df = extraer_todos_los_movimientos(data_esf, data_eri, lang_field)

    if df.empty:
        st.info("No hay movimientos para análisis.")
        return

    # ----------------------------
    # VARIACIONES MENSUALES - GENERAL
    # ----------------------------
    st.markdown("## Variaciones mensuales (Debe/Haber)")

    df["Mes"] = df["Fecha"].dt.month

    df_variaciones = (
        df
        .groupby("Mes", as_index=False)
        .agg({
            "Debe": "sum",
            "Haber": "sum"
        })
        .sort_values("Mes")
    )

    st.dataframe(df_variaciones, use_container_width=True)

    fig = px.bar(
        df_variaciones,
        x="Mes",
        y=["Debe", "Haber"],
        barmode="group",
        title="Variaciones mensuales"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ----------------------------
    # ANÁLISIS DE CUENTA ESPECÍFICA
    # ----------------------------
    st.markdown("## Análisis de Cuenta Específica")

    cuentas_unicas = df[["Código Cuenta", "Nombre Cuenta"]].drop_duplicates()
    cuentas_unicas["Etiqueta"] = (
        cuentas_unicas["Código Cuenta"] + " - " + cuentas_unicas["Nombre Cuenta"]
    )

    cuenta_elegida = st.selectbox(
        "Selecciona una cuenta para análisis evolutivo:",
        cuentas_unicas["Etiqueta"].sort_values()
    )

    codigo_seleccionado = cuenta_elegida.split(" - ")[0]

    df_cuenta = df[
        df["Código Cuenta"] == codigo_seleccionado
    ]

    if not df_cuenta.empty:
        st.markdown("### Movimientos de la cuenta seleccionada")
        st.dataframe(df_cuenta, use_container_width=True)

        # Calcular evolución mensual
        df_cuenta["Mes"] = df_cuenta["Fecha"].dt.month

        df_evolucion = (
            df_cuenta
            .groupby("Mes", as_index=False)
            .agg({
                "Debe": "sum",
                "Haber": "sum"
            })
            .sort_values("Mes")
        )

        # Mostrar tabla evolución
        st.markdown("### Evolución mensual de la cuenta seleccionada")
        st.dataframe(df_evolucion, use_container_width=True)

        # Graficar evolución
        fig_cuenta = px.bar(
            df_evolucion,
            x="Mes",
            y=["Debe", "Haber"],
            barmode="group",
            title=f"Evolución mensual - {cuenta_elegida}"
        )
        st.plotly_chart(fig_cuenta, use_container_width=True)

        # Totales
        total_debe = df_cuenta["Debe"].sum()
        total_haber = df_cuenta["Haber"].sum()

        st.markdown(
            f"""
            <div style='text-align:right; font-weight:bold; color:#0A58CA;'>
                Total Debe: {formatear_monto(total_debe, metadata.get("moneda", "CLP"))}<br>
                Total Haber: {formatear_monto(total_haber, metadata.get("moneda", "CLP"))}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("No hay movimientos para la cuenta seleccionada.")

def extraer_todos_los_movimientos(data_esf, data_eri, lang_field="nombre_es"):
    """
    Extrae todos los movimientos desde ESF y ERI en un solo DataFrame.
    """
    rows = []

    # --- Recorrer ESF ---
    if data_esf is not None:
        for bloque_name in ["activos", "pasivos", "patrimonio"]:
            bloque = data_esf.get(bloque_name, {})
            if not bloque:
                continue

            for sub_bloque_name in ["corrientes", "no_corrientes", "capital"]:
                sub_bloque = bloque.get(sub_bloque_name, {})
                if not sub_bloque:
                    continue

                grupos = sub_bloque.get("grupos", {})
                for grupo, info in grupos.items():
                    cuentas = info.get("cuentas", [])
                    for cuenta in cuentas:
                        movimientos = cuenta.get("movimientos", [])
                        for mov in movimientos:
                            rows.append({
                                "Origen": "ESF",
                                "Fecha": mov.get("fecha", ""),
                                "Código Cuenta": cuenta.get("codigo", ""),
                                "Nombre Cuenta": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                                "Descripción": mov.get("descripcion", ""),
                                "Tipo Doc": mov.get("tipo_documento", ""),
                                "N° Doc": mov.get("numero_documento", ""),
                                "Debe": mov.get("debe", 0.0),
                                "Haber": mov.get("haber", 0.0),
                            })

    # --- Recorrer ERI ---
    if data_eri is not None:
        for bloque_key in ["ganancias_brutas", "ganancia_perdida"]:
            bloque = data_eri.get(bloque_key, {})
            grupos = bloque.get("grupos", {})
            for grupo, info in grupos.items():
                cuentas = info.get("cuentas", [])
                for cuenta in cuentas:
                    movimientos = cuenta.get("movimientos", [])
                    for mov in movimientos:
                        rows.append({
                            "Origen": "ERI",
                            "Fecha": mov.get("fecha", ""),
                            "Código Cuenta": cuenta.get("codigo", ""),
                            "Nombre Cuenta": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                            "Descripción": mov.get("descripcion", ""),
                            "Tipo Doc": mov.get("tipo_documento", ""),
                            "N° Doc": mov.get("numero_documento", ""),
                            "Debe": mov.get("debe", 0.0),
                            "Haber": mov.get("haber", 0.0),
                        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Convertir fecha a datetime
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Ordenar por fecha
    df = df.sort_values("Fecha")

    return df


def formatear_monto(monto, moneda="CLP"):
    """
    Formatea un monto según la moneda especificada.
    """
    if monto is None:
        return "-"
    if monto < 0:
        monto_formateado = f"({abs(monto):,.0f})"
    else:
        monto_formateado = f"{monto:,.0f}"

    if moneda.upper() == "CLP":
        return f"${monto_formateado} CLP"
    elif moneda.upper() == "USD":
        return f"US${monto_formateado}"
    elif moneda.upper() == "EUR":
        return f"€{monto_formateado}"
    else:
        return f"{monto_formateado} {moneda}"
