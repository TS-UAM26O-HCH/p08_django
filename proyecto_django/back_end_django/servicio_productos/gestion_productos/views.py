import logging  # ← NUEVO
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .DAO.productoDAO import ProductoDAO
from .serializers import ProductoCompletoSerializer, ProductoParcialSerializer
from gestion_productos.serializers import (
    ProductoCompletoSerializer,
    ProductoParcialSerializer,
)
from gestion_productos.exceptions.productoExceptions import (
    DatosInvalidos_400,
    ProductoNoEncontrado_404,
    ConflictoProducto_409,
    ErrorInternoServidor_500,
    ProductoNoAutorizado_401,
    ProductoProhibido_403,
)

# ── Loggers ────────────────────────────────────────────────────────────────────
logger = logging.getLogger("gestion_productos")  # técnico
logger_auditoria = logging.getLogger("auditoria")  # auditoría


def obtener_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "IP desconocida")


class ProductoViewSet(viewsets.ViewSet):
    """
    API para la gestión de Productos.
    """

    @swagger_auto_schema(
        operation_summary="Obtener todos los productos",
        responses={
            200: "Éxito",
            401: "No autorizado",
            403: "Prohibido",
            500: "Error interno del servidor",
        },
    )
    def list(self, request, *args, **kwargs):
        """Devuelve una lista de todos los productos."""
        try:
            logger.debug("Solicitando lista de todos los productos")  # ← NUEVO
            productos = ProductoDAO.obtener_todos()
            serializer = ProductoCompletoSerializer(productos, many=True)
            logger.info(
                f"Lista de productos devuelta: {len(serializer.data)} registros"
            )  # ← NUEVO
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ProductoNoAutorizado_401 as e:
            logger.warning(f"Acceso no autorizado a lista de productos: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except ProductoProhibido_403 as e:
            logger.warning(f"Acceso prohibido a lista de productos: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno al listar productos: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Obtener un producto por ID",
        responses={
            200: "Éxito",
            401: "No Autorizado",
            403: "Prohibido",
            404: "Producto no encontrado",
            500: "Error interno del servidor",
        },
    )
    def retrieve(self, request, pk=None):
        """Obtiene los detalles de un producto específico."""
        try:
            logger.debug(f"Solicitando producto con id={pk}")  # ← NUEVO
            producto = ProductoDAO.obtener_producto_por_id(pk)
            serializer = ProductoCompletoSerializer(producto)
            logger.info(f"Producto id={pk} devuelto correctamente")  # ← NUEVO
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ProductoNoAutorizado_401 as e:
            logger.warning(f"No autorizado para retrieve producto id={pk}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except ProductoProhibido_403 as e:
            logger.warning(f"Prohibido retrieve producto id={pk}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto id={pk} no encontrado en retrieve")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno en retrieve producto id={pk}: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crear un nuevo producto",
        request_body=ProductoCompletoSerializer,
        responses={
            201: "Producto creado exitosamente",
            400: "Error en la validación",
            409: "Conflicto",
            500: "Error interno del servidor",
        },
    )
    def create(self, request):
        """Crea un nuevo producto con la información proporcionada."""
        ip = obtener_ip(request)
        try:
            logger.debug(
                f"Intentando crear producto: {request.data.get('product_key')}"
            )  # ← NUEVO
            producto = ProductoDAO.crear_producto(**request.data)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:CREAR_PRODUCTO] "
                f"[realizado_por:{request.user}] "
                f"[product_key:{request.data.get('product_key')}]"
            )
            return Response(
                ProductoCompletoSerializer(producto).data,
                status=status.HTTP_201_CREATED,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Datos inválidos al crear producto: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ConflictoProducto_409 as e:
            logger.warning(
                f"Conflicto al crear producto {request.data.get('product_key')}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno al crear producto: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Actualizar un producto (completo)",
        request_body=ProductoCompletoSerializer,
        responses={
            200: "Producto actualizado exitosamente",
            400: "Datos inválidos",
            404: "Producto no encontrado",
            409: "Conflicto",
            500: "Error interno",
        },
    )
    def update(self, request, pk=None):
        """Actualiza completamente un producto especificado por su ID."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando actualizar producto id={pk}")  # ← NUEVO
            productoDTO = ProductoDAO.actualizar_producto(pk, **request.data)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_PRODUCTO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                ProductoCompletoSerializer(productoDTO).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(
                f"Datos inválidos al actualizar producto id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto id={pk} no encontrado al actualizar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoProducto_409 as e:
            logger.warning(f"Conflicto al actualizar producto id={pk}: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno al actualizar producto id={pk}: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Actualizar un producto (parcialmente)",
        request_body=ProductoParcialSerializer,
        responses={
            200: "Producto actualizado parcialmente",
            400: "Datos inválidos",
            404: "Producto no encontrado",
            409: "Conflicto",
            500: "Error interno",
        },
    )
    def partial_update(self, request, pk=None):
        """Actualiza parcialmente un producto especificado por su ID."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Actualización parcial producto id={pk}")  # ← NUEVO
            productoDTO = ProductoDAO.actualizar_producto_parcial(pk, **request.data)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_PARCIAL_PRODUCTO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                ProductoParcialSerializer(productoDTO).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(
                f"Datos inválidos en partial_update producto id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ProductoNoEncontrado_404 as e:
            logger.warning(
                f"Producto id={pk} no encontrado en partial_update"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoProducto_409 as e:
            logger.warning(
                f"Conflicto en partial_update producto id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno en partial_update producto id={pk}: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Elimina un producto (borrado lógico).",
        responses={
            200: "Producto eliminado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Producto no encontrado",
        },
    )
    def destroy(self, request, pk=None):
        """Marca el producto como eliminado sin borrarlo físicamente."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando eliminar producto id={pk}")  # ← NUEVO
            ProductoDAO.eliminar_producto(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ELIMINAR_PRODUCTO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {"mensaje": "Producto eliminado correctamente"},
                status=status.HTTP_200_OK,
            )

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto id={pk} no encontrado al eliminar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"ValueError al eliminar producto id={pk}: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Restaurar un producto eliminado.",
        responses={
            200: "Producto restaurado exitosamente",
            401: "No autorizado",
            400: "El producto no estaba eliminado",
            404: "Producto no encontrado",
        },
    )
    def restore(self, request, pk=None):
        """Restaura un producto eliminado lógicamente."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Restaurando producto id={pk}")  # ← NUEVO
            ProductoDAO.restaurar_producto(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:RESTAURAR_PRODUCTO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {"mensaje": "Producto restaurado correctamente"},
                status=status.HTTP_200_OK,
            )

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto id={pk} no encontrado al restaurar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            logger.warning(
                f"ValidationError al restaurar producto id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="search")
    @swagger_auto_schema(
        operation_summary="Buscar productos por nombre o descripción",
        manual_parameters=[
            openapi.Parameter(
                "q",
                openapi.IN_QUERY,
                description="Texto a buscar en nombre o descripción",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: ProductoCompletoSerializer(many=True),
            400: "Consulta inválida",
            401: "No autorizado",
            403: "Prohibido",
            404: "No se encontraron productos",
            500: "Error interno",
        },
    )
    def search(self, request):
        query = request.GET.get("q", "")
        if not query:
            logger.warning("Búsqueda de productos sin parámetro 'q'")  # ← NUEVO
            return Response(
                {"error": "Debe proporcionar un parámetro de búsqueda"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.debug(f"Búsqueda de productos con query='{query}'")  # ← NUEVO
        productos = ProductoDAO.buscar_productos(query)
        serializer = ProductoCompletoSerializer(productos, many=True)
        logger.info(
            f"Búsqueda '{query}' devolvió {len(serializer.data)} resultados"
        )  # ← NUEVO
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Actualizar imagen de producto",
        manual_parameters=[
            openapi.Parameter(
                "image_link",
                openapi.IN_QUERY,
                description="URL válida, máximo 200 caracteres",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: "Imagen actualizada exitosamente",
            400: "URL inválida",
            404: "Producto no encontrado",
            500: "Error interno",
        },
    )
    def update_image(self, request, pk=None):
        """Actualiza la URL de la imagen de un producto específico."""
        ip = obtener_ip(request)
        try:
            img = request.GET.get("image_link", "")
            logger.debug(f"Actualizando imagen de producto id={pk}")  # ← NUEVO
            producto = ProductoDAO.actualizar_img(pk, img)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_IMAGEN_PRODUCTO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {
                    "codigo": 200,
                    "mensaje": "Imagen del producto actualizada exitosamente.",
                    "resultado": {
                        "id": str(producto.id),
                        "image_link": producto.image_link,
                        "modified_at": producto.modified_at.isoformat(),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except ProductoNoEncontrado_404 as e:
            logger.warning(
                f"Producto id={pk} no encontrado al actualizar imagen"
            )  # ← NUEVO
            return Response(
                {
                    "codigo": 404,
                    "mensaje": "Producto no encontrado.",
                    "resultado": "null",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError:
            logger.warning(f"URL de imagen inválida para producto id={pk}")  # ← NUEVO
            return Response(
                {
                    "codigo": 400,
                    "mensaje": "La URL de la imagen no es válida o excede el límite.",
                    "resultado": "null",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(
                f"Error inesperado al actualizar imagen producto id={pk}: {e}",  # ← NUEVO
                exc_info=True,
            )
            return Response(
                {
                    "codigo": 500,
                    "mensaje": "Error interno del servidor al actualizar la imagen.",
                    "resultado": "null",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Desactivar un producto",
        responses={
            200: "Producto desactivado exitosamente",
            401: "No autorizado",
            400: "El producto ya estaba desactivado",
            403: "Prohibido",
            404: "Producto no encontrado",
            500: "Error interno",
        },
    )
    def deactivate(self, request, pk=None):
        """Desactiva un producto estableciendo el campo status en false."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Desactivando producto id={pk}")  # ← NUEVO
            producto = ProductoDAO.desactivar_producto(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:DESACTIVAR_PRODUCTO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {
                    "codigo": 200,
                    "mensaje": "Producto desactivado exitosamente.",
                    "resultado": {
                        "id": str(producto.id),
                        "status": producto.status,
                        "modified_at": producto.modified_at.isoformat(),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto id={pk} no encontrado al desactivar")  # ← NUEVO
            return Response(
                {"codigo": 404, "mensaje": str(e)}, status=status.HTTP_404_NOT_FOUND
            )

        except ValidationError as e:
            logger.warning(f"Producto id={pk} ya estaba desactivado: {e}")  # ← NUEVO
            return Response(
                {"codigo": 400, "mensaje": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(
                f"Error inesperado al desactivar producto id={pk}: {e}",  # ← NUEVO
                exc_info=True,
            )
            return Response(
                {
                    "codigo": 500,
                    "mensaje": "Error interno del servidor",
                    "detalle": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Activar un producto",
        responses={
            200: "Producto activado correctamente",
            401: "No autorizado",
            400: "El producto ya estaba activado",
            404: "Producto no encontrado",
        },
    )
    def activate(self, request, pk=None):
        """Activa un producto estableciendo el campo status en true."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Activando producto id={pk}")  # ← NUEVO
            ProductoDAO.activar_producto(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ACTIVAR_PRODUCTO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {"mensaje": "Producto activado correctamente"},
                status=status.HTTP_200_OK,
            )

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto id={pk} no encontrado al activar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            logger.warning(f"Producto id={pk} ya estaba activado: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
