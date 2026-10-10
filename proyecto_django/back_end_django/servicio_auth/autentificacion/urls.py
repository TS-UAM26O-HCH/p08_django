from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from autentificacion.views import (
    CustomTokenObtainPairView,
    LoginView,
    LogoutView,
)
from autentificacion.views import CustomTokenObtainPairSerializer
from autentificacion.log_views import LogAuditoriaView, LogTecnicoView

urlpatterns = [
    # Login con auditoría (reemplaza a TokenObtainPairView)
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # Renovar access token
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Logout con invalidación de refresh token
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    # estos endpoints nos serviran mas adelante cuando implementemos la funcionalidad de logs.
    path("logs/auditoria/", LogAuditoriaView.as_view(), name="log_auditoria"),
    path("logs/tecnico/", LogTecnicoView.as_view(), name="log_tecnico"),
]
