# payroll/urls.py
from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [
    # Aquí puedes agregar tus URLs específicas para payroll
    # Ejemplo:
    # path("employees/", views.employee_list, name="employee_list"),
    # path("payslips/", views.payslip_list, name="payslip_list"),
]
