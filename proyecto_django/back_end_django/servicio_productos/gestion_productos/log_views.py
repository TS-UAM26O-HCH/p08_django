from pathlib import Path

from core.permissions import IsStaffFromToken
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"


def leer_log(nombre_archivo, filtros=None, limite=100):
    """
    Lee un archivo .log y devuelve sus líneas como lista.
    Aplica filtros opcionales (dict de clave:valor a buscar en cada línea).
    """
    ruta = LOGS_DIR / nombre_archivo
    if not ruta.exists():
        return []

    with open(ruta, encoding="utf-8") as f:
        lineas = f.readlines()
    lineas = [l for l in lineas if l.startswith("[")]
    # Aplicar filtros si se proporcionaron
    if filtros:
        for clave, valor in filtros.items():
            if valor:
                lineas = [l for l in lineas if valor.lower() in l.lower()]

    # Devolver las últimas N líneas (más recientes primero)
    return [l.strip() for l in reversed(lineas[-limite:])]


class LogAuditoriaView(APIView):
    """
    GET /api/logs/auditoria/
    Devuelve entradas del log de auditoría.
    Solo accesible para administradores (claim is_staff del JWT).

    Parámetros opcionales de query:
    ?usuario=Admin
    ?accion=CREAR_PRODUCTO
    ?limite=50
    """

    permission_classes = [IsAuthenticated, IsStaffFromToken]

    def get(self, request):
        filtros = {
            "usuario": request.query_params.get("usuario"),
            "accion": request.query_params.get("accion"),
        }
        limite = int(request.query_params.get("limite", 100))

        entradas = leer_log("auditoria.log", filtros=filtros, limite=limite)

        return Response(
            {
                "total": len(entradas),
                "filtros_aplicados": {k: v for k, v in filtros.items() if v},
                "entradas": entradas,
            },
            status=status.HTTP_200_OK,
        )


class LogTecnicoView(APIView):
    """
    GET /api/logs/tecnico/
    Devuelve entradas del log técnico (WARNING, ERROR, CRITICAL).
    Solo accesible para administradores (claim is_staff del JWT).

    Parámetros opcionales:
    ?nivel=ERROR
    ?modulo=views
    ?limite=50
    """

    permission_classes = [IsAuthenticated, IsStaffFromToken]

    def get(self, request):
        filtros = {
            "nivel": request.query_params.get("nivel"),
            "modulo": request.query_params.get("modulo"),
        }
        limite = int(request.query_params.get("limite", 100))

        entradas = leer_log("tecnico.log", filtros=filtros, limite=limite)

        return Response(
            {
                "total": len(entradas),
                "filtros_aplicados": {k: v for k, v in filtros.items() if v},
                "entradas": entradas,
            },
            status=status.HTTP_200_OK,
        )
