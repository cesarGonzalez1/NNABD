from django.db import models
from django.contrib.auth.models import AbstractUser

class Empleado(models.Model):
    nombre_completo = models.CharField(max_length=150)
    rfc = models.CharField(max_length=13, unique=True)
    curp = models.CharField(max_length=18, unique=True)
    
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)

    edad = models.IntegerField()
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

    # ----- DATOS PARA USO DEL SISTEMA -----
    correo = models.EmailField(unique=True)
    activo = models.BooleanField(default=True)

    # Fecha de registro automática
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_completo
# Create your models here.
