# 🏗️ Estrategia de Separación: Contabilidad vs Nómina

**Fecha:** 14 de noviembre de 2025  
**Objetivo:** Organizar módulos según áreas de negocio

---

## 🎯 SITUACIÓN ACTUAL

### Módulos Refactorizados:
1. **Auth** - Transversal (usado por ambas áreas)
2. **Menu** - Mixto (tiene opciones para ambas áreas)

### Problema:
Los módulos actuales no están organizados por área de negocio, lo que dificulta:
- Desarrollo paralelo de equipos separados
- Despliegue independiente de funcionalidades
- Mantenimiento específico por área
- Escalabilidad del sistema

---

## 💡 PROPUESTA DE ARQUITECTURA

### Opción 1: **Separación Horizontal por Dominio** (RECOMENDADA)

```
src/
├── modules/
│   ├── shared/               # Módulos compartidos
│   │   ├── auth/            # ✅ Ya existe - Autenticación
│   │   └── common/          # Componentes compartidos (Header, Footer, Layout)
│   │
│   ├── contabilidad/        # Dominio de Contabilidad
│   │   ├── menu/            # Menu específico de contabilidad
│   │   ├── clientes/        # Gestión de clientes contables
│   │   ├── cierres/         # Cierres contables
│   │   ├── clasificacion/   # Clasificación de cuentas
│   │   ├── cobranza/        # Gestión de cobranza
│   │   └── proyectos-bdo/   # Proyectos BDO
│   │
│   └── nomina/              # Dominio de Nómina
│       ├── menu/            # Menu específico de nómina
│       ├── empleados/       # Gestión de empleados
│       ├── cierres/         # Cierres de nómina
│       ├── remuneraciones/  # Libro de remuneraciones
│       └── incidencias/     # Gestión de incidencias
```

**Ventajas:**
- ✅ Separación clara por dominio de negocio
- ✅ Equipos pueden trabajar independientemente
- ✅ Fácil escalar cada área por separado
- ✅ Deploy independiente posible
- ✅ Menos conflictos en Git

**Desventajas:**
- ⚠️ Requiere refactorización del menu actual
- ⚠️ Posible duplicación de código común

---

### Opción 2: **Separación con Módulos Compartidos**

```
src/
├── modules/
│   ├── core/                # Núcleo del sistema
│   │   ├── auth/           # ✅ Ya existe
│   │   ├── menu/           # ✅ Ya existe (adaptado)
│   │   └── common/         # Componentes comunes
│   │
│   ├── features/           # Funcionalidades por área
│   │   ├── contabilidad/
│   │   │   ├── clientes/
│   │   │   ├── cierres/
│   │   │   ├── clasificacion/
│   │   │   ├── cobranza/
│   │   │   └── proyectos-bdo/
│   │   │
│   │   └── nomina/
│   │       ├── empleados/
│   │       ├── cierres/
│   │       ├── remuneraciones/
│   │       └── incidencias/
│   │
│   └── integrations/       # Integraciones externas
│       └── talana/         # API Talana
```

**Ventajas:**
- ✅ Menu compartido (getUserMenuOptions decide qué mostrar)
- ✅ Auth permanece compartido
- ✅ Código común en un solo lugar
- ✅ Estructura clara core vs features

**Desventajas:**
- ⚠️ Menu puede volverse complejo con lógica mixta
- ⚠️ Dependencias entre core y features

---

### Opción 3: **Micro-Frontends (Avanzado)**

```
src/
├── apps/                    # Aplicaciones independientes
│   ├── contabilidad/
│   │   ├── modules/
│   │   ├── pages/
│   │   └── App.jsx
│   │
│   └── nomina/
│       ├── modules/
│       ├── pages/
│       └── App.jsx
│
└── shared/                  # Compartido entre apps
    ├── auth/
    ├── components/
    └── utils/
```

**Ventajas:**
- ✅ Separación total
- ✅ Deploy independiente garantizado
- ✅ Escalabilidad máxima
- ✅ Equipos completamente independientes

**Desventajas:**
- ❌ Complejidad alta
- ❌ Requiere configuración avanzada (Module Federation, etc.)
- ❌ Más esfuerzo inicial

---

## 🎯 RECOMENDACIÓN: OPCIÓN 1

