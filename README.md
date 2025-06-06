# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript and enable type-aware lint rules. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Manual testing

Run the backend tests with:

```bash
backend/venv/bin/python backend/manage.py test
```

Luego de subir un Libro de Remuneraciones, verifica que las columnas usadas para
crear `Empleado` (RUT, DV, nombres, apellidos y fecha de ingreso) no aparezcan en
`header_json`.

### Registro de nómina

Cada fila del Libro de Remuneraciones se almacena en el modelo `RegistroNomina`.
Los valores se guardan en el campo JSON `data` y pueden consultarse a través del
endpoint `/registros-nomina/`.

### Filtro de movimientos por clasificación

El endpoint `/contabilidad/cierres/<id>/movimientos-resumen/` acepta los
parámetros opcionales `set_id` y `opcion_id` para filtrar las cuentas según su
clasificación. Ejemplo:

```
/api/contabilidad/cierres/1/movimientos-resumen/?set_id=2&opcion_id=5
```

Retorna únicamente las cuentas que estén clasificadas con la opción indicada.
