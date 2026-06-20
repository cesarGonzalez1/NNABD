from django.contrib import admin
from .models import (
    Empleado, Domicilio, Asentamiento, Municipio, EntidadFederativa,
    NNA, Tutor, HechoVictimal, SeguimientoNNA,
    Derecho, InstitucionEjecutora, PlanRestitucion, DerechoVulnerado,
    MedidaProteccion, SeguimientoMedida,
    ConsentimientoDatos, SolicitudARCO, BitacoraAcceso,
    Sexo, Nacionalidad, TipoContacto, NivelCompetenciaOral,
    ModoAdquisicionLengua, GradoDependencia, TipoDiscapacidad,
    Discapacidad, CapituloEnfermedad, Enfermedad,
    FamiliaLinguistica, Lengua, VarianteLinguistica,
    NNATutor, NacionalidadNNA, ContactoNNA,
    IdiomaNNA, IdiomaTutor, IdiomaEmpleado, DiscapacidadNNA,
    PadecimientoNNA, DocumentoExpediente,
    ContactoTutor, ContactoEmpleado,
)


@admin.register(Asentamiento)
class AsentamientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_postal', 'municipio')
    search_fields = ('nombre', 'codigo_postal')
    list_per_page = 50


@admin.register(Domicilio)
class DomicilioAdmin(admin.ModelAdmin):
    search_fields = ('calle', 'asentamiento__nombre')
    autocomplete_fields = ['asentamiento']


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'rol', 'rfc')
    search_fields = ('nombre', 'apellido_paterno', 'rfc')
    autocomplete_fields = ['domicilio']


admin.site.register(Municipio)
admin.site.register(EntidadFederativa)
admin.site.register(CapituloEnfermedad)
admin.site.register(Enfermedad)
admin.site.register(VarianteLinguistica)
admin.site.register(Sexo)
admin.site.register(Nacionalidad)
admin.site.register(GradoDependencia)


@admin.register(TipoContacto)
class TipoContactoAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'descripcion')
    search_fields = ('clave', 'nombre', 'descripcion')


@admin.register(NivelCompetenciaOral)
class NivelCompetenciaOralAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'puede_declarar', 'requiere_interprete')
    list_filter = ('puede_declarar', 'requiere_interprete')
    search_fields = ('clave', 'nombre', 'significado')


@admin.register(ModoAdquisicionLengua)
class ModoAdquisicionLenguaAdmin(admin.ModelAdmin):
    list_display = ('clave', 'categoria', 'descripcion', 'contexto')
    search_fields = ('clave', 'categoria', 'descripcion', 'contexto')


@admin.register(FamiliaLinguistica)
class FamiliaLinguisticaAdmin(admin.ModelAdmin):
    list_display = ('catalogo_id', 'nombre')
    search_fields = ('catalogo_id', 'nombre')


@admin.register(Lengua)
class LenguaAdmin(admin.ModelAdmin):
    list_display = (
        'catalogo_id', 'familia', 'agrupacion_linguistica',
        'variante_linguistica', 'autodenominacion', 'estado_region',
    )
    list_filter = ('familia', 'estado_region')
    search_fields = (
        'catalogo_id', 'nombre', 'agrupacion_linguistica',
        'variante_linguistica', 'autodenominacion', 'estado_region',
    )


@admin.register(TipoDiscapacidad)
class TipoDiscapacidadAdmin(admin.ModelAdmin):
    list_display = ('clave_inegi', 'nombre', 'descripcion')
    search_fields = ('clave_inegi', 'nombre', 'descripcion')


@admin.register(Discapacidad)
class DiscapacidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'descripcion')
    list_filter = ('tipo',)
    search_fields = ('nombre', 'tipo__nombre', 'descripcion')


