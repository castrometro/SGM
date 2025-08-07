"""
URL configuration for sgm_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#backend/sgm_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from api.views import CustomTokenObtainPairView

# Importar admin personalizado de nóminas
try:
    from payroll.payroll_admin_site import payroll_admin
    PAYROLL_ADMIN_AVAILABLE = True
except ImportError:
    PAYROLL_ADMIN_AVAILABLE = False

urlpatterns = [
    # Admin principal (superusuarios)
    path('admin/', admin.site.urls),
    
    # APIs
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('api.urls')),
    path('api/contabilidad/', include('contabilidad.urls')),
    path('api/payroll/', include('payroll.urls')),  # ← Nueva app payroll
    path('', include('task_manager.urls')),  # ← URLs del task manager global
]

# Agregar admin de nóminas si está disponible
if PAYROLL_ADMIN_AVAILABLE:
    urlpatterns.insert(1, path('admin-nominas/', payroll_admin.urls))

# Esto debe ir DESPUÉS de definir urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
