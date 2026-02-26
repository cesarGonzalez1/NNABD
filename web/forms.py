from django import forms
from django.contrib.auth.models import User
from .models import Empleado

class EmpleadoForm(forms.ModelForm):
    # Campos adicionales para la cuenta de acceso
    
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    class Meta:
        model = Empleado
        fields = [
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'rfc',
            'curp',
            'sexo',
            'fecha_nacimiento',
            'direccion',
            'rol',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

   