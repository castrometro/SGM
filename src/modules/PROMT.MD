Claro, aquí te dejo un prompt completo y detallado que puedes usar para futuras refactorizaciones:

---

## 📋 PROMPT PARA REFACTORIZACIÓN DE PÁGINAS

```
Necesito refactorizar la página [NOMBRE_PÁGINA] para [ÁREA: Contabilidad/Nómina].

IMPORTANTE - REGLAS FUNDAMENTALES:
1. NO MODIFICAR ningún código existente
2. NO USAR wrappers ni componentes intermedios
3. COPIAR y RECREAR código existente en la nueva estructura
4. Seguir EXACTAMENTE el patrón de /src/modules establecido

ESTRUCTURA A CREAR:
/src/modules/[contabilidad|nomina]/[nombre-modulo]/
├── api/
│   └── [nombre].api.js          # Funciones de API
├── components/
│   └── [Componentes].jsx         # Componentes específicos
├── constants/
│   └── [nombre].constants.js     # Mensajes, labels, constantes
├── pages/
│   └── [Nombre]Page.jsx          # Página principal
├── utils/
│   └── [nombre]Helpers.js        # Funciones auxiliares
└── index.js                       # Exports del módulo

PÁGINA ORIGINAL A REFACTORIZAR:
- Ubicación: /src/pages/[NombreOriginal].jsx
- Componentes usados: [listar componentes de /src/components]
- APIs usadas: [listar de /src/api]

REQUISITOS TÉCNICOS:

1. VALIDACIÓN DE ACCESO:
   - Usar getUsuario() de '../../../shared/auth/utils/storage'
   - NO hacer llamadas API para validar (usar localStorage)
   - Función validarAcceso[Area]() que valide:
     * Gerente: acceso total
     * Otros: verificar array 'areas' con normalización (sin acentos, case-insensitive)
     * Fallback: verificar 'area_asignada'

2. API:
   - Todas las funciones async/await
   - Console.log con emojis (🔍 ✅ ❌)
   - Try-catch en todas las llamadas
   - clienteId convertido a Number() donde se envíe al backend
   - Respetar nombres de campos del backend (ej: 'checklist' no 'tareas')

3. CONSTANTES:
   - MENSAJES: todos los textos de UI
   - LABELS: labels de formularios
   - Cualquier valor hardcodeado

4. DISEÑO (FIEL AL ORIGINAL):
   - Colores simples: bg-gray-800, bg-gray-900, bg-blue-600
   - NO usar gradientes complejos
   - NO usar backdrop-blur ni efectos especiales
   - rounded-lg para cards, rounded-xl para botones
   - Mantener estructura HTML del original

5. INTEGRACIÓN /dev/modules:
   - Crear [Nombre]ModuleDemo.jsx con:
     * Input para cambiar clienteId/recursoId dinámicamente
     * Banner amarillo superior con info del módulo
     * Estructura con Routes anidadas: <Route path="/:id?" element={<DemoLayout />} />
     * Mensaje cuando no hay ID
   - Crear [Nombre]ModuleDocs.jsx con:
     * Descripción completa
     * Características principales
     * Estructura de archivos
     * Endpoints API
     * Ejemplo de uso
     * Links a demo y showcase

6. APP.JSX:
   - Agregar imports de Demo y Docs
   - Rutas /dev/modules/[nombre]/demo/* (con asterisco para subrutas)
   - Rutas /dev/modules/[nombre]/docs

7. MODULESSHOWCASE.JSX:
   - Agregar tarjeta del módulo con:
     * id, name, status: 'completed'
     * description clara
     * route y docsRoute
     * features (array de características)
     * stats (files, lines, components, endpoints)

ARCHIVOS A ENTREGAR:
✅ Estructura completa del módulo en /src/modules/[area]/[nombre]/
✅ index.js con todos los exports
✅ Páginas Demo y Docs en /src/pages/
✅ Rutas integradas en App.jsx
✅ Tarjeta en ModulesShowcase.jsx
✅ Sin errores de linting

VALIDACIONES FINALES:
- Ejecutar get_errors en todos los archivos creados
- Verificar imports (rutas relativas correctas)
- Confirmar que no se modificó código existente
- Comprobar que el diseño es fiel al original
```

---

### 🎯 EJEMPLO DE USO:

```
Necesito refactorizar la página AnalisisLibro para Contabilidad.

[COPIAR TODO EL PROMPT DE ARRIBA]

PÁGINA ORIGINAL A REFACTORIZAR:
- Ubicación: /src/pages/AnalisisLibro.jsx
- Componentes usados: TablaLibroMayor, FiltrosLibro
- APIs usadas: obtenerLibroMayor, obtenerClasificaciones

NOTAS ADICIONALES:
- La página recibe cierreId por parámetro
- Tiene filtros por cuenta y fecha
- Incluye descarga de Excel
```

---

Este prompt te asegura que:
- ✅ No se modifique código existente
- ✅ Se siga el patrón exacto de módulos
- ✅ Se valide acceso correctamente
- ✅ Se integre en /dev/modules
- ✅ El diseño sea fiel al original
- ✅ Todo funcione sin errores