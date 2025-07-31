import streamlit as st
import json
import pathlib
import os


def mostrar_sidebar():
    if st.sidebar.button("🏠 **Home**", use_container_width=True):
        st.session_state.selected_tab = "📊 Dashboard General"
        if 'scroll_to_top' not in st.session_state:
            st.session_state.scroll_to_top = True
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # 🚀 NUEVA SECCIÓN: Selección de fuente de datos
    st.sidebar.markdown("� **Fuente de Datos:**")
    
    fuente_datos = st.sidebar.radio(
        "Seleccionar fuente:",
        ["�📁 Archivos Locales", "📡 Redis (Tiempo Real)"],
        index=0,
        key="fuente_datos"
    )
    
    selected_config = None
    
    if fuente_datos == "📡 Redis (Tiempo Real)":
        # Configuración Redis
        st.sidebar.markdown("---")
        st.sidebar.markdown("⚙️ **Configuración Redis:**")
        
        # Obtener información de Redis
        try:
            from data.loader_nomina import obtener_info_redis_completa
            info_redis = obtener_info_redis_completa()
            
            st.sidebar.info(f"🔗 **Ruta Redis:**\n{info_redis.get('ruta_redis', 'N/A')}")
            
            # Selector de cliente
            cliente_id = st.sidebar.number_input(
                "ID Cliente:",
                min_value=1,
                max_value=999,
                value=6,
                key="cliente_id_redis"
            )
            
            # Selector de período
            periodo = st.sidebar.text_input(
                "Período (YYYY-MM):",
                value="2025-03",
                key="periodo_redis"
            )
            
            # Mostrar cierres disponibles si hay información
            cierres = info_redis.get('cierres_disponibles', [])
            if cierres:
                st.sidebar.success(f"✅ {len(cierres)} informes en Redis")
                
                # Mostrar lista de períodos disponibles
                with st.sidebar.expander("📋 Informes Disponibles"):
                    for cierre in cierres[:5]:  # Mostrar máximo 5
                        st.write(f"• **{cierre['periodo']}** - {cierre['cliente_nombre']}")
                        if cierre['ttl_segundos'] > 0:
                            st.write(f"  TTL: {cierre['ttl_segundos']//3600}h {(cierre['ttl_segundos']%3600)//60}m")
            else:
                error_info = info_redis.get('error', None)
                if error_info:
                    st.sidebar.error(f"❌ Error Redis: {error_info}")
                else:
                    st.sidebar.warning("⚠️ No hay informes en Redis")
            
            selected_config = {
                'fuente': 'redis',
                'cliente_id': cliente_id,
                'periodo': periodo
            }
            
        except Exception as e:
            st.sidebar.error(f"❌ Error conectando a Redis: {e}")
            selected_config = None
    
    else:
        # Configuración de archivos locales (comportamiento original)
        st.sidebar.markdown("📁 **Seleccionar Datos:**")
        
        current_dir = pathlib.Path(__file__).parent.parent.resolve() / "data"
        archivos_disponibles = []
        
        try:
            for archivo in current_dir.glob("*.json"):
                if archivo.name.startswith("payroll_") and archivo.exists():
                    archivos_disponibles.append(archivo.name)
        except:
            archivos_disponibles = ["payroll_prueba.json"]
        
        archivos_disponibles = [archivo for archivo in archivos_disponibles if (current_dir / archivo).exists()]
        
        if not archivos_disponibles:
            archivos_disponibles = ["payroll_prueba.json"]
        
        archivo_seleccionado = st.sidebar.selectbox(
            "Período Actual:",
            sorted(archivos_disponibles),
            index=0,
            format_func=lambda x: x.replace("payroll_", "").replace(".json", "").replace("_", " ").title()
        )
        
        archivo_comparar = st.sidebar.selectbox(
            "Período a Comparar:",
            sorted(archivos_disponibles),
            index=1 if len(archivos_disponibles) > 1 else 0,
            format_func=lambda x: x.replace("payroll_", "").replace(".json", "").replace("_", " ").title()
        )
        
        if st.sidebar.button("🔄 **Actualizar**", use_container_width=True, help="Recargar datos manteniendo selecciones"):
            st.rerun()
        
        # Cargar y almacenar datos de archivos locales
        data_actual = cargar_datos_sidebar(archivo_seleccionado)
        data_comparar = cargar_datos_sidebar(archivo_comparar)
        
        st.session_state.archivo_seleccionado = archivo_seleccionado
        st.session_state.archivo_comparar = archivo_comparar
        st.session_state.data = data_actual
        st.session_state.data_comparar = data_comparar
        
        selected_config = {
            'fuente': 'archivos',
            'archivo_actual': archivo_seleccionado,
            'archivo_comparar': archivo_comparar
        }
    
    # Selección de pestañas (común para ambas fuentes)
    st.sidebar.markdown("---")
    st.sidebar.markdown("📊 **Reportes Disponibles:**")
    
    opciones_reportes = [
        "📊 Dashboard General",
        "📈 Análisis Financiero", 
        "📋 Comparación Histórica"
    ]
    
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "📊 Dashboard General"
    
    try:
        index_actual = opciones_reportes.index(st.session_state.selected_tab)
    except ValueError:
        index_actual = 0
        st.session_state.selected_tab = "📊 Dashboard General"
    
    selected_tab = st.sidebar.radio(
        "Selecciona un reporte:",
        opciones_reportes,
        index=index_actual
    )
    
    if st.session_state.selected_tab != selected_tab:
        st.session_state.selected_tab = selected_tab
    
    # Información del cliente (solo si hay datos cargados)
    if fuente_datos == "📁 Archivos Locales" and 'data' in st.session_state:
        data_actual = st.session_state.data
        st.sidebar.markdown("---")
        st.sidebar.markdown("💼 **Información del Cliente**")
        st.sidebar.markdown(f"**Cliente:** {data_actual.get('cliente_nombre', 'N/A')}")
        st.sidebar.markdown(f"**RUT:** {data_actual.get('cliente_rut', 'N/A')}")
        st.sidebar.markdown(f"**Período:** {data_actual.get('periodo', 'N/A')}")
        st.sidebar.markdown(f"**Generado por:** {data_actual.get('generado_por', 'N/A')}")
        
        st.sidebar.markdown("---")
        
        mostrar_excepciones_extraordinarias(data_actual, st.session_state.get('data_comparar'), 
                                          st.session_state.get('archivo_seleccionado'), 
                                          st.session_state.get('archivo_comparar'))
    
    return st.session_state.get('selected_tab', selected_tab), selected_config


