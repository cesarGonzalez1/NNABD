"""
web/admin.py — Configuración del panel de administración de Django.

Se registran los modelos con ``@admin.register`` para tener un control
explícito de ``list_display``, ``search_fields`` y campos autocompletados.
"""

from django.contrib import admin

from .models import (
    Asentamiento,
    Domicilio,
    Empleado,
    EntidadFederativa,
    EquipoMultidisciplinario,
    HechoVictimal,
    Municipio,
    NNA,
    Tutor,
    DocumentoExpediente,
)


# ── SEPOMEX ───────────────────────────────────────────────────────────────────

@admin.register(EntidadFederativa)
class EntidadFederativaAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'abreviatura')
    search_fields = ('nombre', 'clave')


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'entidad')
    search_fields = ('nombre',)
    list_filter = ('entidad',)


@admin.register(Asentamiento)
class AsentamientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_postal', 'municipio')
    search_fields = ('nombre', 'codigo_postal')
    list_per_page = 50


@admin.register(Domicilio)
class DomicilioAdmin(admin.ModelAdmin):
    search_fields = ('calle', 'asentamiento__nombre')
    autocomplete_fields = ['asentamiento']


# ── EMPLEADOS ─────────────────────────────────────────────────────────────────

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'rol', 'rfc')
    search_fields = ('nombre', 'apellido_paterno', 'rfc')
    list_filter = ('rol', 'tipo_trabajador')
    autocomplete_fields = ['domicilio']


# ── EQUIPOS ───────────────────────────────────────────────────────────────────

@admin.register(EquipoMultidisciplinario)
class EquipoMultidisciplinarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abogado', 'doctor', 'trabajador_social', 'psicologo')
    search_fields = ('nombre',)


# ── TUTORES ───────────────────────────────────────────────────────────────────

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'parentesco_con_nna', 'telefono_principal')
    search_fields = ('nombre', 'apellido_paterno', 'curp')
    list_filter = ('parentesco_con_nna',)


# ── NNA ───────────────────────────────────────────────────────────────────────

@admin.register(NNA)
class NNAAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'estatus', 'fecha_ingreso')
    search_fields = ('nombre', 'apellido_paterno', 'curp')
    list_filter = ('estatus',)


# ── HECHO VICTIMAL ────────────────────────────────────────────────────────────

@admin.register(HechoVictimal)
class HechoVictimalAdmin(admin.ModelAdmin):
    list_display = ('nna', 'tipo_delito', 'estatus_juridico', 'fecha_hecho')
    search_fields = ('nna__nombre', 'nna__apellido_paterno')
    list_filter = ('tipo_delito', 'estatus_juridico')


# ── DOCUMENTOS ────────────────────────────────────────────────────────────────

@admin.register(DocumentoExpediente)
class DocumentoExpedienteAdmin(admin.ModelAdmin):
    list_display = ('nna', 'tipo', 'nombre_archivo', 'fecha_subida')
    search_fields = ('nna__nombre', 'nombre_archivo')
    list_filter = ('tipo',)