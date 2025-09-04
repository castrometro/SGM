import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.loader_nomina import obtener_informes_disponibles_redis, cargar_datos_redis


def _inject_css():
	st.markdown(
		"""
		<style>
		.pill {display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;border:1px solid #1f2937;margin:4px 6px 0 0;font-size:12px;color:#e5e7eb}
		.pill-a {background: rgba(13,148,136,0.15); border-color: rgba(13,148,136,0.35)}
		.pill-b {background: rgba(59,130,246,0.15); border-color: rgba(59,130,246,0.35)}
		.card {background: rgba(17,24,39,0.6); border: 1px solid #1f2937; border-radius: 12px; padding: 14px;}
		.metric-label {color:#9ca3af;font-size:12px}
		.metric-value {color:#e5e7eb;font-size:20px;font-weight:700}
		</style>
		""",
		unsafe_allow_html=True,
	)


def _fmt_pct(x):
	try:
		return f"{float(x)*100:.1f}%"
	except Exception:
		return "N/A"


def _normalize_period(p: str) -> str:
	if not p:
		return p
	p = str(p)
	if '-' in p:
		return p
	if len(p) == 6 and p.isdigit():
		return f"{p[:4]}-{p[4:6]}"
	return p


def _period_sort_key(p: str):
	try:
		p = str(p)
		if '-' in p:
			y, m = p.split('-')
			return (int(y), int(m))
		if len(p) == 6 and p.isdigit():
			return (int(p[:4]), int(p[4:6]))
	except Exception:
		return (0, 0)
	return (0, 0)


