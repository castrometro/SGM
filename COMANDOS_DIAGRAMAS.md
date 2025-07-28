# Comandos para Generar Diagramas Django con django-extensions

Una vez que docker-extensions está instalado y GraphViz configurado, puedes generar diferentes tipos de diagramas de tus modelos Django.

## 🚀 Comandos Básicos

### 1. Diagrama de Todos los Modelos
```bash
docker exec sgm-django-1 python manage.py graph_models -a -g -o diagrams/all_models.png
```
- `-a`: Incluye todas las aplicaciones
- `-g`: Agrupa los modelos por aplicación
- `-o`: Especifica el archivo de salida

### 2. Diagramas por Aplicación Específica
```bash
# Modelos de Contabilidad
docker exec sgm-django-1 python manage.py graph_models contabilidad -o diagrams/contabilidad_models.png

# Modelos de Nómina
docker exec sgm-django-1 python manage.py graph_models nomina -o diagrams/nomina_models.png

# Modelos de API
docker exec sgm-django-1 python manage.py graph_models api -o diagrams/api_models.png
```

### 3. Diagramas Personalizados
```bash
# Diagrama sin etiquetas de relaciones (más limpio)
docker exec sgm-django-1 python manage.py graph_models -a -g --hide-edge-labels -o diagrams/clean_models.png

# Diagrama con códigos de color
docker exec sgm-django-1 python manage.py graph_models -a -g --color-code-deletions -o diagrams/colored_models.png

# Diagrama en formato SVG (escalable)
docker exec sgm-django-1 python manage.py graph_models -a -g -o diagrams/models.svg
```

### 4. Generar Archivo DOT para Personalización
```bash
docker exec sgm-django-1 python manage.py graph_models -a -g > diagrams/models.dot
```

## 🎯 Opciones Avanzadas

### Filtrar Campos Específicos
```bash
# Solo mostrar campos de clave foránea
docker exec sgm-django-1 python manage.py graph_models -a -g --hide-edge-labels --exclude-columns=id -o diagrams/fk_only.png

# Excluir campos específicos
docker exec sgm-django-1 python manage.py graph_models -a -g --exclude-columns=created_at,updated_at -o diagrams/no_timestamps.png
```

### Incluir Solo Modelos Específicos
```bash
# Solo User y modelos relacionados
docker exec sgm-django-1 python manage.py graph_models api.User contabilidad.Empresa -o diagrams/user_empresa.png
```

### Diferentes Formatos de Salida
```bash
# PDF
docker exec sgm-django-1 python manage.py graph_models -a -g -o diagrams/models.pdf

# SVG
docker exec sgm-django-1 python manage.py graph_models -a -g -o diagrams/models.svg

# DOT (texto)
docker exec sgm-django-1 python manage.py graph_models -a -g --output-format=dot -o diagrams/models.dot
```

## 📋 Script de Generación Automática

Para generar múltiples diagramas de una vez, usa el script incluido:

```bash
# Copiar script al contenedor (si no está)
docker cp generate_diagrams.py sgm-django-1:/app/

# Ejecutar script
docker exec sgm-django-1 python3 /app/generate_diagrams.py

# Copiar diagramas al host
docker cp sgm-django-1:/app/diagrams ./
```

## 🗂️ Archivos Generados

- `all_models.png`: Diagrama completo con todos los modelos
- `contabilidad_models.png`: Solo modelos de contabilidad
- `nomina_models.png`: Solo modelos de nómina
- `api_models.png`: Solo modelos de API
- `clean_models.png`: Diagrama limpio sin etiquetas
- `colored_models.png`: Diagrama con códigos de color
- `models.svg`: Diagrama vectorial escalable
- `models.dot`: Archivo DOT para personalización

## 💡 Consejos Útiles

1. **Para proyectos grandes**: Usa `-g` para agrupar por aplicación
2. **Para diagramas limpios**: Usa `--hide-edge-labels`
3. **Para personalizar**: Genera archivo DOT y edítalo manualmente
4. **Para presentaciones**: Usa formato SVG para mejor calidad
5. **Para documentación**: PDF es ideal para documentos estáticos

## 🔧 Troubleshooting

Si encuentras errores:

1. **Error de django-extensions**:
   ```bash
   docker exec sgm-django-1 pip install django-extensions
   ```

2. **Error de GraphViz**:
   ```bash
   docker exec sgm-django-1 apt-get update && apt-get install -y graphviz
   ```

3. **Error de permisos**:
   ```bash
   docker exec sgm-django-1 mkdir -p /app/diagrams
   docker exec sgm-django-1 chmod 755 /app/diagrams
   ```
