from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('empleados/nuevo/', views.crear_empleado, name='crear_empleado'),
]