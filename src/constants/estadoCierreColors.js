//src/constants/estadoCierreColors.js
// Sistema global de estados y colores para la aplicación SGM
const estadoCierreColors = {
  // Estados principales de cierres
  pendiente:          { texto: "Pendiente", color: "bg-yellow-600" },
  procesando:         { texto: "Procesando", color: "bg-blue-500" },
  clasificacion:      { texto: "Esperando Clasificación", color: "bg-yellow-400" },
  incidencias:        { texto: "Incidencias Abiertas", color: "bg-red-400" },
  sin_incidencias:    { texto: "Sin Incidencias", color: "bg-green-600" },
  generando_reportes: { texto: "Generando Reportes", color: "bg-yellow-500" },
  en_revision:        { texto: "En Revisión", color: "bg-orange-400" },
  rechazado:          { texto: "Rechazado", color: "bg-red-600" },
  aprobado:           { texto: "Aprobado", color: "bg-green-500" },
  finalizado:         { texto: "Finalizado", color: "bg-green-700" },
  completo:           { texto: "Completado", color: "bg-green-700" },
  
  // Estados específicos de documentos y archivos
  no_subido:          { texto: "No subido", color: "bg-gray-600" },
  subido:             { texto: "Subido", color: "bg-green-400" },
  procesado:          { texto: "Procesado", color: "bg-green-600" },
  con_error:          { texto: "Error", color: "bg-red-500" },
  
  // Estados específicos de libros y clasificaciones
  analizando_hdrs:    { texto: "Analizando Headers", color: "bg-blue-400" },
  hdrs_analizados:    { texto: "Headers Analizados", color: "bg-green-400" },
  clasif_pendiente:   { texto: "Clasificación Pendiente", color: "bg-yellow-500" },
  clasif_en_proceso:  { texto: "Clasificando", color: "bg-blue-400" },
  clasificado:        { texto: "Clasificado", color: "bg-green-500" },
  
  // Estados específicos de movimientos
  en_proceso:         { texto: "Procesando", color: "bg-blue-400" },
  
  // Estados de traducción
  traduciendo:        { texto: "Traduciendo", color: "bg-blue-400" },
  traducido:          { texto: "Traducido", color: "bg-green-500" },
};

// Función helper para renderizar estados de manera consistente
export const renderEstadoCierre = (estado, size = "sm") => {
  const obj = estadoCierreColors[estado] || { texto: estado, color: "bg-gray-600" };
  
  const sizeClasses = {
    xs: "px-2 py-0.5 text-xs",
    sm: "px-3 py-1 text-sm", 
    md: "px-4 py-1 text-base",
    lg: "px-5 py-2 text-lg"
  };
  
  return {
    texto: obj.texto,
    color: obj.color,
    className: `inline-block ${sizeClasses[size]} rounded-full text-white font-semibold ${obj.color}`
  };
};

export default estadoCierreColors;
