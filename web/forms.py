from django import forms
from django.contrib.auth.models import User
from .models import Empleado

class EmpleadoForm(forms.ModelForm):
    # Campos adicionales para la cuenta de acceso
    username = forms.CharField(max_length=150, label="Nombre de usuario")
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

    # Esta función valida el username automáticamente antes de llegar a la vista
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso. Elige otro.")
        return username
