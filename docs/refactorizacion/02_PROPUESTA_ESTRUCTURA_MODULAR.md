# 🏗️ Propuesta de Refactorización - Estructura Modular

**Fecha:** 11 de noviembre de 2025  
**Objetivo:** Definir patrón de diseño reproducible para todos los módulos del sistema

---

## 🎯 Filosofía de Diseño

### **Principios Fundamentales**

1. **Colocalización**: Todo lo relacionado con un módulo debe estar en una carpeta
2. **Autocontenido**: Cada módulo debe ser independiente y portable
3. **Documentación Integrada**: Cada módulo incluye su propia documentación
4. **No Romper Nada**: La refactorización se hace copiando archivos, no modificando los existentes
5. **Escalabilidad**: El patrón debe funcionar para módulos simples y complejos

---

## 📁 Estructura Propuesta

### **Patrón General**

```
src/
└── modules/
    └── [NOMBRE_MODULO]/
        ├── README.md                 # Documentación del módulo
        ├── index.js                  # Exportaciones públicas del módulo
        │
        ├── pages/                    # Páginas principales
        │   └── [NombrePage].jsx
        │
        ├── components/               # Componentes del módulo
        │   ├── [Componente1].jsx
        │   └── [Componente2].jsx
        │
        ├── api/                      # Cliente API específico
        │   ├── [modulo].api.js
        │   └── types.js              # (opcional) TypeScript types
        │
        ├── hooks/                    # Custom hooks (opcional)
        │   └── use[Nombre].js
        │
        ├── utils/                    # Utilidades del módulo (opcional)
        │   └── [utilidad].js
        │
        ├── constants/                # Constantes (opcional)
        │   └── [constants].js
        │
        └── router/                   # Configuración de rutas
            └── routes.jsx
```

---

## 🔍 Estructura Detallada para el Módulo LOGIN

```
src/
└── modules/
    └── auth/                         # Módulo de Autenticación
        │
        ├── README.md                 # 📄 Documentación completa del módulo
        │   ├── Descripción general
        │   ├── Componentes incluidos
        │   ├── APIs consumidas
        │   ├── Flujo de autenticación
        │   ├── Uso y ejemplos
        │   └── Troubleshooting
        │
        ├── index.js                  # 📦 Exportaciones públicas
        │   └── export { LoginPage, useAuth, authApi, authRoutes }
        │
        ├── pages/
        │   └── LoginPage.jsx         # 🖥️ Página principal de login
        │       ├── Orquestación del flujo
        │       ├── Validación de sesión
        │       ├── Manejo de redirección
        │       └── Layout completo
        │
        ├── components/
        │   ├── LoginForm.jsx         # 📝 Formulario de login
        │   │   ├── Captura de credenciales
        │   │   ├── Validaciones en tiempo real
        │   │   ├── UI con animaciones
        │   │   └── Manejo de estados
        │   │
        │   ├── LoginHeader.jsx       # 🎨 Header específico de login
        │   │   ├── Logo BDO
        │   │   ├── Título del sistema
        │   │   └── Indicadores de ambiente
        │   │
        │   └── PrivateRoute.jsx      # 🔒 Protección de rutas
        │       └── Validación de token
        │
        ├── api/
        │   └── auth.api.js           # 🌐 Cliente API de autenticación
        │       ├── loginUsuario()
        │       ├── obtenerUsuario()
        │       ├── refreshToken()
        │       └── logout()
        │
        ├── hooks/
        │   ├── useAuth.js            # 🎣 Hook de autenticación
        │   │   ├── Estado global de usuario
        │   │   ├── Funciones de login/logout
        │   │   └── Verificación de sesión
        │   │
        │   └── useSession.js         # 🎣 Hook de validación de sesión
        │       ├── Auto-validación de token
        │       └── Redirección automática
        │
        ├── utils/
        │   ├── validators.js         # ✅ Validaciones de formulario
        │   │   ├── validateEmail()
        │   │   ├── validatePassword()
        │   │   └── validateBDOEmail()
        │   │
        │   └── storage.js            # 💾 Gestión de localStorage
        │       ├── saveAuthData()
        │       ├── getAuthData()
        │       ├── clearAuthData()
        │       └── hasValidSession()
        │
        ├── constants/
        │   └── auth.constants.js     # 📋 Constantes del módulo
        │       ├── ERROR_MESSAGES
        │       ├── VALIDATION_RULES
        │       └── STORAGE_KEYS
        │
        └── router/
            └── auth.routes.jsx       # 🛣️ Configuración de rutas
                └── { path: "/", element: <LoginPage /> }
```

