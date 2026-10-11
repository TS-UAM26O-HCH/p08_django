# Practica 4 para TSCC — Microservicios Django + JWT

## Debido a ciertas complicaciones con el documento proporcionado, el uso de IA fue gran parte para hacer los fix

## Tambien fue util para generar el README junto al diagrama mermaid

## Arquitectura

El monolito original (`proyecto_django/back_end_django/` con las apps
`autentificacion`, `gestion_usuarios` y `gestion_productos`) se separó en
3 microservicios Django independientes, cada uno con su propia base de
datos PostgreSQL:

| Servicio           | Carpeta                                              | Puerto host | BD (puerto host)    | Responsabilidad                                                              |
| ------------------ | ---------------------------------------------------- | ----------- | ------------------- | ---------------------------------------------------------------------------- |
| gateway (nginx)    | `proyecto_django/back_end_django/gateway/nginx.conf` | 80          | —                   | Punto único de entrada: `/api/auth/*`, `/api/usuarios/*`, `/api/productos/*` |
| servicio_auth      | `proyecto_django/back_end_django/servicio_auth`      | — (interno) | auth_db (5433)      | Emite JWT (RS256), refresh, logout, logs                                     |
| servicio_usuarios  | `.../servicio_usuarios`                              | — (interno) | usuarios_db (5434)  | CRUD de usuarios                                                             |
| servicio_productos | `.../servicio_productos`                             | — (interno) | productos_db (5435) | CRUD de productos                                                            |

> Los servicios Django NO publican puertos: solo el gateway expone el
> puerto 80, así nunca hay que cambiar de puerto para usar las APIs.
> (Para depurar un servicio directo, descomenta su bloque `ports` en el
> `docker-compose.yml`: 8001/8002/8003.)

Autenticación entre servicios: `servicio_auth` firma los tokens con la
llave privada `servicio_auth/keys/private.pem` (RS256) e incluye los
claims `username`, `email`, `is_staff`, `is_superuser`. Los demás
servicios solo poseen `keys/public.pem` y validan de forma stateless
(`JWTStatelessUserAuthentication` + permiso `IsStaffFromToken` para los
endpoints de logs). La llave privada y los `.env` nunca se commitean
(ver `.gitignore`); por eso un clon fresco debe generarlos (paso 2).

### Diagrama de arquitectura

```mermaid
flowchart TB
    Cliente(["Cliente / curl / Swagger"])

    subgraph Gateway ["Gateway nginx :80"]
        NG["gateway/nginx.conf<br/>/api/auth/* · /api/usuarios/* · /api/productos/*"]
    end

    subgraph Auth ["servicio_auth :8000"]
        A["autentificacion<br/>login · refresh · logout · logs"]
        PRIV[("keys/private.pem<br/>(firma RS256)")]
    end

    subgraph Usuarios ["servicio_usuarios :8000"]
        U["gestion_usuarios<br/>CRUD /api/users/ · logs"]
        PUB1[("keys/public.pem<br/>(verifica)")]
    end

    subgraph Productos ["servicio_productos :8000"]
        P["gestion_productos<br/>CRUD /api/products/ · logs"]
        PUB2[("keys/public.pem<br/>(verifica)")]
    end

    DBA[("auth_db<br/>Postgres :5433")]
    DBU[("usuarios_db<br/>Postgres :5434")]
    DBP[("productos_db<br/>Postgres :5435")]

    Cliente -->|"/api/auth/*"| NG
    Cliente -->|"/api/usuarios/*"| NG
    Cliente -->|"/api/productos/*"| NG

    NG -->|strip /api/auth| A
    NG -->|strip /api/usuarios| U
    NG -->|strip /api/productos| P

    A --> PRIV
    A --> DBA
    U --> PUB1
    U --> DBU
    P --> PUB2
    P --> DBP

    A -.->|"JWT RS256 + claims<br/>is_staff, is_superuser"| U
    A -.->|"JWT RS256 + claims<br/>is_staff, is_superuser"| P
```

## Guía desde cero (clon fresco)

### 0. Requisitos previos

- Git, Docker y Docker Compose (plugin `docker compose`)
- OpenSSL (para generar las llaves JWT)
- Opcional para correr tests en local: Python 3.14 + `uv`

Verifica con:

```bash
git --version
docker --version
docker compose version
openssl version
```

### 1. Clonar el repositorio

```bash
git clone <URL-del-repositorio>
cd practica4/proyecto_django/back_end_django
```

Todos los comandos siguientes se ejecutan desde
`proyecto_django/back_end_django` (donde está el `docker-compose.yml`
de microservicios).

### 2. Generar las llaves JWT (RS256) y los `.env`

En un clon fresco no existen `keys/private.pem` ni los archivos `.env`
(están ignorados por git), así que hay que crearlos:

```bash
# Llave privada (SOLO la posee servicio_auth) + llave pública
openssl genrsa -out servicio_auth/keys/private.pem 2048
openssl rsa -in servicio_auth/keys/private.pem -pubout -out servicio_auth/keys/public.pem
chmod 600 servicio_auth/keys/private.pem

# Repartir la llave PÚBLICA a los demás servicios (solo verifican firmas)
cp servicio_auth/keys/public.pem servicio_usuarios/keys/public.pem
cp servicio_auth/keys/public.pem servicio_productos/keys/public.pem

# Variables de entorno de cada servicio (valores de desarrollo por defecto)
cp servicio_auth/.env.example servicio_auth/.env
cp servicio_usuarios/.env.example servicio_usuarios/.env
cp servicio_productos/.env.example servicio_productos/.env
```

