# 🔐 Módulo de Autenticación

**Ubicación:** `/src/modules/auth/`  
**Versión:** 1.0.0  
**Última actualización:** 11 de noviembre de 2025

---

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Estructura del Módulo](#estructura-del-módulo)
3. [Componentes](#componentes)
4. [API y Endpoints](#api-y-endpoints)
5. [Utilidades](#utilidades)
6. [Flujo de Autenticación](#flujo-de-autenticación)
7. [Uso del Módulo](#uso-del-módulo)
8. [Configuración](#configuración)
9. [Manejo de Errores](#manejo-de-errores)
10. [Troubleshooting](#troubleshooting)

---

## 📖 Descripción General

El módulo de autenticación es el **punto de entrada** al sistema SGM (Sistema de Gestión y Monitoreo). Implementa:

- ✅ Autenticación mediante **JWT tokens**
- ✅ Validación automática de sesión existente
- ✅ Validaciones de formulario en tiempo real
- ✅ Manejo de errores específicos
- ✅ Protección de rutas privadas
- ✅ Gestión de tokens de refresco
- ✅ UI responsive con animaciones

### **Tecnologías Utilizadas**
- React 18
- React Router v6
- Framer Motion (animaciones)
- React Icons
- Tailwind CSS
- Axios

---

## 🗂️ Estructura del Módulo

```
auth/
├── README.md                    # Esta documentación
├── index.js                     # Exportaciones públicas del módulo
│
├── pages/
│   └── LoginPage.jsx            # Página principal de login
│
├── components/
│   ├── LoginForm.jsx            # Formulario de credenciales
│   ├── LoginHeader.jsx          # Header visual del login
│   ├── PrivateRoute.jsx         # Protección de rutas
│   └── DevModulesButton.jsx     # Botón flotante de desarrollo
│
├── api/
│   └── auth.api.js              # Cliente API de autenticación
│
├── utils/
│   ├── storage.js               # Gestión de localStorage
│   └── validators.js            # Validaciones de formulario
│
├── constants/
│   └── auth.constants.js        # Constantes del módulo
│
└── router/
    └── auth.routes.jsx          # Configuración de rutas
```

---

## 🧩 Componentes

### **LoginPage** (`pages/LoginPage.jsx`)

Página principal que orquesta todo el flujo de login.

**Responsabilidades:**
- Validar sesión existente al cargar
- Manejar el proceso de autenticación
- Redirigir según estado de autenticación
- Mostrar errores al usuario

**Estados:**
```javascript
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState(null);
const [isCheckingSession, setIsCheckingSession] = useState(true);
```

**Props:** Ninguna (es una página raíz)

**Uso:**
```jsx
import { LoginPage } from '@/modules/auth';

<Route path="/" element={<LoginPage />} />
```

---

### **LoginForm** (`components/LoginForm.jsx`)

Formulario con validaciones en tiempo real.

**Props:**
```typescript
{
  onLogin: (correo: string, password: string, recordar: boolean) => void;
  isLoading?: boolean;
  error?: string | null;
}
```

**Validaciones:**
- Email debe tener formato válido
- Email debe ser del dominio `@bdo.cl`
- Contraseña mínimo 6 caracteres
- Validación en tiempo real después de `onBlur`

**Estados Internos:**
```javascript
const [correo, setCorreo] = useState("");
const [password, setPassword] = useState("");
const [showPassword, setShowPassword] = useState(false);
const [recordar, setRecordar] = useState(false);
const [errors, setErrors] = useState({ correo: "", password: "" });
const [touched, setTouched] = useState({ correo: false, password: false });
```

**Características:**
- Animaciones con Framer Motion
- Toggle de visibilidad de contraseña
- Indicadores visuales de error
- Soporte para Enter key
- Deshabilita submit si hay errores

**Uso:**
```jsx
import { LoginForm } from '@/modules/auth';

<LoginForm 
  onLogin={handleLogin}
  isLoading={isAuthenticating}
  error={authError}
/>
```

---

### **LoginHeader** (`components/LoginHeader.jsx`)

Header visual específico para la página de login.

**Características:**
- Logo de BDO animado
- Indicador de ambiente (desarrollo/producción)
- Enlaces a sitio web y soporte
- Diseño responsive
- Sticky positioning

**Props:** Ninguna

**Uso:**
```jsx
import { LoginHeader } from '@/modules/auth';

<LoginHeader />
```

---

### **PrivateRoute** (`components/PrivateRoute.jsx`)

Componente de orden superior para proteger rutas.

**Props:**
```typescript
{
  children: React.ReactNode;
}
```

**Lógica:**
- Verifica existencia de token en localStorage
- Redirige a `/` si no hay token
- Renderiza children si hay token

**Uso:**
```jsx
import { PrivateRoute } from '@/modules/auth';

<Route path="/menu" element={
  <PrivateRoute>
    <MenuPage />
  </PrivateRoute>
}>
```

---

### **DevModulesButton** (`components/DevModulesButton.jsx`)

Botón flotante de desarrollo para acceso rápido al showcase de módulos refactorizados.

**Características:**
- Solo visible en modo desarrollo (`NODE_ENV === 'development'`)
- Posición fija en esquina inferior derecha
- Menú expandible con animaciones de Framer Motion
- Badge "DEV" para identificación rápida

**Enlaces incluidos:**
```jsx
📦 Ver Módulos    → /dev/modules (showcase completo)
🔐 Demo Auth      → /dev/modules/auth/demo (prueba en vivo)
📚 Documentación  → /dev/modules/docs (docs integradas)
```

**Uso:**
```jsx
import { DevModulesButton } from '@/modules/auth';

function App() {
  return (
    <div>
      <MainContent />
      {/* Solo visible en desarrollo */}
      <DevModulesButton />
    </div>
  );
}
```

**Estados internos:**
```javascript
const [isOpen, setIsOpen] = useState(false); // Control del menú expandible
```

**Comportamiento:**
- Click en botón principal: expande/contrae menú
- Click en enlace: navega y cierra menú automáticamente
- Animaciones suaves con AnimatePresence
- No renderiza nada en producción (retorna `null`)

---

## 🌐 API y Endpoints

### **authApi** (`api/auth.api.js`)

Cliente para comunicación con el backend.

#### **loginUsuario(correo, password)**
```javascript
import { authApi } from '@/modules/auth';

const result = await authApi.loginUsuario(
  "usuario@bdo.cl", 
  "password123"
);
// Retorna: { access: "jwt_token", refresh: "refresh_token" }
```

#### **obtenerUsuario()**
```javascript
const usuario = await authApi.obtenerUsuario();
// Retorna: { id, nombre, correo_bdo, tipo_usuario, areas, ... }
```

#### **refreshToken(refreshToken)**
```javascript
const newTokens = await authApi.refreshToken(refreshToken);
// Retorna: { access: "new_jwt_token" }
```

#### **parseError(error)**
```javascript
const errorMessage = authApi.parseError(error);
// Retorna: string con mensaje amigable
```

### **Endpoints Consumidos**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/token/` | Login - Obtener tokens JWT |
| POST | `/api/token/refresh/` | Renovar access token |
| GET | `/api/usuarios/me/` | Datos del usuario autenticado |

---

## 🛠️ Utilidades

### **storage** (`utils/storage.js`)

Gestión centralizada de localStorage.

```javascript
import { authStorage } from '@/modules/auth';

// Guardar datos de autenticación
authStorage.saveAuthData({ access: "token", refresh: "refresh" }, true);

// Guardar usuario
authStorage.saveUsuario({ id: 1, nombre: "Juan" });

// Obtener datos
const token = authStorage.getToken();
const usuario = authStorage.getUsuario();

// Verificar sesión
if (authStorage.hasValidSession()) {
  // Usuario autenticado
}

// Limpiar todo
authStorage.clearAuthData();
```

**Funciones Disponibles:**
- `saveAuthData(authData, recordar)`
- `saveUsuario(usuario)`
- `getToken()`
- `getRefreshToken()`
- `getUsuario()`
- `hasValidSession()`
- `shouldRemember()`
- `clearAuthData()`
- `getAllAuthData()`

---

### **validators** (`utils/validators.js`)

Validaciones de formulario.

```javascript
import { authValidators } from '@/modules/auth';

// Validar email
const emailError = authValidators.validateEmail("test@bdo.cl");
// Retorna: "" si es válido, o mensaje de error

// Validar password
const passError = authValidators.validatePassword("abc123");
// Retorna: "" si es válida, o mensaje de error

// Validar dominio BDO
const isBDO = authValidators.validateBDOEmail("user@bdo.cl");
// Retorna: boolean

// Validar formulario completo
const errors = authValidators.validateLoginForm(correo, password);
// Retorna: { correo: string, password: string }

// Verificar si hay errores
const hasErrs = authValidators.hasErrors(errors);
// Retorna: boolean
```

---

## 🔄 Flujo de Autenticación

### **Diagrama de Flujo Completo**

```
┌──────────────────────────────────────────────────────────────┐
│                    Usuario accede a "/"                      │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ ¿Existe token en    │
            │   localStorage?     │
            └─────┬───────────┬───┘
                  │           │
            No ◀──┘           └──▶ Sí
            │                     │
            ▼                     ▼
    ┌──────────────┐     ┌────────────────────┐
    │ Mostrar      │     │ Validar token con  │
    │ LoginForm    │     │ API (obtenerUsuario)│
    └──────┬───────┘     └─────┬──────────┬───┘
           │                   │          │
           │             Válido│          │Inválido
           │                   │          │
           │                   ▼          ▼
           │          ┌────────────┐  ┌──────────────┐
           │          │ Navigate   │  │ Limpiar      │
           │          │ a /menu    │  │ localStorage │
           │          └────────────┘  └──────┬───────┘
           │                                 │
           │◀────────────────────────────────┘
           │
           ▼
    ┌────────────────────┐
    │ Usuario ingresa    │
    │ credenciales       │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Validar formulario │
    │ (email + password) │
    └────┬───────┬───────┘
         │       │
   Error │       │ OK
         │       │
         │       ▼
         │  ┌─────────────────┐
         │  │ POST /api/token/│
         │  │ loginUsuario()  │
         │  └────┬──────┬─────┘
         │       │      │
         │   200 │      │ 401/403/500
         │       │      │
         │       ▼      ▼
         │  ┌────────┐ ┌────────────┐
         │  │ Guardar│ │ Mostrar    │
         │  │ tokens │ │ error      │
         │  └───┬────┘ └────────────┘
         │      │
         │      ▼
         │  ┌─────────────────────┐
         │  │ GET /api/usuarios/me│
         │  │ obtenerUsuario()    │
         │  └───┬─────────────────┘
         │      │
         │      ▼
         │  ┌──────────────┐
         │  │ Guardar      │
         │  │ usuario      │
         │  └───┬──────────┘
         │      │
         │      ▼
         │  ┌──────────────┐
         │  │ Navigate     │
         │  │ a /menu      │
         │  └──────────────┘
         │
         └──▶ Usuario permanece en login
```

---

## 💻 Uso del Módulo

### **Importación Básica**

```javascript
// Importar componentes específicos
import { LoginPage, PrivateRoute } from '@/modules/auth';

// Importar API
import { authApi } from '@/modules/auth';

// Importar utilidades
import { authStorage, authValidators } from '@/modules/auth';

// Importar constantes
import { ERROR_MESSAGES, STORAGE_KEYS } from '@/modules/auth';
```

### **Configurar Rutas**

```jsx
// En App.jsx
import { LoginPage, PrivateRoute } from '@/modules/auth';

function App() {
  return (
    <Router>
      <Routes>
        {/* Ruta pública */}
        <Route path="/" element={<LoginPage />} />
        
        {/* Rutas protegidas */}
        <Route path="/menu" element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }>
          {/* Rutas anidadas */}
        </Route>
      </Routes>
    </Router>
  );
}
```

### **Uso Programático del API**

```javascript
import { authApi, authStorage } from '@/modules/auth';

// Login manual
try {
  const { access, refresh } = await authApi.loginUsuario(
    "usuario@bdo.cl",
    "password123"
  );
  
  authStorage.saveAuthData({ access, refresh }, true);
  
  const usuario = await authApi.obtenerUsuario();
  authStorage.saveUsuario(usuario);
  
  // Redirigir
  navigate('/menu');
} catch (error) {
  const message = authApi.parseError(error);
  console.error(message);
}

// Logout
authStorage.clearAuthData();
navigate('/');
```

---

## ⚙️ Configuración

### **Variables de Entorno**

El módulo usa la configuración base de Axios en `/src/api/config.js`:

```javascript
const api = axios.create({
  baseURL: "http://172.17.11.18:8000/api",
});
```

**Para cambiar el backend:**
1. Modificar `baseURL` en `/src/api/config.js`
2. O crear variable de entorno `VITE_API_URL`

### **Configuración JWT en Backend**

```python
# backend/sgm_backend/settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}
```

### **Personalizar Validaciones**

```javascript
// src/modules/auth/constants/auth.constants.js
export const VALIDATION_RULES = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  BDO_DOMAIN: '@bdo.cl',  // ← Cambiar dominio aquí
  MIN_PASSWORD_LENGTH: 6,  // ← Cambiar longitud mínima
};
```

---

## ⚠️ Manejo de Errores

### **Códigos de Error HTTP**

| Código | Significado | Mensaje al Usuario |
|--------|-------------|-------------------|
| 401 | Unauthorized | "Correo o contraseña incorrectos" |
| 403 | Forbidden | "Acceso denegado. Contacte al administrador" |
| 500+ | Server Error | "Error del servidor. Intente nuevamente más tarde" |
| Network | Sin conexión | "No se pudo conectar con el servidor" |

### **Errores de Validación**

```javascript
// Errores de email
"El correo es requerido"
"Formato de correo inválido"
"Debe usar un correo @bdo.cl"

// Errores de contraseña
"La contraseña es requerida"
"Mínimo 6 caracteres"
```

### **Captura y Display de Errores**

```jsx
<LoginForm
  onLogin={handleLogin}
  isLoading={isLoading}
  error={error}  // ← Error se muestra automáticamente
/>
```

---

## 🐛 Troubleshooting

### **Problema: "Token inválido o expirado"**

**Causa:** El access token expiró (dura 7 días)

**Solución:**
```javascript
// Implementar refresh automático en interceptor
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      const refreshToken = authStorage.getRefreshToken();
      if (refreshToken) {
        try {
          const { access } = await authApi.refreshToken(refreshToken);
          authStorage.saveAuthData({ access }, false);
          // Reintentar request original
          error.config.headers.Authorization = `Bearer ${access}`;
          return api(error.config);
        } catch {
          authStorage.clearAuthData();
          window.location.href = '/';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

---

### **Problema: "Debe usar un correo @bdo.cl"**

**Causa:** Validación de dominio activa

**Solución:**
- Usar email con dominio @bdo.cl
- O modificar `BDO_DOMAIN` en constantes para ambiente de desarrollo

---

### **Problema: Usuario autenticado pero redirige a login**

**Causa:** Token no se está enviando en headers

**Verificar:**
```javascript
// src/api/config.js debe tener:
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

### **Problema: CORS error en desarrollo**

**Causa:** Backend no permite el origin del frontend

**Solución en Backend:**
```python
# backend/sgm_backend/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5174",
    "http://172.17.11.18:5174",
]
```

---

## 📊 Métricas del Módulo

- **Archivos:** 12
- **Líneas de código:** ~1,220
- **Componentes React:** 5 (LoginPage, LoginForm, LoginHeader, PrivateRoute, DevModulesButton)
- **Funciones de API:** 4
- **Utilidades:** 2 archivos, 15+ funciones
- **Constantes:** 4 categorías
- **Dependencias:** Framer Motion, React Icons, React Router, Axios

---

## 🔗 Enlaces Relacionados

- [Documentación Estado Actual](/docs/refactorizacion/01_LOGIN_ESTADO_ACTUAL.md)
- [Propuesta de Estructura Modular](/docs/refactorizacion/02_PROPUESTA_ESTRUCTURA_MODULAR.md)
- [Backend API Documentation](/backend/api/views.py)
- [React Router Docs](https://reactrouter.com/)

---

## 📝 Changelog

### v1.0.0 (11 Nov 2025)
- ✨ Refactorización completa del módulo de auth
- 📁 Nueva estructura modular
- 📚 Documentación completa integrada
- 🧩 Separación de utilidades y constantes
- 🎨 Componentes organizados por responsabilidad

---

**Mantenido por:** Equipo de Desarrollo SGM  
**Contacto:** soporte@bdo.cl
