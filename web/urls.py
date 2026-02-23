from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path('', views.login_view, name='login'),
    path('empleados/<int:empleado_id>/', views.consultar_empleado, name='consultar_empleado'),
    path('empleados/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleados/nuevo/', views.crear_empleado, name='crear_empleado'),
    # Esta línea es la que falta para que http://127.0.0.1:8000/ funcione
    path('', views.home, name='home'), 
    path('empleados/', views.mostrar_db, name='lista_empleados'),

]