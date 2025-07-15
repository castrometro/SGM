"""
Funciones auxiliares para integrar la exportación Excel en Streamlit
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io

try:
    from .excel_templates import excel_generator
except ImportError:
    # Si falla el import relativo, intentar absoluto
    try:
        from utils.excel_templates import excel_generator
    except ImportError:
        # Si no se puede importar, crear un mock
        class MockExcelGenerator:
            def generate_esf_template(self, *args, **kwargs):
                return None
            def generate_eri_template(self, *args, **kwargs):
                return None
            def generate_movimientos_template(self, *args, **kwargs):
                return None
            def generate_ecp_template(self, *args, **kwargs):
                return None
            def workbook_to_bytes(self, workbook):
                return b""
        
        excel_generator = MockExcelGenerator()


def create_excel_download_button(
    data, 
    metadata, 
    report_type, 
    button_label="📥 Descargar Excel",
    file_prefix="reporte",
    extra_data=None
):
    """
    Crear botón de descarga Excel para diferentes tipos de reporte
    
    Args:
        data: Datos del reporte (data_esf, data_eri, etc.)
        metadata: Metadatos del reporte (cliente, período, etc.)
        report_type: Tipo de reporte ('esf', 'eri', 'ecp', 'movimientos')
        button_label: Etiqueta del botón
        file_prefix: Prefijo del archivo
        extra_data: Datos adicionales necesarios para algunos reportes
    """
    
    if not data and report_type != 'movimientos':
        st.info("ℹ️ No hay datos disponibles para exportar")
        return
    
    try:
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        cliente_name = metadata.get('cliente_nombre', 'cliente').replace(' ', '_')
        periodo = metadata.get('periodo', 'periodo').replace('-', '_')
        filename = f"{file_prefix}_{report_type}_{cliente_name}_{periodo}_{timestamp}.xlsx"
        
        # Generar workbook según el tipo de reporte
        workbook = None
        
        if report_type == 'esf':
            # Para ESF necesitamos también datos del ERI para incluir ganancia/pérdida del ejercicio
            data_eri = extra_data.get('data_eri') if extra_data else None
            workbook = excel_generator.generate_esf_template(data, metadata, data_eri)
        elif report_type == 'eri':
            workbook = excel_generator.generate_eri_template(data, metadata)
        elif report_type == 'ecp':
            # Para ECP necesitamos también datos del ERI
            data_eri = extra_data.get('data_eri') if extra_data else None
            workbook = excel_generator.generate_ecp_template(data, metadata, data_eri)
        elif report_type == 'movimientos':
            # Para movimientos necesitamos el DataFrame
            df_movimientos = extra_data.get('df_movimientos') if extra_data else pd.DataFrame()
            tipo_vista = extra_data.get('tipo_vista', 'Movimientos') if extra_data else 'Movimientos'
            if not df_movimientos.empty:
                workbook = excel_generator.generate_movimientos_template(df_movimientos, metadata, tipo_vista)
        
        if workbook:
            # Convertir a bytes
            excel_data = excel_generator.workbook_to_bytes(workbook)
            
            # Crear botón de descarga
            st.download_button(
                label=button_label,
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help=f"Descargar {report_type.upper()} en formato Excel con formato profesional"
            )
            
            # Mostrar información adicional
            with st.expander("ℹ️ Información del archivo Excel"):
                st.success(f"✅ **Archivo generado:** {filename}")
                st.info(f"""
                📋 **Contenido del Excel:**
                • Reporte principal: {report_type.upper()}
                • Hoja de metadatos con información del cliente
                • Formato profesional con estilos y colores
                • Datos organizados y totales calculados
                """)
                
                st.markdown("**📊 Detalles del reporte:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"• **Cliente:** {metadata.get('cliente_nombre', 'N/A')}")
                    st.write(f"• **Período:** {metadata.get('periodo', 'N/A')}")
                with col2:
                    st.write(f"• **Moneda:** {metadata.get('moneda', 'CLP')}")
                    st.write(f"• **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        else:
            st.error("❌ Error al generar el archivo Excel")
            
    except Exception as e:
        st.error(f"❌ Error al generar Excel: {str(e)}")
        
        # Debug information
        with st.expander("🔧 Información de debug"):
            st.error(f"Error detallado: {e}")
            st.write(f"Tipo de reporte: {report_type}")
            st.write(f"Datos disponibles: {data is not None}")
            st.write(f"Metadatos: {metadata}")


def create_template_download_section():
    """
    Crear sección con templates vacíos para diferentes reportes
    """
    st.markdown("### 📋 Plantillas Excel")
    st.info("""
    💡 **Plantillas disponibles:** Descarga plantillas Excel vacías con el formato profesional 
    del SGM para crear tus propios reportes o para entender la estructura de los datos.
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Template ESF", help="Plantilla Estado de Situación Financiera"):
            # Generar template vacío para ESF
            template_data = create_empty_esf_template()
            st.download_button(
                label="📥 Descargar Template ESF",
                data=template_data,
                file_name="template_esf.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📈 Template ERI", help="Plantilla Estado de Resultado Integral"):
            template_data = create_empty_eri_template()
            st.download_button(
                label="📥 Descargar Template ERI",
                data=template_data,
                file_name="template_eri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col3:
        if st.button("📋 Template ECP", help="Plantilla Estado de Cambios en Patrimonio"):
            template_data = create_empty_ecp_template()
            st.download_button(
                label="📥 Descargar Template ECP",
                data=template_data,
                file_name="template_ecp.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col4:
        if st.button("📑 Template Movimientos", help="Plantilla Movimientos Contables"):
            template_data = create_empty_movimientos_template()
            st.download_button(
                label="📥 Descargar Template Movimientos",
                data=template_data,
                file_name="template_movimientos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


def create_empty_esf_template():
    """Crear template vacío para ESF"""
    try:
        metadata_sample = {
            'cliente_nombre': '[NOMBRE DEL CLIENTE]',
            'periodo': '[PERÍODO]', 
            'moneda': 'CLP',
            'idioma': 'Español'
        }
        
        # Estructura básica ESF vacía
        data_esf_sample = {
            "activos": {
                "corrientes": {
                    "grupos": {
                        "Ejemplo Grupo Activos": {
                            "cuentas": [
                                {
                                    "codigo": "11001",
                                    "nombre_es": "Ejemplo Cuenta Activo",
                                    "saldo_final": 0
                                }
                            ]
                        }
                    },
                    "total": 0
                },
                "no_corrientes": {
                    "grupos": {},
                    "total": 0
                }
            },
            "pasivos": {
                "corrientes": {
                    "grupos": {},
                    "total": 0
                },
                "no_corrientes": {
                    "grupos": {},
                    "total": 0
                }
            },
            "patrimonio": {
                "grupos": {},
                "total": 0
            }
        }
        
        workbook = excel_generator.generate_esf_template(data_esf_sample, metadata_sample)
        return excel_generator.workbook_to_bytes(workbook)
    except:
        return b""


def create_empty_eri_template():
    """Crear template vacío para ERI"""
    try:
        metadata_sample = {
            'cliente_nombre': '[NOMBRE DEL CLIENTE]',
            'periodo': '[PERÍODO]',
            'moneda': 'CLP',
            'idioma': 'Español'
        }
        
        data_eri_sample = {
            "ganancias_brutas": {
                "grupos": {
                    "Ejemplo Grupo Ingresos": {
                        "cuentas": [
                            {
                                "codigo": "41001",
                                "nombre_es": "Ejemplo Cuenta Ingreso",
                                "saldo_final": 0
                            }
                        ]
                    }
                },
                "total": 0
            },
            "ganancia_perdida": {
                "grupos": {},
                "total": 0
            }
        }
        
        workbook = excel_generator.generate_eri_template(data_eri_sample, metadata_sample)
        return excel_generator.workbook_to_bytes(workbook)
    except:
        return b""


def create_empty_ecp_template():
    """Crear template vacío para ECP"""
    try:
        metadata_sample = {
            'cliente_nombre': '[NOMBRE DEL CLIENTE]',
            'periodo': '[PERÍODO]',
            'moneda': 'CLP',
            'idioma': 'Español'
        }
        
        data_ecp_sample = {
            "patrimonio": {
                "capital": {
                    "saldo_anterior": 0,
                    "cambios": 0
                },
                "otras_reservas": {
                    "saldo_anterior": 0,
                    "cambios": 0
                }
            }
        }
        
        workbook = excel_generator.generate_ecp_template(data_ecp_sample, metadata_sample)
        return excel_generator.workbook_to_bytes(workbook)
    except:
        return b""


def create_empty_movimientos_template():
    """Crear template vacío para movimientos"""
    try:
        metadata_sample = {
            'cliente_nombre': '[NOMBRE DEL CLIENTE]',
            'periodo': '[PERÍODO]',
            'moneda': 'CLP',
            'idioma': 'Español'
        }
        
        # DataFrame de ejemplo vacío
        df_sample = pd.DataFrame({
            'Fecha': ['2024-01-01'],
            'Código Cuenta': ['11001'],
            'Nombre Cuenta': ['Ejemplo Cuenta'],
            'Debe': [0],
            'Haber': [0],
            'Descripción': ['Ejemplo Movimiento']
        })
        
        workbook = excel_generator.generate_movimientos_template(df_sample, metadata_sample)
        return excel_generator.workbook_to_bytes(workbook)
    except:
        return b""


def show_excel_export_help():
    """Mostrar ayuda sobre la exportación Excel"""
    with st.expander("❓ Ayuda - Exportación Excel"):
        st.markdown("""
        ### 📋 Funcionalidades de Exportación Excel
        
        **🎯 Tipos de exportación disponibles:**
        
        1. **📊 Estado de Situación Financiera (ESF)**
           - Activos corrientes y no corrientes
           - Pasivos corrientes y no corrientes  
           - Patrimonio
           - Totales automáticos
        
        2. **📈 Estado de Resultado Integral (ERI)**
           - Ganancias brutas
           - Ganancia/pérdida
           - Resultado antes de impuestos
           - Total general
        
        3. **📋 Estado de Cambios en Patrimonio (ECP)**
           - Saldos iniciales y finales
           - Cambios en capital
           - Resultado del ejercicio
           - Movimientos de reservas
        
        4. **📑 Movimientos Contables**
           - Lista completa de movimientos
           - Filtros aplicados
           - Totales de debe y haber
        
        **✨ Características del Excel generado:**
        
        - 🎨 **Formato profesional** con colores corporativos
        - 📊 **Totales automáticos** calculados
        - 📋 **Hoja de metadatos** con información del reporte
        - 🗂️ **Organización clara** por secciones
        - 💾 **Compatible** con Excel y LibreOffice
        
        **📁 Nombre de archivos:**
        ```
        reporte_[tipo]_[cliente]_[periodo]_[timestamp].xlsx
        ```
        
        **💡 Consejos:**
        - Los archivos incluyen toda la información visible en pantalla
        - Los filtros aplicados se reflejan en el Excel
        - La moneda se mantiene según la configuración del cliente
        - El idioma se aplica según la selección del usuario
        """)
