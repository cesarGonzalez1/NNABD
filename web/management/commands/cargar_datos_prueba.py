"""
Comando de gestión: cargar_datos_prueba
Pobla la BD con datos realistas para pruebas locales:
  - 23 empleados (1 director, 2 coordinadores, 5 TS, 5 psicólogos, 5 abogados, 5 doctores)
  - 5 equipos multidisciplinarios
  - 10 tutores
  - 10 NNA (2 por equipo)
  - Registros de idioma para 4 NNA de comunidades indígenas

Contraseña de todos los usuarios de prueba: prueba1234
Es idempotente: puede ejecutarse varias veces sin duplicar registros.

Uso:
    python manage.py cargar_datos_prueba
    python manage.py cargar_datos_prueba --limpiar   # borra todo primero
"""

from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from web.models import (
    Empleado, EquipoMultidisciplinario, IdiomaNNA, Lengua,
    ModoAdquisicionLengua, NNA, NNAEquipo, NNATutor,
    NivelCompetenciaOral, Sexo, Tutor,
)

PASSWORD = 'prueba1234'

# ── Catálogos (se resuelven en handle para que Django esté listo) ─────────────

def _sexo(nombre_inicio):
    return Sexo.objects.filter(nombre__istartswith=nombre_inicio).first()

def _nivel(nombre_inicio):
    return NivelCompetenciaOral.objects.filter(nombre__istartswith=nombre_inicio).first()

def _modo(categoria_inicio):
    return ModoAdquisicionLengua.objects.filter(categoria__istartswith=categoria_inicio).first()

def _lengua(nombre):
    return Lengua.objects.filter(nombre__iexact=nombre).first()

# ── Datos ─────────────────────────────────────────────────────────────────────

EMPLEADOS = [
    # (nombre, ap_pat, ap_mat, rol, rfc, curp, fecha_nac, sexo_inicial)
    # 0 director
    ('Ana Maria', 'Gonzalez', 'Ruiz', 'director',
     'GORA750105AA1', 'GORA750105MDFRNN08', date(1975, 1, 5), 'F'),
    # 1,2 coordinadores
    ('Carlos Alberto', 'Mendoza', 'Perez', 'coordinador',
     'MEPC850312BB2', 'MEPC850312HDFNZR07', date(1985, 3, 12), 'M'),
    ('Laura Elena', 'Sanchez', 'Torres', 'coordinador',
     'SATL910124CC3', 'SATL910124MDFNCR04', date(1991, 1, 24), 'F'),
    # 3-7 trabajadores sociales (uno por equipo)
    ('Maria Isabel', 'Ramirez', 'Flores', 'trabajador_social',
     'RAFI870418DD4', 'RAFI870418MDFMZR09', date(1987, 4, 18), 'F'),
    ('Jose Antonio', 'Morales', 'Jimenez', 'trabajador_social',
     'MOJJ920612EE5', 'MOJJ920612HDFRMZ06', date(1992, 6, 12), 'M'),
    ('Patricia', 'Hernandez', 'Luna', 'trabajador_social',
     'HELP880321FF6', 'HELP880321MDFRNZ02', date(1988, 3, 21), 'F'),
    ('Roberto', 'Cruz', 'Vargas', 'trabajador_social',
     'CUVR950730GG7', 'CUVR950730HDFRZB03', date(1995, 7, 30), 'M'),
    ('Adriana', 'Lopez', 'Reyes', 'trabajador_social',
     'LORA810116HH8', 'LORA810116MDFPZR05', date(1981, 1, 16), 'F'),
    # 8-12 psicólogos
    ('Diana', 'Martinez', 'Castro', 'psicologo',
     'MACD881024II9', 'MACD881024MDFRZN01', date(1988, 10, 24), 'F'),
    ('Eduardo', 'Garcia', 'Nieto', 'psicologo',
     'GANE930419JJ0', 'GANE930419HDFRZR08', date(1993, 4, 19), 'M'),
    ('Sandra', 'Perez', 'Guzman', 'psicologo',
     'PEGS860813KK1', 'PEGS860813MDFRZM07', date(1986, 8, 13), 'F'),
    ('Miguel Angel', 'Torres', 'Ramos', 'psicologo',
     'TORM900927LL2', 'TORM900927HDFRMG04', date(1990, 9, 27), 'M'),
    ('Claudia', 'Vega', 'Salinas', 'psicologo',
     'VESC851121MM3', 'VESC851121MDFGLZ09', date(1985, 11, 21), 'F'),
    # 13-17 abogados
    ('Fernando', 'Rios', 'Castillo', 'abogado',
     'RICF790318NN4', 'RICF790318HDFSSL06', date(1979, 3, 18), 'M'),
    ('Gabriela', 'Ortiz', 'Moreno', 'abogado',
     'OMGB820513OO5', 'OMGB820513MDFRZZ03', date(1982, 5, 13), 'F'),
    ('Hector', 'Navarro', 'Espinoza', 'abogado',
     'NAEH940620PP6', 'NAEH940620HDFVZR01', date(1994, 6, 20), 'M'),
    ('Veronica', 'Gutierrez', 'Alvarado', 'abogado',
     'GUAV861223QQ7', 'GUAV861223MDFTZR05', date(1986, 12, 23), 'F'),
    ('Alejandro', 'Ruiz', 'Dominguez', 'abogado',
     'RUDA780715RR8', 'RUDA780715HDFZMG02', date(1978, 7, 15), 'M'),
    # 18-22 doctores
    ('Beatriz', 'Fuentes', 'Medina', 'doctor',
     'FUMB800717SS9', 'FUMB800717MDFNZR08', date(1980, 7, 17), 'F'),
    ('Cesar', 'Maldonado', 'Bravo', 'doctor',
     'MABC860924TT0', 'MABC860924HDFLLZ04', date(1986, 9, 24), 'M'),
    ('Ingrid', 'Suarez', 'Quiroga', 'doctor',
     'SUQI831113UU1', 'SUQI831113MDFRZG07', date(1983, 11, 13), 'F'),
    ('Jaime', 'Acosta', 'Villalobos', 'doctor',
     'AVIJ790518VV2', 'AVIJ790518HDFSSL03', date(1979, 5, 18), 'M'),
    ('Karina', 'Espinoza', 'Serrano', 'doctor',
     'ESSK900724WW3', 'ESSK900724MDFPZZ06', date(1990, 7, 24), 'F'),
]

