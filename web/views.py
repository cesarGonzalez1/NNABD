"""
web/views.py — Vistas principales del sistema SIGA-NNA.

Convenciones:
  · Cada vista tiene un docstring que describe su propósito y permisos.
  · El acceso por rol se controla mediante el decorador ``director_requerido``
    o con verificación explícita dentro de la vista (ej. ``crear_nna``).
  · El patrón transaccional «formulario + domicilio opcional» se centraliza
    en el helper ``_guardar_con_domicilio`` para evitar duplicación.
"""

from functools import wraps

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .forms import DomicilioForm, EmpleadoForm, EquipoForm, NNAForm, TutorForm
from .models import (
    Asentamiento,
    Empleado,
    EquipoMultidisciplinario,
    Municipio,
    NNA,
    Tutor,
)

DOM_PREFIX = 'dom'

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS / DECORADORES
# ─────────────────────────────────────────────────────────────────────────────


def _es_director_o_super(user):
    """Retorna True si el usuario es superusuario o tiene rol de director."""
    if user.is_superuser:
        return True
    try:
        return user.empleado.rol == 'director'
    except Empleado.DoesNotExist:
        return False


def director_requerido(vista):
    """Decorador que restringe el acceso a directores y superusuarios."""
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if not _es_director_o_super(request.user):
            return HttpResponseForbidden(
                "Solo el director puede acceder a esta sección."
            )
        return vista(request, *args, **kwargs)
    return wrapper


def _guardar_con_domicilio(request, form_class, template, redirect_url,
                           domicilio_existente=None, extra_context=None,
                           pre_save=None, post_save=None, instance=None):
    """
    Patrón reutilizable para vistas que crean/editan un modelo con domicilio.

    Parámetros
    ----------
    form_class : ModelForm
        Formulario principal del modelo.
    template : str
        Ruta del template a renderizar.
    redirect_url : str
        Nombre de la URL a la que redirigir tras guardar exitosamente.
    domicilio_existente : Domicilio | None
        Instancia existente del domicilio para edición.
    extra_context : dict | None
        Contexto adicional para el template.
    pre_save : callable | None
        Función ``(obj, request) -> obj`` que se ejecuta antes de ``save()``.
    post_save : callable | None
        Función ``(obj, request) -> redirect_args`` para personalizar la
        redirección (ej. pasar el ID del objeto recién creado).
    instance : Model | None
        Instancia existente para edición.
    """
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance) if instance else form_class(request.POST)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        if form.is_valid() and dom_form.is_valid():
            try:
                with transaction.atomic():
                    domicilio = dom_form.guardar_domicilio(domicilio_existente)
                    obj = form.save(commit=False)
                    obj.domicilio = domicilio
                    if pre_save:
                        obj = pre_save(obj, request)
                    obj.save()
                if post_save:
                    return redirect(redirect_url, **post_save(obj, request))
                return redirect(redirect_url)
            except IntegrityError as e:
                form.add_error(None, f'Error de integridad en la base de datos: {e}')
    else:
        form = form_class(instance=instance) if instance else form_class()
        if domicilio_existente:
            dom_form = DomicilioForm.desde_domicilio(domicilio_existente, prefix=DOM_PREFIX)
        else:
            dom_form = DomicilioForm(prefix=DOM_PREFIX)

    context = {'form': form, 'dom_form': dom_form}
    if extra_context:
        context.update(extra_context)
    return render(request, template, context)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH / HOME
# ─────────────────────────────────────────────────────────────────────────────

def login_view(request):
    """Muestra la página de inicio de sesión."""
    return render(request, 'registration/login.html')


@login_required
def home(request):
    """Panel principal — accesos rápidos según el rol del usuario."""
    return render(request, 'home.html')


# ─────────────────────────────────────────────────────────────────────────────
# API: búsqueda de asentamientos y municipios (AJAX)
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
    """Devuelve JSON con los municipios de un estado (para select dinámico)."""
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
@director_requerido
def lista_empleados(request):
    """Lista todos los empleados. Solo director o superusuario."""
    empleados = Empleado.objects.select_related('usuario', 'domicilio').all()
    return render(request, 'empleados/mostrar_db.html', {'lista_empleados': empleados})


@login_required
def consultar_empleado(request, empleado_id):
    """Detalle de un empleado específico."""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    return render(request, 'empleados/consultar_empleado.html', {'empleado': empleado})


