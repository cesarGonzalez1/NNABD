from django.contrib import admin
from .models import (
    Empleado, Domicilio, Asentamiento, Municipio, EntidadFederativa,
    NNA, Tutor, HechoVictimal
)

# 1. Configuración de SEPOMEX (Indispensable para que funcione el buscador)
@admin.register(Asentamiento)
class AsentamientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_postal', 'municipio')
    search_fields = ('nombre', 'codigo_postal') # Esto habilita la lupa de búsqueda
    list_per_page = 50

# 2. Configuración de Domicilio (Aquí es donde seleccionas la colonia)
@admin.register(Domicilio)
class DomicilioAdmin(admin.ModelAdmin):
    search_fields = ('calle', 'asentamiento__nombre')
    autocomplete_fields = ['asentamiento'] # Esto cambia el desplegable por un buscador de texto

# 3. Tu perfil de Empleado
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'rol', 'rfc')
    search_fields = ('nombre', 'apellido_paterno', 'rfc')
    autocomplete_fields = ['domicilio'] # También permite buscar el domicilio por texto

# Registros básicos para que aparezcan las otras tablas
admin.site.register(Municipio)
admin.site.register(EntidadFederativa)
admin.site.register(NNA)
admin.site.register(Tutor)
admin.site.register(HechoVictimal)