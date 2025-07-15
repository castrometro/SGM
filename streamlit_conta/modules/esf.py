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

# Importar utilidades de exportación Excel
try:
    from utils.excel_export import create_excel_download_button, show_excel_export_help
except ImportError:
    # Si no se puede importar, crear funciones dummy
    def create_excel_download_button(*args, **kwargs):
        st.warning("⚠️ Funcionalidad de exportación Excel no disponible")
    def show_excel_export_help():
        pass

def show(data_esf=None, metadata=None, data_eri=None):
    st.subheader("Estado de Situación Financiera (ESF)")

    # DEBUG: Verificar datos recibidos (comentado para evitar output en sidebar)
    # print("=" * 80)
    # print("DEBUG: Parámetros recibidos en ESF:")
    # print(f"- data_esf: {'✓ Recibido' if data_esf is not None else '✗ None'}")
    # print(f"- metadata: {'✓ Recibido' if metadata is not None else '✗ None'}")
    # print(f"- data_eri: {'✓ Recibido' if data_eri is not None else '✗ None'}")
    # print("=" * 80)

    # DEBUG: Ver estructura completa del data_esf (comentado)
    # print("=" * 80)
    # print("DEBUG: Estructura completa de data_esf:")
    # print("=" * 80)
    # if data_esf:
    #     import json
    #     print(json.dumps(data_esf, indent=2, ensure_ascii=False))
    # else:
    #     print("data_esf is None")
    # print("=" * 80)

    # Leer idioma global
    lang_field = st.session_state.get("lang_field", "nombre_es")
    idioma_legible = "Español" if lang_field == "nombre_es" else "English"

    # DEBUG: Ver metadata (comentado)
    # print("DEBUG: Metadata:")
    # print(metadata)
    # print("-" * 40)

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
    # BOTÓN DE EXPORTACIÓN EXCEL
    # ===========================
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("### 📥 Exportar Reporte")
        create_excel_download_button(
            data=data_esf,
            metadata=metadata or {},
            report_type='esf',
            button_label="📊 Descargar ESF en Excel",
            file_prefix="estado_situacion_financiera"
        )
    
    with col2:
        if st.button("❓ Ayuda Excel", help="Ver información sobre la exportación Excel"):
            show_excel_export_help()
    
    st.markdown("---")
    
    # ===========================
    # Mostrar cantidad de cuentas ESF
    # ===========================

    cuentas_esf = extraer_cuentas_desde_esf(data_esf, lang_field=st.session_state.get("lang_field", "nombre_es"))

    st.markdown(f"#### Total cuentas procesadas en ESF: **{len(cuentas_esf)}**")

    if not cuentas_esf.empty:
        with st.expander(f"Ver detalle de las {len(cuentas_esf)} cuentas procesadas"):
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
        "Total Liabilities and Patrimony": "Total Pasivos y Patrimonio",
        "Earnings / (Loss) for the Period": "Ganancia / (Pérdida) del Ejercicio"
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
    st.markdown(f"""
        <div style='
            text-align: right; 
            margin: 20px 0; 
            padding: 15px; 
            background-color: #000000; 
            color: #ffffff; 
            border-radius: 5px;
        '>
            <h3 style='margin: 0;'>{traducir('Total Assets')}: {formatear_monto(total_activos, metadata.get('moneda', 'CLP'))}</h3>
        </div>
    """, unsafe_allow_html=True)

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
    st.markdown(f"""
        <div style='
            text-align: right; 
            margin: 20px 0; 
            padding: 15px; 
            background-color: #000000; 
            color: #ffffff; 
            border-radius: 5px;
        '>
            <h3 style='margin: 0;'>{traducir('Total Liabilities')}: {formatear_monto(total_pasivos, metadata.get('moneda', 'CLP'))}</h3>
        </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------
    # Patrimonio
    # ---------------------------------------------
    patrimonio_capital = data_esf.get("patrimonio", {}).get("capital", {})
    st.markdown(f"## {traducir('Patrimony')}")
    mostrar_bloque(patrimonio_capital, traducir("Total Patrimony"), metadata.get("moneda", "CLP"), lang_field)

    total_patrimonio = patrimonio_capital.get("total", 0)

    # Agregar el total del ERI al patrimonio como subgrupo
    total_eri = 0.0
    if data_eri is not None:
        total_eri = calcular_total_eri(data_eri)
        # print(f"DEBUG: Total ERI calculado: {total_eri}")  # Debug comentado
        if total_eri != 0.0:
            # Mostrar el ERI como un expander adicional en Patrimonio
            with st.expander(f"**{traducir('Earnings / (Loss) for the Period')}** - {formatear_monto(total_eri, metadata.get('moneda', 'CLP'))} ({traducir('Del ERI') if lang_field == 'nombre_es' else 'From ERI'})"):
                st.info(f"{'Este monto proviene del Estado de Resultado Integral (ERI) y representa el resultado del ejercicio.' if lang_field == 'nombre_es' else 'This amount comes from the Statement of Comprehensive Income (ERI) and represents the earnings for the period.'}")
                st.markdown(f"**{'Total del Resultado del Ejercicio' if lang_field == 'nombre_es' else 'Total Earnings for the Period'}:** {formatear_monto(total_eri, metadata.get('moneda', 'CLP'))}")
        else:
            st.info("El total del ERI es 0, no se muestra en el patrimonio.")
    else:
        st.info("No se proporcionaron datos del ERI para incluir en el patrimonio.")

    # Total patrimonio incluyendo ERI
    total_patrimonio_con_eri = total_patrimonio + total_eri

    # Mostrar total del patrimonio incluyendo ERI
    st.markdown(f"""
        <div style='
            text-align: right; 
            margin: 15px 0; 
            padding: 15px; 
            background-color: #000000; 
            color: #ffffff; 
            border-radius: 5px;
        '>
            <b>TOTAL {traducir('Patrimony')} (incluyendo resultado del ejercicio): {formatear_monto(total_patrimonio_con_eri, metadata.get('moneda', 'CLP'))}</b>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    total_pasivos_patrimonio = total_pasivos + total_patrimonio_con_eri
    st.markdown(f"""
        <div style='
            text-align: right; 
            margin: 20px 0; 
            padding: 15px; 
            background-color: #000000; 
            color: #ffffff; 
            border-radius: 5px;
        '>
            <h3 style='margin: 0;'>{traducir('Total Liabilities and Patrimony')}: {formatear_monto(total_pasivos_patrimonio, metadata.get('moneda', 'CLP'))}</h3>
        </div>
    """, unsafe_allow_html=True)

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
    agrupado por AGRUPACION INFORME con UI expandible.
    """
    # DEBUG: Ver estructura del bloque (comentado)
    # print(f"\n{'='*60}")
    # print(f"DEBUG: mostrar_bloque - {total_label}")
    # print(f"{'='*60}")
    # print("Estructura del bloque:")
    # import json
    # print(json.dumps(bloque, indent=2, ensure_ascii=False))
    # print(f"{'='*60}")
    
    if "grupos" in bloque:
        # print(f"DEBUG: El bloque tiene 'grupos'. Cantidad: {len(bloque['grupos'])}")
        for grupo_key, grupo_info in bloque["grupos"].items():
            # print(f"  - Grupo: {grupo_key}")
            # print(f"    Tipo: {type(grupo_info)}")
            if isinstance(grupo_info, dict):
                # print(f"    Keys: {list(grupo_info.keys())}")
                if "cuentas" in grupo_info:
                    # print(f"    Cantidad cuentas: {len(grupo_info['cuentas'])}")
                    pass
        # print("-" * 40)
        
        agrupacion = agrupar_por_agrupacion_informe(bloque, lang_field)

        # DEBUG: Ver resultado de agrupación (comentado)
        # print("DEBUG: Resultado de agrupar_por_agrupacion_informe:")
        # for grupo, cuentas in agrupacion.items():
        #     print(f"  - {grupo}: {len(cuentas)} cuentas")
        # print("-" * 40)

        # Mostrar grupos con UI expandible
        for grupo, cuentas in agrupacion.items():
            total_grupo = sum([cuenta["Saldo Final"] for cuenta in cuentas])
            
            # Crear el expander con el nombre del grupo y su total
            with st.expander(f"**{grupo}** - {formatear_monto(total_grupo, moneda)} ({len(cuentas)} cuentas)"):
                cuentas_formateadas = []
                for cuenta in cuentas:
                    cuenta_copia = cuenta.copy()
                    cuenta_copia["Saldo Final"] = formatear_monto(cuenta["Saldo Final"], moneda)
                    cuentas_formateadas.append(cuenta_copia)

                df = pd.DataFrame(cuentas_formateadas)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No hay cuentas en este grupo.")

        # Mostrar total del bloque
        total_bloque = bloque.get("total", 0)
        st.markdown(f"<div style='text-align:right; margin-top: 15px; padding: 15px; background-color: #000000; color: #ffffff; border-radius: 5px;'><b>{total_label}: {formatear_monto(total_bloque, moneda)}</b></div>", unsafe_allow_html=True)
        st.markdown("---")

    elif "cuentas" in bloque:
        cuentas = bloque.get("cuentas", [])
        total_bloque = 0.0
        
        # Calcular total del bloque
        for cuenta in cuentas:
            total_bloque += cuenta.get("saldo_final", 0)

        # Mostrar como un solo expander
        with st.expander(f"**{total_label}** - {formatear_monto(total_bloque, moneda)} ({len(cuentas)} cuentas)"):
            cuentas_formateadas = []
            for cuenta in cuentas:
                saldo_final = cuenta.get("saldo_final", 0)
                cuentas_formateadas.append({
                    "Código": cuenta.get("codigo", ""),
                    "Nombre": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                    "Saldo Final": formatear_monto(saldo_final, moneda)
                })

            df = pd.DataFrame(cuentas_formateadas)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hay cuentas en este bloque.")

        st.markdown("---")

    else:
        st.markdown("_No hay información disponible en este bloque._")


def agrupar_por_agrupacion_informe(bloque, lang_field="nombre_es"):
    """
    Agrupa cuentas según clasificaciones_cliente["AGRUPACION INFORME"].
    """
    # DEBUG: Ver proceso de agrupación (comentado)
    # print(f"\n{'*'*50}")
    # print("DEBUG: agrupar_por_agrupacion_informe")
    # print(f"{'*'*50}")
    
    grupos = bloque.get("grupos", {})
    # print(f"Grupos encontrados: {list(grupos.keys())}")
    
    agrupacion_final = {}

    for grupo, info in grupos.items():
        # print(f"\nProcesando grupo: {grupo}")
        # print(f"Info del grupo: {type(info)} - Keys: {list(info.keys()) if isinstance(info, dict) else 'No es dict'}")
        
        cuentas = info.get("cuentas", [])
        # print(f"Cuentas en este grupo: {len(cuentas)}")
        
        for i, cuenta in enumerate(cuentas):
            # print(f"  Cuenta {i+1}:")
            # print(f"    Código: {cuenta.get('codigo', 'N/A')}")
            # print(f"    Nombre: {cuenta.get(lang_field, cuenta.get('nombre_en', 'N/A'))}")
            # print(f"    Saldo final: {cuenta.get('saldo_final', 0)}")
            
            clasif = cuenta.get("clasificaciones_cliente", {})
            # print(f"    Clasificaciones cliente: {clasif}")
            
            agrupacion_informe = clasif.get("AGRUPACION INFORME", grupo)
            # print(f"    Agrupación informe: {agrupacion_informe}")

            nombre_cuenta = cuenta.get(lang_field, cuenta.get("nombre_en", ""))

            if agrupacion_informe not in agrupacion_final:
                agrupacion_final[agrupacion_informe] = []

            agrupacion_final[agrupacion_informe].append({
                "Código": cuenta.get("codigo"),
                "Nombre": nombre_cuenta,
                "Saldo Final": cuenta.get("saldo_final", 0)
            })

    # print(f"\nAgrupación final: {list(agrupacion_final.keys())}")
    # print(f"{'*'*50}")
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
