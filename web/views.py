from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction


from .models import Empleado, Asentamiento, Municipio, NNA, Tutor, EquipoMultidisciplinario
from .forms import EmpleadoForm, DomicilioForm, NNAForm, TutorForm, EquipoForm

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _es_director_o_super(user):
    if user.is_superuser:
        return True
    try:
        return user.empleado.rol == 'director'
    except Empleado.DoesNotExist:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# AUTH / HOME
# ─────────────────────────────────────────────────────────────────────────────

def login_view(request):
    return render(request, 'registration/login.html')


@login_required
def home(request):
    return render(request, 'home.html')


# ─────────────────────────────────────────────────────────────────────────────
# API: búsqueda de asentamientos por C.P. (AJAX)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def api_asentamientos(request):
    """Devuelve JSON con los asentamientos que coinciden con un C.P."""
    cp = request.GET.get('cp', '').strip()
    data = []
    if cp:
        qs = (
            Asentamiento.objects
            .filter(codigo_postal=cp)
            .select_related('municipio__entidad')
            .order_by('nombre')
        )
        data = [
            {
                'id':        a.id,
                'nombre':    a.nombre,
                'municipio': a.municipio.nombre,
                'estado':    a.municipio.entidad.nombre,
            }
            for a in qs
        ]
    return JsonResponse({'asentamientos': data})


@login_required
def api_municipios(request):
    """Devuelve JSON con los municipios de un estado (para NNA)."""
    estado_id = request.GET.get('estado_id', '').strip()
    data = []
    if estado_id:
        qs = Municipio.objects.filter(entidad_id=estado_id).order_by('nombre')
        data = [{'id': m.id, 'nombre': m.nombre} for m in qs]
    return JsonResponse({'municipios': data})


# ─────────────────────────────────────────────────────────────────────────────
# EMPLEADOS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def mostrar_db(request):
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    empleados = Empleado.objects.select_related('usuario', 'domicilio').all()
    return render(request, 'empleados/mostrar_db.html', {'lista_empleados': empleados})


@login_required
def consultar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    return render(request, 'empleados/consultar_empleado.html', {'empleado': empleado})


@login_required
def crear_empleado(request):
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("Solo el director puede crear empleados.")

    DOM_PREFIX = 'dom'

    if request.method == 'POST':
        form     = EmpleadoForm(request.POST)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        # Validamos ambos formularios juntos
        form_ok = form.is_valid()
        dom_ok  = dom_form.is_valid()

        if form_ok and dom_ok:
            rfc      = form.cleaned_data['rfc']
            password = form.cleaned_data['password']

            if not password:
                form.add_error('password', 'La contraseña es obligatoria al crear un empleado.')
            elif User.objects.filter(username=rfc).exists():
                form.add_error(None, 'Ya existe un empleado con este RFC registrado.')
            else:
                try:
                    with transaction.atomic():
                        # 1. Domicilio (opcional: si el usuario no llenó CP, queda None)
                        domicilio = dom_form.guardar_domicilio()

                        # 2. Usuario Django (RFC como username)
                        user = User.objects.create_user(username=rfc, password=password)
                        user.is_active = form.cleaned_data['estatus'] == 'True'
                        user.save()

                        # 3. Empleado
                        empleado          = form.save(commit=False)
                        empleado.usuario  = user
                        empleado.domicilio = domicilio
                        empleado.save()

                    return redirect('lista_empleados')
                except Exception as e:
                    form.add_error(None, f'Error inesperado: {e}')
    else:
        form     = EmpleadoForm()
        dom_form = DomicilioForm(prefix=DOM_PREFIX)

    return render(request, 'empleados/crear_empleado.html', {
        'form':     form,
        'dom_form': dom_form,
    })


@login_required
def editar_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    DOM_PREFIX = 'dom'

    if request.method == 'POST':
        form     = EmpleadoForm(request.POST, instance=empleado)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        form_ok = form.is_valid()
        dom_ok  = dom_form.is_valid()

        if form_ok and dom_ok:
            try:
                with transaction.atomic():
                    # 1. Domicilio: actualizar si ya existe, crear si no
                    domicilio = dom_form.guardar_domicilio(empleado.domicilio)

                    # 2. Empleado
                    empleado           = form.save(commit=False)
                    empleado.domicilio = domicilio
                    empleado.save()

                    # 3. Usuario
                    user = empleado.usuario
                    user.is_active = form.cleaned_data['estatus'] == 'True'
                    if form.cleaned_data['password']:
                        user.set_password(form.cleaned_data['password'])
                    user.save()

                return redirect('consultar_empleado', empleado_id=empleado.id)
            except Exception as e:
                form.add_error(None, f'Error inesperado: {e}')
    else:
        form     = EmpleadoForm(
            instance=empleado,
            initial={'estatus': str(empleado.usuario.is_active)},
        )
        dom_form = DomicilioForm.desde_domicilio(empleado.domicilio, prefix=DOM_PREFIX)

    return render(request, 'empleados/editar_empleado.html', {
        'form':     form,
        'dom_form': dom_form,
        'empleado': empleado,
    })


