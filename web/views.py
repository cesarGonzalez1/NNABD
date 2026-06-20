from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.utils import timezone


from .models import (
    Empleado, Asentamiento, Municipio, NNA, Tutor,
    EquipoMultidisciplinario, SeguimientoNNA, BitacoraAcceso,
    HechoVictimal, PlanRestitucion, NNATutor,
)
from .forms import (
    EmpleadoForm, DomicilioForm, NNAForm, NNAProcesoForm, TutorForm,
    EquipoForm, SeguimientoNNAForm,
    HechoVictimalForm, ContactoNNAFormSet, IdiomaNNAFormSet,
    DiscapacidadNNAFormSet, PadecimientoNNAFormSet,
    DocumentoExpedienteFormSet, PlanRestitucionForm,
    DerechoVulneradoFormSet,
    ContactoTutorFormSet, ContactoEmpleadoFormSet,
    IdiomaTutorFormSet, IdiomaEmpleadoFormSet,
)

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


def _empleado_actual(user):
    try:
        return user.empleado
    except Empleado.DoesNotExist:
        return None


def _es_super_director_o_coordinador(user):
    if user.is_superuser:
        return True
    empleado = _empleado_actual(user)
    return bool(empleado and empleado.rol in ('director', 'coordinador'))


def _puede_gestionar_tutores(user):
    if _es_super_director_o_coordinador(user):
        return True
    empleado = _empleado_actual(user)
    return bool(empleado and empleado.rol == 'trabajador_social')


def _puede_gestionar_diagnosticos(user):
    """Los datos clínicos quedan reservados al rol médico (y superusuario)."""
    if user.is_superuser:
        return True
    empleado = _empleado_actual(user)
    return bool(empleado and empleado.rol == 'doctor')


def _puede_gestionar_datos_nna(user, nna):
    if _es_super_director_o_coordinador(user):
        return True
    empleado = _empleado_actual(user)
    return bool(
        empleado
        and empleado.rol == 'trabajador_social'
        and (
            nna.registrado_por_id == empleado.id
            or _empleado_en_equipo(empleado, nna.equipo)
        )
    )


def _area_para_rol(rol):
    return {
        'abogado': 'legal',
        'doctor': 'medica',
        'psicologo': 'psicologica',
        'trabajador_social': 'social',
    }.get(rol)


def _empleado_en_equipo(empleado, equipo):
    if not empleado or not equipo:
        return False
    return any([
        equipo.abogado_id == empleado.id,
        equipo.doctor_id == empleado.id,
        equipo.trabajador_social_id == empleado.id,
        equipo.psicologo_id == empleado.id,
        equipo.coordinador_id == empleado.id,
    ])


def _puede_ver_nna(user, nna):
    if _es_super_director_o_coordinador(user):
        return True
    empleado = _empleado_actual(user)
    if not empleado:
        return False
    if nna.registrado_por_id == empleado.id:
        return True
    return _empleado_en_equipo(empleado, nna.equipo)


def _registrar_consulta(request, modelo, objeto_id, nna=None, detalle=''):
    BitacoraAcceso.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        accion='consulta',
        modelo=modelo,
        objeto_id=str(objeto_id),
        nna=nna,
        ip=request.META.get('REMOTE_ADDR'),
        detalle=detalle[:255],
    )


def _sincronizar_tutor_principal(nna, tutor):
    if not tutor:
        return
    NNATutor.objects.update_or_create(
        nna=nna,
        tutor=tutor,
        defaults={
            'parentesco': tutor.parentesco_con_nna,
            'principal': True,
            'fecha_inicio': nna.fecha_ingreso,
        },
    )


def _domicilio_para_nna(form, dom_form):
    tutor = form.cleaned_data.get('tutor')
    if form.cleaned_data.get('vive_con_tutor') and tutor and tutor.domicilio:
        return tutor.domicilio
    return dom_form.guardar_domicilio()


