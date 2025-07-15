import streamlit as st

# Importar utilidades de exportación Excel
try:
    from utils.excel_export import create_template_download_section, show_excel_export_help
except ImportError:
    # Si no se puede importar, crear funciones dummy
    def create_template_download_section():
        st.warning("⚠️ Funcionalidad de templates Excel no disponible")
    def show_excel_export_help():
        pass

def show_excel_tools_section():
    """
    Muestra la sección completa de herramientas Excel incluyendo templates y guía.
    """
    st.markdown("## 📊 Herramientas Excel")
    
    # Sección de templates Excel
    st.markdown("### 📋 Templates y Plantillas")
    create_template_download_section()
    
    # Ayuda sobre exportación Excel
    st.markdown("---")
    st.markdown("### 📖 Guía de Exportación Excel")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("""
        🎯 **¿Nuevo en las exportaciones Excel?** Haz clic en "Ver Guía Completa" para conocer 
        todas las funcionalidades disponibles y cómo aprovechar al máximo los reportes en Excel.
        """)
    with col2:
        if st.button("📚 Ver Guía Completa", help="Mostrar ayuda detallada sobre Excel"):
            show_excel_export_help()

def show_templates_only():
    """
    Muestra solo la sección de templates sin la guía.
    """
    st.markdown("### 📋 Templates Excel")
    create_template_download_section()

def show_help_only():
    """
    Muestra solo la sección de ayuda/guía.
    """
    st.markdown("### 📖 Guía de Exportación Excel")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("""
        🎯 **¿Nuevo en las exportaciones Excel?** Haz clic en "Ver Guía Completa" para conocer 
        todas las funcionalidades disponibles y cómo aprovechar al máximo los reportes en Excel.
        """)
    with col2:
        if st.button("📚 Ver Guía Completa", help="Mostrar ayuda detallada sobre Excel"):
            show_excel_export_help()
