import streamlit as st
import pandas as pd

# Importar la función de cálculo del ERI
try:
    from .eri import calcular_total_eri
except ImportError:
    # Si falla el import relativo, intentar import absoluto
    try:
        from eri import calcular_total_eri
    except ImportError:
        # Si todo falla, definir una función dummy
        def calcular_total_eri(data_eri):
            return 0.0
        st.warning("No se pudo importar la función calcular_total_eri del módulo ERI")

def show(data_ecp=None, metadata=None, data_eri=None, data_esf=None):
    st.subheader("Estado de Cambios en el Patrimonio (ECP)")
    
    # DEBUG: Verificar datos recibidos
    print("=" * 80)
    print("DEBUG: Parámetros recibidos en ECP:")
    print(f"- data_ecp: {'✓ Recibido' if data_ecp is not None else '✗ None'}")
    print(f"- metadata: {'✓ Recibido' if metadata is not None else '✗ None'}")
    print(f"- data_eri: {'✓ Recibido' if data_eri is not None else '✗ None'}")
    print(f"- data_esf: {'✓ Recibido' if data_esf is not None else '✗ None'}")
    print("=" * 80)
    
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
    
    if data_ecp is None:
        st.info("Aún no se ha cargado ningún archivo ECP.")
        return
    
    # Títulos traducidos
    titulos = {
        "es": {
            "title": "Estado de Cambios en el Patrimonio",
            "capital": "Capital",
            "other_reserves": "Otras Reservas", 
            "r_accumulated": "Resultados Acumulados",
            "capital_attributable": "Capital Atribuible a los propietarios de la controladora",
            "uncontrolled": "Participaciones no controladoras",
            "total": "Total",
            "initial_balance": "Saldo Inicial al 1 de Enero",
            "changes_capital": "Cambios en capital",
            "dividends": "Dividendos distribuidos",
            "result_exercise": "Resultado del ejercicio",
            "other_settings": "Otros ajustes",
            "final_balance": "Saldo Final",
            "show_details": "Ver detalles de cuentas"
        },
        "en": {
            "title": "Statement of Changes in Equity",
            "capital": "Capital",
            "other_reserves": "Other Reserves",
            "r_accumulated": "Accumulated Results", 
            "capital_attributable": "Capital Attributable to owners of the controller's instruments",
            "uncontrolled": "Uncontrolled participations",
            "total": "Total",
            "initial_balance": "Initial Balance as of January 1",
            "changes_capital": "Changes in capital",
            "dividends": "Dividend distributions", 
            "result_exercise": "Result of the exercise",
            "other_settings": "Other settings",
            "final_balance": "Final Balance",
            "show_details": "Show account details"
        }
    }
    
    t = titulos["es" if lang_field == "nombre_es" else "en"]
    
    # Extraer datos del ECP
    capital_data = data_ecp.get("capital", {})
    otras_reservas_data = data_ecp.get("otras_reservas", {})
    
    # Calcular el total del ERI (resultado del ejercicio)
    total_eri = 0.0
    if data_eri is not None:
        total_eri = calcular_total_eri(data_eri)
        print(f"DEBUG: Total ERI calculado: {total_eri}")
    
    # Calcular R Accumulated (Total patrimonio ESF sin incluir resultado del ejercicio)
    r_accumulated_inicial = 0.0
    if data_esf is not None:
        patrimonio_capital = data_esf.get("patrimonio", {}).get("capital", {})
        total_patrimonio_esf = patrimonio_capital.get("total", 0)
        # R accumulated es el patrimonio total menos el resultado del ejercicio actual
        r_accumulated_inicial = total_patrimonio_esf - total_eri
        print(f"DEBUG: R Accumulated inicial = {total_patrimonio_esf} - {total_eri} = {r_accumulated_inicial}")
    
    # Datos del período
    capital_inicial = capital_data.get("saldo_inicial", 0)
    capital_cambios = capital_data.get("cambios", 0)
    capital_final = capital_data.get("saldo_final", 0)
    
    otras_reservas_inicial = otras_reservas_data.get("saldo_inicial", 0)
    otras_reservas_cambios = otras_reservas_data.get("cambios", 0)
    otras_reservas_final = otras_reservas_data.get("saldo_final", 0)
    
    # Preparar datos para la tabla
    filas = []
    
    # Fila: Saldo inicial
    filas.append({
        "Concepto": t["initial_balance"],
        t["capital"]: capital_inicial,
        t["other_reserves"]: otras_reservas_inicial,
        t["r_accumulated"]: r_accumulated_inicial,
        t["capital_attributable"]: capital_inicial + otras_reservas_inicial + r_accumulated_inicial,
        t["uncontrolled"]: 0,
        t["total"]: capital_inicial + otras_reservas_inicial + r_accumulated_inicial
    })
    
    # Fila: Cambios en capital
    filas.append({
        "Concepto": t["changes_capital"],
        t["capital"]: capital_cambios,
        t["other_reserves"]: 0,
        t["r_accumulated"]: 0,
        t["capital_attributable"]: capital_cambios,
        t["uncontrolled"]: 0,
        t["total"]: capital_cambios
    })
    
    # Fila: Dividendos distribuidos
    filas.append({
        "Concepto": t["dividends"],
        t["capital"]: 0,
        t["other_reserves"]: 0,
        t["r_accumulated"]: 0,
        t["capital_attributable"]: 0,
        t["uncontrolled"]: 0,
        t["total"]: 0
    })
    
    # Fila: Resultado del ejercicio
    filas.append({
        "Concepto": t["result_exercise"],
        t["capital"]: 0,
        t["other_reserves"]: 0,
        t["r_accumulated"]: total_eri,
        t["capital_attributable"]: total_eri,
        t["uncontrolled"]: 0,
        t["total"]: total_eri
    })
    
    # Fila: Otros ajustes
    filas.append({
        "Concepto": t["other_settings"],
        t["capital"]: 0,
        t["other_reserves"]: otras_reservas_cambios,
        t["r_accumulated"]: 0,
        t["capital_attributable"]: otras_reservas_cambios,
        t["uncontrolled"]: 0,
        t["total"]: otras_reservas_cambios
    })
    
    # Fila: Saldo final
    r_accumulated_final = r_accumulated_inicial + total_eri
    capital_attributable_final = capital_final + otras_reservas_final + r_accumulated_final
    
    filas.append({
        "Concepto": t["final_balance"],
        t["capital"]: capital_final,
        t["other_reserves"]: otras_reservas_final,
        t["r_accumulated"]: r_accumulated_final,
        t["capital_attributable"]: capital_attributable_final,
        t["uncontrolled"]: 0,
        t["total"]: capital_attributable_final
    })
    
    # Crear DataFrame
    df = pd.DataFrame(filas)
    
    # Aplicar formato a las columnas numéricas
    columnas_numericas = [col for col in df.columns if col != "Concepto"]
    
    # Crear una copia del DataFrame con formato
    df_formateado = df.copy()
    for col in columnas_numericas:
        df_formateado[col] = df[col].apply(lambda x: formatear_monto(x, metadata.get("moneda", "CLP")))
    
    # Aplicar estilos al DataFrame
    def highlight_rows(row):
        if row["Concepto"] in [t["initial_balance"], t["final_balance"]]:
            return ['background-color: #000000; color: white; font-weight: bold'] * len(row)
        else:
            return [''] * len(row)
    
    # Mostrar tabla con estilos
    st.markdown("### " + t["title"])
    
    styled_df = df_formateado.style.apply(highlight_rows, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=250)
    
    # Sección expandible para mostrar detalles de las cuentas
    with st.expander(t["show_details"]):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {t['capital']}")
            for grupo_nombre, grupo_data in capital_data.get("grupos", {}).items():
                st.markdown(f"**{grupo_nombre}**")
                cuentas_capital = []
                for cuenta in grupo_data.get("cuentas", []):
                    cuentas_capital.append({
                        "Código": cuenta.get("codigo", ""),
                        "Nombre": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                        "Saldo Inicial": formatear_monto(cuenta.get("saldo_anterior", 0), metadata.get("moneda", "CLP")),
                        "Cambios": formatear_monto(cuenta.get("cambios", 0), metadata.get("moneda", "CLP")),
                        "Saldo Final": formatear_monto(cuenta.get("saldo_final", 0), metadata.get("moneda", "CLP"))
                    })
                if cuentas_capital:
                    df_capital = pd.DataFrame(cuentas_capital)
                    st.dataframe(df_capital, use_container_width=True)
        
        with col2:
            st.markdown(f"#### {t['other_reserves']}")
            for grupo_nombre, grupo_data in otras_reservas_data.get("grupos", {}).items():
                st.markdown(f"**{grupo_nombre}**")
                cuentas_reservas = []
                for cuenta in grupo_data.get("cuentas", []):
                    cuentas_reservas.append({
                        "Código": cuenta.get("codigo", ""),
                        "Nombre": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                        "Saldo Inicial": formatear_monto(cuenta.get("saldo_anterior", 0), metadata.get("moneda", "CLP")),
                        "Cambios": formatear_monto(cuenta.get("cambios", 0), metadata.get("moneda", "CLP")),
                        "Saldo Final": formatear_monto(cuenta.get("saldo_final", 0), metadata.get("moneda", "CLP"))
                    })
                if cuentas_reservas:
                    df_reservas = pd.DataFrame(cuentas_reservas)
                    st.dataframe(df_reservas, use_container_width=True)
    
    # Resumen de totales
    st.markdown("---")
    st.markdown("### Resumen de Cambios en el Patrimonio")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=t["initial_balance"],
            value=formatear_monto(capital_inicial + otras_reservas_inicial + r_accumulated_inicial, metadata.get("moneda", "CLP"))
        )
    
    with col2:
        cambio_total = capital_cambios + otras_reservas_cambios + total_eri
        st.metric(
            label="Cambio Total del Período",
            value=formatear_monto(cambio_total, metadata.get("moneda", "CLP")),
            delta=f"{'+' if cambio_total >= 0 else ''}{cambio_total:,.0f}"
        )
    
    with col3:
        st.metric(
            label=t["final_balance"],
            value=formatear_monto(capital_attributable_final, metadata.get("moneda", "CLP"))
        )


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