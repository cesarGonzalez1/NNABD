"""
Data migration: siembra el catalogo de Derechos del Art. 13 LGDNNA
(enunciativo, no limitativo) y un conjunto base de instituciones ejecutoras.
"""
from django.db import migrations


DERECHOS = [
    ("I",     "Derecho a la vida, a la paz, a la supervivencia y al desarrollo", "LGDNNA arts. 14-16"),
    ("II",    "Derecho de prioridad", "LGDNNA art. 17"),
    ("III",   "Derecho a la identidad", "LGDNNA arts. 19-21"),
    ("IV",    "Derecho a vivir en familia", "LGDNNA arts. 22-30"),
    ("V",     "Derecho a la igualdad sustantiva", "LGDNNA arts. 36-37"),
    ("VI",    "Derecho a no ser discriminado", "LGDNNA arts. 39-42"),
    ("VII",   "Derecho a vivir en condiciones de bienestar y a un sano desarrollo integral", "LGDNNA arts. 43-45"),
    ("VIII",  "Derecho a una vida libre de violencia y a la integridad personal", "LGDNNA arts. 46-49"),
    ("IX",    "Derecho a la proteccion de la salud y a la seguridad social", "LGDNNA arts. 50-53"),
    ("X",     "Derecho a la inclusion de NNA con discapacidad", "LGDNNA arts. 54-56"),
    ("XI",    "Derecho a la educacion", "LGDNNA arts. 57-59"),
    ("XII",   "Derecho al descanso y al esparcimiento", "LGDNNA arts. 60-61"),
    ("XIII",  "Derecho a la libertad de convicciones eticas, pensamiento, conciencia, religion y cultura", "LGDNNA arts. 62-64"),
    ("XIV",   "Derecho a la libertad de expresion y de acceso a la informacion", "LGDNNA arts. 65-68"),
    ("XV",    "Derecho de participacion", "LGDNNA arts. 71-74"),
    ("XVI",   "Derecho de asociacion y reunion", "LGDNNA art. 75"),
    ("XVII",  "Derecho a la intimidad", "LGDNNA arts. 76-80"),
    ("XVIII", "Derecho a la seguridad juridica y al debido proceso", "LGDNNA arts. 82-87"),
    ("XIX",   "Derechos de NNA migrantes", "LGDNNA arts. 89-101"),
    ("XX",    "Derecho de acceso a las Tecnologias de la Informacion y Comunicacion", "LGDNNA arts. 101 Bis"),
]

INSTITUCIONES = [
    ("Procuraduria Federal de Proteccion de NNA (SNDIF)", "procuraduria", "federal"),
    ("Sistema Nacional DIF", "dif", "federal"),
    ("Secretaria de Salud", "salud", "federal"),
    ("Secretaria de Educacion Publica", "educacion", "federal"),
    ("Fiscalia General de la Republica", "fiscalia", "federal"),
    ("Comision Nacional de los Derechos Humanos", "cdh", "federal"),
]


def cargar(apps, schema_editor):
    Derecho = apps.get_model("web", "Derecho")
    Institucion = apps.get_model("web", "InstitucionEjecutora")
    for clave, nombre, fundamento in DERECHOS:
        Derecho.objects.update_or_create(
            clave=clave, defaults={"nombre": nombre, "fundamento": fundamento})
    for nombre, tipo, nivel in INSTITUCIONES:
        Institucion.objects.get_or_create(
            nombre=nombre, nivel=nivel, defaults={"tipo": tipo})


def revertir(apps, schema_editor):
    Derecho = apps.get_model("web", "Derecho")
    Derecho.objects.filter(clave__in=[d[0] for d in DERECHOS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("web", "0006_derecho_bitacoraacceso_consentimientodatos_and_more"),
    ]
    operations = [migrations.RunPython(cargar, revertir)]
