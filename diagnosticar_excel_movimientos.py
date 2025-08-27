#!/usr/bin/env python3
# Script para diagnosticar el contenido del archivo Excel de movimientos_mes

import pandas as pd
import os
import sys

# Agregar el directorio del proyecto al path
project_root = "/root/SGM/backend"
sys.path.append(project_root)

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sgm_backend.settings")
import django
django.setup()

from payroll.models.models_fase_1 import ArchivoSubido

def diagnosticar_excel():
    # Obtener el último archivo de movimientos_mes subido
    ultimo_archivo = ArchivoSubido.objects.filter(
        tipo_archivo='movimientos_mes'
    ).order_by('-id').first()
    
    if not ultimo_archivo:
        print("❌ No se encontraron archivos de movimientos_mes")
        return
    
    print(f"🔍 Analizando archivo: {ultimo_archivo.archivo.name}")
    print(f"📁 Ruta completa: {ultimo_archivo.archivo.path}")
    
    try:
        # Leer Excel
        excel_file = pd.ExcelFile(ultimo_archivo.archivo.path)
        print(f"📋 Hojas disponibles: {excel_file.sheet_names}")
        
        # Analizar hoja 'Altas y Bajas'
        if 'Altas y Bajas' in excel_file.sheet_names:
            print("\n🔍 ANÁLISIS DE HOJA 'Altas y Bajas':")
            
            # Leer con header=2 (fila 3)
            df = pd.read_excel(ultimo_archivo.archivo.path, sheet_name='Altas y Bajas', header=2)
            
            print(f"📊 Columnas encontradas: {list(df.columns)}")
            print(f"📏 Filas: {len(df)}")
            
            # Verificar si existe alguna variante de la columna Alta/Baja
            columnas_relevantes = [col for col in df.columns if 'alta' in str(col).lower() or 'baja' in str(col).lower()]
            print(f"🎯 Columnas con 'Alta' o 'Baja': {columnas_relevantes}")
            
            # Mostrar primeras filas
            print("\n📝 PRIMERAS 5 FILAS DE DATOS:")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            print(df.head())
            
            # Analizar la columna Alta/Baja específicamente
            if 'Alta / Baja' in df.columns:
                print(f"\n🔍 ANÁLISIS DE COLUMNA 'Alta / Baja':")
                columna_alta_baja = df['Alta / Baja']
                print(f"📊 Valores únicos: {columna_alta_baja.unique()}")
                print(f"📊 Conteo de valores:")
                print(columna_alta_baja.value_counts(dropna=False))
                
                # Mostrar algunos valores específicos
                print(f"\n📋 PRIMEROS 10 VALORES:")
                for i, valor in enumerate(columna_alta_baja.head(10)):
                    print(f"  Fila {i+4}: '{valor}' (tipo: {type(valor)})")
            
            # Verificar si hay valores no nulos
            df_clean = df.dropna(how='all')
            print(f"\n📊 Filas después de limpiar vacías: {len(df_clean)}")
            
            # Analizar filas que tienen RUT y Nombre
            df_validas = df_clean[df_clean['Rut'].notna() & df_clean['Nombre'].notna()]
            print(f"📊 Filas con RUT y Nombre válidos: {len(df_validas)}")
            
            if len(df_validas) > 0 and 'Alta / Baja' in df_validas.columns:
                print(f"\n🎯 VALORES DE 'Alta / Baja' EN FILAS VÁLIDAS:")
                for idx, row in df_validas.iterrows():
                    valor_alta_baja = row['Alta / Baja']
                    print(f"  Fila {idx+4}: RUT={row['Rut']}, Nombre={row['Nombre'][:20]}..., Alta/Baja='{valor_alta_baja}' ({type(valor_alta_baja)})")
        
    except Exception as e:
        print(f"❌ Error analizando archivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnosticar_excel()