# (nombre, coord_idx, ts_idx, psic_idx, ab_idx, doc_idx)
EQUIPOS = [
    ('Equipo Esperanza',     1, 3,  8, 13, 18),
    ('Equipo Fortaleza',     1, 4,  9, 14, 19),
    ('Equipo Dignidad',      2, 5, 10, 15, 20),
    ('Equipo Renacimiento',  2, 6, 11, 16, 21),
    ('Equipo Amparo',        2, 7, 12, 17, 22),
]

# (nombre, ap_pat, ap_mat, curp, fecha_nac, sexo_ini, parentesco, telefono, escolaridad)
TUTORES = [
    ('Veronica', 'Alvarado', 'Rosales',
     'ALRV820315MDFLDS09', date(1982, 3, 15), 'F', 'tia', '5512345601', 'secundaria'),
    ('Francisco', 'Perez', 'Contreras',
     'PECF780522HDFRRC04', date(1978, 5, 22), 'M', 'tio', '5512345602', 'preparatoria'),
    ('Rosa Elena', 'Jimenez', 'Vega',
     'JIVR850910MDFMGG06', date(1985, 9, 10), 'F', 'abuela', '5512345603', 'primaria'),
    ('Arturo', 'Morales', 'Mendoza',
     'MOMA580412HDFRRZ07', date(1958, 4, 12), 'M', 'abuelo', '5512345604', 'primaria'),
    ('Leticia', 'Cruz', 'Soto',
     'CUSL790708MDFRZR02', date(1979, 7, 8), 'F', 'madrina', '5512345605', 'secundaria'),
    ('Jorge', 'Ramirez', 'Castillo',
     'RACJ831120HDFRMS05', date(1983, 11, 20), 'M', 'padrino', '5512345606', 'preparatoria'),
    ('Carmen', 'Flores', 'Garcia',
     'FOGC760214MDFRLR08', date(1976, 2, 14), 'F', 'tia', '5512345607', 'secundaria'),
    ('Rafael', 'Torres', 'Luna',
     'TOLR840619HDFRRS01', date(1984, 6, 19), 'M', 'tio', '5512345608', 'preparatoria'),
    ('Marcela', 'Hernandez', 'Ruiz',
     'HERM870325MDFRZR09', date(1987, 3, 25), 'F', 'abuela', '5512345609', 'secundaria'),
    ('Dulce Maria', 'Reyes', 'Zamora',
     'REZD910804MDFYMM03', date(1991, 8, 4), 'F', 'tia', '5512345610', 'preparatoria'),
]

