from django.apps import AppConfig


class PayrollConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payroll'
    verbose_name = 'Sistema de Nómina'
    
    def ready(self):
        # import payroll.signals  # Importar señales cuando las creemos
        pass
