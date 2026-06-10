from django.urls import path, include
from . import views

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.home, name='home'),

    # ── Empleados ──────────────────────────────────────────────────────────
    path('empleados/',                         views.mostrar_db,        name='lista_empleados'),
    path('empleados/nuevo/',                   views.crear_empleado,    name='crear_empleado'),
    path('empleados/<int:empleado_id>/',       views.consultar_empleado,name='consultar_empleado'),
    path('empleados/<int:empleado_id>/editar/',views.editar_empleado,   name='editar_empleado'),
    path('empleados/<int:empleado_id>/eliminar/', views.eliminar_persona, name='eliminar_persona'),
    path('empleados/<int:empleado_id>/revocar/', views.revocar_acceso,  name='revocar_acceso'),

    # ── Tutores ────────────────────────────────────────────────────────────
    path('tutores/',        views.lista_tutores, name='lista_tutores'),
    path('tutores/nuevo/',  views.crear_tutor,   name='crear_tutor'),

    # ── Equipos Multidisciplinarios ────────────────────────────────────────
    path('equipos/',        views.lista_equipos, name='lista_equipos'),
    path('equipos/nuevo/',  views.crear_equipo,  name='crear_equipo'),
    
    # ── NNA ────────────────────────────────────────────────────────────────
    path('nna/',        views.lista_nna,  name='lista_nna'),
    path('nna/nuevo/',  views.crear_nna,  name='crear_nna'),
    path('nna/<int:nna_id>/', views.detalle_nna, name='detalle_nna'),
    path(
        'nna/<int:nna_id>/seguimientos/nuevo/',
        views.crear_seguimiento_nna,
        name='crear_seguimiento_nna',
    ),

    # ── Seguimientos del expediente ───────────────────────────────────────
    path(
        'seguimientos/<int:seguimiento_id>/',
        views.detalle_seguimiento_nna,
        name='detalle_seguimiento_nna',
    ),
    path(
        'seguimientos/<int:seguimiento_id>/editar/',
        views.editar_seguimiento_nna,
        name='editar_seguimiento_nna',
    ),
    path(
        'seguimientos/<int:seguimiento_id>/eliminar/',
        views.eliminar_seguimiento_nna,
        name='eliminar_seguimiento_nna',
    ),

    # ── API (AJAX) ─────────────────────────────────────────────────────────
    path('api/asentamientos/', views.api_asentamientos, name='api_asentamientos'),
    path('api/municipios/',    views.api_municipios,    name='api_municipios'),
]
