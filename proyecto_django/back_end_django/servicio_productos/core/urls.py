from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from gestion_productos.log_views import LogAuditoriaView, LogTecnicoView
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Servicio Productos — API",
        default_version="v1",
        description="Microservicio de gestión de productos. Autenticación con JWT (RS256) emitido por servicio_auth.",
        contact=openapi.Contact(email="soporte@example.com"),
        license=openapi.License(name="MIT Licence"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("gestion_productos.urls")),
    path("api/logs/auditoria/", LogAuditoriaView.as_view(), name="log_auditoria"),
    path("api/logs/tecnico/", LogTecnicoView.as_view(), name="log_tecnico"),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]


if settings.DEBUG:
    # Sirve /static/* vía finders en dev (Swagger UI, admin, ...).
    # El gateway quita el prefijo /api/<servicio> (como con el resto),
    # así que aquí llega /static/... El handler automático de runserver
    # no coincide (STATIC_URL lleva el prefijo) y esta vista explícita
    # sí resuelve con finders.
    import mimetypes
    import os

    from django.contrib.staticfiles import finders
    from django.http import FileResponse, Http404

    def dev_static(request, path):
        found = finders.find(path)
        if not found or os.path.isdir(found):
            raise Http404("Static file not found")
        content_type, _ = mimetypes.guess_type(found)
        return FileResponse(
            open(found, "rb"),
            content_type=content_type or "application/octet-stream",
        )

    urlpatterns += [re_path(r"^static/(?P<path>.*)$", dev_static)]
