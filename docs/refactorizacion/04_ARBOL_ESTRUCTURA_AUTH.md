# 🌲 Árbol de Estructura - Módulo Auth

Visualización completa de la nueva estructura del módulo de autenticación.

---

## 📁 Estructura Completa

```
src/modules/auth/
│
├── 📄 README.md                          # 📚 850 líneas - Documentación completa del módulo
│   ├── Descripción general
│   ├── Componentes y sus props
│   ├── API y endpoints
│   ├── Utilidades y helpers
│   ├── Flujo de autenticación (diagramas)
│   ├── Ejemplos de uso
│   ├── Configuración
│   ├── Manejo de errores
│   └── Troubleshooting
│
├── 📄 index.js                           # 📦 Exportaciones públicas centralizadas
│   ├── export { LoginPage }
│   ├── export { LoginForm, LoginHeader, PrivateRoute }
│   ├── export * as authApi
│   ├── export * as authStorage
│   ├── export * as authValidators
│   ├── export * from constants
│   └── export { authRoutes }
│
├── 📁 pages/                             # 🖥️ Páginas del módulo
│   └── 📄 LoginPage.jsx                  # Página principal de login
│       ├── Estado: isLoading, error, isCheckingSession
│       ├── useEffect: Validación automática de sesión
│       ├── handleLogin: Proceso de autenticación
│       ├── UI: Background animado + Header + Form + Footer
│       └── Responsabilidades:
│           ├── Orquestación del flujo completo
│           ├── Validación de sesión existente
│           ├── Gestión de redirección
│           └── Manejo de estados globales
│
├── 📁 components/                        # 🧩 Componentes reutilizables
│   │
│   ├── 📄 LoginForm.jsx                  # 📝 Formulario de credenciales
│   │   ├── Props: onLogin, isLoading, error
│   │   ├── Estados:
│   │   │   ├── correo, password
│   │   │   ├── showPassword, recordar
│   │   │   ├── errors { correo, password }
│   │   │   └── touched { correo, password }
│   │   ├── Validaciones:
│   │   │   ├── validateEmail() - Formato + dominio @bdo.cl
│   │   │   └── validatePassword() - Mínimo 6 caracteres
│   │   ├── Características:
│   │   │   ├── Validación en tiempo real (después de blur)
│   │   │   ├── Toggle de visibilidad de contraseña
│   │   │   ├── Indicadores visuales de error
│   │   │   ├── Soporte para Enter key
│   │   │   └── Animaciones con Framer Motion
│   │   └── UI:
│   │       ├── Campo Email (con iconos y validación)
│   │       ├── Campo Contraseña (con toggle de visibilidad)
│   │       ├── Checkbox "Recordar sesión"
│   │       ├── Botón "Olvidó su contraseña"
│   │       └── Botón Submit (con loading state)
│   │
│   ├── 📄 LoginHeader.jsx                # 🎨 Header visual de la página
│   │   ├── Logo BDO animado
│   │   ├── Título del sistema
│   │   ├── Badge de ambiente (dev/prod)
│   │   ├── Enlaces a sitio web y soporte
│   │   ├── Diseño responsive
│   │   └── Sticky positioning con backdrop blur
│   │
│   └── 📄 PrivateRoute.jsx               # 🔒 Protección de rutas privadas
│       ├── Props: children
│       ├── Lógica: Verifica token en localStorage
│       ├── Si no hay token → Navigate a "/"
│       └── Si hay token → Renderiza children
│
├── 📁 api/                               # 🌐 Cliente API de autenticación
│   └── 📄 auth.api.js
│       ├── loginUsuario(correo, password)
│       │   ├── POST /api/token/
│       │   ├── Body: { correo_bdo, password }
│       │   └── Returns: { access, refresh }
│       │
│       ├── obtenerUsuario()
│       │   ├── GET /api/usuarios/me/
│       │   ├── Headers: Authorization Bearer token
│       │   └── Returns: { id, nombre, tipo_usuario, ... }
│       │
│       ├── refreshToken(refreshToken)
│       │   ├── POST /api/token/refresh/
│       │   ├── Body: { refresh }
│       │   └── Returns: { access }
│       │
│       ├── parseError(error)
│       │   ├── Analiza error de Axios
│       │   ├── Mapea códigos HTTP a mensajes
│       │   └── Returns: string (mensaje amigable)
│       │
│       └── logout()
│           └── Returns: Promise.resolve()
│
├── 📁 utils/                             # 🛠️ Utilidades del módulo
│   │
│   ├── 📄 storage.js                     # 💾 Gestión de localStorage
│   │   ├── saveAuthData(authData, recordar)
│   │   │   └── Guarda tokens en localStorage
│   │   │
│   │   ├── saveUsuario(usuario)
│   │   │   └── Guarda datos del usuario (JSON)
│   │   │
│   │   ├── getToken()
│   │   │   └── Obtiene access token
│   │   │
│   │   ├── getRefreshToken()
│   │   │   └── Obtiene refresh token
│   │   │
│   │   ├── getUsuario()
│   │   │   └── Obtiene datos del usuario (parse JSON)
│   │   │
│   │   ├── hasValidSession()
│   │   │   └── Verifica si existe token
│   │   │
│   │   ├── shouldRemember()
│   │   │   └── Verifica preferencia de "recordar"
│   │   │
│   │   ├── clearAuthData()
│   │   │   └── Limpia todo (logout)
│   │   │
│   │   └── getAllAuthData()
│   │       └── Retorna todo: token, refresh, usuario, remember
│   │
│   └── 📄 validators.js                  # ✅ Validaciones de formulario
│       ├── validateEmail(email)
│       │   ├── Verifica formato (regex)
│       │   ├── Verifica dominio @bdo.cl
│       │   └── Returns: string (error o "")
│       │
│       ├── validatePassword(password)
│       │   ├── Verifica longitud mínima (6)
│       │   └── Returns: string (error o "")
│       │
│       ├── validateBDOEmail(email)
│       │   └── Returns: boolean
│       │
│       ├── validateLoginForm(correo, password)
│       │   └── Returns: { correo: string, password: string }
│       │
│       └── hasErrors(errors)
│           └── Returns: boolean
│
├── 📁 constants/                         # 📋 Constantes del módulo
│   └── 📄 auth.constants.js
│       ├── STORAGE_KEYS
│       │   ├── TOKEN: 'token'
│       │   ├── REFRESH_TOKEN: 'refreshToken'
│       │   ├── USUARIO: 'usuario'
│       │   └── REMEMBER: 'recordarSesion'
│       │
│       ├── ERROR_MESSAGES
│       │   ├── EMAIL_REQUIRED: "El correo es requerido"
│       │   ├── EMAIL_INVALID: "Formato de correo inválido"
│       │   ├── EMAIL_NOT_BDO: "Debe usar un correo @bdo.cl"
│       │   ├── PASSWORD_REQUIRED: "La contraseña es requerida"
│       │   ├── PASSWORD_TOO_SHORT: "Mínimo 6 caracteres"
│       │   ├── LOGIN_FAILED: "Credenciales incorrectas..."
│       │   ├── UNAUTHORIZED: "Correo o contraseña incorrectos"
│       │   ├── FORBIDDEN: "Acceso denegado..."
│       │   ├── SERVER_ERROR: "Error del servidor..."
│       │   └── NETWORK_ERROR: "No se pudo conectar..."
│       │
│       ├── VALIDATION_RULES
│       │   ├── EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
│       │   ├── BDO_DOMAIN: '@bdo.cl'
│       │   └── MIN_PASSWORD_LENGTH: 6
│       │
│       ├── API_ENDPOINTS
│       │   ├── LOGIN: '/token/'
│       │   ├── REFRESH: '/token/refresh/'
│       │   └── ME: '/usuarios/me/'
│       │
│       └── HTTP_STATUS
│           ├── UNAUTHORIZED: 401
│           ├── FORBIDDEN: 403
│           └── SERVER_ERROR: 500
│
└── 📁 router/                            # 🛣️ Configuración de rutas
    └── 📄 auth.routes.jsx
        └── authRoutes = [
            {
              path: '/',
              element: <LoginPage />,
              meta: {
                title: 'Iniciar Sesión - SGM',
                requiresAuth: false,
                public: true
              }
            }
          ]
```

