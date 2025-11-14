# ⚡ Guía Rápida - Implementación del Módulo Menu Refactorizado

**Fecha:** 14 de noviembre de 2025  
**Tiempo estimado:** 5 minutos

---

## 🎯 Objetivo

Guía paso a paso para empezar a usar el módulo `/menu` refactorizado en tu aplicación.

---

## 📋 Pasos de Implementación

### **1. Actualizar Importaciones en App.jsx**

**Ubicación:** `/root/SGM/src/App.jsx`

**Buscar:**
```jsx
import MenuUsuario from "./pages/MenuUsuario";
```

**Reemplazar por:**
```jsx
import { MenuUsuarioPage } from "./modules/menu";
```

### **2. Actualizar el Elemento de Ruta**

**Buscar:**
```jsx
<Route path="/menu" element={<MenuUsuario />} />
```

**Reemplazar por:**
```jsx
<Route path="/menu" element={<MenuUsuarioPage />} />
```

### **3. Verificar Rutas Hijas (si existen)**

Si tienes rutas anidadas bajo `/menu`, asegúrate de que sigan funcionando:

```jsx
<Route path="/menu" element={<Layout />}>
  <Route index element={<MenuUsuarioPage />} />
  {/* Otras rutas hijas */}
</Route>
```

---

## ✅ Validación

### **1. Probar en Desarrollo**

```bash
npm run dev
```

### **2. Acceder al Menú**

Navega a: `http://localhost:5174/menu`

### **3. Verificar Roles**

Prueba con diferentes tipos de usuario:

- **Analista:** Debería ver 2 opciones (Clientes, Herramientas)
- **Supervisor:** Debería ver 3 opciones (Mis Analistas, Clientes, Validaciones)
- **Gerente:** Debería ver opciones según áreas asignadas

### **4. Debug si algo falla**

```jsx
// En MenuUsuarioPage.jsx (temporalmente)
const usuario = JSON.parse(localStorage.getItem("usuario"));
console.log("Usuario completo:", usuario);
console.log("Tipo:", usuario.tipo_usuario);
console.log("Áreas:", usuario.areas);

const opciones = getUserMenuOptions(usuario);
console.log("Opciones generadas:", opciones);
```

---

## 🎨 Personalización Rápida

### **Cambiar Opacidad de Tarjetas**

```javascript
// /src/modules/menu/constants/menu.constants.js
export const CARD_OPACITY = 0.85; // Cambiar de 0.9 a 0.85
```

### **Ajustar Velocidad de Animación**

```javascript
// /src/modules/menu/constants/menu.constants.js
export const ANIMATION_DELAY_STEP = 150; // Cambiar de 100 a 150ms
```

### **Agregar Nueva Opción de Menú**

```javascript
// /src/modules/menu/utils/menuConfig.js

// 1. Importar el icono
import { TuNuevoIcono } from "lucide-react";

// 2. Agregar a la constante apropiada
const OPCIONES_ANALISTA = [
  // ... opciones existentes
  { 
    label: "Tu Nueva Opción", 
    descripcion: "Descripción breve", 
    icon: TuNuevoIcono, 
    color: "#HEX_COLOR", 
    path: "/menu/tu-ruta" 
  }
];
```

---

## 🧪 Testing Rápido

### **Test Manual**

1. Login como analista → Ver 2 opciones
2. Login como supervisor → Ver 3 opciones
3. Login como gerente contabilidad → Ver ~8 opciones
4. Login como gerente nómina → Ver ~7 opciones
5. Click en cada tarjeta → Verificar navegación correcta

### **Test Consola**

```javascript
// En la consola del navegador
const usuario = JSON.parse(localStorage.getItem("usuario"));
console.table(usuario);

// Importar y probar (si usas módulos en navegador)
import { getUserMenuOptions } from './modules/menu';
console.table(getUserMenuOptions(usuario));
```

---

## 🚨 Solución de Problemas Comunes

### **Problema 1: Pantalla en blanco**

**Causa:** Error de importación

**Solución:**
```bash
# Verificar que existen los archivos
ls -la src/modules/menu/

# Reiniciar el servidor de desarrollo
npm run dev
```

### **Problema 2: No se muestran opciones**

**Causa:** Usuario en localStorage corrupto o inexistente

**Solución:**
```javascript
// En consola del navegador
const usuario = JSON.parse(localStorage.getItem("usuario"));
console.log(usuario); // Debe tener tipo_usuario y areas

// Si está corrupto, hacer logout y login nuevamente
localStorage.clear();
```

### **Problema 3: Estilos no se aplican**

**Causa:** Tailwind no está procesando las nuevas clases

**Solución:**
```bash
# Reiniciar el servidor
npm run dev
```

---

## 📚 Recursos Adicionales

- **README del módulo:** `/src/modules/menu/README.md`
- **Documentación completa:** `/docs/refactorizacion/07_RESUMEN_MODULO_MENU.md`
- **Ejemplo de referencia:** `/src/modules/auth/` (mismo patrón)

---

## 🎉 ¡Listo!

Si llegaste hasta aquí y todo funciona, ¡has implementado exitosamente el módulo refactorizado!

### **Siguiente Paso Opcional**

Una vez validado que todo funciona correctamente, puedes eliminar los archivos antiguos:

```bash
# NO HACER HASTA ESTAR 100% SEGURO
# rm src/pages/MenuUsuario.jsx
# rm src/components/OpcionMenu.jsx
```

---

## 💬 ¿Necesitas Ayuda?

Si algo no funciona:

1. Revisa los logs de la consola del navegador
2. Verifica los logs del servidor de desarrollo
3. Compara con la estructura del módulo `/auth`
4. Consulta la documentación completa en `/docs/refactorizacion/`

---

**¡Happy coding! 🚀**