@admin.register(NNA)
class NNAAdmin(admin.ModelAdmin):
    list_display = ('folio_nna', 'nombre', 'apellido_paterno', 'apellido_materno', 'estatus', 'equipo')
    list_filter = ('estatus', 'sexo')
    search_fields = ('folio_nna', 'nombre', 'apellido_paterno', 'apellido_materno', 'curp')
    autocomplete_fields = ['domicilio']


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'parentesco_con_nna', 'telefono_principal')
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'curp')


admin.site.register(HechoVictimal)
admin.site.register(NNATutor)
admin.site.register(NacionalidadNNA)
admin.site.register(ContactoNNA)
admin.site.register(IdiomaNNA)
admin.site.register(IdiomaTutor)
admin.site.register(IdiomaEmpleado)
admin.site.register(DiscapacidadNNA)
admin.site.register(PadecimientoNNA)
admin.site.register(DocumentoExpediente)
admin.site.register(ContactoTutor)
admin.site.register(ContactoEmpleado)


@admin.register(SeguimientoNNA)
class SeguimientoNNAAdmin(admin.ModelAdmin):
    list_display = ('nna', 'area', 'titulo', 'fecha', 'registrado_por', 'estatus')
    list_filter = ('area', 'estatus', 'fecha')
    search_fields = (
        'nna__nombre', 'nna__apellido_paterno', 'nna__apellido_materno',
        'titulo', 'descripcion',
    )
    autocomplete_fields = ['registrado_por']


# ============================================================================
# MODULO DE RESTITUCION DE DERECHOS
# ============================================================================

@admin.register(Derecho)
class DerechoAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'fundamento')
    search_fields = ('clave', 'nombre')


@admin.register(InstitucionEjecutora)
class InstitucionEjecutoraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'nivel', 'telefono')
    list_filter = ('tipo', 'nivel')
    search_fields = ('nombre',)


class DerechoVulneradoInline(admin.TabularInline):
    model = DerechoVulnerado
    extra = 1
    raw_id_fields = ('derecho',)


@admin.register(PlanRestitucion)
class PlanRestitucionAdmin(admin.ModelAdmin):
    list_display = ('folio', 'nna', 'estatus', 'grado_peligro', 'vigente', 'fecha_apertura')
    list_filter = ('estatus', 'grado_peligro', 'vigente')
    search_fields = ('folio', 'nna__nombre', 'nna__apellido_paterno')
    raw_id_fields = ('nna', 'elaborado_por', 'equipo')
    inlines = [DerechoVulneradoInline]


class SeguimientoMedidaInline(admin.TabularInline):
    model = SeguimientoMedida
    extra = 1
    raw_id_fields = ('registrado_por',)


@admin.register(MedidaProteccion)
class MedidaProteccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'derecho_vulnerado', 'institucion', 'tipo', 'estatus', 'judicializada')
    list_filter = ('tipo', 'estatus', 'judicializada')
    raw_id_fields = ('derecho_vulnerado', 'institucion', 'responsable')
    inlines = [SeguimientoMedidaInline]


# ============================================================================
# MODULO DE PRIVACIDAD Y AUDITORIA
# ============================================================================

@admin.register(ConsentimientoDatos)
class ConsentimientoDatosAdmin(admin.ModelAdmin):
    list_display = ('nna', 'acepta_tratamiento', 'vigente', 'fecha_otorgamiento', 'fecha_revocacion')
    list_filter = ('acepta_tratamiento', 'acepta_datos_sensibles')
    raw_id_fields = ('nna', 'otorgado_por')


@admin.register(SolicitudARCO)
class SolicitudARCOAdmin(admin.ModelAdmin):
    list_display = ('nna', 'tipo', 'estatus', 'fecha_solicitud', 'fecha_respuesta')
    list_filter = ('tipo', 'estatus')
    raw_id_fields = ('nna', 'atendida_por')


@admin.register(BitacoraAcceso)
class BitacoraAccesoAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'accion', 'modelo', 'objeto_id', 'nna', 'ip')
    list_filter = ('accion', 'modelo', 'fecha_hora')
    search_fields = ('modelo', 'objeto_id', 'usuario__username')
    date_hierarchy = 'fecha_hora'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
