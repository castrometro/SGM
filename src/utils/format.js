export const formatMoney = (num) => {
  if (num === null || num === undefined) return '';
  return new Intl.NumberFormat('es-CL', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(num));
};
