# Generated manually to add FK cuenta to Incidencia and backfill from cuenta_codigo
from django.db import migrations, models


def backfill_incidencia_cuenta(apps, schema_editor):
    Incidencia = apps.get_model('contabilidad', 'Incidencia')
    CuentaContable = apps.get_model('contabilidad', 'CuentaContable')
    CierreContabilidad = apps.get_model('contabilidad', 'CierreContabilidad')

    # Recorremos incidencias sin FK y con codigo presente
    qs = Incidencia.objects.filter(cuenta__isnull=True).exclude(cuenta_codigo__isnull=True).exclude(cuenta_codigo='')
    # Optimización: obtener mapa cierre->cliente para resolver cliente de la cuenta
    cierres = {}
    for inc in qs.iterator():
        cierre_id = inc.cierre_id
        cliente_id = cierres.get(cierre_id)
        if cliente_id is None:
            cliente_id = CierreContabilidad.objects.only('cliente_id').get(id=cierre_id).cliente_id
            cierres[cierre_id] = cliente_id
        try:
            cuenta = CuentaContable.objects.only('id').get(cliente_id=cliente_id, codigo=inc.cuenta_codigo)
        except CuentaContable.DoesNotExist:
            cuenta = None
        if cuenta:
            inc.cuenta_id = cuenta.id
            inc.save(update_fields=['cuenta'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0053_alter_nombreingles_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidencia',
            name='cuenta',
            field=models.ForeignKey(blank=True, help_text='Referencia directa a la cuenta contable', null=True, on_delete=models.deletion.SET_NULL, to='contabilidad.cuentacontable'),
        ),
        migrations.RunPython(backfill_incidencia_cuenta, noop_reverse),
        migrations.AlterModelOptions(
            name='incidencia',
            options={'ordering': ['tipo', 'cuenta_codigo', 'tipo_doc_codigo', 'fecha_creacion']},
        ),
        migrations.AddIndex(
            model_name='incidencia',
            index=models.Index(fields=['cuenta'], name='incid_cuenta_idx'),
        ),
    ]
