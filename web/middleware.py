"""
web/middleware.py
────────────────────────────────────────────────────────────────────────────
Middleware de auditoría: expone el request actual (usuario + IP) a las señales
de modelo mediante un almacenamiento thread-local, para poder registrar QUIÉN
accede o modifica datos personales sensibles de NNA (LGDNNA Art. 76).
"""
import threading

_local = threading.local()


def get_current_request():
    """Devuelve el request en curso para este hilo, o None fuera de una vista."""
    return getattr(_local, "request", None)


class AuditoriaMiddleware:
    """Guarda el request en thread-local durante el ciclo de la petición."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.request = request
        try:
            response = self.get_response(request)
        finally:
            _local.request = None
        return response
