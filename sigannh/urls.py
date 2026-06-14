from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esto habilita el login en /accounts/login/
    path('accounts/', include('django.contrib.auth.urls')), 
    # Esto conecta con las urls de tu app 'web'
    path('', include('web.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
