// Configuración para determinar el área del usuario y módulo del cierre
export const determinarAreaUsuario = (usuario) => {
  // TODO: Implementar lógica basada en el usuario logueado
  // Por ahora retorna contabilidad por defecto
  if (!usuario) return 'contabilidad';
  
  // Lógica basada en roles o departamento del usuario
  if (usuario.departamento === 'nomina' || usuario.role?.includes('nomina')) {
    return 'nomina';
  }
  
  if (usuario.departamento === 'rrhh' || usuario.role?.includes('rrhh')) {
    return 'rrhh';
  }
  
  return 'contabilidad'; // Por defecto
};

export const determinarModuloCierre = (cierre, usuario, path) => {
  // Prioridad 1: Detectar desde la URL
  if (path.includes('/nomina/') || path.includes('/cierres-payroll/')) return 'payroll';
  if (path.includes('/rrhh/')) return 'rrhh';
  if (path.includes('/contabilidad/')) return 'contabilidad';
  
  // Prioridad 2: Tipo específico del cierre
  if (cierre?.tipo_modulo) return cierre.tipo_modulo;
  
  // Prioridad 3: Área del usuario
  return determinarAreaUsuario(usuario);
};

export const AREAS_CONFIG = {
  contabilidad: {
    nombre: 'Contabilidad',
    color: 'blue',
    descripcion: 'Gestión de cierres contables y libros mayores'
  },
  payroll: {
    nombre: 'Payroll', 
    color: 'green',
    descripcion: 'Procesamiento de nóminas y remuneraciones'
  },
  nomina: {
    nombre: 'Nómina', 
    color: 'green',
    descripcion: 'Procesamiento de nóminas y remuneraciones'
  },
  rrhh: {
    nombre: 'Recursos Humanos',
    color: 'purple', 
    descripcion: 'Indicadores de personal y gestión humana'
  }
};
