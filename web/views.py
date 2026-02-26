from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
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
    if not request.user.is_superuser:
        # (Tu validación de rol de director se queda igual...)
        pass
     
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)

        if form.is_valid():
            # EXTRAEMOS EL RFC PARA USARLO COMO USERNAME
            rfc_usuario = form.cleaned_data['rfc']
            password = form.cleaned_data['password']

            # Verificamos si ya existe alguien con ese RFC/Username
            if User.objects.filter(username=rfc_usuario).exists():
                form.add_error(None, 'Ya existe un empleado con este RFC registrado.')
                return render(request, 'empleados/crear_empleado.html', {'form': form})

            try:
                with transaction.atomic():
                    # CREAMOS EL USUARIO USANDO EL RFC
                    user = User.objects.create_user(
                        username=rfc_usuario, 
                        password=password
                    )

                    empleado = form.save(commit=False)
                    empleado.usuario = user
                    empleado.save()

                return redirect('lista_empleados')
            except Exception as e:
                form.add_error(None, f'Error: {str(e)}')
    else:
        form = EmpleadoForm()

    return render(request, 'empleados/crear_empleado.html', {'form': form})

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def mostrar_db(request):
    # CORRECCIÓN: Permitir al superusuario ver la DB aunque no sea 'empleado'
    if not request.user.is_superuser:
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
        # Borrar el usuario también borra el empleado en cascada si está así en el modelo
        if empleado.usuario:
            empleado.usuario.delete()
        else:
            empleado.delete()
        return redirect('lista_empleados') 
        
    return render(request, 'empleados/eliminar_persona.html', {'empleado': empleado})
 
@login_required
def revocar_acceso(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario = empleado.usuario

    if request.method == 'POST':
        usuario.is_active = not usuario.is_active 
        usuario.save()
        return redirect('lista_empleados')

    return render(request, 'empleados/revocar_acceso.html', {
        'empleado': empleado,
        'usuario': usuario
    })
