"""
Recarga idempotente de los catalogos del profesor (lenguas, familias,
discapacidades, etc.) por si la migracion 0011 se aplico con datos parciales,
y siembra el catalogo CIE-10 (capitulos + enfermedades comunes), que antes
solo tenia 4 registros de ejemplo.
"""
import importlib
from django.db import migrations


def recargar_catalogos_profesor(apps, schema_editor):
    # Reutiliza la funcion ya probada de 0011 con los CSV actuales (completos).
    mod = importlib.import_module("web.migrations.0011_seed_catalogos_profesor")
    mod.seed_catalogos_profesor(apps, schema_editor)


CAPITULOS = [
    ("I",    "Ciertas enfermedades infecciosas y parasitarias", "A00", "B99"),
    ("II",   "Neoplasias (tumores)", "C00", "D48"),
    ("III",  "Enfermedades de la sangre y de los organos hematopoyeticos", "D50", "D89"),
    ("IV",   "Enfermedades endocrinas, nutricionales y metabolicas", "E00", "E90"),
    ("V",    "Trastornos mentales y del comportamiento", "F00", "F99"),
    ("VI",   "Enfermedades del sistema nervioso", "G00", "G99"),
    ("VII",  "Enfermedades del ojo y sus anexos", "H00", "H59"),
    ("VIII", "Enfermedades del oido y de la apofisis mastoides", "H60", "H95"),
    ("IX",   "Enfermedades del sistema circulatorio", "I00", "I99"),
    ("X",    "Enfermedades del sistema respiratorio", "J00", "J99"),
    ("XI",   "Enfermedades del sistema digestivo", "K00", "K93"),
    ("XII",  "Enfermedades de la piel y del tejido subcutaneo", "L00", "L99"),
    ("XIII", "Enfermedades del sistema osteomuscular y del tejido conjuntivo", "M00", "M99"),
    ("XIV",  "Enfermedades del sistema genitourinario", "N00", "N99"),
    ("XV",   "Embarazo, parto y puerperio", "O00", "O99"),
    ("XVI",  "Ciertas afecciones originadas en el periodo perinatal", "P00", "P96"),
    ("XVII", "Malformaciones congenitas, deformidades y anomalias cromosomicas", "Q00", "Q99"),
    ("XVIII","Sintomas, signos y hallazgos anormales clinicos y de laboratorio", "R00", "R99"),
    ("XIX",  "Traumatismos, envenenamientos y otras consecuencias de causas externas", "S00", "T98"),
    ("XX",   "Causas externas de morbilidad y de mortalidad", "V01", "Y98"),
    ("XXI",  "Factores que influyen en el estado de salud y contacto con servicios de salud", "Z00", "Z99"),
    ("XXII", "Codigos para situaciones especiales", "U00", "U99"),
]

