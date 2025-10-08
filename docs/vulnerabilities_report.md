# Vulnerabilities report

Este documento es una plantilla para registrar vulnerabilidades detectadas en el proyecto y su estado de mitigación. Úsalo para pegar o añadir las vulnerabilidades que me indiques y llevar el seguimiento.

Formato por entrada
--------------------
- Id / Reference: (p. ej. SNYK-JS-FORMDATA-10841150)
- CVE: (p. ej. CVE-2025-7783)
- Paquete / Componente: (p. ej. form-data)
- Ubicación: (p. ej. imagen: redislabs/redisinsight:2.70.1 -> /usr/src/app/redisinsight/api/node_modules)
- Version(es afectada(s)): (p. ej. 4.0.0)
- Versión recomendada / fix: (p. ej. >=4.0.4)
- Severidad: (Low/Medium/High/Critical)
- Descripción corta: (una línea)
- Riesgo / impacto: (una frase)
- Pasos de mitigación sugeridos: (acción inmediata / plan a medio plazo)
- Estado: (Open / In progress / Mitigated / Deferred)
- Responsable: (quién hará el cambio)
- Evidencia / notas: (comandos, salidas, archivos modificados)

Tabla de ejemplo
----------------
| Id | CVE | Paquete | Ubicación | Afecta | Fix | Severidad | Estado |
|---|---:|---|---|---:|---|---|---|
| SNYK-JS-FORMDATA-10841150 | CVE-2025-7783 | form-data | redisinsight image (/usr/src/app/redisinsight/api) | 4.0.0 | 4.0.4+ | High | Open |

Comandos útiles para reproducir evidencia
----------------------------------------
- Mostrar package.json dentro de una imagen:

```bash
docker run --rm --entrypoint sh redislabs/redisinsight:2.70.1 -c "cat /usr/src/app/redisinsight/api/node_modules/form-data/package.json | grep '\"version\"' -m1"
```

- Buscar en el repo local:

```bash
grep -R "form-data" -n || true
npm ls form-data --all || true
```

- Crear dump o backup (para DB-related fixes): ejemplo ya disponible en `scripts/refresh_collation.sh`.

Proceso recomendado al añadir una entrada
---------------------------------------
1. Añadir la entrada rellenando los campos de la plantilla.
2. Añadir evidencia (comandos y salidas) en el campo `Evidencia / notas` o como attachments.
3. Definir un responsable y plazo para mitigación.
4. Si la mitigación requiere build/deploy (por ejemplo parchear una imagen), documentar el Dockerfile/steps en `docs/` y enlazarlo desde aquí.

Cuando me des la lista de vulnerabilidades (cada una con la info que tengas: id, paquete, ubicación, CVE si existe), yo las añadiré aquí y propondré pasos concretos para cada una (patch immediate, plan de testing y deploy, PRs, etc.).

Entradas detectadas (08-10-2025)
-------------------------------

A continuación se registran las vulnerabilidades detectadas por la herramienta Davis (resumen aportado). Cada entrada incluye la metadata disponible desde el escaneo. Revisa y añade evidencia local si la tienes (comandos, contenedores, package.json, etc.).


1) Id: S-2 — Command Injection
- CVE: (no provisto)
- Paquete / Componente: Node.js (runtime)
- Ubicación: Runtime (posibles binarios o scripts en ejecución)
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: investigar origen exacto (archivo/binario) y aplicar actualización/patch según vendor
- Severidad: CVSS 98 (CVSS vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
- Descripción corta: Command injection detectado por análisis dinámico (exploit status: Available)
- Riesgo / impacto: ejecución remota de comandos; alta prioridad para investigación y mitigación inmediata.
- Pasos de mitigación sugeridos: identificar binario/servicio afectado (logs de Dynatrace, paths), aislar servicio, actualizar paquete o aplicar mitigación de entrada. Si procede, detener/redeploy con imagen parcheada.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 86; abierto desde 08-10-2025 16:17.

2) Id: S-21 — Function Call With Incorrect Argument Type
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library (no path específicado)
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: revisar dependencia que originó el hallazgo y actualizar a la versión que corrige el bug según vendor
- Severidad: CVSS 91 (CVSS vector: CVSS:4.0/AV:N/AC:H/AT:P/PR:N/UI:N/VC:N/VI:H/VA:H/SC:H/SI:H/SA:N)
- Descripción corta: llamadas con tipos incorrectos que pueden causar fallos o comportamientos inesperados.
- Riesgo / impacto: posibilidad de fallo/denegación de servicio o comportamiento inseguro; priorizar revisión de stack trace y librería implicada.
- Pasos de mitigación sugeridos: identificar la librería y la llamada, revisar changelog y tests, actualizar o aplicar parche local.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 72; abierto desde 08-10-2025 16:17.

