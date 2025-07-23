# 📱 Frontend SGM - Documentación de Arquitectura

## 🏗️ Estructura General del Proyecto

### 📂 Organización de Carpetas
```
src/
├── App.jsx                 # Punto de entrada y router principal
├── main.jsx               # Configuración de React
├── api/                   # Servicios y llamadas a APIs
├── assets/                # Recursos estáticos (imágenes, iconos)
├── components/            # Componentes reutilizables
│   ├── Gerente/          # Componentes específicos del rol Gerente
│   ├── TarjetasCierreContabilidad/  # ⚠️ PROBLEMA: Tarjetas específicas
│   ├── TarjetasCierreNomina/        # ⚠️ PROBLEMA: Tarjetas específicas
│   └── ...
├── constants/             # Constantes globales
├── hooks/                 # React hooks personalizados
├── pages/                 # Componentes de páginas principales
├── ui/                   # Componentes UI básicos (botones, inputs, etc.)
└── utils/                # Utilidades y helpers

```

## 🎯 Arquitectura de Rutas (App.jsx)

### 📊 Análisis de Rutas Actuales

#### ✅ Rutas Bien Organizadas
- **Públicas**: `/` (Login)
- **Protegidas**: Todas bajo `/menu/*`

#### ⚠️ Problemas Identificados en la Organización

1. **Mezcla de Responsabilidades**:
   ```jsx
   // Contabilidad y Nómina mezcladas
   <Route path="cierres/:cierreId" element={<CierreDetalle />} />
   <Route path="nomina/cierres/:cierreId" element={<CierreDetalleNomina />} />
   ```

2. **Inconsistencia en Agrupación**:
   ```jsx
   // Algunos por área, otros por funcionalidad
   {/* ÁREA: CLIENTES */}
   {/* ÁREA: CONTABILIDAD */}
   {/* ÁREA: GESTIÓN DE ANALISTAS */}  // ¿Por qué no está con Gerente?
   ```

3. **Comentarios Inconsistentes**:
   - Algunos usan `----------`, otros no
   - Longitud variable de separadores

### 🔄 Propuesta de Reorganización de Rutas

#### Por Módulos de Negocio:
```jsx
{/* ==================== MÓDULO: AUTENTICACIÓN ==================== */}
<Route path="/" element={<Login />} />

{/* ==================== MÓDULO: DASHBOARD ==================== */}
<Route index element={<MenuUsuario />} />
<Route path="analytics" element={<Dashboard />} />

{/* ==================== MÓDULO: CLIENTES ==================== */}
<Route path="clientes" element={<Clientes />} />
<Route path="clientes/:id" element={<ClienteDetalle />} />

{/* ==================== MÓDULO: CONTABILIDAD ==================== */}
<Route path="contabilidad/cierres/:cierreId" element={<CierreDetalle />} />
<Route path="contabilidad/clasificacion" element={<ClasificacionCierre />} />

{/* ==================== MÓDULO: NÓMINA ==================== */}
<Route path="nomina/cierres/:cierreId" element={<CierreDetalleNomina />} />

{/* ==================== MÓDULO: GESTIÓN (ROL GERENTE/SUPERVISOR) ==================== */}
<Route path="gestion/analistas" element={<GestionAnalistas />} />
<Route path="gestion/mis-analistas" element={<MisAnalistas />} />
<Route path="gestion/logs-actividad" element={<LogsActividad />} />
```

## 🧩 Análisis de Componentes

### ⚠️ Problemas Identificados

#### 1. **Componentes Específicos por Área (Anti-patrón)**
```
components/
├── TarjetasCierreContabilidad/   # ❌ Específico por área
├── TarjetasCierreNomina/         # ❌ Específico por área
└── DashboardGerente/             # ❌ Específico por rol
```

**Problema**: Duplicación de lógica, difícil mantenimiento.

**Solución Propuesta**: Componentes genéricos y configurables.

#### 2. **Falta de Componentes UI Base**
- No hay un sistema de diseño consistente
- Componentes básicos mezclados con lógica de negocio

### 🎨 Propuesta de Arquitectura de Componentes

```
components/
├── ui/                    # Componentes base del sistema de diseño
│   ├── Button/
│   ├── Card/
│   ├── Modal/
│   └── Table/
├── common/                # Componentes comunes reutilizables
│   ├── Layout/
│   ├── Navigation/
│   └── Forms/
├── features/              # Componentes específicos por funcionalidad
│   ├── Cierres/
│   │   ├── TarjetaCierre.jsx       # Genérico para cualquier tipo
│   │   ├── DetalleCierre.jsx       # Genérico
│   │   └── EstadosCierre.jsx
│   ├── Clientes/
│   └── Analistas/
└── layouts/               # Layouts específicos por sección
```

## 🚨 Issues Críticos Detectados

### 1. **Estructura Duplicada**
- Existe `/root/SGM/frontend/src/` (vacío)
- Existe `/root/SGM/src/` (en uso)
- **Acción**: Eliminar estructura duplicada

### 2. **Imports Desordenados en App.jsx**
```jsx
// ❌ Actual: Sin agrupación lógica
import Login from "./pages/Login";
import MenuUsuario from "./pages/MenuUsuario";
import PrivateRoute from "./components/PrivateRoute";
// ... mezclado

// ✅ Propuesto: Agrupado por tipo
// React y librerías
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Páginas por módulo
import Login from "./pages/auth/Login";
import MenuUsuario from "./pages/dashboard/MenuUsuario";

// Componentes comunes
import PrivateRoute from "./components/common/PrivateRoute";
```

### 3. **Problema de Tarjetas (Flujo Desordenado)**
- `TarjetasCierreContabilidad/` y `TarjetasCierreNomina/` duplican lógica
- Cada área tiene sus propias tarjetas en lugar de un componente genérico

## 📋 Plan de Refactoring Propuesto

### Fase 1: Limpieza Inmediata
1. ✅ Documentar estructura actual
2. 🔄 Eliminar carpeta `/root/SGM/frontend/` duplicada
3. 🔄 Reorganizar imports en App.jsx
4. 🔄 Estandarizar comentarios de rutas

### Fase 2: Reorganización de Componentes
1. 🔄 Crear sistema de componentes UI base
2. 🔄 Unificar componentes de tarjetas
3. 🔄 Mover componentes específicos a carpetas features/

### Fase 3: Optimización de Rutas
1. 🔄 Reagrupar rutas por módulos de negocio
2. 🔄 Implementar lazy loading
3. 🔄 Crear rutas anidadas más lógicas

---

## 🔍 Próximos Pasos Sugeridos

1. **Revisar y aprobar** esta documentación
2. **Ejecutar Fase 1** de limpieza
3. **Analizar componentes específicos** (TarjetasCierre*, etc.)
4. **Crear plan detallado** para unificación de tarjetas

---
*Documento creado el: 21 de julio de 2025*
*Estado: 🚧 En revisión*