---

## 📄 Contenido de Archivos Clave

### **1. `/modules/auth/README.md`**

```markdown
# 🔐 Módulo de Autenticación

## Descripción
Módulo encargado de la autenticación de usuarios mediante JWT tokens.

## Componentes
- **LoginPage**: Página principal de login
- **LoginForm**: Formulario de captura de credenciales
- **LoginHeader**: Header visual de la página
- **PrivateRoute**: Protección de rutas privadas

## APIs Consumidas
- POST /api/token/ - Obtener tokens JWT
- GET /api/usuarios/me/ - Datos del usuario autenticado

## Flujo de Autenticación
[Diagrama y explicación detallada]

## Uso
\`\`\`javascript
import { LoginPage, useAuth } from '@/modules/auth';
\`\`\`

## Configuración
[Detalles de configuración]
```

### **2. `/modules/auth/index.js`**

```javascript
// Exportaciones públicas del módulo
export { default as LoginPage } from './pages/LoginPage';
export { default as LoginForm } from './components/LoginForm';
export { default as PrivateRoute } from './components/PrivateRoute';

export { useAuth } from './hooks/useAuth';
export { useSession } from './hooks/useSession';

export * as authApi from './api/auth.api';
export { authRoutes } from './router/auth.routes';

export * from './constants/auth.constants';
```

### **3. `/modules/auth/hooks/useAuth.js`** (NUEVO)

```javascript
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import * as authApi from '../api/auth.api';
import * as storage from '../utils/storage';

export const useAuth = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [usuario, setUsuario] = useState(storage.getUsuario());

  const login = useCallback(async (correo, password, recordar) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await authApi.loginUsuario(correo, password);
      storage.saveAuthData(result, recordar);
      
      const userData = await authApi.obtenerUsuario();
      storage.saveUsuario(userData);
      setUsuario(userData);
      
      navigate('/menu');
    } catch (err) {
      const errorMessage = authApi.parseError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);

  const logout = useCallback(() => {
    storage.clearAuthData();
    setUsuario(null);
    navigate('/');
  }, [navigate]);

  const validateSession = useCallback(async () => {
    if (!storage.hasValidSession()) {
      return false;
    }

    try {
      const userData = await authApi.obtenerUsuario();
      storage.saveUsuario(userData);
      setUsuario(userData);
      return true;
    } catch {
      storage.clearAuthData();
      return false;
    }
  }, []);

  return {
    usuario,
    isLoading,
    error,
    login,
    logout,
    validateSession,
    isAuthenticated: !!usuario,
  };
};
```

### **4. `/modules/auth/utils/storage.js`** (NUEVO)

```javascript
import { STORAGE_KEYS } from '../constants/auth.constants';

export const saveAuthData = (authData, recordar = false) => {
  localStorage.setItem(STORAGE_KEYS.TOKEN, authData.access);
  
  if (authData.refresh) {
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, authData.refresh);
  }
  
  if (recordar) {
    localStorage.setItem(STORAGE_KEYS.REMEMBER, 'true');
  }
};

export const saveUsuario = (usuario) => {
  localStorage.setItem(STORAGE_KEYS.USUARIO, JSON.stringify(usuario));
};

export const getToken = () => {
  return localStorage.getItem(STORAGE_KEYS.TOKEN);
};

export const getUsuario = () => {
  const usuario = localStorage.getItem(STORAGE_KEYS.USUARIO);
  return usuario ? JSON.parse(usuario) : null;
};

export const hasValidSession = () => {
  return !!getToken();
};

export const clearAuthData = () => {
  localStorage.removeItem(STORAGE_KEYS.TOKEN);
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USUARIO);
  localStorage.removeItem(STORAGE_KEYS.REMEMBER);
};
```

### **5. `/modules/auth/utils/validators.js`** (NUEVO)