3) Id: S-9 — Uncaught Exception
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: mitigar mediante manejo de excepciones y actualizar la dependencia si es un bug conocido
- Severidad: CVSS 87 (CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H)
- Descripción corta: excepciones no capturadas que pueden derivar en crashes o leaks de información.
- Riesgo / impacto: denegación de servicio o exposición de datos; revisar logs y añadir try/catch donde proceda.
- Pasos de mitigación sugeridos: localizar stack traces, añadir manejo de errores, actualizar dependencias implicadas.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 71; abierto desde 08-10-2025 16:32.

4) Id: S-11 — Remote Code Execution (RCE)
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: investigar la librería implicada; parchear o actualizar según vendor
- Severidad: CVSS 66 (CVSS:3.1/AV:N/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H)
- Descripción corta: posible ejecución remota de código en condiciones específicas.
- Riesgo / impacto: RCE es crítico; tratar con máxima prioridad si se confirma exploitability.
- Pasos de mitigación sugeridos: aislar servicio, bloquear acceso de red, parchear, aplicar WAF/protecciones temporales.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 55; abierto desde 08-10-2025 10:37.

5) Id: S-17 — Arbitrary File Write
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: actualizar la librería afectada según vendor
- Severidad: CVSS 81 (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)
- Descripción corta: escritura arbitraria de archivos por entrada controlada por el atacante.
- Riesgo / impacto: posibilidad de persistencia de código malicioso; revisar paths y permisos de archivos.
- Pasos de mitigación sugeridos: restringir permisos, validar entradas y actualizar paquete.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 54; abierto desde 08-10-2025 10:37.

6) Id: S-15 — Arbitrary File Overwrite
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: actualizar la dependencia implicada
- Severidad: CVSS 81 (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)
- Descripción corta: sobreescritura arbitraria de archivos.
- Riesgo / impacto: integridad de archivos comprometida; similar a Arbitrary File Write.
- Pasos de mitigación sugeridos: validar entradas, fijar rutas seguras y actualizar paquete.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 54; abierto desde 08-10-2025 10:37.

7) Id: S-27 — Allocation of Resources Without Limits or Throttling
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: revisar la función y version(es) implicadas; aplicar límites/quotas
- Severidad: CVSS 69 (CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:L)
- Descripción corta: consumo de recursos sin límites o throttling.
- Riesgo / impacto: DoS por agotamiento de recursos; planear throttling y límites.
- Pasos de mitigación sugeridos: aplicar rate-limiting, circuit-breakers, actualizar librerías implicadas.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 53; abierto desde 08-10-2025 16:17.

8) Id: S-18 — Insertion of Sensitive Information into Log File
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: corregir logging y sanitizar datos sensibles; actualizar componentes si corresponde
- Severidad: CVSS 53 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N)
- Descripción corta: datos sensibles escritos a logs.
- Riesgo / impacto: exposición de secretos/PII en logs; revisar políticas de logging y rotación.
- Pasos de mitigación sugeridos: sanitizar logs, rotación, ACLs y actualizar librerías si necesario.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 53; abierto desde 08-10-2025 10:37.

9) Id: S-14 — Access Restriction Bypass
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: corregir controles de acceso y actualizar librería si aplica
- Severidad: CVSS 53 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N)
- Descripción corta: bypass de restricciones de acceso.
- Riesgo / impacto: exposición de funciones no autorizadas; revisar políticas de authz y logs.
- Pasos de mitigación sugeridos: revisar rutas, middleware de autenticación/autorización y parches.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 53; abierto desde 08-10-2025 10:37.

