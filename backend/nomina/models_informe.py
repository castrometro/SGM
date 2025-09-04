# backend/nomina/models_informe.py

from django.db import models
from django.utils import timezone
from .models import CierreNomina
import json


class InformeNomina(models.Model):
    """
    📊 INFORME COMPREHENSIVO DE CIERRE DE NÓMINA (contenedor JSON)
    
    Mantiene un JSON con datos del cierre. La generación se realiza fuera de este modelo.
    """
    
    # Relación con el cierre
    cierre = models.OneToOneField(
        CierreNomina, 
        on_delete=models.CASCADE, 
        related_name='informe'
    )
    
    # Datos del cierre - estructura simple
    datos_cierre = models.JSONField(
        help_text="Datos consolidados del cierre de nómina"
    )
    
    # Metadatos
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    version_calculo = models.CharField(max_length=10, default="1.0")
    tiempo_calculo = models.DurationField(null=True, blank=True)
    
    class Meta:
        db_table = 'nomina_informe_cierre'
        verbose_name = 'Informe de Nómina'
        verbose_name_plural = 'Informes de Nómina'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Informe {self.cierre.cliente.nombre} - {self.cierre.periodo}"
    
    def enviar_a_redis(self, ttl_hours: int | None = None) -> dict:
        """
        🚀 Envía el informe completo a Redis DB 2
        
        Args:
            ttl_hours: Tiempo de vida en Redis en horas. None o <=0 = sin expiración
            
        Returns:
            dict: Resultado de la operación
        """
        from .cache_redis import get_cache_system_nomina
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Obtener sistema de cache
            cache_system = get_cache_system_nomina()
            
            # Preparar datos para Redis (simple, orientado a almacenar el JSON)
            datos_redis = {
                'informe_id': self.id,
                'cliente_id': self.cierre.cliente.id,
                'cliente_nombre': self.cierre.cliente.nombre,
                'periodo': self.cierre.periodo,
                'estado_cierre': self.cierre.estado,
                'fecha_generacion': self.fecha_generacion.isoformat(),
                'fecha_finalizacion': self.cierre.fecha_finalizacion.isoformat() if self.cierre.fecha_finalizacion else None,
                'usuario_finalizacion': self.cierre.usuario_finalizacion.correo_bdo if self.cierre.usuario_finalizacion else None,
                'version_calculo': self.version_calculo,
                'tiempo_calculo_segundos': self.tiempo_calculo.total_seconds() if self.tiempo_calculo else None,
                
                # Datos del cierre completos
                'datos_cierre': self.datos_cierre,
                
                # Dejado vacío adrede; el cliente puede leer KPIs directamente del JSON
                'kpis_principales': {}
            }
            
            # Convertir TTL a segundos
            ttl_seconds = None if (ttl_hours is None or ttl_hours <= 0) else ttl_hours * 3600
            
            # Enviar a Redis
            success = cache_system.set_informe_nomina(
                cliente_id=self.cierre.cliente.id,
                periodo=self.cierre.periodo,
                informe_data=datos_redis,
                ttl=ttl_seconds
            )
            
            if success:
                logger.info(f"✅ Informe enviado a Redis: {self.cierre.cliente.nombre} - {self.cierre.periodo}")
                return {
                    'success': True,
                    'mensaje': 'Informe enviado exitosamente a Redis',
                    'clave_redis': f"sgm:nomina:{self.cierre.cliente.id}:{self.cierre.periodo}:informe",
                    'ttl_hours': ttl_hours,
                    'size_kb': len(str(datos_redis)) / 1024
                }
            else:
                return {
                    'success': False,
                    'error': 'Error al enviar informe a Redis'
                }
                
        except Exception as e:
            logger.error(f"❌ Error enviando informe a Redis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def obtener_desde_redis(cls, cliente_id: int, periodo: str) -> dict:
        """
        📥 Obtiene un informe desde Redis
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            
        Returns:
            dict: Datos del informe o None si no existe
        """
        from .cache_redis import get_cache_system_nomina
        
        try:
            cache_system = get_cache_system_nomina()
            return cache_system.get_informe_nomina(cliente_id, periodo)
        except Exception as e:
            return None