def _puede_registrar_seguimiento(user, nna, area=None):
    if _es_super_director_o_coordinador(user):
        return True
    empleado = _empleado_actual(user)
    if not empleado:
        return False
    area_permitida = _area_para_rol(empleado.rol)
    if not area_permitida:
        return False
    if area and area != area_permitida:
        return False
    if nna.registrado_por_id == empleado.id and area_permitida == 'social':
        return True
    return _empleado_en_equipo(empleado, nna.equipo)


def _puede_editar_seguimiento(user, seguimiento):
    if _es_super_director_o_coordinador(user):
        return True
    empleado = _empleado_actual(user)
    return bool(empleado and seguimiento.registrado_por_id == empleado.id)


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
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("No tienes permiso para ver empleados.")
    empleado = get_object_or_404(
        Empleado.objects.prefetch_related('idiomas__lengua', 'idiomas__nivel_competencia'),
        id=empleado_id,
    )
    return render(request, 'empleados/consultar_empleado.html', {'empleado': empleado})


@login_required
def crear_empleado(request):
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("Solo el director puede crear empleados.")

    DOM_PREFIX = 'dom'

    if request.method == 'POST':
        form     = EmpleadoForm(request.POST)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)

        contacto_formset = ContactoEmpleadoFormSet(request.POST, prefix='contactos')
        idioma_formset = IdiomaEmpleadoFormSet(request.POST, prefix='idiomas')

        # Validamos ambos formularios juntos
        form_ok = form.is_valid()
        dom_ok  = dom_form.is_valid()
        cf_ok   = contacto_formset.is_valid()
        idiomas_ok = idioma_formset.is_valid()

        if form_ok and dom_ok and cf_ok and idiomas_ok:
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
                        contacto_formset.instance = empleado
                        contacto_formset.save()
                        idioma_formset.instance = empleado
                        idioma_formset.save()

                    return redirect('lista_empleados')
                except Exception as e:
                    form.add_error(None, f'Error inesperado: {e}')
    else:
        form     = EmpleadoForm()
        dom_form = DomicilioForm(prefix=DOM_PREFIX)
        contacto_formset = ContactoEmpleadoFormSet(prefix='contactos')
        idioma_formset = IdiomaEmpleadoFormSet(prefix='idiomas')

    return render(request, 'empleados/crear_empleado.html', {
        'form':     form,
        'dom_form': dom_form,
        'contacto_formset': contacto_formset,
        'idioma_formset': idioma_formset,
    })


@login_required
def editar_empleado(request, empleado_id):
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("Solo el director puede editar empleados.")
    empleado = get_object_or_404(Empleado, id=empleado_id)
    DOM_PREFIX = 'dom'

    if request.method == 'POST':
        form     = EmpleadoForm(request.POST, instance=empleado)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)
        idioma_formset = IdiomaEmpleadoFormSet(
            request.POST, instance=empleado, prefix='idiomas'
        )

        form_ok = form.is_valid()
        dom_ok  = dom_form.is_valid()
        idiomas_ok = idioma_formset.is_valid()

        if form_ok and dom_ok and idiomas_ok:
            try:
                with transaction.atomic():
                    # 1. Domicilio: actualizar si ya existe, crear si no
                    domicilio = dom_form.guardar_domicilio(empleado.domicilio)

                    # 2. Empleado
                    empleado           = form.save(commit=False)
                    empleado.domicilio = domicilio
                    empleado.save()
                    idioma_formset.save()

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
        idioma_formset = IdiomaEmpleadoFormSet(
            instance=empleado, prefix='idiomas'
        )

    return render(request, 'empleados/editar_empleado.html', {
        'form':     form,
        'dom_form': dom_form,
        'empleado': empleado,
        'idioma_formset': idioma_formset,
    })


