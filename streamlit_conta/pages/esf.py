import streamlit as st
import pandas as pd

def show(data_esf=None, metadata=None):
    st.subheader("Estado de Situación Financiera (ESF)")

    # Leer idioma global
    lang_field = st.session_state.get("lang_field", "nombre_es")
    idioma_legible = "Español" if lang_field == "nombre_es" else "English"

    # Encabezado
    if metadata:
        cliente = metadata.get("cliente_nombre", "Cliente desconocido")
        periodo = metadata.get("periodo", "Periodo desconocido")
        moneda = metadata.get("moneda", "CLP")

        st.markdown(f"""
            <div style='
                padding: 10px 0; 
                border-left: 3px solid #0A58CA;
                padding-left: 15px;
                margin-bottom: 15px;
            '>
                <div style='margin-bottom: 8px;'>
                    <strong style='color: #0A58CA;'>Información del Reporte</strong>
                </div>
                <div style='display: flex; gap: 30px; flex-wrap: wrap; color: #333;'>
                    <div><strong>Empresa:</strong> {cliente}</div>
                    <div><strong>Período:</strong> {periodo}</div>
                    <div><strong>Moneda:</strong> {moneda}</div>
                    <div><strong>Idioma:</strong> {idioma_legible}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se encontró información de encabezado.")

    if data_esf is None:
        st.info("Aún no se ha cargado ningún archivo ESF.")
        return
    # ===========================
    # Mostrar cantidad de cuentas ESF
    # ===========================

    cuentas_esf = extraer_cuentas_desde_esf(data_esf, lang_field=st.session_state.get("lang_field", "nombre_es"))

    st.markdown(f"#### Total cuentas procesadas en ESF: **{len(cuentas_esf)}**")

    if not cuentas_esf.empty:
        st.dataframe(cuentas_esf, use_container_width=True)
    else:
        st.info("No se encontraron cuentas en el ESF.")


    # Mapas de títulos traducidos
    titulos_es = {
        "Current Assets": "Activos Corrientes",
        "Non-current Assets": "Activos No Corrientes",
        "Total Current Assets": "Total Activos Corrientes",
        "Total Non-current Assets": "Total Activos No Corrientes",
        "Current Liabilities": "Pasivos Corrientes",
        "Non-current Liabilities": "Pasivos No Corrientes",
        "Total Current Liabilities": "Total Pasivos Corrientes",
        "Total Non-current Liabilities": "Total Pasivos No Corrientes",
        "Patrimony": "Patrimonio",
        "Total Patrimony": "Total Patrimonio",
        "Total Assets": "Total Activos",
        "Total Liabilities": "Total Pasivos",
        "Total Liabilities and Patrimony": "Total Pasivos y Patrimonio"
    }

    # Función para traducir
    def traducir(label):
        if lang_field == "nombre_en":
            return label
        else:
            return titulos_es.get(label, label)

    # ---------------------------------------------
    # Activos Corrientes
    # ---------------------------------------------
    activos_corrientes = data_esf.get("activos", {}).get("corrientes", {})
    st.markdown(f"## {traducir('Current Assets')}")
    mostrar_bloque(activos_corrientes, traducir("Total Current Assets"), metadata.get("moneda", "CLP"), lang_field)

    # ---------------------------------------------
    # Activos No Corrientes
    # ---------------------------------------------
    activos_no_corrientes = data_esf.get("activos", {}).get("no_corrientes", {})
    st.markdown(f"## {traducir('Non-current Assets')}")
    mostrar_bloque(activos_no_corrientes, traducir("Total Non-current Assets"), metadata.get("moneda", "CLP"), lang_field)

    # Total Activos
    total_activos = activos_corrientes.get("total", 0) + activos_no_corrientes.get("total", 0)
    st.markdown(f"<div style='text-align:right;'><b>{traducir('Total Assets')}: {formatear_monto(total_activos, metadata.get('moneda', 'CLP'))}</b></div>", unsafe_allow_html=True)
    st.markdown("___")

    # ---------------------------------------------
    # Pasivos Corrientes
    # ---------------------------------------------
    pasivos_corrientes = data_esf.get("pasivos", {}).get("corrientes", {})
    st.markdown(f"## {traducir('Current Liabilities')}")
    mostrar_bloque(pasivos_corrientes, traducir("Total Current Liabilities"), metadata.get("moneda", "CLP"), lang_field)

    # ---------------------------------------------
    # Pasivos No Corrientes
    # ---------------------------------------------
    pasivos_no_corrientes = data_esf.get("pasivos", {}).get("no_corrientes", {})
    st.markdown(f"## {traducir('Non-current Liabilities')}")
    mostrar_bloque(pasivos_no_corrientes, traducir("Total Non-current Liabilities"), metadata.get("moneda", "CLP"), lang_field)

    total_pasivos = pasivos_corrientes.get("total", 0) + pasivos_no_corrientes.get("total", 0)
    st.markdown(f"<div style='text-align:right;'><b>{traducir('Total Liabilities')}: {formatear_monto(total_pasivos, metadata.get('moneda', 'CLP'))}</b></div>", unsafe_allow_html=True)
    st.markdown("___")

    # ---------------------------------------------
    # Patrimonio
    # ---------------------------------------------
    patrimonio_capital = data_esf.get("patrimonio", {}).get("capital", {})
    st.markdown(f"## {traducir('Patrimony')}")
    mostrar_bloque(patrimonio_capital, traducir("Total Patrimony"), metadata.get("moneda", "CLP"), lang_field)

    total_patrimonio = patrimonio_capital.get("total", 0)

    total_pasivos_patrimonio = total_pasivos + total_patrimonio
    st.markdown(f"<div style='text-align:right;'><b>{traducir('Total Liabilities and Patrimony')}: {formatear_monto(total_pasivos_patrimonio, metadata.get('moneda', 'CLP'))}</b></div>", unsafe_allow_html=True)
    st.markdown("---")

def extraer_cuentas_desde_esf(data_esf, lang_field="nombre_es"):
    """
    Extrae lista de cuentas procesadas en ESF.
    Devuelve DataFrame con Código y Nombre.
    """
    rows = []
    if data_esf:
        for bloque in ["activos", "pasivos", "patrimonio"]:
            bloque_data = data_esf.get(bloque, {})
            for sub in ["corrientes", "no_corrientes", "capital"]:
                sub_data = bloque_data.get(sub, {})
                grupos = sub_data.get("grupos", {})
                for grupo, info in grupos.items():
                    cuentas = info.get("cuentas", [])
                    for cuenta in cuentas:
                        rows.append({
                            "Código": cuenta.get("codigo", ""),
                            "Nombre": cuenta.get(lang_field, cuenta.get("nombre_en", ""))
                        })
    return pd.DataFrame(rows)

def mostrar_bloque(bloque, total_label, moneda="CLP", lang_field="nombre_es"):
    """
    Muestra un bloque (corriente, no corriente, patrimonio)
    agrupado por AGRUPACION INFORME.
    """
    if "grupos" in bloque:
        agrupacion = agrupar_por_agrupacion_informe(bloque, lang_field)

        for grupo, cuentas in agrupacion.items():
            st.markdown(f"## {grupo}")

            total_grupo = sum([cuenta["Saldo Final"] for cuenta in cuentas])

            cuentas_formateadas = []
            for cuenta in cuentas:
                cuenta_copia = cuenta.copy()
                cuenta_copia["Saldo Final"] = formatear_monto(cuenta["Saldo Final"], moneda)
                cuentas_formateadas.append(cuenta_copia)

            df = pd.DataFrame(cuentas_formateadas)
            if not df.empty:
                st.dataframe(df, use_container_width=True)

            st.markdown(
                f"<div style='text-align:right;'><b>Total {grupo}: {formatear_monto(total_grupo, moneda)}</b></div>",
                unsafe_allow_html=True
            )
            st.markdown("---")

        total_bloque = bloque.get("total", 0)
        st.markdown(f"<div style='text-align:right;'><b>{total_label}: {formatear_monto(total_bloque, moneda)}</b></div>", unsafe_allow_html=True)
        st.markdown("---")

    elif "cuentas" in bloque:
        cuentas = bloque.get("cuentas", [])
        cuentas_formateadas = []
        total_bloque = 0.0

        for cuenta in cuentas:
            saldo_final = cuenta.get("saldo_final", 0)
            total_bloque += saldo_final
            cuentas_formateadas.append({
                "Código": cuenta.get("codigo", ""),
                "Nombre": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                "Saldo Final": formatear_monto(saldo_final, moneda)
            })

        df = pd.DataFrame(cuentas_formateadas)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.markdown("_No hay cuentas en este bloque._")

        st.markdown(
            f"<div style='text-align:right;'><b>{total_label}: {formatear_monto(total_bloque, moneda)}</b></div>",
            unsafe_allow_html=True
        )
        st.markdown("---")

    else:
        st.markdown("_No hay información disponible en este bloque._")


def agrupar_por_agrupacion_informe(bloque, lang_field="nombre_es"):
    """
    Agrupa cuentas según clasificaciones_cliente["AGRUPACION INFORME"].
    """
    grupos = bloque.get("grupos", {})
    agrupacion_final = {}

    for grupo, info in grupos.items():
        cuentas = info.get("cuentas", [])
        for cuenta in cuentas:
            clasif = cuenta.get("clasificaciones_cliente", {})
            agrupacion_informe = clasif.get("AGRUPACION INFORME", grupo)

            nombre_cuenta = cuenta.get(lang_field, cuenta.get("nombre_en", ""))

            if agrupacion_informe not in agrupacion_final:
                agrupacion_final[agrupacion_informe] = []

            agrupacion_final[agrupacion_informe].append({
                "Código": cuenta.get("codigo"),
                "Nombre": nombre_cuenta,
                "Saldo Final": cuenta.get("saldo_final", 0)
            })

    return agrupacion_final


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
