# 📦 Principio de Colocación en Módulos

**Fecha:** 11 de noviembre de 2025  
**Contexto:** Refactorización del Sistema SGM

---

## 🎯 Objetivo de este Documento

Explicar el **principio de colocación** aplicado en la refactorización de módulos del sistema SGM, garantizando que cada módulo sea **autocontenido** y no dependa de recursos externos al módulo.

---

## 🧠 ¿Qué es el Principio de Colocación?

El **principio de colocación** (o **colocation principle**) establece que:

> **"Todo lo que un módulo necesita para funcionar debe estar dentro del módulo mismo"**

### ✅ Esto significa:

1. **Componentes específicos** del módulo → dentro del módulo
2. **Utilidades** usadas solo por el módulo → dentro del módulo
3. **Constantes** del dominio del módulo → dentro del módulo
4. **Estilos** específicos → dentro del módulo (si los hay)
5. **Assets** (imágenes, iconos) → dentro del módulo
6. **Documentación** → dentro del módulo (README.md)

### ❌ Evitar:

- Crear componentes genéricos en `/src/components` que solo usa un módulo
- Colocar utilidades del módulo en `/src/utils` compartido
- Referencias cruzadas entre módulos sin pasar por `index.js`

---

## 📂 Estructura Correcta vs Incorrecta

### ❌ **INCORRECTO** (Dispersión)

```
src/
├── components/
│   ├── DevModulesButton.jsx    ❌ Componente del módulo auth fuera
│   ├── LoginForm.jsx            ❌ Pertenece a auth
│   └── LoginHeader.jsx          ❌ Pertenece a auth
│
├── utils/
│   ├── authValidators.js        ❌ Utilidad específica de auth
│   └── authStorage.js           ❌ Utilidad específica de auth
│
└── modules/
    └── auth/
        └── pages/
            └── LoginPage.jsx     ✅ Solo la página
```

**Problemas:**
- 🔴 Difícil encontrar qué pertenece a qué módulo
- 🔴 Imposible mover/eliminar el módulo sin buscar en todo el proyecto
- 🔴 Coupling implícito con otros módulos
- 🔴 Dificulta pruebas aisladas

---

### ✅ **CORRECTO** (Colocación)

```
src/
├── components/        ← Solo componentes VERDADERAMENTE compartidos
│   ├── Header.jsx            ✅ Usado por múltiples módulos
│   ├── Footer.jsx            ✅ Usado por múltiples módulos
│   └── Layout.jsx            ✅ Usado por toda la app
│
└── modules/
    └── auth/                 ← TODO lo del módulo aquí
        ├── README.md         ✅ Documentación del módulo
        ├── index.js          ✅ Exportaciones públicas
        ├── pages/
        │   └── LoginPage.jsx
        ├── components/
        │   ├── LoginForm.jsx
        │   ├── LoginHeader.jsx
        │   ├── PrivateRoute.jsx
        │   └── DevModulesButton.jsx    ✅ Dentro del módulo
        ├── api/
        │   └── auth.api.js
        ├── utils/
        │   ├── storage.js              ✅ Utilidades del módulo
        │   └── validators.js           ✅ Utilidades del módulo
        ├── constants/
        │   └── auth.constants.js       ✅ Constantes del módulo
        └── router/
            └── auth.routes.jsx
```

**Beneficios:**
- ✅ Todo lo relacionado está junto
- ✅ Fácil de navegar y entender
- ✅ Módulo portable (copiar/mover/eliminar)
- ✅ Testing aislado
- ✅ Escalabilidad clara

---

## 🔧 Caso Práctico: DevModulesButton

### 📖 Historia

Inicialmente, se creó `DevModulesButton.jsx` en `/src/components/`:

```jsx
// ❌ Ubicación inicial (INCORRECTA)
/src/components/DevModulesButton.jsx
```

**Problema identificado:**
- Este componente solo lo usa el módulo `auth` y páginas del showcase
- No es un componente "global" como Header o Footer
- Rompe el principio de colocación

### ✅ Solución Aplicada

1. **Mover el componente al módulo:**
   ```
   /src/modules/auth/components/DevModulesButton.jsx
   ```

2. **Exportarlo desde el módulo:**
   ```javascript
   // src/modules/auth/index.js
   export { default as DevModulesButton } from './components/DevModulesButton';
   ```

3. **Usarlo desde otras páginas:**
   ```jsx
   // src/pages/ModulesShowcase.jsx
   import { DevModulesButton } from '../modules/auth';
   ```

