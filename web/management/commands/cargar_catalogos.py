"""
web/management/commands/cargar_catalogos.py
────────────────────────────────────────────────────────────────────────────
Carga (o recarga) todos los catálogos base desde los CSV del proyecto:
Sexo, Nacionalidad, TipoContacto, NivelCompetenciaOral, ModoAdquisicionLengua,
GradoDependencia, FamiliaLinguistica, Lengua, TipoDiscapacidad, Discapacidad,
CapituloEnfermedad, Enfermedad.

Es idempotente: se puede correr varias veces sin duplicar filas (usa
update_or_create con la clave natural de cada catálogo).

Uso:
    python manage.py cargar_catalogos --dir ruta/a/carpeta/con/csv

Si no se pasa --dir, busca los CSV en BASE_DIR/data/catalogos/.
"""
import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from web.models import (
    Sexo, Nacionalidad, TipoContacto, NivelCompetenciaOral,
    ModoAdquisicionLengua, GradoDependencia, FamiliaLinguistica, Lengua,
    TipoDiscapacidad, Discapacidad, CapituloEnfermedad, Enfermedad,
)


def leer_csv(path):
    """Lee un CSV con encoding UTF-8 (con o sin BOM) y devuelve lista de dicts."""
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    help = "Carga los catalogos base (sexo, lenguas, discapacidades, etc.) desde CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir', type=str, default=None,
            help='Carpeta donde estan los CSV de catalogos.',
        )
        parser.add_argument(
            '--limpiar-discapacidades', action='store_true',
            help=(
                'Borra TipoDiscapacidad y Discapacidad existentes antes de '
                'recargarlos desde CSV. Usar si una carga anterior dejo '
                'duplicados (ej. "Habla" y "Habla/Lenguaje" por separado).'
            ),
        )
        parser.add_argument(
            '--limpiar-todo', action='store_true',
            help=(
                'Borra TODOS los catalogos (sexo, nacionalidad, lenguas, '
                'discapacidades, enfermedades, etc.) antes de recargarlos. '
                'Util en fase de pruebas, sin NNA/Tutor reales capturados. '
                'NO usar si ya hay datos reales que dependan de estos catalogos.'
            ),
        )

    def handle(self, *args, **options):
        carpeta = Path(options['dir']) if options['dir'] else Path(settings.BASE_DIR) / 'data' / 'catalogos'
        if not carpeta.exists():
            raise CommandError(
                f"No encontre la carpeta {carpeta}. Pasa --dir con la ruta correcta, "
                f"por ejemplo: python manage.py cargar_catalogos --dir C:\\ruta\\a\\csv"
            )

        with transaction.atomic():
            if options['limpiar_todo']:
                self._limpiar_todo()
            elif options['limpiar_discapacidades']:
                self._limpiar_discapacidades(carpeta)

            self._cargar_sexo(carpeta)
            self._cargar_nacionalidad(carpeta)
            self._cargar_tipo_contacto(carpeta)
            self._cargar_nivel_competencia_oral(carpeta)
            self._cargar_modo_adquisicion_lengua(carpeta)
            self._cargar_grado_dependencia(carpeta)
            self._cargar_familias_y_lenguas(carpeta)
            self._cargar_tipos_y_discapacidades(carpeta)
            self._cargar_cie10(carpeta)

        self.stdout.write(self.style.SUCCESS("Catalogos cargados correctamente."))

    def _limpiar_todo(self):
        """
        Borra todos los catalogos base por completo. Solo seguro en fase de
        pruebas, sin NNA/Tutor reales que dependan de estos registros.
        """
        modelos = [
            Enfermedad, CapituloEnfermedad,
            Discapacidad, TipoDiscapacidad,
            Lengua, FamiliaLinguistica,
            GradoDependencia, ModoAdquisicionLengua, NivelCompetenciaOral,
            TipoContacto, Nacionalidad, Sexo,
        ]
        for modelo in modelos:
            n, _ = modelo.objects.all().delete()
            self.stdout.write(f"  {modelo.__name__}: {n} eliminados")
        self.stdout.write(self.style.WARNING("Todos los catalogos fueron vaciados."))

    def _limpiar_discapacidades(self, carpeta):
        """
        Borra por completo TipoDiscapacidad y Discapacidad para eliminar
        cualquier duplicado/basura dejado por una carga anterior con otro
        script (ej. "Habla" y "Habla/Lenguaje" como filas separadas).

        Como no hay NNA/Tutor reales con discapacidades capturadas todavia,
        no se necesita reasignar nada: se borra y se recarga limpio desde
        los CSV oficiales.
        """
        n_disc, _ = Discapacidad.objects.all().delete()
        n_tipo, _ = TipoDiscapacidad.objects.all().delete()
        self.stdout.write(f"Limpieza: {n_disc} Discapacidad y {n_tipo} TipoDiscapacidad eliminados.")

    # ── Catalogos simples (clave, nombre, descripcion) ──────────────────

    def _cargar_sexo(self, carpeta):
        path = carpeta / 'sexos.csv'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path.name} no existe"))
            return
        n = 0
        for row in leer_csv(path):
            Sexo.objects.update_or_create(
                clave=row['clave'].strip(),
                defaults={
                    'nombre': row['nombre'].strip(),
                    'descripcion': (row.get('descripcion') or '').strip(),
                },
            )
            n += 1
        self.stdout.write(f"Sexo: {n} registros")

    def _cargar_nacionalidad(self, carpeta):
        path = carpeta / 'nacionalidades.csv'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path.name} no existe"))
            return
        n = 0
        for row in leer_csv(path):
            Nacionalidad.objects.update_or_create(
                clave=row['clave'].strip(),
                defaults={
                    'nombre': row['nombre'].strip(),
                    'descripcion': (row.get('descripcion') or '').strip(),
                },
            )
            n += 1
        self.stdout.write(f"Nacionalidad: {n} registros")

    def _cargar_tipo_contacto(self, carpeta):
        path = carpeta / 'tipos_contacto.csv'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path.name} no existe"))
            return
        n = 0
        for row in leer_csv(path):
            # El CSV trae 'id' numerico; lo usamos como clave de texto.
            clave = str(row['id']).strip()
            TipoContacto.objects.update_or_create(
                clave=clave,
                defaults={
                    'nombre': row['nombre'].strip(),
                    'descripcion': (row.get('descripcion') or '').strip(),
                },
            )
            n += 1
        self.stdout.write(f"TipoContacto: {n} registros")

    def _cargar_nivel_competencia_oral(self, carpeta):
        path = carpeta / 'niveles_competencia_oral.csv'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path.name} no existe"))
            return
        n = 0
        for row in leer_csv(path):
            clave = str(row['id']).strip()
            texto_interprete = (row.get('sin_necesidad_interprete') or '').strip().lower()
            requiere_interprete = not texto_interprete.startswith('s')  # "Sí sin necesidad..." -> no requiere
            NivelCompetenciaOral.objects.update_or_create(
                clave=clave,
                defaults={
                    'nombre': row['nivel_practico'].strip(),
                    'significado': (row.get('significado') or '').strip(),
                    'puede_declarar': True,
                    'requiere_interprete': requiere_interprete,
                },
            )
            n += 1
        self.stdout.write(f"NivelCompetenciaOral: {n} registros")

    def _cargar_modo_adquisicion_lengua(self, carpeta):
        path = carpeta / 'modos_adquisicion_lengua.csv'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path.name} no existe"))
            return
        n = 0
        for row in leer_csv(path):
            clave = str(row['id']).strip()
            ModoAdquisicionLengua.objects.update_or_create(
                clave=clave,
                defaults={
                    'categoria': row['categoria'].strip(),
                    'descripcion': (row.get('como_se_adquiere') or '').strip(),
                    'contexto': (row.get('contexto_tipico') or '').strip(),
                },
            )
            n += 1
        self.stdout.write(f"ModoAdquisicionLengua: {n} registros")

    def _cargar_grado_dependencia(self, carpeta):
        path = carpeta / 'grados_dependencia.csv'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path.name} no existe"))
            return
        n = 0
        for row in leer_csv(path):
            GradoDependencia.objects.update_or_create(
                clave=row['clave'].strip(),
                defaults={
                    'nombre': row['nombre'].strip(),
                    'descripcion': (row.get('descripcion') or '').strip(),
                },
            )
            n += 1
        self.stdout.write(f"GradoDependencia: {n} registros")

    # ── Familias linguisticas + Lenguas (con FK) ────────────────────────

    def _cargar_familias_y_lenguas(self, carpeta):
        path_familias = carpeta / 'familias_linguisticas.csv'
        path_lenguas = carpeta / 'lenguas.csv'

        familia_por_nombre = {}
        if path_familias.exists():
            n = 0
            for row in leer_csv(path_familias):
                familia, _ = FamiliaLinguistica.objects.update_or_create(
                    catalogo_id=int(row['id']),
                    defaults={'nombre': row['familia_linguistica'].strip()},
                )
                familia_por_nombre[row['familia_linguistica'].strip()] = familia
                n += 1
            self.stdout.write(f"FamiliaLinguistica: {n} registros")
        else:
            self.stdout.write(self.style.WARNING(f"Omitido: {path_familias.name} no existe"))

        if not path_lenguas.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path_lenguas.name} no existe"))
            return

        n = 0
        for row in leer_csv(path_lenguas):
            nombre_familia = (row.get('familia_linguistica') or '').strip()
            familia = familia_por_nombre.get(nombre_familia)

            # El nombre real de la lengua viene en 'agrupacion_linguistica'
            # (ej. "Kickapoo", "Cochimí"), NO en una columna 'nombre'.
            nombre_lengua = (row.get('agrupacion_linguistica') or '').strip()
            if not nombre_lengua:
                continue  # fila sin nombre util, se omite

            autodenominacion = (row.get('autodenominacion') or '').strip()
            if autodenominacion.lower() == 'pendiente':
                autodenominacion = ''

            Lengua.objects.update_or_create(
                catalogo_id=int(row['id']),
                defaults={
                    'nombre': nombre_lengua,
                    'familia': familia,
                    'es_indigena': True,
                    'autodenominacion': autodenominacion,
                },
            )
            n += 1
        self.stdout.write(f"Lengua: {n} registros")

        # Asegura que exista Español como lengua no indigena para el caso comun.
        Lengua.objects.update_or_create(
            clave_inali='ESP',
            defaults={'nombre': 'Español', 'es_indigena': False, 'familia': None},
        )

    # ── Tipos de discapacidad + Discapacidades especificas ──────────────

    def _cargar_tipos_y_discapacidades(self, carpeta):
        path_tipos = carpeta / 'tipos_discapacidad.csv'
        path_discapacidades = carpeta / 'discapacidades_minimo.csv'

        tipo_por_id_csv = {}
        if path_tipos.exists():
            n = 0
            for row in leer_csv(path_tipos):
                tipo, _ = TipoDiscapacidad.objects.update_or_create(
                    clave_inegi=str(row['id']).strip(),
                    defaults={
                        'nombre': row['nombre'].strip(),
                        'descripcion': (row.get('descripcion') or '').strip(),
                    },
                )
                tipo_por_id_csv[str(row['id']).strip()] = tipo
                n += 1
            self.stdout.write(f"TipoDiscapacidad: {n} registros")
        else:
            self.stdout.write(self.style.WARNING(f"Omitido: {path_tipos.name} no existe"))

        if not path_discapacidades.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path_discapacidades.name} no existe"))
            return

        # discapacidades_minimo.csv trae 'tipo' como TEXTO (ej. "Motriz"),
        # no como id numerico de tipos_discapacidad.csv. Hay que mapear
        # ese texto a la categoria INEGI correspondiente.
        mapa_texto_a_clave_inegi = {
            'motriz':              '1',  # Física
            'visual':              '2',  # Sensorial
            'auditiva':            '2',  # Sensorial
            'habla/lenguaje':      '2',  # Sensorial
            'intelectual':         '3',  # Intelectual / Cognitiva
            'psicosocial/mental':  '4',  # Psicosocial (Salud Mental)
            'multiple':            '5',  # Múltiple
        }

        n = 0
        omitidos = []
        for row in leer_csv(path_discapacidades):
            texto_tipo = row['tipo'].strip().lower()
            clave_inegi = mapa_texto_a_clave_inegi.get(texto_tipo)
            tipo = tipo_por_id_csv.get(clave_inegi) if clave_inegi else None

            if tipo is None:
                omitidos.append(row['tipo'])
                continue

            Discapacidad.objects.update_or_create(
                nombre=row['nombre'].strip(),
                defaults={
                    'tipo': tipo,
                    'descripcion': (row.get('descripcion') or '').strip(),
                },
            )
            n += 1
        self.stdout.write(f"Discapacidad: {n} registros")
        if omitidos:
            self.stdout.write(self.style.WARNING(
                f"  Tipos sin mapear, omitidos: {set(omitidos)}"
            ))

    # ── CIE-10 minimo ────────────────────────────────────────────────────

    def _cargar_cie10(self, carpeta):
        path = carpeta / 'cie10_minimo.csv'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Omitido: {path.name} no existe"))
            return

        capitulo_cache = {}
        n_cap = 0
        n_enf = 0
        for row in leer_csv(path):
            codigo_cap = row['capitulo'].strip()
            capitulo = capitulo_cache.get(codigo_cap)
            if capitulo is None:
                capitulo, creado = CapituloEnfermedad.objects.update_or_create(
                    codigo=codigo_cap,
                    defaults={'nombre': f'Capítulo {codigo_cap}'},
                )
                capitulo_cache[codigo_cap] = capitulo
                if creado:
                    n_cap += 1

            Enfermedad.objects.update_or_create(
                codigo_cie10=row['codigo_cie10'].strip(),
                defaults={
                    'nombre': row['nombre'].strip(),
                    'nombre_corto': (row.get('nombre_corto') or '').strip() or row['nombre'].strip()[:100],
                    'capitulo': capitulo,
                },
            )
            n_enf += 1

        self.stdout.write(f"CapituloEnfermedad: {n_cap} nuevos")
        self.stdout.write(f"Enfermedad: {n_enf} registros")
