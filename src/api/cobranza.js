// src/api/cobranza.js
import api from './config';

export async function parseAuxiliarCXC(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await api.post('/cobranza/parse-auxiliar/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}
