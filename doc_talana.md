# Documentación API Talana

## Introducción

La API REST de Talana permite integrar tu ecosistema de software con Talana, facilitando el intercambio seguro de información entre sistemas. A través de sus métodos podrás consultar, inyectar y actualizar información automatizando el flujo de datos sin intervención humana.

## Módulos Disponibles

- **Gestión de Personas**
- **Remuneraciones**
- **Firma Digital**
- **Asistencia y Turnos**

## Acceso a la API

### Requisitos
Para utilizar la API necesitas:
1. Credenciales de acceso (usuario activo)
2. Token de autenticación

### Obtención del Token
**Endpoint:** `https://talana.com/es/api/api-token-auth/`

El token debe incluirse en los headers de cada petición:
```
Key: Authorization
Value: Token 32f9c307c33e6d2aae786cca1189172bbe6bfe23
```

### Solicitud de Cuenta
El administrador de Talana en tu empresa debe solicitar la cuenta proporcionando:
- Módulo al cual desea acceder
- Tipo de acceso (escritura/lectura)
- Mostrar sueldos (sí/no)
- Nombre de la base de datos
- RUT de empresa principal

## Códigos de Respuesta HTTP

| Código | Significado | Descripción |
|--------|-------------|-------------|
| 200 | OK | Solicitud exitosa |
| 201 | Created | Recurso creado exitosamente |

## Endpoints Principales

### Personas
- **GET /persona/** - Listar personas
- **POST /persona/** - Crear personas
- **GET /persona/{id}/** - Obtener persona específica
- **PUT /persona/{id}/** - Actualizar persona
- **PATCH /persona/{id}/** - Actualizar parcialmente
- **GET /persona/{id}/saldo_vacaciones/** - Obtener saldo de vacaciones

**Filtros disponibles:**
- `rut`: Filtrar por RUT
- `nombre`: Filtrar por nombre
- `apellidoPaterno`: Filtrar por apellido paterno
- `apellidoMaterno`: Filtrar por apellido materno

### Contratos
- **GET /contrato/** - Listar contratos
- **GET /contrato-midt/** - Listar contratos DT (MiDT)
- **POST /contrato-midt/** - Crear contrato DT
- **GET /contrato-midt/{id}/** - Obtener contrato DT específico

**Filtros disponibles:**
- `rut` o `nro_documento` (Perú)
- `show_details`: Mostrar contratos en detalle (boolean)
- `solo-activos`: Filtrar solo contratos activos

### Liquidaciones
- **GET /liquidaciones/** - Lista de liquidaciones con desglose
- **GET /liquidaciones/{id}/** - Obtener liquidación específica
- **GET /liquidaciones/comprobantes/** - Lista de PDFs de liquidaciones
- **GET /payslips-wide-view** - Liquidaciones detalladas para BI

**Filtros disponibles:**
- `empleado`: ID del empleado
- `rut`: RUT del empleado
- `tipoLiquidacion`: sueldo, anticipo, finiquito, histórica, reliquidacion, sueldo reprocesada
- `periodo`: ID del periodo
- `periodo__mes`: Mes del periodo
- `periodo__ano`: Año del periodo

### Documentos
- **GET /documentos/** - Listar documentos
- **POST /documentos/** - Crear documentos
- **GET /documentos/{id}/** - Obtener documento
- **PUT /documentos/{id}/** - Actualizar documento
- **PATCH /documentos/{id}/** - Actualizar parcialmente

**Filtros disponibles:**
- `empleado`: ID de empleado
- `rut`: RUT del empleado
- `desde`: Fecha desde (YYYY-MM-DD)
- `hasta`: Fecha hasta (YYYY-MM-DD)

### Firma Digital
- **POST /document/requestSignature** - Enviar documento a firma

### Marcas (Asistencia)
- **GET /mark/** - Listar marcas (paginado)
- **POST /mark/** - Crear marcas

**Filtros disponibles:**
- `desde`: Fecha desde (YYYY-MM-DD)
- `hasta`: Fecha hasta (YYYY-MM-DD)
- `persona`: ID de empleado
- `checksum`: Filtrar por checksum

### Ausentismos
- **GET /personaAusencia-paginado/** - Listar ausentismos (licencias, permisos)

### Jornada Calculada
- **GET /assignationSummaryApi/** - Resumen de jornadas
- **GET /assignationSummaryApi/{id}/** - Obtener asignación específica

**Filtros disponibles:**
- `from_date`: Fecha inicio (YYYY-MM-DD)
- `to_date`: Fecha fin (YYYY-MM-DD)
- `status`: anomalia, inexistente, invalida, justificada, valida, en_curso, en_revision

### Otros Endpoints
- **GET /banco/** - Listar bancos soportados
- **GET /mutualSeguridad/** - Listar mutuales de seguridad
- **GET /pais/** - Lista de países
- **GET /periodos/** - Periodos de trabajo
- **GET /payroll-parameters/** - Variables de entrada en Talana
- **GET /enrolments-paginado/** - Enrolamientos paginados

## Paginación

La mayoría de endpoints soportan paginación con los parámetros:
- `page`: Número de página
- `page_size`: Resultados por página
- `cursor`: Valor del cursor de paginación

## Recursos Adicionales

- **Portal del desarrollador:** https://developers.talana.com/
- **Changelog:** https://developers.talana.com/changelog#/

## Soporte Técnico

Para soporte técnico, contacta inmediatamente con el SAC de Talana incluyendo:
- Detalle del problema
- Endpoint utilizado
- Ejemplo de request/response
- Contexto técnico

## Notas Importantes

- Prioriza el uso de APIs paginadas
- Las versiones activas se indican en la ruta o documentación
- Cambios importantes se anuncian en el Changelog
- Debes adecuar tus sistemas según tu flujo de negocio