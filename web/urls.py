"""
web/urls.py — Rutas de la aplicación SIGA-NNA.

Convención de nombres:
  lista_<entidad>     → listado
  crear_<entidad>     → formulario de creación
  consultar_<entidad> → detalle de lectura
  editar_<entidad>    → formulario de edición
  eliminar_<entidad>  → confirmación de eliminación
"""

from django.urls import path, include

from . import views

urlpatterns = [
    # ── Autenticación (login, logout, password reset, etc.) ────────────
    path('accounts/', include('django.contrib.auth.urls')),

    # ── Inicio ─────────────────────────────────────────────────────────
    path('', views.home, name='home'),

    # ── Empleados ──────────────────────────────────────────────────────
    path('empleados/',                             views.lista_empleados,    name='lista_empleados'),
    path('empleados/nuevo/',                       views.crear_empleado,     name='crear_empleado'),
    path('empleados/<int:empleado_id>/',           views.consultar_empleado, name='consultar_empleado'),
    path('empleados/<int:empleado_id>/editar/',    views.editar_empleado,    name='editar_empleado'),
    path('empleados/<int:empleado_id>/eliminar/',  views.eliminar_empleado,  name='eliminar_empleado'),
    path('empleados/<int:empleado_id>/revocar/',   views.revocar_acceso,     name='revocar_acceso'),

    # ── Tutores ────────────────────────────────────────────────────────
    path('tutores/',       views.lista_tutores, name='lista_tutores'),
    path('tutores/nuevo/', views.crear_tutor,   name='crear_tutor'),

    # ── Equipos Multidisciplinarios ────────────────────────────────────
    path('equipos/',       views.lista_equipos, name='lista_equipos'),
    path('equipos/nuevo/', views.crear_equipo,  name='crear_equipo'),

    # ── NNA ────────────────────────────────────────────────────────────
    path('nna/',       views.lista_nna, name='lista_nna'),
    path('nna/nuevo/', views.crear_nna, name='crear_nna'),

    # ── API (AJAX) ─────────────────────────────────────────────────────
    path('api/asentamientos/', views.api_asentamientos, name='api_asentamientos'),
    path('api/municipios/',    views.api_municipios,    name='api_municipios'),
]