---

## 🔗 Dependencias entre Archivos

```
LoginPage
    ├─── usa ──→ LoginForm
    ├─── usa ──→ LoginHeader
    ├─── usa ──→ authApi.loginUsuario()
    ├─── usa ──→ authApi.obtenerUsuario()
    └─── usa ──→ localStorage (directo)

LoginForm
    ├─── usa ──→ validateEmail() (interno)
    ├─── usa ──→ validatePassword() (interno)
    └─── recibe ──→ onLogin (callback desde LoginPage)

authApi
    ├─── usa ──→ api de config.js (axios instance)
    ├─── usa ──→ API_ENDPOINTS (constants)
    ├─── usa ──→ ERROR_MESSAGES (constants)
    └─── usa ──→ HTTP_STATUS (constants)

storage.js
    └─── usa ──→ STORAGE_KEYS (constants)

validators.js
    ├─── usa ──→ VALIDATION_RULES (constants)
    └─── usa ──→ ERROR_MESSAGES (constants)
```

---

## 📊 Estadísticas del Módulo

| Métrica | Valor |
|---------|-------|
| **Archivos totales** | 11 |
| **Líneas de código** | ~1,100 |
| **Líneas de documentación** | ~850 (README) |
| **Componentes React** | 4 |
| **Funciones de API** | 4 |
| **Funciones de utilidades** | 15+ |
| **Constantes definidas** | 25+ |
| **Dependencias externas** | 4 (Framer Motion, React Icons, React Router, Axios) |

