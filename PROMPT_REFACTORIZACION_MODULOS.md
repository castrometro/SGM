# 📋 Prompt para Refactorización de Módulos

**Usar este prompt con cualquier módulo que quieras refactorizar**

---

## 🎯 PROMPT PARA COPIAR Y PEGAR

```
Necesito refactorizar el módulo [NOMBRE_DEL_MODULO] siguiendo el mismo patrón 
que se aplicó en /src/modules/auth y /src/modules/menu.

Archivos actuales a refactorizar:
- /src/pages/[PaginaPrincipal].jsx
- /src/components/[ComponentesRelacionados].jsx
- [Otros archivos relacionados]

Por favor:

1. Crea la estructura modular en /src/modules/[nombre_modulo]/ con:
   - README.md (documentación completa)
   - index.js (exportaciones públicas)
   - pages/ (páginas del módulo)
   - components/ (componentes colocados)
   - utils/ (utilidades y lógica de negocio)
   - constants/ (constantes centralizadas)
   - api/ (cliente API si aplica)
   - router/ (configuración de rutas)

2. Aplica los principios:
   - Colocación: Todo dentro del módulo
   - Separación: Lógica separada de UI
   - Documentación: README integrado
   - Constantes tipadas: Sin strings mágicos

3. Crea documentación en /docs/refactorizacion/:
   - [XX]_RESUMEN_MODULO_[NOMBRE].md
   - [XX]_GUIA_RAPIDA_[NOMBRE].md
   - [XX]_ARBOL_ESTRUCTURA_[NOMBRE].md

4. Integra en rutas de desarrollo:
   - Agregar al ModulesShowcase.jsx
   - Crear [Nombre]ModuleDemo.jsx
   - Agregar ruta en App.jsx: /dev/modules/[nombre]/demo
   - Actualizar DevModulesButton.jsx

5. La página demo debe ser simple:
   - Renderizar el componente principal del módulo
   - Incluir Header y Footer del sistema
   - Banner de demo arriba
   - DevModulesButton flotante

Referencia: /src/modules/auth y /src/modules/menu como ejemplos completos.
```

---

## 📝 EJEMPLO CONCRETO DE USO

### Para refactorizar el módulo de Clientes:

```
Necesito refactorizar el módulo de Clientes siguiendo el mismo patrón 
que se aplicó en /src/modules/auth y /src/modules/menu.

Archivos actuales a refactorizar:
- /src/pages/Clientes.jsx
- /src/pages/ClienteDetalle.jsx
- /src/components/ClienteCard.jsx
- /src/components/ClienteForm.jsx

Por favor:

1. Crea la estructura modular en /src/modules/clientes/ con:
   - README.md (documentación completa del módulo clientes)
   - index.js (exportaciones públicas)
   - pages/ (ClientesPage.jsx, ClienteDetallePage.jsx)
   - components/ (ClienteCard, ClienteForm, etc.)
   - utils/ (clienteHelpers.js con funciones de negocio)
   - constants/ (clientes.constants.js)
   - api/ (clientes.api.js)
   - router/ (clientes.routes.jsx)

2. Aplica los principios:
   - Colocación: Todo dentro del módulo
   - Separación: Lógica de clientes en utils/
   - Documentación: README con ejemplos
   - Constantes: CLIENTE_ESTADOS, etc.

3. Crea documentación en /docs/refactorizacion/:
   - 10_RESUMEN_MODULO_CLIENTES.md
   - 11_GUIA_RAPIDA_CLIENTES.md
   - 12_ARBOL_ESTRUCTURA_CLIENTES.md

4. Integra en rutas de desarrollo:
   - Agregar módulo clientes al ModulesShowcase.jsx
   - Crear ClientesModuleDemo.jsx
   - Agregar ruta en App.jsx: /dev/modules/clientes/demo
   - Actualizar DevModulesButton.jsx con link a demo

5. ClientesModuleDemo.jsx debe:
   - Renderizar <ClientesPage /> (componente principal)
   - Incluir <Header /> y <Footer />
   - Banner de demo con "DEMO: Módulo Clientes Refactorizado"
   - <DevModulesButton /> flotante

Referencia: /src/modules/auth y /src/modules/menu como ejemplos completos.
```

---

## 🎯 VARIACIONES DEL PROMPT

### Para módulos sin API:

```
Necesito refactorizar el módulo [NOMBRE] siguiendo el patrón de /src/modules/menu.

Este módulo NO tiene API propia, solo UI y lógica local.

Excluir carpeta api/ de la estructura.

[resto del prompt igual]
```

