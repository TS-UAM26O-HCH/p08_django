import logging

from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed


logger_auditoria = logging.getLogger("auditoria")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Claims propios para que los demás microservicios puedan
        # autorizar sin consultar la BD de auth.
        token["username"] = user.username
        token["email"] = user.email
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser
        return token

    def validate(self, attrs):

        username = attrs.get("username")
        password = attrs.get("password")

        request = self.context.get("request")

        user = authenticate(request=request, username=username, password=password)

        ip = request.META.get("REMOTE_ADDR", "IP desconocida")

        if user is None:
            logger_auditoria.warning(
                f"ip:{ip}] [accion:LOGIN_FALLIDO] "
                f"[usuario:{username}] "
                f"[detalle:credenciales incorrectas]"
            )

            raise AuthenticationFailed("Credenciales inválidas.")

        data = super().validate(attrs)

        logger_auditoria.info(
            f"ip:{ip}] [accion:LOGIN_EXITOSO] [usuario:{username}] [id:{user.id}]"
        )

        return data
