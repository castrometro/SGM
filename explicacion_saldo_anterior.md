# Explicación del Saldo Anterior en Libro Mayor

## Cómo funciona actualmente:

### 1. Origen del Saldo Anterior
- El saldo anterior se obtiene **por cuenta individual** desde el archivo Excel
- Se extrae de la fila que contiene "SALDO ANTERIOR DE LA CUENTA: [codigo] [nombre]"
- El valor se toma de:
  - Columna **SALDO** (si existe)
  - Columna **DEBE** (si no existe SALDO)

### 2. Ejemplo del archivo Excel:
```
SALDO ANTERIOR DE LA CUENTA: 1-01-001-001-0001  Caja                     | DEBE: 50000 | HABER: 0
SALDO ANTERIOR DE LA CUENTA: 2-01-001-001-0001  Proveedores              | DEBE: 0     | HABER: 30000
SALDO ANTERIOR DE LA CUENTA: 3-01-001-001-0001  Capital                  | DEBE: 0     | HABER: 100000
SALDO ANTERIOR DE LA CUENTA: 4-01-001-001-0001  Ventas                   | DEBE: 0     | HABER: 0
SALDO ANTERIOR DE LA CUENTA: 5-01-001-001-0001  Gastos Administración    | DEBE: 0     | HABER: 0
```

### 3. Clasificación por ESF/ERI:
- **Caja (1-01-001-001-0001)**: Clasificada como ESF → Saldo: $50,000
- **Proveedores (2-01-001-001-0001)**: Clasificada como ESF → Saldo: $-30,000
- **Capital (3-01-001-001-0001)**: Clasificada como ESF → Saldo: $-100,000
- **Ventas (4-01-001-001-0001)**: Clasificada como ERI → Saldo: $0
- **Gastos (5-01-001-001-0001)**: Clasificada como ERI → Saldo: $0

### 4. Acumulación en totales ESF/ERI:
```python
totales_esf_eri = {
    'ESF': {'saldo_ant': 50000 + (-30000) + (-100000) = -80000},
    'ERI': {'saldo_ant': 0 + 0 = 0}
}
```

## Problema identificado:

### ¿Es correcto este enfoque?
- **SÍ**: El saldo anterior de cada cuenta debe sumarse según su clasificación ESF/ERI
- **PERO**: La lógica de identificación ESF/ERI podría no ser precisa
- **IMPORTANTE**: El saldo anterior **NO se recalcula** - viene del archivo Excel

### ¿Qué podría estar fallando?
1. **Clasificación incorrecta** de cuentas como ESF/ERI
2. **Cuentas sin clasificar** no se incluyen en los totales
3. **Formato del archivo Excel** podría ser inconsistente

## Sugerencias de mejora:

### 1. Validar clasificación ESF/ERI
- Asegurar que todas las cuentas estén correctamente clasificadas
- Implementar validación de que la suma ESF + ERI = 0 (balance cuadrado)

### 2. Logging detallado
- Registrar qué cuentas se clasifican como ESF/ERI
- Mostrar el saldo anterior de cada cuenta y su contribución al total

### 3. Manejo de cuentas sin clasificar
- Decidir qué hacer con cuentas que no tienen clasificación ESF/ERI
- ¿Se ignoran? ¿Se reportan como incidencia?

### 4. Validación del archivo Excel
- Verificar que el formato sea consistente
- Validar que los saldos anteriores sean coherentes
