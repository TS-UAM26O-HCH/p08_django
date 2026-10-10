"""
Django settings for servicio_auth.

Microservicio de autenticación: emite y valida tokens JWT (RS256).
Es el ÚNICO servicio que posee la llave privada.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-auth-only-change-me")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,servicio_auth,gateway",
    cast=lambda v: [h.strip() for h in v.split(",")],
)

# ─────────────────────────────────────────
# Gateway nginx como punto único de entrada.
# El gateway QUITA el prefijo /api/auth antes de reenviar
# (rewrite en nginx) y Django genera URLs CON prefijo gracias a
# FORCE_SCRIPT_NAME, de modo que el Swagger funciona vía gateway:
#   http://localhost/api/auth/swagger/  →  Django ve /swagger/ (200)
#   y el JSON/paths salen como /api/auth/...
# En local (runserver sin gateway) dejar FORCE_SCRIPT_NAME vacío.
# ─────────────────────────────────────────
FORCE_SCRIPT_NAME = config("FORCE_SCRIPT_NAME", default="") or None
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost,http://127.0.0.1",
    cast=lambda v: [h.strip() for h in v.split(",")],
)

INSTALLED_APPS = [
    "autentificacion.apps.AutentificacionConfig",
    "rest_framework_simplejwt.token_blacklist",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_yasg",
    "rest_framework",
    "corsheaders",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": config("DATABASE_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DATABASE_NAME", default="auth_db"),
        "USER": config("DATABASE_USER", default="postgres"),
        "PASSWORD": config("DATABASE_PASSWORD", default="postgres"),
        "HOST": config("DATABASE_HOST", default="127.0.0.1"),
        "PORT": config("DATABASE_PORT", default="5433"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = f"{FORCE_SCRIPT_NAME}/static/" if FORCE_SCRIPT_NAME else "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# ─────────────────────────────────────────
# JWT RS256 — este servicio FIRMA tokens
# ─────────────────────────────────────────
_JWT_PRIVATE_KEY_PATH = BASE_DIR / "keys" / "private.pem"
_JWT_PUBLIC_KEY_PATH = BASE_DIR / "keys" / "public.pem"

JWT_SIGNING_KEY = (
    _JWT_PRIVATE_KEY_PATH.read_text() if _JWT_PRIVATE_KEY_PATH.exists() else None
)
JWT_VERIFYING_KEY = (
    _JWT_PUBLIC_KEY_PATH.read_text() if _JWT_PUBLIC_KEY_PATH.exists() else None
)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "RS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "VERIFYING_KEY": JWT_VERIFYING_KEY,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
    "VALIDATOR_URL": None,
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": (
                "Encabezado para autenticación JWT con esquema Bearer. "
                'Ejemplo: "Bearer {token}"'
            ),
        }
    },
}

# ─────────────────────────────────────────
# CORS
# ─────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://localhost:4200",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ─────────────────────────────────────────
# LOGGING — técnico + auditoría
# ─────────────────────────────────────────
LOGS_DIR = BASE_DIR / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "tecnico_detallado": {
            "format": "[{asctime}] [{levelname}] [{name}] [{module}:{lineno}] {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "consola_simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
        "auditoria_formato": {
            "format": "[{asctime}] [AUDITORIA] [Usuario: {message}]",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "consola": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "consola_simple",
            "filters": ["require_debug_true"],
        },
        "archivo_tecnico": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "tecnico.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "tecnico_detallado",
            "encoding": "utf-8",
        },
        "archivo_debug": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "debug.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 3,
            "formatter": "tecnico_detallado",
            "encoding": "utf-8",
        },
        "archivo_auditoria": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "auditoria.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 10,
            "formatter": "auditoria_formato",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["consola", "archivo_tecnico"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["archivo_tecnico"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["archivo_debug"],
            "level": "DEBUG",
            "propagate": False,
            "filters": ["require_debug_true"],
        },
        "back_end_django": {
            "handlers": ["consola", "archivo_tecnico", "archivo_debug"],
            "level": "DEBUG",
            "propagate": False,
        },
        "servicio_auth": {
            "handlers": ["consola", "archivo_tecnico", "archivo_debug"],
            "level": "DEBUG",
            "propagate": False,
        },
        "autentificacion": {
            "handlers": ["consola", "archivo_tecnico", "archivo_debug"],
            "level": "DEBUG",
            "propagate": False,
        },
        "auditoria": {
            "handlers": ["archivo_auditoria", "consola"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
