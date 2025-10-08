# Parchear form-data en RedisInsight (plan)

Contexto
-------
La imagen `redislabs/redisinsight:2.70.1` incluye `form-data@4.0.0`, que está afectada por la vulnerabilidad CVE-2025-7783 / SNYK-JS-FORMDATA-10841150. Hay que actualizar a `form-data@4.0.4` o superior.

Opciones
-------
- Esperar release oficial de Redis Labs (preferible si se publica pronto).
- Construir imagen parcheada localmente (recomendado si necesitas cerrar la alerta ya).

Pasos para construir imagen parcheada (manual)
--------------------------------------------
1. Crear directorio: `docker/redisinsight/`
2. Añadir `Dockerfile` con el contenido:

```dockerfile
FROM redislabs/redisinsight:2.70.1
USER root
RUN set -eux; \
    cd /usr/src/app/redisinsight/api || exit 1; \
    npm install --production --no-audit --no-fund form-data@4.0.4 || true; \
    npm cache clean --force || true
LABEL patched.form-data="4.0.4"
```

3. Build:

```bash
docker build -t local/redisinsight:2.70.1-patched -f docker/redisinsight/Dockerfile .
```

4. Verificar:

```bash
docker run --rm local/redisinsight:2.70.1-patched sh -c "cat /usr/src/app/redisinsight/api/node_modules/form-data/package.json | grep '\"version\"' -m1"
```

5. Si es correcto, actualizar `docker-compose.yml` para apuntar a `local/redisinsight:2.70.1-patched` y `docker compose up -d redisinsight`.

Notas
-----
- Si la imagen base no incluye `npm` o está construida en varias etapas, el proceso requiere un Dockerfile más complejo (multi-stage) para reconstruir node_modules en una etapa builder.
- Mantener una nota en este repo para recordar rebuilds futuros cuando se haya liberado nueva versión del vendor.