> Si los puertos 80 o 5433-5435 están ocupados, o quieres cambiar
> credenciales, edita los `.env` y el `docker-compose.yml` antes de seguir.

### 3. Construir y levantar los servicios

```bash
docker compose build
docker compose up -d
docker ps   # los 7 contenedores deben estar Up (gateway + 3 APIs + 3 Postgres)
```

Verifica que el gateway responde:

```bash
curl -s http://127.0.0.1/
# {"gateway":"ok","base":"/api","servicios":{"auth":"/api/auth/",...},...}
```

### 4. Aplicar migraciones (una BD por servicio)

Espera ~15 segundos a que los Postgres estén sanos y luego:

```bash
docker compose exec servicio_auth python manage.py migrate
docker compose exec servicio_usuarios python manage.py migrate
docker compose exec servicio_productos python manage.py migrate
```

### 5. Crear el usuario administrador (solo existe en servicio_auth)

```bash
docker compose exec servicio_auth python manage.py initadmin
```

Credenciales: usuario `Admin`, contraseña `AdminApiDjango123`.

### 6. Uso y prueba de la API

**Vía única: el gateway** (`http://127.0.0.1`
Todas las peticiones —curl, Swagger o frontend— usan esta base URL:

| URL del gateway    | Destino            |
| ------------------ | ------------------ |
| `/api/auth/*`      | servicio_auth      |
| `/api/usuarios/*`  | servicio_usuarios  |
| `/api/productos/*` | servicio_productos |

**a) Login — obtener el token:**

```bash
curl -s -X POST http://127.0.0.1/api/auth/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "Admin", "password": "AdminApiDjango123"}'
# Responde {"refresh": "...", "access": "..."} — guarda ambos.
# El "access" dura 30 minutos; el "refresh" 1 día.
```

**b) Usar el token** en cualquier endpoint protegido:

```bash
export TOKEN="<pega-aqui-el-access-token>"
export REFRESH="<pega-aqui-el-refresh-token>"
curl -s http://127.0.0.1/api/usuarios/api/users/ \
  -H "Authorization: Bearer $TOKEN"
```

**c) Renovar el access cuando expire:**

```bash
curl -s -X POST http://127.0.0.1/api/auth/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}"
# Devuelve un "access" nuevo. El refresh usado puede quedar invalidado
# (reusarlo responde 400), así que guarda el nuevo par si rota.
```

**d) Logout (requiere Bearer + refresh vigente):**

```bash
curl -s -X POST http://127.0.0.1/api/auth/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"refresh\": \"$REFRESH\"}"
# {"mensaje": "Sesión cerrada correctamente."}
```

#### 6.1 Probar desde Swagger

Documentación (vía gateway, punto único de entrada):

```
http://127.0.0.1/api/auth/swagger/       # auth
http://127.0.0.1/api/usuarios/swagger/   # usuarios
http://127.0.0.1/api/productos/swagger/  # productos
```

Pulsa `Authorize` e ingresa `Bearer <access-token>` (con un espacio
entre `Bearer` y el token); luego el "Try it out" de cada endpoint ya
envía el token automáticamente.

#### 6.2 Códigos de respuesta esperados

| Código | Cuándo lo verás                                                                                                                                     |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| 200    | GET, PUT, PATCH, refresh, logout, DELETE (lógico), `activate/deactivate/restore/verify_email/change_password/search/update_image`                   |
| 201    | POST de usuario/producto creado                                                                                                                     |
| 400    | Campos inválidos; `q` faltante en `search`; `image_link` inválido; refresh reusado o expirado (`Token inválido o ya expirado`); email ya verificado |
| 401    | Sin header `Authorization`, token expirado o falso                                                                                                  |
| 403    | Usuario sin `is_staff` en `/api/logs/*`                                                                                                             |
| 404    | Ruta o `id` inexistente                                                                                                                             |
| 409    | Conflicto: `username`/`email`/`product_key` duplicado                                                                                               |
| 500    | `POST /api/users/` sin `password` (pendiente de validar como 400)                                                                                   |

Sin token (o con uno falso) los servicios responden `401`; un usuario
sin `is_staff` recibe `403` en `/api/logs/*`.

### 7. Correr los tests (deben estar activos los servicios)

```bash
cd proyecto_django/back_end_django

docker compose exec -e DATABASE_ENGINE=django.db.backends.sqlite3 -e DATABASE_NAME=/tmp/t_auth.db servicio_auth python manage.py test autentificacion -v 2
docker compose exec -e DATABASE_ENGINE=django.db.backends.sqlite3 -e DATABASE_NAME=/tmp/t_usu.db servicio_usuarios python manage.py test gestion_usuarios -v 2
docker compose exec -e DATABASE_ENGINE=django.db.backends.sqlite3 -e DATABASE_NAME=/tmp/t_prod.db servicio_productos python manage.py test gestion_productos -v 2
```

### 8. Comandos útiles

```bash
docker compose logs -f gateway              # ver el tráfico del gateway
docker compose logs -f servicio_auth       # ver logs de un servicio
docker compose logs -f servicio_usuarios
docker compose logs -f servicio_productos
docker compose down                        # detener todo (conserva datos)
docker compose down -v                     # detener y BORRAR las BDs
```

Si los logs dan error de permisos en local:

```bash
sudo chown -R $USER:$USER proyecto_django/back_end_django/servicio_*/logs
chmod -R u+rwX proyecto_django/back_end_django/servicio_*/logs
```
