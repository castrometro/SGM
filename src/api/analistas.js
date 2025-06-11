import api from "./config";

export const obtenerAnalistasPerformance = async () => {
  const res = await api.get("/bi-analistas/");
  return res.data;
};