@login_required
def eliminar_persona(request, empleado_id):
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("Solo el director puede eliminar empleados.")
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
    if not _es_director_o_super(request.user):
        return HttpResponseForbidden("Solo el director puede revocar accesos.")
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
        idioma_formset = IdiomaNNAFormSet(request.POST, prefix='idiomas')
        discapacidad_formset = DiscapacidadNNAFormSet(request.POST, prefix='discapacidades')

        ok = all([
            form.is_valid(), dom_form.is_valid(),
            idioma_formset.is_valid(), discapacidad_formset.is_valid(),
        ])

        if ok:
            try:
                with transaction.atomic():
                    domicilio = _domicilio_para_nna(form, dom_form)
                    nna               = form.save(commit=False)
                    nna.domicilio     = domicilio
                    if empleado_actual and empleado_actual.rol == 'trabajador_social':
                        nna.registrado_por = empleado_actual
                    nna.save()
                    _sincronizar_tutor_principal(nna, form.cleaned_data.get('tutor'))
                    for fs in (idioma_formset, discapacidad_formset):
                        fs.instance = nna
                        fs.save()
                return redirect('lista_nna')
            except Exception as e:
                form.add_error(None, f'Error inesperado: {e}')
    else:
        form     = NNAForm()
        dom_form = DomicilioForm(prefix=DOM_PREFIX)
        idioma_formset = IdiomaNNAFormSet(prefix='idiomas')
        discapacidad_formset = DiscapacidadNNAFormSet(prefix='discapacidades')

    return render(request, 'nna/crear_nna.html', {
        'form':     form,
        'dom_form': dom_form,
        'idioma_formset': idioma_formset,
        'discapacidad_formset': discapacidad_formset,
    })


@login_required
def lista_nna(request):
    nna_list = NNA.objects.select_related(
        'tutor', 'equipo', 'registrado_por', 'domicilio'
    )
    if not _es_super_director_o_coordinador(request.user):
        empleado = _empleado_actual(request.user)
        if empleado:
            nna_list = nna_list.filter(
                Q(registrado_por=empleado) |
                Q(equipo__abogado=empleado) |
                Q(equipo__doctor=empleado) |
                Q(equipo__trabajador_social=empleado) |
                Q(equipo__psicologo=empleado)
            )
        else:
            nna_list = NNA.objects.none()
    return render(request, 'nna/lista_nna.html', {'nna_list': nna_list})


@login_required
def detalle_nna(request, nna_id):
    nna = get_object_or_404(
        NNA.objects.select_related(
            'tutor', 'equipo',
            'equipo__abogado', 'equipo__doctor',
            'equipo__trabajador_social', 'equipo__psicologo',
            'equipo__coordinador',
            'registrado_por', 'domicilio',
            'lugar_nacimiento_estado', 'lugar_nacimiento_municipio',
        ),
        id=nna_id,
    )
    if not _puede_ver_nna(request.user, nna):
        return HttpResponseForbidden("No tienes permiso para ver este expediente.")
    _registrar_consulta(request, 'NNA', nna.id, nna=nna, detalle='Consulta de expediente integral')

    seguimientos = (
        nna.seguimientos
        .select_related('registrado_por')
        .order_by('-fecha', '-fecha_registro')
    )
    resumen_areas = {
        'social': 0,
        'medica': 0,
        'psicologica': 0,
        'legal': 0,
        'general': 0,
    }
    for seguimiento in seguimientos:
        resumen_areas[seguimiento.area] = resumen_areas.get(seguimiento.area, 0) + 1
    plan_vigente = (
        nna.planes_restitucion
        .filter(vigente=True)
        .prefetch_related('derechos_vulnerados__derecho', 'derechos_vulnerados__medidas')
        .first()
    )

    return render(request, 'nna/detalle_nna.html', {
        'nna': nna,
        'seguimientos': seguimientos,
        'resumen_areas': resumen_areas,
        'plan_vigente': plan_vigente,
        'puede_crear_seguimiento': _puede_registrar_seguimiento(request.user, nna),
        'puede_editar_expediente': _puede_registrar_seguimiento(request.user, nna),
        'puede_ver_diagnosticos': _puede_gestionar_diagnosticos(request.user),
    })


