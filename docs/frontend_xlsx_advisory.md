# Advisory: SheetJS (`xlsx`) en el frontend

Resumen
-------
El `npm audit` reporta una vulnerabilidad HIGH en la librería `xlsx` (SheetJS):

- Prototype Pollution (GHSA-4r6h-8v6p-xvw6) afecta versiones `<0.19.3`.
- ReDoS (GHSA-5pgg-2g8v-p4x9) afecta versiones `<0.20.2`.

Estado en este proyecto
-----------------------
- `package.json` actual: `xlsx@^0.18.5`.
- `npm view xlsx versions` muestra versiones hasta `0.18.5` en el registro público consultado. No se encontró una versión `0.20.x` en el registro público desde este host.
- `npm audit` indica que no hay fix automático disponible (fixAvailable: false).

Recomendaciones
---------------
1. Revisar el advisory oficial y la página de SheetJS (repositorio) para confirmar qué versiones corrigen esas vulnerabilidades y si han publicado paquetes con otro esquema de versionado.
2. Si SheetJS no publica una versión parcheada en el registro público, valorar alternativas:
   - Reemplazar `xlsx` por otra librería (por ejemplo `exceljs` o `sheetjs` forks seguros) — requiere adaptación de código.
   - Limitar formatos permitidos en la UI/servidor y validar/parsear en el backend en lugar de hacerlo en el cliente.
3. Contactar con SheetJS o revisar su changelog para pedir orientación sobre la versión segura.

Pasos inmediatos sugeridos
-------------------------
- Hacer una branch feature: `feature/upgrade-xlsx`.
- Cambiar `xlsx` a una versión aprobada si existe (si encuentras `0.20.2` o superior en el registro). Probar y ejecutar `npm run dev` y tests.
- Si no existe fix publicado, implementar mitigaciones y plan de migración a `exceljs` en una rama separada.
