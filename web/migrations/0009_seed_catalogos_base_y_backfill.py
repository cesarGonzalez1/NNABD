from django.db import migrations


def seed_catalogos(apps, schema_editor):
    Sexo = apps.get_model('web', 'Sexo')
    Nacionalidad = apps.get_model('web', 'Nacionalidad')
    TipoContacto = apps.get_model('web', 'TipoContacto')
    NivelCompetenciaOral = apps.get_model('web', 'NivelCompetenciaOral')
    ModoAdquisicionLengua = apps.get_model('web', 'ModoAdquisicionLengua')
    GradoDependencia = apps.get_model('web', 'GradoDependencia')
    TipoDiscapacidad = apps.get_model('web', 'TipoDiscapacidad')
    Discapacidad = apps.get_model('web', 'Discapacidad')
    FamiliaLinguistica = apps.get_model('web', 'FamiliaLinguistica')
    Lengua = apps.get_model('web', 'Lengua')
    CapituloEnfermedad = apps.get_model('web', 'CapituloEnfermedad')
    Enfermedad = apps.get_model('web', 'Enfermedad')

    for clave, nombre in [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro / No especificado')]:
        Sexo.objects.update_or_create(clave=clave, defaults={'nombre': nombre})

    for clave, nombre in [
        ('MEX', 'Mexicana'),
        ('USA', 'Estadounidense'),
        ('GTM', 'Guatemalteca'),
        ('HND', 'Hondurena'),
        ('SLV', 'Salvadorena'),
        ('OTR', 'Otra'),
    ]:
        Nacionalidad.objects.update_or_create(clave=clave, defaults={'nombre': nombre})

    for clave, nombre in [
        ('telefono', 'Telefono'),
        ('celular', 'Celular'),
        ('correo', 'Correo electronico'),
        ('emergencia', 'Contacto de emergencia'),
        ('notificacion', 'Medio de notificacion'),
    ]:
        TipoContacto.objects.update_or_create(clave=clave, defaults={'nombre': nombre})

    for clave, nombre, puede, interprete in [
        ('basico', 'Basico', False, True),
        ('intermedio', 'Intermedio', True, False),
        ('avanzado', 'Avanzado', True, False),
        ('nativo', 'Nativo / lengua materna', True, False),
    ]:
        NivelCompetenciaOral.objects.update_or_create(
            clave=clave,
            defaults={'nombre': nombre, 'puede_declarar': puede, 'requiere_interprete': interprete},
        )

    for clave, categoria in [
        ('materna', 'Lengua materna'),
        ('familiar', 'Adquirida en familia'),
        ('escolar', 'Adquirida en escuela'),
        ('comunitaria', 'Adquirida en comunidad'),
        ('segunda', 'Segunda lengua'),
    ]:
        ModoAdquisicionLengua.objects.update_or_create(clave=clave, defaults={'categoria': categoria})

    for clave, nombre in [
        ('leve', 'Leve'),
        ('moderada', 'Moderada'),
        ('severa', 'Severa'),
        ('total', 'Total'),
    ]:
        GradoDependencia.objects.update_or_create(clave=clave, defaults={'nombre': nombre})

    tipos = {}
    for nombre in ['Motriz', 'Visual', 'Auditiva', 'Habla/Lenguaje', 'Intelectual', 'Psicosocial/Mental', 'Multiple']:
        tipos[nombre], _ = TipoDiscapacidad.objects.update_or_create(nombre=nombre, defaults={})
    for tipo_nombre, discapacidad_nombre in [
        ('Motriz', 'Limitacion para caminar o moverse'),
        ('Visual', 'Baja vision o ceguera'),
        ('Auditiva', 'Hipoacusia o sordera'),
        ('Habla/Lenguaje', 'Limitacion del habla o lenguaje'),
        ('Intelectual', 'Discapacidad intelectual'),
        ('Psicosocial/Mental', 'Discapacidad psicosocial'),
        ('Multiple', 'Discapacidad multiple'),
    ]:
        Discapacidad.objects.update_or_create(
            tipo=tipos[tipo_nombre],
            nombre=discapacidad_nombre,
            defaults={},
        )

    espanol, _ = Lengua.objects.update_or_create(
        clave_inali='SPA',
        defaults={'nombre': 'Espanol', 'es_indigena': False, 'familia': None},
    )
    yuto, _ = FamiliaLinguistica.objects.update_or_create(nombre='Yuto-nahua')
    Lengua.objects.update_or_create(
        clave_inali='NAH',
        defaults={'nombre': 'Nahuatl', 'familia': yuto, 'es_indigena': True},
    )

    cap, _ = CapituloEnfermedad.objects.update_or_create(
        codigo='XVIII',
        defaults={'nombre': 'Sintomas, signos y hallazgos anormales', 'rango_inicio': 'R00', 'rango_fin': 'R99'},
    )
    for codigo, nombre in [
        ('R51', 'Cefalea'),
        ('I10', 'Hipertension esencial'),
        ('E11', 'Diabetes mellitus tipo 2'),
        ('F43', 'Reaccion a estres grave y trastornos de adaptacion'),
    ]:
        Enfermedad.objects.update_or_create(codigo_cie10=codigo, defaults={'nombre': nombre, 'capitulo': cap})


def backfill_relaciones(apps, schema_editor):
    Sexo = apps.get_model('web', 'Sexo')
    Nacionalidad = apps.get_model('web', 'Nacionalidad')
    NacionalidadNNA = apps.get_model('web', 'NacionalidadNNA')
    NNATutor = apps.get_model('web', 'NNATutor')
    Empleado = apps.get_model('web', 'Empleado')
    Tutor = apps.get_model('web', 'Tutor')
    NNA = apps.get_model('web', 'NNA')

    sexo_por_clave = {sexo.clave: sexo for sexo in Sexo.objects.all()}
    for Model in (Empleado, Tutor, NNA):
        for obj in Model.objects.filter(sexo_catalogo__isnull=True):
            sexo = sexo_por_clave.get(getattr(obj, 'sexo', None))
            if sexo:
                Model.objects.filter(pk=obj.pk).update(sexo_catalogo=sexo)

    mexicana = Nacionalidad.objects.filter(clave='MEX').first()
    otra = Nacionalidad.objects.filter(clave='OTR').first()
    for nna in NNA.objects.all():
        if not nna.folio_nna:
            NNA.objects.filter(pk=nna.pk).update(folio_nna=f"NNA-{nna.pk:06d}")
        if nna.tutor_id:
            try:
                tutor = Tutor.objects.get(pk=nna.tutor_id)
            except Tutor.DoesNotExist:
                tutor = None
            if tutor:
                NNATutor.objects.update_or_create(
                    nna=nna,
                    tutor=tutor,
                    defaults={
                        'parentesco': tutor.parentesco_con_nna,
                        'principal': True,
                        'fecha_inicio': nna.fecha_ingreso,
                    },
                )
        nacionalidad = otra if nna.es_extranjero else mexicana
        if nacionalidad:
            NacionalidadNNA.objects.get_or_create(
                nna=nna,
                nacionalidad=nacionalidad,
                defaults={'principal': True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ('web', '0008_contactonna_discapacidad_gradodependencia_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_catalogos, migrations.RunPython.noop),
        migrations.RunPython(backfill_relaciones, migrations.RunPython.noop),
    ]
