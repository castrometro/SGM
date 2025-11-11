# ⚡ Guía Rápida de Implementación - Módulo Auth

**Para:** Desarrolladores que quieren usar el nuevo módulo  
**Tiempo estimado:** 15 minutos

---

## 🎯 Objetivos de esta Guía

1. Entender cómo usar el nuevo módulo
2. Migrar de la estructura antigua a la nueva
3. Aprovechar las nuevas utilidades
4. Aplicar el patrón a otros módulos

---

## 📦 Opción 1: Usar el Módulo Refactorizado

### **Paso 1: Importar el módulo**

```jsx
// Antes (estructura antigua)
import Login from "./pages/Login";
import PrivateRoute from "./components/PrivateRoute";
import { loginUsuario, obtenerUsuario } from "./api/auth";

// Después (estructura nueva)
import { LoginPage, PrivateRoute, authApi } from "./modules/auth";
```

### **Paso 2: Actualizar App.jsx**

```jsx
// src/App.jsx
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { LoginPage, PrivateRoute } from "./modules/auth";
import Layout from "./components/Layout";
// ... otros imports

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

export default App;
```

### **Paso 3: Verificar que funcione**

1. Iniciar el servidor: `npm run dev`
2. Acceder a `http://localhost:5174/`
3. Probar login con credenciales válidas
4. Verificar que redirige a `/menu`

✅ **Listo!** El módulo refactorizado está funcionando.

---

## 🛠️ Opción 2: Usar las Utilidades en Código Existente

### **Escenario: Validar email en otro componente**

```jsx
// Antes (duplicar lógica)
const validateEmail = (email) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) return "El correo es requerido";
  if (!regex.test(email)) return "Formato de correo inválido";
  if (!email.endsWith("@bdo.cl")) return "Debe usar un correo @bdo.cl";
  return "";
};

// Después (reutilizar utilidad)
import { authValidators } from "./modules/auth";

const error = authValidators.validateEmail(email);
if (error) {
  console.error(error);
}
```

### **Escenario: Gestionar sesión en otro componente**

```jsx
// Antes (acceso directo a localStorage)
const token = localStorage.getItem("token");
const usuario = JSON.parse(localStorage.getItem("usuario"));

if (!token) {
  navigate("/");
}

// Después (usar utilidades)
import { authStorage } from "./modules/auth";

if (!authStorage.hasValidSession()) {
  navigate("/");
}

const usuario = authStorage.getUsuario();
```

### **Escenario: Logout desde cualquier componente**

```jsx
// Antes
const handleLogout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("usuario");
  navigate("/");
};

// Después
import { authStorage } from "./modules/auth";

const handleLogout = () => {
  authStorage.clearAuthData();
  navigate("/");
};
```

---

## 🔄 Migración Gradual (Sin Romper Nada)

### **Fase 1: Probar el nuevo módulo (1 día)**

1. No modificar imports existentes
2. Crear ruta de prueba:

```jsx
// App.jsx - AGREGAR ruta de prueba
import { LoginPage as LoginPageNew } from "./modules/auth";

<Route path="/login-new" element={<LoginPageNew />} />
```

3. Acceder a `http://localhost:5174/login-new`
4. Probar que funcione igual que `/`

### **Fase 2: Migrar ruta principal (1 día)**

1. Hacer backup de `App.jsx`
2. Cambiar import de Login:

```jsx
// Comentar import antiguo
// import Login from "./pages/Login";

// Usar nuevo import
import { LoginPage } from "./modules/auth";

// Actualizar ruta
<Route path="/" element={<LoginPage />} />
```

3. Probar exhaustivamente
4. Si hay problemas, revertir al backup

### **Fase 3: Actualizar PrivateRoute (1 día)**

```jsx
// Cambiar import
// import PrivateRoute from "./components/PrivateRoute";
import { PrivateRoute } from "./modules/auth";
```

### **Fase 4: Deprecar archivos antiguos (1 semana después)**

```jsx
// src/pages/Login.jsx
/**
 * @deprecated
 * Este archivo está deprecado. Usar LoginPage desde modules/auth
 * @see /src/modules/auth/pages/LoginPage.jsx
 */
import { LoginPage } from "../modules/auth";
export default LoginPage;
```

---

## 🎨 Aplicar el Patrón a Otros Módulos

### **Ejemplo: Refactorizar módulo de Clientes**

#### **1. Crear estructura**

```bash
mkdir -p src/modules/clientes/{pages,components,api,utils,constants,router}
touch src/modules/clientes/{README.md,index.js}
```

#### **2. Mover archivos**

```bash
# Copiar (no mover) archivos existentes
cp src/pages/Clientes.jsx src/modules/clientes/pages/ClientesPage.jsx
cp src/pages/ClienteDetalle.jsx src/modules/clientes/pages/ClienteDetallePage.jsx
cp src/components/ClienteCard.jsx src/modules/clientes/components/
```

#### **3. Crear utilidades**

```javascript
// src/modules/clientes/api/clientes.api.js
import api from "../../../api/config";

export const obtenerClientes = async () => {
  const response = await api.get("/clientes/");
  return response.data;
};

export const obtenerCliente = async (id) => {
  const response = await api.get(`/clientes/${id}/`);
  return response.data;
};

export const crearCliente = async (data) => {
  const response = await api.post("/clientes/", data);
  return response.data;
};
```

#### **4. Crear constantes**

```javascript
// src/modules/clientes/constants/clientes.constants.js
export const STORAGE_KEYS = {
  CLIENTE_ACTUAL: 'clienteActual',
  CLIENTES_CACHE: 'clientesCache',
};

export const FILTROS = {
  TODOS: 'todos',
  ACTIVOS: 'activos',
  INACTIVOS: 'inactivos',
};
```