@login_required
def editar_expediente_nna(request, nna_id):
    nna = get_object_or_404(
        NNA.objects.select_related('equipo', 'registrado_por', 'tutor', 'domicilio'),
        id=nna_id,
    )
    if not _puede_registrar_seguimiento(request.user, nna):
        return HttpResponseForbidden("No tienes permiso para editar este expediente.")

    hecho = getattr(nna, 'hecho_victimal', None)
    plan_vigente = nna.planes_restitucion.filter(vigente=True).first()
    empleado = _empleado_actual(request.user)
    puede_gestionar_datos = _puede_gestionar_datos_nna(request.user, nna)
    puede_gestionar_diagnosticos = _puede_gestionar_diagnosticos(request.user)

    if request.method == 'POST':
        datos_proceso_enviados = puede_gestionar_datos and any(
            key.startswith('nna-') for key in request.POST
        )
        nna_proceso_form = NNAProcesoForm(
            request.POST, instance=nna, prefix='nna'
        ) if datos_proceso_enviados else (
            NNAProcesoForm(instance=nna, prefix='nna') if puede_gestionar_datos else None
        )
        hecho_form = HechoVictimalForm(request.POST, instance=hecho, prefix='fud')
        contacto_formset = ContactoNNAFormSet(request.POST, instance=nna, prefix='contactos')
        idioma_formset = IdiomaNNAFormSet(request.POST, instance=nna, prefix='idiomas')
        discapacidad_formset = DiscapacidadNNAFormSet(request.POST, instance=nna, prefix='discapacidades')
        padecimiento_formset = PadecimientoNNAFormSet(
            request.POST, instance=nna, prefix='padecimientos'
        ) if puede_gestionar_diagnosticos else None
        documento_formset = DocumentoExpedienteFormSet(
            request.POST, request.FILES, instance=nna, prefix='documentos'
        )
        plan_form = PlanRestitucionForm(request.POST, instance=plan_vigente, prefix='plan')
        derecho_formset = DerechoVulneradoFormSet(
            request.POST,
            instance=plan_vigente or PlanRestitucion(nna=nna),
            prefix='derechos',
        )

        fud_tiene_datos = any(
            request.POST.get(f'fud-{name}')
            for name in ('tipo_delito', 'descripcion_delito', 'nombre_victima_directa')
        ) or hecho is not None
        plan_tiene_datos = any(
            request.POST.get(f'plan-{name}')
            for name in ('folio', 'fecha_apertura', 'grado_peligro', 'grado_coercion')
        ) or plan_vigente is not None

        forms_validos = all([
            (not datos_proceso_enviados or nna_proceso_form.is_valid()),
            contacto_formset.is_valid(),
            idioma_formset.is_valid(),
            discapacidad_formset.is_valid(),
            (not puede_gestionar_diagnosticos or padecimiento_formset.is_valid()),
            documento_formset.is_valid(),
            (not fud_tiene_datos or hecho_form.is_valid()),
            (not plan_tiene_datos or plan_form.is_valid()),
            (not plan_tiene_datos or derecho_formset.is_valid()),
        ])

        if forms_validos:
            with transaction.atomic():
                if datos_proceso_enviados:
                    nna_proceso_form.save()

                if fud_tiene_datos:
                    hecho_obj = hecho_form.save(commit=False)
                    hecho_obj.nna = nna
                    if empleado and not hecho_obj.registrado_por_id:
                        hecho_obj.registrado_por = empleado
                    hecho_obj.save()

                contacto_formset.save()
                idioma_formset.save()
                discapacidad_formset.save()
                if puede_gestionar_diagnosticos:
                    diagnosticos = padecimiento_formset.save(commit=False)
                    for obj in padecimiento_formset.deleted_objects:
                        obj.delete()
                    for diagnostico in diagnosticos:
                        if empleado and empleado.rol == 'doctor':
                            diagnostico.diagnosticado_por = empleado
                        diagnostico.save()

                documentos = documento_formset.save(commit=False)
                for obj in documento_formset.deleted_objects:
                    obj.delete()
                for documento in documentos:
                    if empleado and not documento.subido_por_id:
                        documento.subido_por = empleado
                    documento.save()
                documento_formset.save_m2m()

                if plan_tiene_datos:
                    plan = plan_form.save(commit=False)
                    plan.nna = nna
                    if empleado and not plan.elaborado_por_id:
                        plan.elaborado_por = empleado
                    plan.save()
                    derecho_formset.instance = plan
                    derecho_formset.save()

            return redirect('detalle_nna', nna_id=nna.id)
    else:
        nna_proceso_form = NNAProcesoForm(
            instance=nna, prefix='nna'
        ) if puede_gestionar_datos else None
        hecho_form = HechoVictimalForm(instance=hecho, prefix='fud')
        contacto_formset = ContactoNNAFormSet(instance=nna, prefix='contactos')
        idioma_formset = IdiomaNNAFormSet(instance=nna, prefix='idiomas')
        discapacidad_formset = DiscapacidadNNAFormSet(instance=nna, prefix='discapacidades')
        padecimiento_formset = PadecimientoNNAFormSet(
            instance=nna, prefix='padecimientos'
        ) if puede_gestionar_diagnosticos else None
        documento_formset = DocumentoExpedienteFormSet(instance=nna, prefix='documentos')
        derecho_formset = DerechoVulneradoFormSet(
            instance=plan_vigente or PlanRestitucion(nna=nna),
            prefix='derechos',
        )
        plan_form = PlanRestitucionForm(
            instance=plan_vigente,
            prefix='plan',
            initial={
                'folio': f'PR-{nna.folio_nna or nna.id}',
                'fecha_apertura': timezone.localdate(),
                'equipo': nna.equipo,
            } if plan_vigente is None else None,
        )

    return render(request, 'nna/editar_expediente.html', {
        'nna': nna,
        'nna_proceso_form': nna_proceso_form,
        'hecho_form': hecho_form,
        'contacto_formset': contacto_formset,
        'idioma_formset': idioma_formset,
        'discapacidad_formset': discapacidad_formset,
        'padecimiento_formset': padecimiento_formset,
        'documento_formset': documento_formset,
        'plan_form': plan_form,
        'derecho_formset': derecho_formset,
        'puede_gestionar_datos': puede_gestionar_datos,
        'puede_gestionar_diagnosticos': puede_gestionar_diagnosticos,
    })


