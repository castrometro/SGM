from django.http import Http404
from api.models import Cliente


def get_cliente_or_404(cliente_id):
    try:
        return Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        raise Http404("Cliente no encontrado")
