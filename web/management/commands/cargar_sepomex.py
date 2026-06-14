"""
Management command: cargar_sepomex
===================================
Importa el catálogo SEPOMEX (Correos de México) a las tablas:
  EntidadFederativa · Municipio · TipoAsentamiento · Asentamiento

USO
---
  # Desde archivo descargado manualmente:
  python manage.py cargar_sepomex --archivo /ruta/al/CPdescarga.txt

  # Con descarga automática (requiere conexión a Internet):
  python manage.py cargar_sepomex --descargar

  # Borrar datos previos y reimportar:
  python manage.py cargar_sepomex --archivo CPdescarga.txt --limpiar

FUENTE OFICIAL
--------------
  https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/Descarga.aspx
  Formato: TXT separado por '|', codificación UTF-8 (o latin-1 en versiones antiguas)

COLUMNAS DEL ARCHIVO SEPOMEX (en orden)
-----------------------------------------
  0  d_codigo       → Código Postal
  1  d_asenta       → Nombre del asentamiento / colonia
  2  d_tipo_asenta  → Tipo de asentamiento (Colonia, Fraccionamiento, etc.)
  3  D_mnpio        → Nombre del municipio / alcaldía
  4  d_estado       → Nombre del estado
  5  d_ciudad       → Ciudad (puede estar vacío)
  6  d_CP           → CP de la administración postal (ignorado)
  7  c_estado       → Clave INEGI del estado (2 dígitos)
  8  c_oficina      → (ignorado)
  9  c_CP           → (ignorado)
  10 c_tipo_asenta  → Clave del tipo de asentamiento
  11 c_mnpio        → Clave INEGI del municipio (3 dígitos)
  12 id_asenta_cpcons → (ignorado)
  13 d_zona         → (ignorado)
  14 c_cve_ciudad   → (ignorado)
"""

import io
import os
import sys
import zipfile
import urllib.request
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from web.models import (
    EntidadFederativa, Municipio, TipoAsentamiento, Asentamiento
)

# URL oficial de descarga de Correos de México (ZIP con el TXT adentro)
URL_SEPOMEX = (
    "https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/Descarga.aspx"
)
# URL alternativa (datos.gob.mx CDN — actualizada periódicamente)
URL_ALTERNATIVA = (
    "https://www.inegi.org.mx/contenidos/app/ageeml/"
    "AgeemlCsv.zip"
)


