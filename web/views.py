
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.db import transaction
from .models import Empleado
from .forms import EmpleadoForm

def login_view(request):
    return render(request, 'registration/login.html')

@login_required
def consultar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    return render(request, 'empleados/consultar_empleado.html', {'empleado': empleado})

@login_required
def editar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)

    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            return redirect('consultar_empleado', empleado_id=empleado.id)
    else:
        form = EmpleadoForm(instance=empleado)

    return render(request, 'empleados/editar_empleado.html', {'form': form})

@login_required
def crear_empleado(request):
    try:
        if request.user.empleado.rol != 'director':
            return HttpResponseForbidden("no tienes permiso para esto")
    except Empleado.DoesNotExist:
        return HttpResponseForbidden("Debes tener un perfil de empleado")   
     
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Este usuario ya existe')
                return render(request, 'empleados/crear_empleado.html', {'form': form})

            try:
                with transaction.atomic():

                    user = User.objects.create_user(
                        username=username,
                        password=password
                    )

                    empleado = form.save(commit=False)
                    empleado.usuario = user
                    empleado.save()

                return redirect('lista_empleados')

            except Exception as e:
                form.add_error(None, f'Error al crear empleado: {str(e)}')

    else:
        form = EmpleadoForm()

    return render(request, 'empleados/crear_empleado.html', {'form': form})

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def mostrar_db(request):
    try:
        if request.user.empleado.rol != 'director':
            return HttpResponseForbidden("No tienes permiso")
    except Empleado.DoesNotExist:
        return HttpResponseForbidden("No tienes perfil de empleado")

    empleados = Empleado.objects.all()
    return render(request, 'empleados/mostrar_db.html', {'lista_empleados': empleados})

@login_required
def eliminar_persona(request, empleado_id):
    
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        
        empleado.usuario.delete() 
        return redirect('lista_empleados') 
        
    return render(request, 'empleados/eliminar_persona.html', {'empleado': empleado})
 
@login_required
def revocar_acceso(request, empleado_id):
    
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        
        usuario = empleado.usuario
        usuario.is_active = False 
        usuario.save() 
        return redirect('lista_empleados')
        
    return render(request, 'empleados/revocar_acceso.html', {'empleado': empleado})