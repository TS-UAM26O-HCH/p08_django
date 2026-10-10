from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet

# Crear un router y registrar el ViewSet
router = DefaultRouter()
router.register(r"products", ProductoViewSet, basename="products")

urlpatterns = [
    path("", include(router.urls)),
]
