from gestion_usuarios.models import Usuario
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from datetime import timedelta
from gestion_usuarios.serializers import (
    UsuarioParcialSerializer,
    UsuarioContrasenaSerializer,
)
from gestion_usuarios.exceptions.usuarioExeptions import (
    DatosInvalidos_400,
    UsuarioNoEncontrado_404,
    ConflictoUsuario_409,
    ErrorInternoServidor_500,
    UsuarioNoAutorizado_401,
    UsuarioProhibido_403,
)
from django.db.utils import IntegrityError, DatabaseError
import uuid


class UsuarioDAO:
    """
    Data Access Object (DAO) para la gestion de usuarions en la base de datos.
    Proporciona metodos para realizar operaciones CRUD sobre el modelo Usuario.
    """

    @staticmethod
    def obtener_todos():
        return Usuario.objects.all()

    @staticmethod
    def obtener_usuario_por_id(usuario_id):
        """
        Obtiene un usuario por su ID si no ha sido eliminado.

        :param usuario_id: UUID del usuario a buscar.
        :return: Instancia de Usuario o None si no se encuentra.
        """
        try:
            usuario_uuid = (
                usuario_id
                if isinstance(usuario_id, uuid.UUID)
                else uuid.UUID(str(usuario_id))
            )
        except (ValueError, AttributeError, TypeError):
            raise DatosInvalidos_400("El ID del usuario no es un UUID válido.")
        try:
            usuario = Usuario.objects.filter(id=usuario_uuid, is_deleted=False).first()
        except ValidationError:
            raise DatosInvalidos_400("El ID del usuario no es un UUID válido.")
        if not usuario:
            raise UsuarioNoEncontrado_404()
        return usuario

    @staticmethod
    def activar_usuario(pk):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        if not usuario:
            raise UsuarioNoEncontrado_404
        if usuario.is_active:
            raise DatosInvalidos_400("El usuario ya estaba activo")
        usuario.is_active = True
        usuario.save()
        return usuario

    @staticmethod
    def crear_usuario(
        username: str,
        password: str,
        date_of_birth: str,
        email: str,
        first_name: str,
        last_name: str,
    ):
        """
        Crea un nuevo usuario con validaciones.
        """
        # Validar email
        try:
            validate_email(email)
        except ValidationError:
            raise DatosInvalidos_400()

        # Validar username (máximo 20 caracteres)
        UsuarioParcialSerializer.validar_username(username)

        try:
            usuario = Usuario.objects.create(
                username=username,
                password=make_password(password),
                date_of_birth=date_of_birth,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            return usuario
        except IntegrityError:
            raise ConflictoUsuario_409()
        except DatabaseError as e:
            raise ErrorInternoServidor_500()

    @staticmethod
    def actualizar_usuario(usuario_id, **datos_actualizados):
        """
        Actualiza completamente los datos de un usuario.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")

        # Validar username duplicado

        if (
            "username" in datos_actualizados
            and datos_actualizados["username"] != usuario.username
        ):
            if (
                Usuario.objects.filter(username=datos_actualizados["username"])
                .exclude(id=usuario_id)
                .exists()
            ):
                raise ConflictoUsuario_409("El nombre de usuario ya está registrado.")

        # Validar email duplicado

        if (
            "email" in datos_actualizados
            and datos_actualizados["email"] != usuario.email
        ):
            if (
                Usuario.objects.filter(email=datos_actualizados["email"])
                .exclude(id=usuario_id)
                .exists()
            ):
                raise ConflictoUsuario_409("El correo electrónico ya está registrado.")
        # Actualizar campos
        for campo, valor in datos_actualizados.items():
            if campo == "password":
                usuario.password = make_password(valor)
        else:
            setattr(usuario, campo, valor)
        usuario.save()

        return usuario

    @staticmethod
    def eliminar_usuario(pk):
        """
        Marca un usuario como eliminado en lugar de eliminarlo físicamente.
        :param pk: ID del usuario a eliminar.
        :return: Instancia del usuario eliminado.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        # este if es redundante porque obtener_usuario_por_id ya lanza excepción , pero lo dejo
        if not usuario:
            raise UsuarioNoEncontrado_404()  # <-- fatal corregido (faltaban paréntesis)
        usuario.is_deleted = True
        usuario.deleted_at = timezone.now()
        usuario.save()
        return usuario

    CAMPOS_OPCIONALES = [
        "username",
        "password",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_superuser",
        "profile_picture",
        "nationality",
        "occupation",
        "date_of_birth",
        "contact_phone_number",
        "gender",
        "address",
        "address_number",
        "address_interior_number",
        "address_complement",
        "address_neighborhood",
        "address_zip_code",
        "address_city",
        "address_state",
        "role",
    ]

    @staticmethod
    def actualizar_usuario_parcial(pk, **datos):
        """
        Actualiza los datos de un usuario existente de forma parcial.
        :param pk: UUID del usuario a actualizar.
        :param datos: Diccionario con los campos a modificar.
        :return: Instancia del usuario actualizado.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")
        # Verificación de username y email duplicados
        if "username" in datos and datos["username"] != usuario.username:
            if (
                Usuario.objects.filter(username=datos["username"])
                .exclude(id=pk)
                .exists()
            ):
                raise ConflictoUsuario_409("El nombre de usuario ya está registrado.")
        if "email" in datos and datos["email"] != usuario.email:
            if Usuario.objects.filter(email=datos["email"]).exclude(id=pk).exists():
                raise ConflictoUsuario_409("El correo electrónico ya está registrado.")
        # Actualización de campos permitidos
        for campo, valor in datos.items():
            if campo in UsuarioDAO.CAMPOS_OPCIONALES:
                if campo == "password":
                    usuario.password = make_password(valor)
                else:
                    setattr(usuario, campo, valor)
        # Guardar cambios
        usuario.save()
        return usuario

    @staticmethod
    def restaurar_usuario(pk):
        """
        Restaura un usuario previamente marcado como eliminado lógicamente.
        :param pk: ID del usuario a restaurar.
        :return: Instancia del usuario restaurado.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")
        usuario.is_deleted = False
        usuario.deleted_at = None
        usuario.save()
        return usuario

    @staticmethod
    def verificar_email(pk):
        """
        Verifica el email del usuario especificado por su ID.
        :param pk: ID del usuario a verificar.
        :return: Instancia del usuario con el email verificado.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")
        if usuario.email_verified:
            raise DatosInvalidos_400("El email ya estaba verificado.")
        usuario.email_verified = True
        usuario.email_verified_at = timezone.now()
        usuario.save()
        return usuario

    @staticmethod
    def desactivar_usuario(pk):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")
            if usuario.is_active:
                usuario.is_active = False
                usuario.save()
                return usuario
        else:
            raise DatosInvalidos_400("El usuario ya estaba desactivado.")

    @staticmethod
    def actualizar_contrasena(pk, current_password, new_password, confirm_password):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        if not usuario:
            raise UsuarioNoEncontrado_404("El usuario no existe.")
        if not usuario.check_password(current_password):
            raise ValidationError("La contraseña actual no es correcta.")
        serializer = UsuarioContrasenaSerializer(
            data={
                "current_password": current_password,
                "new_password": new_password,
                "confirm_password": confirm_password,
            }
        )
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        usuario.password = make_password(new_password)
        usuario.save()
        return usuario

    @staticmethod
    def reset_password(token, new_password):
        """Restablece la contraseña usando el token."""
        usuario = Usuario.objects.filter(reset_password_token=token).first()
        if not usuario or not usuario.is_reset_token_valid():
            raise Exception("Token inválido o expirado")
        # Restablece la contraseña y borra el token
        usuario.set_password(new_password)
        usuario.reset_password_token = None
        usuario.reset_password_expires_at = None
        usuario.save()
        return usuario

    @staticmethod
    def reset_password_request(email):
        """
        Genera un token de recuperación de contraseña.
        """
        usuario = Usuario.objects.filter(email=email, is_deleted=False).first()
        if not usuario:
            raise UsuarioNoEncontrado_404()
        usuario.reset_password_token = uuid.uuid4()
        usuario.reset_password_expires_at = timezone.now() + timedelta(hours=1)
        usuario.save()
        return {
            "token": str(usuario.reset_password_token),
            "expires_at": usuario.reset_password_expires_at,
        }
