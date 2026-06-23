from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import (
    Empleado, Domicilio, Asentamiento, Sexo,
    NNA, EntidadFederativa, Municipio,
    Tutor, EquipoMultidisciplinario, SeguimientoNNA,
    ContactoNNA, IdiomaNNA, IdiomaTutor, IdiomaEmpleado,
    DiscapacidadNNA, PadecimientoNNA,
    ContactoTutor, ContactoEmpleado,
    HechoVictimal, DocumentoExpediente, PlanRestitucion,
    DerechoVulnerado,
)


# ─────────────────────────────────────────────────────────────────────────────
# FORMULARIO DE DOMICILIO (reutilizable para Empleado, NNA y Tutor)
# ─────────────────────────────────────────────────────────────────────────────

class DomicilioForm(forms.Form):
    cp = forms.CharField(
        max_length=5, label='Código Postal', required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '00000', 'maxlength': '5',
            'class': 'form-control cp-input',
        }),
    )
    asentamiento = forms.ModelChoiceField(
        queryset=Asentamiento.objects.none(),
        label='Colonia / Asentamiento', required=False,
        empty_label='— Ingresa el C.P. primero —',
        widget=forms.Select(attrs={'class': 'form-select asentamiento-select'}),
    )
    calle = forms.CharField(
        max_length=200, label='Calle', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    numero_exterior = forms.CharField(
        max_length=20, label='Número exterior', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    numero_interior = forms.CharField(
        max_length=20, label='Número interior', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    referencias = forms.CharField(
        label='Referencias', required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Entre calles u otras referencias',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Repoblar queryset del asentamiento en POST para que valide bien
        cp_key = self.add_prefix('cp')
        cp_val = (self.data or {}).get(cp_key, '').strip()
        if cp_val:
            self.fields['asentamiento'].queryset = (
                Asentamiento.objects
                .filter(codigo_postal=cp_val)
                .select_related('municipio__entidad')
            )
        elif self.initial.get('asentamiento'):
            obj = self.initial['asentamiento']
            if isinstance(obj, Asentamiento):
                self.fields['asentamiento'].queryset = (
                    Asentamiento.objects
                    .filter(codigo_postal=obj.codigo_postal)
                    .select_related('municipio__entidad')
                )

    def tiene_datos(self):
        datos = getattr(self, 'cleaned_data', {})
        return bool(datos.get('asentamiento') or datos.get('calle'))

    def guardar_domicilio(self, domicilio_existente=None):
        """Crea o actualiza el Domicilio. Retorna None si no hay datos."""
        if not self.tiene_datos():
            return domicilio_existente
        asentamiento = self.cleaned_data.get('asentamiento')
        if not asentamiento:
            return domicilio_existente
        data = {
            'asentamiento':    asentamiento,
            'calle':           self.cleaned_data.get('calle', ''),
            'numero_exterior': self.cleaned_data.get('numero_exterior', ''),
            'numero_interior': self.cleaned_data.get('numero_interior', ''),
            'referencias':     self.cleaned_data.get('referencias', ''),
        }
        if domicilio_existente:
            for attr, val in data.items():
                setattr(domicilio_existente, attr, val)
            domicilio_existente.save()
            return domicilio_existente
        return Domicilio.objects.create(**data)

    @classmethod
    def desde_domicilio(cls, domicilio, prefix='dom'):
        if domicilio is None:
            return cls(prefix=prefix)
        return cls(
            prefix=prefix,
            initial={
                'cp':              domicilio.asentamiento.codigo_postal,
                'asentamiento':    domicilio.asentamiento,
                'calle':           domicilio.calle,
                'numero_exterior': domicilio.numero_exterior,
                'numero_interior': domicilio.numero_interior,
                'referencias':     domicilio.referencias,
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# EMPLEADO
# ─────────────────────────────────────────────────────────────────────────────

class EmpleadoForm(forms.ModelForm):
    estatus = forms.ChoiceField(
        choices=[('True', 'Activo'), ('False', 'Inactivo')],
        widget=forms.RadioSelect(),
        required=True,
        label='Estatus',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'readonly': True, 'onfocus': "this.removeAttribute('readonly')", 'data-lpignore': 'true', 'data-1p-ignore': ''}),
        label='Contraseña',
        required=False,
    )

    class Meta:
        model = Empleado
        # 'domicilio' se maneja con DomicilioForm independiente
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'rfc', 'curp', 'sexo_catalogo', 'fecha_nacimiento',
            'tipo_trabajador', 'rol', 'cedula_profesional', 'telefono',
        ]
        widgets = {
            'fecha_nacimiento':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno':  forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno':  forms.TextInput(attrs={'class': 'form-control'}),
            'rfc':               forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13', 'autocomplete': 'off', 'readonly': True, 'onfocus': "this.removeAttribute('readonly')", 'data-lpignore': 'true'}),
            'curp':              forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18', 'autocomplete': 'off'}),
            'sexo_catalogo':     forms.Select(attrs={'class': 'form-select'}),
            'tipo_trabajador':   forms.Select(attrs={'class': 'form-select'}),
            'rol':               forms.Select(attrs={'class': 'form-select'}),
            'cedula_profesional': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'readonly': True, 'onfocus': "this.removeAttribute('readonly')", 'data-lpignore': 'true'}),
            'telefono':          forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# NNA — Niña, Niño o Adolescente
# ─────────────────────────────────────────────────────────────────────────────

class NNAForm(forms.ModelForm):
    lugar_nacimiento_estado = forms.ModelChoiceField(
        queryset=EntidadFederativa.objects.all().order_by('nombre'),
        label='Estado de nacimiento', required=False,
        empty_label='— Selecciona estado —',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_estado_nac'}),
    )
    lugar_nacimiento_municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.none(),
        label='Municipio de nacimiento', required=False,
        empty_label='— Selecciona municipio —',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_municipio_nac'}),
    )
    tutor = forms.ModelChoiceField(
        queryset=Tutor.objects.all().order_by('apellido_paterno', 'nombre'),
        label='Tutor principal', required=False,
        empty_label='— Sin tutor —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = NNA
        # domicilio y registrado_por se asignan en la vista
        # tutor se maneja como campo explícito (no FK en el modelo — 5FN usa NNATutor)
        fields = [
            'folio_nna', 'nombre', 'nombre_preferido',
            'apellido_paterno', 'apellido_materno',
            'fecha_nacimiento', 'sexo_catalogo', 'curp',
            'escolaridad', 'nombre_escuela',
            'lugar_nacimiento_estado', 'lugar_nacimiento_municipio',
            'es_extranjero', 'pais_origen',
            'condicion_migratoria', 'pais_destino',
            'pertenece_comunidad_indigena', 'comunidad_indigena',
            'situacion_calle', 'requiere_interprete', 'lengua_interprete',
            'vive_con_tutor', 'equipo',
            'estatus', 'estatus_proceso', 'fecha_ingreso',
            'observaciones_generales',
        ]
        widgets = {
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_preferido':  forms.TextInput(attrs={'class': 'form-control'}),
            'folio_nna':         forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno':  forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno':  forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sexo_catalogo':     forms.Select(attrs={'class': 'form-select'}),
            'curp':              forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18', 'autocomplete': 'off'}),
            'escolaridad':       forms.Select(attrs={'class': 'form-select'}),
            'nombre_escuela':    forms.TextInput(attrs={'class': 'form-control'}),
            'es_extranjero':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pais_origen':       forms.TextInput(attrs={'class': 'form-control'}),
            'condicion_migratoria': forms.Select(attrs={'class': 'form-select'}),
            'pais_destino':      forms.TextInput(attrs={'class': 'form-control'}),
            'pertenece_comunidad_indigena': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comunidad_indigena': forms.TextInput(attrs={'class': 'form-control'}),
            'situacion_calle':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_interprete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lengua_interprete': forms.TextInput(attrs={'class': 'form-control'}),
            'vive_con_tutor':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'equipo':            forms.Select(attrs={'class': 'form-select'}),
            'estatus':           forms.Select(attrs={'class': 'form-select'}),
            'estatus_proceso':   forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso':     forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones_generales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Compatibilidad con altas anteriores a la incorporación del flujo.
        self.fields['estatus_proceso'].required = False
        # Repoblar municipios según estado seleccionado
        estado_id = None
        if self.data.get('lugar_nacimiento_estado'):
            estado_id = self.data.get('lugar_nacimiento_estado')
        elif self.instance.pk and self.instance.lugar_nacimiento_estado_id:
            estado_id = self.instance.lugar_nacimiento_estado_id
        if estado_id:
            self.fields['lugar_nacimiento_municipio'].queryset = (
                Municipio.objects.filter(entidad_id=estado_id).order_by('nombre')
            )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('es_extranjero') and not cleaned.get('pais_origen'):
            self.add_error('pais_origen', 'Indica el pais de origen cuando el NNA es extranjero.')
        return cleaned

    def clean_estatus_proceso(self):
        return self.cleaned_data.get('estatus_proceso') or 'ingreso'


class NNAProcesoForm(forms.ModelForm):
    """Edición acotada de identidad de uso y estado del expediente."""

    # Campo no-modelo para cambiar tutor principal (igual que en NNAForm)
    tutor = forms.ModelChoiceField(
        queryset=Tutor.objects.all().order_by('apellido_paterno', 'nombre'),
        label='Tutor principal', required=False,
        empty_label='— Sin tutor —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    motivo_cambio_equipo = forms.CharField(
        required=False, label='Motivo del cambio (equipo)',
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Opcional — razón del cambio de equipo'}),
    )

    class Meta:
        model = NNA
        fields = [
            'nombre_preferido', 'estatus', 'estatus_proceso',
            'equipo', 'fecha_egreso', 'observaciones_generales',
        ]
        widgets = {
            'nombre_preferido': forms.TextInput(attrs={'class': 'form-control'}),
            'estatus': forms.Select(attrs={'class': 'form-select'}),
            'estatus_proceso': forms.Select(attrs={'class': 'form-select'}),
            'equipo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_egreso': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones_generales': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-seleccionar el tutor principal actual
        if self.instance and self.instance.pk:
            self.fields['tutor'].initial = self.instance.tutor_principal

# ─────────────────────────────────────────────────────────────────────────────
# TUTOR
# ─────────────────────────────────────────────────────────────────────────────

class TutorForm(forms.ModelForm):
    class Meta:
        model  = Tutor
        # domicilio se maneja con DomicilioForm independiente
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'sexo_catalogo', 'fecha_nacimiento', 'curp', 'rfc',
            'tipo_identificacion', 'numero_identificacion',
            'parentesco_con_nna',
            'estado_civil', 'escolaridad', 'ocupacion',
            'ingreso_mensual_aproximado',
            'telefono_principal', 'telefono_alternativo',
            'correo_electronico',
        ]
        widgets = {
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno':  forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno':  forms.TextInput(attrs={'class': 'form-control'}),
            'sexo_catalogo':     forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'curp':              forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18', 'autocomplete': 'off'}),
            'rfc':               forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13', 'autocomplete': 'off', 'readonly': True, 'onfocus': "this.removeAttribute('readonly')", 'data-lpignore': 'true'}),
            'tipo_identificacion':   forms.Select(attrs={'class': 'form-select'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'parentesco_con_nna':    forms.Select(attrs={'class': 'form-select'}),
            'estado_civil':      forms.Select(attrs={'class': 'form-select'}),
            'escolaridad':       forms.Select(attrs={'class': 'form-select'}),
            'ocupacion':         forms.TextInput(attrs={'class': 'form-control'}),
            'ingreso_mensual_aproximado': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0',
            }),
            'telefono_principal':   forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_alternativo': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_electronico':   forms.EmailInput(attrs={'class': 'form-control'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# EQUIPO MULTIDISCIPLINARIO
# Cada select se filtra por rol para mostrar solo los empleados adecuados.
# ─────────────────────────────────────────────────────────────────────────────

class EquipoForm(forms.ModelForm):
    class Meta:
        model  = EquipoMultidisciplinario
        fields = [
            'nombre',
            'abogado', 'doctor', 'trabajador_social', 'psicologo',
            'coordinador',
        ]
        widgets = {
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'abogado':           forms.Select(attrs={'class': 'form-select'}),
            'doctor':            forms.Select(attrs={'class': 'form-select'}),
            'trabajador_social': forms.Select(attrs={'class': 'form-select'}),
            'psicologo':         forms.Select(attrs={'class': 'form-select'}),
            'coordinador':       forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar cada campo por rol y ordenar por apellido
        rol_campo = {
            'abogado':           'abogado',
            'doctor':            'doctor',
            'trabajador_social': 'trabajador_social',
            'psicologo':         'psicologo',
            'coordinador':       'coordinador',
        }
        for campo, rol in rol_campo.items():
            qs = (
                Empleado.objects
                .filter(rol=rol, usuario__is_active=True)
                .select_related('usuario')
                .order_by('apellido_paterno', 'nombre')
            )
            self.fields[campo].queryset = qs
            if campo == 'coordinador':
                self.fields[campo].required = False
                self.fields[campo].empty_label = '— Sin coordinador —'
            else:
                self.fields[campo].empty_label = f'— Selecciona {rol.replace("_", " ")} —'


# ─────────────────────────────────────────────────────────────────────────────
# SEGUIMIENTO INTEGRAL DEL NNA
# ─────────────────────────────────────────────────────────────────────────────

class SeguimientoNNAForm(forms.ModelForm):
    ROL_AREA = {
        'abogado': 'legal',
        'doctor': 'medica',
        'psicologo': 'psicologica',
        'trabajador_social': 'social',
    }

    class Meta:
        model = SeguimientoNNA
        fields = [
            'area', 'fecha', 'titulo', 'descripcion',
            'acuerdos', 'proxima_accion', 'estatus',
        ]
        widgets = {
            'area': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'acuerdos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'proxima_accion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estatus': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if not self.user or self.user.is_superuser:
            return

        try:
            rol = self.user.empleado.rol
        except Empleado.DoesNotExist:
            self.fields['area'].choices = []
            return

        if rol in ('director', 'coordinador'):
            return

        area = self.ROL_AREA.get(rol)
        if area:
            self.fields['area'].choices = [
                choice for choice in self.fields['area'].choices if choice[0] == area
            ]
            self.fields['area'].initial = area
        else:
            self.fields['area'].choices = []


class HechoVictimalForm(forms.ModelForm):
    class Meta:
        model = HechoVictimal
        fields = [
            'nombre_victima_directa', 'parentesco_victima_nna',
            'tipo_delito', 'descripcion_delito', 'fecha_hecho', 'hora_hecho',
            'ambito_ocurrencia', 'lugar_hecho', 'lugar_hecho_municipio',
            'numero_carpeta_investigacion', 'fiscalia_o_ministerio',
            'numero_expediente_judicial', 'juzgado', 'estatus_juridico',
            'hay_detenidos', 'datos_detenidos', 'nna_fue_testigo',
            'nna_tambien_victima', 'descripcion_impacto_nna',
            'derivado_por', 'tipo_institucion_derivadora', 'observaciones',
        ]
        widgets = {
            'fecha_hecho': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_hecho': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'descripcion_delito': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'lugar_hecho': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'datos_detenidos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'descripcion_impacto_nna': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.DateInput, forms.TimeInput, forms.Textarea)):
                field.widget.attrs.setdefault('class', 'form-control')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'


class ContactoNNAForm(forms.ModelForm):
    class Meta:
        model = ContactoNNA
        fields = ['tipo', 'valor', 'descripcion', 'principal']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IdiomaNNAForm(forms.ModelForm):
    class Meta:
        model = IdiomaNNA
        fields = [
            'lengua', 'nivel', 'nivel_competencia',
            'modo_adquisicion', 'es_lengua_materna',
            'preferente', 'autodenominacion',
        ]
        widgets = {
            'lengua': forms.Select(attrs={'class': 'form-select idioma-lengua-sel'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'nivel_competencia': forms.Select(attrs={'class': 'form-select'}),
            'modo_adquisicion': forms.Select(attrs={'class': 'form-select'}),
            'es_lengua_materna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preferente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'autodenominacion': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DiscapacidadNNAForm(forms.ModelForm):
    class Meta:
        model = DiscapacidadNNA
        fields = [
            'tipo', 'discapacidad', 'descripcion_especifica',
            'grado_dependencia',
            'causa', 'certificado_medico', 'observaciones',
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'discapacidad': forms.Select(attrs={'class': 'form-select'}),
            'descripcion_especifica': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'grado_dependencia': forms.Select(attrs={'class': 'form-select'}),
            'causa': forms.Select(attrs={'class': 'form-select'}),
            'certificado_medico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PadecimientoNNAForm(forms.ModelForm):
    class Meta:
        model = PadecimientoNNA
        fields = [
            'enfermedad', 'fecha_diagnostico', 'diagnostico_medico',
            'es_cronica', 'bajo_tratamiento', 'requiere_medicamento',
            'estado_tratamiento', 'esta_controlada', 'requiere_atencion_fundacion',
            'medicamentos', 'observaciones_medicas',
        ]
        widgets = {
            'enfermedad': forms.Select(attrs={'class': 'form-select'}),
            'fecha_diagnostico': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'diagnostico_medico': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'es_cronica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bajo_tratamiento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_medicamento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estado_tratamiento': forms.Select(attrs={'class': 'form-select'}),
            'esta_controlada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_atencion_fundacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medicamentos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones_medicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DocumentoExpedienteForm(forms.ModelForm):
    class Meta:
        model = DocumentoExpediente
        fields = ['tipo', 'nombre_archivo', 'archivo', 'descripcion', 'fecha_documento']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nombre_archivo': forms.TextInput(attrs={'class': 'form-control'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fecha_documento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class PlanRestitucionForm(forms.ModelForm):
    class Meta:
        model = PlanRestitucion
        fields = [
            'folio', 'fecha_apertura', 'equipo', 'grado_peligro',
            'grado_coercion', 'diagnostico_general',
            'determinacion_interes_superior', 'estatus', 'vigente',
            'fecha_cierre',
        ]
        widgets = {
            'folio': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_apertura': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'equipo': forms.Select(attrs={'class': 'form-select'}),
            'grado_peligro': forms.Select(attrs={'class': 'form-select'}),
            'grado_coercion': forms.Select(attrs={'class': 'form-select'}),
            'diagnostico_general': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'determinacion_interes_superior': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estatus': forms.Select(attrs={'class': 'form-select'}),
            'vigente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_cierre': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class DerechoVulneradoForm(forms.ModelForm):
    class Meta:
        model = DerechoVulnerado
        fields = ['derecho', 'grado', 'descripcion']
        widgets = {
            'derecho': forms.Select(attrs={'class': 'form-select'}),
            'grado': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


ContactoNNAFormSet = inlineformset_factory(
    NNA, ContactoNNA, form=ContactoNNAForm, extra=1, can_delete=True
)
IdiomaNNAFormSet = inlineformset_factory(
    NNA, IdiomaNNA, form=IdiomaNNAForm, extra=0, can_delete=True
)
DiscapacidadNNAFormSet = inlineformset_factory(
    NNA, DiscapacidadNNA, form=DiscapacidadNNAForm, extra=1, can_delete=True
)
PadecimientoNNAFormSet = inlineformset_factory(
    NNA, PadecimientoNNA, form=PadecimientoNNAForm, extra=1, can_delete=True
)
DocumentoExpedienteFormSet = inlineformset_factory(
    NNA, DocumentoExpediente, form=DocumentoExpedienteForm, extra=1, can_delete=True
)
DerechoVulneradoFormSet = inlineformset_factory(
    PlanRestitucion, DerechoVulnerado, form=DerechoVulneradoForm, extra=1, can_delete=True
)


# ─────────────────────────────────────────────────────────────────────────────
# CONTACTOS MULTIPLES — Tutor y Empleado (telefonos/correos adicionales)
# ─────────────────────────────────────────────────────────────────────────────

class ContactoTutorForm(forms.ModelForm):
    class Meta:
        model = ContactoTutor
        fields = ['tipo', 'valor', 'descripcion', 'principal']
        widgets = {
            'tipo':        forms.Select(attrs={'class': 'form-select'}),
            'valor':       forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'principal':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContactoEmpleadoForm(forms.ModelForm):
    class Meta:
        model = ContactoEmpleado
        fields = ['tipo', 'valor', 'descripcion', 'principal']
        widgets = {
            'tipo':        forms.Select(attrs={'class': 'form-select'}),
            'valor':       forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'principal':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IdiomaTutorForm(forms.ModelForm):
    class Meta:
        model = IdiomaTutor
        fields = [
            'lengua', 'nivel', 'nivel_competencia',
            'modo_adquisicion', 'es_lengua_materna', 'preferente',
        ]
        widgets = {
            'lengua': forms.Select(attrs={'class': 'form-select idioma-lengua-sel'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'nivel_competencia': forms.Select(attrs={'class': 'form-select'}),
            'modo_adquisicion': forms.Select(attrs={'class': 'form-select'}),
            'es_lengua_materna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preferente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IdiomaEmpleadoForm(forms.ModelForm):
    class Meta:
        model = IdiomaEmpleado
        fields = [
            'lengua', 'nivel', 'nivel_competencia',
            'modo_adquisicion', 'es_lengua_materna', 'preferente',
        ]
        widgets = {
            'lengua': forms.Select(attrs={'class': 'form-select idioma-lengua-sel'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'nivel_competencia': forms.Select(attrs={'class': 'form-select'}),
            'modo_adquisicion': forms.Select(attrs={'class': 'form-select'}),
            'es_lengua_materna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preferente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


ContactoTutorFormSet = inlineformset_factory(
    Tutor, ContactoTutor, form=ContactoTutorForm, extra=1, can_delete=True
)
ContactoEmpleadoFormSet = inlineformset_factory(
    Empleado, ContactoEmpleado, form=ContactoEmpleadoForm, extra=1, can_delete=True
)
IdiomaTutorFormSet = inlineformset_factory(
    Tutor, IdiomaTutor, form=IdiomaTutorForm, extra=0, can_delete=True
)
IdiomaEmpleadoFormSet = inlineformset_factory(
    Empleado, IdiomaEmpleado, form=IdiomaEmpleadoForm, extra=0, can_delete=True
)
