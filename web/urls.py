from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('empleado/<int:empleado_id>/', views.consultar_empleado, name='consultar_empleado'),
    path('empleado/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
]