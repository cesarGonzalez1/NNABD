"""
NNABD — web/models.py  v2.0
════════════════════════════════════════════════════════════════════════════════
REGLAS RESPETADAS DEL PROYECTO ORIGINAL:
  · Empleado.usuario = OneToOneField(User)  → activo/inactivo vive en User.is_active
  · RFC se usa como username del User (lógica en views.py / crear_empleado)
  · Rol de director controla permisos de vista (views + templates)
  · tipo_trabajador ya existe desde migración 0002
  · Campo "activo" fue eliminado en migración 0003 → no se vuelve a agregar
  · direccion (TextField) se reemplaza por FK opcional a Domicilio;
    null=True / blank=True para migración no destructiva.

NUEVOS MÓDULOS AGREGADOS (5.1 → 5.5):
  · Catálogo SEPOMEX   (EntidadFederativa, Municipio, TipoAsentamiento,
                        Asentamiento, Domicilio)
  · Catálogo INALI     (FamiliaLinguistica, Lengua, VarianteLinguistica)
  · Discapacidades CIF (TipoDiscapacidad)
  · Enfermedades CIE-10(CapituloEnfermedad, Enfermedad)
  · EquipoMultidisciplinario
  · Tutor              (+ IdiomaTutor, DiscapacidadTutor, PadecimientoTutor)
  · NNA                (+ IdiomaNNA, DiscapacidadNNA, PadecimientoNNA)
  · HechoVictimal (FUD)
  · DocumentoExpediente
════════════════════════════════════════════════════════════════════════════════
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO SEPOMEX
# Fuente oficial: Correos de México / datos.gob.mx
# Jerarquía: EntidadFederativa → Municipio → Asentamiento (con CP único)
# Los datos se cargan vía fixtures (CSV SEPOMEX).
# ══════════════════════════════════════════════════════════════════════════════

class EntidadFederativa(models.Model):
    """32 estados de la República + CDMX."""
    clave       = models.CharField(max_length=2, unique=True,
                                   help_text="Clave INEGI 01-32")
    nombre      = models.CharField(max_length=100)
    abreviatura = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Entidad Federativa"
        verbose_name_plural = "Entidades Federativas"

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    entidad = models.ForeignKey(EntidadFederativa, on_delete=models.CASCADE,
                                related_name='municipios')
    clave   = models.CharField(max_length=5,
                               help_text="Clave INEGI del municipio/alcaldía")
    nombre  = models.CharField(max_length=150)

    class Meta:
        ordering = ['nombre']
        unique_together = ('entidad', 'clave')
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"

    def __str__(self):
        return f"{self.nombre}, {self.entidad.abreviatura}"


class TipoAsentamiento(models.Model):
    """Colonia, Fraccionamiento, Ejido, Pueblo, Barrio, etc. (catálogo SEPOMEX)."""
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Tipo de Asentamiento"
        verbose_name_plural = "Tipos de Asentamiento"

    def __str__(self):
        return self.nombre


class Asentamiento(models.Model):
    """
    Colonia / asentamiento humano con su Código Postal oficial SEPOMEX.
    Un CP puede tener varios asentamientos; cada asentamiento tiene un único CP.
    """
    municipio         = models.ForeignKey(Municipio, on_delete=models.CASCADE,
                                          related_name='asentamientos')
    tipo_asentamiento = models.ForeignKey(TipoAsentamiento, on_delete=models.SET_NULL,
                                          null=True, blank=True)
    nombre            = models.CharField(max_length=200)
    codigo_postal     = models.CharField(max_length=5, db_index=True)
    ciudad            = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['codigo_postal', 'nombre']
        verbose_name = "Asentamiento / Colonia"
        verbose_name_plural = "Asentamientos / Colonias"
        constraints = [
            models.UniqueConstraint(
                fields=['municipio', 'codigo_postal', 'nombre'],
                name='uniq_asentamiento_municipio_cp_nombre',
            ),
        ]

    def __str__(self):
        return f"{self.nombre}, C.P. {self.codigo_postal}"


class Domicilio(models.Model):
    """
    Domicilio estructurado con referencia al catálogo SEPOMEX.
    Reutilizable para Empleado, NNA y Tutor.
    """
    asentamiento    = models.ForeignKey(Asentamiento, on_delete=models.PROTECT,
                                        help_text="Colonia del catálogo SEPOMEX")
    calle           = models.CharField(max_length=200)
    numero_exterior = models.CharField(max_length=20, blank=True)
    numero_interior = models.CharField(max_length=20, blank=True)
    referencias     = models.TextField(blank=True,
                                       help_text="Entre calles u otras referencias")

    class Meta:
        verbose_name = "Domicilio"
        verbose_name_plural = "Domicilios"

    def __str__(self):
        num = f"#{self.numero_exterior}" if self.numero_exterior else "s/n"
        return f"{self.calle} {num}, {self.asentamiento}"


class Sexo(models.Model):
    """Catalogo relacional de sexo para alinear el modelo con el ER."""
    clave = models.CharField(max_length=3, unique=True)
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Sexo"
        verbose_name_plural = "Catalogo de Sexo"

    def __str__(self):
        return self.nombre


class Nacionalidad(models.Model):
    clave = models.CharField(max_length=3, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Nacionalidad"
        verbose_name_plural = "Nacionalidades"

    def __str__(self):
        return self.nombre


class TipoContacto(models.Model):
    clave = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Tipo de Contacto"
        verbose_name_plural = "Tipos de Contacto"

    def __str__(self):
        return self.nombre


class NivelCompetenciaOral(models.Model):
    clave = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    significado = models.TextField(blank=True)
    puede_declarar = models.BooleanField(default=True)
    requiere_interprete = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        verbose_name = "Nivel de Competencia Oral"
        verbose_name_plural = "Niveles de Competencia Oral"

    def __str__(self):
        return self.nombre


class ModoAdquisicionLengua(models.Model):
    clave = models.CharField(max_length=30, unique=True)
    categoria = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    contexto = models.TextField(blank=True)

    class Meta:
        ordering = ['categoria']
        verbose_name = "Modo de Adquisicion de Lengua"
        verbose_name_plural = "Modos de Adquisicion de Lengua"

    def __str__(self):
        return self.categoria


class GradoDependencia(models.Model):
    clave = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = "Grado de Dependencia"
        verbose_name_plural = "Grados de Dependencia"

    def __str__(self):
        return self.nombre


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO DE IDIOMAS — INALI
# Instituto Nacional de Lenguas Indígenas
# https://www.inali.gob.mx/clin-inali/
# Jerarquía: FamiliaLinguistica → Lengua → VarianteLinguistica
# ══════════════════════════════════════════════════════════════════════════════

class FamiliaLinguistica(models.Model):
    """Ej.: Oto-mangue, Maya, Yuto-nahua, Totonaco-tepehua…"""
    catalogo_id = models.PositiveIntegerField(
        null=True, blank=True, unique=True,
        help_text="Id del catalogo proporcionado por la escuela/profesor"
    )
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Familia Lingüística"
        verbose_name_plural = "Familias Lingüísticas"

    def __str__(self):
        return self.nombre


class Lengua(models.Model):
    """
    Lengua del Catálogo de Lenguas Indígenas Nacionales (INALI).
    Incluye también Español y lenguas extranjeras (familia=NULL, es_indigena=False).
    """
    catalogo_id = models.PositiveIntegerField(
        null=True, blank=True, unique=True,
        help_text="Id del catalogo proporcionado por la escuela/profesor"
    )
    familia     = models.ForeignKey(FamiliaLinguistica, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='lenguas')
    nombre      = models.CharField(max_length=100)
    clave_inali = models.CharField(max_length=20, blank=True, unique=True,
                                   help_text="Clave oficial INALI (ej. NAH para Náhuatl)")
    es_indigena = models.BooleanField(default=True)
    agrupacion_linguistica = models.CharField(max_length=150, blank=True)
    variante_linguistica = models.CharField(max_length=200, blank=True)
    autodenominacion = models.CharField(max_length=200, blank=True)
    estado_region = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['catalogo_id', 'nombre']
        verbose_name = "Lengua"
        verbose_name_plural = "Lenguas"

    def __str__(self):
        if self.catalogo_id:
            return f"{self.catalogo_id}. {self.nombre}"
        return self.nombre


class VarianteLinguistica(models.Model):
    """
    Variante dialectal de una lengua según INALI.
    Ej.: Náhuatl de la Sierra de Puebla, Náhuatl de la Huasteca Hidalguense…
    """
    lengua      = models.ForeignKey(Lengua, on_delete=models.CASCADE,
                                    related_name='variantes')
    nombre      = models.CharField(max_length=150)
    clave_inali = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Variante Lingüística"
        verbose_name_plural = "Variantes Lingüísticas"

    def __str__(self):
        return f"{self.nombre} ({self.lengua.nombre})"


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO DE DISCAPACIDADES
# Base: Clasificación Internacional del Funcionamiento (CIF, OMS)
# Complementado con clasificación INEGI para México
# ══════════════════════════════════════════════════════════════════════════════

class TipoDiscapacidad(models.Model):
    """
    Tipos oficiales: Motriz, Visual, Auditiva, del Habla/Lenguaje,
    Intelectual, Psicosocial/Mental, Múltiple.
    """
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    clave_inegi = models.CharField(max_length=10, blank=True,
                                   help_text="Clave INEGI si aplica")

    class Meta:
        ordering = ['nombre']
        verbose_name = "Tipo de Discapacidad"
        verbose_name_plural = "Tipos de Discapacidad"

    def __str__(self):
        return self.nombre


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO DE ENFERMEDADES — CIE-10
# Clasificación Internacional de Enfermedades, 10.ª revisión (OMS / SS México)
# ══════════════════════════════════════════════════════════════════════════════

class Discapacidad(models.Model):
    """Catalogo especifico de discapacidades, subordinado al tipo general."""
    tipo = models.ForeignKey(TipoDiscapacidad, on_delete=models.PROTECT,
                             related_name='discapacidades')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['tipo__nombre', 'nombre']
        unique_together = ('tipo', 'nombre')
        verbose_name = "Discapacidad"
        verbose_name_plural = "Discapacidades"

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"


class CapituloEnfermedad(models.Model):
    """
    Capítulo CIE-10.
    Ej.: I = Enfermedades infecciosas, IV = Enfermedades endocrinas…
    """
    codigo       = models.CharField(max_length=5, unique=True)
    nombre       = models.CharField(max_length=200)
    rango_inicio = models.CharField(max_length=5, blank=True)
    rango_fin    = models.CharField(max_length=5, blank=True)

    class Meta:
        ordering = ['codigo']
        verbose_name = "Capítulo CIE-10"
        verbose_name_plural = "Capítulos CIE-10"

    def __str__(self):
        return f"Cap. {self.codigo} — {self.nombre}"


class Enfermedad(models.Model):
    """
    Enfermedad del catálogo CIE-10 oficial (SS México).
    Ej.: E11 = Diabetes mellitus tipo 2, I10 = Hipertensión esencial.
    """
    capitulo     = models.ForeignKey(CapituloEnfermedad, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='enfermedades')
    codigo_cie10 = models.CharField(max_length=10, unique=True)
    nombre       = models.CharField(max_length=300)
    nombre_corto = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['codigo_cie10']
        verbose_name = "Enfermedad (CIE-10)"
        verbose_name_plural = "Enfermedades (CIE-10)"

    def __str__(self):
        return f"{self.codigo_cie10} — {self.nombre_corto or self.nombre}"


# ══════════════════════════════════════════════════════════════════════════════
# EMPLEADO
# Se respeta EXACTAMENTE la lógica original:
#   · usuario = OneToOneField(User) → is_active maneja estatus (visto en views.py)
#   · RFC como username (views.py / crear_empleado lo construye así)
#   · tipo_trabajador y rol sin cambios
#   · NO hay campo "activo" (eliminado en migración 0003)
#   · direccion TextField se reemplaza por FK opcional a Domicilio (null=True)
#     para migración no destructiva; la vista puede seguir funcionando igual.
# ══════════════════════════════════════════════════════════════════════════════

class Empleado(models.Model):

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    # ----- DATOS PERSONALES (sin cambios respecto al original) -----
    nombre           = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)

    rfc  = models.CharField(max_length=13, unique=True)
    curp = models.CharField(max_length=18, unique=True)

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    sexo_catalogo = models.ForeignKey(Sexo, on_delete=models.PROTECT,
                                      null=True, blank=True,
                                      related_name='empleados')

    fecha_nacimiento = models.DateField()

    # direccion (TextField original) → reemplazado por FK estructurado a Domicilio.
    # null=True / blank=True para que la migración no rompa registros existentes.
    domicilio = models.ForeignKey(Domicilio, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='empleados')

    TIPO_CHOICES = [
        ('empleado',   'Empleado'),
        ('voluntario', 'Voluntario'),
    ]
    tipo_trabajador = models.CharField(max_length=20, choices=TIPO_CHOICES,
                                       default='empleado')

    ROL_CHOICES = [
        ('director',          'Director'),
        ('coordinador',       'Coordinador'),
        ('psicologo',         'Psicólogo'),
        ('doctor',            'Doctor'),
        ('abogado',           'Abogado'),
        ('trabajador_social', 'Trabajador Social'),
        ('analista',          'Analista'),
    ]
    rol = models.CharField(max_length=50, choices=ROL_CHOICES)

    # Campos complementarios opcionales (nuevos, no rompen nada)
    cedula_profesional = models.CharField(max_length=20, blank=True,
                                          help_text="Cédula profesional (roles con licencia)")
    telefono           = models.CharField(max_length=15, blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    # activo NO está aquí — se toma de usuario.is_active (migración 0003)

    class Meta:
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno}"


# ══════════════════════════════════════════════════════════════════════════════
# EQUIPO MULTIDISCIPLINARIO
# Cada NNA debe tener un equipo con los 4 roles requeridos.
# ══════════════════════════════════════════════════════════════════════════════

class EquipoMultidisciplinario(models.Model):
    nombre = models.CharField(max_length=100,
                              help_text="Nombre o clave interna del equipo")

    abogado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT,
        related_name='equipos_como_abogado',
        limit_choices_to={'rol': 'abogado'}
    )
    doctor = models.ForeignKey(
        Empleado, on_delete=models.PROTECT,
        related_name='equipos_como_doctor',
        limit_choices_to={'rol': 'doctor'}
    )
    trabajador_social = models.ForeignKey(
        Empleado, on_delete=models.PROTECT,
        related_name='equipos_como_ts',
        limit_choices_to={'rol': 'trabajador_social'}
    )
    psicologo = models.ForeignKey(
        Empleado, on_delete=models.PROTECT,
        related_name='equipos_como_psicologo',
        limit_choices_to={'rol': 'psicologo'}
    )
    coordinador = models.ForeignKey(
        Empleado, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='equipos_coordinados',
        limit_choices_to={'rol': 'coordinador'}
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Equipo Multidisciplinario"
        verbose_name_plural = "Equipos Multidisciplinarios"

    def __str__(self):
        return self.nombre


# ══════════════════════════════════════════════════════════════════════════════
# TUTOR DEL MENOR
# ~80 % adultas mayores; importante registrar enfermedades y discapacidades.
# ══════════════════════════════════════════════════════════════════════════════

class Tutor(models.Model):

    PARENTESCO_CHOICES = [
        ('abuela',        'Abuela'),
        ('abuelo',        'Abuelo'),
        ('tia',           'Tía'),
        ('tio',           'Tío'),
        ('hermana_mayor', 'Hermana Mayor'),
        ('hermano_mayor', 'Hermano Mayor'),
        ('madrina',       'Madrina'),
        ('padrino',       'Padrino'),
        ('vecino',        'Vecino / Conocido'),
        ('institucion',   'Institución'),
        ('otro',          'Otro'),
    ]
    ESTADO_CIVIL_CHOICES = [
        ('soltero',     'Soltero/a'),
        ('casado',      'Casado/a'),
        ('union_libre', 'Unión libre'),
        ('divorciado',  'Divorciado/a'),
        ('viudo',       'Viudo/a'),
        ('separado',    'Separado/a'),
    ]
    ESCOLARIDAD_CHOICES = [
        ('sin_escolaridad',     'Sin escolaridad'),
        ('primaria_incompleta', 'Primaria incompleta'),
        ('primaria',            'Primaria'),
        ('secundaria',          'Secundaria'),
        ('preparatoria',        'Preparatoria / Bachillerato'),
        ('tecnico',             'Técnico / Vocacional'),
        ('licenciatura',        'Licenciatura'),
        ('posgrado',            'Posgrado'),
    ]
    TIPO_ID_CHOICES = [
        ('ine',             'INE / IFE'),
        ('pasaporte',       'Pasaporte'),
        ('acta_nacimiento', 'Acta de Nacimiento'),
        ('cedula',          'Cédula de Identidad'),
        ('otro',            'Otro'),
    ]
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    # --- Identificación ---
    nombre           = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50, blank=True)
    sexo             = models.CharField(max_length=1, choices=SEXO_CHOICES, default='F')
    sexo_catalogo    = models.ForeignKey(Sexo, on_delete=models.PROTECT,
                                         null=True, blank=True,
                                         related_name='tutores')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    curp             = models.CharField(max_length=18, unique=True, null=True, blank=True)
    rfc              = models.CharField(max_length=13, blank=True)

    tipo_identificacion   = models.CharField(max_length=20, choices=TIPO_ID_CHOICES, blank=True)
    numero_identificacion = models.CharField(max_length=50, blank=True)

    # --- Situación personal ---
    parentesco_con_nna         = models.CharField(max_length=30, choices=PARENTESCO_CHOICES)
    estado_civil               = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES, blank=True)
    escolaridad                = models.CharField(max_length=30, choices=ESCOLARIDAD_CHOICES, blank=True)
    ocupacion                  = models.CharField(max_length=100, blank=True)
    ingreso_mensual_aproximado = models.DecimalField(max_digits=10, decimal_places=2,
                                                     null=True, blank=True)

    # --- Contacto ---
    telefono_principal   = models.CharField(max_length=15, blank=True)
    telefono_alternativo = models.CharField(max_length=15, blank=True)
    correo_electronico   = models.EmailField(blank=True)
    domicilio            = models.ForeignKey(Domicilio, on_delete=models.SET_NULL,
                                             null=True, blank=True,
                                             related_name='tutores')

    observaciones       = models.TextField(blank=True)
    fecha_registro      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['apellido_paterno', 'nombre']
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}".strip()


class IdiomaTutor(models.Model):
    """Lenguas que habla el tutor (catálogo INALI)."""
    NIVEL_CHOICES = [
        ('basico',     'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado',   'Avanzado'),
        ('nativo',     'Nativo / Lengua materna'),
    ]
    tutor             = models.ForeignKey(Tutor, on_delete=models.CASCADE,
                                          related_name='idiomas')
    lengua            = models.ForeignKey(Lengua, on_delete=models.PROTECT)
    variante          = models.ForeignKey(VarianteLinguistica, on_delete=models.SET_NULL,
                                          null=True, blank=True)
    nivel             = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='nativo')
    nivel_competencia = models.ForeignKey(NivelCompetenciaOral, on_delete=models.PROTECT,
                                          null=True, blank=True,
                                          related_name='idiomas_tutor')
    modo_adquisicion  = models.ForeignKey(ModoAdquisicionLengua, on_delete=models.PROTECT,
                                          null=True, blank=True,
                                          related_name='idiomas_tutor')
    es_lengua_materna = models.BooleanField(default=False)
    autodenominacion  = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('tutor', 'lengua', 'variante')
        verbose_name = "Idioma del Tutor"
        verbose_name_plural = "Idiomas del Tutor"

    def __str__(self):
        return f"{self.tutor} — {self.lengua}"

    @property
    def requiere_interprete(self):
        return bool(self.nivel_competencia and self.nivel_competencia.requiere_interprete)


class DiscapacidadTutor(models.Model):
    """Discapacidades del tutor (CIF/OMS + INEGI)."""
    GRADO_CHOICES = [
        ('leve',     'Leve — no requiere apoyo permanente'),
        ('moderada', 'Moderada — requiere apoyo parcial'),
        ('severa',   'Severa — requiere apoyo permanente'),
        ('total',    'Total — dependencia completa'),
    ]
    CAUSA_CHOICES = [
        ('congenita',   'Congénita'),
        ('enfermedad',  'Por enfermedad'),
        ('accidente',   'Por accidente'),
        ('violencia',   'Por violencia'),
        ('otra',        'Otra'),
        ('desconocida', 'Desconocida'),
    ]
    tutor                  = models.ForeignKey(Tutor, on_delete=models.CASCADE,
                                               related_name='discapacidades')
    tipo                   = models.ForeignKey(TipoDiscapacidad, on_delete=models.PROTECT)
    discapacidad           = models.ForeignKey(Discapacidad, on_delete=models.PROTECT,
                                               null=True, blank=True)
    descripcion_especifica = models.TextField(blank=True)
    grado_dependencia      = models.CharField(max_length=20, choices=GRADO_CHOICES)
    grado_dependencia_catalogo = models.ForeignKey(
        GradoDependencia, on_delete=models.PROTECT,
        null=True, blank=True, related_name='discapacidades_tutor'
    )
    causa                  = models.CharField(max_length=20, choices=CAUSA_CHOICES,
                                              default='desconocida')
    certificado_medico     = models.BooleanField(default=False)
    observaciones          = models.TextField(blank=True)

    class Meta:
        unique_together = ('tutor', 'tipo', 'descripcion_especifica')
        verbose_name = "Discapacidad del Tutor"
        verbose_name_plural = "Discapacidades del Tutor"


class PadecimientoTutor(models.Model):
    """
    Enfermedades del tutor (CIE-10).
    Especialmente relevante para adultas mayores que son las tutoras más frecuentes.
    """
    tutor                       = models.ForeignKey(Tutor, on_delete=models.CASCADE,
                                                    related_name='padecimientos')
    enfermedad                  = models.ForeignKey(Enfermedad, on_delete=models.PROTECT)
    fecha_diagnostico           = models.DateField(null=True, blank=True)
    es_cronica                  = models.BooleanField(default=False)
    esta_controlada             = models.BooleanField(default=False)
    requiere_atencion_fundacion = models.BooleanField(
        default=False,
        help_text="¿Requiere apoyo médico de la fundación?"
    )
    medicamentos          = models.TextField(blank=True)
    observaciones_medicas = models.TextField(blank=True)

    class Meta:
        unique_together = ('tutor', 'enfermedad')
        verbose_name = "Padecimiento del Tutor"
        verbose_name_plural = "Padecimientos del Tutor"

    def __str__(self):
        return f"{self.tutor} — {self.enfermedad}"


# ══════════════════════════════════════════════════════════════════════════════
# NNA — NIÑA, NIÑO O ADOLESCENTE
# Alta realizada exclusivamente por el Trabajador Social del equipo asignado.
# ══════════════════════════════════════════════════════════════════════════════

class NNA(models.Model):

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro / No binario'),
    ]
    ESCOLARIDAD_CHOICES = [
        ('sin_escolaridad',       'Sin escolaridad'),
        ('preescolar',            'Preescolar'),
        ('primaria_incompleta',   'Primaria incompleta'),
        ('primaria',              'Primaria'),
        ('secundaria_incompleta', 'Secundaria incompleta'),
        ('secundaria',            'Secundaria'),
        ('preparatoria',          'Preparatoria / Bachillerato'),
        ('otro',                  'Otro'),
    ]
    ESTATUS_CHOICES = [
        ('activo',     'Activo — en atención'),
        ('egresado',   'Egresado'),
        ('suspendido', 'Suspendido temporalmente'),
        ('cerrado',    'Caso cerrado'),
    ]

    # --- Identificación ---
    folio_nna        = models.CharField(max_length=20, unique=True,
                                        null=True, blank=True)
    nombre           = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50, blank=True)
    fecha_nacimiento = models.DateField()
    sexo             = models.CharField(max_length=1, choices=SEXO_CHOICES)
    sexo_catalogo    = models.ForeignKey(Sexo, on_delete=models.PROTECT,
                                         null=True, blank=True,
                                         related_name='nna')
    curp             = models.CharField(max_length=18, unique=True, null=True, blank=True)

    # --- Situación escolar ---
    escolaridad    = models.CharField(max_length=30, choices=ESCOLARIDAD_CHOICES, blank=True)
    nombre_escuela = models.CharField(max_length=200, blank=True)

    # --- Lugar de nacimiento ---
    lugar_nacimiento_estado    = models.ForeignKey(
        EntidadFederativa, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='nna_nacidos'
    )
    lugar_nacimiento_municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='nna_nacidos'
    )
    es_extranjero = models.BooleanField(default=False)
    pais_origen   = models.CharField(max_length=100, blank=True,
                                     help_text="País de origen si es extranjero")
    nacionalidades = models.ManyToManyField(
        Nacionalidad, through='NacionalidadNNA', blank=True, related_name='nna'
    )

    # --- Situacion de vulnerabilidad (FUD, hoja 8) ---
    CONDICION_MIGRATORIA_CHOICES = [
        ('ninguna',    'Ninguna'),
        ('migrante',   'Migrante'),
        ('refugiado',  'Refugiado/a'),
        ('asilado',    'Asilado/a politico/a'),
        ('repatriado', 'Repatriado/a'),
    ]
    condicion_migratoria = models.CharField(
        max_length=12, choices=CONDICION_MIGRATORIA_CHOICES, default='ninguna')
    pais_destino = models.CharField(max_length=100, blank=True,
                                    help_text='Pais de destino (si es migrante)')
    pertenece_comunidad_indigena = models.BooleanField(default=False)
    comunidad_indigena = models.CharField(max_length=150, blank=True,
                                          help_text='Pueblo o comunidad indigena')
    situacion_calle = models.BooleanField(
        default=False, help_text='Se encuentra en situacion de calle')
    requiere_interprete = models.BooleanField(default=False)
    lengua_interprete = models.CharField(max_length=100, blank=True,
                                         help_text='Lengua para la que requiere interprete')

    # --- Domicilio y convivencia ---
    domicilio      = models.ForeignKey(Domicilio, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='nna')
    vive_con_tutor = models.BooleanField(default=True,
                                         help_text="¿Vive en el domicilio del tutor?")

    # --- Relaciones principales ---
    tutor  = models.ForeignKey(Tutor, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='nna_a_cargo')
    equipo = models.ForeignKey(EquipoMultidisciplinario, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='nna_asignados')

    # --- Estado del caso ---
    estatus       = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='activo')
    fecha_ingreso = models.DateField(help_text="Fecha de ingreso al sistema de la fundación")
    fecha_egreso  = models.DateField(null=True, blank=True)

    # --- Registro (solo trabajador social puede dar de alta) ---
    registrado_por = models.ForeignKey(
        Empleado, on_delete=models.SET_NULL, null=True,
        related_name='nna_registrados',
        limit_choices_to={'rol': 'trabajador_social'},
        help_text="Trabajador social que realizó el alta"
    )
    fecha_registro          = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion     = models.DateTimeField(auto_now=True)
    observaciones_generales = models.TextField(blank=True)

    class Meta:
        ordering = ['apellido_paterno', 'nombre']
        verbose_name = "NNA"
        verbose_name_plural = "NNA"

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}".strip()

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}".strip()

    @property
    def tutor_principal(self):
        relacion = self.tutores_relacion.filter(principal=True).select_related('tutor').first()
        if relacion:
            return relacion.tutor
        return self.tutor

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.folio_nna:
            self.folio_nna = f"NNA-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(folio_nna=self.folio_nna)


class NNATutor(models.Model):
    """Tabla puente NNA x Tutor para permitir historico y multiples tutores."""
    nna = models.ForeignKey(NNA, on_delete=models.CASCADE,
                            related_name='tutores_relacion')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE,
                              related_name='nna_relacionados')
    parentesco = models.CharField(max_length=30, blank=True)
    principal = models.BooleanField(default=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ['-principal', 'tutor__apellido_paterno', 'tutor__nombre']
        unique_together = ('nna', 'tutor')
        constraints = [
            models.UniqueConstraint(
                fields=['nna'],
                condition=models.Q(principal=True),
                name='un_tutor_principal_por_nna',
            ),
        ]
        verbose_name = "Tutor del NNA"
        verbose_name_plural = "Tutores del NNA"

    def __str__(self):
        return f"{self.nna} - {self.tutor}"


class NacionalidadNNA(models.Model):
    nna = models.ForeignKey(NNA, on_delete=models.CASCADE,
                            related_name='nacionalidades_relacion')
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.PROTECT,
                                     related_name='nna_relacion')
    principal = models.BooleanField(default=True)

    class Meta:
        unique_together = ('nna', 'nacionalidad')
        verbose_name = "Nacionalidad del NNA"
        verbose_name_plural = "Nacionalidades del NNA"

    def __str__(self):
        return f"{self.nna} - {self.nacionalidad}"


class ContactoNNA(models.Model):
    nna = models.ForeignKey(NNA, on_delete=models.CASCADE,
                            related_name='contactos')
    tipo = models.ForeignKey(TipoContacto, on_delete=models.PROTECT,
                             related_name='contactos_nna')
    valor = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200, blank=True)
    principal = models.BooleanField(default=False)

    class Meta:
        ordering = ['-principal', 'tipo__nombre']
        unique_together = ('nna', 'tipo', 'valor')
        verbose_name = "Contacto del NNA"
        verbose_name_plural = "Contactos del NNA"

    def __str__(self):
        return f"{self.tipo}: {self.valor}"


class SeguimientoNNA(models.Model):
    """Registro transversal de seguimiento para el expediente integral del NNA."""
    AREA_CHOICES = [
        ('social', 'Social'),
        ('medica', 'Médica'),
        ('psicologica', 'Psicológica'),
        ('legal', 'Legal'),
        ('general', 'General'),
    ]
    ESTATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('concluido', 'Concluido'),
    ]

    nna = models.ForeignKey(
        NNA, on_delete=models.CASCADE, related_name='seguimientos'
    )
    area = models.CharField(max_length=20, choices=AREA_CHOICES)
    registrado_por = models.ForeignKey(
        Empleado, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguimientos_registrados'
    )
    fecha = models.DateField()
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    acuerdos = models.TextField(blank=True)
    proxima_accion = models.TextField(blank=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='pendiente')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-fecha_registro']
        verbose_name = "Seguimiento del NNA"
        verbose_name_plural = "Seguimientos del NNA"

    def __str__(self):
        return f"{self.get_area_display()} — {self.nna} — {self.titulo}"


class IdiomaNNA(models.Model):
    """Lenguas que habla el NNA (catálogo INALI)."""
    NIVEL_CHOICES = [
        ('basico',     'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado',   'Avanzado'),
        ('nativo',     'Nativo / Lengua materna'),
    ]
    nna               = models.ForeignKey(NNA, on_delete=models.CASCADE,
                                          related_name='idiomas')
    lengua            = models.ForeignKey(Lengua, on_delete=models.PROTECT)
    variante          = models.ForeignKey(VarianteLinguistica, on_delete=models.SET_NULL,
                                          null=True, blank=True)
    nivel             = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='nativo')
    nivel_competencia = models.ForeignKey(NivelCompetenciaOral, on_delete=models.PROTECT,
                                          null=True, blank=True,
                                          related_name='idiomas_nna')
    modo_adquisicion  = models.ForeignKey(ModoAdquisicionLengua, on_delete=models.PROTECT,
                                          null=True, blank=True,
                                          related_name='idiomas_nna')
    es_lengua_materna = models.BooleanField(default=False)
    preferente        = models.BooleanField(default=False)
    autodenominacion  = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('nna', 'lengua', 'variante')
        verbose_name = "Idioma del NNA"
        verbose_name_plural = "Idiomas del NNA"

    def __str__(self):
        return f"{self.nna} — {self.lengua}"

    @property
    def requiere_interprete(self):
        return bool(self.nivel_competencia and self.nivel_competencia.requiere_interprete)


class DiscapacidadNNA(models.Model):
    """Discapacidades del NNA (CIF/OMS + INEGI)."""
    GRADO_CHOICES = [
        ('leve',     'Leve'),
        ('moderada', 'Moderada'),
        ('severa',   'Severa'),
        ('total',    'Total'),
    ]
    CAUSA_CHOICES = [
        ('congenita',   'Congénita'),
        ('enfermedad',  'Por enfermedad'),
        ('accidente',   'Por accidente'),
        ('violencia',   'Por violencia'),
        ('otra',        'Otra'),
        ('desconocida', 'Desconocida'),
    ]
    nna                    = models.ForeignKey(NNA, on_delete=models.CASCADE,
                                               related_name='discapacidades')
    tipo                   = models.ForeignKey(TipoDiscapacidad, on_delete=models.PROTECT)
    discapacidad           = models.ForeignKey(Discapacidad, on_delete=models.PROTECT,
                                               null=True, blank=True)
    descripcion_especifica = models.TextField(blank=True)
    grado_dependencia      = models.CharField(max_length=20, choices=GRADO_CHOICES)
    grado_dependencia_catalogo = models.ForeignKey(
        GradoDependencia, on_delete=models.PROTECT,
        null=True, blank=True, related_name='discapacidades_nna'
    )
    causa                  = models.CharField(max_length=20, choices=CAUSA_CHOICES,
                                              default='desconocida')
    certificado_medico     = models.BooleanField(default=False)
    observaciones          = models.TextField(blank=True)

    class Meta:
        unique_together = ('nna', 'tipo', 'descripcion_especifica')
        verbose_name = "Discapacidad del NNA"
        verbose_name_plural = "Discapacidades del NNA"


class PadecimientoNNA(models.Model):
    """Enfermedades y padecimientos del NNA (CIE-10)."""
    nna                         = models.ForeignKey(NNA, on_delete=models.CASCADE,
                                                    related_name='padecimientos')
    enfermedad                  = models.ForeignKey(Enfermedad, on_delete=models.PROTECT)
    fecha_diagnostico           = models.DateField(null=True, blank=True)
    es_cronica                  = models.BooleanField(default=False)
    esta_controlada             = models.BooleanField(default=False)
    requiere_atencion_fundacion = models.BooleanField(default=False)
    medicamentos                = models.TextField(blank=True)
    observaciones_medicas       = models.TextField(blank=True)

    class Meta:
        unique_together = ('nna', 'enfermedad')
        verbose_name = "Padecimiento del NNA"
        verbose_name_plural = "Padecimientos del NNA"

    def __str__(self):
        return f"{self.nna} — {self.enfermedad}"


# ══════════════════════════════════════════════════════════════════════════════
# HECHO VICTIMAL — FUD (Ficha Única de Datos)
# Registra el delito que originó el desamparo del NNA.
# Campos basados en la FUD y la Caja de Herramientas NNABD.
# ══════════════════════════════════════════════════════════════════════════════

class HechoVictimal(models.Model):

    TIPO_DELITO_CHOICES = [
        ('homicidio',          'Homicidio doloso'),
        ('feminicidio',        'Feminicidio'),
        ('desaparicion',       'Desaparición forzada'),
        ('abandono',           'Abandono de persona'),
        ('violencia_familiar', 'Violencia familiar'),
        ('trata_personas',     'Trata de personas'),
        ('abuso_sexual',       'Abuso sexual'),
        ('lesiones',           'Lesiones graves'),
        ('otro',               'Otro delito'),
    ]
    AMBITO_CHOICES = [
        ('familiar',      'Familiar'),
        ('comunitario',   'Comunitario'),
        ('institucional', 'Institucional'),
        ('escolar',       'Escolar'),
        ('laboral',       'Laboral'),
        ('otro',          'Otro'),
    ]
    ESTATUS_JURIDICO_CHOICES = [
        ('denuncia_presentada',   'Denuncia presentada'),
        ('carpeta_investigacion', 'Carpeta de investigación / Av. previa'),
        ('proceso_judicial',      'En proceso judicial'),
        ('sentencia',             'Con sentencia'),
        ('sin_denuncia',          'Sin denuncia'),
        ('desconocido',           'Desconocido'),
    ]
    INSTITUCION_DERIVADORA_CHOICES = [
        ('fgr',            'FGR / Fiscalía'),
        ('dif',            'DIF'),
        ('imss',           'IMSS'),
        ('issste',         'ISSSTE'),
        ('ssalud',         'Secretaría de Salud'),
        ('inpi',           'INPI'),
        ('sociedad_civil', 'Sociedad Civil'),
        ('autoderiva',     'Se autoderiró / Familiar'),
        ('otro',           'Otro'),
    ]

    nna = models.OneToOneField(NNA, on_delete=models.CASCADE,
                               related_name='hecho_victimal')

    # --- Víctima directa (generalmente la madre) ---
    nombre_victima_directa = models.CharField(
        max_length=150, blank=True,
        help_text="Nombre completo de la víctima directa (ej. madre del NNA)"
    )
    parentesco_victima_nna = models.CharField(
        max_length=50, blank=True,
        help_text="Relación de la víctima con el NNA"
    )

    # --- Datos del delito ---
    tipo_delito        = models.CharField(max_length=30, choices=TIPO_DELITO_CHOICES)
    descripcion_delito = models.TextField(help_text="Descripción detallada del hecho (FUD)")
    fecha_hecho        = models.DateField(null=True, blank=True)
    hora_hecho         = models.TimeField(null=True, blank=True)
    ambito_ocurrencia  = models.CharField(max_length=20, choices=AMBITO_CHOICES, blank=True)
    lugar_hecho        = models.TextField(blank=True, help_text="Descripción del lugar")
    lugar_hecho_municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='hechos_victimales'
    )

    # --- Expediente jurídico ---
    numero_carpeta_investigacion = models.CharField(
        max_length=100, blank=True,
        help_text="Número de carpeta de investigación / av. previa"
    )
    fiscalia_o_ministerio      = models.CharField(max_length=200, blank=True,
                                                  help_text="Fiscalía o MP que lleva el caso")
    numero_expediente_judicial = models.CharField(max_length=100, blank=True)
    juzgado                    = models.CharField(max_length=200, blank=True)
    estatus_juridico           = models.CharField(max_length=30,
                                                  choices=ESTATUS_JURIDICO_CHOICES,
                                                  default='desconocido')
    hay_detenidos   = models.BooleanField(default=False)
    datos_detenidos = models.TextField(blank=True,
                                       help_text="Nombre(s) y relación con el NNA")

    # --- Impacto en el NNA ---
    nna_fue_testigo         = models.BooleanField(default=False,
                                                  help_text="¿El NNA presenció el hecho?")
    nna_tambien_victima     = models.BooleanField(default=False,
                                                  help_text="¿El NNA fue víctima directa?")
    descripcion_impacto_nna = models.TextField(blank=True,
                                               help_text="Impacto psicosocial en el NNA")

    # --- Derivación ---
    derivado_por                = models.CharField(max_length=200, blank=True)
    tipo_institucion_derivadora = models.CharField(max_length=30,
                                                   choices=INSTITUCION_DERIVADORA_CHOICES,
                                                   blank=True)

    # --- Registro ---
    registrado_por = models.ForeignKey(
        Empleado, on_delete=models.SET_NULL, null=True,
        related_name='hechos_registrados',
        limit_choices_to={'rol': 'trabajador_social'}
    )
    fecha_registro      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    observaciones       = models.TextField(blank=True)

    class Meta:
        verbose_name = "Hecho Victimal"
        verbose_name_plural = "Hechos Victimales"

    def __str__(self):
        return f"Hecho victimal — {self.nna} ({self.get_tipo_delito_display()})"


class DocumentoExpediente(models.Model):
    """Documentos digitalizados del expediente del NNA."""
    TIPO_DOC_CHOICES = [
        ('acta_nacimiento',       'Acta de Nacimiento'),
        ('curp',                  'CURP'),
        ('carpeta_investigacion', 'Carpeta de Investigación'),
        ('sentencia',             'Sentencia Judicial'),
        ('tutela_legal',          'Resolución de Tutela Legal'),
        ('identificacion_tutor',  'Identificación del Tutor'),
        ('fud',                   'Ficha Única de Datos (FUD)'),
        ('informe_medico',        'Informe Médico'),
        ('informe_psicologico',   'Informe Psicológico'),
        ('otro',                  'Otro'),
    ]

    nna             = models.ForeignKey(NNA, on_delete=models.CASCADE,
                                        related_name='documentos')
    tipo            = models.CharField(max_length=30, choices=TIPO_DOC_CHOICES)
    nombre_archivo  = models.CharField(max_length=255)
    archivo         = models.FileField(upload_to='expedientes/%Y/%m/', blank=True)
    descripcion     = models.TextField(blank=True)
    fecha_documento = models.DateField(null=True, blank=True)
    subido_por      = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True)
    fecha_subida    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_subida']
        verbose_name = "Documento del Expediente"
        verbose_name_plural = "Documentos del Expediente"

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.nna}"


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO DE RESTITUCIÓN DE DERECHOS  (Caja de Herramientas — Procuraduría)
# Fundamento: LGDNNA arts. 2, 6, 13, 18  ·  Caja de Herramientas, capítulo 4
#
# DISEÑO NORMALIZADO HASTA 5FN (PJ/NF):
#   · 1FN  — atributos atómicos; sin grupos repetidos.
#   · 2FN/3FN — sin dependencias parciales ni transitivas: los catálogos
#     (Derecho, InstitucionEjecutora) viven en su propia tabla.
#   · 4FN  — los hechos multivaluados (derechos de un plan, medidas de un
#     derecho, seguimientos de una medida) se separan en tablas propias.
#   · 5FN  — la relación n-aria NNA x Derecho x Institucion x Medida se
#     descompone en relaciones binarias encadenadas
#     (PlanRestitucion -> DerechoVulnerado -> MedidaProteccion -> Institucion),
#     de modo que toda dependencia de junta queda implicada por las claves
#     candidatas y el JOIN reconstruye los datos sin perdida ni espurios.
# ══════════════════════════════════════════════════════════════════════════════


class Derecho(models.Model):
    """Catalogo de los derechos del Art. 13 LGDNNA (enunciativo, no limitativo)."""
    clave       = models.CharField(max_length=6, unique=True,
                                   help_text="Fraccion del Art. 13, p.ej. 'IX'")
    nombre      = models.CharField(max_length=200, unique=True)
    fundamento  = models.CharField(max_length=200, blank=True,
                                   help_text="Articulo(s) LGDNNA que lo desarrollan")
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = "Derecho (Art. 13 LGDNNA)"
        verbose_name_plural = "Catalogo de Derechos (LGDNNA)"

    def __str__(self):
        return f"{self.clave}. {self.nombre}"


class InstitucionEjecutora(models.Model):
    """Catalogo de instituciones que ejecutan las medidas de proteccion especial."""
    NIVEL_CHOICES = [
        ('federal',        'Federal'),
        ('estatal',        'Estatal'),
        ('municipal',      'Municipal'),
        ('sociedad_civil', 'Sociedad civil'),
        ('internacional',  'Internacional'),
    ]
    TIPO_CHOICES = [
        ('salud',        'Salud'),
        ('educacion',    'Educacion'),
        ('dif',          'DIF'),
        ('procuraduria', 'Procuraduria de Proteccion'),
        ('fiscalia',     'Fiscalia / Ministerio Publico'),
        ('seguridad',    'Seguridad publica'),
        ('cdh',          'Comision de Derechos Humanos'),
        ('asistencia',   'Asistencia social'),
        ('otra',         'Otra'),
    ]
    nombre    = models.CharField(max_length=200)
    tipo      = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nivel     = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    contacto  = models.CharField(max_length=200, blank=True)
    telefono  = models.CharField(max_length=20, blank=True)
    domicilio = models.ForeignKey(Domicilio, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='instituciones')

    class Meta:
        ordering = ['nombre']
        unique_together = ('nombre', 'nivel')
        verbose_name = "Institucion Ejecutora"
        verbose_name_plural = "Instituciones Ejecutoras"

    def __str__(self):
        return self.nombre


class PlanRestitucion(models.Model):
    """
    Diagnostico de derechos restringidos + plan de restitucion (Caja 4.4).
    Un NNA puede tener varios planes en el tiempo, pero solo uno vigente.
    """
    GRADO_PELIGRO_CHOICES = [
        ('bajo',      'Bajo'),
        ('medio',     'Medio'),
        ('alto',      'Alto'),
        ('inminente', 'Riesgo inminente'),
    ]
    GRADO_COERCION_CHOICES = [
        ('nula',  'Nula'),
        ('baja',  'Baja'),
        ('media', 'Media'),
        ('alta',  'Alta'),
    ]
    ESTATUS_CHOICES = [
        ('diagnostico', 'En diagnostico'),
        ('ejecucion',   'En ejecucion'),
        ('seguimiento', 'En seguimiento'),
        ('concluido',   'Concluido'),
        ('suspendido',  'Suspendido'),
    ]

    nna   = models.ForeignKey(NNA, on_delete=models.CASCADE, related_name='planes_restitucion')
    folio = models.CharField(max_length=30, unique=True)

    fecha_apertura = models.DateField()
    elaborado_por  = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True,
                                       related_name='planes_elaborados')
    equipo         = models.ForeignKey(EquipoMultidisciplinario, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='planes')

    grado_peligro  = models.CharField(max_length=12, choices=GRADO_PELIGRO_CHOICES,
                                      help_text="Peligro a la integridad fisica/emocional (Caja 4.4.1)")
    grado_coercion = models.CharField(max_length=12, choices=GRADO_COERCION_CHOICES,
                                      help_text="Grado de coercion (Caja 4.4.2)")

    diagnostico_general            = models.TextField(blank=True)
    determinacion_interes_superior = models.TextField(
        blank=True, help_text="Evaluacion y determinacion del interes superior (LGDNNA Art. 18)")

    estatus      = models.CharField(max_length=15, choices=ESTATUS_CHOICES, default='diagnostico')
    vigente      = models.BooleanField(default=True)
    fecha_cierre = models.DateField(null=True, blank=True)

    fecha_registro      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_apertura']
        verbose_name = "Plan de Restitucion de Derechos"
        verbose_name_plural = "Planes de Restitucion de Derechos"
        constraints = [
            models.UniqueConstraint(
                fields=['nna'],
                condition=models.Q(vigente=True),
                name='un_plan_vigente_por_nna',
            ),
        ]

    def __str__(self):
        return f"Plan {self.folio} - {self.nna}"


class DerechoVulnerado(models.Model):
    """Relacion normalizada Plan x Derecho: que derechos estan restringidos."""
    GRADO_CHOICES = [
        ('riesgo',      'En riesgo'),
        ('restringido', 'Restringido'),
        ('vulnerado',   'Vulnerado'),
    ]
    plan        = models.ForeignKey(PlanRestitucion, on_delete=models.CASCADE,
                                    related_name='derechos_vulnerados')
    derecho     = models.ForeignKey(Derecho, on_delete=models.PROTECT,
                                    related_name='vulneraciones')
    grado       = models.CharField(max_length=12, choices=GRADO_CHOICES, default='vulnerado')
    descripcion = models.TextField(blank=True)

    class Meta:
        unique_together = ('plan', 'derecho')
        verbose_name = "Derecho Vulnerado"
        verbose_name_plural = "Derechos Vulnerados"

    def __str__(self):
        return f"{self.derecho.clave} - {self.get_grado_display()}"


class MedidaProteccion(models.Model):
    """Medida de proteccion especial para restituir un derecho (Caja 4.5)."""
    TIPO_CHOICES = [
        ('urgente',   'Urgente / cautelar'),
        ('especial',  'Proteccion especial'),
        ('ordinaria', 'Ordinaria'),
    ]
    ESTATUS_CHOICES = [
        ('solicitada',  'Solicitada'),
        ('en_proceso',  'En proceso'),
        ('cumplida',    'Cumplida'),
        ('no_cumplida', 'No cumplida'),
        ('cancelada',   'Cancelada'),
    ]
    derecho_vulnerado = models.ForeignKey(DerechoVulnerado, on_delete=models.CASCADE,
                                          related_name='medidas')
    institucion       = models.ForeignKey(InstitucionEjecutora, on_delete=models.PROTECT,
                                          related_name='medidas')
    tipo          = models.CharField(max_length=12, choices=TIPO_CHOICES, default='especial')
    descripcion   = models.TextField()
    judicializada = models.BooleanField(default=False,
                                        help_text="Se promovio judicializacion? (Caja 4.5.2.b)")
    responsable   = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='medidas_responsable')

    fecha_solicitud  = models.DateField(null=True, blank=True)
    fecha_inicio     = models.DateField(null=True, blank=True)
    fecha_conclusion = models.DateField(null=True, blank=True)
    estatus          = models.CharField(max_length=12, choices=ESTATUS_CHOICES, default='solicitada')

    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name = "Medida de Proteccion"
        verbose_name_plural = "Medidas de Proteccion"

    def __str__(self):
        return f"Medida ({self.get_tipo_display()}) - {self.derecho_vulnerado.derecho.clave}"


class SeguimientoMedida(models.Model):
    """Bitacora de seguimiento a la ejecucion de cada medida (Caja 4.6)."""
    medida            = models.ForeignKey(MedidaProteccion, on_delete=models.CASCADE,
                                          related_name='seguimientos')
    fecha             = models.DateField()
    avance            = models.TextField()
    porcentaje_avance = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Avance acumulado de la medida (0-100)")
    registrado_por    = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True,
                                          related_name='seguimientos_medida')
    evidencia         = models.FileField(upload_to='seguimientos/%Y/%m/', blank=True)
    fecha_registro    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Seguimiento de Medida"
        verbose_name_plural = "Seguimientos de Medidas"

    def __str__(self):
        return f"Seguimiento {self.fecha} - {self.porcentaje_avance}%"


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO DE PRIVACIDAD Y PROTECCIÓN DE DATOS PERSONALES
# Fundamento: LGDNNA arts. 76-80 (intimidad y datos personales del NNA),
# aviso de privacidad y derechos ARCO del FUD, Ley de Proteccion de Datos.
# ══════════════════════════════════════════════════════════════════════════════


class ConsentimientoDatos(models.Model):
    """
    Consentimiento informado para el tratamiento de datos personales sensibles
    del NNA, otorgado por quien ejerce patria potestad/tutela (LGDNNA Art. 78).
    """
    nna           = models.OneToOneField(NNA, on_delete=models.CASCADE,
                                         related_name='consentimiento')
    otorgado_por  = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='consentimientos')
    version_aviso = models.CharField(max_length=20, default='1.0')
    finalidad     = models.TextField(help_text="Finalidad del tratamiento informada al titular")

    acepta_tratamiento                = models.BooleanField(default=False)
    acepta_datos_sensibles            = models.BooleanField(default=False)
    permite_uso_estadistico_disociado = models.BooleanField(
        default=True, help_text="Permite uso estadistico previa disociacion (anonimizacion)")

    fecha_otorgamiento = models.DateField(null=True, blank=True)
    fecha_revocacion   = models.DateField(null=True, blank=True)
    documento          = models.FileField(upload_to='consentimientos/%Y/%m/', blank=True)
    fecha_registro     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Consentimiento de Datos"
        verbose_name_plural = "Consentimientos de Datos"

    @property
    def vigente(self):
        return self.acepta_tratamiento and self.fecha_revocacion is None

    def __str__(self):
        estado = 'vigente' if self.vigente else 'no vigente'
        return f"Consentimiento - {self.nna} ({estado})"


class SolicitudARCO(models.Model):
    """Ejercicio de derechos ARCO y revocacion (aviso de privacidad del FUD)."""
    TIPO_CHOICES = [
        ('acceso',        'Acceso'),
        ('rectificacion', 'Rectificacion'),
        ('cancelacion',   'Cancelacion'),
        ('oposicion',     'Oposicion'),
        ('revocacion',    'Revocacion del consentimiento'),
    ]
    ESTATUS_CHOICES = [
        ('recibida',     'Recibida'),
        ('en_tramite',   'En tramite'),
        ('procedente',   'Procedente'),
        ('improcedente', 'Improcedente'),
    ]
    nna             = models.ForeignKey(NNA, on_delete=models.CASCADE,
                                        related_name='solicitudes_arco')
    tipo            = models.CharField(max_length=15, choices=TIPO_CHOICES)
    solicitante     = models.CharField(max_length=150,
                                       help_text="Persona que ejerce el derecho ARCO")
    descripcion     = models.TextField(blank=True)
    fecha_solicitud = models.DateField()
    estatus         = models.CharField(max_length=15, choices=ESTATUS_CHOICES, default='recibida')
    fecha_respuesta = models.DateField(null=True, blank=True)
    resolucion      = models.TextField(blank=True)
    atendida_por    = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='arco_atendidas')

    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name = "Solicitud ARCO"
        verbose_name_plural = "Solicitudes ARCO"

    def __str__(self):
        return f"ARCO {self.get_tipo_display()} - {self.nna}"


class BitacoraAcceso(models.Model):
    """
    Registro de auditoria de acceso a datos personales sensibles de NNA
    (LGDNNA Art. 76). Se puebla automaticamente via signals + middleware.
    """
    ACCION_CHOICES = [
        ('consulta',     'Consulta'),
        ('creacion',     'Creacion'),
        ('modificacion', 'Modificacion'),
        ('eliminacion',  'Eliminacion'),
        ('exportacion',  'Exportacion'),
    ]
    usuario    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='accesos')
    accion     = models.CharField(max_length=15, choices=ACCION_CHOICES)
    modelo     = models.CharField(max_length=80)
    objeto_id  = models.CharField(max_length=40, blank=True)
    nna        = models.ForeignKey(NNA, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='accesos_bitacora')
    ip         = models.GenericIPAddressField(null=True, blank=True)
    detalle    = models.CharField(max_length=255, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = "Bitacora de Acceso"
        verbose_name_plural = "Bitacora de Accesos"

    def __str__(self):
        return f"{self.fecha_hora:%Y-%m-%d %H:%M} - {self.usuario} - {self.accion} - {self.modelo}"


# ==============================================================================
# CONTACTOS MULTIPLES (telefonos / correos) para Tutor y Empleado
# Mismo patron que ContactoNNA, usando el catalogo TipoContacto.
# ==============================================================================


class ContactoTutor(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='contactos')
    tipo = models.ForeignKey(TipoContacto, on_delete=models.PROTECT, related_name='contactos_tutor')
    valor = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200, blank=True)
    principal = models.BooleanField(default=False)

    class Meta:
        ordering = ['-principal', 'tipo__nombre']
        unique_together = ('tutor', 'tipo', 'valor')
        verbose_name = "Contacto del Tutor"
        verbose_name_plural = "Contactos del Tutor"

    def __str__(self):
        return f"{self.tutor} - {self.valor}"


class ContactoEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='contactos')
    tipo = models.ForeignKey(TipoContacto, on_delete=models.PROTECT, related_name='contactos_empleado')
    valor = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200, blank=True)
    principal = models.BooleanField(default=False)

    class Meta:
        ordering = ['-principal', 'tipo__nombre']
        unique_together = ('empleado', 'tipo', 'valor')
        verbose_name = "Contacto del Empleado"
        verbose_name_plural = "Contactos del Empleado"

    def __str__(self):
        return f"{self.empleado} - {self.valor}"