### **Separación Horizontal por Dominio**

**Razones:**
1. Clara separación de responsabilidades
2. Mantenible a mediano plazo
3. No requiere infraestructura compleja
4. Permite trabajo paralelo de equipos
5. Fácil de entender y documentar

---

## 📋 PLAN DE IMPLEMENTACIÓN

### Fase 1: **Reorganizar Menu** (Actual)

El módulo `menu` actual ya tiene lógica separada por área en `menuConfig.js`.

**Opción A: Mantener un solo módulo menu con lógica condicional**
```javascript
// Ya está implementado así
getUserMenuOptions(usuario) {
  // Retorna opciones según usuario.areas
  if (hasArea(usuario, 'Contabilidad')) { ... }
  if (hasArea(usuario, 'Nomina')) { ... }
}
```

✅ **Ventaja:** Funciona actualmente, menos refactorización
❌ **Desventaja:** Crece con el tiempo, difícil de mantener

**Opción B: Separar en dos módulos menu**
```
modules/
├── shared/
│   └── auth/
├── contabilidad/
│   └── menu/              # Menu de contabilidad
│       ├── pages/
│       │   └── MenuContabilidadPage.jsx
│       └── utils/
│           └── menuContabilidadConfig.js
└── nomina/
    └── menu/              # Menu de nómina
        ├── pages/
        │   └── MenuNominaPage.jsx
        └── utils/
            └── menuNominaConfig.js
```

✅ **Ventaja:** Separación clara, fácil mantenimiento
❌ **Desventaja:** Requiere refactorización, lógica de enrutamiento más compleja

---

### Fase 2: **Crear Módulos por Dominio**

#### Contabilidad
```bash
# Próximos módulos a refactorizar
modules/contabilidad/
├── clientes/
├── cierres/
├── clasificacion/
├── cobranza/
└── proyectos-bdo/
```

#### Nómina
```bash
# Próximos módulos a refactorizar
modules/nomina/
├── empleados/
├── cierres/
├── remuneraciones/
└── incidencias/
```

---

## 🔧 IMPLEMENTACIÓN PASO A PASO

### PASO 1: Decidir estrategia de Menu

**Pregunta clave:** ¿Quieres mantener un menu unificado o separar en dos?

**A. Menu Unificado (Recomendado para empezar)**
```javascript
// Mantener estructura actual
/src/modules/menu/
```
- ✅ Menos cambios
- ✅ Usuario ve un solo menú filtrado por área
- ⚠️ Archivo `menuConfig.js` crecerá

**B. Menu Separado (Para escalar mejor)**
```javascript
// Dividir en dos módulos
/src/modules/contabilidad/menu/
/src/modules/nomina/menu/
```
- ✅ Separación completa por dominio
- ✅ Fácil mantenimiento a largo plazo
- ⚠️ Requiere lógica de routing más compleja

---

### PASO 2: Refactorizar próximos módulos por dominio

**Ejemplo: Módulo Clientes**

**Si es compartido entre áreas:**
```bash
/src/modules/shared/clientes/
```

**Si es específico de contabilidad:**
```bash
/src/modules/contabilidad/clientes/
```

**Si hay uno por área:**
```bash
/src/modules/contabilidad/clientes/
/src/modules/nomina/empleados/     # Equivalente en nómina
```

---

### PASO 3: Crear módulo `common` para compartir código

```bash
/src/modules/shared/common/
├── components/
│   ├── Header.jsx
│   ├── Footer.jsx
│   ├── Layout.jsx
│   └── LoadingSpinner.jsx
├── hooks/
│   ├── useAuth.js
│   └── useNotifications.js
└── utils/
    ├── formatters.js
    └── validators.js
```

---

## 🎨 ESTRUCTURA PROPUESTA FINAL