def mostrar(cliente_id: int | None):
	if not cliente_id:
		st.info("Selecciona 'Redis' como fuente o provee ?cliente_id en la URL.")
		return

	info = obtener_informes_disponibles_redis(cliente_id)
	periodos = sorted({i.get('periodo') for i in info.get('informes', []) if i.get('periodo')})
	if len(periodos) < 1:
		st.info("No hay períodos en Redis para este cliente.")
		return

	st.markdown("Selecciona dos períodos del mismo cliente para comparar KPIs, totales y movimientos.")
	c1, c2 = st.columns(2)
	with c1:
		p1 = st.selectbox("Período A", periodos, index=len(periodos) - 1)
	with c2:
		p2 = st.selectbox("Período B", periodos, index=max(0, len(periodos) - 2))

	show_pair = bool(p1 and p2 and p1 != p2)
	a = b = None
	if show_pair:
		a = cargar_datos_redis(cliente_id, p1)
		b = cargar_datos_redis(cliente_id, p2)
		if not a or not b:
			st.warning("No fue posible cargar ambos períodos para comparación; se mostrará la evolución temporal igualmente.")
			show_pair = False
	# Cargar último período disponible para encabezado si no hay A/B
	data_last = None
	if not show_pair:
		try:
			data_last = cargar_datos_redis(cliente_id, periodos[-1])
		except Exception:
			data_last = None

	# Encabezado
	_inject_css()
	cliente_nombre = (a or data_last or {}).get('cliente_nombre', '')
	cliente_rut = (a or data_last or {}).get('cliente_rut', '')
	st.markdown(f"### Cliente {cliente_nombre} · {cliente_rut}")
	if show_pair:
		st.markdown(f"<div class='pill pill-a'>Período A: {p1}</div> <div class='pill pill-b'>Período B: {p2}</div>", unsafe_allow_html=True)

	# KPIs comparados
	if show_pair and a and b:
		st.subheader("KPIs")
		col1, col2, col3 = st.columns(3)
		for k, label, col in [
			('tasa_ingreso', 'Ingreso', col1),
			('tasa_rotacion', 'Rotación', col2),
			('tasa_ausentismo', 'Ausentismo', col3)
		]:
			va = float((a.get('kpis') or {}).get(k, 0) or 0)
			vb = float((b.get('kpis') or {}).get(k, 0) or 0)
			delta = (va - vb) * 100
			with col:
				st.metric(label=f"{label}", value=_fmt_pct(va), delta=f"{delta:+.1f} pp ({p1} vs {p2})")
				st.caption(f"{p2}: {_fmt_pct(vb)}")

	# Totales libro comparados
	if show_pair and a and b:
		st.subheader("Totales Libro")
		ta, tb = a.get('totales_libro', {}) or {}, b.get('totales_libro', {}) or {}
		cols = st.columns(5)
		campos = [
			('empleados', 'Dotación'),
			('haberes_imponibles', 'Haberes Imponibles'),
			('descuentos_legales', 'Descuentos Legales'),
			('aportes_patronales', 'Aportes Patronales'),
			('otros_descuentos', 'Otros Descuentos')
		]
		for i, (key, label) in enumerate(campos):
			va, vb = ta.get(key, 0) or 0, tb.get(key, 0) or 0
			with cols[i]:
				if key == 'empleados':
					st.metric(label, f"{int(va)}", delta=f"{(int(va) - int(vb)):+d} vs {p2}")
				else:
					st.metric(label, f"${va:,.0f}", delta=f"${(va - vb):+,.0f} vs {p2}")

	# Composición 100% (por categoría) como dumbbell de porcentajes
	if show_pair and a and b:
		st.subheader("Composición del Libro (puntos 100%)")
	categorias = [
		('haberes_imponibles', 'Haberes Imponibles'),
		('descuentos_legales', 'Descuentos Legales'),
		('aportes_patronales', 'Aportes Patronales'),
		('otros_descuentos', 'Otros Descuentos'),
		('impuestos', 'Impuestos'),
	]
	total_a = sum(float(ta.get(k, 0) or 0) for k, _ in categorias) or 1.0
	total_b = sum(float(tb.get(k, 0) or 0) for k, _ in categorias) or 1.0
	cats = [label for _, label in categorias]
	perc_a = [float(ta.get(k, 0) or 0) / total_a for k, _ in categorias]
	perc_b = [float(tb.get(k, 0) or 0) / total_b for k, _ in categorias]
	fig_comp = go.Figure()
	# Líneas por categoría
	for i, cat in enumerate(cats):
		fig_comp.add_trace(go.Scatter(x=[perc_a[i], perc_b[i]], y=[cat, cat], mode='lines',
									  line=dict(color='#4b5563', width=2), showlegend=False))
	# Puntos A y B
	fig_comp.add_trace(go.Scatter(x=perc_a, y=cats, mode='markers', name=p1,
								  marker=dict(color='#14b8a6', size=10)))
	fig_comp.add_trace(go.Scatter(x=perc_b, y=cats, mode='markers', name=p2,
								  marker=dict(color='#3b82f6', size=10)))
	fig_comp.update_layout(title='Participación por categoría (A vs B)', height=360, template='plotly_dark',
						   xaxis=dict(tickformat='.0%', title='Participación'), yaxis=dict(title='Categoría'),
						   margin=dict(t=50, r=20, l=20, b=40))
	st.plotly_chart(fig_comp, use_container_width=True)

	# Totales movimientos comparados como dumbbell
	if show_pair and a and b:
		st.subheader("Movimientos (puntos)")
		ma, mb = a.get('totales_movimientos', {}) or {}, b.get('totales_movimientos', {}) or {}
	mov_labels = ['Ingresos', 'Finiquitos', 'Ausentismos']
	mov_keys = ['ingresos', 'finiquitos', 'ausentismos']
	vals_a = [int(ma.get(k, 0) or 0) for k in mov_keys]
	vals_b = [int(mb.get(k, 0) or 0) for k in mov_keys]
	fig_mov = go.Figure()
	for i, cat in enumerate(mov_labels):
		fig_mov.add_trace(go.Scatter(x=[vals_a[i], vals_b[i]], y=[cat, cat], mode='lines',
									 line=dict(color='#4b5563', width=2), showlegend=False))
	fig_mov.add_trace(go.Scatter(x=vals_a, y=mov_labels, mode='markers', name=p1,
								 marker=dict(color='#14b8a6', size=10)))
	fig_mov.add_trace(go.Scatter(x=vals_b, y=mov_labels, mode='markers', name=p2,
								 marker=dict(color='#3b82f6', size=10)))
	fig_mov.update_layout(title='Movimientos por tipo (A vs B)', height=300, template='plotly_dark',
						  xaxis=dict(title='Cantidad'), yaxis=dict(title='Tipo'),
						  margin=dict(t=50, r=20, l=20, b=40))
	st.plotly_chart(fig_mov, use_container_width=True)

	# Variación por categoría (lollipop de Δ)
	if show_pair and a and b:
		st.subheader("Variación por categoría (Δ A - B)")
		deltas = []
		for k, label in categorias:
			va, vb = float(ta.get(k, 0) or 0), float(tb.get(k, 0) or 0)
			deltas.append((label, va - vb))
		cats_var = [c for c, _ in deltas]
		vals_var = [v for _, v in deltas]
		order = list(pd.Series(vals_var, index=cats_var).sort_values().index)
		cats_var_sorted = order
		vals_sorted = [dict(deltas)[c] for c in cats_var_sorted]
		fig_var = go.Figure()
		# líneas desde 0 al delta
		for i, cat in enumerate(cats_var_sorted):
			fig_var.add_trace(go.Scatter(x=[0, vals_sorted[i]], y=[cat, cat], mode='lines',
										 line=dict(color='#4b5563', width=2), showlegend=False))
		colors = ['#34d399' if v >= 0 else '#f87171' for v in vals_sorted]
		fig_var.add_trace(go.Scatter(x=vals_sorted, y=cats_var_sorted, mode='markers', marker=dict(color=colors, size=10),
									 showlegend=False))
		fig_var.update_layout(height=360, xaxis_tickformat='$,.0f', template='plotly_dark',
							  title='Aumentos (verde) / Disminuciones (rojo)',
							  margin=dict(t=50, r=20, l=20, b=40))
		st.plotly_chart(fig_var, use_container_width=True)

	# Evolución temporal (series de tiempo)
	st.subheader("Evolución temporal")
	try:
		info_all = obtener_informes_disponibles_redis(cliente_id)
		periodos_all = [i.get('periodo') for i in info_all.get('informes', []) if i.get('periodo')]
		periodos_all = sorted(list(set(periodos_all)), key=_period_sort_key)
		if not periodos_all:
			st.info("No hay suficientes períodos para graficar evolución")
		else:
			total_periodos = len(periodos_all)
			if total_periodos <= 2:
				n = total_periodos
			else:
				min_slider = 3
				max_slider = min(24, total_periodos)
				default_slider = min(6, max_slider)
				n = st.slider("Cantidad de períodos a mostrar", min_value=min_slider, max_value=max_slider, value=default_slider)
			periodos_sel = periodos_all[-n:]
			# Cargar informes seleccionados
			serie = []
			for pr in periodos_sel:
				data_p = cargar_datos_redis(cliente_id, pr)
				if not data_p:
					continue
				tot = data_p.get('totales_libro', {}) or {}
				mov = data_p.get('totales_movimientos', {}) or {}
				k = data_p.get('kpis', {}) or {}
				serie.append({
					'periodo': _normalize_period(pr),
					'empleados': int(tot.get('empleados', 0) or 0),
					'haberes_imponibles': float(tot.get('haberes_imponibles', 0) or 0),
					'descuentos_legales': float(tot.get('descuentos_legales', 0) or 0),
					'aportes_patronales': float(tot.get('aportes_patronales', 0) or 0),
					'otros_descuentos': float(tot.get('otros_descuentos', 0) or 0),
					'impuestos': float(tot.get('impuestos', 0) or 0),
					'tasa_ingreso': float(k.get('tasa_ingreso', 0) or 0),
					'tasa_rotacion': float(k.get('tasa_rotacion', 0) or 0),
					'tasa_ausentismo': float(k.get('tasa_ausentismo', 0) or 0),
					'ingresos': int(mov.get('ingresos', 0) or 0),
					'finiquitos': int(mov.get('finiquitos', 0) or 0),
					'ausentismos': int(mov.get('ausentismos', 0) or 0),
				})
			if serie:
				df_ts = pd.DataFrame(serie)
				df_ts = df_ts.sort_values('periodo')

				# KPIs
				kpi_cols = ['tasa_ingreso', 'tasa_rotacion', 'tasa_ausentismo']
				df_k = df_ts.melt(id_vars='periodo', value_vars=kpi_cols, var_name='KPI', value_name='valor')
				fig_kpi = px.line(df_k, x='periodo', y='valor', color='KPI', markers=True, title='KPIs en el tiempo')
				fig_kpi.update_layout(template='plotly_dark', height=320, yaxis_tickformat='.0%', margin=dict(t=50, r=20, l=20, b=40))
				st.plotly_chart(fig_kpi, use_container_width=True)

				# Totales del libro (montos)
				tot_cols = ['haberes_imponibles', 'descuentos_legales', 'aportes_patronales', 'otros_descuentos', 'impuestos']
				seleccion = st.multiselect("Series de montos a mostrar", options=tot_cols, default=['haberes_imponibles', 'descuentos_legales'])
				if seleccion:
					df_t = df_ts.melt(id_vars='periodo', value_vars=seleccion, var_name='Concepto', value_name='monto')
					fig_tot = px.line(df_t, x='periodo', y='monto', color='Concepto', markers=True, title='Montos del libro en el tiempo')
					fig_tot.update_layout(template='plotly_dark', height=360, yaxis_tickformat='$,.0f', margin=dict(t=50, r=20, l=20, b=40))
					st.plotly_chart(fig_tot, use_container_width=True)

				# Dotación
				fig_dot = px.line(df_ts, x='periodo', y='empleados', markers=True, title='Dotación (empleados)')
				fig_dot.update_layout(template='plotly_dark', height=280, margin=dict(t=50, r=20, l=20, b=40))
				st.plotly_chart(fig_dot, use_container_width=True)

				# Movimientos
				mov_cols = ['ingresos', 'finiquitos', 'ausentismos']
				df_m = df_ts.melt(id_vars='periodo', value_vars=mov_cols, var_name='Movimiento', value_name='cantidad')
				fig_mov_ts = px.line(df_m, x='periodo', y='cantidad', color='Movimiento', markers=True, title='Movimientos en el tiempo')
				fig_mov_ts.update_layout(template='plotly_dark', height=320, margin=dict(t=50, r=20, l=20, b=40))
				st.plotly_chart(fig_mov_ts, use_container_width=True)
			else:
				st.info("No se pudieron cargar datos de períodos seleccionados")
	except Exception as e:
		st.warning(f"No fue posible construir las series temporales: {e}")

	# Top conceptos (dumbbell A vs B)
	if show_pair and a and b:
		da, db = a.get('desglose_libro', {}) or {}, b.get('desglose_libro', {}) or {}
	else:
		da = db = {}
	if show_pair and (da or db):
		st.subheader("Top conceptos (A vs B)")
		categoria_map = [
			('haberes_imponibles', 'Haberes Imponibles'),
			('descuentos_legales', 'Descuentos Legales'),
			('aportes_patronales', 'Aportes Patronales'),
			('otros_descuentos', 'Otros Descuentos'),
			('impuestos', 'Impuestos'),
		]
		for k, titulo in categoria_map:
			ia, ib = da.get(k) or [], db.get(k) or []
			if not ia and not ib:
				continue
			# Armar set de conceptos top combinado (max entre A y B) y top 10
			dfa = pd.DataFrame(ia) if ia else pd.DataFrame(columns=['concepto', 'monto_total'])
			dfb = pd.DataFrame(ib) if ib else pd.DataFrame(columns=['concepto', 'monto_total'])
			dfa = dfa.groupby('concepto', as_index=False)['monto_total'].sum()
			dfb = dfb.groupby('concepto', as_index=False)['monto_total'].sum()
			merged = pd.merge(dfa, dfb, on='concepto', how='outer', suffixes=('_a', '_b')).fillna(0)
			merged['max_val'] = merged[['monto_total_a', 'monto_total_b']].max(axis=1)
			merged = merged.sort_values('max_val', ascending=False).head(10)
			if merged.empty:
				continue
			cats_c = list(merged['concepto'])
			vals_a_c = list(merged['monto_total_a'])
			vals_b_c = list(merged['monto_total_b'])
			fig_c = go.Figure()
			for i, cat in enumerate(cats_c):
				fig_c.add_trace(go.Scatter(x=[vals_a_c[i], vals_b_c[i]], y=[cat, cat], mode='lines',
										   line=dict(color='#4b5563', width=2), showlegend=False))
			fig_c.add_trace(go.Scatter(x=vals_a_c, y=cats_c, mode='markers', name=p1,
									   marker=dict(color='#14b8a6', size=9)))
			fig_c.add_trace(go.Scatter(x=vals_b_c, y=cats_c, mode='markers', name=p2,
									   marker=dict(color='#3b82f6', size=9)))
			fig_c.update_layout(title=f"{titulo} · Top conceptos (A vs B)", height=360, template='plotly_dark',
								xaxis=dict(tickformat='$,.0f', title='Monto'), yaxis=dict(title='Concepto'),
								margin=dict(t=50, r=20, l=20, b=40))
			st.plotly_chart(fig_c, use_container_width=True)