# (codigo_cie10, nombre, capitulo)
ENFERMEDADES = [
    ("A00","Colera","I"),("A06","Amebiasis","I"),("A09","Diarrea y gastroenteritis de presunto origen infeccioso","I"),
    ("A15","Tuberculosis respiratoria confirmada","I"),("A33","Tetanos neonatal","I"),("A37","Tos ferina","I"),
    ("A38","Escarlatina","I"),("A90","Dengue clasico","I"),("B01","Varicela","I"),("B05","Sarampion","I"),
    ("B06","Rubeola","I"),("B15","Hepatitis aguda tipo A","I"),("B26","Parotiditis (paperas)","I"),
    ("B34","Infeccion viral de sitio no especificado","I"),("B86","Escabiosis (sarna)","I"),("B82","Parasitosis intestinal","I"),
    ("C91","Leucemia linfoide","II"),("C71","Tumor maligno del encefalo","II"),("D18","Hemangioma y linfangioma","II"),
    ("D50","Anemia por deficiencia de hierro","III"),("D56","Talasemia","III"),("D57","Trastornos falciformes","III"),
    ("D69","Purpura y otras afecciones hemorragicas","III"),
    ("E03","Hipotiroidismo","IV"),("E10","Diabetes mellitus tipo 1","IV"),("E11","Diabetes mellitus tipo 2","IV"),
    ("E44","Desnutricion proteico-calorica moderada y leve","IV"),("E46","Desnutricion proteico-calorica no especificada","IV"),
    ("E66","Obesidad","IV"),("E86","Deshidratacion","IV"),("E89","Trastornos endocrinos posprocedimiento","IV"),
    ("F32","Episodio depresivo","V"),("F41","Otros trastornos de ansiedad","V"),("F43","Reaccion a estres grave y trastornos de adaptacion","V"),
    ("F70","Retraso mental leve","V"),("F71","Retraso mental moderado","V"),("F80","Trastornos del desarrollo del habla y del lenguaje","V"),
    ("F84","Trastornos generalizados del desarrollo (espectro autista)","V"),("F90","Trastorno por deficit de atencion e hiperactividad","V"),
    ("F91","Trastornos de la conducta","V"),("F94","Trastornos del comportamiento social en la infancia","V"),
    ("G40","Epilepsia","VI"),("G80","Paralisis cerebral infantil","VI"),("G43","Migrana","VI"),("G93","Otros trastornos del encefalo","VI"),
    ("H10","Conjuntivitis","VII"),("H52","Trastornos de la refraccion y de la acomodacion","VII"),("H54","Ceguera y disminucion de la agudeza visual","VII"),
    ("H65","Otitis media no supurativa","VIII"),("H66","Otitis media supurativa","VIII"),("H90","Hipoacusia conductiva y neurosensorial","VIII"),("H91","Otras hipoacusias","VIII"),
    ("I10","Hipertension esencial (primaria)","IX"),("I50","Insuficiencia cardiaca","IX"),
    ("J00","Rinofaringitis aguda (resfriado comun)","X"),("J02","Faringitis aguda","X"),("J03","Amigdalitis aguda","X"),
    ("J06","Infeccion aguda de las vias respiratorias superiores","X"),("J11","Influenza (gripe)","X"),
    ("J18","Neumonia, organismo no especificado","X"),("J20","Bronquitis aguda","X"),("J21","Bronquiolitis aguda","X"),
    ("J45","Asma","X"),("J46","Estado asmatico","X"),
    ("K02","Caries dental","XI"),("K21","Enfermedad por reflujo gastroesofagico","XI"),("K29","Gastritis y duodenitis","XI"),
    ("K30","Dispepsia funcional","XI"),("K52","Colitis y gastroenteritis no infecciosas","XI"),("K59","Estrenimiento","XI"),
    ("L01","Impetigo","XII"),("L20","Dermatitis atopica","XII"),("L23","Dermatitis alergica de contacto","XII"),
    ("L29","Prurito","XII"),("L50","Urticaria","XII"),
    ("M21","Otras deformidades adquiridas de los miembros","XIII"),("M41","Escoliosis","XIII"),("M79","Otros trastornos de los tejidos blandos","XIII"),
    ("N18","Enfermedad renal cronica","XIV"),("N39","Otros trastornos del sistema urinario (infeccion urinaria)","XIV"),("N47","Trastornos del prepucio","XIV"),
    ("P05","Retardo del crecimiento fetal y desnutricion fetal","XVI"),("P07","Trastornos por duracion corta de la gestacion y bajo peso al nacer","XVI"),
    ("P59","Ictericia neonatal","XVI"),
    ("Q21","Malformaciones congenitas de los tabiques cardiacos","XVII"),("Q35","Fisura del paladar","XVII"),
    ("Q37","Fisura del paladar con labio leporino","XVII"),("Q66","Deformidades congenitas de los pies","XVII"),
    ("Q90","Sindrome de Down","XVII"),("Q99","Otras anomalias de los cromosomas","XVII"),
    ("R05","Tos","XVIII"),("R10","Dolor abdominal y pelvico","XVIII"),("R50","Fiebre de origen desconocido","XVIII"),
    ("R51","Cefalea","XVIII"),("R56","Convulsiones, no clasificadas en otra parte","XVIII"),("R63","Sintomas relativos a la ingestion de alimentos","XVIII"),
    ("S00","Traumatismo superficial de la cabeza","XIX"),("S52","Fractura del antebrazo","XIX"),("T14","Traumatismo de region no especificada","XIX"),
    ("T74","Sindromes del maltrato","XIX"),("T78","Efectos adversos no clasificados (alergia)","XIX"),
    ("Z00","Examen general e investigacion de personas sin quejas","XXI"),("Z23","Necesidad de inmunizacion (vacunacion)","XXI"),
    ("Z63","Otros problemas relacionados con el grupo primario de apoyo","XXI"),("Z76","Personas en contacto con los servicios de salud","XXI"),
]


def seed_cie10(apps, schema_editor):
    Capitulo = apps.get_model("web", "CapituloEnfermedad")
    Enfermedad = apps.get_model("web", "Enfermedad")
    caps = {}
    for codigo, nombre, ini, fin in CAPITULOS:
        cap, _ = Capitulo.objects.update_or_create(
            codigo=codigo,
            defaults={"nombre": nombre, "rango_inicio": ini, "rango_fin": fin},
        )
        caps[codigo] = cap
    for codigo, nombre, cap_codigo in ENFERMEDADES:
        Enfermedad.objects.update_or_create(
            codigo_cie10=codigo,
            defaults={"nombre": nombre, "capitulo": caps.get(cap_codigo)},
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("web", "0011_seed_catalogos_profesor")]
    operations = [
        migrations.RunPython(recargar_catalogos_profesor, noop),
        migrations.RunPython(seed_cie10, noop),
    ]
