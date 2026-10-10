from rest_framework import serializers
from .models import Productos


class ProductoCompletoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Productos
        fields = [
            "id",
            "type",
            "name",
            "price",
            "status",
            "description",
            "product_key",
            "image_link",
        ]


class ProductoParcialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Productos
        fields = [
            "type",
            "name",
            "price",
            "status",
            "description",
            "product_key",
            "image_link",
        ]
        extra_kwargs = {campo: {"required": False} for campo in fields}
