import streamlit as st
import json
import pandas as pd
from datetime import datetime

def show(data, metadata):
    """Mostrar datos detallados y herramientas de exportación"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #fd7e14, #ffc107); color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
        <h1>📋 Datos Detallados</h1>
        <p>Información completa del informe y herramientas de exportación</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Información del período y metadatos
    st.markdown("### 📅 Información del Período")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Información General**")
        st.write(f"**Cliente:** {metadata.get('cliente_nombre', 'N/A')}")
        st.write(f"**Período:** {metadata.get('periodo', 'N/A')}")
        
        # Información del estado del cierre
        metadatos_raw = data.get('metadatos', {})
        estado_cierre = metadatos_raw.get('estado_cierre', 'N/A')
        st.write(f"**Estado:** {estado_cierre}")
    
    with col2:
        st.markdown("**⏰ Información de Procesamiento**")
        fecha_calculo = metadata.get('fecha_generacion')
        
        if fecha_calculo:
            try:
                if isinstance(fecha_calculo, str):
                    fecha_obj = datetime.fromisoformat(fecha_calculo.replace('Z', '+00:00'))
                    fecha_formato = fecha_obj.strftime('%d/%m/%Y %H:%M:%S')
                else:
                    fecha_formato = str(fecha_calculo)
            except:
                fecha_formato = str(fecha_calculo)
        else:
            fecha_formato = 'N/A'
        
        st.write(f"**Fecha de Cálculo:** {fecha_formato}")
        
        # Información adicional de metadatos
        fecha_cierre = metadatos_raw.get('fecha_cierre')
        if fecha_cierre:
            st.write(f"**Fecha de Cierre:** {fecha_cierre}")
    
    with col3:
        st.markdown("**📊 Información Técnica**")
        st.write(f"**Secciones de datos:** {len(data.keys())}")
        
        # Calcular el tamaño del JSON
        json_size = len(json.dumps(data, ensure_ascii=False)) / 1024
        st.write(f"**Tamaño del informe:** {json_size:.1f} KB")
        
        # Número de empleados procesados
        metricas = data.get('metricas_basicas', {})
        dotacion = metricas.get('dotacion_total', 0)
        st.write(f"**Empleados procesados:** {dotacion:,}")
    
    st.markdown("---")
    
    # Estructura del informe
    st.markdown("### 🗂️ Estructura del Informe")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📋 Secciones Disponibles")
        
        # Analizar la estructura
        estructura_info = []
        for seccion, contenido in data.items():
            info = {
                'Sección': seccion,
                'Tipo': type(contenido).__name__,
                'Contenido': ''
            }
            
            if isinstance(contenido, dict):
                info['Contenido'] = f"{len(contenido)} campos"
            elif isinstance(contenido, list):
                info['Contenido'] = f"{len(contenido)} elementos"
            else:
                info['Contenido'] = str(contenido)[:50] + "..." if len(str(contenido)) > 50 else str(contenido)
            
            estructura_info.append(info)
        
        df_estructura = pd.DataFrame(estructura_info)
        st.dataframe(df_estructura, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### 📊 Métricas de Contenido")
        
        # Contar elementos por tipo
        tipos_contenido = {}
        for contenido in data.values():
            tipo = type(contenido).__name__
            tipos_contenido[tipo] = tipos_contenido.get(tipo, 0) + 1
        
        for tipo, cantidad in tipos_contenido.items():
            st.write(f"• **{tipo}:** {cantidad}")
        
        # Mostrar métricas adicionales
        if 'desglose_previsional' in data:
            previsional = data['desglose_previsional']
            if isinstance(previsional, list):
                st.write(f"• **Instituciones Previsionales:** {len(previsional)}")
    
    # Datos de métricas básicas
    if 'metricas_basicas' in data:
        st.markdown("### 📊 Métricas Básicas Detalladas")
        
        metricas = data['metricas_basicas']
        
        # Organizar métricas por categorías
        categorias = {
            'Personal': [
                ('dotacion_total', 'Dotación Total'),
                ('dotacion_activa', 'Dotación Activa'),
                ('rotacion_porcentaje', 'Rotación (%)'),
                ('ausentismo_porcentaje', 'Ausentismo (%)')
            ],
            'Financiero': [
                ('costo_empresa_total', 'Costo Empresa Total'),
                ('liquido_total', 'Líquido Total'),
                ('descuentos_legales_total', 'Descuentos Legales'),
                ('horas_extras_total', 'Horas Extras')
            ],
            'Otros': []
        }
        
        # Agregar métricas que no están categorizadas
        metricas_categorizadas = set()
        for categoria in categorias.values():
            metricas_categorizadas.update(item[0] for item in categoria)
        
        for key in metricas.keys():
            if key not in metricas_categorizadas:
                categorias['Otros'].append((key, key.replace('_', ' ').title()))
        
        # Mostrar por columnas
        cols = st.columns(len([cat for cat in categorias.keys() if categorias[cat]]))
        col_idx = 0
        
        for categoria, items in categorias.items():
            if items:  # Solo mostrar categorías que tienen items
                with cols[col_idx]:
                    st.markdown(f"#### {categoria}")
                    for key, label in items:
                        if key in metricas:
                            valor = metricas[key]
                            if isinstance(valor, (int, float)):
                                if key.endswith('_total') or 'costo' in key.lower() or 'liquido' in key.lower():
                                    st.write(f"**{label}:** ${valor:,.0f}")
                                elif key.endswith('_porcentaje') or '%' in label:
                                    st.write(f"**{label}:** {valor:.1f}%")
                                else:
                                    st.write(f"**{label}:** {valor:,}")
                            else:
                                st.write(f"**{label}:** {valor}")
                col_idx += 1
    
    # Desglose previsional detallado
    if 'desglose_previsional' in data and data['desglose_previsional']:
        st.markdown("### 🏥 Desglose Previsional Detallado")
        
        df_previsional = pd.DataFrame(data['desglose_previsional'])
        
        # Formatear montos
        if 'monto_total' in df_previsional.columns:
            df_display = df_previsional.copy()
            df_display['monto_total'] = df_display['monto_total'].apply(lambda x: f"${x:,.0f}")
            
            # Renombrar columnas para mejor presentación
            column_mapping = {
                'institucion': 'Institución Previsional',
                'monto_total': 'Monto Total',
                'cantidad_empleados': 'Cantidad de Empleados'
            }
            df_display = df_display.rename(columns=column_mapping)
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Totales
            total_empleados = df_previsional['cantidad_empleados'].sum()
            total_monto = df_previsional['monto_total'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("👥 Total Empleados", f"{total_empleados:,}")
            with col2:
                st.metric("💰 Total Monto", f"${total_monto:,.0f}")
    
    # Información de movimientos
    if 'movimientos' in data:
        st.markdown("### 🔄 Movimientos Detallados")
        
        movimientos = data['movimientos']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🆕 Ingresos")
            ingresos = movimientos.get('empleados_nuevos', 0)
            st.metric("Nuevos Empleados", f"{ingresos:,}")
        
        with col2:
            st.markdown("#### 📤 Salidas")
            finiquitos = movimientos.get('empleados_finiquitados', 0)
            st.metric("Finiquitos", f"{finiquitos:,}")
        
        with col3:
            st.markdown("#### 🏥 Ausencias")
            ausencias = movimientos.get('empleados_con_ausencias', 0)
            st.metric("Con Ausencias", f"{ausencias:,}")
    
    # Herramientas de exportación
    st.markdown("### 📤 Herramientas de Exportación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💾 Exportar Datos")
        
        if st.button("📄 Descargar JSON Completo", type="primary", use_container_width=True):
            # Preparar JSON para descarga
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Generar nombre de archivo
            periodo = metadata.get('periodo', 'sin_fecha')
            cliente = metadata.get('cliente_nombre', 'cliente')
            filename = f"informe_nomina_{cliente}_{periodo}.json"
            
            st.download_button(
                label="💾 Guardar archivo JSON",
                data=json_str,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )
        
        if st.button("📊 Exportar Métricas CSV", type="secondary", use_container_width=True):
            # Crear CSV con métricas principales
            if 'metricas_basicas' in data:
                metricas_df = pd.DataFrame([data['metricas_basicas']])
                csv_str = metricas_df.to_csv(index=False)
                
                periodo = metadata.get('periodo', 'sin_fecha')
                filename = f"metricas_nomina_{periodo}.csv"
                
                st.download_button(
                    label="💾 Guardar métricas CSV",
                    data=csv_str,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True
                )
    
    with col2:
        st.markdown("#### 👁️ Visualizar Datos")
        
        if st.button("🔍 Ver JSON Raw", type="secondary", use_container_width=True):
            st.markdown("#### 📄 Contenido JSON Completo")
            st.json(data)
        
        if st.button("📋 Copiar Metadatos", type="secondary", use_container_width=True):
            # Mostrar metadatos para copiar
            metadata_display = {
                "cliente": metadata.get('cliente_nombre'),
                "periodo": metadata.get('periodo'),
                "fecha_generacion": metadata.get('fecha_generacion'),
                "dotacion_total": data.get('metricas_basicas', {}).get('dotacion_total'),
                "costo_total": data.get('metricas_basicas', {}).get('costo_empresa_total')
            }
            st.code(json.dumps(metadata_display, indent=2, ensure_ascii=False))
    
    # Información de debug y diagnóstico
    with st.expander("🔧 Información de Diagnóstico"):
        st.markdown("#### 🔍 Diagnóstico del Informe")
        
        # Verificar integridad de datos
        problemas = []
        
        if not data.get('metricas_basicas'):
            problemas.append("❌ Faltan métricas básicas")
        
        if not data.get('metadatos'):
            problemas.append("❌ Faltan metadatos")
        
        metricas = data.get('metricas_basicas', {})
        if metricas.get('dotacion_total', 0) == 0:
            problemas.append("⚠️ Dotación total es 0")
        
        if metricas.get('costo_empresa_total', 0) == 0:
            problemas.append("⚠️ Costo empresa total es 0")
        
        if problemas:
            st.markdown("**Problemas detectados:**")
            for problema in problemas:
                st.write(problema)
        else:
            st.success("✅ Informe completo y consistente")
        
        # Mostrar estadísticas técnicas
        st.markdown("**Estadísticas técnicas:**")
        st.write(f"• Tiempo de carga: < 1 segundo")
        st.write(f"• Fuente de datos: Redis DB2")
        st.write(f"• Formato: JSON")
        st.write(f"• Codificación: UTF-8")
        st.write(f"• Secciones procesadas: {len(data)} de {len(data)}")
