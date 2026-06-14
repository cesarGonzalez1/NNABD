import csv
from pathlib import Path

from django.db import migrations
from django.db.models.deletion import ProtectedError


CATALOG_DIR = Path(__file__).resolve().parents[2] / "data" / "catalogos"


def read_csv(filename):
    with (CATALOG_DIR / filename).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def delete_unreferenced(queryset):
    for obj in list(queryset):
        try:
            obj.delete()
        except ProtectedError:
            pass


def delete_by_catalog_id(model, keep):
    for obj in model.objects.all():
        if obj.catalogo_id not in keep:
            try:
                obj.delete()
            except ProtectedError:
                pass


def seed_catalogos_profesor(apps, schema_editor):
    TipoContacto = apps.get_model("web", "TipoContacto")
    NivelCompetenciaOral = apps.get_model("web", "NivelCompetenciaOral")
    ModoAdquisicionLengua = apps.get_model("web", "ModoAdquisicionLengua")
    TipoDiscapacidad = apps.get_model("web", "TipoDiscapacidad")
    Discapacidad = apps.get_model("web", "Discapacidad")
    FamiliaLinguistica = apps.get_model("web", "FamiliaLinguistica")
    Lengua = apps.get_model("web", "Lengua")

    keep_modos = set()
    for row in read_csv("modos_adquisicion_lengua.csv"):
        keep_modos.add(row["id"])
        ModoAdquisicionLengua.objects.update_or_create(
            clave=row["id"],
            defaults={
                "categoria": row["categoria"],
                "descripcion": row["como_se_adquiere"],
                "contexto": row["contexto_tipico"],
            },
        )
    delete_unreferenced(ModoAdquisicionLengua.objects.exclude(clave__in=keep_modos))

    keep_contactos = set()
    for row in read_csv("tipos_contacto.csv"):
        keep_contactos.add(row["id"])
        contacto = (
            TipoContacto.objects.filter(clave=row["id"]).first()
            or TipoContacto.objects.filter(nombre__iexact=row["nombre"]).first()
        )
        if contacto:
            contacto.clave = row["id"]
            contacto.nombre = row["nombre"]
            contacto.descripcion = row["descripcion"]
            contacto.save()
        else:
            TipoContacto.objects.create(
                clave=row["id"], nombre=row["nombre"], descripcion=row["descripcion"]
            )
    delete_unreferenced(TipoContacto.objects.exclude(clave__in=keep_contactos))

    keep_niveles = set()
    for row in read_csv("niveles_competencia_oral.csv"):
        keep_niveles.add(row["id"])
        sin_interprete = "sin necesidad" in row["sin_necesidad_interprete"].lower()
        nivel = (
            NivelCompetenciaOral.objects.filter(clave=row["id"]).first()
            or NivelCompetenciaOral.objects.filter(nombre__iexact=row["nivel_practico"]).first()
        )
        defaults = {
            "clave": row["id"],
            "nombre": row["nivel_practico"],
            "significado": row["significado"],
            "puede_declarar": sin_interprete,
            "requiere_interprete": not sin_interprete,
        }
        if nivel:
            for field, value in defaults.items():
                setattr(nivel, field, value)
            nivel.save()
        else:
            NivelCompetenciaOral.objects.create(
                clave=row["id"],
                nombre=row["nivel_practico"],
                significado=row["significado"],
                puede_declarar=sin_interprete,
                requiere_interprete=not sin_interprete,
            )
    delete_unreferenced(NivelCompetenciaOral.objects.exclude(clave__in=keep_niveles))

    keep_tipos_dis = set()
    for row in read_csv("tipos_discapacidad.csv"):
        keep_tipos_dis.add(row["id"])
        tipo = (
            TipoDiscapacidad.objects.filter(clave_inegi=row["id"]).first()
            or TipoDiscapacidad.objects.filter(nombre__iexact=row["nombre"]).first()
        )
        if tipo:
            tipo.clave_inegi = row["id"]
            tipo.nombre = row["nombre"]
            tipo.descripcion = row["descripcion"]
            tipo.save()
        else:
            tipo = TipoDiscapacidad.objects.create(
                clave_inegi=row["id"], nombre=row["nombre"], descripcion=row["descripcion"]
            )
        Discapacidad.objects.update_or_create(
            tipo=tipo,
            nombre=row["nombre"],
            defaults={"descripcion": row["descripcion"]},
        )
    delete_unreferenced(Discapacidad.objects.exclude(tipo__clave_inegi__in=keep_tipos_dis))
    delete_unreferenced(TipoDiscapacidad.objects.exclude(clave_inegi__in=keep_tipos_dis))

    keep_familias = set()
    for row in read_csv("familias_linguisticas.csv"):
        catalog_id = int(row["id"])
        keep_familias.add(catalog_id)
        nombre = row["familia_linguistica"]
        familia = (
            FamiliaLinguistica.objects.filter(catalogo_id=catalog_id).first()
            or FamiliaLinguistica.objects.filter(nombre__iexact=nombre).first()
        )
        if familia:
            familia.catalogo_id = catalog_id
            familia.nombre = nombre
            familia.save()
        else:
            FamiliaLinguistica.objects.create(catalogo_id=catalog_id, nombre=nombre)

    familias = {
        familia.nombre: familia
        for familia in FamiliaLinguistica.objects.exclude(catalogo_id__isnull=True)
    }
    keep_lenguas = set()
    for row in read_csv("lenguas.csv"):
        catalog_id = int(row["id"])
        keep_lenguas.add(catalog_id)
        familia = familias.get(row["familia_linguistica"])
        clave = f"PROF-{catalog_id:03d}"
        nombre = row["agrupacion_linguistica"]
        lengua = (
            Lengua.objects.filter(catalogo_id=catalog_id).first()
            or Lengua.objects.filter(clave_inali=clave).first()
        )
        defaults = {
            "catalogo_id": catalog_id,
            "familia": familia,
            "nombre": nombre,
            "clave_inali": clave,
            "es_indigena": True,
            "agrupacion_linguistica": nombre,
            "variante_linguistica": row["variante_linguistica"],
            "autodenominacion": row["autodenominacion"],
            "estado_region": row["estado_region"],
        }
        if lengua:
            for field, value in defaults.items():
                setattr(lengua, field, value)
            lengua.save()
        else:
            Lengua.objects.create(**defaults)

    delete_by_catalog_id(Lengua, keep_lenguas)
    delete_by_catalog_id(FamiliaLinguistica, keep_familias)


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0010_alter_lengua_options_familialinguistica_catalogo_id_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_catalogos_profesor, migrations.RunPython.noop),
    ]