class Command(BaseCommand):
    help = "Carga el catálogo SEPOMEX en las tablas de la base de datos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--archivo",
            type=str,
            help="Ruta al archivo TXT de SEPOMEX (CPdescarga.txt o similar).",
        )
        parser.add_argument(
            "--descargar",
            action="store_true",
            help="Intentar descargar el archivo automáticamente de Correos de México.",
        )
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Eliminar todos los registros SEPOMEX existentes antes de importar.",
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=0,
            help="Limitar la importación a N filas (útil para pruebas). 0 = sin límite.",
        )

    # ──────────────────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        if not options["archivo"] and not options["descargar"]:
            self.stderr.write(self.style.ERROR(
                "\nDebes indicar --archivo <ruta> o usar --descargar.\n"
                "\nEjemplo:\n"
                "  python manage.py cargar_sepomex --archivo CPdescarga.txt\n"
                "\nDescarga manual:\n"
                "  1. Ve a: https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/Descarga.aspx\n"
                "  2. Acepta los términos y descarga el archivo .txt o .zip\n"
                "  3. Descomprime si es ZIP y ejecuta:\n"
                "     python manage.py cargar_sepomex --archivo CPdescarga.txt\n"
            ))
            return

        # ── Obtener la ruta/contenido del archivo ─────────────────────────
        if options["descargar"]:
            lines = self._descargar()
            if lines is None:
                return
        else:
            ruta = options["archivo"]
            if not os.path.exists(ruta):
                raise CommandError(f"El archivo no existe: {ruta}")
            lines = self._leer_archivo(ruta)

        if not lines:
            raise CommandError("El archivo está vacío o no pudo leerse.")

        # ── Limpiar si se pidió ───────────────────────────────────────────
        if options["limpiar"]:
            self.stdout.write(" Eliminando datos SEPOMEX previos…")
            Asentamiento.objects.all().delete()
            Municipio.objects.all().delete()
            TipoAsentamiento.objects.all().delete()
            EntidadFederativa.objects.all().delete()
            self.stdout.write(self.style.WARNING("   Datos previos eliminados."))

        # ── Importar ──────────────────────────────────────────────────────
        self._importar(lines, limite=options["limite"])

    # ──────────────────────────────────────────────────────────────────────
    def _leer_archivo(self, ruta):
        """Lee el archivo TXT de SEPOMEX probando varias codificaciones."""
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                with open(ruta, encoding=encoding) as fh:
                    lines = fh.readlines()
                self.stdout.write(f" Archivo leído con codificación {encoding} ({len(lines)} líneas)")
                return lines
            except UnicodeDecodeError:
                continue
        raise CommandError("No se pudo leer el archivo con ninguna codificación conocida.")

    def _descargar(self):
        """
        Intenta descargar el ZIP de SEPOMEX de Correos de México.
        Correos de México requiere aceptar términos vía POST; la descarga
        directa de datos.gob.mx suele funcionar sin restricciones.
        """
        urls = [
            # Enlace directo al ZIP más reciente en datos.gob.mx
            "https://www.datos.gob.mx/busca/dataset/catalogo-nacional-de-codigos-postales",
            # Fallback: archivo hospedado por la CDMX
            "https://datos.cdmx.gob.mx/dataset/codigos-postales/resource/37924cf1-1f57-4f96-9c49-e94cf36c6a23",
        ]
        self.stderr.write(self.style.WARNING(
            "\n La descarga automática de SEPOMEX requiere aceptar términos de uso.\n"
            "   Descarga manualmente desde:\n"
            "   https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/Descarga.aspx\n"
            "   y luego ejecuta:\n"
            "   python manage.py cargar_sepomex --archivo CPdescarga.txt\n"
        ))
        return None

    # ──────────────────────────────────────────────────────────────────────
    def _importar(self, lines, limite=0):
        """Parsea línea a línea e inserta en BD usando bulk_create con caché."""

        header_idx = 0
        for idx, line in enumerate(lines):
            normalized = line.strip().lower()
            if normalized.startswith("d_codigo|") or normalized.startswith("d_codigo\t"):
                header_idx = idx
                break

        # Detectar separador: '|' (oficial) o '\t' (algunas versiones)
        primera = lines[header_idx] if lines else ""
        sep = "|" if "|" in primera else "\t"
        self.stdout.write(f" Separador detectado: '{sep}'")

        # Saltar texto legal y encabezado real.
        data_lines = lines[header_idx + 1:]
        if limite:
            data_lines = data_lines[:limite]
            self.stdout.write(f" Modo prueba: importando solo {limite} filas.")

        # ── Cachés en memoria para evitar consultas repetidas ─────────────
        estados   = {}   # clave_inegi → EntidadFederativa
        municipios = {}  # (clave_estado, clave_mpio) → Municipio
        tipos      = {}  # nombre → TipoAsentamiento

        # Precargar existentes (útil si se importa incrementalmente)
        for e in EntidadFederativa.objects.all():
            estados[e.clave] = e
        for m in Municipio.objects.select_related("entidad").all():
            municipios[(m.entidad.clave, m.clave)] = m
        for t in TipoAsentamiento.objects.all():
            tipos[t.nombre] = t

        asentamientos_bulk = []
        errores = 0
        procesadas = 0
        BATCH = 2000

        self.stdout.write(" Importando… (esto puede tardar 2-5 minutos para el catálogo completo)")

        with transaction.atomic():
            for i, linea in enumerate(data_lines, start=2):
                linea = linea.rstrip("\n\r")
                if not linea.strip():
                    continue

                cols = linea.split(sep)
                if len(cols) < 12:
                    errores += 1
                    continue

                try:
                    cp             = cols[0].strip().zfill(5)
                    nom_asenta     = cols[1].strip()
                    nom_tipo       = cols[2].strip() or "Colonia"
                    nom_mpio       = cols[3].strip()
                    nom_estado     = cols[4].strip()
                    ciudad         = cols[5].strip() if len(cols) > 5 else ""
                    clave_estado   = cols[7].strip().zfill(2) if len(cols) > 7 else "00"
                    clave_mpio     = cols[11].strip().zfill(3) if len(cols) > 11 else "000"

                    if not cp or not nom_asenta:
                        continue

                    # ── EntidadFederativa ──────────────────────────────────
                    if clave_estado not in estados:
                        estado, _ = EntidadFederativa.objects.get_or_create(
                            clave=clave_estado,
                            defaults={"nombre": nom_estado, "abreviatura": ""},
                        )
                        estados[clave_estado] = estado
                    estado = estados[clave_estado]

                    # ── Municipio ──────────────────────────────────────────
                    key_mpio = (clave_estado, clave_mpio)
                    if key_mpio not in municipios:
                        mpio, _ = Municipio.objects.get_or_create(
                            entidad=estado,
                            clave=clave_mpio,
                            defaults={"nombre": nom_mpio},
                        )
                        municipios[key_mpio] = mpio
                    municipio = municipios[key_mpio]

                    # ── TipoAsentamiento ───────────────────────────────────
                    if nom_tipo not in tipos:
                        tipo, _ = TipoAsentamiento.objects.get_or_create(nombre=nom_tipo)
                        tipos[nom_tipo] = tipo
                    tipo = tipos[nom_tipo]

                    # ── Asentamiento (buffer bulk) ─────────────────────────
                    asentamientos_bulk.append(Asentamiento(
                        municipio=municipio,
                        tipo_asentamiento=tipo,
                        nombre=nom_asenta,
                        codigo_postal=cp,
                        ciudad=ciudad,
                    ))
                    procesadas += 1

                    # Flush cada BATCH filas
                    if len(asentamientos_bulk) >= BATCH:
                        Asentamiento.objects.bulk_create(
                            asentamientos_bulk, ignore_conflicts=True
                        )
                        asentamientos_bulk = []
                        self.stdout.write(f"   … {procesadas:,} colonias procesadas", ending="\r")
                        sys.stdout.flush()

                except Exception as exc:
                    errores += 1
                    if errores <= 5:
                        self.stderr.write(f"    Línea {i}: {exc}")

            # Flush restantes
            if asentamientos_bulk:
                Asentamiento.objects.bulk_create(asentamientos_bulk, ignore_conflicts=True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"\n Importación completada:"
            f"\n   Estados:    {len(estados):,}"
            f"\n   Municipios: {len(municipios):,}"
            f"\n   Tipos:      {len(tipos):,}"
            f"\n   Colonias:   {procesadas:,}"
            f"\n   Errores:    {errores:,}"
        ))
        if errores > 5:
            self.stderr.write(self.style.WARNING(
                f"   (Se omitieron {errores} líneas con formato inesperado)"
            ))
