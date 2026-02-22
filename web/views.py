from django.shortcuts import render, get_object_or_404, redirect
from .models import Empleado
from .forms import EmpleadoForm

def consultar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    return render(request, 'consultar_empleado.html', {'empleado': empleado})

def editar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)

    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            return redirect('consultar_empleado', empleado_id=empleado.id)
    else:
        form = EmpleadoForm(instance=empleado)

    return render(request, 'editar_empleado.html', {'form': form})

# Create your views here.