---

## 🎨 Flujo Visual de Datos

```
Usuario → LoginPage
              ↓
          [Validar sesión existente]
              ↓
          ¿Token existe?
         /            \
       Sí             No
       ↓               ↓
   [obtenerUsuario]  [Mostrar LoginForm]
       ↓               ↓
   Navigate("/menu") [Usuario ingresa datos]
                       ↓
                   [Validar formulario]
                       ↓
                   [loginUsuario API]
                       ↓
                   [Guardar tokens]
                       ↓
                   [obtenerUsuario]
                       ↓
                   [Guardar usuario]
                       ↓
                   Navigate("/menu")
```

---

## 🔄 Flujo de Importaciones

```javascript
// Uso externo típico del módulo

import { 
  LoginPage,           // Página
  PrivateRoute,        // Componente
  authApi,             // API functions
  authStorage,         // Storage functions
  authValidators,      // Validators
  ERROR_MESSAGES       // Constantes
} from '@/modules/auth';

// Uso interno (dentro del módulo)

// LoginPage.jsx
import LoginForm from '../components/LoginForm';
import LoginHeader from '../components/LoginHeader';
import { loginUsuario, obtenerUsuario } from '../api/auth.api';

// LoginForm.jsx
// (Todo auto-contenido, no importa del módulo)

// auth.api.js
import api from '../../../api/config';
import { API_ENDPOINTS, ERROR_MESSAGES, HTTP_STATUS } from '../constants/auth.constants';

// storage.js
import { STORAGE_KEYS } from '../constants/auth.constants';

// validators.js
import { VALIDATION_RULES, ERROR_MESSAGES } from '../constants/auth.constants';
```

---

## 💡 Notas Importantes

### **Archivos Originales Preservados**
```
src/
├── pages/
│   └── Login.jsx                    ✅ INTACTO - No modificado
├── components/
│   ├── LoginForm.jsx                ✅ INTACTO - No modificado
│   ├── Header_login.jsx             ✅ INTACTO - No modificado
│   └── PrivateRoute.jsx             ✅ INTACTO - No modificado
└── api/
    └── auth.js                      ✅ INTACTO - No modificado
```

**El sistema actual sigue funcionando sin cambios.**

### **Sistema Dual**
- Sistema Antiguo: `import Login from "./pages/Login"`
- Sistema Nuevo: `import { LoginPage } from "./modules/auth"`

**Ambos coexisten sin conflictos.**

---

## 🚀 Ventajas de la Estructura

1. **Colocalización Total**
   - Todo en `/src/modules/auth/`
   - Búsqueda instantánea

2. **Reutilización Maximizada**
   - `authStorage`: Usado en cualquier parte
   - `authValidators`: Reutilizable en otros forms

3. **Testabilidad Mejorada**
   - Funciones puras fáciles de testear
   - Mocks simples de implementar

4. **Documentación Integrada**
   - README.md dentro del módulo
   - JSDoc en cada función

5. **Escalabilidad**
   - Patrón reproducible
   - Fácil agregar nuevas features

6. **Mantenibilidad**
   - Cambios localizados
   - Impacto reducido

---

**Última actualización:** 11 de noviembre de 2025  
**Versión:** 1.0.0
