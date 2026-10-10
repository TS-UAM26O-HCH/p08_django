import logging
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class TestLogin(TestCase):
    """Pruebas sobre el endpoint POST /api/auth/token/"""

    def setUp(self):
        self.client = APIClient()
        self.url_login = "/api/auth/token/"
        self.url_refresh = "/api/auth/token/refresh/"
        self.url_logout = "/api/auth/logout/"

        # Usuario de prueba
        self.user = User.objects.create_superuser(
            username="testadmin",
            password="TestPass123",
            email="test@test.com",
        )

    # ── Login ──────────────────────────────────────────────────────────────────

    def test_login_exitoso_devuelve_tokens(self):
        """Login con credenciales correctas debe devolver access y refresh."""
        response = self.client.post(
            self.url_login,
            {
                "username": "testadmin",
                "password": "TestPass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_password_incorrecta_devuelve_401(self):
        """Login con contraseña incorrecta debe devolver 401."""
        response = self.client.post(
            self.url_login,
            {
                "username": "testadmin",
                "password": "wrongpassword",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_login_usuario_inexistente_devuelve_401(self):
        """Login con usuario que no existe debe devolver 401."""
        response = self.client.post(
            self.url_login,
            {
                "username": "noexiste",
                "password": "TestPass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_sin_credenciales_devuelve_400(self):
        """Login sin body debe devolver 400."""
        response = self.client.post(self.url_login, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Refresh ────────────────────────────────────────────────────────────────

    def test_refresh_token_valido_devuelve_nuevo_access(self):
        """Un refresh token válido debe generar un nuevo access token."""
        login = self.client.post(
            self.url_login,
            {
                "username": "testadmin",
                "password": "TestPass123",
            },
            format="json",
        )

        response = self.client.post(
            self.url_refresh,
            {
                "refresh": login.data["refresh"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_token_invalido_devuelve_401(self):
        """Un refresh token falso debe devolver 401."""
        response = self.client.post(
            self.url_refresh,
            {
                "refresh": "token.falso.invalido",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Logout ─────────────────────────────────────────────────────────────────

    def test_logout_invalida_refresh_token(self):
        """Logout exitoso debe devolver 200 y el refresh token ya no debe funcionar."""
        login = self.client.post(
            self.url_login,
            {
                "username": "testadmin",
                "password": "TestPass123",
            },
            format="json",
        )

        access = login.data["access"]
        refresh = login.data["refresh"]

        # Hacer logout
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout = self.client.post(
            self.url_logout,
            {
                "refresh": refresh,
            },
            format="json",
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        # Intentar usar el mismo refresh token — debe fallar
        reuso = self.client.post(
            self.url_refresh,
            {
                "refresh": refresh,
            },
            format="json",
        )
        self.assertIn(
            reuso.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_400_BAD_REQUEST,
            ],
        )

    def test_logout_sin_token_devuelve_401(self):
        """Logout sin Authorization header debe devolver 401."""
        self.client.credentials()  # sin token
        response = self.client.post(
            self.url_logout,
            {
                "refresh": "cualquier-cosa",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Endpoints de logs ──────────────────────────────────────────────────────

    def test_logs_auditoria_accesible_para_admin(self):
        """Un superusuario debe poder acceder al endpoint de logs de auditoría."""
        login = self.client.post(
            self.url_login,
            {
                "username": "testadmin",
                "password": "TestPass123",
            },
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get("/api/logs/auditoria/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("entradas", response.data)
        self.assertIn("total", response.data)

    def test_logs_auditoria_bloqueado_para_usuario_normal(self):
        """Un usuario sin is_staff debe recibir 403 al intentar ver los logs."""
        usuario_normal = User.objects.create_user(
            username="normal",
            password="Normal123",
            email="normal@test.com",
        )
        login = self.client.post(
            self.url_login,
            {
                "username": "normal",
                "password": "Normal123",
            },
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get("/api/logs/auditoria/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logs_auditoria_bloqueado_sin_autenticacion(self):
        """Sin token no debe ser posible acceder a los logs."""
        self.client.credentials()
        response = self.client.get("/api/logs/auditoria/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Contrato con los demás microservicios ────────────────────────────────

    def test_token_incluye_claims_para_microservicios(self):
        """El access token debe llevar username/is_staff/is_superuser (RS256).

        servicio_usuarios y servicio_productos autorizan de forma stateless
        a partir de estos claims.
        """
        import jwt

        login = self.client.post(
            self.url_login,
            {
                "username": "testadmin",
                "password": "TestPass123",
            },
            format="json",
        )

        payload = jwt.decode(login.data["access"], options={"verify_signature": False})
        self.assertEqual(payload["username"], "testadmin")
        self.assertTrue(payload["is_staff"])
        self.assertTrue(payload["is_superuser"])

    def test_token_usa_rs256(self):
        """El access token debe estar firmado con RS256 (llave asimétrica)."""
        import jwt

        login = self.client.post(
            self.url_login,
            {
                "username": "testadmin",
                "password": "TestPass123",
            },
            format="json",
        )

        header = jwt.get_unverified_header(login.data["access"])
        self.assertEqual(header["alg"], "RS256")