4. **Eliminar archivo original:**
   ```bash
   rm /src/components/DevModulesButton.jsx
   ```

5. **Revertir cambios en Layout.jsx:**
   - Se quitó el import
   - Se quitó el render del componente
   - Layout.jsx vuelve a ser independiente

---

## 📋 Reglas de Oro para Colocación

### 1️⃣ **Pregúntate: "¿Esto es específico del módulo?"**

- **SÍ** → Va dentro de `/modules/{nombre}/`
- **NO** → Puede ir en `/src/components/` o `/src/utils/`

### 2️⃣ **Si solo un módulo lo usa, va en el módulo**

Ejemplo:
```javascript
// ❌ INCORRECTO
/src/utils/nominaHelpers.js    // Solo lo usa el módulo nómina

// ✅ CORRECTO
/src/modules/nomina/utils/helpers.js
```

### 3️⃣ **Componentes compartidos deben ser VERDADERAMENTE compartidos**

Criterio:
- Usado por **2+ módulos diferentes**
- Funcionalidad **genérica** (Header, Footer, Modal, Button)
- No contiene lógica de dominio específica

### 4️⃣ **Documentación viaja con el código**

```
/src/modules/auth/
├── README.md          ✅ Explica el módulo
├── components/
├── utils/
└── ...
```

### 5️⃣ **Las exportaciones deben ser explícitas**

```javascript
// src/modules/auth/index.js

// ✅ CORRECTO: Exportaciones controladas
export { default as LoginPage } from './pages/LoginPage';
export { default as DevModulesButton } from './components/DevModulesButton';

// ❌ INCORRECTO: Export wildcard sin control
export * from './components';  // No sabes qué estás exponiendo
```

---

## 🎯 Beneficios del Principio de Colocación

### 1. **Mantenibilidad**
- Código relacionado está junto
- Fácil encontrar dependencias
- Cambios localizados

### 2. **Escalabilidad**
- Agregar módulos sin conflictos
- Equipos pueden trabajar en módulos independientes
- Módulos se pueden versionar independientemente

### 3. **Portabilidad**
- Módulo completo en una carpeta
- Copiar/mover sin romper dependencias
- Reutilizar en otros proyectos

### 4. **Testing**
- Pruebas aisladas por módulo
- Mock de dependencias claro
- Coverage por módulo

### 5. **Onboarding**
- Nuevo desarrollador navega fácilmente
- Documentación cerca del código
- Estructura predecible

---

## 🚀 Aplicación en SGM

### Módulos Actuales

#### ✅ Auth (Implementado)
```
/src/modules/auth/
├── README.md (715 líneas)
├── 12 archivos
├── 5 componentes (incluyendo DevModulesButton)
├── Completamente autocontenido
└── Zero dependencias externas
```

#### 🔄 Próximos Módulos (Patrón a seguir)

**Clientes:**
```
/src/modules/clientes/
├── README.md
├── pages/
│   ├── ClientesListPage.jsx
│   └── ClienteDetailPage.jsx
├── components/
│   ├── ClienteCard.jsx
│   ├── ClienteForm.jsx
│   └── ClienteFilters.jsx
├── api/
│   └── clientes.api.js
├── utils/
│   └── clienteHelpers.js
└── constants/
    └── clientes.constants.js
```

**Contabilidad:**
```
/src/modules/contabilidad/
├── README.md
├── pages/
├── components/
├── api/
├── utils/
└── constants/
```

**Nómina:**
```
/src/modules/nomina/
├── README.md
├── pages/
├── components/
├── api/
├── utils/
└── constants/
```

---

## 📊 Comparación: Antes vs Después

### Antes (Sistema Actual)
```
Archivos relacionados a Login: Dispersos en 4 carpetas
- /src/pages/Login.jsx
- /src/components/LoginForm.jsx
- /src/components/Header_login.jsx
- /src/components/PrivateRoute.jsx
- /src/api/auth.js

❌ Difícil de mantener
❌ Acoplamiento implícito
❌ No portable
```

### Después (Refactorizado)
```
Todo en un lugar: /src/modules/auth/
- 12 archivos organizados
- 7 subcarpetas por responsabilidad
- README.md integrado
- Exportaciones controladas desde index.js

✅ Fácil de mantener
✅ Desacoplado
✅ Portable
✅ Documentado
```

---

## 🛡️ Excepciones Permitidas

### Cuándo NO aplicar colocación:

1. **Componentes UI genéricos:**
   ```
   /src/components/ui/
   ├── Button.jsx       ← Usado por TODOS los módulos
   ├── Modal.jsx        ← Usado por TODOS los módulos
   └── Input.jsx        ← Usado por TODOS los módulos
   ```

