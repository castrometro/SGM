# CierreDetalle - Arquitectura Feature Folder por Áreas

## Estructura Implementada

```
CierreDetalle/
├── areas/                          # Componentes específicos por área de negocio
│   ├── Contabilidad/               # Lógica específica de contabilidad
│   │   ├── CierreProgresoContabilidad.jsx
│   │   ├── TipoDocumentoCard.jsx   # Re-exporta componente original
│   │   ├── LibroMayorCard.jsx      # Re-exporta componente original
│   │   ├── ClasificacionBulkCard.jsx
│   │   └── NombresEnInglesCard.jsx
│   ├── Nomina/                     # Lógica específica de nómina
│   │   └── CierreProgresoNomina.jsx
│   └── RRHH/                       # Lógica específica de recursos humanos
│       └── CierreProgresoRRHH.jsx
├── components/                     # Componentes compartidos
│   ├── CierreInfoBar.jsx          # Barra de información (adaptada para multi-área)
│   └── CierreAreaRouter.jsx       # Router que decide qué área mostrar
├── hooks/                          # Hooks reutilizables
│   └── useCierreDetalle.js        # Hook principal para cargar datos
├── config/                         # Configuración y lógica de negocio
│   └── areas.js                   # Determina qué área mostrar según contexto
└── index.jsx                      # Componente principal
```

## Patrón de Diseño: Feature Folder con Separación por Áreas (Opción A)

### Características:

1. **Autocontainment por Área**: Cada área tiene sus propios componentes específicos
2. **Componentes Compartidos**: Elementos comunes como CierreInfoBar
3. **Routing Dinámico**: Determina automáticamente qué área mostrar
4. **Lazy Loading**: Los componentes de contabilidad usan lazy loading
5. **Configuración Centralizada**: La lógica de enrutamiento está en `config/areas.js`

### Ventajas:

- ✅ Separación clara de lógica de negocio por área
- ✅ Reutilización de componentes comunes
- ✅ Escalabilidad para nuevas áreas
- ✅ Mantenimiento independiente por área
- ✅ Carga bajo demanda de componentes pesados

### APIs Utilizadas:

- **Contabilidad**: `api/contabilidad` (completamente implementado)
- **Nómina**: `api/nomina` (pendiente de implementación)
- **RRHH**: `api/rrhh` (pendiente de implementación)

### Flujo de Funcionamiento:

1. `index.jsx` carga los datos del cierre usando `useCierreDetalle`
2. `config/areas.js` determina qué área mostrar según:
   - Tipo de cierre
   - Usuario logueado
   - URL actual
3. `CierreAreaRouter` renderiza el componente específico del área
4. `CierreInfoBar` muestra información común pero con acciones específicas por área

### Próximos Pasos:

- [ ] Implementar APIs de nómina y RRHH
- [ ] Mejorar componentes de nómina y RRHH con lógica real
- [ ] Añadir testing unitario por área
- [ ] Documentar APIs específicas de cada área

### Dependencias Externas Minimizadas:

- **EstadoBadge**: Componente compartido del sistema
- **APIs**: Específicas por área
- **React Router**: Para navegación básica
- **Hooks de React**: useState, useEffect, useParams

Esta arquitectura permite un crecimiento orgánico donde cada área puede evolucionar independientemente mientras mantiene la coherencia del sistema.
