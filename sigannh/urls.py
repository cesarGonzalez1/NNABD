"""
sigannh/urls.py — Rutas raíz del proyecto.

Las rutas de autenticación (accounts/) y todas las de la app se
definen en ``web/urls.py`` para evitar duplicación.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web.urls')),
]