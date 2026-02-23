from django.urls import path
from . import views

urlpatterns = [
    # Esta es la ruta para ver tu tabla de empleados
    path('empleados/', views.mostrar_db, name='lista_empleados'),
]
