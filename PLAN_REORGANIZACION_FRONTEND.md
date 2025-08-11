# Plan de Reorganización Frontend - Separación Contabilidad vs Nómina

## Elementos a ELIMINAR (relacionados con nómina actual)

### 1. Páginas
- `/pages/CierreDetalleNomina.jsx`

### 2. Componentes
- `/components/DashboardNomina/` (directorio completo)
- `/components/TarjetasCierreNomina/` (directorio completo)  
- `/components/LibroRemuneraciones/` (directorio completo)
- `/components/MovimientosMes/` (directorio completo)
- `/components/nomina/` (directorio completo)
- `/components/Gerente/EstadosCierresNomina.jsx`
- `/components/Gerente/LogsActividadNomina.jsx`
- `/components/Gerente/CacheRedisNomina.jsx`

### 3. APIs
- `/api/nomina.js`
- `/api/gerenteNomina.js`
- `/api/payroll/` (directorio completo - será reemplazado)

### 4. Rutas en App.jsx
- Todas las rutas con "nomina" en el path
- Rutas de gerente con "nomina"

## Elementos a MANTENER (contabilidad)

### 1. Páginas Core
- Login.jsx
- MenuUsuario.jsx
- Clientes.jsx
- ClienteDetalle.jsx
- PaginaClasificacion.jsx
- ClasificacionCierre.jsx
- HistorialCierresPage.jsx
- CrearCierre.jsx
- CierreDetalle.jsx
- AnalisisLibro.jsx
- MovimientosCuenta.jsx
- InformesAnalistas.jsx
- Dashboard.jsx
- CapturaMasivaGastos.jsx
- DashboardGerente.jsx
- VistaGerencial.jsx
- Tools.jsx
- MisAnalistas.jsx

### 2. Componentes Core
- Layout.jsx
- PrivateRoute.jsx
- Header.jsx
- Navbar.jsx
- Sidebar.jsx
- Footer.jsx
- Notificacion.jsx
- EstadoBadge.jsx
- AreaIndicator.jsx
- Todos los componentes de DashboardGerente/
- TarjetasCierreContabilidad/
- InfoCards/
- VistaGerencial/
- CrearCierre/

### 3. APIs Core
- auth.js
- clientes.js
- contabilidad.js
- areas.js
- analistas.js
- supervisores.js
- gerente.js
- capturaGastos.js
- config.js

## Pasos de Reorganización

1. **FASE 1: ELIMINAR** - Remover todo lo relacionado con nómina
2. **FASE 2: LIMPIAR** - Actualizar rutas y referencias
3. **FASE 3: REORGANIZAR** - Restructurar directorios si es necesario
4. **FASE 4: PREPARAR** - Dejar listo para nueva implementación de payroll
