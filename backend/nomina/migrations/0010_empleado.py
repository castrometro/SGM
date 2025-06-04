from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0009_alter_libroremuneracionesupload_estado'),
    ]

    operations = [
        migrations.CreateModel(
            name='Empleado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=12, unique=True)),
                ('nombres', models.CharField(max_length=120)),
                ('apellido_paterno', models.CharField(max_length=120)),
                ('apellido_materno', models.CharField(blank=True, max_length=120)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_ingreso', models.DateField(blank=True, null=True)),
            ],
        ),
    ]
