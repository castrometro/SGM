# ============================================================================
#                    IMPLEMENTACIÓN PRÁCTICA - MULTI ADMIN
# ============================================================================
"""
Setup script para implementar múltiples admin sites en SGM
Ejecutar: python manage.py shell < setup_multi_admin.py
"""

# Crear grupos de usuarios
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def setup_user_groups():
    """Crear grupos para diferentes áreas"""
    
    # Grupo para equipo de nóminas
    nominas_group, created = Group.objects.get_or_create(name='nominas')
    if created:
        print("✅ Grupo 'nominas' creado")
    
    # Grupo para equipo contable
    contabilidad_group, created = Group.objects.get_or_create(name='contabilidad') 
    if created:
        print("✅ Grupo 'contabilidad' creado")
        
    # Grupo para project managers
    task_managers_group, created = Group.objects.get_or_create(name='task_managers')
    if created:
        print("✅ Grupo 'task_managers' creado")
    
    return nominas_group, contabilidad_group, task_managers_group

def assign_permissions():
    """Asignar permisos específicos a cada grupo"""
    
    nominas_group = Group.objects.get(name='nominas')
    contabilidad_group = Group.objects.get(name='contabilidad')
    task_managers_group = Group.objects.get(name='task_managers')
    
    # Permisos para nóminas (modelos de payroll)
    try:
        from payroll.models import PayrollClosure, PayrollFileUpload, DiscrepancyResult
        
        payroll_ct = ContentType.objects.get_for_model(PayrollClosure)
        file_ct = ContentType.objects.get_for_model(PayrollFileUpload)
        disc_ct = ContentType.objects.get_for_model(DiscrepancyResult)
        
        payroll_perms = Permission.objects.filter(content_type__in=[payroll_ct, file_ct, disc_ct])
        nominas_group.permissions.set(payroll_perms)
        print(f"✅ Permisos de nóminas asignados: {payroll_perms.count()}")
        
    except Exception as e:
        print(f"❌ Error asignando permisos de nóminas: {e}")
    
    # Permisos para contabilidad
    try:
        from contabilidad.models import RegistroContable
        
        contable_ct = ContentType.objects.get_for_model(RegistroContable)
        contable_perms = Permission.objects.filter(content_type=contable_ct)
        contabilidad_group.permissions.set(contable_perms)
        print(f"✅ Permisos de contabilidad asignados: {contable_perms.count()}")
        
    except Exception as e:
        print(f"❌ Error asignando permisos de contabilidad: {e}")
    
    # Permisos para task managers
    try:
        from task_manager.models import Task, TaskNotification
        
        task_ct = ContentType.objects.get_for_model(Task)
        notif_ct = ContentType.objects.get_for_model(TaskNotification)
        
        task_perms = Permission.objects.filter(content_type__in=[task_ct, notif_ct])
        task_managers_group.permissions.set(task_perms)
        print(f"✅ Permisos de task manager asignados: {task_perms.count()}")
        
    except Exception as e:
        print(f"❌ Error asignando permisos de task manager: {e}")

def create_test_users():
    """Crear usuarios de prueba para cada grupo"""
    
    from api.models import Usuario
    
    # Usuario para nóminas
    nominas_user, created = Usuario.objects.get_or_create(
        username='admin_nominas',
        defaults={
            'email': 'nominas@sgm.com',
            'first_name': 'Admin',
            'last_name': 'Nóminas',
            'is_staff': True,
            'is_active': True,
        }
    )
    if created:
        nominas_user.set_password('admin123')
        nominas_user.save()
        nominas_group = Group.objects.get(name='nominas')
        nominas_user.groups.add(nominas_group)
        print("✅ Usuario admin_nominas creado")
    
    # Usuario para contabilidad
    contable_user, created = Usuario.objects.get_or_create(
        username='admin_contabilidad',
        defaults={
            'email': 'contabilidad@sgm.com',
            'first_name': 'Admin', 
            'last_name': 'Contabilidad',
            'is_staff': True,
            'is_active': True,
        }
    )
    if created:
        contable_user.set_password('admin123')
        contable_user.save()
        contabilidad_group = Group.objects.get(name='contabilidad')
        contable_user.groups.add(contabilidad_group)
        print("✅ Usuario admin_contabilidad creado")
    
    # Usuario para task manager
    task_user, created = Usuario.objects.get_or_create(
        username='admin_tareas',
        defaults={
            'email': 'tareas@sgm.com',
            'first_name': 'Admin',
            'last_name': 'Tareas', 
            'is_staff': True,
            'is_active': True,
        }
    )
    if created:
        task_user.set_password('admin123')
        task_user.save()
        task_group = Group.objects.get(name='task_managers')
        task_user.groups.add(task_group)
        print("✅ Usuario admin_tareas creado")

def main():
    print("🚀 CONFIGURANDO SISTEMA MULTI-ADMIN")
    print("=====================================")
    
    # Paso 1: Crear grupos
    setup_user_groups()
    
    # Paso 2: Asignar permisos
    assign_permissions()
    
    # Paso 3: Crear usuarios de prueba
    create_test_users()
    
    print()
    print("🎉 CONFIGURACIÓN COMPLETADA!")
    print("=============================")
    print("Usuarios creados:")
    print("• admin_nominas / admin123 (acceso a nóminas)")
    print("• admin_contabilidad / admin123 (acceso a contabilidad)")
    print("• admin_tareas / admin123 (acceso a tareas)")
    print()
    print("URLs disponibles:")
    print("• /admin/ (superusuarios)")
    print("• /admin-nominas/ (equipo RRHH)")
    print("• /admin-contabilidad/ (equipo Finanzas)")
    print("• /admin-tareas/ (Project Managers)")

if __name__ == "__main__":
    main()
