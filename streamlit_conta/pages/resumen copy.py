import streamlit as st
import pandas as pd
import plotly.express as px

# Definimos los bloques ERI a considerar
BLOQUES_ERI = [
    "ganancias_brutas",
    "ganancia_perdida",
    "ganancia_perdida_antes_impuestos"
]

def show(data_esf=None, data_eri=None, metadata=None):
    st.subheader("Centro de Mando - Dashboard Ejecutivo")

    lang_field = st.session_state.get("lang_field", "nombre_es")

    if data_esf is None and data_eri is None:
        st.info("No hay datos para mostrar el resumen.")
        return

    # ==========================
    # KPIs principales
    # ==========================
    resultado_final = data_eri.get("totales", {}).get("resultado_final", 0) if data_eri else 0
    estructura_esf = calcular_estructura_esf(data_esf)

    patrimonio = estructura_esf.get("Patrimonio", 0)
    activos = estructura_esf.get("Activos", 0)
    pasivos = estructura_esf.get("Pasivos", 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Resultado Neto (ERI)", formatear_monto(resultado_final, metadata.get("moneda", "CLP")))
    with col2:
        st.metric("Total Activos", formatear_monto(activos, metadata.get("moneda", "CLP")))
    with col3:
        st.metric("Total Pasivos", formatear_monto(pasivos, metadata.get("moneda", "CLP")))
    with col4:
        st.metric("Patrimonio", formatear_monto(patrimonio, metadata.get("moneda", "CLP")))

    st.markdown("---")

    # ==========================
    # Evolución mensual Resultado Neto
    # ==========================
    st.markdown("### Evolución mensual del Resultado Neto")

    df_resultado_mensual = calcular_resultado_mensual(data_eri, lang_field)
    if not df_resultado_mensual.empty:
        fig = px.line(
            df_resultado_mensual,
            x="Mes",
            y="Resultado Neto",
            markers=True,
            title="Evolución mensual del Resultado Neto"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para graficar evolución mensual del resultado.")

    st.markdown("---")

    # ==========================
    # Top cuentas por saldo (ERI)
    # ==========================
    st.markdown("### Top cuentas ERI por saldo acumulado")

    df_top_cuentas = extraer_top_cuentas_eri(data_eri, lang_field)
    if not df_top_cuentas.empty:
        fig_top = px.bar(
            df_top_cuentas,
            x="Saldo Final",
            y="Cuenta",
            orientation="h",
            text_auto=True,
            title="Top cuentas ERI"
        )
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info("No hay cuentas relevantes para mostrar.")

    st.markdown("---")

    # ==========================
    # Estructura financiera (ESF)
    # ==========================
    st.markdown("### Estructura Financiera (ESF)")

    if estructura_esf:
        df_esf = pd.DataFrame([
            {"Elemento": "Activos", "Monto": activos},
            {"Elemento": "Pasivos", "Monto": pasivos},
            {"Elemento": "Patrimonio", "Monto": patrimonio}
        ])
        fig_esf = px.bar(
            df_esf,
            x="Elemento",
            y="Monto",
            color="Elemento",
            text_auto=True,
            title="Activos vs Pasivos vs Patrimonio"
        )
        st.plotly_chart(fig_esf, use_container_width=True)
    else:
        st.info("No hay datos de estructura financiera.")

    st.markdown("---")

    # ==========================
    # Volumen de movimientos
    # ==========================
    st.markdown("### Volumen de Movimientos Contables")

    total_movs = contar_movimientos(data_esf, data_eri)
    st.success(f"Se detectaron **{total_movs:,}** movimientos contables en este período.")

# ================================
# FUNCIONES AUXILIARES
# ================================

def calcular_resultado_mensual(data_eri, lang_field):
    rows = []
    if data_eri:
        for bloque_key in BLOQUES_ERI:
            bloque = data_eri.get(bloque_key, {})
            grupos = bloque.get("grupos", {})
            for info in grupos.values():
                for cuenta in info.get("cuentas", []):
                    for mov in cuenta.get("movimientos", []):
                        fecha = mov.get("fecha", "")
                        mes = pd.to_datetime(fecha, errors="coerce").month if fecha else None
                        saldo = mov.get("haber", 0) - mov.get("debe", 0)
                        rows.append({
                            "Mes": mes,
                            "Resultado Neto": saldo
                        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.groupby("Mes", as_index=False).agg({"Resultado Neto": "sum"})
    return df


def extraer_top_cuentas_eri(data_eri, lang_field, top_n=5):
    rows = []
    if data_eri:
        for bloque_key in BLOQUES_ERI:
            bloque = data_eri.get(bloque_key, {})
            grupos = bloque.get("grupos", {})
            for info in grupos.values():
                for cuenta in info.get("cuentas", []):
                    saldo = cuenta.get("saldo_final", 0.0)
                    rows.append({
                        "Cuenta": cuenta.get(lang_field, cuenta.get("nombre_en", "")),
                        "Saldo Final": abs(saldo)
                    })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values("Saldo Final", ascending=False).head(top_n)


def calcular_estructura_esf(data_esf):
    if data_esf is None:
        return {}

    activos_corrientes = data_esf.get("activos", {}).get("corrientes", {}).get("total", 0)
    activos_no_corrientes = data_esf.get("activos", {}).get("no_corrientes", {}).get("total", 0)
    pasivos_corrientes = data_esf.get("pasivos", {}).get("corrientes", {}).get("total", 0)
    pasivos_no_corrientes = data_esf.get("pasivos", {}).get("no_corrientes", {}).get("total", 0)
    patrimonio = data_esf.get("patrimonio", {}).get("capital", {}).get("total", 0)

    total_activos = activos_corrientes + activos_no_corrientes
    total_pasivos = pasivos_corrientes + pasivos_no_corrientes

    return {
        "Activos": total_activos,
        "Pasivos": total_pasivos,
        "Patrimonio": patrimonio
    }


def contar_movimientos(data_esf, data_eri):
    total = 0

    if data_esf:
        for bloque_name in ["activos", "pasivos", "patrimonio"]:
            bloque = data_esf.get(bloque_name, {})
            for sub in ["corrientes", "no_corrientes", "capital"]:
                for info in bloque.get(sub, {}).get("grupos", {}).values():
                    for cuenta in info.get("cuentas", []):
                        total += len(cuenta.get("movimientos", []))

    if data_eri:
        for bloque_key in BLOQUES_ERI:
            bloque = data_eri.get(bloque_key, {})
            for info in bloque.get("grupos", {}).values():
                for cuenta in info.get("cuentas", []):
                    total += len(cuenta.get("movimientos", []))

    return total


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