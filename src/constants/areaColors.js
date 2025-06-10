// src/constants/areaColors.js
// Sistema global de colores para las áreas del sistema SGM

export const areaColors = {
  "Contabilidad": "bg-blue-600",
  "Nomina": "bg-violet-600",
  "Riesgo": "bg-orange-600",
  "Auditoria": "bg-red-600",
  "Consultoria": "bg-green-600",
  // Agrega más áreas según sea necesario
};

export const getAreaColor = (area) => {
  return areaColors[area] || "bg-gray-600";
};

export default areaColors;
