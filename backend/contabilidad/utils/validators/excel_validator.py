from contabilidad.views import limpiar_archivos_temporales_antiguos

def limpiar_archivos_temporales():
    """Wrapper used by Celery task to remove old temp files."""
    return limpiar_archivos_temporales_antiguos()
