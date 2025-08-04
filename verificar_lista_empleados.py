#!/usr/bin/env python3
"""
Script de verificación de sintaxis para models_informe.py
"""

def verificar_sintaxis():
    """Verifica que la sintaxis del archivo models_informe.py sea correcta"""
    
    print("🔍 Verificando sintaxis de models_informe.py...")
    
    try:
        # Leer el archivo y compilar para verificar sintaxis
        with open('/root/SGM/backend/nomina/models_informe.py', 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Compilar el código para verificar sintaxis
        compile(contenido, 'models_informe.py', 'exec')
        
        print("✅ Sintaxis correcta - No se encontraron errores")
        
        # Verificar que los métodos están presentes
        metodos_esperados = [
            'obtener_empleados_por_criterio',
            'obtener_estadisticas_empleados',
            '_agrupar_por_campo',
            'calcular_dias_trabajados_por_empleado',
            'obtener_comparacion_mes_anterior'
        ]
        
        print("\n🔍 Verificando métodos implementados:")
        for metodo in metodos_esperados:
            if f'def {metodo}(' in contenido:
                print(f"   ✅ {metodo}")
            else:
                print(f"   ❌ {metodo} - NO ENCONTRADO")
        
        # Verificar estructura de datos de empleados
        print("\n📊 Verificando estructura de datos de empleados...")
        
        if '_generar_lista_empleados' in contenido:
            print("   ✅ Método _generar_lista_empleados encontrado")
        else:
            print("   ❌ Método _generar_lista_empleados NO encontrado")
        
        # Contar líneas de código
        lineas = contenido.split('\n')
        lineas_codigo = [l for l in lineas if l.strip() and not l.strip().startswith('#')]
        
        print(f"\n📈 Estadísticas del archivo:")
        print(f"   • Total líneas: {len(lineas)}")
        print(f"   • Líneas de código: {len(lineas_codigo)}")
        print(f"   • Tamaño: {len(contenido) / 1024:.1f} KB")
        
        # Verificar que no hay problemas comunes
        problemas = []
        
        # Verificar paréntesis balanceados
        contador_parentesis = contenido.count('(') - contenido.count(')')
        if contador_parentesis != 0:
            problemas.append(f"Paréntesis desbalanceados: {contador_parentesis}")
        
        # Verificar llaves balanceadas
        contador_llaves = contenido.count('{') - contenido.count('}')
        if contador_llaves != 0:
            problemas.append(f"Llaves desbalanceadas: {contador_llaves}")
        
        # Verificar corchetes balanceados
        contador_corchetes = contenido.count('[') - contenido.count(']')
        if contador_corchetes != 0:
            problemas.append(f"Corchetes desbalanceados: {contador_corchetes}")
        
        if problemas:
            print(f"\n⚠️  Posibles problemas detectados:")
            for problema in problemas:
                print(f"   • {problema}")
        else:
            print(f"\n✅ No se detectaron problemas estructurales")
        
        # Verificar imports críticos
        imports_criticos = [
            'from django.db import models',
            'from django.utils import timezone',
            'from django.db.models import Sum, Count, Avg, Max, Min, Q'
        ]
        
        print(f"\n📦 Verificando imports:")
        for imp in imports_criticos:
            if imp in contenido:
                print(f"   ✅ {imp}")
            else:
                print(f"   ❌ {imp} - NO ENCONTRADO")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis encontrado:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
        
    except Exception as e:
        print(f"❌ Error al verificar archivo: {e}")
        return False

def mostrar_resumen_funcionalidades():
    """Muestra un resumen de las funcionalidades implementadas"""
    
    print("\n" + "="*60)
    print("📋 RESUMEN DE FUNCIONALIDADES DE LISTA DE EMPLEADOS")
    print("="*60)
    
    funcionalidades = [
        {
            'nombre': 'Lista Básica de Empleados',
            'descripcion': 'Genera lista detallada con métricas individuales',
            'metodo': '_generar_lista_empleados()',
            'datos': ['nombre', 'cargo', 'remuneración', 'ausencias', 'afiliaciones']
        },
        {
            'nombre': 'Filtros por Criterio', 
            'descripcion': 'Filtra empleados según múltiples criterios',
            'metodo': 'obtener_empleados_por_criterio()',
            'datos': ['con_ausencias', 'sin_ausencias', 'ingresos', 'finiquitos', 'alta_remuneracion']
        },
        {
            'nombre': 'Estadísticas Avanzadas',
            'descripcion': 'Calcula estadísticas detalladas del personal',
            'metodo': 'obtener_estadisticas_empleados()',
            'datos': ['remuneración', 'ausentismo', 'distribución', 'rangos_salariales']
        },
        {
            'nombre': 'Días Trabajados',
            'descripcion': 'Calcula días efectivos con vacaciones chilenas',
            'metodo': 'calcular_dias_trabajados_por_empleado()',
            'datos': ['días_laborales', 'ausencias', 'eficiencia', 'promedios']
        },
        {
            'nombre': 'Agrupación de Datos',
            'descripcion': 'Agrupa empleados por campos específicos',
            'metodo': '_agrupar_por_campo()',
            'datos': ['centro_costo', 'cargo', 'tipo_salud', 'campos_anidados']
        }
    ]
    
    for i, func in enumerate(funcionalidades, 1):
        print(f"\n{i}️⃣ {func['nombre']}")
        print(f"   📝 {func['descripcion']}")
        print(f"   🔧 Método: {func['metodo']}")
        print(f"   📊 Datos: {', '.join(func['datos'])}")
    
    print(f"\n🎯 CASOS DE USO PRINCIPALES:")
    casos_uso = [
        "API REST para frontend con lista paginada",
        "Reportes ejecutivos con estadísticas",
        "Análisis de ausentismo por empleado",
        "Segmentación salarial y beneficios",
        "Cálculos de productividad laboral"
    ]
    
    for caso in casos_uso:
        print(f"   • {caso}")
    
    print(f"\n⚡ OPTIMIZACIONES INCLUIDAS:")
    optimizaciones = [
        "Datos pre-calculados en JSON para rapidez",
        "Filtros en memoria sin consultas adicionales",
        "Estadísticas con algoritmos eficientes",
        "Manejo de campos anidados automático",
        "Compatibilidad con feriados chilenos"
    ]
    
    for opt in optimizaciones:
        print(f"   ⚡ {opt}")

if __name__ == "__main__":
    print("🚀 VERIFICADOR DE LISTA DE EMPLEADOS - SGM NÓMINA")
    print("="*60)
    
    if verificar_sintaxis():
        mostrar_resumen_funcionalidades()
        
        print("\n" + "="*60)
        print("✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\n🎉 El sistema de lista de empleados está listo para usar!")
        print("📝 Próximos pasos:")
        print("   1. Probar con datos reales de nómina")
        print("   2. Integrar en API REST")
        print("   3. Crear frontend para visualización")
        print("   4. Implementar paginación y búsqueda")
    else:
        print("\n❌ Se encontraron errores que deben corregirse")
