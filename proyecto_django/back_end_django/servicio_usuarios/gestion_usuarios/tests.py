import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class TestEndpointsUsuarios(APITestCase):
    """Pruebas sobre /api/users/.

    NOTA de microservicios: el login (emisión de JWT) vive en
    servicio_auth. Aquí la autenticación se simula con
    ``force_authenticate`` (equivale a una petición con un JWT válido
    verificado con la llave pública RS256).
    """

    def setUp(self):
        self.client = APIClient()
        self.url_users = "/api/users/"

        self.admin = User.objects.create_superuser(
            username="admin_test",
            password="Admin123",
            email="admin@test.com",
        )
        self.normal = User.objects.create_user(
            username="normal_test",
            password="Normal123",
            email="normal@test.com",
        )

    # ── Protección de endpoints ────────────────────────────────────────────────

    def test_listar_usuarios_sin_token_devuelve_401(self):
        """GET /api/users/ sin autenticación debe devolver 401."""
        response = self.client.get(self.url_users)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_usuarios_con_token_valido_devuelve_200(self):
        """GET /api/users/ autenticado debe devolver 200."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url_users)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_usuarios_con_token_falso_devuelve_401(self):
        """GET /api/users/ con token inventado debe devolver 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token.falso.abc123")
        response = self.client.get(self.url_users)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Creación ───────────────────────────────────────────────────────────────

    def test_crear_usuario_devuelve_201(self):
        """POST /api/users/ con datos válidos debe devolver 201."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url_users,
            {
                "username": "nuevo_usuario",
                "email": "nuevo@test.com",
                "password": "NuevoPass123",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "date_of_birth": "1990-01-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_usuario_sin_token_devuelve_401(self):
        """POST /api/users/ sin autenticación debe devolver 401."""
        response = self.client.post(
            self.url_users,
            {
                "username": "sin_token",
                "email": "sintoken@test.com",
                "date_of_birth": "1990-01-01",
                "password": "Pass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Auditoría ──────────────────────────────────────────────────────────────

    def test_crear_usuario_registra_en_log_auditoria(self):
        """Crear un usuario debe escribir una entrada en el log de auditoría."""
        with self.assertLogs("auditoria", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin)
            self.client.post(
                self.url_users,
                {
                    "username": "auditado",
                    "email": "auditado@test.com",
                    "password": "AuditPass123",
                    "first_name": "Test",
                    "date_of_birth": "1990-01-01",
                    "last_name": "Auditoria",
                },
                format="json",
            )

        mensajes = "\n".join(cm.output)
        self.assertIn("CREAR_USUARIO", mensajes)

    # ── Logs (permiso por claims del JWT) ──────────────────────────────────────

    def test_logs_auditoria_accesible_para_admin(self):
        """Un staff debe poder acceder al endpoint de logs de auditoría."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/logs/auditoria/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("entradas", response.data)
        self.assertIn("total", response.data)

    def test_logs_auditoria_bloqueado_para_usuario_normal(self):
        """Un usuario sin is_staff debe recibir 403 al intentar ver los logs."""
        self.client.force_authenticate(user=self.normal)
        response = self.client.get("/api/logs/auditoria/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logs_auditoria_bloqueado_sin_autenticacion(self):
        """Sin autenticación no debe ser posible acceder a los logs."""
        response = self.client.get("/api/logs/auditoria/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