@login_required
def crear_seguimiento_nna(request, nna_id):
    nna = get_object_or_404(NNA.objects.select_related('equipo', 'registrado_por'), id=nna_id)
    if not _puede_ver_nna(request.user, nna):
        return HttpResponseForbidden("No tienes permiso para ver este expediente.")
    if not _puede_registrar_seguimiento(request.user, nna):
        return HttpResponseForbidden("No tienes permiso para registrar seguimientos.")

    if request.method == 'POST':
        form = SeguimientoNNAForm(request.POST, user=request.user)
        if form.is_valid():
            area = form.cleaned_data['area']
            if not _puede_registrar_seguimiento(request.user, nna, area):
                return HttpResponseForbidden("No tienes permiso para registrar seguimientos en esta área.")
            seguimiento = form.save(commit=False)
            seguimiento.nna = nna
            seguimiento.registrado_por = _empleado_actual(request.user)
            seguimiento.save()
            return redirect('detalle_nna', nna_id=nna.id)
    else:
        form = SeguimientoNNAForm(
            user=request.user,
            initial={'fecha': timezone.localdate()},
        )

    return render(request, 'seguimientos/crear_seguimiento.html', {
        'form': form,
        'nna': nna,
    })


@login_required
def detalle_seguimiento_nna(request, seguimiento_id):
    seguimiento = get_object_or_404(
        SeguimientoNNA.objects.select_related('nna', 'nna__equipo', 'registrado_por'),
        id=seguimiento_id,
    )
    if not _puede_ver_nna(request.user, seguimiento.nna):
        return HttpResponseForbidden("No tienes permiso para ver este seguimiento.")

    return render(request, 'seguimientos/detalle_seguimiento.html', {
        'seguimiento': seguimiento,
        'puede_editar': _puede_editar_seguimiento(request.user, seguimiento),
        'puede_eliminar': _es_super_director_o_coordinador(request.user),
    })


