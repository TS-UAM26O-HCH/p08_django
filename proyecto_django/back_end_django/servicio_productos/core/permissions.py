from rest_framework.permissions import BasePermission


class IsStaffFromToken(BasePermission):
    """Permiso de administrador basado en los claims del JWT.

    servicio_productos no tiene la tabla de usuarios de auth, por lo que
    ``IsAdminUser`` nativo no funciona (el ``TokenUser`` de SimpleJWT no
    consulta la BD). servicio_auth incluye ``is_staff`` e ``is_superuser``
    como claims al firmar el token; aquí se leen del token validado
    (``request.auth``) con respaldo a ``request.user``.
    """

    message = "Se requieren permisos de administrador."

    def has_permission(self, request, view):
        user = request.user
        if user is not None and getattr(user, "is_staff", False):
            return True
        token = request.auth
        if token is not None:
            payload = getattr(token, "payload", {}) or {}
            if payload.get("is_staff") or payload.get("is_superuser"):
                return True
        return False
