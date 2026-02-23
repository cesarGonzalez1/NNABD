from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import EmpleadoForm

@login_required
def crear_empleado(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            empleado = form.save(commit=False)
            empleado.usuario = request.user
            empleado.save()
            return redirect('lista_empleados')  # luego hacemos esta vista
    else:
        form = EmpleadoForm()

    return render(request, 'empleados/crear_empleado.html', {'form': form})

def login_view(request):
    return render(request, 'login.html')


# Create your views here.
