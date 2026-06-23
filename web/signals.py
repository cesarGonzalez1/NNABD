"""
web/signals.py
────────────────────────────────────────────────────────────────────────────
Auditoría automática de datos personales sensibles (LGDNNA Art. 76).

Registra en BitacoraAcceso toda creación / modificación / eliminación de los
modelos que contienen información sensible de NNA. El usuario y la IP se toman
del request en curso (web.middleware.AuditoriaMiddleware). Si la operación
ocurre fuera de una petición HTTP (shell, comando, seed) se registra sin
usuario, pero el evento queda trazado igual.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .middleware import get_current_request
from .models import (
    BitacoraAcceso,
    NNA, Tutor, HechoVictimal, DocumentoExpediente, SeguimientoNNA,
    ContactoNNA, IdiomaNNA, DiscapacidadNNA, PadecimientoNNA,
    PlanRestitucion, DerechoVulnerado,
)

# Modelos cuyo acceso debe quedar auditado.
MODELOS_SENSIBLES = (
    NNA, Tutor, HechoVictimal, DocumentoExpediente, SeguimientoNNA,
    ContactoNNA, IdiomaNNA, DiscapacidadNNA, PadecimientoNNA,
    PlanRestitucion, DerechoVulnerado,
)


def _contexto():
    """(usuario, ip) del request actual, o (None, None) fuera de una vista."""
    req = get_current_request()
    if req is None:
        return None, None
    user = getattr(req, "user", None)
    if not getattr(user, "is_authenticated", False):
        user = None
    ip = req.META.get("REMOTE_ADDR")
    return user, ip


def _nna_asociado(instance):
    """Mejor esfuerzo para asociar el evento con un NNA, sin consultas extra."""
    if isinstance(instance, NNA):
        return instance
    nna = getattr(instance, "nna", None)
    return nna if isinstance(nna, NNA) else None


def _registrar(instance, accion):
    if not isinstance(instance, MODELOS_SENSIBLES):
        return
    user, ip = _contexto()
    BitacoraAcceso.objects.create(
        usuario=user,
        accion=accion,
        modelo=type(instance).__name__,
        objeto_id=str(getattr(instance, "pk", "")),
        nna=_nna_asociado(instance),
        ip=ip,
    )


@receiver(post_save)
def auditar_guardado(sender, instance, created, **kwargs):
    _registrar(instance, "creacion" if created else "modificacion")


@receiver(post_delete)
def auditar_eliminacion(sender, instance, **kwargs):
    _registrar(instance, "eliminacion")
