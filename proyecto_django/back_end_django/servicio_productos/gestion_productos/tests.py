from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class TestCORS(APITestCase):
    """Verifica que los headers CORS están presentes en las respuestas."""

    def setUp(self):
        self.client = APIClient()

    def test_options_devuelve_header_cors(self):
        """
        Una petición OPTIONS desde un origen permitido debe incluir
        Access-Control-Allow-Origin en la respuesta.
        """
        response = self.client.options(
            "/api/products/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="Authorization",
        )
        self.assertIn(
            "Access-Control-Allow-Origin",
            response.headers,
        )

    def test_origen_no_permitido_no_recibe_header_cors(self):
        """
        Un origen que no está en CORS_ALLOWED_ORIGINS no debe recibir
        el header Access-Control-Allow-Origin.
        """
        response = self.client.options(
            "/api/products/",
            HTTP_ORIGIN="http://sitiomalicioso.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )
        self.assertNotEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://sitiomalicioso.com",
        )


class TestEndpointsProductos(APITestCase):
    """Pruebas sobre /api/products/.

    NOTA de microservicios: el login (emisión de JWT) vive en
    servicio_auth. Aquí la autenticación se simula con
    ``force_authenticate`` (equivale a una petición con un JWT válido
    verificado con la llave pública RS256).
    """

    def setUp(self):
        self.client = APIClient()
        self.url_products = "/api/products/"

        self.admin = User.objects.create_superuser(
            username="admin_prod",
            password="AdminProd123",
            email="adminprod@test.com",
        )

    # ── Protección ─────────────────────────────────────────────────────────────

    def test_listar_productos_sin_token_devuelve_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url_products)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_productos_con_token_devuelve_200(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url_products)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── Creación ───────────────────────────────────────────────────────────────

    def test_crear_producto_devuelve_201(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url_products,
            {
                "type": "BIEN",
                "name": "Producto test",
                "price": "99.99",
                "status": True,
                "description": "Descripción del producto de prueba",
                "product_key": "TEST0001",
                "image_link": "http://example.com/img.png",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_producto_sin_token_devuelve_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.url_products,
            {
                "name": "Sin token",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Auditoría ──────────────────────────────────────────────────────────────

    def test_crear_producto_registra_en_log_auditoria(self):
        """Crear un producto debe escribir CREAR_PRODUCTO en el log de auditoría."""
        with self.assertLogs("auditoria", level="INFO") as cm:
            self.client.force_authenticate(user=self.admin)
            self.client.post(
                self.url_products,
                {
                    "type": "BIEN",
                    "name": "Producto auditado",
                    "price": "50.00",
                    "status": True,
                    "description": "Para test de auditoría",
                    "product_key": "AUD00001",
                    "image_link": "http://example.com/img.png",
                },
                format="json",
            )

        mensajes = "\n".join(cm.output)
        self.assertIn("CREAR_PRODUCTO", mensajes)

    def test_eliminar_producto_registra_en_log_auditoria(self):
        """Eliminar un producto debe escribir ELIMINAR_PRODUCTO en auditoría."""
        # Primero crear un producto
        self.client.force_authenticate(user=self.admin)
        crear = self.client.post(
            self.url_products,
            {
                "type": "BIEN",
                "name": "Para eliminar",
                "price": "10.00",
                "status": True,
                "description": "Se eliminará en el test",
                "product_key": "DEL00001",
                "image_link": "http://example.com/img.png",
            },
            format="json",
        )

        producto_id = crear.data["id"]

        # Luego eliminarlo y verificar el log
        with self.assertLogs("auditoria", level="INFO") as cm:
            self.client.delete(f"{self.url_products}{producto_id}/")

        mensajes = "\n".join(cm.output)
        self.assertIn("ELIMINAR_PRODUCTO", mensajes)