### Para módulos con hooks personalizados:

```
Necesito refactorizar el módulo [NOMBRE] siguiendo el patrón de /src/modules/auth.

Este módulo incluye custom hooks:
- use[Nombre].js
- use[OtroHook].js

Incluir carpeta hooks/ en la estructura modular.

[resto del prompt igual]
```

### Para módulos con estilos CSS:

```
Necesito refactorizar el módulo [NOMBRE] siguiendo el patrón establecido.

Este módulo tiene estilos CSS propios:
- [archivo].css
- [archivo].module.css

Incluir carpeta styles/ dentro del módulo para colocar los estilos.

[resto del prompt igual]
```

---

## 📚 CHECKLIST PARA VALIDAR LA REFACTORIZACIÓN

Usa esto para verificar que la refactorización esté completa:

```
□ Estructura de carpetas creada en /src/modules/[nombre]/
□ README.md completo con ejemplos
□ index.js con todas las exportaciones públicas
□ Páginas en pages/ refactorizadas
□ Componentes colocados en components/
□ Lógica extraída a utils/
□ Constantes centralizadas en constants/
□ API client en api/ (si aplica)
□ Router configurado en router/

□ Documentación creada en /docs/refactorizacion/:
  □ XX_RESUMEN_MODULO_[NOMBRE].md
  □ XX_GUIA_RAPIDA_[NOMBRE].md
  □ XX_ARBOL_ESTRUCTURA_[NOMBRE].md
  □ README.md actualizado

□ Integración en desarrollo:
  □ Agregado a ModulesShowcase.jsx
  □ [Nombre]ModuleDemo.jsx creado
  □ Ruta agregada en App.jsx
  □ DevModulesButton.jsx actualizado

□ Demo funcional:
  □ Renderiza componente principal
  □ Incluye Header y Footer
  □ Banner de demo visible
  □ DevModulesButton presente
  □ Navegación funciona correctamente
```

---

## 🔗 ARCHIVOS DE REFERENCIA

Al usar el prompt, menciona estos archivos como referencia:

**Estructura de módulo:**
- `/src/modules/auth/` - Módulo con API
- `/src/modules/menu/` - Módulo solo UI

**Documentación:**
- `/docs/refactorizacion/02_PROPUESTA_ESTRUCTURA_MODULAR.md`
- `/docs/refactorizacion/06_PRINCIPIO_COLOCACION.md`

**Integración en desarrollo:**
- `/src/pages/ModulesShowcase.jsx` - Lista de módulos
- `/src/pages/AuthModuleDemo.jsx` - Demo con API
- `/src/pages/MenuModuleDemo.jsx` - Demo solo UI
- `/src/modules/auth/components/DevModulesButton.jsx` - Botón flotante

**Ejemplos de uso:**
- `/src/App.jsx` - Ver cómo se importan y usan los módulos

---

## 💡 TIPS PARA USAR EL PROMPT

1. **Sé específico** con los archivos que quieres refactorizar
2. **Menciona características especiales** del módulo (API, hooks, estilos, etc.)
3. **Indica el número de documentación** para mantener orden en /docs/refactorizacion/
4. **Pide validación** de que todo funciona antes de eliminar archivos antiguos
5. **Solicita el checklist** al final para verificar completitud

---

## 📋 TEMPLATE COMPLETO LISTO PARA USAR

```markdown
Tal como se hizo la refactorización de /menu, hazla con /[NOMBRE_MODULO].

Archivos a refactorizar:
- [listar archivos]

Características especiales:
- [API/hooks/estilos/etc. si aplica]

Número de documentación:
- Iniciar en [XX]_RESUMEN_MODULO_[NOMBRE].md

Referencia: /src/modules/auth y /src/modules/menu
```

---

**Fecha de creación:** 14 de noviembre de 2025  
**Versión:** 1.0  
**Mantenido por:** Sistema SGM

---

## 🎉 EJEMPLO REAL USADO

Este fue el prompt que funcionó para /menu:

> "Tal como se hizo la refactorización de login.
> Hazla con /menu"

Y el sistema:
1. ✅ Analizó /src/modules/auth como referencia
2. ✅ Identificó MenuUsuario.jsx y OpcionMenu.jsx
3. ✅ Creó estructura completa en /src/modules/menu
4. ✅ Documentó en /docs/refactorizacion/
5. ✅ Integró en /dev/modules
6. ✅ Creó MenuModuleDemo.jsx funcional

**¡Usa este mismo patrón para cualquier módulo!** 🚀
