from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import Empleado

def home(request):
    return render(request, 'home.html')

# Esta línea hace que si no es admin, lo mande al login o le niegue el acceso
@user_passes_test(lambda u: u.is_staff)
def mostrar_db(request):
    empleados = Empleado.objects.all()
    return render(request, 'mostrar_db.html', {'lista_empleados': empleados})