```
src/
├── modules/
│   │
│   ├── shared/                    # Código compartido entre áreas
│   │   ├── auth/                 # ✅ Ya existe - Login, JWT, etc.
│   │   ├── common/               # TODO: Crear - Header, Footer, Layout
│   │   └── menu/                 # ✅ Ya existe - Menu unificado
│   │
│   ├── contabilidad/             # Dominio de Contabilidad
│   │   ├── clientes/            # TODO: Refactorizar
│   │   ├── cierres/             # TODO: Refactorizar
│   │   ├── clasificacion/       # TODO: Refactorizar
│   │   ├── libro-mayor/         # TODO: Refactorizar
│   │   ├── cobranza/            # TODO: Refactorizar
│   │   └── proyectos-bdo/       # TODO: Refactorizar
│   │
│   └── nomina/                   # Dominio de Nómina
│       ├── empleados/           # TODO: Refactorizar
│       ├── cierres/             # TODO: Refactorizar
│       ├── remuneraciones/      # TODO: Refactorizar
│       ├── incidencias/         # TODO: Refactorizar
│       └── dashboard/           # TODO: Refactorizar
│
├── pages/                        # Páginas antiguas (ir eliminando)
├── components/                   # Componentes antiguos (ir eliminando)
└── App.jsx                       # Punto de entrada
```

---

## 📊 COMPARACIÓN DE OPCIONES

| Criterio | Menu Unificado | Menu Separado | Micro-Frontends |
|----------|---------------|---------------|-----------------|
| **Complejidad** | Baja | Media | Alta |
| **Mantenimiento** | Media | Alta | Muy Alta |
| **Separación de equipos** | Media | Alta | Total |
| **Deploy independiente** | No | Parcial | Sí |
| **Tiempo de implementación** | 1 semana | 2-3 semanas | 1-2 meses |
| **Escalabilidad** | Media | Alta | Muy Alta |
| **Recomendado para SGM** | ✅ Corto plazo | ✅ Mediano plazo | ❌ Innecesario |

---

## 🚀 ROADMAP SUGERIDO

### **Corto Plazo (1-2 meses)**
1. ✅ Mantener menu unificado actual
2. ✅ Refactorizar módulos con estructura de dominio:
   - `modules/contabilidad/clientes/`
   - `modules/contabilidad/cierres/`
   - `modules/nomina/empleados/`
   - `modules/nomina/cierres/`
3. ✅ Crear `modules/shared/common/` para código compartido

### **Mediano Plazo (3-6 meses)**
1. Evaluar si menu necesita separación
2. Si crece mucho → Separar en dos módulos
3. Continuar refactorizando módulos restantes

### **Largo Plazo (6+ meses)**
1. Evaluar micro-frontends si hay equipos grandes
2. Considerar deploy independiente si es necesario
3. Optimizar performance por área

---

## 💬 PREGUNTAS PARA DECIDIR

1. **¿Los equipos de Contabilidad y Nómina trabajan completamente separados?**
   - Sí → Separar menu y módulos por dominio
   - No → Mantener menu unificado

2. **¿Necesitan deployar funcionalidades independientemente?**
   - Sí → Micro-frontends o separación fuerte
   - No → Estructura de dominio es suficiente

3. **¿Cuántas personas trabajan en cada área?**
   - 1-2 por área → Menu unificado OK
   - 3+ por área → Considerar separación

4. **¿Hay código compartido entre áreas?**
   - Mucho → modules/shared/
   - Poco → Duplicar si es necesario

---

## ✅ MI RECOMENDACIÓN ESPECÍFICA PARA SGM

**Estructura Híbrida:**

```
src/modules/
├── shared/
│   ├── auth/              # ✅ Mantener como está
│   ├── menu/              # ✅ Mantener como está (con lógica condicional)
│   └── common/            # ⭐ CREAR - Header, Footer, Layout
│
├── contabilidad/          # ⭐ USAR para nuevos módulos
│   └── [modulos]/
│
└── nomina/                # ⭐ USAR para nuevos módulos
    └── [modulos]/
```

**Razones:**
1. ✅ Mínimo cambio en lo que ya funciona
2. ✅ Clara separación para nuevos módulos
3. ✅ Fácil de entender y mantener
4. ✅ Escalable a futuro
5. ✅ No sobre-ingenierizado

---

## 🎯 PROMPT PARA PRÓXIMOS MÓDULOS

```
Refactoriza /clientes siguiendo el patrón de /menu, 
pero colócalo en /src/modules/contabilidad/clientes/

Este módulo es específico del dominio de Contabilidad.

Referencia: /src/modules/menu
```

---

**¿Qué opción prefieres?** 🤔
