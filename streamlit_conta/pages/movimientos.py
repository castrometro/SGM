import streamlit as st
import pandas as pd

# Definimos los bloques ERI a considerar
BLOQUES_ERI = [
    "ganancias_brutas",
    "ganancia_perdida",
    "ganancia_perdida_antes_impuestos"
]

def show(data_esf=None, data_eri=None, metadata=None):
    st.subheader("Movimientos Contables")

    lang_field = st.session_state.get("lang_field", "nombre_es")
    idioma_legible = "Español" if lang_field == "nombre_es" else "English"

    if data_esf is None and data_eri is None:
        st.info("No se encontró información de movimientos.")
        return

    # Extraer movimientos desde ESF y ERI
    df = extraer_todos_los_movimientos(data_esf, data_eri, lang_field)

    if df.empty:
        st.info("No hay movimientos para mostrar.")
        return

    # ------------------------------------------
    # FILTROS
    # ------------------------------------------

    st.markdown("### Filtros")

    # Rango fechas
    fechas = pd.to_datetime(df["Fecha"], errors="coerce")
    min_date = fechas.min()
    max_date = fechas.max()

    rango_fechas = st.date_input(
        "Rango de fechas:",
        value=(min_date, max_date)
    )

    # Manejar caso de una sola fecha
    if isinstance(rango_fechas, tuple):
        fecha_ini, fecha_fin = rango_fechas
    else:
        fecha_ini = fecha_fin = rango_fechas

    mask = (fechas >= pd.Timestamp(fecha_ini)) & (fechas <= pd.Timestamp(fecha_fin))
    df = df[mask]

    # Buscador texto libre
    texto_buscar = st.text_input("Buscar texto en descripción o nombre cuenta:")

    if texto_buscar:
        mask = df["Descripción"].str.contains(texto_buscar, case=False, na=False) | \
               df["Nombre Cuenta"].str.contains(texto_buscar, case=False, na=False)
        df = df[mask]

    # ------------------------------------------
    # AGRUPACIÓN
    # ------------------------------------------

    agrupado = st.checkbox("Mostrar agrupado por cuenta y origen", value=False)

    if agrupado:
        # Agrupar por Origen + Código + Nombre
        df_grouped = (
            df
            .groupby(["Origen", "Código Cuenta", "Nombre Cuenta"], as_index=False)
            .agg({
                "Debe": "sum",
                "Haber": "sum"
            })
        )
        df_to_show = df_grouped
    else:
        df_to_show = df

    # ------------------------------------------
    # MOSTRAR TABLA
    # ------------------------------------------

    st.markdown("### Movimientos Filtrados")

    if not df_to_show.empty:
        st.dataframe(df_to_show, use_container_width=True)

        # Totales
        total_debe = df_to_show["Debe"].sum()
        total_haber = df_to_show["Haber"].sum()

        st.markdown(
            f"""
            <div style='text-align:right; font-weight:bold; color:#0A58CA;'>
                Total Debe: {formatear_monto(total_debe, metadata.get("moneda", "CLP"))}<br>
                Total Haber: {formatear_monto(total_haber, metadata.get("moneda", "CLP"))}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Descarga CSV
        st.download_button(
            label="Descargar en CSV",
            data=df_to_show.to_csv(index=False, encoding="utf-8-sig"),
            file_name="movimientos_contables.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay movimientos que coincidan con los filtros.")



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
                for info in grupos.values():
                    for cuenta in info.get("cuentas", []):
                        for mov in cuenta.get("movimientos", []):
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
        for bloque_key in BLOQUES_ERI:
            bloque = data_eri.get(bloque_key, {}) or {}
            grupos = bloque.get("grupos", {})
            for info in grupos.values():
                for cuenta in info.get("cuentas", []):
                    for mov in cuenta.get("movimientos", []):
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

    # Convertir fecha a datetime y ordenar
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df.sort_values("Fecha")


def formatear_monto(monto, moneda="CLP"):
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
    return f"{monto_formateado} {moneda}"