@login_required
@director_requerido
def crear_empleado(request):
    """Crea un nuevo empleado con su usuario Django (RFC como username)."""
    if request.method == 'POST':
        form     = EmpleadoForm(request.POST)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        if form.is_valid() and dom_form.is_valid():
            rfc      = form.cleaned_data['rfc']
            password = form.cleaned_data['password']

            if not password:
                form.add_error('password', 'La contraseña es obligatoria al crear un empleado.')
            elif User.objects.filter(username=rfc).exists():
                form.add_error(None, 'Ya existe un empleado con este RFC registrado.')
            else:
                try:
                    with transaction.atomic():
                        domicilio = dom_form.guardar_domicilio()
                        user = User.objects.create_user(username=rfc, password=password)
                        user.is_active = form.cleaned_data['estatus'] == 'True'
                        user.save()

                        empleado           = form.save(commit=False)
                        empleado.usuario   = user
                        empleado.domicilio = domicilio
                        empleado.save()

                    return redirect('lista_empleados')
                except IntegrityError as e:
                    form.add_error(None, f'Error de integridad: {e}')
    else:
        form     = EmpleadoForm()
        dom_form = DomicilioForm(prefix=DOM_PREFIX)

    return render(request, 'empleados/crear_empleado.html', {
        'form':     form,
        'dom_form': dom_form,
    })


@login_required
def editar_empleado(request, empleado_id):
    """Edita datos de un empleado existente, incluyendo domicilio y contraseña."""
    empleado = get_object_or_404(Empleado, id=empleado_id)

    if request.method == 'POST':
        form     = EmpleadoForm(request.POST, instance=empleado)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        if form.is_valid() and dom_form.is_valid():
            try:
                with transaction.atomic():
                    domicilio = dom_form.guardar_domicilio(empleado.domicilio)

                    empleado           = form.save(commit=False)
                    empleado.domicilio = domicilio
                    empleado.save()

                    user = empleado.usuario
                    user.is_active = form.cleaned_data['estatus'] == 'True'
                    if form.cleaned_data['password']:
                        user.set_password(form.cleaned_data['password'])
                    user.save()

                return redirect('consultar_empleado', empleado_id=empleado.id)
            except IntegrityError as e:
                form.add_error(None, f'Error de integridad: {e}')
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
def eliminar_empleado(request, empleado_id):
    """Elimina un empleado y su usuario Django asociado."""
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
    """Activa/desactiva el acceso de un empleado al sistema."""
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
    Registra un nuevo NNA.

    Solo el trabajador social (o director/superusuario) puede registrar.
    El campo ``registrado_por`` se asigna automáticamente al empleado actual
    si éste tiene rol de trabajador social.
    """
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

    def _asignar_registrador(nna, request):
        """Pre-save: asigna el trabajador social que registra al NNA."""
        if empleado_actual and empleado_actual.rol == 'trabajador_social':
            nna.registrado_por = empleado_actual
        return nna

    return _guardar_con_domicilio(
        request,
        form_class=NNAForm,
        template='nna/crear_nna.html',
        redirect_url='lista_nna',
        pre_save=_asignar_registrador,
    )


@login_required
def lista_nna(request):
    """Lista todos los NNA registrados en el sistema."""
    nna_list = NNA.objects.select_related(
        'tutor', 'equipo', 'registrado_por', 'domicilio'
    ).all()
    return render(request, 'nna/lista_nna.html', {'nna_list': nna_list})


# ─────────────────────────────────────────────────────────────────────────────
# TUTOR
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def lista_tutores(request):
    """Lista todos los tutores registrados."""
    tutores = Tutor.objects.select_related('domicilio').order_by(
        'apellido_paterno', 'nombre'
    )
    return render(request, 'tutor/lista_tutores.html', {'tutores': tutores})


@login_required
def crear_tutor(request):
    """Registra un nuevo tutor con domicilio opcional."""
    return _guardar_con_domicilio(
        request,
        form_class=TutorForm,
        template='tutor/crear_tutor.html',
        redirect_url='lista_tutores',
    )


# ─────────────────────────────────────────────────────────────────────────────
# EQUIPO MULTIDISCIPLINARIO
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def lista_equipos(request):
    """Lista todos los equipos multidisciplinarios."""
    equipos = EquipoMultidisciplinario.objects.select_related(
        'abogado', 'doctor', 'trabajador_social', 'psicologo', 'coordinador'
    ).order_by('nombre')
    return render(request, 'equipo/lista_equipos.html', {'equipos': equipos})


@login_required
@director_requerido
def crear_equipo(request):
    """Crea un nuevo equipo multidisciplinario. Solo director o superusuario."""
    if request.method == 'POST':
        form = EquipoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                return redirect('lista_equipos')
            except IntegrityError as e:
                form.add_error(None, f'Error de integridad: {e}')
    else:
        form = EquipoForm()

    return render(request, 'equipo/crear_equipo.html', {'form': form})
