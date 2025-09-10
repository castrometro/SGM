import { useMemo } from 'react';

export function useMovimientosMetrics(datos){
  return useMemo(()=> {
    const movs = datos?.movimientos || [];
    let ingresos=0, finiquitos=0, diasAusJustificados=0, vacacionesDias=0, ausSinJustificar=0;
    const ingresosSet=new Set(), finiquitosSet=new Set(), diasAusJustSet=new Set(), vacacionesSet=new Set(), ausSinJustSet=new Set();
    for (const mv of movs) {
      const cat = mv.categoria;
      const empKey = mv?.empleado ? (mv.empleado.id || mv.empleado.rut || mv.empleado.uuid || mv.empleado.run || null) : null;
      if (cat === 'ingreso') ingresos += 1;
      else if (cat === 'finiquito') finiquitos += 1;
      else if (cat === 'ausencia') {
        const st = (mv.subtipo || '').trim() || 'sin_justificar';
        const dias = Number(mv.dias_en_periodo ?? mv.dias_evento ?? 0) || 0;
        if (st === 'vacaciones') vacacionesDias += dias;
        else if (st === 'sin_justificar') ausSinJustificar += 1;
        else diasAusJustificados += dias;
      }
      if (empKey) {
        if (cat === 'ingreso') ingresosSet.add(empKey);
        else if (cat === 'finiquito') finiquitosSet.add(empKey);
        else if (cat === 'ausencia') {
          const st = (mv.subtipo || '').trim() || 'sin_justificar';
            if (st === 'vacaciones') vacacionesSet.add(empKey);
            else if (st === 'sin_justificar') ausSinJustSet.add(empKey);
            else diasAusJustSet.add(empKey);
        }
      }
    }
    return {
      ingresos, finiquitos, diasAusJustificados, vacacionesDias, ausSinJustificar,
      ingresosEmp: ingresosSet.size,
      finiquitosEmp: finiquitosSet.size,
      diasAusJustEmp: diasAusJustSet.size,
      vacacionesEmp: vacacionesSet.size,
      ausSinJustEmp: ausSinJustSet.size,
      total: movs.length
    };
  }, [datos]);
}
