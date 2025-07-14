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
    # VISTA: MOVIMIENTOS O RESUMEN POR CUENTA
    # ------------------------------------------
    
    vista_opciones = ["Movimientos detallados", "Resumen por cuenta", "Tabla completa de cuentas"]
    vista_seleccionada = st.radio("Seleccionar vista:", vista_opciones, horizontal=True)

    if vista_seleccionada == "Movimientos detallados":
        # Vista original de movimientos
        df_to_show = df
        
    elif vista_seleccionada == "Resumen por cuenta":
        # Agrupar por Origen + Código + Nombre
        df_grouped = (
            df
            .groupby(["Origen", "Código Cuenta", "Nombre Cuenta", "Clasificación"], as_index=False)
            .agg({
                "Saldo Inicial": "first",  # Tomar el primer valor
                "Debe": "sum",
                "Haber": "sum"
            })
        )
        # Convertir a float normal de Python (no numpy)
        df_grouped["Saldo Inicial"] = df_grouped["Saldo Inicial"].astype(float)
        df_grouped["Debe"] = df_grouped["Debe"].astype(float)
        df_grouped["Haber"] = df_grouped["Haber"].astype(float)
        
        # Calcular saldo final y variación
        df_grouped["Saldo Final"] = df_grouped["Saldo Inicial"] + df_grouped["Debe"] - df_grouped["Haber"]
        df_grouped["Variación"] = df_grouped["Saldo Final"] - df_grouped["Saldo Inicial"]
        df_to_show = df_grouped
        
    else:  # Tabla completa de cuentas
        # Extraer información completa de cuentas
        df_cuentas = extraer_info_cuentas_completa(data_esf, data_eri, lang_field)
        df_to_show = df_cuentas

    # ------------------------------------------
    # MOSTRAR TABLA
    # ------------------------------------------

    st.markdown(f"### {vista_seleccionada}")

    if not df_to_show.empty:
        # Asegurar que las columnas numéricas no tengan None y sean float de Python
        columnas_numericas = ["Debe", "Haber", "Saldo Inicial", "Saldo Final", "Variación", 
                             "Debe Movimientos", "Haber Movimientos"]
        
        for col in columnas_numericas:
            if col in df_to_show.columns:
                # Convertir a numeric, llenar NaN con 0, y asegurar que sea float de Python
                df_to_show[col] = pd.to_numeric(df_to_show[col], errors='coerce').fillna(0).astype(float)
        
        # Crear una copia del dataframe para mostrar con formato
        df_display = df_to_show.copy()
        
        # Aplicar formato CLP a las columnas numéricas para visualización
        for col in columnas_numericas:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: formatear_monto(x, metadata.get('moneda', 'CLP') if metadata else 'CLP')
                )
        
        # Mostrar el dataframe con formato aplicado
        st.dataframe(
            df_display, 
            use_container_width=True,
            hide_index=True
        )

        # Totales (solo para vistas con Debe/Haber)
        if "Debe" in df_to_show.columns and "Haber" in df_to_show.columns:
            total_debe = df_to_show["Debe"].sum()
            total_haber = df_to_show["Haber"].sum()

            st.markdown(
                f"""
                <div style='text-align:right; font-weight:bold; color:#0A58CA;'>
                    Total Debe: {formatear_monto(total_debe, metadata.get("moneda", "CLP") if metadata else "CLP")}<br>
                    Total Haber: {formatear_monto(total_haber, metadata.get("moneda", "CLP") if metadata else "CLP")}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Descarga CSV (usar df_to_show original sin formato para el CSV)
        nombre_archivo = f"{vista_seleccionada.lower().replace(' ', '_')}.csv"
        st.download_button(
            label="Descargar en CSV",
            data=df_to_show.to_csv(index=False, encoding="utf-8-sig"),
            file_name=nombre_archivo,
            mime="text/csv"
        )
    else:
        st.info("No hay datos que coincidan con los filtros.")


def extraer_todos_los_movimientos(data_esf, data_eri, lang_field="nombre_es"):
    """
    Extrae todos los movimientos desde ESF y ERI en un solo DataFrame.
    Ahora incluye saldo inicial y clasificación.
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
                        # Obtener información de la cuenta
                        codigo_cuenta = cuenta.get("codigo", "")
                        nombre_cuenta = cuenta.get(lang_field, cuenta.get("nombre_en", ""))
                        saldo_inicial = float(cuenta.get("saldo_anterior", 0) or 0)  # CAMBIADO: saldo_anterior
                        clasificacion = cuenta.get("clasificacion", f"{bloque_name.title()} - {sub_bloque_name.title()}")
                        
                        for mov in cuenta.get("movimientos", []):
                            rows.append({
                                "Origen": "ESF",
                                "Fecha": mov.get("fecha", ""),
                                "Código Cuenta": codigo_cuenta,
                                "Nombre Cuenta": nombre_cuenta,
                                "Clasificación": clasificacion,
                                "Saldo Inicial": saldo_inicial,
                                "Descripción": mov.get("descripcion", ""),
                                "Tipo Doc": mov.get("tipo_documento", ""),
                                "N° Doc": mov.get("numero_documento", ""),
                                "Debe": float(mov.get("debe", 0) or 0),
                                "Haber": float(mov.get("haber", 0) or 0),
                            })

    # --- Recorrer ERI ---
    if data_eri is not None:
        # Primero buscar en ingresos y gastos directos
        for tipo in ["ingresos", "gastos"]:
            cuentas_dict = data_eri.get(tipo, {})
            if isinstance(cuentas_dict, dict):
                for codigo, info_cuenta in cuentas_dict.items():
                    if isinstance(info_cuenta, dict):
                        nombre_cuenta = info_cuenta.get(lang_field, info_cuenta.get("nombre", ""))
                        saldo_inicial = float(info_cuenta.get("saldo_anterior", 0) or 0)  # CAMBIADO: saldo_anterior
                        clasificacion = info_cuenta.get("clasificacion", tipo.title())
                        
                        # Si hay movimientos en la cuenta
                        movimientos = info_cuenta.get("movimientos", [])
                        if movimientos:
                            for mov in movimientos:
                                rows.append({
                                    "Origen": "ERI",
                                    "Fecha": mov.get("fecha", ""),
                                    "Código Cuenta": codigo,
                                    "Nombre Cuenta": nombre_cuenta,
                                    "Clasificación": clasificacion,
                                    "Saldo Inicial": saldo_inicial,
                                    "Descripción": mov.get("descripcion", ""),
                                    "Tipo Doc": mov.get("tipo_documento", ""),
                                    "N° Doc": mov.get("numero_documento", ""),
                                    "Debe": float(mov.get("debe", 0) or 0),
                                    "Haber": float(mov.get("haber", 0) or 0),
                                })
        
        # También buscar en bloques de resumen
        for bloque_key in BLOQUES_ERI:
            bloque = data_eri.get(bloque_key, {}) or {}
            grupos = bloque.get("grupos", {})
            for info in grupos.values():
                for cuenta in info.get("cuentas", []):
                    codigo_cuenta = cuenta.get("codigo", "")
                    nombre_cuenta = cuenta.get(lang_field, cuenta.get("nombre_en", ""))
                    saldo_inicial = float(cuenta.get("saldo_anterior", 0) or 0)  # CAMBIADO: saldo_anterior
                    clasificacion = cuenta.get("clasificacion", bloque_key.replace("_", " ").title())
                    
                    for mov in cuenta.get("movimientos", []):
                        rows.append({
                            "Origen": "ERI",
                            "Fecha": mov.get("fecha", ""),
                            "Código Cuenta": codigo_cuenta,
                            "Nombre Cuenta": nombre_cuenta,
                            "Clasificación": clasificacion,
                            "Saldo Inicial": saldo_inicial,
                            "Descripción": mov.get("descripcion", ""),
                            "Tipo Doc": mov.get("tipo_documento", ""),
                            "N° Doc": mov.get("numero_documento", ""),
                            "Debe": float(mov.get("debe", 0) or 0),
                            "Haber": float(mov.get("haber", 0) or 0),
                        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Convertir fecha a datetime y ordenar
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df.sort_values("Fecha")


def extraer_info_cuentas_completa(data_esf, data_eri, lang_field="nombre_es"):
    """
    Extrae la información completa de todas las cuentas (sin movimientos individuales).
    Útil para ver un resumen general de todas las cuentas.
    """
    cuentas_dict = {}  # Usamos dict para evitar duplicados
    
    # --- Procesar ESF ---
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
                        codigo = cuenta.get("codigo", "")
                        if codigo:
                            cuentas_dict[codigo] = {
                                "Origen": "ESF",
                                "Código Cuenta": codigo,
                                "Nombre Cuenta": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                                "Nombre Inglés": cuenta.get("nombre_en", ""),
                                "Clasificación": cuenta.get("clasificacion", f"{bloque_name.title()} - {sub_bloque_name.title()}"),
                                "Saldo Inicial": float(cuenta.get("saldo_anterior", 0) or 0),  # CAMBIADO: saldo_anterior
                                "Debe Movimientos": float(cuenta.get("debe_movimientos", 0) or 0),
                                "Haber Movimientos": float(cuenta.get("haber_movimientos", 0) or 0),
                                "Saldo Final": float(cuenta.get("saldo", 0) or 0),
                                "Cantidad Movimientos": cuenta.get("movimientos_count", len(cuenta.get("movimientos", [])))
                            }

    # --- Procesar ERI ---
    if data_eri is not None:
        # Procesar ingresos y gastos directos
        for tipo in ["ingresos", "gastos"]:
            cuentas_tipo = data_eri.get(tipo, {})
            if isinstance(cuentas_tipo, dict):
                for codigo, info_cuenta in cuentas_tipo.items():
                    if isinstance(info_cuenta, dict) and codigo not in cuentas_dict:
                        cuentas_dict[codigo] = {
                            "Origen": "ERI",
                            "Código Cuenta": codigo,
                            "Nombre Cuenta": info_cuenta.get(lang_field, info_cuenta.get("nombre", "")),
                            "Nombre Inglés": info_cuenta.get("nombre_en", ""),
                            "Clasificación": info_cuenta.get("clasificacion", tipo.title()),
                            "Saldo Inicial": float(info_cuenta.get("saldo_anterior", 0) or 0),  # CAMBIADO: saldo_anterior
                            "Debe Movimientos": float(info_cuenta.get("debe_movimientos", 0) or 0),
                            "Haber Movimientos": float(info_cuenta.get("haber_movimientos", 0) or 0),
                            "Saldo Final": float(info_cuenta.get("monto", 0) or 0),
                            "Cantidad Movimientos": len(info_cuenta.get("movimientos", []))
                        }

    # Convertir a DataFrame
    df = pd.DataFrame(list(cuentas_dict.values()))
    
    if not df.empty:
        # Calcular variación
        df["Variación"] = df["Saldo Final"] - df["Saldo Inicial"]
        
        # Ordenar por origen y código
        df = df.sort_values(["Origen", "Código Cuenta"])
    
    return df


def formatear_monto(monto, moneda="CLP"):
    """Formatea el monto con el símbolo de moneda apropiado"""
    if monto is None or pd.isna(monto):
        return "-"
    
    # Convertir a float si no lo es
    try:
        monto = float(monto)
    except:
        return "-"
    
    # Formatear con separadores de miles
    if monto < 0:
        monto_formateado = f"({abs(monto):,.0f})"
    else:
        monto_formateado = f"{monto:,.0f}"
    
    # Reemplazar comas por puntos para formato chileno
    monto_formateado = monto_formateado.replace(",", ".")

    if moneda.upper() == "CLP":
        return f"${monto_formateado} CLP"
    elif moneda.upper() == "USD":
        return f"US${monto_formateado}"
    elif moneda.upper() == "EUR":
        return f"€{monto_formateado}"
    return f"{monto_formateado} {moneda}"
