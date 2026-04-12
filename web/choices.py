"""
Constantes de choices reutilizables.

Centraliza las tuplas de opciones que se repiten en varios modelos
(Empleado, Tutor, NNA y sus tablas relacionadas) para cumplir con el
principio DRY y facilitar futuras modificaciones.
"""

# ── Sexo ──────────────────────────────────────────────────────────────────────
SEXO_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Femenino'),
    ('O', 'Otro'),
]

SEXO_NNA_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Femenino'),
    ('O', 'Otro / No binario'),
]

# ── Escolaridad ───────────────────────────────────────────────────────────────
ESCOLARIDAD_TUTOR_CHOICES = [
    ('sin_escolaridad',     'Sin escolaridad'),
    ('primaria_incompleta', 'Primaria incompleta'),
    ('primaria',            'Primaria'),
    ('secundaria',          'Secundaria'),
    ('preparatoria',        'Preparatoria / Bachillerato'),
    ('tecnico',             'Técnico / Vocacional'),
    ('licenciatura',        'Licenciatura'),
    ('posgrado',            'Posgrado'),
]

ESCOLARIDAD_NNA_CHOICES = [
    ('sin_escolaridad',       'Sin escolaridad'),
    ('preescolar',            'Preescolar'),
    ('primaria_incompleta',   'Primaria incompleta'),
    ('primaria',              'Primaria'),
    ('secundaria_incompleta', 'Secundaria incompleta'),
    ('secundaria',            'Secundaria'),
    ('preparatoria',          'Preparatoria / Bachillerato'),
    ('otro',                  'Otro'),
]

# ── Nivel de idioma (IdiomaTutor / IdiomaNNA) ────────────────────────────────
NIVEL_IDIOMA_CHOICES = [
    ('basico',     'Básico'),
    ('intermedio', 'Intermedio'),
    ('avanzado',   'Avanzado'),
    ('nativo',     'Nativo / Lengua materna'),
]

# ── Grado de dependencia (DiscapacidadTutor / DiscapacidadNNA) ───────────────
GRADO_DEPENDENCIA_TUTOR_CHOICES = [
    ('leve',     'Leve — no requiere apoyo permanente'),
    ('moderada', 'Moderada — requiere apoyo parcial'),
    ('severa',   'Severa — requiere apoyo permanente'),
    ('total',    'Total — dependencia completa'),
]

GRADO_DEPENDENCIA_NNA_CHOICES = [
    ('leve',     'Leve'),
    ('moderada', 'Moderada'),
    ('severa',   'Severa'),
    ('total',    'Total'),
]

# ── Causa de discapacidad (compartida Tutor  y NNA) ──────────────────────────
CAUSA_DISCAPACIDAD_CHOICES = [
    ('congenita',   'Congénita'),
    ('enfermedad',  'Por enfermedad'),
    ('accidente',   'Por accidente'),
    ('violencia',   'Por violencia'),
    ('otra',        'Otra'),
    ('desconocida', 'Desconocida'),
]