```javascript
import { VALIDATION_RULES, ERROR_MESSAGES } from '../constants/auth.constants';

export const validateEmail = (email) => {
  if (!email) {
    return ERROR_MESSAGES.EMAIL_REQUIRED;
  }
  
  if (!VALIDATION_RULES.EMAIL_REGEX.test(email)) {
    return ERROR_MESSAGES.EMAIL_INVALID;
  }
  
  if (!email.endsWith(VALIDATION_RULES.BDO_DOMAIN)) {
    return ERROR_MESSAGES.EMAIL_NOT_BDO;
  }
  
  return '';
};

export const validatePassword = (password) => {
  if (!password) {
    return ERROR_MESSAGES.PASSWORD_REQUIRED;
  }
  
  if (password.length < VALIDATION_RULES.MIN_PASSWORD_LENGTH) {
    return ERROR_MESSAGES.PASSWORD_TOO_SHORT;
  }
  
  return '';
};

export const validateBDOEmail = (email) => {
  return email.endsWith(VALIDATION_RULES.BDO_DOMAIN);
};
```

### **6. `/modules/auth/constants/auth.constants.js`** (NUEVO)

```javascript
export const STORAGE_KEYS = {
  TOKEN: 'token',
  REFRESH_TOKEN: 'refreshToken',
  USUARIO: 'usuario',
  REMEMBER: 'recordarSesion',
};

export const ERROR_MESSAGES = {
  EMAIL_REQUIRED: 'El correo es requerido',
  EMAIL_INVALID: 'Formato de correo inválido',
  EMAIL_NOT_BDO: 'Debe usar un correo @bdo.cl',
  PASSWORD_REQUIRED: 'La contraseña es requerida',
  PASSWORD_TOO_SHORT: 'Mínimo 6 caracteres',
  LOGIN_FAILED: 'Credenciales incorrectas. Verifique su correo y contraseña.',
  UNAUTHORIZED: 'Correo o contraseña incorrectos.',
  FORBIDDEN: 'Acceso denegado. Contacte al administrador.',
  SERVER_ERROR: 'Error del servidor. Intente nuevamente más tarde.',
  NETWORK_ERROR: 'No se pudo conectar con el servidor. Verifique su conexión.',
};

export const VALIDATION_RULES = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  BDO_DOMAIN: '@bdo.cl',
  MIN_PASSWORD_LENGTH: 6,
};

export const API_ENDPOINTS = {
  LOGIN: '/token/',
  REFRESH: '/token/refresh/',
  ME: '/usuarios/me/',
};
```

### **7. `/modules/auth/router/auth.routes.jsx`** (NUEVO)

```javascript
import { LoginPage } from '../pages/LoginPage';

export const authRoutes = [
  {
    path: '/',
    element: <LoginPage />,
    meta: {
      title: 'Iniciar Sesión - SGM',
      requiresAuth: false,
      public: true,
    },
  },
];
```

---

## 🔄 Migración de Archivos

### **Plan de Copia (Sin Romper el Sistema Actual)**

```
Estado Actual → Estado Refactorizado
────────────────────────────────────────────────────────────

src/pages/Login.jsx
  ↓ COPIAR → modules/auth/pages/LoginPage.jsx

src/components/LoginForm.jsx
  ↓ COPIAR → modules/auth/components/LoginForm.jsx

src/components/Header_login.jsx
  ↓ COPIAR → modules/auth/components/LoginHeader.jsx

src/components/PrivateRoute.jsx
  ↓ COPIAR → modules/auth/components/PrivateRoute.jsx

src/api/auth.js
  ↓ COPIAR → modules/auth/api/auth.api.js

────────────────────────────────────────────────────────────
NUEVOS ARCHIVOS (No existen en la estructura actual):

modules/auth/hooks/useAuth.js
modules/auth/hooks/useSession.js
modules/auth/utils/storage.js
modules/auth/utils/validators.js
modules/auth/constants/auth.constants.js
modules/auth/router/auth.routes.jsx
modules/auth/index.js
modules/auth/README.md
```

---

## 🎨 Ventajas de la Nueva Estructura

### **1. Colocalización**
✅ Todos los archivos relacionados con autenticación están en un solo lugar  
✅ Fácil de encontrar y modificar  
✅ Reduce tiempo de navegación en el proyecto