# (nombre, ap_pat, ap_mat, curp, fecha_nac, sexo_ini, equipo_idx, tutor_idx, ts_idx,
#  escolaridad, condicion, comunidad_indigena, requiere_interprete, situacion_calle, fecha_ingreso)
NNA_DATA = [
    # Equipo Esperanza (idx 0) — TS: RAFI (idx 3)
    ('Miguel Angel', 'Alvarado', 'Reyes',
     'AHRM161204HDFLDS05', date(2016, 12, 4), 'M',
     0, 0, 3,
     'primaria', 'ninguna', '', False, False,
     date(2024, 3, 10)),
    ('Sofia', 'Perez', 'Diaz',
     'PEDS130817MDFRRZ07', date(2013, 8, 17), 'F',
     0, 1, 3,
     'primaria', 'ninguna', '', False, False,
     date(2024, 5, 22)),
    # Equipo Fortaleza (idx 1) — TS: MOJJ (idx 4)
    ('Carlos Eduardo', 'Jimenez', 'Morales',
     'JIMC141205HDFMRZ09', date(2014, 12, 5), 'M',
     1, 2, 4,
     'primaria', 'migrante', 'Comunidad Nahua de Veracruz', True, False,
     date(2024, 2, 14)),
    ('Valentina', 'Morales', 'Cruz',
     'MOCV150330MDFRLZ02', date(2015, 3, 30), 'F',
     1, 3, 4,
     'preescolar', 'ninguna', '', False, False,
     date(2024, 7, 8)),
    # Equipo Dignidad (idx 2) — TS: HELP (idx 5)
    ('Sebastian', 'Cruz', 'Garcia',
     'CUGS170914HDFRZZ06', date(2017, 9, 14), 'M',
     2, 4, 5,
     'preescolar', 'ninguna', '', False, True,
     date(2024, 1, 30)),
    ('Isabella', 'Ramirez', 'Torres',
     'RATI100623MDFRMZ08', date(2010, 6, 23), 'F',
     2, 5, 5,
     'secundaria', 'refugiado', '', False, False,
     date(2023, 11, 15)),
    # Equipo Renacimiento (idx 3) — TS: CUVR (idx 6)
    ('Diego', 'Flores', 'Hernandez',
     'FLHD130712HDFRLZ01', date(2013, 7, 12), 'M',
     3, 6, 6,
     'primaria', 'ninguna', '', False, False,
     date(2024, 4, 3)),
    ('Camila', 'Torres', 'Reyes',
     'TORC180108MDFRRM04', date(2018, 1, 8), 'F',
     3, 7, 6,
     'preescolar', 'ninguna', '', False, False,
     date(2024, 8, 19)),
    # Equipo Amparo (idx 4) — TS: LORA (idx 7)
    ('Andres', 'Hernandez', 'Lopez',
     'HELA110320HDFRZZ07', date(2011, 3, 20), 'M',
     4, 8, 7,
     'secundaria', 'ninguna', '', False, False,
     date(2024, 6, 5)),
    ('Renata', 'Reyes', 'Salinas',
     'RESR160614MDFYML05', date(2016, 6, 14), 'F',
     4, 9, 7,
     'primaria', 'ninguna', 'Comunidad Amuzga de Guerrero', True, False,
     date(2024, 9, 12)),
]

# Idiomas para NNA que pertenecen a comunidades indígenas
# (curp_nna, nombre_lengua, es_materna, nivel_inicio)
IDIOMAS_NNA = [
    ('JIMC141205HDFMRZ09', 'Cora',    True,  'Avanzado'),     # Carlos Eduardo
    ('JIMC141205HDFMRZ09', 'Chatino', False, 'Basico'),        # también algo de chatino
    ('RESR160614MDFYML05', 'Amuzgo',  True,  'Avanzado'),     # Renata
]


