from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esto habilita el login en /accounts/login/
    path('accounts/', include('django.contrib.auth.urls')), 
    # Esto conecta con las urls de tu app 'web'
    path('', include('web.urls')),
]