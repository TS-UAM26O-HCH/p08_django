################CODIGO 6############################
class DatosInvalidos_400(Exception):
    def __init__(self, message="Datos inválidos"):
        super().__init__(message)


class ProductoNoEncontrado_404(Exception):
    def __init__(self, message="Producto no encontrado"):
        super().__init__(message)


class ConflictoProducto_409(Exception):
    def __init__(self, message="Conflicto (product_key ya registrado)"):
        super().__init__(message)


class ErrorInternoServidor_500(Exception):
    def __init__(self, message="Error interno del servidor"):
        super().__init__(message)


class ProductoNoAutorizado_401(Exception):
    def __init__(self, message="No autorizado"):
        super().__init__(message)


class ProductoProhibido_403(Exception):
    def __init__(self, message="Prohibido"):
        super().__init__(message)
