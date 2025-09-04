import streamlit as st
import pandas as pd
import plotly.express as px


def _fmt_pct(x):
    try:
        return f"{float(x)*100:.1f}%"
    except Exception:
        return "N/A"


def _inject_css():
    st.markdown(
        """
        <style>
        .sgm-header {background: linear-gradient(90deg, rgba(13,148,136,0.2), rgba(13,148,136,0)); border-bottom: 1px solid #1f2937; padding: 14px 16px; border-radius: 10px;}
        .sgm-title {display:flex;align-items:center;gap:8px;color:#2dd4bf;font-weight:700;font-size:20px;margin:0}
        .sgm-sub   {color:#9ca3af;font-size:13px;margin-top:4px}
        .card {background: rgba(17,24,39,0.6); border: 1px solid #1f2937; border-radius: 12px; padding: 16px;}
        .pill {display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;border:1px solid transparent;margin:4px 6px 0 0;font-size:12px}
        .pill-ingreso {background: rgba(16,185,129,0.16); color:#34d399; border-color: rgba(16,185,129,0.3)}
        .pill-finiquito {background: rgba(244,63,94,0.16); color:#f87171; border-color: rgba(244,63,94,0.3)}
        .pill-ausentismo {background: rgba(245,158,11,0.16); color:#fbbf24; border-color: rgba(245,158,11,0.3)}
        .metric-label {color:#9ca3af;font-size:12px}
        .metric-value {color:#e5e7eb;font-size:22px;font-weight:700}
        .grid {display:grid; gap:14px}
        @media (min-width: 768px){ .grid-3 {grid-template-columns: repeat(3, minmax(0,1fr));} .grid-4{grid-template-columns: repeat(4, minmax(0,1fr));}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar(data: dict):
    """Dashboard para el informe compacto (totales_libro, totales_movimientos, desglose_libro, kpis) con estilo tipo React."""
    if not data:
        st.warning("No hay datos de informe")
        return

    _inject_css()

    # Header visual
    cliente = data.get('cliente_nombre', 'N/A')
    rut = data.get('cliente_rut', 'N/A')
    periodo = data.get('periodo', 'N/A')
    st.markdown(
        f"""
        <div class="sgm-header">
            <div class="sgm-title">✨ Informe de Nómina</div>
            <div class="sgm-sub">{cliente} · {rut} · {periodo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPIs (tarjetas)
    kpis = data.get('kpis', {}) or {}
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown("<div class='card'><div class='metric-label'>Tasa de Ingreso</div><div class='metric-value'>" + _fmt_pct(kpis.get('tasa_ingreso')) + "</div></div>", unsafe_allow_html=True)
    with k2:
        st.markdown("<div class='card'><div class='metric-label'>Tasa de Rotación</div><div class='metric-value'>" + _fmt_pct(kpis.get('tasa_rotacion')) + "</div></div>", unsafe_allow_html=True)
    with k3:
        st.markdown("<div class='card'><div class='metric-label'>Tasa de Ausentismo</div><div class='metric-value'>" + _fmt_pct(kpis.get('tasa_ausentismo')) + "</div></div>", unsafe_allow_html=True)

    # Chips de movimientos
    tot_mov = data.get('totales_movimientos', {}) or {}
    if tot_mov:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        chips_html = "<div>"
        if 'ingresos' in tot_mov:
            chips_html += f"<span class='pill pill-ingreso'>Ingreso • {tot_mov.get('ingresos',0)}</span>"
        if 'finiquitos' in tot_mov:
            chips_html += f"<span class='pill pill-finiquito'>Finiquito • {tot_mov.get('finiquitos',0)}</span>"
        if 'ausentismos' in tot_mov:
            chips_html += f"<span class='pill pill-ausentismo'>Ausentismo • {tot_mov.get('ausentismos',0)}</span>"
        chips_html += "</div>"
        st.markdown(chips_html, unsafe_allow_html=True)

    # Grid de totales del libro (tarjetas)
    totales = data.get('totales_libro', {}) or {}
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='card'><div class='metric-label'>Dotación</div><div class='metric-value'>{int(totales.get('empleados',0))}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='metric-label'>Haberes Imponibles</div><div class='metric-value'>${totales.get('haberes_imponibles',0):,.0f}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='metric-label'>Descuentos Legales</div><div class='metric-value'>${totales.get('descuentos_legales',0):,.0f}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='card'><div class='metric-label'>Aportes Patronales</div><div class='metric-value'>${totales.get('aportes_patronales',0):,.0f}</div></div>", unsafe_allow_html=True)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown(f"<div class='card'><div class='metric-label'>Otros Descuentos</div><div class='metric-value'>${totales.get('otros_descuentos',0):,.0f}</div></div>", unsafe_allow_html=True)
    with d2:
        st.markdown(f"<div class='card'><div class='metric-label'>Impuestos</div><div class='metric-value'>${totales.get('impuestos',0):,.0f}</div></div>", unsafe_allow_html=True)
    with d3:
        st.markdown(f"<div class='card'><div class='metric-label'>Horas Extras (cant)</div><div class='metric-value'>{totales.get('horas_extras_cantidad',0)}</div></div>", unsafe_allow_html=True)
    with d4:
        st.markdown(f"<div class='card'><div class='metric-label'>Haberes No Imponibles</div><div class='metric-value'>${totales.get('haberes_no_imponibles',0):,.0f}</div></div>", unsafe_allow_html=True)

    # Gráfico: Movimientos por tipo
    if tot_mov:
        df_mov = pd.DataFrame([
            {"Tipo": "Ingreso", "Valor": tot_mov.get('ingresos', 0)},
            {"Tipo": "Finiquito", "Valor": tot_mov.get('finiquitos', 0)},
            {"Tipo": "Ausentismo", "Valor": tot_mov.get('ausentismos', 0)},
        ])
        fig_mov = px.bar(df_mov, x='Tipo', y='Valor', title='Movimientos por tipo', color='Tipo',
                         color_discrete_map={"Ingreso":"#34d399","Finiquito":"#f87171","Ausentismo":"#fbbf24"})
        fig_mov.update_layout(height=360, template='plotly_dark', margin=dict(t=50, r=20, l=20, b=40))
        st.plotly_chart(fig_mov, use_container_width=True)

    # Gráficos: Top conceptos por categoría
    desglose = data.get('desglose_libro', {}) or {}
    categorias = [
        ('haberes_imponibles', 'Haberes Imponibles'),
        ('descuentos_legales', 'Descuentos Legales'),
        ('aportes_patronales', 'Aportes Patronales'),
        ('otros_descuentos', 'Otros Descuentos'),
        ('impuestos', 'Impuestos'),
    ]
    for key, titulo in categorias:
        items = desglose.get(key) or []
        if not items:
            continue
        df = pd.DataFrame(items)
        if not df.empty and 'monto_total' in df:
            df = df.sort_values('monto_total', ascending=False).head(10)
            fig = px.bar(df, x='monto_total', y='concepto', orientation='h', title=f"Top {titulo}",
                         labels={'monto_total': 'Monto', 'concepto': 'Concepto'})
            fig.update_layout(height=380, xaxis_tickformat='$,.0f', template='plotly_dark', margin=dict(t=50, r=20, l=20, b=40))
            st.plotly_chart(fig, use_container_width=True)

    # Descarga de informe
    st.markdown("---")
    st.download_button(
        label="⬇️ Descargar informe JSON",
        data=pd.Series(data).to_json(),
        file_name=f"informe_nomina_{cliente}_{periodo}.json",
        mime="application/json"
    )

    with st.expander("📦 Datos crudos"):
        st.json(data)