def cargar_datos_sidebar(archivo_nombre):
    current_dir = pathlib.Path(__file__).parent.parent.resolve() / "data"
    json_file_path = current_dir / archivo_nombre
    
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error cargando datos en sidebar: {e}")
        return {}


def mostrar_excepciones_extraordinarias(data_actual, data_comparar, archivo_actual, archivo_comparar):
    st.sidebar.markdown("⚠️ **Excepciones Extraordinarias**")
    
    if not data_actual or not data_comparar:
        st.sidebar.info("No se pueden comparar los períodos")
        return
    
    if archivo_actual == archivo_comparar:
        st.sidebar.info("Selecciona períodos diferentes para comparar")
        return
    
    periodo_actual = data_actual.get('periodo', 'N/A')
    periodo_comparar = data_comparar.get('periodo', 'N/A')
    st.sidebar.caption(f"📊 Comparando: {periodo_actual} vs {periodo_comparar}")
    
    def calcular_cambio_porcentual(actual, anterior):
        if anterior == 0 or anterior is None:
            return 0 if actual == 0 else 100
        return ((actual - anterior) / anterior) * 100
    
    def formatear_numero(numero):
        if numero >= 1000000:
            return f"{numero/1000000:.1f}M"
        elif numero >= 1000:
            return f"{numero/1000:.0f}K"
        else:
            return f"{numero:,.0f}"
    
    cambios_significativos = []
    
    dotacion_actual = data_actual.get("resumen_dotacion", {})
    dotacion_comparar = data_comparar.get("resumen_dotacion", {})
    
    dot_actual = dotacion_actual.get("dotacion_final", 0)
    dot_anterior = dotacion_comparar.get("dotacion_final", 0)
    cambio_dot = calcular_cambio_porcentual(dot_actual, dot_anterior)
    if abs(cambio_dot) >= 30:
        cambios_significativos.append({
            "tipo": "kpi",
            "titulo": "👥 Dotación Final",
            "cambio": cambio_dot,
            "actual": dot_actual,
            "anterior": dot_anterior,
            "detalle": f"Cambió de {dot_anterior} a {dot_actual} trabajadores"
        })
    
    rot_actual = dotacion_actual.get("rotacion_pct", 0)
    rot_anterior = dotacion_comparar.get("rotacion_pct", 0)
    cambio_rot = calcular_cambio_porcentual(rot_actual, rot_anterior)
    if abs(cambio_rot) >= 30:
        cambios_significativos.append({
            "tipo": "kpi",
            "titulo": "🔄 Rotación %",
            "cambio": cambio_rot,
            "actual": rot_actual,
            "anterior": rot_anterior,
            "detalle": f"Cambió de {rot_anterior}% a {rot_actual}%"
        })
    
    costos_actual = data_actual.get("resumen_costos", {})
    costos_comparar = data_comparar.get("resumen_costos", {})
    
    hab_actual = costos_actual.get("total_haberes", 0)
    hab_anterior = costos_comparar.get("total_haberes", 0)
    cambio_hab = calcular_cambio_porcentual(hab_actual, hab_anterior)
    if abs(cambio_hab) >= 30:
        cambios_significativos.append({
            "tipo": "kpi",
            "titulo": "💰 Total Haberes",
            "cambio": cambio_hab,
            "actual": hab_actual,
            "anterior": hab_anterior,
            "detalle": f"Cambió de ${formatear_numero(hab_anterior)} a ${formatear_numero(hab_actual)}"
        })
    
    costo_actual = costos_actual.get("costo_empresa", 0)
    costo_anterior = costos_comparar.get("costo_empresa", 0)
    cambio_costo = calcular_cambio_porcentual(costo_actual, costo_anterior)
    if abs(cambio_costo) >= 30:
        cambios_significativos.append({
            "tipo": "kpi",
            "titulo": "🏢 Costo Empresa",
            "cambio": cambio_costo,
            "actual": costo_actual,
            "anterior": costo_anterior,
            "detalle": f"Cambió de ${formatear_numero(costo_anterior)} a ${formatear_numero(costo_actual)}"
        })
    
    rem_actual = data_actual.get("remuneracion_promedio", {}).get("global", 0)
    rem_anterior = data_comparar.get("remuneracion_promedio", {}).get("global", 0)
    cambio_rem = calcular_cambio_porcentual(rem_actual, rem_anterior)
    if abs(cambio_rem) >= 30:
        cambios_significativos.append({
            "tipo": "kpi",
            "titulo": "📊 Remuneración Promedio",
            "cambio": cambio_rem,
            "actual": rem_actual,
            "anterior": rem_anterior,
            "detalle": f"Cambió de ${formatear_numero(rem_anterior)} a ${formatear_numero(rem_actual)}"
        })
    
    horas_actual = data_actual.get("horas_extras", {})
    horas_comparar = data_comparar.get("horas_extras", {})
    
    h50_actual = horas_actual.get("total_horas_50", 0)
    h50_anterior = horas_comparar.get("total_horas_50", 0)
    cambio_h50 = calcular_cambio_porcentual(h50_actual, h50_anterior)
    if abs(cambio_h50) >= 30:
        cambios_significativos.append({
            "tipo": "kpi",
            "titulo": "⏰ Horas Extras 50%",
            "cambio": cambio_h50,
            "actual": h50_actual,
            "anterior": h50_anterior,
            "detalle": f"Cambió de {h50_anterior} a {h50_actual} horas"
        })
    
    h100_actual = horas_actual.get("total_horas_100", 0)
    h100_anterior = horas_comparar.get("total_horas_100", 0)
    cambio_h100 = calcular_cambio_porcentual(h100_actual, h100_anterior)
    if abs(cambio_h100) >= 30:
        cambios_significativos.append({
            "tipo": "kpi",
            "titulo": "⏰ Horas Extras 100%",
            "cambio": cambio_h100,
            "actual": h100_actual,
            "anterior": h100_anterior,
            "detalle": f"Cambió de {h100_anterior} a {h100_actual} horas"
        })
    
    incidencias_actual = []
    for key, value in data_actual.items():
        if key.startswith("incidencias_fase_") and isinstance(value, list):
            incidencias_actual.extend(value)
    
    for incidencia in incidencias_actual:
        cambios_significativos.append({
            "tipo": "incidencia",
            "titulo": f"⚠️ {incidencia.get('concepto', 'Incidencia')}",
            "nombre": incidencia.get('nombre', 'N/A'),
            "rut": incidencia.get('rut', 'N/A'),
            "concepto": incidencia.get('concepto', 'N/A'),
            "detalle": incidencia.get('detalle_actual', {})
        })
    
    if cambios_significativos:
        st.sidebar.markdown("**Cambios ≥30% e Incidencias:**")
        
        cambios_agrupados = {}
        for cambio in cambios_significativos:
            titulo = cambio['titulo']
            if titulo not in cambios_agrupados:
                cambios_agrupados[titulo] = []
            cambios_agrupados[titulo].append(cambio)
        
        i = 0
        for titulo, grupo in cambios_agrupados.items():
            col1, col2 = st.sidebar.columns([3, 1])
            
            with col1:
                if len(grupo) == 1:
                    cambio = grupo[0]
                    if cambio["tipo"] == "kpi":
                        signo = "+" if cambio["cambio"] > 0 else ""
                        st.markdown(f"• {cambio['titulo']}")
                        st.markdown(f"  {signo}{cambio['cambio']:.1f}%")
                    else:
                        st.markdown(f"• {cambio['titulo']}")
                        st.markdown(f"  {cambio['nombre']}")
                else:
                    st.markdown(f"• {titulo}")
                    if grupo[0]["tipo"] == "kpi":
                        cambios_valores = [abs(g["cambio"]) for g in grupo]
                        promedio = sum(cambios_valores) / len(cambios_valores)
                        st.markdown(f"  {len(grupo)} items (promedio: {promedio:.1f}%)")
                    else:
                        st.markdown(f"  {len(grupo)} incidencias")
            
            with col2:
                if st.button("...", key=f"detalle_{i}", help="Ver detalles"):
                    st.session_state[f"show_detail_{i}"] = not st.session_state.get(f"show_detail_{i}", False)
            
            if st.session_state.get(f"show_detail_{i}", False):
                with st.sidebar.expander(f"Detalles - {titulo}", expanded=True):
                    if len(grupo) == 1:
                        cambio = grupo[0]
                        if cambio["tipo"] == "kpi":
                            st.write(f"**Período anterior:** {cambio['anterior']}")
                            st.write(f"**Período actual:** {cambio['actual']}")
                            st.write(f"**Cambio:** {cambio['cambio']:.1f}%")
                            st.write(f"**Descripción:** {cambio['detalle']}")
                        else:
                            st.write(f"**Trabajador:** {cambio['nombre']}")
                            st.write(f"**RUT:** {cambio['rut']}")
                            st.write(f"**Concepto:** {cambio['concepto']}")
                            if cambio['detalle']:
                                st.write("**Detalles:**")
                                for key, value in cambio['detalle'].items():
                                    st.write(f"• {key}: {value}")
                    else:
                        st.write(f"**Total de elementos:** {len(grupo)}")
                        st.write("---")
                        for j, cambio in enumerate(grupo, 1):
                            st.write(f"**Elemento {j}:**")
                            if cambio["tipo"] == "kpi":
                                st.write(f"• Período anterior: {cambio['anterior']}")
                                st.write(f"• Período actual: {cambio['actual']}")
                                st.write(f"• Cambio: {cambio['cambio']:.1f}%")
                                st.write(f"• Descripción: {cambio['detalle']}")
                            else:
                                st.write(f"• Trabajador: {cambio['nombre']}")
                                st.write(f"• RUT: {cambio['rut']}")
                                st.write(f"• Concepto: {cambio['concepto']}")
                                if cambio['detalle']:
                                    st.write("• Detalles:")
                                    for key, value in cambio['detalle'].items():
                                        st.write(f"  - {key}: {value}")
                            if j < len(grupo):
                                st.write("---")
            
            i += 1
    else:
        st.sidebar.success("✅ Sin cambios ≥30% ni incidencias")
    
    st.sidebar.markdown("---")