10) Id: S-4 — Predictable Value Range from Previous Values
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: revisar la librería que genera valores pseudo-aleatorios y actualizarla (ej. form-data was related previously)
- Severidad: CVSS 94 (CVSS:4.0/AV:N/AC:H/AT:N/PR:N/UI:N/VC:H/VI:H/VA:N/SC:H/SI:H/SA:N)
- Descripción corta: rango de valores predecible a partir de valores previos (Math.random misuse)
- Riesgo / impacto: manipulación de límites en multipart boundaries u otros; validar uso cryptográficamente seguro (crypto.randomBytes)
- Pasos de mitigación sugeridos: identificar función afectada, usar RNG criptográfico y actualizar paquete.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 53; abierto desde 08-10-2025 16:17.

11) Id: S-10 — Improper Handling of Unexpected Data Type
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: añadir validaciones y actualizar librería si es bug conocido
- Severidad: CVSS 46 (CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:L/VI:L/VA:N)
- Descripción corta: manejo incorrecto de tipos de datos inesperados.
- Riesgo / impacto: posibles crashes o comportamientos incorrectos; añadir validation layers.
- Pasos de mitigación sugeridos: input validation, tests y actualización.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 46; abierto desde 08-10-2025 16:17.

12) Id: S-12 — npm Token Leak
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library (posible exposición en logs/configs)
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: rotar tokens afectados y eliminar uso de tokens en repositorios; actualizar procesos CI/CD
- Severidad: CVSS 68 (CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N)
- Descripción corta: leak de token npm (credentials exposure).
- Riesgo / impacto: uso no autorizado de registries o publicación de paquetes; rotar credenciales inmediatamente.
- Pasos de mitigación sugeridos: rotar npm tokens, revisar logs/commits, invalidar tokens en npmjs, auditoría de repositorios.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 42; abierto desde 08-10-2025 10:37.

13) Id: S-13 — Symlink attack due to predictable tmp folder names
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: utilizar funciones seguras para tmp dirs o usar mkdtemp; actualizar librería si es vulnerabilidad conocida
- Severidad: CVSS 36 (CVSS:3.1/AV:L/AC:H/PR:L/UI:N/S:U/C:N/I:L/A:L)
- Descripción corta: ataques de symlink por nombres de carpetas temporales predecibles.
- Riesgo / impacto: escalada o corrupción de archivos temporales.
- Pasos de mitigación sugeridos: usar mkdtemp, permisos restrictivos y revisar librerías que usan tmp paths.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 36; abierto desde 08-10-2025 10:37.

14) Id: S-19 — CVE-2025-23084
- CVE: CVE-2025-23084
- Paquete / Componente: Node.js (Runtime)
- Ubicación: Runtime
- Version(es afectada(s)): no especificado (ver CVE vendor advisory)
- Versión recomendada / fix: seguir el advisory del CVE y aplicar patches del vendor / runtime
- Severidad: CVSS 55 (CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N)
- Descripción corta: vulnerabilidad con identificador CVE-2025-23084 reportada por Davis
- Riesgo / impacto: según advisory; revisar detalles del CVE y aplicar parche del runtime
- Pasos de mitigación sugeridos: revisar advisory, actualizar runtime/paquete responsable y aplicar mitigaciones compensatorias
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 33; abierto desde 08-10-2025 16:17.

15) Id: S-16 — Unauthorized File Access
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: actualizar librería y revisar permisos de filesystem
- Severidad: CVSS 26 (CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:N/A:N)
- Descripción corta: acceso no autorizado a archivos.
- Riesgo / impacto: exposición limitada de archivos; revisar ACLs.
- Pasos de mitigación sugeridos: revisar rutas, permisos y actualizar la dependencia.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 26; abierto desde 08-10-2025 10:37.

16) Id: S-3 — Regular Expression Denial of Service (ReDoS)
- CVE: (no provisto)
- Paquete / Componente: Node.js (Library)
- Ubicación: Library
- Version(es afectada(s)): no especificado
- Versión recomendada / fix: actualizar la librería que usa regex vulnerable o mitigar con timeouts/input limits
- Severidad: CVSS 23 (CVSS:4.0/AV:N/AC:L/AT:P/PR:L/UI:N/VC:N/VI:N/VA:L)
- Descripción corta: ReDoS mediante expresiones regulares maliciosas.
- Riesgo / impacto: CPU exhaustion/DoS; añadir límites de entrada y actualizar dependencias.
- Pasos de mitigación sugeridos: validar inputs, actualizar librerías y añadir timeouts/circuit-breakers.
- Estado: Open
- Responsable: TBD
- Evidencia / notas: Davis score 21; abierto desde 08-10-2025 16:17.

