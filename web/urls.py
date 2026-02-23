from django.urls import path
from . import views

urlpatterns = [
    # Esta línea es la que falta para que http://127.0.0.1:8000/ funcione
    path('', views.home, name='home'), 
    path('empleados/', views.mostrar_db, name='lista_empleados'),
]