@login_required
def editar_seguimiento_nna(request, seguimiento_id):
    seguimiento = get_object_or_404(
        SeguimientoNNA.objects.select_related('nna', 'nna__equipo', 'registrado_por'),
        id=seguimiento_id,
    )
    if not _puede_ver_nna(request.user, seguimiento.nna):
        return HttpResponseForbidden("No tienes permiso para ver este seguimiento.")
    if not _puede_editar_seguimiento(request.user, seguimiento):
        return HttpResponseForbidden("No tienes permiso para editar este seguimiento.")

    if request.method == 'POST':
        form = SeguimientoNNAForm(request.POST, instance=seguimiento, user=request.user)
        if form.is_valid():
            area = form.cleaned_data['area']
            if not _puede_registrar_seguimiento(request.user, seguimiento.nna, area):
                return HttpResponseForbidden("No tienes permiso para registrar seguimientos en esta área.")
            form.save()
            return redirect('detalle_seguimiento_nna', seguimiento_id=seguimiento.id)
    else:
        form = SeguimientoNNAForm(instance=seguimiento, user=request.user)

    return render(request, 'seguimientos/editar_seguimiento.html', {
        'form': form,
        'seguimiento': seguimiento,
        'nna': seguimiento.nna,
    })


@login_required
def eliminar_seguimiento_nna(request, seguimiento_id):
    seguimiento = get_object_or_404(
        SeguimientoNNA.objects.select_related('nna', 'nna__equipo', 'registrado_por'),
        id=seguimiento_id,
    )
    if not _puede_ver_nna(request.user, seguimiento.nna):
        return HttpResponseForbidden("No tienes permiso para ver este seguimiento.")
    if not _es_super_director_o_coordinador(request.user):
        return HttpResponseForbidden("Solo dirección o coordinación puede eliminar seguimientos.")

    nna_id = seguimiento.nna_id
    if request.method == 'POST':
        seguimiento.delete()
        return redirect('detalle_nna', nna_id=nna_id)

    return render(request, 'seguimientos/eliminar_seguimiento.html', {
        'seguimiento': seguimiento,
        'nna': seguimiento.nna,
    })

# ─────────────────────────────────────────────────────────────────────────────
# TUTOR
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def lista_tutores(request):
    if not _puede_gestionar_tutores(request.user):
        return HttpResponseForbidden("No tienes permiso para consultar tutores.")
    tutores = Tutor.objects.select_related('domicilio').prefetch_related(
        'idiomas__lengua', 'idiomas__nivel_competencia'
    ).order_by(
        'apellido_paterno', 'nombre'
    )
    return render(request, 'tutor/lista_tutores.html', {'tutores': tutores})


@login_required
def crear_tutor(request):
    if not _puede_gestionar_tutores(request.user):
        return HttpResponseForbidden("No tienes permiso para registrar tutores.")
    DOM_PREFIX = 'dom'

    if request.method == 'POST':
        form     = TutorForm(request.POST)
        dom_form = DomicilioForm(request.POST, prefix=DOM_PREFIX)
        contacto_formset = ContactoTutorFormSet(request.POST, prefix='contactos')
        idioma_formset = IdiomaTutorFormSet(request.POST, prefix='idiomas')

        ok = all([
            form.is_valid(), dom_form.is_valid(), contacto_formset.is_valid(),
            idioma_formset.is_valid(),
        ])

        if ok:
            try:
                with transaction.atomic():
                    domicilio        = dom_form.guardar_domicilio()
                    tutor            = form.save(commit=False)
                    tutor.domicilio  = domicilio
                    tutor.save()
                    contacto_formset.instance = tutor
                    contacto_formset.save()
                    idioma_formset.instance = tutor
                    idioma_formset.save()
                return redirect('lista_tutores')
            except Exception as e:
                form.add_error(None, f'Error inesperado: {e}')
    else:
        form     = TutorForm()
        dom_form = DomicilioForm(prefix=DOM_PREFIX)
        contacto_formset = ContactoTutorFormSet(prefix='contactos')
        idioma_formset = IdiomaTutorFormSet(prefix='idiomas')

    return render(request, 'tutor/crear_tutor.html', {
        'form':     form,
        'dom_form': dom_form,
        'contacto_formset': contacto_formset,
        'idioma_formset': idioma_formset,
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
