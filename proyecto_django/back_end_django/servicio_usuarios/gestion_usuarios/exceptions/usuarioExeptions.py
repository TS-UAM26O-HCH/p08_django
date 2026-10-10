class DatosInvalidos_400(Exception):
    """Excepción para cuando los datos enviados son inválidos (Código 400)."""

    def __init__(self, mensaje="Datos inválidos"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class UsuarioNoAutorizado_401(Exception):
    """Excepción para cuando un usuario no está autorizado (Código 401)."""

    def __init__(self, mensaje="No autorizado"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class UsuarioProhibido_403(Exception):
    """Excepción para cuando un usuario tiene el acceso prohibido (Código 403)."""

    def __init__(self, mensaje="Prohibido"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class UsuarioNoEncontrado_404(Exception):
    """Excepción para cuando no se encuentra un usuario (Código 404)."""

    def __init__(self, mensaje="Usuario no encontrado"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ConflictoUsuario_409(Exception):
    """Excepción para conflictos como nombre de usuario o correo ya registrado (Código 409)."""

    def __init__(self, mensaje="Conflicto (nombre de usuario o email ya registrado)"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ErrorInternoServidor_500(Exception):
    """Excepción para errores internos del servidor (Código 500)."""

    def __init__(self, mensaje="Error interno del servidor"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)