class Command(BaseCommand):
    help = 'Carga datos de prueba: 5 equipos, 10 NNA, tutores y empleados.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina todos los datos de prueba antes de cargar.',
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            self._limpiar()

        with transaction.atomic():
            sexo_m = _sexo('Mascul')
            sexo_f = _sexo('Femen')
            nivel_avanzado = _nivel('Avanzado')
            nivel_basico   = _nivel('Basico') or _nivel('Básico')
            modo_materna   = _modo('Lengua materna')

            emps = self._crear_empleados(sexo_m, sexo_f)
            equipos = self._crear_equipos(emps)
            tutores = self._crear_tutores(sexo_m, sexo_f)
            self._crear_nna(emps, equipos, tutores, sexo_m, sexo_f,
                            nivel_avanzado, nivel_basico, modo_materna)

        self.stdout.write(self.style.SUCCESS(
            '\n[OK] Datos de prueba cargados exitosamente.'
            '\n  Contrasena de todos los usuarios: prueba1234'
            '\n  Usuario director: GORA750105AA1'
        ))

    # ── Limpieza ──────────────────────────────────────────────────────────────

    def _limpiar(self):
        self.stdout.write('Eliminando datos de prueba anteriores...')
        rfcs       = [e[4] for e in EMPLEADOS]
        curps_tutor = [t[3] for t in TUTORES]
        curps_nna   = [n[3] for n in NNA_DATA]
        nombres_eq  = [e[0] for e in EQUIPOS]

        # Los constraints FK en la BD son NO ACTION: se eliminan en orden correcto
        # via SQL directo para evitar que Django intente re-recoger references dentro
        # de su transaction.atomic() y choque con la verificación a nivel statement.
        with connection.cursor() as cur:
            ph_nna   = ','.join(['%s'] * len(curps_nna))
            ph_tutor = ','.join(['%s'] * len(curps_tutor))
            ph_rfcs  = ','.join(['%s'] * len(rfcs))
            ph_eq    = ','.join(['%s'] * len(nombres_eq))

            cur.execute(
                f"UPDATE web_bitacoraacceso SET nna_id=NULL "
                f"WHERE nna_id IN (SELECT id FROM web_nna WHERE curp IN ({ph_nna}))",
                curps_nna,
            )
            for tabla in (
                'web_nnatutor', 'web_nnaequipo', 'web_idiomanna',
                'web_discapacidadnna', 'web_padecimientonna',
                'web_contactonna', 'web_nacionalidadnna',
                'web_hechovictimal', 'web_seguimientonna',
                'web_documentoexpediente', 'web_planrestitucion',
            ):
                cur.execute(
                    f"DELETE FROM {tabla} "
                    f"WHERE nna_id IN (SELECT id FROM web_nna WHERE curp IN ({ph_nna}))",
                    curps_nna,
                )
            cur.execute(f"DELETE FROM web_nna WHERE curp IN ({ph_nna})", curps_nna)
            cur.execute(f"DELETE FROM web_tutor WHERE curp IN ({ph_tutor})", curps_tutor)
            cur.execute(
                f"DELETE FROM web_equipomultidisciplinario WHERE nombre IN ({ph_eq})",
                nombres_eq,
            )
            cur.execute(
                f"DELETE FROM web_empleado WHERE rfc IN ({ph_rfcs})", rfcs
            )
            cur.execute(
                f"DELETE FROM auth_user WHERE username IN ({ph_rfcs})", rfcs
            )
        self.stdout.write('  Limpieza completada.')

    # ── Empleados ─────────────────────────────────────────────────────────────

    def _crear_empleados(self, sexo_m, sexo_f):
        emps = []
        creados = 0
        for (nombre, ap_pat, ap_mat, rol, rfc, curp, fnac, sx) in EMPLEADOS:
            if User.objects.filter(username=rfc).exists():
                emp = Empleado.objects.get(rfc=rfc)
                emps.append(emp)
                continue
            user = User.objects.create_user(username=rfc, password=PASSWORD)
            emp = Empleado.objects.create(
                usuario=user,
                nombre=nombre,
                apellido_paterno=ap_pat,
                apellido_materno=ap_mat,
                rol=rol,
                rfc=rfc,
                curp=curp,
                fecha_nacimiento=fnac,
                sexo_catalogo=sexo_f if sx == 'F' else sexo_m,
                tipo_trabajador='empleado',
            )
            emps.append(emp)
            creados += 1
        self.stdout.write(f'  Empleados: {creados} nuevos / {len(EMPLEADOS)} total')
        return emps

    # ── Equipos ───────────────────────────────────────────────────────────────

    def _crear_equipos(self, emps):
        equipos = []
        creados = 0
        for (nombre, coord_i, ts_i, psic_i, ab_i, doc_i) in EQUIPOS:
            eq, nuevo = EquipoMultidisciplinario.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'coordinador':      emps[coord_i],
                    'trabajador_social': emps[ts_i],
                    'psicologo':         emps[psic_i],
                    'abogado':           emps[ab_i],
                    'doctor':            emps[doc_i],
                },
            )
            equipos.append(eq)
            if nuevo:
                creados += 1
        self.stdout.write(f'  Equipos: {creados} nuevos / {len(EQUIPOS)} total')
        return equipos

    # ── Tutores ───────────────────────────────────────────────────────────────

    def _crear_tutores(self, sexo_m, sexo_f):
        tutores = []
        creados = 0
        for (nombre, ap_pat, ap_mat, curp, fnac, sx, parentesco, tel, esc) in TUTORES:
            tutor, nuevo = Tutor.objects.get_or_create(
                curp=curp,
                defaults={
                    'nombre': nombre,
                    'apellido_paterno': ap_pat,
                    'apellido_materno': ap_mat,
                    'sexo_catalogo': sexo_f if sx == 'F' else sexo_m,
                    'fecha_nacimiento': fnac,
                    'parentesco_con_nna': parentesco,
                    'telefono_principal': tel,
                    'escolaridad': esc,
                    'estado_civil': 'soltero',
                },
            )
            tutores.append(tutor)
            if nuevo:
                creados += 1
        self.stdout.write(f'  Tutores: {creados} nuevos / {len(TUTORES)} total')
        return tutores

    # ── NNA ───────────────────────────────────────────────────────────────────

    def _crear_nna(self, emps, equipos, tutores,
                   sexo_m, sexo_f, nivel_avanzado, nivel_basico, modo_materna):
        creados = 0
        for row in NNA_DATA:
            (nombre, ap_pat, ap_mat, curp, fnac, sx,
             eq_i, tutor_i, ts_i,
             escolaridad, condicion, comunidad, interprete, calle,
             fecha_ingreso) = row

            nna, nuevo = NNA.objects.get_or_create(
                curp=curp,
                defaults={
                    'nombre': nombre,
                    'apellido_paterno': ap_pat,
                    'apellido_materno': ap_mat,
                    'sexo_catalogo': sexo_f if sx == 'F' else sexo_m,
                    'fecha_nacimiento': fnac,
                    'escolaridad': escolaridad,
                    'condicion_migratoria': condicion,
                    'pertenece_comunidad_indigena': bool(comunidad),
                    'comunidad_indigena': comunidad,
                    'requiere_interprete': interprete,
                    'situacion_calle': calle,
                    'equipo': equipos[eq_i],
                    'registrado_por': emps[ts_i],
                    'estatus': 'activo',
                    'estatus_proceso': 'seguimiento',
                    'fecha_ingreso': fecha_ingreso,
                    'vive_con_tutor': True,
                },
            )

            if nuevo:
                creados += 1
                # Relación tutor
                NNATutor.objects.get_or_create(
                    nna=nna,
                    tutor=tutores[tutor_i],
                    defaults={
                        'parentesco': tutores[tutor_i].parentesco_con_nna,
                        'principal': True,
                        'fecha_inicio': fecha_ingreso,
                    },
                )
                # Historial de equipo
                NNAEquipo.objects.get_or_create(
                    nna=nna,
                    equipo=equipos[eq_i],
                    defaults={
                        'fecha_inicio': fecha_ingreso,
                        'activo': True,
                    },
                )

        self.stdout.write(f'  NNA: {creados} nuevos / {len(NNA_DATA)} total')

        # Idiomas para NNA de comunidades indígenas
        self._crear_idiomas_nna(nivel_avanzado, nivel_basico, modo_materna)

    def _crear_idiomas_nna(self, nivel_avanzado, nivel_basico, modo_materna):
        creados = 0
        for (curp_nna, nombre_lengua, es_materna, nivel_txt) in IDIOMAS_NNA:
            try:
                nna    = NNA.objects.get(curp=curp_nna)
                lengua = Lengua.objects.filter(nombre__iexact=nombre_lengua).first()
                if not lengua:
                    self.stdout.write(
                        self.style.WARNING(f'  Lengua no encontrada: {nombre_lengua}')
                    )
                    continue
                nivel = nivel_avanzado if 'Avanzado' in nivel_txt else nivel_basico
                _, nuevo = IdiomaNNA.objects.get_or_create(
                    nna=nna,
                    lengua=lengua,
                    defaults={
                        'es_lengua_materna': es_materna,
                        'preferente': es_materna,
                        'nivel': 'avanzado' if es_materna else 'basico',
                        'nivel_competencia': nivel,
                        'modo_adquisicion': modo_materna if es_materna else None,
                    },
                )
                if nuevo:
                    creados += 1
            except NNA.DoesNotExist:
                pass
        self.stdout.write(f'  Idiomas NNA: {creados} nuevos')