### **2. Escalabilidad**
✅ Patrón reproducible para otros módulos (Contabilidad, Nómina, Clientes, etc.)  
✅ Estructura clara para nuevos desarrolladores  
✅ Fácil agregar nuevas funcionalidades

### **3. Mantenibilidad**
✅ Cambios localizados en una carpeta  
✅ Menos riesgo de romper otros módulos  
✅ Documentación integrada (README.md)

### **4. Testabilidad**
✅ Tests pueden vivir junto al código (`__tests__/`)  
✅ Mocks y fixtures en el mismo módulo  
✅ Fácil aislar componentes para testing

### **5. Reutilización**
✅ Hooks compartibles (`useAuth`, `useSession`)  
✅ Utilidades extraíbles (`validators.js`, `storage.js`)  
✅ Exportaciones limpias via `index.js`

---

## 🛠️ Aplicación del Patrón a Otros Módulos

### **Ejemplo: Módulo de Clientes**

```
modules/
└── clientes/
    ├── README.md
    ├── index.js
    ├── pages/
    │   ├── ClientesPage.jsx
    │   ├── ClienteDetallePage.jsx
    │   └── CrearClientePage.jsx
    ├── components/
    │   ├── ClienteCard.jsx
    │   ├── ClienteForm.jsx
    │   └── ClienteList.jsx
    ├── api/
    │   └── clientes.api.js
    ├── hooks/
    │   ├── useClientes.js
    │   └── useClienteDetalle.js
    ├── utils/
    │   └── clienteFormatters.js
    ├── constants/
    │   └── clientes.constants.js
    └── router/
        └── clientes.routes.jsx
```

### **Ejemplo: Módulo de Contabilidad**

```
modules/
└── contabilidad/
    ├── README.md
    ├── index.js
    ├── pages/
    │   ├── HistorialCierresPage.jsx
    │   ├── CierreDetallePage.jsx
    │   ├── CrearCierrePage.jsx
    │   └── ClasificacionCierrePage.jsx
    ├── components/
    │   ├── CierreCard.jsx
    │   ├── CierreForm.jsx
    │   ├── ClasificacionTable.jsx
    │   └── LibroMayorAnalisis.jsx
    ├── api/
    │   ├── cierres.api.js
    │   ├── clasificaciones.api.js
    │   └── libros.api.js
    ├── hooks/
    │   ├── useCierres.js
    │   ├── useClasificaciones.js
    │   └── useLibroMayor.js
    ├── utils/
    │   ├── contabilidadFormatters.js
    │   └── excelProcessors.js
    ├── constants/
    │   └── contabilidad.constants.js
    └── router/
        └── contabilidad.routes.jsx
```

---

## 🚀 Implementación Incremental

### **Fase 1: Login (Piloto)**
1. Crear estructura `modules/auth/`
2. Copiar archivos existentes
3. Crear nuevos hooks y utilidades
4. Refactorizar componentes para usar hooks
5. Documentar en README.md
6. Probar exhaustivamente
7. **Mantener archivos originales intactos**

### **Fase 2: Validación**
1. Usar módulo `auth/` en una feature flag
2. Probar en desarrollo
3. Comparar con implementación original
4. Ajustar según feedback

### **Fase 3: Expansión**
1. Aplicar patrón a módulo de Clientes
2. Aplicar patrón a módulo de Contabilidad
3. Aplicar patrón a módulo de Nómina
4. Continuar con otros módulos

### **Fase 4: Migración Completa**
1. Actualizar App.jsx para usar nuevos módulos
2. Deprecar archivos antiguos (con aviso)
3. Eliminar archivos antiguos después de validación completa

---

## 📋 Checklist de Refactorización

Para cada módulo refactorizado, verificar:

- [ ] Estructura de carpetas completa
- [ ] README.md documentado
- [ ] index.js con exportaciones públicas
- [ ] Componentes funcionando correctamente
- [ ] APIs funcionando
- [ ] Hooks (si aplica)
- [ ] Utilidades (si aplica)
- [ ] Constantes definidas
- [ ] Rutas configuradas
- [ ] Tests escritos (opcional en fase inicial)
- [ ] Sin errores en consola
- [ ] No rompe funcionalidad existente
- [ ] Documentación actualizada

---

## 🎯 Próximo Paso

Implementar la refactorización del módulo Login siguiendo esta estructura.
