// Construye un resumen "v2" reutilizando las respuestas existentes
// del Libro de Remuneraciones: `obtenerDetalleNominaConsolidada` (detalle)
// y `obtenerResumenNominaConsolidada` (resumen).
// No depende de movimientos de personal; toma todo desde conceptos/empleados y el resumen consolidado.

/*
Contrato de entrada esperado (parcial):
detalle = {
  cierre: { id, cliente, periodo },
  empleados: [
    {
      id, nombre_empleado, rut_empleado,
      conceptos: [ { nombre, clasificacion, monto_total, cantidad } ],
      valores_headers: { [headerName]: string | number }
    }
  ],
  headers: string[]
}

resumen = {
  resumen: {
    total_empleados,
    total_haberes_imponibles,
    total_haberes_no_imponibles,
    total_dctos_legales,
    total_otros_dctos,
    total_impuestos,
    total_aportes_patronales,
    liquido_total,
    horas_extras_cantidad_total,
    dias_ausencia_total
  },
  por_estado: { activo, nueva_incorporacion, finiquito, ausente_total, ausente_parcial }
}

Salida (parcial):
{
  version: 'v2-front',
  metadatos: { cierre_id, cliente, periodo },
  totales_por_clasificacion: { haber_imponible, haber_no_imponible, descuento_legal, otro_descuento, impuesto, aporte_patronal, liquido_total },
  horas_extras_total, dias_ausencia_total,
  salud: { total, isapre, fonasa, isapre_pct, fonasa_pct },
  afp: { total, por_afp: { habitat: n, capital: n, ... }, sin_afp },
  top_conceptos: [ { name, value } ],
  por_estado
}
*/

const num = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

const ISAPRE_PATTERNS = [
  /\bisapre\b/i,
  /(colmena|consalud|banm[ée]dica|vida\s*tres|cruz\s*blanca|vidatres|banmedica|nou|newport|fusat|san\s*lorenzo)/i,
  /plan\s+complementario/i,
  /adicional\s+salud/i,
];

const FONASA_PATTERNS = [
  /\bfonasa\b/i,
  /salud\s*7/i,
];

// Mapeo simple de AFP por nombre en concepto
const AFP_PATTERNS = {
  habitat: /habita[td]/i,
  capital: /capital/i,
  cuprum: /cuprum/i,
  modelo: /modelo/i,
  planvital: /plan\s*vital|planvital/i,
  provida: /provida/i,
  uno: /\buno\b/i,
  dipreca: /dipreca/i,
  capredena: /capredena/i,
  ips: /\bips\b|\binp\b/i,
};

const CATEGORIAS = [
  'haber_imponible',
  'haber_no_imponible',
  'descuento_legal',
  'otro_descuento',
  'impuesto',
  'aporte_patronal',
];

const normalize = (s) => (s || '').toString().toLowerCase();

function matchSome(patterns, text) {
  if (!text) return false;
  for (const re of patterns) {
    if (re.test(text)) return true;
  }
  return false;
}

export function construirInformeV2DesdeLibro(detalle, resumen) {
  const empleados = Array.isArray(detalle?.empleados) ? detalle.empleados : [];
  const res = resumen?.resumen || {};

  // Totales por clasificación desde el resumen consolidado
  const totales_por_clasificacion = {
    haber_imponible: num(res.total_haberes_imponibles),
    haber_no_imponible: num(res.total_haberes_no_imponibles),
    descuento_legal: num(res.total_dctos_legales),
    otro_descuento: num(res.total_otros_dctos),
    impuesto: num(res.total_impuestos),
    aporte_patronal: num(res.total_aportes_patronales),
    liquido_total: num(res.liquido_total),
  };

  // Horas extras (cantidad total)
  let horas_extras_total = num(res.horas_extras_cantidad_total);
  if (!horas_extras_total && empleados.length) {
    // fallback: contar cantidades de conceptos que contengan "hora extra"
    let acum = 0;
    for (const emp of empleados) {
      for (const c of emp?.conceptos || []) {
        const n = normalize(c?.nombre);
        if (/hora(s)?\s*extra(s)?/i.test(n)) {
          const cant = num(c?.cantidad);
          if (cant) acum += cant;
        }
      }
    }
    horas_extras_total = acum;
  }

  // Ausencias (total de días) si viene en resumen; no desglosamos por tipo aquí
  const dias_ausencia_total = num(res.dias_ausencia_total);

  // Salud: split exclusivo por empleado
  let totalEmps = 0, isapre = 0, fonasa = 0;
  for (const emp of empleados) {
    totalEmps += 1;
    const conceptos = emp?.conceptos || [];
    let marcaIsapre = false;
    let marcaFonasa = false;
    for (const c of conceptos) {
      const name = normalize(c?.nombre);
      if (!marcaIsapre && matchSome(ISAPRE_PATTERNS, name)) marcaIsapre = true;
      if (!marcaFonasa && matchSome(FONASA_PATTERNS, name)) marcaFonasa = true;
      if (marcaIsapre && marcaFonasa) break;
    }
    if (marcaIsapre) isapre += 1;
    else if (marcaFonasa) fonasa += 1;
  }
  const salud = {
    total: totalEmps,
    isapre,
    fonasa,
    isapre_pct: totalEmps ? +(isapre / totalEmps * 100).toFixed(2) : 0,
    fonasa_pct: totalEmps ? +(fonasa / totalEmps * 100).toFixed(2) : 0,
  };

  // AFP por empleado (elige la primera coincidencia por prioridad en AFP_PATTERNS)
  const por_afp = {};
  let sin_afp = 0;
  for (const key of Object.keys(AFP_PATTERNS)) por_afp[key] = 0;
  for (const emp of empleados) {
    const conceptos = emp?.conceptos || [];
    let asignada = null;
    OUTER: for (const c of conceptos) {
      const name = normalize(c?.nombre);
      for (const [afp, re] of Object.entries(AFP_PATTERNS)) {
        if (re.test(name)) { asignada = afp; break OUTER; }
      }
    }
    if (asignada) por_afp[asignada] = (por_afp[asignada] || 0) + 1;
    else sin_afp += 1;
  }
  const afp = {
    total: totalEmps,
    por_afp,
    sin_afp,
  };

  // Top conceptos (monto total)
  const acumConceptos = new Map();
  for (const emp of empleados) {
    for (const c of emp?.conceptos || []) {
      const name = c?.nombre || 'Sin nombre';
      const monto = num(c?.monto_total);
      if (!monto) continue;
      acumConceptos.set(name, (acumConceptos.get(name) || 0) + monto);
    }
  }
  const top_conceptos = Array.from(acumConceptos.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  // Por estado (si sirve para dotación/rotación básica)
  const por_estado = resumen?.por_estado || {};

  return {
    version: 'v2-front',
    metadatos: {
      cierre_id: detalle?.cierre?.id ?? null,
      cliente: detalle?.cierre?.cliente ?? null,
      periodo: detalle?.cierre?.periodo ?? null,
    },
    totales_por_clasificacion,
    horas_extras_total,
    dias_ausencia_total,
    salud,
    afp,
    top_conceptos,
    por_estado,
    dotacion: num(res.total_empleados),
  };
}

export default construirInformeV2DesdeLibro;
