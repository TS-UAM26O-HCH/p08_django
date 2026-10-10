import logging  # ← NUEVO
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema

from gestion_usuarios.DAO.usuarioDAO import UsuarioDAO

from gestion_usuarios.serializers import (
    UsuarioParcialSerializer,
    UsuarioCompletoSerializer,
    UsuarioContrasenaSerializer,
    PasswordResetRequestSerializer,
)

from gestion_usuarios.exceptions.usuarioExeptions import (
    DatosInvalidos_400,
    UsuarioNoEncontrado_404,
    ConflictoUsuario_409,
    ErrorInternoServidor_500,
    UsuarioNoAutorizado_401,
    UsuarioProhibido_403,
)

# ── Loggers ────────────────────────────────────────────────────────────────────
# Van aquí, fuera de la clase, después de los imports y antes de class
logger = logging.getLogger("gestion_usuarios")  # técnico
logger_auditoria = logging.getLogger("auditoria")  # auditoría


def obtener_ip(request):
    """Extrae la IP real considerando proxies."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "IP desconocida")


class UsuarioViewSet(viewsets.ViewSet):
    """
    API para la gestión de Usuarios.
    """

    @swagger_auto_schema(
        operation_summary="Obtener todos los usuarios",
        responses={
            200: "Éxito",
            401: "No autorizado",
            403: "Prohibido",
            500: "Error interno del servidor",
        },
    )
    def list(self, request, *args, **kwargs):
        """Devuelve una lista de todos los usuarios."""
        try:
            logger.debug("Solicitando lista de todos los usuarios")  # ← NUEVO
            usuarios = UsuarioDAO.obtener_todos()
            serializer = UsuarioCompletoSerializer(usuarios, many=True)
            logger.info(
                f"Lista de usuarios devuelta: {len(serializer.data)} registros"
            )  # ← NUEVO
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UsuarioNoAutorizado_401 as e:
            logger.warning(f"Acceso no autorizado a lista de usuarios: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except UsuarioProhibido_403 as e:
            logger.warning(f"Acceso prohibido a lista de usuarios: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno al listar usuarios: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Obtener un usuario por ID",
        responses={
            200: "Exito",
            401: "No Autorizado",
            403: "Prohibido",
            404: "Usuario no encontrado",
            500: "Error interno del servidor",
        },
    )
    def retrieve(self, request, pk=None):
        """Devuelve un usuario específico si existe."""
        try:
            logger.debug(f"Solicitando usuario con id={pk}")  # ← NUEVO
            usuario = UsuarioDAO.obtener_usuario_por_id(pk)
            serializer = UsuarioCompletoSerializer(usuario)
            logger.info(f"Usuario id={pk} devuelto correctamente")  # ← NUEVO
            return Response(serializer.data, status=status.HTTP_200_OK)

        except DatosInvalidos_400 as e:
            logger.warning(f"ID inválido en retrieve usuario id={pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            logger.warning(f"ValueError en retrieve usuario id={pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except UsuarioNoAutorizado_401 as e:
            logger.warning(f"No autorizado para retrieve usuario id={pk}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except UsuarioProhibido_403 as e:
            logger.warning(f"Prohibido retrieve usuario id={pk}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario id={pk} no encontrado en retrieve")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno en retrieve usuario id={pk}: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crear un nuevo usuario",
        request_body=UsuarioParcialSerializer,
        responses={
            201: "Usuario creado exitosamente",
            400: "Error en la validación",
            409: "Conflicto",
            500: "Error interno del servidor",
        },
    )
    def create(self, request):
        """Crea un nuevo usuario con la información proporcionada."""
        ip = obtener_ip(request)
        try:
            logger.debug(
                f"Intentando crear usuario: {request.data.get('username')}"
            )  # ← NUEVO
            usuario_dto = UsuarioDAO.crear_usuario(**request.data)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:CREAR_USUARIO] "
                f"[realizado_por:{request.user}] "
                f"[nuevo_usuario:{request.data.get('username')}]"
            )
            return Response(
                UsuarioCompletoSerializer(usuario_dto).data,
                status=status.HTTP_201_CREATED,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Datos inválidos al crear usuario: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ConflictoUsuario_409 as e:
            logger.warning(
                f"Conflicto al crear usuario {request.data.get('username')}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno al crear usuario: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Actualizar un usuario completamente",
        request_body=UsuarioCompletoSerializer,
        responses={
            200: "Usuario actualizado exitosamente",
            400: "Datos inválidos",
            404: "Usuario no encontrado",
            409: "Conflicto",
            500: "Error interno",
        },
    )
    def update(self, request, pk=None):
        """Actualiza completamente un usuario especificado por su id."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando actualizar usuario id={pk}")  # ← NUEVO
            usuarioDTO = UsuarioDAO.actualizar_usuario(pk, **request.data)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_USUARIO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                UsuarioCompletoSerializer(usuarioDTO).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(
                f"Datos inválidos al actualizar usuario id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario id={pk} no encontrado al actualizar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoUsuario_409 as e:
            logger.warning(f"Conflicto al actualizar usuario id={pk}: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno al actualizar usuario id={pk}: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Elimina un usuario (borrado lógico).",
        responses={
            200: "Usuario eliminado Correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def destroy(self, request, pk=None):
        """Marca el usuario como eliminado sin borrarlo físicamente."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando eliminar usuario id={pk}")  # ← NUEVO
            UsuarioDAO.eliminar_usuario(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ELIMINAR_USUARIO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {"mensaje": "Usuario eliminado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario id={pk} no encontrado al eliminar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"ID inválido al eliminar usuario id={pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            logger.warning(f"ValueError al eliminar usuario id={pk}: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Actualizar un usuario (parcial)",
        request_body=UsuarioParcialSerializer,
        responses={
            200: "Usuario actualizado parcialmente",
            400: "Datos inválidos",
            404: "Usuario no encontrado",
            409: "Conflicto",
            500: "Error interno",
        },
    )
    def partial_update(self, request, pk=None):
        """Actualiza parcialmente un usuario especificado por su id."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Actualización parcial usuario id={pk}")  # ← NUEVO
            usuarioDTO = UsuarioDAO.actualizar_usuario_parcial(pk, **request.data)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_PARCIAL_USUARIO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                UsuarioParcialSerializer(usuarioDTO).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(
                f"Datos inválidos en partial_update usuario id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(
                f"Usuario id={pk} no encontrado en partial_update"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoUsuario_409 as e:
            logger.warning(
                f"Conflicto en partial_update usuario id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(
                f"Error interno en partial_update usuario id={pk}: {e}", exc_info=True
            )  # ← NUEVO
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Activar un usuario",
        responses={
            200: "Usuario activado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def activate(self, request, pk=None):
        """Activa un usuario estableciendo el campo is_active en true."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Activando usuario id={pk}")  # ← NUEVO
            usuario = UsuarioDAO.activar_usuario(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:ACTIVAR_USUARIO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {
                    "mensaje": "Usuario activado correctamente",
                    "usuario": UsuarioParcialSerializer(usuario).data,
                },
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario id={pk} no encontrado al activar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"Error al activar usuario id={pk}: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Desactivar un usuario",
        responses={
            200: "Usuario desactivado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def deactivate(self, request, pk=None):
        """Desactiva un usuario estableciendo el campo is_active en false."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Desactivando usuario id={pk}")  # ← NUEVO
            UsuarioDAO.desactivar_usuario(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:DESACTIVAR_USUARIO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {"mensaje": "Usuario eliminado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario id={pk} no encontrado al desactivar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"ID inválido al desactivar usuario id={pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            logger.warning(f"ValueError al desactivar usuario id={pk}: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Restaurar un usuario eliminado",
        responses={
            200: "Usuario restaurado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def restore(self, request, pk=None):
        """Restaura un usuario marcado como eliminado lógicamente."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Restaurando usuario id={pk}")  # ← NUEVO
            UsuarioDAO.restaurar_usuario(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:RESTAURAR_USUARIO] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {"mensaje": "Usuario restaurado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario id={pk} no encontrado al restaurar")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"ID inválido al restaurar usuario id={pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            logger.warning(f"ValueError al restaurar usuario id={pk}: {e}")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    @swagger_auto_schema(
        operation_summary="Verificar email del usuario",
        responses={
            200: "Email verificado exitosamente",
            401: "No autorizado",
            403: "Prohibido",
            400: "El email ya estaba verificado",
            404: "Usuario no encontrado",
            500: "Error interno del servidor",
        },
    )
    def verify_email(self, request, pk=None):
        """Marca el email de un usuario como verificado."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Verificando email de usuario id={pk}")  # ← NUEVO
            UsuarioDAO.verificar_email(pk)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:VERIFICAR_EMAIL] "
                f"[realizado_por:{request.user}] [id_afectado:{pk}]"
            )
            return Response(
                {"mensaje": "Email verificado exitosamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(
                f"Usuario id={pk} no encontrado al verificar email"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"ID inválido al verificar email usuario id={pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            logger.warning(
                f"Email ya verificado o error en usuario id={pk}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    @swagger_auto_schema(
        operation_summary="Cambiar contraseña del usuario",
        request_body=UsuarioContrasenaSerializer,
        responses={
            200: "Contraseña actualizada correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def change_password(self, request, pk=None):
        """Permite cambiar la contraseña proporcionando la actual y la nueva."""
        ip = obtener_ip(request)
        serializer = UsuarioContrasenaSerializer(data=request.data)
        if serializer.is_valid():
            try:
                logger.debug(f"Cambiando contraseña de usuario id={pk}")  # ← NUEVO
                UsuarioDAO.actualizar_contrasena(
                    pk,
                    serializer.validated_data["current_password"],
                    serializer.validated_data["new_password"],
                    serializer.validated_data["confirm_password"],
                )
                logger_auditoria.info(  # ← NUEVO
                    f"ip:{ip}] [accion:CAMBIO_CONTRASENA] "
                    f"[realizado_por:{request.user}] [id_afectado:{pk}]"
                )
                return Response(
                    {"mensaje": "Contraseña actualizada correctamente"},
                    status=status.HTTP_200_OK,
                )

            except UsuarioNoEncontrado_404 as e:
                logger.warning(
                    f"Usuario id={pk} no encontrado al cambiar contraseña"
                )  # ← NUEVO
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

            except DatosInvalidos_400 as e:
                logger.warning(f"ID inválido al cambiar contraseña usuario id={pk}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            except ValueError as e:
                logger.warning(
                    f"Contraseña inválida para usuario id={pk}: {e}"
                )  # ← NUEVO
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_summary="Solicitar restablecimiento de contraseña",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: "Se ha enviado un enlace de restablecimiento a tu correo",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def request_password_reset(self, request):
        """Solicita restablecimiento de contraseña enviando un token al correo."""
        ip = obtener_ip(request)
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        try:
            logger.debug(
                f"Solicitud de reset de contraseña para email={email}"
            )  # ← NUEVO
            UsuarioDAO.reset_password_request(email)
            logger_auditoria.info(  # ← NUEVO
                f"ip:{ip}] [accion:RESET_CONTRASENA_SOLICITADO] [email:{email}]"
            )
            return Response(
                {"mensaje": "Se ha enviado un enlace de restablecimiento a tu correo"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Email {email} no encontrado en reset_password")  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(
                f"Error en reset_password para email={email}: {e}"
            )  # ← NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
