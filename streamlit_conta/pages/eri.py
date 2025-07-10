import streamlit as st
import pandas as pd

# Definimos los bloques ERI a procesar
BLOQUES_ERI = [
    "ganancias_brutas",
    "ganancia_perdida",
    "ganancia_perdida_antes_impuestos"
]

def show(data_eri=None, metadata=None):
    st.subheader("Estado de Resultado Integral (ERI)")

    # Tomar idioma desde session_state
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

    if data_eri is None:
        st.info("Aún no se ha cargado ningún archivo ERI.")
        return

    # ===========================
    # Mostrar cantidad de cuentas ERI
    # ===========================
    cuentas_eri = extraer_cuentas_desde_eri(data_eri, lang_field)
    st.markdown(f"#### Total cuentas procesadas en ERI: **{len(cuentas_eri)}**")

    if not cuentas_eri.empty:
        st.dataframe(cuentas_eri, use_container_width=True)
    else:
        st.info("No se encontraron cuentas en el ERI.")

    # Procesar cada bloque definido en BLOQUES_ERI
    for bloque_key in BLOQUES_ERI:
        bloque_data = data_eri.get(bloque_key)
        if bloque_data:
            procesar_bloque_eri(bloque_data, metadata, lang_field)


def procesar_bloque_eri(bloque, metadata, lang_field):
    nombre_bloque = bloque.get(lang_field, "Bloque sin nombre")
    st.markdown(f"## {nombre_bloque}")

    total_bloque = 0.0

    # 1. Procesar cuentas sueltas en el bloque
    cuentas_sueltas = bloque.get("cuentas", [])
    if cuentas_sueltas:
        st.markdown("### Cuentas Directas del Bloque")
        agrupaciones = agrupar_por_agrupacion_informe(cuentas_sueltas, lang_field)
        total_sueltas = 0.0

        for agrupacion, cuentas_agrupadas in agrupaciones.items():
            st.markdown(f"#### {agrupacion}")
            total_agrupacion = sum(c["Saldo Final"] for c in cuentas_agrupadas)
            total_sueltas += total_agrupacion

            cuentas_formateadas = [
                {"Código": c.get("Código", ""), "Nombre": c.get("Nombre", ""), "Saldo Final": formatear_monto(c.get("Saldo Final", 0.0), metadata.get("moneda", "CLP"))}
                for c in cuentas_agrupadas
            ]
            df = pd.DataFrame(cuentas_formateadas)
            if not df.empty:
                st.dataframe(df[["Código", "Nombre", "Saldo Final"]], use_container_width=True)
            st.markdown(
                f"<div style='text-align:right; font-weight:bold;'>Total {agrupacion}: {formatear_monto(total_agrupacion, metadata.get('moneda', 'CLP'))}</div>",
                unsafe_allow_html=True
            )
            st.markdown("---")

        st.markdown(f"""
            <div style='
                display: flex;
                justify-content: space-between;
                border-top: 1px solid #ddd;
                margin-top: 8px;
                padding-top: 5px;
                font-weight: bold;
                color: #0A58CA;
            '>
                <div>TOTAL Cuentas Directas</div>
                <div>{formatear_monto(total_sueltas, metadata.get("moneda", "CLP"))}</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("___")
        total_bloque += total_sueltas

    # 2. Procesar grupos en el bloque
    grupos = bloque.get("grupos", {})
    for grupo_nombre, grupo_info in grupos.items():
        grupo_titulo = grupo_info.get(lang_field, grupo_nombre)
        st.markdown(f"### {grupo_titulo}")
        cuentas = grupo_info.get("cuentas", [])
        agrupaciones = agrupar_por_agrupacion_informe(cuentas, lang_field)

        total_grupo = 0.0
        for agrupacion, cuentas_agrupadas in agrupaciones.items():
            if agrupacion != grupo_titulo:
                st.markdown(f"#### {agrupacion}")
            total_agrupacion = sum(c["Saldo Final"] for c in cuentas_agrupadas)
            total_grupo += total_agrupacion
            cuentas_formateadas = [
                {"Código": c.get("Código", ""), "Nombre": c.get("Nombre", ""), "Saldo Final": formatear_monto(c.get("Saldo Final", 0.0), metadata.get("moneda", "CLP"))}
                for c in cuentas_agrupadas
            ]
            df = pd.DataFrame(cuentas_formateadas)
            if not df.empty:
                st.dataframe(df[["Código", "Nombre", "Saldo Final"]], use_container_width=True)
            st.markdown(
                f"<div style='text-align:right; font-weight:bold;'>Total {agrupacion}: {formatear_monto(total_agrupacion, metadata.get('moneda', 'CLP'))}</div>",
                unsafe_allow_html=True
            )
            st.markdown("---")

        st.markdown(f"""
            <div style='
                display: flex;
                justify-content: space-between;
                border-top: 1px solid #ddd;
                margin-top: 8px;
                padding-top: 5px;
                font-weight: bold;
                color: #0A58CA;
            '>
                <div>TOTAL {grupo_titulo}</div>
                <div>{formatear_monto(total_grupo, metadata.get("moneda", "CLP"))}</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("___")
        total_bloque += total_grupo

    # Total del bloque
    st.markdown(f"""
        <div style='
            display: flex;
            justify-content: space-between;
            border-top: 2px solid #0A58CA;
            margin-top: 10px;
            padding-top: 8px;
            font-size: 18px;
            font-weight: bold;
            color: #0A58CA;
        '>
            <div>TOTAL {nombre_bloque}</div>
            <div>{formatear_monto(total_bloque, metadata.get('moneda', 'CLP'))}</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


def extraer_cuentas_desde_eri(data_eri, lang_field="nombre_es"):
    """
    Extrae TODAS las cuentas del ERI, incluidas:
    - cuentas dentro de grupos
    - cuentas sueltas directamente en el bloque
    """
    rows = []
    for bloque in BLOQUES_ERI:
        bloque_data = data_eri.get(bloque, {})
        # Cuentas sueltas
        for cuenta in bloque_data.get("cuentas", []):
            rows.append({
                "Código": cuenta.get("codigo", ""),
                "Nombre": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                "Agrupación": cuenta.get("clasificaciones_cliente", {}).get("AGRUPACION INFORME", "Sin Agrupación"),
                "Saldo Final": cuenta.get("saldo_final", 0.0),
            })
        # Cuentas en grupos
        for grupo_info in bloque_data.get("grupos", {}).values():
            for cuenta in grupo_info.get("cuentas", []):
                rows.append({
                    "Código": cuenta.get("codigo", ""),
                    "Nombre": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                    "Agrupación": cuenta.get("clasificaciones_cliente", {}).get("AGRUPACION INFORME", "Sin Agrupación"),
                    "Saldo Final": cuenta.get("saldo_final", 0.0),
                })
    return pd.DataFrame(rows)


def agrupar_por_agrupacion_informe(cuentas, lang_field):
    agrupaciones = {}
    for cuenta in cuentas:
        agrup = cuenta.get("clasificaciones_cliente", {}).get("AGRUPACION INFORME", "Sin Agrupación")
        nombre = cuenta.get(lang_field, cuenta.get("nombre_en", ""))
        if agrup not in agrupaciones:
            agrupaciones[agrup] = []
        agrupaciones[agrup].append({
            "Código": cuenta.get("codigo", ""),
            "Nombre": nombre,
            "Saldo Final": cuenta.get("saldo_final", 0.0)
        })
    return agrupaciones


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
