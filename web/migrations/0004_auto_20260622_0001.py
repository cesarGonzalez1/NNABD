from django.db import migrations

def crear_roles_equipo(apps, schema_editor):
    RolEquipo = apps.get_model('web', 'RolEquipo')

    roles = [
        ('ABOGADO', 'Abogado'),
        ('DOCTOR', 'Doctor'),
        ('TRABAJADOR_SOCIAL', 'Trabajador Social'),
        ('PSICOLOGO', 'Psicólogo'),
        ('COORDINADOR', 'Coordinador'),
    ]

    for clave, nombre in roles:
        RolEquipo.objects.get_or_create(
            clave=clave,
            defaults={'nombre': nombre}
        )

class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_alter_tipodiscapacidad_clave_inegi'),
    ]

    operations = [
        migrations.RunPython(crear_roles_equipo),
    ]