2. **Utilidades de framework:**
   ```
   /src/utils/
   ├── axios.config.js  ← Configuración global
   └── dateHelpers.js   ← Usado transversalmente
   ```

3. **Constantes globales:**
   ```
   /src/constants/
   ├── api.constants.js ← URLs base, timeouts
   └── app.constants.js ← Configuración app
   ```

4. **Estilos globales:**
   ```
   /src/styles/
   └── tailwind.config.js
   ```

---

## 📚 Referencias y Patrones

### Inspiración de Arquitecturas

1. **Feature-Sliced Design (FSD)**
   - Módulos por dominio de negocio
   - Colocación estricta

2. **Domain-Driven Design (DDD)**
   - Bounded contexts como módulos
   - Cada contexto autocontenido

3. **Atomic Design (para componentes)**
   - Atoms → compartidos
   - Molecules/Organisms → dentro del módulo

### Lecturas Recomendadas

- [Colocation in React](https://kentcdodds.com/blog/colocation)
- [Feature-Sliced Design](https://feature-sliced.design/)
- [Domain-Driven Design en Frontend](https://khalilstemmler.com/articles/domain-driven-design-intro/)

---

## ✅ Checklist de Colocación

Antes de crear un archivo, pregúntate:

- [ ] ¿Este componente/utilidad es específico de UN módulo?
- [ ] ¿Contiene lógica de dominio de un módulo específico?
- [ ] ¿Solo un módulo lo está usando actualmente?
- [ ] ¿Si elimino el módulo, este archivo debería eliminarse también?

**Si respondiste SÍ a alguna:** ✅ Va dentro del módulo

**Si respondiste NO a todas:** 🤔 Considéralo compartido

---

## 🎓 Ejemplos Prácticos

### Ejemplo 1: Validador de RUT (Chile)

```javascript
// ❓ ¿Dónde va este validador?

function validarRUT(rut) {
  // Lógica de validación
}
```

**Análisis:**
- ¿Es específico de un módulo? **NO**
- ¿Lo usan múltiples módulos? **SÍ** (Clientes, Nómina, Contabilidad)
- ¿Es lógica de dominio específica? **NO** (es validación general)

**Decisión:** ✅ `/src/utils/validators.js`

---

### Ejemplo 2: Formatter de Número de Empleado

```javascript
// ❓ ¿Dónde va este formatter?

function formatEmployeeNumber(num) {
  return `EMP-${num.toString().padStart(6, '0')}`;
}
```

**Análisis:**
- ¿Es específico de un módulo? **SÍ** (Solo Nómina)
- ¿Lo usan otros módulos? **NO**
- ¿Es lógica de dominio específica? **SÍ** (Nómina)

**Decisión:** ✅ `/src/modules/nomina/utils/formatters.js`

---

### Ejemplo 3: Modal de Confirmación

```jsx
// ❓ ¿Dónde va este modal?

function ConfirmModal({ message, onConfirm, onCancel }) {
  // UI genérica
}
```

**Análisis:**
- ¿Es específico de un módulo? **NO**
- ¿Lo usan múltiples módulos? **SÍ**
- ¿Es lógica de dominio específica? **NO** (UI genérico)

**Decisión:** ✅ `/src/components/ui/ConfirmModal.jsx`

---

## 🔄 Plan de Migración Gradual

### Fase 1: Módulos Nuevos (Actual)
- ✅ Auth implementado con colocación
- Crear próximos módulos siguiendo el patrón

### Fase 2: Refactorización Módulos Existentes
- Identificar código disperso de cada dominio
- Crear estructura modular
- Mover archivos gradualmente
- Deprecar archivos antiguos

### Fase 3: Limpieza
- Eliminar archivos duplicados
- Consolidar utilidades compartidas
- Actualizar imports en toda la app

---

## 📝 Conclusión

El **principio de colocación** es fundamental para:

- 🎯 **Organización:** Todo relacionado junto
- 🚀 **Escalabilidad:** Agregar módulos sin conflictos
- 🧪 **Testing:** Pruebas aisladas
- 📚 **Documentación:** Cerca del código
- 🔧 **Mantenimiento:** Cambios localizados

**Regla de oro:**

> "Si dudo si algo va en el módulo o fuera, probablemente va dentro del módulo"

---

**Última actualización:** 11 de noviembre de 2025  
**Mantenido por:** Equipo de Desarrollo SGM  
**Siguiente revisión:** Al implementar módulo Clientes
