import streamlit as st
import pandas as pd

# Importar utilidades de exportación Excel
try:
    from utils.excel_export import create_template_download_section, show_excel_export_help
except ImportError:
    # Si no se puede importar, crear funciones dummy
    def create_template_download_section():
        st.warning("⚠️ Funcionalidad de templates Excel no disponible")
    def show_excel_export_help():
        pass

def show(data_esf=None, data_eri=None, metadata=None):
    st.subheader("Resumen General")

    # Sección de templates Excel
    st.markdown("---")
    create_template_download_section()
    
    # Ayuda sobre exportación Excel
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📖 Guía de Exportación Excel")
        st.info("""
        🎯 **¿Nuevo en las exportaciones Excel?** Haz clic en "Ver Guía Completa" para conocer 
        todas las funcionalidades disponibles y cómo aprovechar al máximo los reportes en Excel.
        """)
    with col2:
        if st.button("📚 Ver Guía Completa", help="Mostrar ayuda detallada sobre Excel"):
            show_excel_export_help()
    
    st.markdown("---")

    # Llamar a conciliación si tenemos datos
    if data_esf and data_eri:
        mostrar_conciliacion(data_esf, data_eri, metadata)
    else:
        st.warning("No se ha cargado información para mostrar la conciliación.")

def mostrar_conciliacion(data_esf=None, data_eri=None, metadata=None):
    st.markdown("## Conciliación Resultado del Ejercicio")

    if data_esf is None or data_eri is None:
        st.info("No se encontró información suficiente para la conciliación.")
        return

    # Buscar cuenta 'Resultados acumulados' en ESF
    saldo_anterior = 0.0
    saldo_final = 0.0

    patrimonio_capital = data_esf.get("patrimonio", {}).get("capital", {})
    grupos = patrimonio_capital.get("grupos", {})

    for grupo_nombre, grupo_info in grupos.items():
        cuentas = grupo_info.get("cuentas", [])
        for cuenta in cuentas:
            agrupacion = cuenta.get("clasificaciones_cliente", {}).get("AGRUPACION INFORME", "")
            if agrupacion.lower() == "gains (losses) accumulated":
                saldo_anterior = cuenta.get("saldo_anterior", 0.0)
                saldo_final = cuenta.get("saldo_final", 0.0)

    # Resultado del ejercicio según ERI
    resultado_eri = data_eri.get("totales", {}).get("resultado_final", 0.0)

    # Calcular ajuste
    ajuste = saldo_final - saldo_anterior - resultado_eri

    st.markdown(f"""
        <div style='
            border-left: 4px solid #0A58CA;
            padding-left: 15px;
            margin-bottom: 15px;
        '>
            <h4 style='color: #0A58CA;'>Conciliación Patrimonio - Resultado del Ejercicio</h4>
            <p><strong>Resultados acumulados iniciales:</strong> {formatear_monto(saldo_anterior, metadata.get("moneda", "CLP"))}</p>
            <p><strong>+ Resultado del ejercicio (ERI):</strong> {formatear_monto(resultado_eri, metadata.get("moneda", "CLP"))}</p>
            <p><strong>± Ajustes:</strong> {formatear_monto(ajuste, metadata.get("moneda", "CLP"))}</p>
            <hr>
            <p><strong>= Resultados acumulados finales (calculado):</strong> {formatear_monto(saldo_anterior + resultado_eri + ajuste, metadata.get("moneda", "CLP"))}</p>
            <p><strong>= Resultados acumulados finales (en ESF):</strong> {formatear_monto(saldo_final, metadata.get("moneda", "CLP"))}</p>
        </div>
    """, unsafe_allow_html=True)

    if abs((saldo_anterior + resultado_eri + ajuste) - saldo_final) < 1:
        st.success("¡Conciliación correcta! Los saldos coinciden.")
    else:
        st.warning("Atención: hay diferencias en la conciliación. Revisa ajustes.")


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