#### **5. Crear index.js**

```javascript
// src/modules/clientes/index.js
export { default as ClientesPage } from './pages/ClientesPage';
export { default as ClienteDetallePage } from './pages/ClienteDetallePage';
export { default as ClienteCard } from './components/ClienteCard';
export * as clientesApi from './api/clientes.api';
export * from './constants/clientes.constants';
```

#### **6. Crear README.md**

```markdown
# 📋 Módulo de Clientes

## Descripción
Gestión de clientes del sistema SGM.

## Componentes
- **ClientesPage**: Lista de clientes
- **ClienteDetallePage**: Detalle de un cliente
- **ClienteCard**: Tarjeta visual de cliente

## APIs
- `obtenerClientes()`: GET /clientes/
- `obtenerCliente(id)`: GET /clientes/:id/
- `crearCliente(data)`: POST /clientes/

## Uso
\`\`\`javascript
import { ClientesPage, clientesApi } from '@/modules/clientes';
\`\`\`
```

---

## 📊 Checklist de Refactorización

Para asegurar calidad en cada módulo:

### **Estructura**
- [ ] Crear carpetas: `pages/`, `components/`, `api/`, `utils/`, `constants/`, `router/`
- [ ] Crear `README.md` con documentación
- [ ] Crear `index.js` con exportaciones

### **Archivos**
- [ ] Copiar (no mover) componentes existentes
- [ ] Extraer utilidades reutilizables a `utils/`
- [ ] Centralizar constantes en `constants/`
- [ ] Crear cliente API en `api/`

### **Documentación**
- [ ] JSDoc en funciones principales
- [ ] README con ejemplos de uso
- [ ] Diagramas de flujo (si aplica)

### **Testing**
- [ ] Probar importaciones
- [ ] Probar funcionalidad
- [ ] Comparar con versión original
- [ ] No hay errores en consola

### **Validación**
- [ ] Code review
- [ ] Aprobación de tech lead
- [ ] Testing en desarrollo
- [ ] Deploy a staging (si aplica)

---

## 🐛 Problemas Comunes y Soluciones

### **Problema: Import no encontrado**

```
Error: Cannot find module './modules/auth'
```

**Solución:**
```javascript
// Verificar ruta relativa correcta
import { LoginPage } from "./modules/auth";  // ✅ Correcto
import { LoginPage } from "@/modules/auth";  // ❌ Requiere alias en vite.config.js
```

**Configurar alias en `vite.config.js`:**
```javascript
export default defineConfig({
  resolve: {
    alias: {
      '@': '/src'
    }
  }
});
```

---

### **Problema: Componente no se renderiza**

```
Warning: LoginPage(...): Nothing was returned from render
```

**Solución:**
Verificar que el componente exporta correctamente:
```javascript
// ❌ Incorrecto
const LoginPage = () => { ... }

// ✅ Correcto
const LoginPage = () => { ... }
export default LoginPage;
```

---

### **Problema: localStorage no definido**

```
ReferenceError: localStorage is not defined
```

**Solución:**
Solo usar `localStorage` en el cliente (browser):
```javascript
// ❌ Incorrecto - En SSR falla
const token = localStorage.getItem("token");

// ✅ Correcto - Verificar si está en browser
const token = typeof window !== 'undefined' 
  ? localStorage.getItem("token") 
  : null;
```

---

## 🎓 Mejores Prácticas

### **1. Siempre documentar**
```javascript
/**
 * Valida el formato de un email
 * @param {string} email - Email a validar
 * @returns {string} Mensaje de error o string vacío
 */
export const validateEmail = (email) => {
  // ...
};
```

### **2. Usar constantes**
```javascript
// ❌ Evitar magic strings
if (status === 401) { ... }

// ✅ Usar constantes
import { HTTP_STATUS } from './constants';
if (status === HTTP_STATUS.UNAUTHORIZED) { ... }
```

### **3. Extraer lógica compleja**
```javascript
// ❌ Lógica en componente
const MyComponent = () => {
  const validateAndSave = () => {
    // 50 líneas de lógica...
  };
};

// ✅ Lógica en utilidad
import { validateAndSave } from '../utils/helpers';
const MyComponent = () => {
  // Componente limpio
};
```

### **4. Exportaciones consistentes**
```javascript
// index.js - Siempre usar mismo patrón
export { default as MyPage } from './pages/MyPage';
export { default as MyComponent } from './components/MyComponent';
export * as myApi from './api/my.api';
export * from './constants/my.constants';
```

---

## ⏱️ Timeline Sugerido por Módulo

| Actividad | Tiempo |
|-----------|--------|
| Crear estructura de carpetas | 15 min |
| Copiar archivos existentes | 30 min |
| Extraer utilidades | 1-2 horas |
| Crear constantes | 30 min |
| Crear cliente API | 1 hora |
| Escribir README.md | 1-2 horas |
| Testing y validación | 2-3 horas |
| **TOTAL** | **6-9 horas** |

---

## 📞 Soporte

**¿Dudas? ¿Problemas?**

1. Revisar documentación: `/docs/refactorizacion/README.md`
2. Consultar ejemplos en módulo `auth/`
3. Contactar al equipo: soporte@bdo.cl
4. Slack: #sgm-desarrollo

---

## ✅ Próximos Pasos

1. [ ] Probar el módulo auth refactorizado
2. [ ] Familiarizarse con la estructura
3. [ ] Usar utilidades en código existente
4. [ ] Aplicar patrón al siguiente módulo
5. [ ] Documentar aprendizajes

---

**¡Éxito en la refactorización!** 🚀

---

**Última actualización:** 11 de noviembre de 2025  
**Versión:** 1.0.0  
**Autor:** Equipo de Desarrollo SGM
