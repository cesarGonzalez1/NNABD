from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User

class Empleado(models.Model):

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    # ----- DATOS PERSONALES -----
    nombre = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)

    rfc = models.CharField(max_length=13, unique=True)
    curp = models.CharField(max_length=18, unique=True)

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)

    fecha_nacimiento = models.DateField()
    direccion = models.TextField()

    # ----- DATOS LABORALES -----
    ROL_CHOICES = [
        ('director', 'Director'),
        ('coordinador', 'Coordinador'),
        ('psicologo', 'Psicólogo'),
        ('doctor', 'Doctor'),
        ('abogado', 'Abogado'),
        ('trabajador_social', 'Trabajador Social'),
        ('analista', 'Analista'),
        ('voluntario', 'Voluntario'),
    ]
    rol = models.CharField(max_length=50, choices=ROL_CHOICES)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno}"

# Create your models here.
