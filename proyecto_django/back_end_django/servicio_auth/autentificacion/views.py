from django.shortcuts import render

# Create your views here.
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from autentificacion.serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import authenticate

logger_auditoria = logging.getLogger("auditoria")
logger_tecnico = logging.getLogger("back_end_django")


def obtener_ip(request):
    """Extrae la IP real del cliente, considerando proxies."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "IP desconocida")


def agregar_claims(token, user):
    """Agrega claims propios al token para autorización en otros servicios."""
    token["username"] = user.username
    token["email"] = user.email
    token["is_staff"] = user.is_staff
    token["is_superuser"] = user.is_superuser
    return token


class LoginView(APIView):
    """
    Autenticación manual con registro de auditoría.
    Devuelve access y refresh token si las credenciales son válidas.
    """

    permission_classes = []  # endpoint público

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        ip = obtener_ip(request)

        if not username or not password:
            logger_auditoria.warning(
                f"ip:{ip}] [accion:LOGIN_FALLIDO] [detalle:credenciales incompletas]"
            )
            return Response(
                {"error": "Se requieren username y password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            # Registrar intento fallido — útil para detectar ataques de fuerza bruta
            logger_auditoria.warning(
                f"ip:{ip}] [accion:LOGIN_FALLIDO] "
                f"[usuario:{username}] [detalle:credenciales incorrectas]"
            )
            return Response(
                {"error": "Credenciales inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Credenciales correctas — generar tokens
        refresh = RefreshToken.for_user(user)
        refresh = agregar_claims(refresh, user)

        logger_auditoria.info(
            f"ip:{ip}] [accion:LOGIN_EXITOSO] [usuario:{username}] [id:{user.id}]"
        )

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Cierre de sesión: invalida el refresh token añadiéndolo a la blacklist.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ip = obtener_ip(request)
        username = request.user.username

        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Se requiere el refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # invalida el token

            logger_auditoria.info(
                f"ip:{ip}] [accion:LOGOUT] [usuario:{username}] [id:{request.user.id}]"
            )
            return Response(
                {"mensaje": "Sesión cerrada correctamente."},
                status=status.HTTP_200_OK,
            )

        except TokenError as e:
            logger_tecnico.warning(f"Logout fallido para {username}: {e}")
            return Response(
                {"error": "Token inválido o ya expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
