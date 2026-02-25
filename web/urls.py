from django.urls import path,include
from . import views
from django.contrib import admin

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.home, name='home'), 
    path('empleados/<int:empleado_id>/', views.consultar_empleado, name='consultar_empleado'),
    path('empleados/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleados/<int:empleado_id>/eliminar/', views.eliminar_persona, name='eliminar_persona'),
    path('empleados/<int:empleado_id>/revocar/', views.revocar_acceso, name='revocar_acceso'),
    path('empleados/nuevo/', views.crear_empleado, name='crear_empleado'),
    # Esta línea es la que falta para que http://127.0.0.1:8000/ funcione
    path('empleados/', views.mostrar_db, name='lista_empleados'),

]