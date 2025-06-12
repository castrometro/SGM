export const formatMoney = (num) => {
  if (num === null || num === undefined) return '';
  return new Intl.NumberFormat('es-CL', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(num));
};

export const formatMoneyCompact = (num) => {
  if (num === null || num === undefined) return '';
  const number = Number(num);
  
  if (number >= 1000000) {
    return `${(number / 1000000).toFixed(1)}M`;
  } else if (number >= 1000) {
    return `${(number / 1000).toFixed(1)}K`;
  }
  return formatMoney(number);
};

export const formatPercentage = (num, decimals = 1) => {
  if (num === null || num === undefined) return '';
  return `${Number(num).toFixed(decimals)}%`;
};

export const formatNumber = (num, decimals = 0) => {
  if (num === null || num === undefined) return '';
  return new Intl.NumberFormat('es-CL', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(Number(num));
};

export const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('es-CL');
};

export const formatDateTime = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString('es-CL');
};
