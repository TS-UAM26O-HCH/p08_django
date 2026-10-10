from uuid import UUID
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from gestion_productos.exceptions.productoExceptions import (
    ProductoNoEncontrado_404,
)
from gestion_productos.models import Productos


class ProductoDAO:
    """
    Data Access Object (DAO) para la gestión de productos en la base de datos.
    Proporciona métodos para realizar operaciones CRUD sobre el modelo Productos.
    """

    @staticmethod
    def obtener_todos():
        return Productos.objects.filter(is_deleted=False)

    @staticmethod
    def obtener_producto_por_id(producto_id):
        """
        Obtiene un producto por su ID si no ha sido eliminado.

        :param producto_id: UUID (string o UUID) del producto a buscar.
        :return: Instancia de Productos o lanza excepción si no se encuentra.
        """
        try:
            producto_uuid = (
                producto_id if isinstance(producto_id, UUID) else UUID(str(producto_id))
            )
            producto = Productos.objects.get(id=producto_uuid, is_deleted=False)
            return producto
        except Productos.DoesNotExist:
            raise ProductoNoEncontrado_404()
        except ValueError:
            raise ValidationError("El ID del producto no es un UUID válido.")

    @staticmethod
    def crear_producto(
        type: str,
        name: str,
        price,
        status: bool = True,
        product_key: str = None,
        image_link: str = None,
        description: str = None,
    ):
        # Validación de type
        if len(type) > 10:
            raise ValidationError(
                {"type": "El campo 'type' no puede tener más de 10 caracteres."}
            )

        # Validación de name
        if len(name) > 255:
            raise ValidationError(
                {"name": "El campo 'name' no puede tener más de 255 caracteres."}
            )

        # Validación de product_key
        if product_key and len(product_key) > 8:
            raise ValidationError(
                {
                    "product_key": "El campo 'product_key' no puede tener más de 8 caracteres."
                }
            )

        if product_key and Productos.objects.filter(product_key=product_key).exists():
            raise ValidationError({"product_key": "El 'product_key' ya existe."})

        # Validación de URL
        if image_link:
            validator = URLValidator()
            try:
                validator(image_link)
            except DjangoValidationError:
                raise ValidationError(
                    {"image_link": "El campo 'image_link' debe ser una URL válida."}
                )

        try:
            producto = Productos.objects.create(
                type=type,
                name=name,
                price=price,
                status=status,
                description=description,
                product_key=product_key,
                image_link=image_link,
            )

            return producto

        except IntegrityError as e:
            raise ValidationError({"error": f"Error al crear el producto: {str(e)}"})

    @staticmethod
    def actualizar_producto(pk, **datos_actualizar):
        """
        Actualiza los datos de un producto existente.
        """
        producto = ProductoDAO.obtener_producto_por_id(pk)

        if "type" in datos_actualizar and len(datos_actualizar["type"]) > 10:
            raise ValidationError(
                {"type": "El campo 'type' no puede tener más de 10 caracteres."}
            )

        if "name" in datos_actualizar and len(datos_actualizar["name"]) > 255:
            raise ValidationError(
                {"name": "El campo 'name' no puede tener más de 255 caracteres."}
            )

        if "product_key" in datos_actualizar:
            product_key = datos_actualizar["product_key"]

            if len(product_key) > 8:
                raise ValidationError(
                    {
                        "product_key": "El campo 'product_key' no puede tener más de 8 caracteres."
                    }
                )

            if (
                Productos.objects.filter(product_key=product_key)
                .exclude(id=producto.id)
                .exists()
            ):
                raise ValidationError({"product_key": "El 'product_key' ya existe."})

        if "image_link" in datos_actualizar:
            validator = URLValidator()

            try:
                validator(datos_actualizar["image_link"])
            except DjangoValidationError:
                raise ValidationError(
                    {"image_link": "El campo 'image_link' debe ser una URL válida."}
                )

        for campo, valor in datos_actualizar.items():
            setattr(producto, campo, valor)

        producto.save()

        return producto

    @staticmethod
    def actualizar_producto_parcial(pk, **campos_actualizar):
        """
        Actualiza parcialmente los campos de un producto existente.
        """
        producto = ProductoDAO.obtener_producto_por_id(pk)

        if "type" in campos_actualizar and len(campos_actualizar["type"]) > 10:
            raise ValidationError(
                {"type": "El campo 'type' no puede tener más de 10 caracteres."}
            )

        if "name" in campos_actualizar and len(campos_actualizar["name"]) > 255:
            raise ValidationError(
                {"name": "El campo 'name' no puede tener más de 255 caracteres."}
            )

        if "product_key" in campos_actualizar:
            product_key = campos_actualizar["product_key"]
            if len(product_key) > 8:
                raise ValidationError(
                    {
                        "product_key": "El campo 'product_key' no puede tener más de 8 caracteres."
                    }
                )

            if (
                Productos.objects.filter(product_key=product_key)
                .exclude(id=producto.id)
                .exists()
            ):
                raise ValidationError({"product_key": "El 'product_key' ya existe."})

        if "image_link" in campos_actualizar:
            validator = URLValidator()
            try:
                validator(campos_actualizar["image_link"])
            except DjangoValidationError:
                raise ValidationError(
                    {"image_link": "El campo 'image_link' debe ser una URL válida."}
                )

        for campo, valor in campos_actualizar.items():
            setattr(producto, campo, valor)

        producto.save()
        return producto

    @staticmethod
    def eliminar_producto(pk):
        producto = ProductoDAO.obtener_producto_por_id(pk)
        producto.is_deleted = True
        producto.deleted_at = timezone.now()
        producto.save()
        return producto

    @staticmethod
    def restaurar_producto(pk):
        try:
            producto_id = UUID(str(pk))
            producto = Productos.objects.get(id=producto_id)
        except Productos.DoesNotExist:
            raise ProductoNoEncontrado_404()
        except ValueError:
            raise ValidationError("El ID del producto no es un UUID válido.")

        if not producto.is_deleted:
            raise ValidationError("El producto no está eliminado")

        producto.is_deleted = False
        producto.deleted_at = None
        producto.save()
        return producto

    @staticmethod
    def buscar_productos(query):
        return Productos.objects.filter(
            Q(is_deleted=False)
            & (Q(name__icontains=query) | Q(description__icontains=query))
        )

    @staticmethod
    def filtrar_por_rango_precio(precio_min, precio_max):
        """
        Obtiene los productos cuyo precio se encuentra dentro del rango especificado.
        """

        return Productos.objects.filter(
            is_deleted=False, price__gte=precio_min, price__lte=precio_max
        )

    @staticmethod
    def actualizar_img(pk, img_link):
        producto = ProductoDAO.obtener_producto_por_id(pk)

        if len(img_link) > 200:
            raise ValidationError("La URL excede el límite de 200 caracteres.")

        producto.image_link = img_link
        producto.modified_at = timezone.now()
        producto.save()
        return producto

    @staticmethod
    def desactivar_producto(pk):
        try:
            producto_id = UUID(str(pk))
        except ValueError:
            raise ValidationError("El ID del producto no es un UUID válido.")

        try:
            producto = Productos.objects.get(id=producto_id)
        except Productos.DoesNotExist:
            raise ProductoNoEncontrado_404("Producto no encontrado")

        if producto.status:
            producto.status = False
            producto.modified_at = timezone.now()
            producto.save()

        return producto

    @staticmethod
    def activar_producto(pk):
        try:
            producto_id = UUID(str(pk))
        except ValueError:
            raise ValidationError("El ID del producto no es un UUID válido.")

        try:
            producto = Productos.objects.get(id=producto_id)
        except Productos.DoesNotExist:
            raise ProductoNoEncontrado_404("Producto no encontrado")

        if producto.status:
            raise ValidationError("El producto ya está activado")

        producto.status = True
        producto.modified_at = timezone.now()
        producto.save()
        return producto
