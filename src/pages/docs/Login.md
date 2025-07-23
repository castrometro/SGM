# 🔑 Login.jsx - Documentación Detallada

## 🎯 Propósito
Página de autenticación del sistema. Maneja el login de usuarios y redirección automática si ya existe sesión válida.

## 👤 Usuarios Objetivo
- **Todos los usuarios** del sistema (Analista, Supervisor, Gerente)
- **Punto de entrada único** para toda la aplicación

## 📋 Funcionalidades

### ✅ Funcionalidades Principales
1. **Login de usuario** con correo y contraseña
2. **Validación automática de sesión** existente al cargar
3. **Redirección automática** a `/menu` si ya está autenticado
4. **Gestión de tokens** en localStorage
5. **Manejo de errores** de autenticación

### 🔄 Flujo de Funcionamiento
```mermaid
flowchart TD
    A[Usuario accede a /] --> B[Cargar Login.jsx]
    B --> C{¿Existe token en localStorage?}
    C -->|Sí| D[Validar token con obtenerUsuario()]
    C -->|No| E[Mostrar formulario login]
    D -->|Token válido| F[Redirigir a /menu]
    D -->|Token inválido| G[Limpiar localStorage]
    G --> E
    E --> H[Usuario ingresa credenciales]
    H --> I[Llamar loginUsuario()]
    I -->|Éxito| J[Guardar token y usuario]
    I -->|Error| K[Mostrar alerta error]
    J --> F
    K --> E
```

---

## 🔗 Dependencias Frontend

### 📦 Componentes Utilizados
```jsx
import LoginForm from "../components/LoginForm";           // ✅ Formulario de login
import Header_login from "../components/Header_login";     // ✅ Header específico login
```

### 📚 Librerías/Hooks
```jsx
import { useNavigate } from "react-router-dom";           // ✅ Navegación programática
import { useEffect } from "react";                       // ✅ Efectos de ciclo de vida
```

---

## 🌐 Dependencias Backend

### 🔌 APIs Utilizadas
```jsx
import { loginUsuario, obtenerUsuario } from "../api/auth";
```

### 📊 Endpoints Involucrados
1. **`loginUsuario(correo, password)`**
   - **Método**: POST  
   - **Endpoint**: `/api/auth/login/`
   - **Payload**: `{ email, password }`
   - **Response**: `{ access: "jwt_token" }`

2. **`obtenerUsuario()`**
   - **Método**: GET
   - **Endpoint**: `/api/auth/user/`
   - **Headers**: `Authorization: Bearer {token}`
   - **Response**: `{ id, nombre, correo, tipo_usuario, areas }`

---

## 💾 Gestión de Estado

### 🗃️ LocalStorage
```javascript
// Datos persistidos
localStorage.setItem("token", result.access);              // JWT token
localStorage.setItem("usuario", JSON.stringify(usuario));  // Datos del usuario
```

### 🔄 Estado Local (useState)
- **No utiliza useState** - es una página principalmente funcional

### ⚡ Efectos (useEffect)
```javascript
useEffect(() => {
  const validarSesion = async () => {
    // Validación automática al montar componente
  };
  validarSesion();
}, []); // Solo se ejecuta al montar
```

---

## 🎨 Estilos y UI

### 🌈 Clases CSS Principales
```jsx
className="flex flex-col w-full h-screen overflow-hidden bg-gray-900 text-gray-100"
// Fondo fullscreen con tema oscuro

className="fixed inset-0 z-0"
// Background con gradiente y blur

className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 opacity-80"
// Gradiente de fondo

className="relative z-10 flex flex-col h-full"
// Contenedor principal sobre el fondo
```

### 🎯 Estructura Visual
```
┌─────────────────────────────────────────┐
│ Header_login                            │
├─────────────────────────────────────────┤
│                                         │
│           LoginForm                     │
│      (centrado verticalmente)           │
│                                         │
└─────────────────────────────────────────┘
```

---

## ⚠️ Problemas Identificados

### 🚨 Seguridad
1. **Token en localStorage**: Vulnerable a XSS
   - **Recomendación**: Usar httpOnly cookies
2. **Error handling simple**: Solo console.error + alert
   - **Recomendación**: Sistema de notificaciones más robusto

### 🔧 UX/UI
1. **Alert nativo**: `alert("Credenciales incorrectas")`
   - **Recomendación**: Componente de notificación personalizado
2. **No hay loading state**: Durante login/validación
   - **Recomendación**: Agregar spinner o skeleton

### 🏗️ Arquitectura
1. **Lógica mezclada**: Autenticación + UI en misma página
   - **Recomendación**: Separar en custom hook `useAuth`

---

## 🔄 Navegación

### 📍 Rutas Relacionadas
- **Desde**: Cualquier ruta (redirigida por router si no auth)
- **Hacia**: `/menu` (al login exitoso)
- **Desde**: Automática si token válido existe

### 🗺️ Flujo en App.jsx
```jsx
<Route path="/" element={<Login />} />  // Ruta pública
```

---

## 🔍 Componentes Hijos Analizados

### LoginForm.jsx
- **Ubicación**: `../components/LoginForm`
- **Propósito**: Formulario con campos email/password
- **Props**: `{ onLogin: function }`

### Header_login.jsx  
- **Ubicación**: `../components/Header_login`
- **Propósito**: Header específico para página de login
- **Props**: Ninguna (componente estático)

---

## 📈 Métricas de Complejidad
- **Líneas de código**: 60
- **Funciones**: 3 (Login, validarSesion, handleLogin)
- **Dependencias externas**: 4
- **APIs**: 2
- **Complejidad**: ⭐⭐ (Baja-Media)

---

*Documentado: 21 de julio de 2025*
*Estado: ✅ Completo*
