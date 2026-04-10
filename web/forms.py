from django import forms
from django.contrib.auth.models import User

from .models import (
    Empleado, Domicilio, Asentamiento,
    NNA, EntidadFederativa, Municipio,
    Tutor, EquipoMultidisciplinario,
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
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Contraseña',
        required=False,
    )

    class Meta:
        model = Empleado
        # 'domicilio' se maneja con DomicilioForm independiente
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'rfc', 'curp', 'sexo', 'fecha_nacimiento',
            'tipo_trabajador', 'rol', 'cedula_profesional', 'telefono',
        ]
        widgets = {
            'fecha_nacimiento':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno':  forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno':  forms.TextInput(attrs={'class': 'form-control'}),
            'rfc':               forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}),
            'curp':              forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18'}),
            'sexo':              forms.Select(attrs={'class': 'form-select'}),
            'tipo_trabajador':   forms.Select(attrs={'class': 'form-select'}),
            'rol':               forms.Select(attrs={'class': 'form-select'}),
            'cedula_profesional': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono':          forms.TextInput(attrs={'class': 'form-control'}),
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

    class Meta:
        model = NNA
        # domicilio y registrado_por se asignan en la vista
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'fecha_nacimiento', 'sexo', 'curp',
            'escolaridad', 'nombre_escuela',
            'lugar_nacimiento_estado', 'lugar_nacimiento_municipio',
            'es_extranjero', 'pais_origen',
            'vive_con_tutor', 'tutor', 'equipo',
            'estatus', 'fecha_ingreso', 'observaciones_generales',
        ]
        widgets = {
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno':  forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno':  forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sexo':              forms.Select(attrs={'class': 'form-select'}),
            'curp':              forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18'}),
            'escolaridad':       forms.Select(attrs={'class': 'form-select'}),
            'nombre_escuela':    forms.TextInput(attrs={'class': 'form-control'}),
            'es_extranjero':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pais_origen':       forms.TextInput(attrs={'class': 'form-control'}),
            'vive_con_tutor':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tutor':             forms.Select(attrs={'class': 'form-select'}),
            'equipo':            forms.Select(attrs={'class': 'form-select'}),
            'estatus':           forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso':     forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones_generales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

# ─────────────────────────────────────────────────────────────────────────────
# TUTOR
# ─────────────────────────────────────────────────────────────────────────────

class TutorForm(forms.ModelForm):
    class Meta:
        model  = Tutor
        # domicilio se maneja con DomicilioForm independiente
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'sexo', 'fecha_nacimiento', 'curp', 'rfc',
            'tipo_identificacion', 'numero_identificacion',
            'parentesco_con_nna',
            'estado_civil', 'escolaridad', 'ocupacion',
            'ingreso_mensual_aproximado',
            'telefono_principal', 'telefono_alternativo',
            'correo_electronico',
            'observaciones',
        ]
        widgets = {
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno':  forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno':  forms.TextInput(attrs={'class': 'form-control'}),
            'sexo':              forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'curp':              forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18'}),
            'rfc':               forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}),
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
            'observaciones':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
