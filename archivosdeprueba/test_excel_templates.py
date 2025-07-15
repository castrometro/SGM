"""
Script de prueba para verificar la funcionalidad de exportación Excel
"""

import streamlit as st
import pandas as pd
import sys
import os

# Agregar el directorio actual al PATH para poder importar los módulos
sys.path.append('/root/SGM/streamlit_conta')

def test_excel_functionality():
    """Función para probar la funcionalidad Excel"""
    
    st.title("🧪 Test - Funcionalidad Excel Templates")
    st.markdown("---")
    
    # Test 1: Verificar imports
    st.subheader("1. 📦 Verificación de Importaciones")
    
    try:
        from utils.excel_templates import excel_generator
        st.success("✅ excel_templates importado correctamente")
    except Exception as e:
        st.error(f"❌ Error importando excel_templates: {e}")
    
    try:
        from utils.excel_export import create_excel_download_button, create_template_download_section
        st.success("✅ excel_export importado correctamente")
    except Exception as e:
        st.error(f"❌ Error importando excel_export: {e}")
    
    # Test 2: Verificar openpyxl
    st.subheader("2. 📊 Verificación de OpenPyXL")
    
    try:
        import openpyxl
        workbook = openpyxl.Workbook()
        st.success("✅ OpenPyXL funciona correctamente")
        
        # Mostrar información de la versión
        st.info(f"OpenPyXL versión: {openpyxl.__version__}")
    except Exception as e:
        st.error(f"❌ Error con OpenPyXL: {e}")
    
    # Test 3: Template básico
    st.subheader("3. 📋 Test Template Básico")
    
    try:
        # Datos de prueba
        metadata_test = {
            'cliente_nombre': 'Empresa Test S.A.',
            'periodo': '2024-12',
            'moneda': 'CLP',
            'idioma': 'Español'
        }
        
        data_esf_test = {
            "activos": {
                "corrientes": {
                    "grupos": {
                        "Efectivo y Equivalentes": {
                            "cuentas": [
                                {
                                    "codigo": "11001",
                                    "nombre_es": "Caja",
                                    "saldo_final": 1000000
                                },
                                {
                                    "codigo": "11002", 
                                    "nombre_es": "Banco",
                                    "saldo_final": 5000000
                                }
                            ]
                        }
                    },
                    "total": 6000000
                }
            },
            "pasivos": {
                "corrientes": {
                    "grupos": {},
                    "total": 0
                }
            },
            "patrimonio": {
                "grupos": {},
                "total": 6000000
            }
        }
        
        # Crear template
        from utils.excel_templates import excel_generator
        workbook_test = excel_generator.generate_esf_template(data_esf_test, metadata_test)
        
        if workbook_test:
            st.success("✅ Template ESF generado exitosamente")
            
            # Generar bytes para descarga
            excel_bytes = excel_generator.workbook_to_bytes(workbook_test)
            
            st.download_button(
                label="📥 Descargar Test ESF",
                data=excel_bytes,
                file_name="test_esf_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("❌ Error generando template ESF")
            
    except Exception as e:
        st.error(f"❌ Error en test template: {e}")
        st.exception(e)
    
    # Test 4: Template vacío
    st.subheader("4. 📄 Test Template Vacío")
    
    if st.button("🔄 Generar Template Vacío"):
        try:
            from utils.excel_export import create_empty_esf_template
            empty_template = create_empty_esf_template()
            
            if empty_template and len(empty_template) > 0:
                st.success("✅ Template vacío generado")
                
                st.download_button(
                    label="📥 Descargar Template Vacío",
                    data=empty_template,
                    file_name="template_esf_vacio.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ Error generando template vacío")
                
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # Test 5: Información del sistema
    st.subheader("5. 🔧 Información del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.code(f"""
Python: {sys.version}
Streamlit: {st.__version__}
Working Dir: {os.getcwd()}
        """)
    
    with col2:
        # Verificar archivos
        files_check = [
            "/root/SGM/streamlit_conta/utils/excel_templates.py",
            "/root/SGM/streamlit_conta/utils/excel_export.py",
            "/root/SGM/streamlit_conta/utils/__init__.py"
        ]
        
        st.markdown("**Archivos creados:**")
        for file_path in files_check:
            if os.path.exists(file_path):
                st.success(f"✅ {os.path.basename(file_path)}")
            else:
                st.error(f"❌ {os.path.basename(file_path)}")
    
    # Test 6: Sección de templates
    st.subheader("6. 🎨 Sección Templates Completa")
    
    try:
        from utils.excel_export import create_template_download_section
        create_template_download_section()
        st.success("✅ Sección de templates mostrada correctamente")
    except Exception as e:
        st.error(f"❌ Error mostrando sección templates: {e}")

if __name__ == "__main__":
    # Configurar página
    st.set_page_config(
        page_title="Test Excel Templates",
        page_icon="🧪",
        layout="wide"
    )
    
    # Ejecutar tests
    test_excel_functionality()