@login_required
def eliminar_persona(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    if request.method == 'POST':
        if empleado.usuario:
            empleado.usuario.delete()  # Borra en cascada al empleado
        else:
            empleado.delete()
        return redirect('lista_empleados')
    return render(request, 'empleados/eliminar_persona.html', {'empleado': empleado})


@login_required
def revocar_acceso(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario  = empleado.usuario
    if request.method == 'POST':
        usuario.is_active = not usuario.is_active
        usuario.save()
        return redirect('lista_empleados')
    return render(request, 'empleados/revocar_acceso.html', {
        'empleado': empleado,
        'usuario':  usuario,
    })


# ─────────────────────────────────────────────────────────────────────────────
# NNA — Niña, Niño o Adolescente
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def crear_nna(request):
    """
    Solo el trabajador social del equipo (o el director/superusuario) puede
    registrar un NNA. El campo 'registrado_por' se asigna automáticamente.
    """
    # Verificar que el usuario sea trabajador social, director o superusuario
    es_autorizado = request.user.is_superuser
    empleado_actual = None
    if not es_autorizado:
        try:
            empleado_actual = request.user.empleado
            es_autorizado = empleado_actual.rol in ('trabajador_social', 'director')
        except Empleado.DoesNotExist:
            pass

    if not es_autorizado:
        return HttpResponseForbidden(
            "Solo el Trabajador Social o el Director pueden registrar NNA."
        )

    DOM_PREFIX = 'dom'

    if request.method == 'POST':
        form     = NNAForm(request.POST)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        form_ok = form.is_valid()
        dom_ok  = dom_form.is_valid()

        if form_ok and dom_ok:
            try:
                with transaction.atomic():
                    # 1. Domicilio (opcional)
                    domicilio = dom_form.guardar_domicilio()

                    # 2. NNA
                    nna               = form.save(commit=False)
                    nna.domicilio     = domicilio
                    # Asignar registrado_por al empleado actual si aplica
                    if empleado_actual and empleado_actual.rol == 'trabajador_social':
                        nna.registrado_por = empleado_actual
                    nna.save()

                return redirect('lista_nna')
            except Exception as e:
                form.add_error(None, f'Error inesperado: {e}')
    else:
        form     = NNAForm()
        dom_form = DomicilioForm(prefix=DOM_PREFIX)

    return render(request, 'nna/crear_nna.html', {
        'form':     form,
        'dom_form': dom_form,
    })


@login_required
def lista_nna(request):
    nna_list = NNA.objects.select_related(
        'tutor', 'equipo', 'registrado_por', 'domicilio'
    ).all()
    return render(request, 'nna/lista_nna.html', {'nna_list': nna_list})

# ─────────────────────────────────────────────────────────────────────────────
# TUTOR
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def lista_tutores(request):
    tutores = Tutor.objects.select_related('domicilio').order_by(
        'apellido_paterno', 'nombre'
    )
    return render(request, 'tutor/lista_tutores.html', {'tutores': tutores})


@login_required
def crear_tutor(request):
    DOM_PREFIX = 'dom'

    if request.method == 'POST':
        form     = TutorForm(request.POST)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        form_ok = form.is_valid()
        dom_ok  = dom_form.is_valid()

        if form_ok and dom_ok:
            try:
                with transaction.atomic():
                    domicilio        = dom_form.guardar_domicilio()
                    tutor            = form.save(commit=False)
                    tutor.domicilio  = domicilio
                    tutor.save()
                return redirect('lista_tutores')
            except Exception as e:
                form.add_error(None, f'Error inesperado: {e}')
    else:
        form     = TutorForm()
        dom_form = DomicilioForm(prefix=DOM_PREFIX)

    return render(request, 'tutor/crear_tutor.html', {
        'form':     form,
        'dom_form': dom_form,
    })


# ─────────────────────────────────────────────────────────────────────────────
# EQUIPO MULTIDISCIPLINARIO
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def lista_equipos(request):
    equipos = EquipoMultidisciplinario.objects.select_related(
        'abogado', 'doctor', 'trabajador_social', 'psicologo', 'coordinador'
    ).order_by('nombre')
    return render(request, 'equipo/lista_equipos.html', {'equipos': equipos})


@login_required
def crear_equipo(request):
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("Solo el director puede crear equipos.")

    if request.method == 'POST':
        form = EquipoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                return redirect('lista_equipos')
            except Exception as e:
                form.add_error(None, f'Error inesperado: {e}')
    else:
        form = EquipoForm()

    return render(request, 'equipo/crear_equipo.html', {'form': form})
